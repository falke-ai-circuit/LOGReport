package telnet

import (
	"context"
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
// with via REST API — send commands, retrieve output.
type SessionManager struct {
	sessions map[string]*Session
	mu       sync.RWMutex
}

// Session wraps a persistent telnet connection with output buffering.
type Session struct {
	ID           string
	Client       *Client
	Address      string
	Port         int
	Connected    bool
	Output       chan string // streamed output (kept for compat, not actively used)
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
		return fmt.Sprintf("sess-%d", time.Now().UnixNano())
	}
	return "sess-" + hex.EncodeToString(b)
}

// Connect creates a new persistent telnet session.
// After establishing the TCP connection, verifySystemMode() is called
// to initialize the DNA debugger into system mode. This matches the
// Python session_manager.py verify_system_mode():
//  1. Send "yes\r\n" (handle "someone else is connected" conflict prompt)
//  2. Send Ctrl+Z (0x1a) to clear terminal
//  3. Send "systemmode\r\n" to switch to system mode
func (sm *SessionManager) Connect(sessionID, host string, port int, timeout time.Duration) (*Session, error) {
	return sm.ConnectContext(context.Background(), sessionID, host, port, timeout)
}

// ConnectContext creates a new persistent telnet session with a context-aware
// dial. If ctx is cancelled (e.g. queue Cancel/Pause closes cancelCh), the
// Dial aborts immediately instead of blocking for the full timeout.
// This is critical for F8: Cancel must work even when the host is unreachable
// and Dial is the blocking call.
func (sm *SessionManager) ConnectContext(ctx context.Context, sessionID, host string, port int, timeout time.Duration) (*Session, error) {
	if sessionID == "" {
		sessionID = generateSessionID()
	}

	client, err := DialContext(ctx, host, port, timeout)
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
	sm.verifySystemMode(sess)

	sm.mu.Lock()
	sm.sessions[sessionID] = sess
	sm.mu.Unlock()

	return sess, nil
}

// verifySystemMode initializes the DNA debugger into system mode.
// Mirrors the Python session_manager.py verify_system_mode():
//  1. Send "yes\r\n" — handles the "someone else is connected, disconnect?" prompt
//  2. Send Ctrl+Z (0x1a) — clears terminal
//  3. Send "systemmode\r\n" — switches from application mode to system mode
//
// Any errors during initialization are non-fatal — the session remains usable.
func (sm *SessionManager) verifySystemMode(sess *Session) {
	conn := sess.Client.conn
	if conn == nil {
		return
	}

	drainBuf := make([]byte, 4096)

	// Step 1: Read initial response to check for override prompt
	// DIA may show "Active connection exists / Do you want to override?"
	// or just a normal prompt
	time.Sleep(1 * time.Second)
	conn.SetReadDeadline(time.Now().Add(2 * time.Second))
	n, _ := conn.Read(drainBuf)
	if n > 0 {
		cleaned := sess.Client.stripIAC(drainBuf[:n])
		initialResp := string(cleaned)
		// Check if override prompt is present
		if strings.Contains(strings.ToLower(initialResp), "override") ||
			strings.Contains(initialResp, "y(es)/n(o)") {
			// Send "y" to override
			conn.SetWriteDeadline(time.Now().Add(3 * time.Second))
			conn.Write([]byte("y\r\n"))
			time.Sleep(2 * time.Second)
			// Drain override response
			conn.SetReadDeadline(time.Now().Add(1 * time.Second))
			conn.Read(drainBuf)
		}
		// Send initial response to output channel
		filtered := FilterOutput(initialResp)
		if filtered != "" {
			select {
			case sess.Output <- filtered:
			default:
			}
		}
	}

	// Step 2: Clear the DIA line editor with Ctrl+X + Ctrl+Z + Enter
	// This is critical because the DIA retains text from previous sessions
	conn.SetWriteDeadline(time.Now().Add(3 * time.Second))
	conn.Write([]byte{0x18}) // Ctrl+X
	time.Sleep(100 * time.Millisecond)
	conn.Write([]byte{0x1a}) // Ctrl+Z
	time.Sleep(500 * time.Millisecond)

	// Drain clear response
	conn.SetReadDeadline(time.Now().Add(500 * time.Millisecond))
	conn.Read(drainBuf)

	// Send Enter to submit empty line and get fresh prompt
	conn.SetWriteDeadline(time.Now().Add(3 * time.Second))
	conn.Write([]byte("\r\n"))
	time.Sleep(500 * time.Millisecond)
	conn.SetReadDeadline(time.Now().Add(500 * time.Millisecond))
	conn.Read(drainBuf)

	// Step 3: Send "systemmode" to switch to system mode
	conn.SetWriteDeadline(time.Now().Add(3 * time.Second))
	conn.Write([]byte("systemmode\r\n"))
	time.Sleep(1 * time.Second)

	// Drain systemmode response
	conn.SetReadDeadline(time.Now().Add(1 * time.Second))
	if n, err := conn.Read(drainBuf); n > 0 && err == nil {
		cleaned := sess.Client.stripIAC(drainBuf[:n])
		filtered := FilterOutput(string(cleaned))
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

// readLoop continuously reads from the telnet connection. This runs only
// when no synchronous command is in progress. It's started by Connect for
// streaming mode but SendCommand stops it during synchronous reads.
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

		conn.SetReadDeadline(time.Now().Add(200 * time.Millisecond))
		n, err := conn.Read(buf)
		if n > 0 {
			cleaned := s.Client.stripIAC(buf[:n])
			s.mu.Lock()
			s.outputBuffer.WriteString(string(cleaned))
			s.mu.Unlock()
		}
		if err != nil {
			if netErr, ok := err.(net.Error); ok && netErr.Timeout() {
				continue
			}
			s.mu.Lock()
			s.Connected = false
			s.mu.Unlock()
			return
		}
	}
}

