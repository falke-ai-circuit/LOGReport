// Package api provides HTTP handlers for the LOGReport REST API.
// It implements all 11 endpoints defined in the API specification,
// using Go 1.22+ routing patterns with method-based dispatch.
package api

import (
	"embed"
	"encoding/json"
	"fmt"
	"io"
	"log"
	"net/http"
	"os"
	"path/filepath"
	"strings"
	"time"

	"github.com/falke-ai-circuit/LOGReport/internal/bstool"
	"github.com/falke-ai-circuit/LOGReport/internal/commandqueue"
	"github.com/falke-ai-circuit/LOGReport/internal/parser"
	"github.com/falke-ai-circuit/LOGReport/internal/report"
	"github.com/falke-ai-circuit/LOGReport/internal/server"
	"github.com/falke-ai-circuit/LOGReport/internal/store"
	"github.com/falke-ai-circuit/LOGReport/internal/telnet"
	"github.com/falke-ai-circuit/LOGReport/internal/types"
)

// ─── Response Helpers ───────────────────────────────────────────

// writeJSON writes a JSON response with the given status code.
func writeJSON(w http.ResponseWriter, status int, v interface{}) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(status)
	if err := json.NewEncoder(w).Encode(v); err != nil {
		log.Printf("api: json encode error: %v", err)
	}
}

// writeError writes a JSON error response.
func writeError(w http.ResponseWriter, status int, code, message string) {
	writeJSON(w, status, map[string]string{
		"error":   code,
		"message": message,
	})
}

// writeErrorDetails writes a JSON error response with extra details.
func writeErrorDetails(w http.ResponseWriter, status int, code, message string, details interface{}) {
	resp := map[string]interface{}{
		"error":   code,
		"message": message,
	}
	if details != nil {
		resp["details"] = details
	}
	writeJSON(w, status, resp)
}

// ─── API Response Types ─────────────────────────────────────────

// apiNode is the JSON response shape for a node (matches API spec).
type apiNode struct {
	ID            int    `json:"id"`
	Address       string `json:"address"`
	Port          int    `json:"port"`
	Name          string `json:"name"`
	NodeType      string `json:"node_type"`
	Token         string `json:"token"`
	Status        string `json:"status"`
	LastConnected string `json:"last_connected"`
	CreatedAt     string `json:"created_at"`
	UpdatedAt     string `json:"updated_at"`
}

// nodeToAPI converts a types.Node to the API response shape.
func nodeToAPI(n *types.Node) apiNode {
	now := time.Now().UTC().Format(time.RFC3339)
	lastSeen := ""
	if !n.LastSeen.IsZero() {
		lastSeen = n.LastSeen.UTC().Format(time.RFC3339)
	}
	return apiNode{
		ID:            0, // SQLite rowid not exposed in types.Node
		Address:       n.Address,
		Port:          n.Port,
		Name:          n.Name,
		NodeType:      string(n.Type),
		Token:         n.TokenID,
		Status:        string(n.Status),
		LastConnected: lastSeen,
		CreatedAt:     now,
		UpdatedAt:     now,
	}
}

// apiFBCModule is the JSON response shape for an FBC module.
type apiFBCModule struct {
	ModulePosition int              `json:"module_position"`
	Channels       []apiFBCChannel  `json:"channels"`
}

// apiFBCChannel is the JSON response shape for an FBC channel.
type apiFBCChannel struct {
	ChannelPosition int    `json:"channel_position"`
	ChannelType     string `json:"channel_type"`
}

// apiRPCModule is the JSON response shape for an RPC module.
type apiRPCModule struct {
	ModulePosition int              `json:"module_position"`
	Counters       []apiRPCCounter  `json:"counters"`
}

// apiRPCCounter is the JSON response shape for an RPC counter.
type apiRPCCounter struct {
	CounterName  string `json:"counter_name"`
	CounterValue int    `json:"counter_value"`
}

// apiReport is the JSON response shape for a report.
type apiReport struct {
	ReportID      string   `json:"report_id"`
	Status        string   `json:"status"`
	Format        string   `json:"format"`
	Template      string   `json:"template"`
	NodeAddresses []string `json:"node_addresses"`
	FilePath      string   `json:"file_path,omitempty"`
	FileSize      *int64   `json:"file_size,omitempty"`
	CreatedAt     string   `json:"created_at"`
	CompletedAt   string   `json:"completed_at,omitempty"`
	ErrorMessage  string   `json:"error_message,omitempty"`
}

