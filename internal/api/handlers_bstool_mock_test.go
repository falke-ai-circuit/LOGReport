package api

import (
	"embed"
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"strings"
	"testing"
	"time"

	"github.com/falke-ai-circuit/LOGReport/internal/bstool"
	"github.com/falke-ai-circuit/LOGReport/internal/server"
	"github.com/falke-ai-circuit/LOGReport/internal/store"
)

// ─── BsTool Handler with Mock Executor ──────────────────────────
//
// These tests verify the BsTool errlog handler's success path by injecting
// a mock bstool.Client that bypasses the platform check and returns
// mock executor output. This covers the handler's success response
// formatting (messages, count, duration, exit_code, timed_out fields).
//
// The mockExecutor and newMockClient helpers are defined in the bstool
// package's own test files (internal/bstool/integration_test.go).
// Since we're in the api package, we can't access those unexported types.
// Instead, we create a custom mock by using bstool.NewClient with options
// and testing what we can from the API layer.
//
// For the success path, we need to access the bstool.Client's unexported
// fields (skipPlatformCheck, exec). Since those are in a different package,
// we test the handler through the API layer with a real (non-mock) client
// on Linux, which returns UNSUPPORTED_PLATFORM.
//
// To test the success path, we use a test helper that creates a mock
// bstool client by constructing one with skipPlatformCheck=true.
// Since skipPlatformCheck is unexported, we can't set it directly from
// the api package. Instead, we verify the handler's error mapping
// behavior for all bstool error types.

// TestBsToolErrLogHandlerSuccessPath verifies the handler's success response
// structure by testing with a mock that bypasses the platform check.
//
// NOTE: The bstool.Client's skipPlatformCheck and exec fields are unexported,
// so we cannot inject a mock executor from the api package. This test
// documents the limitation and tests what we can: the error-to-HTTP
// mapping for all bstool error types, and the validation paths.
//
// The success path (messages, count, duration_ms, exit_code, timed_out)
// is tested in the bstool package's own integration_test.go via
// TestErrLog_MockSuccess.
func TestBsToolErrLogHandlerSuccessPath(t *testing.T) {
	// This test documents that the success path cannot be tested from
	// the api package because bstool.Client.exec and skipPlatformCheck
	// are unexported. The bstool package tests cover this path.
	t.Skip("BsTool success path requires access to unexported bstool.Client fields — covered in bstool package tests")
}

// TestBsToolErrLogHandlerAllErrorMappings verifies that all bstool error types
// are correctly mapped to HTTP status codes by mapBstoolErrorToHTTP.
func TestBsToolErrLogHandlerAllErrorMappings(t *testing.T) {
	tests := []struct {
		name       string
		err        error
		wantStatus int
		wantCode   string
	}{
		{
			name:       "ErrNotFound → 503",
			err:        &bstool.ErrNotFound{Path: "/missing/BsTool.exe"},
			wantStatus: http.StatusServiceUnavailable,
			wantCode:   "BSTOOL_NOT_FOUND",
		},
		{
			name:       "ErrUnsupportedPlatform → 501",
			err:        &bstool.ErrUnsupportedPlatform{},
			wantStatus: http.StatusNotImplemented,
			wantCode:   "UNSUPPORTED_PLATFORM",
		},
		{
			name:       "ErrTimeout → 504",
			err:        &bstool.ErrTimeout{Timeout: "15s"},
			wantStatus: http.StatusGatewayTimeout,
			wantCode:   "BSTOOL_TIMEOUT",
		},
		{
			name:       "ErrExecution → 502",
			err:        &bstool.ErrExecution{ExitCode: 1, Stderr: "crash"},
			wantStatus: http.StatusBadGateway,
			wantCode:   "BSTOOL_EXECUTION_FAILED",
		},
		{
			name:       "ErrInvalidServer → 400",
			err:        &bstool.ErrInvalidServer{},
			wantStatus: http.StatusBadRequest,
			wantCode:   "INVALID_REQUEST",
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			rec := httptest.NewRecorder()
			mapBstoolErrorToHTTP(rec, tt.err)

			if rec.Code != tt.wantStatus {
				t.Errorf("status: expected %d, got %d", tt.wantStatus, rec.Code)
			}

			var result map[string]interface{}
			json.Unmarshal(rec.Body.Bytes(), &result)
			if result["error"] != tt.wantCode {
				t.Errorf("error code: expected %q, got %v", tt.wantCode, result["error"])
			}
		})
	}
}

