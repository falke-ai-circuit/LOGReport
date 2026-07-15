package browser

import (
	"testing"
	"time"
)

func TestLaunchDisabled(t *testing.T) {
	cmd := Launch("http://localhost:8642", "/nonexistent/browser/path/browser.exe")
	if cmd != nil {
		t.Error("expected nil cmd (Launch disabled)")
	}
}

func TestLaunchDisabledEmptyPath(t *testing.T) {
	cmd := Launch("http://localhost:8642", "")
	if cmd != nil {
		t.Error("expected nil cmd (Launch disabled)")
	}
}

func TestWaitForServerReadyTimeout(t *testing.T) {
	start := time.Now()
	WaitForServerReady("http://127.0.0.1:1", 500*time.Millisecond)
	elapsed := time.Since(start)
	if elapsed < 400*time.Millisecond {
		t.Errorf("expected to wait at least ~500ms, got %v", elapsed)
	}
}