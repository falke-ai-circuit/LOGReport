//go:build windows

package bstool

import "context"

// windowsExecutor is disabled to avoid AV/SmartScreen triggers on CreateProcess.
// Subprocess mode was removed in v3.9.60 — use TCP transport instead.
// To re-enable, restore the exec.CommandContext implementation and uncomment
// the subprocess paths in handlers_bstool_exec.go and handlers_settings.go.
type windowsExecutor struct{}

func (e *windowsExecutor) execute(ctx context.Context, exePath string, args []string, env []string) ([]byte, []byte, int, error) {
	return nil, nil, -1, &ErrUnsupportedPlatform{}
}

// platformExecutor returns the windowsExecutor on Windows.
func platformExecutor() executor {
	return &windowsExecutor{}
}