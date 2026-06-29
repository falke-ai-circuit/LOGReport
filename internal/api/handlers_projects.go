package api

import (
	"encoding/json"
	"fmt"
	"log"
	"net/http"
	"strconv"

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

	p := &types.Project{
		ProjectNumber: req.ProjectNumber,
		ShipName:      req.ShipName,
		LogRoot:       req.LogRoot,
		NodesConfig:   req.NodesConfig,
		Status:        req.Status,
	}

	created, err := s.store.CreateProject(p)
	if err != nil {
		writeError(w, http.StatusInternalServerError, "internal_error",
			fmt.Sprintf("failed to create project: %v", err))
		return
	}

	writeJSON(w, http.StatusCreated, map[string]interface{}{
		"project": created,
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
		os.Remove(nodesConfigPathForProject(id))
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
	Format string `json:"format"` // "pdf" or "docx" (default: "pdf")
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