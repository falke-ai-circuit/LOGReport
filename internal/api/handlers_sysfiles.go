package api

import (
	"context"
	"encoding/json"
	"fmt"
	"io"
	"log"
	"net/http"
	"os"
	"path/filepath"
	"runtime"
	"strings"
	"time"

	"github.com/falke-ai-circuit/LOGReport/internal/bstool"
	"github.com/falke-ai-circuit/LOGReport/internal/parser"
	"github.com/falke-ai-circuit/LOGReport/internal/sysloader"
	"github.com/falke-ai-circuit/LOGReport/internal/telnet"
	"github.com/falke-ai-circuit/LOGReport/internal/types"
)

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

// handleScanNodes retrieves .sys files from the BU and parses them for node detection.
// It first tries the local BU directory (fast path), then falls back to remote BsTool
// TCP retrieval from the BU at the configured BsTool host:port.
// POST /api/v1/sysfiles/scan-nodes
func (s *Server) handleScanNodes(w http.ResponseWriter, r *http.Request) {
	ctx, cancel := context.WithTimeout(r.Context(), 95*time.Second)
	defer cancel()
	_ = ctx

	if !globalSettings.loaded {
		s.initSettings()
	}
	st := getSettings()

	buDir := st.BUDir
	if buDir == "" {
		buDir = "C:\\dna\\CA\\bu"
		if runtime.GOOS != "windows" {
			buDir = "/dna/CA/bu"
		}
	}

	buHost := st.BsToolHost
	if buHost == "" {
		buHost = "127.0.0.1"
	}
	buPort := st.BsToolPort
	if buPort == 0 {
		buPort = 1516
	}
	commLine := st.CommunicationLine
	if commLine == "" {
		commLine = "AB01"
	}

	// Scan method: "remote_bu" (default) uses BsTool TCP, "local_dir" uses local BU directory.
	// The user selects this in Settings — no automatic fallback.
	scanMethod := st.ScanMethod
	if scanMethod == "" {
		scanMethod = "remote_bu"
	}

	// Step 1: If scan method is local_dir, read .sys files from the local BU directory.
	if scanMethod == "local_dir" {
		buConfigs := tryLoadSysFromBUDir(buDir)
		if len(buConfigs) > 0 {
			// Apply XdSysUsed filtering from local filesystem too.
			buConfigs, filterInfo := filterLocalSysByXdSysUsed(buDir, buConfigs)
			filtered := filterNodeConfigs(buConfigs, st.NodeFilter)
			writeJSON(w, http.StatusOK, map[string]interface{}{
				"configs":     filtered,
				"count":       len(filtered),
				"method":      "bu_local_sys_files",
				"bu_dir":      buDir,
				"filter_info": filterInfo,
			})
			return
		}
		// Local dir selected but no .sys files found — return error, do NOT fallback to remote
		writeError(w, http.StatusNotFound, "no_sys_files",
			fmt.Sprintf("No .sys files found in local BU directory %s (scan_method=local_dir)", buDir))
		return
	}

	// Step 2: scan_method=remote_bu — retrieve .sys files from remote BU.
	// Uses native Go TCP protocol (no BsTool.exe subprocess needed).
	// VERIFIED 2026-07-07: Works on buc_16.20.exe with 3x handshake + READ_DIR.

	timeout := 10 * time.Second
	sysFileData, err := bstool.RetrieveSysFileData(buHost, buPort, commLine, timeout)
	if err != nil {
		writeError(w, http.StatusBadGateway, "bu_connection_failed",
			fmt.Sprintf("Remote BU %s:%d retrieval failed: %v", buHost, buPort, err))
		return
	}
	if len(sysFileData) == 0 {
		writeError(w, http.StatusNotFound, "no_sys_files",
			fmt.Sprintf("No .sys files found on BU %s:%d (commLine=%s)", buHost, buPort, commLine))
		return
	}

	// Filter .sys files by active config (XdSysUsed → _sys file → active hw addresses).
	// This eliminates stale nodes from old .sys files that are no longer active.
	sysFileData, filterInfo := filterSysDataByXdSysUsed(buHost, buPort, commLine, timeout, sysFileData)

	// Convert SysFileData to the struct format expected by LoadSysFilesFromData
	dataSlice := make([]sysloader.SysFileData, len(sysFileData))
	for i, sf := range sysFileData {
		dataSlice[i] = sysloader.SysFileData{Name: sf.Name, Data: sf.Data}
	}

	configs, err := sysloader.LoadSysFilesFromData(dataSlice)
	if err != nil || len(configs) == 0 {
		writeError(w, http.StatusInternalServerError, "parse_failed",
			fmt.Sprintf("Parsed %d .sys files but got 0 configs: %v", len(sysFileData), err))
		return
	}

	filtered := filterNodeConfigs(configs, st.NodeFilter)
	writeJSON(w, http.StatusOK, map[string]interface{}{
		"configs":     filtered,
		"count":       len(filtered),
		"method":      "bstool_remote_sys_files",
		"bu_host":     buHost,
		"bu_port":     buPort,
		"sys_count":   len(sysFileData),
		"filter_info": filterInfo,
	})
}