// reportToAPI converts a types.Report to the API response shape.
func reportToAPI(r *types.Report) apiReport {
	ar := apiReport{
		ReportID:      r.ID,
		Status:        string(r.Status),
		Format:        string(r.Format),
		Template:      r.Template,
		NodeAddresses: []string{r.NodeAddress},
		FilePath:      r.FilePath,
		CreatedAt:     r.CreatedAt,
		CompletedAt:   r.CompletedAt,
	}
	if r.FilePath != "" {
		if fi, err := os.Stat(r.FilePath); err == nil {
			size := fi.Size()
			ar.FileSize = &size
		}
	}
	return ar
}

// ─── Server Struct ──────────────────────────────────────────────

// Server holds the dependencies needed by all API handlers.
type Server struct {
	store         *store.Store
	startTime     time.Time
	config        *server.Config
	embedFS       embed.FS
	bstoolClient  *bstool.Client
	telnetSM      *telnet.SessionManager   // Commander: persistent telnet sessions
	commandQueue  *commandqueue.Queue       // Commander: sequential command queue
	logRootDir    string                    // Commander: root dir for log files
}

// NewServer creates a new API Server with the given store, config, embedded filesystem, and bstool client.
func NewServer(s *store.Store, cfg *server.Config, embedFS embed.FS, bstoolClient *bstool.Client) *Server {
	return &Server{
		store:         s,
		startTime:     time.Now(),
		config:        cfg,
		embedFS:       embedFS,
		bstoolClient:  bstoolClient,
		telnetSM:      telnet.NewSessionManager(),
		commandQueue:  commandqueue.NewQueue(nil, nil),
		logRootDir:    "logs",
	}
}

// logRoot returns the log root directory, ensuring it exists.
func (s *Server) logRoot() string {
	return s.logRootDir
}

// Store returns the underlying store (used by server.go for health).
func (s *Server) Store() *store.Store {
	return s.store
}

// StartTime returns the server start time.
func (s *Server) StartTime() time.Time {
	return s.startTime
}

// ─── Handler 1: GET /health ─────────────────────────────────────

func (s *Server) healthHandler(w http.ResponseWriter, r *http.Request) {
	h := server.GetHealth(s.store.DB(), s.startTime)
	writeJSON(w, http.StatusOK, h)
}

// ─── Handler 2: POST /api/v1/connect ────────────────────────────

type connectRequest struct {
	Address  string `json:"address"`
	Port     int    `json:"port"`
	Name     string `json:"name"`
	NodeType string `json:"node_type"`
	Token    string `json:"token"`
	Username string `json:"username"`
	Password string `json:"password"`
}

func (s *Server) connectHandler(w http.ResponseWriter, r *http.Request) {
	var req connectRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		writeError(w, http.StatusBadRequest, "validation_error", "invalid JSON body")
		return
	}

	// Validate required fields
	if req.Address == "" || req.Name == "" {
		writeErrorDetails(w, http.StatusBadRequest, "validation_error",
			"address and name are required", map[string]string{
				"address": cond(req.Address == "", "missing required field", ""),
				"name":    cond(req.Name == "", "missing required field", ""),
			})
		return
	}

	// Defaults
	if req.Port == 0 {
		req.Port = 23
	}
	nodeType := req.NodeType
	if nodeType == "" {
		nodeType = "unknown"
	}

	// Attempt telnet connection to verify reachability
	client, err := telnet.Dial(req.Address, req.Port, 10*time.Second)
	if err != nil {
		writeErrorDetails(w, http.StatusBadGateway, "connection_failed",
			fmt.Sprintf("telnet connection to %s:%d failed: %v", req.Address, req.Port, err),
			map[string]string{"node_address": req.Address})
		return
	}
	client.Close() // just verifying connectivity

	// Build and save node
	node := &types.Node{
		Address:  req.Address,
		Name:     req.Name,
		Type:     types.NodeType(nodeType),
		Status:   types.StatusConnected,
		TokenID:  req.Token,
		Port:     req.Port,
		Username: req.Username,
		Password: req.Password,
		LastSeen: time.Now(),
	}

	if err := s.store.SaveNode(node); err != nil {
		writeError(w, http.StatusInternalServerError, "internal_error",
			fmt.Sprintf("failed to save node: %v", err))
		return
	}

	writeJSON(w, http.StatusOK, map[string]interface{}{
		"node": nodeToAPI(node),
	})
}

