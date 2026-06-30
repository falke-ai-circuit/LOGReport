package store

import (
	"fmt"
	"log"
	"sort"

	"github.com/falke-ai-circuit/LOGReport/internal/types"
)

// SaveReport inserts or replaces a report record.
func (s *Store) SaveReport(r *types.Report) error {
	s.mu.Lock()
	defer s.mu.Unlock()

	// Store a copy
	cpy := *r
	s.reports[r.ID] = &cpy

	if err := s.persistReports(); err != nil {
		return fmt.Errorf("store: save report %s: %w", r.ID, err)
	}
	return nil
}

// GetReport retrieves a report by its ID. Returns an error if not found.
func (s *Store) GetReport(id string) (*types.Report, error) {
	s.mu.RLock()
	defer s.mu.RUnlock()

	r, ok := s.reports[id]
	if !ok {
		return nil, fmt.Errorf("store: report %s not found", id)
	}

	cpy := *r
	return &cpy, nil
}

// ListReports returns all reports sorted by created_at descending.
// Returns an empty slice (not nil) when none exist.
func (s *Store) ListReports() ([]*types.Report, error) {
	s.mu.RLock()
	defer s.mu.RUnlock()

	reports := make([]*types.Report, 0, len(s.reports))
	for _, r := range s.reports {
		cpy := *r
		reports = append(reports, &cpy)
	}

	sort.Slice(reports, func(i, j int) bool {
		return reports[i].CreatedAt > reports[j].CreatedAt
	})

	return reports, nil
}

// DeleteReport removes a report by ID. No error if it doesn't exist.
func (s *Store) DeleteReport(id string) error {
	s.mu.Lock()
	defer s.mu.Unlock()

	delete(s.reports, id)

	if err := s.persistReports(); err != nil {
		return fmt.Errorf("store: delete report %s: %w", id, err)
	}
	return nil
}

// ListReportsByProject returns all reports for a given project ID,
// sorted by created_at descending.
func (s *Store) ListReportsByProject(projectID int64) []*types.Report {
	s.mu.RLock()
	defer s.mu.RUnlock()

	var reports []*types.Report
	for _, r := range s.reports {
		if r.ProjectID == projectID {
			cpy := *r
			reports = append(reports, &cpy)
		}
	}

	if reports == nil {
		reports = []*types.Report{}
	}

	sort.Slice(reports, func(i, j int) bool {
		return reports[i].CreatedAt > reports[j].CreatedAt
	})

	if len(reports) == 0 {
		log.Printf("store: ListReportsByProject: no reports for project %d", projectID)
	}

	return reports
}