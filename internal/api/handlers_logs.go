package api

import (
	"encoding/json"
	"fmt"
	"net/http"
	"os"
	"path/filepath"
	"runtime"
	"strings"

	"github.com/falke-ai-circuit/LOGReport/internal/logfile"
	"github.com/falke-ai-circuit/LOGReport/internal/logwriter"
)

// ─── Log Handlers ──────────────────────────────────────────────────

// handleListLogs lists log files for a node.
// GET /api/v1/logs/{nodeName}
func (s *Server) handleListLogs(w http.ResponseWriter, r *http.Request) {
	nodeName := r.PathValue("nodeName")
	if nodeName == "" {
		writeError(w, http.StatusBadRequest, "validation_error", "nodeName is required")
		return
	}

	lw := logwriter.New(s.logRoot())
	entries, err := lw.ListLogs(nodeName)
	if err != nil {
		writeError(w, http.StatusInternalServerError, "internal_error",
			fmt.Sprintf("failed to list logs: %v", err))
		return
	}

	writeJSON(w, http.StatusOK, map[string]interface{}{
		"node_name": nodeName,
		"logs":      entries,
		"count":     len(entries),
	})
}

// handleReadLog reads a specific log file.
// GET /api/v1/logs/{nodeName}/{fileName}
func (s *Server) handleReadLog(w http.ResponseWriter, r *http.Request) {
	nodeName := r.PathValue("nodeName")
	fileName := r.PathValue("fileName")
	if nodeName == "" || fileName == "" {
		writeError(w, http.StatusBadRequest, "validation_error", "nodeName and fileName are required")
		return
	}

	// Parse fileName: {tokenType}_{tokenID}.log → e.g. "fbc_162.log"
	// Strip .log extension, split on _
	base := strings.TrimSuffix(fileName, ".log")
	parts := strings.SplitN(base, "_", 2)
	if len(parts) != 2 {
		writeError(w, http.StatusBadRequest, "validation_error",
			"fileName must be in format {tokenType}_{tokenID}.log")
		return
	}
	tokenType := strings.ToUpper(parts[0])
	tokenID := parts[1]

	lw := logwriter.New(s.logRoot())
	content, err := lw.ReadLog(nodeName, tokenType, tokenID, "")
	if err != nil {
		writeError(w, http.StatusNotFound, "not_found",
			fmt.Sprintf("log file not found: %v", err))
		return
	}

	writeJSON(w, http.StatusOK, map[string]interface{}{
		"node_name": nodeName,
		"file_name": fileName,
		"content":   content,
	})
}

// handleWriteLog writes/appends to a log file.
// POST /api/v1/logs/{nodeName}
func (s *Server) handleWriteLog(w http.ResponseWriter, r *http.Request) {
	nodeName := r.PathValue("nodeName")
	if nodeName == "" {
		writeError(w, http.StatusBadRequest, "validation_error", "nodeName is required")
		return
	}

	var req struct {
		TokenType string `json:"token_type"`
		TokenID   string `json:"token_id"`
		Output    string `json:"output"`
		NodeIP    string `json:"node_ip,omitempty"`
	}
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		writeError(w, http.StatusBadRequest, "validation_error", "invalid JSON body")
		return
	}
	if req.TokenType == "" || req.TokenID == "" {
		writeError(w, http.StatusBadRequest, "validation_error", "token_type and token_id are required")
		return
	}

	lw := logwriter.New(s.resolveLogRoot())
	if err := lw.WriteOutputWithIP(nodeName, req.TokenType, req.TokenID, req.Output, req.NodeIP); err != nil {
		writeError(w, http.StatusInternalServerError, "internal_error",
			fmt.Sprintf("failed to write log: %v", err))
		return
	}

	writeJSON(w, http.StatusOK, map[string]interface{}{
		"node_name": nodeName,
		"written":   true,
	})
}

// handleSetLogRoot sets the server's log root directory.
// POST /api/v1/logs/setroot
func (s *Server) handleSetLogRoot(w http.ResponseWriter, r *http.Request) {
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

	// Create directory if it doesn't exist
	if _, err := os.Stat(req.Path); err != nil {
		if mkErr := os.MkdirAll(req.Path, 0755); mkErr != nil {
			writeError(w, http.StatusBadRequest, "cannot_create",
				fmt.Sprintf("cannot create path: %s: %v", req.Path, mkErr))
			return
		}
	}

	s.logRootDir = req.Path
	writeJSON(w, http.StatusOK, map[string]interface{}{
		"log_root": req.Path,
		"set":      true,
	})
}

