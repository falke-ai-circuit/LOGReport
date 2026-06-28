// Package report generates DOCX and JSON reports from node data
// stored in the LOGReport SQLite database.
package report

import (
	"archive/zip"
	"bytes"
	"crypto/rand"
	"fmt"
	"os"
	"path/filepath"
	"strings"
	"time"

	"github.com/falke-ai-circuit/LOGReport/internal/logfile"
	"github.com/falke-ai-circuit/LOGReport/internal/store"
	"github.com/falke-ai-circuit/LOGReport/internal/types"
)

// DefaultOutputDir is the default directory for generated reports.
const DefaultOutputDir = "/tmp/logreport-reports"

// GenerateReport loads node and IO point data from the store, generates
// a report in the specified format, and returns a Report record with
// the file path and completed status.
func GenerateReport(cfg types.ReportConfig, s *store.Store) (*types.Report, error) {
	// Validate format
	if cfg.Format != types.FormatDOCX && cfg.Format != types.FormatJSON && cfg.Format != types.FormatPDF {
		return nil, fmt.Errorf("report: unsupported format %q", cfg.Format)
	}

	// PDF/DOCX with log_root: generate from log files (no SQLite data needed)
	if (cfg.Format == types.FormatPDF || cfg.Format == types.FormatDOCX) && cfg.LogRoot != "" {
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
		filePath, err = generatePDF(reportID, "", scanEntries)
	}
	if err != nil {
		return nil, fmt.Errorf("report: generate %s: %w", cfg.Format, err)
	}

	// Build report record
	report := &types.Report{
		ID:          reportID,
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
		filePath, err = generatePDF(reportID, cfg.LogRoot, scanEntries)
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
		return nil, fmt.Errorf("report: save report: %w", err)
	}

	return report, nil
}

// generateDOCXFromLogs creates a simplified DOCX report from log file entries.
// It builds a document with a title, file summary table, and per-file key-value
// tables using the same raw Office Open XML approach as docx.go.
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
</Types>`
	writeZipEntry(zw, "[Content_Types].xml", contentTypes)

	// _rels/.rels
	rels := `<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>
</Relationships>`
	writeZipEntry(zw, "_rels/.rels", rels)

	// word/_rels/document.xml.rels
	docRels := `<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
</Relationships>`
	writeZipEntry(zw, "word/_rels/document.xml.rels", docRels)

	// word/document.xml — title + summary table + per-file contents
	var sb strings.Builder
	sb.WriteString(`<?xml version="1.0" encoding="UTF-8" standalone="yes"?>`)
	sb.WriteString(`<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">`)
	sb.WriteString(`<w:body>`)

	// Title
	titleText := "LOGReport — Log File Report"
	if cfg.Title != "" {
		titleText = cfg.Title
	}
	sb.WriteString(paragraph(titleText, true, 48))
	sb.WriteString(paragraph("", false, 0))

	// Metadata
	if cfg.LogRoot != "" {
		sb.WriteString(paragraph(boldText("Log Root: ")+cfg.LogRoot, false, 0))
	}
	sb.WriteString(paragraph(boldText("Generated: ")+time.Now().UTC().Format("2006-01-02 15:04:05 UTC"), false, 0))
	sb.WriteString(paragraph("", false, 0))

	// File summary table
	if len(scanEntries) > 0 {
		sb.WriteString(paragraph("File Summary", true, 28))
		var rows [][]string
		for _, e := range scanEntries {
			rows = append(rows, []string{
				e.FileName,
				e.FileType,
				e.NodeName,
				fmt.Sprintf("%d", e.KeyValueCount),
				fmt.Sprintf("%d", e.Size),
			})
		}
		sb.WriteString(buildTable([]string{"File Name", "Type", "Node", "Entries", "Size (bytes)"}, rows))
		sb.WriteString(paragraph("", false, 0))
	}

	// Per-file key-value contents
	for _, e := range scanEntries {
		if e.Parsed == nil {
			continue
		}
		sb.WriteString(paragraph(fmt.Sprintf("%s [%s]", e.FileName, e.FileType), true, 28))
		if e.Parsed.Header != "" {
			sb.WriteString(paragraph(e.Parsed.Header, false, 0))
		}
		if len(e.Parsed.KeyValues) > 0 {
			var kvRows [][]string
			for _, kv := range e.Parsed.KeyValues {
				kvRows = append(kvRows, []string{kv.Key, kv.Value})
			}
			sb.WriteString(buildTable([]string{"Key", "Value"}, kvRows))
		} else if len(e.Parsed.Lines) > 0 {
			for _, line := range e.Parsed.Lines {
				sb.WriteString(paragraph(line, false, 0))
			}
		}
		sb.WriteString(paragraph("", false, 0))
	}

	if len(scanEntries) == 0 {
		sb.WriteString(paragraph("(No log files found in the specified directory.)", false, 0))
	}

	sb.WriteString(`</w:body></w:document>`)
	writeZipEntry(zw, "word/document.xml", sb.String())

	if err := zw.Close(); err != nil {
		return "", fmt.Errorf("docx: close zip: %w", err)
	}

	if err := os.WriteFile(filePath, buf.Bytes(), 0644); err != nil {
		return "", fmt.Errorf("docx: write: %w", err)
	}

	return filePath, nil
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
