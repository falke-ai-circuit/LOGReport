package logfile

import (
	"os"
	"path/filepath"
	"testing"
	"time"
)

// ─── LogFile Scanner Tests ────────────────────────────────────────
// Covers: scan empty dir, scan with .fbc files, scan mixed files,
// scan station-nested structure, scan file data, scan no matching files.

func TestScanFilesEmptyDir(t *testing.T) {
	tmpDir := t.TempDir()

	entries, err := ScanFiles(tmpDir)
	if err != nil {
		t.Fatalf("ScanFiles on empty dir: %v", err)
	}
	if len(entries) != 0 {
		t.Errorf("expected 0 entries in empty dir, got %d", len(entries))
	}
}

func TestScanFilesWithFBC(t *testing.T) {
	tmpDir := t.TempDir()
	os.WriteFile(filepath.Join(tmpDir, "AP01_192-168-0-11_162.fbc"), []byte("FBC data"), 0644)
	os.WriteFile(filepath.Join(tmpDir, "BP01_192-168-0-12_164.fbc"), []byte("FBC data 2"), 0644)

	entries, err := ScanFiles(tmpDir)
	if err != nil {
		t.Fatalf("ScanFiles: %v", err)
	}
	if len(entries) != 2 {
		t.Errorf("expected 2 entries, got %d", len(entries))
	}
		for _, e := range entries {
			if e.Extension != ".fbc" {
				t.Errorf("expected .fbc extension, got %s", e.Extension)
			}
			if e.FileType != "fbc" {
				t.Errorf("expected file_type 'fbc', got %s", e.FileType)
			}
			if e.Size <= 0 {
				t.Errorf("expected non-zero size, got %d", e.Size)
			}
		}
}

func TestScanFilesMixed(t *testing.T) {
	tmpDir := t.TempDir()
	os.WriteFile(filepath.Join(tmpDir, "a.fbc"), []byte("fbc"), 0644)
	os.WriteFile(filepath.Join(tmpDir, "b.rpc"), []byte("rpc"), 0644)
	os.WriteFile(filepath.Join(tmpDir, "c.log"), []byte("log"), 0644)
	os.WriteFile(filepath.Join(tmpDir, "d.lis"), []byte("lis"), 0644)
	// Non-matching file should be excluded
	os.WriteFile(filepath.Join(tmpDir, "e.txt"), []byte("txt"), 0644)

	entries, err := ScanFiles(tmpDir)
	if err != nil {
		t.Fatalf("ScanFiles: %v", err)
	}
	if len(entries) != 4 {
		t.Errorf("expected 4 supported entries, got %d", len(entries))
	}

	// Verify all extensions are supported
	for _, e := range entries {
		if !isSupported(e.Extension) {
			t.Errorf("unsupported extension in results: %s", e.Extension)
		}
	}
}

func TestScanFilesStationNested(t *testing.T) {
	tmpDir := t.TempDir()
	// Create station-nested structure: {logRoot}/{station}/{type}/{file}
	stationDir := filepath.Join(tmpDir, "AP01m", "FBC")
	os.MkdirAll(stationDir, 0755)
	os.WriteFile(filepath.Join(stationDir, "AP01_192-168-0-11_162.fbc"), []byte("nested fbc"), 0644)

	// Also _LOG structure
	logDir := filepath.Join(tmpDir, "_LOG", "BP01r", "RPC")
	os.MkdirAll(logDir, 0755)
	os.WriteFile(filepath.Join(logDir, "BP01_192-168-0-12_164.rpc"), []byte("nested rpc"), 0644)

	entries, err := ScanFiles(tmpDir)
	if err != nil {
		t.Fatalf("ScanFiles: %v", err)
	}
	if len(entries) != 2 {
		t.Errorf("expected 2 entries, got %d", len(entries))
	}

	// Verify station names are derived from path
	for _, e := range entries {
		if e.StationName == "" {
			t.Errorf("expected non-empty station name for %s", e.FileName)
		}
		if e.NodeName == "" {
			t.Errorf("expected non-empty node name for %s", e.FileName)
		}
	}
}

