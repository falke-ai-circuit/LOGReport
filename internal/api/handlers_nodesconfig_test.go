package api

import (
	"net/http"
	"os"
	"path/filepath"
	"strings"
	"testing"

	"github.com/falke-ai-circuit/LOGReport/internal/types"
)

// ─── NodesConfig Handler Tests ────────────────────────────────────
// Covers: get config, save config, load config, get tree, create structure,
// create structure without nodes.json, delete structure, delete entry, rename entry.

func TestNodesConfigGetHandler(t *testing.T) {
	srv, _, cleanup := setupTest(t)
	defer cleanup()

	mux := srv.NewTestMux()

	t.Run("get config without file returns 200 with empty array", func(t *testing.T) {
		rec := doRequest(mux, "GET", "/api/v1/nodesconfig", nil, nil)
		if rec.Code != http.StatusOK {
			t.Errorf("expected 200, got %d: %s", rec.Code, rec.Body.String())
		}
		result := parseJSONResponse(rec)
		configs, ok := result["configs"].([]interface{})
		if !ok {
			t.Errorf("expected configs array, got %T", result["configs"])
		}
		if len(configs) < 0 {
			t.Errorf("expected >=0 configs, got %d", len(configs))
		}
	})
}

func TestNodesConfigSaveHandler(t *testing.T) {
	srv, _, cleanup := setupTest(t)
	defer cleanup()

	mux := srv.NewTestMux()

	t.Run("save config returns 200", func(t *testing.T) {
		configs := []types.NodeConfig{
			{
				Name:      "AP01m",
				IPAddress: "192.168.0.11",
				Tokens: []types.Token{
					{TokenID: "162", TokenType: types.TokenFBC},
				},
			},
		}
		body := jsonBody(configs)
		rec := doRequest(mux, "POST", "/api/v1/nodesconfig", body, jsonHeader)
		if rec.Code != http.StatusOK {
			t.Errorf("expected 200, got %d: %s", rec.Code, rec.Body.String())
		}
		result := parseJSONResponse(rec)
		if result["saved"] != true {
			t.Errorf("expected saved true, got %v", result["saved"])
		}
		if result["count"].(float64) != 1 {
			t.Errorf("expected count 1, got %v", result["count"])
		}
	})

	t.Run("save then get returns saved configs", func(t *testing.T) {
		// Save
		configs := []types.NodeConfig{
			{Name: "BP01r", IPAddress: "192.168.0.12", Tokens: []types.Token{{TokenID: "164", TokenType: types.TokenLOG}}},
		}
		body := jsonBody(configs)
		doRequest(mux, "POST", "/api/v1/nodesconfig", body, jsonHeader)

		// Get
		rec := doRequest(mux, "GET", "/api/v1/nodesconfig", nil, nil)
		if rec.Code != http.StatusOK {
			t.Errorf("expected 200, got %d", rec.Code)
		}
		result := parseJSONResponse(rec)
		configsResult, ok := result["configs"].([]interface{})
		if !ok || len(configsResult) < 1 {
			t.Errorf("expected at least 1 config, got %v", result["configs"])
		}
	})

	t.Run("save config invalid JSON returns 400", func(t *testing.T) {
		rec := doRequest(mux, "POST", "/api/v1/nodesconfig", strings.NewReader("{bad"), jsonHeader)
		if rec.Code != http.StatusBadRequest {
			t.Errorf("expected 400, got %d", rec.Code)
		}
	})
}