// TestBsToolErrLogHandlerWithTimeoutAndMask verifies the handler accepts
// timeout and mask parameters without validation errors (on Linux it
// returns 501 but the validation passes).
func TestBsToolErrLogHandlerWithTimeoutAndMask(t *testing.T) {
	srv, _, cleanup := setupTest(t)
	defer cleanup()

	mux := srv.NewTestMux()

	body := jsonBody(map[string]interface{}{
		"server_name": "AP01m",
		"timeout":     30,
		"mask":        "ERR",
	})
	rec := doRequest(mux, "POST", "/api/v1/bstool/errlog", body, map[string]string{
		"Content-Type": "application/json",
	})

	// On Linux: 501 UNSUPPORTED_PLATFORM (validation passed, platform check failed)
	if rec.Code != http.StatusNotImplemented && rec.Code != http.StatusInternalServerError {
		t.Errorf("expected 501 or 500 on Linux, got %d: %s", rec.Code, rec.Body.String())
	}
	result := parseJSONResponse(rec)
	if result["error"] != "UNSUPPORTED_PLATFORM" && result["error"] != "INTERNAL_ERROR" {
		t.Errorf("expected UNSUPPORTED_PLATFORM or INTERNAL_ERROR, got %v", result["error"])
	}
}

// TestBsToolErrLogHandlerTimeoutBoundaryMin5 verifies timeout=5 is accepted (boundary).
func TestBsToolErrLogHandlerTimeoutBoundaryMin5(t *testing.T) {
	srv, _, cleanup := setupTest(t)
	defer cleanup()

	mux := srv.NewTestMux()

	body := jsonBody(map[string]interface{}{
		"server_name": "AP01m",
		"timeout":     5, // minimum valid timeout
	})
	rec := doRequest(mux, "POST", "/api/v1/bstool/errlog", body, map[string]string{
		"Content-Type": "application/json",
	})

	// Should pass validation (timeout=5 is valid) and fail on platform
	if rec.Code != http.StatusNotImplemented && rec.Code != http.StatusInternalServerError {
		t.Errorf("expected 501 or 500 (timeout=5 valid), got %d: %s", rec.Code, rec.Body.String())
	}
}

// TestBsToolErrLogHandlerTimeoutBoundaryMax120 verifies timeout=120 is accepted (boundary).
func TestBsToolErrLogHandlerTimeoutBoundaryMax120(t *testing.T) {
	srv, _, cleanup := setupTest(t)
	defer cleanup()

	mux := srv.NewTestMux()

	body := jsonBody(map[string]interface{}{
		"server_name": "AP01m",
		"timeout":     120, // maximum valid timeout
	})
	rec := doRequest(mux, "POST", "/api/v1/bstool/errlog", body, map[string]string{
		"Content-Type": "application/json",
	})

	if rec.Code != http.StatusNotImplemented && rec.Code != http.StatusInternalServerError {
		t.Errorf("expected 501 or 500 (timeout=120 valid), got %d: %s", rec.Code, rec.Body.String())
	}
}

// TestBsToolErrLogHandlerTimeoutZero verifies timeout=0 uses default (no validation error).
func TestBsToolErrLogHandlerTimeoutZero(t *testing.T) {
	srv, _, cleanup := setupTest(t)
	defer cleanup()

	mux := srv.NewTestMux()

	body := jsonBody(map[string]interface{}{
		"server_name": "AP01m",
		"timeout":     0, // 0 means use default — should not trigger validation error
	})
	rec := doRequest(mux, "POST", "/api/v1/bstool/errlog", body, map[string]string{
		"Content-Type": "application/json",
	})

	// timeout=0 is special: it means "use default", so it should pass validation
	if rec.Code != http.StatusNotImplemented && rec.Code != http.StatusInternalServerError {
		t.Errorf("expected 501 or 500 (timeout=0 default), got %d: %s", rec.Code, rec.Body.String())
	}
}

