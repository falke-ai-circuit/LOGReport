// Package parser provides parsers for DNA telnet command output.
// sysfile.go parses Valmet DNA .sys configuration files into typed structs.
//
// Reference: Python sys_file_parser.py:293 lines (src/commander/utils/)
// and Python file_utils.py parse_sys_file (src/utils/)
package parser

import (
	"bufio"
	"fmt"
	"os"
	"regexp"
	"strings"

	"github.com/falke-ai-circuit/LOGReport/internal/types"
)

// Regex patterns for :e:hw: token mapping format.
// Python sys_file_parser.py:71-86
var (
	// sysEntryPattern matches :e:hw:<hex> <LID> <config> [// comment]
	// Python ENTRY_PATTERN: r'^:e:hw:([0-9a-fA-F]{2,4})\s+(\w+)\s+([\w:\-]+)(?:\s*//\s*(.*))?$'
	sysEntryPattern = regexp.MustCompile(
		`^:e:hw:([0-9a-fA-F]{2,4})\s+` + // Hardware address (2-4 hex digits)
			`(\w+)\s+` + // LID (alphanumeric with underscores)
			`([\w:\-]+)` + // Config (pxe:*, or just -)
			`(?:\s*//\s*(.*))?$`, // Optional comment
	)

	// sysEntryFlexPattern handles entries with tabs and irregular spacing.
	// Python ENTRY_PATTERN_FLEXIBLE: r'^:e:hw:([0-9a-fA-F]{2,4})[\s\t]+(\w+)[\s\t]+([\w:\-]+)(?:[\s\t]*//[\s\t]*(.*))?'
	sysEntryFlexPattern = regexp.MustCompile(
		`^:e:hw:([0-9a-fA-F]{2,4})` + // Hardware address
			`[\s\t]+` + // Any whitespace
			`(\w+)` + // LID
			`[\s\t]+` + // Any whitespace
			`([\w:\-]+)` + // Config
			`(?:[\s\t]*//[\s\t]*(.*))?`, // Optional comment
	)
)

// Regex patterns for slot configuration format.
var (
	// slotPattern matches "Slot N" lines.
	slotPattern = regexp.MustCompile(`^Slot\s+(\d+)\s*$`)

	// titlePattern matches "TITLE=..." lines, stripping trailing // comments.
	titlePattern = regexp.MustCompile(`^TITLE=(.+?)(?:\s*//.*)?$`)

	// programPattern matches "PROGRAM=..." lines, stripping trailing // comments.
	programPattern = regexp.MustCompile(`^PROGRAM=(.+?)(?:\s*//.*)?$`)

	// ipAddrPattern matches "set XD_IP_ADDR=..." lines.
	ipAddrPattern = regexp.MustCompile(`^set\s+XD_IP_ADDR=(\S+)`)
)

// SysFileResult holds the parsed output from a .sys file.
type SysFileResult struct {
	Entries []types.SysFileEntry // :e:hw: token mapping entries
	Nodes   []types.SysFileNode  // Slot configuration nodes
	IPAddr  string               // Extracted IP address (from set XD_IP_ADDR)
}

// ParseSysFile parses a Valmet DNA .sys file from the given path.
// It handles both :e:hw: token mapping format and slot configuration format.
// Returns a SysFileResult with entries and/or nodes, or an error if the file
// cannot be read.
func ParseSysFile(path string) (*SysFileResult, error) {
	f, err := os.Open(path)
	if err != nil {
		return nil, fmt.Errorf("sysfile parser: cannot open %s: %w", path, err)
	}
	defer f.Close()

	scanner := bufio.NewScanner(f)
	scanner.Buffer(make([]byte, 0, 1024*1024), 1024*1024) // 1MB max line — handles binary .sys files
	return parseSysFileScanner(scanner)
}

// ParseSysFileString parses .sys file content from a string.
// Useful for testing with inline fixtures.
func ParseSysFileString(content string) *SysFileResult {
	scanner := bufio.NewScanner(strings.NewReader(content))
	scanner.Buffer(make([]byte, 0, 1024*1024), 1024*1024) // 1MB max line — consistent with ParseSysFile
	result, _ := parseSysFileScanner(scanner)
	return result
}

