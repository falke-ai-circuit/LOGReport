package fbc

import (
	"bufio"
	"fmt"
	"os"
	"strings"
)

// IORow represents a single IO point from FBC output
type IORow struct {
	Index  string `json:"index"`
	Type   string `json:"type"`
	Name   string `json:"name"`
	Value  string `json:"value"`
	Status string `json:"status"`
}

// FBCResult holds parsed FBC output for one node+token
type FBCResult struct {
	Node    string  `json:"node"`
	Token   string  `json:"token"`
	Rows    []IORow `json:"rows"`
	Raw     string  `json:"raw"`
	Error   string  `json:"error,omitempty"`
}

// ParseFile parses a .fbc file from disk
func ParseFile(path, node, token string) (*FBCResult, error) {
	f, err := os.Open(path)
	if err != nil {
		return nil, fmt.Errorf("open %s: %w", path, err)
	}
	defer f.Close()

	var sb strings.Builder
	var rows []IORow
	scanner := bufio.NewScanner(f)
	for scanner.Scan() {
		line := scanner.Text()
		sb.WriteString(line + "\n")
		row := parseLine(line)
		if row != nil {
			rows = append(rows, *row)
		}
	}
	return &FBCResult{Node: node, Token: token, Rows: rows, Raw: sb.String()}, nil
}

// ParseOutput parses raw telnet output string
func ParseOutput(raw, node, token string) *FBCResult {
	var rows []IORow
	for _, line := range strings.Split(raw, "\n") {
		row := parseLine(line)
		if row != nil {
			rows = append(rows, *row)
		}
	}
	return &FBCResult{Node: node, Token: token, Rows: rows, Raw: raw}
}

func parseLine(line string) *IORow {
	line = strings.TrimSpace(line)
	if line == "" || strings.HasPrefix(line, "#") || strings.HasPrefix(line, "-") {
		return nil
	}
	// Typical FBC line: "  001  DI   Valve_Open          1    OK"
	// or:               "  001  DO   Pump_Run            0    OK"
	fields := strings.Fields(line)
	if len(fields) < 3 {
		return nil
	}
	// Index must be numeric-ish
	idx := fields[0]
	if len(idx) == 0 || (idx[0] < '0' || idx[0] > '9') {
		return nil
	}
	row := &IORow{Index: idx}
	if len(fields) >= 2 {
		row.Type = fields[1]
	}
	if len(fields) >= 3 {
		row.Name = fields[2]
	}
	if len(fields) >= 4 {
		row.Value = fields[3]
	}
	if len(fields) >= 5 {
		row.Status = strings.Join(fields[4:], " ")
	}
	return row
}
