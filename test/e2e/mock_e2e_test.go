// Package e2e provides mock-based end-to-end tests for LOGReport.
// These tests use mock TCP servers to simulate Valmet DNA nodes,
// allowing full pipeline testing without real hardware.
package e2e

import (
	"bytes"
	"context"
	"embed"
	"encoding/json"
	"fmt"
	"io"
	"mime/multipart"
	"net"
	"net/http"
	"os"
	"path/filepath"
	"strings"
	"sync"
	"testing"
	"time"

	"github.com/falke-ai-circuit/LOGReport/internal/api"
	"github.com/falke-ai-circuit/LOGReport/internal/bstool"
	"github.com/falke-ai-circuit/LOGReport/internal/server"
	"github.com/falke-ai-circuit/LOGReport/internal/store"
	"github.com/falke-ai-circuit/LOGReport/internal/types"
)

// ─── Mock DNA Server ──────────────────────────────────────────────

// mockDNAServer starts a TCP listener that mimics a Valmet DNA node.
// It accepts multiple connections and responds with FBC/RPC output.
// Returns the host:port address and a stop function.
func mockDNAServer(t *testing.T, behavior func(net.Conn)) (addr string, stop func()) {
	t.Helper()

	listener, err := net.Listen("tcp", "127.0.0.1:0")
	if err != nil {
		t.Fatalf("mock server listen: %v", err)
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
				behavior(c)
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

// mockDNAServerOnIP starts a mock DNA server on a specific IP for
// multi-node tests requiring unique addresses.
func mockDNAServerOnIP(t *testing.T, ip string, behavior func(net.Conn)) (addr string, stop func()) {
	t.Helper()

	listener, err := net.Listen("tcp", ip+":0")
	if err != nil {
		t.Fatalf("mock server listen on %s: %v", ip, err)
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
				behavior(c)
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

// fbcRPCBehavior responds with realistic FBC and RPC output.
// It handles both FBC and RPC commands sequentially on the same connection,
// matching the scan handler's flow: send FBC → read → send RPC → read.
func fbcRPCBehavior(conn net.Conn) {
	buf := make([]byte, 4096)

	// Send banner
	conn.Write([]byte("Welcome to Valmet DNA\r\n"))

	// Read first command (FBC)
	n, _ := conn.Read(buf)
	cmd := strings.TrimSpace(string(buf[:n]))

	if strings.Contains(cmd, "fbc io structure") {
		fbcOutput := "[2024-01-15 10:30:00]\r\n" +
			"print from fbc io structure 1620000\r\n" +
			"FBC agent 162\r\n\r\n" +
			" PIC    5    6    7    8    9   10   11   12   13   14   15   16   17   18   19   20  sum\r\n" +
			"----------------------------------------------------------------------------------------------\r\n" +
			"  0   AI8  BI8  BO8  BI8  BI8  BI8  BO8  BI8  BI8  BI8  BI8  BI8  BI8  BI8  TI6  AO4   15\r\n" +
			"  1   AI8  BI8  BI8  BI8  BO8  BI8  BO8  BI8  BI8  BI8  BI8  BI8  BI8  BI8  TI6  BI8   15\r\n" +
			"  2   AI8  BI8  BI8  BI8  BO8  BI8  BO8  BI8  BI8  BI8  BI8  BI8  BI8  BI8  BI8  BI8   15\r\n" +
			"  3   AI8  BI8  BO8  BI8  BO8  BI8  BO8  BI8  BI8  BI8  BI8  BI8  BI8  BI8  TI6  BI8   15\r\n\r\n" +
			"Total sum: 238 I/O-units, 1843 Channels (1323 input, 520 output)\r\n" +
			"AIU8: 15, AOU4: 4, BIU8: 131, BI8N: 6, BOU8: 63, FIU1: 2, AIU4: 1, TIU6: 16\r\n" +
			"162a% "
		conn.Write([]byte(fbcOutput))

		// Read second command (RPC)
		n2, _ := conn.Read(buf)
		cmd2 := strings.TrimSpace(string(buf[:n2]))

		if strings.Contains(cmd2, "rupi counters") {
			rpcOutput := "[2024-01-15 10:30:00]\r\n" +
				"print from fbc rupi counters 1620000\r\n" +
				"RPC agent 162\r\n\r\n" +
				" PIC  5  6  7  8  sum\r\n" +
				"-------------------------------\r\n" +
				"  0    12  34  56  78   180\r\n" +
				"  1    90  10  20  30   150\r\n" +
				"  2    5   15  25  35    80\r\n" +
				"  3    100 200 300 400  1000\r\n\r\n" +
				"Total sum: 1410 counters\r\n" +
				"162a% "
			conn.Write([]byte(rpcOutput))
		} else {
			conn.Write([]byte("162a% "))
		}
	} else if strings.Contains(cmd, "rupi counters") {
		rpcOutput := "[2024-01-15 10:30:00]\r\n" +
			"print from fbc rupi counters 1620000\r\n" +
			"RPC agent 162\r\n\r\n" +
			" PIC  5  6  7  8  sum\r\n" +
			"-------------------------------\r\n" +
			"  0    12  34  56  78   180\r\n" +
			"  1    90  10  20  30   150\r\n" +
			"  2    5   15  25  35    80\r\n" +
			"  3    100 200 300 400  1000\r\n\r\n" +
			"Total sum: 1410 counters\r\n" +
			"162a% "
		conn.Write([]byte(rpcOutput))
	} else {
		// Generic response for connect verification
		conn.Write([]byte("162a% "))
	}
}

// connectOnlyBehavior responds only to connect verification (no scan data).
func connectOnlyBehavior(conn net.Conn) {
	buf := make([]byte, 4096)
	conn.Write([]byte("Welcome to Valmet DNA\r\n"))
	conn.Read(buf)
	conn.Write([]byte("162a% "))
}

// ─── Test Server Helpers ──────────────────────────────────────────

// e2eServer wraps a running LOGReport HTTP server for E2E tests.
type e2eServer struct {
	srv     *api.Server
	store   *store.Store
	baseURL string
	httpSrv *http.Server
}

// startE2EServer creates and starts a LOGReport HTTP server with a
// file-based SQLite DB (needed for concurrent access).
func startE2EServer(t *testing.T) *e2eServer {
	t.Helper()

	dbPath := filepath.Join(os.TempDir(), fmt.Sprintf("logreport-e2e-%d", time.Now().UnixNano()))
	st, err := store.Open(dbPath)
	if err != nil {
		t.Fatalf("open store: %v", err)
	}

	// Create default template so report generation works
	st.SaveTemplate(&types.Template{
		Name:    "default",
		Format:  "docx",
		Content: "Default LOGReport template",
	})

	cfg := &server.Config{
		Port:       0,
		DBPath:     dbPath,
		LogLevel:   "debug",
		CORSOrigin: "*",
	}

	srv := api.NewServer(st, cfg, embed.FS{}, bstool.NewClient())

	mux := http.NewServeMux()
	srv.RegisterRoutesForTest(mux)

	var handler http.Handler = mux
	handler = api.LoggingMiddlewareForTest(handler)
	handler = api.CORSMiddlewareForTest(cfg.CORSOrigin)(handler)
	handler = api.ContentTypeMiddlewareForTest(handler)

	httpSrv := &http.Server{
		Addr:    cfg.Addr(),
		Handler: handler,
	}

	listener, err := net.Listen("tcp", "127.0.0.1:0")
	if err != nil {
		st.Close()
		t.Fatalf("listen: %v", err)
	}

	baseURL := fmt.Sprintf("http://%s", listener.Addr().String())

	go func() {
		httpSrv.Serve(listener)
	}()

	// Wait for server to be ready
	time.Sleep(100 * time.Millisecond)

	es := &e2eServer{
		srv:     srv,
		store:   st,
		baseURL: baseURL,
		httpSrv: httpSrv,
	}

	t.Cleanup(func() {
		ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
		defer cancel()
		httpSrv.Shutdown(ctx)
		listener.Close()
		st.Close()
		os.Remove(dbPath)
	})

	return es
}

// doRequest performs an HTTP request against the E2E server.
func (es *e2eServer) doRequest(method, path string, body io.Reader, headers map[string]string) (*http.Response, []byte) {
	url := es.baseURL + path
	req, err := http.NewRequest(method, url, body)
	if err != nil {
		panic(fmt.Sprintf("create request: %v", err))
	}
	for k, v := range headers {
		req.Header.Set(k, v)
	}

	client := &http.Client{Timeout: 15 * time.Second}
	resp, err := client.Do(req)
	if err != nil {
		panic(fmt.Sprintf("do request: %v", err))
	}
	defer resp.Body.Close()

	respBody, err := io.ReadAll(resp.Body)
	if err != nil {
		panic(fmt.Sprintf("read body: %v", err))
	}

	return resp, respBody
}

// parseJSON parses a JSON response body into a map.
func parseJSON(body []byte) map[string]interface{} {
	var result map[string]interface{}
	json.Unmarshal(body, &result)
	return result
}

// parseAddr splits host:port into components.
func parseAddr(t *testing.T, addr string) (string, int) {
	t.Helper()
	host, portStr, err := net.SplitHostPort(addr)
	if err != nil {
		t.Fatalf("split host port %q: %v", addr, err)
	}
	var port int
	fmt.Sscanf(portStr, "%d", &port)
	return host, port
}

// findSysFile locates a .sys test file from the parser testdata directory.
func findSysFile(t *testing.T) string {
	t.Helper()

	dir, err := os.Getwd()
	if err != nil {
		return ""
	}

	// Walk up to find go.mod
	for {
		if _, err := os.Stat(filepath.Join(dir, "go.mod")); err == nil {
			break
		}
		parent := filepath.Dir(dir)
		if parent == dir {
			return ""
		}
		dir = parent
	}

	candidates := []string{
		"internal/parser/testdata/sysfile_hw.txt",
		"internal/parser/testdata/sysfile_mixed.txt",
		"internal/parser/testdata/sysfile_slot.txt",
	}

	for _, p := range candidates {
		abs := filepath.Join(dir, p)
		if _, err := os.Stat(abs); err == nil {
			return abs
		}
	}

	return ""
}

// ─── Mock E2E Tests ───────────────────────────────────────────────

// TestMockE2EFullWorkflow exercises the complete pipeline using mock
// DNA servers: connect → scan → get FBC → get RPC → generate report →
// list reports → download report.
func TestMockE2EFullWorkflow(t *testing.T) {
	// Start mock DNA server
	dnaAddr, dnaStop := mockDNAServer(t, fbcRPCBehavior)
	defer dnaStop()

	host, port := parseAddr(t, dnaAddr)

	// Start E2E server
	es := startE2EServer(t)

	// Step 1: Health check
	resp, body := es.doRequest("GET", "/health", nil, nil)
	if resp.StatusCode != http.StatusOK {
		t.Fatalf("health check: expected 200, got %d: %s", resp.StatusCode, string(body))
	}
	health := parseJSON(body)
	if health["status"] != "ok" {
		t.Errorf("health status: expected 'ok', got %v", health["status"])
	}

	// Step 2: Connect to mock DNA node
	connectBody, _ := json.Marshal(map[string]interface{}{
		"address":   host,
		"port":      port,
		"name":      "MockE2E-ACN-01",
		"node_type": "ACN",
		"token":     "162",
	})
	resp, body = es.doRequest("POST", "/api/v1/connect", bytes.NewReader(connectBody),
		map[string]string{"Content-Type": "application/json"})
	if resp.StatusCode != http.StatusOK {
		t.Fatalf("connect: expected 200, got %d: %s", resp.StatusCode, string(body))
	}
	connectResp := parseJSON(body)
	node, ok := connectResp["node"].(map[string]interface{})
	if !ok {
		t.Fatalf("connect response missing 'node': %v", connectResp)
	}
	if node["address"] != host {
		t.Errorf("node address: expected %q, got %v", host, node["address"])
	}
	if node["status"] != "connected" {
		t.Errorf("node status: expected 'connected', got %v", node["status"])
	}

	// Step 3: Scan node (FBC + RPC)
	scanBody, _ := json.Marshal(map[string]interface{}{
		"modules": []string{"fbc", "rpc"},
		"token":   "162",
	})
	resp, body = es.doRequest("POST", "/api/v1/nodes/"+host+"/scan",
		bytes.NewReader(scanBody), map[string]string{"Content-Type": "application/json"})
	if resp.StatusCode != http.StatusOK {
		t.Fatalf("scan: expected 200, got %d: %s", resp.StatusCode, string(body))
	}
	scanResp := parseJSON(body)
	fbcModules, _ := scanResp["fbc_modules"].([]interface{})
	rpcModules, _ := scanResp["rpc_modules"].([]interface{})
	ioTotal, _ := scanResp["io_points_total"].(float64)

	if len(fbcModules) == 0 {
		t.Error("expected FBC modules in scan response")
	}
	if len(rpcModules) == 0 {
		t.Error("expected RPC modules in scan response")
	}
	if ioTotal == 0 {
		t.Error("expected IO points total > 0")
	}
	t.Logf("Scan: %d FBC modules, %d RPC modules, %.0f total IO points",
		len(fbcModules), len(rpcModules), ioTotal)

	// Step 4: Get FBC data via GET endpoint
	resp, body = es.doRequest("GET", "/api/v1/nodes/"+host+"/fbc", nil, nil)
	if resp.StatusCode != http.StatusOK {
		t.Fatalf("get FBC: expected 200, got %d: %s", resp.StatusCode, string(body))
	}
	fbcResp := parseJSON(body)
	fbcMods, _ := fbcResp["fbc_modules"].([]interface{})
	if len(fbcMods) == 0 {
		t.Error("expected FBC modules from GET /fbc")
	}

	// Step 5: Get RPC data via GET endpoint
	resp, body = es.doRequest("GET", "/api/v1/nodes/"+host+"/rpc", nil, nil)
	if resp.StatusCode != http.StatusOK {
		t.Fatalf("get RPC: expected 200, got %d: %s", resp.StatusCode, string(body))
	}
	rpcResp := parseJSON(body)
	rpcMods, _ := rpcResp["rpc_modules"].([]interface{})
	if len(rpcMods) == 0 {
		t.Error("expected RPC modules from GET /rpc")
	}

	// Step 6: Generate JSON report
	genBody, _ := json.Marshal(map[string]interface{}{
		"node_addresses": []string{host},
		"format":         "json",
		"template":       "default",
	})
	resp, body = es.doRequest("POST", "/api/v1/reports/generate",
		bytes.NewReader(genBody), map[string]string{"Content-Type": "application/json"})
	if resp.StatusCode != http.StatusOK {
		t.Fatalf("generate report: expected 200, got %d: %s", resp.StatusCode, string(body))
	}
	genResp := parseJSON(body)
	reportID, _ := genResp["report_id"].(string)
	if reportID == "" {
		t.Fatal("expected report_id in generate response")
	}
	t.Logf("Generated report: %s", reportID)

	// Step 7: List reports
	resp, body = es.doRequest("GET", "/api/v1/reports", nil, nil)
	if resp.StatusCode != http.StatusOK {
		t.Fatalf("list reports: expected 200, got %d", resp.StatusCode)
	}
	reportsResp := parseJSON(body)
	reportsList, _ := reportsResp["reports"].([]interface{})
	if len(reportsList) == 0 {
		t.Error("expected at least 1 report in list")
	}

	// Step 8: Download report
	resp, body = es.doRequest("GET", "/api/v1/reports/"+reportID, nil, nil)
	if resp.StatusCode != http.StatusOK {
		t.Fatalf("download report: expected 200, got %d: %s", resp.StatusCode, string(body))
	}
	if len(body) == 0 {
		t.Error("expected non-empty report body")
	}

	// Verify it's valid JSON (the report was JSON format)
	var reportJSON map[string]interface{}
	if err := json.Unmarshal(body, &reportJSON); err != nil {
		t.Errorf("downloaded report is not valid JSON: %v", err)
	}

	// Step 9: Generate DOCX report and verify it can be downloaded
	genBody2, _ := json.Marshal(map[string]interface{}{
		"node_addresses": []string{host},
		"format":         "docx",
		"template":       "default",
	})
	resp, body = es.doRequest("POST", "/api/v1/reports/generate",
		bytes.NewReader(genBody2), map[string]string{"Content-Type": "application/json"})
	if resp.StatusCode != http.StatusOK {
		t.Fatalf("generate DOCX report: expected 200, got %d: %s", resp.StatusCode, string(body))
	}
	genResp2 := parseJSON(body)
	reportID2, _ := genResp2["report_id"].(string)
	if reportID2 == "" {
		t.Fatal("expected report_id for DOCX report")
	}

	resp, body = es.doRequest("GET", "/api/v1/reports/"+reportID2, nil, nil)
	if resp.StatusCode != http.StatusOK {
		t.Fatalf("download DOCX report: expected 200, got %d", resp.StatusCode)
	}
	if len(body) == 0 {
		t.Error("expected non-empty DOCX report body")
	}

	// Verify it starts with ZIP magic bytes (DOCX = ZIP)
	if len(body) < 4 || body[0] != 'P' || body[1] != 'K' {
		t.Error("downloaded DOCX does not have ZIP magic bytes (PK)")
	}
}

// TestMockE2ESysFileUpload tests sysfile upload and parse through the API.
func TestMockE2ESysFileUpload(t *testing.T) {
	es := startE2EServer(t)

	// Find a real .sys test file
	sysFilePath := findSysFile(t)
	if sysFilePath == "" {
		t.Skip("no .sys test file found")
	}

	fileData, err := os.ReadFile(sysFilePath)
	if err != nil {
		t.Fatalf("read sys file: %v", err)
	}

	// Create multipart form with store_nodes=true
	var buf bytes.Buffer
	writer := multipart.NewWriter(&buf)
	part, err := writer.CreateFormFile("file", filepath.Base(sysFilePath))
	if err != nil {
		t.Fatalf("create form file: %v", err)
	}
	part.Write(fileData)
	writer.WriteField("store_nodes", "true")
	writer.Close()

	resp, body := es.doRequest("POST", "/api/v1/parse/sysfile", &buf,
		map[string]string{"Content-Type": writer.FormDataContentType()})
	if resp.StatusCode != http.StatusOK {
		t.Fatalf("parse sysfile: expected 200, got %d: %s", resp.StatusCode, string(body))
	}

	parseResp := parseJSON(body)
	entries, _ := parseResp["entries"].([]interface{})
	totalEntries, _ := parseResp["total_entries"].(float64)
	nodesCreated, _ := parseResp["nodes_created"].(float64)

	t.Logf("SysFile parse: %d entries, %.0f nodes created", len(entries), nodesCreated)

	if totalEntries == 0 {
		t.Error("expected entries from sysfile parse")
	}
	if nodesCreated == 0 {
		t.Error("expected nodes to be created from sysfile (store_nodes=true)")
	}

	// Verify nodes were stored
	resp, body = es.doRequest("GET", "/api/v1/nodes", nil, nil)
	if resp.StatusCode != http.StatusOK {
		t.Fatalf("list nodes after sysfile: expected 200, got %d", resp.StatusCode)
	}
	nodesResp := parseJSON(body)
	nodesList, _ := nodesResp["nodes"].([]interface{})
	if len(nodesList) == 0 {
		t.Error("expected nodes in list after sysfile parse with store_nodes=true")
	}
	t.Logf("Nodes after sysfile: %d", len(nodesList))

	// Verify each entry has expected fields
	for i, entry := range entries {
		e, ok := entry.(map[string]interface{})
		if !ok {
			t.Errorf("entry %d is not an object", i)
			continue
		}
		if e["lid"] == nil || e["lid"] == "" {
			t.Errorf("entry %d missing 'lid' field", i)
		}
		if e["node_type"] == nil || e["node_type"] == "" {
			t.Errorf("entry %d missing 'node_type' field", i)
		}
	}
}

// TestMockE2EMultiNodeReport tests connecting to multiple mock nodes,
// scanning all, and generating reports for all via wildcard.
func TestMockE2EMultiNodeReport(t *testing.T) {
	// Start 3 mock DNA servers on different loopback IPs
	dnaAddr1, dnaStop1 := mockDNAServerOnIP(t, "127.0.0.1", fbcRPCBehavior)
	defer dnaStop1()
	dnaAddr2, dnaStop2 := mockDNAServerOnIP(t, "127.0.0.2", fbcRPCBehavior)
	defer dnaStop2()
	dnaAddr3, dnaStop3 := mockDNAServerOnIP(t, "127.0.0.3", fbcRPCBehavior)
	defer dnaStop3()

	host1, port1 := parseAddr(t, dnaAddr1)
	host2, port2 := parseAddr(t, dnaAddr2)
	host3, port3 := parseAddr(t, dnaAddr3)

	es := startE2EServer(t)

	// Connect to all 3 nodes
	nodes := []struct {
		host, name, token string
		port              int
	}{
		{host1, "ACN-01", "162", port1},
		{host2, "ACN-02", "163", port2},
		{host3, "CIS-01", "164", port3},
	}

	for _, n := range nodes {
		connectBody, _ := json.Marshal(map[string]interface{}{
			"address":   n.host,
			"port":      n.port,
			"name":      n.name,
			"node_type": "ACN",
			"token":     n.token,
		})
		resp, body := es.doRequest("POST", "/api/v1/connect", bytes.NewReader(connectBody),
			map[string]string{"Content-Type": "application/json"})
		if resp.StatusCode != http.StatusOK {
			t.Fatalf("connect %s: expected 200, got %d: %s", n.name, resp.StatusCode, string(body))
		}
	}

	// Verify all 3 nodes listed
	resp, body := es.doRequest("GET", "/api/v1/nodes", nil, nil)
	if resp.StatusCode != http.StatusOK {
		t.Fatalf("list nodes: expected 200, got %d", resp.StatusCode)
	}
	nodesResp := parseJSON(body)
	nodesList, _ := nodesResp["nodes"].([]interface{})
	if len(nodesList) != 3 {
		t.Errorf("expected 3 nodes, got %d", len(nodesList))
	}

	// Scan all 3 nodes
	for _, n := range nodes {
		scanBody, _ := json.Marshal(map[string]interface{}{
			"modules": []string{"fbc", "rpc"},
			"token":   n.token,
		})
		resp, body = es.doRequest("POST", "/api/v1/nodes/"+n.host+"/scan",
			bytes.NewReader(scanBody), map[string]string{"Content-Type": "application/json"})
		if resp.StatusCode != http.StatusOK {
			t.Fatalf("scan %s: expected 200, got %d: %s", n.name, resp.StatusCode, string(body))
		}
		scanResp := parseJSON(body)
		ioTotal, _ := scanResp["io_points_total"].(float64)
		if ioTotal == 0 {
			t.Errorf("node %s: expected IO points > 0", n.name)
		}
		t.Logf("Node %s: %.0f IO points", n.name, ioTotal)
	}

	// Verify IO points stored for each node
	for _, n := range nodes {
		resp, _ := es.doRequest("GET", "/api/v1/nodes/"+n.host+"/fbc", nil, nil)
		if resp.StatusCode != http.StatusOK {
			t.Errorf("get FBC for %s: expected 200, got %d", n.name, resp.StatusCode)
		}
		resp, _ = es.doRequest("GET", "/api/v1/nodes/"+n.host+"/rpc", nil, nil)
		if resp.StatusCode != http.StatusOK {
			t.Errorf("get RPC for %s: expected 200, got %d", n.name, resp.StatusCode)
		}
	}

	// Generate report for all nodes using wildcard
	genBody, _ := json.Marshal(map[string]interface{}{
		"node_addresses": []string{"*"},
		"format":         "json",
		"template":       "default",
	})
	resp, body = es.doRequest("POST", "/api/v1/reports/generate",
		bytes.NewReader(genBody), map[string]string{"Content-Type": "application/json"})
	if resp.StatusCode != http.StatusOK {
		t.Fatalf("generate wildcard report: expected 200, got %d: %s", resp.StatusCode, string(body))
	}
	genResp := parseJSON(body)
	reports, _ := genResp["reports"].([]interface{})
	if len(reports) != 3 {
		t.Errorf("expected 3 reports for wildcard, got %d", len(reports))
	}
	t.Logf("Generated %d reports via wildcard", len(reports))

	// Verify all reports are listed
	resp, body = es.doRequest("GET", "/api/v1/reports", nil, nil)
	if resp.StatusCode != http.StatusOK {
		t.Fatalf("list reports: expected 200, got %d", resp.StatusCode)
	}
	reportsResp := parseJSON(body)
	reportsList, _ := reportsResp["reports"].([]interface{})
	if len(reportsList) < 3 {
		t.Errorf("expected at least 3 reports in list, got %d", len(reportsList))
	}
}

// TestMockE2EConcurrentScan tests that concurrent scan requests to
// different nodes don't interfere with each other.
func TestMockE2EConcurrentScan(t *testing.T) {
	// Start 3 mock DNA servers
	dnaAddr1, dnaStop1 := mockDNAServerOnIP(t, "127.0.0.1", fbcRPCBehavior)
	defer dnaStop1()
	dnaAddr2, dnaStop2 := mockDNAServerOnIP(t, "127.0.0.2", fbcRPCBehavior)
	defer dnaStop2()
	dnaAddr3, dnaStop3 := mockDNAServerOnIP(t, "127.0.0.3", fbcRPCBehavior)
	defer dnaStop3()

	host1, port1 := parseAddr(t, dnaAddr1)
	host2, port2 := parseAddr(t, dnaAddr2)
	host3, port3 := parseAddr(t, dnaAddr3)

	es := startE2EServer(t)

	// Connect to all 3 nodes sequentially (must be done before concurrent scans)
	nodeSpecs := []struct {
		host, name, token string
		port              int
	}{
		{host1, "Concurrent-01", "162", port1},
		{host2, "Concurrent-02", "163", port2},
		{host3, "Concurrent-03", "164", port3},
	}

	for _, n := range nodeSpecs {
		connectBody, _ := json.Marshal(map[string]interface{}{
			"address":   n.host,
			"port":      n.port,
			"name":      n.name,
			"node_type": "ACN",
			"token":     n.token,
		})
		resp, body := es.doRequest("POST", "/api/v1/connect", bytes.NewReader(connectBody),
			map[string]string{"Content-Type": "application/json"})
		if resp.StatusCode != http.StatusOK {
			t.Fatalf("connect %s: expected 200, got %d: %s", n.name, resp.StatusCode, string(body))
		}
	}

	// Launch concurrent scan requests
	var wg sync.WaitGroup
	results := make([]struct {
		name    string
		success bool
		ioTotal int
		err     error
	}, len(nodeSpecs))

	for i, n := range nodeSpecs {
		wg.Add(1)
		go func(idx int, spec struct {
			host, name, token string
			port              int
		}) {
			defer wg.Done()

			scanBody, _ := json.Marshal(map[string]interface{}{
				"modules": []string{"fbc", "rpc"},
				"token":   spec.token,
			})
			resp, body := es.doRequest("POST", "/api/v1/nodes/"+spec.host+"/scan",
				bytes.NewReader(scanBody), map[string]string{"Content-Type": "application/json"})

			if resp.StatusCode != http.StatusOK {
				results[idx].name = spec.name
				results[idx].success = false
				results[idx].err = fmt.Errorf("scan %s: got %d: %s", spec.name, resp.StatusCode, string(body))
				return
			}

			scanResp := parseJSON(body)
			ioTotal, _ := scanResp["io_points_total"].(float64)
			results[idx].name = spec.name
			results[idx].success = true
			results[idx].ioTotal = int(ioTotal)
		}(i, n)
	}

	wg.Wait()

	// Verify all concurrent scans succeeded
	allSuccess := true
	for _, r := range results {
		if !r.success {
			t.Errorf("concurrent scan %s failed: %v", r.name, r.err)
			allSuccess = false
		} else if r.ioTotal == 0 {
			t.Errorf("concurrent scan %s: expected IO points > 0, got 0", r.name)
			allSuccess = false
		} else {
			t.Logf("Concurrent scan %s: %d IO points", r.name, r.ioTotal)
		}
	}
	if !allSuccess {
		t.Error("not all concurrent scans succeeded")
	}

	// Verify each node has the correct IO data (no cross-contamination)
	for _, n := range nodeSpecs {
		resp, body := es.doRequest("GET", "/api/v1/nodes/"+n.host+"/fbc", nil, nil)
		if resp.StatusCode != http.StatusOK {
			t.Errorf("get FBC for %s after concurrent scan: expected 200, got %d", n.name, resp.StatusCode)
			continue
		}
		fbcResp := parseJSON(body)
		fbcMods, _ := fbcResp["fbc_modules"].([]interface{})
		if len(fbcMods) == 0 {
			t.Errorf("node %s: no FBC data after concurrent scan", n.name)
		}
	}
}
