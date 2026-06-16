package api

import (
	"bytes"
	"encoding/json"
	"io"
	"mime/multipart"
	"net/http"
	"net/http/httptest"
	"os"
	"path/filepath"
	"strings"
	"testing"

	"github.com/falke-ai-circuit/LOGReport/internal/server"
	"github.com/falke-ai-circuit/LOGReport/internal/store"
	"github.com/falke-ai-circuit/LOGReport/internal/types"
)

// ─── Test Helpers ────────────────────────────────────────────────

// setupTest creates a test server with in-memory SQLite and returns
// the server, store, and a cleanup function.
func setupTest(t *testing.T) (*Server, *store.Store, func()) {
	t.Helper()

	st, err := store.Open(":memory:")
	if err != nil {
		t.Fatalf("failed to open in-memory store: %v", err)
	}

	cfg := &server.Config{
		Port:       0,
		DBPath:     ":memory:",
		LogLevel:   "debug",
		CORSOrigin: "*",
	}

	srv := NewServer(st, cfg)
	cleanup := func() {
		st.Close()
	}

	return srv, st, cleanup
}

// doRequest performs an HTTP request against the test mux and returns the response.
func doRequest(mux http.Handler, method, path string, body io.Reader, headers map[string]string) *httptest.ResponseRecorder {
	req := httptest.NewRequest(method, path, body)
	for k, v := range headers {
		req.Header.Set(k, v)
	}
	rec := httptest.NewRecorder()
	mux.ServeHTTP(rec, req)
	return rec
}

// jsonBody creates an io.Reader from a JSON-serializable value.
func jsonBody(v interface{}) io.Reader {
	data, _ := json.Marshal(v)
	return bytes.NewReader(data)
}

// parseJSONResponse parses the response body into a map.
func parseJSONResponse(rec *httptest.ResponseRecorder) map[string]interface{} {
	var result map[string]interface{}
	json.Unmarshal(rec.Body.Bytes(), &result)
	return result
}

// ─── Test: GET /health → 200, valid JSON ────────────────────────

func TestHealthHandler(t *testing.T) {
	srv, st, cleanup := setupTest(t)
	defer cleanup()

	// Add a node so node_count > 0
	st.SaveNode(&types.Node{
		Address: "10.0.0.1",
		Name:    "test-node",
		Type:    types.ACN,
		Status:  types.StatusConnected,
		Port:    23,
	})

	mux := srv.NewTestMux()
	rec := doRequest(mux, "GET", "/health", nil, nil)

	if rec.Code != http.StatusOK {
		t.Errorf("expected 200, got %d", rec.Code)
	}

	result := parseJSONResponse(rec)
	if result["status"] != "ok" {
		t.Errorf("expected status 'ok', got %v", result["status"])
	}
	if result["version"] != "0.1.0" {
		t.Errorf("expected version '0.1.0', got %v", result["version"])
	}
	if result["db_status"] != "connected" {
		t.Errorf("expected db_status 'connected', got %v", result["db_status"])
	}
	if result["uptime"] == nil || result["uptime"] == "" {
		t.Error("expected non-empty uptime")
	}
	nc, ok := result["node_count"].(float64)
	if !ok || nc < 1 {
		t.Errorf("expected node_count >= 1, got %v", result["node_count"])
	}
}

// ─── Test: POST /api/v1/connect → 200, node saved ───────────────

func TestConnectHandler(t *testing.T) {
	srv, _, cleanup := setupTest(t)
	defer cleanup()

	mux := srv.NewTestMux()

	// connectHandler tries a real telnet connection, which will fail in tests.
	// We test the validation path instead.
	t.Run("missing required fields", func(t *testing.T) {
		body := jsonBody(map[string]interface{}{
			"address": "",
			"name":    "",
		})
		rec := doRequest(mux, "POST", "/api/v1/connect", body, map[string]string{
			"Content-Type": "application/json",
		})
		if rec.Code != http.StatusBadRequest {
			t.Errorf("expected 400, got %d", rec.Code)
		}
		result := parseJSONResponse(rec)
		if result["error"] != "validation_error" {
			t.Errorf("expected validation_error, got %v", result["error"])
		}
	})

	t.Run("invalid JSON body", func(t *testing.T) {
		body := strings.NewReader("not json")
		rec := doRequest(mux, "POST", "/api/v1/connect", body, map[string]string{
			"Content-Type": "application/json",
		})
		if rec.Code != http.StatusBadRequest {
			t.Errorf("expected 400, got %d", rec.Code)
		}
	})

	t.Run("valid request but connection fails", func(t *testing.T) {
		body := jsonBody(map[string]interface{}{
			"address":   "192.168.1.100",
			"name":      "AP01m",
			"node_type": "ACN",
			"token":     "162",
		})
		rec := doRequest(mux, "POST", "/api/v1/connect", body, map[string]string{
			"Content-Type": "application/json",
		})
		// Should get 502 because telnet connection will fail
		if rec.Code != http.StatusBadGateway {
			t.Errorf("expected 502, got %d: %s", rec.Code, rec.Body.String())
		}
	})
}

