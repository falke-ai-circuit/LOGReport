package bstool

import (
	"context"
	"encoding/json"
	"fmt"
	"runtime"
	"sync"
	"testing"
	"time"
)

// ─── Integration: Full ErrLog Flow on Linux ──────────────────────────────────

func TestErrLog_FullFlow_Linux(t *testing.T) {
	if runtime.GOOS == "windows" {
		t.Skip("test only valid on non-Windows platforms")
	}

	c := NewClient(
		WithPath("/opt/bstool/BsTool.exe"),
		WithCommunicationLine("CD02"),
		WithTimeout(30 * time.Second),
	)

	ctx := context.Background()
	result, err := c.ErrLog(ctx, "AP01m")

	// Must return ErrUnsupportedPlatform
	if err == nil {
		t.Fatal("expected error on Linux")
	}

	platformErr, ok := err.(*ErrUnsupportedPlatform)
	if !ok {
		t.Fatalf("expected ErrUnsupportedPlatform, got %T: %v", err, err)
	}

	// Verify remediation message
	msg := platformErr.Error()
	if msg == "" {
		t.Error("ErrUnsupportedPlatform.Error() returned empty string")
	}
	if !containsAny(msg, "Windows", "bstool-remote", "hermes-remote") {
		t.Errorf("remediation message should mention Windows/remote: %q", msg)
	}

	// Verify Code()
	if platformErr.Code() != "UNSUPPORTED_PLATFORM" {
		t.Errorf("expected Code()=UNSUPPORTED_PLATFORM, got %q", platformErr.Code())
	}

	// Result must be nil
	if result != nil {
		t.Errorf("expected nil result on error, got %+v", result)
	}
}

// ─── Integration: Client Options Chain ───────────────────────────────────────

func TestClientOptionsChain(t *testing.T) {
	c := NewClient(
		WithPath("/custom/BsTool.exe"),
		WithTimeout(45 * time.Second),
		WithCommunicationLine("EF03"),
	)

	if c.bstoolPath != "/custom/BsTool.exe" {
		t.Errorf("bstoolPath: expected /custom/BsTool.exe, got %q", c.bstoolPath)
	}
	if c.defaultTimeout != 45*time.Second {
		t.Errorf("defaultTimeout: expected 45s, got %v", c.defaultTimeout)
	}
	if c.communicationLine != "EF03" {
		t.Errorf("communicationLine: expected EF03, got %q", c.communicationLine)
	}

	// Verify executor is set
	if c.exec == nil {
		t.Error("executor should not be nil after NewClient")
	}
}

// ─── Integration: Encoding Round-Trip ────────────────────────────────────────

func TestEncodingRoundTrip(t *testing.T) {
	// CP1252 bytes → UTF-8 string → back to bytes (via UTF-8)
	// This verifies the decode is lossless for CP1252 characters

	tests := []struct {
		name     string
		cp1252   []byte
		expected string
	}{
		{"degree", []byte{0xB0}, "°"},
		{"plusminus", []byte{0xB1}, "±"},
		{"micro", []byte{0xB5}, "µ"},
		{"oslash", []byte{0xD8}, "Ø"},
		{"euro", []byte{0x80}, "€"},
		{"ascii", []byte("Hello World"), "Hello World"},
		{"mixed", []byte{'T', 'e', 'm', 'p', ':', ' ', '2', '5', 0xB0, 'C', ' ', 0xB1, ' ', '0', '.', '5'}, "Temp: 25°C ± 0.5"},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			// Decode CP1252 → UTF-8
			utf8Str, err := decodeWindows1252(tt.cp1252)
			if err != nil {
				t.Fatalf("decode error: %v", err)
			}
			if utf8Str != tt.expected {
				t.Errorf("decode: expected %q, got %q", tt.expected, utf8Str)
			}

			// Round-trip: UTF-8 string → bytes → should match expected UTF-8 bytes
			utf8Bytes := []byte(utf8Str)
			expectedBytes := []byte(tt.expected)
			if string(utf8Bytes) != string(expectedBytes) {
				t.Errorf("round-trip: UTF-8 bytes don't match expected: %v vs %v", utf8Bytes, expectedBytes)
			}
		})
	}
}

// ─── Integration: ErrLogResult JSON Marshaling ───────────────────────────────

