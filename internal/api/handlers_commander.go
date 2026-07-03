package api

import (
	"context"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"log"
	"net/http"
	"os"
	"path/filepath"
	"runtime"
	"strconv"
	"strings"
	"time"

	"github.com/falke-ai-circuit/LOGReport/internal/commandqueue"
	"github.com/falke-ai-circuit/LOGReport/internal/lisdiag"
	"github.com/falke-ai-circuit/LOGReport/internal/logfile"
	"github.com/falke-ai-circuit/LOGReport/internal/logwriter"
	"github.com/falke-ai-circuit/LOGReport/internal/nodesconfig"
	"github.com/falke-ai-circuit/LOGReport/internal/parser"
	"github.com/falke-ai-circuit/LOGReport/internal/sysloader"
	"github.com/falke-ai-circuit/LOGReport/internal/telnet"
	"github.com/falke-ai-circuit/LOGReport/internal/types"
)

// ─── NodesConfig Handlers ──────────────────────────────────────────

// nodesConfigPath returns the default path to nodes.json.
// It checks the data directory (from -db-path flag), then cwd, then config dir.
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
	// nodes.json lives inside {logRoot}/_LOG/
	return filepath.Join(p.LogRoot, "_LOG", "nodes.json")
}

// resolveLogRoot returns the effective log root for file writing.
// Priority: server's logRootDir (set via /logs/setroot by frontend) →
// settings LogRoot → first active project's log_root → default temp dir.
func (s *Server) resolveLogRoot() string {
	lr := s.logRoot()
	if lr != "" && lr != "logs" {
		return lr
	}
	// Fall back to settings
	if !globalSettings.loaded {
		s.initSettings()
	}
	st := getSettings()
	if st.LogRoot != "" {
		return st.LogRoot
	}
	// Try to find log_root from the first active project in the store
	if s.store != nil {
		if projs, err := s.store.ListProjects(); err == nil && len(projs) > 0 {
			for _, p := range projs {
				if p.LogRoot != "" && p.Status == "active" {
					return p.LogRoot
				}
			}
			// If no active project, use the first one with a log_root
			if projs[0].LogRoot != "" {
				return projs[0].LogRoot
			}
		}
	}
	// Last resort: temp dir
	if runtime.GOOS == "windows" {
		return "C:\\temp\\logreport-output"
	}
	return "/tmp/logreport-output"
}

// nodesConfigPathForLogRoot returns
func (s *Server) nodesConfigPathForLogRoot(logRoot string) string {
	if logRoot == "" {
		return s.nodesConfigPath()
	}
	return filepath.Join(logRoot, "_LOG", "nodes.json")
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

	// hide_missing=true: Commander mode — only show files that exist on disk
	hideMissing := r.URL.Query().Get("hide_missing") == "true"

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

// ─── Telnet Session Handlers ───────────────────────────────────────

// telnetConnectRequest is the JSON body for creating a telnet session.
type telnetConnectRequest struct {
	Host    string `json:"host"`
	Port    int    `json:"port"`
	Timeout int    `json:"timeout"` // seconds, default 10
}

// handleTelnetConnect creates a persistent telnet session.
// POST /api/v1/telnet/connect
func (s *Server) handleTelnetConnect(w http.ResponseWriter, r *http.Request) {
	var req telnetConnectRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		writeError(w, http.StatusBadRequest, "validation_error", "invalid JSON body")
		return
	}
	if req.Host == "" {
		writeError(w, http.StatusBadRequest, "validation_error", "host is required")
		return
	}
	if req.Port == 0 {
		req.Port = 23
	}
	timeout := 10 * time.Second
	if req.Timeout > 0 {
		timeout = time.Duration(req.Timeout) * time.Second
	}

	sess, err := s.telnetSM.Connect("", req.Host, req.Port, timeout)
	if err != nil {
		writeErrorDetails(w, http.StatusBadGateway, "connection_failed",
			fmt.Sprintf("telnet connect %s:%d failed: %v", req.Host, req.Port, err),
			map[string]string{"host": req.Host, "port": fmt.Sprintf("%d", req.Port)})
		return
	}

	writeJSON(w, http.StatusOK, map[string]interface{}{
		"session_id": sess.ID,
		"host":       req.Host,
		"port":       req.Port,
		"connected":  true,
	})
}

// handleTelnetCommand sends a command to an existing session.
// POST /api/v1/telnet/{sessionID}/command
func (s *Server) handleTelnetCommand(w http.ResponseWriter, r *http.Request) {
	sessionID := r.PathValue("sessionID")
	if sessionID == "" {
		writeError(w, http.StatusBadRequest, "validation_error", "session_id is required")
		return
	}

	var req struct {
		Command string `json:"command"`
	}
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		writeError(w, http.StatusBadRequest, "validation_error", "invalid JSON body")
		return
	}
	if req.Command == "" {
		writeError(w, http.StatusBadRequest, "validation_error", "command is required")
		return
	}

	// Clear the output buffer before sending so the caller gets clean
	// per-command output when they poll GET /telnet/{sessionID}/output.
	// Note: SendCommand is now synchronous — it writes the result to the
	// output buffer before returning. ClearOutput just ensures any stale
	// data from prior commands is removed before the new command runs.
	_ = s.telnetSM.ClearOutput(sessionID)

	if err := s.telnetSM.SendCommand(sessionID, req.Command); err != nil {
		writeError(w, http.StatusBadGateway, "command_failed",
			fmt.Sprintf("failed to send command: %v", err))
		return
	}

	// SendCommand is synchronous — the output is already in the buffer.
	// Read it and include in the response for convenience.
	output, _ := s.telnetSM.GetOutput(sessionID)

	writeJSON(w, http.StatusOK, map[string]interface{}{
		"session_id": sessionID,
		"command":    req.Command,
		"sent":       true,
		"output":     output,
	})
}

// handleTelnetDisconnect closes a telnet session.
// DELETE /api/v1/telnet/{sessionID}
func (s *Server) handleTelnetDisconnect(w http.ResponseWriter, r *http.Request) {
	sessionID := r.PathValue("sessionID")
	if sessionID == "" {
		writeError(w, http.StatusBadRequest, "validation_error", "session_id is required")
		return
	}

	if err := s.telnetSM.Disconnect(sessionID); err != nil {
		writeError(w, http.StatusNotFound, "not_found",
			fmt.Sprintf("session not found: %v", err))
		return
	}

	writeJSON(w, http.StatusOK, map[string]interface{}{
		"session_id":   sessionID,
		"disconnected": true,
	})
}

// handleListTelnetSessions lists all active telnet sessions.
// GET /api/v1/telnet/sessions
func (s *Server) handleListTelnetSessions(w http.ResponseWriter, r *http.Request) {
	ids := s.telnetSM.ListSessions()
	if ids == nil {
		ids = make([]string, 0)
	}
	writeJSON(w, http.StatusOK, map[string]interface{}{
		"sessions": ids,
		"count":    len(ids),
	})
}

// handleTelnetOutput returns the accumulated output buffer for a session.
// GET /api/v1/telnet/{sessionID}/output
func (s *Server) handleTelnetOutput(w http.ResponseWriter, r *http.Request) {
	sessionID := r.PathValue("sessionID")
	if sessionID == "" {
		writeError(w, http.StatusBadRequest, "validation_error", "session_id is required")
		return
	}

	output, err := s.telnetSM.GetOutput(sessionID)
	if err != nil {
		writeError(w, http.StatusNotFound, "not_found",
			fmt.Sprintf("session not found: %v", err))
		return
	}

	writeJSON(w, http.StatusOK, map[string]interface{}{
		"session_id": sessionID,
		"output":     output,
		"length":     len(output),
	})
}

