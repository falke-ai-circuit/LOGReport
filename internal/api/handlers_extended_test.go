package api

import (
	"bytes"
	"context"
	"embed"
	"encoding/json"
	"mime/multipart"
	"net/http"
	"net/http/httptest"
	"os"
	"strings"
	"testing"
	"time"

	"github.com/falke-ai-circuit/LOGReport/internal/bstool"
	"github.com/falke-ai-circuit/LOGReport/internal/server"
	"github.com/falke-ai-circuit/LOGReport/internal/store"
	"github.com/falke-ai-circuit/LOGReport/internal/types"
)

// TestLoggingMiddleware verifies that loggingMiddleware wraps requests and logs.
func TestLoggingMiddleware(t *testing.T) {
	handler := http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusOK)
		w.Write([]byte("ok"))
	})

	wrapped := loggingMiddleware(handler)

	req := httptest.NewRequest("GET", "/test", nil)
	rec := httptest.NewRecorder()
	wrapped.ServeHTTP(rec, req)

	if rec.Code != http.StatusOK {
		t.Errorf("expected 200, got %d", rec.Code)
	}
	if rec.Body.String() != "ok" {
		t.Errorf("expected body 'ok', got %q", rec.Body.String())
	}
}

// TestLoggingMiddlewareErrorStatus verifies logging captures error status codes.
func TestLoggingMiddlewareErrorStatus(t *testing.T) {
	handler := http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusInternalServerError)
	})

	wrapped := loggingMiddleware(handler)

	req := httptest.NewRequest("POST", "/api/test", nil)
	rec := httptest.NewRecorder()
	wrapped.ServeHTTP(rec, req)

	if rec.Code != http.StatusInternalServerError {
		t.Errorf("expected 500, got %d", rec.Code)
	}
}

// TestLoggingResponseWriterWriteHeader verifies status code capture.
func TestLoggingResponseWriterWriteHeader(t *testing.T) {
	base := httptest.NewRecorder()
	lrw := &loggingResponseWriter{
		ResponseWriter: base,
		statusCode:     http.StatusOK,
	}

	lrw.WriteHeader(http.StatusNotFound)

	if lrw.statusCode != http.StatusNotFound {
		t.Errorf("expected statusCode 404, got %d", lrw.statusCode)
	}
	if base.Code != http.StatusNotFound {
		t.Errorf("expected base code 404, got %d", base.Code)
	}
}

// TestCorsMiddlewareWithOrigin verifies CORS headers are added when origin is set.
func TestCorsMiddlewareWithOrigin(t *testing.T) {
	handler := http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusOK)
	})

	wrapped := corsMiddleware("http://localhost:3000")(handler)

	req := httptest.NewRequest("GET", "/api/test", nil)
	rec := httptest.NewRecorder()
	wrapped.ServeHTTP(rec, req)

	if rec.Code != http.StatusOK {
		t.Errorf("expected 200, got %d", rec.Code)
	}
	if rec.Header().Get("Access-Control-Allow-Origin") != "http://localhost:3000" {
		t.Errorf("expected CORS origin, got %q", rec.Header().Get("Access-Control-Allow-Origin"))
	}
	if rec.Header().Get("Access-Control-Allow-Methods") == "" {
		t.Error("expected Access-Control-Allow-Methods header")
	}
	if rec.Header().Get("Access-Control-Allow-Headers") == "" {
		t.Error("expected Access-Control-Allow-Headers header")
	}
}

// TestCorsMiddlewarePreflight verifies OPTIONS preflight handling.
func TestCorsMiddlewarePreflight(t *testing.T) {
	handler := http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		t.Error("handler should not be called for preflight")
	})

	wrapped := corsMiddleware("*")(handler)

	req := httptest.NewRequest("OPTIONS", "/api/test", nil)
	rec := httptest.NewRecorder()
	wrapped.ServeHTTP(rec, req)

	if rec.Code != http.StatusNoContent {
		t.Errorf("expected 204 for preflight, got %d", rec.Code)
	}
}

// TestCorsMiddlewareNoOrigin verifies CORS is disabled when origin is empty.
func TestCorsMiddlewareNoOrigin(t *testing.T) {
	handler := http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusOK)
	})

	wrapped := corsMiddleware("")(handler)

	req := httptest.NewRequest("GET", "/api/test", nil)
	rec := httptest.NewRecorder()
	wrapped.ServeHTTP(rec, req)

	if rec.Code != http.StatusOK {
		t.Errorf("expected 200, got %d", rec.Code)
	}
	if rec.Header().Get("Access-Control-Allow-Origin") != "" {
		t.Errorf("expected no CORS header, got %q", rec.Header().Get("Access-Control-Allow-Origin"))
	}
}

