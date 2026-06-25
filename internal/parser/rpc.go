// Package parser provides parsers for DNA telnet command output.
// rpc.go parses RPC (RUPI Counters) output into typed structs.
//
// Reference: Python fbc_parser_service.py:49-51 (RPC shares the same parser service)
// The RPC output format is similar to FBC but with counter values instead of channel types.
package parser

import (
	"fmt"
	"regexp"
	"strconv"
	"strings"

	"github.com/falke-ai-circuit/LOGReport/internal/types"
)

// RPC-specific regex patterns.
var (
	// rpcDigitPattern matches integer counter values in the middle section.
	// Used to extract all counter digits, which are then mapped to column positions.
	rpcDigitPattern = regexp.MustCompile(`\d+`)

	// rpcRowPattern matches an RPC data row: position, counter values, sum.
	// Uses non-greedy (.*?) for the middle section; the engine expands it
	// until the final whitespace-separated number is left as the sum group.
	// Format: position  counter1  counter2  ...  sum
	rpcRowPattern = regexp.MustCompile(`^\s*(\d+)\s+(.*?)\s+(\d+)\s*$`)

	// rpcTotalPattern matches the RPC footer summary line.
	// Python equivalent: simpler than FBC — just "Total sum: N counters"
	rpcTotalPattern = regexp.MustCompile(`Total sum:\s*(\d+)\s*counters`)
)

// extractCounters parses the counter values string (middle section of an RPC row)
// into a slice of RPCCounter, mapping each found value to its column name.
// All digit sequences in the string are treated as counter values.
// Extra values beyond the column count are ignored.
func extractCounters(counterStr string, columnNames []string) []types.RPCCounter {
	digits := rpcDigitPattern.FindAllString(counterStr, -1)
	if len(digits) == 0 {
		return nil
	}

	var counters []types.RPCCounter
	for i, d := range digits {
		if i >= len(columnNames) {
			break
		}
		val, err := strconv.Atoi(d)
		if err != nil {
			continue
		}
		counters = append(counters, types.RPCCounter{
			Name:  columnNames[i],
			Value: val,
		})
	}

	return counters
}

// parseRPCNotExistsRow handles a "Not Exists" row by extracting the position number
// and returning an RPCModule with Exists=false and no counters.
func parseRPCNotExistsRow(line string) *types.RPCModule {
	// Extract position number from beginning of line
	posRe := regexp.MustCompile(`^\s*(\d+)\s+`)
	m := posRe.FindStringSubmatch(line)
	if m == nil {
		return nil
	}
	pos, err := strconv.Atoi(m[1])
	if err != nil {
		return nil
	}
	return &types.RPCModule{
		Position: pos,
		Counters: []types.RPCCounter{},
		Exists:   false,
	}
}

// rpcHeaderPattern matches the RPC header line in a case-insensitive manner.
// Real Valmet DNA output uses lowercase "pic" (e.g. "pic  IREX ERROR  POLL ERROR...")
// but some nodes may output uppercase "PIC". This pattern accepts both.
// Unlike the FBC headerPattern which requires "sum" at the end, the RPC header
// has counter column names (IREX ERROR, POLL ERROR, etc.) and no "sum" suffix.
var rpcHeaderPattern = regexp.MustCompile(`(?i)^\s*(PIC|IBC)\s+(.+?)\s*$`)

// rpcColumnNames extracts column names from the RPC header.
// Unlike FBC which has numeric column positions (5, 6, 7, 8), the RPC header
// has text column names: "IREX ERROR  POLL ERROR  RESP FAIL  IREX COUNT  TIMEOUT".
// We split on 2+ whitespace to get individual column names.
var rpcColumnSplit = regexp.MustCompile(`\s{2,}`)

// parseRPCColumnNames extracts the counter column names from the RPC header.
// Returns the names as a slice (e.g. ["IREX ERROR", "POLL ERROR", "RESP FAIL", "IREX COUNT", "TIMEOUT"]).
// These become the names of the RPCCounter structs.
func parseRPCColumnNames(headerColPart string) []string {
	// Split on 2+ whitespace — the header columns are separated by multiple spaces
	parts := rpcColumnSplit.Split(strings.TrimSpace(headerColPart), -1)
	var names []string
	for _, p := range parts {
		p = strings.TrimSpace(p)
		if p != "" {
			names = append(names, p)
		}
	}
	return names
}

