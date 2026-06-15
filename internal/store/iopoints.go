package store

import (
	"database/sql"
	"fmt"

	"github.com/falke-ai-circuit/LOGReport/internal/types"
)

// SaveIOPoints batch-inserts IO points for a node. Uses a transaction
// for atomicity and performance.
func (s *Store) SaveIOPoints(nodeAddress string, points []types.IOPoint) error {
	tx, err := s.db.Begin()
	if err != nil {
		return fmt.Errorf("store: begin tx: %w", err)
	}
	defer tx.Rollback()

	// Delete existing points for this node first (clean slate)
	_, err = tx.Exec("DELETE FROM io_points WHERE node_address = ?", nodeAddress)
	if err != nil {
		return fmt.Errorf("store: delete old io_points for %s: %w", nodeAddress, err)
	}

	stmt, err := tx.Prepare(`
	INSERT INTO io_points
		(node_address, module_position, channel_position, channel_type, module_type, counter_name, counter_value)
	VALUES (?, ?, ?, ?, ?, ?, ?)
	`)
	if err != nil {
		return fmt.Errorf("store: prepare insert io_points: %w", err)
	}
	defer stmt.Close()

	for _, p := range points {
		var channelType interface{}
		if p.ChannelType != "" {
			channelType = string(p.ChannelType)
		}
		var counterName interface{}
		if p.CounterName != "" {
			counterName = p.CounterName
		}
		var counterValue interface{}
		if p.ModuleType == types.ModuleRPC {
			counterValue = p.CounterValue
		}

		_, err = stmt.Exec(
			nodeAddress,
			p.ModulePosition,
			p.ChannelPosition,
			channelType,
			string(p.ModuleType),
			counterName,
			counterValue,
		)
		if err != nil {
			return fmt.Errorf("store: insert io_point for %s: %w", nodeAddress, err)
		}
	}

	if err := tx.Commit(); err != nil {
		return fmt.Errorf("store: commit io_points: %w", err)
	}

	return nil
}

// GetIOPoints retrieves all IO points for a given node address.
// Returns an empty slice (not nil) when no points exist.
func (s *Store) GetIOPoints(nodeAddress string) ([]types.IOPoint, error) {
	query := `
	SELECT node_address, module_position, channel_position, channel_type, module_type, counter_name, counter_value
	FROM io_points WHERE node_address = ?
	ORDER BY module_position, channel_position
	`
	rows, err := s.db.Query(query, nodeAddress)
	if err != nil {
		return nil, fmt.Errorf("store: query io_points for %s: %w", nodeAddress, err)
	}
	defer rows.Close()

	points := make([]types.IOPoint, 0)
	for rows.Next() {
		var p types.IOPoint
		var channelType, moduleType sql.NullString
		var counterName sql.NullString
		var counterValue sql.NullInt64

		err := rows.Scan(
			&p.NodeAddress,
			&p.ModulePosition,
			&p.ChannelPosition,
			&channelType,
			&moduleType,
			&counterName,
			&counterValue,
		)
		if err != nil {
			return nil, fmt.Errorf("store: scan io_point: %w", err)
		}

		if channelType.Valid {
			p.ChannelType = types.ChannelType(channelType.String)
		}
		if moduleType.Valid {
			p.ModuleType = types.ModuleType(moduleType.String)
		}
		if counterName.Valid {
			p.CounterName = counterName.String
		}
		if counterValue.Valid {
			p.CounterValue = int(counterValue.Int64)
		}

		points = append(points, p)
	}

	if err := rows.Err(); err != nil {
		return nil, fmt.Errorf("store: rows iteration: %w", err)
	}

	return points, nil
}

// DeleteIOPoints removes all IO points for a given node address.
func (s *Store) DeleteIOPoints(nodeAddress string) error {
	_, err := s.db.Exec("DELETE FROM io_points WHERE node_address = ?", nodeAddress)
	if err != nil {
		return fmt.Errorf("store: delete io_points for %s: %w", nodeAddress, err)
	}
	return nil
}
