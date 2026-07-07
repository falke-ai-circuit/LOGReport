package api

import (
	"encoding/json"
	"fmt"
	"log"
	"net/http"
	"os"
	"path/filepath"
	"strings"

	"github.com/falke-ai-circuit/LOGReport/internal/logwriter"
	"github.com/falke-ai-circuit/LOGReport/internal/nodesconfig"
	"github.com/falke-ai-circuit/LOGReport/internal/types"
)

// handleCreateLogStructure creates the folder/file structure at the log root
// based on the saved nodes.json configuration. For each node, for each token,
// it creates: {logRoot}/{stationName}/{tokenType}/{filename}
// Files are created empty (0 bytes) so the tree shows them with red color.
//
// POST /api/v1/nodesconfig/create-structure
// Body: {"log_root": "C:\\temp\\logreport-output"} (optional, uses settings if empty)
func (s *Server) handleCreateLogStructure(w http.ResponseWriter, r *http.Request) {
	var req struct {
		LogRoot string `json:"log_root"`
	}
	// Body is optional — ignore decode errors
	_ = json.NewDecoder(r.Body).Decode(&req)

	// Determine log root
	logRoot := req.LogRoot
	if logRoot == "" {
		if !globalSettings.loaded {
			s.initSettings()
		}
		st := getSettings()
		logRoot = st.LogRoot
	}
	if logRoot == "" {
		writeError(w, http.StatusBadRequest, "validation_error",
			"log_root is required (set in Settings or provide in request body)")
		return
	}

	createdDirs, createdFiles, stationCount, createdPaths, err := s.createLogStructure(logRoot)
	if err != nil {
		writeError(w, err.(*apiError).code, err.(*apiError).label, err.(*apiError).message)
		return
	}

	writeJSON(w, http.StatusOK, map[string]interface{}{
		"created_dirs":  createdDirs,
		"created_files": createdFiles,
		"log_root":      logRoot,
		"station_count": stationCount,
		"paths":         createdPaths,
	})
}

// handleDeleteLogStructure deletes the entire _LOG folder structure at the
// given log root. This allows the user to recreate the structure from scratch.
//
// DELETE /api/v1/nodesconfig/delete-structure
// Body: {"log_root": "C:\\Ships\\TEST_SHIP"} (optional, uses project's log_root)
func (s *Server) handleDeleteLogStructure(w http.ResponseWriter, r *http.Request) {
	var req struct {
		LogRoot   string `json:"log_root"`
		ProjectID int    `json:"project_id"`
	}
	_ = json.NewDecoder(r.Body).Decode(&req)

	logRoot := req.LogRoot
	if logRoot == "" {
		if req.ProjectID > 0 {
			if proj, err := s.store.GetProject(int64(req.ProjectID)); err == nil && proj != nil {
				logRoot = proj.LogRoot
			}
		}
	}
	if logRoot == "" {
		if !globalSettings.loaded {
			s.initSettings()
		}
		st := getSettings()
		logRoot = st.LogRoot
	}
	if logRoot == "" {
		writeError(w, http.StatusBadRequest, "validation_error",
			"log_root is required (set in Settings or provide in request body)")
		return
	}

	logDir := filepath.Join(logRoot, "_LOG")

	if _, err := os.Stat(logDir); os.IsNotExist(err) {
		writeJSON(w, http.StatusOK, map[string]interface{}{
			"deleted":   false,
			"log_root":  logRoot,
			"message":   "_LOG directory does not exist",
			"log_dir":   logDir,
		})
		return
	}

	if err := os.RemoveAll(logDir); err != nil {
		writeError(w, http.StatusInternalServerError, "delete_error",
			fmt.Sprintf("failed to delete _LOG directory: %v", err))
		return
	}

	writeJSON(w, http.StatusOK, map[string]interface{}{
		"deleted":  true,
		"log_root": logRoot,
		"log_dir":  logDir,
		"message":  "_LOG directory deleted successfully",
	})
}

// apiError is a simple error type carrying an HTTP status code, label, and message.
type apiError struct {
	code    int
	label   string
	message string
}

func (e *apiError) Error() string { return e.message }