// handleExecuteSingleCommand executes a single command via telnet and returns
// the output. This is used by the context menu for "Print FieldBus Structure",
// "Print Rupi counters", etc. — commands that should execute immediately and
// show output in the terminal, without adding to the queue.
// POST /api/v1/telnet/execute
// Body: {"command": "fis AB010000", "host": "127.0.0.1", "port": 1234}
func (s *Server) handleExecuteSingleCommand(w http.ResponseWriter, r *http.Request) {
	var req struct {
		Command    string `json:"command"`
		Host       string `json:"host"`
		Port       int    `json:"port"`
		NodeName   string `json:"node_name"`
		TokenType  string `json:"token_type"`
		TokenID    string `json:"token_id"`
		IPAddress  string `json:"ip_address"`
	}
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		writeError(w, http.StatusBadRequest, "validation_error", "invalid JSON body")
		return
	}
	if req.Command == "" {
		writeError(w, http.StatusBadRequest, "validation_error", "command is required")
		return
	}
	if req.Host == "" {
		// Use settings if available, otherwise default
		if !globalSettings.loaded {
			s.initSettings()
		}
		st := getSettings()
		if st.DIAHost != "" {
			req.Host = st.DIAHost
		} else {
			req.Host = "127.0.0.1"
		}
	}
	if req.Port == 0 {
		if !globalSettings.loaded {
			s.initSettings()
		}
		st := getSettings()
		if st.DIAPort > 0 {
			req.Port = st.DIAPort
		} else {
			req.Port = 1234
		}
	}

	// Sanitize token_id: if it looks like a filename (contains both _ and .),
	// extract just the token number part (last _-separated segment without extension)
	if req.TokenID != "" {
		if strings.Contains(req.TokenID, "_") && strings.Contains(req.TokenID, ".") {
			base := strings.TrimSuffix(req.TokenID, filepath.Ext(req.TokenID))
			parts := strings.Split(base, "_")
			if len(parts) > 0 {
				req.TokenID = parts[len(parts)-1]
			}
		}
	}

	// Find an existing session or create a new one
	ids := s.telnetSM.ListSessions()
	var sessionID string

	if len(ids) > 0 {
		sessionID = ids[0]
		sess, ok := s.telnetSM.GetSession(sessionID)
		if ok && sess != nil && !sess.Connected {
			s.telnetSM.Disconnect(sessionID)
			sessionID = ""
		}
	}

	if sessionID == "" {
		sess, err := s.telnetSM.Connect("", req.Host, req.Port, 10*time.Second)
		if err != nil {
			writeError(w, http.StatusBadGateway, "connection_failed",
				fmt.Sprintf("telnet connect %s:%d failed: %v", req.Host, req.Port, err))
			return
		}
		sessionID = sess.ID
	}

	// Clear and send command
	_ = s.telnetSM.ClearOutput(sessionID)
	if err := s.telnetSM.SendCommand(sessionID, req.Command); err != nil {
		sess, ok := s.telnetSM.GetSession(sessionID)
		if ok && sess != nil {
			sess.Connected = false
		}
		writeError(w, http.StatusBadGateway, "command_failed",
			fmt.Sprintf("failed to send command: %v", err))
		return
	}

	// Wait for output
	output := waitForOutput(s.telnetSM, sessionID, 10*time.Second, 2*time.Second, nil)

	// Write output to log file if node info is provided (from context menu)
	fileWritten := false
	var filePathStr string
	if req.NodeName != "" && req.TokenType != "" {
		// If IP address not provided, look it up from nodes.json
		if req.IPAddress == "" {
			// Try project-scoped path first if we can resolve it from settings/logroot
			configPath := s.nodesConfigPath()
			if lr := s.resolveLogRoot(); lr != "" {
				projectPath := s.nodesConfigPathForLogRoot(lr)
				if _, err := os.Stat(projectPath); err == nil {
					configPath = projectPath
				}
			}
			if configs, err := nodesconfig.LoadFromFile(configPath); err == nil {
				for _, c := range configs {
					if c.Name == req.NodeName {
						req.IPAddress = c.IPAddress
						break
					}
					// Also check station name match (e.g. AP01m matches AP01)
					if extractStationNameFromConfig(c.Name) == req.NodeName {
						req.IPAddress = c.IPAddress
						break
					}
				}
			}
		}
		// Use resolveLogRoot for file writing (project-aware)
		lr := s.resolveLogRoot()
		_ = os.MkdirAll(lr, 0755)
		lw := logwriter.New(lr)
		if err := lw.WriteOutputWithIP(req.NodeName, req.TokenType, req.TokenID, output, req.IPAddress); err != nil {
			log.Printf("telnet/execute: failed to write log for %s/%s: %v", req.NodeName, req.TokenID, err)
		} else {
			fileWritten = true
			filePathStr = lw.LogPath(req.NodeName, req.TokenType, req.TokenID, req.IPAddress)
		}
	}

	writeJSON(w, http.StatusOK, map[string]interface{}{
		"session_id":   sessionID,
		"command":      req.Command,
		"output":       output,
		"sent":         true,
		"file_written": fileWritten,
		"file_path":    filePathStr,
	})
}

// ─── Command Queue Handlers ────────────────────────────────────────

// handleQueueAdd adds a command to the queue.
// POST /api/v1/commandqueue/add
func (s *Server) handleQueueAdd(w http.ResponseWriter, r *http.Request) {
	var cmd commandqueue.QueuedCommand
	if err := json.NewDecoder(r.Body).Decode(&cmd); err != nil {
		writeError(w, http.StatusBadRequest, "validation_error", "invalid JSON body")
		return
	}
	if cmd.Command == "" {
		writeError(w, http.StatusBadRequest, "validation_error", "command is required")
		return
	}

	s.commandQueue.Add(cmd)
	_, total, _ := s.commandQueue.Status()
	writeJSON(w, http.StatusOK, map[string]interface{}{
		"added": true,
		"total": total,
	})
}

