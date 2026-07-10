package api

import (
	"context"
	"encoding/json"
	"fmt"
	"log"
	"net/http"
	"os"
	"path/filepath"
	"strings"
	"time"

	"github.com/falke-ai-circuit/LOGReport/internal/bstool"
	"github.com/falke-ai-circuit/LOGReport/internal/commandqueue"
	"github.com/falke-ai-circuit/LOGReport/internal/lisdiag"
	"github.com/falke-ai-circuit/LOGReport/internal/logwriter"
	"github.com/falke-ai-circuit/LOGReport/internal/nodesconfig"
	"github.com/falke-ai-circuit/LOGReport/internal/types"
)

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

	// Generate ID if not provided
	if cmd.ID == "" {
		cmd.ID = fmt.Sprintf("%s-%s-%s-%d", cmd.NodeName, cmd.Type, cmd.TokenID, time.Now().UnixNano())
	}

	s.commandQueue.Add(cmd)
	_, total, _ := s.commandQueue.Status()
	writeJSON(w, http.StatusOK, map[string]interface{}{
		"added": true,
		"total": total,
		"id":    cmd.ID,
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
		// Circuit breaker: check before executing each command
		if !s.circuitBreaker.AllowExecution() {
			return "", fmt.Errorf("circuit breaker open")
		}

		// LISDIAG commands go through a separate telnet connection to port 4321,
		// not through the DIA session on port 1234.
		if cmd.Type == commandqueue.CmdLISDiag {
			return s.executeLISDiag(cmd)
		}

		// DiagLis: fetch .dia file from BU via BsTool (technician created it via DiagLis GUI)
		if cmd.Type == commandqueue.CmdDiagLis {
			return s.executeDiagLis(cmd)
		}

		// BsTool commands go through the BsTool client (TCP or subprocess)
		if cmd.Type == commandqueue.CmdBsTool {
			return s.executeBsToolQueued(cmd)
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
		// Map command types to logwriter types
		tokenType := string(cmd.Type)
		switch cmd.Type {
		case commandqueue.CmdLIS, commandqueue.CmdRSU, commandqueue.CmdDiagLis:
			// RSU→RSU directory, LISDiag→LIS directory, DiagLis→DIA directory
			if cmd.Type == commandqueue.CmdRSU {
				tokenType = "RSU"
			} else if cmd.Type == commandqueue.CmdDiagLis {
				tokenType = "DIA"
			} else if cmd.Type == commandqueue.CmdLIS {
				tokenType = "LIS"
			}
		case commandqueue.CmdLISDiag:
			tokenType = "LIS"
		default:
			if tokenType == "" {
				tokenType = "raw"
			}
		}
		if err := lw.WriteOutputWithIP(cmd.NodeName, tokenType, cmd.TokenID, output, cmd.IPAddress); err != nil {
			log.Printf("commandqueue: failed to write log for %s/%s: %v", cmd.NodeName, cmd.TokenID, err)
		}

		// 5. Return the output string
		return output, nil
	}

	// Wrap executor with circuit breaker recording
	cbExecutor := func(cmd commandqueue.QueuedCommand) (string, error) {
		out, err := executor(cmd)
		if err != nil {
			s.circuitBreaker.RecordFailure()
		} else {
			s.circuitBreaker.RecordSuccess()
		}
		return out, err
	}

	go func() {
		if err := s.commandQueue.Start(cbExecutor); err != nil {
			log.Printf("commandqueue: start error: %v", err)
		}
		// Close cached LisDiag connections after queue completes
		s.CloseLISDiagConns()
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
		// Circuit breaker: check before executing each command
		if !s.circuitBreaker.AllowExecution() {
			return "", fmt.Errorf("circuit breaker open")
		}

		// LISDIAG commands go through a separate telnet connection to port 4321,
		// not through the DIA session on port 1234.
		if cmd.Type == commandqueue.CmdLISDiag {
			return s.executeLISDiag(cmd)
		}

		// DiagLis: fetch .dia file from BU via BsTool (technician created it via DiagLis GUI)
		if cmd.Type == commandqueue.CmdDiagLis {
			return s.executeDiagLis(cmd)
		}

		// BsTool commands go through the BsTool client (TCP or subprocess)
		if cmd.Type == commandqueue.CmdBsTool {
			return s.executeBsToolQueued(cmd)
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
		// Map command types to logwriter types
		tokenType := string(cmd.Type)
		switch cmd.Type {
		case commandqueue.CmdLIS, commandqueue.CmdRSU, commandqueue.CmdDiagLis:
			// RSU→RSU directory, LISDiag→LIS directory, DiagLis→DIA directory
			if cmd.Type == commandqueue.CmdRSU {
				tokenType = "RSU"
			} else if cmd.Type == commandqueue.CmdDiagLis {
				tokenType = "DIA"
			} else if cmd.Type == commandqueue.CmdLIS {
				tokenType = "LIS"
			}
		case commandqueue.CmdLISDiag:
			tokenType = "LIS"
		default:
			if tokenType == "" {
				tokenType = "raw"
			}
		}
		if err := lw.WriteOutputWithIP(cmd.NodeName, tokenType, cmd.TokenID, output, cmd.IPAddress); err != nil {
			log.Printf("commandqueue: failed to write log for %s/%s: %v", cmd.NodeName, cmd.TokenID, err)
		}

		return output, nil
	}

	// Wrap executor with circuit breaker recording
	cbExecutor := func(cmd commandqueue.QueuedCommand) (string, error) {
		out, err := executor(cmd)
		if err != nil {
			s.circuitBreaker.RecordFailure()
		} else {
			s.circuitBreaker.RecordSuccess()
		}
		return out, err
	}

	go func() {
		if err := s.commandQueue.Start(cbExecutor); err != nil {
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

// handleQueueRemove removes a pending command from the queue by ID.
// POST /api/v1/commandqueue/remove
// Body: {"id": "..."}
func (s *Server) handleQueueRemove(w http.ResponseWriter, r *http.Request) {
	var req struct {
		ID string `json:"id"`
	}
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		writeError(w, http.StatusBadRequest, "validation_error", "invalid JSON body")
		return
	}
	if req.ID == "" {
		writeError(w, http.StatusBadRequest, "validation_error", "id is required")
		return
	}
	removed := s.commandQueue.Remove(req.ID)
	writeJSON(w, http.StatusOK, map[string]interface{}{
		"removed": removed,
	})
}

// handleQueueReorder moves a pending command from one position to another.
// POST /api/v1/commandqueue/reorder
// Body: {"from": N, "to": M}
func (s *Server) handleQueueReorder(w http.ResponseWriter, r *http.Request) {
	var req struct {
		From int `json:"from"`
		To   int `json:"to"`
	}
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		writeError(w, http.StatusBadRequest, "validation_error", "invalid JSON body")
		return
	}
	moved := s.commandQueue.Reorder(req.From, req.To)
	writeJSON(w, http.StatusOK, map[string]interface{}{
		"moved": moved,
	})
}

// handleQueueClear removes all pending commands, keeping completed/failed/cancelled history.
// POST /api/v1/commandqueue/clear
func (s *Server) handleQueueClear(w http.ResponseWriter, r *http.Request) {
	s.commandQueue.ClearPending()
	writeJSON(w, http.StatusOK, map[string]interface{}{
		"cleared": true,
	})
}

// handleQueueRestart resets all commands back to pending, allowing re-execution.
// POST /api/v1/commandqueue/restart
func (s *Server) handleQueueRestart(w http.ResponseWriter, r *http.Request) {
	s.commandQueue.Restart()
	writeJSON(w, http.StatusOK, map[string]interface{}{
		"restarted": true,
	})
}

// handleLogSave writes content to a file at the given path.
// POST /api/v1/logs/save
// Body: {"path": "...", "content": "..."}
func (s *Server) handleLogSave(w http.ResponseWriter, r *http.Request) {
	var req struct {
		Path    string `json:"path"`
		Content string `json:"content"`
	}
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		writeError(w, http.StatusBadRequest, "validation_error", "invalid JSON body")
		return
	}
	if req.Path == "" {
		writeError(w, http.StatusBadRequest, "validation_error", "path is required")
		return
	}

	// Ensure parent directory exists
	dir := filepath.Dir(req.Path)
	if err := os.MkdirAll(dir, 0755); err != nil {
		writeError(w, http.StatusInternalServerError, "internal_error",
			fmt.Sprintf("failed to create directory: %v", err))
		return
	}

	if err := os.WriteFile(req.Path, []byte(req.Content), 0644); err != nil {
		writeError(w, http.StatusInternalServerError, "internal_error",
			fmt.Sprintf("failed to write file: %v", err))
		return
	}

	writeJSON(w, http.StatusOK, map[string]interface{}{
		"saved": true,
		"path":  req.Path,
	})
}

// executeBsToolQueued runs a BsTool errlog command through the queue.
// On error, writes an empty file so the tree shows it as red (command ran, no data).
// On success, writes output to .log files via logwriter.
func (s *Server) executeBsToolQueued(cmd commandqueue.QueuedCommand) (string, error) {
	result, err := s.bstoolClient.ErrLog(context.Background(), cmd.NodeName)
	if err != nil {
		// Write empty file so tree shows it as red (command ran, no data)
		ipAddress := cmd.IPAddress
		if ipAddress == "" {
			if configs, cfgErr := nodesconfig.LoadFromFile(s.nodesConfigPath()); cfgErr == nil {
				for _, c := range configs {
					if c.Name == cmd.NodeName || extractStationNameFromConfig(c.Name) == cmd.NodeName {
						ipAddress = c.IPAddress
						break
					}
				}
			}
		}
		lr := s.resolveLogRoot()
		os.MkdirAll(lr, 0755)
		lw := logwriter.New(lr)
		lw.WriteOutputWithIP(cmd.NodeName, "LOG", "", "", ipAddress)
		return "", fmt.Errorf("bstool error: %w", err)
	}

	// Build output from result messages
	var sb strings.Builder
	if result != nil && len(result.Messages) > 0 {
		for _, m := range result.Messages {
			sb.WriteString(m)
			sb.WriteString("\n")
		}
	}
	output := sb.String()

	// Write output to .log file
	ipAddress := cmd.IPAddress
	if ipAddress == "" {
		if configs, cfgErr := nodesconfig.LoadFromFile(s.nodesConfigPath()); cfgErr == nil {
			for _, c := range configs {
				if c.Name == cmd.NodeName || extractStationNameFromConfig(c.Name) == cmd.NodeName {
					ipAddress = c.IPAddress
					break
				}
			}
		}
	}
	lr := s.resolveLogRoot()
	os.MkdirAll(lr, 0755)
	lw := logwriter.New(lr)
	if err := lw.WriteOutputWithIP(cmd.NodeName, "LOG", "", output, ipAddress); err != nil {
		log.Printf("commandqueue/bstool: failed to write log for %s: %v", cmd.NodeName, err)
	}

	return output, nil
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
	s.commandQueue.AddBatchFromNodes(req.Configs, req.SessionID, s.telnetSM, getSettings().LISMode, getSettings().LISExeCount)
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
	// Match by exact name first, then by station name (e.g. "AP01m" matches "AP01_main", "AP01_m2")
	var filtered []types.NodeConfig
	for _, c := range configs {
		if c.Name == req.NodeName || matchStationName(c.Name, req.NodeName) {
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
		}
	}

	if len(filtered) == 0 {
		writeError(w, http.StatusNotFound, "not_found",
			fmt.Sprintf("node %s not found in nodes.json", req.NodeName))
		return
	}

	s.commandQueue.Reset()
	lisMode := getSettings().LISMode
	lisdiagPwd := getSettings().LISDiagPassword
	if strings.EqualFold(req.TokenType, "LISDiag") {
		// Explicit LISDiag request — always use LISDiag path
		s.commandQueue.AddBatchFromNodesLISDiag(filtered, lisdiagPwd, getSettings().LISExeCount)
	} else if strings.EqualFold(req.TokenType, "LIS") && lisMode == "lisdiag" {
		// LIS mode is set to lisdiag in settings — route LIS tokens through LISDiag
		s.commandQueue.AddBatchFromNodesLISDiag(filtered, lisdiagPwd, getSettings().LISExeCount)
	} else if strings.EqualFold(req.TokenType, "LIS") && lisMode == "diaglis" {
		// DiagLIS mode — manual capture, generate placeholder commands via AddBatchFromNodes
		s.commandQueue.AddBatchFromNodes(filtered, "", s.telnetSM, lisMode, getSettings().LISExeCount)
	} else {
		s.commandQueue.AddBatchFromNodes(filtered, "", s.telnetSM, lisMode, getSettings().LISExeCount)
	}
	_, total, _ := s.commandQueue.Status()

	writeJSON(w, http.StatusOK, map[string]interface{}{
		"batch_added": true,
		"node_name":   req.NodeName,
		"token_type":  req.TokenType,
		"total":       total,
	})
}

// executeDiagLis fetches a .dia file from the BU via BsTool file transport.
// The technician runs DiagLis GUI on the BU, which generates .dia files in the
// BU directory. This method searches for a matching file by station name and
// exe number, reads its content, and writes it to the local _LOG DIA directory.
// If no file is found in BU, it writes an empty file (technician may not have
// created it yet) but does NOT fail — the queue continues.
func (s *Server) executeDiagLis(cmd commandqueue.QueuedCommand) (string, error) {
	st := getSettings()
	bstoolHost := st.BsToolHost
	if bstoolHost == "" {
		bstoolHost = "127.0.0.1"
	}
	bstoolPort := st.BsToolPort
	if bstoolPort == 0 {
		bstoolPort = 1516
	}

	// Parse exe number from token ID (format: "181_exe1")
	exeNum := 0
	if idx := strings.Index(cmd.TokenID, "_exe"); idx >= 0 {
		fmt.Sscanf(cmd.TokenID[idx+4:], "%d", &exeNum)
	}

	// Build station name for search — strip _Remote_monitor suffix if present
	stationName := cmd.NodeName
	if idx := strings.Index(stationName, "_"); idx > 0 {
		stationName = stationName[:idx]
	}
	_ = stationName // kept for potential future filtering

	// Search for matching .dia files in BU using BsTool.
	// The technician creates files named like: AL01_192-168-0-11_181_exe1.dia
	// The tokenID (e.g. "181_exe1") uniquely identifies the file.
	// BsTool READ_DIR may not support complex wildcard patterns like *181_exe1*.dia,
	// so we list ALL .dia files and filter in Go for an exact match.
	ft := bstool.NewFileTransport(bstoolHost, bstoolPort, 15*time.Second)
	defer ft.Close()

	commLine := "s"
	entries, err := ft.ListDir(commLine, "*.dia")

	var fileContent []byte
	if err != nil {
		log.Printf("diaglis: BsTool ListDir failed (host=%s:%d pattern=*.dia): %v", bstoolHost, bstoolPort, err)
	} else {
		// Filter entries: find the one whose name contains the tokenID
		// tokenID is like "181_exe1" — the filename should be AL02_192-168-1-12_181_exe1.dia
		var matchedEntry *bstool.DirEntry
		for i := range entries {
			if strings.Contains(entries[i].Name, cmd.TokenID) {
				matchedEntry = &entries[i]
				break
			}
		}
		if matchedEntry == nil {
			log.Printf("diaglis: no .dia file matching tokenID=%s in %d BU entries (node=%s exe=%d)",
				cmd.TokenID, len(entries), cmd.NodeName, exeNum)
		} else {
			fileContent, err = ft.ReadFile(commLine, matchedEntry.Name)
			if err != nil {
				log.Printf("diaglis: failed to read %s from BU: %v", matchedEntry.Name, err)
			} else {
				log.Printf("diaglis: fetched %s from BU (%d bytes)", matchedEntry.Name, len(fileContent))
			}
		}
	}

	// Write content (or empty if not found) to local log directory
	lw := logwriter.New(s.resolveLogRoot())
	tokenType := "DIA"
	content := ""
	if fileContent != nil {
		content = string(fileContent)
	}
	if err := lw.WriteOutputWithIP(cmd.NodeName, tokenType, cmd.TokenID, content, cmd.IPAddress); err != nil {
		log.Printf("commandqueue: failed to write log for %s/%s: %v", cmd.NodeName, cmd.TokenID, err)
	}
	return content, nil
}

// executeLISDiag executes a LISDiag command by connecting to the LisDiag
// telnet server. The connection target is cmd.IPAddress (the AL station IP)
// — a port proxy on the VM redirects AL_station_IP:4321 to localhost:4321
// where LisDiag.exe listens.
//
// For "exe N" commands (batch mode), the executor automatically follows with
// "io N-1" and writes ONLY the io output (frame data) to the .lis file.
// For standalone commands (from the LisDiag tab), it sends the command as-is.
func (s *Server) executeLISDiag(cmd commandqueue.QueuedCommand) (string, error) {
	st := getSettings()
	// Connect to the AL station's IP on port 4321 — port proxy redirects
	// to localhost where LisDiag.exe runs.
	host := cmd.IPAddress
	if host == "" {
		host = "127.0.0.1"
	}

	// Default port and password
	port := 4321
	password := cmd.LISDiagPwd
	if password == "" {
		password = st.LISDiagPassword
	}
	// If still empty, no auth needed (LisDiag started without -x flag)

	// Reuse cached LisDiag connection if available (same host+port+password)
	connKey := fmt.Sprintf("%s:%d:%s", host, port, password)
	s.lisdiagMu.Lock()
	cached := s.lisdiagConns[connKey]
	s.lisdiagMu.Unlock()

	if cached == nil {
		cached = lisdiag.NewClient(host, port, password)
		if err := cached.Connect(10 * time.Second); err != nil {
			return "", fmt.Errorf("lisdiag connect %s:%d: %w", host, port, err)
		}
		s.lisdiagMu.Lock()
		s.lisdiagConns[connKey] = cached
		s.lisdiagMu.Unlock()
		log.Printf("lisdiag: connected to %s:%d (cached)", host, port)
	}

	// Combined exe+io mode: if command starts with "exe ", send exe N then
	// io N-1, write ONLY the io output to the .lis file.
	if strings.HasPrefix(cmd.Command, "exe ") {
		var exeNum int
		fmt.Sscanf(cmd.Command, "exe %d", &exeNum)
		channel := exeNum - 1

		// Send "exe N" — sets the channel, minimal output
		_, _ = cached.SendCommand(cmd.Command, 10*time.Second)

		// Send "io N-1" — produces the actual frame data
		ioCmd := lisdiag.IOCommand(channel)
		output, err := cached.SendCommand(ioCmd, 15*time.Second)
		if err != nil {
			// Connection might be stale — close cache and retry once
			s.lisdiagMu.Lock()
			delete(s.lisdiagConns, connKey)
			s.lisdiagMu.Unlock()
			cached.Close()

			cached = lisdiag.NewClient(host, port, password)
			if err2 := cached.Connect(10 * time.Second); err2 != nil {
				return output, fmt.Errorf("lisdiag connect %s:%d (retry): %w", host, port, err2)
			}
			s.lisdiagMu.Lock()
			s.lisdiagConns[connKey] = cached
			s.lisdiagMu.Unlock()
			// Re-send exe then io on the fresh connection
			_, _ = cached.SendCommand(cmd.Command, 10*time.Second)
			output, err = cached.SendCommand(ioCmd, 15*time.Second)
			if err != nil {
				return output, err
			}
		}

		// Write ONLY the io output to .lis log file
		lw := logwriter.New(s.resolveLogRoot())
		if err := lw.WriteOutputWithIP(cmd.NodeName, "LIS", cmd.TokenID, output, cmd.IPAddress); err != nil {
			log.Printf("lisdiag: failed to write log for %s/%s: %v", cmd.NodeName, cmd.TokenID, err)
		}
		return output, nil
	}

	// Standalone command (from LisDiag tab) — send and write as before
	output, err := cached.SendCommand(cmd.Command, 15*time.Second)
	if err != nil {
		// Connection might be stale — close cache and retry once
		s.lisdiagMu.Lock()
		delete(s.lisdiagConns, connKey)
		s.lisdiagMu.Unlock()
		cached.Close()

		cached = lisdiag.NewClient(host, port, password)
		if err2 := cached.Connect(10 * time.Second); err2 != nil {
			return output, fmt.Errorf("lisdiag connect %s:%d (retry): %w", host, port, err2)
		}
		s.lisdiagMu.Lock()
		s.lisdiagConns[connKey] = cached
		s.lisdiagMu.Unlock()
		output, err = cached.SendCommand(cmd.Command, 15*time.Second)
		if err != nil {
			return output, err
		}
	}

	// Write output to .lis log file
	lw := logwriter.New(s.resolveLogRoot())
	if err := lw.WriteOutputWithIP(cmd.NodeName, "LIS", cmd.TokenID, output, cmd.IPAddress); err != nil {
		log.Printf("lisdiag: failed to write log for %s/%s: %v", cmd.NodeName, cmd.TokenID, err)
	}

	return output, nil
}

// CloseLISDiagConns closes all cached LisDiag connections (called after queue completes).
func (s *Server) CloseLISDiagConns() {
	s.lisdiagMu.Lock()
	defer s.lisdiagMu.Unlock()
	for key, conn := range s.lisdiagConns {
		conn.Close()
		delete(s.lisdiagConns, key)
	}
}
