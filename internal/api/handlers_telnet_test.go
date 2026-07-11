package api

import (
	"net"
	"net/http"
	"strings"
	"sync"
	"testing"
	"time"
)

// ─── Telnet Handler Tests ─────────────────────────────────────────
// Covers: connect (200), connect missing fields (400), command, output,
// disconnect, list sessions, disconnect nonexistent, execute single.
// Uses mock TCP server pattern from existing tests.

// mockTelnetServer starts a TCP listener that mimics a Valmet DNA telnet node.
// Returns address and stop function.
func mockTelnetServer(t *testing.T) (addr string, stop func()) {
	t.Helper()

	listener, err := net.Listen("tcp", "127.0.0.1:0")
	if err != nil {
		t.Fatalf("mock telnet listen: %v", err)
	}
	addr = listener.Addr().String()

	var wg sync.WaitGroup
	done := make(chan struct{})

	wg.Add(1)
	go func() {
		defer wg.Done()
		for {
			conn, err := listener.Accept()
			if err != nil {
				select {
				case <-done:
					return
				default:
					return
				}
			}
			go func(c net.Conn) {
				defer c.Close()
				c.SetDeadline(time.Now().Add(10 * time.Second))
				c.Write([]byte("Welcome to Valmet DNA\r\n"))
				buf := make([]byte, 4096)
				for {
					n, err := c.Read(buf)
					if err != nil {
						return
					}
					cmd := strings.TrimSpace(string(buf[:n]))
					if cmd == "quit" {
						return
					}
					// Echo a prompt for any command
					c.Write([]byte("162a% "))
				}
			}(conn)
		}
	}()

	stop = func() {
		close(done)
		listener.Close()
		wg.Wait()
	}
	return addr, stop
}

func TestTelnetConnectHandler(t *testing.T) {
	srv, _, cleanup := setupTest(t)
	defer cleanup()

	mux := srv.NewTestMux()

	t.Run("connect to mock server returns 200", func(t *testing.T) {
		addr, stop := mockTelnetServer(t)
		defer stop()

		host, portStr, _ := net.SplitHostPort(addr)
		var port int
		for _, c := range portStr {
			port = port*10 + int(c-'0')
		}

		body := jsonBody(map[string]interface{}{
			"host":    host,
			"port":    port,
			"timeout": 5,
		})
		rec := doRequest(mux, "POST", "/api/v1/telnet/connect", body, jsonHeader)
		if rec.Code != http.StatusOK {
			t.Errorf("expected 200, got %d: %s", rec.Code, rec.Body.String())
		}
		result := parseJSONResponse(rec)
		if result["connected"] != true {
			t.Errorf("expected connected true, got %v", result["connected"])
		}
		if result["session_id"] == nil || result["session_id"] == "" {
			t.Error("expected non-empty session_id")
		}
	})

	t.Run("connect missing host returns 400", func(t *testing.T) {
		body := jsonBody(map[string]interface{}{
			"port": 23,
		})
		rec := doRequest(mux, "POST", "/api/v1/telnet/connect", body, jsonHeader)
		if rec.Code != http.StatusBadRequest {
			t.Errorf("expected 400, got %d", rec.Code)
		}
		result := parseJSONResponse(rec)
		if result["error"] != "validation_error" {
			t.Errorf("expected validation_error, got %v", result["error"])
		}
	})

	t.Run("connect invalid JSON returns 400", func(t *testing.T) {
		rec := doRequest(mux, "POST", "/api/v1/telnet/connect", strings.NewReader("{bad"), jsonHeader)
		if rec.Code != http.StatusBadRequest {
			t.Errorf("expected 400, got %d", rec.Code)
		}
	})

	t.Run("connect to unreachable host returns 502", func(t *testing.T) {
		body := jsonBody(map[string]interface{}{
			"host":    "192.168.255.255",
			"port":    9999,
			"timeout": 1,
		})
		rec := doRequest(mux, "POST", "/api/v1/telnet/connect", body, jsonHeader)
		if rec.Code != http.StatusBadGateway {
			t.Errorf("expected 502, got %d: %s", rec.Code, rec.Body.String())
		}
		result := parseJSONResponse(rec)
		if result["error"] != "connection_failed" {
			t.Errorf("expected connection_failed, got %v", result["error"])
		}
	})
}