// TestContentTypeMiddlewareJSON verifies JSON content type passes through.
func TestContentTypeMiddlewareJSON(t *testing.T) {
	handler := http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusOK)
	})

	wrapped := contentTypeMiddleware(handler)

	req := httptest.NewRequest("POST", "/api/test", strings.NewReader("{}"))
	req.Header.Set("Content-Type", "application/json")
	rec := httptest.NewRecorder()
	wrapped.ServeHTTP(rec, req)

	if rec.Code != http.StatusOK {
		t.Errorf("expected 200, got %d", rec.Code)
	}
}

// TestContentTypeMiddlewareMultipart verifies multipart passes through.
func TestContentTypeMiddlewareMultipart(t *testing.T) {
	handler := http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusOK)
	})

	wrapped := contentTypeMiddleware(handler)

	req := httptest.NewRequest("POST", "/api/v1/parse/sysfile", strings.NewReader("data"))
	req.Header.Set("Content-Type", "multipart/form-data; boundary=something")
	rec := httptest.NewRecorder()
	wrapped.ServeHTTP(rec, req)

	if rec.Code != http.StatusOK {
		t.Errorf("expected 200, got %d", rec.Code)
	}
}

// TestContentTypeMiddlewareWrongType verifies wrong content type returns 415.
func TestContentTypeMiddlewareWrongType(t *testing.T) {
	handler := http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		t.Error("handler should not be called for wrong content type")
	})

	wrapped := contentTypeMiddleware(handler)

	req := httptest.NewRequest("POST", "/api/test", strings.NewReader("data"))
	req.Header.Set("Content-Type", "text/plain")
	rec := httptest.NewRecorder()
	wrapped.ServeHTTP(rec, req)

	if rec.Code != http.StatusUnsupportedMediaType {
		t.Errorf("expected 415, got %d", rec.Code)
	}
}

// TestContentTypeMiddlewareGETPassthrough verifies GET requests skip content type check.
func TestContentTypeMiddlewareGETPassthrough(t *testing.T) {
	handler := http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusOK)
	})

	wrapped := contentTypeMiddleware(handler)

	req := httptest.NewRequest("GET", "/api/test", nil)
	// No Content-Type header at all
	rec := httptest.NewRecorder()
	wrapped.ServeHTTP(rec, req)

	if rec.Code != http.StatusOK {
		t.Errorf("expected 200, got %d", rec.Code)
	}
}

// TestContentTypeMiddlewarePUTWrongType verifies PUT with wrong type returns 415.
func TestContentTypeMiddlewarePUTWrongType(t *testing.T) {
	handler := http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		t.Error("handler should not be called for wrong content type")
	})

	wrapped := contentTypeMiddleware(handler)

	req := httptest.NewRequest("PUT", "/api/test", strings.NewReader("data"))
	req.Header.Set("Content-Type", "text/html")
	rec := httptest.NewRecorder()
	wrapped.ServeHTTP(rec, req)

	if rec.Code != http.StatusUnsupportedMediaType {
		t.Errorf("expected 415, got %d", rec.Code)
	}
}

// TestContentTypeMiddlewarePATCHWrongType verifies PATCH with wrong type returns 415.
func TestContentTypeMiddlewarePATCHWrongType(t *testing.T) {
	handler := http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		t.Error("handler should not be called for wrong content type")
	})

	wrapped := contentTypeMiddleware(handler)

	req := httptest.NewRequest("PATCH", "/api/test", strings.NewReader("data"))
	req.Header.Set("Content-Type", "text/xml")
	rec := httptest.NewRecorder()
	wrapped.ServeHTTP(rec, req)

	if rec.Code != http.StatusUnsupportedMediaType {
		t.Errorf("expected 415, got %d", rec.Code)
	}
}

// TestCondHelper verifies the cond helper function.
func TestCondHelper(t *testing.T) {
	if cond(true, "a", "b") != "a" {
		t.Error("cond(true, a, b) should return a")
	}
	if cond(false, "a", "b") != "b" {
		t.Error("cond(false, a, b) should return b")
	}
}

// TestWriteJSON verifies writeJSON sets correct headers and body.
func TestWriteJSON(t *testing.T) {
	rec := httptest.NewRecorder()
	writeJSON(rec, http.StatusOK, map[string]string{"key": "value"})

	if rec.Code != http.StatusOK {
		t.Errorf("expected 200, got %d", rec.Code)
	}
	if ct := rec.Header().Get("Content-Type"); !strings.Contains(ct, "application/json") {
		t.Errorf("expected application/json content type, got %q", ct)
	}
	if !strings.Contains(rec.Body.String(), `"key"`) {
		t.Errorf("expected body to contain key, got %q", rec.Body.String())
	}
	if !strings.Contains(rec.Body.String(), `"value"`) {
		t.Errorf("expected body to contain value, got %q", rec.Body.String())
	}
}

