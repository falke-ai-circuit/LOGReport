package api

import (
	"bytes"
	"mime/multipart"
	"net/http"
	"os"
	"path/filepath"
	"strings"
	"testing"
)

// ─── SysFiles Handler Tests ───────────────────────────────────────
// Covers: scan, scan missing dir (400), parse, parse-multi, scan-nodes, load.

func TestSysFilesScanHandler(t *testing.T) {
	srv, _, cleanup := setupTest(t)
	defer cleanup()

	mux := srv.NewTestMux()

	t.Run("scan valid directory returns 200", func(t *testing.T) {
		tmpDir := t.TempDir()
		// Create a .sys file
		sysContent := ":e:hw:1a1   AL01   pxe:sys-csg2   // Main LIS node\n"
		os.WriteFile(filepath.Join(tmpDir, "AL01.sys"), []byte(sysContent), 0644)

		rec := doRequest(mux, "GET", "/api/v1/sysfiles/scan?dir="+tmpDir, nil, nil)
		if rec.Code != http.StatusOK {
			t.Errorf("expected 200, got %d: %s", rec.Code, rec.Body.String())
		}
		result := parseJSONResponse(rec)
		if _, ok := result["configs"]; !ok {
			t.Error("expected configs field")
		}
		if _, ok := result["sys_files"]; !ok {
			t.Error("expected sys_files field")
		}
		if _, ok := result["filters"]; !ok {
			t.Error("expected filters field")
		}
	})

	t.Run("scan missing dir parameter returns 400", func(t *testing.T) {
		rec := doRequest(mux, "GET", "/api/v1/sysfiles/scan", nil, nil)
		if rec.Code != http.StatusBadRequest {
			t.Errorf("expected 400, got %d", rec.Code)
		}
		result := parseJSONResponse(rec)
		if result["error"] != "validation_error" {
			t.Errorf("expected validation_error, got %v", result["error"])
		}
	})

	t.Run("scan non-existent directory returns 500", func(t *testing.T) {
		rec := doRequest(mux, "GET", "/api/v1/sysfiles/scan?dir=/nonexistent/path/12345", nil, nil)
		// LoadSysFiles returns error for non-existent dir
		if rec.Code != http.StatusInternalServerError {
			t.Errorf("expected 500, got %d: %s", rec.Code, rec.Body.String())
		}
	})

	t.Run("scan with filter parameters returns 200", func(t *testing.T) {
		tmpDir := t.TempDir()
		sysContent := ":e:hw:1a1   AL01   pxe:sys-csg2   // Main LIS node\n"
		os.WriteFile(filepath.Join(tmpDir, "AL01.sys"), []byte(sysContent), 0644)

		rec := doRequest(mux, "GET", "/api/v1/sysfiles/scan?dir="+tmpDir+"&include_fbc=true&include_rpc=false&include_lis=true", nil, nil)
		if rec.Code != http.StatusOK {
			t.Errorf("expected 200, got %d: %s", rec.Code, rec.Body.String())
		}
		result := parseJSONResponse(rec)
		filters, ok := result["filters"].(map[string]interface{})
		if !ok {
			t.Error("expected filters object")
		}
		if filters["include_fbc"] != true {
			t.Errorf("expected include_fbc true, got %v", filters["include_fbc"])
		}
		if filters["include_rpc"] != false {
			t.Errorf("expected include_rpc false, got %v", filters["include_rpc"])
		}
		if filters["include_lis"] != true {
			t.Errorf("expected include_lis true, got %v", filters["include_lis"])
		}
	})
}

func TestSysFilesParseHandler(t *testing.T) {
	srv, _, cleanup := setupTest(t)
	defer cleanup()

	mux := srv.NewTestMux()

	t.Run("parse valid directory returns 200", func(t *testing.T) {
		tmpDir := t.TempDir()
		sysContent := ":e:hw:1a1   AL01   pxe:sys-csg2   // Main LIS node\n"
		os.WriteFile(filepath.Join(tmpDir, "AL01.sys"), []byte(sysContent), 0644)

		rec := doRequest(mux, "GET", "/api/v1/sysfiles/parse?dir="+tmpDir, nil, nil)
		if rec.Code != http.StatusOK {
			t.Errorf("expected 200, got %d: %s", rec.Code, rec.Body.String())
		}
		result := parseJSONResponse(rec)
		if _, ok := result["configs"]; !ok {
			t.Error("expected configs field")
		}
		if _, ok := result["count"]; !ok {
			t.Error("expected count field")
		}
	})

	t.Run("parse missing dir parameter returns 400", func(t *testing.T) {
		rec := doRequest(mux, "GET", "/api/v1/sysfiles/parse", nil, nil)
		if rec.Code != http.StatusBadRequest {
			t.Errorf("expected 400, got %d", rec.Code)
		}
	})
}

