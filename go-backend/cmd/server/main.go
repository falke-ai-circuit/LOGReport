package main

import (
	"flag"
	"fmt"
	"log"
	"net/http"

	"github.com/rs/cors"
	"github.com/goranjovic55/LOGReport/internal/api"
	"github.com/goranjovic55/LOGReport/internal/api/handlers"
	"github.com/goranjovic55/LOGReport/internal/commander/bstool"
	"github.com/goranjovic55/LOGReport/internal/nodes"
)

func main() {
	port := flag.String("port", "8080", "HTTP listen port")
	nodesFile := flag.String("nodes", "nodes.json", "Path to nodes.json")
	bstoolConfig := flag.String("bstool", "", "Path to BsTool.exe (optional, auto-detected if omitted)")
	flag.Parse()

	nm, loadErr := nodes.NewManager(*nodesFile)
	if loadErr != nil {
		log.Printf("Warning: could not load nodes file %s: %v", *nodesFile, loadErr)
	} else {
		log.Printf("Nodes file: %s", *nodesFile)
	}

	bsPath, bsErr := bstool.Find(*bstoolConfig)
	if bsErr != nil {
		log.Printf("BsTool: not found (%v) — BsTool tab will show unavailable", bsErr)
	} else {
		log.Printf("BsTool: %s", bsPath)
		handlers.SetBstoolPath(bsPath)
	}

	router := api.NewRouter(nm)
	c := cors.New(cors.Options{
		AllowedOrigins: []string{
			"http://localhost:3000",
			"http://localhost:5173",
			"http://127.0.0.1:5173",
			"http://127.0.0.1:3000",
		},
		AllowedMethods: []string{"GET", "POST", "PUT", "DELETE", "OPTIONS"},
		AllowedHeaders: []string{"Content-Type", "Authorization"},
	})

	addr := fmt.Sprintf(":%s", *port)
	log.Printf("LOGReport server starting on %s", addr)
	if err := http.ListenAndServe(addr, c.Handler(router)); err != nil {
		log.Fatalf("Server error: %v", err)
	}
}
