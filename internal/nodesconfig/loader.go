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
	"path/filepath"
	"sort"
	"strings"

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

// BuildFileTree builds a tree that includes actual log files from the log root
// directory, matching the Python app's behavior where the tree shows:
//   station → FBC/RPC/LOG sections → individual files (with filenames)
//
// All slots of a station are grouped under a single station node.
// e.g. AP01m → FBC → AP01_...161.fbc, AP01_m2_...162.fbc, AP01_m3_...163.fbc
//
// This is the tree the frontend Commander uses for context menus and double-click.
// If logRoot is empty or doesn't exist, falls back to the token-only tree.
func BuildFileTree(configs []types.NodeConfig, logRoot string) *types.TreeNode {
	// If no log root, use the basic token tree
	if logRoot == "" {
		return BuildTree(configs)
	}
	if _, err := os.Stat(logRoot); err != nil {
		return BuildTree(configs)
	}

	root := &types.TreeNode{
		Name:     "Root",
		Type:     "root",
		Children: make([]types.TreeNode, 0),
	}

	groupOrder := []string{"FBC", "RPC", "LOG", "LIS"}

	// Group configs by station name, preserving discovery order
	stationOrder := make([]string, 0)
	stationConfigs := make(map[string][]types.NodeConfig)
	for _, cfg := range configs {
		station := extractStationName(cfg.Name)
		if _, exists := stationConfigs[station]; !exists {
			stationOrder = append(stationOrder, station)
		}
		stationConfigs[station] = append(stationConfigs[station], cfg)
	}

	for _, stationName := range stationOrder {
		memberCfgs := stationConfigs[stationName]

		stationNode := types.TreeNode{
			Name:     stationName,
			Type:     "node",
			Children: make([]types.TreeNode, 0),
		}

		for _, gType := range groupOrder {
			sectionNode := types.TreeNode{
				Name:       gType,
				Type:       "group",
				SectionType: gType,
				Children:   make([]types.TreeNode, 0),
			}

			// Scan for files of this type for all member nodes of this station
			// FBC dir: {logRoot}/FBC/{stationName}/
			// RPC dir: {logRoot}/RPC/{stationName}/
			// LOG dir: {logRoot}/LOG/  (flat, filenames start with any member node name)
			// LIS dir: {logRoot}/LIS/{stationName}/
			var scanDir string
			if gType == "LOG" {
				scanDir = filepath.Join(logRoot, stationName, "LOG")
			} else {
				scanDir = filepath.Join(logRoot, stationName, gType)
			}

			entries, err := os.ReadDir(scanDir)
			if err != nil {
				// Dir doesn't exist — add tokens from all member configs as placeholders
				for _, cfg := range memberCfgs {
					sectionNode.Children = append(sectionNode.Children, addTokensFromConfig(cfg, gType)...)
				}
				if len(sectionNode.Children) > 0 {
					stationNode.Children = append(stationNode.Children, sectionNode)
				}
				continue
			}

			ext := "." + strings.ToLower(gType)
			if gType == "LOG" {
				ext = ".log"
			}

			for _, entry := range entries {
				if entry.IsDir() {
					continue
				}
				entryExt := strings.ToLower(filepath.Ext(entry.Name()))
				if entryExt != ext {
					continue
				}

				// For LOG, filter by any member node name prefix
				if gType == "LOG" {
					matched := false
					for _, cfg := range memberCfgs {
						nodeNameUnderscore := strings.ReplaceAll(cfg.Name, " ", "_")
						if strings.HasPrefix(entry.Name(), nodeNameUnderscore+"_") ||
							strings.HasPrefix(entry.Name(), nodeNameUnderscore) {
							matched = true
							break
						}
					}
					if !matched {
						continue
					}
				}

				fullPath := filepath.Join(scanDir, entry.Name())
				lineCount := countLines(fullPath)

				fileNode := types.TreeNode{
					Name:        entry.Name(),
					Type:        "file",
					FileName:    entry.Name(),
					FilePath:    fullPath,
					SectionType: gType,
					LineCount:   lineCount,
					Status:      fileStatus(lineCount),
				}

				// Extract token_id from filename for context menu commands
				// Find which member node this file belongs to for token extraction
				for _, cfg := range memberCfgs {
					nodeNameUnderscore := strings.ReplaceAll(cfg.Name, " ", "_")
					if strings.HasPrefix(entry.Name(), nodeNameUnderscore+"_") ||
						strings.HasPrefix(entry.Name(), nodeNameUnderscore) {
						tokID := extractTokenID(entry.Name(), nodeNameUnderscore, gType)
						if tokID != "" {
							fileNode.TokenID = tokID
						}
						break
					}
				}

				sectionNode.Children = append(sectionNode.Children, fileNode)
			}

			// Sort files by name
			sort.Slice(sectionNode.Children, func(i, j int) bool {
				return sectionNode.Children[i].Name < sectionNode.Children[j].Name
			})

			// If no files found, add tokens from all member configs as placeholders
			if len(sectionNode.Children) == 0 {
				for _, cfg := range memberCfgs {
					sectionNode.Children = append(sectionNode.Children, addTokensFromConfig(cfg, gType)...)
				}
			}

			if len(sectionNode.Children) > 0 {
				stationNode.Children = append(stationNode.Children, sectionNode)
			}
		}

		root.Children = append(root.Children, stationNode)
	}

	return root
}