// ─── Test: GET /api/v1/nodes → 200, nodes array ─────────────────

func TestListNodesHandler(t *testing.T) {
	srv, st, cleanup := setupTest(t)
	defer cleanup()

	mux := srv.NewTestMux()

	t.Run("empty nodes returns empty array not null", func(t *testing.T) {
		rec := doRequest(mux, "GET", "/api/v1/nodes", nil, nil)
		if rec.Code != http.StatusOK {
			t.Errorf("expected 200, got %d", rec.Code)
		}
		result := parseJSONResponse(rec)
		nodes, ok := result["nodes"].([]interface{})
		if !ok {
			t.Errorf("expected nodes to be array, got %T", result["nodes"])
		}
		if len(nodes) != 0 {
			t.Errorf("expected empty array, got %d elements", len(nodes))
		}
	})

	t.Run("with nodes", func(t *testing.T) {
		st.SaveNode(&types.Node{
			Address: "10.0.0.1",
			Name:    "node1",
			Type:    types.ACN,
			Status:  types.StatusConnected,
			Port:    23,
		})
		st.SaveNode(&types.Node{
			Address: "10.0.0.2",
			Name:    "node2",
			Type:    types.DIA,
			Status:  types.StatusDisconnected,
			Port:    23,
		})

		rec := doRequest(mux, "GET", "/api/v1/nodes", nil, nil)
		if rec.Code != http.StatusOK {
			t.Errorf("expected 200, got %d", rec.Code)
		}
		result := parseJSONResponse(rec)
		nodes, ok := result["nodes"].([]interface{})
		if !ok {
			t.Errorf("expected nodes to be array, got %T", result["nodes"])
		}
		if len(nodes) != 2 {
			t.Errorf("expected 2 nodes, got %d", len(nodes))
		}
		total, ok := result["total"].(float64)
		if !ok || total != 2 {
			t.Errorf("expected total 2, got %v", result["total"])
		}
	})
}

// ─── Test: GET /api/v1/nodes/{addr} → 200/404 ───────────────────

func TestGetNodeHandler(t *testing.T) {
	srv, st, cleanup := setupTest(t)
	defer cleanup()

	st.SaveNode(&types.Node{
		Address: "10.0.0.1",
		Name:    "test-node",
		Type:    types.ACN,
		Status:  types.StatusConnected,
		Port:    23,
	})

	mux := srv.NewTestMux()

	t.Run("existing node returns 200", func(t *testing.T) {
		rec := doRequest(mux, "GET", "/api/v1/nodes/10.0.0.1", nil, nil)
		if rec.Code != http.StatusOK {
			t.Errorf("expected 200, got %d: %s", rec.Code, rec.Body.String())
		}
		result := parseJSONResponse(rec)
		node, ok := result["node"].(map[string]interface{})
		if !ok {
			t.Errorf("expected node object, got %T", result["node"])
		}
		if node["address"] != "10.0.0.1" {
			t.Errorf("expected address 10.0.0.1, got %v", node["address"])
		}
	})

	t.Run("non-existent node returns 404", func(t *testing.T) {
		rec := doRequest(mux, "GET", "/api/v1/nodes/10.0.0.99", nil, nil)
		if rec.Code != http.StatusNotFound {
			t.Errorf("expected 404, got %d", rec.Code)
		}
		result := parseJSONResponse(rec)
		if result["error"] != "not_found" {
			t.Errorf("expected not_found, got %v", result["error"])
		}
	})
}

// ─── Test: POST /api/v1/reports/generate → 200, report created ──