// filterSysDataByXdSysUsed implements the 3-layer active config filter:
// 1. Fetch XdSysUsed from BU → parse to find active _sys filename
// 2. Fetch _sys file from BU → parse :e:hw: entries for active hw addresses
// 3. Filter .sys files — only keep those whose filename stem matches an active hw address
//
// If any step fails (file not found, parse error), returns the original data unchanged
// with a description of what happened in the filter_info string.
func filterSysDataByXdSysUsed(host string, port int, commLine string, timeout time.Duration, sysFileData []bstool.SysFileData) ([]bstool.SysFileData, string) {
	ft := bstool.NewFileTransport(host, port, timeout)
	defer ft.Close()

	// Step 1: Fetch XdSysUsed file from BU.
	xdData, err := ft.ReadFile(commLine, "XdSysUsed")
	if err != nil {
		return sysFileData, fmt.Sprintf("XdSysUsed fetch failed: %v (no filtering applied)", err)
	}

	xdText := string(xdData)
	// Parse XdSysUsed: each line has "station_name sys_file grp_file" format.
	// Extract the _sys filenames (second column, ends with _sys).
	var activeSysFiles []string
	for _, line := range strings.Split(xdText, "\n") {
		line = strings.TrimSpace(line)
		if line == "" || strings.HasPrefix(line, ":") || strings.HasPrefix(line, "#") {
			continue
		}
		parts := strings.Fields(line)
		if len(parts) >= 2 {
			sysFile := parts[1]
			if strings.HasSuffix(strings.ToLower(sysFile), "_sys") {
				activeSysFiles = append(activeSysFiles, sysFile)
			}
		}
	}

	if len(activeSysFiles) == 0 {
		return sysFileData, "XdSysUsed parsed but no _sys files found (no filtering applied)"
	}

	// Step 2: Fetch each _sys file and extract active hw addresses from :e:hw: entries.
	activeHW := make(map[string]bool)
	for _, sysFile := range activeSysFiles {
		sysData, err := ft.ReadFile(commLine, sysFile)
		if err != nil {
			continue
		}
		// Parse :e:hw:{hw_addr} {station} {config} entries
		for _, line := range strings.Split(string(sysData), "\n") {
			line = strings.TrimSpace(line)
			if !strings.HasPrefix(line, ":e:hw:") {
				continue
			}
			rest := strings.TrimPrefix(line, ":e:hw:")
			fields := strings.Fields(rest)
			if len(fields) >= 1 {
				hwAddr := strings.TrimSpace(fields[0])
				if hwAddr != "" {
					activeHW[hwAddr] = true
				}
			}
		}
	}

	if len(activeHW) == 0 {
		return sysFileData, fmt.Sprintf("Parsed %d _sys files but found 0 :e:hw: entries (no filtering applied)", len(activeSysFiles))
	}

	// Step 3: Filter .sys files — only keep those whose filename stem matches an active hw address.
	var filtered []bstool.SysFileData
	skipped := 0
	for _, sf := range sysFileData {
		stem := strings.TrimSuffix(sf.Name, filepath.Ext(sf.Name))
		if activeHW[stem] {
			filtered = append(filtered, sf)
		} else {
			skipped++
		}
	}

	if len(filtered) == 0 {
		// All files were filtered out — this likely means the hw address format doesn't match.
		// Return original data to avoid breaking the scan.
		return sysFileData, fmt.Sprintf("All %d .sys files filtered out by hw address match (returned original, filter may need format adjustment)", len(sysFileData))
	}

	return filtered, fmt.Sprintf("XdSysUsed→%d _sys files→%d active hw addresses: %d .sys files kept, %d stale files removed", len(activeSysFiles), len(activeHW), len(filtered), skipped)
}