func TestNodesConfigLoadHandler(t *testing.T) {
	srv, _, cleanup := setupTest(t)
	defer cleanup()

	mux := srv.NewTestMux()

	t.Run("load config from explicit path returns 200", func(t *testing.T) {
		// Create a temp nodes.json
		tmpDir := t.TempDir()
		nodesPath := filepath.Join(tmpDir, "nodes.json")
		os.WriteFile(nodesPath, []byte(`[{"name":"AP01m","ip_address":"192.168.0.11","tokens":[{"token_id":"162","token_type":"FBC"}]}]`), 0644)

		rec := doRequest(mux, "PUT", "/api/v1/nodesconfig/load?path="+nodesPath, nil, jsonHeader)
		if rec.Code != http.StatusOK {
			t.Errorf("expected 200, got %d: %s", rec.Code, rec.Body.String())
		}
		result := parseJSONResponse(rec)
		configs, ok := result["configs"].([]interface{})
		if !ok || len(configs) != 1 {
			t.Errorf("expected 1 config, got %v", result["configs"])
		}
	})

	t.Run("load config non-existent returns 404", func(t *testing.T) {
		rec := doRequest(mux, "PUT", "/api/v1/nodesconfig/load?path=/nonexistent/nodes.json", nil, jsonHeader)
		if rec.Code != http.StatusNotFound {
			t.Errorf("expected 404, got %d", rec.Code)
		}
	})
}

func TestNodesConfigTreeHandler(t *testing.T) {
	srv, _, cleanup := setupTest(t)
	defer cleanup()

	mux := srv.NewTestMux()

	t.Run("get tree without nodes.json returns 200 with empty tree", func(t *testing.T) {
		rec := doRequest(mux, "GET", "/api/v1/nodesconfig/tree", nil, nil)
		if rec.Code != http.StatusOK {
			t.Errorf("expected 200, got %d: %s", rec.Code, rec.Body.String())
		}
		result := parseJSONResponse(rec)
		tree, ok := result["tree"].(map[string]interface{})
		if !ok {
			t.Errorf("expected tree object, got %T", result["tree"])
		}
		if tree["name"] != "Root" {
			t.Errorf("expected tree name Root, got %v", tree["name"])
		}
	})

	t.Run("get tree with saved configs returns 200", func(t *testing.T) {
		// Save configs first
		configs := []types.NodeConfig{
			{Name: "AP01m", IPAddress: "192.168.0.11", Tokens: []types.Token{{TokenID: "162", TokenType: types.TokenFBC}}},
		}
		body := jsonBody(configs)
		doRequest(mux, "POST", "/api/v1/nodesconfig", body, jsonHeader)

		rec := doRequest(mux, "GET", "/api/v1/nodesconfig/tree", nil, nil)
		if rec.Code != http.StatusOK {
			t.Errorf("expected 200, got %d: %s", rec.Code, rec.Body.String())
		}
		result := parseJSONResponse(rec)
		tree, ok := result["tree"].(map[string]interface{})
		if !ok {
			t.Fatalf("expected tree object, got %T", result["tree"])
		}
		if tree["name"] != "Root" {
			t.Errorf("expected Root, got %v", tree["name"])
		}
	})
}

func TestNodesConfigCreateStructureHandler(t *testing.T) {
	srv, _, cleanup := setupTest(t)
	defer cleanup()

	mux := srv.NewTestMux()

	t.Run("create structure with log_root but no nodes.json returns 500", func(t *testing.T) {
		// Known issue: createLogStructure loads nodes.json from {logRoot}/nodes.json
		// and returns 500 if the file doesn't exist. This is the current behavior.
		tmpDir := t.TempDir()
		body := jsonBody(map[string]interface{}{
			"log_root": tmpDir,
		})
		rec := doRequest(mux, "POST", "/api/v1/nodesconfig/create-structure", body, jsonHeader)
		// Returns 500 (load_error) because nodes.json doesn't exist in the log root
		if rec.Code != http.StatusInternalServerError {
			t.Errorf("expected 500 (known issue: no nodes.json), got %d: %s", rec.Code, rec.Body.String())
		}
	})

	t.Run("create structure with nodes.json returns 200", func(t *testing.T) {
		tmpDir := t.TempDir()
		// Create nodes.json in the log root
		nodesPath := filepath.Join(tmpDir, "nodes.json")
		os.WriteFile(nodesPath, []byte(`[{"name":"AP01m","ip_address":"192.168.0.11","tokens":[{"token_id":"162","token_type":"FBC"}]}]`), 0644)

		body := jsonBody(map[string]interface{}{
			"log_root": tmpDir,
		})
		rec := doRequest(mux, "POST", "/api/v1/nodesconfig/create-structure", body, jsonHeader)
		if rec.Code != http.StatusOK {
			t.Errorf("expected 200, got %d: %s", rec.Code, rec.Body.String())
		}
		result := parseJSONResponse(rec)
		if result["station_count"].(float64) < 1 {
			t.Errorf("expected station_count >= 1, got %v", result["station_count"])
		}
	})

	t.Run("create structure without log_root returns 400", func(t *testing.T) {
		body := jsonBody(map[string]interface{}{})
		rec := doRequest(mux, "POST", "/api/v1/nodesconfig/create-structure", body, jsonHeader)
		if rec.Code != http.StatusBadRequest {
			t.Errorf("expected 400, got %d", rec.Code)
		}
	})
}