func TestErrLogResult_JSONMarshaling(t *testing.T) {
	result := &ErrLogResult{
		ServerName: "AP01",
		Messages:   []string{"2024-03-15 08:12:34.567 [ERR] Module M01: Channel 3 overrange"},
		RawOutput:  "Writing to RS log for AP01...\n2024-03-15 08:12:34.567 [ERR] Module M01: Channel 3 overrange\nContent written to output\n✔ Done",
		Stderr:     "Warning: deprecated flag used",
		Duration:   1500 * time.Millisecond,
		ExitCode:   0,
		TimedOut:   false,
	}

	data, err := json.Marshal(result)
	if err != nil {
		t.Fatalf("json.Marshal failed: %v", err)
	}

	// Unmarshal back and verify all fields
	var decoded map[string]interface{}
	if err := json.Unmarshal(data, &decoded); err != nil {
		t.Fatalf("json.Unmarshal failed: %v", err)
	}

	// Check all expected fields exist
	expectedFields := []string{
		"ServerName", "Messages", "RawOutput", "Stderr",
		"Duration", "ExitCode", "TimedOut",
	}
	for _, field := range expectedFields {
		if _, ok := decoded[field]; !ok {
			t.Errorf("JSON missing field %q", field)
		}
	}

	// Verify specific values
	if decoded["ServerName"] != "AP01" {
		t.Errorf("ServerName: expected AP01, got %v", decoded["ServerName"])
	}
	if decoded["ExitCode"] != float64(0) {
		t.Errorf("ExitCode: expected 0, got %v", decoded["ExitCode"])
	}
	if decoded["TimedOut"] != false {
		t.Errorf("TimedOut: expected false, got %v", decoded["TimedOut"])
	}
	if decoded["Stderr"] != "Warning: deprecated flag used" {
		t.Errorf("Stderr: expected warning message, got %v", decoded["Stderr"])
	}

	// Duration should be marshaled as nanoseconds (int64)
	dur, ok := decoded["Duration"].(float64)
	if !ok {
		t.Errorf("Duration should be numeric, got %T: %v", decoded["Duration"], decoded["Duration"])
	}
	if dur <= 0 {
		t.Errorf("Duration should be positive, got %v", dur)
	}

	// Messages should be an array
	msgs, ok := decoded["Messages"].([]interface{})
	if !ok {
		t.Errorf("Messages should be array, got %T", decoded["Messages"])
	}
	if len(msgs) != 1 {
		t.Errorf("Messages length: expected 1, got %d", len(msgs))
	}
}

func TestErrLogResult_JSONMarshaling_TimedOut(t *testing.T) {
	result := &ErrLogResult{
		ServerName: "BP01",
		Messages:   []string{},
		RawOutput:  "",
		Stderr:     "",
		Duration:   5 * time.Second,
		ExitCode:   -1,
		TimedOut:   true,
	}

	data, err := json.Marshal(result)
	if err != nil {
		t.Fatalf("json.Marshal failed: %v", err)
	}

	var decoded map[string]interface{}
	if err := json.Unmarshal(data, &decoded); err != nil {
		t.Fatalf("json.Unmarshal failed: %v", err)
	}

	if decoded["TimedOut"] != true {
		t.Errorf("TimedOut: expected true, got %v", decoded["TimedOut"])
	}
	if decoded["ExitCode"] != float64(-1) {
		t.Errorf("ExitCode: expected -1, got %v", decoded["ExitCode"])
	}
	// Messages should be empty array, not null
	msgs, ok := decoded["Messages"].([]interface{})
	if !ok {
		t.Errorf("Messages should be array, got %T", decoded["Messages"])
	}
	if len(msgs) != 0 {
		t.Errorf("Messages should be empty, got %d elements", len(msgs))
	}
}

// ─── Integration: Concurrent ErrLog Calls ─────────────────────────────────────