// SendCommand sends a command through an existing session.
//
// This is a SYNCHRONOUS operation that mirrors the Python
// session_manager.py send_command():
//  1. Drain any pending data from the input buffer
//  2. Send Ctrl+X (0x18) + Ctrl+Z (0x1A) to clear the DIA line editor
//  3. Drain the clear response (including any help text triggered by Ctrl+Z)
//  4. Send the command with \r\n termination
//  5. Read response synchronously with prompt detection (up to timeout)
//  6. Filter output (strip ANSI, control chars, backspaces, normalize whitespace)
//  7. Remove command echo from the response
//  8. Store the result in the session output buffer
//
// The readLoop must NOT be running during this call to avoid concurrent
// reads on the same TCP socket. SendCommand does NOT start readLoop.
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
	timeout := 5 * time.Second
	if sess.Client.timeout > 0 {
		timeout = sess.Client.timeout
	}

	// Step 1: Drain any pending data from the input buffer
	conn.SetReadDeadline(time.Now().Add(100 * time.Millisecond))
	drainBuf := make([]byte, 4096)
	conn.Read(drainBuf) // discard pending data

	// Step 2: Clear the DIA line editor:
	//   a) Ctrl+X (0x18) — cancel current input
	//   b) Ctrl+Z (0x1A) — clears the visible line (sends backspaces+spaces)
	//   c) Enter (\r\n) — submit the cleared (empty) line to get a fresh prompt
	// This 3-step sequence is critical because the DIA line editor retains
	// text from previous commands/sessions. Without clearing, new command
	// characters are typed over old text in REPLACE mode, producing garbled
	// output and BEL (0x07) errors.
	conn.SetWriteDeadline(time.Now().Add(3 * time.Second))
	conn.Write([]byte{0x18}) // Ctrl+X
	time.Sleep(100 * time.Millisecond)
	conn.Write([]byte{0x1a}) // Ctrl+Z
	time.Sleep(500 * time.Millisecond)

	// Drain the Ctrl+Z clear response (backspaces + spaces)
	conn.SetReadDeadline(time.Now().Add(300 * time.Millisecond))
	conn.Read(drainBuf)

	// Send Enter to submit the empty line and get a fresh prompt
	conn.SetWriteDeadline(time.Now().Add(3 * time.Second))
	conn.Write([]byte("\r\n"))
	time.Sleep(300 * time.Millisecond)

	// Drain the Enter response (prompt)
	conn.SetReadDeadline(time.Now().Add(300 * time.Millisecond))
	conn.Read(drainBuf)

	// Step 4: Send the command with \r\n termination
	conn.SetWriteDeadline(time.Now().Add(3 * time.Second))
	cmdBytes := []byte(cmd + "\r\n")
	n, err := conn.Write(cmdBytes)
	if err != nil {
		return fmt.Errorf("telnet write: %w", err)
	}
	if n != len(cmdBytes) {
		return fmt.Errorf("telnet: short write (%d/%d bytes)", n, len(cmdBytes))
	}

	// Step 5: Read response synchronously with prompt detection
	response, readErr := sess.Client.ReadUntilPromptContextWithTimeout(timeout)

	// Step 6: Filter output
	filtered := FilterOutput(response)

	// Step 7: Do NOT remove command echo — the user wants to see the full
	// DIA response including command echo and any error indicators (BEL).
	// This matches raw telnet behavior where you see what you typed + the
	// response. The Python reference also keeps the echo in some code paths.
	// The echo is useful for debugging and matches what a standard telnet
	// client shows.
	//
	// Old behavior (removed): echo was stripped via regex, which also
	// stripped the command text when DIA echoed it with backspaces.

	if readErr != nil && filtered == "" {
		return fmt.Errorf("telnet read: %w", readErr)
	}

	// Step 8: Store result in output buffer
	sess.outputBuffer.Reset()
	sess.outputBuffer.WriteString(filtered)

	// Also push to Output channel for any streaming consumers
	if filtered != "" {
		select {
		case sess.Output <- filtered:
		default:
		}
	}

	return nil
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

	close(sess.Done)

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
// The output is already filtered when stored in the buffer (by SendCommand),
// so we return it directly without re-filtering to avoid double-processing.
func (sm *SessionManager) GetOutput(sessionID string) (string, error) {
	sm.mu.RLock()
	sess, ok := sm.sessions[sessionID]
	sm.mu.RUnlock()
	if !ok {
		return "", fmt.Errorf("session %s not found", sessionID)
	}

	sess.mu.Lock()
	defer sess.mu.Unlock()
	return sess.outputBuffer.String(), nil
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

// SendSystemCommand sends a command in DIA system mode.
// It clears the DIA line editor with Ctrl+X + Enter (NOT Ctrl+Z which exits system mode),
// then sends the command. The response is stored in the session output buffer.
func (sm *SessionManager) SendSystemCommand(sessionID, cmd string) error {
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

	// Step 1: Drain pending data
	conn.SetReadDeadline(time.Now().Add(100 * time.Millisecond))
	drainBuf := make([]byte, 4096)
	conn.Read(drainBuf)

	// Step 2: Clear line editor with Ctrl+X only (NOT Ctrl+Z — that exits system mode)
	conn.SetWriteDeadline(time.Now().Add(3 * time.Second))
	conn.Write([]byte{0x18}) // Ctrl+X — cancel current input
	time.Sleep(100 * time.Millisecond)

	// Drain Ctrl+X response
	conn.SetReadDeadline(time.Now().Add(200 * time.Millisecond))
	conn.Read(drainBuf)

	// Step 3: Send Enter to get a fresh prompt (without exiting system mode)
	conn.SetWriteDeadline(time.Now().Add(3 * time.Second))
	conn.Write([]byte("\r\n"))
	time.Sleep(300 * time.Millisecond)

	// Drain the Enter response (prompt)
	conn.SetReadDeadline(time.Now().Add(300 * time.Millisecond))
	conn.Read(drainBuf)

	// Step 4: Send the actual command
	if err := sess.Client.SendCommand(cmd); err != nil {
		return err
	}

	// Read the response
	timeout := 10 * time.Second
	if sess.Client.timeout > 0 {
		timeout = sess.Client.timeout
	}
	response, readErr := sess.Client.ReadUntilPromptContextWithTimeout(timeout)
	filtered := FilterOutput(response)

	if readErr != nil && filtered == "" {
		return fmt.Errorf("telnet read: %w", readErr)
	}

	// Store result
	sess.outputBuffer.Reset()
	sess.outputBuffer.WriteString(filtered)

	if filtered != "" {
		select {
		case sess.Output <- filtered:
		default:
		}
	}

	return nil
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

type mockServer struct {
	ln     net.Listener
	output chan string
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
		conn.Write([]byte(received + "\n1a% "))
	}
}

func (ms *mockServer) addr() string {
	return ms.ln.Addr().String()
}

func (ms *mockServer) close() {
	ms.ln.Close()
}