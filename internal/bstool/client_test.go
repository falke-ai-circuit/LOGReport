package bstool

import (
	"context"
	"runtime"
	"strings"
	"testing"
	"time"
)

// ─── NewClient Tests ────────────────────────────────────────────────────────

func TestNewClient_Defaults(t *testing.T) {
	c := NewClient()
	if c.communicationLine != "AB01" {
		t.Errorf("expected communicationLine=AB01, got %q", c.communicationLine)
	}
	if c.defaultTimeout != 10*time.Second {
		t.Errorf("expected defaultTimeout=10s, got %v", c.defaultTimeout)
	}
	if c.bstoolPath != "" {
		t.Errorf("expected bstoolPath=\"\", got %q", c.bstoolPath)
	}
}

func TestNewClient_WithOptions(t *testing.T) {
	c := NewClient(
		WithPath("/custom/path/BsTool.exe"),
		WithCommunicationLine("CD02"),
		WithTimeout(30*time.Second),
	)
	if c.bstoolPath != "/custom/path/BsTool.exe" {
		t.Errorf("expected bstoolPath=/custom/path/BsTool.exe, got %q", c.bstoolPath)
	}
	if c.communicationLine != "CD02" {
		t.Errorf("expected communicationLine=CD02, got %q", c.communicationLine)
	}
	if c.defaultTimeout != 30*time.Second {
		t.Errorf("expected defaultTimeout=30s, got %v", c.defaultTimeout)
	}
}

// ─── Node Name Stripping Tests ──────────────────────────────────────────────

func TestStripNodeSuffix(t *testing.T) {
	tests := []struct {
		input    string
		expected string
	}{
		{"AP01m", "AP01"},
		{"BP01r", "BP01"},
		{"AP01", "AP01"},
		{"CP03m", "CP03"},
		{"DP05r", "DP05"},
		{"EP99", "EP99"},
		{"m", ""}, // edge: only suffix
		{"r", ""}, // edge: only suffix
		{"", ""},   // edge: empty
	}
	for _, tt := range tests {
		result := stripNodeSuffix(tt.input)
		if result != tt.expected {
			t.Errorf("stripNodeSuffix(%q) = %q, want %q", tt.input, result, tt.expected)
		}
	}
}

// ─── ErrLog Validation Tests ────────────────────────────────────────────────

func TestErrLog_EmptyServerName(t *testing.T) {
	c := NewClient()
	_, err := c.ErrLog(context.Background(), "")
	if err == nil {
		t.Fatal("expected error for empty server name")
	}
	if _, ok := err.(*ErrInvalidServer); !ok {
		t.Errorf("expected ErrInvalidServer, got %T: %v", err, err)
	}
}

func TestErrLog_OnlySuffix(t *testing.T) {
	c := NewClient()
	_, err := c.ErrLog(context.Background(), "m")
	if err == nil {
		t.Fatal("expected error for suffix-only server name")
	}
	if _, ok := err.(*ErrInvalidServer); !ok {
		t.Errorf("expected ErrInvalidServer, got %T: %v", err, err)
	}
}

func TestErrLog_LinuxUnsupportedPlatform(t *testing.T) {
	if runtime.GOOS == "windows" {
		t.Skip("test only valid on non-Windows platforms")
	}
	c := NewClient()
	_, err := c.ErrLog(context.Background(), "AP01m")
	if err == nil {
		t.Fatal("expected error on non-Windows platform")
	}
	if _, ok := err.(*ErrUnsupportedPlatform); !ok {
		t.Errorf("expected ErrUnsupportedPlatform, got %T: %v", err, err)
	}
}

// ─── Filter Tests ───────────────────────────────────────────────────────────

func TestFilterStatusMessages_WritingTo(t *testing.T) {
	if isBstoolStatusMessage("Writing to RS log for AP01...") != true {
		t.Error("expected 'Writing to' line to be filtered")
	}
}

