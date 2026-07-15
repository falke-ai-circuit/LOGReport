// Package report generates DOCX and JSON reports from node data
// stored in the LOGReport SQLite database.
package report

import (
	"archive/zip"
	"bytes"
	"crypto/rand"
	"encoding/json"
	"fmt"
	"log"
	"os"
	"path/filepath"
	"strings"
	"time"

	"github.com/falke-ai-circuit/LOGReport/internal/logfile"
	"github.com/falke-ai-circuit/LOGReport/internal/store"
	"github.com/falke-ai-circuit/LOGReport/internal/types"
)

// DefaultOutputDir is the default directory for generated reports.
var DefaultOutputDir = filepath.Join(os.TempDir(), "logreport-reports")

// GenerateReport loads node and IO point data from the store, generates
// a report in the specified format, and returns a Report record with
// the file path and completed status.
func GenerateReport(cfg types.ReportConfig, s *store.Store) (*types.Report, error) {
	// Validate format
	if cfg.Format != types.FormatDOCX && cfg.Format != types.FormatJSON && cfg.Format != types.FormatPDF {
		return nil, fmt.Errorf("report: unsupported format %q", cfg.Format)
	}

	// PDF/DOCX/JSON with log_root: generate from log files (no SQLite data needed)
	if (cfg.Format == types.FormatPDF || cfg.Format == types.FormatDOCX || cfg.Format == types.FormatJSON) && cfg.LogRoot != "" {
		return generateFromLogs(cfg, s)
	}

	// Load node from store
	node, err := s.GetNode(cfg.NodeAddress)
	if err != nil {
		return nil, fmt.Errorf("report: load node %s: %w", cfg.NodeAddress, err)
	}

	// Load IO points from store
	ioPoints, err := s.GetIOPoints(cfg.NodeAddress)
	if err != nil {
		return nil, fmt.Errorf("report: load io points for %s: %w", cfg.NodeAddress, err)
	}

	// Load template if specified. "default" is a soft default — if not
	// found in the store, fall through with nil (use built-in title).
	var tmpl *types.Template
	if cfg.Template != "" {
		tmpl, err = s.GetTemplate(cfg.Template)
		if err != nil {
			if cfg.Template == "default" {
				// No default template seeded — use built-in title, not an error.
				tmpl = nil
			} else {
				return nil, fmt.Errorf("report: load template %s: %w", cfg.Template, err)
			}
		}
	}

	// Ensure output directory exists
	if err := os.MkdirAll(DefaultOutputDir, 0755); err != nil {
		return nil, fmt.Errorf("report: create output dir: %w", err)
	}

	// Generate report file
	var filePath string
	now := time.Now().UTC()
	reportID := newReportID()

	switch cfg.Format {
	case types.FormatDOCX:
		filePath, err = generateDOCX(node, ioPoints, tmpl, reportID)
	case types.FormatJSON:
		filePath, err = generateJSON(node, ioPoints, reportID)
	case types.FormatPDF:
		// PDF without log_root: generate from SQLite data
		scanEntries := ioPointsToScanEntries(node, ioPoints)
		filePath, err = generatePDF(reportID, "", scanEntries, cfg.Appearance)
	}
	if err != nil {
		return nil, fmt.Errorf("report: generate %s: %w", cfg.Format, err)
	}

	// Build report record
	report := &types.Report{
		ID:          reportID,
		ReportType:  cfg.ReportType,
		ProjectID:   cfg.ProjectID,
		NodeAddress: cfg.NodeAddress,
		Format:      cfg.Format,
		Template:    cfg.Template,
		Title:       cfg.Title,
		Author:      cfg.Author,
		Status:      types.StatusCompleted,
		FilePath:    filePath,
		CreatedAt:   now.Format(time.RFC3339),
		CompletedAt: now.Format(time.RFC3339),
	}

	// Save report to store
	if err := s.SaveReport(report); err != nil {
		return nil, fmt.Errorf("report: save report: %w", err)
	}

	return report, nil
}