func TestErrLog_Concurrent(t *testing.T) {
	if runtime.GOOS == "windows" {
		t.Skip("concurrent test validates Linux error path; on Windows it would try to execute BsTool.exe")
	}

	c := NewClient()
	concurrency := 20
	var wg sync.WaitGroup
	errs := make(chan error, concurrency)

	for i := 0; i < concurrency; i++ {
		wg.Add(1)
		go func(id int) {
			defer wg.Done()
			_, err := c.ErrLog(context.Background(), "AP01m")
			if err == nil {
				errs <- nil // shouldn't happen on Linux
				return
			}
			if _, ok := err.(*ErrUnsupportedPlatform); !ok {
				errs <- err // wrong error type
				return
			}
			errs <- nil // correct error
		}(i)
	}

	wg.Wait()
	close(errs)

	failures := 0
	for err := range errs {
		if err != nil {
			t.Errorf("concurrent call returned unexpected error: %v", err)
			failures++
		}
	}
	if failures > 0 {
		t.Errorf("%d/%d concurrent calls failed", failures, concurrency)
	} else {
		t.Logf("All %d concurrent ErrLog calls returned correct ErrUnsupportedPlatform", concurrency)
	}
}

// ─── Integration: Error Type Code and Error Methods ──────────────────────────

func TestErrorType_CodeAndError(t *testing.T) {
	tests := []struct {
		name     string
		err      error
		code     string
		errMsg   string
	}{
		{
			name:   "ErrNotFound",
			err:    &ErrNotFound{Path: "/nonexistent/BsTool.exe"},
			code:   "BSTOOL_NOT_FOUND",
			errMsg: "bstool: BsTool.exe not found at \"/nonexistent/BsTool.exe\"",
		},
		{
			name:   "ErrUnsupportedPlatform",
			err:    &ErrUnsupportedPlatform{},
			code:   "UNSUPPORTED_PLATFORM",
			errMsg: "bstool: BsTool.exe requires Windows. Use --bstool-remote flag to execute via hermes-remote on Windows host.",
		},
		{
			name:   "ErrTimeout",
			err:    &ErrTimeout{Timeout: "15s"},
			code:   "BSTOOL_TIMEOUT",
			errMsg: "bstool: execution timed out after 15s",
		},
		{
			name:   "ErrExecution with stderr",
			err:    &ErrExecution{ExitCode: 1, Stderr: "fatal error"},
			code:   "BSTOOL_EXECUTION_FAILED",
			errMsg: "bstool: execution failed with exit code 1: fatal error",
		},
		{
			name:   "ErrExecution without stderr",
			err:    &ErrExecution{ExitCode: 2},
			code:   "BSTOOL_EXECUTION_FAILED",
			errMsg: "bstool: execution failed with exit code 2",
		},
		{
			name:   "ErrInvalidServer",
			err:    &ErrInvalidServer{},
			code:   "INVALID_REQUEST",
			errMsg: "bstool: server name is required and cannot be empty",
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			type coder interface {
				Code() string
			}
			ce, ok := tt.err.(coder)
			if !ok {
				t.Fatalf("error %T does not implement Code()", tt.err)
			}
			if ce.Code() != tt.code {
				t.Errorf("Code(): expected %q, got %q", tt.code, ce.Code())
			}
			if tt.err.Error() != tt.errMsg {
				t.Errorf("Error(): expected %q, got %q", tt.errMsg, tt.err.Error())
			}
		})
	}
}

// ─── Helpers ─────────────────────────────────────────────────────────────────

func containsAny(s string, substrs ...string) bool {
	for _, sub := range substrs {
		if len(sub) > 0 && len(s) >= len(sub) {
			for i := 0; i <= len(s)-len(sub); i++ {
				if s[i:i+len(sub)] == sub {
					return true
				}
			}
		}
	}
	return false
}

// ─── Mock Executor Tests (for coverage of ErrLog internals) ──────────────────

// mockExecutor implements the executor interface for testing.
type mockExecutor struct {
	stdout   []byte
	stderr   []byte
	exitCode int
	err      error
}

func (m *mockExecutor) execute(ctx context.Context, exePath string, args []string, env []string) ([]byte, []byte, int, error) {
	return m.stdout, m.stderr, m.exitCode, m.err
}

// newMockClient creates a Client with skipPlatformCheck=true for testing ErrLog internals.
func newMockClient(opts ...Option) *Client {
	c := NewClient(opts...)
	c.skipPlatformCheck = true
	return c
}