func TestSysFilesParseMultiHandler(t *testing.T) {
	srv, _, cleanup := setupTest(t)
	defer cleanup()

	mux := srv.NewTestMux()

	t.Run("parse-multi with valid .sys files returns 200", func(t *testing.T) {
		sysContent := ":e:hw:1a1   AL01   pxe:sys-csg2   // Main LIS node\n"

		body := &bytes.Buffer{}
		writer := multipart.NewWriter(body)
		part, _ := writer.CreateFormFile("files", "AL01.sys")
		part.Write([]byte(sysContent))
		writer.Close()

		rec := doRequest(mux, "POST", "/api/v1/sysfiles/parse-multi", body, map[string]string{
			"Content-Type": writer.FormDataContentType(),
		})
		if rec.Code != http.StatusOK {
			t.Errorf("expected 200, got %d: %s", rec.Code, rec.Body.String())
		}
		result := parseJSONResponse(rec)
		if _, ok := result["configs"]; !ok {
			t.Error("expected configs field")
		}
		if _, ok := result["files"]; !ok {
			t.Error("expected files field")
		}
		if _, ok := result["file_count"]; !ok {
			t.Error("expected file_count field")
		}
	})

	t.Run("parse-multi without .sys files returns 400", func(t *testing.T) {
		body := &bytes.Buffer{}
		writer := multipart.NewWriter(body)
		part, _ := writer.CreateFormFile("files", "notasys.txt")
		part.Write([]byte("not a sys file"))
		writer.Close()

		rec := doRequest(mux, "POST", "/api/v1/sysfiles/parse-multi", body, map[string]string{
			"Content-Type": writer.FormDataContentType(),
		})
		if rec.Code != http.StatusBadRequest {
			t.Errorf("expected 400, got %d: %s", rec.Code, rec.Body.String())
		}
	})
}

func TestSysFilesLoadHandler(t *testing.T) {
	srv, _, cleanup := setupTest(t)
	defer cleanup()

	mux := srv.NewTestMux()

	t.Run("load sys files from valid directory returns 200", func(t *testing.T) {
		tmpDir := t.TempDir()
		outputDir := t.TempDir()
		sysContent := ":e:hw:1a1   AL01   pxe:sys-csg2   // Main LIS node\n"
		os.WriteFile(filepath.Join(tmpDir, "AL01.sys"), []byte(sysContent), 0644)

		body := jsonBody(map[string]interface{}{
			"directory":  tmpDir,
			"output_dir": outputDir,
		})
		rec := doRequest(mux, "POST", "/api/v1/sysfiles/load", body, jsonHeader)
		if rec.Code != http.StatusOK {
			t.Errorf("expected 200, got %d: %s", rec.Code, rec.Body.String())
		}
		result := parseJSONResponse(rec)
		if _, ok := result["configs_count"]; !ok {
			t.Error("expected configs_count field")
		}
		if result["directory"] != tmpDir {
			t.Errorf("expected directory %s, got %v", tmpDir, result["directory"])
		}
		if result["output_dir"] != outputDir {
			t.Errorf("expected output_dir %s, got %v", outputDir, result["output_dir"])
		}
	})

	t.Run("load sys files missing directory returns 400", func(t *testing.T) {
		body := jsonBody(map[string]interface{}{
			"output_dir": "/tmp/out",
		})
		rec := doRequest(mux, "POST", "/api/v1/sysfiles/load", body, jsonHeader)
		if rec.Code != http.StatusBadRequest {
			t.Errorf("expected 400, got %d", rec.Code)
		}
	})

	t.Run("load sys files missing output_dir returns 400", func(t *testing.T) {
		body := jsonBody(map[string]interface{}{
			"directory": "/tmp",
		})
		rec := doRequest(mux, "POST", "/api/v1/sysfiles/load", body, jsonHeader)
		if rec.Code != http.StatusBadRequest {
			t.Errorf("expected 400, got %d", rec.Code)
		}
	})

	t.Run("load sys files invalid JSON returns 400", func(t *testing.T) {
		rec := doRequest(mux, "POST", "/api/v1/sysfiles/load", strings.NewReader("{bad"), jsonHeader)
		if rec.Code != http.StatusBadRequest {
			t.Errorf("expected 400, got %d", rec.Code)
		}
	})
}

func TestSysFilesScanNodesHandler(t *testing.T) {
	srv, _, cleanup := setupTest(t)
	defer cleanup()

	mux := srv.NewTestMux()

	t.Run("scan-nodes with local_dir method and .sys files returns 200", func(t *testing.T) {
		tmpDir := t.TempDir()
		sysContent := ":e:hw:1a1   AL01   pxe:sys-csg2   // Main LIS node\n"
		os.WriteFile(filepath.Join(tmpDir, "AL01.sys"), []byte(sysContent), 0644)

		// Save settings to use local_dir scan method and our temp BU dir
		settingsBody := jsonBody(map[string]interface{}{
			"scan_method": "local_dir",
			"bu_dir":      tmpDir,
		})
		doRequest(mux, "POST", "/api/v1/settings", settingsBody, jsonHeader)

		rec := doRequest(mux, "POST", "/api/v1/sysfiles/scan-nodes", nil, jsonHeader)
		if rec.Code != http.StatusOK {
			t.Errorf("expected 200, got %d: %s", rec.Code, rec.Body.String())
		}
		result := parseJSONResponse(rec)
		if result["method"] != "bu_local_sys_files" {
			t.Errorf("expected method 'bu_local_sys_files', got %v", result["method"])
		}
		if _, ok := result["configs"]; !ok {
			t.Error("expected configs field")
		}
	})

	t.Run("scan-nodes with local_dir method and no .sys files returns 404", func(t *testing.T) {
		tmpDir := t.TempDir()

		settingsBody := jsonBody(map[string]interface{}{
			"scan_method": "local_dir",
			"bu_dir":      tmpDir,
		})
		doRequest(mux, "POST", "/api/v1/settings", settingsBody, jsonHeader)

		rec := doRequest(mux, "POST", "/api/v1/sysfiles/scan-nodes", nil, jsonHeader)
		if rec.Code != http.StatusNotFound {
			t.Errorf("expected 404, got %d: %s", rec.Code, rec.Body.String())
		}
	})
}