func TestFilterStatusMessages_ContentWritten(t *testing.T) {
	if isBstoolStatusMessage("Content written to output file") != true {
		t.Error("expected 'Content written to' line to be filtered")
	}
}

func TestFilterStatusMessages_NowFutureLog(t *testing.T) {
	if isBstoolStatusMessage("Now the future log is ready") != true {
		t.Error("expected 'Now the future log' line to be filtered")
	}
}

func TestFilterStatusMessages_Checkmark(t *testing.T) {
	if isBstoolStatusMessage("\u2714 Done") != true {
		t.Error("expected ✔ line to be filtered")
	}
}

func TestFilterStatusMessages_CheckmarkUnicode(t *testing.T) {
	if isBstoolStatusMessage("\u2713 Complete") != true {
		t.Error("expected ✓ line to be filtered")
	}
}

func TestFilterStatusMessages_RealLogMessage(t *testing.T) {
	msg := "2024-03-15 08:12:34.567 [ERR] Module M01: Channel 3 overrange"
	if isBstoolStatusMessage(msg) != false {
		t.Error("expected real log message to NOT be filtered")
	}
}

func TestFilterStatusMessages_Empty(t *testing.T) {
	if isBstoolStatusMessage("") != false {
		t.Error("expected empty line to NOT be filtered (handled upstream)")
	}
}

func TestFilterStatusMessages_PartialMatch(t *testing.T) {
	// "Content written" alone should NOT match "Content written to"
	if isBstoolStatusMessage("Content written") != false {
		t.Error("expected partial match 'Content written' to NOT be filtered")
	}
}

func TestFilterStatusMessages_FullOutput(t *testing.T) {
	raw := strings.Join([]string{
		"Writing to RS log for AP01...",
		"2024-03-15 08:12:34.567 [ERR] Module M01: Channel 3 overrange",
		"2024-03-15 08:12:35.001 [WRN] Module M02: Communication timeout",
		"Content written to output",
		"\u2714 Done",
		"",
	}, "\n")

	filtered := filterStatusMessages(raw)
	messages := splitMessages(filtered)

	if len(messages) != 2 {
		t.Errorf("expected 2 messages, got %d: %v", len(messages), messages)
	}
	if messages[0] != "2024-03-15 08:12:34.567 [ERR] Module M01: Channel 3 overrange" {
		t.Errorf("unexpected message[0]: %q", messages[0])
	}
	if messages[1] != "2024-03-15 08:12:35.001 [WRN] Module M02: Communication timeout" {
		t.Errorf("unexpected message[1]: %q", messages[1])
	}
}

func TestSplitMessages_Empty(t *testing.T) {
	msgs := splitMessages("")
	if msgs != nil {
		t.Errorf("expected nil for empty input, got %v", msgs)
	}
}

func TestSplitMessages_WhitespaceOnly(t *testing.T) {
	msgs := splitMessages("  \n  \n  ")
	if len(msgs) != 0 {
		t.Errorf("expected 0 messages for whitespace-only, got %d", len(msgs))
	}
}

// ─── Encoding Tests ─────────────────────────────────────────────────────────

func TestDecodeWindows1252_Degree(t *testing.T) {
	// 0xB0 = ° in CP1252
	result, err := decodeWindows1252([]byte{0xB0})
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if result != "°" {
		t.Errorf("expected '°', got %q", result)
	}
}

func TestDecodeWindows1252_PlusMinus(t *testing.T) {
	// 0xB1 = ± in CP1252
	result, err := decodeWindows1252([]byte{0xB1})
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if result != "±" {
		t.Errorf("expected '±', got %q", result)
	}
}

func TestDecodeWindows1252_Micro(t *testing.T) {
	// 0xB5 = µ in CP1252
	result, err := decodeWindows1252([]byte{0xB5})
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if result != "µ" {
		t.Errorf("expected 'µ', got %q", result)
	}
}