// TestWriteError verifies writeError produces correct error response.
func TestWriteError(t *testing.T) {
	rec := httptest.NewRecorder()
	writeError(rec, http.StatusBadRequest, "validation_error", "field is required")

	if rec.Code != http.StatusBadRequest {
		t.Errorf("expected 400, got %d", rec.Code)
	}

	var result map[string]interface{}
	json.Unmarshal(rec.Body.Bytes(), &result)
	if result["error"] != "validation_error" {
		t.Errorf("expected error 'validation_error', got %v", result["error"])
	}
	if result["message"] != "field is required" {
		t.Errorf("expected message 'field is required', got %v", result["message"])
	}
}

// TestWriteErrorDetails verifies writeErrorDetails includes details.
func TestWriteErrorDetails(t *testing.T) {
	rec := httptest.NewRecorder()
	writeErrorDetails(rec, http.StatusConflict, "node_not_connected", "node is not connected",
		map[string]string{"node_status": "disconnected"})

	if rec.Code != http.StatusConflict {
		t.Errorf("expected 409, got %d", rec.Code)
	}

	var result map[string]interface{}
	json.Unmarshal(rec.Body.Bytes(), &result)
	if result["error"] != "node_not_connected" {
		t.Errorf("expected error 'node_not_connected', got %v", result["error"])
	}
	details, ok := result["details"].(map[string]interface{})
	if !ok {
		t.Fatalf("expected details map, got %T", result["details"])
	}
	if details["node_status"] != "disconnected" {
		t.Errorf("expected node_status 'disconnected', got %v", details["node_status"])
	}
}

// TestWriteErrorDetailsNilDetails verifies nil details are omitted.
func TestWriteErrorDetailsNilDetails(t *testing.T) {
	rec := httptest.NewRecorder()
	writeErrorDetails(rec, http.StatusBadRequest, "validation_error", "bad input", nil)

	var result map[string]interface{}
	json.Unmarshal(rec.Body.Bytes(), &result)
	if _, ok := result["details"]; ok {
		t.Error("details should be omitted when nil")
	}
}

// TestNodeToAPI verifies nodeToAPI conversion.
func TestNodeToAPI(t *testing.T) {
	now := time.Now()
	n := &types.Node{
		Address:  "10.0.0.1",
		Name:     "test-node",
		Type:     types.ACN,
		Status:   types.StatusConnected,
		TokenID:  "162",
		Port:     23,
		LastSeen: now,
	}

	api := nodeToAPI(n)

	if api.Address != "10.0.0.1" {
		t.Errorf("Address: got %q, want 10.0.0.1", api.Address)
	}
	if api.Name != "test-node" {
		t.Errorf("Name: got %q, want test-node", api.Name)
	}
	if api.NodeType != "ACN" {
		t.Errorf("NodeType: got %q, want ACN", api.NodeType)
	}
	if api.Status != "connected" {
		t.Errorf("Status: got %q, want connected", api.Status)
	}
	if api.Token != "162" {
		t.Errorf("Token: got %q, want 162", api.Token)
	}
	if api.Port != 23 {
		t.Errorf("Port: got %d, want 23", api.Port)
	}
	if api.LastConnected == "" {
		t.Error("LastConnected should not be empty when LastSeen is set")
	}
}

// TestNodeToAPIZeroLastSeen verifies nodeToAPI with zero LastSeen.
func TestNodeToAPIZeroLastSeen(t *testing.T) {
	n := &types.Node{
		Address: "10.0.0.1",
		Name:    "test-node",
		Type:    types.ACN,
		Status:  types.StatusUnknown,
		Port:    23,
	}

	api := nodeToAPI(n)

	if api.LastConnected != "" {
		t.Errorf("LastConnected should be empty when LastSeen is zero, got %q", api.LastConnected)
	}
}

