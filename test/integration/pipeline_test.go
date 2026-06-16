// Package integration provides end-to-end pipeline tests for LOGReport.
// These tests exercise the full stack: HTTP server → telnet → parser → store → report generator.
package integration

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

// ─── Mock DNA Server ─────────────────────────────────────────────

// mockDNAServer starts a TCP listener that mimics a Valmet DNA node.
// It accepts multiple connections and responds with realistic FBC/RPC output.
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

	// Accept connections in a loop until stopped
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
					t.Logf("mock server accept: %v", err)
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

// fbcRPCBehavior responds with realistic FBC and RPC output for scan operations.
// It handles both FBC and RPC commands sequentially on the same connection,
// matching the scan handler's flow: send FBC → read → send RPC → read.
func fbcRPCBehavior(conn net.Conn) {
	buf := make([]byte, 4096)

	// Send banner
	conn.Write([]byte("Welcome to Valmet DNA\r\n"))

	// Read first command (FBC)
	n, _ := conn.Read(buf)
	cmd := string(buf[:n])
	cmd = strings.TrimSpace(cmd)

	if strings.Contains(cmd, "fbc io structure") {
		// Return realistic FBC output (PIC format)
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

		// Read second command (RPC) — scan handler sends FBC then RPC on same connection
		n2, _ := conn.Read(buf)
		cmd2 := string(buf[:n2])
		cmd2 = strings.TrimSpace(cmd2)

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
		// RPC-only scan
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

// ─── Test Server Helpers ─────────────────────────────────────────

// integrationServer wraps a running LOGReport HTTP server for integration tests.
type integrationServer struct {
	srv     *api.Server
	store   *store.Store
	baseURL string
	httpSrv *http.Server
}

// startIntegrationServerFile creates and starts a LOGReport HTTP server using a file-based DB.
// This is needed for concurrent tests where in-memory SQLite has locking issues.
func startIntegrationServerFile(t *testing.T) *integrationServer {
	t.Helper()

	dbPath := filepath.Join(os.TempDir(), fmt.Sprintf("logreport-integration-%d.db", time.Now().UnixNano()))
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
	if cfg.CORSOrigin != "" {
		handler = api.CORSMiddlewareForTest(cfg.CORSOrigin)(handler)
	}
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

	time.Sleep(100 * time.Millisecond)

	is := &integrationServer{
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

	return is
}

// startIntegrationServer creates and starts a LOGReport HTTP server on a random port
// using an in-memory SQLite database.
func startIntegrationServer(t *testing.T) *integrationServer {
	t.Helper()

	st, err := store.Open(":memory:")
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
		Port:       0, // random port
		DBPath:     ":memory:",
		LogLevel:   "debug",
		CORSOrigin: "*",
	}

	srv := api.NewServer(st, cfg, embed.FS{}, bstool.NewClient())

	// Create mux with all routes
	mux := http.NewServeMux()
	srv.RegisterRoutesForTest(mux)

	var handler http.Handler = mux
	handler = api.LoggingMiddlewareForTest(handler)
	if cfg.CORSOrigin != "" {
		handler = api.CORSMiddlewareForTest(cfg.CORSOrigin)(handler)
	}
	handler = api.ContentTypeMiddlewareForTest(handler)

	httpSrv := &http.Server{
		Addr:    cfg.Addr(),
		Handler: handler,
	}

	// Start server in background
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

	is := &integrationServer{
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
	})

	return is
}

// doRequest performs an HTTP request against the integration server.
func (is *integrationServer) doRequest(method, path string, body io.Reader, headers map[string]string) (*http.Response, []byte) {
	url := is.baseURL + path
	req, err := http.NewRequest(method, url, body)
	if err != nil {
		panic(fmt.Sprintf("create request: %v", err))
	}
	for k, v := range headers {
		req.Header.Set(k, v)
	}

	client := &http.Client{Timeout: 10 * time.Second}
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

// ─── Test: Full Pipeline ──────────────────────────────────────────

// TestFullPipeline exercises the complete pipeline:
// connect → scan (FBC+RPC) → store IO points → generate report → download report
func TestFullPipeline(t *testing.T) {
	// Start mock DNA server
	dnaAddr, dnaStop := mockDNAServer(t, fbcRPCBehavior)
	defer dnaStop()

	host, port := parseAddr(t, dnaAddr)

	// Start integration server
	is := startIntegrationServer(t)

	// Step 1: Health check
	resp, body := is.doRequest("GET", "/health", nil, nil)
	if resp.StatusCode != http.StatusOK {
		t.Fatalf("health check: expected 200, got %d: %s", resp.StatusCode, string(body))
	}
	health := parseJSON(body)
	if health["status"] != "ok" {
		t.Errorf("health status: expected 'ok', got %v", health["status"])
	}

	// Step 2: Connect to mock DNA node
	connectBody := map[string]interface{}{
		"address":   host,
		"port":      port,
		"name":      "Test-ACN-01",
		"node_type": "ACN",
		"token":     "162",
	}
	connectJSON, _ := json.Marshal(connectBody)
	resp, body = is.doRequest("POST", "/api/v1/connect", bytes.NewReader(connectJSON),
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

	// Step 3: List nodes — verify node is stored
	resp, body = is.doRequest("GET", "/api/v1/nodes", nil, nil)
	if resp.StatusCode != http.StatusOK {
		t.Fatalf("list nodes: expected 200, got %d", resp.StatusCode)
	}
	nodesResp := parseJSON(body)
	nodesList, _ := nodesResp["nodes"].([]interface{})
	if len(nodesList) != 1 {
		t.Errorf("expected 1 node, got %d", len(nodesList))
	}

	// Step 4: Scan node (FBC + RPC)
	scanBody := map[string]interface{}{
		"modules": []string{"fbc", "rpc"},
		"token":   "162",
	}
	scanJSON, _ := json.Marshal(scanBody)
	resp, body = is.doRequest("POST", "/api/v1/nodes/"+host+"/scan",
		bytes.NewReader(scanJSON), map[string]string{"Content-Type": "application/json"})
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
	t.Logf("Scan result: %d FBC modules, %d RPC modules, %.0f total IO points",
		len(fbcModules), len(rpcModules), ioTotal)

	// Step 5: Get FBC data
	resp, body = is.doRequest("GET", "/api/v1/nodes/"+host+"/fbc", nil, nil)
	if resp.StatusCode != http.StatusOK {
		t.Fatalf("get FBC: expected 200, got %d: %s", resp.StatusCode, string(body))
	}
	fbcResp := parseJSON(body)
	fbcMods, _ := fbcResp["fbc_modules"].([]interface{})
	if len(fbcMods) == 0 {
		t.Error("expected FBC modules from GET /fbc")
	}

	// Step 6: Get RPC data
	resp, body = is.doRequest("GET", "/api/v1/nodes/"+host+"/rpc", nil, nil)
	if resp.StatusCode != http.StatusOK {
		t.Fatalf("get RPC: expected 200, got %d: %s", resp.StatusCode, string(body))
	}
	rpcResp := parseJSON(body)
	rpcMods, _ := rpcResp["rpc_modules"].([]interface{})
	if len(rpcMods) == 0 {
		t.Error("expected RPC modules from GET /rpc")
	}

	// Step 7: Generate report (JSON format)
	genBody := map[string]interface{}{
		"node_addresses": []string{host},
		"format":         "json",
		"template":       "default",
	}
	genJSON, _ := json.Marshal(genBody)
	resp, body = is.doRequest("POST", "/api/v1/reports/generate",
		bytes.NewReader(genJSON), map[string]string{"Content-Type": "application/json"})
	if resp.StatusCode != http.StatusOK {
		t.Fatalf("generate report: expected 200, got %d: %s", resp.StatusCode, string(body))
	}
	genResp := parseJSON(body)
	reportID, _ := genResp["report_id"].(string)
	if reportID == "" {
		t.Fatal("expected report_id in generate response")
	}
	t.Logf("Generated report: %s", reportID)

	// Step 8: List reports
	resp, body = is.doRequest("GET", "/api/v1/reports", nil, nil)
	if resp.StatusCode != http.StatusOK {
		t.Fatalf("list reports: expected 200, got %d", resp.StatusCode)
	}
	reportsResp := parseJSON(body)
	reportsList, _ := reportsResp["reports"].([]interface{})
	if len(reportsList) == 0 {
		t.Error("expected at least 1 report in list")
	}

	// Step 9: Get report (download)
	resp, body = is.doRequest("GET", "/api/v1/reports/"+reportID, nil, nil)
	if resp.StatusCode != http.StatusOK {
		t.Fatalf("get report: expected 200, got %d: %s", resp.StatusCode, string(body))
	}
	// Report should be served as file download
	contentType := resp.Header.Get("Content-Type")
	if contentType != "application/json" {
		t.Logf("Report content-type: %s", contentType)
	}
	if len(body) == 0 {
		t.Error("expected non-empty report body")
	}

	// Step 10: Generate DOCX report
	genBody2 := map[string]interface{}{
		"node_addresses": []string{host},
		"format":         "docx",
		"template":       "default",
	}
	genJSON2, _ := json.Marshal(genBody2)
	resp, body = is.doRequest("POST", "/api/v1/reports/generate",
		bytes.NewReader(genJSON2), map[string]string{"Content-Type": "application/json"})
	if resp.StatusCode != http.StatusOK {
		t.Fatalf("generate DOCX report: expected 200, got %d: %s", resp.StatusCode, string(body))
	}
	genResp2 := parseJSON(body)
	reportID2, _ := genResp2["report_id"].(string)
	if reportID2 == "" {
		t.Fatal("expected report_id for DOCX report")
	}
	t.Logf("Generated DOCX report: %s", reportID2)

	// Verify DOCX report can be downloaded
	resp, body = is.doRequest("GET", "/api/v1/reports/"+reportID2, nil, nil)
	if resp.StatusCode != http.StatusOK {
		t.Fatalf("get DOCX report: expected 200, got %d", resp.StatusCode)
	}
	if len(body) == 0 {
		t.Error("expected non-empty DOCX report body")
	}
}

// ─── Test: Multi-Node ─────────────────────────────────────────────

// TestMultiNodePipeline tests connecting to 3 mock nodes, scanning all, and verifying all stored.
func TestMultiNodePipeline(t *testing.T) {
	// Start 3 mock DNA servers on different loopback IPs to get unique addresses
	dnaAddr1, dnaStop1 := mockDNAServerOnIP(t, "127.0.0.1", fbcRPCBehavior)
	defer dnaStop1()
	dnaAddr2, dnaStop2 := mockDNAServerOnIP(t, "127.0.0.2", fbcRPCBehavior)
	defer dnaStop2()
	dnaAddr3, dnaStop3 := mockDNAServerOnIP(t, "127.0.0.3", fbcRPCBehavior)
	defer dnaStop3()

	host1, port1 := parseAddr(t, dnaAddr1)
	host2, port2 := parseAddr(t, dnaAddr2)
	host3, port3 := parseAddr(t, dnaAddr3)

	// Start integration server
	is := startIntegrationServer(t)

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
		connectBody := map[string]interface{}{
			"address":   n.host,
			"port":      n.port,
			"name":      n.name,
			"node_type": "ACN",
			"token":     n.token,
		}
		connectJSON, _ := json.Marshal(connectBody)
		resp, body := is.doRequest("POST", "/api/v1/connect", bytes.NewReader(connectJSON),
			map[string]string{"Content-Type": "application/json"})
		if resp.StatusCode != http.StatusOK {
			t.Fatalf("connect %s: expected 200, got %d: %s", n.name, resp.StatusCode, string(body))
		}
	}

	// Verify all 3 nodes listed
	resp, body := is.doRequest("GET", "/api/v1/nodes", nil, nil)
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
		scanBody := map[string]interface{}{
			"modules": []string{"fbc", "rpc"},
			"token":   n.token,
		}
		scanJSON, _ := json.Marshal(scanBody)
		resp, body := is.doRequest("POST", "/api/v1/nodes/"+n.host+"/scan",
			bytes.NewReader(scanJSON), map[string]string{"Content-Type": "application/json"})
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
		resp, _ := is.doRequest("GET", "/api/v1/nodes/"+n.host+"/fbc", nil, nil)
		if resp.StatusCode != http.StatusOK {
			t.Errorf("get FBC for %s: expected 200, got %d", n.name, resp.StatusCode)
		}
		resp, _ = is.doRequest("GET", "/api/v1/nodes/"+n.host+"/rpc", nil, nil)
		if resp.StatusCode != http.StatusOK {
			t.Errorf("get RPC for %s: expected 200, got %d", n.name, resp.StatusCode)
		}
	}

	// Generate report for all nodes using wildcard
	genBody := map[string]interface{}{
		"node_addresses": []string{"*"},
		"format":         "json",
		"template":       "default",
	}
	genJSON, _ := json.Marshal(genBody)
	resp, body = is.doRequest("POST", "/api/v1/reports/generate",
		bytes.NewReader(genJSON), map[string]string{"Content-Type": "application/json"})
	if resp.StatusCode != http.StatusOK {
		t.Fatalf("generate wildcard report: expected 200, got %d: %s", resp.StatusCode, string(body))
	}
	genResp := parseJSON(body)
	reports, _ := genResp["reports"].([]interface{})
	if len(reports) != 3 {
		t.Errorf("expected 3 reports for wildcard, got %d", len(reports))
	}
	t.Logf("Generated %d reports via wildcard", len(reports))
}

// ─── Test: SysFile Upload → Parse → Store ────────────────────────

// TestSysFileUploadPipeline tests uploading a .sys file, parsing it, and verifying entries stored.
func TestSysFileUploadPipeline(t *testing.T) {
	is := startIntegrationServer(t)

	// Find a real .sys file from parser testdata
	sysFilePath := findSysFile(t)
	if sysFilePath == "" {
		t.Skip("no .sys test file found")
	}

	// Read the file
	fileData, err := os.ReadFile(sysFilePath)
	if err != nil {
		t.Fatalf("read sys file: %v", err)
	}

	// Create multipart form
	var buf bytes.Buffer
	writer := multipart.NewWriter(&buf)
	part, err := writer.CreateFormFile("file", filepath.Base(sysFilePath))
	if err != nil {
		t.Fatalf("create form file: %v", err)
	}
	part.Write(fileData)
	// Add store_nodes=true field
	writer.WriteField("store_nodes", "true")
	writer.Close()

	resp, body := is.doRequest("POST", "/api/v1/parse/sysfile", &buf,
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
	resp, body = is.doRequest("GET", "/api/v1/nodes", nil, nil)
	if resp.StatusCode != http.StatusOK {
		t.Fatalf("list nodes after sysfile: expected 200, got %d", resp.StatusCode)
	}
	nodesResp := parseJSON(body)
	nodesList, _ := nodesResp["nodes"].([]interface{})
	if len(nodesList) == 0 {
		t.Error("expected nodes after sysfile upload with store_nodes=true")
	}
}

// ─── Test: API Error Paths ────────────────────────────────────────

// TestAPIErrorPaths tests various error conditions in the API.
func TestAPIErrorPaths(t *testing.T) {
	is := startIntegrationServer(t)

	t.Run("invalid JSON body", func(t *testing.T) {
		resp, body := is.doRequest("POST", "/api/v1/connect",
			bytes.NewReader([]byte("not json")),
			map[string]string{"Content-Type": "application/json"})
		if resp.StatusCode != http.StatusBadRequest {
			t.Errorf("expected 400, got %d: %s", resp.StatusCode, string(body))
		}
		errResp := parseJSON(body)
		if errResp["error"] != "validation_error" {
			t.Errorf("expected 'validation_error', got %v", errResp["error"])
		}
	})

	t.Run("missing required fields", func(t *testing.T) {
		connectBody := map[string]interface{}{
			"port": 23,
		}
		connectJSON, _ := json.Marshal(connectBody)
		resp, body := is.doRequest("POST", "/api/v1/connect",
			bytes.NewReader(connectJSON),
			map[string]string{"Content-Type": "application/json"})
		if resp.StatusCode != http.StatusBadRequest {
			t.Errorf("expected 400, got %d: %s", resp.StatusCode, string(body))
		}
	})

	t.Run("wrong content-type", func(t *testing.T) {
		connectBody := map[string]interface{}{
			"address": "10.0.0.1",
			"name":    "test",
		}
		connectJSON, _ := json.Marshal(connectBody)
		resp, body := is.doRequest("POST", "/api/v1/connect",
			bytes.NewReader(connectJSON),
			map[string]string{"Content-Type": "text/plain"})
		if resp.StatusCode != http.StatusUnsupportedMediaType {
			t.Errorf("expected 415, got %d: %s", resp.StatusCode, string(body))
		}
	})

	t.Run("node not found", func(t *testing.T) {
		resp, body := is.doRequest("GET", "/api/v1/nodes/10.255.255.255", nil, nil)
		if resp.StatusCode != http.StatusNotFound {
			t.Errorf("expected 404, got %d: %s", resp.StatusCode, string(body))
		}
	})

	t.Run("scan non-existent node", func(t *testing.T) {
		scanBody := map[string]interface{}{
			"modules": []string{"fbc"},
		}
		scanJSON, _ := json.Marshal(scanBody)
		resp, body := is.doRequest("POST", "/api/v1/nodes/10.255.255.255/scan",
			bytes.NewReader(scanJSON),
			map[string]string{"Content-Type": "application/json"})
		if resp.StatusCode != http.StatusNotFound {
			t.Errorf("expected 404, got %d: %s", resp.StatusCode, string(body))
		}
	})

	t.Run("generate report without scan data", func(t *testing.T) {
		// Connect a node but don't scan
		dnaAddr, dnaStop := mockDNAServer(t, connectOnlyBehavior)
		defer dnaStop()
		host, port := parseAddr(t, dnaAddr)

		connectBody := map[string]interface{}{
			"address":   host,
			"port":      port,
			"name":      "NoScan-Node",
			"node_type": "ACN",
			"token":     "162",
		}
		connectJSON, _ := json.Marshal(connectBody)
		is.doRequest("POST", "/api/v1/connect", bytes.NewReader(connectJSON),
			map[string]string{"Content-Type": "application/json"})

		genBody := map[string]interface{}{
			"node_addresses": []string{host},
			"format":         "json",
		}
		genJSON, _ := json.Marshal(genBody)
		resp, body := is.doRequest("POST", "/api/v1/reports/generate",
			bytes.NewReader(genJSON),
			map[string]string{"Content-Type": "application/json"})
		if resp.StatusCode != http.StatusBadRequest {
			t.Errorf("expected 400 for no scan data, got %d: %s", resp.StatusCode, string(body))
		}
	})

	t.Run("unsupported report format", func(t *testing.T) {
		genBody := map[string]interface{}{
			"node_addresses": []string{"10.0.0.1"},
			"format":         "pdf",
		}
		genJSON, _ := json.Marshal(genBody)
		resp, body := is.doRequest("POST", "/api/v1/reports/generate",
			bytes.NewReader(genJSON),
			map[string]string{"Content-Type": "application/json"})
		if resp.StatusCode != http.StatusBadRequest {
			t.Errorf("expected 400 for unsupported format, got %d: %s", resp.StatusCode, string(body))
		}
	})

	t.Run("report not found", func(t *testing.T) {
		resp, body := is.doRequest("GET", "/api/v1/reports/nonexistent-id", nil, nil)
		if resp.StatusCode != http.StatusNotFound {
			t.Errorf("expected 404, got %d: %s", resp.StatusCode, string(body))
		}
	})

	t.Run("sysfile without file field", func(t *testing.T) {
		var buf bytes.Buffer
		writer := multipart.NewWriter(&buf)
		writer.WriteField("store_nodes", "true")
		writer.Close()

		resp, body := is.doRequest("POST", "/api/v1/parse/sysfile", &buf,
			map[string]string{"Content-Type": writer.FormDataContentType()})
		if resp.StatusCode != http.StatusBadRequest {
			t.Errorf("expected 400, got %d: %s", resp.StatusCode, string(body))
		}
	})

	t.Run("scan disconnected node", func(t *testing.T) {
		// Add a node directly to store with disconnected status
		is.store.SaveNode(&types.Node{
			Address: "10.99.99.99",
			Name:    "Disconnected-Node",
			Type:    types.ACN,
			Status:  types.StatusDisconnected,
			Port:    23,
		})

		scanBody := map[string]interface{}{
			"modules": []string{"fbc"},
			"token":   "162",
		}
		scanJSON, _ := json.Marshal(scanBody)
		resp, body := is.doRequest("POST", "/api/v1/nodes/10.99.99.99/scan",
			bytes.NewReader(scanJSON),
			map[string]string{"Content-Type": "application/json"})
		if resp.StatusCode != http.StatusConflict {
			t.Errorf("expected 409 for disconnected node, got %d: %s", resp.StatusCode, string(body))
		}
	})
}

// ─── Test: Concurrent API Calls ────────────────────────────────────

// TestConcurrentAPICalls tests multiple simultaneous requests to the server.
func TestConcurrentAPICalls(t *testing.T) {
	is := startIntegrationServerFile(t)

	// Start a mock DNA server that can handle multiple connections
	dnaAddr, dnaStop := mockDNAServer(t, fbcRPCBehavior)
	defer dnaStop()
	host, port := parseAddr(t, dnaAddr)

	// Connect first
	connectBody := map[string]interface{}{
		"address":   host,
		"port":      port,
		"name":      "Concurrent-Node",
		"node_type": "ACN",
		"token":     "162",
	}
	connectJSON, _ := json.Marshal(connectBody)
	resp, _ := is.doRequest("POST", "/api/v1/connect", bytes.NewReader(connectJSON),
		map[string]string{"Content-Type": "application/json"})
	if resp.StatusCode != http.StatusOK {
		t.Fatalf("connect failed: %d", resp.StatusCode)
	}

	// Scan first to populate data
	scanBody := map[string]interface{}{
		"modules": []string{"fbc", "rpc"},
		"token":   "162",
	}
	scanJSON, _ := json.Marshal(scanBody)
	resp, _ = is.doRequest("POST", "/api/v1/nodes/"+host+"/scan",
		bytes.NewReader(scanJSON), map[string]string{"Content-Type": "application/json"})
	if resp.StatusCode != http.StatusOK {
		t.Fatalf("scan failed: %d", resp.StatusCode)
	}

	// Run concurrent requests
	var wg sync.WaitGroup
	concurrency := 10
	errors := make(chan error, concurrency*3)

	for i := 0; i < concurrency; i++ {
		wg.Add(3)

		// Concurrent health checks
		go func() {
			defer wg.Done()
			resp, _ := is.doRequest("GET", "/health", nil, nil)
			if resp.StatusCode != http.StatusOK {
				errors <- fmt.Errorf("health: %d", resp.StatusCode)
			}
		}()

		// Concurrent node list
		go func() {
			defer wg.Done()
			resp, _ := is.doRequest("GET", "/api/v1/nodes", nil, nil)
			if resp.StatusCode != http.StatusOK {
				errors <- fmt.Errorf("list nodes: %d", resp.StatusCode)
			}
		}()

		// Concurrent FBC queries
		go func() {
			defer wg.Done()
			resp, _ := is.doRequest("GET", "/api/v1/nodes/"+host+"/fbc", nil, nil)
			if resp.StatusCode != http.StatusOK {
				errors <- fmt.Errorf("get fbc: %d", resp.StatusCode)
			}
		}()
	}

	wg.Wait()
	close(errors)

	errCount := 0
	for err := range errors {
		t.Errorf("concurrent error: %v", err)
		errCount++
	}
	if errCount > 0 {
		t.Errorf("%d concurrent requests failed", errCount)
	} else {
		t.Logf("All %d concurrent requests succeeded", concurrency*3)
	}
}

// ─── Test: Server Graceful Shutdown ───────────────────────────────

// TestGracefulShutdown verifies the server stops cleanly when shut down.
func TestGracefulShutdown(t *testing.T) {
	st, err := store.Open(":memory:")
	if err != nil {
		t.Fatalf("open store: %v", err)
	}
	defer st.Close()

	cfg := &server.Config{
		Port:       0,
		DBPath:     ":memory:",
		LogLevel:   "debug",
		CORSOrigin: "*",
	}

	srv := api.NewServer(st, cfg, embed.FS{}, bstool.NewClient())

	mux := http.NewServeMux()
	srv.RegisterRoutesForTest(mux)

	var handler http.Handler = mux
	handler = api.LoggingMiddlewareForTest(handler)
	handler = api.ContentTypeMiddlewareForTest(handler)

	httpSrv := &http.Server{
		Addr:    cfg.Addr(),
		Handler: handler,
	}

	listener, err := net.Listen("tcp", "127.0.0.1:0")
	if err != nil {
		t.Fatalf("listen: %v", err)
	}
	baseURL := fmt.Sprintf("http://%s", listener.Addr().String())

	// Start server
	go httpSrv.Serve(listener)
	time.Sleep(100 * time.Millisecond)

	// Verify server is running
	resp, err := http.Get(baseURL + "/health")
	if err != nil {
		t.Fatalf("health check before shutdown: %v", err)
	}
	resp.Body.Close()
	if resp.StatusCode != http.StatusOK {
		t.Fatalf("health before shutdown: expected 200, got %d", resp.StatusCode)
	}

	// Shutdown gracefully
	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()

	shutdownDone := make(chan error, 1)
	go func() {
		shutdownDone <- httpSrv.Shutdown(ctx)
	}()

	select {
	case err := <-shutdownDone:
		if err != nil {
			t.Errorf("shutdown error: %v", err)
		} else {
			t.Log("Server shut down gracefully")
		}
	case <-time.After(6 * time.Second):
		t.Error("shutdown timed out")
	}

	// Verify server is no longer accepting connections
	_, err = http.Get(baseURL + "/health")
	if err == nil {
		t.Error("expected connection refused after shutdown")
	}
}

// ─── Test: Connect Failure ────────────────────────────────────────

// TestConnectFailure tests connecting to an unreachable node.
func TestConnectFailure(t *testing.T) {
	is := startIntegrationServer(t)

	connectBody := map[string]interface{}{
		"address":   "127.0.0.1",
		"port":      19999, // no listener
		"name":      "Dead-Node",
		"node_type": "ACN",
	}
	connectJSON, _ := json.Marshal(connectBody)
	resp, body := is.doRequest("POST", "/api/v1/connect", bytes.NewReader(connectJSON),
		map[string]string{"Content-Type": "application/json"})
	if resp.StatusCode != http.StatusBadGateway {
		t.Errorf("expected 502 for connection failure, got %d: %s", resp.StatusCode, string(body))
	}
	errResp := parseJSON(body)
	if errResp["error"] != "connection_failed" {
		t.Errorf("expected 'connection_failed', got %v", errResp["error"])
	}
}

// ─── Test: Get Node Detail ────────────────────────────────────────

// TestGetNodeDetail tests the GET /api/v1/nodes/{addr} endpoint with scan data.
func TestGetNodeDetail(t *testing.T) {
	dnaAddr, dnaStop := mockDNAServer(t, fbcRPCBehavior)
	defer dnaStop()
	host, port := parseAddr(t, dnaAddr)

	is := startIntegrationServer(t)

	// Connect
	connectBody := map[string]interface{}{
		"address":   host,
		"port":      port,
		"name":      "Detail-Node",
		"node_type": "ACN",
		"token":     "162",
	}
	connectJSON, _ := json.Marshal(connectBody)
	is.doRequest("POST", "/api/v1/connect", bytes.NewReader(connectJSON),
		map[string]string{"Content-Type": "application/json"})

	// Scan
	scanBody := map[string]interface{}{
		"modules": []string{"fbc", "rpc"},
		"token":   "162",
	}
	scanJSON, _ := json.Marshal(scanBody)
	is.doRequest("POST", "/api/v1/nodes/"+host+"/scan",
		bytes.NewReader(scanJSON), map[string]string{"Content-Type": "application/json"})

	// Get node detail
	resp, body := is.doRequest("GET", "/api/v1/nodes/"+host, nil, nil)
	if resp.StatusCode != http.StatusOK {
		t.Fatalf("get node: expected 200, got %d: %s", resp.StatusCode, string(body))
	}

	detail := parseJSON(body)
	node, _ := detail["node"].(map[string]interface{})
	ioSummary, _ := detail["io_summary"].(map[string]interface{})

	if node["name"] != "Detail-Node" {
		t.Errorf("node name: expected 'Detail-Node', got %v", node["name"])
	}
	fbcMods, _ := ioSummary["fbc_modules"].(float64)
	rpcMods, _ := ioSummary["rpc_modules"].(float64)
	if fbcMods == 0 {
		t.Error("expected FBC modules in io_summary")
	}
	if rpcMods == 0 {
		t.Error("expected RPC modules in io_summary")
	}
	t.Logf("Node detail: FBC=%.0f, RPC=%.0f, Total=%.0f",
		fbcMods, rpcMods, ioSummary["total_io_points"])
}

// ─── Helpers ──────────────────────────────────────────────────────

// parseAddr splits "host:port" into host string and port int.
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

// mockDNAServerOnIP starts a mock DNA server on a specific IP address.
// This is needed for multi-node tests where each node must have a unique address.
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
					t.Logf("mock server accept: %v", err)
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

// findSysFile locates a .sys test file from the parser testdata directory.
// It searches relative to the module root (where go.mod lives).
// Prefers text-based fixtures with :e:hw: entries for integration testing.
func findSysFile(t *testing.T) string {
	t.Helper()

	// Find the module root by looking for go.mod
	dir, err := os.Getwd()
	if err != nil {
		t.Logf("getwd: %v", err)
		return ""
	}

	// Walk up to find go.mod
	for {
		if _, err := os.Stat(filepath.Join(dir, "go.mod")); err == nil {
			break
		}
		parent := filepath.Dir(dir)
		if parent == dir {
			t.Log("could not find go.mod")
			return ""
		}
		dir = parent
	}

	// Try text-based fixtures first (they have :e:hw: entries)
	candidates := []string{
		"internal/parser/testdata/sysfile_hw.txt",
		"internal/parser/testdata/sysfile_mixed.txt",
		"internal/parser/testdata/sysfile_slot.txt",
	}

	for _, p := range candidates {
		abs := filepath.Join(dir, p)
		if _, err := os.Stat(abs); err == nil {
			t.Logf("Found sys file: %s", abs)
			return abs
		}
	}

	t.Logf("Module root: %s", dir)
	t.Log("No sys test files found")
	return ""
}