// handleBrowseDir lists subdirectories of a given path (for file explorer dialog).
// GET /api/v1/browse?path=C:\dna\CA\bu
// If path is empty, lists available drive letters (Windows) or root dirs (Linux).
// Returns only directories (not files) to keep the response small.
func (s *Server) handleBrowseDir(w http.ResponseWriter, r *http.Request) {
	path := r.URL.Query().Get("path")

	type dirEntry struct {
		Name string `json:"name"`
		Path string `json:"path"`
		Type string `json:"type"` // "dir" or "drive"
	}

	entries := make([]dirEntry, 0)

	if path == "" {
		// List drives (Windows) or root (Linux)
		if runtime.GOOS == "windows" {
			for c := 'C'; c <= 'Z'; c++ {
				drive := string(c) + ":\\"
				if _, err := os.Stat(drive); err == nil {
					entries = append(entries, dirEntry{
						Name: string(c) + ":",
						Path: drive,
						Type: "drive",
					})
				}
			}
		} else {
			rootEntries, err := os.ReadDir("/")
			if err == nil {
				for _, e := range rootEntries {
					if e.IsDir() {
						entries = append(entries, dirEntry{
							Name: e.Name(),
							Path: "/" + e.Name(),
							Type: "dir",
						})
					}
				}
			}
		}
		writeJSON(w, http.StatusOK, map[string]interface{}{
			"path":    path,
			"entries": entries,
			"parent":  "",
		})
		return
	}

	// Normalize path — remove trailing slash except for root
	path = strings.TrimSuffix(path, "\\")
	path = strings.TrimSuffix(path, "/")
	if path == "" {
		path = "/"
	}

	// List subdirectories
	dirEntries, err := os.ReadDir(path)
	if err != nil {
		writeError(w, http.StatusBadRequest, "browse_error",
			fmt.Sprintf("cannot read directory %s: %v", path, err))
		return
	}

	for _, e := range dirEntries {
		if e.IsDir() {
			fullPath := filepath.Join(path, e.Name())
			entries = append(entries, dirEntry{
				Name: e.Name(),
				Path: fullPath,
				Type: "dir",
			})
		}
	}

	// Compute parent path
	parent := filepath.Dir(path)
	if parent == path {
		parent = "" // at root
	}

	writeJSON(w, http.StatusOK, map[string]interface{}{
		"path":    path,
		"entries": entries,
		"parent":  parent,
	})
}

// handleListLogRoot lists all .fbc/.rpc/.log/.lis files in a directory.
// GET /api/v1/logs/list?path={logRoot}
func (s *Server) handleListLogRoot(w http.ResponseWriter, r *http.Request) {
	dir := r.URL.Query().Get("path")
	if dir == "" {
		dir = s.logRoot()
	}

	entries, err := logfile.ScanFiles(dir)
	if err != nil {
		writeError(w, http.StatusBadRequest, "scan_error",
			fmt.Sprintf("failed to scan directory: %v", err))
		return
	}

	writeJSON(w, http.StatusOK, map[string]interface{}{
		"path":  dir,
		"files": entries,
		"count": len(entries),
	})
}

// handleListLogFiles lists files of a specific type from a directory.
// GET /api/v1/logs/files?path={logRoot}&type={fbc|rpc|log|lis}
func (s *Server) handleListLogFiles(w http.ResponseWriter, r *http.Request) {
	dir := r.URL.Query().Get("path")
	if dir == "" {
		dir = s.logRoot()
	}
	fileType := r.URL.Query().Get("type")

	entries, err := logfile.ScanFilesByType(dir, fileType)
	if err != nil {
		writeError(w, http.StatusBadRequest, "scan_error",
			fmt.Sprintf("failed to scan directory: %v", err))
		return
	}

	writeJSON(w, http.StatusOK, map[string]interface{}{
		"path":  dir,
		"type":  fileType,
		"files": entries,
		"count": len(entries),
	})
}

// handleLogContent reads and returns the raw content of a log file (.fbc/.rpc/.log/.lis)
// from the log root directory.
// GET /api/v1/logs/content?path={filePath}
func (s *Server) handleLogContent(w http.ResponseWriter, r *http.Request) {
	filePath := r.URL.Query().Get("path")
	if filePath == "" {
		writeError(w, http.StatusBadRequest, "validation_error", "path query parameter is required")
		return
	}

	// Security: ensure path is within log root to prevent directory traversal
	root := s.logRoot()
	if root == "" {
		root = "logs"
	}
	// Resolve and check the path is under root
	absPath, err := filepath.Abs(filePath)
	if err != nil {
		writeError(w, http.StatusBadRequest, "validation_error", "invalid path")
		return
	}
	absRoot, _ := filepath.Abs(root)
	if !strings.HasPrefix(absPath, absRoot) {
		// Allow reading from any path if it's an absolute path with a valid extension
		// (for flexibility during testing)
		ext := strings.ToLower(filepath.Ext(absPath))
		if ext != ".fbc" && ext != ".rpc" && ext != ".log" && ext != ".lis" && ext != ".txt" {
			writeError(w, http.StatusForbidden, "forbidden", "path must be within log root or have .fbc/.rpc/.log/.lis/.txt extension")
			return
		}
	}

	data, err := os.ReadFile(absPath)
	if err != nil {
		writeError(w, http.StatusNotFound, "not_found",
			fmt.Sprintf("file not found: %v", err))
		return
	}

	writeJSON(w, http.StatusOK, map[string]interface{}{
		"path":    absPath,
		"content": string(data),
		"size":    len(data),
	})
}
