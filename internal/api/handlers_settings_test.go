package api

import (
	"net/http"
	"strings"
	"testing"
)

// ─── Settings Handler Tests ───────────────────────────────────────
// Covers: get settings (all 13 fields), save settings, persistence, partial save.

func TestSettingsGetHandler(t *testing.T) {
	srv, _, cleanup := setupTest(t)
	defer cleanup()

	mux := srv.NewTestMux()

	t.Run("get settings returns 200 with all 13 fields", func(t *testing.T) {
		rec := doRequest(mux, "GET", "/api/v1/settings", nil, nil)
		if rec.Code != http.StatusOK {
			t.Errorf("expected 200, got %d: %s", rec.Code, rec.Body.String())
		}
		result := parseJSONResponse(rec)
		settings, ok := result["settings"].(map[string]interface{})
		if !ok {
			t.Fatalf("expected settings object, got %T", result["settings"])
		}

		// Verify all 13 fields are present:
		// dia_host, dia_port, bstool_host, bstool_port, log_root, logroot_name,
		// bstool_path, communication_line, output_dir, bu_dir,
		// lis_mode, scan_method, node_filter, lis_exe_count, lisdiag_password
		// (Settings struct has 15 fields, not exactly 13 — but the task says 13;
		// we verify the core fields exist and have sensible defaults)
		expectedFields := []string{
			"dia_host",
			"dia_port",
			"bstool_host",
			"bstool_port",
			"log_root",
			"logroot_name",
			"bstool_path",
			"communication_line",
			"output_dir",
			"bu_dir",
			"lis_mode",
			"scan_method",
			"node_filter",
			"lis_exe_count",
			"lisdiag_password",
		}
		for _, field := range expectedFields {
			if _, ok := settings[field]; !ok {
				t.Errorf("expected field %q in settings, missing", field)
			}
		}

		// Verify default values
		if settings["dia_host"] != "127.0.0.1" {
			t.Errorf("expected dia_host '127.0.0.1', got %v", settings["dia_host"])
		}
		if int(settings["dia_port"].(float64)) != 1234 {
			t.Errorf("expected dia_port 1234, got %v", settings["dia_port"])
		}
		if int(settings["bstool_port"].(float64)) != 1516 {
			t.Errorf("expected bstool_port 1516, got %v", settings["bstool_port"])
		}
		if settings["lis_mode"] != "rsu" {
			t.Errorf("expected lis_mode 'rsu', got %v", settings["lis_mode"])
		}
		if settings["scan_method"] == "" {
			t.Errorf("expected scan_method to be non-empty, got %v", settings["scan_method"])
		}
		if int(settings["lis_exe_count"].(float64)) != 6 {
			t.Errorf("expected lis_exe_count 6, got %v", settings["lis_exe_count"])
		}
	})
}

func TestSettingsSaveHandler(t *testing.T) {
	srv, _, cleanup := setupTest(t)
	defer cleanup()

	mux := srv.NewTestMux()

	t.Run("save settings returns 200", func(t *testing.T) {
		body := jsonBody(map[string]interface{}{
			"dia_host":           "192.168.1.100",
			"dia_port":           2345,
			"bstool_host":        "192.168.1.200",
			"bstool_port":        1516,
			"log_root":           "/tmp/test-logs",
			"logroot_name":       "_LOG",
			"bstool_path":        "/custom/BsTool.exe",
			"communication_line": "AB01",
			"output_dir":         "/tmp/output",
			"bu_dir":             "/dna/CA/bu",
			"lis_mode":           "lisdiag",
			"scan_method":        "local_dir",
			"node_filter":        "AP,AL",
			"lis_exe_count":      4,
			"lisdiag_password":   "secret123",
		})
		rec := doRequest(mux, "POST", "/api/v1/settings", body, jsonHeader)
		if rec.Code != http.StatusOK {
			t.Errorf("expected 200, got %d: %s", rec.Code, rec.Body.String())
		}
		result := parseJSONResponse(rec)
		if result["saved"] != true {
			t.Errorf("expected saved true, got %v", result["saved"])
		}
		settings, ok := result["settings"].(map[string]interface{})
		if !ok {
			t.Fatalf("expected settings object, got %T", result["settings"])
		}
		if settings["dia_host"] != "192.168.1.100" {
			t.Errorf("expected dia_host '192.168.1.100', got %v", settings["dia_host"])
		}
		if int(settings["dia_port"].(float64)) != 2345 {
			t.Errorf("expected dia_port 2345, got %v", settings["dia_port"])
		}
		if settings["lis_mode"] != "lisdiag" {
			t.Errorf("expected lis_mode 'lisdiag', got %v", settings["lis_mode"])
		}
		if settings["lisdiag_password"] != "secret123" {
			t.Errorf("expected lisdiag_password 'secret123', got %v", settings["lisdiag_password"])
		}
	})

	t.Run("save settings invalid JSON returns 400", func(t *testing.T) {
		rec := doRequest(mux, "POST", "/api/v1/settings", strings.NewReader("{bad json"), jsonHeader)
		if rec.Code != http.StatusBadRequest {
			t.Errorf("expected 400, got %d", rec.Code)
		}
	})
}

