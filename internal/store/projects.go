package store

import (
	"database/sql"
	"fmt"

	"github.com/falke-ai-circuit/LOGReport/internal/types"
)

// CreateProject inserts a new project and returns the created record with
// the assigned ID and timestamps.
func (s *Store) CreateProject(p *types.Project) (*types.Project, error) {
	if p.Status == "" {
		p.Status = types.ProjectActive
	}

	query := `
INSERT INTO projects (project_number, ship_name, log_root, nodes_config, status)
VALUES (?, ?, ?, ?, ?)
`
	res, err := s.db.Exec(query, p.ProjectNumber, p.ShipName, p.LogRoot, p.NodesConfig, string(p.Status))
	if err != nil {
		return nil, fmt.Errorf("store: create project: %w", err)
	}

	id, err := res.LastInsertId()
	if err != nil {
		return nil, fmt.Errorf("store: create project last insert id: %w", err)
	}
	p.ID = id

	// Read back the generated timestamps
	got, err := s.GetProject(id)
	if err != nil {
		return nil, fmt.Errorf("store: read back project %d: %w", id, err)
	}
	p.CreatedAt = got.CreatedAt
	p.UpdatedAt = got.UpdatedAt

	return p, nil
}

// GetProject retrieves a project by ID. Returns an error if not found.
func (s *Store) GetProject(id int64) (*types.Project, error) {
	query := `
SELECT id, project_number, ship_name, log_root, nodes_config, status, created_at, updated_at
FROM projects WHERE id = ?
`
	row := s.db.QueryRow(query, id)

	p := &types.Project{}
	var nodesConfig sql.NullString
	var logRoot sql.NullString

	err := row.Scan(
		&p.ID,
		&p.ProjectNumber,
		&p.ShipName,
		&logRoot,
		&nodesConfig,
		&p.Status,
		&p.CreatedAt,
		&p.UpdatedAt,
	)
	if err == sql.ErrNoRows {
		return nil, fmt.Errorf("store: project %d not found", id)
	}
	if err != nil {
		return nil, fmt.Errorf("store: get project %d: %w", id, err)
	}

	if logRoot.Valid {
		p.LogRoot = logRoot.String
	}
	if nodesConfig.Valid {
		p.NodesConfig = nodesConfig.String
	}

	return p, nil
}

// ListProjects returns all projects ordered by project_number.
// Returns an empty slice (not nil) when no projects exist.
func (s *Store) ListProjects() ([]*types.Project, error) {
	query := `
SELECT id, project_number, ship_name, log_root, nodes_config, status, created_at, updated_at
FROM projects ORDER BY project_number
`
	rows, err := s.db.Query(query)
	if err != nil {
		return nil, fmt.Errorf("store: list projects: %w", err)
	}
	defer rows.Close()

	projects := make([]*types.Project, 0)
	for rows.Next() {
		p := &types.Project{}
		var nodesConfig sql.NullString
		var logRoot sql.NullString

		err := rows.Scan(
			&p.ID,
			&p.ProjectNumber,
			&p.ShipName,
			&logRoot,
			&nodesConfig,
			&p.Status,
			&p.CreatedAt,
			&p.UpdatedAt,
		)
		if err != nil {
			return nil, fmt.Errorf("store: scan project: %w", err)
		}

		if logRoot.Valid {
			p.LogRoot = logRoot.String
		}
		if nodesConfig.Valid {
			p.NodesConfig = nodesConfig.String
		}

		projects = append(projects, p)
	}

	if err := rows.Err(); err != nil {
		return nil, fmt.Errorf("store: rows iteration: %w", err)
	}

	return projects, nil
}

// UpdateProject updates an existing project identified by ID.
// Only non-empty fields in the request are updated.
func (s *Store) UpdateProject(id int64, p *types.Project) (*types.Project, error) {
	query := `
UPDATE projects
SET project_number = ?, ship_name = ?, log_root = ?, nodes_config = ?, status = ?, updated_at = CURRENT_TIMESTAMP
WHERE id = ?
`
	_, err := s.db.Exec(query, p.ProjectNumber, p.ShipName, p.LogRoot, p.NodesConfig, string(p.Status), id)
	if err != nil {
		return nil, fmt.Errorf("store: update project %d: %w", id, err)
	}

	return s.GetProject(id)
}

// DeleteProject removes a project by ID. No error if the project doesn't exist.
func (s *Store) DeleteProject(id int64) error {
	_, err := s.db.Exec("DELETE FROM projects WHERE id = ?", id)
	if err != nil {
		return fmt.Errorf("store: delete project %d: %w", id, err)
	}
	return nil
}

// EnsureProjectsTable creates the projects table if it doesn't exist.
// Called during migration to add the projects table to existing databases.
func (s *Store) EnsureProjectsTable() error {
	schema := `
CREATE TABLE IF NOT EXISTS projects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_number TEXT NOT NULL,
    ship_name TEXT NOT NULL,
    log_root TEXT,
    nodes_config TEXT,
    status TEXT DEFAULT 'active',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
`
	_, err := s.db.Exec(schema)
	if err != nil {
		return fmt.Errorf("store: ensure projects table: %w", err)
	}
	return nil
}