package telnet

import (
	"fmt"
	"net"
	"strings"
	"testing"
	"time"
)

func TestNewSessionManager(t *testing.T) {
	sm := NewSessionManager()
	if sm == nil {
		t.Fatal("expected non-nil SessionManager")
	}
	if sm.SessionCount() != 0 {
		t.Errorf("expected 0 sessions, got %d", sm.SessionCount())
	}
}

func TestSessionConnectDisconnect(t *testing.T) {
	ms, err := newMockServer()
	if err != nil {
		t.Fatalf("mock server: %v", err)
	}
	defer ms.close()

	sm := NewSessionManager()

	// Parse host:port from mock server address
	addr := ms.addr()
	host, port, _ := net.SplitHostPort(addr)
	portInt := 0
	fmt.Sscanf(port, "%d", &portInt)

	sess, err := sm.Connect("", host, portInt, 5*time.Second)
	if err != nil {
		t.Fatalf("Connect failed: %v", err)
	}
	if sess.ID == "" {
		t.Error("expected non-empty session ID")
	}
	if !sess.Connected {
		t.Error("expected session to be connected")
	}

	// Verify session is listed
	ids := sm.ListSessions()
	if len(ids) != 1 {
		t.Fatalf("expected 1 session, got %d", len(ids))
	}
	if ids[0] != sess.ID {
		t.Errorf("expected session ID %s, got %s", sess.ID, ids[0])
	}

	// GetSession
	got, ok := sm.GetSession(sess.ID)
	if !ok {
		t.Fatal("GetSession returned false")
	}
	if got.ID != sess.ID {
		t.Errorf("expected ID %s, got %s", sess.ID, got.ID)
	}

	// Disconnect
	if err := sm.Disconnect(sess.ID); err != nil {
		t.Fatalf("Disconnect failed: %v", err)
	}
	if sm.SessionCount() != 0 {
		t.Errorf("expected 0 sessions after disconnect, got %d", sm.SessionCount())
	}
}

func TestSessionSendCommand(t *testing.T) {
	ms, err := newMockServer()
	if err != nil {
		t.Fatalf("mock server: %v", err)
	}
	defer ms.close()

	sm := NewSessionManager()

	addr := ms.addr()
	host, port, _ := net.SplitHostPort(addr)
	portInt := 0
	fmt.Sscanf(port, "%d", &portInt)

	sess, err := sm.Connect("", host, portInt, 5*time.Second)
	if err != nil {
		t.Fatalf("Connect failed: %v", err)
	}
	defer sm.Disconnect(sess.ID)

	// Send a command
	cmd := "show all"
	if err := sm.SendCommand(sess.ID, cmd); err != nil {
		t.Fatalf("SendCommand failed: %v", err)
	}

	// Verify the mock server received the command.
	// The Connect() call sends verifySystemMode messages (yes, Ctrl+Z, systemmode)
	// and SendCommand sends buffer-clearing (Ctrl+X, Ctrl+Z) before the actual command.
	// That's 6 messages total. Collect until we see the actual command.
	found := false
	for i := 0; i < 15; i++ {
		select {
		case received := <-ms.output:
			if strings.Contains(received, cmd) {
				found = true
			}
		case <-time.After(2 * time.Second):
			if i == 0 {
				t.Fatal("timeout waiting for mock server to receive any data")
			}
		}
	}
	if !found {
		t.Errorf("expected to receive command %q from mock server", cmd)
	}
}

func TestSessionSendCommandNotFound(t *testing.T) {
	sm := NewSessionManager()
	err := sm.SendCommand("nonexistent", "test")
	if err == nil {
		t.Fatal("expected error for non-existent session")
	}
}

func TestSessionDisconnectNotFound(t *testing.T) {
	sm := NewSessionManager()
	err := sm.Disconnect("nonexistent")
	if err == nil {
		t.Fatal("expected error for disconnecting non-existent session")
	}
}

func TestSessionConnectFailure(t *testing.T) {
	sm := NewSessionManager()
	// Connect to a port that doesn't exist (port 1 is reserved/unlikely to be open)
	_, err := sm.Connect("test-fail", "127.0.0.1", 1, 500*time.Millisecond)
	if err == nil {
		t.Fatal("expected error for connection to non-existent server")
	}
}

func TestSessionCloseAll(t *testing.T) {
	ms, err := newMockServer()
	if err != nil {
		t.Fatalf("mock server: %v", err)
	}
	defer ms.close()

	sm := NewSessionManager()
	addr := ms.addr()
	host, port, _ := net.SplitHostPort(addr)
	portInt := 0
	fmt.Sscanf(port, "%d", &portInt)

	_, err = sm.Connect("", host, portInt, 5*time.Second)
	if err != nil {
		t.Fatalf("Connect failed: %v", err)
	}
	_, err = sm.Connect("", host, portInt, 5*time.Second)
	if err != nil {
		t.Fatalf("Connect 2 failed: %v", err)
	}

	if sm.SessionCount() != 2 {
		t.Fatalf("expected 2 sessions, got %d", sm.SessionCount())
	}

	sm.CloseAll()
	if sm.SessionCount() != 0 {
		t.Errorf("expected 0 sessions after CloseAll, got %d", sm.SessionCount())
	}
}