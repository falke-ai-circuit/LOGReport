package types

// ReportFormat specifies the output format for generated reports.
type ReportFormat string

const (
	FormatDOCX ReportFormat = "docx"
	FormatJSON ReportFormat = "json"
)

// ReportStatus tracks the lifecycle of a report generation job.
type ReportStatus string

const (
	StatusPending    ReportStatus = "pending"
	StatusGenerating ReportStatus = "generating"
	StatusCompleted  ReportStatus = "completed"
	StatusFailed     ReportStatus = "failed"
)

// ReportConfig holds the parameters for generating a report.
type ReportConfig struct {
	NodeAddress string       `json:"node_address"`
	Format      ReportFormat `json:"format"`
	Template    string       `json:"template"`
	Title       string       `json:"title"`
	Author      string       `json:"author"`
}

// Template represents a report template definition.
type Template struct {
	Name    string `json:"name"`
	Format  string `json:"format"`
	Content string `json:"content"`
}
