package api

import (
	"archive/zip"
	"encoding/json"
	"fmt"
	"io"
	"log"
	"net/http"
	"os"
	"path/filepath"
	"strconv"
	"strings"

	"github.com/falke-ai-circuit/LOGReport/internal/report"
	"github.com/falke-ai-circuit/LOGReport/internal/types"
)

// ─── POST /api/v1/projects ──────────────────────────────────────

func (s *Server) createProjectHandler(w http.ResponseWriter, r *http.Request) {
	var req types.ProjectRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		writeError(w, http.StatusBadRequest, "validation_error", "invalid JSON body")
		return
	}

	if req.ProjectNumber == "" || req.ShipName == "" {
		writeErrorDetails(w, http.StatusBadRequest, "validation_error",
			"project_number and ship_name are required", map[string]string{
				"project_number": cond(req.ProjectNumber == "", "missing required field", ""),
				"ship_name":      cond(req.ShipName == "", "missing required field", ""),
			})
		return
	}

	// Build the project folder path: {logRoot}/{project_number}_{ship_name}/
	// If user provided a log_root, we create a subfolder for this project inside it.
	// If no log_root provided, we use a default base (cwd or data dir).
	baseDir := req.LogRoot
	if baseDir == "" {
		baseDir = "."
	}
	projectFolderName := fmt.Sprintf("%s_%s", req.ProjectNumber, req.ShipName)
	projectDir := filepath.Join(baseDir, projectFolderName)

	// Create the project folder structure:
	// {projectDir}/
	//   _LOG/          (log structure: station/type/files)
	//   reports/        (generated PDF/DOCX reports)
	//   nodes.json      (node configuration, starts empty)
	logDir := filepath.Join(projectDir, "_LOG")
	reportsDir := filepath.Join(projectDir, "reports")
	nodesJSONPath := filepath.Join(projectDir, "nodes.json")

	if err := os.MkdirAll(logDir, 0755); err != nil {
		writeError(w, http.StatusInternalServerError, "internal_error",
			fmt.Sprintf("failed to create project log directory: %v", err))
		return
	}
	if err := os.MkdirAll(reportsDir, 0755); err != nil {
		writeError(w, http.StatusInternalServerError, "internal_error",
			fmt.Sprintf("failed to create project reports directory: %v", err))
		return
	}
	// Create empty nodes.json if it doesn't exist
	if _, err := os.Stat(nodesJSONPath); os.IsNotExist(err) {
		if err := os.WriteFile(nodesJSONPath, []byte("[]"), 0644); err != nil {
			log.Printf("create-project: write nodes.json: %v", err)
		}
	}

	// Store the full project directory path as LogRoot
	p := &types.Project{
		ProjectNumber: req.ProjectNumber,
		ShipName:      req.ShipName,
		LogRoot:       projectDir,
		NodesConfig:   req.NodesConfig,
		Status:        req.Status,
	}

	created, err := s.store.CreateProject(p)
	if err != nil {
		writeError(w, http.StatusInternalServerError, "internal_error",
			fmt.Sprintf("failed to create project: %v", err))
		return
	}

	// Auto-create _LOG/{station}/{type}/ folder structure if nodes.json has content
	if created.LogRoot != "" {
		if _, _, _, _, structErr := s.createLogStructure(created.LogRoot); structErr != nil {
			// Non-fatal: structure may not exist yet (no nodes scanned)
			log.Printf("create-project: auto-create structure at %s: %v", created.LogRoot, structErr)
		}
	}

	writeJSON(w, http.StatusCreated, map[string]interface{}{
		"project":       created,
		"project_folder": projectDir,
		"created_dirs":   []string{logDir, reportsDir},
		"nodes_json":     nodesJSONPath,
	})
}

// ─── GET /api/v1/projects ───────────────────────────────────────

func (s *Server) listProjectsHandler(w http.ResponseWriter, r *http.Request) {
	projects, err := s.store.ListProjects()
	if err != nil {
		writeError(w, http.StatusInternalServerError, "internal_error",
			fmt.Sprintf("failed to list projects: %v", err))
		return
	}

	if projects == nil {
		projects = []*types.Project{}
	}

	writeJSON(w, http.StatusOK, map[string]interface{}{
		"projects": projects,
		"total":    len(projects),
	})
}

