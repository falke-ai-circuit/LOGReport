package server

import (
	"testing"
	"time"
)

func TestParseFlagsDefaults(t *testing.T) {
	cfg := ParseFlags()

	if cfg.Port != 8642 {
		t.Errorf("default Port: got %d, want 8642", cfg.Port)
	}
	if cfg.DBPath != "logreport-data" {
		t.Errorf("default DBPath: got %q, want logreport-data", cfg.DBPath)
	}
	if cfg.LogLevel != "info" {
		t.Errorf("default LogLevel: got %q, want info", cfg.LogLevel)
	}
	if cfg.CORSOrigin != "" {
		t.Errorf("default CORSOrigin: got %q, want empty", cfg.CORSOrigin)
	}
}

func TestConfigAddr(t *testing.T) {
	cfg := &Config{Port: 8080}
	addr := cfg.Addr()
	if addr != ":8080" {
		t.Errorf("Addr: got %q, want :8080", addr)
	}

	cfg2 := &Config{Port: 3000}
	if cfg2.Addr() != ":3000" {
		t.Errorf("Addr: got %q, want :3000", cfg2.Addr())
	}

	cfg3 := &Config{Port: 0}
	if cfg3.Addr() != ":0" {
		t.Errorf("Addr: got %q, want :0", cfg3.Addr())
	}
}

func TestFormatUptime(t *testing.T) {
	tests := []struct {
		name     string
		duration time.Duration
		want     string
	}{
		{"sub-second", 500 * time.Millisecond, "0s"},
		{"seconds only", 45 * time.Second, "45s"},
		{"minutes and seconds", 5*time.Minute + 30*time.Second, "5m30s"},
		{"hours minutes seconds", 2*time.Hour + 15*time.Minute + 10*time.Second, "2h15m10s"},
		{"exactly one hour", 1 * time.Hour, "1h0m0s"},
		{"exactly one minute", 1 * time.Minute, "1m0s"},
		{"zero duration", 0, "0s"},
		{"large duration", 48*time.Hour + 30*time.Minute + 45*time.Second, "48h30m45s"},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			got := formatUptime(tt.duration)
			if got != tt.want {
				t.Errorf("formatUptime(%v): got %q, want %q", tt.duration, got, tt.want)
			}
		})
	}
}
