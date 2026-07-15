package store

import (
	"fmt"
	"sort"
	"time"

	"github.com/falke-ai-circuit/LOGReport/internal/types"
)

// CreateProject inserts a new project and returns the created record with
// the assigned ID and timestamps.
func (s *Store) CreateProject(p *types.Project) (*types.Project, error) {
	s.mu.Lock()
	defer s.mu.Unlock()

	if p.Status == "" {
		p.Status = types.ProjectActive
	}

	p.ID = s.meta.NextProjectID
	s.meta.NextProjectID++

	now := time.Now().Format("2006-01-02T15:04:05Z07:00")
	p.CreatedAt = now
	p.UpdatedAt = now

	// Store a copy
	cpy := *p
	s.projects[p.ID] = &cpy

	if err := s.persistProjects(); err != nil {
		return nil, fmt.Errorf("store: create project: %w", err)
	}
	if err := s.persistMeta(); err != nil {
		return nil, fmt.Errorf("store: create project (meta): %w", err)
	}

	// Return the copy
	result := cpy
	return &result, nil
}

// GetProject retrieves a project by ID. Returns an error if not found.
func (s *Store) GetProject(id int64) (*types.Project, error) {
	s.mu.RLock()
	defer s.mu.RUnlock()

	p, ok := s.projects[id]
	if !ok {
		return nil, fmt.Errorf("store: project %d not found", id)
	}

	cpy := *p
	return &cpy, nil
}

// ListProjects returns all projects ordered by project_number.
// Returns an empty slice (not nil) when no projects exist.
func (s *Store) ListProjects() ([]*types.Project, error) {
	s.mu.RLock()
	defer s.mu.RUnlock()

	projects := make([]*types.Project, 0, len(s.projects))
	for _, p := range s.projects {
		cpy := *p
		projects = append(projects, &cpy)
	}

	sort.Slice(projects, func(i, j int) bool {
		return projects[i].ProjectNumber < projects[j].ProjectNumber
	})

	return projects, nil
}

// UpdateProject updates an existing project identified by ID.
// Only non-empty fields in the request are updated.
func (s *Store) UpdateProject(id int64, p *types.Project) (*types.Project, error) {
	s.mu.Lock()
	defer s.mu.Unlock()

	existing, ok := s.projects[id]
	if !ok {
		return nil, fmt.Errorf("store: project %d not found", id)
	}

	// Update fields
	existing.ProjectNumber = p.ProjectNumber
	existing.ShipName = p.ShipName
	existing.LogRoot = p.LogRoot
	existing.NodesConfig = p.NodesConfig
	existing.SettingsJSON = p.SettingsJSON
	if p.Status != "" {
		existing.Status = p.Status
	}
	existing.UpdatedAt = time.Now().Format("2006-01-02T15:04:05Z07:00")

	if err := s.persistProjects(); err != nil {
		return nil, fmt.Errorf("store: update project %d: %w", id, err)
	}

	cpy := *existing
	return &cpy, nil
}

// DeleteProject removes a project by ID. No error if the project doesn't exist.
func (s *Store) DeleteProject(id int64) error {
	s.mu.Lock()
	defer s.mu.Unlock()

	delete(s.projects, id)

	if err := s.persistProjects(); err != nil {
		return fmt.Errorf("store: delete project %d: %w", id, err)
	}
	return nil
}

// EnsureProjectsTable is a no-op for the JSON store.
// Kept for API compatibility with existing callers.
func (s *Store) EnsureProjectsTable() error {
	return nil
}