package main

import (
	"fmt"
	"os"
	"runtime"
	"strings"
	"time"

	assets "github.com/falke-ai-circuit/LOGReport"
	"github.com/falke-ai-circuit/LOGReport/internal/api"
	"github.com/falke-ai-circuit/LOGReport/internal/bstool"
	"github.com/falke-ai-circuit/LOGReport/internal/server"
	"github.com/falke-ai-circuit/LOGReport/internal/store"
)

// version is injected at build time via LDFLAGS:
//
//	go build -ldflags "-X main.version=v1.0.0" -o logreport ./cmd/logreport/
var version = "dev"

func main() {
	// --version flag: print and exit
	if len(os.Args) > 1 && (os.Args[1] == "--version" || os.Args[1] == "-v") {
		fmt.Printf("LOGReport %s (%s/%s)\n", version, runtime.GOOS, runtime.GOARCH)
		os.Exit(0)
	}

	// --help flag: print usage and exit
	if len(os.Args) > 1 && (os.Args[1] == "--help" || os.Args[1] == "-h") {
		printUsage()
		os.Exit(0)
	}

	// Parse command-line flags
	cfg := server.ParseFlags()

	// Open the SQLite store
	st, err := store.Open(cfg.DBPath)
	if err != nil {
		fmt.Fprintf(os.Stderr, "Failed to open database: %v\n", err)
		os.Exit(1)
	}
	defer st.Close()

	// Create the BsTool client
	var bstoolOpts []bstool.Option
	if cfg.BsToolPath != "" {
		bstoolOpts = append(bstoolOpts, bstool.WithPath(cfg.BsToolPath))
	}
	if cfg.BsToolTimeout > 0 {
		bstoolOpts = append(bstoolOpts, bstool.WithTimeout(time.Duration(cfg.BsToolTimeout)*time.Second))
		if cfg.CommunicationLine != "" {
			bstoolOpts = append(bstoolOpts, bstool.WithCommunicationLine(cfg.CommunicationLine))
		}
	}
	bstoolClient := bstool.NewClient(bstoolOpts...)

	// Create the API server with embedded web UI
	srv := api.NewServer(st, cfg, assets.FS, bstoolClient)

	// Verify embedded assets are populated (guard against empty //go:embed)
	// If web/dist/ wasn't built before go build, the binary serves 404 for all GUI routes.
	// Check inside web/dist, not the root — embed.FS root contains the "web" dir.
	entries, _ := assets.FS.ReadDir("web/dist")
	if len(entries) == 0 {
		fmt.Fprintln(os.Stderr, "ERROR: Embedded web UI is empty — run 'make build' to build frontend before compiling.")
		fmt.Fprintln(os.Stderr, "       GUI routes will return 404 until rebuilt.")
	}

	// Print startup banner
	printBanner(cfg.Port, cfg.DBPath)

	// Start the HTTP server (blocks until shutdown)
	if err := srv.Start(); err != nil {
		fmt.Fprintf(os.Stderr, "Server error: %v\n", err)
		os.Exit(1)
	}
}

func printBanner(port int, dbPath string) {
	url := fmt.Sprintf("http://localhost:%d", port)
	api := fmt.Sprintf("http://localhost:%d/api/v1", port)
	health := fmt.Sprintf("http://localhost:%d/health", port)

	// Fixed 48-char inner width for clean alignment
	w := 48
	pad := func(s string) string {
		return s + strings.Repeat(" ", w-len(s))
	}

	fmt.Println()
	fmt.Printf("╔%s╗\n", strings.Repeat("═", w))
	fmt.Printf("║%s║\n", pad("  LOGReport "+version))
	fmt.Printf("╠%s╣\n", strings.Repeat("═", w))
	fmt.Printf("║%s║\n", pad(""))
	fmt.Printf("║%s║\n", pad("  Web UI:   "+url))
	fmt.Printf("║%s║\n", pad("  API:      "+api))
	fmt.Printf("║%s║\n", pad("  Health:   "+health))
	fmt.Printf("║%s║\n", pad("  Database: "+dbPath))
	fmt.Printf("║%s║\n", pad(""))
	fmt.Printf("║%s║\n", pad("  Open the Web UI URL in your browser."))
	fmt.Printf("║%s║\n", pad("  Press Ctrl+C to stop."))
	fmt.Printf("╚%s╝\n", strings.Repeat("═", w))
	fmt.Println()
}

func printUsage() {
	fmt.Printf(`
LOGReport %s — Structured log analysis & reporting tool

Usage:
  logreport [flags]

Flags:
  --port int          HTTP server port (default 8642)
  --db-path string    SQLite database path (default "logreport.db")
  --log-level string  Log level: debug, info, warn, error (default "info")
  --cors-origin       Allowed CORS origin (default "" = no CORS)
  --bstool-path       Path to BsTool.exe (auto-detect if empty)
  --bstool-remote     Hermes-remote agent for remote BsTool execution
  --bstool-timeout    BsTool timeout in seconds (default 15)
  --version           Print version and exit
  --help              Print this help and exit

Build:
  make build          Build frontend + backend into one binary
  make run             Build and run on default port
  make run PORT=9000   Build and run on custom port

The binary has the React frontend embedded — no separate web server needed.
Just run the binary and open the printed URL in a browser.
`, version)
}
