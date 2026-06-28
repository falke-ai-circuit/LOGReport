package server

import (
	"database/sql"
	"testing"
	"time"

	_ "modernc.org/sqlite"
)

func TestGetHealthConnected(t *testing.T) {
	// Open an in-memory SQLite DB
	db, err := sql.Open("sqlite", ":memory:")
	if err != nil {
		t.Fatalf("sql.Open: %v", err)
	}
	defer db.Close()

	// Create the nodes table so COUNT works
	_, err = db.Exec(`CREATE TABLE nodes (address TEXT PRIMARY KEY, name TEXT, type TEXT, status TEXT)`)
	if err != nil {
		t.Fatalf("create table: %v", err)
	}

	// Insert some nodes
	_, err = db.Exec(`INSERT INTO nodes VALUES ('10.0.0.1', 'node1', 'ACN', 'connected')`)
	if err != nil {
		t.Fatalf("insert: %v", err)
	}
	_, err = db.Exec(`INSERT INTO nodes VALUES ('10.0.0.2', 'node2', 'DIA', 'disconnected')`)
	if err != nil {
		t.Fatalf("insert: %v", err)
	}

	startTime := time.Now().Add(-5 * time.Minute)
	h := GetHealth(db, startTime)

	if h.Status != "ok" {
		t.Errorf("Status: got %q, want ok", h.Status)
	}
	if h.Version != "1.0.0" {
		t.Errorf("Version: got %q, want 1.0.0", h.Version)
	}
	if h.DBStatus != "connected" {
		t.Errorf("DBStatus: got %q, want connected", h.DBStatus)
	}
	if h.NodeCount != 2 {
		t.Errorf("NodeCount: got %d, want 2", h.NodeCount)
	}
	if h.Uptime == "" || h.Uptime == "0s" {
		t.Errorf("Uptime: got %q, want non-zero uptime", h.Uptime)
	}
}

func TestGetHealthNilDB(t *testing.T) {
	startTime := time.Now()
	h := GetHealth(nil, startTime)

	if h.Status != "degraded" {
		t.Errorf("Status: got %q, want degraded", h.Status)
	}
	if h.DBStatus != "disconnected" {
		t.Errorf("DBStatus: got %q, want disconnected", h.DBStatus)
	}
	if h.NodeCount != 0 {
		t.Errorf("NodeCount: got %d, want 0", h.NodeCount)
	}
}

func TestGetHealthDBPingError(t *testing.T) {
	// Open a DB then close it to simulate ping failure
	db, err := sql.Open("sqlite", ":memory:")
	if err != nil {
		t.Fatalf("sql.Open: %v", err)
	}
	db.Close() // close immediately to cause ping failure

	startTime := time.Now()
	h := GetHealth(db, startTime)

	if h.Status != "degraded" {
		t.Errorf("Status: got %q, want degraded", h.Status)
	}
	if h.DBStatus == "connected" {
		t.Errorf("DBStatus should not be connected after close, got %q", h.DBStatus)
	}
}

func TestGetHealthEmptyNodes(t *testing.T) {
	db, err := sql.Open("sqlite", ":memory:")
	if err != nil {
		t.Fatalf("sql.Open: %v", err)
	}
	defer db.Close()

	// Create table but no nodes
	_, err = db.Exec(`CREATE TABLE nodes (address TEXT PRIMARY KEY, name TEXT, type TEXT, status TEXT)`)
	if err != nil {
		t.Fatalf("create table: %v", err)
	}

	startTime := time.Now()
	h := GetHealth(db, startTime)

	if h.Status != "ok" {
		t.Errorf("Status: got %q, want ok", h.Status)
	}
	if h.NodeCount != 0 {
		t.Errorf("NodeCount: got %d, want 0", h.NodeCount)
	}
}
