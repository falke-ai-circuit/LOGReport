package store

import (
	"database/sql"
	"fmt"

	"github.com/falke-ai-circuit/LOGReport/internal/types"
)

// SaveNode inserts or replaces a node in the database.
func (s *Store) SaveNode(n *types.Node) error {
	query := `
	INSERT OR REPLACE INTO nodes
		(address, name, type, status, token_id, port, username, password, last_seen)
	VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
	`
	_, err := s.db.Exec(query,
		n.Address,
		n.Name,
		string(n.Type),
		string(n.Status),
		n.TokenID,
		n.Port,
		n.Username,
		n.Password,
		n.LastSeen.Format("2006-01-02T15:04:05Z07:00"),
	)
	if err != nil {
		return fmt.Errorf("store: save node %s: %w", n.Address, err)
	}
	return nil
}

// GetNode retrieves a node by its address. Returns an error if not found.
func (s *Store) GetNode(address string) (*types.Node, error) {
	query := `
	SELECT address, name, type, status, token_id, port, username, password, last_seen
	FROM nodes WHERE address = ?
	`
	row := s.db.QueryRow(query, address)

	n := &types.Node{}
	var typeStr, statusStr string
	var lastSeen sql.NullString
	var tokenID, username, password sql.NullString
	var port sql.NullInt64

	err := row.Scan(
		&n.Address,
		&n.Name,
		&typeStr,
		&statusStr,
		&tokenID,
		&port,
		&username,
		&password,
		&lastSeen,
	)
	if err == sql.ErrNoRows {
		return nil, fmt.Errorf("store: node %s not found", address)
	}
	if err != nil {
		return nil, fmt.Errorf("store: get node %s: %w", address, err)
	}

	n.Type = types.NodeType(typeStr)
	n.Status = types.NodeStatus(statusStr)
	if tokenID.Valid {
		n.TokenID = tokenID.String
	}
	if port.Valid {
		n.Port = int(port.Int64)
	} else {
		n.Port = 23
	}
	if username.Valid {
		n.Username = username.String
	}
	if password.Valid {
		n.Password = password.String
	}
	if lastSeen.Valid {
		t, err := parseTime(lastSeen.String)
		if err == nil {
			n.LastSeen = t
		}
	}

	return n, nil
}

// ListNodes returns all nodes. Returns an empty slice (not nil) when no nodes exist.
func (s *Store) ListNodes() ([]*types.Node, error) {
	query := `
	SELECT address, name, type, status, token_id, port, username, password, last_seen
	FROM nodes ORDER BY address
	`
	rows, err := s.db.Query(query)
	if err != nil {
		return nil, fmt.Errorf("store: list nodes: %w", err)
	}
	defer rows.Close()

	nodes := make([]*types.Node, 0)
	for rows.Next() {
		n := &types.Node{}
		var typeStr, statusStr string
		var lastSeen sql.NullString
		var tokenID, username, password sql.NullString
		var port sql.NullInt64

		err := rows.Scan(
			&n.Address,
			&n.Name,
			&typeStr,
			&statusStr,
			&tokenID,
			&port,
			&username,
			&password,
			&lastSeen,
		)
		if err != nil {
			return nil, fmt.Errorf("store: scan node: %w", err)
		}

		n.Type = types.NodeType(typeStr)
		n.Status = types.NodeStatus(statusStr)
		if tokenID.Valid {
			n.TokenID = tokenID.String
		}
		if port.Valid {
			n.Port = int(port.Int64)
		} else {
			n.Port = 23
		}
		if username.Valid {
			n.Username = username.String
		}
		if password.Valid {
			n.Password = password.String
		}
		if lastSeen.Valid {
			t, err := parseTime(lastSeen.String)
			if err == nil {
				n.LastSeen = t
			}
		}

		nodes = append(nodes, n)
	}

	if err := rows.Err(); err != nil {
		return nil, fmt.Errorf("store: rows iteration: %w", err)
	}

	return nodes, nil
}

// DeleteNode removes a node by address. No error if the node doesn't exist.
func (s *Store) DeleteNode(address string) error {
	_, err := s.db.Exec("DELETE FROM nodes WHERE address = ?", address)
	if err != nil {
		return fmt.Errorf("store: delete node %s: %w", address, err)
	}
	return nil
}
