package api

import (
	"encoding/json"
	"fmt"
	"net/http"
	"os"
	"path/filepath"
	"runtime"
	"sync"

	"github.com/falke-ai-circuit/LOGReport/internal/bstool"
)

// Settings holds runtime-configurable settings persisted to settings.json.
// These are separate from command-line flags (Config) — settings can be
// changed at runtime via the Settings UI without restarting the server.
type Settings struct {
	DIAHost           string `json:"dia_host"`
	DIAPort           int    `json:"dia_port"`
	BsToolHost        string `json:"bstool_host"`
	BsToolPort        int    `json:"bstool_port"`
	LogRoot           string `json:"log_root"`
	LogRootName       string `json:"logroot_name"`
	BsToolPath        string `json:"bstool_path"`
	CommunicationLine string `json:"communication_line"`
	OutputDir         string `json:"output_dir"`
	BUDir             string `json:"bu_dir"`  // path to .sys files directory (default: C:\dna\CA\bu)
	LISMode           string `json:"lis_mode"`    // LIS capture method: "rsu" (RSU6 via DIA), "lisdiag" (telnet port 4321), "diaglis" (manual)
	ScanMethod        string `json:"scan_method"` // Node scan method: "remote_bu" (BsTool TCP, default), "local_dir" (local .sys files)
	NodeFilter        string `json:"node_filter"` // Comma-separated station prefixes to include/exclude (e.g. "AP,AL" or "AP,AL,-A1O,-B1O")
	LISExeCount       int    `json:"lis_exe_count"` // number of exe channels (default: 6)
	LISDiagPassword   string `json:"lisdiag_password"` // password for LisDiag telnet auth (empty = no password)
}

// defaultSettings returns platform-appropriate defaults.
func defaultSettings() Settings {
	buDir := "C:\\dna\\CA\\bu"
	if runtime.GOOS != "windows" {
		buDir = "/dna/CA/bu"
	}
	return Settings{
		DIAHost:     "127.0.0.1",
		DIAPort:     1234,
		BsToolHost:  "127.0.0.1",
		BsToolPort:  1516,
		LogRoot:     "",
		LogRootName: "",
		OutputDir:   "",
		BUDir:       buDir,
		LISMode:     "rsu",       // default: RSU6 via DIA (requires RSU6 hardware)
		ScanMethod:  "remote_bu", // default: BsTool TCP remote BU
		LISExeCount: 6,
		LISDiagPassword: "", // empty = no auth
	}
}

// settingsStore is a thread-safe settings persister.
type settingsStore struct {
	mu       sync.Mutex
	path     string
	settings Settings
	loaded   bool
}

var globalSettings settingsStore

