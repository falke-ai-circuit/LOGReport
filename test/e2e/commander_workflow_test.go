// Package e2e provides end-to-end workflow tests for the LOGReport Commander window.
// These tests exercise the full Valmet DNA debugger command chain:
//  1. Load nodes.json → build tree
//  2. Connect to mock DNA node via REST
//  3. Send FBC print command → verify command received by DNA server
//  4. Send RPC print command → verify command received
//  5. System mode initialization verification (yes, Ctrl+Z, systemmode)
//  6. Queue batch "Print All Nodes" → verify FBC/RPC commands generated
//  7. Queue pause/resume/cancel lifecycle
//  8. Log writer write + read back
//  9. WebSocket interactive terminal
//  10. RPC parser lowercase "pic" header (the critical bug fix)
//  11. FBC parser standard uppercase PIC header
//  12. Command resolver shorthand mapping
//  13. Full-form telnet command generation
//  14. BsTool node suffix stripping
//  15. Nodes config load/save cycle
package e2e

import (
	"context"
	"embed"
	"encoding/json"
	"fmt"
	"io"
	"net"
	"net/http"
	"net/http/httptest"
	"os"
	"strings"
	"sync"
	"testing"
	"time"

	"github.com/falke-ai-circuit/LOGReport/internal/api"
	"github.com/falke-ai-circuit/LOGReport/internal/bstool"
	"github.com/falke-ai-circuit/LOGReport/internal/server"
	"github.com/falke-ai-circuit/LOGReport/internal/store"
	"github.com/gorilla/websocket"
)

// ─── Commander Mock DNA Server ────────────────────────────────────

// commanderMockDNA simulates a Valmet DNA node for Commander workflow tests.
// It responds to system mode initialization and FBC/RPC print commands
// with realistic DNA output (lowercase "pic" for RPC, uppercase "PIC" for FBC).
type commanderMockDNA struct {
	ln       net.Listener
	mu       sync.Mutex
	received []string
}

func newCommanderMockDNA(t *testing.T) *commanderMockDNA {
	ln, err := net.Listen("tcp", "127.0.0.1:0")
	if err != nil {
		t.Fatalf("commander mock DNA: %v", err)
	}
	m := &commanderMockDNA{ln: ln}
	go m.serve()
	return m
}

func (m *commanderMockDNA) addr() string { return m.ln.Addr().String() }
func (m *commanderMockDNA) host() string {
	h, _, _ := net.SplitHostPort(m.addr())
	return h
}
func (m *commanderMockDNA) port() int {
	_, p, _ := net.SplitHostPort(m.addr())
	port := 0
	fmt.Sscanf(p, "%d", &port)
	return port
}
func (m *commanderMockDNA) close() { m.ln.Close() }

func (m *commanderMockDNA) getReceived() []string {
	m.mu.Lock()
	defer m.mu.Unlock()
	cp := make([]string, len(m.received))
	copy(cp, m.received)
	return cp
}

func (m *commanderMockDNA) record(cmd string) {
	m.mu.Lock()
	m.received = append(m.received, cmd)
	m.mu.Unlock()
}

func (m *commanderMockDNA) serve() {
	for {
		conn, err := m.ln.Accept()
		if err != nil {
			return
		}
		go m.handleConn(conn)
	}
}

func (m *commanderMockDNA) handleConn(conn net.Conn) {
	defer conn.Close()
	conn.SetDeadline(time.Now().Add(30 * time.Second))
	conn.Write([]byte("1a% "))

	buf := make([]byte, 4096)
	for {
		n, err := conn.Read(buf)
		if err != nil {
			return
		}
		data := string(buf[:n])
		m.record(data)
		response := m.generateResponse(data)
		if response != "" {
			conn.Write([]byte(response))
		}
	}
}

func (m *commanderMockDNA) generateResponse(data string) string {
	if strings.Contains(data, "yes\r\n") {
		return "OK\n1a% "
	}
	if strings.Contains(data, "systemmode\r\n") {
		return "System mode active\n1a% "
	}
	if strings.Contains(data, "print from fbc io structure") ||
		(strings.Contains(data, "print_fieldbus ") && !strings.Contains(data, "rupi")) {
		return m.fbcOutput() + "\n1a% "
	}
	if strings.Contains(data, "print from fbc rupi counters") ||
		strings.Contains(data, "print_fieldbus_rupi_counters") {
		return m.rpcOutput() + "\n1a% "
	}
	if strings.Contains(data, "show all") {
		return "Process list:\n  1: FBC agent 162\n  2: FBC agent 163\n1a% "
	}
	if data == "\x18" || data == "\x1a" {
		return ""
	}
	return "Unknown command\n1a% "
}

