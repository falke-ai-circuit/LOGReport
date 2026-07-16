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

// ReportAppearance holds font and layout settings for PDF/DOCX report generation.
// These are optional — empty/zero values fall back to defaults.
type ReportAppearance struct {
	FontFamily   string `json:"font_family,omitempty"`    // "Courier" (default), "Helvetica", "Times"
	FontSize     int    `json:"font_size,omitempty"`      // 8-14, default 10
	LineSpacing  int    `json:"line_spacing,omitempty"`   // 8-20 (leading in points), default 12
	MarginMM     int    `json:"margin_mm,omitempty"`       // page margins in mm, default 20
	WrapWidth    int    `json:"wrap_width,omitempty"`      // chars per line, default 80
	IncludeFBC   *bool  `json:"include_fbc,omitempty"`     // include FBC files, default true
	IncludeRPC   *bool  `json:"include_rpc,omitempty"`    // include RPC files, default true
	IncludeLOG   *bool  `json:"include_log,omitempty"`     // include LOG files, default true
	IncludeLIS  *bool  `json:"include_lis,omitempty"`     // include LIS files, default true
	ShowHeader   *bool  `json:"show_header,omitempty"`     // page header with project name + page number, default true
	ShowLogo     *bool  `json:"show_logo,omitempty"`       // Valmet logo on title page, default true
}

// ReportConfig holds the parameters for generating a report.
type ReportConfig struct {
	NodeAddress   string           `json:"node_address"`
	Format        ReportFormat     `json:"format"`
	Template      string          `json:"template"`
	Title         string           `json:"title"`
	Author        string           `json:"author"`
	LogRoot       string           `json:"log_root"`              // root directory for log files (optional)
	ReportType    string           `json:"report_type,omitempty"` // "survey" or "drydock"
	ProjectID     int64            `json:"project_id,omitempty"`  // associated project
	ProjectNumber string           `json:"project_number,omitempty"` // e.g. "T6004"
	ShipName      string           `json:"ship_name,omitempty"`    // e.g. "ADORA MEDITERANNEA"
	OutputDir     string           `json:"output_dir,omitempty"`   // directory for report output (defaults to temp)
	Appearance    *ReportAppearance `json:"appearance,omitempty"`  // font/layout settings (optional)
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
