package api

import (
	"archive/zip"
	"bytes"
	"embed"
	"encoding/json"
	"fmt"
	"io"
	"mime/multipart"
	"net"
	"net/http"
	"net/http/httptest"
	"os"
	"path/filepath"
	"strings"
	"sync"
	"testing"
	"time"

	"github.com/falke-ai-circuit/LOGReport/internal/bstool"
	"github.com/falke-ai-circuit/LOGReport/internal/server"
	"github.com/falke-ai-circuit/LOGReport/internal/store"
	"github.com/falke-ai-circuit/LOGReport/internal/types"
)

// ─── SPA Fallback Tests ─────────────────────────────────────────

// TestSPAFallbackWithEmptyEmbedFS verifies that registerStaticFiles handles
// an empty embed.FS gracefully (logs warning, does not register "/" handler).
func TestSPAFallbackWithEmptyEmbedFS(t *testing.T) {
	st, err := store.Open(":memory:")
	if err != nil {
		t.Fatalf("open store: %v", err)
	}
	defer st.Close()

	cfg := &server.Config{Port: 0, DBPath: ":memory:", LogLevel: "debug", CORSOrigin: "*"}
	srv := NewServer(st, cfg, embed.FS{}, bstool.NewClient())

	mux := http.NewServeMux()
	srv.registerRoutes(mux)
	srv.registerStaticFiles(mux)

	// With empty embed.FS, the "/" handler is not registered.
	// The default mux returns 404 for unmatched paths.
	rec := httptest.NewRecorder()
	req := httptest.NewRequest("GET", "/", nil)
	mux.ServeHTTP(rec, req)

	if rec.Code != http.StatusNotFound {
		t.Errorf("expected 404 with empty embed FS, got %d", rec.Code)
	}
}

// TestSPAFallbackLogic verifies the SPA fallback behavior by simulating
// what registerStaticFiles would do if the embed FS had content.
func TestSPAFallbackLogic(t *testing.T) {
	indexHTML := []byte("<!DOCTYPE html><html><head><title>LOGReport</title></head><body><div id=\"root\"></div></body></html>")

	mux := http.NewServeMux()
	// Simulate the SPA fallback handler
	mux.HandleFunc("/", func(w http.ResponseWriter, r *http.Request) {
		if strings.HasPrefix(r.URL.Path, "/api/") || r.URL.Path == "/health" {
			http.NotFound(w, r)
			return
		}
		path := strings.TrimPrefix(r.URL.Path, "/")
		if path == "" {
			path = "index.html"
		}
		// SPA fallback: serve index.html for any non-file path
		w.Header().Set("Content-Type", "text/html; charset=utf-8")
		w.WriteHeader(http.StatusOK)
		w.Write(indexHTML)
	})

	t.Run("GET / serves index.html", func(t *testing.T) {
		rec := httptest.NewRecorder()
		req := httptest.NewRequest("GET", "/", nil)
		mux.ServeHTTP(rec, req)
		if rec.Code != http.StatusOK {
			t.Errorf("expected 200, got %d", rec.Code)
		}
		if !strings.Contains(rec.Body.String(), "<div id=\"root\">") {
			t.Errorf("expected index.html content, got %q", rec.Body.String())
		}
		ct := rec.Header().Get("Content-Type")
		if !strings.Contains(ct, "text/html") {
			t.Errorf("expected text/html, got %q", ct)
		}
	})

	t.Run("GET /unknown/spa/route serves index.html", func(t *testing.T) {
		rec := httptest.NewRecorder()
		req := httptest.NewRequest("GET", "/nodes/10.0.0.1/details", nil)
		mux.ServeHTTP(rec, req)
		if rec.Code != http.StatusOK {
			t.Errorf("expected 200 for SPA route, got %d", rec.Code)
		}
		if !strings.Contains(rec.Body.String(), "<div id=\"root\">") {
			t.Error("SPA fallback should serve index.html")
		}
	})

	t.Run("GET /api/v1/nodes returns 404 (not intercepted by SPA)", func(t *testing.T) {
		rec := httptest.NewRecorder()
		req := httptest.NewRequest("GET", "/api/v1/nodes", nil)
		mux.ServeHTTP(rec, req)
		if rec.Code != http.StatusNotFound {
			t.Errorf("expected 404 for API path in SPA handler, got %d", rec.Code)
		}
	})

	t.Run("GET /health returns 404 (not intercepted by SPA)", func(t *testing.T) {
		rec := httptest.NewRecorder()
		req := httptest.NewRequest("GET", "/health", nil)
		mux.ServeHTTP(rec, req)
		if rec.Code != http.StatusNotFound {
			t.Errorf("expected 404 for health path in SPA handler, got %d", rec.Code)
		}
	})
}

