package integration

import (
	"bytes"
	"encoding/json"
	"net/http"
	"testing"
)

// ─── BsTool Integration Tests ──────────────────────────────────────

// TestBsToolErrLogIntegration verifies the full HTTP → handler → bstool
// client → error mapping pipeline through a real HTTP server.
// On Linux, BsTool.exe is not available, so the platform check should
// return 501 UNSUPPORTED_PLATFORM.
func TestBsToolErrLogIntegration(t *testing.T) {
	is := startIntegrationServer(t)

	t.Run("valid request gets 501 UNSUPPORTED_PLATFORM on Linux", func(t *testing.T) {
		body, _ := json.Marshal(map[string]interface{}{
			"server_name": "AP01m",
			"timeout":     30,
		})
		resp, respBody := is.doRequest("POST", "/api/v1/bstool/errlog",
			bytes.NewReader(body), map[string]string{"Content-Type": "application/json"})

		if resp.StatusCode != http.StatusNotImplemented {
			t.Errorf("expected 501 UNSUPPORTED_PLATFORM, got %d: %s", resp.StatusCode, string(respBody))
		}

		result := parseJSON(respBody)
		if result["error"] != "UNSUPPORTED_PLATFORM" {
			t.Errorf("expected error code UNSUPPORTED_PLATFORM, got %v", result["error"])
		}
		msg, ok := result["message"].(string)
		if !ok || msg == "" {
			t.Error("UNSUPPORTED_PLATFORM response should have non-empty message")
		}
	})

	t.Run("empty server_name gets 400 INVALID_REQUEST", func(t *testing.T) {
		body, _ := json.Marshal(map[string]interface{}{
			"server_name": "",
			"timeout":     30,
		})
		resp, respBody := is.doRequest("POST", "/api/v1/bstool/errlog",
			bytes.NewReader(body), map[string]string{"Content-Type": "application/json"})

		if resp.StatusCode != http.StatusBadRequest {
			t.Errorf("expected 400 for empty server_name, got %d: %s", resp.StatusCode, string(respBody))
		}

		result := parseJSON(respBody)
		if result["error"] != "INVALID_REQUEST" {
			t.Errorf("expected error INVALID_REQUEST, got %v", result["error"])
		}
	})

	t.Run("timeout below 5 gets 400 INVALID_TIMEOUT", func(t *testing.T) {
		body, _ := json.Marshal(map[string]interface{}{
			"server_name": "AP01m",
			"timeout":     3,
		})
		resp, respBody := is.doRequest("POST", "/api/v1/bstool/errlog",
			bytes.NewReader(body), map[string]string{"Content-Type": "application/json"})

		if resp.StatusCode != http.StatusBadRequest {
			t.Errorf("expected 400 for timeout=3, got %d: %s", resp.StatusCode, string(respBody))
		}

		result := parseJSON(respBody)
		if result["error"] != "INVALID_TIMEOUT" {
			t.Errorf("expected error INVALID_TIMEOUT, got %v", result["error"])
		}
	})

	t.Run("timeout above 120 gets 400 INVALID_TIMEOUT", func(t *testing.T) {
		body, _ := json.Marshal(map[string]interface{}{
			"server_name": "AP01m",
			"timeout":     200,
		})
		resp, respBody := is.doRequest("POST", "/api/v1/bstool/errlog",
			bytes.NewReader(body), map[string]string{"Content-Type": "application/json"})

		if resp.StatusCode != http.StatusBadRequest {
			t.Errorf("expected 400 for timeout=200, got %d: %s", resp.StatusCode, string(respBody))
		}

		result := parseJSON(respBody)
		if result["error"] != "INVALID_TIMEOUT" {
			t.Errorf("expected error INVALID_TIMEOUT, got %v", result["error"])
		}
	})

	t.Run("mask parameter still gets 501 on Linux", func(t *testing.T) {
		body, _ := json.Marshal(map[string]interface{}{
			"server_name": "AP01m",
			"timeout":     30,
			"mask":        "ERR",
		})
		resp, respBody := is.doRequest("POST", "/api/v1/bstool/errlog",
			bytes.NewReader(body), map[string]string{"Content-Type": "application/json"})

		// On Linux: 501 UNSUPPORTED_PLATFORM — mask is accepted by the
		// validation layer, but the platform check fires before execution.
		if resp.StatusCode != http.StatusNotImplemented {
			t.Errorf("expected 501 on Linux with mask, got %d: %s", resp.StatusCode, string(respBody))
		}

		result := parseJSON(respBody)
		if result["error"] != "UNSUPPORTED_PLATFORM" {
			t.Errorf("expected UNSUPPORTED_PLATFORM with mask, got %v", result["error"])
		}
	})

	t.Run("timeout=0 defaults to valid range (501 on Linux)", func(t *testing.T) {
		body, _ := json.Marshal(map[string]interface{}{
			"server_name": "AP01m",
			"timeout":     0,
		})
		resp, respBody := is.doRequest("POST", "/api/v1/bstool/errlog",
			bytes.NewReader(body), map[string]string{"Content-Type": "application/json"})

		// timeout=0 means "use default" — not a validation error, so it
		// passes validation and hits the platform check (501 on Linux).
		if resp.StatusCode != http.StatusNotImplemented {
			t.Errorf("expected 501 for timeout=0 (default), got %d: %s", resp.StatusCode, string(respBody))
		}
	})

	t.Run("invalid JSON gets 400", func(t *testing.T) {
		resp, respBody := is.doRequest("POST", "/api/v1/bstool/errlog",
			bytes.NewReader([]byte("{invalid json")),
			map[string]string{"Content-Type": "application/json"})

		if resp.StatusCode != http.StatusBadRequest {
			t.Errorf("expected 400 for invalid JSON, got %d: %s", resp.StatusCode, string(respBody))
		}
	})

	t.Run("response is valid JSON with error and message fields", func(t *testing.T) {
		body, _ := json.Marshal(map[string]interface{}{
			"server_name": "AP01m",
		})
		resp, respBody := is.doRequest("POST", "/api/v1/bstool/errlog",
			bytes.NewReader(body), map[string]string{"Content-Type": "application/json"})

		// Must be valid JSON
		var rawJSON map[string]interface{}
		if err := json.Unmarshal(respBody, &rawJSON); err != nil {
			t.Fatalf("response is not valid JSON: %v", err)
		}

		// Must have "error" and "message" fields
		if _, ok := rawJSON["error"]; !ok {
			t.Error("response missing 'error' field")
		}
		if _, ok := rawJSON["message"]; !ok {
			t.Error("response missing 'message' field")
		}

		// Verify Content-Type is application/json
		ct := resp.Header.Get("Content-Type")
		if ct != "application/json" {
			t.Errorf("expected Content-Type application/json, got %q", ct)
		}
	})
}