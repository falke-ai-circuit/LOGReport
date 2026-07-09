package report

import (
	"archive/zip"
	"bytes"
	"fmt"
	"os"
	"strings"
	"time"

	"github.com/falke-ai-circuit/LOGReport/internal/types"
)

// generateDOCX creates a .docx report file with title page, FBC summary,
// RPC summary, and IO point detail tables. Returns the file path.
// Uses raw Office Open XML (ZIP of XML files) — no external library needed.
func generateDOCX(node *types.Node, ioPoints []types.IOPoint, tmpl *types.Template, reportID string) (string, error) {
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

	// word/document.xml — the actual content
	docXML := buildDocumentXML(node, ioPoints, tmpl)
	writeZipEntry(zw, "word/document.xml", docXML)

	if err := zw.Close(); err != nil {
		return "", fmt.Errorf("docx: close zip: %w", err)
	}

	if err := os.WriteFile(filePath, buf.Bytes(), 0644); err != nil {
		return "", fmt.Errorf("docx: write: %w", err)
	}

	return filePath, nil
}

// buildDocumentXML constructs the word/document.xml content.
func buildDocumentXML(node *types.Node, ioPoints []types.IOPoint, tmpl *types.Template) string {
	var sb strings.Builder
	sb.WriteString(`<?xml version="1.0" encoding="UTF-8" standalone="yes"?>`)
	sb.WriteString(`<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">`)
	sb.WriteString(`<w:body>`)

	// Title
	titleText := "LOGReport — Node Report"
	if tmpl != nil && tmpl.Content != "" {
		titleText = tmpl.Content
	}
	sb.WriteString(paragraph(titleText, true, 48)) // 24pt = 48 half-points

	// Spacer
	sb.WriteString(paragraph("", false, 0))

	// Node details
	sb.WriteString(paragraph(boldText("Node Name: ")+node.Name, false, 0))
	sb.WriteString(paragraph(boldText("Node Address: ")+node.Address, false, 0))
	sb.WriteString(paragraph(boldText("Node Type: ")+string(node.Type), false, 0))
	sb.WriteString(paragraph(boldText("Report Date: ")+time.Now().UTC().Format("2006-01-02 15:04:05 UTC"), false, 0))

	sb.WriteString(paragraph("", false, 0)) // spacer

	// FBC Module Summary
	fbcPoints := filterByModuleType(ioPoints, types.ModuleFBC)
	sb.WriteString(paragraph("FBC Module Summary", true, 28)) // 14pt
	if len(fbcPoints) > 0 {
		sb.WriteString(buildTable([]string{"Module Pos", "Channel Pos", "Channel Type"}, fbcPointsToRows(fbcPoints)))
	} else {
		sb.WriteString(paragraph("(No FBC modules found)", false, 0))
	}
	sb.WriteString(paragraph("", false, 0))

	// RPC Counter Summary
	rpcPoints := filterByModuleType(ioPoints, types.ModuleRPC)
	sb.WriteString(paragraph("RPC Counter Summary", true, 28))
	if len(rpcPoints) > 0 {
		sb.WriteString(buildTable([]string{"Module Pos", "Counter Name", "Counter Value"}, rpcPointsToRows(rpcPoints)))
	} else {
		sb.WriteString(paragraph("(No RPC counters found)", false, 0))
	}
	sb.WriteString(paragraph("", false, 0))

	// IO Point Detail
	sb.WriteString(paragraph("IO Point Detail", true, 28))
	if len(ioPoints) > 0 {
		sb.WriteString(buildTable(
			[]string{"Module Type", "Module Pos", "Channel Pos", "Channel Type", "Counter Name", "Counter Value"},
			ioPointsToRows(ioPoints),
		))
	} else {
		sb.WriteString(paragraph("(No IO points)", false, 0))
	}

	sb.WriteString(`</w:body></w:document>`)
	return sb.String()
}

// paragraph returns a w:p element with optional bold and font size.
// sz is in half-points (0 = default).
func paragraph(text string, bold bool, sz int) string {
	var runs string
	if text == "" {
		// Empty paragraph for spacing
		return `<w:p><w:r><w:t xml:space="preserve"> </w:t></w:r></w:p>`
	}

	if bold {
		runs = fmt.Sprintf(`<w:r><w:rPr><w:b/><w:bCs/>%s</w:rPr><w:t xml:space="preserve">%s</w:t></w:r>`, szAttr(sz), xmlEscape(text))
	} else {
		runs = fmt.Sprintf(`<w:r>%s<w:t xml:space="preserve">%s</w:t></w:r>`, szAttrTag(sz), xmlEscape(text))
	}
	return `<w:p>` + runs + `</w:p>`
}

// boldText returns a w:r element with bold formatting for inline use.
func boldText(text string) string {
	return fmt.Sprintf(`<w:r><w:rPr><w:b/><w:bCs/></w:rPr><w:t xml:space="preserve">%s</w:t></w:r>`, xmlEscape(text))
}

// szAttr returns w:sz element if sz > 0.
func szAttr(sz int) string {
	if sz <= 0 {
		return ""
	}
	return fmt.Sprintf(`<w:sz w:val="%d"/><w:szCs w:val="%d"/>`, sz, sz)
}

