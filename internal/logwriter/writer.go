// Package logwriter writes command output to per-node log files.
// It mirrors the Python log_writer.py behavior for the Commander window.
//
// Log directory structure: {logRoot}/{stationName}/{tokenType}/{filename}
// Filename patterns (matching Python log_creator.py):
//
//	FBC: {stationName}_{ipFormatted}_{tokenID}.fbc
//	RPC: {stationName}_{ipFormatted}_{tokenID}.rpc
//	LOG: {stationName}_{ipFormatted}.log
//	LIS: {stationName}_{ipFormatted}_exe{i}_irb_orb.lis
//
// Where ipFormatted = IP address with dots replaced by hyphens (e.g. 192-168-0-11).
// All slots of a station share the station name in the filename.
// e.g. AP01m_192-168-0-11_162.fbc, AP01m_192-168-0-11_163.fbc (both under AP01m/FBC/)
package logwriter

import (
	"fmt"
	"os"
	"path/filepath"
	"sort"
	"strings"
	"time"
)

// LogWriter writes command output to per-node log files.
type LogWriter struct {
	logRoot string
}

// LogEntry represents a log file entry.
type LogEntry struct {
	FileName   string    `json:"file_name"`
	FilePath   string    `json:"file_path"`
	Size       int64     `json:"size"`
	ModifiedAt time.Time `json:"modified_at"`
}

// New creates a LogWriter with the given root directory.
func New(logRoot string) *LogWriter {
	return &LogWriter{logRoot: logRoot}
}

// formatIP replaces dots with hyphens in an IP address for filename use.
func formatIP(ip string) string {
	if ip == "" {
		return "unknown-ip"
	}
	return strings.ReplaceAll(ip, ".", "-")
}

// extractStationName derives the station folder name from a node name.
// "AP01" -> "AP01m", "AP01 Main" -> "AP01m", "AP01_m2" -> "AP01m"
// "AP02 Reserve" -> "AP02r", "AP02_r2" -> "AP02r"
// "AL01" -> "AL01" (LIS, no suffix), "A1OA OPS" -> "A1OA" (OPS, no suffix)
func extractStationName(nodeName string) string {
	if strings.HasPrefix(nodeName, "AL") || strings.Contains(nodeName, "OPS") {
		base := nodeName
		if idx := strings.Index(base, " "); idx >= 0 {
			base = base[:idx]
		}
		return base
	}

	isReserve := strings.Contains(nodeName, "Reserve") || strings.Contains(nodeName, "_r")

	base := nodeName
	if idx := strings.Index(base, " "); idx >= 0 {
		base = base[:idx]
	}
	if idx := strings.Index(base, "_"); idx >= 0 {
		base = base[:idx]
	}

	if isReserve {
		return base + "r"
	}
	return base + "m"
}

// fileExtension returns the file extension for a token type.
func fileExtension(tokenType string) string {
	switch strings.ToUpper(tokenType) {
	case "FBC":
		return ".fbc"
	case "RPC":
		return ".rpc"
	case "LIS":
		return ".lis"
	default:
		return ".log"
	}
}

// logPath returns the full path for a specific log file.
// Directory: {logRoot}/{stationName}/{tokenType}/
// Filename: {stationName}_{ipFormatted}_{tokenID}.{ext}
// For LOG type: {stationName}_{ipFormatted}.log (no tokenID in filename)
func (lw *LogWriter) logPath(nodeName, tokenType, tokenID, ip string) string {
	ext := fileExtension(tokenType)
	ipFmt := formatIP(ip)
	typeDir := strings.ToUpper(tokenType)
	stationName := extractStationName(nodeName)

	var fileName string
	if strings.ToUpper(tokenType) == "LOG" {
		fileName = fmt.Sprintf("%s_%s%s", stationName, ipFmt, ext)
	} else {
		fileName = fmt.Sprintf("%s_%s_%s%s", stationName, ipFmt, tokenID, ext)
	}

	return filepath.Join(lw.logRoot, stationName, typeDir, fileName)
}

// nodeDir returns the directory path for a node's logs, creating it if needed.
// Directory: {logRoot}/{stationName}/{tokenType}/
func (lw *LogWriter) nodeDir(nodeName, tokenType string) (string, error) {
	stationName := extractStationName(nodeName)
	dir := filepath.Join(lw.logRoot, stationName, strings.ToUpper(tokenType))
	if err := os.MkdirAll(dir, 0755); err != nil {
		return "", fmt.Errorf("logwriter: create dir %s: %w", dir, err)
	}
	return dir, nil
}

