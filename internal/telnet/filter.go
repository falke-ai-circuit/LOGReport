package telnet

import (
	"regexp"
	"strings"
)

// ansiPattern matches ANSI escape sequences (CSI sequences ending in m or K).
// Mirrors Python telnet_client.py:191: re.sub(r'\x1b\[[0-9;]*[mK]', '', text)
var ansiPattern = regexp.MustCompile(`\x1b\[[0-9;]*[mK]`)

// controlCharPattern matches control characters except newline (\x0A).
// Mirrors Python telnet_client.py:193: re.sub(r'[\x00-\x09\x0B-\x1F\x7F]', '', filtered)
var controlCharPattern = regexp.MustCompile(`[\x00-\x09\x0B-\x1F\x7F]`)

// texitoggleurePattern matches the "texitoggleure" artifact.
// Mirrors Python telnet_client.py:196: re.sub(r'texitoggleure', '', filtered)
var texitoggleurePattern = regexp.MustCompile(`texitoggleure`)

// multiSpacePattern matches runs of spaces/tabs.
// Mirrors Python telnet_client.py:198: re.sub(r'[ \t]+', ' ', filtered)
var multiSpacePattern = regexp.MustCompile(`[ \t]+`)

// leadingWhitespaceAfterNewline matches whitespace immediately after a newline.
// Mirrors Python telnet_client.py:199: re.sub(r'\n\s+', '\n', filtered)
var leadingWhitespaceAfterNewline = regexp.MustCompile(`\n[ \t]+`)

// FilterOutput cleans raw telnet response text by removing ANSI escape codes,
// control characters, known artifacts, and normalizing whitespace.
// It mirrors the Python telnet_client.py:185-201 _filter_output method.
func FilterOutput(raw string) string {
	if raw == "" {
		return ""
	}

	// Step 1: Remove ANSI escape codes
	filtered := ansiPattern.ReplaceAllString(raw, "")

	// Step 2: Remove control characters but preserve newlines (\x0A)
	filtered = controlCharPattern.ReplaceAllString(filtered, "")

	// Step 3: Remove the "texitoggleure" artifact
	filtered = texitoggleurePattern.ReplaceAllString(filtered, "")

	// Step 4: Normalize whitespace — collapse multiple spaces/tabs to single space
	filtered = multiSpacePattern.ReplaceAllString(filtered, " ")

	// Step 5: Remove leading whitespace after newlines
	filtered = leadingWhitespaceAfterNewline.ReplaceAllString(filtered, "\n")

	return strings.TrimSpace(filtered)
}
