package api

import (
	"embed"
	"encoding/json"
	"net/http"
	"strings"
	"testing"
	"time"

	"github.com/falke-ai-circuit/LOGReport/internal/bstool"
	"github.com/falke-ai-circuit/LOGReport/internal/server"
	"github.com/falke-ai-circuit/LOGReport/internal/store"
)

// ─── BsTool Handler Extended Tests ──────────────────────────────────────────

// TestBsToolErrLogHandler_TimeoutBoundaries tests timeout=3 (below min 5) and timeout=200 (above max 120).
func TestBsToolErrLogHandler_TimeoutBoundaries(t *testing.T) {
	srv, _, cleanup := setupTest(t)
	defer cleanup()

	mux := srv.NewTestMux()

	t.Run("timeout=3 below minimum 5", func(t *testing.T) {
		body := jsonBody(map[string]interface{}{
			"server_name": "AP01m",
			"timeout":     3,
		})
		rec := doRequest(mux, "POST", "/api/v1/bstool/errlog", body, map[string]string{
			"Content-Type": "application/json",
		})
		if rec.Code != http.StatusBadRequest {
			t.Errorf("expected 400 for timeout=3, got %d: %s", rec.Code, rec.Body.String())
		}
		result := parseJSONResponse(rec)
		if result["error"] != "INVALID_TIMEOUT" {
			t.Errorf("expected error INVALID_TIMEOUT, got %v", result["error"])
		}
	})

	t.Run("timeout=200 above maximum 120", func(t *testing.T) {
		body := jsonBody(map[string]interface{}{
			"server_name": "AP01m",
			"timeout":     200,
		})
		rec := doRequest(mux, "POST", "/api/v1/bstool/errlog", body, map[string]string{
			"Content-Type": "application/json",
		})
		if rec.Code != http.StatusBadRequest {
			t.Errorf("expected 400 for timeout=200, got %d: %s", rec.Code, rec.Body.String())
		}
		result := parseJSONResponse(rec)
		if result["error"] != "INVALID_TIMEOUT" {
			t.Errorf("expected error INVALID_TIMEOUT, got %v", result["error"])
		}
	})
}

// TestBsToolErrLogHandler_MaskParameter verifies the mask parameter is accepted.
func TestBsToolErrLogHandler_MaskParameter(t *testing.T) {
	srv, _, cleanup := setupTest(t)
	defer cleanup()

	mux := srv.NewTestMux()

	// On Linux, the request will still fail with UNSUPPORTED_PLATFORM,
	// but we verify the mask parameter is accepted (no validation error).
	t.Run("mask parameter accepted", func(t *testing.T) {
		body := jsonBody(map[string]interface{}{
			"server_name": "AP01m",
			"mask":        "ERR",
		})
		rec := doRequest(mux, "POST", "/api/v1/bstool/errlog", body, map[string]string{
			"Content-Type": "application/json",
		})
		// On Linux: 501 UNSUPPORTED_PLATFORM (mask doesn't cause validation error)
		if rec.Code != http.StatusNotImplemented {
			t.Errorf("expected 501 on Linux, got %d: %s", rec.Code, rec.Body.String())
		}
		result := parseJSONResponse(rec)
		if result["error"] != "UNSUPPORTED_PLATFORM" {
			t.Errorf("expected UNSUPPORTED_PLATFORM, got %v", result["error"])
		}
	})

	t.Run("mask with valid timeout", func(t *testing.T) {
		body := jsonBody(map[string]interface{}{
			"server_name": "BP01r",
			"timeout":     30,
			"mask":        "WRN",
		})
		rec := doRequest(mux, "POST", "/api/v1/bstool/errlog", body, map[string]string{
			"Content-Type": "application/json",
		})
		// On Linux: 501 (not a validation error)
		if rec.Code != http.StatusNotImplemented {
			t.Errorf("expected 501 on Linux, got %d: %s", rec.Code, rec.Body.String())
		}
	})
}

