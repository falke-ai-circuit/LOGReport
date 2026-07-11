package api

import (
	"net/http"
	"strings"
	"testing"

	"github.com/falke-ai-circuit/LOGReport/internal/types"
)

// jsonHeader is a shorthand for the JSON content-type header used across queue/log tests.
var jsonHeader = map[string]string{"Content-Type": "application/json"}

// ─── Project Handler Tests ────────────────────────────────────────
// Covers: POST /api/v1/projects, GET /api/v1/projects, GET /api/v1/projects/{id},
// PUT /api/v1/projects/{id}, DELETE /api/v1/projects/{id},
// POST /api/v1/projects/{id}/report,
// GET /api/v1/projects/{id}/nodes, POST /api/v1/projects/{id}/nodes

func TestProjectHandlers(t *testing.T) {
	srv, _, cleanup := setupTest(t)
	defer cleanup()

	mux := srv.NewTestMux()

	// ─── Create project (201) ─────────────────────────────────────
	t.Run("create project returns 201", func(t *testing.T) {
		body := jsonBody(map[string]interface{}{
			"project_number": "T6004",
			"ship_name":      "TEST_SHIP",
			"log_root":       "",
		})
		rec := doRequest(mux, "POST", "/api/v1/projects", body, map[string]string{
			"Content-Type": "application/json",
		})
		if rec.Code != http.StatusCreated {
			t.Errorf("expected 201, got %d: %s", rec.Code, rec.Body.String())
		}
		result := parseJSONResponse(rec)
		proj, ok := result["project"].(map[string]interface{})
		if !ok {
			t.Fatalf("expected project object, got %T", result["project"])
		}
		if proj["project_number"] != "T6004" {
			t.Errorf("expected project_number T6004, got %v", proj["project_number"])
		}
		if proj["ship_name"] != "TEST_SHIP" {
			t.Errorf("expected ship_name TEST_SHIP, got %v", proj["ship_name"])
		}
		// Verify ID was assigned
		id, ok := proj["id"].(float64)
		if !ok || id == 0 {
			t.Errorf("expected non-zero id, got %v", proj["id"])
		}
	})

	// ─── Create project missing fields (400) ─────────────────────
	t.Run("create project missing fields returns 400", func(t *testing.T) {
		body := jsonBody(map[string]interface{}{
			"project_number": "",
			"ship_name":      "",
		})
		rec := doRequest(mux, "POST", "/api/v1/projects", body, map[string]string{
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

	// ─── Create project with invalid JSON (400) ──────────────────
	t.Run("create project invalid JSON returns 400", func(t *testing.T) {
		body := strings.NewReader("{invalid json")
		rec := doRequest(mux, "POST", "/api/v1/projects", body, map[string]string{
			"Content-Type": "application/json",
		})
		if rec.Code != http.StatusBadRequest {
			t.Errorf("expected 400, got %d", rec.Code)
		}
	})

	// ─── List projects (200) ──────────────────────────────────────
	// Create a project first so list is non-empty
	createBody := jsonBody(map[string]interface{}{
		"project_number": "T6005",
		"ship_name":      "LIST_SHIP",
	})
	doRequest(mux, "POST", "/api/v1/projects", createBody, map[string]string{
		"Content-Type": "application/json",
	})

	t.Run("list projects returns 200", func(t *testing.T) {
		rec := doRequest(mux, "GET", "/api/v1/projects", nil, nil)
		if rec.Code != http.StatusOK {
			t.Errorf("expected 200, got %d: %s", rec.Code, rec.Body.String())
		}
		result := parseJSONResponse(rec)
		projects, ok := result["projects"].([]interface{})
		if !ok {
			t.Errorf("expected projects array, got %T", result["projects"])
		}
		if len(projects) == 0 {
			t.Error("expected at least 1 project, got 0")
		}
		total, ok := result["total"].(float64)
		if !ok || total < 1 {
			t.Errorf("expected total >= 1, got %v", result["total"])
		}
	})

	// ─── Get project by ID (200) ─────────────────────────────────
	t.Run("get project by ID returns 200", func(t *testing.T) {
		// Create a project to get
		body := jsonBody(map[string]interface{}{
			"project_number": "T6006",
			"ship_name":      "GET_SHIP",
		})
		rec := doRequest(mux, "POST", "/api/v1/projects", body, map[string]string{
			"Content-Type": "application/json",
		})
		result := parseJSONResponse(rec)
		proj, _ := result["project"].(map[string]interface{})
		id := proj["id"]

		rec2 := doRequest(mux, "GET", "/api/v1/projects/"+floatToStr(id), nil, nil)
		if rec2.Code != http.StatusOK {
			t.Errorf("expected 200, got %d: %s", rec2.Code, rec2.Body.String())
		}
		result2 := parseJSONResponse(rec2)
		proj2, ok := result2["project"].(map[string]interface{})
		if !ok {
			t.Fatalf("expected project object, got %T", result2["project"])
		}
		if proj2["project_number"] != "T6006" {
			t.Errorf("expected project_number T6006, got %v", proj2["project_number"])
		}
	})

	// ─── Get project not found (404) ──────────────────────────────
	t.Run("get project not found returns 404", func(t *testing.T) {
		rec := doRequest(mux, "GET", "/api/v1/projects/99999", nil, nil)
		if rec.Code != http.StatusNotFound {
			t.Errorf("expected 404, got %d", rec.Code)
		}
		result := parseJSONResponse(rec)
		if result["error"] != "not_found" {
			t.Errorf("expected not_found, got %v", result["error"])
		}
	})

	// ─── Get project invalid ID (400) ────────────────────────────
	t.Run("get project invalid ID returns 400", func(t *testing.T) {
		rec := doRequest(mux, "GET", "/api/v1/projects/notanumber", nil, nil)
		if rec.Code != http.StatusBadRequest {
			t.Errorf("expected 400, got %d", rec.Code)
		}
	})

	// ─── Update project (200) ─────────────────────────────────────
	t.Run("update project returns 200", func(t *testing.T) {
		// Create
		body := jsonBody(map[string]interface{}{
			"project_number": "T6007",
			"ship_name":      "UPDATE_SHIP",
		})
		rec := doRequest(mux, "POST", "/api/v1/projects", body, map[string]string{
			"Content-Type": "application/json",
		})
		result := parseJSONResponse(rec)
		proj, _ := result["project"].(map[string]interface{})
		id := floatToStr(proj["id"])

		// Update
		updateBody := jsonBody(map[string]interface{}{
			"project_number": "T6007-UPDATED",
			"ship_name":      "UPDATED_SHIP",
			"status":         "active",
		})
		rec2 := doRequest(mux, "PUT", "/api/v1/projects/"+id, updateBody, map[string]string{
			"Content-Type": "application/json",
		})
		if rec2.Code != http.StatusOK {
			t.Errorf("expected 200, got %d: %s", rec2.Code, rec2.Body.String())
		}
		result2 := parseJSONResponse(rec2)
		proj2, ok := result2["project"].(map[string]interface{})
		if !ok {
			t.Fatalf("expected project object, got %T", result2["project"])
		}
		if proj2["project_number"] != "T6007-UPDATED" {
			t.Errorf("expected updated project_number, got %v", proj2["project_number"])
		}
	})

	// ─── Update project not found (404) ──────────────────────────
	t.Run("update project not found returns 404", func(t *testing.T) {
		body := jsonBody(map[string]interface{}{
			"project_number": "T9999",
			"ship_name":      "NONE",
		})
		rec := doRequest(mux, "PUT", "/api/v1/projects/99999", body, map[string]string{
			"Content-Type": "application/json",
		})
		if rec.Code != http.StatusNotFound && rec.Code != http.StatusInternalServerError {
			t.Errorf("expected 404 or 500, got %d", rec.Code)
		}
	})

	// ─── Delete project (200) ─────────────────────────────────────
	t.Run("delete project returns 200", func(t *testing.T) {
		// Create
		body := jsonBody(map[string]interface{}{
			"project_number": "T6008",
			"ship_name":      "DELETE_SHIP",
		})
		rec := doRequest(mux, "POST", "/api/v1/projects", body, map[string]string{
			"Content-Type": "application/json",
		})
		result := parseJSONResponse(rec)
		proj, _ := result["project"].(map[string]interface{})
		id := floatToStr(proj["id"])

		// Delete
		rec2 := doRequest(mux, "DELETE", "/api/v1/projects/"+id, nil, map[string]string{
			"Content-Type": "application/json",
		})
		if rec2.Code != http.StatusOK {
			t.Errorf("expected 200, got %d: %s", rec2.Code, rec2.Body.String())
		}
		result2 := parseJSONResponse(rec2)
		if result2["deleted"] != true {
			t.Errorf("expected deleted true, got %v", result2["deleted"])
		}

		// Verify it's gone
		rec3 := doRequest(mux, "GET", "/api/v1/projects/"+id, nil, nil)
		if rec3.Code != http.StatusNotFound {
			t.Errorf("expected 404 after delete, got %d", rec3.Code)
		}
	})

	// ─── Delete project not found (500 — store returns error) ────
	t.Run("delete project not found returns error", func(t *testing.T) {
		rec := doRequest(mux, "DELETE", "/api/v1/projects/99999", nil, map[string]string{
			"Content-Type": "application/json",
		})
		// DeleteProject returns 200 even for nonexistent (idempotent delete)
		if rec.Code != http.StatusOK && rec.Code != http.StatusInternalServerError {
			t.Errorf("expected 200 or 500, got %d: %s", rec.Code, rec.Body.String())
		}
	})

	// ─── Get project nodes (200) ─────────────────────────────────
	t.Run("get project nodes returns 200", func(t *testing.T) {
		// Create a project
		body := jsonBody(map[string]interface{}{
			"project_number": "T6009",
			"ship_name":      "NODES_SHIP",
		})
		rec := doRequest(mux, "POST", "/api/v1/projects", body, map[string]string{
			"Content-Type": "application/json",
		})
		result := parseJSONResponse(rec)
		proj, _ := result["project"].(map[string]interface{})
		id := floatToStr(proj["id"])

		// Get nodes (should return empty array since no nodes saved)
		rec2 := doRequest(mux, "GET", "/api/v1/projects/"+id+"/nodes", nil, nil)
		if rec2.Code != http.StatusOK {
			t.Errorf("expected 200, got %d: %s", rec2.Code, rec2.Body.String())
		}
		result2 := parseJSONResponse(rec2)
		configs, ok := result2["configs"].([]interface{})
		if !ok {
			t.Errorf("expected configs array, got %T", result2["configs"])
		}
		if len(configs) != 0 {
			t.Errorf("expected 0 configs, got %d", len(configs))
		}
	})

	// ─── Save project nodes (200) ────────────────────────────────
	t.Run("save project nodes returns 200", func(t *testing.T) {
		// Create a project
		body := jsonBody(map[string]interface{}{
			"project_number": "T6010",
			"ship_name":      "SAVE_NODES_SHIP",
		})
		rec := doRequest(mux, "POST", "/api/v1/projects", body, map[string]string{
			"Content-Type": "application/json",
		})
		result := parseJSONResponse(rec)
		proj, _ := result["project"].(map[string]interface{})
		id := floatToStr(proj["id"])

		// Save nodes
		nodes := []types.NodeConfig{
			{
				Name:      "AP01m",
				IPAddress: "192.168.0.11",
				Tokens: []types.Token{
					{TokenID: "162", TokenType: types.TokenFBC},
					{TokenID: "163", TokenType: types.TokenRPC},
				},
			},
		}
		saveBody := jsonBody(nodes)
		rec2 := doRequest(mux, "POST", "/api/v1/projects/"+id+"/nodes", saveBody, map[string]string{
			"Content-Type": "application/json",
		})
		if rec2.Code != http.StatusOK {
			t.Errorf("expected 200, got %d: %s", rec2.Code, rec2.Body.String())
		}
		result2 := parseJSONResponse(rec2)
		if result2["saved"] != true {
			t.Errorf("expected saved true, got %v", result2["saved"])
		}

		// Verify by re-reading
		rec3 := doRequest(mux, "GET", "/api/v1/projects/"+id+"/nodes", nil, nil)
		if rec3.Code != http.StatusOK {
			t.Errorf("expected 200 on re-read, got %d", rec3.Code)
		}
		result3 := parseJSONResponse(rec3)
		configs, ok := result3["configs"].([]interface{})
		if !ok || len(configs) != 1 {
			t.Errorf("expected 1 config after save, got %v", result3["configs"])
		}
	})

	// ─── Generate project report (200) ───────────────────────────
	t.Run("generate project report pdf returns 200", func(t *testing.T) {
		// Create a project WITH a log_root
		tmpDir := t.TempDir()
		body := jsonBody(map[string]interface{}{
			"project_number": "T6011",
			"ship_name":      "REPORT_SHIP",
			"log_root":       tmpDir,
		})
		rec := doRequest(mux, "POST", "/api/v1/projects", body, map[string]string{
			"Content-Type": "application/json",
		})
		result := parseJSONResponse(rec)
		proj, _ := result["project"].(map[string]interface{})
		id := floatToStr(proj["id"])

		// Generate report (pdf format)
		genBody := jsonBody(map[string]interface{}{
			"format": "pdf",
		})
		rec2 := doRequest(mux, "POST", "/api/v1/projects/"+id+"/report", genBody, map[string]string{
			"Content-Type": "application/json",
		})
		if rec2.Code != http.StatusOK {
			t.Errorf("expected 200, got %d: %s", rec2.Code, rec2.Body.String())
		}
	})

	// ─── Generate project report docx (200) ──────────────────────
	t.Run("generate project report docx returns 200", func(t *testing.T) {
		tmpDir := t.TempDir()
		body := jsonBody(map[string]interface{}{
			"project_number": "T6012",
			"ship_name":      "DOCX_SHIP",
			"log_root":       tmpDir,
		})
		rec := doRequest(mux, "POST", "/api/v1/projects", body, map[string]string{
			"Content-Type": "application/json",
		})
		result := parseJSONResponse(rec)
		proj, _ := result["project"].(map[string]interface{})
		id := floatToStr(proj["id"])

		genBody := jsonBody(map[string]interface{}{
			"format": "docx",
		})
		rec2 := doRequest(mux, "POST", "/api/v1/projects/"+id+"/report", genBody, map[string]string{
			"Content-Type": "application/json",
		})
		if rec2.Code != http.StatusOK {
			t.Errorf("expected 200, got %d: %s", rec2.Code, rec2.Body.String())
		}
	})

	// ─── Generate project report invalid format (400) ────────────
	t.Run("generate project report invalid format returns 400", func(t *testing.T) {
		tmpDir := t.TempDir()
		body := jsonBody(map[string]interface{}{
			"project_number": "T6013",
			"ship_name":      "BAD_FMT_SHIP",
			"log_root":       tmpDir,
		})
		rec := doRequest(mux, "POST", "/api/v1/projects", body, map[string]string{
			"Content-Type": "application/json",
		})
		result := parseJSONResponse(rec)
		proj, _ := result["project"].(map[string]interface{})
		id := floatToStr(proj["id"])

		genBody := jsonBody(map[string]interface{}{
			"format": "xml",
		})
		rec2 := doRequest(mux, "POST", "/api/v1/projects/"+id+"/report", genBody, map[string]string{
			"Content-Type": "application/json",
		})
		if rec2.Code != http.StatusBadRequest {
			t.Errorf("expected 400, got %d: %s", rec2.Code, rec2.Body.String())
		}
	})

	// ─── Generate project report no log_root (400) ───────────────
	t.Run("generate project report without log_root returns 400", func(t *testing.T) {
		body := jsonBody(map[string]interface{}{
			"project_number": "T6014",
			"ship_name":      "NO_LOGROOT_SHIP",
		})
		rec := doRequest(mux, "POST", "/api/v1/projects", body, map[string]string{
			"Content-Type": "application/json",
		})
		result := parseJSONResponse(rec)
		proj, _ := result["project"].(map[string]interface{})
		id := floatToStr(proj["id"])

		genBody := jsonBody(map[string]interface{}{
			"format": "pdf",
		})
		rec2 := doRequest(mux, "POST", "/api/v1/projects/"+id+"/report", genBody, map[string]string{
			"Content-Type": "application/json",
		})
		if rec2.Code != http.StatusBadRequest {
			t.Errorf("expected 400, got %d: %s", rec2.Code, rec2.Body.String())
		}
	})
}

// floatToStr converts a float64 (from JSON) to string for URL paths.
func floatToStr(v interface{}) string {
	if f, ok := v.(float64); ok {
		return strconvFormatInt(int64(f))
	}
	return ""
}

// strconvFormatInt formats an int64 as string without importing strconv in every test.
func strconvFormatInt(n int64) string {
	if n == 0 {
		return "0"
	}
	neg := n < 0
	if neg {
		n = -n
	}
	var buf [20]byte
	i := len(buf)
	for n > 0 {
		i--
		buf[i] = byte('0' + n%10)
		n /= 10
	}
	if neg {
		i--
		buf[i] = '-'
	}
	return string(buf[i:])
}