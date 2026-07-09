package api

import (
	"encoding/json"
	"errors"
	"fmt"
	"log"
	"net/http"
	"os"
	"path/filepath"
	"strconv"
	"strings"

	"github.com/falke-ai-circuit/LOGReport/internal/nodesconfig"
	"github.com/falke-ai-circuit/LOGReport/internal/types"
)

func (s *Server) nodesConfigPath() string {
	// First: check in the data directory (where -db-path points)
	if s.config != nil && s.config.DBPath != "" {
		dbPath := filepath.Join(s.config.DBPath, "nodes.json")
		if _, err := os.Stat(dbPath); err == nil {
			return dbPath
		}
	}
	// Then: check cwd
	candidates := []string{
		"nodes.json",
		"./config/nodes.json",
		filepath.Join("data", "nodes.json"),
	}
	for _, c := range candidates {
		if _, err := os.Stat(c); err == nil {
			return c
		}
	}
	// Default: create in data directory if set, otherwise cwd
	if s.config != nil && s.config.DBPath != "" {
		return filepath.Join(s.config.DBPath, "nodes.json")
	}
	return "nodes.json" // default, may not exist yet
}

// nodesConfigPathForProject returns the path to nodes.json for a project.
// If projectID is non-empty, looks up the project's log_root from the store
// and returns {logRoot}/_LOG/nodes.json — the nodes config lives alongside
// the log files inside the project's _LOG subfolder.
// If projectID is empty or the project/log_root is not found, falls back
// to the default nodesConfigPath().
func (s *Server) nodesConfigPathForProject(projectID string) string {
	if projectID == "" {
		return s.nodesConfigPath()
	}
	// Try to look up the project's log_root from the store
	id, err := strconv.ParseInt(projectID, 10, 64)
	if err != nil {
		return s.nodesConfigPath()
	}
	p, err := s.store.GetProject(id)
	if err != nil || p == nil || p.LogRoot == "" {
		// Fall back to old-style nodes_{id}.json for backward compat
		return fmt.Sprintf("nodes_%s.json", projectID)
	}
	// nodes.json lives inside {logRoot}/
	return filepath.Join(p.LogRoot, "nodes.json")
}

func (s *Server) nodesConfigPathForLogRoot(logRoot string) string {
	if logRoot == "" {
		return s.nodesConfigPath()
	}
	return filepath.Join(logRoot, "nodes.json")
}

// handleGetNodesConfig loads and returns nodes.json as NodeConfig[].
// GET /api/v1/nodesconfig?project_id={id}
// If project_id is provided, loads from nodes_{id}.json instead of nodes.json.
// GET /api/v1/nodesconfig
func (s *Server) handleGetNodesConfig(w http.ResponseWriter, r *http.Request) {
	projectID := r.URL.Query().Get("project_id")
	path := s.nodesConfigPathForProject(projectID)
	configs, err := nodesconfig.LoadFromFile(path)
	if err != nil {
		log.Printf("handleGetNodesConfig: LoadFromFile(%q) error: %v", path, err)
		if errors.Is(err, os.ErrNotExist) {
			// Return empty array if file doesn't exist
			writeJSON(w, http.StatusOK, map[string]interface{}{
				"configs": make([]types.NodeConfig, 0),
				"path":    path,
			})
			return
		}
		writeError(w, http.StatusInternalServerError, "load_error",
			fmt.Sprintf("failed to load nodes.json: %v", err))
		return
	}
	writeJSON(w, http.StatusOK, map[string]interface{}{
		"configs": configs,
		"path":    path,
	})
}

// handleSaveNodesConfig saves NodeConfig[] to nodes.json.
// POST /api/v1/nodesconfig
func (s *Server) handleSaveNodesConfig(w http.ResponseWriter, r *http.Request) {
	var configs []types.NodeConfig
	if err := json.NewDecoder(r.Body).Decode(&configs); err != nil {
		writeError(w, http.StatusBadRequest, "validation_error", "invalid JSON body")
		return
	}

	projectID := r.URL.Query().Get("project_id")
	path := s.nodesConfigPathForProject(projectID)
	// Ensure parent directory exists (especially for {logRoot}/_LOG/nodes.json)
	dir := filepath.Dir(path)
	if err := os.MkdirAll(dir, 0755); err != nil {
		writeError(w, http.StatusInternalServerError, "save_error",
			fmt.Sprintf("failed to create directory %s: %v", dir, err))
		return
	}
	// Sanitize token_ids: if a token_id looks like a filename (contains both
	// "_" and "."), extract just the token number from it. This prevents
	// doubled filenames like "AP01m_192-168-0-11_22.fbc.fbc" when command
	// output is written with the filename as token_id.
	for i := range configs {
		for j := range configs[i].Tokens {
			tid := configs[i].Tokens[j].TokenID
			if strings.Contains(tid, "_") && strings.Contains(tid, ".") {
				// Extract last segment after "_" and strip extension
				parts := strings.Split(tid, "_")
				last := parts[len(parts)-1]
				last = strings.TrimSuffix(last, filepath.Ext(last))
				if last != "" {
					configs[i].Tokens[j].TokenID = last
				}
			}
		}
	}

	if err := nodesconfig.SaveToFile(path, configs); err != nil {
		writeError(w, http.StatusInternalServerError, "save_error",
			fmt.Sprintf("failed to save nodes.json: %v", err))
		return
	}

	writeJSON(w, http.StatusOK, map[string]interface{}{
		"saved": true,
		"count": len(configs),
		"path":  path,
	})
}

