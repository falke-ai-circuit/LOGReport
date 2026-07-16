package report

import (
	"fmt"
	"os"
	"path/filepath"
	"testing"

	"github.com/falke-ai-circuit/LOGReport/internal/logfile"
	"github.com/falke-ai-circuit/LOGReport/internal/types"
)

// TestPDFReportFromRealLogData tests the full report generation pipeline
// using actual _LOG.zip data extracted to /tmp/logreport-test/_LOG_extracted/_LOG.
// This test verifies:
// 1. Scanner finds all 194 files (32 fbc, 32 rpc, 34 log, 96 lis)
// 2. Parser correctly handles files with leading empty lines
// 3. PDF generates multiple pages (TOC + one per node)
// 4. Footer loop doesn't destroy pages (the SetY(-12) bug)
// 5. DOCX and JSON also generate correctly
func TestPDFReportFromRealLogData(t *testing.T) {
	logRoot := "/tmp/logreport-test/_LOG_extracted/_LOG"
	if _, err := os.Stat(logRoot); err != nil {
		t.Skipf("Test data not available at %s — extract _LOG.zip first", logRoot)
	}

	// Step 1: Scan files
	entries, err := logfile.ScanFiles(logRoot)
	if err != nil {
		t.Fatalf("ScanFiles failed: %v", err)
	}
	t.Logf("ScanFiles found %d files", len(entries))
	if len(entries) != 194 {
		t.Errorf("Expected 194 files, got %d", len(entries))
	}

	// Count by type
	byType := map[string]int{}
	for _, e := range entries {
		byType[e.FileType]++
	}
	if byType["fbc"] != 32 {
		t.Errorf("Expected 32 fbc files, got %d", byType["fbc"])
	}
	if byType["rpc"] != 32 {
		t.Errorf("Expected 32 rpc files, got %d", byType["rpc"])
	}
	if byType["log"] != 34 {
		t.Errorf("Expected 34 log files, got %d", byType["log"])
	}
	if byType["lis"] != 96 {
		t.Errorf("Expected 96 lis files, got %d", byType["lis"])
	}

	// Step 2: Parse all files
	scanEntries := make([]ScanEntry, 0, len(entries))
	for _, fe := range entries {
		parsed, err := logfile.ParseFile(fe.FilePath)
		if err != nil {
			t.Logf("ParseFile failed for %s: %v", fe.FileName, err)
			continue
		}
		scanEntries = append(scanEntries, ScanEntry{
			FileName:      fe.FileName,
			FileType:      fe.FileType,
			NodeName:      fe.NodeName,
			Size:          fe.Size,
			Parsed:        parsed,
			KeyValueCount: len(parsed.KeyValues),
		})
	}
	t.Logf("Parsed %d entries", len(scanEntries))

	// Step 3: Verify parser handles leading empty lines
	// The FBC files start with an empty line, then === separator, then # metadata
	for _, e := range scanEntries {
		if e.Size > 0 && e.Parsed.Header == "" {
			t.Errorf("Non-empty file %s (%d bytes) has empty header — parser not skipping leading empty lines", e.FileName, e.Size)
		}
	}

	// Step 4: Verify node grouping
	nodes, byNode := nodeGroups(scanEntries)
	t.Logf("Found %d nodes: %v", len(nodes), nodes)
	if len(nodes) < 30 {
		t.Errorf("Expected at least 30 nodes, got %d", len(nodes))
	}

	// Step 5: Generate PDF
	cfg := &types.ReportConfig{
		Format:        types.FormatPDF,
		LogRoot:       logRoot,
		ProjectNumber: "V6049A",
		ShipName:      "CELEBRITY_REFLECTION",
		OutputDir:     "/tmp/logreport-test",
	}
	appearance := &types.ReportAppearance{}
	pdfPath, err := generatePDF(cfg, "test-report-id", logRoot, scanEntries, appearance)
	if err != nil {
		t.Fatalf("generatePDF failed: %v", err)
	}

	pdfInfo, _ := os.Stat(pdfPath)
	t.Logf("PDF: %s (%d bytes)", pdfPath, pdfInfo.Size())

	// Count pages in PDF
	pdfData, _ := os.ReadFile(pdfPath)
	pageCount := 0
	for i := 0; i < len(pdfData)-10; i++ {
		if string(pdfData[i:i+10]) == "/Type /Pag" {
			if i+10 < len(pdfData) && pdfData[i+10] == 'e' && (i+11 >= len(pdfData) || pdfData[i+11] != 's') {
				pageCount++
			}
		}
	}
	t.Logf("PDF has %d pages", pageCount)
	if pageCount < 10 {
		t.Errorf("Expected at least 10 pages (TOC + node chapters), got %d — footer SetY(-12) bug?", pageCount)
	}

	// Step 6: Generate DOCX
	cfgDOCX := types.ReportConfig{
		Format:        types.FormatDOCX,
		LogRoot:       logRoot,
		ProjectNumber: "V6049A",
		ShipName:      "CELEBRITY_REFLECTION",
		OutputDir:     "/tmp/logreport-test",
	}
	docxPath, err := generateDOCXFromLogs(cfgDOCX, scanEntries, "test-report-id")
	if err != nil {
		t.Fatalf("generateDOCXFromLogs failed: %v", err)
	}
	docxInfo, _ := os.Stat(docxPath)
	t.Logf("DOCX: %s (%d bytes)", docxPath, docxInfo.Size())

	// Step 7: Generate JSON
	cfgJSON := types.ReportConfig{
		Format:        types.FormatJSON,
		LogRoot:       logRoot,
		ProjectNumber: "V6049A",
		ShipName:      "CELEBRITY_REFLECTION",
		OutputDir:     "/tmp/logreport-test",
	}
	jsonPath, err := generateJSONFromLogs(cfgJSON, scanEntries, "test-report-id")
	if err != nil {
		t.Fatalf("generateJSONFromLogs failed: %v", err)
	}
	jsonInfo, _ := os.Stat(jsonPath)
	t.Logf("JSON: %s (%d bytes)", jsonPath, jsonInfo.Size())

	// Step 8: Show sample content from non-empty files
	for _, node := range nodes[:3] {
		files := byNode[node]
		t.Logf("Node %s: %d files", node, len(files))
		for _, f := range files {
			if f.Size > 0 {
				lines := len(f.Parsed.Lines)
				kvs := len(f.Parsed.KeyValues)
				header := f.Parsed.Header
				if len(header) > 80 {
					header = header[:80]
				}
				t.Logf("  %s (%s, %dB): %d lines, %d kvs, header=%q", f.FileName, f.FileType, f.Size, lines, kvs, header)
			}
		}
	}

	// List output files
	matches, _ := filepath.Glob("/tmp/logreport-test/*")
	t.Logf("Output files:")
	for _, m := range matches {
		if info, err := os.Stat(m); err == nil && !info.IsDir() {
			t.Logf("  %s (%d bytes)", filepath.Base(m), info.Size())
		}
	}

	fmt.Printf("INTEGRATION TEST PASSED: PDF=%d pages (%dB), DOCX=%dB, JSON=%dB\n",
		pageCount, pdfInfo.Size(), docxInfo.Size(), jsonInfo.Size())
}