// ─── Handler 3: GET /api/v1/nodes ────────────────────────────────

func (s *Server) listNodesHandler(w http.ResponseWriter, r *http.Request) {
	nodes, err := s.store.ListNodes()
	if err != nil {
		writeError(w, http.StatusInternalServerError, "internal_error",
			fmt.Sprintf("failed to list nodes: %v", err))
		return
	}

	// AXON safety: ensure nodes is never nil
	if nodes == nil {
		nodes = []*types.Node{}
	}

	apiNodes := make([]apiNode, 0, len(nodes))
	for _, n := range nodes {
		apiNodes = append(apiNodes, nodeToAPI(n))
	}

	writeJSON(w, http.StatusOK, map[string]interface{}{
		"nodes":  apiNodes,
		"total":  len(apiNodes),
		"limit":  50,
		"offset": 0,
	})
}

// ─── Handler 4: GET /api/v1/nodes/{addr} ────────────────────────

func (s *Server) getNodeHandler(w http.ResponseWriter, r *http.Request) {
	addr := r.PathValue("addr")
	if addr == "" {
		writeError(w, http.StatusBadRequest, "validation_error", "node address is required")
		return
	}

	node, err := s.store.GetNode(addr)
	if err != nil {
		writeError(w, http.StatusNotFound, "not_found",
			fmt.Sprintf("node with address '%s' not found", addr))
		return
	}

	// Get IO summary
	ioPoints, _ := s.store.GetIOPoints(addr)
	fbcCount := 0
	rpcCount := 0
	for _, p := range ioPoints {
		switch p.ModuleType {
		case types.ModuleFBC:
			fbcCount++
		case types.ModuleRPC:
			rpcCount++
		}
	}

	writeJSON(w, http.StatusOK, map[string]interface{}{
		"node": nodeToAPI(node),
		"io_summary": map[string]interface{}{
			"fbc_modules":    fbcCount,
			"rpc_modules":    rpcCount,
			"total_io_points": len(ioPoints),
			"last_scan":      nil,
		},
	})
}

// ─── Handler 5: POST /api/v1/nodes/{addr}/scan ──────────────────

type scanRequest struct {
	Modules []string `json:"modules"`
	Token   string   `json:"token"`
}