func TestSettingsPersistenceAndPartialSave(t *testing.T) {
	srv, _, cleanup := setupTest(t)
	defer cleanup()

	mux := srv.NewTestMux()

	t.Run("save then get returns saved values (persistence)", func(t *testing.T) {
		// Save with custom values
		body := jsonBody(map[string]interface{}{
			"dia_host":      "10.0.0.1",
			"dia_port":      9999,
			"lis_mode":      "diaglis",
			"lis_exe_count": 3,
		})
		rec := doRequest(mux, "POST", "/api/v1/settings", body, jsonHeader)
		if rec.Code != http.StatusOK {
			t.Errorf("save: expected 200, got %d: %s", rec.Code, rec.Body.String())
		}

		// Get — should return saved values
		rec2 := doRequest(mux, "GET", "/api/v1/settings", nil, nil)
		if rec2.Code != http.StatusOK {
			t.Errorf("get: expected 200, got %d", rec2.Code)
		}
		result := parseJSONResponse(rec2)
		settings, ok := result["settings"].(map[string]interface{})
		if !ok {
			t.Fatalf("expected settings object, got %T", result["settings"])
		}
		if settings["dia_host"] != "10.0.0.1" {
			t.Errorf("expected dia_host '10.0.0.1', got %v", settings["dia_host"])
		}
		if int(settings["dia_port"].(float64)) != 9999 {
			t.Errorf("expected dia_port 9999, got %v", settings["dia_port"])
		}
		if settings["lis_mode"] != "diaglis" {
			t.Errorf("expected lis_mode 'diaglis', got %v", settings["lis_mode"])
		}
		if int(settings["lis_exe_count"].(float64)) != 3 {
			t.Errorf("expected lis_exe_count 3, got %v", settings["lis_exe_count"])
		}
	})

	t.Run("partial save fills defaults for missing fields", func(t *testing.T) {
		// Save with only one field — others should get defaults
		body := jsonBody(map[string]interface{}{
			"dia_host": "172.16.0.1",
		})
		rec := doRequest(mux, "POST", "/api/v1/settings", body, jsonHeader)
		if rec.Code != http.StatusOK {
			t.Errorf("expected 200, got %d: %s", rec.Code, rec.Body.String())
		}
		result := parseJSONResponse(rec)
		settings, ok := result["settings"].(map[string]interface{})
		if !ok {
			t.Fatalf("expected settings object, got %T", result["settings"])
		}
		// dia_host should be what we sent
		if settings["dia_host"] != "172.16.0.1" {
			t.Errorf("expected dia_host '172.16.0.1', got %v", settings["dia_host"])
		}
		// dia_port should be default (1234) since we didn't send it
		if int(settings["dia_port"].(float64)) != 1234 {
			t.Errorf("expected dia_port default 1234, got %v", settings["dia_port"])
		}
		// bstool_host should be default
		if settings["bstool_host"] != "127.0.0.1" {
			t.Errorf("expected bstool_host default '127.0.0.1', got %v", settings["bstool_host"])
		}
		// lis_mode should be default
		if settings["lis_mode"] != "rsu" {
			t.Errorf("expected lis_mode default 'rsu', got %v", settings["lis_mode"])
		}
	})
}