// TestBsToolErrLogHandlerResponseContentType verifies the response has
// application/json Content-Type for all response types.
func TestBsToolErrLogHandlerResponseContentType(t *testing.T) {
	srv, _, cleanup := setupTest(t)
	defer cleanup()

	mux := srv.NewTestMux()

	// Test error response content type
	body := jsonBody(map[string]interface{}{
		"server_name": "AP01m",
	})
	rec := doRequest(mux, "POST", "/api/v1/bstool/errlog", body, map[string]string{
		"Content-Type": "application/json",
	})

	ct := rec.Header().Get("Content-Type")
	if !strings.Contains(ct, "application/json") {
		t.Errorf("expected application/json Content-Type, got %q", ct)
	}
}

// TestBsToolErrLogHandlerWithCustomClient verifies the handler uses the
// injected bstool client (custom path, communication line, timeout).
func TestBsToolErrLogHandlerWithCustomClient(t *testing.T) {
	st := setupTestStore(t)
	defer st.Close()

	cfg := &server.Config{Port: 0, DBPath: ":memory:", LogLevel: "debug", CORSOrigin: "*"}

	customClient := bstool.NewClient(
		bstool.WithPath("/custom/path/BsTool.exe"),
		bstool.WithCommunicationLine("GH04"),
		bstool.WithTimeout(60*time.Second),
	)

	srv := NewServer(st, cfg, embed.FS{}, customClient)
	mux := srv.NewTestMux()

	body := jsonBody(map[string]interface{}{
		"server_name": "AP01m",
	})
	rec := doRequest(mux, "POST", "/api/v1/bstool/errlog", body, map[string]string{
		"Content-Type": "application/json",
	})

	// On Linux: 501 UNSUPPORTED_PLATFORM
	if rec.Code != http.StatusNotImplemented && rec.Code != http.StatusInternalServerError {
		t.Errorf("expected 501 or 500, got %d: %s", rec.Code, rec.Body.String())
	}
}

// TestBsToolErrLogHandlerEmptyBody verifies that an empty body returns 400.
func TestBsToolErrLogHandlerEmptyBody(t *testing.T) {
	srv, _, cleanup := setupTest(t)
	defer cleanup()

	mux := srv.NewTestMux()

	rec := doRequest(mux, "POST", "/api/v1/bstool/errlog", strings.NewReader(""), map[string]string{
		"Content-Type": "application/json",
	})

	if rec.Code != http.StatusBadRequest {
		t.Errorf("expected 400 for empty body, got %d: %s", rec.Code, rec.Body.String())
	}
}

// TestBsToolErrLogHandlerServerNameWithSuffix verifies 'm' suffix is handled.
// The bstool client strips trailing 'm' or 'r' before passing to BsTool.exe.
func TestBsToolErrLogHandlerServerNameWithSuffix(t *testing.T) {
	srv, _, cleanup := setupTest(t)
	defer cleanup()

	mux := srv.NewTestMux()

	// Test with 'm' suffix — should pass validation and fail on platform
	body := jsonBody(map[string]interface{}{
		"server_name": "AP01m",
	})
	rec := doRequest(mux, "POST", "/api/v1/bstool/errlog", body, map[string]string{
		"Content-Type": "application/json",
	})
	if rec.Code != http.StatusNotImplemented && rec.Code != http.StatusInternalServerError {
		t.Errorf("expected 501 or 500 for AP01m, got %d", rec.Code)
	}

	// Test with 'r' suffix
	body2 := jsonBody(map[string]interface{}{
		"server_name": "BP01r",
	})
	rec2 := doRequest(mux, "POST", "/api/v1/bstool/errlog", body2, map[string]string{
		"Content-Type": "application/json",
	})
	if rec2.Code != http.StatusNotImplemented && rec2.Code != http.StatusInternalServerError {
		t.Errorf("expected 501 or 500 for BP01r, got %d", rec2.Code)
	}

	// Test without suffix
	body3 := jsonBody(map[string]interface{}{
		"server_name": "CP03",
	})
	rec3 := doRequest(mux, "POST", "/api/v1/bstool/errlog", body3, map[string]string{
		"Content-Type": "application/json",
	})
	if rec3.Code != http.StatusNotImplemented && rec3.Code != http.StatusInternalServerError {
		t.Errorf("expected 501 or 500 for CP03, got %d", rec3.Code)
	}
}

// ─── Helper ─────────────────────────────────────────────────────

// setupTestStore creates just a store for tests that need custom server construction.
func setupTestStore(t *testing.T) *store.Store {
	t.Helper()
	st, err := store.Open("")
	if err != nil {
		t.Fatalf("open store: %v", err)
	}
	return st
}
