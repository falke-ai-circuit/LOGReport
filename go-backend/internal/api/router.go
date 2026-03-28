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

	r.Get("/api/health", handlers.Health)
	r.Route("/api/nodes", func(r chi.Router) {
		r.Get("/", nh.GetAll)
		r.Post("/", nh.Create)
		r.Get("/{name}", nh.GetOne)
		r.Put("/{name}", nh.Update)
		r.Delete("/{name}", nh.Delete)
	})

	return r
}
