package api

import (
	"encoding/json"
	"fmt"
	"net/http"
	"os"
	"path/filepath"
	"runtime"
	"sync"
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
		st.BsToolPath = def.BsToolPath
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
		st.ScanMethod = def.ScanMethod
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
// GET /api/v1/settings
func (s *Server) handleGetSettings(w http.ResponseWriter, r *http.Request) {
	if !globalSettings.loaded {
		s.initSettings()
	}
	st := getSettings()
	writeJSON(w, http.StatusOK, map[string]interface{}{
		"settings": st,
	})
}

// handleSaveSettings updates settings.
// POST /api/v1/settings
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
	if req.BsToolPath == "" {
		req.BsToolPath = def.BsToolPath
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
		req.ScanMethod = def.ScanMethod
	}

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