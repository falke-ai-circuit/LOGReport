// Package parser provides parsers for DNA telnet command output.
// fbc.go parses FBC (FieldBus Configuration) output into typed structs.
//
// Reference: Python fbc_parser_service.py:29-361
package parser

import (
	"fmt"
	"regexp"
	"strconv"
	"strings"

	"github.com/falke-ai-circuit/LOGReport/internal/types"
)

// Regex patterns mirroring Python fbc_parser_service.py:42-46.
var (
	// headerPattern matches "PIC  5  6  7  8  sum" or "IBC  0  1  2  3  sum".
	// Case-insensitive: real Valmet DNA output may use lowercase "pic" (see rpc.go:83).
	// Python: r'\s*(PIC|IBC)\s+(.+?)\s*sum\s*$'
	headerPattern = regexp.MustCompile(`(?i)^\s*(PIC|IBC)\s+(.+?)\s*sum\s*$`)

	// rowPattern matches a data row: position, I/O units string, sum.
	// Python: r'^\s*(\d+)\s(.+)\s(\d+)\s*$'
	// Uses single \s (not \s+) to preserve leading spaces that indicate empty first slots.
	rowPattern = regexp.MustCompile(`^\s*(\d+)\s(.+)\s(\d+)\s*$`)

	// totalPattern matches the footer summary line.
	// Python: r'Total sum:\s*(\d+)\s*I/O-units,\s*(\d+)\s*Channels\s*\((\d+)\s*input,\s*(\d+)\s*output\)'
	totalPattern = regexp.MustCompile(`Total sum:\s*(\d+)\s*I/O-units,\s*(\d+)\s*Channels\s*\((\d+)\s*input,\s*(\d+)\s*output\)`)

	// ioUnitPattern matches I/O unit type codes in the row's middle section.
	// Alternation: group 1 captures a unit code (e.g. AI8, BI8N, Di16),
	// or matches 4+ spaces indicating an empty slot.
	// Python: r'([A-Z][A-Za-z]\d+N?)|\s{4,}'
	ioUnitPattern = regexp.MustCompile(`([A-Z][A-Za-z]\d+N?)|\s{4,}`)

	// columnNumPattern extracts digit sequences from the header's column part.
	columnNumPattern = regexp.MustCompile(`\d+`)

	// notExistsPattern detects "Not Exists" rows (case-insensitive).
	notExistsPattern = regexp.MustCompile(`(?i)not\s+exists`)
)

// channelSum extracts the channel count from a ChannelType by parsing its numeric suffix.
// AI8 → 8, AO4 → 4, DI16 → 16, BI8N → 8, N/E → 0.
func channelSum(ct types.ChannelType) int {
	s := string(ct)
	// Find digits in the type string
	digits := regexp.MustCompile(`\d+`).FindString(s)
	if digits == "" {
		return 0
	}
	n, _ := strconv.Atoi(digits)
	return n
}

// resolveChannelType maps a raw I/O unit code string (e.g. "AI8", "BI8N", "Di16")
// to the corresponding ChannelType constant. Returns NotExists for unrecognized codes.
func resolveChannelType(raw string) types.ChannelType {
	// Normalize to uppercase for matching
	upper := strings.ToUpper(raw)

	// Direct map lookup
	direct := map[string]types.ChannelType{
		"AI8":  types.AI8,
		"AO4":  types.AO4,
		"AO8":  types.AO8,
		"DI16": types.DI16,
		"DO16": types.DO16,
		"BI8":  types.BI8,
		"BI8N": types.BI8N,
		"BO8":  types.BO8,
		"TI6":  types.TI6,
		"TO6":  types.TO6,
		"PI4":  types.PI4,
		"PO4":  types.PO4,
		"SI8":  types.SI8,
		"SO8":  types.SO8,
		"CI4":  types.CI4,
		"CO4":  types.CO4,
		"RI4":  types.RI4,
		"RO4":  types.RO4,
		"II4":  types.II4,
		"IO4":  types.IO4,
		"N/E":  types.NotExists,
	}

	if ct, ok := direct[upper]; ok {
		return ct
	}

	// Handle N-suffix variants not in the direct map (e.g. "AO4N")
	base := strings.TrimSuffix(upper, "N")
	if ct, ok := direct[base]; ok {
		return ct
	}

	return types.NotExists
}

// extractChannels parses the I/O units string (middle section of a row) into
// a slice of FBCChannel, mapping each found unit to its column position.
// Empty slots (4+ spaces) are skipped — no channel is created for them.
// Extra units beyond the column count are ignored.
func extractChannels(ioUnitsStr string, columnPositions []int) []types.FBCChannel {
	matches := ioUnitPattern.FindAllStringSubmatchIndex(ioUnitsStr, -1)
	if len(matches) == 0 {
		return nil
	}

	var channels []types.FBCChannel
	colIdx := 0

	for _, m := range matches {
		if colIdx >= len(columnPositions) {
			break
		}

		// m[0], m[1] = full match bounds
		// m[2], m[3] = group 1 bounds (I/O unit code); -1 if empty-slot match
		if m[2] != -1 {
			unitCode := ioUnitsStr[m[2]:m[3]]
			ct := resolveChannelType(unitCode)
			channels = append(channels, types.FBCChannel{
				Position: columnPositions[colIdx],
				Type:     ct,
				Sum:      channelSum(ct),
			})
		}
		// else: empty slot (4+ spaces) — advance column index without creating a channel
		colIdx++
	}

	return channels
}