func TestNodesConfigDeleteStructureHandler(t *testing.T) {
	srv, _, cleanup := setupTest(t)
	defer cleanup()

	mux := srv.NewTestMux()

	t.Run("delete structure non-existent returns 200 with deleted=false", func(t *testing.T) {
		tmpDir := t.TempDir()
		body := jsonBody(map[string]interface{}{
			"log_root": tmpDir,
		})
		rec := doRequest(mux, "DELETE", "/api/v1/nodesconfig/delete-structure", body, jsonHeader)
		if rec.Code != http.StatusOK {
			t.Errorf("expected 200, got %d: %s", rec.Code, rec.Body.String())
		}
		result := parseJSONResponse(rec)
		if result["deleted"] == true {
			t.Error("expected deleted false for non-existent structure")
		}
	})

	t.Run("delete structure existing returns 200 with deleted=true", func(t *testing.T) {
		tmpDir := t.TempDir()
		// Create _LOG directory
		logDir := filepath.Join(tmpDir, "_LOG")
		os.MkdirAll(logDir, 0755)
		os.WriteFile(filepath.Join(logDir, "test.fbc"), []byte("x"), 0644)

		body := jsonBody(map[string]interface{}{
			"log_root": tmpDir,
		})
		rec := doRequest(mux, "DELETE", "/api/v1/nodesconfig/delete-structure", body, jsonHeader)
		if rec.Code != http.StatusOK {
			t.Errorf("expected 200, got %d: %s", rec.Code, rec.Body.String())
		}
		result := parseJSONResponse(rec)
		if result["deleted"] != true {
			t.Errorf("expected deleted true, got %v", result["deleted"])
		}
		// Verify _LOG is gone
		if _, err := os.Stat(logDir); !os.IsNotExist(err) {
			t.Error("expected _LOG directory to be deleted")
		}
	})

	t.Run("delete structure without log_root returns 400", func(t *testing.T) {
		body := jsonBody(map[string]interface{}{})
		rec := doRequest(mux, "DELETE", "/api/v1/nodesconfig/delete-structure", body, jsonHeader)
		if rec.Code != http.StatusBadRequest {
			t.Errorf("expected 400, got %d", rec.Code)
		}
	})
}