// createLogStructure creates the _LOG/{station}/{type}/ folder structure and
// empty files at the given log root, based on the saved nodes.json configuration.
// Returns counts of created dirs/files and the list of created file paths.
func (s *Server) createLogStructure(logRoot string) (createdDirs, createdFiles, stationCount int, createdPaths []string, err error) {
	// Load nodes from nodes.json inside {logRoot}/_LOG/
	path := s.nodesConfigPathForLogRoot(logRoot)
	configs, err := nodesconfig.LoadFromFile(path)
	if err != nil {
		return 0, 0, 0, nil, &apiError{
			code:    http.StatusInternalServerError,
			label:   "load_error",
			message: fmt.Sprintf("failed to load nodes.json: %v", err),
		}
	}
	if len(configs) == 0 {
		return 0, 0, 0, nil, &apiError{
			code:    http.StatusBadRequest,
			label:   "no_nodes",
			message: "no nodes configured. Save nodes first.",
		}
	}

	// Determine log root folder name (default: _LOG, configurable in Settings)
	logRootName := "_LOG"
	if !globalSettings.loaded {
		s.initSettings()
	}
	st := getSettings()
	if st.LogRootName != "" {
		logRootName = st.LogRootName
	}

	// Create folder structure and empty files
	for _, cfg := range configs {
		stationName := extractStationNameFromConfig(cfg.Name)
		ip := cfg.IPAddress

		// Group tokens by type
		tokenTypes := make(map[string][]types.Token)
		for _, tok := range cfg.Tokens {
			tt := strings.ToUpper(string(tok.TokenType))
			tokenTypes[tt] = append(tokenTypes[tt], tok)
		}

		for tokenType, tokens := range tokenTypes {
			// Create directory: {logRoot}/{_LOG}/{station}/{tokenType}/
			dir := filepath.Join(logRoot, logRootName, stationName, strings.ToLower(tokenType))
			if mkErr := os.MkdirAll(dir, 0755); mkErr != nil {
				log.Printf("create-structure: mkdir %s: %v", dir, mkErr)
				continue
			}
			createdDirs++

			// Create empty file for each token (deduplicate LOG — one file per station)
			seenLog := make(map[string]bool)
			for _, tok := range tokens {
				fileName := buildLogFileName(stationName, ip, tokenType, tok.TokenID)
				if tokenType == "LOG" {
					if seenLog[fileName] {
						continue
					}
					seenLog[fileName] = true
				}
				filePath := filepath.Join(dir, fileName)
				// Only create if file doesn't exist (don't overwrite existing files)
				if _, statErr := os.Stat(filePath); statErr == nil {
					// File already exists — skip
					continue
				}

				if wErr := os.WriteFile(filePath, []byte{}, 0644); wErr != nil {
					log.Printf("create-structure: write %s: %v", filePath, wErr)
					continue
				}
				createdFiles++
				createdPaths = append(createdPaths, filePath)
			}
		}
	}

	return createdDirs, createdFiles, len(configs), createdPaths, nil
}

// buildLogFileName creates the expected filename for a log file.
// FBC: {station}_{ip}_{token}.fbc
// RPC: {station}_{ip}_{token}.rpc
// LOG: {station}_{ip}.log (no token ID in filename)
// LIS: {station}_{ip}_{token}.lis
func buildLogFileName(stationName, ip, tokenType, tokenID string) string {
	ipFmt := formatIPForLog(ip)
	ext := logFileExtension(tokenType)

	if tokenType == "LOG" {
		return fmt.Sprintf("%s_%s%s", stationName, ipFmt, ext)
	}
	return fmt.Sprintf("%s_%s_%s%s", stationName, ipFmt, tokenID, ext)
}

func formatIPForLog(ip string) string {
	if ip == "" {
		return "unknown-ip"
	}
	return strings.ReplaceAll(ip, ".", "-")
}

func logFileExtension(tokenType string) string {
	switch strings.ToUpper(tokenType) {
	case "FBC":
		return ".fbc"
	case "RPC":
		return ".rpc"
	case "LIS":
		return ".lis"
	default:
		return ".log"
	}
}

// handleEraseLogFile empties a log file (sets content to 0 bytes).
// POST /api/v1/logs/erase
// Body: {"path": "C:\	emp\\logreport-output\\AP01m\\FBC\\AP01m_192-168-0-11_22.fbc"}
// Or: {"node_name": "AP01m", "token_type": "FBC", "token_id": "22"} (looks up path from logwriter)
func (s *Server) handleEraseLogFile(w http.ResponseWriter, r *http.Request) {
	var req struct {
		Path      string `json:"path"`
		NodeName  string `json:"node_name"`
		TokenType string `json:"token_type"`
		TokenID   string `json:"token_id"`
		IPAddress string `json:"ip_address"`
	}
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		writeError(w, http.StatusBadRequest, "validation_error", "invalid JSON body")
		return
	}

	filePath := req.Path
	if filePath == "" && req.NodeName != "" {
		// Look up IP from nodes.json if not provided
		if req.IPAddress == "" {
			if configs, err := nodesconfig.LoadFromFile(s.nodesConfigPath()); err == nil {
				for _, c := range configs {
					if c.Name == req.NodeName || extractStationNameFromConfig(c.Name) == req.NodeName {
						req.IPAddress = c.IPAddress
						break
					}
				}
			}
		}
		lw := logwriter.New(s.logRoot())
		filePath = lw.LogPath(req.NodeName, req.TokenType, req.TokenID, req.IPAddress)
	}

	if filePath == "" {
		writeError(w, http.StatusBadRequest, "validation_error", "path or node_name+token_type is required")
		return
	}

	// Check file exists
	if _, err := os.Stat(filePath); err != nil {
		writeError(w, http.StatusNotFound, "not_found", fmt.Sprintf("file not found: %s", filePath))
		return
	}

	// Empty the file (truncate to 0 bytes)
	if err := os.WriteFile(filePath, []byte{}, 0644); err != nil {
		writeError(w, http.StatusInternalServerError, "erase_error",
			fmt.Sprintf("failed to erase file: %v", err))
		return
	}

	writeJSON(w, http.StatusOK, map[string]interface{}{
		"erased": true,
		"path":    filePath,
	})
}

