package main

import (
	"flag"
	"fmt"
	"io/fs"
	"log"
	"net"
	"net/http"
	"os"
	"os/exec"
	"path/filepath"
	"runtime"
	"time"

	"github.com/rs/cors"
	"github.com/goranjovic55/LOGReport/internal/api"
	"github.com/goranjovic55/LOGReport/internal/api/handlers"
	"github.com/goranjovic55/LOGReport/internal/commander/bstool"
	"github.com/goranjovic55/LOGReport/internal/embedfs"
	"github.com/goranjovic55/LOGReport/internal/nodes"
)

func main() {
	port := flag.Int("port", 0, "HTTP port (0 = auto-select starting from 8080)")
	nodesFile := flag.String("nodes", "", "Path to nodes.json (default: next to executable)")
	noBrowser := flag.Bool("no-browser", false, "Do not auto-open browser")
	flag.Parse()

	// Resolve nodes.json — default next to .exe
	nodesPath := *nodesFile
	if nodesPath == "" {
		if exePath, err := os.Executable(); err == nil {
			nodesPath = filepath.Join(filepath.Dir(exePath), "nodes.json")
		} else {
			nodesPath = "nodes.json"
		}
	}

	// Extract embedded BsTool.exe to temp dir
	bsToolPath := extractBsTool()

	// Load nodes
	nm, loadErr := nodes.NewManager(nodesPath)
	if loadErr != nil {
		log.Printf("Warning: nodes file %s: %v — starting with empty list", nodesPath, loadErr)
	} else {
		log.Printf("Nodes: %s", nodesPath)
	}

	// Wire up BsTool path
	if bsToolPath != "" {
		handlers.SetBstoolPath(bsToolPath)
		log.Printf("BsTool: %s", bsToolPath)
	} else if p, err := bstool.Find(""); err == nil {
		handlers.SetBstoolPath(p)
		log.Printf("BsTool (discovered): %s", p)
	}

	// Build API router
	router := api.NewRouter(nm)

	// Serve embedded React from /
	distFS, err := fs.Sub(embedfs.StaticFiles, "web/dist")
	if err != nil {
		log.Fatalf("embed FS error: %v", err)
	}
	router.Handle("/*", http.FileServer(http.FS(distFS)))

	c := cors.New(cors.Options{
		AllowedOrigins: []string{"*"},
		AllowedMethods: []string{"GET", "POST", "PUT", "DELETE", "OPTIONS"},
		AllowedHeaders: []string{"Content-Type", "Authorization"},
	})

	// Pick port
	listenPort := pickPort(*port)
	url := fmt.Sprintf("http://localhost:%d", listenPort)
	log.Printf("LOGReport → %s", url)

	if !*noBrowser {
		go func() {
			time.Sleep(600 * time.Millisecond)
			openBrowser(url)
		}()
	}

	if err := http.ListenAndServe(fmt.Sprintf(":%d", listenPort), c.Handler(router)); err != nil {
		log.Fatalf("Server: %v", err)
	}
}

func extractBsTool() string {
	data := embedfs.BsTool
	if len(data) < 200 {
		// placeholder only — real BsTool not embedded
		return ""
	}
	dir := filepath.Join(os.TempDir(), "logreport")
	if err := os.MkdirAll(dir, 0755); err != nil {
		return ""
	}
	dest := filepath.Join(dir, "BsTool.exe")
	// Skip re-extract if same size
	if info, err := os.Stat(dest); err == nil && info.Size() == int64(len(data)) {
		return dest
	}
	if err := os.WriteFile(dest, data, 0755); err != nil {
		return ""
	}
	return dest
}

func pickPort(start int) int {
	if start <= 0 {
		start = 8080
	}
	for p := start; p < start+20; p++ {
		if ln, err := net.Listen("tcp", fmt.Sprintf(":%d", p)); err == nil {
			ln.Close()
			return p
		}
	}
	return start
}

func openBrowser(url string) {
	var cmd *exec.Cmd
	switch runtime.GOOS {
	case "windows":
		cmd = exec.Command("cmd", "/c", "start", url)
	case "darwin":
		cmd = exec.Command("open", url)
	default:
		cmd = exec.Command("xdg-open", url)
	}
	cmd.Start()
}
