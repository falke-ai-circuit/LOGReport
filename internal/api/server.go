package api

import (
	"context"
	"embed"
	"fmt"
	"io/fs"
	"log"
	"net/http"
	"strings"
	"time"

	"github.com/falke-ai-circuit/LOGReport/internal/bstool"
	"github.com/falke-ai-circuit/LOGReport/internal/server"
	"github.com/falke-ai-circuit/LOGReport/internal/store"
)

// Start begins listening on the configured port and serves HTTP requests.
// It blocks until the server is shut down or an error occurs.
func (s *Server) Start() error {
	mux := http.NewServeMux()

	// Register all 11 routes using Go 1.22+ method patterns
	s.registerRoutes(mux)

	// Register static file server for embedded web/dist/
	// API routes take priority (registered first), then static fallback
	s.registerStaticFiles(mux)

	// Apply middleware stack (outermost first)
	var handler http.Handler = mux
	handler = loggingMiddleware(handler)
	if s.config.CORSOrigin != "" {
		handler = corsMiddleware(s.config.CORSOrigin)(handler)
	}
	handler = contentTypeMiddleware(handler)
	handler = recoveryMiddleware(handler)

	httpServer := &http.Server{
		Addr:         s.config.Addr(),
		Handler:      handler,
		ReadTimeout:  60 * time.Second,
		WriteTimeout: 120 * time.Second, // long enough for scan-nodes (worst case ~95s)
		IdleTimeout:  120 * time.Second,
	}

	log.Printf("LOGReport API server starting on %s", s.config.Addr())
	log.Printf("Database: %s", s.config.DBPath)

	// Load settings from settings.json
	s.initSettings()

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

// registerStaticFiles serves the embedded web/dist/ directory.
// API routes are registered first and take priority.
// SPA fallback: any non-API, non-static-file path serves index.html.
func (s *Server) registerStaticFiles(mux *http.ServeMux) {
	// Strip the "web/dist-new-flat" prefix from embedded filesystem
	distFS, err := fs.Sub(s.embedFS, "web/dist-new-flat")
	if err != nil {
		log.Printf("WARNING: embedded web/dist not available: %v", err)
		return
	}

	// Read index.html once for SPA fallback
	indexHTML, err := fs.ReadFile(distFS, "index.html")
	if err != nil {
		log.Printf("WARNING: embedded index.html not found: %v", err)
		return
	}

	fileServer := http.FileServer(http.FS(distFS))

	// Serve static files at / — but only for paths that don't match API routes.
	// Since API routes are registered first on the mux, they take priority.
	// For SPA fallback: if the path doesn't match a static file, serve index.html.
	mux.HandleFunc("/", func(w http.ResponseWriter, r *http.Request) {
		// Don't intercept API or health paths
		if strings.HasPrefix(r.URL.Path, "/api/") || r.URL.Path == "/health" {
			// These should have been caught by registered routes; 404 if not
			http.NotFound(w, r)
			return
		}

		// Try to serve the exact file
		path := strings.TrimPrefix(r.URL.Path, "/")
		if path == "" {
			path = "index.html"
		}

		f, err := distFS.Open(path)
		if err == nil {
			f.Close()
			// File exists, serve it via file server
			fileServer.ServeHTTP(w, r)
			return
		}

		// SPA fallback: serve index.html content directly
		// (avoid http.FileServer redirect for directory-like paths)
		w.Header().Set("Content-Type", "text/html; charset=utf-8")
		w.WriteHeader(http.StatusOK)
		w.Write(indexHTML)
	})
}

// registerRoutes sets up all 11 API endpoints on the given mux.
func (s *Server) registerRoutes(mux *http.ServeMux) {
	// 1. Health (also registered at /api/v1/health for frontend compatibility)
	mux.HandleFunc("GET /health", s.healthHandler)
	mux.HandleFunc("GET /api/v1/health", s.healthHandler)

	// 2. Connect
	mux.HandleFunc("POST /api/v1/connect", s.connectHandler)

	// 3. List nodes
	mux.HandleFunc("GET /api/v1/nodes", s.listNodesHandler)

	// 4. Get node
	mux.HandleFunc("GET /api/v1/nodes/{addr}", s.getNodeHandler)

	// 5. Scan node
	mux.HandleFunc("POST /api/v1/nodes/{addr}/scan", s.scanNodeHandler)

	// 5a. Delete node (SQLite store)
	mux.HandleFunc("DELETE /api/v1/nodes/{addr}", s.deleteNodeHandler)

	// 5b. Rename node (SQLite store)
	mux.HandleFunc("POST /api/v1/nodes/{addr}/rename", s.renameNodeHandler)

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
	mux.HandleFunc("DELETE /api/v1/reports/{id}", s.deleteReportHandler)

	// 12. BsTool errlog
	mux.HandleFunc("POST /api/v1/bstool/errlog", s.handleBsToolErrLog)

	// ─── Commander endpoints ──────────────────────────────────────

	// Nodes config CRUD
	mux.HandleFunc("GET /api/v1/nodesconfig", s.handleGetNodesConfig)
	mux.HandleFunc("POST /api/v1/nodesconfig", s.handleSaveNodesConfig)
	mux.HandleFunc("PUT /api/v1/nodesconfig/load", s.handleLoadNodesConfig)
	mux.HandleFunc("GET /api/v1/nodesconfig/tree", s.handleGetNodesConfigTree)

	// Telnet sessions
	mux.HandleFunc("POST /api/v1/telnet/connect", s.handleTelnetConnect)
	mux.HandleFunc("POST /api/v1/telnet/execute", s.handleExecuteSingleCommand)
	mux.HandleFunc("POST /api/v1/telnet/{sessionID}/command", s.handleTelnetCommand)
	mux.HandleFunc("DELETE /api/v1/telnet/{sessionID}", s.handleTelnetDisconnect)
	mux.HandleFunc("GET /api/v1/telnet/sessions", s.handleListTelnetSessions)
	mux.HandleFunc("GET /api/v1/telnet/{sessionID}/output", s.handleTelnetOutput)

	// WebSocket endpoints (GET method to avoid path conflict with {sessionID} patterns)
	mux.HandleFunc("GET /api/v1/telnet/ws", s.telnetWSHandler)
	mux.HandleFunc("GET /api/v1/bstool/ws", s.bstoolWSHandler)

	// Command queue
	mux.HandleFunc("POST /api/v1/commandqueue/add", s.handleQueueAdd)
	mux.HandleFunc("POST /api/v1/commandqueue/start", s.handleQueueStart)
	mux.HandleFunc("POST /api/v1/commandqueue/pause", s.handleQueuePause)
	mux.HandleFunc("POST /api/v1/commandqueue/resume", s.handleQueueResume)
	mux.HandleFunc("POST /api/v1/commandqueue/cancel", s.handleQueueCancel)
	mux.HandleFunc("GET /api/v1/commandqueue/status", s.handleQueueStatus)
	mux.HandleFunc("POST /api/v1/commandqueue/batch", s.handleQueueBatch)
	mux.HandleFunc("POST /api/v1/commandqueue/batch-node", s.handleQueueBatchNode)

	// Log files
	mux.HandleFunc("GET /api/v1/logs/{nodeName}", s.handleListLogs)
	mux.HandleFunc("GET /api/v1/logs/{nodeName}/{fileName}", s.handleReadLog)
	mux.HandleFunc("POST /api/v1/logs/{nodeName}", s.handleWriteLog)

	// Log root directory scanning
	mux.HandleFunc("GET /api/v1/logs/list", s.handleListLogRoot)
	mux.HandleFunc("GET /api/v1/logs/files", s.handleListLogFiles)
	mux.HandleFunc("GET /api/v1/logs/content", s.handleLogContent)
	mux.HandleFunc("POST /api/v1/logs/setroot", s.handleSetLogRoot)

	// Scan comparison
	mux.HandleFunc("POST /api/v1/scan/compare", s.handleScanCompare)

	// Sys file loading and folder structure creation
	mux.HandleFunc("POST /api/v1/sysfiles/load", s.handleLoadSysFiles)
	mux.HandleFunc("GET /api/v1/sysfiles/parse", s.handleSysFileParseDir)
	mux.HandleFunc("GET /api/v1/sysfiles/scan", s.handleSysFileScan)
	mux.HandleFunc("POST /api/v1/sysfiles/parse-multi", s.handleSysFileParseMulti)

	// Scan nodes via DIA
	mux.HandleFunc("POST /api/v1/sysfiles/scan-nodes", s.handleScanNodes)

	// ─── Project management endpoints ──────────────────────────────

	mux.HandleFunc("POST /api/v1/projects", s.createProjectHandler)
	mux.HandleFunc("GET /api/v1/projects", s.listProjectsHandler)
	mux.HandleFunc("GET /api/v1/projects/{id}", s.getProjectHandler)
	mux.HandleFunc("PUT /api/v1/projects/{id}", s.updateProjectHandler)
	mux.HandleFunc("DELETE /api/v1/projects/{id}", s.deleteProjectHandler)
	mux.HandleFunc("POST /api/v1/projects/{id}/report", s.generateProjectReportHandler)

	// Project-scoped nodes config
	mux.HandleFunc("GET /api/v1/projects/{id}/nodes", s.handleGetProjectNodes)
	mux.HandleFunc("POST /api/v1/projects/{id}/nodes", s.handleSaveProjectNodes)

	// Settings
	mux.HandleFunc("GET /api/v1/settings", s.handleGetSettings)
	mux.HandleFunc("POST /api/v1/settings", s.handleSaveSettings)

	// Create log structure
	mux.HandleFunc("POST /api/v1/nodesconfig/create-structure", s.handleCreateLogStructure)
	mux.HandleFunc("DELETE /api/v1/nodesconfig/delete-structure", s.handleDeleteLogStructure)

	// Erase/empty a log file
	mux.HandleFunc("POST /api/v1/logs/erase", s.handleEraseLogFile)

	// Delete a log file from disk
	mux.HandleFunc("POST /api/v1/logs/delete", s.handleDeleteLogFile)

	// Create a new log file (empty) on disk
	mux.HandleFunc("POST /api/v1/logs/create", s.handleCreateLogFile)

	// Move/rename a log file to a different subfolder
	mux.HandleFunc("POST /api/v1/logs/move", s.handleMoveLogFile)

	// Create a new folder (directory) on disk
	mux.HandleFunc("POST /api/v1/logs/create-folder", s.handleCreateFolder)
	mux.HandleFunc("GET /api/v1/browse", s.handleBrowseDir)

	// Delete/rename node entries in nodes.json
	mux.HandleFunc("DELETE /api/v1/nodesconfig/entry", s.handleDeleteNodesConfigEntry)
	mux.HandleFunc("POST /api/v1/nodesconfig/rename", s.handleRenameNodesConfigEntry)
}

// NewTestServer creates a Server suitable for testing with a temp JSON store.
func NewTestServer() (*Server, *store.Store, error) {
	// Use temp directory for tests (empty string = temp dir)
	st, err := store.Open("")
	if err != nil {
		return nil, nil, fmt.Errorf("test server: open store: %w", err)
	}

	cfg := &server.Config{
		Port:       0, // random port
		DBPath:     "",
		LogLevel:   "debug",
		CORSOrigin: "*",
	}

	srv := NewServer(st, cfg, embed.FS{}, bstool.NewClient())
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

// RegisterRoutesForTest is an exported wrapper around registerRoutes for integration tests.
func (s *Server) RegisterRoutesForTest(mux *http.ServeMux) {
	s.registerRoutes(mux)
}

// LoggingMiddlewareForTest is an exported wrapper around loggingMiddleware for integration tests.
func LoggingMiddlewareForTest(next http.Handler) http.Handler {
	return loggingMiddleware(next)
}

// CORSMiddlewareForTest is an exported wrapper around corsMiddleware for integration tests.
func CORSMiddlewareForTest(origin string) func(http.Handler) http.Handler {
	return corsMiddleware(origin)
}

// ContentTypeMiddlewareForTest is an exported wrapper around contentTypeMiddleware for integration tests.
func ContentTypeMiddlewareForTest(next http.Handler) http.Handler {
	return contentTypeMiddleware(next)
}