// handleDeleteLogFile removes a log file from disk entirely.
// POST /api/v1/logs/delete
// Body: {"path": "C:\	emp\\...\\file.fbc"}
// Or: {"node_name": "AP01m", "token_type": "FBC", "token_id": "22"} (looks up path)
func (s *Server) handleDeleteLogFile(w http.ResponseWriter, r *http.Request) {
	var req struct {
		Path      string `json:"path"`
		NodeName  string `json:"node_name"`
		TokenType string `json:"token_type"`
		TokenID   string `json:"token_id"`
		IPAddress string `json:"ip_address"`
	}
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		writeError(w, http.StatusBadRequest, "validation_error", "invalid JSON body")
		return
	}

	filePath := req.Path
	if filePath == "" && req.NodeName != "" {
		if req.IPAddress == "" {
			if configs, err := nodesconfig.LoadFromFile(s.nodesConfigPath()); err == nil {
				for _, c := range configs {
					if c.Name == req.NodeName || extractStationNameFromConfig(c.Name) == req.NodeName {
						req.IPAddress = c.IPAddress
						break
					}
				}
			}
		}
		lw := logwriter.New(s.logRoot())
		filePath = lw.LogPath(req.NodeName, req.TokenType, req.TokenID, req.IPAddress)
	}

	if filePath == "" {
		writeError(w, http.StatusBadRequest, "validation_error", "path or node_name+token_type is required")
		return
	}

	if _, err := os.Stat(filePath); err != nil {
		writeError(w, http.StatusNotFound, "not_found", fmt.Sprintf("file not found: %s", filePath))
		return
	}

	// Try to clear read-only attribute before deleting (Windows may set it)
	_ = os.Chmod(filePath, 0666)

	if err := os.Remove(filePath); err != nil {
		writeError(w, http.StatusInternalServerError, "delete_error",
			fmt.Sprintf("failed to delete file: %v", err))
		return
	}

	writeJSON(w, http.StatusOK, map[string]interface{}{
		"deleted": true,
		"path":    filePath,
	})
}

// handleCreateLogFile creates a new empty log file on disk.
// POST /api/v1/logs/create
// Body: {"path": "C:\	emp\\...\\file.fbc"} or
//       {"node_name": "AP01m", "token_type": "FBC", "token_id": "22", "ip_address": "192.168.0.11"}
func (s *Server) handleCreateLogFile(w http.ResponseWriter, r *http.Request) {
	var req struct {
		Path      string `json:"path"`
		NodeName  string `json:"node_name"`
		TokenType string `json:"token_type"`
		TokenID   string `json:"token_id"`
		IPAddress string `json:"ip_address"`
	}
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		writeError(w, http.StatusBadRequest, "validation_error", "invalid JSON body")
		return
	}

	filePath := req.Path
	if filePath == "" && req.NodeName != "" {
		if req.IPAddress == "" {
			if configs, err := nodesconfig.LoadFromFile(s.nodesConfigPath()); err == nil {
				for _, c := range configs {
					if c.Name == req.NodeName || extractStationNameFromConfig(c.Name) == req.NodeName {
						req.IPAddress = c.IPAddress
						break
					}
				}
			}
		}
		lw := logwriter.New(s.logRoot())
		filePath = lw.LogPath(req.NodeName, req.TokenType, req.TokenID, req.IPAddress)
	}

	if filePath == "" {
		writeError(w, http.StatusBadRequest, "validation_error", "path or node_name+token_type is required")
		return
	}

	// Check if file already exists
	if _, err := os.Stat(filePath); err == nil {
		writeError(w, http.StatusConflict, "already_exists", fmt.Sprintf("file already exists: %s", filePath))
		return
	}

	// Create parent directories
	dir := filepath.Dir(filePath)
	if err := os.MkdirAll(dir, 0755); err != nil {
		writeError(w, http.StatusInternalServerError, "create_error",
			fmt.Sprintf("failed to create directory: %v", err))
		return
	}

	// Create empty file
	f, err := os.Create(filePath)
	if err != nil {
		writeError(w, http.StatusInternalServerError, "create_error",
			fmt.Sprintf("failed to create file: %v", err))
		return
	}
	f.Close()

	writeJSON(w, http.StatusOK, map[string]interface{}{
		"created": true,
		"path":    filePath,
	})
}

