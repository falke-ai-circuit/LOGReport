package server

import (
	"testing"
	"time"
)

func TestGetHealthConnected(t *testing.T) {
	startTime := time.Now().Add(-5 * time.Minute)
	h := GetHealth(true, startTime)

	if h.Status != "ok" {
		t.Errorf("Status: got %q, want ok", h.Status)
	}
	if h.Version != "1.0.0" {
		t.Errorf("Version: got %q, want 1.0.0", h.Version)
	}
	if h.DBStatus != "connected" {
		t.Errorf("DBStatus: got %q, want connected", h.DBStatus)
	}
	if h.Uptime == "" || h.Uptime == "0s" {
		t.Errorf("Uptime: got %q, want non-zero uptime", h.Uptime)
	}
}

func TestGetHealthNilDB(t *testing.T) {
	startTime := time.Now()
	h := GetHealth(false, startTime)

	if h.Status != "degraded" {
		t.Errorf("Status: got %q, want degraded", h.Status)
	}
	if h.DBStatus != "disconnected" {
		t.Errorf("DBStatus: got %q, want disconnected", h.DBStatus)
	}
}

func TestGetHealthEmptyNodes(t *testing.T) {
	startTime := time.Now()
	h := GetHealth(true, startTime)

	if h.Status != "ok" {
		t.Errorf("Status: got %q, want ok", h.Status)
	}
}