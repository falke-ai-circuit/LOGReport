package generator

import (
	"fmt"
	"path/filepath"
	"strings"
	"time"

	"github.com/jung-kurt/gofpdf"
	"github.com/goranjovic55/LOGReport/internal/processor"
)

const (
	colorTitleR, colorTitleG, colorTitleB = 93, 62, 142   // #5D3E8E purple
	colorSubR, colorSubG, colorSubB       = 122, 82, 153  // #7A5299 lighter purple
	colorBodyR, colorBodyG, colorBodyB    = 30, 30, 30    // near black
	colorBgR, colorBgG, colorBgB         = 245, 245, 245 // light gray bg
)

type ReportOptions struct {
	Title      string
	MaxLines   int  // max lines per file, 0 = all
}

// GeneratePDF creates a PDF report from a scan result
func GeneratePDF(result *processor.ScanResult, outputPath string, opts ReportOptions) error {
	pdf := gofpdf.New("P", "mm", "A4", "")
	pdf.SetMargins(15, 15, 15)
	pdf.SetAutoPageBreak(true, 15)

	title := opts.Title
	if title == "" {
		title = fmt.Sprintf("LOGReport - %s", filepath.Base(result.RootPath))
	}
	// Sanitize title for gofpdf Latin-1 encoding
	title = sanitize(title)

	// Cover page
	pdf.AddPage()
	pdf.SetFont("Helvetica", "B", 18)
	pdf.SetTextColor(colorTitleR, colorTitleG, colorTitleB)
	pdf.CellFormat(0, 12, title, "", 1, "C", false, 0, "")

	pdf.SetFont("Helvetica", "", 10)
	pdf.SetTextColor(100, 100, 100)
	pdf.CellFormat(0, 8, fmt.Sprintf("Generated: %s", time.Now().Format("2006-01-02 15:04:05")), "", 1, "C", false, 0, "")
	pdf.CellFormat(0, 8, fmt.Sprintf("Source: %s", result.RootPath), "", 1, "C", false, 0, "")
	pdf.CellFormat(0, 8, fmt.Sprintf("Total files: %d | Groups: %d", result.Total, len(result.Groups)), "", 1, "C", false, 0, "")

	// One section per folder group
	for _, group := range result.Groups {
		pdf.AddPage()

		// Group header
		pdf.SetFont("Helvetica", "B", 13)
		pdf.SetTextColor(colorTitleR, colorTitleG, colorTitleB)
		pdf.SetFillColor(colorBgR, colorBgG, colorBgB)
		pdf.CellFormat(0, 9, group.Name, "B", 1, "L", true, 0, "")
		pdf.Ln(2)

		for _, file := range group.Files {
			// File subtitle
			pdf.SetFont("Helvetica", "B", 10)
			pdf.SetTextColor(colorSubR, colorSubG, colorSubB)
			pdf.CellFormat(0, 7, file.Name, "", 1, "L", false, 0, "")

			if len(file.Lines) == 0 {
				pdf.SetFont("Courier", "I", 8)
				pdf.SetTextColor(150, 150, 150)
				pdf.CellFormat(0, 5, "(empty)", "", 1, "L", false, 0, "")
			} else {
				pdf.SetFont("Courier", "", 7)
				pdf.SetTextColor(colorBodyR, colorBodyG, colorBodyB)
				maxLines := opts.MaxLines
				lines := file.Lines
				if maxLines > 0 && len(lines) > maxLines {
					lines = lines[:maxLines]
				}
				for _, line := range lines {
					// Sanitize: replace non-latin1 chars
					safe := sanitize(line)
					pdf.CellFormat(0, 4, safe, "", 1, "L", false, 0, "")
					if pdf.GetY() > 270 {
						pdf.AddPage()
					}
				}
			}
			pdf.Ln(3)
		}
	}

	return pdf.OutputFileAndClose(outputPath)
}

func sanitize(s string) string {
	var b strings.Builder
	for _, r := range s {
		if r >= 32 && r < 256 {
			b.WriteRune(r)
		} else {
			b.WriteRune(' ')
		}
	}
	return b.String()
}