// generateFromLogs scans the log_root directory for log files and generates
// a PDF or DOCX report from their contents, depending on cfg.Format.
func generateFromLogs(cfg types.ReportConfig, s *store.Store) (*types.Report, error) {
	// Ensure output directory exists
	if err := os.MkdirAll(DefaultOutputDir, 0755); err != nil {
		return nil, fmt.Errorf("report: create output dir: %w", err)
	}

	// Scan log files from log_root
	allFiles, err := logfile.ScanFiles(cfg.LogRoot)
	if err != nil {
		return nil, fmt.Errorf("report: scan log root %s: %w", cfg.LogRoot, err)
	}

	// If node_address specified, filter files by node name
	if cfg.NodeAddress != "" && cfg.NodeAddress != "*" {
		filtered := make([]logfile.FileEntry, 0)
		for _, f := range allFiles {
			if f.NodeName == cfg.NodeAddress {
				filtered = append(filtered, f)
			}
		}
		allFiles = filtered
	}

	// Parse each file
	scanEntries := make([]ScanEntry, 0, len(allFiles))
	for _, fe := range allFiles {
		parsed, err := logfile.ParseFile(fe.FilePath)
		if err != nil {
			continue
		}
		scanEntries = append(scanEntries, ScanEntry{
			FileName:      fe.FileName,
			FileType:      strings.TrimPrefix(fe.Extension, "."),
			NodeName:      fe.NodeName,
			Size:          fe.Size,
			Parsed:        parsed,
			KeyValueCount: len(parsed.KeyValues),
		})
	}

	now := time.Now().UTC()
	reportID := newReportID()

	var filePath string
	switch cfg.Format {
	case types.FormatDOCX:
		filePath, err = generateDOCXFromLogs(cfg, scanEntries, reportID)
	case types.FormatPDF:
		filePath, err = generatePDF(reportID, cfg.LogRoot, scanEntries, cfg.Appearance)
	case types.FormatJSON:
		filePath, err = generateJSONFromLogs(cfg, scanEntries, reportID)
	default:
		return nil, fmt.Errorf("report: unsupported log-root format %q", cfg.Format)
	}
	if err != nil {
		return nil, fmt.Errorf("report: generate %s: %w", cfg.Format, err)
	}

	// Build report record — use log_root or first node name as node address
	nodeAddr := cfg.NodeAddress
	if nodeAddr == "" || nodeAddr == "*" {
		if len(scanEntries) > 0 {
			nodeAddr = scanEntries[0].NodeName
		} else {
			nodeAddr = "all"
		}
	}

	report := &types.Report{
		ID:          reportID,
		ReportType:  cfg.ReportType,
		ProjectID:   cfg.ProjectID,
		NodeAddress: nodeAddr,
		Format:      cfg.Format,
		Template:    cfg.Template,
		Title:       cfg.Title,
		Author:      cfg.Author,
		Status:      types.StatusCompleted,
		FilePath:    filePath,
		CreatedAt:   now.Format(time.RFC3339),
		CompletedAt: now.Format(time.RFC3339),
	}

	if err := s.SaveReport(report); err != nil {
		// Log but don't fail — the report file was generated successfully
		log.Printf("report: save report to store failed (non-fatal): %v", err)
	}

	return report, nil
}