// initSettings loads settings from settings.json in the data directory,
// or creates it with defaults if it doesn't exist.
func (s *Server) initSettings() {
	globalSettings.mu.Lock()
	defer globalSettings.mu.Unlock()

	dir := "logreport-data"
	if s.config != nil && s.config.DBPath != "" {
		dir = s.config.DBPath
	}
	globalSettings.path = filepath.Join(dir, "settings.json")

	data, err := os.ReadFile(globalSettings.path)
	if err != nil {
		// File doesn't exist — use defaults and write them
		globalSettings.settings = defaultSettings()
		globalSettings.loaded = true
		// Try to write defaults (best-effort)
		os.MkdirAll(dir, 0755)
		w, _ := json.MarshalIndent(globalSettings.settings, "", "  ")
		os.WriteFile(globalSettings.path, w, 0644)
		return
	}

	var st Settings
	if err := json.Unmarshal(data, &st); err != nil {
		globalSettings.settings = defaultSettings()
		globalSettings.loaded = true
		return
	}

	// Fill in any zero-value fields with defaults
	def := defaultSettings()
	if st.DIAHost == "" {
		st.DIAHost = def.DIAHost
	}
	if st.DIAPort == 0 {
		st.DIAPort = def.DIAPort
	}
	if st.BsToolHost == "" {
		st.BsToolHost = def.BsToolHost
	}
	if st.BsToolPort == 0 {
		st.BsToolPort = def.BsToolPort
	}
	if st.LogRootName == "" {
		st.LogRootName = def.LogRootName
	}
	if st.BsToolPath == "" {
		// Auto-detect BsTool.exe in current directory (logreport root)
		if _, err := os.Stat("BsTool.exe"); err == nil {
			abs, _ := filepath.Abs("BsTool.exe")
			st.BsToolPath = abs
		} else {
			st.BsToolPath = def.BsToolPath
		}
	}
	if st.CommunicationLine == "" {
		st.CommunicationLine = def.CommunicationLine
	}
	if st.BUDir == "" {
		st.BUDir = def.BUDir
	}
	if st.LISMode == "" {
		st.LISMode = def.LISMode
	}
	if st.LISExeCount == 0 {
		st.LISExeCount = def.LISExeCount
	}
	if st.ScanMethod == "" {
		// If BsTool.exe detected locally, prefer local_exe
		if st.BsToolPath != "" && st.BsToolPath != def.BsToolPath {
			st.ScanMethod = "local_exe"
		} else {
			st.ScanMethod = def.ScanMethod
		}
	}

	globalSettings.settings = st
	globalSettings.loaded = true

	// Apply log_root to server if set
	if st.LogRoot != "" {
		s.logRootDir = st.LogRoot
	}
}

// getSettings returns the current settings (thread-safe).
func getSettings() Settings {
	globalSettings.mu.Lock()
	defer globalSettings.mu.Unlock()
	return globalSettings.settings
}

// resolveBsToolPath returns the BsTool.exe path from settings, auto-detecting
// from the logreport root directory if bstool_path is "./BsTool.exe" or empty.
// On Windows, checks: logreport root (.), ./BsTool.exe, ./bstool/BsTool.exe.
func resolveBsToolPath(st Settings) string {
	path := st.BsToolPath
	if path == "" {
		return ""
	}
	// If relative path like "./BsTool.exe", resolve against cwd
	if path == "./BsTool.exe" || path == "BsTool.exe" {
		if _, err := os.Stat(path); err == nil {
			abs, _ := filepath.Abs(path)
			return abs
		}
		return ""
	}
	if _, err := os.Stat(path); err == nil {
		return path
	}
	return ""
}

// newBsToolClientFromSettings creates a bstool.Client configured from settings.
// If scan_method is "local_exe" or bstool_path is set and exists, creates a
// subprocess client with the path and communication line.
// Otherwise, creates a TCP client using bstool_host/bstool_port.
func newBsToolClientFromSettings(st Settings) *bstool.Client {
	exePath := resolveBsToolPath(st)
	if exePath != "" {
		// Use subprocess mode (BsTool.exe)
		return bstool.NewClient(
			bstool.WithPath(exePath),
			bstool.WithCommunicationLine(st.CommunicationLine),
		)
	}
	// Use TCP mode
	if st.BsToolHost != "" {
		tcpOpts := []bstool.TCPTransportOption{
			bstool.WithTCPHost(st.BsToolHost),
		}
		if st.BsToolPort > 0 {
			tcpOpts = append(tcpOpts, bstool.WithTCPPort(st.BsToolPort))
		}
		tcp := bstool.NewTCPTransport(tcpOpts...)
		return bstool.NewClient(bstool.WithTCPTransport(tcp))
	}
	return bstool.NewClient()
}

// isLocalExeMode returns true if settings indicate BsTool.exe subprocess should be used.
func isLocalExeMode(st Settings) bool {
	return st.ScanMethod == "local_exe" || resolveBsToolPath(st) != ""
}

