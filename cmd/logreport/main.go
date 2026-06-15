package main

import (
	"flag"
	"fmt"
	"os"
)

func main() {
	port := flag.Int("port", 8080, "HTTP server port")
	flag.Parse()

	fmt.Printf("LOGReport v0.1.0 — Valmet DNA report generation tool\n")
	fmt.Printf("Starting server on port %d...\n", *port)
	fmt.Printf("Web UI: http://localhost:%d\n", *port)
	fmt.Printf("API:    http://localhost:%d/api/v1/*\n", *port)
	fmt.Printf("Health: http://localhost:%d/health\n", *port)

	// TODO: Start actual HTTP server with embedded web UI and REST API
	os.Exit(0)
}
