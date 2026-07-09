package report

import (
	"archive/zip"
	"bytes"
	"encoding/json"
	"fmt"
	"os"
	"testing"

	"github.com/falke-ai-circuit/LOGReport/internal/types"
)

// ─── Injection / Special-Character Tests ──────────────────────────

// TestInjectionDOCXSpecialChars verifies that XML special characters in
// template text (<, >, &, ", ') are properly escaped in the generated
// DOCX, and the resulting file is still a valid ZIP.
func TestInjectionDOCXSpecialChars(t *testing.T) {
	s := openTestStore(t)

	// Seed a node with special chars in the name
	addr := "10.0.0.1"
	seedNode(t, s, addr, `Node<Name>&"Quotes"'Apostrophe`, types.ACN)
	seedIOPoints(t, s, addr, []types.IOPoint{
		{NodeAddress: addr, ModulePosition: 1, ChannelPosition: 1, ChannelType: types.AI8, ModuleType: types.ModuleFBC},
	})

	// Seed a template with ALL XML special characters
	seedTemplate(t, s, "xml-inject", "docx", `<Title> & "Quotes" & 'Apos' >`)

	cfg := types.ReportConfig{
		NodeAddress: addr,
		Format:      types.FormatDOCX,
		Template:    "xml-inject",
	}

	report, err := GenerateReport(cfg, s)
	if err != nil {
		t.Fatalf("GenerateReport with special chars: %v", err)
	}
	t.Cleanup(func() { os.Remove(report.FilePath) })

	// Verify the DOCX is a valid ZIP file
	data, err := os.ReadFile(report.FilePath)
	if err != nil {
		t.Fatalf("ReadFile: %v", err)
	}

	zipReader, err := zip.NewReader(bytes.NewReader(data), int64(len(data)))
	if err != nil {
		t.Fatalf("Generated DOCX is not a valid ZIP: %v", err)
	}

	// Verify word/document.xml exists
	hasDocument := false
	for _, f := range zipReader.File {
		if f.Name == "word/document.xml" {
			hasDocument = true
			rc, err := f.Open()
			if err != nil {
				t.Fatalf("Open document.xml: %v", err)
			}
			defer rc.Close()

			var buf bytes.Buffer
			buf.ReadFrom(rc)

			// Verify the template text was properly escaped — the raw
			// <, >, & should appear as &lt;, &gt;, &amp; in the XML
			if !bytes.Contains(buf.Bytes(), []byte("&lt;Title&gt;")) {
				t.Errorf("document.xml does not contain escaped &lt;Title&gt;")
			}
			if !bytes.Contains(buf.Bytes(), []byte("&amp;")) {
				t.Errorf("document.xml does not contain escaped &amp;")
			}
			if !bytes.Contains(buf.Bytes(), []byte("&quot;Quotes&quot;")) {
				t.Errorf("document.xml does not contain escaped &quot;Quotes&quot;")
			}
			if !bytes.Contains(buf.Bytes(), []byte("&apos;Apos&apos;")) {
				t.Errorf("document.xml does not contain escaped &apos;Apos&apos;")
			}
		}
	}
	if !hasDocument {
		t.Fatal("DOCX missing word/document.xml")
	}
}

// TestInjectionLargeIOPointCount verifies that report generation works
// correctly with a large number of IO points (500+).
func TestInjectionLargeIOPointCount(t *testing.T) {
	s := openTestStore(t)

	addr := "192.168.100.1"
	seedNode(t, s, addr, "LargeNode", types.ACN)

	// Generate 500+ IO points — mix of FBC and RPC
	numFBC := 400
	numRPC := 150
	points := make([]types.IOPoint, 0, numFBC+numRPC)

	for i := 0; i < numFBC; i++ {
		points = append(points, types.IOPoint{
			NodeAddress:     addr,
			ModulePosition:  (i / 16) + 1,
			ChannelPosition: (i % 16) + 1,
			ChannelType:     types.AI8,
			ModuleType:      types.ModuleFBC,
		})
	}
	for i := 0; i < numRPC; i++ {
		points = append(points, types.IOPoint{
			NodeAddress:    addr,
			ModulePosition: 50 + (i / 10),
			ModuleType:     types.ModuleRPC,
			CounterName:    fmt.Sprintf("ERR_%d", i),
			CounterValue:   i * 10,
		})
	}

	seedIOPoints(t, s, addr, points)

	// Generate JSON report (faster to validate programmatically)
	cfg := types.ReportConfig{
		NodeAddress: addr,
		Format:      types.FormatJSON,
	}

	report, err := GenerateReport(cfg, s)
	if err != nil {
		t.Fatalf("GenerateReport with %d IO points: %v", numFBC+numRPC, err)
	}
	t.Cleanup(func() { os.Remove(report.FilePath) })

	// Verify the JSON report
	data, err := os.ReadFile(report.FilePath)
	if err != nil {
		t.Fatalf("ReadFile: %v", err)
	}

	var parsed map[string]interface{}
	if err := json.Unmarshal(data, &parsed); err != nil {
		t.Fatalf("JSON parse: %v", err)
	}

	totalIO, ok := parsed["total_io_points"].(float64)
	if !ok {
		t.Fatalf("total_io_points is not a number: %T", parsed["total_io_points"])
	}
	if int(totalIO) != numFBC+numRPC {
		t.Errorf("total_io_points: got %d, want %d", int(totalIO), numFBC+numRPC)
	}

	totalFBC, ok := parsed["total_fbc_points"].(float64)
	if !ok || int(totalFBC) != numFBC {
		t.Errorf("total_fbc_points: got %v, want %d", parsed["total_fbc_points"], numFBC)
	}

	totalRPC, ok := parsed["total_rpc_points"].(float64)
	if !ok || int(totalRPC) != numRPC {
		t.Errorf("total_rpc_points: got %v, want %d", parsed["total_rpc_points"], numRPC)
	}

	// Also generate a DOCX report to verify it doesn't break with large data
	cfgDOCX := types.ReportConfig{
		NodeAddress: addr,
		Format:      types.FormatDOCX,
	}
	reportDOCX, err := GenerateReport(cfgDOCX, s)
	if err != nil {
		t.Fatalf("GenerateReport DOCX with %d IO points: %v", numFBC+numRPC, err)
	}
	t.Cleanup(func() { os.Remove(reportDOCX.FilePath) })

	if !isValidDOCX(t, reportDOCX.FilePath) {
		t.Error("Large IO DOCX is not a valid DOCX")
	}
}