// ─── Report Download Header Tests ───────────────────────────────

// TestReportDownloadHeaders verifies Content-Type and Content-Disposition headers
// for DOCX and JSON report downloads.
func TestReportDownloadHeaders(t *testing.T) {
	srv, st, cleanup := setupTest(t)
	defer cleanup()

	st.SaveNode(&types.Node{
		Address: "10.0.0.1",
		Name:    "test-node",
		Type:    types.ACN,
		Status:  types.StatusConnected,
		Port:    23,
	})
	st.SaveIOPoints("10.0.0.1", []types.IOPoint{
		{NodeAddress: "10.0.0.1", ModulePosition: 0, ChannelPosition: 5, ChannelType: types.AI8, ModuleType: types.ModuleFBC},
	})
	st.SaveTemplate(&types.Template{
		Name:    "default",
		Format:  "docx",
		Content: "LOGReport — Node Report",
	})

	mux := srv.NewTestMux()

	t.Run("DOCX report download headers", func(t *testing.T) {
		genBody := jsonBody(map[string]interface{}{
			"node_addresses": []string{"10.0.0.1"},
			"format":         "docx",
		})
		genRec := doRequest(mux, "POST", "/api/v1/reports/generate", genBody, map[string]string{
			"Content-Type": "application/json",
		})
		if genRec.Code != http.StatusOK {
			t.Fatalf("generate DOCX: expected 200, got %d: %s", genRec.Code, genRec.Body.String())
		}
		genResult := parseJSONResponse(genRec)
		reportID, ok := genResult["report_id"].(string)
		if !ok {
			t.Fatalf("missing report_id: %v", genResult)
		}

		rec := doRequest(mux, "GET", "/api/v1/reports/"+reportID, nil, nil)
		if rec.Code != http.StatusOK {
			t.Fatalf("download DOCX: expected 200, got %d: %s", rec.Code, rec.Body.String())
		}

		ct := rec.Header().Get("Content-Type")
		if !strings.Contains(ct, "application/vnd.openxmlformats-officedocument.wordprocessingml.document") {
			t.Errorf("DOCX Content-Type: expected OOXML wordprocessing, got %q", ct)
		}

		cd := rec.Header().Get("Content-Disposition")
		if !strings.Contains(cd, "attachment") {
			t.Errorf("DOCX Content-Disposition: expected attachment, got %q", cd)
		}
		if !strings.Contains(cd, ".docx") {
			t.Errorf("DOCX Content-Disposition: expected .docx filename, got %q", cd)
		}
	})

	t.Run("JSON report download headers", func(t *testing.T) {
		genBody := jsonBody(map[string]interface{}{
			"node_addresses": []string{"10.0.0.1"},
			"format":         "json",
		})
		genRec := doRequest(mux, "POST", "/api/v1/reports/generate", genBody, map[string]string{
			"Content-Type": "application/json",
		})
		if genRec.Code != http.StatusOK {
			t.Fatalf("generate JSON: expected 200, got %d: %s", genRec.Code, genRec.Body.String())
		}
		genResult := parseJSONResponse(genRec)
		reportID, ok := genResult["report_id"].(string)
		if !ok {
			t.Fatalf("missing report_id: %v", genResult)
		}

		rec := doRequest(mux, "GET", "/api/v1/reports/"+reportID, nil, nil)
		if rec.Code != http.StatusOK {
			t.Fatalf("download JSON: expected 200, got %d: %s", rec.Code, rec.Body.String())
		}

		ct := rec.Header().Get("Content-Type")
		if !strings.Contains(ct, "application/json") {
			t.Errorf("JSON Content-Type: expected application/json, got %q", ct)
		}

		cd := rec.Header().Get("Content-Disposition")
		if !strings.Contains(cd, "attachment") {
			t.Errorf("JSON Content-Disposition: expected attachment, got %q", cd)
		}
		if !strings.Contains(cd, ".json") {
			t.Errorf("JSON Content-Disposition: expected .json filename, got %q", cd)
		}
	})
}

