package logwriter

import (
	"fmt"
	"os"
	"path/filepath"
	"strings"
	"testing"
)

func TestWriteAndReadLog(t *testing.T) {
	dir := t.TempDir()
	lw := New(dir)

	// Write output
	err := lw.WriteOutput("AP01", "FBC", "162", "FBC agent 162\nPIC 5 6 7 8 sum\n0 AI8 BI8")
	if err != nil {
		t.Fatalf("WriteOutput failed: %v", err)
	}

	// Verify file exists — station-based nesting: {dir}/AP01m/FBC/AP01m_unknown-ip_162.fbc
	path := filepath.Join(dir, "AP01m", "FBC", "AP01m_unknown-ip_162.fbc")
	if _, err := os.Stat(path); err != nil {
		t.Fatalf("expected log file to exist at %s: %v", path, err)
	}

	// Read back
	content, err := lw.ReadLog("AP01", "FBC", "162", "")
	if err != nil {
		t.Fatalf("ReadLog failed: %v", err)
	}
	if !strings.Contains(content, "FBC agent 162") {
		t.Errorf("expected content to contain 'FBC agent 162', got: %s", content)
	}
	if !strings.Contains(content, "PIC 5 6 7") {
		t.Errorf("expected content to contain PIC data, got: %s", content)
	}
}

func TestWriteOutputAppends(t *testing.T) {
	dir := t.TempDir()
	lw := New(dir)

	lw.WriteOutput("AP01", "FBC", "100", "first output")
	lw.WriteOutput("AP01", "FBC", "100", "second output")

	content, _ := lw.ReadLog("AP01", "FBC", "100", "")
	if !strings.Contains(content, "first output") {
		t.Error("expected first output in log")
	}
	if !strings.Contains(content, "second output") {
		t.Error("expected second output in log")
	}
}

func TestListLogs(t *testing.T) {
	dir := t.TempDir()
	lw := New(dir)

	lw.WriteOutput("AP01", "FBC", "162", "fbc data 162")
	lw.WriteOutput("AP01_m2", "FBC", "163", "fbc data 163")
	lw.WriteOutput("AP01", "RPC", "363", "rpc data 363")

	entries, err := lw.ListLogs("AP01")
	if err != nil {
		t.Fatalf("ListLogs failed: %v", err)
	}
	if len(entries) != 3 {
		t.Fatalf("expected 3 log files, got %d", len(entries))
	}

	for _, e := range entries {
		if e.Size <= 0 {
			t.Errorf("expected non-zero size for %s, got %d", e.FileName, e.Size)
		}
	}

	if entries[0].FileName > entries[1].FileName {
		t.Errorf("expected sorted order, got %s before %s", entries[0].FileName, entries[1].FileName)
	}
}

func TestListLogsEmpty(t *testing.T) {
	dir := t.TempDir()
	lw := New(dir)

	entries, err := lw.ListLogs("NonExistentNode")
	if err != nil {
		t.Fatalf("ListLogs for non-existent node should not error: %v", err)
	}
	if entries == nil {
		t.Fatal("expected non-nil entries for non-existent node")
	}
	if len(entries) != 0 {
		t.Errorf("expected 0 entries, got %d", len(entries))
	}
}

func TestReadLogNotFound(t *testing.T) {
	dir := t.TempDir()
	lw := New(dir)

	_, err := lw.ReadLog("NonExistent", "FBC", "999", "")
	if err == nil {
		t.Fatal("expected error for non-existent log file")
	}
}

func TestWriteOutputEmptyNodeName(t *testing.T) {
	dir := t.TempDir()
	lw := New(dir)
	err := lw.WriteOutput("", "FBC", "162", "data")
	if err == nil {
		t.Fatal("expected error for empty node name")
	}
}

func TestLISFilename(t *testing.T) {
	dir := t.TempDir()
	lw := New(dir)

	// LIS tokenID format: "102_exe1" — should produce {station}_{ip}_exe1.lis
	err := lw.WriteOutputWithIP("AL01", "LIS", "102_exe1", "lis frame data", "127.0.0.1")
	if err != nil {
		t.Fatalf("WriteOutputWithIP for LIS failed: %v", err)
	}

	// Expected: {dir}/AL01/LIS/AL01_127-0-0-1_exe1.lis
	path := filepath.Join(dir, "AL01", "LIS", "AL01_127-0-0-1_exe1.lis")
	if _, err := os.Stat(path); err != nil {
		t.Fatalf("expected LIS file at %s: %v", path, err)
	}

	// Verify content
	content, err := lw.ReadLog("AL01", "LIS", "102_exe1", "127.0.0.1")
	if err != nil {
		t.Fatalf("ReadLog for LIS failed: %v", err)
	}
	if !strings.Contains(content, "lis frame data") {
		t.Errorf("expected 'lis frame data' in content, got: %s", content)
	}
}

func TestLISAllExeFiles(t *testing.T) {
	dir := t.TempDir()
	lw := New(dir)

	// Write all 6 exe files for one token
	for exe := 1; exe <= 6; exe++ {
		tokenID := fmt.Sprintf("102_exe%d", exe)
		err := lw.WriteOutputWithIP("AL01", "LIS", tokenID, fmt.Sprintf("frame data exe%d", exe), "127.0.0.1")
		if err != nil {
			t.Fatalf("WriteOutputWithIP for LIS exe%d failed: %v", exe, err)
		}
	}

	// Verify all 6 files exist
	for exe := 1; exe <= 6; exe++ {
		path := filepath.Join(dir, "AL01", "LIS", fmt.Sprintf("AL01_127-0-0-1_exe%d.lis", exe))
		if _, err := os.Stat(path); err != nil {
			t.Errorf("expected exe%d file at %s: %v", exe, path, err)
		}
	}
}

func TestExtractExeNum(t *testing.T) {
	tests := []struct {
		tokenID  string
		expected int
	}{
		{"102_exe1", 1},
		{"102_exe6", 6},
		{"501_exe3", 3},
		{"102", 0},
		{"", 0},
		{"_exe2", 2},
	}
	for _, tt := range tests {
		got := extractExeNum(tt.tokenID)
		if got != tt.expected {
			t.Errorf("extractExeNum(%q) = %d, want %d", tt.tokenID, got, tt.expected)
		}
	}
}