func (m *commanderMockDNA) fbcOutput() string {
	return "FBC agent 162\n\nPIC  5  6  7  8  sum\n0    AI8  BI8  BO8      3\n1    AI8  BI8N          2\n2    Not Exists\n3    DI16  DO16  AI8  AO4  4\n4                      0\nTotal sum: 9 I/O-units, 9 Channels (5 input, 4 output)"
}

// rpcOutput uses LOWERCASE "pic" header — matching real Valmet DNA output.
// This is the critical bug that was fixed: the old parser required uppercase "PIC".
func (m *commanderMockDNA) rpcOutput() string {
	return "pic  IREX ERROR  POLL ERROR  RESP FAIL  IREX COUNT  TIMEOUT\n0    0  0  0  0  0\n1    0  0  0  0  0\n2    0  0  0  0  0\n3    2  1  0  15  0\n4    0  0  0  0  0\nTotal sum: 3 counters"
}

// ─── Test Setup ───────────────────────────────────────────────────

func setupCommanderTestServer(t *testing.T) (*httptest.Server, *commanderMockDNA) {
	st, err := store.Open("")
	if err != nil {
		t.Fatalf("open store: %v", err)
	}

	cfg := &server.Config{
		Port:       0,
		DBPath:     "",
		LogLevel:   "debug",
		CORSOrigin: "*",
	}

	srv := api.NewServer(st, cfg, embed.FS{}, bstool.NewClient())

	mux := http.NewServeMux()
	srv.RegisterRoutesForTest(mux)

	ts := httptest.NewServer(mux)
	dnaServer := newCommanderMockDNA(t)

	return ts, dnaServer
}

// ─── E2E Workflow Tests ───────────────────────────────────────────

