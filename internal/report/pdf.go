package report

import (
	"fmt"
	"strings"
	"time"

	"github.com/falke-ai-circuit/LOGReport/internal/logfile"
	"github.com/jung-kurt/gofpdf"
)

// generatePDF creates a PDF report from log files in the given directory.
// If logRoot is empty, falls back to SQLite-based generation (node + IO points).
// Returns the file path.
func generatePDF(reportID, logRoot string, scanEntries []ScanEntry) (string, error) {
	filePath := outputPath(reportID, ".pdf")

	pdf := gofpdf.New("P", "mm", "A4", "")
	pdf.SetMargins(15, 20, 15)
	pdf.SetAutoPageBreak(true, 20)
	pdf.AddPage()

	// ─── Title ───────────────────────────────────────────
	pdf.SetFont("Helvetica", "B", 20)
	pdf.Cell(0, 12, "LOGReport - Node Report")
	pdf.Ln(14)

	// Generation metadata
	pdf.SetFont("Helvetica", "", 9)
	pdf.SetTextColor(120, 120, 120)
	pdf.Cell(0, 5, fmt.Sprintf("Generated: %s", time.Now().UTC().Format("2006-01-02 15:04:05 UTC")))
	pdf.Ln(5)
	if logRoot != "" {
		pdf.Cell(0, 5, fmt.Sprintf("Log Root: %s", logRoot))
		pdf.Ln(5)
	}
	pdf.SetTextColor(0, 0, 0)
	pdf.Ln(4)

	// ─── Log File Summary ───────────────────────────────
	if len(scanEntries) > 0 {
		pdf.SetFont("Helvetica", "B", 13)
		pdf.Cell(0, 8, "Log File Summary")
		pdf.Ln(8)

		// Summary table
		pdf.SetFont("Helvetica", "B", 8)
		pdf.SetFillColor(220, 220, 220)
		pdf.Cell(40, 6, "File Name")
		pdf.Cell(25, 6, "Type")
		pdf.Cell(30, 6, "Node")
		pdf.Cell(25, 6, "Entries")
		pdf.Cell(30, 6, "Size (bytes)")
		pdf.Ln(6)
		pdf.SetFillColor(255, 255, 255)

		pdf.SetFont("Helvetica", "", 8)
		for _, e := range scanEntries {
			pdf.Cell(40, 5, e.FileName)
			pdf.Cell(25, 5, strings.ToUpper(e.FileType))
			pdf.Cell(30, 5, e.NodeName)
			pdf.Cell(25, 5, fmt.Sprintf("%d", e.KeyValueCount))
			pdf.Cell(30, 5, fmt.Sprintf("%d", e.Size))
			pdf.Ln(5)
		}
		pdf.Ln(4)
	}

	// ─── File Contents ──────────────────────────────────
	for _, e := range scanEntries {
		if e.Parsed == nil {
			continue
		}
		pdf.AddPage()

		// File header bar
		pdf.SetFont("Helvetica", "B", 12)
		pdf.SetFillColor(200, 210, 240)
		pdf.Cell(0, 8, fmt.Sprintf("  %s  [%s]  ", e.FileName, strings.ToUpper(e.FileType)))
		pdf.Ln(9)
		pdf.SetFillColor(255, 255, 255)

		// Metadata
		pdf.SetFont("Helvetica", "I", 8)
		pdf.SetTextColor(100, 100, 100)
		if e.Parsed.Header != "" {
			pdf.Cell(0, 5, e.Parsed.Header)
			pdf.Ln(5)
		}
		pdf.SetTextColor(0, 0, 0)
		pdf.Ln(2)

		// Key-Value table
		if len(e.Parsed.KeyValues) > 0 {
			pdf.SetFont("Helvetica", "B", 8)
			pdf.SetFillColor(230, 230, 230)
			pdf.CellFormat(80, 6, "Key", "1", 0, "L", true, 0, "")
			pdf.CellFormat(0, 6, "Value", "1", 0, "L", true, 0, "")
			pdf.Ln(6)
			pdf.SetFillColor(255, 255, 255)

			pdf.SetFont("Courier", "", 7)
			for _, kv := range e.Parsed.KeyValues {
				pdf.CellFormat(80, 4.5, truncate(kv.Key, 40), "LR", 0, "L", false, 0, "")
				pdf.CellFormat(0, 4.5, truncate(kv.Value, 60), "LR", 0, "L", false, 0, "")
				pdf.Ln(4.5)
			}
			// Close table border
			pdf.CellFormat(80, 0, "", "T", 0, "L", false, 0, "")
			pdf.CellFormat(0, 0, "", "T", 0, "L", false, 0, "")
			pdf.Ln(2)
		}

		// Raw lines (for .log files or files without key=value)
		if e.FileType == "log" && len(e.Parsed.Lines) > 0 {
			pdf.SetFont("Courier", "", 7)
			pdf.SetTextColor(60, 60, 60)
			for _, line := range e.Parsed.Lines {
				pdf.MultiCell(0, 4, truncate(line, 100), "", "L", false)
			}
			pdf.SetTextColor(0, 0, 0)
		}
	}

	// ─── SQLite fallback data (if no log files) ──────────
	if len(scanEntries) == 0 {
		pdf.SetFont("Helvetica", "I", 10)
		pdf.SetTextColor(150, 150, 150)
		pdf.MultiCell(0, 5, "No log files found in the specified directory. Report contains metadata only.", "", "L", false)
		pdf.SetTextColor(0, 0, 0)
	}

	// Save PDF
	if err := pdf.OutputFileAndClose(filePath); err != nil {
		return "", fmt.Errorf("pdf: write: %w", err)
	}

	return filePath, nil
}

// ScanEntry holds parsed log file data for the report.
type ScanEntry struct {
	FileName      string
	FileType      string
	NodeName      string
	Size          int64
	Parsed        *logfile.FileData
	KeyValueCount int
}

// truncate clips a string to maxLen characters.
func truncate(s string, maxLen int) string {
	if len(s) <= maxLen {
		return s
	}
	return s[:maxLen-3] + "..."
}
