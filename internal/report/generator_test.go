package report

import (
	"archive/zip"
	"bytes"
	"encoding/json"
	"fmt"
	"os"
	"strings"
	"testing"
	"time"

	"github.com/falke-ai-circuit/LOGReport/internal/store"
	"github.com/falke-ai-circuit/LOGReport/internal/types"
)

// openTestStore creates a temporary SQLite database for testing.
func openTestStore(t *testing.T) *store.Store {
	t.Helper()
	path := fmt.Sprintf("/tmp/logreport-test-%d.db", time.Now().UnixNano())
	s, err := store.Open(path)
	if err != nil {
		t.Fatalf("Open: %v", err)
	}
	t.Cleanup(func() {
		s.Close()
		os.Remove(path)
	})
	return s
}

// seedNode creates a test node in the store.
func seedNode(t *testing.T, s *store.Store, addr, name string, ntype types.NodeType) {
	t.Helper()
	n := &types.Node{
		Address:  addr,
		Name:     name,
		Type:     ntype,
		Status:   types.StatusConnected,
		Port:     23,
		LastSeen: time.Now(),
	}
	if err := s.SaveNode(n); err != nil {
		t.Fatalf("SaveNode: %v", err)
	}
}

// seedIOPoints creates test IO points for a node.
func seedIOPoints(t *testing.T, s *store.Store, addr string, points []types.IOPoint) {
	t.Helper()
	if err := s.SaveIOPoints(addr, points); err != nil {
		t.Fatalf("SaveIOPoints: %v", err)
	}
}

// seedTemplate creates a test template in the store.
func seedTemplate(t *testing.T, s *store.Store, name, format, content string) {
	t.Helper()
	tmpl := &types.Template{
		Name:    name,
		Format:  format,
		Content: content,
	}
	if err := s.SaveTemplate(tmpl); err != nil {
		t.Fatalf("SaveTemplate: %v", err)
	}
}

// TestGenerateReportDOCX verifies DOCX report generation: file exists and is valid DOCX.
func TestGenerateReportDOCX(t *testing.T) {
	s := openTestStore(t)
	seedNode(t, s, "192.168.1.100", "ACN-01", types.ACN)
	seedIOPoints(t, s, "192.168.1.100", []types.IOPoint{
		{NodeAddress: "192.168.1.100", ModulePosition: 1, ChannelPosition: 1, ChannelType: types.AI8, ModuleType: types.ModuleFBC},
		{NodeAddress: "192.168.1.100", ModulePosition: 1, ChannelPosition: 2, ChannelType: types.AI8, ModuleType: types.ModuleFBC},
		{NodeAddress: "192.168.1.100", ModulePosition: 2, ChannelPosition: 1, ChannelType: types.DI16, ModuleType: types.ModuleFBC},
		{NodeAddress: "192.168.1.100", ModulePosition: 3, ChannelPosition: 1, ModuleType: types.ModuleRPC, CounterName: "ERR_TX", CounterValue: 42},
	})

	cfg := types.ReportConfig{
		NodeAddress: "192.168.1.100",
		Format:      types.FormatDOCX,
		Title:       "Test DOCX Report",
		Author:      "Test Author",
	}

	report, err := GenerateReport(cfg, s)
	if err != nil {
		t.Fatalf("GenerateReport DOCX: %v", err)
	}

	// Verify report record
	if report.Status != types.StatusCompleted {
		t.Errorf("Status: got %q, want %q", report.Status, types.StatusCompleted)
	}
	if report.Format != types.FormatDOCX {
		t.Errorf("Format: got %q, want %q", report.Format, types.FormatDOCX)
	}
	if report.NodeAddress != "192.168.1.100" {
		t.Errorf("NodeAddress: got %q, want %q", report.NodeAddress, "192.168.1.100")
	}

	// Verify file exists
	if _, err := os.Stat(report.FilePath); os.IsNotExist(err) {
		t.Fatalf("DOCX file not found: %s", report.FilePath)
	}
	t.Cleanup(func() { os.Remove(report.FilePath) })

	// Verify it's a valid DOCX (ZIP with word/document.xml)
	if !isValidDOCX(t, report.FilePath) {
		t.Error("Generated file is not a valid DOCX")
	}

	// Verify report saved in store
	saved, err := s.GetReport(report.ID)
	if err != nil {
		t.Fatalf("GetReport: %v", err)
	}
	if saved.FilePath != report.FilePath {
		t.Errorf("Saved FilePath: got %q, want %q", saved.FilePath, report.FilePath)
	}
}

