package handlers

import (
	"encoding/json"
	"net/http"
	"sync"

	"github.com/goranjovic55/LOGReport/internal/commander/bstool"
)

var (
	bstoolPathMu  sync.RWMutex
	bstoolPath    string
)

// SetBstoolPath sets the resolved BsTool path at startup
func SetBstoolPath(path string) {
	bstoolPathMu.Lock()
	bstoolPath = path
	bstoolPathMu.Unlock()
}

type BstoolRequest struct {
	IP         string `json:"ip"`
	Token      string `json:"token"`
	TimeoutSec int    `json:"timeout_sec"`
}

type BstoolStatusResponse struct {
	Available bool   `json:"available"`
	Path      string `json:"path"`
}

func BstoolStatus(w http.ResponseWriter, r *http.Request) {
	bstoolPathMu.RLock()
	p := bstoolPath
	bstoolPathMu.RUnlock()
	writeJSON(w, http.StatusOK, BstoolStatusResponse{
		Available: p != "",
		Path:      p,
	})
}

func BstoolRun(w http.ResponseWriter, r *http.Request) {
	bstoolPathMu.RLock()
	p := bstoolPath
	bstoolPathMu.RUnlock()

	if p == "" {
		writeError(w, http.StatusServiceUnavailable, "BsTool.exe not found — place it next to LOGReporter.exe or in resources/")
		return
	}

	var req BstoolRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		writeError(w, http.StatusBadRequest, "invalid JSON")
		return
	}
	if req.IP == "" || req.Token == "" {
		writeError(w, http.StatusBadRequest, "ip and token required")
		return
	}

	result, err := bstool.Run(p, req.IP, req.Token, req.TimeoutSec)
	if err != nil {
		writeError(w, http.StatusInternalServerError, err.Error())
		return
	}
	writeJSON(w, http.StatusOK, result)
}
