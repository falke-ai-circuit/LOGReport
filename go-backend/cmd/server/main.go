package main

import (
	"flag"
	"fmt"
	"log"
	"net/http"

	"github.com/rs/cors"
	"github.com/goranjovic55/LOGReport/internal/api"
	"github.com/goranjovic55/LOGReport/internal/nodes"
)

func main() {
	port := flag.Int("port", 8080, "HTTP server port")
	nodesFile := flag.String("nodes", "./nodes.json", "Path to nodes.json")
	flag.Parse()

	nm, err := nodes.NewManager(*nodesFile)
	if err != nil {
		log.Fatalf("failed to load nodes: %v", err)
	}

	router := api.NewRouter(nm)

	c := cors.New(cors.Options{
		AllowedOrigins: []string{"http://localhost:3000", "http://localhost:5173", "http://127.0.0.1:*"},
		AllowedMethods: []string{"GET", "POST", "PUT", "DELETE", "OPTIONS"},
		AllowedHeaders: []string{"Content-Type"},
	})

	handler := c.Handler(router)

	addr := fmt.Sprintf(":%d", *port)
	log.Printf("LOGReport server starting on %s", addr)
	log.Printf("Nodes file: %s", *nodesFile)

	if err := http.ListenAndServe(addr, handler); err != nil {
		log.Fatalf("server error: %v", err)
	}
}
