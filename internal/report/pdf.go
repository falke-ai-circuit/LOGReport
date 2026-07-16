package report

import (
	"fmt"
	"os"
	"path/filepath"
	"sort"
	"strings"
	"time"

	"github.com/falke-ai-circuit/LOGReport/internal/logfile"
	"github.com/falke-ai-circuit/LOGReport/internal/types"
	"github.com/jung-kurt/gofpdf"
)

// fileTypeOrder defines the processing order for file types within each node,
// matching the Python generator's TYPE_ORDER.
var fileTypeOrder = map[string]int{
	"fbc": 0,
	"rpc": 1,
	"log": 2,
	"lis": 3,
}

// hexToRGB parses a #RRGGBB hex color string into r, g, b int values (0-255).
func hexToRGB(hex string) (int, int, int) {
	hex = strings.TrimPrefix(hex, "#")
	if len(hex) != 6 {
		return 0, 0, 0
	}
	var r, g, b int
	fmt.Sscanf(hex, "%02x%02x%02x", &r, &g, &b)
	return r, g, b
}

// PDF theme colors — Valmet green theme.
var (
	pdfTitleColor       = "#008a00" // Title: Valmet green
	pdfSubtitleColor    = "#006100" // Subtitle: darker green
	pdfNodeChapterColor = "#004c00" // Node chapter: dark green
	pdfFileHeadingColor = "#008a00" // File subheading: Valmet green
)

// valmetLogoSVG is a simple Valmet-style logo drawn as PDF vector commands.
// Draws "VALMET" text in green with a decorative line — no external image dependency.
func drawValmetLogo(pdf *gofpdf.Fpdf, x, y, w float64) {
	// Green horizontal bar
	pdf.SetFillColor(0, 138, 0)
	pdf.Rect(x, y, w, 2, "F")
	// "VALMET" text in green
	pdf.SetFont("Helvetica", "B", 22)
	pdf.SetTextColor(0, 138, 0)
	pdf.SetXY(x, y+4)
	pdf.Cell(w, 12, "VALMET")
	pdf.SetTextColor(0, 0, 0)
	// Subtitle
	pdf.SetFont("Helvetica", "", 8)
	pdf.SetTextColor(120, 120, 120)
	pdf.SetXY(x, y+16)
	pdf.Cell(w, 5, "DNA Automation System Report")
	pdf.SetTextColor(0, 0, 0)
}

// applyAppearance fills in defaults for any unset fields.
func applyAppearance(a *types.ReportAppearance) *types.ReportAppearance {
	if a == nil {
		a = &types.ReportAppearance{}
	}
	if a.FontFamily == "" {
		a.FontFamily = "Courier"
	}
	if a.FontSize == 0 {
		a.FontSize = 10
	}
	if a.LineSpacing == 0 {
		a.LineSpacing = 12
	}
	if a.MarginMM == 0 {
		a.MarginMM = 20
	}
	if a.WrapWidth == 0 {
		a.WrapWidth = 80
	}
	if a.IncludeFBC == nil {
		t := true
		a.IncludeFBC = &t
	}
	if a.IncludeRPC == nil {
		t := true
		a.IncludeRPC = &t
	}
	if a.IncludeLOG == nil {
		t := true
		a.IncludeLOG = &t
	}
	if a.IncludeLIS == nil {
		t := true
		a.IncludeLIS = &t
	}
	if a.ShowHeader == nil {
		t := true
		a.ShowHeader = &t
	}
	if a.ShowLogo == nil {
		t := true
		a.ShowLogo = &t
	}
	return a
}

// shouldIncludeType returns true if the given file type should be included
// based on the appearance settings.
func shouldIncludeType(fileType string, a *types.ReportAppearance) bool {
	switch strings.ToLower(fileType) {
	case "fbc":
		return *a.IncludeFBC
	case "rpc":
		return *a.IncludeRPC
	case "log":
		return *a.IncludeLOG
	case "lis", "rsu", "dia":
		return *a.IncludeLIS
	default:
		return true // include unknown types
	}
}

// wrapLine wraps a single line to maxWidth characters, breaking at word
// boundaries when possible and falling back to hard character breaks for
// very long words. Matches Python's textwrap.wrap behavior.
func wrapLine(line string, maxWidth int) []string {
	if len(line) <= maxWidth {
		return []string{line}
	}

	var result []string
	remaining := line
	for len(remaining) > maxWidth {
		// Try to find a space within the last 20 chars of the window
		breakAt := maxWidth
		spaceIdx := strings.LastIndex(remaining[:maxWidth], " ")
		if spaceIdx > 0 && spaceIdx > maxWidth-20 {
			breakAt = spaceIdx
		}

		result = append(result, strings.TrimRight(remaining[:breakAt], " "))
		remaining = strings.TrimLeft(remaining[breakAt:], " ")
	}
	if remaining != "" {
		result = append(result, remaining)
	}
	return result
}

