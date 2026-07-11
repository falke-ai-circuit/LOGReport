package api

import (
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"strings"
	"testing"
	"time"

	"github.com/gorilla/websocket"
)

// ─── WebSocket Handler Tests ──────────────────────────────────────
// Covers: telnet/ws connection, bstool/ws connection.
// Uses gorilla/websocket dialer for testing.

// wsTestServer creates a test HTTP server with the API routes and returns
// the server and a WebSocket URL base.
func wsTestServer(t *testing.T) (*httptest.Server, *Server, func()) {
	t.Helper()
	srv, _, cleanup := setupTest(t)

	mux := http.NewServeMux()
	srv.registerRoutes(mux)

	// Wrap with content type middleware (same as NewTestMux)
	handler := contentTypeMiddleware(mux)

	ts := httptest.NewServer(handler)

	return ts, srv, func() {
		ts.Close()
		cleanup()
	}
}

// wsDial dials a WebSocket connection to the test server.
func wsDial(t *testing.T, ts *httptest.Server, path string) *websocket.Conn {
	t.Helper()
	url := "ws" + strings.TrimPrefix(ts.URL, "http") + path
	conn, _, err := websocket.DefaultDialer.Dial(url, nil)
	if err != nil {
		t.Fatalf("ws dial %s: %v", url, err)
	}
	return conn
}

func TestTelnetWebSocketHandler(t *testing.T) {
	ts, _, cleanup := wsTestServer(t)
	defer cleanup()

	t.Run("ws connect and send invalid JSON", func(t *testing.T) {
		conn := wsDial(t, ts, "/api/v1/telnet/ws")
		defer conn.Close()

		conn.SetReadDeadline(time.Now().Add(5 * time.Second))

		// Send invalid JSON
		conn.WriteMessage(websocket.TextMessage, []byte("not json"))

		// Should receive an error response
		_, msg, err := conn.ReadMessage()
		if err != nil {
			t.Fatalf("read message: %v", err)
		}
		var resp telnetWSResponse
		if err := json.Unmarshal(msg, &resp); err != nil {
			t.Fatalf("unmarshal response: %v (msg: %s)", err, string(msg))
		}
		if resp.Type != "error" {
			t.Errorf("expected type 'error', got %q", resp.Type)
		}
		if resp.Message != "invalid JSON message" {
			t.Errorf("expected 'invalid JSON message', got %q", resp.Message)
		}
	})

	t.Run("ws connect with missing host returns error", func(t *testing.T) {
		conn := wsDial(t, ts, "/api/v1/telnet/ws")
		defer conn.Close()

		conn.SetReadDeadline(time.Now().Add(5 * time.Second))

		// Send connect action without host
		msg, _ := json.Marshal(telnetWSMessage{Action: "connect"})
		conn.WriteMessage(websocket.TextMessage, msg)

		_, respBytes, err := conn.ReadMessage()
		if err != nil {
			t.Fatalf("read: %v", err)
		}
		var resp telnetWSResponse
		json.Unmarshal(respBytes, &resp)
		if resp.Type != "error" {
			t.Errorf("expected type 'error', got %q", resp.Type)
		}
		if !strings.Contains(resp.Message, "host is required") {
			t.Errorf("expected 'host is required', got %q", resp.Message)
		}
	})

	t.Run("ws command without connect returns error", func(t *testing.T) {
		conn := wsDial(t, ts, "/api/v1/telnet/ws")
		defer conn.Close()

		conn.SetReadDeadline(time.Now().Add(5 * time.Second))

		msg, _ := json.Marshal(telnetWSMessage{Action: "command", Command: "show all"})
		conn.WriteMessage(websocket.TextMessage, msg)

		_, respBytes, err := conn.ReadMessage()
		if err != nil {
			t.Fatalf("read: %v", err)
		}
		var resp telnetWSResponse
		json.Unmarshal(respBytes, &resp)
		if resp.Type != "error" {
			t.Errorf("expected type 'error', got %q", resp.Type)
		}
		if !strings.Contains(resp.Message, "not connected") {
			t.Errorf("expected 'not connected', got %q", resp.Message)
		}
	})

	t.Run("ws unknown action returns error", func(t *testing.T) {
		conn := wsDial(t, ts, "/api/v1/telnet/ws")
		defer conn.Close()

		conn.SetReadDeadline(time.Now().Add(5 * time.Second))

		msg, _ := json.Marshal(telnetWSMessage{Action: "unknown_action"})
		conn.WriteMessage(websocket.TextMessage, msg)

		_, respBytes, err := conn.ReadMessage()
		if err != nil {
			t.Fatalf("read: %v", err)
		}
		var resp telnetWSResponse
		json.Unmarshal(respBytes, &resp)
		if resp.Type != "error" {
			t.Errorf("expected type 'error', got %q", resp.Type)
		}
		if !strings.Contains(resp.Message, "unknown action") {
			t.Errorf("expected 'unknown action', got %q", resp.Message)
		}
	})

	t.Run("ws disconnect returns status", func(t *testing.T) {
		conn := wsDial(t, ts, "/api/v1/telnet/ws")
		defer conn.Close()

		conn.SetReadDeadline(time.Now().Add(5 * time.Second))

		msg, _ := json.Marshal(telnetWSMessage{Action: "disconnect"})
		conn.WriteMessage(websocket.TextMessage, msg)

		_, respBytes, err := conn.ReadMessage()
		if err != nil {
			t.Fatalf("read: %v", err)
		}
		var resp telnetWSResponse
		json.Unmarshal(respBytes, &resp)
		if resp.Type != "status" {
			t.Errorf("expected type 'status', got %q", resp.Type)
		}
		if resp.Connected != false {
			t.Errorf("expected connected false, got %v", resp.Connected)
		}
	})
}

