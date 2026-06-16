package store

import (
	"testing"

	"github.com/falke-ai-circuit/LOGReport/internal/types"
)

// TestSaveGetTemplateRoundTrip tests SaveTemplate → GetTemplate round-trip.
func TestSaveGetTemplateRoundTrip(t *testing.T) {
	s := openTestStore(t)

	tmpl := &types.Template{
		Name:    "commissioning",
		Format:  "docx",
		Content: "Commissioning report template for {{.NodeName}}",
	}

	if err := s.SaveTemplate(tmpl); err != nil {
		t.Fatalf("SaveTemplate: %v", err)
	}

	got, err := s.GetTemplate("commissioning")
	if err != nil {
		t.Fatalf("GetTemplate: %v", err)
	}

	if got.Name != tmpl.Name {
		t.Errorf("Name: got %q, want %q", got.Name, tmpl.Name)
	}
	if got.Format != tmpl.Format {
		t.Errorf("Format: got %q, want %q", got.Format, tmpl.Format)
	}
	if got.Content != tmpl.Content {
		t.Errorf("Content: got %q, want %q", got.Content, tmpl.Content)
	}
}

// TestGetTemplateNotFound verifies GetTemplate returns error for non-existent template.
func TestGetTemplateNotFound(t *testing.T) {
	s := openTestStore(t)

	_, err := s.GetTemplate("nonexistent")
	if err == nil {
		t.Error("GetTemplate: expected error for non-existent template, got nil")
	}
}

// TestListTemplates verifies ListTemplates returns all templates.
func TestListTemplates(t *testing.T) {
	s := openTestStore(t)

	// Empty list
	templates, err := s.ListTemplates()
	if err != nil {
		t.Fatalf("ListTemplates empty: %v", err)
	}
	if templates == nil {
		t.Error("ListTemplates returned nil, want empty slice")
	}
	if len(templates) != 0 {
		t.Errorf("ListTemplates empty: got %d templates, want 0", len(templates))
	}

	// Add templates
	s.SaveTemplate(&types.Template{Name: "default", Format: "docx", Content: "Default template"})
	s.SaveTemplate(&types.Template{Name: "custom", Format: "json", Content: "Custom template"})

	templates, err = s.ListTemplates()
	if err != nil {
		t.Fatalf("ListTemplates: %v", err)
	}
	if len(templates) != 2 {
		t.Errorf("ListTemplates: got %d templates, want 2", len(templates))
	}

	// Verify ordering (by name)
	if templates[0].Name != "custom" {
		t.Errorf("first template: got %q, want custom", templates[0].Name)
	}
	if templates[1].Name != "default" {
		t.Errorf("second template: got %q, want default", templates[1].Name)
	}
}

// TestDeleteTemplate verifies DeleteTemplate removes a template.
func TestDeleteTemplate(t *testing.T) {
	s := openTestStore(t)

	tmpl := &types.Template{
		Name:    "to-delete",
		Format:  "docx",
		Content: "Will be deleted",
	}
	if err := s.SaveTemplate(tmpl); err != nil {
		t.Fatalf("SaveTemplate: %v", err)
	}

	// Verify it exists
	_, err := s.GetTemplate("to-delete")
	if err != nil {
		t.Fatalf("GetTemplate before delete: %v", err)
	}

	// Delete
	if err := s.DeleteTemplate("to-delete"); err != nil {
		t.Fatalf("DeleteTemplate: %v", err)
	}

	// Verify it's gone
	_, err = s.GetTemplate("to-delete")
	if err == nil {
		t.Error("GetTemplate after delete: expected error, got nil")
	}
}

// TestDeleteTemplateNonExistent verifies DeleteTemplate doesn't error on non-existent.
func TestDeleteTemplateNonExistent(t *testing.T) {
	s := openTestStore(t)

	// Should not error
	if err := s.DeleteTemplate("nonexistent"); err != nil {
		t.Errorf("DeleteTemplate non-existent: unexpected error: %v", err)
	}
}

