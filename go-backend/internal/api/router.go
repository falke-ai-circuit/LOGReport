package api

import (
	"github.com/go-chi/chi/v5"
	"github.com/go-chi/chi/v5/middleware"
	"github.com/goranjovic55/LOGReport/internal/api/handlers"
	"github.com/goranjovic55/LOGReport/internal/nodes"
)

func NewRouter(nm *nodes.Manager) *chi.Mux {
	r := chi.NewRouter()
	r.Use(middleware.Logger)
	r.Use(middleware.Recoverer)

	nh := handlers.NewNodesHandler(nm)
	nsh := handlers.NewNodeScanHandler(nm)

	r.Get("/api/health", handlers.Health)

	r.Route("/api/nodes", func(r chi.Router) {
		r.Get("/", nh.GetAll)
		r.Post("/", nh.Create)
		r.Get("/{name}", nh.GetOne)
		r.Put("/{name}", nh.Update)
		r.Delete("/{name}", nh.Delete)
	})

	r.Route("/api/logs", func(r chi.Router) {
		r.Post("/scan", handlers.ScanLogs)
		r.Post("/generate", handlers.GenerateReport)
	})
	r.Get("/api/reports/{id}/download", handlers.DownloadReport)
	r.Get("/api/scans/{scanID}/parsed", handlers.ScanParsed)

	r.Route("/api/telnet", func(r chi.Router) {
		r.Get("/", handlers.TelnetSessions)
		r.Post("/connect", handlers.TelnetConnect)
		r.Get("/{id}", handlers.TelnetStatus)
		r.Post("/{id}/command", handlers.TelnetCommand)
		r.Delete("/{id}", handlers.TelnetDisconnect)
	})

	r.Route("/api/bstool", func(r chi.Router) {
		r.Get("/status", handlers.BstoolStatus)
		r.Post("/run", handlers.BstoolRun)
	})

	r.Post("/api/node-scan", nsh.Scan)

	r.Get("/api/sessions", handlers.GetSessions)
	r.Delete("/api/sessions", handlers.ClearSessions)

	return r
}
