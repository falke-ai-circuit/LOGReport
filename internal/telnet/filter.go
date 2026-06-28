package telnet

import (
	"regexp"
	"strings"
)

// ansiPattern matches ANSI escape sequences (CSI sequences ending in m or K).
// Mirrors Python telnet_client.py:191: re.sub(r'\x1b\[[0-9;]*[mK]', ”, text)
var ansiPattern = regexp.MustCompile(`\x1b\[[0-9;]*[mK]`)

// controlCharPattern matches control characters except newline (\x0A),
// carriage return (\x0D), and space (\x20).
// Backspaces (\x08) are handled separately by backspacePattern.
// Mirrors Python telnet_client.py:193: re.sub(r'[\x00-\x09\x0B-\x1F\x7F]', '', filtered)
var controlCharPattern = regexp.MustCompile(`[\x00-\x08\x0B-\x1F\x7F]`)

// backspacePattern matches a backspace character (\x08).
// DIA sends backspaces to erase echoed characters in INSERT mode.
// We process these by removing the previous character.
var backspacePattern = regexp.MustCompile("\x08")

// processBackspaces handles backspace sequences: each \x08 removes the
// preceding character. This strips the DIA's INSERT-mode command echo
// (it echoes "show all" then backspaces to erase it before processing).
func processBackspaces(s string) string {
	var result []rune
	for _, ch := range s {
		if ch == '\x08' {
			if len(result) > 0 {
				result = result[:len(result)-1]
			}
		} else {
			result = append(result, ch)
		}
	}
	return string(result)
}

// texitoggleurePattern matches the "texitoggleure" artifact.
// Mirrors Python telnet_client.py:196: re.sub(r'texitoggleure', ”, filtered)
var texitoggleurePattern = regexp.MustCompile(`texitoggleure`)

// multiSpacePattern matches runs of spaces/tabs.
// Mirrors Python telnet_client.py:198: re.sub(r'[ \t]+', ' ', filtered)
var multiSpacePattern = regexp.MustCompile(`[ \t]+`)

// leadingWhitespaceAfterNewline matches whitespace immediately after a newline.
// Mirrors Python telnet_client.py:199: re.sub(r'\n\s+', '\n', filtered)
var leadingWhitespaceAfterNewline = regexp.MustCompile(`\n[ \t]+`)

// FilterOutputNoBackspace is the same as FilterOutput but skips the
// backspace processing step (since backspaces are already processed
// on the accumulated buffer before calling this).
func FilterOutputNoBackspace(raw string) string {
	if raw == "" {
		return ""
	}

	// Step 1: Remove ANSI escape codes
	filtered := ansiPattern.ReplaceAllString(raw, "")

	// Step 2: Remove control characters but preserve newlines (\x0A)
	// and carriage returns (\x0D)
	filtered = controlCharPattern.ReplaceAllString(filtered, "")

	// Step 3: Remove the "texitoggleure" artifact
	filtered = texitoggleurePattern.ReplaceAllString(filtered, "")

	// Step 4: Normalize whitespace — collapse multiple spaces/tabs to single space
	filtered = multiSpacePattern.ReplaceAllString(filtered, " ")

	// Step 5: Remove leading whitespace after newlines
	filtered = leadingWhitespaceAfterNewline.ReplaceAllString(filtered, "\n")

	return strings.TrimSpace(filtered)
}

// FilterOutput cleans raw telnet response text by removing ANSI escape codes,
// control characters, known artifacts, and normalizing whitespace.
// It mirrors the Python telnet_client.py:185-201 _filter_output method.
func FilterOutput(raw string) string {
	if raw == "" {
		return ""
	}

	// Step 1: Remove ANSI escape codes
	filtered := ansiPattern.ReplaceAllString(raw, "")

	// Step 2: Process backspaces (DIA INSERT mode echo removal)
	// Each \x08 removes the preceding character — this strips the
	// echoed command text that DIA sends before processing.
	filtered = processBackspaces(filtered)

	// Step 3: Remove control characters but preserve newlines (\x0A)
	// and carriage returns (\x0D)
	filtered = controlCharPattern.ReplaceAllString(filtered, "")

	// Step 4: Remove the "texitoggleure" artifact
	filtered = texitoggleurePattern.ReplaceAllString(filtered, "")

	// Step 5: Normalize whitespace — collapse multiple spaces/tabs to single space
	filtered = multiSpacePattern.ReplaceAllString(filtered, " ")

	// Step 6: Remove leading whitespace after newlines
	filtered = leadingWhitespaceAfterNewline.ReplaceAllString(filtered, "\n")

	return strings.TrimSpace(filtered)
}
