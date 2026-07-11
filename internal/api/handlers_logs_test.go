package api

import (
	"net/http"
	"os"
	"path/filepath"
	"strings"
	"testing"
)

// ─── Log Handler Tests ────────────────────────────────────────────
// Covers: list log root, list files, get content, setroot, setroot missing path,
// create file, create conflict, save file, read saved file, erase, delete, move,
// create-folder, browse, write by node, read by node.

func TestLogsListRootHandler(t *testing.T) {
	srv, _, cleanup := setupTest(t)
	defer cleanup()

	mux := srv.NewTestMux()

	t.Run("list log root with valid path returns 200", func(t *testing.T) {
		tmpDir := t.TempDir()
		// Create a .fbc file
		os.WriteFile(filepath.Join(tmpDir, "test.fbc"), []byte("FBC data"), 0644)
		os.WriteFile(filepath.Join(tmpDir, "test.log"), []byte("LOG data"), 0644)

		rec := doRequest(mux, "GET", "/api/v1/logs/list?path="+tmpDir, nil, nil)
		if rec.Code != http.StatusOK {
			t.Errorf("expected 200, got %d: %s", rec.Code, rec.Body.String())
		}
		result := parseJSONResponse(rec)
		if result["path"] != tmpDir {
			t.Errorf("expected path %s, got %v", tmpDir, result["path"])
		}
		count, ok := result["count"].(float64)
		if !ok || count < 1 {
			t.Errorf("expected count >= 1, got %v", result["count"])
		}
	})

	t.Run("list log root non-existent path returns 200 with empty", func(t *testing.T) {
		rec := doRequest(mux, "GET", "/api/v1/logs/list?path=/nonexistent/path/12345", nil, nil)
		// ScanFiles returns empty for non-existent dirs (WalkDir returns nil)
		if rec.Code != http.StatusOK {
			t.Errorf("expected 200, got %d: %s", rec.Code, rec.Body.String())
		}
	})
}

func TestLogsListFilesHandler(t *testing.T) {
	srv, _, cleanup := setupTest(t)
	defer cleanup()

	mux := srv.NewTestMux()

	t.Run("list files by type returns 200", func(t *testing.T) {
		tmpDir := t.TempDir()
		os.WriteFile(filepath.Join(tmpDir, "a.fbc"), []byte("fbc"), 0644)
		os.WriteFile(filepath.Join(tmpDir, "b.rpc"), []byte("rpc"), 0644)

		rec := doRequest(mux, "GET", "/api/v1/logs/files?path="+tmpDir+"&type=fbc", nil, nil)
		if rec.Code != http.StatusOK {
			t.Errorf("expected 200, got %d: %s", rec.Code, rec.Body.String())
		}
		result := parseJSONResponse(rec)
		if result["type"] != "fbc" {
			t.Errorf("expected type fbc, got %v", result["type"])
		}
		count, ok := result["count"].(float64)
		if !ok || count != 1 {
			t.Errorf("expected count 1, got %v", result["count"])
		}
	})
}

func TestLogsContentHandler(t *testing.T) {
	srv, _, cleanup := setupTest(t)
	defer cleanup()

	mux := srv.NewTestMux()

	t.Run("get content of a file returns 200", func(t *testing.T) {
		tmpDir := t.TempDir()
		filePath := filepath.Join(tmpDir, "test.fbc")
		os.WriteFile(filePath, []byte("FBC content here"), 0644)

		rec := doRequest(mux, "GET", "/api/v1/logs/content?path="+filePath, nil, nil)
		if rec.Code != http.StatusOK {
			t.Errorf("expected 200, got %d: %s", rec.Code, rec.Body.String())
		}
		result := parseJSONResponse(rec)
		if result["content"] != "FBC content here" {
			t.Errorf("expected content 'FBC content here', got %v", result["content"])
		}
	})

	t.Run("get content missing path returns 400", func(t *testing.T) {
		rec := doRequest(mux, "GET", "/api/v1/logs/content", nil, nil)
		if rec.Code != http.StatusBadRequest {
			t.Errorf("expected 400, got %d", rec.Code)
		}
		result := parseJSONResponse(rec)
		if result["error"] != "validation_error" {
			t.Errorf("expected validation_error, got %v", result["error"])
		}
	})

	t.Run("get content non-existent file returns 404", func(t *testing.T) {
		rec := doRequest(mux, "GET", "/api/v1/logs/content?path=/nonexistent/file.fbc", nil, nil)
		if rec.Code != http.StatusNotFound {
			t.Errorf("expected 404, got %d", rec.Code)
		}
	})
}