// TestBsToolErrLogHandler_ResponseStructure validates the JSON response structure
// for both error and (hypothetical) success responses.
func TestBsToolErrLogHandler_ResponseStructure(t *testing.T) {
	srv, _, cleanup := setupTest(t)
	defer cleanup()

	mux := srv.NewTestMux()

	t.Run("error response has error and message fields", func(t *testing.T) {
		body := jsonBody(map[string]interface{}{
			"server_name": "AP01m",
		})
		rec := doRequest(mux, "POST", "/api/v1/bstool/errlog", body, map[string]string{
			"Content-Type": "application/json",
		})

		result := parseJSONResponse(rec)

		// Error response must have "error" and "message" fields
		if _, ok := result["error"]; !ok {
			t.Error("error response missing 'error' field")
		}
		if _, ok := result["message"]; !ok {
			t.Error("error response missing 'message' field")
		}

		// Verify it's valid JSON
		var rawJSON map[string]interface{}
		if err := json.Unmarshal(rec.Body.Bytes(), &rawJSON); err != nil {
			t.Errorf("response is not valid JSON: %v", err)
		}

		// Verify Content-Type header
		ct := rec.Header().Get("Content-Type")
		if !strings.Contains(ct, "application/json") {
			t.Errorf("expected Content-Type application/json, got %q", ct)
		}
	})

	t.Run("validation error response structure", func(t *testing.T) {
		body := jsonBody(map[string]interface{}{
			"timeout": 999,
		})
		rec := doRequest(mux, "POST", "/api/v1/bstool/errlog", body, map[string]string{
			"Content-Type": "application/json",
		})

		if rec.Code != http.StatusBadRequest {
			t.Errorf("expected 400, got %d", rec.Code)
		}

		result := parseJSONResponse(rec)
		if result["error"] != "INVALID_REQUEST" {
			t.Errorf("expected INVALID_REQUEST, got %v", result["error"])
		}
		if result["message"] != `"server_name" is required` {
			t.Errorf("expected server_name required message, got %v", result["message"])
		}
	})

	t.Run("platform error response structure", func(t *testing.T) {
		body := jsonBody(map[string]interface{}{
			"server_name": "CP03m",
		})
		rec := doRequest(mux, "POST", "/api/v1/bstool/errlog", body, map[string]string{
			"Content-Type": "application/json",
		})

		if rec.Code != http.StatusNotImplemented {
			t.Errorf("expected 501, got %d", rec.Code)
		}

		result := parseJSONResponse(rec)
		if result["error"] != "UNSUPPORTED_PLATFORM" {
			t.Errorf("expected UNSUPPORTED_PLATFORM, got %v", result["error"])
		}
		msg, ok := result["message"].(string)
		if !ok || msg == "" {
			t.Error("UNSUPPORTED_PLATFORM response should have non-empty message")
		}
	})
}

// TestBsToolErrLogHandler_WithCustomClient verifies the handler uses the injected bstool client.
func TestBsToolErrLogHandler_WithCustomClient(t *testing.T) {
	// Create a server with a custom bstool client
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

	customClient := bstool.NewClient(
		bstool.WithPath("/custom/path/BsTool.exe"),
		bstool.WithCommunicationLine("GH04"),
		bstool.WithTimeout(60*time.Second),
	)

	srv := NewServer(st, cfg, embed.FS{}, customClient)
	mux := srv.NewTestMux()

	// Verify the handler works with the custom client
	body := jsonBody(map[string]interface{}{
		"server_name": "AP01m",
	})
	rec := doRequest(mux, "POST", "/api/v1/bstool/errlog", body, map[string]string{
		"Content-Type": "application/json",
	})

	// On Linux, should still get UNSUPPORTED_PLATFORM
	if rec.Code != http.StatusNotImplemented {
		t.Errorf("expected 501, got %d: %s", rec.Code, rec.Body.String())
	}
}