func TestGenerateReportHandler(t *testing.T) {
	srv, st, cleanup := setupTest(t)
	defer cleanup()

	// Create a node with IO points
	st.SaveNode(&types.Node{
		Address: "10.0.0.1",
		Name:    "test-node",
		Type:    types.ACN,
		Status:  types.StatusConnected,
		Port:    23,
	})
	st.SaveIOPoints("10.0.0.1", []types.IOPoint{
		{NodeAddress: "10.0.0.1", ModulePosition: 0, ChannelPosition: 5, ChannelType: types.AI8, ModuleType: types.ModuleFBC},
		{NodeAddress: "10.0.0.1", ModulePosition: 0, ChannelPosition: 6, ChannelType: types.BI8, ModuleType: types.ModuleFBC},
	})
	// Create a default template so report generation works
	st.SaveTemplate(&types.Template{
		Name:    "default",
		Format:  "docx",
		Content: "LOGReport — Node Report",
	})

	mux := srv.NewTestMux()

	t.Run("generate docx report", func(t *testing.T) {
		body := jsonBody(map[string]interface{}{
			"node_addresses": []string{"10.0.0.1"},
			"format":         "docx",
		})
		rec := doRequest(mux, "POST", "/api/v1/reports/generate", body, map[string]string{
			"Content-Type": "application/json",
		})
		if rec.Code != http.StatusOK {
			t.Errorf("expected 200, got %d: %s", rec.Code, rec.Body.String())
		}
		result := parseJSONResponse(rec)
		if result["status"] != "completed" {
			t.Errorf("expected status 'completed', got %v", result["status"])
		}
		if result["format"] != "docx" {
			t.Errorf("expected format 'docx', got %v", result["format"])
		}
	})

	t.Run("generate json report", func(t *testing.T) {
		body := jsonBody(map[string]interface{}{
			"node_addresses": []string{"10.0.0.1"},
			"format":         "json",
		})
		rec := doRequest(mux, "POST", "/api/v1/reports/generate", body, map[string]string{
			"Content-Type": "application/json",
		})
		if rec.Code != http.StatusOK {
			t.Errorf("expected 200, got %d: %s", rec.Code, rec.Body.String())
		}
	})

	t.Run("missing node_addresses", func(t *testing.T) {
		body := jsonBody(map[string]interface{}{
			"format": "docx",
		})
		rec := doRequest(mux, "POST", "/api/v1/reports/generate", body, map[string]string{
			"Content-Type": "application/json",
		})
		if rec.Code != http.StatusBadRequest {
			t.Errorf("expected 400, got %d", rec.Code)
		}
	})

	t.Run("unsupported format", func(t *testing.T) {
		body := jsonBody(map[string]interface{}{
			"node_addresses": []string{"10.0.0.1"},
			"format":         "pdf",
		})
		rec := doRequest(mux, "POST", "/api/v1/reports/generate", body, map[string]string{
			"Content-Type": "application/json",
		})
		if rec.Code != http.StatusBadRequest {
			t.Errorf("expected 400, got %d", rec.Code)
		}
		result := parseJSONResponse(rec)
		if result["error"] != "validation_error" {
			t.Errorf("expected validation_error, got %v", result["error"])
		}
	})

	t.Run("no scan data", func(t *testing.T) {
		body := jsonBody(map[string]interface{}{
			"node_addresses": []string{"10.0.0.99"},
			"format":         "docx",
		})
		rec := doRequest(mux, "POST", "/api/v1/reports/generate", body, map[string]string{
			"Content-Type": "application/json",
		})
		if rec.Code != http.StatusBadRequest {
			t.Errorf("expected 400, got %d: %s", rec.Code, rec.Body.String())
		}
	})
}

// ─── Test: GET /api/v1/reports/{id} → 200/404 ───────────────────

func TestGetReportHandler(t *testing.T) {
	srv, st, cleanup := setupTest(t)
	defer cleanup()

	// Create a node with IO points and generate a report
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
	// Create a default template so report generation works
	st.SaveTemplate(&types.Template{
		Name:    "default",
		Format:  "docx",
		Content: "LOGReport — Node Report",
	})

	// Generate a report first
	mux := srv.NewTestMux()
	body := jsonBody(map[string]interface{}{
		"node_addresses": []string{"10.0.0.1"},
		"format":         "json",
	})
	genRec := doRequest(mux, "POST", "/api/v1/reports/generate", body, map[string]string{
		"Content-Type": "application/json",
	})
	genResult := parseJSONResponse(genRec)
	reportID, ok := genResult["report_id"].(string)
	if !ok {
		t.Fatalf("failed to get report_id from generate response: %v", genResult)
	}

	t.Run("existing report returns 200", func(t *testing.T) {
		rec := doRequest(mux, "GET", "/api/v1/reports/"+reportID, nil, nil)
		if rec.Code != http.StatusOK {
			t.Errorf("expected 200, got %d: %s", rec.Code, rec.Body.String())
		}
	})

	t.Run("non-existent report returns 404", func(t *testing.T) {
		rec := doRequest(mux, "GET", "/api/v1/reports/nonexistent-id", nil, nil)
		if rec.Code != http.StatusNotFound {
			t.Errorf("expected 404, got %d", rec.Code)
		}
		result := parseJSONResponse(rec)
		if result["error"] != "not_found" {
			t.Errorf("expected not_found, got %v", result["error"])
		}
	})
}

