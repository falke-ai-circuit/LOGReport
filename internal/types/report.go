package types

// ReportFormat specifies the output format for generated reports.
type ReportFormat string

const (
	FormatDOCX ReportFormat = "docx"
	FormatJSON ReportFormat = "json"
	FormatPDF  ReportFormat = "pdf"
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
	LogRoot     string       `json:"log_root"` // root directory for log files (optional)
	ReportType  string       `json:"report_type,omitempty"` // "survey" or "drydock"
	ProjectID   int64        `json:"project_id,omitempty"` // associated project
}

// Report represents a generated report record stored in the database.
type Report struct {
	ID          string       `json:"id"`
	NodeAddress string       `json:"node_address"`
	Format      ReportFormat `json:"format"`
	Template    string       `json:"template,omitempty"`
	Title       string       `json:"title,omitempty"`
	Author      string       `json:"author,omitempty"`
	Status      ReportStatus `json:"status"`
	FilePath    string       `json:"file_path,omitempty"`
	CreatedAt   string       `json:"created_at"`
	CompletedAt string       `json:"completed_at,omitempty"`
	ReportType  string       `json:"report_type,omitempty"`
	ProjectID   int64         `json:"project_id,omitempty"`
}

// Template represents a report template definition.
type Template struct {
	Name    string `json:"name"`
	Format  string `json:"format"`
	Content string `json:"content"`
}
