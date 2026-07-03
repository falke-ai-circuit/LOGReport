// Package types defines core data structures for LOGReport.
// These types model Valmet DNA nodes, FBC/RPC modules, sysfile entries,
// and report configuration — the foundational domain objects shared
// across the telnet client, parsers, store, and report generator.
package types

import "time"

// NodeType identifies the kind of Valmet DNA node.
type NodeType string

const (
	ACN      NodeType = "ACN"      // Application Control Node
	ACN_S    NodeType = "ACN_S"    // Application Control Node (Secondary)
	DIA      NodeType = "DIA"      // Diagnostics / DIA node
	CIS      NodeType = "CIS"      // Control Information Server
	NETWATCH NodeType = "NETWATCH" // NetWatch monitoring
	MAINT    NodeType = "MAINT"    // Maintenance Server
	LIS      NodeType = "LIS"      // Local Information Server
	PCS      NodeType = "PCS"      // Process Control Station
	OPS      NodeType = "OPS"      // Operator Station
	ALP      NodeType = "ALP"      // Alarm Printer
	HISTORY  NodeType = "HISTORY"  // History Server
)

// NodeStatus represents the connection state of a node.
type NodeStatus string

const (
	StatusUnknown      NodeStatus = "unknown"
	StatusConnected    NodeStatus = "connected"
	StatusDisconnected NodeStatus = "disconnected"
	StatusError        NodeStatus = "error"
)

// Node represents a Valmet DNA node with its connection details.
type Node struct {
	Address  string     `json:"address"`
	Name     string     `json:"name"`
	Type     NodeType   `json:"type"`
	Status   NodeStatus `json:"status"`
	TokenID  string     `json:"token_id"`
	Port     int        `json:"port"`
	Username string     `json:"username,omitempty"`
	Password string     `json:"password,omitempty"`
	LastSeen time.Time  `json:"last_seen"`
	Tokens   []Token    `json:"tokens,omitempty"`
}

// ─── Token / NodeConfig / TreeNode ────────────────────────────────

// TokenType identifies the kind of token (FBC, RPC, LOG, LIS, FTP).
type TokenType string

const (
	TokenFBC TokenType = "FBC"
	TokenRPC TokenType = "RPC"
	TokenLOG TokenType = "LOG"
	TokenLIS TokenType = "LIS"
	TokenFTP TokenType = "FTP"
)

// Token represents a single token entry from nodes.json.
type Token struct {
	TokenID   string    `json:"token_id"`
	TokenType TokenType `json:"token_type"`
	Port      int       `json:"port"`
	Protocol  string    `json:"protocol"` // "telnet" or "ftp"
}

// NodeConfig represents the full nodes.json entry (node + all tokens).
type NodeConfig struct {
	Name          string  `json:"name"`
	IPAddress     string  `json:"ip_address"`
	Tokens        []Token `json:"tokens"`
	LISDiagParams string  `json:"lisdiag_params,omitempty"` // PARAMETERS from .sys LISDiag slot (-p port -x password)
}

// TreeNode is the hierarchical structure for the frontend node tree.
type TreeNode struct {
	Name       string     `json:"name"`
	Type       string     `json:"type"` // "root", "node", "group", "token", "file"
	IP         string     `json:"ip,omitempty"`
	TokenID    string     `json:"token_id,omitempty"`
	Port       int        `json:"port,omitempty"`
	Protocol   string     `json:"protocol,omitempty"`
	Status     string     `json:"status,omitempty"` // "idle", "connected", "error"
	FilePath   string     `json:"file_path,omitempty"`   // absolute path for file-type nodes
	FileName   string     `json:"file_name,omitempty"`   // base filename for file-type nodes
	SectionType string    `json:"section_type,omitempty"` // "FBC", "RPC", "LOG", "LIS"
	LineCount  int        `json:"line_count,omitempty"`  // line count for file-type nodes (color indicator)
	Children   []TreeNode `json:"children,omitempty"`
}