// tryLoadSysFromBUDir attempts to load .sys files from the BU directory.
// Returns nil if the directory doesn't exist, has no .sys files, or parsing fails.
// On success, returns the same configs as a manual .sys file import —
// with real IP addresses, FBC/RPC tokens, and full node names.
func tryLoadSysFromBUDir(buDir string) []types.NodeConfig {
	if _, err := os.Stat(buDir); err != nil {
		return nil
	}
	configs, err := sysloader.LoadSysFiles(buDir)
	if err != nil || len(configs) == 0 {
		buVMDir := filepath.Join(filepath.Dir(buDir), "bu_VM")
		configs, err = sysloader.LoadSysFiles(buVMDir)
		if err != nil || len(configs) == 0 {
			return nil
		}
	}
	return configs
}

// filterLocalSysByXdSysUsed applies the same 3-layer XdSysUsed filter as filterSysDataByXdSysUsed,
// but reads from the local BU directory instead of remote BU via TCP.
func filterLocalSysByXdSysUsed(buDir string, configs []types.NodeConfig) ([]types.NodeConfig, string) {
	// Step 1: Read XdSysUsed from local BU directory.
	xdPath := filepath.Join(buDir, "XdSysUsed")
	xdData, err := os.ReadFile(xdPath)
	if err != nil {
		return configs, fmt.Sprintf("XdSysUsed not found in %s: %v (no filtering applied)", buDir, err)
	}

	// Parse XdSysUsed: each line has "station_name sys_file grp_file" format.
	var activeSysFiles []string
	for _, line := range strings.Split(string(xdData), "\n") {
		line = strings.TrimSpace(line)
		if line == "" || strings.HasPrefix(line, ":") || strings.HasPrefix(line, "#") {
			continue
		}
		parts := strings.Fields(line)
		if len(parts) >= 2 {
			sysFile := parts[1]
			if strings.HasSuffix(strings.ToLower(sysFile), "_sys") {
				activeSysFiles = append(activeSysFiles, sysFile)
			}
		}
	}

	if len(activeSysFiles) == 0 {
		return configs, "XdSysUsed parsed but no _sys files found (no filtering applied)"
	}

	// Step 2: Read each _sys file and extract active hw addresses from :e:hw: entries.
	activeHW := make(map[string]bool)
	for _, sysFile := range activeSysFiles {
		sysPath := filepath.Join(buDir, sysFile)
		sysData, err := os.ReadFile(sysPath)
		if err != nil {
			continue
		}
		for _, line := range strings.Split(string(sysData), "\n") {
			line = strings.TrimSpace(line)
			if !strings.HasPrefix(line, ":e:hw:") {
				continue
			}
			rest := strings.TrimPrefix(line, ":e:hw:")
			fields := strings.Fields(rest)
			if len(fields) >= 1 {
				hwAddr := strings.TrimSpace(fields[0])
				if hwAddr != "" {
					activeHW[hwAddr] = true
				}
			}
		}
	}

	if len(activeHW) == 0 {
		return configs, fmt.Sprintf("Parsed %d _sys files but found 0 :e:hw: entries (no filtering applied)", len(activeSysFiles))
	}

	// Step 3: Filter configs — only keep those whose config name's hw address matches.
	// NodeConfig.Name contains the station name (e.g. "AP01m"), and the config was loaded
	// from a .sys file whose stem is the hw address. We need to match by the .sys file
	// that produced this config. Since configs don't carry their source filename,
	// we match by scanning the BU dir for .sys files and mapping hw address → config.
	// Build a map of active .sys file paths.
	activeSysPaths := make(map[string]bool)
	for hwAddr := range activeHW {
		activeSysPaths[hwAddr+".sys"] = true
	}

	// Re-scan the BU directory to find which .sys files exist and match.
	matches, err := filepath.Glob(filepath.Join(buDir, "*.sys"))
	if err != nil || len(matches) == 0 {
		return configs, fmt.Sprintf("Could not scan .sys files in %s: %v (no filtering applied)", buDir, err)
	}

	// Build set of active .sys file basenames.
	activeBases := make(map[string]bool)
	for _, m := range matches {
		base := filepath.Base(m)
		if activeSysPaths[base] {
			activeBases[base] = true
		}
	}

	// Re-load only the active .sys files to get filtered configs.
	if len(activeBases) == 0 {
		return configs, fmt.Sprintf("0 .sys files matched active hw addresses out of %d files (no filtering applied)", len(matches))
	}

	var activePaths []string
	for _, m := range matches {
		if activeBases[filepath.Base(m)] {
			activePaths = append(activePaths, m)
		}
	}

	filteredConfigs, err := sysloader.LoadSysFilesFromPaths(activePaths)
	if err != nil || len(filteredConfigs) == 0 {
		return configs, fmt.Sprintf("Re-load of %d active .sys files failed: %v (no filtering applied)", len(activePaths), err)
	}

	return filteredConfigs, fmt.Sprintf("XdSysUsed→%d _sys files→%d active hw addresses: %d configs kept, %d stale removed", len(activeSysFiles), len(activeHW), len(filteredConfigs), len(configs)-len(filteredConfigs))
}