// TestGenerateReportJSON verifies JSON report generation: file exists, valid JSON, round-trip.
func TestGenerateReportJSON(t *testing.T) {
	s := openTestStore(t)
	seedNode(t, s, "192.168.1.200", "DIA-01", types.DIA)
	seedIOPoints(t, s, "192.168.1.200", []types.IOPoint{
		{NodeAddress: "192.168.1.200", ModulePosition: 1, ChannelPosition: 1, ChannelType: types.AO4, ModuleType: types.ModuleFBC},
		{NodeAddress: "192.168.1.200", ModulePosition: 5, ChannelPosition: 1, ModuleType: types.ModuleRPC, CounterName: "ERR_RX", CounterValue: 7},
	})

	cfg := types.ReportConfig{
		NodeAddress: "192.168.1.200",
		Format:      types.FormatJSON,
		Title:       "Test JSON Report",
	}

	report, err := GenerateReport(cfg, s)
	if err != nil {
		t.Fatalf("GenerateReport JSON: %v", err)
	}

	// Verify file exists
	if _, err := os.Stat(report.FilePath); os.IsNotExist(err) {
		t.Fatalf("JSON file not found: %s", report.FilePath)
	}
	t.Cleanup(func() { os.Remove(report.FilePath) })

	// Read and parse JSON
	data, err := os.ReadFile(report.FilePath)
	if err != nil {
		t.Fatalf("ReadFile: %v", err)
	}

	var parsed map[string]interface{}
	if err := json.Unmarshal(data, &parsed); err != nil {
		t.Fatalf("JSON parse: %v", err)
	}

	// Verify key fields present
	expectedFields := []string{"title", "node", "fbc_modules", "rpc_counters", "io_points", "generated_at", "total_fbc_points", "total_rpc_points", "total_io_points"}
	for _, f := range expectedFields {
		if _, ok := parsed[f]; !ok {
			t.Errorf("JSON missing field %q", f)
		}
	}

	// Verify node data
	node, ok := parsed["node"].(map[string]interface{})
	if !ok {
		t.Fatal("node field is not an object")
	}
	if node["name"] != "DIA-01" {
		t.Errorf("node.name: got %v, want DIA-01", node["name"])
	}
	if node["address"] != "192.168.1.200" {
		t.Errorf("node.address: got %v, want 192.168.1.200", node["address"])
	}

	// Verify counts
	if fbc, ok := parsed["total_fbc_points"].(float64); !ok || int(fbc) != 1 {
		t.Errorf("total_fbc_points: got %v, want 1", parsed["total_fbc_points"])
	}
	if rpc, ok := parsed["total_rpc_points"].(float64); !ok || int(rpc) != 1 {
		t.Errorf("total_rpc_points: got %v, want 1", parsed["total_rpc_points"])
	}

	// Round-trip: re-parse into jsonReport struct
	var jr jsonReport
	if err := json.Unmarshal(data, &jr); err != nil {
		t.Fatalf("JSON round-trip unmarshal: %v", err)
	}
	if jr.Node.Name != "DIA-01" {
		t.Errorf("round-trip node name: got %q, want DIA-01", jr.Node.Name)
	}
}

// TestGenerateReportEmptyIOPoints verifies report generation with no IO points.
func TestGenerateReportEmptyIOPoints(t *testing.T) {
	s := openTestStore(t)
	seedNode(t, s, "10.0.0.1", "EmptyNode", types.CIS)

	cfg := types.ReportConfig{
		NodeAddress: "10.0.0.1",
		Format:      types.FormatDOCX,
	}

	report, err := GenerateReport(cfg, s)
	if err != nil {
		t.Fatalf("GenerateReport empty IO: %v", err)
	}

	if report.Status != types.StatusCompleted {
		t.Errorf("Status: got %q, want completed", report.Status)
	}

	// File should exist
	if _, err := os.Stat(report.FilePath); os.IsNotExist(err) {
		t.Fatalf("DOCX file not found: %s", report.FilePath)
	}
	t.Cleanup(func() { os.Remove(report.FilePath) })

	// Should be valid DOCX
	if !isValidDOCX(t, report.FilePath) {
		t.Error("Empty IO DOCX is not valid")
	}
}

// TestGenerateReportMissingNode verifies error when node doesn't exist.
func TestGenerateReportMissingNode(t *testing.T) {
	s := openTestStore(t)

	cfg := types.ReportConfig{
		NodeAddress: "nonexistent",
		Format:      types.FormatJSON,
	}

	_, err := GenerateReport(cfg, s)
	if err == nil {
		t.Fatal("expected error for missing node, got nil")
	}
	if !strings.Contains(err.Error(), "nonexistent") {
		t.Errorf("error should mention node address: %v", err)
	}
}

// TestGenerateReportInvalidFormat verifies error for unsupported format.
func TestGenerateReportInvalidFormat(t *testing.T) {
	s := openTestStore(t)
	seedNode(t, s, "192.168.1.1", "TestNode", types.ACN)

	cfg := types.ReportConfig{
		NodeAddress: "192.168.1.1",
		Format:      types.ReportFormat("pdf"),
	}

	_, err := GenerateReport(cfg, s)
	if err == nil {
		t.Fatal("expected error for invalid format, got nil")
	}
	if !strings.Contains(err.Error(), "unsupported format") {
		t.Errorf("error should mention unsupported format: %v", err)
	}
}