// ─── GET /api/v1/projects/{id} ──────────────────────────────────

func (s *Server) getProjectHandler(w http.ResponseWriter, r *http.Request) {
	id, err := strconv.ParseInt(r.PathValue("id"), 10, 64)
	if err != nil {
		writeError(w, http.StatusBadRequest, "validation_error", "project id must be a number")
		return
	}

	p, err := s.store.GetProject(id)
	if err != nil {
		writeError(w, http.StatusNotFound, "not_found",
			fmt.Sprintf("project %d not found", id))
		return
	}

	writeJSON(w, http.StatusOK, map[string]interface{}{
		"project": p,
	})
}

// ─── PUT /api/v1/projects/{id} ──────────────────────────────────

func (s *Server) updateProjectHandler(w http.ResponseWriter, r *http.Request) {
	id, err := strconv.ParseInt(r.PathValue("id"), 10, 64)
	if err != nil {
		writeError(w, http.StatusBadRequest, "validation_error", "project id must be a number")
		return
	}

	var req types.ProjectRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		writeError(w, http.StatusBadRequest, "validation_error", "invalid JSON body")
		return
	}

	if req.ProjectNumber == "" || req.ShipName == "" {
		writeErrorDetails(w, http.StatusBadRequest, "validation_error",
			"project_number and ship_name are required", map[string]string{
				"project_number": cond(req.ProjectNumber == "", "missing required field", ""),
				"ship_name":      cond(req.ShipName == "", "missing required field", ""),
			})
		return
	}

	status := req.Status
	if status == "" {
		status = types.ProjectActive
	}

	p := &types.Project{
		ProjectNumber: req.ProjectNumber,
		ShipName:      req.ShipName,
		LogRoot:       req.LogRoot,
		NodesConfig:   req.NodesConfig,
		Status:        status,
	}

	updated, err := s.store.UpdateProject(id, p)
	if err != nil {
		writeError(w, http.StatusInternalServerError, "internal_error",
			fmt.Sprintf("failed to update project %d: %v", id, err))
		return
	}

	writeJSON(w, http.StatusOK, map[string]interface{}{
		"project": updated,
	})
}

// ─── DELETE /api/v1/projects/{id} ───────────────────────────────

func (s *Server) deleteProjectHandler(w http.ResponseWriter, r *http.Request) {
	id, err := strconv.ParseInt(r.PathValue("id"), 10, 64)
	if err != nil {
		writeError(w, http.StatusBadRequest, "validation_error", "project id must be a number")
		return
	}

	if err := s.store.DeleteProject(id); err != nil {
		os.Remove(s.nodesConfigPathForProject(strconv.FormatInt(id, 10)))
		writeError(w, http.StatusInternalServerError, "internal_error",
			fmt.Sprintf("failed to delete project %d: %v", id, err))
		return
	}

	writeJSON(w, http.StatusOK, map[string]interface{}{
		"deleted":  true,
		"project_id": id,
	})
}

// ─── POST /api/v1/projects/{id}/report ──────────────────────────

// generateProjectReportRequest is the JSON body for the project report endpoint.
type generateProjectReportRequest struct {
	Format    string                  `json:"format"`    // "pdf" or "docx" (default: "pdf")
	Appearance *types.ReportAppearance `json:"appearance,omitempty"` // font/layout settings (optional)
}