func TestLogsSetRootHandler(t *testing.T) {
	srv, _, cleanup := setupTest(t)
	defer cleanup()

	mux := srv.NewTestMux()

	t.Run("setroot with valid path returns 200", func(t *testing.T) {
		tmpDir := t.TempDir()
		body := jsonBody(map[string]interface{}{
			"path": tmpDir,
		})
		rec := doRequest(mux, "POST", "/api/v1/logs/setroot", body, jsonHeader)
		if rec.Code != http.StatusOK {
			t.Errorf("expected 200, got %d: %s", rec.Code, rec.Body.String())
		}
		result := parseJSONResponse(rec)
		if result["set"] != true {
			t.Errorf("expected set true, got %v", result["set"])
		}
		if result["log_root"] != tmpDir {
			t.Errorf("expected log_root %s, got %v", tmpDir, result["log_root"])
		}
	})

	t.Run("setroot creates non-existent path returns 200", func(t *testing.T) {
		tmpDir := t.TempDir()
		newPath := filepath.Join(tmpDir, "newdir", "subdir")
		body := jsonBody(map[string]interface{}{
			"path": newPath,
		})
		rec := doRequest(mux, "POST", "/api/v1/logs/setroot", body, jsonHeader)
		if rec.Code != http.StatusOK {
			t.Errorf("expected 200, got %d: %s", rec.Code, rec.Body.String())
		}
		// Verify directory was created
		if _, err := os.Stat(newPath); err != nil {
			t.Errorf("expected directory to be created: %v", err)
		}
	})

	t.Run("setroot missing path returns 400", func(t *testing.T) {
		body := jsonBody(map[string]interface{}{})
		rec := doRequest(mux, "POST", "/api/v1/logs/setroot", body, jsonHeader)
		if rec.Code != http.StatusBadRequest {
			t.Errorf("expected 400, got %d", rec.Code)
		}
		result := parseJSONResponse(rec)
		if result["error"] != "validation_error" {
			t.Errorf("expected validation_error, got %v", result["error"])
		}
	})

	t.Run("setroot invalid JSON returns 400", func(t *testing.T) {
		rec := doRequest(mux, "POST", "/api/v1/logs/setroot", strings.NewReader("{bad"), jsonHeader)
		if rec.Code != http.StatusBadRequest {
			t.Errorf("expected 400, got %d", rec.Code)
		}
	})
}