// ─── Mock DNA Server for Scan Tests ─────────────────────────────

// mockScanDNAServer starts a TCP listener that mimics a Valmet DNA node
// for scan handler tests. Returns the host:port address and a stop function.
func mockScanDNAServer(t *testing.T) (addr string, stop func()) {
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
				buf := make([]byte, 4096)
				c.Write([]byte("Welcome to Valmet DNA\r\n"))
				// Read first command
				n, _ := c.Read(buf)
				cmd := strings.TrimSpace(string(buf[:n]))
				if strings.Contains(cmd, "fbc io structure") {
					fbcOutput := "[2024-01-15 10:30:00]\r\n" +
						"print from fbc io structure 1620000\r\n" +
						"FBC agent 162\r\n\r\n" +
						" PIC    5    6    7    8   sum\r\n" +
						"--------------------------------------\r\n" +
						"  0   AI8  BI8  BO8  BI8   4\r\n" +
						"  1   AI8  BI8  BI8  BI8   4\r\n\r\n" +
						"Total sum: 8 I/O-units\r\n" +
						"162a% "
					c.Write([]byte(fbcOutput))
					// Read second command (RPC)
					n2, _ := c.Read(buf)
					cmd2 := strings.TrimSpace(string(buf[:n2]))
					if strings.Contains(cmd2, "rupi counters") {
						rpcOutput := "[2024-01-15 10:30:00]\r\n" +
							"print from fbc rupi counters 1620000\r\n" +
							"RPC agent 162\r\n\r\n" +
							" PIC  5  6  sum\r\n" +
							"-------------------------------\r\n" +
							"  0    12  34   46\r\n" +
							"  1    90  10   100\r\n\r\n" +
							"Total sum: 146 counters\r\n" +
							"162a% "
						c.Write([]byte(rpcOutput))
					} else {
						c.Write([]byte("162a% "))
					}
				} else if strings.Contains(cmd, "rupi counters") {
					rpcOutput := "[2024-01-15 10:30:00]\r\n" +
						"print from fbc rupi counters 1620000\r\n" +
						"RPC agent 162\r\n\r\n" +
						" PIC  5  6  sum\r\n" +
						"-------------------------------\r\n" +
						"  0    12  34   46\r\n" +
						"162a% "
					c.Write([]byte(rpcOutput))
				} else {
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

// TestScanHandlerWithMockDNA verifies the scan handler with a mock DNA server.
// Tests the full scan flow: connect → scan FBC+RPC → parse → store IO points.
func TestScanHandlerWithMockDNA(t *testing.T) {
	dnaAddr, dnaStop := mockScanDNAServer(t)
	defer dnaStop()

	host, portStr, _ := net.SplitHostPort(dnaAddr)
	var port int
	fmt.Sscanf(portStr, "%d", &port)

	srv, st, cleanup := setupTest(t)
	defer cleanup()

	st.SaveNode(&types.Node{
		Address: host,
		Name:    "Mock-DNA-Node",
		Type:    types.ACN,
		Status:  types.StatusConnected,
		Port:    port,
		TokenID: "162",
	})

	mux := srv.NewTestMux()

	t.Run("scan FBC and RPC with mock DNA", func(t *testing.T) {
		body := jsonBody(map[string]interface{}{
			"modules": []string{"fbc", "rpc"},
			"token":   "162",
		})
		rec := doRequest(mux, "POST", "/api/v1/nodes/"+host+"/scan", body, map[string]string{
			"Content-Type": "application/json",
		})
		if rec.Code != http.StatusOK {
			t.Fatalf("scan: expected 200, got %d: %s", rec.Code, rec.Body.String())
		}

		result := parseJSONResponse(rec)
		fbcModules, ok := result["fbc_modules"].([]interface{})
		if !ok || len(fbcModules) == 0 {
			t.Errorf("expected FBC modules, got %v", result["fbc_modules"])
		}
		rpcModules, ok := result["rpc_modules"].([]interface{})
		if !ok || len(rpcModules) == 0 {
			t.Errorf("expected RPC modules, got %v", result["rpc_modules"])
		}
		ioTotal, ok := result["io_points_total"].(float64)
		if !ok || ioTotal == 0 {
			t.Errorf("expected io_points_total > 0, got %v", result["io_points_total"])
		}
	})

	t.Run("scan FBC only with mock DNA", func(t *testing.T) {
		body := jsonBody(map[string]interface{}{
			"modules": []string{"fbc"},
			"token":   "162",
		})
		rec := doRequest(mux, "POST", "/api/v1/nodes/"+host+"/scan", body, map[string]string{
			"Content-Type": "application/json",
		})
		if rec.Code != http.StatusOK {
			t.Fatalf("scan FBC only: expected 200, got %d: %s", rec.Code, rec.Body.String())
		}
		result := parseJSONResponse(rec)
		fbcModules, ok := result["fbc_modules"].([]interface{})
		if !ok || len(fbcModules) == 0 {
			t.Errorf("expected FBC modules, got %v", result["fbc_modules"])
		}
		// RPC should be empty when only FBC is requested
		rpcModules, ok := result["rpc_modules"].([]interface{})
		if ok && len(rpcModules) > 0 {
			t.Errorf("expected no RPC modules, got %d", len(rpcModules))
		}
	})

	// Verify IO points were stored after scan
	t.Run("IO points stored after scan", func(t *testing.T) {
		points, err := st.GetIOPoints(host)
		if err != nil {
			t.Fatalf("GetIOPoints: %v", err)
		}
		if len(points) == 0 {
			t.Error("expected IO points stored after scan")
		}
	})
}

// ─── Connect Handler with Mock TCP Server ───────────────────────

// TestConnectHandlerWithMockTCP verifies a successful connect against a mock TCP server.
func TestConnectHandlerWithMockTCP(t *testing.T) {
	listener, err := net.Listen("tcp", "127.0.0.1:0")
	if err != nil {
		t.Fatalf("listen: %v", err)
	}
	addr := listener.Addr().String()
	host, portStr, _ := net.SplitHostPort(addr)
	var port int
	fmt.Sscanf(portStr, "%d", &port)

	go func() {
		conn, err := listener.Accept()
		if err != nil {
			return
		}
		conn.Write([]byte("Welcome\r\n"))
		conn.Close()
	}()
	defer listener.Close()

	srv, st, cleanup := setupTest(t)
	defer cleanup()

	mux := srv.NewTestMux()

	body := jsonBody(map[string]interface{}{
		"address":   host,
		"port":      port,
		"name":      "Mock-Node",
		"node_type": "ACN",
		"token":     "162",
	})
	rec := doRequest(mux, "POST", "/api/v1/connect", body, map[string]string{
		"Content-Type": "application/json",
	})

	if rec.Code != http.StatusOK {
		t.Fatalf("connect: expected 200, got %d: %s", rec.Code, rec.Body.String())
	}

	result := parseJSONResponse(rec)
	node, ok := result["node"].(map[string]interface{})
	if !ok {
		t.Fatalf("expected node object, got %v", result["node"])
	}
	if node["address"] != host {
		t.Errorf("address: expected %q, got %v", host, node["address"])
	}
	if node["status"] != "connected" {
		t.Errorf("status: expected 'connected', got %v", node["status"])
	}

	// Verify node was saved to store
	saved, err := st.GetNode(host)
	if err != nil {
		t.Fatalf("GetNode: %v", err)
	}
	if saved.Name != "Mock-Node" {
		t.Errorf("saved name: expected 'Mock-Node', got %q", saved.Name)
	}
}

// ─── Start() Method Test ────────────────────────────────────────

// TestStartMethod verifies that Start() begins listening and serving HTTP.
func TestStartMethod(t *testing.T) {
	st, err := store.Open(":memory:")
	if err != nil {
		t.Fatalf("open store: %v", err)
	}
	defer st.Close()

	st.SaveNode(&types.Node{
		Address: "10.0.0.1",
		Name:    "test",
		Type:    types.ACN,
		Status:  types.StatusConnected,
		Port:    23,
	})

	// Find a free port
	listener, err := net.Listen("tcp", "127.0.0.1:0")
	if err != nil {
		t.Fatalf("listen: %v", err)
	}
	port := listener.Addr().(*net.TCPAddr).Port
	listener.Close()

	cfg := &server.Config{
		Port:       port,
		DBPath:     ":memory:",
		LogLevel:   "debug",
		CORSOrigin: "*",
	}

	srv := NewServer(st, cfg, embed.FS{}, bstool.NewClient())

	// Start in background
	errCh := make(chan error, 1)
	go func() {
		errCh <- srv.Start()
	}()

	// Wait for server to be ready
	time.Sleep(300 * time.Millisecond)

	// Send health check
	resp, err := http.Get(fmt.Sprintf("http://127.0.0.1:%d/health", port))
	if err != nil {
		t.Fatalf("health check failed: %v", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		t.Errorf("health: expected 200, got %d", resp.StatusCode)
	}

	body, _ := io.ReadAll(resp.Body)
	var health map[string]interface{}
	json.Unmarshal(body, &health)
	if health["status"] != "ok" {
		t.Errorf("health status: expected 'ok', got %v", health["status"])
	}
	// Server should still be running (not returned an error)
	select {
	case err := <-errCh:
		t.Errorf("Start() returned early with error: %v", err)
	default:
		// Server is running — good
	}
}

// ─── Password Storage Security Test ─────────────────────────────

// TestPasswordStorageSecurity documents that passwords are stored in plaintext.
// This is a known security issue — the test documents the current behavior.
func TestPasswordStorageSecurity(t *testing.T) {
	srv, st, cleanup := setupTest(t)
	defer cleanup()

	mux := srv.NewTestMux()

	// Start a mock TCP server
	listener, err := net.Listen("tcp", "127.0.0.1:0")
	if err != nil {
		t.Fatalf("listen: %v", err)
	}
	host, portStr, _ := net.SplitHostPort(listener.Addr().String())
	var port int
	fmt.Sscanf(portStr, "%d", &port)

	go func() {
		conn, err := listener.Accept()
		if err != nil {
			return
		}
		conn.Write([]byte("Welcome\r\n"))
		conn.Close()
	}()
	defer listener.Close()

	body := jsonBody(map[string]interface{}{
		"address":  host,
		"port":     port,
		"name":     "Secure-Node",
		"token":    "162",
		"username": "admin",
		"password": "supersecret123",
	})
	rec := doRequest(mux, "POST", "/api/v1/connect", body, map[string]string{
		"Content-Type": "application/json",
	})
	if rec.Code != http.StatusOK {
		t.Fatalf("connect: expected 200, got %d: %s", rec.Code, rec.Body.String())
	}

	// Retrieve the node from the store
	node, err := st.GetNode(host)
	if err != nil {
		t.Fatalf("GetNode: %v", err)
	}

	// Document the security issue: password is stored in plaintext
	if node.Password != "supersecret123" {
		t.Errorf("SECURITY: password should be hashed but is stored in plaintext. "+
			"Expected 'supersecret123', got %q. This is a known security issue.", node.Password)
	}
	t.Log("SECURITY NOTE: Passwords are stored in plaintext in the nodes table. " +
		"This is a known security issue that should be addressed with hashing (bcrypt/argon2).")

	// Verify the password is NOT returned in the API response
	result := parseJSONResponse(rec)
	apiNode, ok := result["node"].(map[string]interface{})
	if !ok {
		t.Fatalf("expected node object in response, got %v", result["node"])
	}
	if _, hasPassword := apiNode["password"]; hasPassword {
		t.Error("SECURITY: password field should not be exposed in API response")
	}
	if _, hasUsername := apiNode["username"]; hasUsername {
		t.Error("SECURITY: username field should not be exposed in API response")
	}
}

// ─── Wildcard Report Generation Test ────────────────────────────

// TestGenerateReportWildcard verifies the "*" wildcard generates reports for all nodes with scan data.
func TestGenerateReportWildcard(t *testing.T) {
	srv, st, cleanup := setupTest(t)
	defer cleanup()

	st.SaveNode(&types.Node{
		Address: "10.0.0.1", Name: "node1", Type: types.ACN,
		Status: types.StatusConnected, Port: 23,
	})
	st.SaveNode(&types.Node{
		Address: "10.0.0.2", Name: "node2", Type: types.DIA,
		Status: types.StatusConnected, Port: 23,
	})
	// Third node WITHOUT IO points (should be excluded from wildcard)
	st.SaveNode(&types.Node{
		Address: "10.0.0.3", Name: "node3", Type: types.CIS,
		Status: types.StatusConnected, Port: 23,
	})

	st.SaveIOPoints("10.0.0.1", []types.IOPoint{
		{NodeAddress: "10.0.0.1", ModulePosition: 0, ChannelPosition: 5, ChannelType: types.AI8, ModuleType: types.ModuleFBC},
	})
	st.SaveIOPoints("10.0.0.2", []types.IOPoint{
		{NodeAddress: "10.0.0.2", ModulePosition: 0, ChannelPosition: 5, ChannelType: types.AI8, ModuleType: types.ModuleFBC},
	})
	st.SaveTemplate(&types.Template{
		Name: "default", Format: "docx", Content: "LOGReport — Node Report",
	})

	mux := srv.NewTestMux()

	body := jsonBody(map[string]interface{}{
		"node_addresses": []string{"*"},
		"format":         "json",
	})
	rec := doRequest(mux, "POST", "/api/v1/reports/generate", body, map[string]string{
		"Content-Type": "application/json",
	})

	if rec.Code != http.StatusOK {
		t.Fatalf("wildcard generate: expected 200, got %d: %s", rec.Code, rec.Body.String())
	}

	result := parseJSONResponse(rec)
	reports, ok := result["reports"].([]interface{})
	if !ok {
		t.Fatalf("expected reports array, got %T", result["reports"])
	}
	if len(reports) != 2 {
		t.Errorf("expected 2 reports (nodes with scan data), got %d", len(reports))
	}
}

// TestGenerateReportWildcardNoScanData verifies wildcard with no scan data returns 400.
func TestGenerateReportWildcardNoScanData(t *testing.T) {
	srv, st, cleanup := setupTest(t)
	defer cleanup()

	st.SaveNode(&types.Node{
		Address: "10.0.0.1", Name: "node1", Type: types.ACN,
		Status: types.StatusConnected, Port: 23,
	})

	mux := srv.NewTestMux()

	body := jsonBody(map[string]interface{}{
		"node_addresses": []string{"*"},
		"format":         "docx",
	})
	rec := doRequest(mux, "POST", "/api/v1/reports/generate", body, map[string]string{
		"Content-Type": "application/json",
	})

	if rec.Code != http.StatusBadRequest {
		t.Errorf("expected 400 when no nodes with scan data, got %d: %s", rec.Code, rec.Body.String())
	}
}

// ─── Report Status Handler Tests ────────────────────────────────

// TestGetReportHandlerPending verifies a pending report returns 409.
func TestGetReportHandlerPending(t *testing.T) {
	srv, st, cleanup := setupTest(t)
	defer cleanup()

	st.SaveReport(&types.Report{
		ID: "rpt-pending", NodeAddress: "10.0.0.1",
		Format: types.FormatDOCX, Status: types.StatusPending,
		CreatedAt: "2026-06-15T10:00:00Z",
	})

	mux := srv.NewTestMux()
	rec := doRequest(mux, "GET", "/api/v1/reports/rpt-pending", nil, nil)

	if rec.Code != http.StatusConflict {
		t.Errorf("expected 409 for pending report, got %d: %s", rec.Code, rec.Body.String())
	}
	result := parseJSONResponse(rec)
	if result["error"] != "report_not_ready" {
		t.Errorf("expected error 'report_not_ready', got %v", result["error"])
	}
}

// TestGetReportHandlerFailed verifies a failed report returns 410.
func TestGetReportHandlerFailed(t *testing.T) {
	srv, st, cleanup := setupTest(t)
	defer cleanup()

	st.SaveReport(&types.Report{
		ID: "rpt-failed", NodeAddress: "10.0.0.1",
		Format: types.FormatDOCX, Status: types.StatusFailed,
		CreatedAt: "2026-06-15T10:00:00Z",
	})

	mux := srv.NewTestMux()
	rec := doRequest(mux, "GET", "/api/v1/reports/rpt-failed", nil, nil)

	if rec.Code != http.StatusGone {
		t.Errorf("expected 410 for failed report, got %d: %s", rec.Code, rec.Body.String())
	}
	result := parseJSONResponse(rec)
	if result["error"] != "report_failed" {
		t.Errorf("expected error 'report_failed', got %v", result["error"])
	}
}

// TestGetReportHandlerGenerating verifies a generating report returns 409.
func TestGetReportHandlerGenerating(t *testing.T) {
	srv, st, cleanup := setupTest(t)
	defer cleanup()

	st.SaveReport(&types.Report{
		ID: "rpt-generating", NodeAddress: "10.0.0.1",
		Format: types.FormatJSON, Status: types.StatusGenerating,
		CreatedAt: "2026-06-15T10:00:00Z",
	})

	mux := srv.NewTestMux()
	rec := doRequest(mux, "GET", "/api/v1/reports/rpt-generating", nil, nil)

	if rec.Code != http.StatusConflict {
		t.Errorf("expected 409 for generating report, got %d", rec.Code)
	}
}

// ─── Sysfile Upload with Store Nodes Test ───────────────────────

// TestParseSysfileStoreNodes verifies that store_nodes=true creates nodes from sysfile entries.
func TestParseSysfileStoreNodes(t *testing.T) {
	srv, st, cleanup := setupTest(t)
	defer cleanup()

	tmpDir := t.TempDir()
	sysPath := filepath.Join(tmpDir, "multi.sys")
	sysContent := ":e:hw:1a1   AL01   pxe:sys-csg2   // Main LIS node\n" +
		":e:hw:1a2   AL02   pxe:sys-csg2   // Backup LIS node\n" +
		":e:hw:1a3   ACN01  pxe:sys-csg2   // Application Control Node\n"
	os.WriteFile(sysPath, []byte(sysContent), 0644)

	body := &bytes.Buffer{}
	writer := multipart.NewWriter(body)
	part, _ := writer.CreateFormFile("file", "multi.sys")
	fileData, _ := os.ReadFile(sysPath)
	part.Write(fileData)
	writer.WriteField("store_nodes", "true")
	writer.Close()

	mux := srv.NewTestMux()
	rec := doRequest(mux, "POST", "/api/v1/parse/sysfile", body, map[string]string{
		"Content-Type": writer.FormDataContentType(),
	})

	if rec.Code != http.StatusOK {
		t.Fatalf("expected 200, got %d: %s", rec.Code, rec.Body.String())
	}

	result := parseJSONResponse(rec)
	nodesCreated, ok := result["nodes_created"].(float64)
	if !ok {
		t.Fatalf("expected nodes_created number, got %v", result["nodes_created"])
	}
	if nodesCreated < 1 {
		t.Errorf("expected nodes_created >= 1, got %v", nodesCreated)
	}

	nodes, err := st.ListNodes()
	if err != nil {
		t.Fatalf("ListNodes: %v", err)
	}
	if len(nodes) == 0 {
		t.Error("expected nodes in store after store_nodes=true")
	}
}

// ─── DOCX Report Content Verification ───────────────────────────

// TestDOCXReportContent verifies that a generated DOCX report is a valid ZIP/OOXML file.
func TestDOCXReportContent(t *testing.T) {
	srv, st, cleanup := setupTest(t)
	defer cleanup()

	st.SaveNode(&types.Node{
		Address: "10.0.0.1", Name: "test-node", Type: types.ACN,
		Status: types.StatusConnected, Port: 23,
	})
	st.SaveIOPoints("10.0.0.1", []types.IOPoint{
		{NodeAddress: "10.0.0.1", ModulePosition: 0, ChannelPosition: 5, ChannelType: types.AI8, ModuleType: types.ModuleFBC},
		{NodeAddress: "10.0.0.1", ModulePosition: 0, ChannelPosition: 6, ChannelType: types.BI8, ModuleType: types.ModuleFBC},
		{NodeAddress: "10.0.0.1", ModulePosition: 0, ChannelPosition: 0, CounterName: "5", CounterValue: 42, ModuleType: types.ModuleRPC},
	})
	st.SaveTemplate(&types.Template{
		Name: "default", Format: "docx", Content: "LOGReport — Node Report",
	})

	mux := srv.NewTestMux()

	genBody := jsonBody(map[string]interface{}{
		"node_addresses": []string{"10.0.0.1"},
		"format":         "docx",
	})
	genRec := doRequest(mux, "POST", "/api/v1/reports/generate", genBody, map[string]string{
		"Content-Type": "application/json",
	})
	if genRec.Code != http.StatusOK {
		t.Fatalf("generate: expected 200, got %d: %s", genRec.Code, genRec.Body.String())
	}
	genResult := parseJSONResponse(genRec)
	reportID, _ := genResult["report_id"].(string)
	if reportID == "" {
		t.Fatal("missing report_id")
	}

	rec := doRequest(mux, "GET", "/api/v1/reports/"+reportID, nil, nil)
	if rec.Code != http.StatusOK {
		t.Fatalf("download: expected 200, got %d", rec.Code)
	}

	bodyBytes := rec.Body.Bytes()
	zipReader, err := zip.NewReader(bytes.NewReader(bodyBytes), int64(len(bodyBytes)))
	if err != nil {
		t.Fatalf("DOCX body is not a valid ZIP: %v", err)
	}

	// Verify required OOXML entries exist
	requiredFiles := map[string]bool{
		"[Content_Types].xml":          false,
		"_rels/.rels":                  false,
		"word/document.xml":            false,
		"word/_rels/document.xml.rels": false,
	}
	for _, f := range zipReader.File {
		if _, ok := requiredFiles[f.Name]; ok {
			requiredFiles[f.Name] = true
		}
	}
	for name, found := range requiredFiles {
		if !found {
			t.Errorf("DOCX missing required entry: %s", name)
		}
	}

	// Verify document.xml contains the node name
	for _, f := range zipReader.File {
		if f.Name == "word/document.xml" {
			rc, err := f.Open()
			if err != nil {
				t.Fatalf("open document.xml: %v", err)
			}
			content, _ := io.ReadAll(rc)
			rc.Close()
			if !strings.Contains(string(content), "test-node") {
				t.Error("document.xml should contain node name 'test-node'")
			}
		}
	}
}