// ─── Test: GET /api/v1/reports → 200, reports array ─────────────

func TestListReportsHandler(t *testing.T) {
	srv, _, cleanup := setupTest(t)
	defer cleanup()

	mux := srv.NewTestMux()

	t.Run("empty reports returns empty array", func(t *testing.T) {
		rec := doRequest(mux, "GET", "/api/v1/reports", nil, nil)
		if rec.Code != http.StatusOK {
			t.Errorf("expected 200, got %d", rec.Code)
		}
		result := parseJSONResponse(rec)
		reports, ok := result["reports"].([]interface{})
		if !ok {
			t.Errorf("expected reports to be array, got %T", result["reports"])
		}
		if len(reports) != 0 {
			t.Errorf("expected empty array, got %d elements", len(reports))
		}
	})
}

// ─── Test: invalid JSON body → 400 ──────────────────────────────

func TestInvalidJSONBody(t *testing.T) {
	srv, _, cleanup := setupTest(t)
	defer cleanup()

	mux := srv.NewTestMux()

	endpoints := []struct {
		method string
		path   string
	}{
		{"POST", "/api/v1/connect"},
		{"POST", "/api/v1/nodes/10.0.0.1/scan"},
		{"POST", "/api/v1/reports/generate"},
	}

	for _, ep := range endpoints {
		t.Run(ep.method+" "+ep.path, func(t *testing.T) {
			body := strings.NewReader("{invalid json")
			rec := doRequest(mux, ep.method, ep.path, body, map[string]string{
				"Content-Type": "application/json",
			})
			if rec.Code != http.StatusBadRequest {
				t.Errorf("%s %s: expected 400, got %d", ep.method, ep.path, rec.Code)
			}
		})
	}
}

// ─── Test: wrong Content-Type → 415 ─────────────────────────────

func TestWrongContentType(t *testing.T) {
	srv, _, cleanup := setupTest(t)
	defer cleanup()

	mux := srv.NewTestMux()

	endpoints := []struct {
		method string
		path   string
	}{
		{"POST", "/api/v1/connect"},
		{"POST", "/api/v1/nodes/10.0.0.1/scan"},
		{"POST", "/api/v1/reports/generate"},
	}

	for _, ep := range endpoints {
		t.Run(ep.method+" "+ep.path, func(t *testing.T) {
			body := jsonBody(map[string]interface{}{"test": true})
			rec := doRequest(mux, ep.method, ep.path, body, map[string]string{
				"Content-Type": "text/plain",
			})
			if rec.Code != http.StatusUnsupportedMediaType {
				t.Errorf("%s %s: expected 415, got %d", ep.method, ep.path, rec.Code)
			}
		})
	}
}

// ─── Test: method not allowed → 405 ─────────────────────────────

func TestMethodNotAllowed(t *testing.T) {
	srv, _, cleanup := setupTest(t)
	defer cleanup()

	mux := srv.NewTestMux()

	tests := []struct {
		method string
		path   string
	}{
		// GET-only endpoints with wrong method
		{"POST", "/health"},
		{"PUT", "/api/v1/nodes"},
		{"DELETE", "/api/v1/nodes/10.0.0.1"},
		{"POST", "/api/v1/nodes/10.0.0.1/fbc"},
		{"POST", "/api/v1/nodes/10.0.0.1/rpc"},
		{"PUT", "/api/v1/reports"},
		{"DELETE", "/api/v1/reports/some-id"},
		// POST-only endpoints with wrong method
		{"GET", "/api/v1/connect"},
		{"GET", "/api/v1/nodes/10.0.0.1/scan"},
	}

	for _, tt := range tests {
		t.Run(tt.method+" "+tt.path, func(t *testing.T) {
			body := jsonBody(map[string]interface{}{"test": true})
			headers := map[string]string{}
			if tt.method == "POST" || tt.method == "PUT" || tt.method == "DELETE" {
				headers["Content-Type"] = "application/json"
			}
			rec := doRequest(mux, tt.method, tt.path, body, headers)
			if rec.Code != http.StatusMethodNotAllowed {
				t.Errorf("%s %s: expected 405, got %d", tt.method, tt.path, rec.Code)
			}
		})
	}
}

