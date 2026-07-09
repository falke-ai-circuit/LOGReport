package rpc

import (
	"bufio"
	"fmt"
	"os"
	"strings"
)

// Counter represents one RPC error counter row
type Counter struct {
	Name  string `json:"name"`
	Value string `json:"value"`
	Unit  string `json:"unit,omitempty"`
}

// RPCResult holds parsed RPC counters for one node+token
type RPCResult struct {
	Node     string    `json:"node"`
	Token    string    `json:"token"`
	Counters []Counter `json:"counters"`
	Raw      string    `json:"raw"`
	Error    string    `json:"error,omitempty"`
}

// ParseFile parses a .rpc file from disk
func ParseFile(path, node, token string) (*RPCResult, error) {
	f, err := os.Open(path)
	if err != nil {
		return nil, fmt.Errorf("open %s: %w", path, err)
	}
	defer f.Close()

	var sb strings.Builder
	var counters []Counter
	scanner := bufio.NewScanner(f)
	for scanner.Scan() {
		line := scanner.Text()
		sb.WriteString(line + "\n")
		c := parseLine(line)
		if c != nil {
			counters = append(counters, *c)
		}
	}
	return &RPCResult{Node: node, Token: token, Counters: counters, Raw: sb.String()}, nil
}

// ParseOutput parses raw telnet output
func ParseOutput(raw, node, token string) *RPCResult {
	var counters []Counter
	for _, line := range strings.Split(raw, "\n") {
		c := parseLine(line)
		if c != nil {
			counters = append(counters, *c)
		}
	}
	return &RPCResult{Node: node, Token: token, Counters: counters, Raw: raw}
}

func parseLine(line string) *Counter {
	line = strings.TrimSpace(line)
	if line == "" || strings.HasPrefix(line, "#") || strings.HasPrefix(line, "-") {
		return nil
	}
	// Typical RPC line: "  CRC errors           :   0"
	// or:               "  Frame errors         :   12   frames"
	if !strings.Contains(line, ":") {
		return nil
	}
	parts := strings.SplitN(line, ":", 2)
	if len(parts) != 2 {
		return nil
	}
	name := strings.TrimSpace(parts[0])
	rest := strings.TrimSpace(parts[1])
	if name == "" {
		return nil
	}
	fields := strings.Fields(rest)
	c := &Counter{Name: name}
	if len(fields) >= 1 {
		c.Value = fields[0]
	}
	if len(fields) >= 2 {
		c.Unit = strings.Join(fields[1:], " ")
	}
	return c
}
