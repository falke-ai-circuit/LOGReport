package handlers

import (
	"encoding/json"
	"fmt"
	"net/http"
	"sync"

	"github.com/go-chi/chi/v5"
	"github.com/goranjovic55/LOGReport/internal/commander/telnet"
)

type sessionEntry struct {
	client *telnet.Client
	ip     string
	port   int
}

var (
	sessionsMu sync.RWMutex
	sessions   = map[string]*sessionEntry{}
	sessionSeq int
)

func nextSessionID() string {
	sessionSeq++
	return fmt.Sprintf("sess_%d", sessionSeq)
}

type ConnectRequest struct {
	IP   string `json:"ip"`
	Port int    `json:"port"`
}

type CommandRequest struct {
	Command      string `json:"command"`
	ContextToken string `json:"context_token"`
	TimeoutMs    int    `json:"timeout_ms"`
}

func TelnetConnect(w http.ResponseWriter, r *http.Request) {
	var req ConnectRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil || req.IP == "" {
		writeError(w, http.StatusBadRequest, "ip required")
		return
	}
	client := telnet.NewClient()
	if err := client.Connect(req.IP, req.Port); err != nil {
		writeError(w, http.StatusBadGateway, err.Error())
		return
	}
	sessionsMu.Lock()
	id := nextSessionID()
	sessions[id] = &sessionEntry{client: client, ip: req.IP, port: req.Port}
	sessionsMu.Unlock()

	writeJSON(w, http.StatusOK, map[string]string{
		"session_id": id,
		"addr":       client.Addr(),
		"status":     "connected",
	})
}

func TelnetDisconnect(w http.ResponseWriter, r *http.Request) {
	id := chi.URLParam(r, "id")
	sessionsMu.Lock()
	entry, ok := sessions[id]
	if ok {
		entry.client.Disconnect()
		delete(sessions, id)
	}
	sessionsMu.Unlock()
	if !ok {
		writeError(w, http.StatusNotFound, "session not found")
		return
	}
	w.WriteHeader(http.StatusNoContent)
}

func TelnetCommand(w http.ResponseWriter, r *http.Request) {
	id := chi.URLParam(r, "id")
	sessionsMu.RLock()
	entry, ok := sessions[id]
	sessionsMu.RUnlock()
	if !ok {
		writeError(w, http.StatusNotFound, "session not found")
		return
	}

	var req CommandRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		writeError(w, http.StatusBadRequest, "invalid JSON")
		return
	}

	resolved := telnet.ResolveCommand(req.Command, req.ContextToken)
	output, err := entry.client.SendCommand(resolved, req.TimeoutMs)
	if err != nil {
		writeError(w, http.StatusInternalServerError, err.Error())
		return
	}
	writeJSON(w, http.StatusOK, map[string]string{
		"command":  resolved,
		"raw":      req.Command,
		"output":   output,
		"session":  id,
	})
}

func TelnetStatus(w http.ResponseWriter, r *http.Request) {
	id := chi.URLParam(r, "id")
	sessionsMu.RLock()
	entry, ok := sessions[id]
	sessionsMu.RUnlock()
	if !ok {
		writeError(w, http.StatusNotFound, "session not found")
		return
	}
	writeJSON(w, http.StatusOK, map[string]interface{}{
		"session_id": id,
		"ip":         entry.ip,
		"port":       entry.port,
		"connected":  entry.client.IsConnected(),
	})
}

func TelnetSessions(w http.ResponseWriter, r *http.Request) {
	sessionsMu.RLock()
	defer sessionsMu.RUnlock()
	list := []map[string]interface{}{}
	for id, e := range sessions {
		list = append(list, map[string]interface{}{
			"session_id": id,
			"ip":         e.ip,
			"port":       e.port,
			"connected":  e.client.IsConnected(),
		})
	}
	writeJSON(w, http.StatusOK, list)
}
