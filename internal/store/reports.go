package store

import (
	"database/sql"
	"fmt"

	"github.com/falke-ai-circuit/LOGReport/internal/types"
)

// SaveReport inserts or replaces a report record.
func (s *Store) SaveReport(r *types.Report) error {
	query := `
	INSERT OR REPLACE INTO reports
		(id, node_address, format, template, title, author, status, file_path, created_at, completed_at)
	VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
	`
	_, err := s.db.Exec(query,
		r.ID,
		r.NodeAddress,
		string(r.Format),
		r.Template,
		r.Title,
		r.Author,
		string(r.Status),
		r.FilePath,
		r.CreatedAt,
		r.CompletedAt,
	)
	if err != nil {
		return fmt.Errorf("store: save report %s: %w", r.ID, err)
	}
	return nil
}

// GetReport retrieves a report by its ID. Returns an error if not found.
func (s *Store) GetReport(id string) (*types.Report, error) {
	query := `
	SELECT id, node_address, format, template, title, author, status, file_path, created_at, completed_at
	FROM reports WHERE id = ?
	`
	row := s.db.QueryRow(query, id)

	r := &types.Report{}
	var formatStr, statusStr string
	var template, title, author, filePath, completedAt sql.NullString

	err := row.Scan(
		&r.ID,
		&r.NodeAddress,
		&formatStr,
		&template,
		&title,
		&author,
		&statusStr,
		&filePath,
		&r.CreatedAt,
		&completedAt,
	)
	if err == sql.ErrNoRows {
		return nil, fmt.Errorf("store: report %s not found", id)
	}
	if err != nil {
		return nil, fmt.Errorf("store: get report %s: %w", id, err)
	}

	r.Format = types.ReportFormat(formatStr)
	r.Status = types.ReportStatus(statusStr)
	if template.Valid {
		r.Template = template.String
	}
	if title.Valid {
		r.Title = title.String
	}
	if author.Valid {
		r.Author = author.String
	}
	if filePath.Valid {
		r.FilePath = filePath.String
	}
	if completedAt.Valid {
		r.CompletedAt = completedAt.String
	}

	return r, nil
}

// ListReports returns all reports. Returns an empty slice (not nil) when none exist.
func (s *Store) ListReports() ([]*types.Report, error) {
	query := `
	SELECT id, node_address, format, template, title, author, status, file_path, created_at, completed_at
	FROM reports ORDER BY created_at DESC
	`
	rows, err := s.db.Query(query)
	if err != nil {
		return nil, fmt.Errorf("store: list reports: %w", err)
	}
	defer rows.Close()

	reports := make([]*types.Report, 0)
	for rows.Next() {
		r := &types.Report{}
		var formatStr, statusStr string
		var template, title, author, filePath, completedAt sql.NullString

		err := rows.Scan(
			&r.ID,
			&r.NodeAddress,
			&formatStr,
			&template,
			&title,
			&author,
			&statusStr,
			&filePath,
			&r.CreatedAt,
			&completedAt,
		)
		if err != nil {
			return nil, fmt.Errorf("store: scan report: %w", err)
		}

		r.Format = types.ReportFormat(formatStr)
		r.Status = types.ReportStatus(statusStr)
		if template.Valid {
			r.Template = template.String
		}
		if title.Valid {
			r.Title = title.String
		}
		if author.Valid {
			r.Author = author.String
		}
		if filePath.Valid {
			r.FilePath = filePath.String
		}
		if completedAt.Valid {
			r.CompletedAt = completedAt.String
		}

		reports = append(reports, r)
	}

	if err := rows.Err(); err != nil {
		return nil, fmt.Errorf("store: rows iteration: %w", err)
	}

	return reports, nil
}

// DeleteReport removes a report by ID. No error if it doesn't exist.
func (s *Store) DeleteReport(id string) error {
	_, err := s.db.Exec("DELETE FROM reports WHERE id = ?", id)
	if err != nil {
		return fmt.Errorf("store: delete report %s: %w", id, err)
	}
	return nil
}
