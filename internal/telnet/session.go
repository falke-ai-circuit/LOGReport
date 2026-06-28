package telnet

import (
	"crypto/rand"
	"encoding/hex"
	"fmt"
	"net"
	"strings"
	"sync"
	"time"
)

// ─── SessionManager ──────────────────────────────────────────────

// SessionManager manages persistent telnet connections keyed by session ID.
// Each session maintains a live telnet connection that can be interacted
// with via WebSocket — send commands, receive streamed output.
type SessionManager struct {
	sessions map[string]*Session
	mu       sync.RWMutex
}

// Session wraps a persistent telnet connection with streaming output.
type Session struct {
	ID           string
	Client       *Client
	Address      string
	Port         int
	Connected    bool
	Output       chan string // streamed output to WebSocket
	Done         chan struct{}
	mu           sync.Mutex
	outputBuffer strings.Builder // accumulated output for REST retrieval
}

// NewSessionManager creates a new session manager.
func NewSessionManager() *SessionManager {
	return &SessionManager{
		sessions: make(map[string]*Session),
	}
}

// generateSessionID produces a random hex session ID.
func generateSessionID() string {
	b := make([]byte, 8)
	if _, err := rand.Read(b); err != nil {
		// Fallback to timestamp
		return fmt.Sprintf("sess-%d", time.Now().UnixNano())
	}
	return "sess-" + hex.EncodeToString(b)
}

// Connect creates a new persistent telnet session.
// The session ID is generated and returned via the Session.
// A background goroutine reads from the telnet connection and pushes
// filtered output to the Session.Output channel.
//
// After establishing the TCP connection, verifySystemMode() is called
// to initialize the DNA debugger into system mode. This matches the
// Python telnet_service.py behavior:
//  1. Send "yes\r\n" (handle "someone else is connected" conflict prompt)
//  2. Send Ctrl+Z (\x1a) to clear terminal
//  3. Send "systemmode\r\n" to switch to system mode
//
// This is required for FBC/RPC print commands to work on real DNA nodes.
func (sm *SessionManager) Connect(sessionID, host string, port int, timeout time.Duration) (*Session, error) {
	if sessionID == "" {
		sessionID = generateSessionID()
	}

	client, err := Dial(host, port, timeout)
	if err != nil {
		return nil, fmt.Errorf("session connect %s:%d: %w", host, port, err)
	}

	sess := &Session{
		ID:        sessionID,
		Client:    client,
		Address:   host,
		Port:      port,
		Connected: true,
		Output:    make(chan string, 256),
		Done:      make(chan struct{}),
	}

	// Initialize system mode on the DNA debugger.
	// This is a no-op on mock servers (they just echo back) but is
	// critical for real DNA nodes which start in application mode.
	sm.verifySystemMode(sess)

	// Background reader: reads from telnet conn, filters, pushes to Output
	go sess.readLoop()

	sm.mu.Lock()
	sm.sessions[sessionID] = sess
	sm.mu.Unlock()

	return sess, nil
}

// verifySystemMode initializes the DNA debugger into system mode.
// This sequence mirrors the Python telnet_service.py verify_system_mode():
//  1. Send "yes\r\n" — handles the "someone else is connected, disconnect?" prompt
//  2. Send "systemmode\r\n" — switches from application mode to system mode
//
// Note: We do NOT send Ctrl+Z (\x1a) here — in DIA system mode, Ctrl+Z
// triggers the "?" help menu, which pollutes the output buffer with
// 1000+ bytes of help text. The original Python code sent Ctrl+Z to
// clear the terminal, but that behavior is specific to application mode.
//
// On real DNA nodes, FBC/RPC print commands only work in system mode.
// On mock/test servers, these writes are harmless (server just echoes or ignores).
// Any errors during initialization are non-fatal — the session remains usable.
// The output from these commands is pushed to the Output channel so the
// frontend can display the initialization sequence.
func (sm *SessionManager) verifySystemMode(sess *Session) {
	conn := sess.Client.conn
	if conn == nil {
		return
	}

	// Step 1: Send "yes" to handle potential conflict prompt
	conn.SetWriteDeadline(time.Now().Add(3 * time.Second))
	conn.Write([]byte("yes\r\n"))
	time.Sleep(500 * time.Millisecond)

	// Drain any response (with IAC stripping)
	conn.SetReadDeadline(time.Now().Add(500 * time.Millisecond))
	drainBuf := make([]byte, 4096)
	if n, err := conn.Read(drainBuf); n > 0 && err == nil {
		cleaned := sess.Client.stripIAC(drainBuf[:n])
		sess.outputBuffer.WriteString(string(cleaned))
		filtered := FilterOutputNoBackspace(processBackspaces(string(cleaned)))
		if filtered != "" {
			select {
			case sess.Output <- filtered:
			default:
			}
		}
	}

	// Step 2: Send "systemmode" to switch to system mode
	// (skip Ctrl+Z — it triggers help menu in system mode)
	conn.SetWriteDeadline(time.Now().Add(3 * time.Second))
	conn.Write([]byte("systemmode\r\n"))
	time.Sleep(500 * time.Millisecond)

	// Drain and push any response to output
	conn.SetReadDeadline(time.Now().Add(1 * time.Second))
	if n, err := conn.Read(drainBuf); n > 0 && err == nil {
		cleaned := sess.Client.stripIAC(drainBuf[:n])
		sess.outputBuffer.WriteString(string(cleaned))
		filtered := FilterOutputNoBackspace(processBackspaces(string(cleaned)))
		if filtered != "" {
			select {
			case sess.Output <- filtered:
			default:
			}
		}
	}

	// Reset deadlines
	conn.SetReadDeadline(time.Time{})
	conn.SetWriteDeadline(time.Time{})
}