// generateDOCXFromLogs creates a DOCX report matching the Python generator format:
// - Title page with Table of Contents listing all nodes
// - Node headings (Arial, bold) sorted alphabetically
// - File subheadings within each node, ordered .fbc → .rpc → .log → .lis
// - Body content in Courier New, wrapped to 80 chars
// - Page breaks after each node section
func generateDOCXFromLogs(cfg types.ReportConfig, scanEntries []ScanEntry, reportID string) (string, error) {
	filePath := outputPath(reportID, ".docx")

	var buf bytes.Buffer
	zw := zip.NewWriter(&buf)

	// [Content_Types].xml
	contentTypes := `<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
  <Override PartName="/word/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/>
</Types>`
	writeZipEntry(zw, "[Content_Types].xml", contentTypes)

	// _rels/.rels
	rels := `<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>
</Relationships>`
	writeZipEntry(zw, "_rels/.rels", rels)

	// word/_rels/document.xml.rels — link to styles.xml
	docRels := `<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>
</Relationships>`
	writeZipEntry(zw, "word/_rels/document.xml.rels", docRels)

	// Build document XML
	var sb strings.Builder
	sb.WriteString(`<?xml version="1.0" encoding="UTF-8" standalone="yes"?>`)
	sb.WriteString(`<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">`)
	sb.WriteString(`<w:body>`)

	// ─── Title ───────────────────────────────────────────────────
	titleText := "Log Report - Node Overview"
	if cfg.Title != "" {
		titleText = cfg.Title
	}
	sb.WriteString(docxParagraph(titleText, docxFontArial, true, 28)) // 14pt = 28 half-points
	sb.WriteString(docxParagraph("", "", false, 0))

	// Metadata
	if cfg.LogRoot != "" {
		sb.WriteString(docxParagraph(boldText("Log Root: ")+xmlEscape(cfg.LogRoot), docxFontCourierNew, false, 0))
	}
	sb.WriteString(docxParagraph(boldText("Generated: ")+time.Now().UTC().Format("2006-01-02 15:04:05 UTC"), docxFontCourierNew, false, 0))
	sb.WriteString(docxParagraph("", "", false, 0))

	// ─── Table of Contents ───────────────────────────────────────
	// Use Word TOC field — auto-generates clickable TOC when opened in Word
	sb.WriteString(`<w:p><w:pPr><w:pStyle w:val="Heading1"/></w:pPr><w:r><w:t xml:space="preserve">Table of Contents</w:t></w:r></w:p>`)
	// TOC field — Word auto-generates from Heading1 styles on open
	sb.WriteString(`<w:p><w:r><w:fldChar w:fldCharType="begin"/></w:r>`)
	sb.WriteString(`<w:r><w:instrText xml:space="preserve"> TOC \o "1-1" \h \z </instrText></w:r>`)
	sb.WriteString(`<w:r><w:fldChar w:fldCharType="separate"/></w:r>`)
	sb.WriteString(`<w:r><w:t xml:space="preserve">Right-click and select "Update Field" to generate the table of contents.</w:t></w:r>`)
	sb.WriteString(`<w:r><w:fldChar w:fldCharType="end"/></w:r></w:p>`)
	sb.WriteString(docxParagraph("", "", false, 0))

	nodes, byNode := nodeGroups(scanEntries)

	// Page break after TOC
	sb.WriteString(docxPageBreak())

	// ─── Node Chapters ───────────────────────────────────────────
	for i, node := range nodes {
		// Node heading with Word Heading1 style + bookmark for TOC navigation
		bookmarkID := fmt.Sprintf("node_%d", i)
		sb.WriteString(`<w:bookmarkStart w:id="` + fmt.Sprintf("%d", i) + `" w:name="` + bookmarkID + `"/>`)
		sb.WriteString(`<w:p><w:pPr><w:pStyle w:val="Heading1"/></w:pPr><w:r><w:t xml:space="preserve">Node: ` + xmlEscape(node) + `</w:t></w:r></w:p>`)
		sb.WriteString(`<w:bookmarkEnd w:id="` + fmt.Sprintf("%d", i) + `"/>`)
		sb.WriteString(docxParagraph("", "", false, 0))

		// Files for this node (already sorted by type)
		for _, e := range byNode[node] {
			if e.Parsed == nil {
				continue
			}

			// File subheading (Arial, bold, 11pt = 22 half-points)
			sb.WriteString(docxParagraph(
				fmt.Sprintf("%s File: %s", strings.ToUpper(e.FileType), e.FileName),
				docxFontArial, true, 22))
			sb.WriteString(docxParagraph("", "", false, 0))

			// Body content — Courier New 10pt (20 half-points), wrapped to 80 chars
			if e.Parsed.Header != "" {
				for _, line := range wrapLine(e.Parsed.Header, 80) {
					sb.WriteString(docxParagraph(xmlEscape(line), docxFontCourierNew, false, 20))
				}
			}

			if len(e.Parsed.KeyValues) > 0 {
				for _, kv := range e.Parsed.KeyValues {
					line := fmt.Sprintf("%s = %s", kv.Key, kv.Value)
					for _, wl := range wrapLine(line, 80) {
						sb.WriteString(docxParagraph(xmlEscape(wl), docxFontCourierNew, false, 20))
					}
				}
			}

			if len(e.Parsed.Lines) > 0 && len(e.Parsed.KeyValues) == 0 {
				wrapped := wrapLines(e.Parsed.Lines, 80)
				for _, line := range wrapped {
					sb.WriteString(docxParagraph(xmlEscape(line), docxFontCourierNew, false, 20))
				}
			} else if len(e.Parsed.Lines) > 0 {
				for _, line := range e.Parsed.Lines {
					if strings.Contains(line, "=") {
						continue
					}
					for _, wl := range wrapLine(line, 80) {
						sb.WriteString(docxParagraph(xmlEscape(wl), docxFontCourierNew, false, 20))
					}
				}
			}

			sb.WriteString(docxParagraph("", "", false, 0))
		}

		// Page break after each node section
		sb.WriteString(docxPageBreak())
	}

	// Empty state
	if len(scanEntries) == 0 {
		sb.WriteString(docxParagraph("(No log files found in the specified directory.)", docxFontCourierNew, false, 20))
	}

	sb.WriteString(`</w:body></w:document>`)
	writeZipEntry(zw, "word/document.xml", sb.String())

	// word/styles.xml — define Heading1 style for TOC navigation
	stylesXML := `<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:styles xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:style w:type="paragraph" w:styleId="Heading1">
    <w:name w:val="heading 1"/>
    <w:basedOn w:val="Normal"/>
    <w:next w:val="Normal"/>
    <w:pPr>
      <w:keepNext/>
      <w:spacing w:before="240" w:after="60"/>
      <w:outlineLvl w:val="0"/>
    </w:pPr>
    <w:rPr>
      <w:rFonts w:ascii="Arial" w:hAnsi="Arial"/>
      <w:b/>
      <w:bCs/>
      <w:sz w:val="32"/>
      <w:szCs w:val="32"/>
      <w:color w:val="4A148C"/>
    </w:rPr>
  </w:style>
  <w:style w:type="paragraph" w:default="1" w:styleId="Normal">
    <w:name w:val="Normal"/>
    <w:pPr><w:spacing w:after="160" w:line="259" w:lineRule="auto"/></w:pPr>
    <w:rPr><w:sz w:val="22"/><w:szCs w:val="22"/></w:rPr>
  </w:style>
</w:styles>`
	writeZipEntry(zw, "word/styles.xml", stylesXML)

	// Update content types to include styles.xml
	// (already written above, but we need to add the styles override)

	if err := zw.Close(); err != nil {
		return "", fmt.Errorf("docx: close zip: %w", err)
	}

	if err := os.WriteFile(filePath, buf.Bytes(), 0644); err != nil {
		return "", fmt.Errorf("docx: write: %w", err)
	}

	return filePath, nil
}

