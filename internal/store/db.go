// Package store provides SQLite persistence for LOGReport data.
// It manages nodes, IO points, reports, and templates with schema
// versioning via PRAGMA user_version.
package store

import (
	"database/sql"
	"fmt"

	_ "modernc.org/sqlite"
)

// Store wraps a SQLite database connection and provides CRUD operations
// for nodes, IO points, reports, and templates.
type Store struct {
	db *sql.DB
}

// Open opens a SQLite database at the given path, runs migrations,
// and returns a ready-to-use Store.
func Open(path string) (*Store, error) {
	db, err := sql.Open("sqlite", path+"?_pragma=journal_mode(WAL)&_pragma=foreign_keys(on)")
	if err != nil {
		return nil, fmt.Errorf("store: open %s: %w", path, err)
	}

	// Verify connection
	if err := db.Ping(); err != nil {
		db.Close()
		return nil, fmt.Errorf("store: ping %s: %w", path, err)
	}

	s := &Store{db: db}
	if err := s.Migrate(); err != nil {
		db.Close()
		return nil, fmt.Errorf("store: migrate: %w", err)
	}

	return s, nil
}

// Close closes the underlying database connection.
func (s *Store) Close() error {
	return s.db.Close()
}

// DB returns the underlying *sql.DB for advanced operations.
func (s *Store) DB() *sql.DB {
	return s.db
}

// currentSchemaVersion is the latest schema version this code expects.
const currentSchemaVersion = 1

// Migrate runs schema migrations. It uses PRAGMA user_version to track
// the current schema version and applies migrations incrementally.
func (s *Store) Migrate() error {
	var version int
	err := s.db.QueryRow("PRAGMA user_version").Scan(&version)
	if err != nil {
		return fmt.Errorf("store: read user_version: %w", err)
	}

	if version >= currentSchemaVersion {
		// Still ensure post-v1 tables exist (idempotent)
		if err := s.EnsureProjectsTable(); err != nil {
			return fmt.Errorf("store: ensure projects table: %w", err)
		}
		if err := s.ensureReportColumns(); err != nil {
			return fmt.Errorf("store: ensure report columns: %w", err)
		}
		return nil
	}

	// Migration 0 → 1: initial schema
	if version < 1 {
		if err := s.migrateV1(); err != nil {
			return fmt.Errorf("store: migrate v1: %w", err)
		}
		version = 1
	}

	// Ensure projects table exists (added post-v1, idempotent)
	if err := s.EnsureProjectsTable(); err != nil {
		return fmt.Errorf("store: ensure projects table: %w", err)
	}
	s.ensureReportColumns()

	// Set final version
	_, err = s.db.Exec(fmt.Sprintf("PRAGMA user_version = %d", version))
	if err != nil {
		return fmt.Errorf("store: set user_version: %w", err)
	}

	return nil
}

// migrateV1 creates the initial schema tables.
func (s *Store) migrateV1() error {
	schema := `
	CREATE TABLE IF NOT EXISTS nodes (
		address TEXT PRIMARY KEY,
		name TEXT NOT NULL,
		type TEXT NOT NULL,
		status TEXT NOT NULL DEFAULT 'unknown',
		token_id TEXT,
		port INTEGER DEFAULT 23,
		username TEXT,
		password TEXT,
		last_seen TEXT
	);

	CREATE TABLE IF NOT EXISTS io_points (
		id INTEGER PRIMARY KEY AUTOINCREMENT,
		node_address TEXT NOT NULL REFERENCES nodes(address) ON DELETE CASCADE,
		module_position INTEGER,
		channel_position INTEGER,
		channel_type TEXT,
		module_type TEXT,
		counter_name TEXT,
		counter_value INTEGER
	);

	CREATE TABLE IF NOT EXISTS reports (
		id TEXT PRIMARY KEY,
		node_address TEXT NOT NULL,
		format TEXT NOT NULL,
		template TEXT,
		title TEXT,
		author TEXT,
		status TEXT NOT NULL DEFAULT 'pending',
		file_path TEXT,
		created_at TEXT NOT NULL,
		completed_at TEXT
	);

	CREATE TABLE IF NOT EXISTS templates (
		name TEXT PRIMARY KEY,
		format TEXT NOT NULL,
		content TEXT NOT NULL
	);

	CREATE INDEX IF NOT EXISTS idx_io_points_node ON io_points(node_address);
	CREATE INDEX IF NOT EXISTS idx_reports_node ON reports(node_address);
	CREATE INDEX IF NOT EXISTS idx_reports_status ON reports(status);
	`

	_, err := s.db.Exec(schema)
	return err
}

// ensureReportColumns idempotently adds report_type and project_id columns to the reports table.
func (s *Store) ensureReportColumns() error {
	cols, err := s.db.Query("PRAGMA table_info(reports)")
	if err != nil {
		return err
	}
	defer cols.Close()
	hasReportType := false
	hasProjectID := false
	for cols.Next() {
		var cid int
		var name, ctype string
		var notnull, pk int
		var dflt sql.NullString
		cols.Scan(&cid, &name, &ctype, &notnull, &dflt, &pk)
		if name == "report_type" { hasReportType = true }
		if name == "project_id" { hasProjectID = true }
	}
	if !hasReportType {
		_, err = s.db.Exec("ALTER TABLE reports ADD COLUMN report_type TEXT DEFAULT ''")
		if err != nil { return err }
	}
	if !hasProjectID {
		_, err = s.db.Exec("ALTER TABLE reports ADD COLUMN project_id INTEGER DEFAULT 0")
		if err != nil { return err }
	}
	return nil
}