// readLoop continuously reads from the telnet connection and pushes
// filtered output to the Output channel. Exits when the connection
// is closed or Done is signaled.
func (s *Session) readLoop() {
	buf := make([]byte, 4096)
	for {
		select {
		case <-s.Done:
			return
		default:
		}

		s.mu.Lock()
		conn := s.Client.conn
		s.mu.Unlock()
		if conn == nil {
			return
		}

		// Set short read deadline so we can check Done periodically
		conn.SetReadDeadline(time.Now().Add(200 * time.Millisecond))
		n, err := conn.Read(buf)
		if n > 0 {
			// Strip IAC commands from the data before filtering
			cleaned := s.Client.stripIAC(buf[:n])
			// Append raw (post-IAC) data to buffer first, THEN filter
			// This ensures backspaces from DIA echo are processed across
			// chunk boundaries (echo and backspaces may arrive in separate reads)
			s.mu.Lock()
			s.outputBuffer.WriteString(string(cleaned))
			// Now apply backspace processing + filter on the full buffer
			full := s.outputBuffer.String()
			s.mu.Unlock()
			// Process backspaces on the full accumulated buffer
			processed := processBackspaces(full)
			filtered := FilterOutputNoBackspace(processed)
			if filtered != "" {
				select {
				case s.Output <- filtered:
				default:
					// Channel full, drop output (avoid blocking reader)
				}
			}
		}
		if err != nil {
			if netErr, ok := err.(net.Error); ok && netErr.Timeout() {
				continue // Normal timeout, keep reading
			}
			// Connection closed or error — mark disconnected and exit
			s.mu.Lock()
			s.Connected = false
			s.mu.Unlock()
			return
		}
	}
}

// SendCommand sends a command through an existing session.
// The readLoop handles all reading from the connection.
// We do NOT send Ctrl+X/Ctrl+Z before commands — in DIA system mode,
// Ctrl+Z triggers the "?" help menu, which pollutes the output buffer.
//
// To clear the DIA's INSERT-mode line editor (which may retain text from
// a previous command or session), we send a bare \r\n first. This submits
// whatever is on the current line (producing an error/no-op) and gives us
// a fresh prompt. The caller should call ClearOutput before sending to get
// clean per-command output.
func (sm *SessionManager) SendCommand(sessionID, cmd string) error {
	sm.mu.RLock()
	sess, ok := sm.sessions[sessionID]
	sm.mu.RUnlock()
	if !ok {
		return fmt.Errorf("session %s not found", sessionID)
	}

	sess.mu.Lock()
	defer sess.mu.Unlock()

	if !sess.Connected || sess.Client.conn == nil {
		return fmt.Errorf("session %s not connected", sessionID)
	}

	conn := sess.Client.conn

	// Step 1: Send a bare Enter to flush the DIA's line editor.
	// In INSERT/REPLACE mode, the DIA line may contain leftover text
	// from a previous command. Pressing Enter submits it (harmless error)
	// and gives us a fresh prompt with an empty line.
	conn.SetWriteDeadline(time.Now().Add(3 * time.Second))
	conn.Write([]byte("\r\n"))
	time.Sleep(300 * time.Millisecond)

	// Step 2: Send the actual command
	return sess.Client.SendCommand(cmd)
}

