// Package nodesconfig loads and saves the nodes.json configuration file
// and builds a hierarchical tree structure for the frontend Commander node tree.
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
func LoadFromFile(path string) ([]types.NodeConfig, error) {
	data, err := os.ReadFile(path)
	if err != nil {
		return nil, fmt.Errorf("nodesconfig: read %s: %w", path, err)
	}
	return LoadFromBytes(data)
}

// LoadFromBytes parses nodes.json from a byte slice.
func LoadFromBytes(data []byte) ([]types.NodeConfig, error) {
	configs := make([]types.NodeConfig, 0)
	if err := json.Unmarshal(data, &configs); err != nil {
		return nil, fmt.Errorf("nodesconfig: unmarshal: %w", err)
	}
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

// extractStationName derives the station folder name from a node name.
// "AP01" -> "AP01m", "AP01 Main" -> "AP01m", "AP01_m2" -> "AP01m"
// "AP02 Reserve" -> "AP02r", "AP02_r2" -> "AP02r"
// "AL01" -> "AL01" (LIS, no suffix), "A1OA OPS" -> "A1OA" (OPS, no suffix)
func extractStationName(nodeName string) string {
	if strings.HasPrefix(nodeName, "AL") || strings.Contains(nodeName, "OPS") {
		base := nodeName
		if idx := strings.Index(base, " "); idx >= 0 {
			base = base[:idx]
		}
		return base
	}

	isReserve := strings.Contains(nodeName, "Reserve") || strings.Contains(nodeName, "_r")

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

// BuildTree converts a flat NodeConfig list into a hierarchical tree
// grouped by station: root -> station -> type groups (FBC/RPC/LOG/LIS) -> token leaves.
//
// All slots of a station (AP01, AP01_m2, AP01_m3) are grouped under
// a single station node (AP01m), with FBC/RPC/LOG subfolders containing
// all slot tokens of that type.
func BuildTree(configs []types.NodeConfig) *types.TreeNode {
	root := &types.TreeNode{
		Name:     "Root",
		Type:     "root",
		Children: make([]types.TreeNode, 0),
	}

	groupOrder := []string{"FBC", "RPC", "LOG", "LIS", "FTP"}

	// Group configs by station name, preserving discovery order
	stationOrder := make([]string, 0)
	stationConfigs := make(map[string][]types.NodeConfig)
	stationIPs := make(map[string]string)
	for _, cfg := range configs {
		station := extractStationName(cfg.Name)
		if _, exists := stationConfigs[station]; !exists {
			stationOrder = append(stationOrder, station)
		}
		stationConfigs[station] = append(stationConfigs[station], cfg)
		if stationIPs[station] == "" && cfg.IPAddress != "" {
			stationIPs[station] = cfg.IPAddress
		}
	}

	for _, stationName := range stationOrder {
		memberCfgs := stationConfigs[stationName]

		stationNode := types.TreeNode{
			Name:     stationName,
			Type:     "node",
			IP:       stationIPs[stationName],
			Status:   "idle",
			Children: make([]types.TreeNode, 0),
		}

		// Collect all tokens from all member configs, grouped by type
		groups := make(map[string][]types.Token)
		for _, cfg := range memberCfgs {
			for _, tok := range cfg.Tokens {
				groups[string(tok.TokenType)] = append(groups[string(tok.TokenType)], tok)
			}
		}

		// Add groups in canonical order
		for _, gType := range groupOrder {
			tokens, ok := groups[gType]
			if !ok {
				continue
			}
			// Sort tokens by token_id
			sort.Slice(tokens, func(i, j int) bool {
				return tokens[i].TokenID < tokens[j].TokenID
			})

			groupNode := types.TreeNode{
				Name:        gType,
				Type:        "group",
				SectionType: gType,
				Children:    make([]types.TreeNode, 0),
			}
			for _, tok := range tokens {
				groupNode.Children = append(groupNode.Children, types.TreeNode{
					Name:        tok.TokenID,
					Type:        "token",
					TokenID:     tok.TokenID,
					Port:        tok.Port,
					Protocol:    tok.Protocol,
					SectionType: gType,
				})
			}
			stationNode.Children = append(stationNode.Children, groupNode)
		}

		root.Children = append(root.Children, stationNode)
	}

	return root
}

// BuildFileTree builds a tree from actual log files on disk.
// Structure: root -> station -> FBC/RPC/LOG/LIS -> files
// Directory layout: {logRoot}/{stationName}/{type}/{stationName}_{ip}_{token}.{ext}
func BuildFileTree(configs []types.NodeConfig, logRoot string) *types.TreeNode {
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

	// Group configs by station name
	stationOrder := make([]string, 0)
	stationConfigs := make(map[string][]types.NodeConfig)
	stationIPs := make(map[string]string)
	for _, cfg := range configs {
		station := extractStationName(cfg.Name)
		if _, exists := stationConfigs[station]; !exists {
			stationOrder = append(stationOrder, station)
		}
		stationConfigs[station] = append(stationConfigs[station], cfg)
		if stationIPs[station] == "" && cfg.IPAddress != "" {
			stationIPs[station] = cfg.IPAddress
		}
	}

	for _, stationName := range stationOrder {
		memberCfgs := stationConfigs[stationName]

		stationNode := types.TreeNode{
			Name:     stationName,
			Type:     "node",
			IP:       stationIPs[stationName],
			Children: make([]types.TreeNode, 0),
		}

		for _, gType := range groupOrder {
			sectionNode := types.TreeNode{
				Name:        gType,
				Type:        "group",
				SectionType: gType,
				Children:    make([]types.TreeNode, 0),
			}

			// Scan for files: {logRoot}/{stationName}/{gType}/
			scanDir := filepath.Join(logRoot, stationName, gType)
			entries, err := os.ReadDir(scanDir)
			if err != nil {
				// Dir doesn't exist -- add tokens from configs as placeholders
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
				tokID := extractTokenIDFromName(entry.Name(), gType)
				if tokID != "" {
					fileNode.TokenID = tokID
				}

				sectionNode.Children = append(sectionNode.Children, fileNode)
			}

			sort.Slice(sectionNode.Children, func(i, j int) bool {
				return sectionNode.Children[i].Name < sectionNode.Children[j].Name
			})

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
				Name:        tok.TokenID,
				Type:        "token",
				TokenID:     tok.TokenID,
				Port:        tok.Port,
				Protocol:    tok.Protocol,
				SectionType: gType,
			})
		}
	}
	return children
}

// countLines returns the number of lines in a file.
func countLines(path string) int {
	data, err := os.ReadFile(path)
	if err != nil {
		return 0
	}
	count := 0
	for _, b := range data {
		if b == 10 {
			count++
		}
	}
	if len(data) > 0 && data[len(data)-1] != 10 {
		count++
	}
	return count
}

// fileStatus returns a color status based on line count.
func fileStatus(lineCount int) string {
	if lineCount == 0 {
		return "error"
	}
	if lineCount < 10 {
		return "warning"
	}
	return "idle"
}

// extractTokenIDFromName extracts the token ID from a filename.
// Pattern: {stationName}_{ip}_{token}.{ext} -> token
// For LOG (no token): {stationName}_{ip}.log -> ""
func extractTokenIDFromName(filename, sectionType string) string {
	base := strings.TrimSuffix(filename, filepath.Ext(filename))
	if sectionType == "LOG" {
		return ""
	}
	parts := strings.Split(base, "_")
	if len(parts) >= 3 {
		return parts[len(parts)-1]
	}
	return base
}