// TestInjectionReportIDUniqueness generates 10 reports and verifies
// all have unique IDs.
func TestInjectionReportIDUniqueness(t *testing.T) {
	s := openTestStore(t)

	addr := "10.0.0.50"
	seedNode(t, s, addr, "UniqueIDNode", types.ACN)
	seedIOPoints(t, s, addr, []types.IOPoint{
		{NodeAddress: addr, ModulePosition: 1, ChannelPosition: 1, ChannelType: types.AI8, ModuleType: types.ModuleFBC},
	})

	ids := make(map[string]bool, 10)

	for i := 0; i < 10; i++ {
		cfg := types.ReportConfig{
			NodeAddress: addr,
			Format:      types.FormatJSON,
		}
		report, err := GenerateReport(cfg, s)
		if err != nil {
			t.Fatalf("GenerateReport %d: %v", i, err)
		}
		t.Cleanup(func() { os.Remove(report.FilePath) })

		if report.ID == "" {
			t.Fatalf("Report %d has empty ID", i)
		}
		if ids[report.ID] {
			t.Fatalf("Duplicate report ID: %s (report %d)", report.ID, i)
		}
		ids[report.ID] = true
	}

	if len(ids) != 10 {
		t.Errorf("Expected 10 unique IDs, got %d", len(ids))
	}
}

// TestInjectionJSONSpecialCharsInNodeName verifies that special characters
// in node names are properly handled in JSON report output.
func TestInjectionJSONSpecialCharsInNodeName(t *testing.T) {
	s := openTestStore(t)

	addr := "10.0.0.77"
	specialName := `Node<script>alert(1)</script>&"quotes"'apos'`
	seedNode(t, s, addr, specialName, types.ACN)
	seedIOPoints(t, s, addr, []types.IOPoint{
		{NodeAddress: addr, ModulePosition: 1, ChannelPosition: 1, ChannelType: types.AI8, ModuleType: types.ModuleFBC},
	})

	cfg := types.ReportConfig{
		NodeAddress: addr,
		Format:      types.FormatJSON,
	}

	report, err := GenerateReport(cfg, s)
	if err != nil {
		t.Fatalf("GenerateReport JSON with special node name: %v", err)
	}
	t.Cleanup(func() { os.Remove(report.FilePath) })

	data, err := os.ReadFile(report.FilePath)
	if err != nil {
		t.Fatalf("ReadFile: %v", err)
	}

	// The JSON must be valid (properly escaped)
	var parsed map[string]interface{}
	if err := json.Unmarshal(data, &parsed); err != nil {
		t.Fatalf("JSON parse with special chars in node name: %v", err)
	}

	// Verify the node name is preserved exactly (JSON handles escaping natively)
	node, ok := parsed["node"].(map[string]interface{})
	if !ok {
		t.Fatal("node field is not an object")
	}
	name, ok := node["name"].(string)
	if !ok {
		t.Fatalf("node.name is not a string: %T", node["name"])
	}
	if name != specialName {
		t.Errorf("node.name: got %q, want %q", name, specialName)
	}

	// Verify the title contains the special name
	title, ok := parsed["title"].(string)
	if !ok {
		t.Fatalf("title is not a string: %T", parsed["title"])
	}
	// Title format: "LOGReport — <NodeName>"
	expected := fmt.Sprintf("LOGReport — %s", specialName)
	if title != expected {
		t.Errorf("title: got %q, want %q", title, expected)
	}
}