// TestReportToAPI verifies reportToAPI conversion.
func TestReportToAPI(t *testing.T) {
	r := &types.Report{
		ID:          "rpt-001",
		NodeAddress: "10.0.0.1",
		Format:      types.FormatDOCX,
		Template:    "default",
		Status:      types.StatusCompleted,
		FilePath:    "",
		CreatedAt:   "2026-06-15T10:00:00Z",
		CompletedAt: "2026-06-15T10:05:00Z",
	}

	api := reportToAPI(r)

	if api.ReportID != "rpt-001" {
		t.Errorf("ReportID: got %q, want rpt-001", api.ReportID)
	}
	if api.Status != "completed" {
		t.Errorf("Status: got %q, want completed", api.Status)
	}
	if api.Format != "docx" {
		t.Errorf("Format: got %q, want docx", api.Format)
	}
	if api.Template != "default" {
		t.Errorf("Template: got %q, want default", api.Template)
	}
	if len(api.NodeAddresses) != 1 || api.NodeAddresses[0] != "10.0.0.1" {
		t.Errorf("NodeAddresses: got %v, want [10.0.0.1]", api.NodeAddresses)
	}
	if api.FileSize != nil {
		t.Error("FileSize should be nil when FilePath is empty")
	}
}

// TestReportToAPIWithFile verifies reportToAPI includes file size when file exists.
func TestReportToAPIWithFile(t *testing.T) {
	// Create a temp file
	tmpDir := t.TempDir()
	tmpFile := tmpDir + "/test-report.docx"
	os.WriteFile(tmpFile, []byte("test content"), 0644)

	r := &types.Report{
		ID:          "rpt-002",
		NodeAddress: "10.0.0.1",
		Format:      types.FormatDOCX,
		Status:      types.StatusCompleted,
		FilePath:    tmpFile,
		CreatedAt:   "2026-06-15T10:00:00Z",
	}

	api := reportToAPI(r)

	if api.FileSize == nil {
		t.Error("FileSize should not be nil when file exists")
	}
	if *api.FileSize != 12 {
		t.Errorf("FileSize: got %d, want 12", *api.FileSize)
	}
}

// TestNewServer verifies NewServer initializes correctly.
func TestNewServer(t *testing.T) {
	st, err := store.Open(":memory:")
	if err != nil {
		t.Fatalf("Open: %v", err)
	}
	defer st.Close()

	cfg := &server.Config{
		Port:       8080,
		DBPath:     ":memory:",
		LogLevel:   "info",
		CORSOrigin: "*",
	}

	srv := NewServer(st, cfg, embed.FS{}, bstool.NewClient())

	if srv.Store() != st {
		t.Error("Store() should return the store passed to NewServer")
	}
	if srv.StartTime().IsZero() {
		t.Error("StartTime() should not be zero")
	}
}

// TestNewTestServer verifies NewTestServer creates a valid test server.
func TestNewTestServer(t *testing.T) {
	srv, st, err := NewTestServer()
	if err != nil {
		t.Fatalf("NewTestServer: %v", err)
	}
	defer st.Close()

	if srv == nil {
		t.Fatal("NewTestServer returned nil server")
	}
	if st == nil {
		t.Fatal("NewTestServer returned nil store")
	}

	// Verify store is functional
	nodes, err := st.ListNodes()
	if err != nil {
		t.Fatalf("ListNodes: %v", err)
	}
	if nodes == nil {
		t.Error("ListNodes returned nil")
	}
}

// TestNewTestMux verifies NewTestMux creates a valid mux with routes.
func TestNewTestMux(t *testing.T) {
	srv, _, cleanup := setupTest(t)
	defer cleanup()

	mux := srv.NewTestMux()

	// Test health endpoint
	req := httptest.NewRequest("GET", "/health", nil)
	rec := httptest.NewRecorder()
	mux.ServeHTTP(rec, req)

	if rec.Code != http.StatusOK {
		t.Errorf("health: expected 200, got %d", rec.Code)
	}
}

// TestShutdown verifies Shutdown doesn't panic.
func TestShutdown(t *testing.T) {
	srv, _, cleanup := setupTest(t)
	defer cleanup()

	ctx := context.Background()
	if err := srv.Shutdown(ctx); err != nil {
		t.Errorf("Shutdown: unexpected error: %v", err)
	}
}

// TestGetFBCHandlerNoData verifies FBC handler returns 404 when no FBC data.
func TestGetFBCHandlerNoData(t *testing.T) {
	srv, st, cleanup := setupTest(t)
	defer cleanup()

	// Create a node without FBC data
	st.SaveNode(&types.Node{
		Address: "10.0.0.1",
		Name:    "test-node",
		Type:    types.ACN,
		Status:  types.StatusConnected,
		Port:    23,
	})
	// Add only RPC data
	st.SaveIOPoints("10.0.0.1", []types.IOPoint{
		{NodeAddress: "10.0.0.1", ModulePosition: 0, ChannelPosition: 0, CounterName: "ERR_TX", CounterValue: 5, ModuleType: types.ModuleRPC},
	})

	mux := srv.NewTestMux()
	rec := doRequest(mux, "GET", "/api/v1/nodes/10.0.0.1/fbc", nil, nil)

	if rec.Code != http.StatusNotFound {
		t.Errorf("expected 404 for no FBC data, got %d: %s", rec.Code, rec.Body.String())
	}
}

