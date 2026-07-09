package bstool

// executionStderr wraps stderr output from a failed execution.
// Used by both windowsExecutor and sshExecutor to return structured
// error information from BsTool.exe runs.
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
