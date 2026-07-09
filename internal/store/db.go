// Package store provides JSON file-based persistence for LOGReport data.
// It manages nodes, IO points, reports, projects, and templates using
// JSON files with atomic writes (write to temp file, then rename).
package store

import (
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"sync"
	"time"

	"github.com/falke-ai-circuit/LOGReport/internal/types"
)

// Store wraps in-memory maps backed by JSON files and provides CRUD
// operations for nodes, IO points, reports, projects, and templates.
type Store struct {
	dataDir   string
	isTemp    bool // true when using a temp directory (for tests)
	mu        sync.RWMutex
	nodes     map[string]*types.Node
	ioPoints  map[string][]types.IOPoint // keyed by node address
	reports   map[string]*types.Report
	templates map[string]*types.Template
	projects  map[int64]*types.Project
	meta      metaFile
}

// metaFile holds the auto-incrementing project ID counter.
type metaFile struct {
	NextProjectID int64 `json:"next_project_id"`
}

// Open creates or opens a data directory at the given path, loads existing
// JSON files, and returns a ready-to-use Store.
//
// If path is ":memory:" or "" (used by tests), a temporary directory is
// created and will be cleaned up on Close().
func Open(path string) (*Store, error) {
	var dataDir string
	var isTemp bool

	if path == "" || path == ":memory:" {
		// Use a temp directory for tests
		tmpDir, err := os.MkdirTemp("", "logreport-json-*")
		if err != nil {
			return nil, fmt.Errorf("store: create temp dir: %w", err)
		}
		dataDir = tmpDir
		isTemp = true
	} else {
		// Resolve to absolute path so the data dir is consistent
		// regardless of the current working directory.
		absDir, err := filepath.Abs(path)
		if err != nil {
			absDir = path
		}
		dataDir = absDir
		if err := os.MkdirAll(dataDir, 0o755); err != nil {
			return nil, fmt.Errorf("store: create data dir %s: %w", dataDir, err)
		}
	}

	s := &Store{
		dataDir:   dataDir,
		isTemp:    isTemp,
		nodes:     make(map[string]*types.Node),
		ioPoints:  make(map[string][]types.IOPoint),
		reports:   make(map[string]*types.Report),
		templates: make(map[string]*types.Template),
		projects:  make(map[int64]*types.Project),
		meta:      metaFile{NextProjectID: 1},
	}

	// Load existing data from disk
	if err := s.loadAll(); err != nil {
		if isTemp {
			os.RemoveAll(dataDir)
		}
		return nil, fmt.Errorf("store: load data: %w", err)
	}

	return s, nil
}

// Close closes the store. If using a temp directory, it cleans up.
func (s *Store) Close() error {
	if s.isTemp && s.dataDir != "" {
		return os.RemoveAll(s.dataDir)
	}
	return nil
}

// Migrate is a no-op for the JSON store — no schema migrations needed.
func (s *Store) Migrate() error {
	return nil
}

// ─── internal: file paths ────────────────────────────────────────

func (s *Store) filePath(name string) string {
	return filepath.Join(s.dataDir, name)
}

func (s *Store) nodesPath() string     { return s.filePath("dia_nodes.json") }
func (s *Store) ioPointsPath() string  { return s.filePath("iopoints.json") }
func (s *Store) reportsPath() string   { return s.filePath("reports.json") }
func (s *Store) templatesPath() string { return s.filePath("templates.json") }
func (s *Store) projectsPath() string  { return s.filePath("projects.json") }
func (s *Store) metaPath() string      { return s.filePath("meta.json") }

// ─── internal: atomic file write ─────────────────────────────────

// writeJSONFile writes data as pretty-printed JSON to a temp file, then
// renames it to the target path. This provides atomic writes.
func writeJSONFile(path string, v interface{}) error {
	data, err := json.MarshalIndent(v, "", "  ")
	if err != nil {
		return fmt.Errorf("marshal: %w", err)
	}

	tmpPath := path + ".tmp"
	if err := os.WriteFile(tmpPath, data, 0o644); err != nil {
		return fmt.Errorf("write temp file: %w", err)
	}

	if err := os.Rename(tmpPath, path); err != nil {
		os.Remove(tmpPath)
		return fmt.Errorf("rename temp file: %w", err)
	}

	return nil
}

// ─── internal: load all data from disk ───────────────────────────

func (s *Store) loadAll() error {
	if err := s.loadJSON(s.nodesPath(), &s.nodes); err != nil {
		return err
	}
	if err := s.loadJSON(s.ioPointsPath(), &s.ioPoints); err != nil {
		return err
	}
	if err := s.loadJSON(s.reportsPath(), &s.reports); err != nil {
		return err
	}
	if err := s.loadJSON(s.templatesPath(), &s.templates); err != nil {
		return err
	}
	if err := s.loadJSON(s.projectsPath(), &s.projects); err != nil {
		return err
	}
	if err := s.loadJSON(s.metaPath(), &s.meta); err != nil {
		return err
	}
	// Ensure meta has a valid counter
	if s.meta.NextProjectID < 1 {
		s.meta.NextProjectID = 1
	}
	return nil
}

// loadJSON reads a JSON file into v. If the file doesn't exist, it silently
// skips (leaving v as-is, which should be pre-initialized).
func (s *Store) loadJSON(path string, v interface{}) error {
	data, err := os.ReadFile(path)
	if err != nil {
		if os.IsNotExist(err) {
			return nil // file doesn't exist yet — that's fine
		}
		return fmt.Errorf("read %s: %w", filepath.Base(path), err)
	}
	if len(data) == 0 {
		return nil
	}
	if err := json.Unmarshal(data, v); err != nil {
		return fmt.Errorf("unmarshal %s: %w", filepath.Base(path), err)
	}
	return nil
}

// ─── internal: persist helpers (must be called with write lock held) ──

func (s *Store) persistNodes() error {
	return writeJSONFile(s.nodesPath(), s.nodes)
}

func (s *Store) persistIOPoints() error {
	return writeJSONFile(s.ioPointsPath(), s.ioPoints)
}

func (s *Store) persistReports() error {
	return writeJSONFile(s.reportsPath(), s.reports)
}

func (s *Store) persistTemplates() error {
	return writeJSONFile(s.templatesPath(), s.templates)
}

func (s *Store) persistProjects() error {
	return writeJSONFile(s.projectsPath(), s.projects)
}

func (s *Store) persistMeta() error {
	return writeJSONFile(s.metaPath(), s.meta)
}

// nowISO returns the current time as an ISO 8601 string.
func nowISO() string {
	return time.Now().Format("2006-01-02T15:04:05Z07:00")
}