// saveSettings persists settings to disk and applies runtime changes.
func saveSettings(st Settings) error {
	globalSettings.mu.Lock()
	defer globalSettings.mu.Unlock()

	globalSettings.settings = st

	// Write to file
	w, err := json.MarshalIndent(st, "", "  ")
	if err != nil {
		return fmt.Errorf("settings: marshal: %w", err)
	}
	if err := os.WriteFile(globalSettings.path, w, 0644); err != nil {
		return fmt.Errorf("settings: write %s: %w", globalSettings.path, err)
	}
	return nil
}

// handleGetSettings returns the current settings.
// GET /api/v1/settings?project_id={id}
// If project_id is provided, returns project-specific settings merged over
// global defaults. Otherwise returns global settings.
func (s *Server) handleGetSettings(w http.ResponseWriter, r *http.Request) {
	if !globalSettings.loaded {
		s.initSettings()
	}
	projectIDStr := r.URL.Query().Get("project_id")
	if projectIDStr != "" {
		// Load project-specific settings
		var projectID int64
		fmt.Sscanf(projectIDStr, "%d", &projectID)
		project, err := s.store.GetProject(projectID)
		if err != nil {
			writeError(w, http.StatusNotFound, "not_found", "project not found")
			return
		}
		// Start with global settings as base, override with project settings
		st := getSettings()
		if project.SettingsJSON != "" {
			var projSettings Settings
			if err := json.Unmarshal([]byte(project.SettingsJSON), &projSettings); err == nil {
				st = mergeSettings(st, projSettings)
			}
		}
		// Always use project's log_root if set
		if project.LogRoot != "" {
			st.LogRoot = project.LogRoot
		}
		writeJSON(w, http.StatusOK, map[string]interface{}{
			"settings": st,
		})
		return
	}
	st := getSettings()
	writeJSON(w, http.StatusOK, map[string]interface{}{
		"settings": st,
	})
}

// handleSaveSettings updates settings.
// POST /api/v1/settings?project_id={id}
// If project_id is provided, saves settings to the project's SettingsJSON
// field (project-specific). Otherwise saves to global settings.json.
func (s *Server) handleSaveSettings(w http.ResponseWriter, r *http.Request) {
	var req Settings
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		writeError(w, http.StatusBadRequest, "validation_error", "invalid JSON body")
		return
	}

	// Fill defaults for empty fields
	def := defaultSettings()
	if req.DIAHost == "" {
		req.DIAHost = def.DIAHost
	}
	if req.DIAPort == 0 {
		req.DIAPort = def.DIAPort
	}
	if req.BsToolHost == "" {
		req.BsToolHost = def.BsToolHost
	}
	if req.BsToolPort == 0 {
		req.BsToolPort = def.BsToolPort
	}
	if req.LogRootName == "" {
		req.LogRootName = def.LogRootName
	}
	// Auto-detect BsTool.exe in logreport root if bstool_path is empty or "./BsTool.exe"
	if req.BsToolPath == "" || req.BsToolPath == "./BsTool.exe" || req.BsToolPath == "BsTool.exe" {
		// Check if BsTool.exe exists in the current directory (logreport root)
		if _, err := os.Stat("BsTool.exe"); err == nil {
			abs, _ := filepath.Abs("BsTool.exe")
			req.BsToolPath = abs
		} else if _, err := os.Stat("./BsTool.exe"); err == nil {
			abs, _ := filepath.Abs("./BsTool.exe")
			req.BsToolPath = abs
		}
	}
	if req.CommunicationLine == "" {
		req.CommunicationLine = def.CommunicationLine
	}
	if req.BUDir == "" {
		req.BUDir = def.BUDir
	}
	if req.LISMode == "" {
		req.LISMode = def.LISMode
	}
	if req.LISExeCount == 0 {
		req.LISExeCount = def.LISExeCount
	}
	if req.ScanMethod == "" {
		// If BsTool.exe is detected locally, prefer local_exe mode
		if req.BsToolPath != "" && req.BsToolPath != def.BsToolPath {
			req.ScanMethod = "local_exe"
		} else {
			req.ScanMethod = def.ScanMethod
		}
	}

	// Check for project_id — save project-specific settings
	projectIDStr := r.URL.Query().Get("project_id")
	if projectIDStr != "" {
		var projectID int64
		fmt.Sscanf(projectIDStr, "%d", &projectID)
		project, err := s.store.GetProject(projectID)
		if err != nil {
			writeError(w, http.StatusNotFound, "not_found", "project not found")
			return
		}
		// Save settings as JSON blob in the project
		settingsBytes, err := json.Marshal(req)
		if err != nil {
			writeError(w, http.StatusInternalServerError, "save_error", "failed to marshal settings")
			return
		}
		project.SettingsJSON = string(settingsBytes)
		// Update log_root on the project if changed
		if req.LogRoot != "" {
			project.LogRoot = req.LogRoot
		}
		if _, err := s.store.UpdateProject(projectID, project); err != nil {
			writeError(w, http.StatusInternalServerError, "save_error",
				fmt.Sprintf("failed to save project settings: %v", err))
			return
		}
		writeJSON(w, http.StatusOK, map[string]interface{}{
			"settings": req,
			"saved":    true,
		})
		return
	}

	// Global settings save
	// Apply log_root immediately
	if req.LogRoot != "" {
		s.logRootDir = req.LogRoot
		// Create directory if needed
		os.MkdirAll(req.LogRoot, 0755)
	}

	if err := saveSettings(req); err != nil {
		writeError(w, http.StatusInternalServerError, "save_error",
			fmt.Sprintf("failed to save settings: %v", err))
		return
	}

	writeJSON(w, http.StatusOK, map[string]interface{}{
		"settings": req,
		"saved":    true,
	})
}