// parseSysFileScanner is the core parser that works with a bufio.Scanner.
func parseSysFileScanner(scanner *bufio.Scanner) (*SysFileResult, error) {
	result := &SysFileResult{
		Entries: []types.SysFileEntry{},
		Nodes:   []types.SysFileNode{},
	}

	var currentSlot *slotBuilder
	var ipAddr string

	lineNum := 0
	for scanner.Scan() {
		lineNum++
		line := scanner.Text()
		line = strings.TrimRight(line, "\r")

		// Skip empty lines
		if strings.TrimSpace(line) == "" {
			continue
		}

		// Skip pure comment lines
		trimmed := strings.TrimSpace(line)
		if strings.HasPrefix(trimmed, "//") {
			continue
		}

		// Try :e:hw: format first
		if strings.HasPrefix(trimmed, ":e:hw:") {
			entry := parseSysEntryLine(trimmed, lineNum)
			if entry != nil {
				result.Entries = append(result.Entries, *entry)
			}
			continue
		}

		// Extract IP address
		if m := ipAddrPattern.FindStringSubmatch(trimmed); m != nil {
			ipAddr = m[1]
			continue
		}

		// Slot configuration format
		if m := slotPattern.FindStringSubmatch(trimmed); m != nil {
			// Flush previous slot if any
			flushSlot(currentSlot, result)
			currentSlot = &slotBuilder{}
			continue
		}

		// Check for TITLE= or PROGRAM= lines
		if m := titlePattern.FindStringSubmatch(trimmed); m != nil {
			title := strings.TrimSpace(m[1])
			// If we're not inside a Slot block, start a new implicit slot
			// (handles NCU2-style sections that have no "Slot N" prefix)
			if currentSlot == nil {
				currentSlot = &slotBuilder{}
			}
			currentSlot.title = title
			continue
		}

		if m := programPattern.FindStringSubmatch(trimmed); m != nil {
			program := strings.TrimSpace(m[1])
			if currentSlot == nil {
				currentSlot = &slotBuilder{}
			}
			currentSlot.program = program
			continue
		}
	}

	// Flush last slot
	flushSlot(currentSlot, result)

	if err := scanner.Err(); err != nil {
		return nil, fmt.Errorf("sysfile parser: read error: %w", err)
	}

	result.IPAddr = ipAddr

	// AXON safety: ensure slices are never nil
	if result.Entries == nil {
		result.Entries = []types.SysFileEntry{}
	}
	if result.Nodes == nil {
		result.Nodes = []types.SysFileNode{}
	}

	return result, nil
}

// flushSlot builds a node from the current slot builder and appends it to result.
func flushSlot(sb *slotBuilder, result *SysFileResult) {
	if sb == nil {
		return
	}
	node := sb.build()
	if node != nil {
		result.Nodes = append(result.Nodes, *node)
	}
}

// slotBuilder accumulates attributes for a single Slot section.
type slotBuilder struct {
	title   string
	program string
}

// build converts accumulated slot attributes into a SysFileNode.
// Returns nil if no title was collected (title is required).
func (sb *slotBuilder) build() *types.SysFileNode {
	if sb.title == "" {
		return nil
	}

	lid := sb.title
	name := sb.title
	nodeType := resolveNodeType(lid)

	// Detect fieldbus slots: PROGRAM contains FBC_CODE (covers <FBC_CODE>,
	// <CIO_FBC_CODE>, <MIO_FBC_CODE>)
	isFieldbus := strings.Contains(sb.program, "FBC_CODE")

	// Extract fieldbus type from PROGRAM string (CIO, MIO, PROFIBUS, IBC)
	fieldbusType := ""
	if isFieldbus {
		switch {
		case strings.Contains(sb.program, "CIO"):
			fieldbusType = "CIO"
		case strings.Contains(sb.program, "MIO"):
			fieldbusType = "MIO"
		case strings.Contains(sb.program, "PROFIBUS"):
			fieldbusType = "PROFIBUS"
		case strings.Contains(sb.program, "IBC"):
			fieldbusType = "IBC"
		}
	}

	return &types.SysFileNode{
		LID:         lid,
		Name:        name,
		Type:        nodeType,
		Program:     sb.program,
		IsFieldbus:  isFieldbus,
		FieldbusType: fieldbusType,
	}
}

// parseSysEntryLine parses a single :e:hw: line into a SysFileEntry.
// Returns nil if the line cannot be parsed.
func parseSysEntryLine(line string, lineNum int) *types.SysFileEntry {
	// Try standard pattern first
	m := sysEntryPattern.FindStringSubmatch(line)
	if m == nil {
		// Try flexible pattern for irregular spacing
		m = sysEntryFlexPattern.FindStringSubmatch(line)
	}
	if m == nil {
		return nil
	}

	lid := m[2]
	config := m[3]
	comment := ""
	if len(m) > 4 {
		comment = strings.TrimSpace(m[4])
	}

	// Determine node type from LID prefix
	nodeType := resolveNodeType(lid)

	// Build description: prefer comment, fall back to config
	description := comment
	if description == "" {
		description = config
	}

	// HWAddr is the hardware address from regex group 1 (e.g. "222", "1a1")
	hwAddr := m[1]

	return &types.SysFileEntry{
		HWAddr:      hwAddr,
		LID:         lid,
		NodeType:    nodeType,
		Description: description,
	}
}

// resolveNodeType determines the node type from a LID string.
// Uses the LIDMapping from types package, matching longest prefix first.
// Python sys_file_parser.py:220-239 (get_node_type_from_lid)
func resolveNodeType(lid string) string {
	// Check for exact matches first (like INFO)
	if t, ok := types.LIDMapping[lid]; ok {
		return t
	}

	// Check prefixes (longest match first)
	var bestMatch string
	bestLen := 0
	for prefix, nodeType := range types.LIDMapping {
		if strings.HasPrefix(lid, prefix) && len(prefix) > bestLen {
			bestMatch = nodeType
			bestLen = len(prefix)
		}
	}

	if bestMatch != "" {
		return bestMatch
	}

	return "UNKNOWN"
}
