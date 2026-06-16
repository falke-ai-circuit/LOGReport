package bstool

import "strings"

// ─── Status Message Filtering ───────────────────────────────────────────────

// bstoolStatusPatterns are substrings that identify BsTool status/progress lines.
// These are removed from the output to leave only actual RS log messages.
// Evidence: valmet report §3.2, bstool_worker.py lines 53-82.
var bstoolStatusPatterns = []string{
	"Writing to",
	"Content written to",
	"Now the future log",
}

// isBstoolStatusMessage returns true if the line is a BsTool progress/status message.
// Also filters lines starting with ✔ or ✓ (checkmark status indicators).
func isBstoolStatusMessage(line string) bool {
	trimmed := strings.TrimSpace(line)

	// Check for checkmark prefixes
	if strings.HasPrefix(trimmed, "\u2714") || strings.HasPrefix(trimmed, "\u2713") {
		return true
	}

	// Check for known status patterns
	for _, pattern := range bstoolStatusPatterns {
		if strings.Contains(trimmed, pattern) {
			return true
		}
	}

	return false
}

// filterStatusMessages removes BsTool status lines from raw output.
// Returns only the actual RS log message lines.
func filterStatusMessages(raw string) string {
	lines := strings.Split(raw, "\n")
	var kept []string
	for _, line := range lines {
		if !isBstoolStatusMessage(line) && strings.TrimSpace(line) != "" {
			kept = append(kept, line)
		}
	}
	return strings.Join(kept, "\n")
}

// splitMessages splits filtered output into individual log messages.
// Empty lines are removed.
func splitMessages(filtered string) []string {
	if filtered == "" {
		return []string{}
	}
	lines := strings.Split(filtered, "\n")
	var msgs []string
	for _, line := range lines {
		trimmed := strings.TrimSpace(line)
		if trimmed != "" {
			msgs = append(msgs, trimmed)
		}
	}
	return msgs
}