func (s *Server) generateProjectReportHandler(w http.ResponseWriter, r *http.Request) {
	id, err := strconv.ParseInt(r.PathValue("id"), 10, 64)
	if err != nil {
		writeError(w, http.StatusBadRequest, "validation_error", "project id must be a number")
		return
	}

	p, err := s.store.GetProject(id)
	if err != nil {
		writeError(w, http.StatusNotFound, "not_found",
			fmt.Sprintf("project %d not found", id))
		return
	}

	// Parse optional request body for format selection
	format := types.FormatPDF
	var req generateProjectReportRequest
	if r.Body != nil {
		// Try to decode; if body is empty or invalid, fall back to defaults
		_ = json.NewDecoder(r.Body).Decode(&req)
	}
	if req.Format != "" {
		f := types.ReportFormat(req.Format)
		if f != types.FormatPDF && f != types.FormatDOCX {
			writeErrorDetails(w, http.StatusBadRequest, "validation_error",
				fmt.Sprintf("unsupported format: '%s'. Supported: pdf, docx", req.Format),
				map[string]string{"requested_format": req.Format})
			return
		}
		format = f
	}

	if p.LogRoot == "" {
		writeError(w, http.StatusBadRequest, "validation_error",
			"project has no log_root configured")
		return
	}

	cfg := types.ReportConfig{
		NodeAddress: "*",
		Format:      format,
		LogRoot:     p.LogRoot,
		Title:       fmt.Sprintf("%s_%s — Log Report", p.ProjectNumber, p.ShipName),
		Appearance:  req.Appearance,
	}

	rpt, err := report.GenerateReport(cfg, s.store)
	if err != nil {
		log.Printf("api: project report generation failed for project %d: %v", id, err)
		writeError(w, http.StatusInternalServerError, "report_generation_failed",
			fmt.Sprintf("failed to generate report: %v", err))
		return
	}

	writeJSON(w, http.StatusOK, reportToAPI(rpt))
}

// ─── GET /api/v1/projects/{id}/export ──────────────────────────────

// handleExportProject zips the entire project folder ({project_number}_{ship_name}/)
// including _LOG/, reports/, nodes.json — and returns it as a downloadable zip file.
//
// GET /api/v1/projects/{id}/export
func (s *Server) handleExportProject(w http.ResponseWriter, r *http.Request) {
	idStr := r.PathValue("id")
	if idStr == "" {
		// Fallback for older Go routing
		parts := strings.Split(r.URL.Path, "/")
		if len(parts) >= 5 {
			idStr = parts[len(parts)-2]
		}
	}
	id, err := strconv.ParseInt(idStr, 10, 64)
	if err != nil {
		writeError(w, http.StatusBadRequest, "validation_error", "invalid project id")
		return
	}

	p, err := s.store.GetProject(id)
	if err != nil || p == nil {
		writeError(w, http.StatusNotFound, "not_found", "project not found")
		return
	}

	projectDir := p.LogRoot
	if projectDir == "" {
		writeError(w, http.StatusBadRequest, "validation_error", "project has no log_root configured")
		return
	}

	// Check the project directory exists
	if _, err := os.Stat(projectDir); os.IsNotExist(err) {
		writeError(w, http.StatusNotFound, "not_found",
			fmt.Sprintf("project folder does not exist: %s", projectDir))
		return
	}

	// Build zip filename: {project_number}_{ship_name}.zip
	zipName := fmt.Sprintf("%s_%s.zip", p.ProjectNumber, p.ShipName)

	// Set headers for file download
	w.Header().Set("Content-Type", "application/zip")
	w.Header().Set("Content-Disposition", fmt.Sprintf("attachment; filename=\"%s\"", zipName))

	// Create zip writer writing directly to the response
	zipWriter := zip.NewWriter(w)
	defer zipWriter.Close()

	// Walk the project directory and add all files
	err = filepath.Walk(projectDir, func(filePath string, info os.FileInfo, err error) error {
		if err != nil {
			return err
		}
		if info.IsDir() {
			return nil
		}

		// Calculate the relative path inside the zip
		// The zip should contain {project_number}_{ship_name}/... as the top-level
		relPath, err := filepath.Rel(filepath.Dir(projectDir), filePath)
		if err != nil {
			return err
		}
		// Convert to forward slashes for zip (Windows compatibility)
		relPath = filepath.ToSlash(relPath)

		// Open the file
		f, err := os.Open(filePath)
		if err != nil {
			log.Printf("export-project: skipping %s: %v", filePath, err)
			return nil // skip files we can't read
		}
		defer f.Close()

		// Create zip entry
		zipEntry, err := zipWriter.Create(relPath)
		if err != nil {
			return fmt.Errorf("create zip entry: %w", err)
		}

		_, err = io.Copy(zipEntry, f)
		return err
	})

	if err != nil {
		log.Printf("export-project: zip failed for project %d: %v", id, err)
		// Can't write a JSON error at this point — headers already sent
		return
	}

	log.Printf("export-project: exported project %d (%s) as %s", id, projectDir, zipName)
}