package store

import (
	"fmt"
	"sort"

	"github.com/falke-ai-circuit/LOGReport/internal/types"
)

// SaveTemplate inserts or replaces a template in the store.
func (s *Store) SaveTemplate(t *types.Template) error {
	s.mu.Lock()
	defer s.mu.Unlock()

	cpy := *t
	s.templates[t.Name] = &cpy

	if err := s.persistTemplates(); err != nil {
		return fmt.Errorf("store: save template %s: %w", t.Name, err)
	}
	return nil
}

// GetTemplate retrieves a template by name. Returns an error if not found.
func (s *Store) GetTemplate(name string) (*types.Template, error) {
	s.mu.RLock()
	defer s.mu.RUnlock()

	t, ok := s.templates[name]
	if !ok {
		return nil, fmt.Errorf("store: template %s not found", name)
	}

	cpy := *t
	return &cpy, nil
}

// ListTemplates returns all templates sorted by name.
// Returns an empty slice (not nil) when none exist.
func (s *Store) ListTemplates() ([]*types.Template, error) {
	s.mu.RLock()
	defer s.mu.RUnlock()

	templates := make([]*types.Template, 0, len(s.templates))
	for _, t := range s.templates {
		cpy := *t
		templates = append(templates, &cpy)
	}

	sort.Slice(templates, func(i, j int) bool {
		return templates[i].Name < templates[j].Name
	})

	return templates, nil
}

// DeleteTemplate removes a template by name. No error if it doesn't exist.
func (s *Store) DeleteTemplate(name string) error {
	s.mu.Lock()
	defer s.mu.Unlock()

	delete(s.templates, name)

	if err := s.persistTemplates(); err != nil {
		return fmt.Errorf("store: delete template %s: %w", name, err)
	}
	return nil
}