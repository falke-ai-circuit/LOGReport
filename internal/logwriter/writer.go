// Package logwriter writes command output to per-node log files.
// It mirrors the Python log_writer.py behavior for the Commander window.
//
// Log directory structure: {logRoot}/{nodeName}/{tokenType}_{tokenID}.log
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

// nodeDir returns the directory path for a node's logs, creating it if needed.
func (lw *LogWriter) nodeDir(nodeName string) (string, error) {
	dir := filepath.Join(lw.logRoot, nodeName)
	if err := os.MkdirAll(dir, 0755); err != nil {
		return "", fmt.Errorf("logwriter: create dir %s: %w", dir, err)
	}
	return dir, nil
}

// logPath returns the full path for a specific log file.
func (lw *LogWriter) logPath(nodeName, tokenType, tokenID string) string {
	fileName := fmt.Sprintf("%s_%s.log", strings.ToLower(tokenType), tokenID)
	return filepath.Join(lw.logRoot, nodeName, fileName)
}

// WriteOutput appends command output to a node's log file.
// File path: {logRoot}/{nodeName}/{tokenType}_{tokenID}.log
// A decorative header with ═══ bars, command metadata, and ─── separators
// is prepended to each write (matching Python log_writer.py style).
func (lw *LogWriter) WriteOutput(nodeName, tokenType, tokenID, output string) error {
	if nodeName == "" {
		return fmt.Errorf("logwriter: nodeName is required")
	}
	if _, err := lw.nodeDir(nodeName); err != nil {
		return err
	}

	path := lw.logPath(nodeName, tokenType, tokenID)

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
func (lw *LogWriter) ReadLog(nodeName, tokenType, tokenID string) (string, error) {
	path := lw.logPath(nodeName, tokenType, tokenID)
	data, err := os.ReadFile(path)
	if err != nil {
		if os.IsNotExist(err) {
			return "", fmt.Errorf("logwriter: log file not found: %s", path)
		}
		return "", fmt.Errorf("logwriter: read %s: %w", path, err)
	}
	return string(data), nil
}

// ListLogs lists all log files for a node.
// Returns a slice of LogEntry sorted by file name.
func (lw *LogWriter) ListLogs(nodeName string) ([]LogEntry, error) {
	dir := filepath.Join(lw.logRoot, nodeName)

	entries, err := os.ReadDir(dir)
	if err != nil {
		if os.IsNotExist(err) {
			return make([]LogEntry, 0), nil
		}
		return nil, fmt.Errorf("logwriter: list %s: %w", dir, err)
	}

	result := make([]LogEntry, 0, len(entries))
	for _, entry := range entries {
		if entry.IsDir() {
			continue
		}
		if !strings.HasSuffix(entry.Name(), ".log") {
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

	// Sort by file name for stable output
	sort.Slice(result, func(i, j int) bool {
		return result[i].FileName < result[j].FileName
	})

	return result, nil
}

// ClearLog truncates a node's log file (removes all content).
func (lw *LogWriter) ClearLog(nodeName, tokenType, tokenID string) error {
	path := lw.logPath(nodeName, tokenType, tokenID)
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