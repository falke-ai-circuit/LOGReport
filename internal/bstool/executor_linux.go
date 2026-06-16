//go:build !windows

package bstool

import "context"

// linuxExecutor cannot run BsTool.exe natively.
// It returns ErrUnsupportedPlatform with a clear remediation message.
type linuxExecutor struct{}

func (e *linuxExecutor) execute(ctx context.Context, exePath string, args []string, env []string) ([]byte, []byte, int, error) {
	return nil, nil, -1, &ErrUnsupportedPlatform{}
}

// platformExecutor returns the linuxExecutor on non-Windows platforms.
func platformExecutor() executor {
	return &linuxExecutor{}
}