// mergeSettings overlays project-specific settings over global settings.
// Non-zero values from proj override global values.
func mergeSettings(global, proj Settings) Settings {
	result := global
	if proj.DIAHost != "" {
		result.DIAHost = proj.DIAHost
	}
	if proj.DIAPort != 0 {
		result.DIAPort = proj.DIAPort
	}
	if proj.BsToolHost != "" {
		result.BsToolHost = proj.BsToolHost
	}
	if proj.BsToolPort != 0 {
		result.BsToolPort = proj.BsToolPort
	}
	if proj.LogRoot != "" {
		result.LogRoot = proj.LogRoot
	}
	if proj.LogRootName != "" {
		result.LogRootName = proj.LogRootName
	}
	if proj.BsToolPath != "" {
		result.BsToolPath = proj.BsToolPath
	}
	if proj.CommunicationLine != "" {
		result.CommunicationLine = proj.CommunicationLine
	}
	if proj.OutputDir != "" {
		result.OutputDir = proj.OutputDir
	}
	if proj.BUDir != "" {
		result.BUDir = proj.BUDir
	}
	if proj.LISMode != "" {
		result.LISMode = proj.LISMode
	}
	if proj.ScanMethod != "" {
		result.ScanMethod = proj.ScanMethod
	}
	if proj.NodeFilter != "" {
		result.NodeFilter = proj.NodeFilter
	}
	if proj.LISExeCount != 0 {
		result.LISExeCount = proj.LISExeCount
	}
	if proj.LISDiagPassword != "" {
		result.LISDiagPassword = proj.LISDiagPassword
	}
	return result
}

// getSettingsForProject returns settings merged with project-specific overrides.
// If the project has no SettingsJSON or projectID is 0, returns global settings.
func (s *Server) getSettingsForProject(projectID int64) Settings {
	st := getSettings()
	if projectID == 0 {
		return st
	}
	project, err := s.store.GetProject(projectID)
	if err != nil || project.SettingsJSON == "" {
		// Still apply log_root from project if available
		if err == nil && project.LogRoot != "" {
			st.LogRoot = project.LogRoot
		}
		return st
	}
	var projSettings Settings
	if err := json.Unmarshal([]byte(project.SettingsJSON), &projSettings); err == nil {
		st = mergeSettings(st, projSettings)
	}
	if project.LogRoot != "" {
		st.LogRoot = project.LogRoot
	}
	return st
}