// addTokensFromConfig creates token-type child nodes from the config tokens.
func addTokensFromConfig(cfg types.NodeConfig, gType string) []types.TreeNode {
	children := make([]types.TreeNode, 0)
	for _, tok := range cfg.Tokens {
		if strings.EqualFold(string(tok.TokenType), gType) {
			children = append(children, types.TreeNode{
				Name:       tok.TokenID,
				Type:       "token",
				TokenID:    tok.TokenID,
				Port:       tok.Port,
				Protocol:   tok.Protocol,
				SectionType: gType,
			})
		}
	}
	return children
}

// countLines returns the number of lines in a file, or 0 if it can't be read.
func countLines(path string) int {
	data, err := os.ReadFile(path)
	if err != nil {
		return 0
	}
	count := 0
	for _, b := range data {
		if b == 10 { // '\n' = 10
			count++
		}
	}
	if len(data) > 0 && data[len(data)-1] != 10 {
		count++ // count last line without trailing newline
	}
	return count
}

// fileStatus returns a color status based on line count.
// 0 = red (empty), <10 = yellow (minimal), >=10 = green (sufficient).
func fileStatus(lineCount int) string {
	if lineCount == 0 {
		return "error" // red
	}
	if lineCount < 10 {
		return "warning" // yellow
	}
	return "idle" // green (using idle so it's not bold)
}

// extractTokenID extracts the token ID from a filename.
// FBC: {node}_{ip}_{token}.fbc → token
// RPC: {node}_{ip}_{token}.rpc → token
// LOG: {node}_{ip}.log → ""
func extractTokenID(filename, nodeName, sectionType string) string {
	base := strings.TrimSuffix(filename, filepath.Ext(filename))
	if sectionType == "LOG" {
		return "" // LOG files don't have a token ID
	}
	// Split on _ and take the last part
	parts := strings.Split(base, "_")
	if len(parts) >= 1 {
		return parts[len(parts)-1]
	}
	return base
}

// extractStationName derives the station folder name from a node name.
// All slots of a station are nested under one station folder:
//
//	"AP01" → "AP01m", "AP01 Main" → "AP01m", "AP01_m2" → "AP01m"
//	"AP02 Reserve" → "AP02r", "AP02_r2" → "AP02r"
//	"AL01" → "AL01" (LIS, no suffix), "A1OA OPS" → "A1OA" (OPS, no suffix)
func extractStationName(nodeName string) string {
	// LIS nodes (AL prefix) and OPS nodes don't get m/r suffix
	if strings.HasPrefix(nodeName, "AL") || strings.Contains(nodeName, "OPS") {
		base := nodeName
		if idx := strings.Index(base, " "); idx >= 0 {
			base = base[:idx]
		}
		return base
	}

	isReserve := strings.Contains(nodeName, "Reserve") || strings.Contains(nodeName, "_r")

	// Strip suffixes to get base name
	base := nodeName
	if idx := strings.Index(base, " "); idx >= 0 {
		base = base[:idx]
	}
	if idx := strings.Index(base, "_"); idx >= 0 {
		base = base[:idx]
	}

	if isReserve {
		return base + "r"
	}
	return base + "m"
}