func TestParseFile(t *testing.T) {
	tmpDir := t.TempDir()
	filePath := filepath.Join(tmpDir, "test.fbc")
	content := "# FBC AP01 2024-01-15\nPIC 5 6 7\nmodule=0\ntype=AI8\nEND\n"
	os.WriteFile(filePath, []byte(content), 0644)

	fd, err := ParseFile(filePath)
	if err != nil {
		t.Fatalf("ParseFile: %v", err)
	}
	if fd.FileName != "test.fbc" {
		t.Errorf("expected FileName test.fbc, got %s", fd.FileName)
	}
	if fd.FileType != "fbc" {
		t.Errorf("expected FileType fbc, got %s", fd.FileType)
	}
	if fd.Header != "# FBC AP01 2024-01-15" {
		t.Errorf("expected header to be first line, got %q", fd.Header)
	}
	// Verify metadata parsed from header
	// strings.Fields splits "# FBC AP01..." → ["#", "FBC", "AP01", "2024-01-15"]
	// Metadata["type"] = TrimPrefix("#", "#") = "" (empty)
	// Metadata["node"] = "FBC" (second field)
	if fd.Metadata["node"] != "FBC" {
		t.Errorf("expected metadata node FBC, got %q", fd.Metadata["node"])
	}
	// Verify lines (excluding header and END)
	if len(fd.Lines) != 3 {
		t.Errorf("expected 3 lines (excluding header and END), got %d", len(fd.Lines))
	}
	// Verify key-values parsed
	if len(fd.KeyValues) != 2 {
		t.Errorf("expected 2 key_values, got %d", len(fd.KeyValues))
	}
}

func TestParseFileNonExistent(t *testing.T) {
	_, err := ParseFile("/nonexistent/file.fbc")
	if err == nil {
		t.Error("expected error for non-existent file")
	}
}

func TestScanFilesNoMatchingFiles(t *testing.T) {
	tmpDir := t.TempDir()
	// Only unsupported files
	os.WriteFile(filepath.Join(tmpDir, "a.txt"), []byte("text"), 0644)
	os.WriteFile(filepath.Join(tmpDir, "b.csv"), []byte("csv"), 0644)
	os.WriteFile(filepath.Join(tmpDir, "c.json"), []byte("json"), 0644)

	entries, err := ScanFiles(tmpDir)
	if err != nil {
		t.Fatalf("ScanFiles: %v", err)
	}
	if len(entries) != 0 {
		t.Errorf("expected 0 entries for non-matching files, got %d", len(entries))
	}
}

func TestScanFilesNonExistentDir(t *testing.T) {
	entries, err := ScanFiles("/nonexistent/path/12345")
	if err != nil {
		t.Fatalf("ScanFiles on non-existent dir should not error: %v", err)
	}
	if len(entries) != 0 {
		t.Errorf("expected 0 entries for non-existent dir, got %d", len(entries))
	}
}

func TestScanFilesByType(t *testing.T) {
	tmpDir := t.TempDir()
	os.WriteFile(filepath.Join(tmpDir, "a.fbc"), []byte("fbc"), 0644)
	os.WriteFile(filepath.Join(tmpDir, "b.rpc"), []byte("rpc"), 0644)
	os.WriteFile(filepath.Join(tmpDir, "c.log"), []byte("log"), 0644)

	t.Run("filter by fbc", func(t *testing.T) {
		entries, err := ScanFilesByType(tmpDir, "fbc")
		if err != nil {
			t.Fatalf("ScanFilesByType: %v", err)
		}
		if len(entries) != 1 {
			t.Errorf("expected 1 fbc entry, got %d", len(entries))
		}
		if entries[0].Extension != ".fbc" {
			t.Errorf("expected .fbc, got %s", entries[0].Extension)
		}
	})

	t.Run("filter by rpc with dot prefix", func(t *testing.T) {
		entries, err := ScanFilesByType(tmpDir, ".rpc")
		if err != nil {
			t.Fatalf("ScanFilesByType: %v", err)
		}
		if len(entries) != 1 {
			t.Errorf("expected 1 rpc entry, got %d", len(entries))
		}
	})

	t.Run("filter by empty ext returns all", func(t *testing.T) {
		entries, err := ScanFilesByType(tmpDir, "")
		if err != nil {
			t.Fatalf("ScanFilesByType: %v", err)
		}
		if len(entries) != 3 {
			t.Errorf("expected 3 entries with empty filter, got %d", len(entries))
		}
	})
}

func TestScanFilesModifiedAt(t *testing.T) {
	tmpDir := t.TempDir()
	filePath := filepath.Join(tmpDir, "test.fbc")
	before := time.Now().Add(-time.Second)
	os.WriteFile(filePath, []byte("data"), 0644)
	after := time.Now().Add(time.Second)

	entries, err := ScanFiles(tmpDir)
	if err != nil {
		t.Fatalf("ScanFiles: %v", err)
	}
	if len(entries) != 1 {
		t.Fatalf("expected 1 entry, got %d", len(entries))
	}
	if entries[0].ModifiedAt.Before(before) || entries[0].ModifiedAt.After(after) {
		t.Errorf("ModifiedAt %v not in expected range [%v, %v]", entries[0].ModifiedAt, before, after)
	}
}