// WriteOutput appends command output to a node's log file.
func (lw *LogWriter) WriteOutput(nodeName, tokenType, tokenID, output string) error {
	return lw.WriteOutputWithIP(nodeName, tokenType, tokenID, output, "")
}

// WriteOutputWithIP is like WriteOutput but includes the IP address in the filename.
func (lw *LogWriter) WriteOutputWithIP(nodeName, tokenType, tokenID, output, ipAddress string) error {
	if nodeName == "" {
		return fmt.Errorf("logwriter: nodeName is required")
	}
	if _, err := lw.nodeDir(nodeName, tokenType); err != nil {
		return err
	}

	filePath := lw.logPath(nodeName, tokenType, tokenID, ipAddress)

	header := formatHeader(nodeName, tokenType, tokenID)
	content := header + output + "\n"

	f, err := os.OpenFile(filePath, os.O_CREATE|os.O_WRONLY|os.O_APPEND, 0644)
	if err != nil {
		return fmt.Errorf("logwriter: open %s: %w", filePath, err)
	}
	defer f.Close()

	if _, err := f.WriteString(content); err != nil {
		return fmt.Errorf("logwriter: write %s: %w", filePath, err)
	}

	return nil
}

// formatHeader creates a decorative header for each log entry.
func formatHeader(nodeName, tokenType, tokenID string) string {
	ts := time.Now().Format("2006-01-02 15:04:05")
	station := extractStationName(nodeName)
	bar := strings.Repeat("=", 70)
	sep := strings.Repeat("-", 70)
	return fmt.Sprintf("\n%s\n# Node: %s | Station: %s | Type: %s | Token: %s | Time: %s\n%s\n", bar, nodeName, station, tokenType, tokenID, ts, sep)
}

// ListFiles returns all log files of a given type in the log root.
func (lw *LogWriter) ListFiles(tokenType string) ([]LogEntry, error) {
	typeDir := strings.ToUpper(tokenType)
	entries := make([]LogEntry, 0)

	rootEntries, err := os.ReadDir(lw.logRoot)
	if err != nil {
		return entries, nil
	}

	for _, stationEntry := range rootEntries {
		if !stationEntry.IsDir() {
			continue
		}
		typePath := filepath.Join(lw.logRoot, stationEntry.Name(), typeDir)
		fileEntries, err := os.ReadDir(typePath)
		if err != nil {
			continue
		}
		for _, fe := range fileEntries {
			if fe.IsDir() {
				continue
			}
			info, err := fe.Info()
			if err != nil {
				continue
			}
			entries = append(entries, LogEntry{
				FileName:   fe.Name(),
				FilePath:   filepath.Join(typePath, fe.Name()),
				Size:       info.Size(),
				ModifiedAt: info.ModTime(),
			})
		}
	}

	sort.Slice(entries, func(i, j int) bool {
		return entries[i].FileName < entries[j].FileName
	})

	return entries, nil
}


// ListLogs returns all log files for a given node (by station name).
// It scans {logRoot}/{stationName}/*/ for all files.
func (lw *LogWriter) ListLogs(nodeName string) ([]LogEntry, error) {
	stationName := extractStationName(nodeName)
	entries := make([]LogEntry, 0)

	stationDir := filepath.Join(lw.logRoot, stationName)
	typeEntries, err := os.ReadDir(stationDir)
	if err != nil {
		return entries, nil
	}

	for _, typeEntry := range typeEntries {
		if !typeEntry.IsDir() {
			continue
		}
		typePath := filepath.Join(stationDir, typeEntry.Name())
		fileEntries, err := os.ReadDir(typePath)
		if err != nil {
			continue
		}
		for _, fe := range fileEntries {
			if fe.IsDir() {
				continue
			}
			info, err := fe.Info()
			if err != nil {
				continue
			}
			entries = append(entries, LogEntry{
				FileName:   fe.Name(),
				FilePath:   filepath.Join(typePath, fe.Name()),
				Size:       info.Size(),
				ModifiedAt: info.ModTime(),
			})
		}
	}

	sort.Slice(entries, func(i, j int) bool {
		return entries[i].FileName < entries[j].FileName
	})

	return entries, nil
}

// ReadLog reads the content of a specific log file.
func (lw *LogWriter) ReadLog(nodeName, tokenType, tokenID, ipAddress string) (string, error) {
	filePath := lw.logPath(nodeName, tokenType, tokenID, ipAddress)
	data, err := os.ReadFile(filePath)
	if err != nil {
		return "", fmt.Errorf("logwriter: read %s: %w", filePath, err)
	}
	return string(data), nil
}