// TestGenerateReportWithTemplate verifies template from store is applied.
func TestGenerateReportWithTemplate(t *testing.T) {
	s := openTestStore(t)
	seedNode(t, s, "192.168.1.50", "TemplateNode", types.ACN)
	seedIOPoints(t, s, "192.168.1.50", []types.IOPoint{
		{NodeAddress: "192.168.1.50", ModulePosition: 1, ChannelPosition: 1, ChannelType: types.BI8, ModuleType: types.ModuleFBC},
	})
	seedTemplate(t, s, "custom-title", "docx", "CUSTOM REPORT TITLE")

	cfg := types.ReportConfig{
		NodeAddress: "192.168.1.50",
		Format:      types.FormatDOCX,
		Template:    "custom-title",
	}

	report, err := GenerateReport(cfg, s)
	if err != nil {
		t.Fatalf("GenerateReport with template: %v", err)
	}

	if report.Template != "custom-title" {
		t.Errorf("Template: got %q, want custom-title", report.Template)
	}

	// Verify file exists
	if _, err := os.Stat(report.FilePath); os.IsNotExist(err) {
		t.Fatalf("DOCX file not found: %s", report.FilePath)
	}
	t.Cleanup(func() { os.Remove(report.FilePath) })

	// Verify template content appears in DOCX
	if !docxContainsText(t, report.FilePath, "CUSTOM REPORT TITLE") {
		t.Error("DOCX does not contain template text 'CUSTOM REPORT TITLE'")
	}
}

// TestGenerateReportJSONEmptyIOPoints verifies JSON report with no IO points.
func TestGenerateReportJSONEmptyIOPoints(t *testing.T) {
	s := openTestStore(t)
	seedNode(t, s, "10.0.0.2", "JSONEmpty", types.OPS)

	cfg := types.ReportConfig{
		NodeAddress: "10.0.0.2",
		Format:      types.FormatJSON,
	}

	report, err := GenerateReport(cfg, s)
	if err != nil {
		t.Fatalf("GenerateReport JSON empty: %v", err)
	}

	data, err := os.ReadFile(report.FilePath)
	if err != nil {
		t.Fatalf("ReadFile: %v", err)
	}
	t.Cleanup(func() { os.Remove(report.FilePath) })

	var parsed map[string]interface{}
	if err := json.Unmarshal(data, &parsed); err != nil {
		t.Fatalf("JSON parse: %v", err)
	}

	if fbc, ok := parsed["total_fbc_points"].(float64); !ok || int(fbc) != 0 {
		t.Errorf("total_fbc_points: got %v, want 0", parsed["total_fbc_points"])
	}
	if rpc, ok := parsed["total_rpc_points"].(float64); !ok || int(rpc) != 0 {
		t.Errorf("total_rpc_points: got %v, want 0", parsed["total_rpc_points"])
	}
}

// TestTemplateNotFound verifies error when template doesn't exist.
func TestTemplateNotFound(t *testing.T) {
	s := openTestStore(t)
	seedNode(t, s, "192.168.1.99", "NoTmpl", types.ACN)

	cfg := types.ReportConfig{
		NodeAddress: "192.168.1.99",
		Format:      types.FormatDOCX,
		Template:    "nonexistent-template",
	}

	_, err := GenerateReport(cfg, s)
	if err == nil {
		t.Fatal("expected error for missing template, got nil")
	}
	if !strings.Contains(err.Error(), "nonexistent-template") {
		t.Errorf("error should mention template name: %v", err)
	}
}

// isValidDOCX checks that a file is a valid DOCX (ZIP containing word/document.xml).
func isValidDOCX(t *testing.T, path string) bool {
	t.Helper()
	data, err := os.ReadFile(path)
	if err != nil {
		t.Errorf("ReadFile: %v", err)
		return false
	}

	zipReader, err := zip.NewReader(bytes.NewReader(data), int64(len(data)))
	if err != nil {
		t.Errorf("Not a valid ZIP: %v", err)
		return false
	}

	hasDocument := false
	for _, f := range zipReader.File {
		if f.Name == "word/document.xml" {
			hasDocument = true
			break
		}
	}
	if !hasDocument {
		t.Error("DOCX missing word/document.xml")
	}
	return hasDocument
}

// docxContainsText checks if a DOCX file contains the given text in its document.xml.
func docxContainsText(t *testing.T, path, text string) bool {
	t.Helper()
	data, err := os.ReadFile(path)
	if err != nil {
		t.Errorf("ReadFile: %v", err)
		return false
	}

	zipReader, err := zip.NewReader(bytes.NewReader(data), int64(len(data)))
	if err != nil {
		t.Errorf("Not a valid ZIP: %v", err)
		return false
	}

	for _, f := range zipReader.File {
		if f.Name == "word/document.xml" {
			rc, err := f.Open()
			if err != nil {
				t.Errorf("Open document.xml: %v", err)
				return false
			}
			defer rc.Close()

			var buf bytes.Buffer
			if _, err := buf.ReadFrom(rc); err != nil {
				t.Errorf("Read document.xml: %v", err)
				return false
			}

			if strings.Contains(buf.String(), text) {
				return true
			}
			t.Logf("document.xml does not contain %q", text)
			return false
		}
	}
	t.Error("word/document.xml not found in DOCX")
	return false
}