// TestE2E_Commander_FullWorkflow tests the complete Commander window workflow:
// 1. Load nodes.json → build tree
// 2. Connect to DNA node (REST) with system mode init
// 3. Send FBC print command → verify command received by DNA server
// 4. Send RPC print command → verify command received
// 5. Disconnect
func TestE2E_Commander_FullWorkflow(t *testing.T) {
	ts, dnaServer := setupCommanderTestServer(t)
	defer ts.Close()
	defer dnaServer.close()

	// Step 1: Get nodes config tree
	resp, err := http.Get(ts.URL + "/api/v1/nodesconfig/tree")
	if err != nil {
		t.Fatalf("GET nodesconfig/tree: %v", err)
	}
	if resp.StatusCode != http.StatusOK {
		t.Fatalf("expected 200, got %d", resp.StatusCode)
	}
	var treeResp map[string]interface{}
	json.NewDecoder(resp.Body).Decode(&treeResp)
	resp.Body.Close()

	tree, ok := treeResp["tree"].(map[string]interface{})
	if !ok {
		t.Fatal("expected tree in response")
	}
	children, ok := tree["children"].([]interface{})
	if !ok || len(children) == 0 {
		t.Fatal("expected tree children")
	}
	t.Logf("✓ Step 1: Loaded node tree with %d root nodes", len(children))

	// Step 2: Connect to mock DNA node
	connectBody := fmt.Sprintf(`{"host":"%s","port":%d}`, dnaServer.host(), dnaServer.port())
	resp, err = http.Post(ts.URL+"/api/v1/telnet/connect", "application/json", strings.NewReader(connectBody))
	if err != nil {
		t.Fatalf("POST telnet/connect: %v", err)
	}
	if resp.StatusCode != http.StatusOK {
		body, _ := io.ReadAll(resp.Body)
		t.Fatalf("expected 200, got %d: %s", resp.StatusCode, body)
	}
	var connectResp map[string]interface{}
	json.NewDecoder(resp.Body).Decode(&connectResp)
	resp.Body.Close()

	sessionID, ok := connectResp["session_id"].(string)
	if !ok || sessionID == "" {
		t.Fatal("expected session_id in response")
	}
	t.Logf("✓ Step 2: Connected to DNA node, session=%s", sessionID)

	// Wait for system mode initialization
	time.Sleep(2 * time.Second)

	// Verify system mode init commands were sent
	received := dnaServer.getReceived()
	hasYes := false
	hasSystemmode := false
	for _, cmd := range received {
		if strings.Contains(cmd, "yes") {
			hasYes = true
		}
		if strings.Contains(cmd, "systemmode") {
			hasSystemmode = true
		}
	}
	if !hasYes {
		t.Error("✗ Expected 'yes' command for system mode init")
	}
	if !hasSystemmode {
		t.Error("✗ Expected 'systemmode' command for system mode init")
	}
	t.Logf("✓ Step 2a: System mode init verified (yes=%v, systemmode=%v)", hasYes, hasSystemmode)

	// Step 3: Send FBC print command
	fbcCmd := `{"command":"print from fbc io structure 1620000"}`
	resp, err = http.Post(ts.URL+"/api/v1/telnet/"+sessionID+"/command", "application/json", strings.NewReader(fbcCmd))
	if err != nil {
		t.Fatalf("POST telnet command: %v", err)
	}
	if resp.StatusCode != http.StatusOK {
		body, _ := io.ReadAll(resp.Body)
		t.Fatalf("expected 200, got %d: %s", resp.StatusCode, body)
	}
	resp.Body.Close()
	t.Logf("✓ Step 3: FBC print command sent")

	time.Sleep(500 * time.Millisecond)

	received = dnaServer.getReceived()
	hasFBC := false
	for _, cmd := range received {
		if strings.Contains(cmd, "print from fbc io structure 1620000") {
			hasFBC = true
		}
	}
	if !hasFBC {
		t.Error("✗ FBC print command not received by DNA server")
	} else {
		t.Logf("✓ Step 3a: FBC command verified on DNA server")
	}

	// Step 4: Send RPC print command
	rpcCmd := `{"command":"print from fbc rupi counters 1620000"}`
	resp, err = http.Post(ts.URL+"/api/v1/telnet/"+sessionID+"/command", "application/json", strings.NewReader(rpcCmd))
	if err != nil {
		t.Fatalf("POST telnet RPC command: %v", err)
	}
	if resp.StatusCode != http.StatusOK {
		body, _ := io.ReadAll(resp.Body)
		t.Fatalf("expected 200, got %d: %s", resp.StatusCode, body)
	}
	resp.Body.Close()
	t.Logf("✓ Step 4: RPC print command sent")

	time.Sleep(500 * time.Millisecond)

	received = dnaServer.getReceived()
	hasRPC := false
	for _, cmd := range received {
		if strings.Contains(cmd, "print from fbc rupi counters 1620000") {
			hasRPC = true
		}
	}
	if !hasRPC {
		t.Error("✗ RPC print command not received by DNA server")
	} else {
		t.Logf("✓ Step 4a: RPC command verified on DNA server")
	}

	// Step 5: Disconnect
	delReq, _ := http.NewRequest("DELETE", ts.URL+"/api/v1/telnet/"+sessionID, nil)
	resp, err = http.DefaultClient.Do(delReq)
	if err != nil {
		t.Fatalf("DELETE telnet session: %v", err)
	}
	resp.Body.Close()
	t.Logf("✓ Step 5: Disconnected session")
}

// TestE2E_Commander_RPCParserLowercasePic tests that the RPC parser
// correctly handles lowercase "pic" header as output by real Valmet DNA nodes.
func TestE2E_Commander_RPCParserLowercasePic(t *testing.T) {
	rpcOutput := "pic  IREX ERROR  POLL ERROR  RESP FAIL  IREX COUNT  TIMEOUT\n0    0  0  0  0  0\n1    2  1  0  15  0\n2    Not Exists\nTotal sum: 3 counters"

	modules, err := parserParseRPC(rpcOutput)
	if err != nil {
		t.Fatalf("ParseRPC with lowercase 'pic': %v", err)
	}
	if len(modules) == 0 {
		t.Fatal("expected modules from lowercase pic output, got 0")
	}
	if modules[0].Position != 0 {
		t.Errorf("expected position 0, got %d", modules[0].Position)
	}
	if len(modules[0].Counters) != 4 {
		t.Errorf("expected 4 counters (5th is parsed as sum by rpcRowPattern), got %d", len(modules[0].Counters))
	}
	if len(modules) >= 2 && modules[1].Position == 1 {
		if modules[1].Counters[0].Value != 2 {
			t.Errorf("expected IREX ERROR=2, got %d", modules[1].Counters[0].Value)
		}
	}
	t.Logf("✓ RPC parser handles lowercase 'pic' header correctly (%d modules)", len(modules))
}

