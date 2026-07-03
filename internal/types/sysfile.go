package types

// SysFileEntry represents a single parsed entry from a _sys configuration file.
// Format: ":e:hw:<hex_address>   <LID>   <config_file>"
// The HWAddr is the hardware address (hex) which serves as the token ID
// for FBC/RPC commands (e.g. "222" → "print from fbc io structure 2220000").
type SysFileEntry struct {
	HWAddr      string `json:"hw_addr"`      // Hardware address (hex, e.g. "222", "1a1") — this IS the token ID
	LID         string `json:"lid"`         // Logical ID (node name, e.g. "AP07_m2")
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
	LID        string `json:"lid"`
	Name       string `json:"name"`
	Type       string `json:"type"`
	Program    string `json:"program"`
	Parameters string `json:"parameters,omitempty"` // PARAMETERS= line (e.g. "-s AL02 -p 4321 -x password")
	SlotNum    int    `json:"slot_num"`
	IsFieldbus bool   `json:"is_fieldbus"`
}