// TestSaveTemplateUpdate verifies that saving a template twice updates it.
func TestSaveTemplateUpdate(t *testing.T) {
	s := openTestStore(t)

	tmpl1 := &types.Template{
		Name:    "update-test",
		Format:  "docx",
		Content: "Version 1",
	}
	if err := s.SaveTemplate(tmpl1); err != nil {
		t.Fatalf("SaveTemplate 1: %v", err)
	}

	tmpl2 := &types.Template{
		Name:    "update-test",
		Format:  "json",
		Content: "Version 2",
	}
	if err := s.SaveTemplate(tmpl2); err != nil {
		t.Fatalf("SaveTemplate 2: %v", err)
	}

	got, err := s.GetTemplate("update-test")
	if err != nil {
		t.Fatalf("GetTemplate: %v", err)
	}

	if got.Format != "json" {
		t.Errorf("Format: got %q, want json", got.Format)
	}
	if got.Content != "Version 2" {
		t.Errorf("Content: got %q, want Version 2", got.Content)
	}
}

// TestCascadeDeleteNodeDeletesIOPoints verifies that deleting a node
// cascades to delete its IO points (ON DELETE CASCADE).
func TestCascadeDeleteNodeDeletesIOPoints(t *testing.T) {
	s := openTestStore(t)

	// Create node
	n := &types.Node{
		Address: "10.0.0.50",
		Name:    "CascadeNode",
		Type:    types.ACN,
		Status:  types.StatusConnected,
		Port:    23,
	}
	if err := s.SaveNode(n); err != nil {
		t.Fatalf("SaveNode: %v", err)
	}

	// Add IO points
	points := []types.IOPoint{
		{NodeAddress: "10.0.0.50", ModulePosition: 1, ChannelPosition: 1, ChannelType: types.AI8, ModuleType: types.ModuleFBC},
		{NodeAddress: "10.0.0.50", ModulePosition: 1, ChannelPosition: 2, ChannelType: types.BI8, ModuleType: types.ModuleFBC},
	}
	if err := s.SaveIOPoints("10.0.0.50", points); err != nil {
		t.Fatalf("SaveIOPoints: %v", err)
	}

	// Verify IO points exist
	got, err := s.GetIOPoints("10.0.0.50")
	if err != nil {
		t.Fatalf("GetIOPoints before delete: %v", err)
	}
	if len(got) != 2 {
		t.Fatalf("expected 2 IO points, got %d", len(got))
	}

	// Delete node — should cascade delete IO points
	if err := s.DeleteNode("10.0.0.50"); err != nil {
		t.Fatalf("DeleteNode: %v", err)
	}

	// Verify IO points are gone
	got, err = s.GetIOPoints("10.0.0.50")
	if err != nil {
		t.Fatalf("GetIOPoints after cascade delete: %v", err)
	}
	if len(got) != 0 {
		t.Errorf("expected 0 IO points after cascade delete, got %d", len(got))
	}
}

// TestEmptyBatchSaveIOPoints verifies saving empty batch doesn't error.
func TestEmptyBatchSaveIOPoints(t *testing.T) {
	s := openTestStore(t)

	// Create node
	n := &types.Node{
		Address: "10.0.0.60",
		Name:    "EmptyBatchNode",
		Type:    types.ACN,
		Status:  types.StatusConnected,
		Port:    23,
	}
	if err := s.SaveNode(n); err != nil {
		t.Fatalf("SaveNode: %v", err)
	}

	// Save empty batch
	if err := s.SaveIOPoints("10.0.0.60", []types.IOPoint{}); err != nil {
		t.Fatalf("SaveIOPoints empty batch: %v", err)
	}

	// Verify no points
	got, err := s.GetIOPoints("10.0.0.60")
	if err != nil {
		t.Fatalf("GetIOPoints: %v", err)
	}
	if len(got) != 0 {
		t.Errorf("expected 0 points, got %d", len(got))
	}
}

// TestListReportsWithData verifies ListReports returns reports when they exist.
func TestListReportsWithData(t *testing.T) {
	s := openTestStore(t)

	r1 := &types.Report{
		ID:          "rpt-001",
		NodeAddress: "10.0.0.1",
		Format:      types.FormatDOCX,
		Status:      types.StatusCompleted,
		CreatedAt:   "2026-06-15T10:00:00Z",
	}
	r2 := &types.Report{
		ID:          "rpt-002",
		NodeAddress: "10.0.0.2",
		Format:      types.FormatJSON,
		Status:      types.StatusPending,
		CreatedAt:   "2026-06-15T11:00:00Z",
	}

	if err := s.SaveReport(r1); err != nil {
		t.Fatalf("SaveReport r1: %v", err)
	}
	if err := s.SaveReport(r2); err != nil {
		t.Fatalf("SaveReport r2: %v", err)
	}

	reports, err := s.ListReports()
	if err != nil {
		t.Fatalf("ListReports: %v", err)
	}
	if len(reports) != 2 {
		t.Errorf("ListReports: got %d reports, want 2", len(reports))
	}

	// Verify ordering (by created_at DESC)
	if reports[0].ID != "rpt-002" {
		t.Errorf("first report: got %q, want rpt-002 (newest first)", reports[0].ID)
	}
	if reports[1].ID != "rpt-001" {
		t.Errorf("second report: got %q, want rpt-001", reports[1].ID)
	}
}

