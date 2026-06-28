//go:build windows

package bstool

import (
	"bytes"
	"context"
	"os"
	"os/exec"
	"syscall"
)

// windowsExecutor runs BsTool.exe via exec.CommandContext on Windows.
type windowsExecutor struct{}

func (e *windowsExecutor) execute(ctx context.Context, exePath string, args []string, env []string) ([]byte, []byte, int, error) {
	cmd := exec.CommandContext(ctx, exePath, args...)

	// stdin: connected to os.DevNull
	cmd.Stdin = nil

	// stdout/stderr: captured via pipes
	var stdout bytes.Buffer
	cmd.Stdout = &stdout
	var stderr bytes.Buffer
	cmd.Stderr = &stderr

	// env: COMMUNICATION_LINE
	cmd.Env = append(os.Environ(), env...)

	// SysProcAttr: CREATE_NO_WINDOW to prevent console window popup
	cmd.SysProcAttr = &syscall.SysProcAttr{
		HideWindow:    true,
		CreationFlags: 0x08000000, // CREATE_NO_WINDOW
	}

	err := cmd.Run()

	exitCode := 0
	if err != nil {
		if exitErr, ok := err.(*exec.ExitError); ok {
			exitCode = exitErr.ExitCode()
		} else {
			exitCode = -1
		}
	}

	// If context was cancelled, return the context error
	if ctx.Err() != nil {
		return stdout.Bytes(), stderr.Bytes(), exitCode, ctx.Err()
	}

	if err != nil {
		return stdout.Bytes(), stderr.Bytes(), exitCode, &executionStderr{exitCode: exitCode, stderr: stderr.String()}
	}

	return stdout.Bytes(), stderr.Bytes(), exitCode, nil
}

// platformExecutor returns the windowsExecutor on Windows.
func platformExecutor() executor {
	return &windowsExecutor{}
}
