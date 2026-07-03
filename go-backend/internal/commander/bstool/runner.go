package bstool

import (
	"context"
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"time"
)

// Find locates BsTool.exe using priority order:
// 1) configPath (if set), 2) same dir as .exe, 3) resources/ subdir, 4) cwd
func Find(configPath string) (string, error) {
	if configPath != "" {
		if _, err := os.Stat(configPath); err == nil {
			return configPath, nil
		}
	}
	exePath, err := os.Executable()
	if err == nil {
		candidates := []string{
			filepath.Join(filepath.Dir(exePath), "BsTool.exe"),
			filepath.Join(filepath.Dir(exePath), "resources", "BsTool.exe"),
		}
		for _, c := range candidates {
			if _, err := os.Stat(c); err == nil {
				return c, nil
			}
		}
	}
	// fallback: cwd
	for _, rel := range []string{"BsTool.exe", "resources/BsTool.exe"} {
		if _, err := os.Stat(rel); err == nil {
			abs, _ := filepath.Abs(rel)
			return abs, nil
		}
	}
	return "", fmt.Errorf("BsTool.exe not found — place it next to LOGReporter.exe or in resources/")
}

// RunResult holds stdout/stderr and exit info
type RunResult struct {
	Output   string `json:"output"`
	ExitCode int    `json:"exit_code"`
	TimedOut bool   `json:"timed_out"`
}

// Run executes BsTool with ip and token, capturing combined output
func Run(bstoolPath, ip, token string, timeoutSec int) (*RunResult, error) {
	if timeoutSec <= 0 {
		timeoutSec = 30
	}
	ctx, cancel := context.WithTimeout(context.Background(), time.Duration(timeoutSec)*time.Second)
	defer cancel()

	cmd := exec.CommandContext(ctx, bstoolPath, ip, token)
	out, err := cmd.CombinedOutput()

	result := &RunResult{Output: string(out)}

	if ctx.Err() == context.DeadlineExceeded {
		result.TimedOut = true
		return result, nil
	}
	if err != nil {
		if exitErr, ok := err.(*exec.ExitError); ok {
			result.ExitCode = exitErr.ExitCode()
			return result, nil
		}
		return result, err
	}
	return result, nil
}