// docxFont identifiers for the enhanced DOCX generator.
const (
	docxFontArial      = "Arial"
	docxFontCourierNew = "Courier New"
)

// docxParagraph returns a w:p element with specified font, bold, and size.
// sz is in half-points (0 = default).
func docxParagraph(text, font string, bold bool, sz int) string {
	if text == "" {
		return `<w:p><w:r><w:t xml:space="preserve"> </w:t></w:r></w:p>`
	}

	rPr := `<w:rPr>`
	if bold {
		rPr += `<w:b/><w:bCs/>`
	}
	if font != "" {
		rPr += fmt.Sprintf(`<w:rFonts w:ascii="%s" w:hAnsi="%s" w:cs="%s"/>`, font, font, font)
	}
	if sz > 0 {
		rPr += fmt.Sprintf(`<w:sz w:val="%d"/><w:szCs w:val="%d"/>`, sz, sz)
	}
	rPr += `</w:rPr>`

	return fmt.Sprintf(`<w:p><w:r>%s<w:t xml:space="preserve">%s</w:t></w:r></w:p>`, rPr, xmlEscape(text))
}

// docxPageBreak returns a w:p element containing a page break.
func docxPageBreak() string {
	return `<w:p><w:r><w:br w:type="page"/></w:r></w:p>`
}

