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

// Client manages BsTool error log retrieval.
// It supports three transport modes:
//   - Subprocess (Windows only): executes BsTool.exe locally
//   - SSH remote (any platform): executes BsTool.exe on a Windows host via SSH
//   - Native TCP (any platform): connects directly to the DNA node, no BsTool.exe needed
//
// Safe for concurrent use — all fields are set at construction and never mutated.
type Client struct {
	bstoolPath        string
	communicationLine string
	defaultTimeout    time.Duration
	exec              executor
	tcp               *TCPTransport // native TCP transport (nil = use executor)
	skipPlatformCheck bool          // test-only: bypass runtime.GOOS check
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
// Default: 15s.
func WithTimeout(d time.Duration) Option {
	return func(c *Client) {
		c.defaultTimeout = d
	}
}

// NewClient creates a new Client with the given options.
// Defaults: timeout=15s, communicationLine="AB01", path="" (auto-detect).
func NewClient(opts ...Option) *Client {
	c := &Client{
		communicationLine: "AB01",
		defaultTimeout:    15 * time.Second,
	}
	for _, opt := range opts {
		opt(c)
	}
	c.exec = newExecutor()
	return c
}

// WithSSHExecutor configures the client to use an SSH-based remote executor,
// allowing BsTool.exe to run on a Windows host accessed via SSH.
// This is the recommended approach when LOGReport runs on Linux.
//
// Usage:
//
//	client := bstool.NewClient(
//	    bstool.WithSSHExecutor(
//	        bstool.NewSSHExecutor(
//	            bstool.WithSSHHost("windows-host:22"),
//	            bstool.WithSSHUser("administrator"),
//	            bstool.WithSSHKeyPath("/path/to/key"),
//	            bstool.WithSSHBsToolPath(`C:\BsTool\BsTool.exe`),
//	        ),
//	    ),
//	)
func WithSSHExecutor(sshExec *SSHExecutor) Option {
	return func(c *Client) {
		c.exec = sshExec
		c.skipPlatformCheck = true // SSH executor works from any platform
	}
}

// WithTCPTransport configures the client to use a native Go TCP transport,
// eliminating the need for BsTool.exe entirely when a TCP connection to the
// DNA node is available. This is the fastest path — no subprocess, no SSH,
// no Windows binary needed.
//
// Usage:
//
//	client := bstool.NewClient(
//	    bstool.WithTCPTransport(
//	        bstool.NewTCPTransport(
//	            bstool.WithTCPHost("192.168.1.100"),
//	            bstool.WithTCPPort(1516),
//	            bstool.WithTCPTimeout(5 * time.Second),
//	        ),
//	    ),
//	)
func WithTCPTransport(tcp *TCPTransport) Option {
	return func(c *Client) {
		c.tcp = tcp
		c.skipPlatformCheck = true // TCP transport works from any platform
	}
}

// ─── ErrLogResult ───────────────────────────────────────────────────────────

// ErrLogResult contains the structured output of an ErrLog call.
type ErrLogResult struct {
	ServerName string        // Original server name (with suffix stripped for BsTool)
	Messages   []string      // Filtered RS log messages (status messages removed)
	RawOutput  string        // Complete unfiltered stdout (for debugging)
	Stderr     string        // Complete stderr output from BsTool.exe
	Duration   time.Duration // Wall-clock execution duration
	ExitCode   int           // Process exit code (-1 if killed by timeout)
	TimedOut   bool          // True if the context deadline was exceeded
}

// ─── ErrLog ──────────────────────────────────────────────────────────────────

// nodeSuffixRE matches trailing 'm' or 'r' suffix on node names.
var nodeSuffixRE = regexp.MustCompile(`[mr]$`)

// stripNodeSuffix removes trailing 'm' or 'r' from a server name.
// "AP01m" → "AP01", "BP01r" → "BP01", "AP01" → "AP01".
func stripNodeSuffix(name string) string {
	return nodeSuffixRE.ReplaceAllString(name, "")
}

// ErrLogOption is a per-call option for ErrLog.
type ErrLogOption func(*errLogConfig)

type errLogConfig struct {
	requestTimeout time.Duration
	mask           string
}

// WithRequestTimeout sets a per-request timeout that overrides the client default.
func WithRequestTimeout(d time.Duration) ErrLogOption {
	return func(c *errLogConfig) {
		c.requestTimeout = d
	}
}

// WithMask sets a BsTool message filter mask.
func WithMask(mask string) ErrLogOption {
	return func(c *errLogConfig) {
		c.mask = mask
	}
}

// ErrLog executes `BsTool.exe -errlog <serverName>` and returns structured results.
//
// The serverName is automatically stripped of m/r suffix:
//
//	"AP01m" → "AP01", "BP01r" → "BP01"
//
// On Windows: executes BsTool.exe as a subprocess with context-based timeout.
// On Linux: returns ErrUnsupportedPlatform with remediation hint.
func (c *Client) ErrLog(ctx context.Context, serverName string, opts ...ErrLogOption) (*ErrLogResult, error) {
	if serverName == "" {
		return nil, &ErrInvalidServer{}
	}

	// Apply per-call options
	cfg := &errLogConfig{}
	for _, opt := range opts {
		opt(cfg)
	}

	// Strip m/r suffix
	stripped := stripNodeSuffix(serverName)
	if stripped == "" {
		return nil, &ErrInvalidServer{}
	}

	// Apply timeout
	timeout := c.defaultTimeout
	if cfg.requestTimeout > 0 {
		timeout = cfg.requestTimeout
	}

	// ── Native TCP transport path ──────────────────────────────────────
	// When a TCPTransport is configured, bypass BsTool.exe entirely and
	// communicate directly with the DNA node over TCP using the reverse-
	// engineered wire protocol.
	if c.tcp != nil {
		ctx2, cancel := context.WithTimeout(ctx, timeout)
		defer cancel()

		start := time.Now()
		// Ensure connection
		if !c.tcp.IsConnected() {
			if err := c.tcp.Connect(); err != nil {
				return nil, fmt.Errorf("bstool tcp connect: %w", err)
			}
		}

		// Use a goroutine so we can respect context cancellation
		type tcpResult struct {
			output string
			err    error
		}
		resultCh := make(chan tcpResult, 1)
		go func() {
			output, err := c.tcp.ErrLog(stripped)
			resultCh <- tcpResult{output, err}
		}()

		select {
		case <-ctx2.Done():
			c.tcp.Close()
			return nil, &ErrTimeout{Timeout: timeout.String()}
		case res := <-resultCh:
			duration := time.Since(start)
			if res.err != nil {
				return nil, fmt.Errorf("bstool tcp: %w", res.err)
			}
			messages := splitMessages(res.output)
			return &ErrLogResult{
				ServerName: stripped,
				Messages:   messages,
				RawOutput:  res.output,
				Duration:   duration,
				ExitCode:   0,
				TimedOut:   false,
			}, nil
		}
	}

	// ── Subprocess / SSH executor path ────────────────────────────────

	// Platform check (only for subprocess mode — TCP and SSH bypass this)
	if runtime.GOOS != "windows" && !c.skipPlatformCheck {
		return nil, &ErrUnsupportedPlatform{}
	}

	// Determine BsTool.exe path
	exePath := c.bstoolPath
	if exePath == "" {
		exePath = "BsTool.exe" // rely on PATH
	}

	// Build args
	args := []string{"-errlog", stripped}
	if cfg.mask != "" {
		args = append(args, "mask", cfg.mask)
	}

	// Build env
	env := []string{fmt.Sprintf("COMMUNICATION_LINE=%s", c.communicationLine)}

	execCtx := ctx
	if _, hasDeadline := ctx.Deadline(); !hasDeadline {
		var cancel context.CancelFunc
		execCtx, cancel = context.WithTimeout(ctx, timeout)
		defer cancel()
	}

	start := time.Now()
	stdout, stderrBytes, exitCode, err := c.exec.execute(execCtx, exePath, args, env)
	duration := time.Since(start)

	timedOut := execCtx.Err() == context.DeadlineExceeded

	if err != nil {
		// Check for timeout
		if timedOut {
			// If we have partial output, return it as success with timed_out=true
			if len(stdout) > 0 {
				rawOutput, decErr := decodeWindows1252(stdout)
				if decErr != nil {
					rawOutput = string(stdout)
				}
				filtered := filterStatusMessages(rawOutput)
				messages := splitMessages(filtered)
				return &ErrLogResult{
					ServerName: stripped,
					Messages:   messages,
					RawOutput:  rawOutput,
					Stderr:     string(stderrBytes),
					Duration:   duration,
					ExitCode:   exitCode,
					TimedOut:   true,
				}, nil
			}
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
		Stderr:     string(stderrBytes),
		Duration:   duration,
		ExitCode:   exitCode,
		TimedOut:   timedOut,
	}, nil
}
