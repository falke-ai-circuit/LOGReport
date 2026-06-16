package main

import (
	"fmt"
	"log"
	"os"
	"time"

	assets "github.com/falke-ai-circuit/LOGReport"
	"github.com/falke-ai-circuit/LOGReport/internal/api"
	"github.com/falke-ai-circuit/LOGReport/internal/bstool"
	"github.com/falke-ai-circuit/LOGReport/internal/server"
	"github.com/falke-ai-circuit/LOGReport/internal/store"
)

func main() {
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
	}
	bstoolClient := bstool.NewClient(bstoolOpts...)

	// Create the API server with embedded web UI
	srv := api.NewServer(st, cfg, assets.FS, bstoolClient)

	// Verify embedded assets are populated (guard against empty //go:embed)
	// If web/dist/ wasn't built before go build, the binary serves 404 for all GUI routes.
	// This check catches that at startup instead of silently failing.
	entries, _ := assets.FS.ReadDir(".")
	if len(entries) <= 1 { // .gitkeep only — real build has index.html + assets/
		log.Printf("WARNING: Embedded web UI appears empty (only %d entries).", len(entries))
		log.Printf("Run 'make build' (not just 'go build') to populate web/dist/ before compiling.")
		log.Printf("GUI routes (/, /nodes, /reports, /sysfile) will return 404 until rebuilt.")
	}

	// Log startup message
	log.Printf("LOGReport server starting on :%d", cfg.Port)
	log.Printf("Database: %s", cfg.DBPath)
	log.Printf("Web UI: http://localhost:%d", cfg.Port)
	log.Printf("API:    http://localhost:%d/api/v1/*", cfg.Port)
	log.Printf("Health: http://localhost:%d/health", cfg.Port)

	// Start the HTTP server (blocks until shutdown)
	if err := srv.Start(); err != nil {
		fmt.Fprintf(os.Stderr, "Server error: %v\n", err)
		os.Exit(1)
	}
}