// wrapLines wraps all lines in a slice to maxWidth characters.
func wrapLines(lines []string, maxWidth int) []string {
	var result []string
	for _, line := range lines {
		result = append(result, wrapLine(line, maxWidth)...)
	}
	return result
}

// nodeGroups groups scan entries by node name and sorts nodes alphabetically.
// Within each node, entries are ordered by file type (.fbc → .rpc → .log → .lis).
// Returns a sorted slice of node names and a map of node → ordered entries.
func nodeGroups(entries []ScanEntry) ([]string, map[string][]ScanEntry) {
	byNode := make(map[string][]ScanEntry)
	for _, e := range entries {
		byNode[e.NodeName] = append(byNode[e.NodeName], e)
	}

	// Sort entries within each node by file type order
	for node, files := range byNode {
		sort.SliceStable(files, func(i, j int) bool {
			oi, ok := fileTypeOrder[files[i].FileType]
			if !ok {
				oi = 999
			}
			oj, ok := fileTypeOrder[files[j].FileType]
			if !ok {
				oj = 999
			}
			if oi != oj {
				return oi < oj
			}
			return files[i].FileName < files[j].FileName
		})
		byNode[node] = files
	}

	// Sort node names alphabetically
	nodes := make([]string, 0, len(byNode))
	for n := range byNode {
		nodes = append(nodes, n)
	}
	sort.Strings(nodes)

	return nodes, byNode
}

