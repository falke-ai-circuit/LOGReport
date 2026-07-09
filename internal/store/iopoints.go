package store

import (
	"fmt"
	"sort"

	"github.com/falke-ai-circuit/LOGReport/internal/types"
)

// SaveIOPoints batch-inserts IO points for a node. It replaces any existing
// points for the given node address.
func (s *Store) SaveIOPoints(nodeAddress string, points []types.IOPoint) error {
	s.mu.Lock()
	defer s.mu.Unlock()

	// Ensure each point has the node address set
	cleaned := make([]types.IOPoint, len(points))
	for i, p := range points {
		p.NodeAddress = nodeAddress
		cleaned[i] = p
	}

	s.ioPoints[nodeAddress] = cleaned

	if err := s.persistIOPoints(); err != nil {
		return fmt.Errorf("store: save io_points for %s: %w", nodeAddress, err)
	}

	return nil
}

// GetIOPoints retrieves all IO points for a given node address.
// Returns an empty slice (not nil) when no points exist.
func (s *Store) GetIOPoints(nodeAddress string) ([]types.IOPoint, error) {
	s.mu.RLock()
	defer s.mu.RUnlock()

	points, ok := s.ioPoints[nodeAddress]
	if !ok {
		return make([]types.IOPoint, 0), nil
	}

	// Return a copy to avoid mutation of internal state
	result := make([]types.IOPoint, len(points))
	copy(result, points)

	// Sort by module_position, then channel_position
	sort.Slice(result, func(i, j int) bool {
		if result[i].ModulePosition != result[j].ModulePosition {
			return result[i].ModulePosition < result[j].ModulePosition
		}
		return result[i].ChannelPosition < result[j].ChannelPosition
	})

	return result, nil
}

// DeleteIOPoints removes all IO points for a given node address.
func (s *Store) DeleteIOPoints(nodeAddress string) error {
	s.mu.Lock()
	defer s.mu.Unlock()

	delete(s.ioPoints, nodeAddress)

	if err := s.persistIOPoints(); err != nil {
		return fmt.Errorf("store: delete io_points for %s: %w", nodeAddress, err)
	}

	return nil
}