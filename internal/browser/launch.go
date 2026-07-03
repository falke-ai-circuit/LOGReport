// Package browser auto-launches a web browser to open the LOGReport UI.
// It looks for Supermium Portable next to the binary, or uses a user-specified
// browser path. This is designed for remote hosts without a modern browser installed.
package browser

import (
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"runtime"
	"time"
)

// Launch opens the given URL in a browser. It searches for Supermium Portable
// in common locations relative to the binary, or uses browserPath if provided.
// Returns the launched process or nil if no browser was found.
func Launch(url, browserPath string) *exec.Cmd {
	exePath := browserPath

	// If no explicit path given, auto-detect Supermium Portable
	if exePath == "" {
		exePath = detectSupermium()
	}

	if exePath == "" {
		return nil
	}

	// Verify the browser executable exists
	if _, err := os.Stat(exePath); err != nil {
		return nil
	}

	// Launch the browser with the URL
	cmd := exec.Command(exePath, url)
	cmd.Stdout = nil
	cmd.Stderr = nil
	cmd.Stdin = nil

	// Detach the process so it survives LOGReport shutdown
	if err := cmd.Start(); err != nil {
		fmt.Fprintf(os.Stderr, "Failed to launch browser: %v\n", err)
		return nil
	}

	fmt.Printf("Launched browser: %s → %s\n", filepath.Base(exePath), url)
	return cmd
}

// detectSupermium searches for Supermium Portable in common locations:
//   - Next to LOGReport binary: ./supermium/SupermiumPortable.exe
//   - Next to LOGReport binary: ./SupermiumPortable/SupermiumPortable.exe
//   - Same directory as binary: ./SupermiumPortable.exe
//   - PortableApps default: ./SupermiumPortable/SupermiumPortable.exe
//   - Standard install paths on Windows
func detectSupermium() string {
	// Get the directory of the current executable
	exeDir, err := os.Executable()
	if err == nil {
		exeDir = filepath.Dir(exeDir)
	} else {
		exeDir = "."
	}

	candidates := []string{
		filepath.Join(exeDir, "supermium", "SupermiumPortable.exe"),
		filepath.Join(exeDir, "SupermiumPortable", "SupermiumPortable.exe"),
		filepath.Join(exeDir, "SupermiumPortable.exe"),
	}

	if runtime.GOOS == "windows" {
		candidates = append(candidates,
			`C:\Program Files\Supermium\supermium.exe`,
			`C:\Program Files (x86)\Supermium\supermium.exe`,
			filepath.Join(os.Getenv("LOCALAPPDATA"), "Supermium", "supermium.exe"),
		)
	}

	for _, p := range candidates {
		if fi, err := os.Stat(p); err == nil && !fi.IsDir() {
			return p
		}
	}

	return ""
}

// WaitForServerReady polls the URL until it responds or timeout expires.
// This ensures the server is up before the browser tries to connect.
func WaitForServerReady(url string, timeout time.Duration) {
	deadline := time.Now().Add(timeout)
	for time.Now().Before(deadline) {
		cmd := exec.Command("curl", "-s", "-o", os.DevNull, url)
		if cmd.Run() == nil {
			return
		}
		time.Sleep(200 * time.Millisecond)
	}
}