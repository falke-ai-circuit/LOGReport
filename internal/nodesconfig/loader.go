// Package nodesconfig loads and saves the nodes.json configuration file
// and builds a hierarchical tree structure for the frontend Commander node tree.
//
// The nodes.json format is an array of NodeConfig objects, each containing
// a node name, IP address, and a list of tokens (FBC/RPC/LOG/LIS/FTP).
package nodesconfig

import (
	"encoding/json"
	"fmt"
	"os"
	"sort"

	"github.com/falke-ai-circuit/LOGReport/internal/types"
)

// LoadFromFile parses nodes.json from the given file path.
// Returns a slice of NodeConfig.
func LoadFromFile(path string) ([]types.NodeConfig, error) {
	data, err := os.ReadFile(path)
	if err != nil {
		return nil, fmt.Errorf("nodesconfig: read %s: %w", path, err)
	}
	return LoadFromBytes(data)
}

// LoadFromBytes parses nodes.json from a byte slice.
// Returns a slice of NodeConfig. Always returns a non-nil slice.
func LoadFromBytes(data []byte) ([]types.NodeConfig, error) {
	configs := make([]types.NodeConfig, 0)
	if err := json.Unmarshal(data, &configs); err != nil {
		return nil, fmt.Errorf("nodesconfig: unmarshal: %w", err)
	}
	// Ensure each config has a non-nil token slice
	for i := range configs {
		if configs[i].Tokens == nil {
			configs[i].Tokens = make([]types.Token, 0)
		}
	}
	return configs, nil
}

// SaveToFile writes a NodeConfig array to the given file path as JSON.
func SaveToFile(path string, configs []types.NodeConfig) error {
	data, err := json.MarshalIndent(configs, "", "    ")
	if err != nil {
		return fmt.Errorf("nodesconfig: marshal: %w", err)
	}
	if err := os.WriteFile(path, data, 0644); err != nil {
		return fmt.Errorf("nodesconfig: write %s: %w", path, err)
	}
	return nil
}

// BuildTree converts a flat NodeConfig list into a hierarchical tree
// for the frontend: root → node → token-type groups → token leaves.
//
// The returned TreeNode is a virtual root with node children.
func BuildTree(configs []types.NodeConfig) *types.TreeNode {
	root := &types.TreeNode{
		Name:     "Root",
		Type:     "root",
		Children: make([]types.TreeNode, 0),
	}

	// Stable ordering of group types
	groupOrder := []string{"FBC", "RPC", "LOG", "LIS", "FTP"}

	for _, cfg := range configs {
		nodeChild := types.TreeNode{
			Name:     cfg.Name,
			Type:     "node",
			IP:       cfg.IPAddress,
			Status:   "idle",
			Children: make([]types.TreeNode, 0),
		}

		// Group tokens by type
		groups := make(map[string][]types.Token)
		for _, tok := range cfg.Tokens {
			groups[string(tok.TokenType)] = append(groups[string(tok.TokenType)], tok)
		}

		// Add groups in canonical order
		for _, gType := range groupOrder {
			tokens, ok := groups[gType]
			if !ok {
				continue
			}
			// Sort tokens within a group by token_id for stable output
			sort.Slice(tokens, func(i, j int) bool {
				return tokens[i].TokenID < tokens[j].TokenID
			})

			groupNode := types.TreeNode{
				Name:     gType,
				Type:     "group",
				Children: make([]types.TreeNode, 0),
			}
			for _, tok := range tokens {
				groupNode.Children = append(groupNode.Children, types.TreeNode{
					Name:     tok.TokenID,
					Type:     "token",
					TokenID:  tok.TokenID,
					Port:     tok.Port,
					Protocol: tok.Protocol,
				})
			}
			nodeChild.Children = append(nodeChild.Children, groupNode)
		}

		root.Children = append(root.Children, nodeChild)
	}

	return root
}