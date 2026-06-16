package bstool

import (
	"context"
	"fmt"
	"regexp"
	"runtime"
	"strings"
	"time"
)

// ─── Client ──────────────────────────────────────────────────────────────────

// Client manages BsTool.exe subprocess execution.
// Safe for concurrent use — all fields are set at construction and never mutated.
type Client struct {
	bstoolPath        string
	communicationLine string
	defaultTimeout    time.Duration
	exec              executor
}

// Option is a functional option for configuring a Client.
type Option func(*Client)

// WithPath sets the path to BsTool.exe.
// Default: "" (auto-detect from common locations on Windows).
func WithPath(p string) Option {
	return func(c *Client) {
		c.bstoolPath = p
	}
}

// WithCommunicationLine sets the COMMUNICATION_LINE env var.
// Default: "AB01".
func WithCommunicationLine(line string) Option {
	return func(c *Client) {
		c.communicationLine = line
	}
}

// WithTimeout sets the default timeout for ErrLog calls.
// Default: 10s.
func WithTimeout(d time.Duration) Option {
	return func(c *Client) {
		c.defaultTimeout = d
	}
}

// NewClient creates a new Client with the given options.
// Defaults: timeout=10s, communicationLine="AB01", path="" (auto-detect).
func NewClient(opts ...Option) *Client {
	c := &Client{
		communicationLine: "AB01",
		defaultTimeout:    10 * time.Second,
	}
	for _, opt := range opts {
		opt(c)
	}
	c.exec = newExecutor()
	return c
}

// ─── ErrLogResult ───────────────────────────────────────────────────────────

// ErrLogResult contains the structured output of an ErrLog call.
type ErrLogResult struct {
	ServerName string        // Original server name (with suffix stripped for BsTool)
	Messages   []string      // Filtered RS log messages (status messages removed)
	RawOutput  string        // Complete unfiltered stdout (for debugging)
	Duration   time.Duration // Wall-clock execution duration
	ExitCode   int           // Process exit code (-1 if killed by timeout)
}

// ─── ErrLog ──────────────────────────────────────────────────────────────────

// nodeSuffixRE matches trailing 'm' or 'r' suffix on node names.
var nodeSuffixRE = regexp.MustCompile(`[mr]$`)

// stripNodeSuffix removes trailing 'm' or 'r' from a server name.
// "AP01m" → "AP01", "BP01r" → "BP01", "AP01" → "AP01".
func stripNodeSuffix(name string) string {
	return nodeSuffixRE.ReplaceAllString(name, "")
}

// ErrLog executes `BsTool.exe -errlog <serverName>` and returns structured results.
//
// The serverName is automatically stripped of m/r suffix:
//
//	"AP01m" → "AP01", "BP01r" → "BP01"
//
// On Windows: executes BsTool.exe as a subprocess with context-based timeout.
// On Linux: returns ErrUnsupportedPlatform with remediation hint.
func (c *Client) ErrLog(ctx context.Context, serverName string) (*ErrLogResult, error) {
	if serverName == "" {
		return nil, &ErrInvalidServer{}
	}

	// Strip m/r suffix
	stripped := stripNodeSuffix(serverName)
	if stripped == "" {
		return nil, &ErrInvalidServer{}
	}

	// Platform check
	if runtime.GOOS != "windows" {
		return nil, &ErrUnsupportedPlatform{}
	}

	// Determine BsTool.exe path
	exePath := c.bstoolPath
	if exePath == "" {
		exePath = "BsTool.exe" // rely on PATH
	}

	// Build args
	args := []string{"-errlog", stripped}

	// Build env
	env := []string{fmt.Sprintf("COMMUNICATION_LINE=%s", c.communicationLine)}

	// Apply timeout from context or default
	execCtx := ctx
	if _, hasDeadline := ctx.Deadline(); !hasDeadline {
		var cancel context.CancelFunc
		execCtx, cancel = context.WithTimeout(ctx, c.defaultTimeout)
		defer cancel()
	}

	start := time.Now()
	stdout, exitCode, err := c.exec.execute(execCtx, exePath, args, env)
	duration := time.Since(start)

	if err != nil {
		// Check for timeout
		if execCtx.Err() == context.DeadlineExceeded {
			return nil, &ErrTimeout{Timeout: c.defaultTimeout.String()}
		}
		// Check for not found
		if strings.Contains(err.Error(), "not found") || strings.Contains(err.Error(), "executable file not found") {
			return nil, &ErrNotFound{Path: exePath}
		}
		return nil, &ErrExecution{ExitCode: exitCode, Stderr: err.Error()}
	}

	// Decode output (CP1252 → UTF-8)
	rawOutput, decErr := decodeWindows1252(stdout)
	if decErr != nil {
		// Fall back to UTF-8 with replacement chars
		rawOutput = string(stdout)
	}

	// Filter status messages
	filtered := filterStatusMessages(rawOutput)
	messages := splitMessages(filtered)

	return &ErrLogResult{
		ServerName: stripped,
		Messages:   messages,
		RawOutput:  rawOutput,
		Duration:   duration,
		ExitCode:   exitCode,
	}, nil
}
