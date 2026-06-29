package api

import (
	"log"
	"net/http"
	"strings"
	"time"
)

// loggingMiddleware logs each request: method, path, duration, and status code.
// It wraps the handler and records timing.
// For WebSocket upgrade requests, it passes the original ResponseWriter directly
// to avoid breaking http.Hijacker interface (needed by gorilla/websocket).
func loggingMiddleware(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		// Skip wrapping for WebSocket upgrades — the wrapped writer breaks Hijacker
		if strings.EqualFold(r.Header.Get("Connection"), "Upgrade") {
			start := time.Now()
			next.ServeHTTP(w, r)
			log.Printf("%s %s WS %s", r.Method, r.URL.Path, time.Since(start))
			return
		}

		start := time.Now()

		// Wrap response writer to capture status code
		lrw := &loggingResponseWriter{ResponseWriter: w, statusCode: http.StatusOK}

		next.ServeHTTP(lrw, r)

		duration := time.Since(start)
		log.Printf("%s %s %d %s", r.Method, r.URL.Path, lrw.statusCode, duration)
	})
}

// loggingResponseWriter wraps http.ResponseWriter to capture the status code.
type loggingResponseWriter struct {
	http.ResponseWriter
	statusCode int
}

func (lrw *loggingResponseWriter) WriteHeader(code int) {
	lrw.statusCode = code
	lrw.ResponseWriter.WriteHeader(code)
}

// corsMiddleware adds CORS headers for the configured origin.
// If origin is empty, CORS is disabled (no headers added).
func corsMiddleware(origin string) func(http.Handler) http.Handler {
	return func(next http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			if origin != "" {
				w.Header().Set("Access-Control-Allow-Origin", origin)
				w.Header().Set("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
				w.Header().Set("Access-Control-Allow-Headers", "Content-Type, Authorization")
				w.Header().Set("Access-Control-Max-Age", "86400")

				// Handle preflight
				if r.Method == http.MethodOptions {
					w.WriteHeader(http.StatusNoContent)
					return
				}
			}
			next.ServeHTTP(w, r)
		})
	}
}

// contentTypeMiddleware validates Content-Type for POST/PUT/PATCH requests.
// JSON endpoints must have Content-Type: application/json.
// Multipart endpoints (parse/sysfile) must have Content-Type: multipart/form-data.
// WebSocket upgrade requests are skipped (they use Connection: Upgrade, not JSON).
func contentTypeMiddleware(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		// Skip for WebSocket upgrades
		if strings.EqualFold(r.Header.Get("Connection"), "Upgrade") {
			next.ServeHTTP(w, r)
			return
		}

		if r.Method == http.MethodPost || r.Method == http.MethodPut || r.Method == http.MethodPatch {
			ct := r.Header.Get("Content-Type")

			// Skip validation for multipart/form-data (handled by parse/sysfile)
			if strings.HasPrefix(ct, "multipart/form-data") {
				next.ServeHTTP(w, r)
				return
			}

			// Require application/json for all other POST/PUT/PATCH
			if !strings.HasPrefix(ct, "application/json") {
				writeJSON(w, http.StatusUnsupportedMediaType, map[string]string{
					"error":   "unsupported_media_type",
					"message": "Content-Type must be application/json",
				})
				return
			}
		}
		next.ServeHTTP(w, r)
	})
}