// handleQueueStart starts queue execution.
// POST /api/v1/commandqueue/start
func (s *Server) handleQueueStart(w http.ResponseWriter, r *http.Request) {
	if s.commandQueue == nil {
		writeError(w, http.StatusInternalServerError, "internal_error", "command queue not initialized")
		return
	}

	// Execute commands via the SessionManager.
	// Auto-reconnects if the telnet session dies (DIA closes connections
	// after timeout or errors). Matches Python sequential_command_processor.py
	// behavior: if connection lost, reconnect and retry.
	executor := func(cmd commandqueue.QueuedCommand) (string, error) {
		// LISDIAG commands go through a separate telnet connection to port 4321,
		// not through the DIA session on port 1234.
		if cmd.Type == commandqueue.CmdLISDiag {
			return s.executeLISDiag(cmd)
		}

		// Find an active session to send commands through
		ids := s.telnetSM.ListSessions()
		var sessionID string

		if len(ids) > 0 {
			sessionID = ids[0]
			// Check if session is still connected
			sess, ok := s.telnetSM.GetSession(sessionID)
			if ok && sess != nil && !sess.Connected {
				// Session died — disconnect and reconnect
				s.telnetSM.Disconnect(sessionID)
				sessionID = ""
			}
		}

		if sessionID == "" {
			// No active session — try to reconnect using settings
			// or stored host/port from a previous session.
			// F8 fix: create a context that cancels when cancelCh closes,
			// so DialContext aborts immediately on Cancel/Pause even if
			// the host is unreachable (Dial would otherwise block 10s).
			cancelCh := s.commandQueue.CancelCh()
			ctx, cancel := context.WithCancel(context.Background())
			if cancelCh != nil {
				go func() {
					select {
					case <-cancelCh:
						cancel()
					case <-ctx.Done():
					}
				}()
			}
			if !globalSettings.loaded {
				s.initSettings()
			}
			st := getSettings()
			host := st.DIAHost
			if host == "" {
				host = "127.0.0.1"
			}
			port := st.DIAPort
			if port == 0 {
				port = 1234
			}
			if len(ids) > 0 {
				oldSess, ok := s.telnetSM.GetSession(ids[0])
				if ok && oldSess != nil {
					host = oldSess.Address
					port = oldSess.Port
				}
			}
			sess, err := s.telnetSM.ConnectContext(ctx, "", host, port, 10*time.Second)
			cancel() // release context resources after connect completes
			if err != nil {
				// Check if the error was due to cancellation
				if ctx.Err() != nil {
					return "", fmt.Errorf("cancelled during connect")
				}
				return "", fmt.Errorf("reconnect failed: %w", err)
			}
			sessionID = sess.ID
		}

		// 1. Clear the session output buffer before sending
		_ = s.telnetSM.ClearOutput(sessionID)

		// 2. Send the command
		if err := s.telnetSM.SendCommand(sessionID, cmd.Command); err != nil {
			// Command failed — mark session as needing reconnect for next command
			sess, ok := s.telnetSM.GetSession(sessionID)
			if ok && sess != nil {
				sess.Connected = false
			}
			return "", err
		}

		// 3. Wait for output: poll GetOutput, wait up to 10 seconds for
		// non-empty output, then collect for 2 more seconds for trailing data
		output := waitForOutput(s.telnetSM, sessionID, 10*time.Second, 2*time.Second, s.commandQueue.CancelCh())

		// 4. Write output to structured log files
		// Resolve log root: use server's logRoot if it's been set via /logs/setroot,
		// otherwise fall back to settings or default. The frontend calls /logs/setroot
		// when a project is selected, so s.logRoot() should be the project's log_root.
		lw := logwriter.New(s.resolveLogRoot())
		tokenType := string(cmd.Type)
		if tokenType == "" {
			tokenType = "raw"
		}
		if err := lw.WriteOutputWithIP(cmd.NodeName, tokenType, cmd.TokenID, output, cmd.IPAddress); err != nil {
			log.Printf("commandqueue: failed to write log for %s/%s: %v", cmd.NodeName, cmd.TokenID, err)
		}

		// 5. Return the output string
		return output, nil
	}

	go func() {
		if err := s.commandQueue.Start(executor); err != nil {
			log.Printf("commandqueue: start error: %v", err)
		}
	}()

	writeJSON(w, http.StatusOK, map[string]interface{}{
		"started": true,
	})
}

// handleQueuePause pauses the queue.
// POST /api/v1/commandqueue/pause
func (s *Server) handleQueuePause(w http.ResponseWriter, r *http.Request) {
	s.commandQueue.Pause()
	writeJSON(w, http.StatusOK, map[string]interface{}{"paused": true})
}

// handleQueueResume resumes the queue and restarts execution.
// POST /api/v1/commandqueue/resume
func (s *Server) handleQueueResume(w http.ResponseWriter, r *http.Request) {
	s.commandQueue.Resume()

	// Re-create the executor with auto-reconnect (same as handleQueueStart)
	executor := func(cmd commandqueue.QueuedCommand) (string, error) {
		// LISDIAG commands go through a separate telnet connection to port 4321,
		// not through the DIA session on port 1234.
		if cmd.Type == commandqueue.CmdLISDiag {
			return s.executeLISDiag(cmd)
		}

		ids := s.telnetSM.ListSessions()
		var sessionID string

		if len(ids) > 0 {
			sessionID = ids[0]
			sess, ok := s.telnetSM.GetSession(sessionID)
			if ok && sess != nil && !sess.Connected {
				s.telnetSM.Disconnect(sessionID)
				sessionID = ""
			}
		}

		if sessionID == "" {
			// F8 fix: context-aware connect so Cancel/Pause aborts Dial immediately
			cancelCh := s.commandQueue.CancelCh()
			ctx, cancel := context.WithCancel(context.Background())
			if cancelCh != nil {
				go func() {
					select {
					case <-cancelCh:
						cancel()
					case <-ctx.Done():
					}
				}()
			}
			if !globalSettings.loaded {
				s.initSettings()
			}
			st := getSettings()
			host := st.DIAHost
			if host == "" {
				host = "127.0.0.1"
			}
			port := st.DIAPort
			if port == 0 {
				port = 1234
			}
			if len(ids) > 0 {
				oldSess, ok := s.telnetSM.GetSession(ids[0])
				if ok && oldSess != nil {
					host = oldSess.Address
					port = oldSess.Port
				}
			}
			sess, err := s.telnetSM.ConnectContext(ctx, "", host, port, 10*time.Second)
			cancel()
			if err != nil {
				if ctx.Err() != nil {
					return "", fmt.Errorf("cancelled during connect")
				}
				return "", fmt.Errorf("reconnect failed: %w", err)
			}
			sessionID = sess.ID
		}

		_ = s.telnetSM.ClearOutput(sessionID)
		if err := s.telnetSM.SendCommand(sessionID, cmd.Command); err != nil {
			sess, ok := s.telnetSM.GetSession(sessionID)
			if ok && sess != nil {
				sess.Connected = false
			}
			return "", err
		}
		output := waitForOutput(s.telnetSM, sessionID, 10*time.Second, 2*time.Second, s.commandQueue.CancelCh())

		lw := logwriter.New(s.resolveLogRoot())
		tokenType := string(cmd.Type)
		if tokenType == "" {
			tokenType = "raw"
		}
		if err := lw.WriteOutputWithIP(cmd.NodeName, tokenType, cmd.TokenID, output, cmd.IPAddress); err != nil {
			log.Printf("commandqueue: failed to write log for %s/%s: %v", cmd.NodeName, cmd.TokenID, err)
		}

		return output, nil
	}

	go func() {
		if err := s.commandQueue.Start(executor); err != nil {
			log.Printf("commandqueue: resume error: %v", err)
		}
	}()

	writeJSON(w, http.StatusOK, map[string]interface{}{
		"resumed": true,
	})
}

// handleQueueCancel cancels the queue.
// POST /api/v1/commandqueue/cancel
func (s *Server) handleQueueCancel(w http.ResponseWriter, r *http.Request) {
	s.commandQueue.Cancel()
	writeJSON(w, http.StatusOK, map[string]interface{}{"cancelled": true})
}

// handleQueueStatus returns the current queue state.
// GET /api/v1/commandqueue/status
func (s *Server) handleQueueStatus(w http.ResponseWriter, r *http.Request) {
	current, total, state := s.commandQueue.Status()
	cmds := s.commandQueue.Commands()
	if cmds == nil {
		cmds = make([]commandqueue.QueuedCommand, 0)
	}
	writeJSON(w, http.StatusOK, map[string]interface{}{
		"current":  current,
		"total":    total,
		"state":    string(state),
		"commands": cmds,
	})
}

