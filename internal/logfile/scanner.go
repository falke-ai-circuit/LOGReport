// Package logfile scans log root directories for .fbc/.rpc/.log/.lis files
// and parses their contents into structured data for report generation.
//
// Supports station-nested directory structure:
//   {logRoot}/{stationName}/{type}/{stationName}_{ip}_{token}.{ext}
//   e.g. {logRoot}/AP01m/FBC/AP01m_192-168-0-11_162.fbc
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
// Includes .rsu (RSU6 mode) and .dia (DiagLis mode) for LIS files.
var SupportedExtensions = []string{".fbc", ".rpc", ".log", ".lis", ".rsu", ".dia"}

// FileEntry represents a log file found during scanning.
type FileEntry struct {
	FileName   string    `json:"file_name"`
	FilePath   string    `json:"file_path"`
	Extension  string    `json:"extension"`
	Size       int64     `json:"size"`
	ModifiedAt time.Time `json:"modified_at"`
	NodeName   string    `json:"node_name"`
	StationName string   `json:"station_name"`
	FileType   string    `json:"file_type"`
}

// FileData represents parsed content of a single log file.
type FileData struct {
	FileName  string            `json:"file_name"`
	FilePath  string            `json:"file_path"`
	NodeName  string            `json:"node_name"`
	StationName string          `json:"station_name"`
	FileType  string            `json:"file_type"`
	Header    string            `json:"header"`
	Metadata  map[string]string `json:"metadata"`
	Lines     []string          `json:"lines"`
	KeyValues []KeyValue        `json:"key_values"`
}

// KeyValue is a parsed key=value pair from FBC/RPC/LIS files.
type KeyValue struct {
	Key   string `json:"key"`
	Value string `json:"value"`
}

// ScanFiles recursively scans the log root for supported log files.
// Handles station-nested structure: {logRoot}/{station}/{type}/{file}
// Also handles flat structure for backward compatibility.
func ScanFiles(dir string) ([]FileEntry, error) {
	result := make([]FileEntry, 0)

	err := filepath.WalkDir(dir, func(path string, d os.DirEntry, err error) error {
		if err != nil {
			return nil // skip errors
		}
		if d.IsDir() {
			return nil
		}

		ext := strings.ToLower(filepath.Ext(d.Name()))
		if !isSupported(ext) {
			return nil
		}

		info, err := d.Info()
		if err != nil {
			return nil
		}

		// Derive station name from path: {logRoot}/{station}/{type}/{file}
		// or {logRoot}/_LOG/{station}/{type}/{file}
		relPath, _ := filepath.Rel(dir, path)
		pathParts := strings.Split(filepath.ToSlash(relPath), "/")
		stationName := ""
		if len(pathParts) >= 3 {
			// Check if first component is _LOG (standard structure)
			if strings.EqualFold(pathParts[0], "_LOG") && len(pathParts) >= 4 {
				stationName = pathParts[1]
			} else {
				stationName = pathParts[0]
			}
		}

		// NodeName: use station name for matching, not the full filename
		nodeName := stationName

		result = append(result, FileEntry{
			FileName:    d.Name(),
			FilePath:    path,
			Extension:   ext,
			Size:        info.Size(),
			ModifiedAt:  info.ModTime(),
			NodeName:    nodeName,
			StationName: stationName,
			FileType:    strings.TrimPrefix(ext, "."),
		})
		return nil
	})

	if err != nil {
		if os.IsNotExist(err) {
			return result, nil
		}
		return nil, fmt.Errorf("logfile: scan %s: %w", dir, err)
	}

	sort.Slice(result, func(i, j int) bool {
		return result[i].FileName < result[j].FileName
	})

	return result, nil
}

// ScanFilesByType scans for files of a specific extension recursively.
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
		FileName:  fileName,
		FilePath:  path,
		NodeName:  nodeName,
		FileType:  fileType,
		Metadata:  make(map[string]string),
		Lines:     make([]string, 0),
	}

	scanner := bufio.NewScanner(strings.NewReader(string(data)))
	scanner.Buffer(make([]byte, 0, 1024*1024), 1024*1024)
	headerFound := false
	for scanner.Scan() {
		line := scanner.Text()

		// Skip leading empty lines before header
		if !headerFound && strings.TrimSpace(line) == "" {
			continue
		}

		// First non-empty line is the header
		if !headerFound {
			fd.Header = line
			headerFound = true
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

		// Detect # metadata lines anywhere in the file (not just first line)
		if strings.HasPrefix(strings.TrimSpace(line), "#") && strings.Contains(line, "|") {
			// Parse "Node: X | Station: Y | Type: Z | Token: T | Time: ..." format
			fields := strings.Split(line, "|")
			for _, field := range fields {
				field = strings.TrimSpace(field)
				if strings.HasPrefix(field, "#") {
					field = strings.TrimPrefix(field, "#")
					field = strings.TrimSpace(field)
				}
				if idx := strings.Index(field, ":"); idx > 0 {
					key := strings.ToLower(strings.TrimSpace(field[:idx]))
					val := strings.TrimSpace(field[idx+1:])
					if key == "node" || key == "station" || key == "type" || key == "token" || key == "time" {
						fd.Metadata[key] = val
					}
				}
			}
			// Still add to lines so content is shown
		}

		if strings.TrimSpace(line) == "END" {
			continue
		}

		fd.Lines = append(fd.Lines, line)

		if idx := strings.Index(line, "="); idx > 0 {
			key := strings.TrimSpace(line[:idx])
			val := strings.TrimSpace(line[idx+1:])
			fd.KeyValues = append(fd.KeyValues, KeyValue{Key: key, Value: val})
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

// ParseAllFiles parses all supported files in a directory (recursive).
func ParseAllFiles(dir string) ([]FileData, error) {
	entries, err := ScanFiles(dir)
	if err != nil {
		return nil, err
	}

	result := make([]FileData, 0, len(entries))
	for _, e := range entries {
		fd, err := ParseFile(e.FilePath)
		if err != nil {
			continue
		}
		fd.StationName = e.StationName
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