func TestDecodeWindows1252_Oslash(t *testing.T) {
	// 0xD8 = Ø in CP1252
	result, err := decodeWindows1252([]byte{0xD8})
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if result != "Ø" {
		t.Errorf("expected 'Ø', got %q", result)
	}
}

func TestDecodeWindows1252_Euro(t *testing.T) {
	// 0x80 = € in CP1252
	result, err := decodeWindows1252([]byte{0x80})
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if result != "€" {
		t.Errorf("expected '€', got %q", result)
	}
}

func TestDecodeWindows1252_ASCII(t *testing.T) {
	result, err := decodeWindows1252([]byte("Hello"))
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if result != "Hello" {
		t.Errorf("expected 'Hello', got %q", result)
	}
}

func TestDecodeWindows1252_Mixed(t *testing.T) {
	// "Temp: 25°C ± 0.5" in CP1252
	input := []byte{'T', 'e', 'm', 'p', ':', ' ', '2', '5', 0xB0, 'C', ' ', 0xB1, ' ', '0', '.', '5'}
	result, err := decodeWindows1252(input)
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if result != "Temp: 25°C ± 0.5" {
		t.Errorf("expected 'Temp: 25°C ± 0.5', got %q", result)
	}
}

func TestDecodeWindows1252_Empty(t *testing.T) {
	result, err := decodeWindows1252([]byte{})
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if result != "" {
		t.Errorf("expected empty string, got %q", result)
	}
}

// ─── Error Type Tests ───────────────────────────────────────────────────────

func TestErrorCodes(t *testing.T) {
	tests := []struct {
		err      error
		expected string
	}{
		{&ErrNotFound{Path: "/fake/path"}, "BSTOOL_NOT_FOUND"},
		{&ErrUnsupportedPlatform{}, "UNSUPPORTED_PLATFORM"},
		{&ErrTimeout{Timeout: "10s"}, "BSTOOL_TIMEOUT"},
		{&ErrExecution{ExitCode: 1, Stderr: "oops"}, "BSTOOL_EXECUTION_FAILED"},
		{&ErrInvalidServer{}, "INVALID_REQUEST"},
	}

	for _, tt := range tests {
		type coder interface {
			Code() string
		}
		if ce, ok := tt.err.(coder); ok {
			if ce.Code() != tt.expected {
				t.Errorf("error %T: expected Code()=%q, got %q", tt.err, tt.expected, ce.Code())
			}
		} else {
			t.Errorf("error %T does not implement Code()", tt.err)
		}
	}
}

func TestErrorMessages(t *testing.T) {
	// Verify error messages are non-empty and human-readable
	tests := []error{
		&ErrNotFound{Path: "/fake/path"},
		&ErrUnsupportedPlatform{},
		&ErrTimeout{Timeout: "10s"},
		&ErrExecution{ExitCode: 1, Stderr: "oops"},
		&ErrExecution{ExitCode: 2},
		&ErrInvalidServer{},
	}

	for _, err := range tests {
		msg := err.Error()
		if msg == "" {
			t.Errorf("error %T has empty Error() string", err)
		}
		if !strings.Contains(msg, "bstool:") && !strings.Contains(msg, "bstool") {
			t.Errorf("error %T message should contain 'bstool': %q", err, msg)
		}
	}
}

// ─── Context Timeout Test ───────────────────────────────────────────────────

func TestErrLog_ContextTimeout(t *testing.T) {
	if runtime.GOOS != "windows" {
		t.Skip("timeout test requires Windows to actually execute")
	}
	c := NewClient(WithTimeout(1 * time.Millisecond))
	ctx, cancel := context.WithTimeout(context.Background(), 1*time.Millisecond)
	defer cancel()

	// This will fail because BsTool.exe doesn't exist, but the timeout
	// should fire before the "not found" error on a real system.
	// On this test VM, we just verify the method doesn't panic.
	_, err := c.ErrLog(ctx, "AP01")
	if err == nil {
		t.Log("unexpected success (BsTool.exe may exist on this system)")
	}
}