// TestGetRPCHandlerNoData verifies RPC handler returns 404 when no RPC data.
func TestGetRPCHandlerNoData(t *testing.T) {
	srv, st, cleanup := setupTest(t)
	defer cleanup()

	// Create a node without RPC data
	st.SaveNode(&types.Node{
		Address: "10.0.0.1",
		Name:    "test-node",
		Type:    types.ACN,
		Status:  types.StatusConnected,
		Port:    23,
	})
	// Add only FBC data
	st.SaveIOPoints("10.0.0.1", []types.IOPoint{
		{NodeAddress: "10.0.0.1", ModulePosition: 0, ChannelPosition: 5, ChannelType: types.AI8, ModuleType: types.ModuleFBC},
	})

	mux := srv.NewTestMux()
	rec := doRequest(mux, "GET", "/api/v1/nodes/10.0.0.1/rpc", nil, nil)

	if rec.Code != http.StatusNotFound {
		t.Errorf("expected 404 for no RPC data, got %d: %s", rec.Code, rec.Body.String())
	}
}

// TestGetNodeHandlerWithIO verifies getNodeHandler includes IO summary.
func TestGetNodeHandlerWithIO(t *testing.T) {
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
		{NodeAddress: "10.0.0.1", ModulePosition: 0, ChannelPosition: 6, ChannelType: types.BI8, ModuleType: types.ModuleFBC},
		{NodeAddress: "10.0.0.1", ModulePosition: 0, ChannelPosition: 0, CounterName: "ERR_TX", CounterValue: 5, ModuleType: types.ModuleRPC},
	})

	mux := srv.NewTestMux()
	rec := doRequest(mux, "GET", "/api/v1/nodes/10.0.0.1", nil, nil)

	if rec.Code != http.StatusOK {
		t.Errorf("expected 200, got %d: %s", rec.Code, rec.Body.String())
	}

	result := parseJSONResponse(rec)
	ioSummary, ok := result["io_summary"].(map[string]interface{})
	if !ok {
		t.Fatalf("expected io_summary map, got %T", result["io_summary"])
	}
	fbcMods, ok := ioSummary["fbc_modules"].(float64)
	if !ok || fbcMods != 2 {
		t.Errorf("expected fbc_modules 2, got %v", ioSummary["fbc_modules"])
	}
	rpcMods, ok := ioSummary["rpc_modules"].(float64)
	if !ok || rpcMods != 1 {
		t.Errorf("expected rpc_modules 1, got %v", ioSummary["rpc_modules"])
	}
}

// TestGetReportHandlerPending verifies getReportHandler returns 409 for pending reports.
func TestGetReportHandlerPending(t *testing.T) {
	srv, st, cleanup := setupTest(t)
	defer cleanup()

	st.SaveReport(&types.Report{
		ID:          "rpt-pending",
		NodeAddress: "10.0.0.1",
		Format:      types.FormatDOCX,
		Status:      types.StatusPending,
		CreatedAt:   "2026-06-15T10:00:00Z",
	})

	mux := srv.NewTestMux()
	rec := doRequest(mux, "GET", "/api/v1/reports/rpt-pending", nil, nil)

	if rec.Code != http.StatusConflict {
		t.Errorf("expected 409 for pending report, got %d: %s", rec.Code, rec.Body.String())
	}
}

// TestGetReportHandlerGenerating verifies getReportHandler returns 409 for generating reports.
func TestGetReportHandlerGenerating(t *testing.T) {
	srv, st, cleanup := setupTest(t)
	defer cleanup()

	st.SaveReport(&types.Report{
		ID:          "rpt-generating",
		NodeAddress: "10.0.0.1",
		Format:      types.FormatDOCX,
		Status:      types.StatusGenerating,
		CreatedAt:   "2026-06-15T10:00:00Z",
	})

	mux := srv.NewTestMux()
	rec := doRequest(mux, "GET", "/api/v1/reports/rpt-generating", nil, nil)

	if rec.Code != http.StatusConflict {
		t.Errorf("expected 409 for generating report, got %d: %s", rec.Code, rec.Body.String())
	}
}

