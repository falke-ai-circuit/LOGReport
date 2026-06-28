// Package logfile scans log root directories for .fbc/.rpc/.log/.lis files
// and parses their contents into structured data for report generation.
package logfile

import (
	"bufio"
	"fmt"
	"os"
	"path/filepath"
	"sort"
	"strings"
	"time"
)

// SupportedExtensions are the file extensions scanned from the log root.
var SupportedExtensions = []string{".fbc", ".rpc", ".log", ".lis"}

// FileEntry represents a log file found during scanning.
type FileEntry struct {
	FileName   string    `json:"file_name"`
	FilePath   string    `json:"file_path"`
	Extension  string    `json:"extension"`
	Size       int64     `json:"size"`
	ModifiedAt time.Time `json:"modified_at"`
	NodeName   string    `json:"node_name"` // derived from filename (e.g. AP01m.fbc → AP01m)
}

// FileData represents parsed content of a single log file.
type FileData struct {
	FileName  string            `json:"file_name"`
	FilePath  string            `json:"file_path"`
	NodeName  string            `json:"node_name"`
	FileType  string            `json:"file_type"`  // "fbc", "rpc", "log", "lis"
	Header    string            `json:"header"`     // first line (e.g. "#FBC AP01m 2026-06-25")
	Metadata  map[string]string `json:"metadata"`   // NODE=, TYPE=, etc.
	Lines     []string          `json:"lines"`      // raw content lines (excluding header)
	KeyValues []KeyValue        `json:"key_values"` // parsed key=value entries
}

// KeyValue is a parsed key=value pair from FBC/RPC/LIS files.
type KeyValue struct {
	Key   string `json:"key"`
	Value string `json:"value"`
}

// ScanFiles scans the given directory for supported log files.
// Returns a slice of FileEntry sorted by file name.
func ScanFiles(dir string) ([]FileEntry, error) {
	entries, err := os.ReadDir(dir)
	if err != nil {
		if os.IsNotExist(err) {
			return make([]FileEntry, 0), nil
		}
		return nil, fmt.Errorf("logfile: scan %s: %w", dir, err)
	}

	result := make([]FileEntry, 0, len(entries))
	for _, entry := range entries {
		if entry.IsDir() {
			continue
		}
		ext := strings.ToLower(filepath.Ext(entry.Name()))
		if !isSupported(ext) {
			continue
		}
		info, err := entry.Info()
		if err != nil {
			continue
		}
		result = append(result, FileEntry{
			FileName:   entry.Name(),
			FilePath:   filepath.Join(dir, entry.Name()),
			Extension:  ext,
			Size:       info.Size(),
			ModifiedAt: info.ModTime(),
			NodeName:   strings.TrimSuffix(entry.Name(), ext),
		})
	}

	sort.Slice(result, func(i, j int) bool {
		return result[i].FileName < result[j].FileName
	})

	return result, nil
}

// ScanFilesByType scans for files of a specific extension (e.g. ".fbc").
func ScanFilesByType(dir, ext string) ([]FileEntry, error) {
	all, err := ScanFiles(dir)
	if err != nil {
		return nil, err
	}
	if ext != "" && !strings.HasPrefix(ext, ".") {
		ext = "." + ext
	}
	filtered := make([]FileEntry, 0)
	for _, e := range all {
		if ext == "" || strings.EqualFold(e.Extension, ext) {
			filtered = append(filtered, e)
		}
	}
	return filtered, nil
}

// ParseFile reads and parses a single log file.
func ParseFile(path string) (*FileData, error) {
	data, err := os.ReadFile(path)
	if err != nil {
		return nil, fmt.Errorf("logfile: read %s: %w", path, err)
	}

	fileName := filepath.Base(path)
	ext := strings.ToLower(filepath.Ext(fileName))
	fileType := strings.TrimPrefix(ext, ".")
	nodeName := strings.TrimSuffix(fileName, ext)

	fd := &FileData{
		FileName: fileName,
		FilePath: path,
		NodeName: nodeName,
		FileType: fileType,
		Metadata: make(map[string]string),
		Lines:    make([]string, 0),
	}

	scanner := bufio.NewScanner(strings.NewReader(string(data)))
	scanner.Buffer(make([]byte, 0, 1024*1024), 1024*1024) // 1MB max line
	first := true
	for scanner.Scan() {
		line := scanner.Text()
		if first {
			fd.Header = line
			first = false
			// Parse header: "#FBC AP01m 2026-06-25" → type, node, date
			if strings.HasPrefix(line, "#") {
				parts := strings.Fields(line)
				if len(parts) >= 1 {
					fd.Metadata["type"] = strings.TrimPrefix(parts[0], "#")
				}
				if len(parts) >= 2 {
					fd.Metadata["node"] = parts[1]
				}
				if len(parts) >= 3 {
					fd.Metadata["date"] = parts[2]
				}
			}
			continue
		}

		// Skip END markers
		if strings.TrimSpace(line) == "END" {
			continue
		}

		fd.Lines = append(fd.Lines, line)

		// Parse key=value lines
		if idx := strings.Index(line, "="); idx > 0 {
			key := strings.TrimSpace(line[:idx])
			val := strings.TrimSpace(line[idx+1:])
			fd.KeyValues = append(fd.KeyValues, KeyValue{Key: key, Value: val})
			// Also check for NODE=, TYPE= metadata
			upperKey := strings.ToUpper(key)
			if upperKey == "NODE" || upperKey == "TYPE" {
				fd.Metadata[strings.ToLower(upperKey)] = val
			}
		}
	}

	if err := scanner.Err(); err != nil {
		return nil, fmt.Errorf("logfile: scan %s: %w", path, err)
	}

	return fd, nil
}

// ParseAllFiles parses all supported files in a directory.
func ParseAllFiles(dir string) ([]FileData, error) {
	entries, err := ScanFiles(dir)
	if err != nil {
		return nil, err
	}

	result := make([]FileData, 0, len(entries))
	for _, e := range entries {
		fd, err := ParseFile(e.FilePath)
		if err != nil {
			continue // skip files that can't be parsed
		}
		result = append(result, *fd)
	}

	return result, nil
}

// isSupported checks if an extension is in the supported list.
func isSupported(ext string) bool {
	for _, s := range SupportedExtensions {
		if strings.EqualFold(ext, s) {
			return true
		}
	}
	return false
}