// handleDeleteNodesConfigEntry deletes a single node entry from nodes.json by name.
// DELETE /api/v1/nodesconfig/entry?project_id={id}&name={name}
func (s *Server) handleDeleteNodesConfigEntry(w http.ResponseWriter, r *http.Request) {
	projectID := r.URL.Query().Get("project_id")
	nodeName := r.URL.Query().Get("name")
	if nodeName == "" {
		writeError(w, http.StatusBadRequest, "validation_error", "name parameter is required")
		return
	}

	path := s.nodesConfigPathForProject(projectID)
	configs, err := nodesconfig.LoadFromFile(path)
	if err != nil && !errors.Is(err, os.ErrNotExist) {
		writeError(w, http.StatusInternalServerError, "load_error",
			fmt.Sprintf("failed to load nodes.json: %v", err))
		return
	}

	// Filter out the node with matching name
	var filtered []types.NodeConfig
	deleted := false
	for _, c := range configs {
		if c.Name == nodeName {
			deleted = true
			continue
		}
		filtered = append(filtered, c)
	}

	if !deleted {
		writeError(w, http.StatusNotFound, "not_found",
			fmt.Sprintf("node '%s' not found in nodes.json", nodeName))
		return
	}

	if err := nodesconfig.SaveToFile(path, filtered); err != nil {
		writeError(w, http.StatusInternalServerError, "save_error",
			fmt.Sprintf("failed to save nodes.json: %v", err))
		return
	}

	writeJSON(w, http.StatusOK, map[string]interface{}{
		"deleted": true,
		"name":    nodeName,
		"count":   len(filtered),
	})
}

// handleRenameNodesConfigEntry renames a node entry in nodes.json by name.
// POST /api/v1/nodesconfig/rename?project_id={id}&name={oldName}
// Body: {"new_name": "NEW_NAME", "new_ip": "192.168.0.99"}
func (s *Server) handleRenameNodesConfigEntry(w http.ResponseWriter, r *http.Request) {
	projectID := r.URL.Query().Get("project_id")
	oldName := r.URL.Query().Get("name")
	if oldName == "" {
		writeError(w, http.StatusBadRequest, "validation_error", "name parameter is required")
		return
	}

	var req struct {
		NewName string `json:"new_name"`
		NewIP   string `json:"new_ip"`
	}
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		writeError(w, http.StatusBadRequest, "invalid_json", "invalid request body")
		return
	}
	if req.NewName == "" && req.NewIP == "" {
		writeError(w, http.StatusBadRequest, "validation_error", "new_name or new_ip is required")
		return
	}

	path := s.nodesConfigPathForProject(projectID)
	configs, err := nodesconfig.LoadFromFile(path)
	if err != nil && !errors.Is(err, os.ErrNotExist) {
		writeError(w, http.StatusInternalServerError, "load_error",
			fmt.Sprintf("failed to load nodes.json: %v", err))
		return
	}

	renamed := false
	for i := range configs {
		if configs[i].Name == oldName {
			if req.NewName != "" {
				configs[i].Name = req.NewName
			}
			if req.NewIP != "" {
				configs[i].IPAddress = req.NewIP
			}
			renamed = true
			break
		}
	}

	if !renamed {
		writeError(w, http.StatusNotFound, "not_found",
			fmt.Sprintf("node '%s' not found in nodes.json", oldName))
		return
	}

	if err := nodesconfig.SaveToFile(path, configs); err != nil {
		writeError(w, http.StatusInternalServerError, "save_error",
			fmt.Sprintf("failed to save nodes.json: %v", err))
		return
	}

	writeJSON(w, http.StatusOK, map[string]interface{}{
		"renamed":  true,
		"old_name": oldName,
		"count":    len(configs),
	})
}

// handleLoadNodesConfig loads nodes.json from a specified file path.
// PUT /api/v1/nodesconfig/load?path={path}
func (s *Server) handleLoadNodesConfig(w http.ResponseWriter, r *http.Request) {
	path := r.URL.Query().Get("path")
	if path == "" {
		path = s.nodesConfigPath()
	}

	configs, err := nodesconfig.LoadFromFile(path)
	if err != nil {
		if errors.Is(err, os.ErrNotExist) {
			writeError(w, http.StatusNotFound, "not_found",
				fmt.Sprintf("nodes.json not found at: %s", path))
			return
		}
		writeError(w, http.StatusInternalServerError, "load_error",
			fmt.Sprintf("failed to load: %v", err))
		return
	}

	writeJSON(w, http.StatusOK, map[string]interface{}{
		"configs": configs,
		"path":    path,
		"count":   len(configs),
	})
}