func TestLogsCreateAndSaveHandler(t *testing.T) {
	srv, _, cleanup := setupTest(t)
	defer cleanup()

	mux := srv.NewTestMux()

	t.Run("create log file returns 200", func(t *testing.T) {
		tmpDir := t.TempDir()
		filePath := filepath.Join(tmpDir, "newfile.fbc")
		body := jsonBody(map[string]interface{}{
			"path": filePath,
		})
		rec := doRequest(mux, "POST", "/api/v1/logs/create", body, jsonHeader)
		if rec.Code != http.StatusOK {
			t.Errorf("expected 200, got %d: %s", rec.Code, rec.Body.String())
		}
		result := parseJSONResponse(rec)
		if result["created"] != true {
			t.Errorf("expected created true, got %v", result["created"])
		}
		// Verify file exists
		if _, err := os.Stat(filePath); err != nil {
			t.Errorf("expected file to exist: %v", err)
		}
	})

	t.Run("create log file conflict returns 409", func(t *testing.T) {
		tmpDir := t.TempDir()
		filePath := filepath.Join(tmpDir, "existing.fbc")
		os.WriteFile(filePath, []byte("existing"), 0644)

		body := jsonBody(map[string]interface{}{
			"path": filePath,
		})
		rec := doRequest(mux, "POST", "/api/v1/logs/create", body, jsonHeader)
		if rec.Code != http.StatusConflict {
			t.Errorf("expected 409, got %d: %s", rec.Code, rec.Body.String())
		}
		result := parseJSONResponse(rec)
		if result["error"] != "already_exists" {
			t.Errorf("expected already_exists, got %v", result["error"])
		}
	})

	t.Run("save log file returns 200", func(t *testing.T) {
		tmpDir := t.TempDir()
		filePath := filepath.Join(tmpDir, "saved.fbc")
		body := jsonBody(map[string]interface{}{
			"path":    filePath,
			"content": "saved content",
		})
		rec := doRequest(mux, "POST", "/api/v1/logs/save", body, jsonHeader)
		if rec.Code != http.StatusOK {
			t.Errorf("expected 200, got %d: %s", rec.Code, rec.Body.String())
		}
		result := parseJSONResponse(rec)
		if result["saved"] != true {
			t.Errorf("expected saved true, got %v", result["saved"])
		}
		// Verify content was written
		data, _ := os.ReadFile(filePath)
		if string(data) != "saved content" {
			t.Errorf("expected 'saved content', got %q", string(data))
		}
	})

	t.Run("read saved file via content endpoint", func(t *testing.T) {
		tmpDir := t.TempDir()
		filePath := filepath.Join(tmpDir, "readtest.fbc")
		// Save
		body := jsonBody(map[string]interface{}{
			"path":    filePath,
			"content": "test content for reading",
		})
		doRequest(mux, "POST", "/api/v1/logs/save", body, jsonHeader)

		// Read
		rec := doRequest(mux, "GET", "/api/v1/logs/content?path="+filePath, nil, nil)
		if rec.Code != http.StatusOK {
			t.Errorf("expected 200, got %d: %s", rec.Code, rec.Body.String())
		}
		result := parseJSONResponse(rec)
		if result["content"] != "test content for reading" {
			t.Errorf("expected 'test content for reading', got %v", result["content"])
		}
	})

	t.Run("save log file missing path returns 400", func(t *testing.T) {
		body := jsonBody(map[string]interface{}{
			"content": "no path",
		})
		rec := doRequest(mux, "POST", "/api/v1/logs/save", body, jsonHeader)
		if rec.Code != http.StatusBadRequest {
			t.Errorf("expected 400, got %d", rec.Code)
		}
	})
}

func TestLogsEraseHandler(t *testing.T) {
	srv, _, cleanup := setupTest(t)
	defer cleanup()

	mux := srv.NewTestMux()

	t.Run("erase log file returns 200", func(t *testing.T) {
		tmpDir := t.TempDir()
		filePath := filepath.Join(tmpDir, "erase.fbc")
		os.WriteFile(filePath, []byte("content to erase"), 0644)

		body := jsonBody(map[string]interface{}{
			"path": filePath,
		})
		rec := doRequest(mux, "POST", "/api/v1/logs/erase", body, jsonHeader)
		if rec.Code != http.StatusOK {
			t.Errorf("expected 200, got %d: %s", rec.Code, rec.Body.String())
		}
		result := parseJSONResponse(rec)
		if result["erased"] != true {
			t.Errorf("expected erased true, got %v", result["erased"])
		}
		// Verify file is empty
		info, _ := os.Stat(filePath)
		if info.Size() != 0 {
			t.Errorf("expected 0 bytes, got %d", info.Size())
		}
	})

	t.Run("erase non-existent file returns 404", func(t *testing.T) {
		body := jsonBody(map[string]interface{}{
			"path": "/nonexistent/file.fbc",
		})
		rec := doRequest(mux, "POST", "/api/v1/logs/erase", body, jsonHeader)
		if rec.Code != http.StatusNotFound {
			t.Errorf("expected 404, got %d", rec.Code)
		}
	})
}