// filterNodeConfigs filters a list of NodeConfig by station name prefix.
// The filter is a comma-separated list of prefixes. A prefix starting with "-"
// excludes stations starting with that prefix. Otherwise it includes them.
// Examples:
//   "AP,AL"          → only AP* and AL* stations
//   "AP,AL,-AL08"    → AP* and AL* stations, but exclude AL08
//   "-A1O,-B1O"      → all stations except A1O* and B1O*
//   ""               → no filtering (return all)
func filterNodeConfigs(configs []types.NodeConfig, filter string) []types.NodeConfig {
	if filter == "" {
		return configs
	}
	parts := strings.Split(filter, ",")
	var includes, excludes []string
	for _, p := range parts {
		p = strings.TrimSpace(p)
		if p == "" {
			continue
		}
		if strings.HasPrefix(p, "-") {
			excludes = append(excludes, strings.ToUpper(p[1:]))
		} else {
			includes = append(includes, strings.ToUpper(p))
		}
	}

	var result []types.NodeConfig
	for _, cfg := range configs {
		station := extractStationNameFromConfig(cfg.Name)
		stationUpper := strings.ToUpper(station)

		// Check excludes first
		excluded := false
		for _, ex := range excludes {
			if strings.HasPrefix(stationUpper, ex) {
				excluded = true
				break
			}
		}
		if excluded {
			continue
		}

		// If includes is empty, include everything not excluded
		if len(includes) == 0 {
			result = append(result, cfg)
			continue
		}

		// Check includes
		for _, inc := range includes {
			if strings.HasPrefix(stationUpper, inc) {
				result = append(result, cfg)
				break
			}
		}
	}
	return result
}
