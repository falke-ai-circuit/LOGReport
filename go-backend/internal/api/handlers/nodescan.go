package handlers

import (
	"encoding/json"
	"net"
	"net/http"
	"sync"
	"time"

	"github.com/goranjovic55/LOGReport/internal/nodes"
	"github.com/goranjovic55/LOGReport/internal/models"
)

type NodeScanRequest struct {
	Names []string `json:"names"` // empty = scan all
}

type NodeScanResult struct {
	Name      string `json:"name"`
	IP        string `json:"ip"`
	Reachable bool   `json:"reachable"`
	Port23    bool   `json:"port_23"`
	Port1234  bool   `json:"port_1234"`
	LatencyMs int64  `json:"latency_ms"`
}

type NodeScanHandler struct {
	nm *nodes.Manager
}

func NewNodeScanHandler(nm *nodes.Manager) *NodeScanHandler {
	return &NodeScanHandler{nm: nm}
}

func (h *NodeScanHandler) Scan(w http.ResponseWriter, r *http.Request) {
	var req NodeScanRequest
	json.NewDecoder(r.Body).Decode(&req)

	all := h.nm.GetAll()
	var toScan []models.Node
	if len(req.Names) == 0 {
		toScan = all
	} else {
		nameSet := map[string]bool{}
		for _, n := range req.Names {
			nameSet[n] = true
		}
		for _, n := range all {
			if nameSet[n.Name] {
				toScan = append(toScan, n)
			}
		}
	}

	results := make([]NodeScanResult, len(toScan))
	var wg sync.WaitGroup
	for i, n := range toScan {
		wg.Add(1)
		go func(idx int, node models.Node) {
			defer wg.Done()
			results[idx] = probeNode(node)
		}(i, n)
	}
	wg.Wait()

	writeJSON(w, http.StatusOK, map[string]interface{}{
		"total":   len(results),
		"results": results,
	})
}

func probeNode(n models.Node) NodeScanResult {
	res := NodeScanResult{Name: n.Name, IP: n.IPAddress}

	start := time.Now()
	conn, err := net.DialTimeout("tcp", n.IPAddress+":23", 3*time.Second)
	res.LatencyMs = time.Since(start).Milliseconds()
	if err == nil {
		conn.Close()
		res.Reachable = true
		res.Port23 = true
	} else if isNetworkRefused(err) {
		// Host up but telnet not listening
		res.Reachable = true
	}

	conn2, err2 := net.DialTimeout("tcp", n.IPAddress+":1234", 2*time.Second)
	if err2 == nil {
		conn2.Close()
		res.Port1234 = true
	}

	return res
}

func isNetworkRefused(err error) bool {
	if opErr, ok := err.(*net.OpError); ok {
		if opErr.Op == "dial" {
			return true
		}
	}
	return false
}
