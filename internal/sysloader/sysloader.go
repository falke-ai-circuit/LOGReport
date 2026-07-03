// Package sysloader loads Valmet DNA .sys configuration files and creates
// the FBC/RPC/LOG/LIS folder structure for log file collection.
//
// It mirrors the Python sys_file_loader.py and log_creator.py behavior.
package sysloader

import (
	"fmt"
	"os"
	"path/filepath"
	"strconv"
	"strings"

	"github.com/falke-ai-circuit/LOGReport/internal/parser"
	"github.com/falke-ai-circuit/LOGReport/internal/types"
)

// nodeTypeToTokenTypes maps a node type string to the token types
// that should be created for that node.
var nodeTypeToTokenTypes = map[string][]types.TokenType{
	"PCS":      {types.TokenFBC, types.TokenRPC}, // PCS fieldbus slots
	"LIS":      {types.TokenLIS},
	"DIA":      {types.TokenLOG},
	"NETWATCH": {types.TokenLOG},
	"MAINT":    {types.TokenLOG},
	"CIS":      {types.TokenLOG},
	"OPS":      {types.TokenLOG},
	"ALP":      {types.TokenLOG},
	"HISTORY":  {types.TokenLOG},
}

// LoadSysFiles scans a directory for .sys files, parses each one,
// groups entries by LID prefix, extracts token IDs, and returns []types.NodeConfig.
//
// Slot handling:
//   - Slot 1 (CPU, PROGRAM=PCS_CODE): LOG-only token (BsTool errlog). No FBC/RPC.
//   - Slot 2+ (fieldbus, PROGRAM=CIO_FBC_CODE): FBC + RPC tokens.
//   - NCU2 nodes: skipped (infrastructure).
func LoadSysFiles(dirPath string) ([]types.NodeConfig, error) {
	entries, err := os.ReadDir(dirPath)
	if err != nil {
		return nil, fmt.Errorf("sysloader: read dir %s: %w", dirPath, err)
	}

	var sysFiles []string
	for _, entry := range entries {
		if entry.IsDir() {
			continue
		}
		if strings.HasSuffix(strings.ToLower(entry.Name()), ".sys") {
			sysFiles = append(sysFiles, filepath.Join(dirPath, entry.Name()))
		}
	}

	if len(sysFiles) == 0 {
		return make([]types.NodeConfig, 0), nil
	}

	return parseSysFiles(sysFiles)
}

// LoadSysFilesFromPaths parses .sys files from explicit file paths (not a directory).
// Used by the multi-file upload endpoint where the browser selects individual files.
func LoadSysFilesFromPaths(filePaths []string) ([]types.NodeConfig, error) {
	if len(filePaths) == 0 {
		return make([]types.NodeConfig, 0), nil
	}
	return parseSysFiles(filePaths)
}

