package telnet

import (
	"regexp"
	"strings"
)

// ansiPattern matches ANSI escape sequences (CSI sequences ending in m or K).
// Mirrors Python telnet_client.py:191: re.sub(r'\x1b\[[0-9;]*[mK]', ”, text)
var ansiPattern = regexp.MustCompile(`\x1b\[[0-9;]*[mK]`)

// belPattern matches the BEL character (0x07) and converts it to a visible
// error indicator. DIA sends BEL when a command fails (e.g., invalid command
// or no process station running). Without this, the error is silently stripped.
var belPattern = regexp.MustCompile("\x07")

// controlCharPattern matches control characters except BEL (0x07, handled
// separately), newline (\x0A), carriage return (\x0D), and space (\x20).
// Backspaces (\x08) are handled separately by backspacePattern.
var controlCharPattern = regexp.MustCompile(`[\x00-\x06\x08\x0B-\x1F\x7F]`)

// backspacePattern matches a backspace character (\x08).
// DIA sends backspaces to erase echoed characters in INSERT mode.
// We process these by removing the previous character.
var backspacePattern = regexp.MustCompile("\x08")

// stripBackspaces removes all backspace (0x08) characters from the string.
// This matches the Python telnet_client.py approach which strips ALL control
// chars in the range \x00-\x09 (which includes 0x08) via:
//   re.sub(r'[\x00-\x09\x0B-\x1F\x7F]', '', filtered)
//
// We strip backspaces rather than processing them as erase operations because
// the DIA's INSERT-mode echo produces interleaved char+backspace sequences that
// would erase actual response content if processed as erase operations.
// The Python code simply removes them, and we match that behavior.
func stripBackspaces(s string) string {
	return strings.ReplaceAll(s, "\x08", "")
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

// FilterOutputNoBackspace is the same as FilterOutput. The name is kept for
// backward compatibility — callers that previously did processBackspaces then
// FilterOutputNoBackspace now just call FilterOutput (which strips backspaces
// as control chars, matching the Python reference implementation).
func FilterOutputNoBackspace(raw string) string {
	return FilterOutput(raw)
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

	// Step 2: Strip backspaces (0x08) — not process as erase, just remove.
	// This matches Python which strips all \x00-\x09 control chars including 0x08.
	filtered = stripBackspaces(filtered)

	// Step 2b: Convert BEL (0x07) to a visible error indicator.
	// DIA sends BEL when a command fails (invalid command, no process station,
	// permission denied). Stripping it silently hides errors from the user.
	// We convert it to "[BEL]" so the caller knows the command produced an error.
	filtered = belPattern.ReplaceAllString(filtered, "[BEL]")

	// Step 3: Remove control characters but preserve newlines (\x0A)
	// and carriage returns (\x0D). BEL is already handled above.
	filtered = controlCharPattern.ReplaceAllString(filtered, "")

	// Step 4: Remove the "texitoggleure" artifact
	filtered = texitoggleurePattern.ReplaceAllString(filtered, "")

	// Step 5: Normalize whitespace — collapse multiple spaces/tabs to single space
	filtered = multiSpacePattern.ReplaceAllString(filtered, " ")

	// Step 6: Remove leading whitespace after newlines
	filtered = leadingWhitespaceAfterNewline.ReplaceAllString(filtered, "\n")

	return strings.TrimSpace(filtered)
}
