// Package logwriter writes command output to per-node log files.
// It mirrors the Python log_writer.py behavior for the Commander window.
//
// Log directory structure: {logRoot}/{tokenType}/{nodeName}/{filename}
// Filename patterns (matching Python log_writer.py):
//
//	FBC: {nodeName}_{ipFormatted}_{tokenID}.fbc
//	RPC: {nodeName}_{ipFormatted}_{tokenID}.rpc
//	LOG: {nodeName}_{ipFormatted}.log
//	LIS: {nodeName}_{ipFormatted}_exe{i}_5irb_5orb.lis
//
// Where ipFormatted = IP address with dots replaced by hyphens (e.g. 192-168-0-11).
// When IP is unknown, "unknown-ip" is used as placeholder.
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
	logRoot string // root directory for log files
}

// LogEntry represents a log file entry.
type LogEntry struct {
	FileName   string    `json:"file_name"`
	FilePath   string    `json:"file_path"`
	Size       int64     `json:"size"`
	ModifiedAt time.Time `json:"modified_at"`
}

// New creates a LogWriter with the given root directory.
// The root directory is created if it doesn't exist.
func New(logRoot string) *LogWriter {
	return &LogWriter{logRoot: logRoot}
}

// formatIP replaces dots with hyphens in an IP address for filename use.
// Returns "unknown-ip" if the IP is empty.
func formatIP(ip string) string {
	if ip == "" {
		return "unknown-ip"
	}
	return strings.ReplaceAll(ip, ".", "-")
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
// Directory: {logRoot}/{tokenType}/{nodeName}/
// Filename: {nodeName}_{ipFormatted}_{tokenID}.{ext}
// For LOG type: {nodeName}_{ipFormatted}.log (no tokenID in filename)
func (lw *LogWriter) logPath(nodeName, tokenType, tokenID, ip string) string {
	ext := fileExtension(tokenType)
	ipFmt := formatIP(ip)
	typeDir := strings.ToUpper(tokenType)

	// Clean node name for filesystem (spaces → underscores)
	safeNode := strings.ReplaceAll(nodeName, " ", "_")

	var fileName string
	if strings.ToUpper(tokenType) == "LOG" {
		fileName = fmt.Sprintf("%s_%s%s", safeNode, ipFmt, ext)
	} else {
		fileName = fmt.Sprintf("%s_%s_%s%s", safeNode, ipFmt, tokenID, ext)
	}

	return filepath.Join(lw.logRoot, typeDir, safeNode, fileName)
}

// nodeDir returns the directory path for a node's logs, creating it if needed.
func (lw *LogWriter) nodeDir(nodeName, tokenType string) (string, error) {
	safeNode := strings.ReplaceAll(nodeName, " ", "_")
	dir := filepath.Join(lw.logRoot, strings.ToUpper(tokenType), safeNode)
	if err := os.MkdirAll(dir, 0755); err != nil {
		return "", fmt.Errorf("logwriter: create dir %s: %w", dir, err)
	}
	return dir, nil
}

// WriteOutput appends command output to a node's log file.
// File path: {logRoot}/{tokenType}/{nodeName}/{nodeName}_{ip}_{tokenID}.{ext}
// A decorative header with ═══ bars, command metadata, and ─── separators
// is prepended to each write (matching Python log_writer.py style).
//
// The ipAddress parameter is used for filename formatting (dots → hyphens).
// If empty, "unknown-ip" is used.
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

	path := lw.logPath(nodeName, tokenType, tokenID, ipAddress)

	// Open in append mode (create if not exists)
	f, err := os.OpenFile(path, os.O_APPEND|os.O_CREATE|os.O_WRONLY, 0644)
	if err != nil {
		return fmt.Errorf("logwriter: open %s: %w", path, err)
	}
	defer f.Close()

	// Write decorative header
	header := buildDecorativeHeader(nodeName, tokenType, tokenID)
	if _, err := f.WriteString(header); err != nil {
		return fmt.Errorf("logwriter: write header: %w", err)
	}
	if _, err := f.WriteString(output); err != nil {
		return fmt.Errorf("logwriter: write output: %w", err)
	}
	if !strings.HasSuffix(output, "\n") {
		f.WriteString("\n")
	}

	// Write footer separator
	footer := buildSeparator()
	if _, err := f.WriteString(footer); err != nil {
		return fmt.Errorf("logwriter: write footer: %w", err)
	}

	return nil
}

// buildDecorativeHeader creates a decorative header block with ═══ bars,
// command metadata, and ─── separators (matching Python log_writer.py style).
func buildDecorativeHeader(nodeName, tokenType, tokenID string) string {
	now := time.Now().UTC().Format("2006-01-02 15:04:05 UTC")
	bar := strings.Repeat("═", 60)
	return fmt.Sprintf("\n%s\n  NODE: %s  |  TYPE: %s  |  TOKEN: %s  |  TIME: %s\n%s\n",
		bar, nodeName, strings.ToUpper(tokenType), tokenID, now, bar)
}

// buildSeparator creates a ─── separator line used after output.
func buildSeparator() string {
	return strings.Repeat("─", 60) + "\n"
}

// ReadLog reads the content of a node's log file.
func (lw *LogWriter) ReadLog(nodeName, tokenType, tokenID, ipAddress string) (string, error) {
	path := lw.logPath(nodeName, tokenType, tokenID, ipAddress)
	data, err := os.ReadFile(path)
	if err != nil {
		if os.IsNotExist(err) {
			return "", fmt.Errorf("logwriter: log file not found: %s", path)
		}
		return "", fmt.Errorf("logwriter: read %s: %w", path, err)
	}
	return string(data), nil
}

// ListLogs lists all log files for a node across all token types.
// Returns a slice of LogEntry sorted by file name.
func (lw *LogWriter) ListLogs(nodeName string) ([]LogEntry, error) {
	safeNode := strings.ReplaceAll(nodeName, " ", "_")
	result := make([]LogEntry, 0)

	// Check all token type directories
	for _, tokenType := range []string{"FBC", "RPC", "LOG", "LIS"} {
		dir := filepath.Join(lw.logRoot, tokenType, safeNode)
		entries, err := os.ReadDir(dir)
		if err != nil {
			continue // Directory doesn't exist, skip
		}

		for _, entry := range entries {
			if entry.IsDir() {
				continue
			}
			info, err := entry.Info()
			if err != nil {
				continue
			}
			result = append(result, LogEntry{
				FileName:   entry.Name(),
				FilePath:   filepath.Join(dir, entry.Name()),
				Size:       info.Size(),
				ModifiedAt: info.ModTime(),
			})
		}
	}

	// Sort by file name for stable output
	sort.Slice(result, func(i, j int) bool {
		return result[i].FileName < result[j].FileName
	})

	return result, nil
}

// ClearLog truncates a node's log file (removes all content).
func (lw *LogWriter) ClearLog(nodeName, tokenType, tokenID, ipAddress string) error {
	path := lw.logPath(nodeName, tokenType, tokenID, ipAddress)
	if err := os.Truncate(path, 0); err != nil {
		if os.IsNotExist(err) {
			return nil // Nothing to clear
		}
		return fmt.Errorf("logwriter: clear %s: %w", path, err)
	}
	return nil
}

// LogRoot returns the configured log root directory.
func (lw *LogWriter) LogRoot() string {
	return lw.logRoot
}