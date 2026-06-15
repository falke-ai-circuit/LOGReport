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
}