// ─── Test: nil slice safety → empty arrays not null ─────────────

func TestNilSliceSafety(t *testing.T) {
	srv, _, cleanup := setupTest(t)
	defer cleanup()

	mux := srv.NewTestMux()

	t.Run("nodes empty array", func(t *testing.T) {
		rec := doRequest(mux, "GET", "/api/v1/nodes", nil, nil)
		body := rec.Body.String()
		if strings.Contains(body, `"nodes":null`) {
			t.Error("nodes should be [] not null")
		}
		if !strings.Contains(body, `"nodes":[]`) {
			t.Error("nodes should be []")
		}
	})

	t.Run("reports empty array", func(t *testing.T) {
		rec := doRequest(mux, "GET", "/api/v1/reports", nil, nil)
		body := rec.Body.String()
		if strings.Contains(body, `"reports":null`) {
			t.Error("reports should be [] not null")
		}
		if !strings.Contains(body, `"reports":[]`) {
			t.Error("reports should be []")
		}
	})
}

// ─── Test: parse sysfile handler ─────────────────────────────────

func TestParseSysfileHandler(t *testing.T) {
	srv, _, cleanup := setupTest(t)
	defer cleanup()

	mux := srv.NewTestMux()

	t.Run("missing file field", func(t *testing.T) {
		body := &bytes.Buffer{}
		writer := multipart.NewWriter(body)
		writer.Close()

		rec := doRequest(mux, "POST", "/api/v1/parse/sysfile", body, map[string]string{
			"Content-Type": writer.FormDataContentType(),
		})
		if rec.Code != http.StatusBadRequest {
			t.Errorf("expected 400, got %d", rec.Code)
		}
	})

	t.Run("valid sys file upload", func(t *testing.T) {
		// Create a temp sys file
		tmpDir := t.TempDir()
		sysPath := filepath.Join(tmpDir, "test.sys")
		os.WriteFile(sysPath, []byte(":e:hw:1a1   AL01   pxe:sys-csg2   // Main LIS node\n"), 0644)

		body := &bytes.Buffer{}
		writer := multipart.NewWriter(body)
		part, _ := writer.CreateFormFile("file", "test.sys")
		fileData, _ := os.ReadFile(sysPath)
		part.Write(fileData)
		writer.WriteField("store_nodes", "true")
		writer.Close()

		rec := doRequest(mux, "POST", "/api/v1/parse/sysfile", body, map[string]string{
			"Content-Type": writer.FormDataContentType(),
		})
		if rec.Code != http.StatusOK {
			t.Errorf("expected 200, got %d: %s", rec.Code, rec.Body.String())
		}
		result := parseJSONResponse(rec)
		if result["filename"] != "test.sys" {
			t.Errorf("expected filename test.sys, got %v", result["filename"])
		}
		entries, ok := result["entries"].([]interface{})
		if !ok || len(entries) == 0 {
			t.Errorf("expected entries array with elements, got %v", result["entries"])
		}
	})
}

// ─── Test: FBC and RPC handlers ──────────────────────────────────