// szAttrTag returns w:rPr with sz if sz > 0, or empty.
func szAttrTag(sz int) string {
	if sz <= 0 {
		return ""
	}
	return fmt.Sprintf(`<w:rPr>%s</w:rPr>`, szAttr(sz))
}

// buildTable creates a w:tbl with header row and data rows.
func buildTable(headers []string, rows [][]string) string {
	var sb strings.Builder
	sb.WriteString(`<w:tbl>`)
	sb.WriteString(`<w:tblPr><w:tblW w:w="5000" w:type="pct"/><w:tblBorders><w:top w:val="single" w:sz="4" w:space="0" w:color="auto"/><w:left w:val="single" w:sz="4" w:space="0" w:color="auto"/><w:bottom w:val="single" w:sz="4" w:space="0" w:color="auto"/><w:right w:val="single" w:sz="4" w:space="0" w:color="auto"/><w:insideH w:val="single" w:sz="4" w:space="0" w:color="auto"/><w:insideV w:val="single" w:sz="4" w:space="0" w:color="auto"/></w:tblBorders></w:tblPr>`)

	// Header row
	sb.WriteString(`<w:tr>`)
	for _, h := range headers {
		sb.WriteString(`<w:tc><w:tcPr><w:tcW w:w="` + colWidth(len(headers)) + `" w:type="dxa"/></w:tcPr>`)
		sb.WriteString(`<w:p><w:r><w:rPr><w:b/><w:bCs/><w:sz w:val="20"/><w:szCs w:val="20"/></w:rPr><w:t xml:space="preserve">` + xmlEscape(h) + `</w:t></w:r></w:p>`)
		sb.WriteString(`</w:tc>`)
	}
	sb.WriteString(`</w:tr>`)

	// Data rows
	for _, row := range rows {
		sb.WriteString(`<w:tr>`)
		for _, cell := range row {
			sb.WriteString(`<w:tc><w:tcPr><w:tcW w:w="` + colWidth(len(headers)) + `" w:type="dxa"/></w:tcPr>`)
			sb.WriteString(`<w:p><w:r><w:rPr><w:sz w:val="20"/><w:szCs w:val="20"/></w:rPr><w:t xml:space="preserve">` + xmlEscape(cell) + `</w:t></w:r></w:p>`)
			sb.WriteString(`</w:tc>`)
		}
		sb.WriteString(`</w:tr>`)
	}

	sb.WriteString(`</w:tbl>`)
	return sb.String()
}

// colWidth returns a fixed column width in twips (1/20 of a point).
func colWidth(numCols int) string {
	w := 9000 / numCols // distribute across ~6.25 inches
	return fmt.Sprintf("%d", w)
}

// fbcPointsToRows converts FBC IO points to table rows.
func fbcPointsToRows(points []types.IOPoint) [][]string {
	rows := make([][]string, len(points))
	for i, p := range points {
		rows[i] = []string{
			fmt.Sprintf("%d", p.ModulePosition),
			fmt.Sprintf("%d", p.ChannelPosition),
			string(p.ChannelType),
		}
	}
	return rows
}

// rpcPointsToRows converts RPC IO points to table rows.
func rpcPointsToRows(points []types.IOPoint) [][]string {
	rows := make([][]string, len(points))
	for i, p := range points {
		rows[i] = []string{
			fmt.Sprintf("%d", p.ModulePosition),
			p.CounterName,
			fmt.Sprintf("%d", p.CounterValue),
		}
	}
	return rows
}

// ioPointsToRows converts all IO points to detail table rows.
func ioPointsToRows(points []types.IOPoint) [][]string {
	rows := make([][]string, len(points))
	for i, p := range points {
		counterName := p.CounterName
		counterVal := ""
		if p.ModuleType == types.ModuleRPC {
			counterVal = fmt.Sprintf("%d", p.CounterValue)
		}
		chType := string(p.ChannelType)
		chPos := fmt.Sprintf("%d", p.ChannelPosition)
		if p.ModuleType == types.ModuleRPC {
			chType = "\u2014" // em dash
			chPos = "\u2014"
		}
		rows[i] = []string{
			string(p.ModuleType),
			fmt.Sprintf("%d", p.ModulePosition),
			chPos,
			chType,
			counterName,
			counterVal,
		}
	}
	return rows
}

// xmlEscape escapes text for XML content.
func xmlEscape(s string) string {
	s = strings.ReplaceAll(s, "&", "&amp;")
	s = strings.ReplaceAll(s, "<", "&lt;")
	s = strings.ReplaceAll(s, ">", "&gt;")
	s = strings.ReplaceAll(s, "\"", "&quot;")
	s = strings.ReplaceAll(s, "'", "&apos;")
	return s
}

// writeZipEntry adds a file to the ZIP writer.
func writeZipEntry(zw *zip.Writer, name, content string) {
	w, _ := zw.Create(name)
	w.Write([]byte(content))
}

// filterByModuleType returns IO points matching the given module type.
func filterByModuleType(points []types.IOPoint, mt types.ModuleType) []types.IOPoint {
	var result []types.IOPoint
	for _, p := range points {
		if p.ModuleType == mt {
			result = append(result, p)
		}
	}
	return result
}
