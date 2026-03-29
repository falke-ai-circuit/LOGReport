package handlers

import (
	"net/http"
	"path/filepath"
	"strings"
	"sync"

	"github.com/go-chi/chi/v5"
	"github.com/goranjovic55/LOGReport/internal/commander/fbc"
	"github.com/goranjovic55/LOGReport/internal/commander/rpc"
)

var (
	parsedScansMu sync.RWMutex
	parsedScans   = map[string]*ParsedScan{}
)

// ParsedScan holds FBC+RPC parsed results for all files in a scan
type ParsedScan struct {
	ScanID string           `json:"scan_id"`
	FBC    []*fbc.FBCResult `json:"fbc"`
	RPC    []*rpc.RPCResult `json:"rpc"`
}

func ScanParsed(w http.ResponseWriter, r *http.Request) {
	scanID := chi.URLParam(r, "scanID")

	scanResult, ok := GetScanResult(scanID)
	if !ok {
		writeError(w, http.StatusNotFound, "scan not found — run POST /api/logs/scan first")
		return
	}

	parsedScansMu.RLock()
	cached, hasCached := parsedScans[scanID]
	parsedScansMu.RUnlock()
	if hasCached {
		writeJSON(w, http.StatusOK, cached)
		return
	}

	result := &ParsedScan{ScanID: scanID}
	for _, group := range scanResult.Groups {
		node := group.Name
		for _, f := range group.Files {
			ext := strings.ToLower(f.Ext)
			token := extractToken(f.Name)
			switch ext {
			case ".fbc":
				parsed, err := fbc.ParseFile(f.Path, node, token)
				if err != nil {
					parsed = &fbc.FBCResult{Node: node, Token: token, Error: err.Error()}
				}
				result.FBC = append(result.FBC, parsed)
			case ".rpc":
				parsed, err := rpc.ParseFile(f.Path, node, token)
				if err != nil {
					parsed = &rpc.RPCResult{Node: node, Token: token, Error: err.Error()}
				}
				result.RPC = append(result.RPC, parsed)
			}
		}
	}

	parsedScansMu.Lock()
	parsedScans[scanID] = result
	parsedScansMu.Unlock()

	writeJSON(w, http.StatusOK, result)
}

// extractToken pulls the numeric token from filenames like "AP01m_192-168-1-11_162.fbc" → "162"
func extractToken(name string) string {
	base := strings.TrimSuffix(name, filepath.Ext(name))
	parts := strings.Split(base, "_")
	if len(parts) >= 3 {
		return parts[len(parts)-1]
	}
	return ""
}
