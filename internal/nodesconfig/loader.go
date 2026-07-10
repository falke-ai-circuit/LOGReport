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
	case "RSU":
		return ".rsu"
	case "DIA":
		return ".dia"
	default:
		return ".log"
	}
}

// lisSectionType returns the effective section type for LIS based on lisMode.
// rsu→"RSU", diaglis→"DIA", lisdiag/empty→"LIS".
func lisSectionType(lisMode string) string {
	switch lisMode {
	case "rsu":
		return "RSU"
	case "diaglis":
		return "DIA"
	default:
		return "LIS"
	}
}

// buildFileName creates the expected filename for a token in a station.
// Pattern: {stationName}_{ipFormatted}_{tokenID}.{ext}
// For LOG: {stationName}_{ipFormatted}.log (no tokenID)
// For LIS: {stationName}_{ipFormatted}_{tokenID}_exe{N}.{ext} when exeNum > 0
//          {stationName}_{ipFormatted}_{tokenID}.{ext} when exeNum == 0
// For LIS tokens, the extension depends on lisMode: rsu→.rsu, diaglis→.dia, lisdiag/empty→.lis
func buildFileName(stationName, ip, tokenType, tokenID, lisMode string, exeNum int) string {
	ext := fileExtension(tokenType)
	// For LIS tokens, the extension depends on lisMode
	if strings.ToUpper(tokenType) == "LIS" {
		switch lisMode {
		case "rsu":
			ext = ".rsu"
		case "diaglis":
			ext = ".dia"
		default:
			ext = ".lis"
		}
	}
	ipFmt := formatIP(ip)
	if strings.ToUpper(tokenType) == "LOG" {
		return fmt.Sprintf("%s_%s%s", stationName, ipFmt, ext)
	}
	if strings.ToUpper(tokenType) == "LIS" {
		if exeNum > 0 {
			return fmt.Sprintf("%s_%s_%s_exe%d%s", stationName, ipFmt, tokenID, exeNum, ext)
		}
		return fmt.Sprintf("%s_%s_%s%s", stationName, ipFmt, tokenID, ext)
	}
	return fmt.Sprintf("%s_%s_%s%s", stationName, ipFmt, tokenID, ext)
}