// TestSaveReportWithNullFields verifies saving a report with minimal fields.
func TestSaveReportWithNullFields(t *testing.T) {
	s := openTestStore(t)

	r := &types.Report{
		ID:          "rpt-minimal",
		NodeAddress: "10.0.0.1",
		Format:      types.FormatJSON,
		Status:      types.StatusPending,
		CreatedAt:   "2026-06-15T10:00:00Z",
	}

	if err := s.SaveReport(r); err != nil {
		t.Fatalf("SaveReport: %v", err)
	}

	got, err := s.GetReport("rpt-minimal")
	if err != nil {
		t.Fatalf("GetReport: %v", err)
	}

	if got.Template != "" {
		t.Errorf("Template: got %q, want empty", got.Template)
	}
	if got.Title != "" {
		t.Errorf("Title: got %q, want empty", got.Title)
	}
	if got.Author != "" {
		t.Errorf("Author: got %q, want empty", got.Author)
	}
	if got.FilePath != "" {
		t.Errorf("FilePath: got %q, want empty", got.FilePath)
	}
	if got.CompletedAt != "" {
		t.Errorf("CompletedAt: got %q, want empty", got.CompletedAt)
	}
}

// TestDeleteNodeNonExistent verifies DeleteNode doesn't error on non-existent.
func TestDeleteNodeNonExistent(t *testing.T) {
	s := openTestStore(t)

	if err := s.DeleteNode("nonexistent"); err != nil {
		t.Errorf("DeleteNode non-existent: unexpected error: %v", err)
	}
}

// TestDeleteReportNonExistent verifies DeleteReport doesn't error on non-existent.
func TestDeleteReportNonExistent(t *testing.T) {
	s := openTestStore(t)

	if err := s.DeleteReport("nonexistent"); err != nil {
		t.Errorf("DeleteReport non-existent: unexpected error: %v", err)
	}
}

// TestDeleteIOPointsNonExistent verifies DeleteIOPoints doesn't error on non-existent.
func TestDeleteIOPointsNonExistent(t *testing.T) {
	s := openTestStore(t)

	if err := s.DeleteIOPoints("nonexistent"); err != nil {
		t.Errorf("DeleteIOPoints non-existent: unexpected error: %v", err)
	}
}

// TestDBMethod verifies the DB() accessor returns the underlying sql.DB.
func TestDBMethod(t *testing.T) {
	s := openTestStore(t)

	db := s.DB()
	if db == nil {
		t.Error("DB() returned nil")
	}

	// Verify we can ping through it
	if err := db.Ping(); err != nil {
		t.Errorf("DB().Ping(): %v", err)
	}
}

// TestParseTime verifies parseTime handles various formats.
func TestParseTime(t *testing.T) {
	tests := []struct {
		name  string
		input string
		valid bool
	}{
		{"RFC3339", "2026-06-15T12:00:00Z", true},
		{"ISO with offset", "2026-06-15T12:00:00+02:00", true},
		{"space separator", "2026-06-15 12:00:00", true},
		{"T separator no TZ", "2026-06-15T12:00:00", true},
		{"date only", "2026-06-15", true},
		{"invalid", "not-a-date", false},
		{"empty", "", false},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			tm, err := parseTime(tt.input)
			if tt.valid {
				if err != nil {
					t.Errorf("parseTime(%q): unexpected error: %v", tt.input, err)
				}
				if tm.IsZero() {
					t.Errorf("parseTime(%q): returned zero time", tt.input)
				}
			} else {
				// parseTime returns zero time on failure, not error
				if !tm.IsZero() {
					t.Errorf("parseTime(%q): expected zero time, got %v", tt.input, tm)
				}
			}
		})
	}
}
