package processor

import (
	"os"
	"path/filepath"
	"sort"
	"strings"
	"time"
)

// Supported file extensions
var SupportedExtensions = map[string]bool{
	".log": true, ".txt": true, ".text": true,
	".lis": true, ".fbc": true, ".rpc": true,
}

// TypeOrder defines display order for file types in report
var TypeOrder = map[string]int{
	".fbc": 0, ".rpc": 1, ".log": 2, ".lis": 3,
}

type LogFile struct {
	Path      string    `json:"path"`
	Name      string    `json:"name"`
	Ext       string    `json:"ext"`
	Size      int64     `json:"size"`
	ModTime   time.Time `json:"mod_time"`
	Lines     []string  `json:"lines,omitempty"`
}

type FolderGroup struct {
	Name     string    `json:"name"`    // folder name (e.g. "AP01")
	RelPath  string    `json:"rel_path"`
	Files    []LogFile `json:"files"`
}

type ScanResult struct {
	RootPath string        `json:"root_path"`
	Groups   []FolderGroup `json:"groups"`
	Total    int           `json:"total"`
	ScannedAt time.Time   `json:"scanned_at"`
}

// ScanOptions controls line reading behaviour
type ScanOptions struct {
	LineLimit int    // 0 = all lines
	LinesMode string // "first", "last", "range"
	LineStart int
	LineEnd   int
	ReadContent bool // if false, skip reading file contents
}

// Scan walks rootPath and returns grouped log files
func Scan(rootPath string, opts ScanOptions) (*ScanResult, error) {
	result := &ScanResult{
		RootPath:  rootPath,
		ScannedAt: time.Now(),
	}

	groupMap := map[string]*FolderGroup{}

	err := filepath.Walk(rootPath, func(path string, info os.FileInfo, err error) error {
		if err != nil || info.IsDir() {
			return nil
		}
		ext := strings.ToLower(filepath.Ext(info.Name()))
		if !SupportedExtensions[ext] {
			return nil
		}

		rel, _ := filepath.Rel(rootPath, path)
		parts := strings.Split(rel, string(filepath.Separator))
		groupName := "root"
		if len(parts) > 1 {
			groupName = parts[0]
		}

		lf := LogFile{
			Path:    path,
			Name:    info.Name(),
			Ext:     ext,
			Size:    info.Size(),
			ModTime: info.ModTime(),
		}

		if opts.ReadContent {
			lines, err := readLines(path)
			if err == nil {
				lf.Lines = filterLines(lines, opts)
			}
		}

		if _, ok := groupMap[groupName]; !ok {
			rel2, _ := filepath.Rel(rootPath, filepath.Dir(path))
			groupMap[groupName] = &FolderGroup{Name: groupName, RelPath: rel2}
		}
		groupMap[groupName].Files = append(groupMap[groupName].Files, lf)
		result.Total++
		return nil
	})

	if err != nil {
		return nil, err
	}

	// Sort groups alphabetically
	names := make([]string, 0, len(groupMap))
	for k := range groupMap {
		names = append(names, k)
	}
	sort.Strings(names)
	for _, n := range names {
		g := groupMap[n]
		// Sort files within group by type order then name
		sort.Slice(g.Files, func(i, j int) bool {
			oi := TypeOrder[g.Files[i].Ext]
			oj := TypeOrder[g.Files[j].Ext]
			if oi != oj {
				return oi < oj
			}
			return g.Files[i].Name < g.Files[j].Name
		})
		result.Groups = append(result.Groups, *g)
	}
	return result, nil
}

func readLines(path string) ([]string, error) {
	data, err := os.ReadFile(path)
	if err != nil {
		return nil, err
	}
	raw := strings.ReplaceAll(string(data), "\r\n", "\n")
	raw = strings.ReplaceAll(raw, "\r", "\n")
	return strings.Split(strings.TrimRight(raw, "\n"), "\n"), nil
}

func filterLines(lines []string, opts ScanOptions) []string {
	if opts.LineLimit == 0 && opts.LinesMode == "" {
		return lines
	}
	switch opts.LinesMode {
	case "last":
		if opts.LineLimit > 0 && len(lines) > opts.LineLimit {
			return lines[len(lines)-opts.LineLimit:]
		}
	case "range":
		start := opts.LineStart
		end := opts.LineEnd
		if start < 0 { start = 0 }
		if end > len(lines) { end = len(lines) }
		if start < end { return lines[start:end] }
	default: // "first"
		if opts.LineLimit > 0 && len(lines) > opts.LineLimit {
			return lines[:opts.LineLimit]
		}
	}
	return lines
}