func TestTelnetCommandAndOutputHandler(t *testing.T) {
	srv, _, cleanup := setupTest(t)
	defer cleanup()

	mux := srv.NewTestMux()

	// Connect to mock server first
	addr, stop := mockTelnetServer(t)
	defer stop()

	host, portStr, _ := net.SplitHostPort(addr)
	var port int
	for _, c := range portStr {
		port = port*10 + int(c-'0')
	}

	body := jsonBody(map[string]interface{}{
		"host":    host,
		"port":    port,
		"timeout": 5,
	})
	rec := doRequest(mux, "POST", "/api/v1/telnet/connect", body, jsonHeader)
	result := parseJSONResponse(rec)
	sessionID, ok := result["session_id"].(string)
	if !ok || sessionID == "" {
		t.Fatalf("failed to get session_id: %v", result)
	}

	t.Run("send command returns 200", func(t *testing.T) {
		body := jsonBody(map[string]interface{}{
			"command": "show all",
		})
		rec := doRequest(mux, "POST", "/api/v1/telnet/"+sessionID+"/command", body, jsonHeader)
		if rec.Code != http.StatusOK {
			t.Errorf("expected 200, got %d: %s", rec.Code, rec.Body.String())
		}
		result := parseJSONResponse(rec)
		if result["sent"] != true {
			t.Errorf("expected sent true, got %v", result["sent"])
		}
		if result["command"] != "show all" {
			t.Errorf("expected command 'show all', got %v", result["command"])
		}
	})

	t.Run("send command to non-existent session returns 502", func(t *testing.T) {
		body := jsonBody(map[string]interface{}{
			"command": "show all",
		})
		rec := doRequest(mux, "POST", "/api/v1/telnet/nonexistent-session/command", body, jsonHeader)
		if rec.Code != http.StatusBadGateway {
			t.Errorf("expected 502, got %d: %s", rec.Code, rec.Body.String())
		}
	})

	t.Run("send command missing command field returns 400", func(t *testing.T) {
		body := jsonBody(map[string]interface{}{})
		rec := doRequest(mux, "POST", "/api/v1/telnet/"+sessionID+"/command", body, jsonHeader)
		if rec.Code != http.StatusBadRequest {
			t.Errorf("expected 400, got %d", rec.Code)
		}
	})

	t.Run("get output returns 200", func(t *testing.T) {
		rec := doRequest(mux, "GET", "/api/v1/telnet/"+sessionID+"/output", nil, nil)
		if rec.Code != http.StatusOK {
			t.Errorf("expected 200, got %d: %s", rec.Code, rec.Body.String())
		}
		result := parseJSONResponse(rec)
		if result["session_id"] != sessionID {
			t.Errorf("expected session_id %s, got %v", sessionID, result["session_id"])
		}
		// output field should exist
		if _, ok := result["output"]; !ok {
			t.Error("expected output field")
		}
	})

	t.Run("get output non-existent session returns 404", func(t *testing.T) {
		rec := doRequest(mux, "GET", "/api/v1/telnet/nonexistent-session/output", nil, nil)
		if rec.Code != http.StatusNotFound {
			t.Errorf("expected 404, got %d", rec.Code)
		}
	})
}

func TestTelnetDisconnectHandler(t *testing.T) {
	srv, _, cleanup := setupTest(t)
	defer cleanup()

	mux := srv.NewTestMux()

	t.Run("disconnect existing session returns 200", func(t *testing.T) {
		addr, stop := mockTelnetServer(t)
		defer stop()

		host, portStr, _ := net.SplitHostPort(addr)
		var port int
		for _, c := range portStr {
			port = port*10 + int(c-'0')
		}

		// Connect
		body := jsonBody(map[string]interface{}{
			"host":    host,
			"port":    port,
			"timeout": 5,
		})
		rec := doRequest(mux, "POST", "/api/v1/telnet/connect", body, jsonHeader)
		result := parseJSONResponse(rec)
		sessionID := result["session_id"].(string)

		// Disconnect
		rec2 := doRequest(mux, "DELETE", "/api/v1/telnet/"+sessionID, nil, jsonHeader)
		if rec2.Code != http.StatusOK {
			t.Errorf("expected 200, got %d: %s", rec2.Code, rec2.Body.String())
		}
		result2 := parseJSONResponse(rec2)
		if result2["disconnected"] != true {
			t.Errorf("expected disconnected true, got %v", result2["disconnected"])
		}
	})

	t.Run("disconnect non-existent session returns 404", func(t *testing.T) {
		rec := doRequest(mux, "DELETE", "/api/v1/telnet/nonexistent-session", nil, jsonHeader)
		if rec.Code != http.StatusNotFound {
			t.Errorf("expected 404, got %d", rec.Code)
		}
		result := parseJSONResponse(rec)
		if result["error"] != "not_found" {
			t.Errorf("expected not_found, got %v", result["error"])
		}
	})
}