// outputPath builds the full output file path for a report.
func outputPath(reportID string, ext string) string {
	return filepath.Join(DefaultOutputDir, reportID+ext)
}

// newReportID generates a random hex report ID.
func newReportID() string {
	b := make([]byte, 16)
	rand.Read(b)
	return fmt.Sprintf("%x", b)
}

// ioPointsToScanEntries converts SQLite IO points to ScanEntry format for
// PDF generation (fallback when no log_root is specified).
func ioPointsToScanEntries(node *types.Node, ioPoints []types.IOPoint) []ScanEntry {
	entries := make([]ScanEntry, 0)

	// Group by module type
	fbcKVs := make([]logfile.KeyValue, 0)
	rpcKVs := make([]logfile.KeyValue, 0)
	for _, p := range ioPoints {
		if p.ModuleType == types.ModuleFBC {
			fbcKVs = append(fbcKVs, logfile.KeyValue{
				Key:   fmt.Sprintf("FBC.%d.%d", p.ModulePosition, p.ChannelPosition),
				Value: string(p.ChannelType),
			})
		} else if p.ModuleType == types.ModuleRPC {
			rpcKVs = append(rpcKVs, logfile.KeyValue{
				Key:   fmt.Sprintf("RPC.%d.%s", p.ModulePosition, p.CounterName),
				Value: fmt.Sprintf("%d", p.CounterValue),
			})
		}
	}

	if len(fbcKVs) > 0 {
		entries = append(entries, ScanEntry{
			FileName:      fmt.Sprintf("%s.fbc", node.Name),
			FileType:      "fbc",
			NodeName:      node.Name,
			Parsed:        &logfile.FileData{KeyValues: fbcKVs, Header: fmt.Sprintf("#FBC %s (from SQLite)", node.Name)},
			KeyValueCount: len(fbcKVs),
		})
	}
	if len(rpcKVs) > 0 {
		entries = append(entries, ScanEntry{
			FileName:      fmt.Sprintf("%s.rpc", node.Name),
			FileType:      "rpc",
			NodeName:      node.Name,
			Parsed:        &logfile.FileData{KeyValues: rpcKVs, Header: fmt.Sprintf("#RPC %s (from SQLite)", node.Name)},
			KeyValueCount: len(rpcKVs),
		})
	}

	return entries
}

// generateJSONFromLogs creates a JSON report from scanned log file entries.
func generateJSONFromLogs(cfg types.ReportConfig, entries []ScanEntry, reportID string) (string, error) {
	report := map[string]interface{}{
		"report_id":   reportID,
		"generated_at": time.Now().UTC().Format(time.RFC3339),
		"log_root":    cfg.LogRoot,
		"node":        cfg.NodeAddress,
		"file_count":  len(entries),
		"files":       entries,
	}

	data, err := json.MarshalIndent(report, "", "  ")
	if err != nil {
		return "", fmt.Errorf("report: marshal JSON: %w", err)
	}

	filePath := filepath.Join(DefaultOutputDir, reportID+".json")
	if err := os.WriteFile(filePath, data, 0644); err != nil {
		return "", fmt.Errorf("report: write JSON: %w", err)
	}

	return filePath, nil
}