// handleGetNodesConfigTree returns the hierarchical tree structure.
// GET /api/v1/nodesconfig/tree
// If ?log_root= is provided, includes actual log files in the tree.
func (s *Server) handleGetNodesConfigTree(w http.ResponseWriter, r *http.Request) {
	// Use project-scoped path if project_id is provided
	projectID := r.URL.Query().Get("project_id")
	path := s.nodesConfigPathForProject(projectID)
	configs, err := nodesconfig.LoadFromFile(path)
	if err != nil {
		if errors.Is(err, os.ErrNotExist) {
			// Return empty tree
			tree := &types.TreeNode{
				Name:     "Root",
				Type:     "root",
				Children: make([]types.TreeNode, 0),
			}
			writeJSON(w, http.StatusOK, map[string]interface{}{
				"tree":  tree,
				"path":  path,
				"count": 0,
			})
			return
		}
		writeError(w, http.StatusInternalServerError, "load_error",
			fmt.Sprintf("failed to load nodes.json: %v", err))
		return
	}

	// Check for log_root query param or use server's logRoot
	logRoot := r.URL.Query().Get("log_root")
	if logRoot == "" {
		// Try to resolve from project
		if projectID != "" {
			if pid, err := strconv.Atoi(projectID); err == nil && pid > 0 {
				if proj, err := s.store.GetProject(int64(pid)); err == nil && proj != nil {
					logRoot = proj.LogRoot
				}
			}
		}
	}
	if logRoot == "" {
		logRoot = s.logRoot()
	}

	// Commander mode: show ALL nodes (files on disk + expected token nodes).
	// Previously used hide_missing=true which hid expected-but-not-yet-executed
	// token nodes, causing "remaining files disappear after command execution."
	hideMissing := false

	var tree *types.TreeNode
	if logRoot != "" {
		tree = nodesconfig.BuildFileTree(configs, logRoot, hideMissing)
	} else {
		tree = nodesconfig.BuildTree(configs)
	}
	writeJSON(w, http.StatusOK, map[string]interface{}{
		"tree":     tree,
		"path":     path,
		"count":    len(configs),
		"log_root": logRoot,
	})
}

// handleGetProjectNodes loads and returns nodes_{id}.json for a specific project.
// GET /api/v1/projects/{id}/nodes
func (s *Server) handleGetProjectNodes(w http.ResponseWriter, r *http.Request) {
	projectID := r.PathValue("id")
	if projectID == "" {
		writeError(w, http.StatusBadRequest, "validation_error", "project id is required")
		return
	}

	path := s.nodesConfigPathForProject(projectID)
	configs, err := nodesconfig.LoadFromFile(path)
	if err != nil {
		log.Printf("handleGetProjectNodes: LoadFromFile(%q) error: %v", path, err)
		if errors.Is(err, os.ErrNotExist) {
			// Return empty array if file doesn't exist
			writeJSON(w, http.StatusOK, map[string]interface{}{
				"configs": make([]types.NodeConfig, 0),
				"path":    path,
			})
			return
		}
		writeError(w, http.StatusInternalServerError, "load_error",
			fmt.Sprintf("failed to load nodes for project %s: %v", projectID, err))
		return
	}
	writeJSON(w, http.StatusOK, map[string]interface{}{
		"configs": configs,
		"path":    path,
	})
}

// handleSaveProjectNodes saves nodes config to nodes_{id}.json for a specific project.
// POST /api/v1/projects/{id}/nodes
func (s *Server) handleSaveProjectNodes(w http.ResponseWriter, r *http.Request) {
	projectID := r.PathValue("id")
	if projectID == "" {
		writeError(w, http.StatusBadRequest, "validation_error", "project id is required")
		return
	}

	var configs []types.NodeConfig
	if err := json.NewDecoder(r.Body).Decode(&configs); err != nil {
		writeError(w, http.StatusBadRequest, "validation_error", "invalid JSON body")
		return
	}

	// Sanitize token_ids (same as handleSaveNodesConfig)
	for i := range configs {
		for j := range configs[i].Tokens {
			tid := configs[i].Tokens[j].TokenID
			if strings.Contains(tid, "_") && strings.Contains(tid, ".") {
				parts := strings.Split(tid, "_")
				last := parts[len(parts)-1]
				last = strings.TrimSuffix(last, filepath.Ext(last))
				if last != "" {
					configs[i].Tokens[j].TokenID = last
				}
			}
		}
	}

	path := s.nodesConfigPathForProject(projectID)
	if err := nodesconfig.SaveToFile(path, configs); err != nil {
		writeError(w, http.StatusInternalServerError, "save_error",
			fmt.Sprintf("failed to save nodes for project %s: %v", projectID, err))
		return
	}

	writeJSON(w, http.StatusOK, map[string]interface{}{
		"saved": true,
		"count": len(configs),
		"path":  path,
	})
}
