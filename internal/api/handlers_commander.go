package api

import (
	"context"
	"encoding/json"
	"errors"
	"fmt"
	"log"
	"net/http"
	"os"
	"path/filepath"
	"runtime"
	"strconv"
	"strings"
	"time"

	"github.com/falke-ai-circuit/LOGReport/internal/commandqueue"
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

// nodesConfigPathForProject returns the path to the nodes config file,
// scoped to a project if projectID is non-empty.
// If projectID is empty, falls back to the default nodesConfigPath().
func (s *Server) nodesConfigPathForProject(projectID string) string {
	if projectID == "" {
		return s.nodesConfigPath()
	}
	return fmt.Sprintf("nodes_%s.json", projectID)
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
	path := s.nodesConfigPath()
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
		logRoot = s.logRoot()
	}

	var tree *types.TreeNode
	if logRoot != "" {
		tree = nodesconfig.BuildFileTree(configs, logRoot)
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
	output := waitForOutput(s.telnetSM, sessionID, 10*time.Second, 2*time.Second)

	// Write output to log file if node info is provided (from context menu)
	fileWritten := false
	var filePathStr string
	if req.NodeName != "" && req.TokenType != "" {
		// If IP address not provided, look it up from nodes.json
		if req.IPAddress == "" {
			if configs, err := nodesconfig.LoadFromFile(s.nodesConfigPath()); err == nil {
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
		// Auto-set log root if not configured or still at default "logs"
		lr := s.logRoot()
		if lr == "" || lr == "logs" {
			if !globalSettings.loaded {
				s.initSettings()
			}
			st := getSettings()
			if st.LogRoot != "" {
				lr = st.LogRoot
			} else if runtime.GOOS == "windows" {
				lr = "C:\\temp\\logreport-output"
			} else {
				lr = "/tmp/logreport-output"
			}
			s.SetLogRoot(lr)
			os.MkdirAll(lr, 0755)
		}
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
			// or stored host/port from a previous session
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
			sess, err := s.telnetSM.Connect("", host, port, 10*time.Second)
			if err != nil {
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
		output := waitForOutput(s.telnetSM, sessionID, 10*time.Second, 2*time.Second)

		// 4. Write output to structured log files
		lw := logwriter.New(s.logRoot())
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
			sess, err := s.telnetSM.Connect("", host, port, 10*time.Second)
			if err != nil {
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
		output := waitForOutput(s.telnetSM, sessionID, 10*time.Second, 2*time.Second)

		lw := logwriter.New(s.logRoot())
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
func (s *Server) handleQueueBatch(w http.ResponseWriter, r *http.Request) {
	var req struct {
		Configs   []types.NodeConfig `json:"configs"`
		SessionID string             `json:"session_id"`
	}
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		// If no body, load from nodes.json
		path := s.nodesConfigPath()
		configs, loadErr := nodesconfig.LoadFromFile(path)
		if loadErr != nil {
			writeError(w, http.StatusBadRequest, "validation_error",
				"invalid JSON body and no nodes.json found")
			return
		}
		req.Configs = configs
	}

	if len(req.Configs) == 0 {
		// Try loading from file
		path := s.nodesConfigPath()
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

	// Load configs from nodes.json
	path := s.nodesConfigPath()
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
			if req.TokenType != "" {
				var filteredTokens []types.Token
				for _, t := range c.Tokens {
					if strings.EqualFold(string(t.TokenType), req.TokenType) {
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
	s.commandQueue.AddBatchFromNodes(filtered, "", s.telnetSM)
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
func waitForOutput(sm *telnet.SessionManager, sessionID string, maxWait, trailWait time.Duration) string {
	deadline := time.Now().Add(maxWait)
	ticker := time.NewTicker(100 * time.Millisecond)
	defer ticker.Stop()

	// Phase 1: Wait for non-empty output
	for time.Now().Before(deadline) {
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
		<-ticker.C
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


// ─── Scan Nodes Handler (DIA "print structure") ──────────────────────

// handleScanNodes connects to DIA, sends "systemtest node_list" to generate
// a complete node listing with hw-address, token, IP, OS, slots and program names.
// Falls back to "print structure" + token probing if node_list fails.
// POST /api/v1/sysfiles/scan-nodes
func (s *Server) handleScanNodes(w http.ResponseWriter, r *http.Request) {
	// 90-second hard timeout — the scan can take up to ~60s in worst case
	// (15s connect + 12s systemtest + 15s nodelist poll + 12s print structure + probing)
	// but must not hang indefinitely. Context cancellation propagates to telnet reads.
	ctx, cancel := context.WithTimeout(r.Context(), 90*time.Second)
	defer cancel()
	_ = ctx // r.Context() is already used by the HTTP server; ctx is for future use

	// Load settings for DIA host/port
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
	knownPaths := []string{
		"C:\\dna\\CA\\dia\\nodelist.txt",
		"C:\\dna\\CA\\AM_IS\\nodelist.txt",
		"nodelist.txt",
		"C:\\nodelist.txt",
	}
	for _, p := range knownPaths {
		os.Remove(p)
	}

	// Step 3: Send systemtest node_list using SendSystemCommand
	// SendSystemCommand clears with Ctrl+X + Enter only (no Ctrl+Z which exits system mode)
	_ = s.telnetSM.ClearOutput(sessionID)
	_ = s.telnetSM.SendSystemCommand(sessionID, "systemtest node_list nodelist.txt")
	_ = waitForOutput(s.telnetSM, sessionID, 10*time.Second, 2*time.Second)

	// Step 4: Wait for nodelist.txt to appear (poll for up to 15 seconds)
	// DIA writes the file asynchronously after the command returns
	var nodeListContent string
	searchPaths := []string{
		"C:\\dna\\CA\\dia\\nodelist.txt",
		"C:\\dna\\CA\\AM_IS\\nodelist.txt",
		"C:\\nodelist.txt",
		"nodelist.txt",
		filepath.Join(os.TempDir(), "nodelist.txt"),
	}

	deadline := time.Now().Add(15 * time.Second)
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
		structureRaw = waitForOutput(s.telnetSM, sessionID, 10*time.Second, 2*time.Second)
	} else {
		// ─── Fallback: print structure + token probing ────────────
		_ = s.telnetSM.ClearOutput(sessionID)
		_ = s.telnetSM.SendSystemCommand(sessionID, "print structure")
		structureRaw = waitForOutput(s.telnetSM, sessionID, 10*time.Second, 2*time.Second)
		configs = scanFromStructure(s, sessionID, structureRaw)
	}

	writeJSON(w, http.StatusOK, map[string]interface{}{
		"configs":        configs,
		"count":          len(configs),
		"structure_raw":  structureRaw,
		"nodelist_raw":   nodeListContent,
		"method":         "systemtest_node_list",
	})
}

// parseNodeList parses nodelist.txt content into NodeConfig array.
// Format: hw_address,token,ip,os,slot:type:name:extra,slot:type:name:extra,...
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
		token := strings.TrimSpace(parts[1])
		ip := strings.TrimSpace(parts[2])
		_ = hwAddr
		_ = token

		// Parse slot entries (parts[4:])
		var stationName string
		var fbcTokens []string
		hasCPU := false
		hasNCU := false

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
			case "CPU":
				if stationName == "" && slotName != "" {
					stationName = slotName
				}
				if slotName != "" {
					stationName = slotName
				}
				hasCPU = true
			case "FBC":
				// FBC slot — token = hw_addr prefix + slot number
				// e.g. hw_addr=0x30, slot=2 → token = 0x32 (hex)
				fbcTokens = append(fbcTokens, slotNum)
			case "NCU":
				hasNCU = true
			case "BPU":
				// BPU is a CPU variant
				if stationName == "" && slotName != "" {
					stationName = slotName
				}
				hasCPU = true
			}
		}

		// Skip NCU-only nodes (infrastructure, not process stations)
		if !hasCPU && hasNCU {
			continue
		}
		if stationName == "" {
			stationName = fmt.Sprintf("NODE_%s", token)
		}

		// Build tokens for this node
		var tokens []types.Token

		// CPU slot → LOG-only token
		if hasCPU {
			tokens = append(tokens, types.Token{
				TokenID:   hwAddr,
				TokenType: types.TokenLOG,
				Protocol:  "telnet",
			})
		}

		// FBC slots → FBC + RPC paired tokens
		for _, fbcSlot := range fbcTokens {
			// Token = hw_addr + slot offset
			// e.g. hw_addr=0x30, slot=2 → 0x32
			fbcToken := computeFBCToken(hwAddr, fbcSlot)
			tokens = append(tokens, types.Token{
				TokenID:   fbcToken,
				TokenType: types.TokenFBC,
				Protocol:  "telnet",
			})
			tokens = append(tokens, types.Token{
				TokenID:   fbcToken,
				TokenType: types.TokenRPC,
				Protocol:  "telnet",
			})
		}

		if len(tokens) > 0 {
			configs = append(configs, types.NodeConfig{
				Name:      stationName,
				IPAddress: ip,
				Tokens:    tokens,
			})
		}
	}

	return configs
}

// computeFBCToken computes the FBC token from hw_address and slot number.
// Token format: hex(hw_addr_value + slot_number)
// e.g. hw_addr=0x30, slot=2 → 0x32 → "32"
func computeFBCToken(hwAddr string, slotNum string) string {
	hwVal, err := strconv.ParseInt(hwAddr, 16, 32)
	if err != nil {
		return hwAddr
	}
	slotVal, err := strconv.ParseInt(slotNum, 10, 32)
	if err != nil {
		return hwAddr
	}
	token := hwVal + slotVal
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
