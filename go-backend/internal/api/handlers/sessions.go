package handlers

import (
	"net/http"
	"sync"
	"time"
)

type SessionRecord struct {
	ID        string    `json:"id"`
	Kind      string    `json:"kind"` // "telnet" | "bstool"
	NodeName  string    `json:"node_name"`
	IP        string    `json:"ip"`
	Token     string    `json:"token,omitempty"`
	StartedAt time.Time `json:"started_at"`
	EndedAt   *time.Time `json:"ended_at,omitempty"`
	Active    bool      `json:"active"`
	Lines     int       `json:"lines"`
}

var (
	sessionLogMu sync.RWMutex
	sessionLog   []*SessionRecord
	sessionLogSeq int
)

func nextSessionLogID(kind string) string {
	sessionLogSeq++
	if kind == "telnet" {
		return sessionLog[len(sessionLog)-1].ID
	}
	return ""
}

func RecordSessionStart(kind, nodeName, ip, token string) string {
	sessionLogMu.Lock()
	defer sessionLogMu.Unlock()
	sessionLogSeq++
	id := kind + "_" + time.Now().Format("150405") + "_" + string(rune('0'+sessionLogSeq%10))
	rec := &SessionRecord{
		ID: id, Kind: kind, NodeName: nodeName,
		IP: ip, Token: token,
		StartedAt: time.Now(), Active: true,
	}
	sessionLog = append(sessionLog, rec)
	return id
}

func RecordSessionEnd(id string, lines int) {
	sessionLogMu.Lock()
	defer sessionLogMu.Unlock()
	for _, r := range sessionLog {
		if r.ID == id {
			now := time.Now()
			r.EndedAt = &now
			r.Active = false
			r.Lines = lines
			return
		}
	}
}

func GetSessions(w http.ResponseWriter, r *http.Request) {
	sessionLogMu.RLock()
	defer sessionLogMu.RUnlock()
	// Return copy, most recent first
	out := make([]*SessionRecord, len(sessionLog))
	for i, r := range sessionLog {
		out[len(sessionLog)-1-i] = r
	}
	writeJSON(w, http.StatusOK, map[string]interface{}{
		"total":    len(out),
		"sessions": out,
	})
}

func ClearSessions(w http.ResponseWriter, r *http.Request) {
	sessionLogMu.Lock()
	sessionLog = nil
	sessionLogMu.Unlock()
	w.WriteHeader(http.StatusNoContent)
}
