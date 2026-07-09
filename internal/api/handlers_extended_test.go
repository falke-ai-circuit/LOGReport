package api

import (
	"context"
	"embed"
	"encoding/json"
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
	st, err := store.Open("")
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
	srv, st, err := NewTestServer()
	if err != nil {
		t.Fatalf("NewTestServer: %v", err)
	}
	defer st.Close()

	mux := srv.NewTestMux()
	if mux == nil {
		t.Fatal("NewTestMux returned nil")
	}

	// Verify routes are registered by hitting health endpoint
	rec := httptest.NewRecorder()
	req := httptest.NewRequest("GET", "/health", nil)
	mux.ServeHTTP(rec, req)

	if rec.Code != http.StatusOK {
		t.Errorf("health via NewTestMux: expected 200, got %d", rec.Code)
	}
}

// TestServerShutdownMethod verifies the Shutdown method returns nil.
func TestServerShutdownMethod(t *testing.T) {
	srv, _, cleanup := setupTest(t)
	defer cleanup()

	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()

	err := srv.Shutdown(ctx)
	if err != nil {
		t.Errorf("Shutdown should return nil, got %v", err)
	}
}
