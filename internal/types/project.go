package types

// ProjectStatus represents the lifecycle state of a project.
type ProjectStatus string

const (
	ProjectActive   ProjectStatus = "active"
	ProjectArchived ProjectStatus = "archived"
)

// Project corresponds to a ship/work package like "T6004_ADORA_MEDITERANNEA".
// It groups a log root directory and node configuration so reports can be
// generated for the entire project in one call.
type Project struct {
	ID            int64         `json:"id"`
	ProjectNumber string        `json:"project_number"`
	ShipName      string        `json:"ship_name"`
	LogRoot       string        `json:"log_root"`
	NodesConfig   string        `json:"nodes_config,omitempty"` // JSON blob of nodes.json content
	Status        ProjectStatus `json:"status"`
	CreatedAt     string        `json:"created_at"`
	UpdatedAt     string        `json:"updated_at"`
}

// ProjectRequest is the JSON body for create/update project endpoints.
type ProjectRequest struct {
	ProjectNumber string        `json:"project_number"`
	ShipName      string        `json:"ship_name"`
	LogRoot       string        `json:"log_root"`
	NodesConfig   string        `json:"nodes_config,omitempty"`
	Status        ProjectStatus `json:"status,omitempty"`
}