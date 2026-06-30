package store

import (
	"fmt"
	"sort"

	"github.com/falke-ai-circuit/LOGReport/internal/types"
)

// SaveNode inserts or replaces a node in the store.
func (s *Store) SaveNode(n *types.Node) error {
	s.mu.Lock()
	defer s.mu.Unlock()

	// Store a copy to avoid external mutation
	cpy := *n
	s.nodes[n.Address] = &cpy

	if err := s.persistNodes(); err != nil {
		return fmt.Errorf("store: save node %s: %w", n.Address, err)
	}
	return nil
}

// GetNode retrieves a node by its address. Returns an error if not found.
func (s *Store) GetNode(address string) (*types.Node, error) {
	s.mu.RLock()
	defer s.mu.RUnlock()

	n, ok := s.nodes[address]
	if !ok {
		return nil, fmt.Errorf("store: node %s not found", address)
	}

	// Return a copy
	cpy := *n
	return &cpy, nil
}

// ListNodes returns all nodes sorted by address.
// Returns an empty slice (not nil) when no nodes exist.
func (s *Store) ListNodes() ([]*types.Node, error) {
	s.mu.RLock()
	defer s.mu.RUnlock()

	nodes := make([]*types.Node, 0, len(s.nodes))
	for _, n := range s.nodes {
		cpy := *n
		nodes = append(nodes, &cpy)
	}

	sort.Slice(nodes, func(i, j int) bool {
		return nodes[i].Address < nodes[j].Address
	})

	return nodes, nil
}

// DeleteNode removes a node by address. No error if the node doesn't exist.
func (s *Store) DeleteNode(address string) error {
	s.mu.Lock()
	defer s.mu.Unlock()

	delete(s.nodes, address)

	if err := s.persistNodes(); err != nil {
		return fmt.Errorf("store: delete node %s: %w", address, err)
	}
	return nil
}