func (s *Server) scanNodeHandler(w http.ResponseWriter, r *http.Request) {
	addr := r.PathValue("addr")
	if addr == "" {
		writeError(w, http.StatusBadRequest, "validation_error", "node address is required")
		return
	}

	var req scanRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		writeError(w, http.StatusBadRequest, "validation_error", "invalid JSON body")
		return
	}

	// Default modules
	if len(req.Modules) == 0 {
		req.Modules = []string{"fbc", "rpc"}
	}

	// Get node from store
	node, err := s.store.GetNode(addr)
	if err != nil {
		writeError(w, http.StatusNotFound, "not_found",
			fmt.Sprintf("node with address '%s' not found", addr))
		return
	}

	// Check node is connected
	if node.Status != types.StatusConnected {
		writeErrorDetails(w, http.StatusConflict, "node_not_connected",
			fmt.Sprintf("node '%s' is not connected. POST /api/v1/connect first.", addr),
			map[string]string{"node_status": string(node.Status)})
		return
	}

	// Use node's token if not provided in request
	token := req.Token
	if token == "" {
		token = node.TokenID
	}
	if token == "" {
		writeError(w, http.StatusBadRequest, "validation_error", "token is required for scan")
		return
	}

	// Connect via telnet
	client, err := telnet.Dial(addr, node.Port, 30*time.Second)
	if err != nil {
		writeErrorDetails(w, http.StatusBadGateway, "connection_failed",
			fmt.Sprintf("telnet connection to %s:%d failed: %v", addr, node.Port, err),
			map[string]string{"node_address": addr})
		return
	}
	defer client.Close()

	scanResults := map[string]interface{}{
		"node_address": addr,
		"scanned_at":   time.Now().UTC().Format(time.RFC3339),
	}

	var allIOPoints []types.IOPoint
	fbcModules := []types.FBCModule{}
	rpcModules := []types.RPCModule{}

	for _, mod := range req.Modules {
		switch strings.ToLower(mod) {
		case "fbc":
			cmd := telnet.FBCPrint(token)
			if err := client.SendCommand(cmd); err != nil {
				writeErrorDetails(w, http.StatusBadGateway, "scan_failed",
					fmt.Sprintf("telnet command '%s' failed: %v", cmd, err),
					map[string]interface{}{
						"failed_module":   "fbc",
						"partial_results": scanResults,
					})
				return
			}
			output, err := client.ReadUntilPrompt()
			if err != nil {
				writeErrorDetails(w, http.StatusBadGateway, "scan_failed",
					fmt.Sprintf("reading FBC output failed: %v", err),
					map[string]interface{}{
						"failed_module":   "fbc",
						"partial_results": scanResults,
					})
				return
			}
			parsed, err := parser.ParseFBC(output)
			if err != nil {
				writeErrorDetails(w, http.StatusBadGateway, "scan_failed",
					fmt.Sprintf("parsing FBC output failed: %v", err),
					map[string]interface{}{
						"failed_module":   "fbc",
						"partial_results": scanResults,
					})
				return
			}
			fbcModules = parsed
			allIOPoints = append(allIOPoints, types.FBCToIOPoints(addr, parsed)...)

		case "rpc":
			cmd := telnet.RPCPrint(token)
			if err := client.SendCommand(cmd); err != nil {
				writeErrorDetails(w, http.StatusBadGateway, "scan_failed",
					fmt.Sprintf("telnet command '%s' failed: %v", cmd, err),
					map[string]interface{}{
						"failed_module":   "rpc",
						"partial_results": scanResults,
					})
				return
			}
			output, err := client.ReadUntilPrompt()
			if err != nil {
				writeErrorDetails(w, http.StatusBadGateway, "scan_failed",
					fmt.Sprintf("reading RPC output failed: %v", err),
					map[string]interface{}{
						"failed_module":   "rpc",
						"partial_results": scanResults,
					})
				return
			}
			parsed, err := parser.ParseRPC(output)
			if err != nil {
				writeErrorDetails(w, http.StatusBadGateway, "scan_failed",
					fmt.Sprintf("parsing RPC output failed: %v", err),
					map[string]interface{}{
						"failed_module":   "rpc",
						"partial_results": scanResults,
					})
				return
			}
			rpcModules = parsed
			allIOPoints = append(allIOPoints, types.RPCToIOPoints(addr, parsed)...)
		}
	}

	// Save IO points to store
	if len(allIOPoints) > 0 {
		if err := s.store.SaveIOPoints(addr, allIOPoints); err != nil {
			log.Printf("api: failed to save IO points for %s: %v", addr, err)
		}
	}

	// Build FBC API response
	apiFBC := make([]apiFBCModule, 0)
	for _, mod := range fbcModules {
		channels := make([]apiFBCChannel, 0)
		for _, ch := range mod.Channels {
			channels = append(channels, apiFBCChannel{
				ChannelPosition: ch.Position,
				ChannelType:     string(ch.Type),
			})
		}
		apiFBC = append(apiFBC, apiFBCModule{
			ModulePosition: mod.Position,
			Channels:       channels,
		})
	}

	// Build RPC API response
	apiRPC := make([]apiRPCModule, 0)
	for _, mod := range rpcModules {
		counters := make([]apiRPCCounter, 0)
		for _, ctr := range mod.Counters {
			counters = append(counters, apiRPCCounter{
				CounterName:  ctr.Name,
				CounterValue: ctr.Value,
			})
		}
		apiRPC = append(apiRPC, apiRPCModule{
			ModulePosition: mod.Position,
			Counters:       counters,
		})
	}

	scanResults["fbc_modules"] = apiFBC
	scanResults["rpc_modules"] = apiRPC
	scanResults["io_points_total"] = len(allIOPoints)

	writeJSON(w, http.StatusOK, scanResults)
}

// ─── Handler 6: GET /api/v1/nodes/{addr}/fbc ────────────────────

