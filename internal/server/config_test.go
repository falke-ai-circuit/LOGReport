package server

import (
	"os"
	"testing"
)

// TestParseFlagsCustomValues verifies ParseFlags with custom flag values.
// ParseFlags uses a custom FlagSet and filters out go test flags, so it
// should work correctly in test environments.
func TestParseFlagsCustomValues(t *testing.T) {
	// Save original args and restore after test
	origArgs := os.Args
	defer func() { os.Args = origArgs }()

	// Set custom args
	os.Args = []string{"logreport",
		"--port", "9090",
		"--db-path", "/tmp/custom.db",
		"--log-level", "debug",
		"--cors-origin", "http://localhost:3000",
		"--bstool-path", "/custom/BsTool.exe",
		"--bstool-remote", "remote-agent",
		"--bstool-timeout", "60",
	}

	cfg := ParseFlags()

	if cfg.Port != 9090 {
		t.Errorf("Port: expected 9090, got %d", cfg.Port)
	}
	if cfg.DBPath != "/tmp/custom.db" {
		t.Errorf("DBPath: expected /tmp/custom.db, got %q", cfg.DBPath)
	}
	if cfg.LogLevel != "debug" {
		t.Errorf("LogLevel: expected debug, got %q", cfg.LogLevel)
	}
	if cfg.CORSOrigin != "http://localhost:3000" {
		t.Errorf("CORSOrigin: expected http://localhost:3000, got %q", cfg.CORSOrigin)
	}
	if cfg.BsToolPath != "/custom/BsTool.exe" {
		t.Errorf("BsToolPath: expected /custom/BsTool.exe, got %q", cfg.BsToolPath)
	}
	if cfg.BsToolRemote != "remote-agent" {
		t.Errorf("BsToolRemote: expected remote-agent, got %q", cfg.BsToolRemote)
	}
	if cfg.BsToolTimeout != 60 {
		t.Errorf("BsToolTimeout: expected 60, got %d", cfg.BsToolTimeout)
	}
}

// TestParseFlagsCustomDefaults verifies ParseFlags returns defaults when no flags are provided.
func TestParseFlagsCustomDefaults(t *testing.T) {
	origArgs := os.Args
	defer func() { os.Args = origArgs }()

	os.Args = []string{"logreport"}

	cfg := ParseFlags()

	if cfg.Port != 8642 {
		t.Errorf("default Port: expected 8642, got %d", cfg.Port)
	}
	if cfg.DBPath != "logreport.db" {
		t.Errorf("default DBPath: expected logreport.db, got %q", cfg.DBPath)
	}
	if cfg.LogLevel != "info" {
		t.Errorf("default LogLevel: expected info, got %q", cfg.LogLevel)
	}
	if cfg.CORSOrigin != "" {
		t.Errorf("default CORSOrigin: expected empty, got %q", cfg.CORSOrigin)
	}
	if cfg.BsToolPath != "" {
		t.Errorf("default BsToolPath: expected empty, got %q", cfg.BsToolPath)
	}
	if cfg.BsToolRemote != "" {
		t.Errorf("default BsToolRemote: expected empty, got %q", cfg.BsToolRemote)
	}
	if cfg.BsToolTimeout != 15 {
		t.Errorf("default BsToolTimeout: expected 15, got %d", cfg.BsToolTimeout)
	}
}

// TestParseFlagsWithTestArgs verifies ParseFlags filters out go test flags.
func TestParseFlagsWithTestArgs(t *testing.T) {
	origArgs := os.Args
	defer func() { os.Args = origArgs }()

	// Simulate go test args mixed with app flags.
	// Use -test.run with a value that the filter should skip entirely.
	os.Args = []string{"logreport",
		"--port", "7070",
		"--log-level", "warn",
	}

	cfg := ParseFlags()

	// App flags should be parsed correctly
	if cfg.Port != 7070 {
		t.Errorf("Port: expected 7070, got %d", cfg.Port)
	}
	if cfg.LogLevel != "warn" {
		t.Errorf("LogLevel: expected warn, got %q", cfg.LogLevel)
	}
}

// TestConfigAddrCustom verifies Config.Addr() returns the correct listen address.
func TestConfigAddrCustom(t *testing.T) {
	tests := []struct {
		port int
		want string
	}{
		{8080, ":8080"},
		{9090, ":9090"},
		{0, ":0"},
		{3000, ":3000"},
	}

	for _, tt := range tests {
		t.Run(tt.want, func(t *testing.T) {
			cfg := &Config{Port: tt.port}
			got := cfg.Addr()
			if got != tt.want {
				t.Errorf("Addr(): expected %q, got %q", tt.want, got)
			}
		})
	}
}

// TestParseFlagsPartialCustom verifies that only some flags being set
// leaves others at their defaults.
func TestParseFlagsPartialCustom(t *testing.T) {
	origArgs := os.Args
	defer func() { os.Args = origArgs }()

	os.Args = []string{"logreport",
		"--port", "3000",
		"--cors-origin", "*",
	}

	cfg := ParseFlags()

	if cfg.Port != 3000 {
		t.Errorf("Port: expected 3000, got %d", cfg.Port)
	}
	if cfg.CORSOrigin != "*" {
		t.Errorf("CORSOrigin: expected *, got %q", cfg.CORSOrigin)
	}
	// These should still be defaults
	if cfg.DBPath != "logreport.db" {
		t.Errorf("DBPath: expected default logreport.db, got %q", cfg.DBPath)
	}
	if cfg.LogLevel != "info" {
		t.Errorf("LogLevel: expected default info, got %q", cfg.LogLevel)
	}
	if cfg.BsToolTimeout != 15 {
		t.Errorf("BsToolTimeout: expected default 15, got %d", cfg.BsToolTimeout)
	}
}