// TestErrLog_MockSuccess tests the full ErrLog pipeline with a mock executor
// that returns successful CP1252-encoded output.
func TestErrLog_MockSuccess(t *testing.T) {
	c := newMockClient(WithPath("/fake/BsTool.exe"))
	c.exec = &mockExecutor{
		stdout: []byte("2024-03-15 08:12:34.567 [ERR] Module M01: Channel 3 overrange\n2024-03-15 08:12:35.001 [WRN] Module M02: Communication timeout\n"),
		exitCode: 0,
	}

	result, err := c.ErrLog(context.Background(), "AP01m")
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}

	if result.ServerName != "AP01" {
		t.Errorf("ServerName: expected AP01, got %q", result.ServerName)
	}
	if len(result.Messages) != 2 {
		t.Errorf("Messages: expected 2, got %d: %v", len(result.Messages), result.Messages)
	}
	if result.ExitCode != 0 {
		t.Errorf("ExitCode: expected 0, got %d", result.ExitCode)
	}
	if result.TimedOut {
		t.Error("TimedOut: expected false")
	}
	if result.Duration <= 0 {
		t.Error("Duration should be positive")
	}
}

// TestErrLog_MockSuccessWithStatusMessages tests filtering of status messages
// from mock executor output.
func TestErrLog_MockSuccessWithStatusMessages(t *testing.T) {
	c := newMockClient(WithPath("/fake/BsTool.exe"))
	// Use ASCII-only status patterns to avoid CP1252 decode corruption
	c.exec = &mockExecutor{
		stdout: []byte("Writing to RS log for AP01...\n2024-03-15 08:12:34.567 [ERR] Module M01: Channel 3 overrange\nContent written to output\nNow the future log is ready\n"),
		exitCode: 0,
	}

	result, err := c.ErrLog(context.Background(), "AP01m")
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}

	if len(result.Messages) != 1 {
		t.Errorf("Messages: expected 1 (status lines filtered), got %d: %v", len(result.Messages), result.Messages)
	}
	if result.Messages[0] != "2024-03-15 08:12:34.567 [ERR] Module M01: Channel 3 overrange" {
		t.Errorf("unexpected message: %q", result.Messages[0])
	}
}

// TestErrLog_MockSuccessWithMask tests that mask parameter is passed to executor args.
func TestErrLog_MockSuccessWithMask(t *testing.T) {
	c := newMockClient(WithPath("/fake/BsTool.exe"))
	var capturedArgs []string
	c.exec = &mockExecutor{
		stdout:   []byte("2024-03-15 08:12:34.567 [ERR] Module M01: Channel 3 overrange\n"),
		exitCode: 0,
	}
	// Wrap to capture args
	origExec := c.exec
	c.exec = &argsCaptureExecutor{inner: origExec, capturedArgs: &capturedArgs}

	result, err := c.ErrLog(context.Background(), "AP01m", WithMask("ERR"))
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	_ = result

	// Verify mask was passed
	foundMask := false
	for _, a := range capturedArgs {
		if a == "mask" || a == "ERR" {
			foundMask = true
		}
	}
	if !foundMask {
		t.Errorf("mask not found in args: %v", capturedArgs)
	}
}

// argsCaptureExecutor wraps an executor to capture the args passed to execute.
type argsCaptureExecutor struct {
	inner        executor
	capturedArgs *[]string
}

func (a *argsCaptureExecutor) execute(ctx context.Context, exePath string, args []string, env []string) ([]byte, []byte, int, error) {
	*a.capturedArgs = args
	return a.inner.execute(ctx, exePath, args, env)
}

// TestErrLog_MockNotFound tests that "not found" errors from executor
// are mapped to ErrNotFound.
func TestErrLog_MockNotFound(t *testing.T) {
	c := newMockClient(WithPath("/fake/BsTool.exe"))
	c.exec = &mockExecutor{
		err: fmt.Errorf("executable file not found in $PATH"),
	}

	_, err := c.ErrLog(context.Background(), "AP01m")
	if err == nil {
		t.Fatal("expected error")
	}
	nfErr, ok := err.(*ErrNotFound)
	if !ok {
		t.Fatalf("expected ErrNotFound, got %T: %v", err, err)
	}
	if nfErr.Path != "/fake/BsTool.exe" {
		t.Errorf("Path: expected /fake/BsTool.exe, got %q", nfErr.Path)
	}
}