// parseSysFiles is the shared core that processes a list of .sys file paths,
// merges results by LID, and returns NodeConfig array.
func parseSysFiles(sysFiles []string) ([]types.NodeConfig, error) {
	nodeMap := make(map[string]*types.NodeConfig)
	nodeOrder := make([]string, 0)

	for _, sysPath := range sysFiles {
		result, err := parser.ParseSysFile(sysPath)
		if err != nil {
			continue
		}

		ipAddr := result.IPAddr

		// Process :e:hw: entries (legacy format)
		for _, entry := range result.Entries {
			lid := entry.LID
			if lid == "" {
				continue
			}

			nodeType := entry.NodeType
			// Skip unknown node types in legacy format too
			if nodeType == "UNKNOWN" {
				continue
			}
			tokenTypes := nodeTypeToTokenTypes[nodeType]
			if len(tokenTypes) == 0 {
				tokenTypes = []types.TokenType{types.TokenLOG}
			}

			node, exists := nodeMap[lid]
			if !exists {
				node = &types.NodeConfig{
					Name:      lid,
					IPAddress: ipAddr,
				}
				nodeMap[lid] = node
				nodeOrder = append(nodeOrder, lid)
			}

			if node.IPAddress == "" && ipAddr != "" {
				node.IPAddress = ipAddr
			}

			tokenID := entry.HWAddr
			if tokenID == "" {
				tokenID = strings.ReplaceAll(lid, " ", "_")
			}

			for _, tt := range tokenTypes {
				alreadyExists := false
				for _, existing := range node.Tokens {
					if existing.TokenType == tt && existing.TokenID == tokenID {
						alreadyExists = true
						break
					}
				}
				if !alreadyExists {
					node.Tokens = append(node.Tokens, types.Token{
						TokenID:   tokenID,
						TokenType: tt,
						Protocol:  "telnet",
					})
				}
			}
		}

		// Process Slot-format nodes (TITLE=/PROGRAM= sections)
		// The filename stem (e.g. "161" from "161.sys") is the base hardware address.
		// Token IDs are calculated based on the slot number:
		//   AP01 (base, slot 1 CPU)    -> token = base (e.g. "161") -- but LOG only
		//   AP01_m2 (slot 2 fieldbus)  -> token = base + 1 (e.g. "162") -- FBC + RPC
		//   AP01_m3 (slot 3 fieldbus)  -> token = base + 2 (e.g. "163") -- FBC + RPC
		// NCU2 nodes are skipped.
		// CPU slots (Slot 1, PROGRAM=PCS_CODE) get LOG-only token (BsTool errlog).
		// Fieldbus slots (Slot 2+, PROGRAM=CIO_FBC_CODE) get FBC + RPC tokens.
		sysFileToken := strings.TrimSuffix(filepath.Base(sysPath), filepath.Ext(sysPath))
		for _, sfn := range result.Nodes {
			lid := sfn.LID
			if lid == "" {
				continue
			}

			// Skip NCU2
			if lid == "NCU2" {
				continue
			}

			// Skip unknown node types — these are infrastructure services
			// (qemgr, smf1, XComServer, Web Diagnostics, etc.) that don't
			// have FBC/RPC/LOG tokens relevant to LOGReport.
			nodeType := sfn.Type
			if nodeType == "UNKNOWN" {
				continue
			}

			node, exists := nodeMap[lid]
			if !exists {
				node = &types.NodeConfig{
					Name:      lid,
					IPAddress: ipAddr,
				}
				nodeMap[lid] = node
				nodeOrder = append(nodeOrder, lid)
			}

			if node.IPAddress == "" && ipAddr != "" {
				node.IPAddress = ipAddr
			}

			// Calculate token ID based on slot number
			tokenID := sysFileToken
			slotNum := sfn.SlotNum
			if slotNum == 0 {
				// Fallback to extracting from LID name (legacy path without Slot tracking)
				slotNum = extractSlotNumber(lid)
			}
			if slotNum > 1 {
				tokenID = offsetToken(sysFileToken, slotNum-1)
			}

			// Determine token types based on whether this is a fieldbus slot or CPU slot.
			// FBC/RPC only apply to fieldbus cards (PROGRAM=CIO_FBC_CODE).
			// CPU slots (PROGRAM=PCS_CODE) get LOG-only (BsTool errlog output).
			var tokenTypes []types.TokenType
			if sfn.IsFieldbus {
				// Fieldbus slot: FBC + RPC (all FBC have corresponding RPC)
				tokenTypes = []types.TokenType{types.TokenFBC, types.TokenRPC}
			} else {
				// CPU slot or other: LOG-only (BsTool errlog)
				// LIS/OPS nodes use their type mapping instead
				tokenTypes = nodeTypeToTokenTypes[sfn.Type]
				if len(tokenTypes) == 0 {
					tokenTypes = []types.TokenType{types.TokenLOG}
				}
				// For PCS CPU slots, override to LOG-only
				if sfn.Type == "PCS" {
					tokenTypes = []types.TokenType{types.TokenLOG}
				}
			}

			for _, tt := range tokenTypes {
				alreadyExists := false
				for _, existing := range node.Tokens {
					if existing.TokenType == tt && existing.TokenID == tokenID {
						alreadyExists = true
						break
					}
				}
				if !alreadyExists {
					node.Tokens = append(node.Tokens, types.Token{
						TokenID:   tokenID,
						TokenType: tt,
						Protocol:  "telnet",
					})
				}
			}
		}
	}

	configs := make([]types.NodeConfig, 0, len(nodeOrder))
	for _, lid := range nodeOrder {
		configs = append(configs, *nodeMap[lid])
	}

	return configs, nil
}

// extractSlotNumber parses the slot number from a node LID name.
// "AP01" -> 1, "AP01_m2" -> 2, "AP01_m3" -> 3, "AP02_r4" -> 4
func extractSlotNumber(lid string) int {
	parts := strings.Split(lid, "_")
	for _, p := range parts {
		if len(p) >= 2 && (p[0] == 'm' || p[0] == 'r') {
			if p[1] >= '0' && p[1] <= '9' {
				n := 0
				for i := 1; i < len(p); i++ {
					if p[i] >= '0' && p[i] <= '9' {
						n = n*10 + int(p[i]-'0')
					} else {
						break
					}
				}
				if n > 0 {
					return n
				}
			}
		}
	}
	return 1
}

// offsetToken adds an offset to a hex token ID string.
func offsetToken(base string, offset int) string {
	val, err := strconv.ParseInt(base, 16, 64)
	if err != nil {
		return base
	}
	val += int64(offset)
	return strconv.FormatInt(val, 16)
}

// extractStationName derives the station folder name from a node name.
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

