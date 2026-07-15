// Package browser auto-launches a web browser to open the LOGReport UI.
// Subprocess launch disabled in v3.9.60 to avoid AV/SmartScreen triggers.
package browser

import (
	"net/http"
	"time"
)

// Launch opens the given URL in a browser.
// Disabled — returns nil to avoid CreateProcess AV triggers.
func Launch(url, browserPath string) *Cmd {
	return nil
}

// Cmd is a placeholder type (was *exec.Cmd).
type Cmd struct{}

// WaitForServerReady polls the URL until it responds or timeout expires.
// Uses net/http instead of exec.Command("curl") to avoid CreateProcess.
func WaitForServerReady(url string, timeout time.Duration) {
	deadline := time.Now().Add(timeout)
	client := &http.Client{Timeout: 2 * time.Second}
	for time.Now().Before(deadline) {
		resp, err := client.Get(url)
		if err == nil {
			resp.Body.Close()
			return
		}
		time.Sleep(200 * time.Millisecond)
	}
}