package store

import (
	"database/sql"
	"fmt"

	"github.com/falke-ai-circuit/LOGReport/internal/types"
)

// SaveTemplate inserts or replaces a template in the database.
func (s *Store) SaveTemplate(t *types.Template) error {
	query := `
	INSERT OR REPLACE INTO templates (name, format, content)
	VALUES (?, ?, ?)
	`
	_, err := s.db.Exec(query, t.Name, t.Format, t.Content)
	if err != nil {
		return fmt.Errorf("store: save template %s: %w", t.Name, err)
	}
	return nil
}

// GetTemplate retrieves a template by name. Returns an error if not found.
func (s *Store) GetTemplate(name string) (*types.Template, error) {
	query := `SELECT name, format, content FROM templates WHERE name = ?`
	row := s.db.QueryRow(query, name)

	t := &types.Template{}
	err := row.Scan(&t.Name, &t.Format, &t.Content)
	if err == sql.ErrNoRows {
		return nil, fmt.Errorf("store: template %s not found", name)
	}
	if err != nil {
		return nil, fmt.Errorf("store: get template %s: %w", name, err)
	}
	return t, nil
}

// ListTemplates returns all templates. Returns an empty slice (not nil) when none exist.
func (s *Store) ListTemplates() ([]*types.Template, error) {
	query := `SELECT name, format, content FROM templates ORDER BY name`
	rows, err := s.db.Query(query)
	if err != nil {
		return nil, fmt.Errorf("store: list templates: %w", err)
	}
	defer rows.Close()

	templates := make([]*types.Template, 0)
	for rows.Next() {
		t := &types.Template{}
		if err := rows.Scan(&t.Name, &t.Format, &t.Content); err != nil {
			return nil, fmt.Errorf("store: scan template: %w", err)
		}
		templates = append(templates, t)
	}
	if err := rows.Err(); err != nil {
		return nil, fmt.Errorf("store: rows iteration: %w", err)
	}
	return templates, nil
}

// DeleteTemplate removes a template by name. No error if it doesn't exist.
func (s *Store) DeleteTemplate(name string) error {
	_, err := s.db.Exec("DELETE FROM templates WHERE name = ?", name)
	if err != nil {
		return fmt.Errorf("store: delete template %s: %w", name, err)
	}
	return nil
}