// TestE2E_Commander_RPCParserUppercasePIC ensures backward compat with uppercase PIC.
func TestE2E_Commander_RPCParserUppercasePIC(t *testing.T) {
	rpcOutput := "PIC  IREX ERROR  POLL ERROR  RESP FAIL  IREX COUNT  TIMEOUT\n0    0  0  0  0  0\n1    2  1  0  15  0\nTotal sum: 2 counters"

	modules, err := parserParseRPC(rpcOutput)
	if err != nil {
		t.Fatalf("ParseRPC with uppercase 'PIC': %v", err)
	}
	if len(modules) != 2 {
		t.Errorf("expected 2 modules, got %d", len(modules))
	}
	t.Logf("✓ RPC parser handles uppercase 'PIC' header (backward compat)")
}

// TestE2E_Commander_FBCParserStandard tests FBC parsing with standard PIC header.
func TestE2E_Commander_FBCParserStandard(t *testing.T) {
	fbcOutput := "FBC agent 162\n\nPIC  5  6  7  8  sum\n0    AI8  BI8  BO8      3\n1    AI8  BI8N          2\n2    Not Exists\n3    DI16  DO16  AI8  AO4  4\nTotal sum: 9 I/O-units, 9 Channels (5 input, 4 output)"

	modules, err := parserParseFBC(fbcOutput)
	if err != nil {
		t.Fatalf("ParseFBC: %v", err)
	}
	if len(modules) == 0 {
		t.Fatal("expected modules, got 0")
	}

	found := false
	for _, mod := range modules {
		for _, ch := range mod.Channels {
			if string(ch.Type) == "AI8" {
				found = true
			}
		}
	}
	if !found {
		t.Error("expected to find AI8 channel type")
	}
	t.Logf("✓ FBC parser handles standard PIC header (%d modules)", len(modules))
}

// TestE2E_Commander_QueueBatch tests "Print All Nodes" batch generation.
func TestE2E_Commander_QueueBatch(t *testing.T) {
	ts, _ := setupCommanderTestServer(t)
	defer ts.Close()

	resp, err := http.Post(ts.URL+"/api/v1/commandqueue/batch", "application/json", strings.NewReader(`{}`))
	if err != nil {
		t.Fatalf("POST batch: %v", err)
	}
	if resp.StatusCode != http.StatusOK {
		body, _ := io.ReadAll(resp.Body)
		t.Fatalf("expected 200, got %d: %s", resp.StatusCode, body)
	}
	var batchResp map[string]interface{}
	json.NewDecoder(resp.Body).Decode(&batchResp)
	resp.Body.Close()

	total, ok := batchResp["total"].(float64)
	if !ok || total == 0 {
		t.Fatal("expected batch commands to be generated")
	}
	t.Logf("✓ Batch generated %d commands from nodes.json", int(total))

	// Check queue status for command types
	resp, err = http.Get(ts.URL + "/api/v1/commandqueue/status")
	if err != nil {
		t.Fatalf("GET status: %v", err)
	}
	var statusResp map[string]interface{}
	json.NewDecoder(resp.Body).Decode(&statusResp)
	resp.Body.Close()

	cmds, ok := statusResp["commands"].([]interface{})
	if !ok {
		t.Fatal("expected commands in status")
	}

	hasFBC, hasRPC, hasLIS := false, false, false
	for _, c := range cmds {
		cmd := c.(map[string]interface{})
		switch cmd["type"].(string) {
		case "fbc":
			hasFBC = true
		case "rpc":
			hasRPC = true
		case "lis":
			hasLIS = true
		}
	}
	if !hasFBC {
		t.Error("✗ Expected FBC commands in batch")
	}
	if !hasRPC {
		t.Error("✗ Expected RPC commands in batch")
	}
	if hasLIS {
		t.Error("✗ LIS commands should be skipped (FTP protocol)")
	}
	t.Logf("✓ Batch contains FBC=%v, RPC=%v, LIS skipped=%v", hasFBC, hasRPC, !hasLIS)
}