// TestGetReportHandlerFailed verifies getReportHandler returns 410 for failed reports.
func TestGetReportHandlerFailed(t *testing.T) {
	srv, st, cleanup := setupTest(t)
	defer cleanup()

	st.SaveReport(&types.Report{
		ID:          "rpt-failed",
		NodeAddress: "10.0.0.1",
		Format:      types.FormatDOCX,
		Status:      types.StatusFailed,
		CreatedAt:   "2026-06-15T10:00:00Z",
	})

	mux := srv.NewTestMux()
	rec := doRequest(mux, "GET", "/api/v1/reports/rpt-failed", nil, nil)

	if rec.Code != http.StatusGone {
		t.Errorf("expected 410 for failed report, got %d: %s", rec.Code, rec.Body.String())
	}
}

// TestGetReportHandlerFileDownload verifies getReportHandler serves file when available.
func TestGetReportHandlerFileDownload(t *testing.T) {
	srv, st, cleanup := setupTest(t)
	defer cleanup()

	// Create a temp file
	tmpDir := t.TempDir()
	tmpFile := tmpDir + "/test-report.json"
	os.WriteFile(tmpFile, []byte(`{"test": true}`), 0644)

	st.SaveReport(&types.Report{
		ID:          "rpt-file",
		NodeAddress: "10.0.0.1",
		Format:      types.FormatJSON,
		Status:      types.StatusCompleted,
		FilePath:    tmpFile,
		CreatedAt:   "2026-06-15T10:00:00Z",
	})

	mux := srv.NewTestMux()
	rec := doRequest(mux, "GET", "/api/v1/reports/rpt-file", nil, nil)

	if rec.Code != http.StatusOK {
		t.Errorf("expected 200, got %d: %s", rec.Code, rec.Body.String())
	}
	// Should serve the file content
	if !strings.Contains(rec.Body.String(), `"test"`) {
		t.Errorf("expected file content in response, got %q", rec.Body.String())
	}
	// Should have Content-Disposition header
	if rec.Header().Get("Content-Disposition") == "" {
		t.Error("expected Content-Disposition header")
	}
}

// TestGenerateReportHandlerWildcard verifies "*" wildcard generates for all nodes.
func TestGenerateReportHandlerWildcard(t *testing.T) {
	srv, st, cleanup := setupTest(t)
	defer cleanup()

	// Create nodes with IO points
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
		Status:  types.StatusConnected,
		Port:    23,
	})
	st.SaveIOPoints("10.0.0.1", []types.IOPoint{
		{NodeAddress: "10.0.0.1", ModulePosition: 0, ChannelPosition: 5, ChannelType: types.AI8, ModuleType: types.ModuleFBC},
	})
	st.SaveIOPoints("10.0.0.2", []types.IOPoint{
		{NodeAddress: "10.0.0.2", ModulePosition: 0, ChannelPosition: 5, ChannelType: types.AI8, ModuleType: types.ModuleFBC},
	})
	// Create a default template
	st.SaveTemplate(&types.Template{
		Name:    "default",
		Format:  "docx",
		Content: "LOGReport — Node Report",
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
		t.Errorf("expected 200, got %d: %s", rec.Code, rec.Body.String())
	}

	result := parseJSONResponse(rec)
	// Should have multiple reports
	reports, ok := result["reports"].([]interface{})
	if !ok {
		t.Errorf("expected reports array, got %T", result["reports"])
	}
	if len(reports) != 2 {
		t.Errorf("expected 2 reports for wildcard, got %d", len(reports))
	}
}

// TestGenerateReportHandlerWildcardNoData verifies wildcard with no scan data returns 400.
func TestGenerateReportHandlerWildcardNoData(t *testing.T) {
	srv, st, cleanup := setupTest(t)
	defer cleanup()

	// Create nodes without IO points
	st.SaveNode(&types.Node{
		Address: "10.0.0.1",
		Name:    "node1",
		Type:    types.ACN,
		Status:  types.StatusConnected,
		Port:    23,
	})

	mux := srv.NewTestMux()
	body := jsonBody(map[string]interface{}{
		"node_addresses": []string{"*"},
		"format":         "json",
	})
	rec := doRequest(mux, "POST", "/api/v1/reports/generate", body, map[string]string{
		"Content-Type": "application/json",
	})

	if rec.Code != http.StatusBadRequest {
		t.Errorf("expected 400, got %d: %s", rec.Code, rec.Body.String())
	}
}