// handleQueueBatch generates "Print All Nodes" batch commands.
// POST /api/v1/commandqueue/batch
// Body: {"configs": [...], "session_id": "...", "project_id": 5}
// If configs is empty, loads from nodes_{project_id}.json (or nodes.json if no project_id).
func (s *Server) handleQueueBatch(w http.ResponseWriter, r *http.Request) {
	var req struct {
		Configs   []types.NodeConfig `json:"configs"`
		SessionID string             `json:"session_id"`
		ProjectID string             `json:"project_id"`
	}
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		// If no body, load from project-scoped nodes file
		path := s.nodesConfigPathForProject(req.ProjectID)
		configs, loadErr := nodesconfig.LoadFromFile(path)
		if loadErr != nil {
			writeError(w, http.StatusBadRequest, "validation_error",
				"invalid JSON body and no nodes.json found")
			return
		}
		req.Configs = configs
	}

	if len(req.Configs) == 0 {
		// Try loading from project-scoped file
		path := s.nodesConfigPathForProject(req.ProjectID)
		configs, _ := nodesconfig.LoadFromFile(path)
		req.Configs = configs
	}

	if len(req.Configs) == 0 {
		writeError(w, http.StatusBadRequest, "validation_error", "no node configs provided")
		return
	}

	s.commandQueue.Reset()
	s.commandQueue.AddBatchFromNodes(req.Configs, req.SessionID, s.telnetSM)
	_, total, _ := s.commandQueue.Status()

	writeJSON(w, http.StatusOK, map[string]interface{}{
		"batch_added": true,
		"total":       total,
	})
}