func (s *Server) getFBCHandler(w http.ResponseWriter, r *http.Request) {
	addr := r.PathValue("addr")
	if addr == "" {
		writeError(w, http.StatusBadRequest, "validation_error", "node address is required")
		return
	}

	// Verify node exists
	_, err := s.store.GetNode(addr)
	if err != nil {
		writeError(w, http.StatusNotFound, "not_found",
			fmt.Sprintf("node with address '%s' not found", addr))
		return
	}

	// Get FBC IO points from store
	ioPoints, err := s.store.GetIOPoints(addr)
	if err != nil {
		writeError(w, http.StatusInternalServerError, "internal_error",
			fmt.Sprintf("failed to get IO points: %v", err))
		return
	}

	// Filter FBC points and group by module position
	fbcMap := make(map[int][]apiFBCChannel)
	for _, p := range ioPoints {
		if p.ModuleType == types.ModuleFBC {
			fbcMap[p.ModulePosition] = append(fbcMap[p.ModulePosition], apiFBCChannel{
				ChannelPosition: p.ChannelPosition,
				ChannelType:     string(p.ChannelType),
			})
		}
	}

	modules := make([]apiFBCModule, 0)
	for pos := 0; pos < 64; pos++ {
		if channels, ok := fbcMap[pos]; ok {
			modules = append(modules, apiFBCModule{
				ModulePosition: pos,
				Channels:       channels,
			})
		}
	}

	if len(modules) == 0 {
		writeError(w, http.StatusNotFound, "not_found",
			fmt.Sprintf("no FBC data for node '%s'. Run POST /api/v1/nodes/{addr}/scan first.", addr))
		return
	}

	writeJSON(w, http.StatusOK, map[string]interface{}{
		"node_address":  addr,
		"fbc_modules":   modules,
		"total_modules": len(modules),
	})
}

// ─── Handler 7: GET /api/v1/nodes/{addr}/rpc ────────────────────

func (s *Server) getRPCHandler(w http.ResponseWriter, r *http.Request) {
	addr := r.PathValue("addr")
	if addr == "" {
		writeError(w, http.StatusBadRequest, "validation_error", "node address is required")
		return
	}

	// Verify node exists
	_, err := s.store.GetNode(addr)
	if err != nil {
		writeError(w, http.StatusNotFound, "not_found",
			fmt.Sprintf("node with address '%s' not found", addr))
		return
	}

	// Get RPC IO points from store
	ioPoints, err := s.store.GetIOPoints(addr)
	if err != nil {
		writeError(w, http.StatusInternalServerError, "internal_error",
			fmt.Sprintf("failed to get IO points: %v", err))
		return
	}

	// Filter RPC points and group by module position
	rpcMap := make(map[int][]apiRPCCounter)
	for _, p := range ioPoints {
		if p.ModuleType == types.ModuleRPC {
			rpcMap[p.ModulePosition] = append(rpcMap[p.ModulePosition], apiRPCCounter{
				CounterName:  p.CounterName,
				CounterValue: p.CounterValue,
			})
		}
	}

	modules := make([]apiRPCModule, 0)
	for pos := 0; pos < 64; pos++ {
		if counters, ok := rpcMap[pos]; ok {
			modules = append(modules, apiRPCModule{
				ModulePosition: pos,
				Counters:       counters,
			})
		}
	}

	if len(modules) == 0 {
		writeError(w, http.StatusNotFound, "not_found",
			fmt.Sprintf("no RPC data for node '%s'. Run POST /api/v1/nodes/{addr}/scan first.", addr))
		return
	}

	writeJSON(w, http.StatusOK, map[string]interface{}{
		"node_address":  addr,
		"rpc_modules":   modules,
		"total_modules": len(modules),
	})
}

// ─── Handler 8: POST /api/v1/parse/sysfile ──────────────────────