// generatePDF creates a PDF report matching the Python generator format:
// - Table of Contents (first page, lists all nodes)
// - Node chapters (sorted alphabetically, Helvetica-Bold 16pt, #4A148C)
// - File subheadings (Helvetica-Bold 11pt, #6A1B9A)
// - Body content (Courier 10pt, leading 12, wrapped to 80 chars)
// - Page breaks after each node section
func generatePDF(cfg *types.ReportConfig, reportID, logRoot string, scanEntries []ScanEntry, appearance *types.ReportAppearance) (string, error) {
	filePath := outputPathForConfig(cfg, reportID, ".pdf")
	// Ensure output directory exists
	if dir := filepath.Dir(filePath); dir != "" {
		os.MkdirAll(dir, 0755)
	}
	appearance = applyAppearance(appearance)

	pdf := gofpdf.New("P", "mm", "A4", "")
	pdf.SetMargins(float64(appearance.MarginMM), float64(appearance.MarginMM), float64(appearance.MarginMM))
	pdf.SetAutoPageBreak(true, float64(appearance.MarginMM))
	pdf.AddPage()

	// ─── Valmet Logo on title page ──────────────────────────────
	if *appearance.ShowLogo {
		drawValmetLogo(pdf, float64(appearance.MarginMM), 15, 80)
		pdf.Ln(25) // space after logo
	}

	// ─── Table of Contents ───────────────────────────────────────
	// Filter entries by file type inclusion settings
	filteredEntries := make([]ScanEntry, 0, len(scanEntries))
	for _, e := range scanEntries {
		if shouldIncludeType(e.FileType, appearance) {
			filteredEntries = append(filteredEntries, e)
		}
	}
	scanEntries = filteredEntries

	nodes, byNode := nodeGroups(scanEntries)

	titleR, titleG, titleB := hexToRGB(pdfTitleColor)
	subR, subG, subB := hexToRGB(pdfSubtitleColor)
	chapR, chapG, chapB := hexToRGB(pdfNodeChapterColor)
	headR, headG, headB := hexToRGB(pdfFileHeadingColor)

	// Title
	pdf.SetFont("Helvetica", "B", 14)
	pdf.SetTextColor(titleR, titleG, titleB)
	pdf.Cell(0, 10, "Log Report - Table of Contents")
	pdf.Ln(14)

	// Subtitle metadata
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

	// TOC entries — one per node, with clickable internal links
	tocLinks := make(map[string]int)
	for _, node := range nodes {
		tocLinks[node] = pdf.AddLink()
	}

	for _, node := range nodes {
		pdf.SetFont("Helvetica", "B", 12)
		pdf.SetTextColor(subR, subG, subB)
		link := tocLinks[node]
		pdf.CellFormat(0, 7, fmt.Sprintf("Node: %s", node), "", 1, "L", false, link, "")
		pdf.Ln(7)
	}
	pdf.SetTextColor(0, 0, 0)

	// ─── Node Chapters ───────────────────────────────────────────
	for _, node := range nodes {
		pdf.AddPage()
		pdf.SetLink(tocLinks[node], -1, pdf.PageNo())

		// Page header (if enabled)
		if *appearance.ShowHeader {
			pdf.SetY(8)
			pdf.SetFont("Helvetica", "", 8)
			pdf.SetTextColor(150, 150, 150)
			pdf.Cell(0, 5, fmt.Sprintf("LOGReport — %s | Page %d", node, pdf.PageNo()))
			pdf.Ln(6)
			pdf.SetTextColor(0, 0, 0)
			pdf.SetY(float64(appearance.MarginMM) + 5)
		}

		// Node chapter heading
		pdf.SetFont("Helvetica", "B", 16)
		pdf.SetTextColor(chapR, chapG, chapB)
		pdf.Cell(0, 12, fmt.Sprintf("Node: %s", node))
		pdf.Ln(14)
		pdf.SetTextColor(0, 0, 0)

		// Files for this node (already sorted by type)
		for _, e := range byNode[node] {
			if e.Parsed == nil {
				continue
			}
			if !shouldIncludeType(e.FileType, appearance) {
				continue
			}

			// File subheading
			pdf.SetFont("Helvetica", "B", 11)
			pdf.SetTextColor(headR, headG, headB)
			pdf.Cell(0, 8, fmt.Sprintf("%s File: %s", strings.ToUpper(e.FileType), e.FileName))
			pdf.Ln(9)
			pdf.SetTextColor(0, 0, 0)

			// Body content — configurable font family and size
			pdf.SetFont(appearance.FontFamily, "", float64(appearance.FontSize))
			lineH := float64(appearance.LineSpacing)

			// Header line if present
			if e.Parsed.Header != "" {
				for _, line := range wrapLine(e.Parsed.Header, appearance.WrapWidth) {
					pdf.MultiCell(0, lineH, line, "", "L", false)
				}
			}

			// Key-value pairs (FBC/RPC files)
			if len(e.Parsed.KeyValues) > 0 {
				for _, kv := range e.Parsed.KeyValues {
					line := fmt.Sprintf("%s = %s", kv.Key, kv.Value)
					for _, wl := range wrapLine(line, appearance.WrapWidth) {
						pdf.MultiCell(0, lineH, wl, "", "L", false)
					}
				}
			}

			// Raw lines (.log/.lis files or files without key=value)
			if len(e.Parsed.Lines) > 0 && len(e.Parsed.KeyValues) == 0 {
				wrapped := wrapLines(e.Parsed.Lines, appearance.WrapWidth)
				for _, line := range wrapped {
					pdf.MultiCell(0, lineH, line, "", "L", false)
				}
			} else if len(e.Parsed.Lines) > 0 {
				for _, line := range e.Parsed.Lines {
					if strings.Contains(line, "=") {
						continue
					}
					for _, wl := range wrapLine(line, appearance.WrapWidth) {
						pdf.MultiCell(0, lineH, wl, "", "L", false)
					}
				}
			}

			pdf.Ln(4) // spacer between files
		}
	}

	// ─── Empty state ─────────────────────────────────────────────
	if len(scanEntries) == 0 {
		pdf.SetFont("Helvetica", "I", 10)
		pdf.SetTextColor(150, 150, 150)
		pdf.MultiCell(0, 5, "No log files found in the specified directory. Report contains metadata only.", "", "L", false)
		pdf.SetTextColor(0, 0, 0)
	}

	// ─── Footer on every page ────────────────────────────────────
	if *appearance.ShowHeader {
		pdf.SetAutoPageBreak(false, float64(appearance.MarginMM)) // disable to prevent infinite page break loop
		for i := 1; i <= pdf.PageNo(); i++ {
			pdf.SetPage(i)
			pdf.SetY(-12)
			pdf.SetFont("Helvetica", "", 8)
			pdf.SetTextColor(150, 150, 150)
			pdf.Cell(0, 5, fmt.Sprintf("Page %d/%d — Generated by LOGReport", i, pdf.PageNo()))
			pdf.SetTextColor(0, 0, 0)
		}
		pdf.SetAutoPageBreak(true, float64(appearance.MarginMM)) // re-enable
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