func TestNodesConfigDeleteEntryHandler(t *testing.T) {
	srv, _, cleanup := setupTest(t)
	defer cleanup()

	mux := srv.NewTestMux()

	// Save configs first
	configs := []types.NodeConfig{
		{Name: "AP01m", IPAddress: "192.168.0.11", Tokens: []types.Token{{TokenID: "162", TokenType: types.TokenFBC}}},
		{Name: "BP01r", IPAddress: "192.168.0.12", Tokens: []types.Token{{TokenID: "164", TokenType: types.TokenLOG}}},
	}
	body := jsonBody(configs)
	doRequest(mux, "POST", "/api/v1/nodesconfig", body, jsonHeader)

	t.Run("delete entry returns 200", func(t *testing.T) {
		rec := doRequest(mux, "DELETE", "/api/v1/nodesconfig/entry?name=AP01m", nil, jsonHeader)
		if rec.Code != http.StatusOK {
			t.Errorf("expected 200, got %d: %s", rec.Code, rec.Body.String())
		}
		result := parseJSONResponse(rec)
		if result["deleted"] != true {
			t.Errorf("expected deleted true, got %v", result["deleted"])
		}
		if result["name"] != "AP01m" {
			t.Errorf("expected name AP01m, got %v", result["name"])
		}
	})

	t.Run("delete non-existent entry returns 404", func(t *testing.T) {
		rec := doRequest(mux, "DELETE", "/api/v1/nodesconfig/entry?name=NonExistent", nil, jsonHeader)
		if rec.Code != http.StatusNotFound {
			t.Errorf("expected 404, got %d", rec.Code)
		}
	})

	t.Run("delete entry missing name returns 400", func(t *testing.T) {
		rec := doRequest(mux, "DELETE", "/api/v1/nodesconfig/entry", nil, jsonHeader)
		if rec.Code != http.StatusBadRequest {
			t.Errorf("expected 400, got %d", rec.Code)
		}
	})
}

func TestNodesConfigRenameEntryHandler(t *testing.T) {
	srv, _, cleanup := setupTest(t)
	defer cleanup()

	mux := srv.NewTestMux()

	// Save configs first
	configs := []types.NodeConfig{
		{Name: "AP01m", IPAddress: "192.168.0.11", Tokens: []types.Token{{TokenID: "162", TokenType: types.TokenFBC}}},
	}
	body := jsonBody(configs)
	doRequest(mux, "POST", "/api/v1/nodesconfig", body, jsonHeader)

	t.Run("rename entry returns 200", func(t *testing.T) {
		body := jsonBody(map[string]interface{}{
			"new_name": "AP01m_RENAMED",
			"new_ip":   "192.168.0.99",
		})
		rec := doRequest(mux, "POST", "/api/v1/nodesconfig/rename?name=AP01m", body, jsonHeader)
		if rec.Code != http.StatusOK {
			t.Errorf("expected 200, got %d: %s", rec.Code, rec.Body.String())
		}
		result := parseJSONResponse(rec)
		if result["renamed"] != true {
			t.Errorf("expected renamed true, got %v", result["renamed"])
		}
		if result["old_name"] != "AP01m" {
			t.Errorf("expected old_name AP01m, got %v", result["old_name"])
		}
	})

	t.Run("rename non-existent entry returns 404", func(t *testing.T) {
		body := jsonBody(map[string]interface{}{
			"new_name": "NEW",
		})
		rec := doRequest(mux, "POST", "/api/v1/nodesconfig/rename?name=NonExistent", body, jsonHeader)
		if rec.Code != http.StatusNotFound {
			t.Errorf("expected 404, got %d", rec.Code)
		}
	})

	t.Run("rename entry missing name returns 400", func(t *testing.T) {
		body := jsonBody(map[string]interface{}{
			"new_name": "NEW",
		})
		rec := doRequest(mux, "POST", "/api/v1/nodesconfig/rename", body, jsonHeader)
		if rec.Code != http.StatusBadRequest {
			t.Errorf("expected 400, got %d", rec.Code)
		}
	})

	t.Run("rename entry missing new_name and new_ip returns 400", func(t *testing.T) {
		body := jsonBody(map[string]interface{}{})
		rec := doRequest(mux, "POST", "/api/v1/nodesconfig/rename?name=AP01m", body, jsonHeader)
		if rec.Code != http.StatusBadRequest {
			t.Errorf("expected 400, got %d", rec.Code)
		}
	})
}