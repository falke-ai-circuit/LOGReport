package report

import (
	"fmt"
	"sort"
	"strings"
	"time"

	"github.com/falke-ai-circuit/LOGReport/internal/logfile"
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

// PDF theme colors matching the Python generator.
var (
	pdfTitleColor       = "#5D3E8E" // Title: Helvetica-Bold 14pt
	pdfSubtitleColor    = "#7A5299" // Subtitle: Helvetica-Bold 12pt
	pdfNodeChapterColor = "#4A148C" // Node chapter: Helvetica-Bold 16pt
	pdfFileHeadingColor = "#6A1B9A" // File subheading: Helvetica-Bold 11pt
)

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
func generatePDF(reportID, logRoot string, scanEntries []ScanEntry) (string, error) {
	filePath := outputPath(reportID, ".pdf")

	pdf := gofpdf.New("P", "mm", "A4", "")
	pdf.SetMargins(20, 20, 20)
	pdf.SetAutoPageBreak(true, 20)
	pdf.AddPage()

	// ─── Table of Contents ───────────────────────────────────────
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
	// First pass: create link placeholders for each node
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

		// Set the link target to this page
		pdf.SetLink(tocLinks[node], -1, pdf.PageNo())

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

			// File subheading
			pdf.SetFont("Helvetica", "B", 11)
			pdf.SetTextColor(headR, headG, headB)
			pdf.Cell(0, 8, fmt.Sprintf("%s File: %s", strings.ToUpper(e.FileType), e.FileName))
			pdf.Ln(9)
			pdf.SetTextColor(0, 0, 0)

			// Body content — Courier 10pt, leading 12, wrapped to 80 chars
			pdf.SetFont("Courier", "", 10)

			// Header line if present
			if e.Parsed.Header != "" {
				for _, line := range wrapLine(e.Parsed.Header, 80) {
					pdf.MultiCell(0, 12, line, "", "L", false)
				}
			}

			// Key-value pairs (FBC/RPC files)
			if len(e.Parsed.KeyValues) > 0 {
				for _, kv := range e.Parsed.KeyValues {
					line := fmt.Sprintf("%s = %s", kv.Key, kv.Value)
					for _, wl := range wrapLine(line, 80) {
						pdf.MultiCell(0, 12, wl, "", "L", false)
					}
				}
			}

			// Raw lines (.log/.lis files or files without key=value)
			if len(e.Parsed.Lines) > 0 && len(e.Parsed.KeyValues) == 0 {
				wrapped := wrapLines(e.Parsed.Lines, 80)
				for _, line := range wrapped {
					pdf.MultiCell(0, 12, line, "", "L", false)
				}
			} else if len(e.Parsed.Lines) > 0 {
				// Files with key-values but also raw lines (e.g. .log with mixed content)
				// Show only lines that aren't key=value pairs
				for _, line := range e.Parsed.Lines {
					if strings.Contains(line, "=") {
						continue
					}
					for _, wl := range wrapLine(line, 80) {
						pdf.MultiCell(0, 12, wl, "", "L", false)
					}
				}
			}

			pdf.Ln(4) // spacer between files
		}

		// Page break after each node (gofpdf AddPage at the start of next iteration handles this;
		// but the last node should also get a clean break — the loop's next AddPage handles it)
	}

	// ─── Empty state ─────────────────────────────────────────────
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