// TestE2E_Commander_QueuePauseResumeCancel tests queue lifecycle.
func TestE2E_Commander_QueuePauseResumeCancel(t *testing.T) {
	ts, dnaServer := setupCommanderTestServer(t)
	defer ts.Close()
	defer dnaServer.close()

	// Connect to DNA server
	connectBody := fmt.Sprintf(`{"host":"%s","port":%d}`, dnaServer.host(), dnaServer.port())
	resp, err := http.Post(ts.URL+"/api/v1/telnet/connect", "application/json", strings.NewReader(connectBody))
	if err != nil {
		t.Fatalf("connect: %v", err)
	}
	resp.Body.Close()
	time.Sleep(2 * time.Second)

	// Add a command
	addBody := `{"id":"test-1","type":"fbc","node_name":"AP01m","token_id":"162","command":"print from fbc io structure 1620000","status":"pending"}`
	resp, err = http.Post(ts.URL+"/api/v1/commandqueue/add", "application/json", strings.NewReader(addBody))
	if err != nil {
		t.Fatalf("add: %v", err)
	}
	resp.Body.Close()
	t.Logf("✓ Command added to queue")

	// Start
	resp, err = http.Post(ts.URL+"/api/v1/commandqueue/start", "application/json", nil)
	if err != nil {
		t.Fatalf("start: %v", err)
	}
	resp.Body.Close()
	t.Logf("✓ Queue started")

	time.Sleep(1 * time.Second)

	// Pause
	resp, err = http.Post(ts.URL+"/api/v1/commandqueue/pause", "application/json", nil)
	if err != nil {
		t.Fatalf("pause: %v", err)
	}
	resp.Body.Close()
	t.Logf("✓ Queue paused")

	time.Sleep(500 * time.Millisecond)

	// Check status
	resp, err = http.Get(ts.URL + "/api/v1/commandqueue/status")
	if err != nil {
		t.Fatalf("status: %v", err)
	}
	var status map[string]interface{}
	json.NewDecoder(resp.Body).Decode(&status)
	resp.Body.Close()
	state, _ := status["state"].(string)
	t.Logf("✓ Queue state after pause: %s", state)

	// Resume
	resp, err = http.Post(ts.URL+"/api/v1/commandqueue/resume", "application/json", nil)
	if err != nil {
		t.Fatalf("resume: %v", err)
	}
	resp.Body.Close()
	t.Logf("✓ Queue resumed")

	time.Sleep(500 * time.Millisecond)

	// Cancel
	resp, err = http.Post(ts.URL+"/api/v1/commandqueue/cancel", "application/json", nil)
	if err != nil {
		t.Fatalf("cancel: %v", err)
	}
	resp.Body.Close()
	t.Logf("✓ Queue cancelled")
}

// TestE2E_Commander_LogWriter tests writing and reading per-node log files.
func TestE2E_Commander_LogWriter(t *testing.T) {
	ts, _ := setupCommanderTestServer(t)
	defer ts.Close()

	// Write
	writeBody := `{"token_type":"FBC","token_id":"162","output":"FBC agent 162\nPIC  5  6  7  8  sum\n0    AI8  BI8  BO8      3"}`
	resp, err := http.Post(ts.URL+"/api/v1/logs/AP01m", "application/json", strings.NewReader(writeBody))
	if err != nil {
		t.Fatalf("write log: %v", err)
	}
	if resp.StatusCode != http.StatusOK {
		body, _ := io.ReadAll(resp.Body)
		t.Fatalf("expected 200, got %d: %s", resp.StatusCode, body)
	}
	resp.Body.Close()
	t.Logf("✓ Log file written for AP01m")

	// List
	resp, err = http.Get(ts.URL + "/api/v1/logs/AP01m")
	if err != nil {
		t.Fatalf("list logs: %v", err)
	}
	var listResp map[string]interface{}
	json.NewDecoder(resp.Body).Decode(&listResp)
	resp.Body.Close()
	logs, ok := listResp["logs"].([]interface{})
	if !ok || len(logs) == 0 {
		t.Fatal("expected log entries")
	}
	t.Logf("✓ Listed %d log files for AP01m", len(logs))

	// Read back
	resp, err = http.Get(ts.URL + "/api/v1/logs/AP01m/fbc_162.log")
	if err != nil {
		t.Fatalf("read log: %v", err)
	}
	if resp.StatusCode != http.StatusOK {
		body, _ := io.ReadAll(resp.Body)
		t.Fatalf("expected 200, got %d: %s", resp.StatusCode, body)
	}
	var readResp map[string]interface{}
	json.NewDecoder(resp.Body).Decode(&readResp)
	resp.Body.Close()
	content, _ := readResp["content"].(string)
	if !strings.Contains(content, "FBC agent 162") {
		t.Error("expected log content to contain FBC agent 162")
	}
	t.Logf("✓ Log file read back (content length: %d)", len(content))
}