// CreateFolderStructure creates the FBC/RPC/LOG/LIS directory tree.
// Only fieldbus slots (FBC/RPC tokens) create FBC and RPC files.
// CPU slots (LOG-only) create LOG files for BsTool errlog output.
// All FBC files have corresponding RPC files in the same station folder.
func CreateFolderStructure(outputDir string, configs []types.NodeConfig) error {
	if err := os.MkdirAll(outputDir, 0755); err != nil {
		return fmt.Errorf("sysloader: create output dir %s: %w", outputDir, err)
	}

	for _, cfg := range configs {
		nodeName := strings.ReplaceAll(cfg.Name, " ", "_")
		if nodeName == "" {
			continue
		}

		stationName := extractStationName(cfg.Name)

		ipFormatted := cfg.IPAddress
		if ipFormatted == "" {
			ipFormatted = "192.168.0.1"
		}
		ipFormatted = strings.ReplaceAll(ipFormatted, ".", "-")

		tokenTypeSet := make(map[types.TokenType]bool)
		for _, tok := range cfg.Tokens {
			tokenTypeSet[tok.TokenType] = true
		}

		// FBC files (only for fieldbus slots)
		if tokenTypeSet[types.TokenFBC] {
			nodeDir := filepath.Join(outputDir, stationName, "FBC")
			if err := os.MkdirAll(nodeDir, 0755); err != nil {
				return fmt.Errorf("sysloader: create FBC dir %s: %w", nodeDir, err)
			}
			for _, tok := range cfg.Tokens {
				if tok.TokenType != types.TokenFBC {
					continue
				}
				fileName := fmt.Sprintf("%s_%s_%s.fbc", stationName, ipFormatted, tok.TokenID)
				filePath := filepath.Join(nodeDir, fileName)
				if _, err := os.Stat(filePath); os.IsNotExist(err) {
					if err := os.WriteFile(filePath, []byte{}, 0644); err != nil {
						return fmt.Errorf("sysloader: create FBC file %s: %w", filePath, err)
					}
				}
			}
		}

		// RPC files (always paired with FBC -- all FBC have corresponding RPC)
		if tokenTypeSet[types.TokenRPC] {
			nodeDir := filepath.Join(outputDir, stationName, "RPC")
			if err := os.MkdirAll(nodeDir, 0755); err != nil {
				return fmt.Errorf("sysloader: create RPC dir %s: %w", nodeDir, err)
			}
			for _, tok := range cfg.Tokens {
				if tok.TokenType != types.TokenRPC {
					continue
				}
				fileName := fmt.Sprintf("%s_%s_%s.rpc", stationName, ipFormatted, tok.TokenID)
				filePath := filepath.Join(nodeDir, fileName)
				if _, err := os.Stat(filePath); os.IsNotExist(err) {
					if err := os.WriteFile(filePath, []byte{}, 0644); err != nil {
						return fmt.Errorf("sysloader: create RPC file %s: %w", filePath, err)
					}
				}
			}
		}

		// LOG files for PCS nodes (both CPU and fieldbus slots get errlog)
		if tokenTypeSet[types.TokenFBC] || tokenTypeSet[types.TokenRPC] || tokenTypeSet[types.TokenLOG] {
			logDir := filepath.Join(outputDir, stationName, "LOG")
			if err := os.MkdirAll(logDir, 0755); err != nil {
				return fmt.Errorf("sysloader: create LOG dir %s: %w", logDir, err)
			}
			fileName := fmt.Sprintf("%s_%s.log", stationName, ipFormatted)
			filePath := filepath.Join(logDir, fileName)
			if _, err := os.Stat(filePath); os.IsNotExist(err) {
				if err := os.WriteFile(filePath, []byte{}, 0644); err != nil {
					return fmt.Errorf("sysloader: create LOG file %s: %w", filePath, err)
				}
			}
		}

		// LIS files (6 per node: exe1..exe6, one set per LIS token)
		for _, tok := range cfg.Tokens {
			if tok.TokenType != types.TokenLIS {
				continue
			}
			lisDir := filepath.Join(outputDir, stationName, "LIS")
			if err := os.MkdirAll(lisDir, 0755); err != nil {
				return fmt.Errorf("sysloader: create LIS dir %s: %w", lisDir, err)
			}
			for i := 1; i <= 6; i++ {
				fileName := fmt.Sprintf("%s_%s_%s_exe%d.lis", stationName, ipFormatted, tok.TokenID, i)
				filePath := filepath.Join(lisDir, fileName)
				if _, err := os.Stat(filePath); os.IsNotExist(err) {
					if err := os.WriteFile(filePath, []byte{}, 0644); err != nil {
						return fmt.Errorf("sysloader: create LIS file %s: %w", filePath, err)
					}
				}
			}
		}
	}

	return nil
}
