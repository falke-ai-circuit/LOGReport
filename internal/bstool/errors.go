// Package bstool provides a Go wrapper for BsTool.exe -errlog subprocess execution.
package bstool

import "fmt"

// ─── Typed Errors ────────────────────────────────────────────────────────────

// ErrNotFound indicates BsTool.exe was not found at the configured path.
type ErrNotFound struct {
	Path string
}

func (e *ErrNotFound) Error() string {
	return fmt.Sprintf("bstool: BsTool.exe not found at %q", e.Path)
}

func (e *ErrNotFound) Code() string {
	return "BSTOOL_NOT_FOUND"
}

// ErrUnsupportedPlatform indicates the current platform cannot run BsTool.exe.
type ErrUnsupportedPlatform struct{}

func (e *ErrUnsupportedPlatform) Error() string {
	return "bstool: BsTool.exe requires Windows. Use --bstool-remote flag to execute via hermes-remote on Windows host."
}

func (e *ErrUnsupportedPlatform) Code() string {
	return "UNSUPPORTED_PLATFORM"
}

// ErrTimeout indicates the BsTool.exe execution exceeded the deadline.
type ErrTimeout struct {
	Timeout string
}

func (e *ErrTimeout) Error() string {
	return fmt.Sprintf("bstool: execution timed out after %s", e.Timeout)
}

func (e *ErrTimeout) Code() string {
	return "BSTOOL_TIMEOUT"
}

// ErrExecution indicates the BsTool.exe subprocess failed with a non-zero exit code.
type ErrExecution struct {
	ExitCode int
	Stderr   string
}

func (e *ErrExecution) Error() string {
	if e.Stderr != "" {
		return fmt.Sprintf("bstool: execution failed with exit code %d: %s", e.ExitCode, e.Stderr)
	}
	return fmt.Sprintf("bstool: execution failed with exit code %d", e.ExitCode)
}

func (e *ErrExecution) Code() string {
	return "BSTOOL_EXECUTION_FAILED"
}

// ErrInvalidServer indicates an empty or invalid server name was provided.
type ErrInvalidServer struct{}

func (e *ErrInvalidServer) Error() string {
	return "bstool: server name is required and cannot be empty"
}

func (e *ErrInvalidServer) Code() string {
	return "INVALID_REQUEST"
}
