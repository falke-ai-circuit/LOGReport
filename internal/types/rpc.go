package types

// RPCCounter represents a single RPC error counter entry.
type RPCCounter struct {
	Name  string `json:"name"`
	Value int    `json:"value"`
}

// RPCModule represents one RPC (Remote Procedure Call) module
// with its error counters.
type RPCModule struct {
	Position int          `json:"position"`
	Counters []RPCCounter `json:"counters"`
	Exists   bool         `json:"exists"`
}
