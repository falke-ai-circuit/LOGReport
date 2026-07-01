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
// Only PCS nodes (AP prefix) get m/r suffix. BU (AB), DIA (AD), ALP (A1A1), OPS (A1O1, B1O1) don't.
func extractStationName(nodeName string) string {
	// Strip _mN or _rN suffix
	base := nodeName
	if idx := strings.Index(base, "_"); idx >= 0 {
		base = base[:idx]
	}
	if idx := strings.Index(base, " "); idx >= 0 {
		base = base[:idx]
	}
	// If base already ends with 'm' or 'r', it's already a station name
	if strings.HasSuffix(base, "m") || strings.HasSuffix(base, "r") {
		return base
	}
	// Only PCS (AP prefix) nodes get m/r suffix
	if strings.HasPrefix(base, "AP") {
		isReserve := strings.Contains(nodeName, "Reserve") || strings.Contains(nodeName, "_r")
		if isReserve {
			return base + "r"
		}
		return base + "m"
	}
	// AL, AB, AD, A1*, B1* — no m/r suffix
	return base
}

// formatIP replaces dots with hyphens.
func formatIP(ip string) string {
	if ip == "" {
		return "unknown-ip"
	}
	return strings.ReplaceAll(ip, ".", "-")
}

// fileExtension returns the file extension for a token type.
func fileExtension(tokenType string) string {
	switch strings.ToUpper(tokenType) {
	case "FBC":
		return ".fbc"
	case "RPC":
		return ".rpc"
	case "LIS":
		return ".lis"
	default:
		return ".log"
	}
}

// buildFileName creates the expected filename for a token in a station.
// Pattern: {stationName}_{ipFormatted}_{tokenID}.{ext}
// For LOG: {stationName}_{ipFormatted}.log (no tokenID)
func buildFileName(stationName, ip, tokenType, tokenID string) string {
	ext := fileExtension(tokenType)
	ipFmt := formatIP(ip)
	if strings.ToUpper(tokenType) == "LOG" {
		return fmt.Sprintf("%s_%s%s", stationName, ipFmt, ext)
	}
	return fmt.Sprintf("%s_%s_%s%s", stationName, ipFmt, tokenID, ext)
}

// BuildTree converts a flat NodeConfig list into a hierarchical tree
// grouped by station: root -> station -> type groups (FBC/RPC/LOG/LIS) -> token leaves.
// Token leaves show the full expected filename (e.g. AP01m_192-168-0-11_162.fbc).
func BuildTree(configs []types.NodeConfig) *types.TreeNode {
	root := &types.TreeNode{
		Name:     "Root",
		Type:     "root",
		Children: make([]types.TreeNode, 0),
	}

	groupOrder := []string{"FBC", "RPC", "LOG", "LIS", "FTP"}

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
		stationIP := stationIPs[stationName]

		stationNode := types.TreeNode{
			Name:     stationName,
			Type:     "node",
			IP:       stationIP,
			Status:   "idle",
			Children: make([]types.TreeNode, 0),
		}

		groups := make(map[string][]types.Token)
		for _, cfg := range memberCfgs {
			for _, tok := range cfg.Tokens {
				groups[string(tok.TokenType)] = append(groups[string(tok.TokenType)], tok)
			}
		}

		for _, gType := range groupOrder {
			tokens, ok := groups[gType]
			if !ok {
				continue
			}
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
				fileName := buildFileName(stationName, stationIP, gType, tok.TokenID)
				groupNode.Children = append(groupNode.Children, types.TreeNode{
					Name:        fileName,
					Type:        "token",
					TokenID:     tok.TokenID,
					Port:        tok.Port,
					Protocol:    tok.Protocol,
					SectionType: gType,
					FileName:    fileName,
				})
			}
			stationNode.Children = append(stationNode.Children, groupNode)
		}

		root.Children = append(root.Children, stationNode)
	}

	return root
}

// BuildFileTree builds a tree from actual log files on disk.
// Structure: root -> station -> FBC/RPC/LOG/LIS -> files (with full filenames)
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
		stationIP := stationIPs[stationName]

		stationNode := types.TreeNode{
			Name:     stationName,
			Type:     "node",
			IP:       stationIP,
			Children: make([]types.TreeNode, 0),
		}

		for _, gType := range groupOrder {
			sectionNode := types.TreeNode{
				Name:        gType,
				Type:        "group",
				SectionType: gType,
				Children:    make([]types.TreeNode, 0),
			}

			// Scan dir: {logRoot}/{_LOG}/{station}/{type}/ (case-insensitive)
			// Try lowercase first, then uppercase for backward compat
			scanDir := filepath.Join(logRoot, "_LOG", stationName, strings.ToLower(gType))
			entries, err := os.ReadDir(scanDir)
			if err != nil {
				// Try old uppercase path (backward compat)
				scanDir = filepath.Join(logRoot, stationName, gType)
				entries, err = os.ReadDir(scanDir)
			}
			if err != nil {
				// Dir doesn't exist -- add token nodes with filenames from config
				for _, cfg := range memberCfgs {
					for _, tok := range cfg.Tokens {
						if strings.EqualFold(string(tok.TokenType), gType) {
							fileName := buildFileName(stationName, stationIP, gType, tok.TokenID)
							sectionNode.Children = append(sectionNode.Children, types.TreeNode{
								Name:        fileName,
								Type:        "token",
								TokenID:     tok.TokenID,
								SectionType: gType,
								FileName:    fileName,
							})
						}
					}
				}
				if len(sectionNode.Children) > 0 {
					stationNode.Children = append(stationNode.Children, sectionNode)
				}
				continue
			}

			ext := fileExtension(gType)

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

				tokID := extractTokenIDFromName(entry.Name(), gType)
				fileNode := types.TreeNode{
					Name:        entry.Name(),
					Type:        "file",
					FileName:    entry.Name(),
					FilePath:    fullPath,
					SectionType: gType,
					LineCount:   lineCount,
					Status:      fileStatus(lineCount),
				}
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
					for _, tok := range cfg.Tokens {
						if strings.EqualFold(string(tok.TokenType), gType) {
							fileName := buildFileName(stationName, stationIP, gType, tok.TokenID)
							sectionNode.Children = append(sectionNode.Children, types.TreeNode{
								Name:        fileName,
								Type:        "token",
								TokenID:     tok.TokenID,
								SectionType: gType,
								FileName:    fileName,
							})
						}
					}
				}
			}

			if len(sectionNode.Children) > 0 {
				stationNode.Children = append(stationNode.Children, sectionNode)
			}
		}

		// Compute aggregate station status from all file/token grandchildren
		stationNode.Status = aggregateStationStatus(stationNode.Children)

		root.Children = append(root.Children, stationNode)
	}

	return root
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

// aggregateStationStatus computes a station node's Status from its children.
// Station children are group nodes (FBC/RPC/LOG/LIS); their children are
// file/token nodes with Status fields set by fileStatus().
// Rules: any descendant "error" → "error", any descendant "warning" → "warning",
// otherwise "idle".
func aggregateStationStatus(groupNodes []types.TreeNode) string {
	hasWarning := false
	for _, group := range groupNodes {
		for _, leaf := range group.Children {
			switch leaf.Status {
			case "error":
				return "error"
			case "warning":
				hasWarning = true
			}
		}
	}
	if hasWarning {
		return "warning"
	}
	return "idle"
}