func (s *Server) parseSysfileHandler(w http.ResponseWriter, r *http.Request) {
	// Parse multipart form (max 10MB)
	if err := r.ParseMultipartForm(10 << 20); err != nil {
		writeError(w, http.StatusBadRequest, "validation_error", "failed to parse multipart form")
		return
	}

	file, header, err := r.FormFile("file")
	if err != nil {
		writeError(w, http.StatusBadRequest, "validation_error", "file field is required")
		return
	}
	defer file.Close()

	// Save uploaded file to temp location
	tmpDir := os.TempDir()
	tmpPath := filepath.Join(tmpDir, header.Filename)
	dst, err := os.Create(tmpPath)
	if err != nil {
		writeError(w, http.StatusInternalServerError, "internal_error",
			fmt.Sprintf("failed to create temp file: %v", err))
		return
	}
	defer os.Remove(tmpPath)

	if _, err := io.Copy(dst, file); err != nil {
		dst.Close()
		writeError(w, http.StatusInternalServerError, "internal_error",
			fmt.Sprintf("failed to write temp file: %v", err))
		return
	}
	dst.Close()

	// Parse the sys file
	result, err := parser.ParseSysFile(tmpPath)
	if err != nil {
		writeError(w, http.StatusBadRequest, "parse_error",
			fmt.Sprintf("failed to parse sys file: %v", err))
		return
	}

	// Get file size
	fi, _ := os.Stat(tmpPath)
	fileSize := int64(0)
	if fi != nil {
		fileSize = fi.Size()
	}

	// Optionally store nodes
	storeNodes := r.FormValue("store_nodes") == "true"
	nodesCreated := 0
	if storeNodes {
		for _, entry := range result.Entries {
			node := &types.Node{
				Address:  "", // sysfile entries don't have IPs
				Name:     entry.LID,
				Type:     types.NodeType(entry.NodeType),
				Status:   types.StatusUnknown,
				Port:     23,
				LastSeen: time.Now(),
			}
			// Use LID as address placeholder
			node.Address = entry.LID
			if err := s.store.SaveNode(node); err != nil {
				log.Printf("api: failed to save node from sysfile: %v", err)
			} else {
				nodesCreated++
			}
		}
	}

	// Build entries response
	type entryResp struct {
		LID         string `json:"lid"`
		NodeType    string `json:"node_type"`
		Description string `json:"description"`
	}
	entries := make([]entryResp, 0, len(result.Entries))
	for _, e := range result.Entries {
		entries = append(entries, entryResp{
			LID:         e.LID,
			NodeType:    e.NodeType,
			Description: e.Description,
		})
	}

	writeJSON(w, http.StatusOK, map[string]interface{}{
		"filename":       header.Filename,
		"file_size_bytes": fileSize,
		"parsed_at":      time.Now().UTC().Format(time.RFC3339),
		"entries":        entries,
		"total_entries":  len(entries),
		"nodes_created":  nodesCreated,
	})
}

// ─── Handler 9: POST /api/v1/reports/generate ───────────────────

type generateReportRequest struct {
	NodeAddresses []string          `json:"node_addresses"`
	Format        string           `json:"format"`
	Template      string           `json:"template"`
	Options       *reportOptions   `json:"options"`
}

type reportOptions struct {
	LineLimit  *int        `json:"line_limit"`
	LineRange  *lineRange  `json:"line_range"`
	WrapWidth  *int        `json:"wrap_width"`
	IncludeRaw *bool       `json:"include_raw"`
}

type lineRange struct {
	Start int `json:"start"`
	End   int `json:"end"`
}