// TestListReportsHandlerWithData verifies list reports returns reports when they exist.
func TestListReportsHandlerWithData(t *testing.T) {
	srv, st, cleanup := setupTest(t)
	defer cleanup()

	st.SaveReport(&types.Report{
		ID:          "rpt-001",
		NodeAddress: "10.0.0.1",
		Format:      types.FormatDOCX,
		Status:      types.StatusCompleted,
		CreatedAt:   "2026-06-15T10:00:00Z",
	})
	st.SaveReport(&types.Report{
		ID:          "rpt-002",
		NodeAddress: "10.0.0.2",
		Format:      types.FormatJSON,
		Status:      types.StatusPending,
		CreatedAt:   "2026-06-15T11:00:00Z",
	})

	mux := srv.NewTestMux()
	rec := doRequest(mux, "GET", "/api/v1/reports", nil, nil)

	if rec.Code != http.StatusOK {
		t.Errorf("expected 200, got %d", rec.Code)
	}

	result := parseJSONResponse(rec)
	reports, ok := result["reports"].([]interface{})
	if !ok {
		t.Errorf("expected reports array, got %T", result["reports"])
	}
	if len(reports) != 2 {
		t.Errorf("expected 2 reports, got %d", len(reports))
	}
	total, ok := result["total"].(float64)
	if !ok || total != 2 {
		t.Errorf("expected total 2, got %v", result["total"])
	}
}

// TestParseSysfileHandlerStoreNodes verifies store_nodes=true creates nodes.
func TestParseSysfileHandlerStoreNodes(t *testing.T) {
	srv, st, cleanup := setupTest(t)
	defer cleanup()

	// Create a temp sys file
	tmpDir := t.TempDir()
	sysPath := tmpDir + "/test.sys"
	os.WriteFile(sysPath, []byte(":e:hw:1a1   AL01   pxe:sys-csg2   // Main LIS node\n:e:hw:1e1   AP01   pxe:sys-csg2   // PCS node\n"), 0644)

	body := &bytes.Buffer{}
	writer := multipart.NewWriter(body)
	part, _ := writer.CreateFormFile("file", "test.sys")
	fileData, _ := os.ReadFile(sysPath)
	part.Write(fileData)
	writer.WriteField("store_nodes", "true")
	writer.Close()

	mux := srv.NewTestMux()
	rec := doRequest(mux, "POST", "/api/v1/parse/sysfile", body, map[string]string{
		"Content-Type": writer.FormDataContentType(),
	})

	if rec.Code != http.StatusOK {
		t.Errorf("expected 200, got %d: %s", rec.Code, rec.Body.String())
	}

	result := parseJSONResponse(rec)
	nodesCreated, ok := result["nodes_created"].(float64)
	if !ok || nodesCreated < 1 {
		t.Errorf("expected nodes_created >= 1, got %v", result["nodes_created"])
	}

	// Verify nodes were actually stored
	nodes, err := st.ListNodes()
	if err != nil {
		t.Fatalf("ListNodes: %v", err)
	}
	if len(nodes) < 2 {
		t.Errorf("expected at least 2 nodes stored, got %d", len(nodes))
	}
}

// TestParseSysfileHandlerInvalidFile verifies parse error handling.
// Note: the parser is lenient and may parse non-sysfile content without error.
func TestParseSysfileHandlerInvalidFile(t *testing.T) {
	srv, _, cleanup := setupTest(t)
	defer cleanup()

	body := &bytes.Buffer{}
	writer := multipart.NewWriter(body)
	part, _ := writer.CreateFormFile("file", "bad.sys")
	part.Write([]byte("not a valid sys file content"))
	writer.Close()

	mux := srv.NewTestMux()
	rec := doRequest(mux, "POST", "/api/v1/parse/sysfile", body, map[string]string{
		"Content-Type": writer.FormDataContentType(),
	})

	// The parser may parse arbitrary text without error; it just returns empty entries.
	// This test verifies the handler doesn't crash on unexpected input.
	if rec.Code != http.StatusOK && rec.Code != http.StatusBadRequest {
		t.Errorf("expected 200 or 400, got %d: %s", rec.Code, rec.Body.String())
	}
}

// TestScanHandlerNoToken verifies scan fails when no token available.
func TestScanHandlerNoToken(t *testing.T) {
	srv, st, cleanup := setupTest(t)
	defer cleanup()

	// Create a connected node without token
	st.SaveNode(&types.Node{
		Address: "10.0.0.1",
		Name:    "test-node",
		Type:    types.ACN,
		Status:  types.StatusConnected,
		Port:    23,
		// No TokenID
	})

	mux := srv.NewTestMux()
	body := jsonBody(map[string]interface{}{
		"modules": []string{"fbc"},
	})
	rec := doRequest(mux, "POST", "/api/v1/nodes/10.0.0.1/scan", body, map[string]string{
		"Content-Type": "application/json",
	})

	if rec.Code != http.StatusBadRequest {
		t.Errorf("expected 400 for missing token, got %d: %s", rec.Code, rec.Body.String())
	}
}