func TestLogsDeleteHandler(t *testing.T) {
	srv, _, cleanup := setupTest(t)
	defer cleanup()

	mux := srv.NewTestMux()

	t.Run("delete log file returns 200", func(t *testing.T) {
		tmpDir := t.TempDir()
		filePath := filepath.Join(tmpDir, "delete.fbc")
		os.WriteFile(filePath, []byte("to be deleted"), 0644)

		body := jsonBody(map[string]interface{}{
			"path": filePath,
		})
		rec := doRequest(mux, "POST", "/api/v1/logs/delete", body, jsonHeader)
		if rec.Code != http.StatusOK {
			t.Errorf("expected 200, got %d: %s", rec.Code, rec.Body.String())
		}
		result := parseJSONResponse(rec)
		if result["deleted"] != true {
			t.Errorf("expected deleted true, got %v", result["deleted"])
		}
		// Verify file is gone
		if _, err := os.Stat(filePath); !os.IsNotExist(err) {
			t.Error("expected file to be deleted")
		}
	})

	t.Run("delete non-existent file returns 404", func(t *testing.T) {
		body := jsonBody(map[string]interface{}{
			"path": "/nonexistent/delete.fbc",
		})
		rec := doRequest(mux, "POST", "/api/v1/logs/delete", body, jsonHeader)
		if rec.Code != http.StatusNotFound {
			t.Errorf("expected 404, got %d", rec.Code)
		}
	})
}

func TestLogsMoveHandler(t *testing.T) {
	srv, _, cleanup := setupTest(t)
	defer cleanup()

	mux := srv.NewTestMux()

	t.Run("move log file returns 200", func(t *testing.T) {
		tmpDir := t.TempDir()
		srcDir := filepath.Join(tmpDir, "src")
		dstDir := filepath.Join(tmpDir, "dst")
		os.MkdirAll(srcDir, 0755)
		os.MkdirAll(dstDir, 0755)
		srcPath := filepath.Join(srcDir, "move.fbc")
		dstPath := filepath.Join(dstDir, "move.fbc")
		os.WriteFile(srcPath, []byte("move me"), 0644)

		body := jsonBody(map[string]interface{}{
			"source_path": srcPath,
			"target_path": dstPath,
		})
		rec := doRequest(mux, "POST", "/api/v1/logs/move", body, jsonHeader)
		if rec.Code != http.StatusOK {
			t.Errorf("expected 200, got %d: %s", rec.Code, rec.Body.String())
		}
		result := parseJSONResponse(rec)
		if result["moved"] != true {
			t.Errorf("expected moved true, got %v", result["moved"])
		}
		// Verify source is gone and target exists
		if _, err := os.Stat(srcPath); !os.IsNotExist(err) {
			t.Error("expected source file to be gone")
		}
		if _, err := os.Stat(dstPath); err != nil {
			t.Error("expected target file to exist")
		}
	})

	t.Run("move non-existent source returns 404", func(t *testing.T) {
		body := jsonBody(map[string]interface{}{
			"source_path": "/nonexistent/src.fbc",
			"target_path": "/tmp/dst.fbc",
		})
		rec := doRequest(mux, "POST", "/api/v1/logs/move", body, jsonHeader)
		if rec.Code != http.StatusNotFound {
			t.Errorf("expected 404, got %d", rec.Code)
		}
	})

	t.Run("move missing source_path returns 400", func(t *testing.T) {
		body := jsonBody(map[string]interface{}{})
		rec := doRequest(mux, "POST", "/api/v1/logs/move", body, jsonHeader)
		if rec.Code != http.StatusBadRequest {
			t.Errorf("expected 400, got %d", rec.Code)
		}
	})
}

