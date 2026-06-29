// Package sysloader loads Valmet DNA .sys configuration files and creates
// the FBC/RPC/LOG/LIS folder structure for log file collection.
//
// It mirrors the Python sys_file_loader.py and log_creator.py behavior:
//   - LoadSysFiles scans a directory for .sys files, parses each one,
//     groups entries by LID prefix, extracts token IDs from hardware
//     addresses, and returns []types.NodeConfig.
//   - CreateFolderStructure creates the output directory tree with
//     placeholder .fbc/.rpc/.log/.lis files per node.
package sysloader

import (
	"fmt"
	"os"
	"path/filepath"
	"strings"

	"github.com/falke-ai-circuit/LOGReport/internal/parser"
	"github.com/falke-ai-circuit/LOGReport/internal/types"
)

// nodeTypeToTokenTypes maps a node type string to the token types
// that should be created for that node (mirrors Python log_creator.py
// node['types'] field).
var nodeTypeToTokenTypes = map[string][]types.TokenType{
	"PCS":      {types.TokenFBC, types.TokenRPC},
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
// groups entries by LID prefix, extracts token IDs from hardware
// addresses, and returns a slice of NodeConfig.
//
// For each .sys file:
//  1. parser.ParseSysFile extracts :e:hw: entries and IP address
//  2. Entries are grouped by LID (each unique LID = one node)
//  3. Token IDs are extracted from the hardware address field
//  4. Node types are derived from the LID prefix via types.LIDMapping
//
// The IP address from set XD_IP_ADDR is assigned to each node config.
func LoadSysFiles(dirPath string) ([]types.NodeConfig, error) {
	entries, err := os.ReadDir(dirPath)
	if err != nil {
		return nil, fmt.Errorf("sysloader: read dir %s: %w", dirPath, err)
	}

	// Collect all .sys file paths
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

	// Parse each .sys file and accumulate nodes
	// Key: LID → NodeConfig (merge tokens from multiple files)
	nodeMap := make(map[string]*types.NodeConfig)
	nodeOrder := make([]string, 0) // preserve discovery order

	for _, sysPath := range sysFiles {
		result, err := parser.ParseSysFile(sysPath)
		if err != nil {
			continue // skip files that can't be parsed
		}

		ipAddr := result.IPAddr

		// Process :e:hw: entries — each entry has a hardware address (token ID)
		// and a LID (node identifier)
		for _, entry := range result.Entries {
			lid := entry.LID
			if lid == "" {
				continue
			}

			// Determine token type from node type
			nodeType := entry.NodeType
			tokenTypes := nodeTypeToTokenTypes[nodeType]
			if len(tokenTypes) == 0 {
				// Default: treat as FBC+RPC for PCS-like nodes
				tokenTypes = []types.TokenType{types.TokenFBC, types.TokenRPC}
			}

			// Get or create node config
			node, exists := nodeMap[lid]
			if !exists {
				node = &types.NodeConfig{
					Name:      lid,
					IPAddress: ipAddr,
				}
				nodeMap[lid] = node
				nodeOrder = append(nodeOrder, lid)
			}

			// Update IP if this file had one and the node doesn't
			if node.IPAddress == "" && ipAddr != "" {
				node.IPAddress = ipAddr
			}

			// Extract token ID from the hardware address
			// The hardware address in :e:hw: lines is a hex string (e.g. "222", "1a1")
			// This is the actual token ID used in DIA commands:
			//   "print from fbc io structure 2220000"
			//   "print from fbc rupi counters 2220000"
			tokenID := entry.HWAddr
			if tokenID == "" {
				// Fallback: use LID with spaces → underscores
				tokenID = strings.ReplaceAll(lid, " ", "_")
			}

			// Add tokens for each token type this node supports
			for _, tt := range tokenTypes {
				// Avoid duplicate tokens
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
		// The filename stem (e.g. "161" from "161.sys") is the hardware address / token ID
		// used in DIA commands like "print from fbc io structure 1610000".
		// This matches the Python file_utils.py parse_sys_file behavior where
		// the filename stem is used as the token when there are no :e:hw: entries.
		sysFileToken := strings.TrimSuffix(filepath.Base(sysPath), filepath.Ext(sysPath))
		for _, sfn := range result.Nodes {
			lid := sfn.LID
			if lid == "" {
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

			// Add default tokens based on node type
			tokenTypes := nodeTypeToTokenTypes[sfn.Type]
			if len(tokenTypes) == 0 {
				tokenTypes = []types.TokenType{types.TokenFBC, types.TokenRPC}
			}
			for _, tt := range tokenTypes {
				alreadyExists := false
				// Use the filename stem (hardware address) as the token ID, not the LID.
				// e.g. "161" from "161.sys" → DIA command "print from fbc io structure 1610000"
				tokenID := sysFileToken
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

	// Build result slice in discovery order
	configs := make([]types.NodeConfig, 0, len(nodeOrder))
	for _, lid := range nodeOrder {
		configs = append(configs, *nodeMap[lid])
	}

	return configs, nil
}

// CreateFolderStructure creates the FBC/RPC/LOG/LIS directory tree with
// placeholder files, mirroring Python log_creator.py create_file_structure().
//
// For each node config, based on token types:
//   - FBC: create outputDir/FBC/{nodeName}/ and placeholder files
//     {nodeName}_{ip}_{tokenID}.fbc
//   - RPC: create outputDir/RPC/{nodeName}/ and placeholder files
//     {nodeName}_{ip}_{tokenID}.rpc
//   - LOG: create outputDir/LOG/ and placeholder file
//     {nodeName}_{ip}.log
//   - LIS: create outputDir/LIS/{nodeName}/ and placeholder files
//     {nodeName}_{ip}_exe{i}_5irb_5orb.lis (i=1..6)
func CreateFolderStructure(outputDir string, configs []types.NodeConfig) error {
	if err := os.MkdirAll(outputDir, 0755); err != nil {
		return fmt.Errorf("sysloader: create output dir %s: %w", outputDir, err)
	}

	for _, cfg := range configs {
		nodeName := strings.ReplaceAll(cfg.Name, " ", "_")
		if nodeName == "" {
			continue
		}

		// Format IP for filename (replace dots with hyphens, matching Python)
		ipFormatted := cfg.IPAddress
		if ipFormatted == "" {
			ipFormatted = "192.168.0.1"
		}
		ipFormatted = strings.ReplaceAll(ipFormatted, ".", "-")

		// Collect unique token types for this node
		tokenTypeSet := make(map[types.TokenType]bool)
		for _, tok := range cfg.Tokens {
			tokenTypeSet[tok.TokenType] = true
		}

		// FBC files
		if tokenTypeSet[types.TokenFBC] {
			nodeDir := filepath.Join(outputDir, "FBC", nodeName)
			if err := os.MkdirAll(nodeDir, 0755); err != nil {
				return fmt.Errorf("sysloader: create FBC dir %s: %w", nodeDir, err)
			}
			for _, tok := range cfg.Tokens {
				if tok.TokenType != types.TokenFBC {
					continue
				}
				fileName := fmt.Sprintf("%s_%s_%s.fbc", nodeName, ipFormatted, tok.TokenID)
				filePath := filepath.Join(nodeDir, fileName)
				if _, err := os.Stat(filePath); os.IsNotExist(err) {
					if err := os.WriteFile(filePath, []byte{}, 0644); err != nil {
						return fmt.Errorf("sysloader: create FBC file %s: %w", filePath, err)
					}
				}
			}
		}

		// RPC files
		if tokenTypeSet[types.TokenRPC] {
			nodeDir := filepath.Join(outputDir, "RPC", nodeName)
			if err := os.MkdirAll(nodeDir, 0755); err != nil {
				return fmt.Errorf("sysloader: create RPC dir %s: %w", nodeDir, err)
			}
			for _, tok := range cfg.Tokens {
				if tok.TokenType != types.TokenRPC {
					continue
				}
				fileName := fmt.Sprintf("%s_%s_%s.rpc", nodeName, ipFormatted, tok.TokenID)
				filePath := filepath.Join(nodeDir, fileName)
				if _, err := os.Stat(filePath); os.IsNotExist(err) {
					if err := os.WriteFile(filePath, []byte{}, 0644); err != nil {
						return fmt.Errorf("sysloader: create RPC file %s: %w", filePath, err)
					}
				}
			}
		}

		// LOG files
		if tokenTypeSet[types.TokenLOG] {
			logDir := filepath.Join(outputDir, "LOG")
			if err := os.MkdirAll(logDir, 0755); err != nil {
				return fmt.Errorf("sysloader: create LOG dir %s: %w", logDir, err)
			}
			fileName := fmt.Sprintf("%s_%s.log", nodeName, ipFormatted)
			filePath := filepath.Join(logDir, fileName)
			if _, err := os.Stat(filePath); os.IsNotExist(err) {
				if err := os.WriteFile(filePath, []byte{}, 0644); err != nil {
					return fmt.Errorf("sysloader: create LOG file %s: %w", filePath, err)
				}
			}
		}

		// LIS files (6 per node: exe1..exe6)
		if tokenTypeSet[types.TokenLIS] {
			lisDir := filepath.Join(outputDir, "LIS", nodeName)
			if err := os.MkdirAll(lisDir, 0755); err != nil {
				return fmt.Errorf("sysloader: create LIS dir %s: %w", lisDir, err)
			}
			for i := 1; i <= 6; i++ {
				fileName := fmt.Sprintf("%s_%s_exe%d_irb_orb.lis", nodeName, ipFormatted, i)
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
