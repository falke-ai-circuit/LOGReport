// Package report generates DOCX and JSON reports from node data
// stored in the LOGReport SQLite database.
package report

import (
	"crypto/rand"
	"fmt"
	"os"
	"path/filepath"
	"time"

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
	if cfg.Format != types.FormatDOCX && cfg.Format != types.FormatJSON {
		return nil, fmt.Errorf("report: unsupported format %q", cfg.Format)
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
