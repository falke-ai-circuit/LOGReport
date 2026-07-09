package bstool

import "context"

// executor is the internal interface for running BsTool.exe.
// Two implementations: windowsExecutor (real) and linuxExecutor (error).
type executor interface {
	// execute runs the command and returns stdout, stderr, exit code, and any error.
	execute(ctx context.Context, exePath string, args []string, env []string) (stdout []byte, stderr []byte, exitCode int, err error)
}

// newExecutor returns the platform-appropriate executor.
func newExecutor() executor {
	return platformExecutor()
}