func (s *Server) generateReportHandler(w http.ResponseWriter, r *http.Request) {
	var req generateReportRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		writeError(w, http.StatusBadRequest, "validation_error", "invalid JSON body")
		return
	}

	// Validate required fields
	if len(req.NodeAddresses) == 0 {
		writeError(w, http.StatusBadRequest, "validation_error", "node_addresses is required")
		return
	}
	if req.Format == "" {
		writeError(w, http.StatusBadRequest, "validation_error", "format is required")
		return
	}

	// Validate format
	format := types.ReportFormat(strings.ToLower(req.Format))
	if format != types.FormatDOCX && format != types.FormatJSON {
		writeErrorDetails(w, http.StatusBadRequest, "validation_error",
			fmt.Sprintf("unsupported format: '%s'. Supported formats: docx, json", req.Format),
			map[string]string{"requested_format": req.Format})
		return
	}

	// Handle "*" wildcard — generate for all nodes with scan data
	addresses := req.NodeAddresses
	if len(addresses) == 1 && addresses[0] == "*" {
		nodes, err := s.store.ListNodes()
		if err != nil {
			writeError(w, http.StatusInternalServerError, "internal_error",
				fmt.Sprintf("failed to list nodes: %v", err))
			return
		}
		addresses = make([]string, 0, len(nodes))
		for _, n := range nodes {
			// Only include nodes that have IO points
			pts, _ := s.store.GetIOPoints(n.Address)
			if len(pts) > 0 {
				addresses = append(addresses, n.Address)
			}
		}
		if len(addresses) == 0 {
			writeError(w, http.StatusBadRequest, "validation_error",
				"no nodes with scan data available")
			return
		}
	}

	// Check all nodes have scan data
	var missingNodes []string
	for _, addr := range addresses {
		pts, err := s.store.GetIOPoints(addr)
		if err != nil || len(pts) == 0 {
			missingNodes = append(missingNodes, addr)
		}
	}
	if len(missingNodes) > 0 {
		writeErrorDetails(w, http.StatusBadRequest, "validation_error",
			fmt.Sprintf("no scan data available for nodes: %s. Run POST /api/v1/nodes/{addr}/scan first.",
				strings.Join(missingNodes, ", ")),
			map[string]interface{}{"missing_data_nodes": missingNodes})
		return
	}

	// Default template
	template := req.Template
	if template == "" {
		template = "default"
	}

	// Generate reports for each node
	var generatedReports []*types.Report
	for _, addr := range addresses {
		cfg := types.ReportConfig{
			NodeAddress: addr,
			Format:      format,
			Template:    template,
		}
		rpt, err := report.GenerateReport(cfg, s.store)
		if err != nil {
			log.Printf("api: failed to generate report for %s: %v", addr, err)
			// Create a failed report record
			failedRpt := &types.Report{
				ID:          fmt.Sprintf("rpt-%s", time.Now().Format("20060102-150405")),
				NodeAddress: addr,
				Format:      format,
				Template:    template,
				Status:      types.StatusFailed,
				CreatedAt:   time.Now().UTC().Format(time.RFC3339),
			}
			s.store.SaveReport(failedRpt)
			generatedReports = append(generatedReports, failedRpt)
			continue
		}
		generatedReports = append(generatedReports, rpt)
	}

	// Return first report as response (or summary if multiple)
	if len(generatedReports) == 1 {
		writeJSON(w, http.StatusOK, reportToAPI(generatedReports[0]))
	} else {
		apiReports := make([]apiReport, 0, len(generatedReports))
		for _, rpt := range generatedReports {
			apiReports = append(apiReports, reportToAPI(rpt))
		}
		writeJSON(w, http.StatusOK, map[string]interface{}{
			"reports":     apiReports,
			"total":       len(apiReports),
			"node_count":  len(addresses),
		})
	}
}

// ─── Handler 10: GET /api/v1/reports ─────────────────────────────

func (s *Server) listReportsHandler(w http.ResponseWriter, r *http.Request) {
	reports, err := s.store.ListReports()
	if err != nil {
		writeError(w, http.StatusInternalServerError, "internal_error",
			fmt.Sprintf("failed to list reports: %v", err))
		return
	}

	// AXON safety
	if reports == nil {
		reports = []*types.Report{}
	}

	apiReports := make([]apiReport, 0, len(reports))
	for _, rpt := range reports {
		apiReports = append(apiReports, reportToAPI(rpt))
	}

	writeJSON(w, http.StatusOK, map[string]interface{}{
		"reports": apiReports,
		"total":   len(apiReports),
		"limit":   50,
		"offset":  0,
	})
}

// ─── Handler 11: GET /api/v1/reports/{id} ────────────────────────

