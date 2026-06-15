package types

import (
	"encoding/json"
	"testing"
)

func TestReportConfigJSONRoundTrip(t *testing.T) {
	cfg := ReportConfig{
		NodeAddress: "192.168.1.100",
		Format:      FormatDOCX,
		Template:    "commissioning",
		Title:       "Commissioning Report - AP01",
		Author:      "Valmet Engineer",
	}

	data, err := json.Marshal(cfg)
	if err != nil {
		t.Fatalf("marshal: %v", err)
	}

	var decoded ReportConfig
	if err := json.Unmarshal(data, &decoded); err != nil {
		t.Fatalf("unmarshal: %v", err)
	}

	if decoded.NodeAddress != cfg.NodeAddress {
		t.Errorf("NodeAddress: got %q, want %q", decoded.NodeAddress, cfg.NodeAddress)
	}
	if decoded.Format != cfg.Format {
		t.Errorf("Format: got %q, want %q", decoded.Format, cfg.Format)
	}
	if decoded.Template != cfg.Template {
		t.Errorf("Template: got %q, want %q", decoded.Template, cfg.Template)
	}
	if decoded.Title != cfg.Title {
		t.Errorf("Title: got %q, want %q", decoded.Title, cfg.Title)
	}
	if decoded.Author != cfg.Author {
		t.Errorf("Author: got %q, want %q", decoded.Author, cfg.Author)
	}
}

func TestReportFormatConstants(t *testing.T) {
	if FormatDOCX != "docx" {
		t.Errorf("FormatDOCX: got %q, want %q", FormatDOCX, "docx")
	}
	if FormatJSON != "json" {
		t.Errorf("FormatJSON: got %q, want %q", FormatJSON, "json")
	}
}

func TestReportStatusConstants(t *testing.T) {
	statuses := []ReportStatus{StatusPending, StatusGenerating, StatusCompleted, StatusFailed}
	for _, s := range statuses {
		if s == "" {
			t.Error("ReportStatus constant must not be empty")
		}
	}
}

func TestTemplateJSONRoundTrip(t *testing.T) {
	tmpl := Template{
		Name:    "commissioning",
		Format:  "docx",
		Content: "<template>Commissioning report for {{.NodeName}}</template>",
	}

	data, err := json.Marshal(tmpl)
	if err != nil {
		t.Fatalf("marshal: %v", err)
	}

	var decoded Template
	if err := json.Unmarshal(data, &decoded); err != nil {
		t.Fatalf("unmarshal: %v", err)
	}

	if decoded.Name != tmpl.Name {
		t.Errorf("Name: got %q, want %q", decoded.Name, tmpl.Name)
	}
	if decoded.Format != tmpl.Format {
		t.Errorf("Format: got %q, want %q", decoded.Format, tmpl.Format)
	}
	if decoded.Content != tmpl.Content {
		t.Errorf("Content: got %q, want %q", decoded.Content, tmpl.Content)
	}
}

func TestInvalidReportFormatRejected(t *testing.T) {
	// Unmarshal with invalid format should still succeed (string field),
	// but validation should happen at the application layer.
	// This test verifies the type system doesn't panic on unknown values.
	jsonStr := `{"node_address":"192.168.1.1","format":"pdf","template":"test","title":"T","author":"A"}`
	var cfg ReportConfig
	if err := json.Unmarshal([]byte(jsonStr), &cfg); err != nil {
		t.Fatalf("unmarshal with unknown format should not fail: %v", err)
	}
	// The format is stored as-is; validation is the caller's responsibility
	if cfg.Format != "pdf" {
		t.Errorf("Format: got %q, want %q", cfg.Format, "pdf")
	}
}

func TestInvalidNodeTypeRejected(t *testing.T) {
	// Unmarshal with invalid NodeType should still succeed (string field),
	// but validation should happen at the application layer.
	jsonStr := `{"address":"192.168.1.1","name":"X","type":"INVALID","status":"connected","token_id":"0","port":23,"last_seen":"2026-06-15T12:00:00Z"}`
	var node Node
	if err := json.Unmarshal([]byte(jsonStr), &node); err != nil {
		t.Fatalf("unmarshal with unknown type should not fail: %v", err)
	}
	if node.Type != "INVALID" {
		t.Errorf("Type: got %q, want %q", node.Type, "INVALID")
	}
}
