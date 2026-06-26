package bstool

// executor_ssh.go — SSH-based remote executor for running BsTool.exe on a Windows host.
//
// This bridges the gap: LOGReport runs on Linux, BsTool.exe runs on Windows.
// Instead of needing BsTool.exe locally, we SSH into a Windows jump host that has
// BsTool.exe installed and execute the command remotely.
//
// Architecture:
//   LOGReport (Linux) → SSH → Windows jump host → BsTool.exe -errlog <server>
//                                                  ↓ stdout
//   LOGReport ← SSH ←─────────────────────────────┘

import (
	"bytes"
	"context"
	"fmt"
	"os"
	"strings"
	"time"

	"golang.org/x/crypto/ssh"
)

// SSHExecutor runs BsTool.exe on a remote Windows host via SSH.
type SSHExecutor struct {
	host       string // Windows host address (host:port)
	user       string // SSH username
	keyPath    string // path to private key file
	password   string // password (if not using key)
	bstoolPath string // path to BsTool.exe on the remote Windows host
}

// SSHOption is a functional option for configuring SSHExecutor.
type SSHOption func(*SSHExecutor)

// WithSSHHost sets the SSH host (host:port).
func WithSSHHost(host string) SSHOption {
	return func(e *SSHExecutor) { e.host = host }
}

// WithSSHUser sets the SSH username.
func WithSSHUser(user string) SSHOption {
	return func(e *SSHExecutor) { e.user = user }
}

// WithSSHKeyPath sets the path to the SSH private key.
func WithSSHKeyPath(path string) SSHOption {
	return func(e *SSHExecutor) { e.keyPath = path }
}

// WithSSHPassword sets the SSH password (alternative to key).
func WithSSHPassword(password string) SSHOption {
	return func(e *SSHExecutor) { e.password = password }
}

// WithSSHBsToolPath sets the path to BsTool.exe on the remote Windows host.
func WithSSHBsToolPath(path string) SSHOption {
	return func(e *SSHExecutor) { e.bstoolPath = path }
}

// NewSSHExecutor creates a new SSH executor with the given options.
func NewSSHExecutor(opts ...SSHOption) *SSHExecutor {
	e := &SSHExecutor{
		bstoolPath: `C:\BsTool\BsTool.exe`, // default path on Windows
	}
	for _, opt := range opts {
		opt(e)
	}
	return e
}

// execute runs BsTool.exe on the remote Windows host via SSH.
// It satisfies the executor interface.
func (e *SSHExecutor) execute(ctx context.Context, exePath string, args []string, env []string) ([]byte, []byte, int, error) {
	if e.host == "" {
		return nil, nil, -1, fmt.Errorf("bstool ssh: host not configured (use WithSSHHost)")
	}

	// Build SSH client config
	config, err := e.buildSSHConfig()
	if err != nil {
		return nil, nil, -1, fmt.Errorf("bstool ssh: %w", err)
	}

	// Dial SSH connection
	conn, err := ssh.Dial("tcp", e.host, config)
	if err != nil {
		return nil, nil, -1, fmt.Errorf("bstool ssh: failed to connect to %s: %w", e.host, err)
	}
	defer conn.Close()

	// Open a session
	session, err := conn.NewSession()
	if err != nil {
		return nil, nil, -1, fmt.Errorf("bstool ssh: failed to create session: %w", err)
	}
	defer session.Close()

	// Set up environment variables on the remote side
	// Windows SSH servers (OpenSSH on Windows) support setting env vars via Setenv,
	// but many don't accept arbitrary env vars. We prepend them to the command instead.
	var cmdParts []string
	for _, envVar := range env {
		// envVar is in "KEY=VALUE" format
		cmdParts = append(cmdParts, fmt.Sprintf("set %s&&", envVar))
	}

	// Use the configured remote path, or fall back to exePath
	remotePath := e.bstoolPath
	if exePath != "" && exePath != "BsTool.exe" {
		remotePath = exePath
	}

	// Build the Windows command
	// Quote the path if it contains spaces
	if strings.Contains(remotePath, " ") {
		cmdParts = append(cmdParts, fmt.Sprintf(`"%s"`, remotePath))
	} else {
		cmdParts = append(cmdParts, remotePath)
	}

	// Add arguments
	for _, arg := range args {
		cmdParts = append(cmdParts, arg)
	}

	cmd := strings.Join(cmdParts, " ")

	// Capture stdout and stderr
	var stdout, stderr bytes.Buffer
	session.Stdout = &stdout
	session.Stderr = &stderr

	// Run with context awareness
	done := make(chan error, 1)
	go func() {
		done <- session.Run(cmd)
	}()

	select {
	case err := <-done:
		exitCode := 0
		if err != nil {
			// Try to extract exit code from SSH error
			if exitErr, ok := err.(*ssh.ExitError); ok {
				exitCode = exitErr.ExitStatus()
			} else {
				exitCode = -1
			}
		}
		// Check context
		if ctx.Err() != nil {
			return stdout.Bytes(), stderr.Bytes(), exitCode, ctx.Err()
		}
		if err != nil && exitCode != 0 {
			return stdout.Bytes(), stderr.Bytes(), exitCode, &executionStderr{
				exitCode: exitCode,
				stderr:   stderr.String(),
			}
		}
		return stdout.Bytes(), stderr.Bytes(), exitCode, nil
	case <-ctx.Done():
		// Context cancelled — try to kill the remote command
		_ = session.Signal(ssh.SIGKILL)
		return stdout.Bytes(), stderr.Bytes(), -1, ctx.Err()
	}
}

// buildSSHConfig creates the SSH client configuration.
func (e *SSHExecutor) buildSSHConfig() (*ssh.ClientConfig, error) {
	config := &ssh.ClientConfig{
		Timeout: 10 * time.Second,
	}

	if e.user != "" {
		config.User = e.user
	} else {
		// Try to get current user
		config.User = os.Getenv("USER")
		if config.User == "" {
			config.User = "administrator" // default for Windows
		}
	}

	// Authentication: key-based or password
	if e.keyPath != "" {
		key, err := os.ReadFile(e.keyPath)
		if err != nil {
			return nil, fmt.Errorf("failed to read SSH key %s: %w", e.keyPath, err)
		}
		signer, err := ssh.ParsePrivateKey(key)
		if err != nil {
			return nil, fmt.Errorf("failed to parse SSH key: %w", err)
		}
		config.Auth = []ssh.AuthMethod{ssh.PublicKeys(signer)}
	} else if e.password != "" {
		config.Auth = []ssh.AuthMethod{ssh.Password(e.password)}
	} else {
		return nil, fmt.Errorf("no SSH authentication configured (use WithSSHKeyPath or WithSSHPassword)")
	}

	config.HostKeyCallback = ssh.InsecureIgnoreHostKey() // TODO: proper host key verification
	return config, nil
}

// executionStderr wraps stderr output from a failed SSH execution.
// (mirrors the type in executor_windows.go)
type executionStderr struct {
	exitCode int
	stderr   string
}

func (e *executionStderr) Error() string {
	if e.stderr != "" {
		return e.stderr
	}
	return "execution failed"
}