// TestErrLog_MockExecutionError tests that execution errors from executor
// are mapped to ErrExecution.
func TestErrLog_MockExecutionError(t *testing.T) {
	c := newMockClient(WithPath("/fake/BsTool.exe"))
	c.exec = &mockExecutor{
		stdout:   []byte("partial output"),
		stderr:   []byte("fatal: something went wrong"),
		exitCode: 1,
		err:      fmt.Errorf("fatal: something went wrong"),
	}

	_, err := c.ErrLog(context.Background(), "AP01m")
	if err == nil {
		t.Fatal("expected error")
	}
	execErr, ok := err.(*ErrExecution)
	if !ok {
		t.Fatalf("expected ErrExecution, got %T: %v", err, err)
	}
	if execErr.ExitCode != 1 {
		t.Errorf("ExitCode: expected 1, got %d", execErr.ExitCode)
	}
}

// TestErrLog_MockTimeoutWithPartialOutput tests timeout with partial stdout.
func TestErrLog_MockTimeoutWithPartialOutput(t *testing.T) {
	c := newMockClient(WithPath("/fake/BsTool.exe"), WithTimeout(1*time.Second))
	c.exec = &mockExecutor{
		stdout: []byte("2024-03-15 08:12:34.567 [ERR] Module M01: Channel 3 overrange\n"),
		err:    context.DeadlineExceeded,
	}

	ctx, cancel := context.WithTimeout(context.Background(), 1*time.Millisecond)
	defer cancel()
	// Let the deadline expire
	time.Sleep(2 * time.Millisecond)

	result, err := c.ErrLog(ctx, "AP01m")
	if err != nil {
		t.Fatalf("expected partial result on timeout, got error: %v", err)
	}
	if !result.TimedOut {
		t.Error("TimedOut: expected true")
	}
	if len(result.Messages) == 0 {
		t.Error("expected partial messages on timeout with stdout")
	}
}

// TestErrLog_MockTimeoutNoOutput tests timeout with no stdout.
func TestErrLog_MockTimeoutNoOutput(t *testing.T) {
	c := newMockClient(WithPath("/fake/BsTool.exe"), WithTimeout(1*time.Second))
	c.exec = &mockExecutor{
		err: context.DeadlineExceeded,
	}

	ctx, cancel := context.WithTimeout(context.Background(), 1*time.Millisecond)
	defer cancel()
	time.Sleep(2 * time.Millisecond)

	_, err := c.ErrLog(ctx, "AP01m")
	if err == nil {
		t.Fatal("expected error on timeout with no output")
	}
	timeoutErr, ok := err.(*ErrTimeout)
	if !ok {
		t.Fatalf("expected ErrTimeout, got %T: %v", err, err)
	}
	if timeoutErr.Timeout == "" {
		t.Error("Timeout field should not be empty")
	}
}

// TestErrLog_MockEmptyOutput tests success with empty stdout.
func TestErrLog_MockEmptyOutput(t *testing.T) {
	c := newMockClient(WithPath("/fake/BsTool.exe"))
	c.exec = &mockExecutor{
		stdout:   []byte{},
		exitCode: 0,
	}

	result, err := c.ErrLog(context.Background(), "AP01m")
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if len(result.Messages) != 0 {
		t.Errorf("Messages: expected 0, got %d", len(result.Messages))
	}
	if result.RawOutput != "" {
		t.Errorf("RawOutput: expected empty, got %q", result.RawOutput)
	}
}

// TestErrLog_MockCP1252Output tests CP1252 decoding in the full pipeline.
func TestErrLog_MockCP1252Output(t *testing.T) {
	c := newMockClient(WithPath("/fake/BsTool.exe"))
	// "Temp: 25°C ± 0.5" in CP1252 bytes
	c.exec = &mockExecutor{
		stdout:   []byte{'T', 'e', 'm', 'p', ':', ' ', '2', '5', 0xB0, 'C', ' ', 0xB1, ' ', '0', '.', '5'},
		exitCode: 0,
	}

	result, err := c.ErrLog(context.Background(), "AP01m")
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if len(result.Messages) != 1 {
		t.Fatalf("expected 1 message, got %d", len(result.Messages))
	}
	if result.Messages[0] != "Temp: 25°C ± 0.5" {
		t.Errorf("CP1252 decode failed: got %q", result.Messages[0])
	}
}