// Disconnect closes a session and removes it from the manager.
func (sm *SessionManager) Disconnect(sessionID string) error {
	sm.mu.Lock()
	sess, ok := sm.sessions[sessionID]
	if ok {
		delete(sm.sessions, sessionID)
	}
	sm.mu.Unlock()

	if !ok {
		return fmt.Errorf("session %s not found", sessionID)
	}

	close(sess.Done) // Signal readLoop to stop

	sess.mu.Lock()
	defer sess.mu.Unlock()
	sess.Connected = false
	if sess.Client != nil {
		err := sess.Client.Close()
		close(sess.Output)
		return err
	}
	close(sess.Output)
	return nil
}

// GetSession returns an active session by ID.
func (sm *SessionManager) GetSession(sessionID string) (*Session, bool) {
	sm.mu.RLock()
	defer sm.mu.RUnlock()
	sess, ok := sm.sessions[sessionID]
	return sess, ok
}

// GetOutput returns the accumulated output buffer for a session.
// The output is processed through backspace removal and filtering
// to produce clean text without DIA INSERT-mode echo artifacts.
func (sm *SessionManager) GetOutput(sessionID string) (string, error) {
	sm.mu.RLock()
	sess, ok := sm.sessions[sessionID]
	sm.mu.RUnlock()
	if !ok {
		return "", fmt.Errorf("session %s not found", sessionID)
	}

	sess.mu.Lock()
	defer sess.mu.Unlock()
	// Process backspaces on the full accumulated buffer, then filter
	processed := processBackspaces(sess.outputBuffer.String())
	return FilterOutputNoBackspace(processed), nil
}

// ClearOutput resets the output buffer for a session.
func (sm *SessionManager) ClearOutput(sessionID string) error {
	sm.mu.RLock()
	sess, ok := sm.sessions[sessionID]
	sm.mu.RUnlock()
	if !ok {
		return fmt.Errorf("session %s not found", sessionID)
	}

	sess.mu.Lock()
	defer sess.mu.Unlock()
	sess.outputBuffer.Reset()
	return nil
}

// ListSessions returns all active session IDs.
func (sm *SessionManager) ListSessions() []string {
	sm.mu.RLock()
	defer sm.mu.RUnlock()
	ids := make([]string, 0, len(sm.sessions))
	for id := range sm.sessions {
		ids = append(ids, id)
	}
	return ids
}

// SessionCount returns the number of active sessions.
func (sm *SessionManager) SessionCount() int {
	sm.mu.RLock()
	defer sm.mu.RUnlock()
	return len(sm.sessions)
}

// CloseAll disconnects all active sessions. Used on server shutdown.
func (sm *SessionManager) CloseAll() {
	sm.mu.Lock()
	defer sm.mu.Unlock()

	for id, sess := range sm.sessions {
		close(sess.Done)
		sess.mu.Lock()
		sess.Connected = false
		if sess.Client != nil {
			sess.Client.Close()
		}
		sess.mu.Unlock()
		delete(sm.sessions, id)
	}
}

// ─── Mock server for testing ─────────────────────────────────────

// mockServer is a simple TCP server that echoes received data back
// with a DNA-style prompt. Used by session_test.go.
// Supports multiple sequential connections (needed for CloseAll test).
type mockServer struct {
	ln     net.Listener
	output chan string // received commands
}

func newMockServer() (*mockServer, error) {
	ln, err := net.Listen("tcp", "127.0.0.1:0")
	if err != nil {
		return nil, err
	}
	ms := &mockServer{
		ln:     ln,
		output: make(chan string, 32),
	}
	go ms.serve()
	return ms, nil
}

func (ms *mockServer) serve() {
	for {
		conn, err := ms.ln.Accept()
		if err != nil {
			return
		}
		go ms.handleConn(conn)
	}
}

func (ms *mockServer) handleConn(conn net.Conn) {
	defer conn.Close()
	// Send initial prompt
	conn.Write([]byte("1a% "))
	buf := make([]byte, 4096)
	for {
		n, err := conn.Read(buf)
		if err != nil {
			return
		}
		received := string(buf[:n])
		select {
		case ms.output <- received:
		default:
		}
		// Echo back with a prompt
		conn.Write([]byte(received + "\n1a% "))
	}
}

func (ms *mockServer) addr() string {
	return ms.ln.Addr().String()
}

func (ms *mockServer) close() {
	ms.ln.Close()
}
