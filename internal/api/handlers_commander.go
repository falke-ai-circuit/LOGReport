package api

import (
	"runtime"
	"strings"
)

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

// matchStationName checks if a node config name belongs to the given station.
// The tree groups nodes by station name (e.g. "AP01m" = "AP01_main" + "AP01_m2").
// This replicates the logic from extractStationName in loader.go.
func matchStationName(configName, stationName string) bool {
	if configName == stationName {
		return true
	}
	// Extract station name from config name (strip _mN or _rN suffix)
	base := configName
	if idx := strings.Index(base, "_"); idx >= 0 {
		base = base[:idx]
	}
	if idx := strings.Index(base, " "); idx >= 0 {
		base = base[:idx]
	}
	// Apply m/r suffix for AP-prefixed nodes (same logic as extractStationName)
	if strings.HasPrefix(base, "AP") {
		isReserve := strings.Contains(configName, "Reserve") || strings.Contains(configName, "_r")
		if isReserve {
			base = base + "r"
		} else {
			base = base + "m"
		}
	}
	return base == stationName
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