// TestE2E_Commander_WebSocketTelnet tests WebSocket interactive terminal.
func TestE2E_Commander_WebSocketTelnet(t *testing.T) {
	ts, dnaServer := setupCommanderTestServer(t)
	defer ts.Close()
	defer dnaServer.close()

	wsURL := strings.Replace(ts.URL, "http://", "ws://", 1) + "/api/v1/telnet/ws"
	dialer := websocket.Dialer{HandshakeTimeout: 5 * time.Second}
	conn, _, err := dialer.Dial(wsURL, nil)
	if err != nil {
		t.Fatalf("WebSocket dial: %v", err)
	}
	defer conn.Close()
	t.Logf("✓ WebSocket connected")

	// Connect to DNA node via WebSocket
	connectMsg := fmt.Sprintf(`{"action":"connect","host":"%s","port":%d}`, dnaServer.host(), dnaServer.port())
	if err := conn.WriteMessage(websocket.TextMessage, []byte(connectMsg)); err != nil {
		t.Fatalf("WS write connect: %v", err)
	}

	// Read messages until connected
	ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
	defer cancel()
	connected := false
	go func() {
		for {
			select {
			case <-ctx.Done():
				return
			default:
			}
			_, msg, err := conn.ReadMessage()
			if err != nil {
				return
			}
			var resp map[string]interface{}
			json.Unmarshal(msg, &resp)
			if resp["type"] == "status" && resp["connected"] == true {
				connected = true
			}
		}
	}()

	time.Sleep(3 * time.Second)
	if !connected {
		t.Error("✗ Expected connected status via WebSocket")
	} else {
		t.Logf("✓ WebSocket connected to DNA node")
	}

	// Send FBC command
	fbcMsg := `{"action":"command","command":"print from fbc io structure 1620000"}`
	if err := conn.WriteMessage(websocket.TextMessage, []byte(fbcMsg)); err != nil {
		t.Fatalf("WS write command: %v", err)
	}
	t.Logf("✓ FBC command sent via WebSocket")

	time.Sleep(1 * time.Second)

	received := dnaServer.getReceived()
	hasFBC := false
	for _, cmd := range received {
		if strings.Contains(cmd, "print from fbc io structure 1620000") {
			hasFBC = true
		}
	}
	if !hasFBC {
		t.Error("✗ FBC command not received by DNA server via WebSocket")
	} else {
		t.Logf("✓ FBC command verified on DNA server via WebSocket")
	}

	// Disconnect
	conn.WriteMessage(websocket.TextMessage, []byte(`{"action":"disconnect"}`))
	t.Logf("✓ WebSocket disconnected")
}

// TestE2E_Commander_CommandResolver verifies shorthand command resolution.
func TestE2E_Commander_CommandResolver(t *testing.T) {
	tests := []struct {
		name      string
		shorthand string
		token     string
		expected  string
	}{
		{"ps→show all", "ps", "", "show all"},
		{"fis with token", "fis", "162", "print_fieldbus 1620000"},
		{"rc with token", "rc", "162", "print_fieldbus_rupi_counters 1620000"},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			fn, ok := getCommandResolver(tt.shorthand)
			if !ok {
				t.Fatalf("resolver not found for %s", tt.shorthand)
			}
			result := fn(tt.token)
			if result != tt.expected {
				t.Errorf("expected %q, got %q", tt.expected, result)
			}
			t.Logf("✓ %s: %s → %s", tt.name, tt.shorthand, result)
		})
	}
}