func TestLogsCreateFolderHandler(t *testing.T) {
	srv, _, cleanup := setupTest(t)
	defer cleanup()

	mux := srv.NewTestMux()

	t.Run("create folder returns 200", func(t *testing.T) {
		tmpDir := t.TempDir()
		newFolder := filepath.Join(tmpDir, "newfolder")
		body := jsonBody(map[string]interface{}{
			"path": newFolder,
		})
		rec := doRequest(mux, "POST", "/api/v1/logs/create-folder", body, jsonHeader)
		if rec.Code != http.StatusOK {
			t.Errorf("expected 200, got %d: %s", rec.Code, rec.Body.String())
		}
		result := parseJSONResponse(rec)
		if result["created"] != true {
			t.Errorf("expected created true, got %v", result["created"])
		}
		// Verify folder exists
		info, _ := os.Stat(newFolder)
		if info == nil || !info.IsDir() {
			t.Error("expected folder to exist")
		}
	})

	t.Run("create existing folder returns 409", func(t *testing.T) {
		tmpDir := t.TempDir()
		existing := filepath.Join(tmpDir, "existing")
		os.MkdirAll(existing, 0755)

		body := jsonBody(map[string]interface{}{
			"path": existing,
		})
		rec := doRequest(mux, "POST", "/api/v1/logs/create-folder", body, jsonHeader)
		if rec.Code != http.StatusConflict {
			t.Errorf("expected 409, got %d", rec.Code)
		}
	})
}

func TestBrowseDirHandler(t *testing.T) {
	srv, _, cleanup := setupTest(t)
	defer cleanup()

	mux := srv.NewTestMux()

	t.Run("browse with path returns 200", func(t *testing.T) {
		tmpDir := t.TempDir()
		// Create subdirectories
		os.MkdirAll(filepath.Join(tmpDir, "sub1"), 0755)
		os.MkdirAll(filepath.Join(tmpDir, "sub2"), 0755)
		// Create a file (should NOT be listed)
		os.WriteFile(filepath.Join(tmpDir, "file.txt"), []byte("x"), 0644)

		rec := doRequest(mux, "GET", "/api/v1/browse?path="+tmpDir, nil, nil)
		if rec.Code != http.StatusOK {
			t.Errorf("expected 200, got %d: %s", rec.Code, rec.Body.String())
		}
		result := parseJSONResponse(rec)
		entries, ok := result["entries"].([]interface{})
		if !ok {
			t.Errorf("expected entries array, got %T", result["entries"])
		}
		// Should have 2 directories (sub1, sub2) but NOT file.txt
		if len(entries) != 2 {
			t.Errorf("expected 2 entries (dirs only), got %d", len(entries))
		}
	})

	t.Run("browse without path returns root dirs 200", func(t *testing.T) {
		rec := doRequest(mux, "GET", "/api/v1/browse", nil, nil)
		if rec.Code != http.StatusOK {
			t.Errorf("expected 200, got %d", rec.Code)
		}
		result := parseJSONResponse(rec)
		entries, ok := result["entries"].([]interface{})
		if !ok {
			t.Errorf("expected entries array, got %T", result["entries"])
		}
		// On Linux, should list root dirs
		if len(entries) == 0 {
			t.Error("expected at least some root entries on Linux")
		}
	})
}