// TestGetFBCHandlerMissingAddr verifies FBC handler behavior with empty addr.
// Go 1.22+ mux redirects // to /, so we test with a path that won't match the route.
func TestGetFBCHandlerMissingAddr(t *testing.T) {
	srv, _, cleanup := setupTest(t)
	defer cleanup()

	mux := srv.NewTestMux()
	// Use a path without addr parameter — mux redirects double-slash
	rec := doRequest(mux, "GET", "/api/v1/nodes//fbc", nil, nil)

	// Go 1.22+ mux redirects // to single / (301) or returns 404
	if rec.Code != http.StatusBadRequest && rec.Code != http.StatusMovedPermanently && rec.Code != http.StatusNotFound {
		t.Errorf("expected 400/301/404, got %d", rec.Code)
	}
}

// TestGetRPCHandlerMissingAddr verifies RPC handler behavior with empty addr.
// Go 1.22+ mux redirects // to /.
func TestGetRPCHandlerMissingAddr(t *testing.T) {
	srv, _, cleanup := setupTest(t)
	defer cleanup()

	mux := srv.NewTestMux()
	rec := doRequest(mux, "GET", "/api/v1/nodes//rpc", nil, nil)

	// Go 1.22+ mux redirects // to single / (301) or returns 404
	if rec.Code != http.StatusBadRequest && rec.Code != http.StatusMovedPermanently && rec.Code != http.StatusNotFound {
		t.Errorf("expected 400/301/404, got %d", rec.Code)
	}
}

// TestGetNodeHandlerMissingAddr verifies getNodeHandler behavior with empty addr.
// Go 1.22+ mux returns 404 for paths that don't match the pattern.
func TestGetNodeHandlerMissingAddr(t *testing.T) {
	srv, _, cleanup := setupTest(t)
	defer cleanup()

	mux := srv.NewTestMux()
	rec := doRequest(mux, "GET", "/api/v1/nodes/", nil, nil)

	// Go 1.22+ mux: /api/v1/nodes/ doesn't match /api/v1/nodes/{addr} pattern
	// because {addr} requires a non-empty value. Returns 404.
	if rec.Code != http.StatusBadRequest && rec.Code != http.StatusNotFound {
		t.Errorf("expected 400 or 404, got %d", rec.Code)
	}
}

// TestScanHandlerMissingAddr verifies scan handler behavior with empty addr.
// Go 1.22+ mux redirects // to /.
func TestScanHandlerMissingAddr(t *testing.T) {
	srv, _, cleanup := setupTest(t)
	defer cleanup()

	mux := srv.NewTestMux()
	body := jsonBody(map[string]interface{}{
		"modules": []string{"fbc"},
	})
	rec := doRequest(mux, "POST", "/api/v1/nodes//scan", body, map[string]string{
		"Content-Type": "application/json",
	})

	// Go 1.22+ mux redirects // to single / (301) or returns 404
	if rec.Code != http.StatusBadRequest && rec.Code != http.StatusMovedPermanently && rec.Code != http.StatusNotFound {
		t.Errorf("expected 400/301/404, got %d", rec.Code)
	}
}

// TestGetReportHandlerMissingID verifies getReportHandler behavior with empty id.
// Go 1.22+ mux returns 404 for paths that don't match the pattern.
func TestGetReportHandlerMissingID(t *testing.T) {
	srv, _, cleanup := setupTest(t)
	defer cleanup()

	mux := srv.NewTestMux()
	rec := doRequest(mux, "GET", "/api/v1/reports/", nil, nil)

	// Go 1.22+ mux: /api/v1/reports/ doesn't match /api/v1/reports/{id} pattern
	// because {id} requires a non-empty value. Returns 404.
	if rec.Code != http.StatusBadRequest && rec.Code != http.StatusNotFound {
		t.Errorf("expected 400 or 404, got %d", rec.Code)
	}
}

// TestGenerateReportHandlerMissingFormat verifies format is required.
func TestGenerateReportHandlerMissingFormat(t *testing.T) {
	srv, _, cleanup := setupTest(t)
	defer cleanup()

	mux := srv.NewTestMux()
	body := jsonBody(map[string]interface{}{
		"node_addresses": []string{"10.0.0.1"},
	})
	rec := doRequest(mux, "POST", "/api/v1/reports/generate", body, map[string]string{
		"Content-Type": "application/json",
	})

	if rec.Code != http.StatusBadRequest {
		t.Errorf("expected 400, got %d: %s", rec.Code, rec.Body.String())
	}
}