// handleQueueBatchNode generates commands for a single node only.
// POST /api/v1/commandqueue/batch-node
// Body: {"node_name": "NCU2", "token_type": "FBC"}  (token_type optional, empty = all types)
// This matches the Python right-click "Execute All Print Commands for {node}" behavior.
func (s *Server) handleQueueBatchNode(w http.ResponseWriter, r *http.Request) {
	var req struct {
		NodeName  string `json:"node_name"`
		TokenType string `json:"token_type"` // optional: FBC, RPC, LOG, or empty for all
	}
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		writeError(w, http.StatusBadRequest, "validation_error", "invalid JSON body")
		return
	}
	if req.NodeName == "" {
		writeError(w, http.StatusBadRequest, "validation_error", "node_name is required")
		return
	}

	// Load configs from project-scoped nodes file
	// Check for project_id in URL query first, then try resolving from logroot
	projectID := r.URL.Query().Get("project_id")
	var path string
	if projectID != "" {
		path = s.nodesConfigPathForProject(projectID)
	} else {
		// Fall back to resolving from log root
		lr := s.resolveLogRoot()
		path = s.nodesConfigPathForLogRoot(lr)
	}
	configs, err := nodesconfig.LoadFromFile(path)
	if err != nil {
		writeError(w, http.StatusInternalServerError, "load_error",
			fmt.Sprintf("failed to load nodes.json: %v", err))
		return
	}

	// Filter to just the requested node
	var filtered []types.NodeConfig
	for _, c := range configs {
		if c.Name == req.NodeName {
			// If token_type specified, filter tokens
			// Exception: "LISDiag" means we want LIS tokens but via LisDiag path
			filterType := req.TokenType
			if strings.EqualFold(filterType, "LISDiag") {
				filterType = "LIS" // map LISDiag to LIS for token filtering
			}
			if filterType != "" {
				var filteredTokens []types.Token
				for _, t := range c.Tokens {
					if strings.EqualFold(string(t.TokenType), filterType) {
						filteredTokens = append(filteredTokens, t)
					}
				}
				c.Tokens = filteredTokens
			}
			filtered = append(filtered, c)
			break
		}
	}

	if len(filtered) == 0 {
		writeError(w, http.StatusNotFound, "not_found",
			fmt.Sprintf("node %s not found in nodes.json", req.NodeName))
		return
	}

	s.commandQueue.Reset()
	if strings.EqualFold(req.TokenType, "LISDiag") {
		// LISDIAG path: generate telnet commands for LisDiag on port 4321
		s.commandQueue.AddBatchFromNodesLISDiag(filtered, "password")
	} else {
		s.commandQueue.AddBatchFromNodes(filtered, "", s.telnetSM)
	}
	_, total, _ := s.commandQueue.Status()

	writeJSON(w, http.StatusOK, map[string]interface{}{
		"batch_added": true,
		"node_name":   req.NodeName,
		"token_type":  req.TokenType,
		"total":       total,
	})
}

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
	}
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		writeError(w, http.StatusBadRequest, "validation_error", "invalid JSON body")
		return
	}
	if req.TokenType == "" || req.TokenID == "" {
		writeError(w, http.StatusBadRequest, "validation_error", "token_type and token_id are required")
		return
	}

	lw := logwriter.New(s.logRoot())
	if err := lw.WriteOutput(nodeName, req.TokenType, req.TokenID, req.Output); err != nil {
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

// ─── Scan Compare Handler ──────────────────────────────────────────

// scanCompareRequest is the JSON body for scan comparison.
type scanCompareRequest struct {
	NodeAddress string `json:"node_address"`
	Port        int    `json:"port"`
	Token       string `json:"token"`
	FileData    string `json:"file_data"`
}

// comparisonCell represents a single cell comparison result.
type comparisonCell struct {
	Row       int    `json:"row"`
	Col       int    `json:"col"`
	FileValue string `json:"file_value,omitempty"`
	LiveValue string `json:"live_value,omitempty"`
	Status    string `json:"status"` // "match", "mismatch", "file_only", "live_only"
}

// handleScanCompare compares file FBC data with live telnet scan.
// POST /api/v1/scan/compare
func (s *Server) handleScanCompare(w http.ResponseWriter, r *http.Request) {
	var req scanCompareRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		writeError(w, http.StatusBadRequest, "validation_error", "invalid JSON body")
		return
	}
	if req.NodeAddress == "" || req.Token == "" {
		writeError(w, http.StatusBadRequest, "validation_error",
			"node_address and token are required")
		return
	}
	if req.Port == 0 {
		req.Port = 23
	}

	// Parse file data
	fileModules, err := parser.ParseFBC(req.FileData)
	if err != nil {
		writeErrorDetails(w, http.StatusBadRequest, "parse_error",
			fmt.Sprintf("failed to parse file data: %v", err),
			map[string]string{"file_data_length": fmt.Sprintf("%d", len(req.FileData))})
		return
	}

	// Connect to live node and scan
	client, err := telnet.Dial(req.NodeAddress, req.Port, 30*time.Second)
	if err != nil {
		writeErrorDetails(w, http.StatusBadGateway, "connection_failed",
			fmt.Sprintf("telnet connect %s:%d failed: %v", req.NodeAddress, req.Port, err),
			map[string]string{"node_address": req.NodeAddress})
		return
	}
	defer client.Close()

	cmd := telnet.FBCPrint(req.Token)
	if err := client.SendCommand(cmd); err != nil {
		writeError(w, http.StatusBadGateway, "scan_failed",
			fmt.Sprintf("telnet command failed: %v", err))
		return
	}
	liveOutput, err := client.ReadUntilPrompt()
	if err != nil {
		writeError(w, http.StatusBadGateway, "scan_failed",
			fmt.Sprintf("reading live output failed: %v", err))
		return
	}

	liveModules, err := parser.ParseFBC(liveOutput)
	if err != nil {
		writeError(w, http.StatusBadGateway, "parse_error",
			fmt.Sprintf("failed to parse live output: %v", err))
		return
	}

	// Build comparison map: module position → channel position → channel type
	fileMap := make(map[int]map[int]string)
	for _, mod := range fileModules {
		fileMap[mod.Position] = make(map[int]string)
		for _, ch := range mod.Channels {
			fileMap[mod.Position][ch.Position] = string(ch.Type)
		}
	}
	liveMap := make(map[int]map[int]string)
	for _, mod := range liveModules {
		liveMap[mod.Position] = make(map[int]string)
		for _, ch := range mod.Channels {
			liveMap[mod.Position][ch.Position] = string(ch.Type)
		}
	}

	// Build cell-by-cell comparison
	cells := make([]comparisonCell, 0)
	matching, mismatched, fileOnly, liveOnly := 0, 0, 0, 0

	// Collect all module positions
	allMods := make(map[int]bool)
	for pos := range fileMap {
		allMods[pos] = true
	}
	for pos := range liveMap {
		allMods[pos] = true
	}

	for modPos := range allMods {
		fileChs := fileMap[modPos]
		liveChs := liveMap[modPos]

		// Collect all channel positions in this module
		allChs := make(map[int]bool)
		for ch := range fileChs {
			allChs[ch] = true
		}
		for ch := range liveChs {
			allChs[ch] = true
		}

		for chPos := range allChs {
			fv := fileChs[chPos]
			lv := liveChs[chPos]
			cell := comparisonCell{Row: modPos, Col: chPos, FileValue: fv, LiveValue: lv}

			switch {
			case fv != "" && lv != "":
				if fv == lv {
					cell.Status = "match"
					matching++
				} else {
					cell.Status = "mismatch"
					mismatched++
				}
			case fv != "" && lv == "":
				cell.Status = "file_only"
				fileOnly++
			case fv == "" && lv != "":
				cell.Status = "live_only"
				liveOnly++
			}

			cells = append(cells, cell)
		}
	}

	totalCells := matching + mismatched + fileOnly + liveOnly

	writeJSON(w, http.StatusOK, map[string]interface{}{
		"comparison": map[string]interface{}{
			"total_cells": totalCells,
			"matching":    matching,
			"mismatched":  mismatched,
			"file_only":   fileOnly,
			"live_only":   liveOnly,
			"cells":       cells,
		},
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

// ─── Helpers ────────────────────────────────────────────────────────

// extractStationNameFromConfig derives station name from a config node name.
// Uses the same logic as logwriter.extractStationName: only AP prefix gets m/r.
func extractStationNameFromConfig(nodeName string) string {
	base := nodeName
	if idx := strings.Index(base, "_"); idx >= 0 {
		base = base[:idx]
	}
	if idx := strings.Index(base, " "); idx >= 0 {
		base = base[:idx]
	}
	if strings.HasSuffix(base, "m") || strings.HasSuffix(base, "r") {
		return base
	}
	if strings.HasPrefix(base, "AP") {
		isReserve := strings.Contains(nodeName, "Reserve") || strings.Contains(nodeName, "_r")
		if isReserve {
			return base + "r"
		}
		return base + "m"
	}
	return base
}

// waitForOutput polls the session output buffer for non-empty output.
// It waits up to maxWait for the first non-empty result, then collects
// for trailWait more seconds to capture trailing data.
// If cancelCh is non-nil and closed, it returns immediately with whatever
// output has been collected so far (used by Pause/Cancel to abort fast).
func waitForOutput(sm *telnet.SessionManager, sessionID string, maxWait, trailWait time.Duration, cancelCh chan struct{}) string {
	deadline := time.Now().Add(maxWait)
	ticker := time.NewTicker(100 * time.Millisecond)
	defer ticker.Stop()

	// Phase 1: Wait for non-empty output
	for time.Now().Before(deadline) {
		select {
		case <-cancelCh:
			// Cancelled — return whatever we have
			out, _ := sm.GetOutput(sessionID)
			return out
		default:
		}

		out, err := sm.GetOutput(sessionID)
		if err != nil {
			return ""
		}
		if out != "" {
			// Phase 2: Collect trailing data
			time.Sleep(trailWait)
			final, _ := sm.GetOutput(sessionID)
			if final != "" {
				return final
			}
			return out
		}

		select {
		case <-ticker.C:
		case <-cancelCh:
			// Cancelled during wait — return whatever we have
			out, _ := sm.GetOutput(sessionID)
			return out
		}
	}

	// Timeout: return whatever we have (may be empty)
	out, _ := sm.GetOutput(sessionID)
	return out
}

// ─── Sys File Handlers ──────────────────────────────────────────────

// handleLoadSysFiles loads .sys files from a directory and creates the
// FBC/RPC/LOG/LIS folder structure.
// POST /api/v1/sysfiles/load
func (s *Server) handleLoadSysFiles(w http.ResponseWriter, r *http.Request) {
	var req struct {
		Directory string `json:"directory"`
		OutputDir string `json:"output_dir"`
	}
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		writeError(w, http.StatusBadRequest, "validation_error", "invalid JSON body")
		return
	}
	if req.Directory == "" {
		writeError(w, http.StatusBadRequest, "validation_error", "directory is required")
		return
	}
	if req.OutputDir == "" {
		writeError(w, http.StatusBadRequest, "validation_error", "output_dir is required")
		return
	}

	log.Printf("handleLoadSysFiles: loading from %q → output %q", req.Directory, req.OutputDir)

	configs, err := sysloader.LoadSysFiles(req.Directory)
	if err != nil {
		writeError(w, http.StatusInternalServerError, "load_error",
			fmt.Sprintf("failed to load sys files: %v", err))
		return
	}
	log.Printf("handleLoadSysFiles: loaded %d configs from %q", len(configs), req.Directory)

	if err := sysloader.CreateFolderStructure(req.OutputDir, configs); err != nil {
		writeError(w, http.StatusInternalServerError, "create_error",
			fmt.Sprintf("failed to create folder structure: %v", err))
		return
	}
	log.Printf("handleLoadSysFiles: created folder structure in %q", req.OutputDir)

	writeJSON(w, http.StatusOK, map[string]interface{}{
		"configs_count": len(configs),
		"directory":     req.Directory,
		"output_dir":    req.OutputDir,
	})
}

// handleSysFileParseDir parses .sys files from a directory and returns
// the configs as JSON without creating folders.
// GET /api/v1/sysfiles/parse?dir={path}
func (s *Server) handleSysFileParseDir(w http.ResponseWriter, r *http.Request) {
	dir := r.URL.Query().Get("dir")
	if dir == "" {
		writeError(w, http.StatusBadRequest, "validation_error", "dir query parameter is required")
		return
	}

	configs, err := sysloader.LoadSysFiles(dir)
	if err != nil {
		writeError(w, http.StatusInternalServerError, "load_error",
			fmt.Sprintf("failed to parse sys files: %v", err))
		return
	}

	writeJSON(w, http.StatusOK, map[string]interface{}{
		"configs": configs,
		"count":   len(configs),
		"dir":     dir,
	})
}

// handleSysFileScan auto-scans a BU directory for .sys files, parses them,
// and returns the configs with optional filtering. The frontend can display
// the configs for review/filtering before saving to nodes.json.
//
// GET /api/v1/sysfiles/scan?dir={path}&include_fbc={bool}&include_rpc={bool}&include_log={bool}&include_lis={bool}&exclude_nodes={comma-separated}
//
// Query params:
//   dir          — directory to scan (required)
//   include_fbc  — include FBC tokens (default true)
//   include_rpc  — include RPC tokens (default true)
//   include_log  — include LOG tokens (default true)
//   include_lis  — include LIS tokens (default false)
//   exclude_nodes — comma-separated node names to exclude
func (s *Server) handleSysFileScan(w http.ResponseWriter, r *http.Request) {
	dir := r.URL.Query().Get("dir")
	if dir == "" {
		writeError(w, http.StatusBadRequest, "validation_error", "dir query parameter is required")
		return
	}

	configs, err := sysloader.LoadSysFiles(dir)
	if err != nil {
		writeError(w, http.StatusInternalServerError, "load_error",
			fmt.Sprintf("failed to parse sys files: %v", err))
		return
	}

	// Parse filter parameters
	includeFBC := r.URL.Query().Get("include_fbc") != "false"
	includeRPC := r.URL.Query().Get("include_rpc") != "false"
	includeLOG := r.URL.Query().Get("include_log") != "false"
	includeLIS := r.URL.Query().Get("include_lis") == "true"
	excludeNodesStr := r.URL.Query().Get("exclude_nodes")
	excludeNodes := make(map[string]bool)
	if excludeNodesStr != "" {
		for _, n := range strings.Split(excludeNodesStr, ",") {
			excludeNodes[strings.TrimSpace(n)] = true
		}
	}

	// Apply filters
	filtered := make([]types.NodeConfig, 0, len(configs))
	for _, cfg := range configs {
		// Skip excluded nodes
		if excludeNodes[cfg.Name] {
			continue
		}

		// Filter tokens by type
		var filteredTokens []types.Token
		for _, tok := range cfg.Tokens {
			switch string(tok.TokenType) {
			case "FBC":
				if includeFBC {
					filteredTokens = append(filteredTokens, tok)
				}
			case "RPC":
				if includeRPC {
					filteredTokens = append(filteredTokens, tok)
				}
			case "LOG":
				if includeLOG {
					filteredTokens = append(filteredTokens, tok)
				}
			case "LIS":
				if includeLIS {
					filteredTokens = append(filteredTokens, tok)
				}
			default:
				// Include unknown types by default
				filteredTokens = append(filteredTokens, tok)
			}
		}
		cfg.Tokens = filteredTokens

		// Only include nodes that have at least one token after filtering
		if len(cfg.Tokens) > 0 {
			filtered = append(filtered, cfg)
		}
	}

	// Also list subdirectories and .sys files found
	sysFiles := make([]string, 0)
	if entries, err := os.ReadDir(dir); err == nil {
		for _, entry := range entries {
			if !entry.IsDir() && strings.HasSuffix(strings.ToLower(entry.Name()), ".sys") {
				sysFiles = append(sysFiles, entry.Name())
			}
		}
	}

	writeJSON(w, http.StatusOK, map[string]interface{}{
		"configs":      filtered,
		"count":        len(filtered),
		"total_before_filter": len(configs),
		"dir":          dir,
		"sys_files":    sysFiles,
		"filters": map[string]interface{}{
			"include_fbc":  includeFBC,
			"include_rpc":  includeRPC,
			"include_log":  includeLOG,
			"include_lis":  includeLIS,
			"exclude_nodes": strings.Split(excludeNodesStr, ","),
		},
	})
}


// handleSysFileParseMulti parses multiple uploaded .sys files and returns merged configs.
// POST /api/v1/sysfiles/parse-multi (multipart/form-data, field "files" repeated)
func (s *Server) handleSysFileParseMulti(w http.ResponseWriter, r *http.Request) {
	// 32MB max upload for multiple sys files
	if err := r.ParseMultipartForm(32 << 20); err != nil {
		writeError(w, http.StatusBadRequest, "validation_error", "failed to parse multipart form")
		return
	}

	// Collect all uploaded files
	r.ParseMultipartForm(32 << 20) // already parsed, safe to call again

	// Save each file to a temp dir, collect paths
	tmpDir, err := os.MkdirTemp("", "logreport-sysfiles-*")
	if err != nil {
		writeError(w, http.StatusInternalServerError, "internal_error", "failed to create temp dir")
		return
	}
	defer os.RemoveAll(tmpDir)

	var filePaths []string
	var fileNames []string

	// r.MultipartForm.File is a map[string][]*multipart.FileHeader
	for _, headers := range r.MultipartForm.File {
		for _, header := range headers {
			if !strings.HasSuffix(strings.ToLower(header.Filename), ".sys") {
				continue
			}
			src, err := header.Open()
			if err != nil {
				continue
			}
			tmpPath := filepath.Join(tmpDir, header.Filename)
			dst, err := os.Create(tmpPath)
			if err != nil {
				src.Close()
				continue
			}
			if _, err := io.Copy(dst, src); err != nil {
				dst.Close()
				src.Close()
				continue
			}
			dst.Close()
			src.Close()
			filePaths = append(filePaths, tmpPath)
			fileNames = append(fileNames, header.Filename)
		}
	}

	if len(filePaths) == 0 {
		writeError(w, http.StatusBadRequest, "validation_error", "no .sys files found in upload")
		return
	}

	configs, err := sysloader.LoadSysFilesFromPaths(filePaths)
	if err != nil {
		writeError(w, http.StatusInternalServerError, "parse_error",
			fmt.Sprintf("failed to parse sys files: %v", err))
		return
	}

	writeJSON(w, http.StatusOK, map[string]interface{}{
		"configs":  configs,
		"count":    len(configs),
		"files":    fileNames,
		"file_count": len(fileNames),
	})
}

// ─── Scan Nodes Handler (DIA "print structure") ──────────────────────

// handleScanNodes connects to DIA, sends "systemtest node_list" to generate
// a complete node listing with hw-address, token, IP, OS, slots and program names.
// Falls back to "print structure" + token probing if node_list fails.
// POST /api/v1/sysfiles/scan-nodes
func (s *Server) handleScanNodes(w http.ResponseWriter, r *http.Request) {
	// 95-second hard timeout — the scan can take up to ~70s in worst case
	// (15s connect + 2s delay + 15s systemtest + 20s nodelist poll + 15s print structure + probing)
	// but must not hang indefinitely. Context cancellation propagates to telnet reads.
	ctx, cancel := context.WithTimeout(r.Context(), 95*time.Second)
	defer cancel()
	_ = ctx // r.Context() is already used by the HTTP server; ctx is for future use

	// Load settings for DIA host/port and BU directory
	if !globalSettings.loaded {
		s.initSettings()
	}
	st := getSettings()
	host := st.DIAHost
	if host == "" {
		host = "127.0.0.1"
	}
	port := st.DIAPort
	if port == 0 {
		port = 1234
	}
	buDir := st.BUDir
	if buDir == "" {
		buDir = "C:\\dna\\CA\\bu"
		if runtime.GOOS != "windows" {
			buDir = "/dna/CA/bu"
		}
	}

	// Step 0: Try reading .sys files from the BU directory first.
	// This gives the SAME result as manually importing .sys files —
	// real IP addresses, FBC/RPC tokens, full node names.
	// The .sys files are the authoritative source of node configuration.
	buConfigs := tryLoadSysFromBUDir(buDir)
	if len(buConfigs) > 0 {
		writeJSON(w, http.StatusOK, map[string]interface{}{
			"configs":    buConfigs,
			"count":      len(buConfigs),
			"method":     "bu_sys_files",
			"bu_dir":     buDir,
		})
		return
	}

	// Disconnect any existing session to avoid conflicts (DIA allows only 1 connection)
	for _, id := range s.telnetSM.ListSessions() {
		s.telnetSM.Disconnect(id)
	}

	// Create a fresh session
	sess, err := s.telnetSM.Connect("", host, port, 15*time.Second)
	if err != nil {
		writeError(w, http.StatusBadGateway, "connection_failed",
			fmt.Sprintf("DIA connect %s:%d failed: %v", host, port, err))
		return
	}
	// Nil session safety — Connect should never return nil+nil, but guard against panics
	if sess == nil {
		writeError(w, http.StatusInternalServerError, "session_error",
			"telnet session returned nil after connect")
		return
	}
	sessionID := sess.ID
	defer s.telnetSM.Disconnect(sessionID)

	// verifySystemMode() in Connect() already:
	// 1. Read initial DIA response, sent "y" only if override prompt was present
	// 2. Cleared the line editor (Ctrl+X + Ctrl+Z + Enter)
	// 3. Entered system mode
	// We're already in system mode here — don't re-handle override or send "systemmode"

	// Step 1: Delete old nodelist files to detect fresh generation
	// DIA writes to its own working directory, not LOGReport's
	// BUT: some DIA versions don't support `systemtest node_list`. In that case,
	// we fall back to the existing nodelist.txt that was generated at DIA startup.
	// Save the existing content before deleting, so we can restore it if the
	// command fails to regenerate the file.
	knownPaths := []string{
		"C:\\dna\\CA\\dia\\nodelist.txt",
		"C:\\dna\\CA\\AM_IS\\nodelist.txt",
		"nodelist.txt",
		"C:\\nodelist.txt",
	}

	// Save existing nodelist content before deleting
	var existingNodeList string
	for _, p := range knownPaths {
		if data, err := os.ReadFile(p); err == nil && len(data) > 0 {
			existingNodeList = string(data)
			break
		}
	}

	// Delete old files to detect fresh generation
	for _, p := range knownPaths {
		os.Remove(p)
	}

	// Step 3: Send systemtest node_list using SendSystemCommand
	// SendSystemCommand clears with Ctrl+X + Enter only (no Ctrl+Z which exits system mode)
	// Small delay to let DIA fully enter system mode after connect
	time.Sleep(2 * time.Second)
	_ = s.telnetSM.ClearOutput(sessionID)
	_ = s.telnetSM.SendSystemCommand(sessionID, "systemtest node_list nodelist.txt")
	_ = waitForOutput(s.telnetSM, sessionID, 15*time.Second, 2*time.Second, nil)

	// Step 4: Wait for nodelist.txt to appear (poll for up to 20 seconds)
	// DIA writes the file asynchronously after the command returns
	var nodeListContent string
	searchPaths := []string{
		"C:\\dna\\CA\\dia\\nodelist.txt",
		"C:\\dna\\CA\\AM_IS\\nodelist.txt",
		"C:\\nodelist.txt",
		"nodelist.txt",
		filepath.Join(os.TempDir(), "nodelist.txt"),
	}

	deadline := time.Now().Add(20 * time.Second)
	for time.Now().Before(deadline) {
		for _, p := range searchPaths {
			if data, err := os.ReadFile(p); err == nil && len(data) > 0 {
				nodeListContent = string(data)
				break
			}
		}
		if nodeListContent != "" {
			break
		}
		time.Sleep(500 * time.Millisecond)
	}

	// If systemtest node_list didn't generate a new file, use the existing
	// nodelist.txt content (saved before deletion). Some DIA versions generate
	// nodelist.txt at startup but don't support the systemtest command.
	if nodeListContent == "" && existingNodeList != "" {
		nodeListContent = existingNodeList
	}

	var configs []types.NodeConfig
	var structureRaw string

	if nodeListContent != "" {
		// ─── Parse nodelist.txt format ───────────────────────────
		// Format: hw_address,token,ip,os,slot:type:name:extra,...
		// Example: 30,1,127.0.0.1,win,1:CPU:AB01:10,2:CPU:AP01:0,...,16:NCU
		configs = parseNodeList(nodeListContent)

		// Also get print structure for the structure_raw field
		_ = s.telnetSM.ClearOutput(sessionID)
		_ = s.telnetSM.SendSystemCommand(sessionID, "print structure")
		structureRaw = waitForOutput(s.telnetSM, sessionID, 10*time.Second, 2*time.Second, nil)
	} else {
		// ─── Fallback: print structure + token probing ────────────
		_ = s.telnetSM.ClearOutput(sessionID)
		_ = s.telnetSM.SendSystemCommand(sessionID, "print structure")
		structureRaw = waitForOutput(s.telnetSM, sessionID, 10*time.Second, 2*time.Second, nil)
		configs = scanFromStructure(s, sessionID, structureRaw)
	}

	writeJSON(w, http.StatusOK, map[string]interface{}{
		"configs":       configs,
		"count":         len(configs),
		"structure_raw": structureRaw,
		"nodelist_raw":  nodeListContent,
		"method":        "systemtest_node_list",
	})
}

// tryLoadSysFromBUDir attempts to load .sys files from the BU directory.
// Returns nil if the directory doesn't exist, has no .sys files, or parsing fails.
// On success, returns the same configs as a manual .sys file import —
// with real IP addresses, FBC/RPC tokens, and full node names.
func tryLoadSysFromBUDir(buDir string) []types.NodeConfig {
	// Check if directory exists
	if _, err := os.Stat(buDir); err != nil {
		return nil
	}

	// Try loading .sys files from the directory
	configs, err := sysloader.LoadSysFiles(buDir)
	if err != nil || len(configs) == 0 {
		// Try bu_VM as fallback (VM-specific directory)
		buVMDir := filepath.Join(filepath.Dir(buDir), "bu_VM")
		configs, err = sysloader.LoadSysFiles(buVMDir)
		if err != nil || len(configs) == 0 {
			return nil
		}
		buDir = buVMDir
	}

	return configs
}

// parseNodeList parses nodelist.txt content into NodeConfig array.
// Format (per LightRAG / AMIS Configuration Manual):
//   hw_address,token,ip,os,slot:type:name,...,slot:type:name,...
//
// Each LINE represents one physical node. CPU/BPU entries are application
// servers (stations); FBC entries are fieldbus cards that belong to the
// preceding CPU station on the same line.
//
// Token calculation: token = hex(hw_addr + slot_number - 1).
//   e.g. hw_addr=0x30, slot 1 → 0x30 → "30"  (LOG)
//        hw_addr=0x30, slot 2 → 0x31 → "31"  (FBC + RPC)
//
// Examples from LightRAG:
//   b030,1,192.168.77.190,ppc,1:CPU:LP01,2:FBC,16:NCU
//   → LP01 with tokens: 30(LOG), 31(FBC), 31(RPC)
//
//   30,1,127.0.0.1,win,1:CPU:AB01:10,2:CPU:AP01:0,3:CPU:A1O1:2,...,16:NCU
//   → AB01(30/LOG), AP01(31/LOG), A1O1(32/LOG), ...
//
// FBC slots without a preceding CPU on the same line get their own config
// named "NODE_<hw_addr>_<slot>" as fallback.
func parseNodeList(content string) []types.NodeConfig {
	lines := strings.Split(strings.TrimSpace(content), "\n")
	var configs []types.NodeConfig

	for _, line := range lines {
		line = strings.TrimSpace(line)
		if line == "" || strings.HasPrefix(line, "#") {
			continue
		}

		parts := strings.Split(line, ",")
		if len(parts) < 5 {
			continue
		}

		hwAddr := strings.TrimSpace(parts[0])
		ip := strings.TrimSpace(parts[2])

		// Track the current station (last CPU entry on this line)
		// so FBC slots can be attached to it.
		var currentStation *types.NodeConfig
		var currentStationIdx int = -1

		// Parse slot entries (parts[4:])
		for _, slotEntry := range parts[4:] {
			fields := strings.Split(strings.TrimSpace(slotEntry), ":")
			if len(fields) < 2 {
				continue
			}
			slotNum := strings.TrimSpace(fields[0])
			slotType := strings.ToUpper(strings.TrimSpace(fields[1]))
			slotName := ""
			if len(fields) >= 3 {
				slotName = strings.TrimSpace(fields[2])
			}

			switch slotType {
			case "CPU", "BPU":
				if slotName == "" {
					continue
				}
				tokenID := computeNodeListToken(hwAddr, slotNum)
				cfg := types.NodeConfig{
					Name:      slotName,
					IPAddress: ip,
					Tokens: []types.Token{{
						TokenID:   tokenID,
						TokenType: types.TokenLOG,
						Protocol:  "telnet",
					}},
				}
				configs = append(configs, cfg)
				currentStation = &configs[len(configs)-1]
				currentStationIdx = len(configs) - 1

			case "FBC":
				// FBC slot — belongs to the preceding CPU station on this line.
				// Gets FBC + RPC tokens with the same token calculation.
				tokenID := computeNodeListToken(hwAddr, slotNum)
				fbcToken := types.Token{
					TokenID:   tokenID,
					TokenType: types.TokenFBC,
					Protocol:  "telnet",
				}
				rpcToken := types.Token{
					TokenID:   tokenID,
					TokenType: types.TokenRPC,
					Protocol:  "telnet",
				}
				if currentStation != nil && currentStationIdx >= 0 {
					// Attach to current station — avoid duplicate tokens
					alreadyExists := false
					for _, t := range configs[currentStationIdx].Tokens {
						if t.TokenType == types.TokenFBC && t.TokenID == tokenID {
							alreadyExists = true
							break
						}
					}
					if !alreadyExists {
						configs[currentStationIdx].Tokens = append(configs[currentStationIdx].Tokens, fbcToken, rpcToken)
					}
				} else {
					// No preceding CPU — create a standalone FBC node
					fallbackName := fmt.Sprintf("NODE_%s_slot%s", hwAddr, slotNum)
					configs = append(configs, types.NodeConfig{
						Name:      fallbackName,
						IPAddress: ip,
						Tokens:    []types.Token{fbcToken, rpcToken},
					})
					currentStation = &configs[len(configs)-1]
					currentStationIdx = len(configs) - 1
				}

			case "NCU":
				// Skip NCU — infrastructure, not a process station
				continue
			}
		}
	}

	return configs
}

// computeNodeListToken computes the LOG token for a nodelist CPU entry.
// Token = hex(hw_addr_value + slot_number - 1).
// e.g. hw_addr=0x30 (48), slot=1 → 48+0=48 → "30"
//      hw_addr=0x30 (48), slot=2 → 48+1=49 → "31"
func computeNodeListToken(hwAddr string, slotNum string) string {
	hwVal, err := strconv.ParseInt(hwAddr, 16, 32)
	if err != nil {
		return hwAddr
	}
	slotVal, err := strconv.ParseInt(slotNum, 10, 32)
	if err != nil {
		return hwAddr
	}
	token := hwVal + slotVal - 1
	return fmt.Sprintf("%x", token)
}

// scanFromStructure is the fallback: parse print structure output and probe tokens
func scanFromStructure(s *Server, sessionID string, structureOutput string) []types.NodeConfig {
	lines := strings.Split(structureOutput, "\n")

	type slotEntry struct {
		token   int
		slotNum int
		slotType string
	}
	var slots []slotEntry

	for _, line := range lines {
		line = strings.TrimSpace(line)
		fields := strings.Fields(line)
		if len(fields) < 3 {
			continue
		}
		// Look for data lines: "1 20 CPU CPU CPU ... NCU"
		// First field = token (hex), second = VME addr (hex), rest = slot types
		tokenNum, err := strconv.ParseInt(fields[0], 16, 32)
		if err != nil {
			continue
		}
		for i := 2; i < len(fields); i++ {
			upperField := strings.ToUpper(fields[i])
			if upperField == "CPU" || upperField == "FBC" || upperField == "NCU" {
				slots = append(slots, slotEntry{
					token:    int(tokenNum),
					slotNum:  i - 1, // slot 1 = first after VME addr
					slotType: upperField,
				})
			}
		}
	}

	// Group by station: CPU starts new station, FBC belongs to current station
	type stationTokens struct {
		name      string
		cpuToken  int
		fbcTokens []int
	}
	var stations []*stationTokens

	for _, sl := range slots {
		if sl.slotType == "NCU" {
			continue
		}
		if sl.slotType == "CPU" {
			stations = append(stations, &stationTokens{
				name:     fmt.Sprintf("NODE_%d", len(stations)+1),
				cpuToken: sl.token,
			})
		} else if sl.slotType == "FBC" && len(stations) > 0 {
			stations[len(stations)-1].fbcTokens = append(stations[len(stations)-1].fbcTokens, sl.token)
		}
	}

	var configs []types.NodeConfig
	for _, st := range stations {
		var tokens []types.Token
		if st.cpuToken > 0 {
			tokens = append(tokens, types.Token{
				TokenID:   fmt.Sprintf("%x", st.cpuToken),
				TokenType: types.TokenLOG,
				Protocol:  "telnet",
			})
		}
		for _, fbcToken := range st.fbcTokens {
			tokens = append(tokens, types.Token{
				TokenID:   fmt.Sprintf("%x", fbcToken),
				TokenType: types.TokenFBC,
				Protocol:  "telnet",
			})
			tokens = append(tokens, types.Token{
				TokenID:   fmt.Sprintf("%x", fbcToken),
				TokenType: types.TokenRPC,
				Protocol:  "telnet",
			})
		}
		if len(tokens) > 0 {
			configs = append(configs, types.NodeConfig{
				Name:   st.name,
				Tokens: tokens,
			})
		}
	}

	return configs
}

// executeLISDiag executes a single LISDIAG command by connecting to the
// LisDiag telnet server on the node's IP at port 4321. Each command opens
// a fresh connection, authenticates, sends the command, captures output,
// writes to .lis log file, and closes. This is safe because LisDiag is
// read-only (doesn't modify shared memory or interfere with PCS).
//
// The command sequence for a full LIS capture is:
//   exe N → irb (channel) → orb (channel)
// The executor receives one command at a time. For "exe N" commands,
// the output is minimal (just sets the channel). For "irb"/"orb" commands,
// the output contains frame data with timestamps.
func (s *Server) executeLISDiag(cmd commandqueue.QueuedCommand) (string, error) {
	// Default port and password
	port := 4321
	password := cmd.LISDiagPwd
	if password == "" {
		password = "password" // fallback default from .sys config
	}

	client := lisdiag.NewClient(cmd.IPAddress, port, password)
	if err := client.Connect(10 * time.Second); err != nil {
		return "", fmt.Errorf("lisdiag connect %s:%d: %w", cmd.IPAddress, port, err)
	}
	defer client.Close()

	// Send the command and capture output
	output, err := client.SendCommand(cmd.Command, 15*time.Second)
	if err != nil {
		return output, err
	}

	// Write output to .lis log file
	lw := logwriter.New(s.resolveLogRoot())
	tokenType := "LIS"
	if err := lw.WriteOutputWithIP(cmd.NodeName, tokenType, cmd.TokenID, output, cmd.IPAddress); err != nil {
		log.Printf("lisdiag: failed to write log for %s/%s: %v", cmd.NodeName, cmd.TokenID, err)
	}

	return output, nil
}