// handleMoveLogFile moves a log file to a different subfolder.
// POST /api/v1/logs/move
// Body: {"source_path": "...", "target_path": "..."} or
//       {"source_path": "...", "target_subfolder": "FBC"} (moves within same station)
func (s *Server) handleMoveLogFile(w http.ResponseWriter, r *http.Request) {
	var req struct {
		SourcePath      string `json:"source_path"`
		TargetPath      string `json:"target_path"`
		TargetSubfolder string `json:"target_subfolder"` // e.g. "FBC", "RPC", "LOG"
	}
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		writeError(w, http.StatusBadRequest, "validation_error", "invalid JSON body")
		return
	}

	if req.SourcePath == "" {
		writeError(w, http.StatusBadRequest, "validation_error", "source_path is required")
		return
	}

	if _, err := os.Stat(req.SourcePath); err != nil {
		writeError(w, http.StatusNotFound, "not_found", fmt.Sprintf("source file not found: %s", req.SourcePath))
		return
	}

	// Determine target path
	targetPath := req.TargetPath
	if targetPath == "" && req.TargetSubfolder != "" {
		// Move within same station to a different subfolder
		dir := filepath.Dir(filepath.Dir(req.SourcePath)) // go up from type folder
		fileName := filepath.Base(req.SourcePath)
		targetPath = filepath.Join(dir, strings.ToLower(req.TargetSubfolder), fileName)
	}

	if targetPath == "" {
		writeError(w, http.StatusBadRequest, "validation_error", "target_path or target_subfolder is required")
		return
	}

	// Don't overwrite existing files
	if _, err := os.Stat(targetPath); err == nil {
		writeError(w, http.StatusConflict, "already_exists", fmt.Sprintf("target file already exists: %s", targetPath))
		return
	}

	// Create target directory if needed
	targetDir := filepath.Dir(targetPath)
	if err := os.MkdirAll(targetDir, 0755); err != nil {
		writeError(w, http.StatusInternalServerError, "move_error",
			fmt.Sprintf("failed to create target directory: %v", err))
		return
	}

	// Move the file
	if err := os.Rename(req.SourcePath, targetPath); err != nil {
		// os.Rename may fail across volumes/drives — fall back to copy+delete
		data, readErr := os.ReadFile(req.SourcePath)
		if readErr != nil {
			writeError(w, http.StatusInternalServerError, "move_error",
				fmt.Sprintf("failed to read source file: %v", readErr))
			return
		}
		if writeErr := os.WriteFile(targetPath, data, 0644); writeErr != nil {
			writeError(w, http.StatusInternalServerError, "move_error",
				fmt.Sprintf("failed to write target file: %v", writeErr))
			return
		}
		os.Remove(req.SourcePath)
	}

	writeJSON(w, http.StatusOK, map[string]interface{}{
		"moved":       true,
		"source_path": req.SourcePath,
		"target_path": targetPath,
	})
}

// handleCreateFolder creates a new directory on disk.
// POST /api/v1/logs/create-folder
// Body: {"path": "C:\	emp\\...\\newfolder"}
func (s *Server) handleCreateFolder(w http.ResponseWriter, r *http.Request) {
	var req struct {
		Path string `json:"path"`
	}
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		writeError(w, http.StatusBadRequest, "validation_error", "invalid JSON body")
		return
	}

	if req.Path == "" {
		writeError(w, http.StatusBadRequest, "validation_error", "path is required")
		return
	}

	// Check if already exists
	if _, err := os.Stat(req.Path); err == nil {
		writeError(w, http.StatusConflict, "already_exists", fmt.Sprintf("folder already exists: %s", req.Path))
		return
	}

	if err := os.MkdirAll(req.Path, 0755); err != nil {
		writeError(w, http.StatusInternalServerError, "create_error",
			fmt.Sprintf("failed to create folder: %v", err))
		return
	}

	writeJSON(w, http.StatusOK, map[string]interface{}{
		"created": true,
		"path":    req.Path,
	})
}