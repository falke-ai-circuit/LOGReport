package logwriter

import (
	"os"
	"path/filepath"
	"strings"
	"testing"
)

func TestWriteAndReadLog(t *testing.T) {
	dir := t.TempDir()
	lw := New(dir)

	// Write output
	err := lw.WriteOutput("AP01m", "FBC", "162", "FBC agent 162\nPIC 5 6 7 8 sum\n0 AI8 BI8")
	if err != nil {
		t.Fatalf("WriteOutput failed: %v", err)
	}

	// Verify file exists
	path := filepath.Join(dir, "AP01m", "fbc_162.log")
	if _, err := os.Stat(path); err != nil {
		t.Fatalf("expected log file to exist: %v", err)
	}

	// Read back
	content, err := lw.ReadLog("AP01m", "FBC", "162")
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

	// Write first output
	lw.WriteOutput("AP01", "FBC", "100", "first output")

	// Write second output
	lw.WriteOutput("AP01", "FBC", "100", "second output")

	content, _ := lw.ReadLog("AP01", "FBC", "100")
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

	// Create multiple log files
	lw.WriteOutput("AP01m", "FBC", "162", "fbc data 162")
	lw.WriteOutput("AP01m", "FBC", "163", "fbc data 163")
	lw.WriteOutput("AP01m", "RPC", "363", "rpc data 363")

	entries, err := lw.ListLogs("AP01m")
	if err != nil {
		t.Fatalf("ListLogs failed: %v", err)
	}
	if len(entries) != 3 {
		t.Fatalf("expected 3 log files, got %d", len(entries))
	}

	// Verify all are .log files
	for _, e := range entries {
		if !strings.HasSuffix(e.FileName, ".log") {
			t.Errorf("expected .log extension, got %s", e.FileName)
		}
		if e.Size <= 0 {
			t.Errorf("expected non-zero size for %s, got %d", e.FileName, e.Size)
		}
	}

	// Verify sorted by name
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

	_, err := lw.ReadLog("NonExistent", "FBC", "999")
	if err == nil {
		t.Fatal("expected error for non-existent log file")
	}
}

func TestClearLog(t *testing.T) {
	dir := t.TempDir()
	lw := New(dir)

	lw.WriteOutput("AP01", "FBC", "100", "some data")
	path := filepath.Join(dir, "AP01", "fbc_100.log")

	info, _ := os.Stat(path)
	if info.Size() == 0 {
		t.Fatal("expected non-zero size before clear")
	}

	if err := lw.ClearLog("AP01", "FBC", "100"); err != nil {
		t.Fatalf("ClearLog failed: %v", err)
	}

	info, _ = os.Stat(path)
	if info.Size() != 0 {
		t.Errorf("expected zero size after clear, got %d", info.Size())
	}
}

func TestClearLogNotFound(t *testing.T) {
	dir := t.TempDir()
	lw := New(dir)
	// Should not error for non-existent file
	if err := lw.ClearLog("NonExistent", "FBC", "999"); err != nil {
		t.Errorf("expected no error for clearing non-existent log, got: %v", err)
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

func TestLogRoot(t *testing.T) {
	lw := New("/some/path")
	if lw.LogRoot() != "/some/path" {
		t.Errorf("expected /some/path, got %s", lw.LogRoot())
	}
}
