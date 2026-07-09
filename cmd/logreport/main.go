package main

import (
	"fmt"
	"os"
	"runtime"
	"strings"
	"time"

	assets "github.com/falke-ai-circuit/LOGReport"
	"github.com/falke-ai-circuit/LOGReport/internal/api"
	"github.com/falke-ai-circuit/LOGReport/internal/browser"
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

	// Open the JSON file-based store
	st, err := store.Open(cfg.DBPath)
	if err != nil {
		fmt.Fprintf(os.Stderr, "Failed to open database: %v\n", err)
		os.Exit(1)
	}
	defer st.Close()

	// Create the BsTool client
	// When --communication-line is set, use TCP transport by default (not subprocess).
	// This allows the frontend to call BsTool errlog without specifying tcp_host.
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
	// When communication-line is set, configure a TCP transport as the default.
	// This enables the frontend WebSocket and REST endpoints to use TCP automatically
	// without the frontend needing to send tcp_host in the request.
	if cfg.CommunicationLine != "" {
		tcpTransport := bstool.NewTCPTransport(
			bstool.WithTCPHost(cfg.CommunicationLine),
			bstool.WithTCPPort(bstool.DefaultTCPPort),
		)
		bstoolOpts = append(bstoolOpts, bstool.WithTCPTransport(tcpTransport))
	}
	bstoolClient := bstool.NewClient(bstoolOpts...)

	// Create the API server with embedded web UI
	srv := api.NewServer(st, cfg, assets.FS, bstoolClient)
	srv.SetVersion(version)

	// Verify embedded assets are populated (guard against empty //go:embed)
	// If web/dist-new-flat/ wasn't built before go build, the binary serves 404 for all GUI routes.
	// Check inside web/dist-new-flat, not the root — embed.FS root contains the "web" dir.
	entries, _ := assets.FS.ReadDir("web/dist-new-flat")
	if len(entries) == 0 {
		fmt.Fprintln(os.Stderr, "ERROR: Embedded web UI is empty — run 'make build' to build frontend before compiling.")
		fmt.Fprintln(os.Stderr, "       GUI routes will return 404 until rebuilt.")
	}

	// Print startup banner
	printBanner(cfg.Port, cfg.DBPath)

	// Auto-launch browser (unless --no-browser flag is set)
	// Looks for Supermium Portable next to the binary, or uses --browser path
	if !cfg.NoBrowser {
		url := fmt.Sprintf("http://localhost:%d", cfg.Port)
		go func() {
			// Wait a moment for the server to start
			time.Sleep(500 * time.Millisecond)
			browser.Launch(url, cfg.BrowserPath)
		}()
	}

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
		if len(s) >= w {
			return s[:w] // truncate if too long
		}
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
  --db-path string    Data directory path (default "logreport-data")
  --log-level string  Log level: debug, info, warn, error (default "info")
  --cors-origin       Allowed CORS origin (default "" = no CORS)
  --bstool-path       Path to BsTool.exe (auto-detect if empty)
  --bstool-remote     Hermes-remote agent for remote BsTool execution
  --bstool-timeout    BsTool timeout in seconds (default 15)
  --browser           Path to browser exe (auto-detect Supermium if empty)
  --no-browser        Disable auto-launching browser
  --version           Print version and exit
  --help              Print this help and exit

Browser Auto-Launch:
  When Supermium Portable is placed next to LOGReport.exe in a folder
  called "supermium" or "SupermiumPortable", it is launched automatically
  on startup. Use --no-browser to disable, or --browser to specify a path.

  Directory layout:
    LOGReport.exe
    supermium/SupermiumPortable.exe   ← auto-detected

Build:
  make build          Build frontend + backend into one binary
  make run             Build and run on default port
  make run PORT=9000   Build and run on custom port

The binary has the React frontend embedded — no separate web server needed.
Just run the binary and open the printed URL in a browser.
`, version)
}