// parseNotExistsRow handles a "Not Exists" row by extracting the position number
// and returning an FBCModule with Exists=false and no channels.
func parseNotExistsRow(line string) *types.FBCModule {
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
	return &types.FBCModule{
		Position: pos,
		Channels: []types.FBCChannel{},
		Exists:   false,
	}
}

// ParseFBC parses FBC (FieldBus Configuration) telnet output into a slice of
// typed FBCModule structs. It detects PIC/IBC header format, extracts column
// positions, parses each data row (including "Not Exists" rows), and returns
// the structured result.
//
// The input is raw telnet output (before FilterOutput whitespace normalization)
// so that empty I/O slots (indicated by 4+ spaces) can be detected.
//
// Returns an empty slice (not nil) when no modules are found — this avoids the
// AXON gotcha where nil slices marshal to JSON null instead of [].
func ParseFBC(output string) ([]types.FBCModule, error) {
	lines := strings.Split(output, "\n")

	// Find header line
	headerIdx := -1
	var columnPositions []int

	for i, line := range lines {
		m := headerPattern.FindStringSubmatch(line)
		if m != nil {
			headerIdx = i
			// Extract column numbers from the header (e.g. "5  6  7  8")
			colPart := m[2]
			colNums := columnNumPattern.FindAllString(colPart, -1)
			for _, cn := range colNums {
				n, err := strconv.Atoi(cn)
				if err != nil {
					continue
				}
				columnPositions = append(columnPositions, n)
			}
			break
		}
	}

	if headerIdx == -1 {
		return nil, fmt.Errorf("fbc parser: no PIC/IBC header found in output")
	}

	if len(columnPositions) == 0 {
		return nil, fmt.Errorf("fbc parser: no channel columns found in header")
	}

	// Find total/footer line to determine data range
	totalIdx := -1
	for i := headerIdx + 1; i < len(lines); i++ {
		if totalPattern.MatchString(lines[i]) {
			totalIdx = i
			break
		}
	}

	endIdx := totalIdx
	if endIdx == -1 {
		endIdx = len(lines)
	}

	// Parse data rows between header and footer
	var modules []types.FBCModule

	for i := headerIdx + 1; i < endIdx; i++ {
		line := strings.TrimSpace(lines[i])

		// Skip blank lines and separators
		if line == "" || strings.HasPrefix(line, "---") || strings.HasPrefix(line, "===") {
			continue
		}

		// Check for "Not Exists" rows (case-insensitive)
		if notExistsPattern.MatchString(line) {
			mod := parseNotExistsRow(lines[i]) // use original line for position extraction
			if mod != nil {
				modules = append(modules, *mod)
			}
			continue
		}

		// Parse standard data row
		// Use original (untrimmed) line for regex matching to preserve leading spaces
		m := rowPattern.FindStringSubmatch(lines[i])
		if m == nil {
			continue // skip malformed rows
		}

		pos, err := strconv.Atoi(m[1])
		if err != nil {
			continue
		}

		ioUnitsStr := m[2]
		channels := extractChannels(ioUnitsStr, columnPositions)

		// AXON safety: ensure channels is never nil
		if channels == nil {
			channels = []types.FBCChannel{}
		}

		modules = append(modules, types.FBCModule{
			Position: pos,
			Channels: channels,
			Exists:   true,
		})
	}

	// AXON gotcha: return empty slice, not nil
	if modules == nil {
		modules = []types.FBCModule{}
	}

	return modules, nil
}

// ParseFBCHeaderType extracts just the header type (PIC or IBC) from FBC output.
// Returns an empty string if no header is found.
func ParseFBCHeaderType(output string) types.HeaderType {
	lines := strings.Split(output, "\n")
	for _, line := range lines {
		m := headerPattern.FindStringSubmatch(line)
		if m != nil {
			return types.HeaderType(strings.ToUpper(m[1])) // canonical uppercase
		}
	}
	return ""
}

// ParseFBCTotals extracts the totals footer from FBC output.
// Returns the totals struct and true if found, zero values and false otherwise.
type FBCTotals struct {
	TotalUnits     int
	TotalChannels  int
	InputChannels  int
	OutputChannels int
}

func ParseFBCTotals(output string) (FBCTotals, bool) {
	lines := strings.Split(output, "\n")
	for _, line := range lines {
		m := totalPattern.FindStringSubmatch(line)
		if m != nil {
			totalUnits, _ := strconv.Atoi(m[1])
			totalChannels, _ := strconv.Atoi(m[2])
			inputChannels, _ := strconv.Atoi(m[3])
			outputChannels, _ := strconv.Atoi(m[4])
			return FBCTotals{
				TotalUnits:     totalUnits,
				TotalChannels:  totalChannels,
				InputChannels:  inputChannels,
				OutputChannels: outputChannels,
			}, true
		}
	}
	return FBCTotals{}, false
}