// ParseRPC parses RPC (RUPI Counters) telnet output into a slice of
// typed RPCModule structs. It detects PIC/IBC header format (case-insensitive
// to handle real DNA output which uses lowercase "pic"), extracts column
// names from the header (text-based, unlike FBC's numeric positions),
// parses each data row (including "Not Exists" rows), and returns
// the structured result.
//
// The input is raw telnet output (before FilterOutput whitespace normalization)
// so that empty counter slots (indicated by 4+ spaces) can be detected.
//
// Returns an empty slice (not nil) when no modules are found — this avoids the
// AXON gotcha where nil slices marshal to JSON null instead of [].
func ParseRPC(output string) ([]types.RPCModule, error) {
	lines := strings.Split(output, "\n")

	// Find header line using case-insensitive RPC-specific pattern.
	// Real DNA output uses lowercase "pic" — the FBC headerPattern requires
	// uppercase "PIC" and a "sum" suffix, which RPC headers don't have.
	headerIdx := -1
	var columnNames []string

	for i, line := range lines {
		m := rpcHeaderPattern.FindStringSubmatch(line)
		if m != nil {
			headerIdx = i
			// Extract column names from the header (text-based, not numeric)
			columnNames = parseRPCColumnNames(m[2])
			break
		}
	}

	if headerIdx == -1 {
		return nil, fmt.Errorf("rpc parser: no PIC/IBC header found in output")
	}

	if len(columnNames) == 0 {
		return nil, fmt.Errorf("rpc parser: no counter columns found in header")
	}

	// Find total/footer line to determine data range
	totalIdx := -1
	for i := headerIdx + 1; i < len(lines); i++ {
		if rpcTotalPattern.MatchString(lines[i]) {
			totalIdx = i
			break
		}
	}

	endIdx := totalIdx
	if endIdx == -1 {
		endIdx = len(lines)
	}

	// Parse data rows between header and footer
	var modules []types.RPCModule

	for i := headerIdx + 1; i < endIdx; i++ {
		line := strings.TrimSpace(lines[i])

		// Skip blank lines and separators
		if line == "" || strings.HasPrefix(line, "---") || strings.HasPrefix(line, "===") {
			continue
		}

		// Check for "Not Exists" rows (case-insensitive)
		if notExistsPattern.MatchString(line) {
			mod := parseRPCNotExistsRow(lines[i]) // use original line for position extraction
			if mod != nil {
				modules = append(modules, *mod)
			}
			continue
		}

		// Parse standard data row
		// Use original (untrimmed) line for regex matching to preserve leading spaces
		m := rpcRowPattern.FindStringSubmatch(lines[i])
		if m == nil {
			continue // skip malformed rows
		}

		pos, err := strconv.Atoi(m[1])
		if err != nil {
			continue
		}

		counterStr := m[2]
		counters := extractCounters(counterStr, columnNames)

		// AXON safety: ensure counters is never nil
		if counters == nil {
			counters = []types.RPCCounter{}
		}

		modules = append(modules, types.RPCModule{
			Position: pos,
			Counters: counters,
			Exists:   true,
		})
	}

	// AXON gotcha: return empty slice, not nil
	if modules == nil {
		modules = []types.RPCModule{}
	}

	return modules, nil
}

// ParseRPCHeaderType extracts just the header type (PIC or IBC) from RPC output.
// Returns an empty string if no header is found.
func ParseRPCHeaderType(output string) types.HeaderType {
	lines := strings.Split(output, "\n")
	for _, line := range lines {
		m := rpcHeaderPattern.FindStringSubmatch(line)
		if m != nil {
			return types.HeaderType(strings.ToUpper(m[1]))
		}
	}
	return ""
}

// RPCTotals holds the parsed RPC footer summary.
type RPCTotals struct {
	TotalCounters int
}

// ParseRPCTotals extracts the totals footer from RPC output.
// Returns the totals struct and true if found, zero values and false otherwise.
func ParseRPCTotals(output string) (RPCTotals, bool) {
	lines := strings.Split(output, "\n")
	for _, line := range lines {
		m := rpcTotalPattern.FindStringSubmatch(line)
		if m != nil {
			totalCounters, _ := strconv.Atoi(m[1])
			return RPCTotals{
				TotalCounters: totalCounters,
			}, true
		}
	}
	return RPCTotals{}, false
}