func TestTelnetListSessionsHandler(t *testing.T) {
	srv, _, cleanup := setupTest(t)
	defer cleanup()

	mux := srv.NewTestMux()

	t.Run("list sessions empty returns 200", func(t *testing.T) {
		rec := doRequest(mux, "GET", "/api/v1/telnet/sessions", nil, nil)
		if rec.Code != http.StatusOK {
			t.Errorf("expected 200, got %d", rec.Code)
		}
		result := parseJSONResponse(rec)
		sessions, ok := result["sessions"].([]interface{})
		if !ok {
			t.Errorf("expected sessions array, got %T", result["sessions"])
		}
		if len(sessions) != 0 {
			t.Errorf("expected 0 sessions, got %d", len(sessions))
		}
		if result["count"].(float64) != 0 {
			t.Errorf("expected count 0, got %v", result["count"])
		}
	})

	t.Run("list sessions after connect returns 200 with 1 session", func(t *testing.T) {
		addr, stop := mockTelnetServer(t)
		defer stop()

		host, portStr, _ := net.SplitHostPort(addr)
		var port int
		for _, c := range portStr {
			port = port*10 + int(c-'0')
		}

		body := jsonBody(map[string]interface{}{
			"host":    host,
			"port":    port,
			"timeout": 5,
		})
		doRequest(mux, "POST", "/api/v1/telnet/connect", body, jsonHeader)

		rec := doRequest(mux, "GET", "/api/v1/telnet/sessions", nil, nil)
		if rec.Code != http.StatusOK {
			t.Errorf("expected 200, got %d", rec.Code)
		}
		result := parseJSONResponse(rec)
		sessions, ok := result["sessions"].([]interface{})
		if !ok {
			t.Errorf("expected sessions array, got %T", result["sessions"])
		}
		if len(sessions) != 1 {
			t.Errorf("expected 1 session, got %d", len(sessions))
		}
	})
}

func TestTelnetExecuteSingleHandler(t *testing.T) {
	srv, _, cleanup := setupTest(t)
	defer cleanup()

	mux := srv.NewTestMux()

	t.Run("execute single command to mock server returns 200", func(t *testing.T) {
		addr, stop := mockTelnetServer(t)
		defer stop()

		host, portStr, _ := net.SplitHostPort(addr)
		var port int
		for _, c := range portStr {
			port = port*10 + int(c-'0')
		}

		body := jsonBody(map[string]interface{}{
			"command": "show all",
			"host":    host,
			"port":    port,
		})
		rec := doRequest(mux, "POST", "/api/v1/telnet/execute", body, jsonHeader)
		if rec.Code != http.StatusOK {
			t.Errorf("expected 200, got %d: %s", rec.Code, rec.Body.String())
		}
		result := parseJSONResponse(rec)
		if result["sent"] != true {
			t.Errorf("expected sent true, got %v", result["sent"])
		}
	})

	t.Run("execute single command missing command returns 400", func(t *testing.T) {
		body := jsonBody(map[string]interface{}{})
		rec := doRequest(mux, "POST", "/api/v1/telnet/execute", body, jsonHeader)
		if rec.Code != http.StatusBadRequest {
			t.Errorf("expected 400, got %d", rec.Code)
		}
	})

	t.Run("execute single command invalid JSON returns 400", func(t *testing.T) {
		rec := doRequest(mux, "POST", "/api/v1/telnet/execute", strings.NewReader("{bad"), jsonHeader)
		if rec.Code != http.StatusBadRequest {
			t.Errorf("expected 400, got %d", rec.Code)
		}
	})

	t.Run("execute single command to unreachable returns 502", func(t *testing.T) {
		body := jsonBody(map[string]interface{}{
			"command": "show all",
			"host":    "192.168.255.255",
			"port":    9999,
		})
		rec := doRequest(mux, "POST", "/api/v1/telnet/execute", body, jsonHeader)
		if rec.Code != http.StatusBadGateway {
			t.Errorf("expected 502, got %d: %s", rec.Code, rec.Body.String())
		}
	})
}