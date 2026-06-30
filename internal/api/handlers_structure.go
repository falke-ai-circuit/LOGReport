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

	// Load nodes from nodes.json
	path := s.nodesConfigPath()
	configs, err := nodesconfig.LoadFromFile(path)
	if err != nil {
		writeError(w, http.StatusInternalServerError, "load_error",
			fmt.Sprintf("failed to load nodes.json: %v", err))
		return
	}
	if len(configs) == 0 {
		writeError(w, http.StatusBadRequest, "no_nodes",
			"no nodes configured. Save nodes first.")
		return
	}

	// Create folder structure and empty files
	createdDirs := 0
	createdFiles := 0
	var createdPaths []string

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
			// Create directory: {logRoot}/{station}/{tokenType}/
			dir := filepath.Join(logRoot, stationName, tokenType)
			if err := os.MkdirAll(dir, 0755); err != nil {
				log.Printf("create-structure: mkdir %s: %v", dir, err)
				continue
			}
			createdDirs++

			// Create empty file for each token
			for _, tok := range tokens {
				fileName := buildLogFileName(stationName, ip, tokenType, tok.TokenID)
				filePath := filepath.Join(dir, fileName)

				// Only create if file doesn't exist (don't overwrite existing files)
				if _, err := os.Stat(filePath); err == nil {
					// File already exists — skip
					continue
				}

				if err := os.WriteFile(filePath, []byte{}, 0644); err != nil {
					log.Printf("create-structure: write %s: %v", filePath, err)
					continue
				}
				createdFiles++
				createdPaths = append(createdPaths, filePath)
			}
		}
	}

	// Update server log root
	s.SetLogRoot(logRoot)

	writeJSON(w, http.StatusOK, map[string]interface{}{
		"created_dirs":  createdDirs,
		"created_files": createdFiles,
		"log_root":      logRoot,
		"station_count": len(configs),
		"paths":         createdPaths,
	})
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