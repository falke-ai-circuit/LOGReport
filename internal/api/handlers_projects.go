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

	"github.com/falke-ai-circuit/LOGReport/internal/logfile"
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
		if f != types.FormatPDF && f != types.FormatDOCX && f != types.FormatJSON {
			writeErrorDetails(w, http.StatusBadRequest, "validation_error",
				fmt.Sprintf("unsupported format: '%s'. Supported: pdf, docx, json", req.Format),
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

	// If project's log_root has no log files, try the server's logRoot
	// (user may have changed log root in Commander dropdown)
	logRootToUse := p.LogRoot
	testFiles, _ := logfile.ScanFiles(logRootToUse)
	if len(testFiles) == 0 {
		lr := s.logRoot()
		if lr != "" && lr != "logs" && lr != logRootToUse {
			altFiles, _ := logfile.ScanFiles(lr)
			if len(altFiles) > 0 {
				log.Printf("api: project %d log_root %s has 0 files, falling back to server logRoot %s (%d files)",
					id, logRootToUse, lr, len(altFiles))
				logRootToUse = lr
			}
		}
	}

	cfg := types.ReportConfig{
		NodeAddress: "*",
		Format:      format,
		LogRoot:     logRootToUse,
		Title:       fmt.Sprintf("%s_%s — Log Report", p.ProjectNumber, p.ShipName),
		Appearance:  req.Appearance,
		ProjectID:   id,
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

// ─── POST /api/v1/projects/import ──────────────────────────────

// handleImportProject accepts a zip file upload, extracts it to a target
// directory, creates a project in the DB, and parses nodes.json if present.
// The zip should contain a top-level {project_number}_{ship_name}/ folder
// with _LOG/, reports/, nodes.json inside (matching the export format).
//
// POST /api/v1/projects/import
// Form fields:
//   - file: the zip file (multipart upload)
//   - target_dir: base directory to extract into (optional, defaults to cwd)
func (s *Server) handleImportProject(w http.ResponseWriter, r *http.Request) {
	// Limit upload size to 500MB
	r.Body = http.MaxBytesReader(w, r.Body, 500<<20)
	if err := r.ParseMultipartForm(500 << 20); err != nil {
		writeError(w, http.StatusBadRequest, "validation_error",
			fmt.Sprintf("failed to parse multipart form: %v", err))
		return
	}

	// Get target directory (optional)
	targetDir := r.FormValue("target_dir")
	if targetDir == "" {
		targetDir = "."
	}

	// Get the uploaded file
	file, header, err := r.FormFile("file")
	if err != nil {
		writeError(w, http.StatusBadRequest, "validation_error",
			"file field is required (zip file upload)")
		return
	}
	defer file.Close()

	// Save the uploaded zip to a temp file
	tmpZip, err := os.CreateTemp("", "logreport-import-*.zip")
	if err != nil {
		writeError(w, http.StatusInternalServerError, "internal_error",
			fmt.Sprintf("failed to create temp file: %v", err))
		return
	}
	tmpZipPath := tmpZip.Name()
	defer os.Remove(tmpZipPath)
	if _, err := io.Copy(tmpZip, file); err != nil {
		tmpZip.Close()
		writeError(w, http.StatusInternalServerError, "internal_error",
			fmt.Sprintf("failed to save uploaded file: %v", err))
		return
	}
	tmpZip.Close()

	// Open the zip and inspect its structure
	zipReader, err := zip.OpenReader(tmpZipPath)
	if err != nil {
		writeError(w, http.StatusBadRequest, "validation_error",
			fmt.Sprintf("failed to open zip file: %v", err))
		return
	}
	defer zipReader.Close()

	// Find the top-level folder name (first path component)
	var topLevelFolder string
	for _, f := range zipReader.File {
		parts := splitFilePath(f.Name)
		if len(parts) > 0 && parts[0] != "" {
			topLevelFolder = parts[0]
			break
		}
	}
	if topLevelFolder == "" {
		writeError(w, http.StatusBadRequest, "validation_error",
			"zip file appears to be empty or has no top-level folder")
		return
	}

	// Derive project_number and ship_name from the folder name
	// Format: {project_number}_{ship_name}
	projectNumber, shipName := parseProjectFolderName(topLevelFolder)
	if projectNumber == "" || shipName == "" {
		writeError(w, http.StatusBadRequest, "validation_error",
			fmt.Sprintf("cannot derive project_number and ship_name from folder name %q. Expected format: PROJECT_NUMBER_SHIP_NAME", topLevelFolder))
		return
	}

	// Check if a project with the same number+ship already exists
	existing, _ := s.store.ListProjects()
	for _, p := range existing {
		if p.ProjectNumber == projectNumber && p.ShipName == shipName {
			writeError(w, http.StatusConflict, "already_exists",
				fmt.Sprintf("project %s_%s already exists (ID: %d). Delete it first or use a different target directory.", projectNumber, shipName, p.ID))
			return
		}
	}

	// Extract the zip to the target directory
	projectDir := filepath.Join(targetDir, topLevelFolder)
	for _, f := range zipReader.File {
		// Prevent zip slip: ensure the destination path stays within targetDir
		destPath := filepath.Join(targetDir, f.Name)
		if !isPathWithinDir(destPath, targetDir) {
			log.Printf("import-project: skipping %s (path traversal detected)", f.Name)
			continue
		}

		if f.FileInfo().IsDir() {
			os.MkdirAll(destPath, 0755)
			continue
		}

		// Create parent directories
		if err := os.MkdirAll(filepath.Dir(destPath), 0755); err != nil {
			log.Printf("import-project: mkdir %s: %v", filepath.Dir(destPath), err)
			continue
		}

		// Extract file
		src, err := f.Open()
		if err != nil {
			log.Printf("import-project: open %s in zip: %v", f.Name, err)
			continue
		}
		dst, err := os.Create(destPath)
		if err != nil {
			src.Close()
			log.Printf("import-project: create %s: %v", destPath, err)
			continue
		}
		_, err = io.Copy(dst, src)
		dst.Close()
		src.Close()
		if err != nil {
			log.Printf("import-project: copy %s: %v", f.Name, err)
		}
	}

	// Read nodes.json if present
	nodesJSONPath := filepath.Join(projectDir, "nodes.json")
	nodesConfig := ""
	if data, err := os.ReadFile(nodesJSONPath); err == nil {
		nodesConfig = string(data)
	}

	// Read settings.json if present
	settingsJSON := ""
	settingsPath := filepath.Join(projectDir, "settings.json")
	if data, err := os.ReadFile(settingsPath); err == nil {
		settingsJSON = string(data)
	}

	// Create the project in the DB
	p := &types.Project{
		ProjectNumber: projectNumber,
		ShipName:      shipName,
		LogRoot:       projectDir,
		NodesConfig:   nodesConfig,
		SettingsJSON:  settingsJSON,
		Status:        types.ProjectActive,
	}

	created, err := s.store.CreateProject(p)
	if err != nil {
		writeError(w, http.StatusInternalServerError, "internal_error",
			fmt.Sprintf("failed to create project: %v", err))
		return
	}

	// If nodes.json has content, auto-create _LOG structure
	if created.LogRoot != "" && nodesConfig != "" && nodesConfig != "[]" {
		if _, _, _, _, structErr := s.createLogStructure(created.LogRoot); structErr != nil {
			log.Printf("import-project: auto-create structure at %s: %v", created.LogRoot, structErr)
		}
	}

	// If settings.json was imported, apply settings
	if settingsJSON != "" {
		var settings map[string]interface{}
		if err := json.Unmarshal([]byte(settingsJSON), &settings); err == nil {
			settingsBytes, _ := json.Marshal(settings)
			_ = settingsBytes // settings are stored in project.SettingsJSON already
		}
	}

	log.Printf("import-project: imported %s from %s (%d bytes), project ID: %d, log_root: %s",
		topLevelFolder, header.Filename, header.Size, created.ID, projectDir)

	writeJSON(w, http.StatusCreated, map[string]interface{}{
		"project":        created,
		"project_folder": projectDir,
		"extracted_from": header.Filename,
		"file_count":     len(zipReader.File),
	})
}

// splitFilePath splits a zip file path into components using forward slashes.
func splitFilePath(path string) []string {
	// Normalize: convert backslashes to forward slashes
	path = filepath.ToSlash(path)
	// Remove leading slash
	path = strings.TrimPrefix(path, "/")
	if path == "" {
		return nil
	}
	return strings.Split(path, "/")
}

// parseProjectFolderName extracts project_number and ship_name from a folder
// name like "V6049A_CELEBRITY_REFLECTION". The first underscore separates
// the project number from the ship name. Ship names may contain underscores.
func parseProjectFolderName(folderName string) (projectNumber, shipName string) {
	idx := strings.Index(folderName, "_")
	if idx <= 0 {
		return "", ""
	}
	projectNumber = folderName[:idx]
	shipName = folderName[idx+1:]
	if shipName == "" {
		return "", ""
	}
	return projectNumber, shipName
}

// isPathWithinDir checks if destPath is within baseDir (prevents zip slip).
func isPathWithinDir(destPath, baseDir string) bool {
	absBase, err := filepath.Abs(baseDir)
	if err != nil {
		return false
	}
	absDest, err := filepath.Abs(destPath)
	if err != nil {
		return false
	}
	return strings.HasPrefix(absDest, absBase+string(filepath.Separator)) || absDest == absBase
}