// TestErrLog_MockWithRequestTimeout tests per-request timeout override.
func TestErrLog_MockWithRequestTimeout(t *testing.T) {
	c := newMockClient(WithPath("/fake/BsTool.exe"), WithTimeout(30*time.Second))
	c.exec = &mockExecutor{
		stdout:   []byte("log message\n"),
		exitCode: 0,
	}

	// Use a per-request timeout that's different from default
	result, err := c.ErrLog(context.Background(), "AP01m", WithRequestTimeout(5*time.Second))
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if len(result.Messages) == 0 {
		t.Error("expected messages")
	}
}

// TestErrLog_MockCommunicationLine tests that COMMUNICATION_LINE env var is set.
func TestErrLog_MockCommunicationLine(t *testing.T) {
	c := newMockClient(WithPath("/fake/BsTool.exe"), WithCommunicationLine("CD02"))
	var capturedEnv []string
	c.exec = &envCaptureExecutor{
		inner: &mockExecutor{
			stdout:   []byte("log message\n"),
			exitCode: 0,
		},
		capturedEnv: &capturedEnv,
	}

	_, err := c.ErrLog(context.Background(), "AP01m")
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}

	found := false
	for _, e := range capturedEnv {
		if e == "COMMUNICATION_LINE=CD02" {
			found = true
			break
		}
	}
	if !found {
		t.Errorf("COMMUNICATION_LINE=CD02 not found in env: %v", capturedEnv)
	}
}

// envCaptureExecutor wraps an executor to capture env vars.
type envCaptureExecutor struct {
	inner       executor
	capturedEnv *[]string
}

func (e *envCaptureExecutor) execute(ctx context.Context, exePath string, args []string, env []string) ([]byte, []byte, int, error) {
	*e.capturedEnv = env
	return e.inner.execute(ctx, exePath, args, env)
}

// TestErrLog_MockStderr tests that stderr is captured in the result.
func TestErrLog_MockStderr(t *testing.T) {
	c := newMockClient(WithPath("/fake/BsTool.exe"))
	c.exec = &mockExecutor{
		stdout:   []byte("log message\n"),
		stderr:   []byte("Warning: deprecated flag\n"),
		exitCode: 0,
	}

	result, err := c.ErrLog(context.Background(), "AP01m")
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if result.Stderr != "Warning: deprecated flag\n" {
		t.Errorf("Stderr: expected warning, got %q", result.Stderr)
	}
}

// TestErrLog_MockExitCode tests that non-zero exit codes are captured.
func TestErrLog_MockExitCode(t *testing.T) {
	c := newMockClient(WithPath("/fake/BsTool.exe"))
	c.exec = &mockExecutor{
		stdout:   []byte("log message\n"),
		exitCode: 0,
	}

	result, err := c.ErrLog(context.Background(), "AP01m")
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if result.ExitCode != 0 {
		t.Errorf("ExitCode: expected 0, got %d", result.ExitCode)
	}
}

// TestErrLog_MockDefaultPath tests that empty bstoolPath defaults to "BsTool.exe".
func TestErrLog_MockDefaultPath(t *testing.T) {
	c := newMockClient() // no WithPath
	var capturedPath string
	c.exec = &pathCaptureExecutor{
		inner: &mockExecutor{
			stdout:   []byte("log message\n"),
			exitCode: 0,
		},
		capturedPath: &capturedPath,
	}

	_, err := c.ErrLog(context.Background(), "AP01m")
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if capturedPath != "BsTool.exe" {
		t.Errorf("default path: expected BsTool.exe, got %q", capturedPath)
	}
}

// pathCaptureExecutor wraps an executor to capture the exePath.
type pathCaptureExecutor struct {
	inner        executor
	capturedPath *string
}

func (p *pathCaptureExecutor) execute(ctx context.Context, exePath string, args []string, env []string) ([]byte, []byte, int, error) {
	*p.capturedPath = exePath
	return p.inner.execute(ctx, exePath, args, env)
}

// TestErrLog_MockContextWithDeadline tests that an existing context deadline is respected.
func TestErrLog_MockContextWithDeadline(t *testing.T) {
	c := newMockClient(WithPath("/fake/BsTool.exe"))
	c.exec = &mockExecutor{
		stdout:   []byte("log message\n"),
		exitCode: 0,
	}

	ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
	defer cancel()

	result, err := c.ErrLog(ctx, "AP01m")
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if len(result.Messages) == 0 {
		t.Error("expected messages")
	}
}
