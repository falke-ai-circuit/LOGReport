package telnet

import (
	"crypto/rand"
	"encoding/hex"
	"fmt"
	"net"
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
	ID        string
	Client    *Client
	Address   string
	Port      int
	Connected bool
	Output    chan string // streamed output to WebSocket
	Done      chan struct{}
	mu        sync.Mutex
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
//   1. Send "yes\r\n" (handle "someone else is connected" conflict prompt)
//   2. Send Ctrl+Z (\x1a) to clear terminal
//   3. Send "systemmode\r\n" to switch to system mode
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
//   1. Send "yes\r\n" — handles the "someone else is connected, disconnect?" prompt
//   2. Send Ctrl+Z (\x1a) — clears the terminal of any leftover content
//   3. Send "systemmode\r\n" — switches from application mode to system mode
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
	time.Sleep(300 * time.Millisecond)

	// Drain any response
	conn.SetReadDeadline(time.Now().Add(300 * time.Millisecond))
	drainBuf := make([]byte, 4096)
	if n, err := conn.Read(drainBuf); n > 0 && err == nil {
		filtered := FilterOutput(string(drainBuf[:n]))
		if filtered != "" {
			select {
			case sess.Output <- filtered:
			default:
			}
		}
	}

	// Step 2: Send Ctrl+Z to clear terminal
	conn.SetWriteDeadline(time.Now().Add(3 * time.Second))
	conn.Write([]byte{0x1a}) // Ctrl+Z
	time.Sleep(200 * time.Millisecond)

	// Drain
	conn.SetReadDeadline(time.Now().Add(300 * time.Millisecond))
	if n, err := conn.Read(drainBuf); n > 0 && err == nil {
		filtered := FilterOutput(string(drainBuf[:n]))
		if filtered != "" {
			select {
			case sess.Output <- filtered:
			default:
			}
		}
	}

	// Step 3: Send "systemmode" to switch to system mode
	conn.SetWriteDeadline(time.Now().Add(3 * time.Second))
	conn.Write([]byte("systemmode\r\n"))
	time.Sleep(300 * time.Millisecond)

	// Drain and push any response to output
	conn.SetReadDeadline(time.Now().Add(500 * time.Millisecond))
	if n, err := conn.Read(drainBuf); n > 0 && err == nil {
		filtered := FilterOutput(string(drainBuf[:n]))
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
			filtered := FilterOutput(string(buf[:n]))
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
// Before sending, it clears the input buffer by sending Ctrl+X (\x18)
// then Ctrl+Z (\x1A) with a short delay, matching the Python
// telnet_client.py:82-89 behavior.
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

	// Buffer clearing: send Ctrl+X then Ctrl+Z with 100ms delay
	// (matches Python telnet_client.py:82-89)
	conn.SetWriteDeadline(time.Now().Add(5 * time.Second))
	conn.Write([]byte{0x18}) // Ctrl+X
	time.Sleep(100 * time.Millisecond)
	conn.Write([]byte{0x1A}) // Ctrl+Z
	time.Sleep(100 * time.Millisecond)

	// Drain any pending read data
	conn.SetReadDeadline(time.Now().Add(100 * time.Millisecond))
	drainBuf := make([]byte, 4096)
	for {
		n, err := conn.Read(drainBuf)
		if n > 0 {
			filtered := FilterOutput(string(drainBuf[:n]))
			if filtered != "" {
				select {
				case sess.Output <- filtered:
				default:
				}
			}
		}
		if err != nil {
			break
		}
	}
	conn.SetReadDeadline(time.Time{})

	// Send the actual command
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