func TestBsToolWebSocketHandler(t *testing.T) {
	ts, _, cleanup := wsTestServer(t)
	defer cleanup()

	t.Run("ws bstool invalid JSON returns error", func(t *testing.T) {
		conn := wsDial(t, ts, "/api/v1/bstool/ws")
		defer conn.Close()

		conn.SetReadDeadline(time.Now().Add(5 * time.Second))

		conn.WriteMessage(websocket.TextMessage, []byte("not json"))

		_, msg, err := conn.ReadMessage()
		if err != nil {
			t.Fatalf("read: %v", err)
		}
		var resp bstoolWSResponse
		if err := json.Unmarshal(msg, &resp); err != nil {
			t.Fatalf("unmarshal: %v (msg: %s)", err, string(msg))
		}
		if resp.Type != "error" {
			t.Errorf("expected type 'error', got %q", resp.Type)
		}
		if resp.Message != "invalid JSON message" {
			t.Errorf("expected 'invalid JSON message', got %q", resp.Message)
		}
	})

	t.Run("ws bstool execute without server_name returns error", func(t *testing.T) {
		conn := wsDial(t, ts, "/api/v1/bstool/ws")
		defer conn.Close()

		conn.SetReadDeadline(time.Now().Add(5 * time.Second))

		msg, _ := json.Marshal(bstoolWSMessage{Action: "execute"})
		conn.WriteMessage(websocket.TextMessage, msg)

		_, respBytes, err := conn.ReadMessage()
		if err != nil {
			t.Fatalf("read: %v", err)
		}
		var resp bstoolWSResponse
		json.Unmarshal(respBytes, &resp)
		if resp.Type != "error" {
			t.Errorf("expected type 'error', got %q", resp.Type)
		}
		if !strings.Contains(resp.Message, "server_name is required") {
			t.Errorf("expected 'server_name is required', got %q", resp.Message)
		}
	})

	t.Run("ws bstool unknown action returns error", func(t *testing.T) {
		conn := wsDial(t, ts, "/api/v1/bstool/ws")
		defer conn.Close()

		conn.SetReadDeadline(time.Now().Add(5 * time.Second))

		msg, _ := json.Marshal(bstoolWSMessage{Action: "unknown"})
		conn.WriteMessage(websocket.TextMessage, msg)

		_, respBytes, err := conn.ReadMessage()
		if err != nil {
			t.Fatalf("read: %v", err)
		}
		var resp bstoolWSResponse
		json.Unmarshal(respBytes, &resp)
		if resp.Type != "error" {
			t.Errorf("expected type 'error', got %q", resp.Type)
		}
		if !strings.Contains(resp.Message, "unknown action") {
			t.Errorf("expected 'unknown action', got %q", resp.Message)
		}
	})

	t.Run("ws bstool execute with server_name returns response", func(t *testing.T) {
		conn := wsDial(t, ts, "/api/v1/bstool/ws")
		defer conn.Close()

		// Set a longer deadline since bstool may try to connect to TCP
		conn.SetReadDeadline(time.Now().Add(15 * time.Second))

		msg, _ := json.Marshal(bstoolWSMessage{Action: "execute", ServerName: "AP01m"})
		conn.WriteMessage(websocket.TextMessage, msg)

		_, respBytes, err := conn.ReadMessage()
		if err != nil {
			t.Fatalf("read: %v", err)
		}
		var resp bstoolWSResponse
		json.Unmarshal(respBytes, &resp)
		// On Linux, bstool returns an error (UNSUPPORTED_PLATFORM or INTERNAL_ERROR)
		// The key is that we get a response (error or done), not a hang
		if resp.Type == "" {
			t.Error("expected non-empty type in response")
		}
	})
}