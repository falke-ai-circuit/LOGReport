package api

import (
	"encoding/json"
	"fmt"
	"log"
	"net/http"
	"os"
	"path/filepath"
	"strings"
	"time"

	"github.com/falke-ai-circuit/LOGReport/internal/logwriter"
	"github.com/falke-ai-circuit/LOGReport/internal/nodesconfig"
	"github.com/falke-ai-circuit/LOGReport/internal/telnet"
)

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