// BuildTree converts a flat NodeConfig list into a hierarchical tree
// grouped by station: root -> station -> type groups (FBC/RPC/LOG/LIS) -> token leaves.
// Token leaves show the full expected filename (e.g. AP01m_192-168-0-11_162.fbc).
func BuildTree(configs []types.NodeConfig, lisMode string, lisExeCount int) *types.TreeNode {
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
		// Map token to its config's IP for per-token IP resolution
		tokenIPs := make(map[string]string) // key: tokenType+tokenID
		for _, cfg := range memberCfgs {
			for _, tok := range cfg.Tokens {
				key := string(tok.TokenType) + ":" + tok.TokenID
				if _, exists := tokenIPs[key]; !exists && cfg.IPAddress != "" {
					tokenIPs[key] = cfg.IPAddress
				}
			}
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
			if gType == "LOG" {
				// LOG files don't include token ID in the filename — one file per station.
				// Deduplicate: create only one LOG entry per station+IP.
				seen := make(map[string]bool)
				for _, tok := range tokens {
					ipForFile := stationIP
					if ip, ok := tokenIPs[string(tok.TokenType)+":"+tok.TokenID]; ok {
						ipForFile = ip
					}
					fileName := buildFileName(stationName, ipForFile, gType, tok.TokenID, lisMode, 0)
					if seen[fileName] {
						continue
					}
					seen[fileName] = true
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
			} else if gType == "LIS" {
				// LIS: deduplicate by tokenID, then generate exe1-exeN placeholder nodes per token.
				sectionType := lisSectionType(lisMode)
				groupNode.Name = sectionType
				groupNode.SectionType = sectionType
				seenTokens := make(map[string]bool)
				for _, tok := range tokens {
					if seenTokens[tok.TokenID] {
						continue
					}
					seenTokens[tok.TokenID] = true
					ipForFile := stationIP
					if ip, ok := tokenIPs[string(tok.TokenType)+":"+tok.TokenID]; ok {
						ipForFile = ip
					}
					for exeNum := 1; exeNum <= lisExeCount; exeNum++ {
						fileName := buildFileName(stationName, ipForFile, gType, tok.TokenID, lisMode, exeNum)
						groupNode.Children = append(groupNode.Children, types.TreeNode{
							Name:        fileName,
							Type:        "token",
							TokenID:     fmt.Sprintf("%s_exe%d", tok.TokenID, exeNum),
							Port:        tok.Port,
							Protocol:    tok.Protocol,
							SectionType: sectionType,
							FileName:    fileName,
						})
					}
				}
			} else {
				for _, tok := range tokens {
					// Use per-token IP if available, otherwise fall back to station IP
					ipForFile := stationIP
					if ip, ok := tokenIPs[string(tok.TokenType)+":"+tok.TokenID]; ok {
						ipForFile = ip
					}
					fileName := buildFileName(stationName, ipForFile, gType, tok.TokenID, lisMode, 0)
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
			}
			stationNode.Children = append(stationNode.Children, groupNode)
		}

		root.Children = append(root.Children, stationNode)
	}

	return root
}

// BuildFileTree builds a tree from actual log files on disk.
// Structure: root -> station -> FBC/RPC/LOG/LIS -> files (with full filenames)
// If hideMissing is true, only files that actually exist on disk are shown —
// no "token" placeholder nodes for expected-but-missing files (used by Commander).
func BuildFileTree(configs []types.NodeConfig, logRoot string, hideMissing bool, lisMode string, lisExeCount int) *types.TreeNode {
	if logRoot == "" {
		return BuildTree(configs, lisMode, lisExeCount)
	}
	if _, err := os.Stat(logRoot); err != nil {
		return BuildTree(configs, lisMode, lisExeCount)
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
			// For LIS, the effective section type depends on lisMode
			effectiveType := gType
			if gType == "LIS" {
				effectiveType = lisSectionType(lisMode)
			}
			sectionNode := types.TreeNode{
				Name:        effectiveType,
				Type:        "group",
				SectionType: effectiveType,
				Children:    make([]types.TreeNode, 0),
			}

			// Scan dir: {logRoot}/_LOG/{station}/{type}/ (standard structure)
			// Try lowercase first, then uppercase
			scanType := gType
			if gType == "LIS" {
				scanType = lisSectionType(lisMode)
			}
			scanDir := filepath.Join(logRoot, "_LOG", stationName, strings.ToLower(scanType))
			entries, err := os.ReadDir(scanDir)
			if err != nil {
				// Try uppercase path
				scanDir = filepath.Join(logRoot, "_LOG", stationName, scanType)
				entries, err = os.ReadDir(scanDir)
			}
			if err != nil {
				// Dir doesn't exist -- add token nodes with filenames from config (unless hideMissing)
				if hideMissing {
					continue
				}
				if gType == "LOG" {
					// LOG: one file per station (no token ID in filename) — deduplicate
					seen := make(map[string]bool)
					for _, cfg := range memberCfgs {
						for _, tok := range cfg.Tokens {
							if strings.EqualFold(string(tok.TokenType), gType) {
								ipForFile := cfg.IPAddress
								if ipForFile == "" { ipForFile = stationIP }
								fileName := buildFileName(stationName, ipForFile, gType, tok.TokenID, lisMode, 0)
								if seen[fileName] { continue }
								seen[fileName] = true
								sectionNode.Children = append(sectionNode.Children, types.TreeNode{
									Name: fileName, Type: "token", TokenID: tok.TokenID,
									SectionType: effectiveType, FileName: fileName,
								})
							}
						}
					}
				} else if gType == "LIS" {
					// LIS: deduplicate by tokenID, generate exe1-exeN placeholders
					seenTokens := make(map[string]bool)
					for _, cfg := range memberCfgs {
						for _, tok := range cfg.Tokens {
							if !strings.EqualFold(string(tok.TokenType), gType) {
								continue
							}
							if seenTokens[tok.TokenID] {
								continue
							}
							seenTokens[tok.TokenID] = true
							ipForFile := cfg.IPAddress
							if ipForFile == "" { ipForFile = stationIP }
							for exeNum := 1; exeNum <= lisExeCount; exeNum++ {
								fileName := buildFileName(stationName, ipForFile, gType, tok.TokenID, lisMode, exeNum)
								sectionNode.Children = append(sectionNode.Children, types.TreeNode{
									Name: fileName, Type: "token",
									TokenID:     fmt.Sprintf("%s_exe%d", tok.TokenID, exeNum),
									SectionType: effectiveType, FileName: fileName,
								})
							}
						}
					}
				} else {
					for _, cfg := range memberCfgs {
						for _, tok := range cfg.Tokens {
							if strings.EqualFold(string(tok.TokenType), gType) {
								ipForFile := cfg.IPAddress
								if ipForFile == "" { ipForFile = stationIP }
								fileName := buildFileName(stationName, ipForFile, gType, tok.TokenID, lisMode, 0)
								sectionNode.Children = append(sectionNode.Children, types.TreeNode{
									Name: fileName, Type: "token", TokenID: tok.TokenID,
									SectionType: effectiveType, FileName: fileName,
								})
							}
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
				// Don't filter by extension — show ALL files in the subfolder.
				// Users may move files between subfolders (e.g. FBC file into RPC folder)
				// and those files should still be visible and selectable.
				_ = ext // keep for potential future use

				fullPath := filepath.Join(scanDir, entry.Name())
				lineCount := countLines(fullPath)

				tokID := extractTokenIDFromName(entry.Name(), scanType)
				// Extract IP from filename: {station}_{ip-hyphens}_{token}.ext or {station}_{ip-hyphens}.log
				fileIP := extractIPFromName(entry.Name())
				fileNode := types.TreeNode{
					Name:        entry.Name(),
					Type:        "file",
					FileName:    entry.Name(),
					FilePath:    fullPath,
					IP:          fileIP,
					SectionType: effectiveType,
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

			// Add placeholder tokens for config files that don't exist on disk yet.
			// This ensures all expected files are visible even when some have been
			// written and others haven't (e.g. 222.fbc exists but 223.fbc doesn't).
			if !hideMissing {
				// Build a set of filenames already on disk
				existingFiles := make(map[string]bool)
				for _, child := range sectionNode.Children {
					existingFiles[child.FileName] = true
				}

				if gType == "LOG" {
					seen := make(map[string]bool)
					for _, cfg := range memberCfgs {
						for _, tok := range cfg.Tokens {
							if strings.EqualFold(string(tok.TokenType), gType) {
								ipForFile := cfg.IPAddress
								if ipForFile == "" { ipForFile = stationIP }
								fileName := buildFileName(stationName, ipForFile, gType, tok.TokenID, lisMode, 0)
								if seen[fileName] { continue }
								seen[fileName] = true
								if !existingFiles[fileName] {
									sectionNode.Children = append(sectionNode.Children, types.TreeNode{
										Name: fileName, Type: "token", TokenID: tok.TokenID,
										SectionType: effectiveType, FileName: fileName,
									})
								}
							}
						}
					}
				} else if gType == "LIS" {
					seenTokens := make(map[string]bool)
					for _, cfg := range memberCfgs {
						for _, tok := range cfg.Tokens {
							if !strings.EqualFold(string(tok.TokenType), gType) {
								continue
							}
							if seenTokens[tok.TokenID] {
								continue
							}
							seenTokens[tok.TokenID] = true
							ipForFile := cfg.IPAddress
							if ipForFile == "" { ipForFile = stationIP }
							for exeNum := 1; exeNum <= lisExeCount; exeNum++ {
								fileName := buildFileName(stationName, ipForFile, gType, tok.TokenID, lisMode, exeNum)
								if !existingFiles[fileName] {
									sectionNode.Children = append(sectionNode.Children, types.TreeNode{
										Name: fileName, Type: "token",
										TokenID:     fmt.Sprintf("%s_exe%d", tok.TokenID, exeNum),
										SectionType: effectiveType, FileName: fileName,
									})
								}
							}
						}
					}
				} else {
					for _, cfg := range memberCfgs {
						for _, tok := range cfg.Tokens {
							if strings.EqualFold(string(tok.TokenType), gType) {
								ipForFile := cfg.IPAddress
								if ipForFile == "" { ipForFile = stationIP }
								fileName := buildFileName(stationName, ipForFile, gType, tok.TokenID, lisMode, 0)
								if !existingFiles[fileName] {
									sectionNode.Children = append(sectionNode.Children, types.TreeNode{
										Name: fileName, Type: "token", TokenID: tok.TokenID,
										SectionType: effectiveType, FileName: fileName,
									})
								}
							}
						}
					}
				}

				// Re-sort after adding placeholders
				sort.Slice(sectionNode.Children, func(i, j int) bool {
					return sectionNode.Children[i].Name < sectionNode.Children[j].Name
				})
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

// extractIPFromName extracts the IP address from a filename.
// Filename patterns: {station}_{ip-hyphens}_{token}.ext or {station}_{ip-hyphens}.log
// Returns IP with dots (e.g. "172.16.120.17") or empty string if not found.
func extractIPFromName(filename string) string {
	base := strings.TrimSuffix(filename, filepath.Ext(filename))
	parts := strings.Split(base, "_")
	if len(parts) < 2 {
		return ""
	}
	// IP is always the second segment (index 1)
	ipHyphens := parts[1]
	if ipHyphens == "unknown-ip" || ipHyphens == "" {
		return ""
	}
	return strings.ReplaceAll(ipHyphens, "-", ".")
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
