// Package telnet provides error detection for command output.
// Mirrors the Python error_detection.py regex-based approach.
package telnet

import (
	"regexp"
	"strings"
)

// errorPatterns matches common DIA/BsTool error indicators.
// Case-insensitive. Matches substrings, not whole lines.
var errorPatterns = regexp.MustCompile(`(?i)(error|failure|exception|timeout|not found|syntax error|permission denied|unknown command|no such|invalid|failed)`)

// validResponsePatterns matches lines that indicate legitimate output:
// numbered lines, table data, prompts, timestamps, hex addresses.
var validResponsePatterns = regexp.MustCompile(`(?i)^\s*\d+[.)\s]|\b\d{2}:\d{2}:\d{2}\b|0x[0-9a-f]+|\bmodule\b|\bchannel\b|\bstation\b|>>>|\$`)

// belMarkerPattern matches the BEL error indicator produced by filter.go.
var belMarkerPattern = regexp.MustCompile(`\[BEL\]`)

// IsErrorResponse checks whether command output indicates an error.
// Returns true only if error patterns are found AND no valid response
// content is present. This prevents false positives on legitimate output
// that happens to contain words like "error" in a data column.
func IsErrorResponse(output string) bool {
	if output == "" {
		return false
	}

	// Check for explicit BEL marker — always an error
	if belMarkerPattern.MatchString(output) {
		// But verify there's no valid content alongside the BEL
		// (some outputs may have a BEL at the end after valid data)
		stripped := belMarkerPattern.ReplaceAllString(output, "")
		stripped = strings.TrimSpace(stripped)
		if stripped == "" {
			return true
		}
		// If there IS content after removing BEL, check if it's valid
		if hasValidContent(stripped) {
			return false
		}
		return true
	}

	// No BEL — check for error keywords
	if !errorPatterns.MatchString(output) {
		return false
	}

	// Error keywords found — check if there's valid response content
	if hasValidContent(output) {
		return false
	}

	return true
}

// hasValidContent returns true if the output contains lines that look like
// legitimate structured data (numbers, tables, prompts, timestamps).
func hasValidContent(output string) bool {
	lines := strings.Split(output, "\n")
	for _, line := range lines {
		line = strings.TrimSpace(line)
		if line == "" {
			continue
		}
		if validResponsePatterns.MatchString(line) {
			return true
		}
	}
	return false
}