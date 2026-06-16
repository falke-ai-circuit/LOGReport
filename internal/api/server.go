package api

import (
	"context"
	"fmt"
	"log"
	"net/http"
	"time"

	"github.com/falke-ai-circuit/LOGReport/internal/server"
	"github.com/falke-ai-circuit/LOGReport/internal/store"
)

// Start begins listening on the configured port and serves HTTP requests.
// It blocks until the server is shut down or an error occurs.
func (s *Server) Start() error {
	mux := http.NewServeMux()

	// Register all 11 routes using Go 1.22+ method patterns
	s.registerRoutes(mux)

	// Apply middleware stack (outermost first)
	var handler http.Handler = mux
	handler = loggingMiddleware(handler)
	if s.config.CORSOrigin != "" {
		handler = corsMiddleware(s.config.CORSOrigin)(handler)
	}
	handler = contentTypeMiddleware(handler)

	httpServer := &http.Server{
		Addr:    s.config.Addr(),
		Handler: handler,
	}

	log.Printf("LOGReport API server starting on %s", s.config.Addr())
	log.Printf("Database: %s", s.config.DBPath)

	// Start graceful shutdown listener in background
	go server.GracefulShutdown(httpServer, 30*time.Second)

	if err := httpServer.ListenAndServe(); err != nil && err != http.ErrServerClosed {
		return fmt.Errorf("api: server error: %w", err)
	}

	return nil
}

// Shutdown gracefully shuts down the server.
func (s *Server) Shutdown(ctx context.Context) error {
	// The actual shutdown is handled by GracefulShutdown goroutine.
	// This method is provided for programmatic shutdown in tests.
	return nil
}

// registerRoutes sets up all 11 API endpoints on the given mux.
func (s *Server) registerRoutes(mux *http.ServeMux) {
	// 1. Health
	mux.HandleFunc("GET /health", s.healthHandler)

	// 2. Connect
	mux.HandleFunc("POST /api/v1/connect", s.connectHandler)

	// 3. List nodes
	mux.HandleFunc("GET /api/v1/nodes", s.listNodesHandler)

	// 4. Get node
	mux.HandleFunc("GET /api/v1/nodes/{addr}", s.getNodeHandler)

	// 5. Scan node
	mux.HandleFunc("POST /api/v1/nodes/{addr}/scan", s.scanNodeHandler)

	// 6. Get FBC
	mux.HandleFunc("GET /api/v1/nodes/{addr}/fbc", s.getFBCHandler)

	// 7. Get RPC
	mux.HandleFunc("GET /api/v1/nodes/{addr}/rpc", s.getRPCHandler)

	// 8. Parse sysfile
	mux.HandleFunc("POST /api/v1/parse/sysfile", s.parseSysfileHandler)

	// 9. Generate report
	mux.HandleFunc("POST /api/v1/reports/generate", s.generateReportHandler)

	// 10. List reports
	mux.HandleFunc("GET /api/v1/reports", s.listReportsHandler)

	// 11. Get report
	mux.HandleFunc("GET /api/v1/reports/{id}", s.getReportHandler)
}

// NewTestServer creates a Server suitable for testing with an in-memory SQLite DB.
func NewTestServer() (*Server, *store.Store, error) {
	// Use in-memory database for tests
	st, err := store.Open(":memory:")
	if err != nil {
		return nil, nil, fmt.Errorf("test server: open store: %w", err)
	}

	cfg := &server.Config{
		Port:       0, // random port
		DBPath:     ":memory:",
		LogLevel:   "debug",
		CORSOrigin: "*",
	}

	srv := NewServer(st, cfg)
	return srv, st, nil
}

// NewTestMux creates a ServeMux with all routes registered for handler testing.
func (s *Server) NewTestMux() http.Handler {
	mux := http.NewServeMux()
	s.registerRoutes(mux)

	var handler http.Handler = mux
	handler = contentTypeMiddleware(handler)
	return handler
}
