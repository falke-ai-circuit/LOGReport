package types

// SysFileEntry represents a single parsed entry from a _sys configuration file.
// Format: ":e:hw:<hex_address>   <LID>   <config_file>"
type SysFileEntry struct {
	LID         string `json:"lid"`
	NodeType    string `json:"node_type"`
	Description string `json:"description"`
}

// LIDMapping maps LID prefixes to their corresponding NodeType strings.
// This mirrors the Python SysFileParser.LID_TYPE_MAPPING dictionary.
var LIDMapping = map[string]string{
	"AD":   "DIA",
	"BD":   "DIA",
	"AC":   "CIS",
	"NW":   "NETWATCH",
	"AM":   "MAINT",
	"AL":   "LIS",
	"AP":   "PCS",
	"A1O":  "OPS",
	"B1O":  "OPS",
	"A1A":  "ALP",
	"B1A":  "ALP",
	"INFO": "HISTORY",
}

// SysFileNode represents a node extracted from a _sys file.
type SysFileNode struct {
	LID     string `json:"lid"`
	Name    string `json:"name"`
	Type    string `json:"type"`
	Program string `json:"program"`
}