func TestFBCAndRPCHandlers(t *testing.T) {
	srv, st, cleanup := setupTest(t)
	defer cleanup()

	// Create a node with IO points
	st.SaveNode(&types.Node{
		Address: "10.0.0.1",
		Name:    "test-node",
		Type:    types.ACN,
		Status:  types.StatusConnected,
		Port:    23,
	})
	st.SaveIOPoints("10.0.0.1", []types.IOPoint{
		{NodeAddress: "10.0.0.1", ModulePosition: 0, ChannelPosition: 5, ChannelType: types.AI8, ModuleType: types.ModuleFBC},
		{NodeAddress: "10.0.0.1", ModulePosition: 0, ChannelPosition: 6, ChannelType: types.BI8, ModuleType: types.ModuleFBC},
		{NodeAddress: "10.0.0.1", ModulePosition: 0, ChannelPosition: 0, CounterName: "5", CounterValue: 12, ModuleType: types.ModuleRPC},
	})

	mux := srv.NewTestMux()

	t.Run("GET /api/v1/nodes/{addr}/fbc returns 200", func(t *testing.T) {
		rec := doRequest(mux, "GET", "/api/v1/nodes/10.0.0.1/fbc", nil, nil)
		if rec.Code != http.StatusOK {
			t.Errorf("expected 200, got %d: %s", rec.Code, rec.Body.String())
		}
		result := parseJSONResponse(rec)
		modules, ok := result["fbc_modules"].([]interface{})
		if !ok || len(modules) == 0 {
			t.Errorf("expected fbc_modules array with elements, got %v", result["fbc_modules"])
		}
	})

	t.Run("GET /api/v1/nodes/{addr}/rpc returns 200", func(t *testing.T) {
		rec := doRequest(mux, "GET", "/api/v1/nodes/10.0.0.1/rpc", nil, nil)
		if rec.Code != http.StatusOK {
			t.Errorf("expected 200, got %d: %s", rec.Code, rec.Body.String())
		}
		result := parseJSONResponse(rec)
		modules, ok := result["rpc_modules"].([]interface{})
		if !ok || len(modules) == 0 {
			t.Errorf("expected rpc_modules array with elements, got %v", result["rpc_modules"])
		}
	})

	t.Run("GET /api/v1/nodes/{addr}/fbc with no data returns 404", func(t *testing.T) {
		rec := doRequest(mux, "GET", "/api/v1/nodes/10.0.0.99/fbc", nil, nil)
		if rec.Code != http.StatusNotFound {
			t.Errorf("expected 404, got %d", rec.Code)
		}
	})

	t.Run("GET /api/v1/nodes/{addr}/rpc with no data returns 404", func(t *testing.T) {
		rec := doRequest(mux, "GET", "/api/v1/nodes/10.0.0.99/rpc", nil, nil)
		if rec.Code != http.StatusNotFound {
			t.Errorf("expected 404, got %d", rec.Code)
		}
	})
}

// ─── Test: scan handler validation ───────────────────────────────

func TestScanHandlerValidation(t *testing.T) {
	srv, st, cleanup := setupTest(t)
	defer cleanup()

	// Create a disconnected node
	st.SaveNode(&types.Node{
		Address: "10.0.0.1",
		Name:    "test-node",
		Type:    types.ACN,
		Status:  types.StatusDisconnected,
		Port:    23,
	})

	mux := srv.NewTestMux()

	t.Run("scan disconnected node returns 409", func(t *testing.T) {
		body := jsonBody(map[string]interface{}{
			"modules": []string{"fbc"},
			"token":   "162",
		})
		rec := doRequest(mux, "POST", "/api/v1/nodes/10.0.0.1/scan", body, map[string]string{
			"Content-Type": "application/json",
		})
		if rec.Code != http.StatusConflict {
			t.Errorf("expected 409, got %d: %s", rec.Code, rec.Body.String())
		}
		result := parseJSONResponse(rec)
		if result["error"] != "node_not_connected" {
			t.Errorf("expected node_not_connected, got %v", result["error"])
		}
	})

	t.Run("scan non-existent node returns 404", func(t *testing.T) {
		body := jsonBody(map[string]interface{}{
			"modules": []string{"fbc"},
		})
		rec := doRequest(mux, "POST", "/api/v1/nodes/10.0.0.99/scan", body, map[string]string{
			"Content-Type": "application/json",
		})
		if rec.Code != http.StatusNotFound {
			t.Errorf("expected 404, got %d", rec.Code)
		}
	})
}

// ─── Test: health handler with degraded DB ──────────────────────

func TestHealthHandlerDegraded(t *testing.T) {
	// Create a server with a store, then close the DB to simulate degradation
	st, err := store.Open(":memory:")
	if err != nil {
		t.Fatalf("failed to open store: %v", err)
	}

	cfg := &server.Config{
		Port:       0,
		DBPath:     ":memory:",
		LogLevel:   "debug",
		CORSOrigin: "*",
	}
	srv := NewServer(st, cfg)

	// Close DB to trigger degraded status
	st.Close()

	mux := srv.NewTestMux()
	rec := doRequest(mux, "GET", "/health", nil, nil)

	if rec.Code != http.StatusOK {
		t.Errorf("expected 200, got %d", rec.Code)
	}
	result := parseJSONResponse(rec)
	if result["status"] != "degraded" {
		t.Errorf("expected status 'degraded', got %v", result["status"])
	}
	if result["db_status"] == "connected" {
		t.Error("expected db_status not 'connected' after DB close")
	}
}
