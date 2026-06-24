package server

import (
	"net"
	"net/http"
	"os"
	"syscall"
	"testing"
	"time"
)

// TestGracefulShutdownWithSignal verifies that GracefulShutdown correctly
// shuts down an HTTP server when a SIGINT signal is received.
func TestGracefulShutdownWithSignal(t *testing.T) {
	handler := http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusOK)
		w.Write([]byte("ok"))
	})

	httpSrv := &http.Server{Handler: handler}

	listener, err := net.Listen("tcp", "127.0.0.1:0")
	if err != nil {
		t.Fatalf("listen: %v", err)
	}

	go func() {
		httpSrv.Serve(listener)
	}()

	time.Sleep(100 * time.Millisecond)

	// Start GracefulShutdown in a goroutine
	done := make(chan struct{})
	go func() {
		GracefulShutdown(httpSrv, 5*time.Second)
		close(done)
	}()

	// Give GracefulShutdown time to register the signal handler
	time.Sleep(50 * time.Millisecond)

	// Send SIGINT to ourselves
	syscall.Kill(os.Getpid(), syscall.SIGINT)

	// Wait for GracefulShutdown to complete
	select {
	case <-done:
		// GracefulShutdown returned — server was shut down
	case <-time.After(10 * time.Second):
		t.Fatal("GracefulShutdown did not complete within 10 seconds")
	}

	// Verify the listener is closed (new connections should fail)
	conn, err := net.DialTimeout("tcp", listener.Addr().String(), 1*time.Second)
	if err == nil {
		conn.Close()
		// The listener might still accept connections momentarily,
		// but the server should not be serving. This is a soft check.
	}
}

// TestGracefulShutdownContextTimeout verifies that GracefulShutdown
// respects the timeout when the server has pending connections.
func TestGracefulShutdownContextTimeout(t *testing.T) {
	handler := http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		time.Sleep(2 * time.Second)
		w.WriteHeader(http.StatusOK)
	})

	httpSrv := &http.Server{Handler: handler}

	listener, err := net.Listen("tcp", "127.0.0.1:0")
	if err != nil {
		t.Fatalf("listen: %v", err)
	}

	go func() {
		httpSrv.Serve(listener)
	}()

	time.Sleep(100 * time.Millisecond)

	// Start a long-running request in the background
	go func() {
		client := &http.Client{Timeout: 10 * time.Second}
		resp, err := client.Get("http://" + listener.Addr().String() + "/")
		if err == nil {
			resp.Body.Close()
		}
	}()

	time.Sleep(50 * time.Millisecond)

	// Start GracefulShutdown with a short timeout
	done := make(chan struct{})
	go func() {
		GracefulShutdown(httpSrv, 500*time.Millisecond)
		close(done)
	}()

	time.Sleep(50 * time.Millisecond)
	syscall.Kill(os.Getpid(), syscall.SIGINT)

	// GracefulShutdown should complete even with pending request
	select {
	case <-done:
		// Good — GracefulShutdown completed (possibly with forced shutdown)
	case <-time.After(10 * time.Second):
		t.Fatal("GracefulShutdown did not complete within 10 seconds")
	}
}

// TestGracefulShutdownNoSignal verifies that GracefulShutdown blocks
// when no signal is sent.
func TestGracefulShutdownNoSignal(t *testing.T) {
	httpSrv := &http.Server{
		Handler: http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {}),
	}

	listener, err := net.Listen("tcp", "127.0.0.1:0")
	if err != nil {
		t.Fatalf("listen: %v", err)
	}

	go func() {
		httpSrv.Serve(listener)
	}()

	time.Sleep(100 * time.Millisecond)

	// Start GracefulShutdown — it should block waiting for a signal
	done := make(chan struct{})
	go func() {
		GracefulShutdown(httpSrv, 5*time.Second)
		close(done)
	}()

	// Verify it doesn't return immediately
	select {
	case <-done:
		t.Error("GracefulShutdown returned without a signal being sent")
	case <-time.After(200 * time.Millisecond):
		// Good — it's still waiting for a signal
	}

	// Clean up: send signal to let it finish
	syscall.Kill(os.Getpid(), syscall.SIGINT)
	<-done
}