func (s *Server) getReportHandler(w http.ResponseWriter, r *http.Request) {
	id := r.PathValue("id")
	if id == "" {
		writeError(w, http.StatusBadRequest, "validation_error", "report id is required")
		return
	}

	rpt, err := s.store.GetReport(id)
	if err != nil {
		writeError(w, http.StatusNotFound, "not_found",
			fmt.Sprintf("report '%s' not found", id))
		return
	}

	// Check report status
	switch rpt.Status {
	case types.StatusPending, types.StatusGenerating:
		writeErrorDetails(w, http.StatusConflict, "report_not_ready",
			fmt.Sprintf("report '%s' is still generating", id),
			map[string]string{"status": string(rpt.Status)})
		return
	case types.StatusFailed:
		writeErrorDetails(w, http.StatusGone, "report_failed",
			fmt.Sprintf("report '%s' generation failed", id),
			map[string]string{"status": string(rpt.Status)})
		return
	}

	// Serve the file if it exists
	if rpt.FilePath != "" {
		if _, err := os.Stat(rpt.FilePath); err == nil {
			// Determine content type
			contentType := "application/octet-stream"
			switch rpt.Format {
			case types.FormatDOCX:
				contentType = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
			case types.FormatJSON:
				contentType = "application/json"
			}

			w.Header().Set("Content-Type", contentType)
			w.Header().Set("Content-Disposition",
				fmt.Sprintf(`attachment; filename="%s"`, filepath.Base(rpt.FilePath)))
			http.ServeFile(w, r, rpt.FilePath)
			return
		}
	}

	// Fallback: return report metadata as JSON
	writeJSON(w, http.StatusOK, reportToAPI(rpt))
}

// ─── Handler 12: POST /api/v1/bstool/errlog ─────────────────────

// bstoolErrLogRequest is the JSON request body for the bstool errlog endpoint.
type bstoolErrLogRequest struct {
	ServerName string `json:"server_name"`
	Timeout    int    `json:"timeout"`
	Mask       string `json:"mask"`
}

func (s *Server) handleBsToolErrLog(w http.ResponseWriter, r *http.Request) {
	// 1. Decode JSON body
	var req bstoolErrLogRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		writeError(w, http.StatusBadRequest, "INVALID_REQUEST", "Invalid JSON body")
		return
	}

	// 2. Validate server_name
	if req.ServerName == "" {
		writeError(w, http.StatusBadRequest, "INVALID_REQUEST", `"server_name" is required`)
		return
	}

	// 3. Validate timeout range
	if req.Timeout != 0 && (req.Timeout < 5 || req.Timeout > 120) {
		writeError(w, http.StatusBadRequest, "INVALID_TIMEOUT", `"timeout" must be between 5 and 120 seconds`)
		return
	}

	// 4. Build ErrLog options
	var opts []bstool.ErrLogOption
	if req.Timeout > 0 {
		opts = append(opts, bstool.WithRequestTimeout(time.Duration(req.Timeout)*time.Second))
	}
	if req.Mask != "" {
		opts = append(opts, bstool.WithMask(req.Mask))
	}

	// 5. Execute
	result, err := s.bstoolClient.ErrLog(r.Context(), req.ServerName, opts...)
	if err != nil {
		mapBstoolErrorToHTTP(w, err)
		return
	}

	// 6. Respond
	writeJSON(w, http.StatusOK, map[string]interface{}{
		"server_name": result.ServerName,
		"messages":    result.Messages,
		"count":       len(result.Messages),
		"duration_ms": result.Duration.Milliseconds(),
		"exit_code":   result.ExitCode,
		"timed_out":   result.TimedOut,
	})
}

// mapBstoolErrorToHTTP maps bstool sentinel errors to HTTP status codes and error codes.
func mapBstoolErrorToHTTP(w http.ResponseWriter, err error) {
	type coder interface {
		Code() string
	}

	code := "INTERNAL_ERROR"
	status := http.StatusInternalServerError

	if ce, ok := err.(coder); ok {
		switch ce.Code() {
		case "BSTOOL_NOT_FOUND":
			status = http.StatusServiceUnavailable // 503
			code = "BSTOOL_NOT_FOUND"
		case "UNSUPPORTED_PLATFORM":
			status = http.StatusNotImplemented // 501
			code = "UNSUPPORTED_PLATFORM"
		case "BSTOOL_TIMEOUT":
			status = http.StatusGatewayTimeout // 504
			code = "BSTOOL_TIMEOUT"
		case "BSTOOL_EXECUTION_FAILED":
			status = http.StatusBadGateway // 502
			code = "BSTOOL_EXECUTION_FAILED"
		case "INVALID_REQUEST":
			status = http.StatusBadRequest // 400
			code = "INVALID_REQUEST"
		}
	}

	writeError(w, status, code, err.Error())
}

// ─── Helpers ─────────────────────────────────────────────────────

// cond returns a if cond is true, otherwise b.
func cond(test bool, a, b string) string {
	if test {
		return a
	}
	return b
}