func TestLogsWriteByNodeHandler(t *testing.T) {
	srv, _, cleanup := setupTest(t)
	defer cleanup()

	// Set a temp log root
	tmpDir := t.TempDir()
	srv.SetLogRoot(tmpDir)

	mux := srv.NewTestMux()

	t.Run("write log by node returns 200", func(t *testing.T) {
		body := jsonBody(map[string]interface{}{
			"token_type": "FBC",
			"token_id":   "162",
			"output":     "FBC scan output here",
		})
		rec := doRequest(mux, "POST", "/api/v1/logs/AP01m", body, jsonHeader)
		if rec.Code != http.StatusOK {
			t.Errorf("expected 200, got %d: %s", rec.Code, rec.Body.String())
		}
		result := parseJSONResponse(rec)
		if result["written"] != true {
			t.Errorf("expected written true, got %v", result["written"])
		}
	})

	t.Run("write log missing token fields returns 400", func(t *testing.T) {
		body := jsonBody(map[string]interface{}{
			"output": "no token",
		})
		rec := doRequest(mux, "POST", "/api/v1/logs/AP01m", body, jsonHeader)
		if rec.Code != http.StatusBadRequest {
			t.Errorf("expected 400, got %d", rec.Code)
		}
	})

	t.Run("write log invalid JSON returns 400", func(t *testing.T) {
		rec := doRequest(mux, "POST", "/api/v1/logs/AP01m", strings.NewReader("{bad"), jsonHeader)
		if rec.Code != http.StatusBadRequest {
			t.Errorf("expected 400, got %d", rec.Code)
		}
	})
}

func TestLogsReadByNodeHandler(t *testing.T) {
	srv, _, cleanup := setupTest(t)
	defer cleanup()

	// Set a temp log root and write a file
	tmpDir := t.TempDir()
	srv.SetLogRoot(tmpDir)

	mux := srv.NewTestMux()

	// Write a file first
	body := jsonBody(map[string]interface{}{
		"token_type": "FBC",
		"token_id":   "162",
		"output":     "test output for reading",
	})
	doRequest(mux, "POST", "/api/v1/logs/AP01m", body, jsonHeader)

	t.Run("read log by node returns 200", func(t *testing.T) {
		rec := doRequest(mux, "GET", "/api/v1/logs/AP01m/fbc_162.log", nil, nil)
		if rec.Code != http.StatusOK {
			t.Errorf("expected 200, got %d: %s", rec.Code, rec.Body.String())
		}
		result := parseJSONResponse(rec)
		if result["node_name"] != "AP01m" {
			t.Errorf("expected node_name AP01m, got %v", result["node_name"])
		}
	})

	t.Run("read log non-existent file returns 404", func(t *testing.T) {
		rec := doRequest(mux, "GET", "/api/v1/logs/AP01m/fbc_999.log", nil, nil)
		if rec.Code != http.StatusNotFound {
			t.Errorf("expected 404, got %d", rec.Code)
		}
	})

	t.Run("read log invalid filename format returns 400", func(t *testing.T) {
		rec := doRequest(mux, "GET", "/api/v1/logs/AP01m/badfilename", nil, nil)
		if rec.Code != http.StatusBadRequest {
			t.Errorf("expected 400, got %d", rec.Code)
		}
	})
}

func TestLogsListByNodeHandler(t *testing.T) {
	srv, _, cleanup := setupTest(t)
	defer cleanup()

	tmpDir := t.TempDir()
	srv.SetLogRoot(tmpDir)

	mux := srv.NewTestMux()

	t.Run("list logs by node returns 200", func(t *testing.T) {
		rec := doRequest(mux, "GET", "/api/v1/logs/AP01m", nil, nil)
		if rec.Code != http.StatusOK {
			t.Errorf("expected 200, got %d: %s", rec.Code, rec.Body.String())
		}
		result := parseJSONResponse(rec)
		if result["node_name"] != "AP01m" {
			t.Errorf("expected node_name AP01m, got %v", result["node_name"])
		}
		// logs and count should be present
		if _, ok := result["logs"]; !ok {
			t.Error("expected logs field")
		}
		if _, ok := result["count"]; !ok {
			t.Error("expected count field")
		}
	})
}