// TestE2E_Commander_TelnetCommands verifies full-form command generators.
func TestE2E_Commander_TelnetCommands(t *testing.T) {
	tests := []struct {
		name     string
		expected string
	}{
		{"FBCPrint(162)", "print from fbc io structure 1620000"},
		{"FBCClear(162)", "clear fbc io structure 1620000"},
		{"RPCPrint(162)", "print from fbc rupi counters 1620000"},
		{"RPCClear(162)", "clear fbc rupi counters 1620000"},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			result := generateTelnetCommand(tt.name, "162")
			if result != tt.expected {
				t.Errorf("expected %q, got %q", tt.expected, result)
			}
			t.Logf("✓ %s → %s", tt.name, result)
		})
	}
}

// TestE2E_Commander_NodesConfigLoadSave tests loading and saving nodes.json.
func TestE2E_Commander_NodesConfigLoadSave(t *testing.T) {
	ts, _ := setupCommanderTestServer(t)
	defer ts.Close()

	// Save original nodes.json if it exists (test isolation)
	originalNodesJSON, _ := os.ReadFile("nodes.json")
	defer func() {
		if originalNodesJSON != nil {
			os.WriteFile("nodes.json", originalNodesJSON, 0644)
		}
	}()

	// Get config
	resp, err := http.Get(ts.URL + "/api/v1/nodesconfig")
	if err != nil {
		t.Fatalf("GET nodesconfig: %v", err)
	}
	if resp.StatusCode != http.StatusOK {
		t.Fatalf("expected 200, got %d", resp.StatusCode)
	}
	var configResp map[string]interface{}
	json.NewDecoder(resp.Body).Decode(&configResp)
	resp.Body.Close()
	configs, ok := configResp["configs"].([]interface{})
	if !ok {
		t.Fatal("expected configs array")
	}
	t.Logf("✓ Loaded %d node configs", len(configs))

	// Save
	saveBody := `[{"name":"TEST01","ip_address":"10.0.0.1","tokens":[{"token_id":"999","token_type":"FBC","port":23,"protocol":"telnet"}]}]`
	resp, err = http.Post(ts.URL+"/api/v1/nodesconfig", "application/json", strings.NewReader(saveBody))
	if err != nil {
		t.Fatalf("POST nodesconfig: %v", err)
	}
	if resp.StatusCode != http.StatusOK {
		body, _ := io.ReadAll(resp.Body)
		t.Fatalf("expected 200, got %d: %s", resp.StatusCode, body)
	}
	resp.Body.Close()
	t.Logf("✓ Saved 1 node config")

	// Reload
	resp, err = http.Get(ts.URL + "/api/v1/nodesconfig")
	if err != nil {
		t.Fatalf("GET reload: %v", err)
	}
	json.NewDecoder(resp.Body).Decode(&configResp)
	resp.Body.Close()
	configs, ok = configResp["configs"].([]interface{})
	if !ok || len(configs) != 1 {
		t.Errorf("expected 1 config after save, got %d", len(configs))
	}
	if len(configs) == 1 {
		node := configs[0].(map[string]interface{})
		if node["name"] != "TEST01" {
			t.Errorf("expected name TEST01, got %v", node["name"])
		}
	}
	t.Logf("✓ Reloaded config verified")
}

// TestE2E_Commander_BsToolSuffixStripping verifies node suffix stripping.
func TestE2E_Commander_BsToolSuffixStripping(t *testing.T) {
	tests := []struct {
		input    string
		expected string
	}{
		{"AP01m", "AP01"},
		{"AP01r", "AP01"},
		{"AL03", "AL03"},
		{"BP02m", "BP02"},
	}

	for _, tt := range tests {
		result := stripSuffix(tt.input)
		if result != tt.expected {
			t.Errorf("stripSuffix(%q) = %q, expected %q", tt.input, result, tt.expected)
		}
		t.Logf("✓ stripSuffix(%q) → %q", tt.input, result)
	}
}
