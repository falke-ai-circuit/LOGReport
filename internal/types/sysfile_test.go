package types

import (
	"encoding/json"
	"testing"
)

func TestSysFileEntryJSONRoundTrip(t *testing.T) {
	entry := SysFileEntry{
		LID:         "AL01",
		NodeType:    "LIS",
		Description: "Local Information Server node 01",
	}

	data, err := json.Marshal(entry)
	if err != nil {
		t.Fatalf("marshal: %v", err)
	}

	var decoded SysFileEntry
	if err := json.Unmarshal(data, &decoded); err != nil {
		t.Fatalf("unmarshal: %v", err)
	}

	if decoded.LID != entry.LID {
		t.Errorf("LID: got %q, want %q", decoded.LID, entry.LID)
	}
	if decoded.NodeType != entry.NodeType {
		t.Errorf("NodeType: got %q, want %q", decoded.NodeType, entry.NodeType)
	}
	if decoded.Description != entry.Description {
		t.Errorf("Description: got %q, want %q", decoded.Description, entry.Description)
	}
}

func TestLIDMappingCoverage(t *testing.T) {
	// Verify all expected LID prefixes from Python source are present
	expected := map[string]string{
		"AD":   "DIA",
		"BD":   "DIA",
		"AC":   "CIS",
		"NW":   "NETWATCH",
		"AM":   "MAINT",
		"AL":   "LIS",
		"BL":   "LIS",
		"AP":   "PCS",
		"BP":   "PCS",
		"A1O":  "OPS",
		"B1O":  "OPS",
		"A1A":  "ALP",
		"B1A":  "ALP",
		"INFO": "HISTORY",
	}

	for prefix, expectedType := range expected {
		got, ok := LIDMapping[prefix]
		if !ok {
			t.Errorf("LIDMapping missing prefix %q", prefix)
			continue
		}
		if got != expectedType {
			t.Errorf("LIDMapping[%q]: got %q, want %q", prefix, got, expectedType)
		}
	}

	// Verify no extra entries
	if len(LIDMapping) != len(expected) {
		t.Errorf("LIDMapping has %d entries, expected %d", len(LIDMapping), len(expected))
	}
}

func TestSysFileNodeJSONRoundTrip(t *testing.T) {
	node := SysFileNode{
		LID:     "AP01_main",
		Name:    "AP01",
		Type:    "PCS",
		Program: "pxe:sys-csg2",
	}

	data, err := json.Marshal(node)
	if err != nil {
		t.Fatalf("marshal: %v", err)
	}

	var decoded SysFileNode
	if err := json.Unmarshal(data, &decoded); err != nil {
		t.Fatalf("unmarshal: %v", err)
	}

	if decoded.LID != node.LID {
		t.Errorf("LID: got %q, want %q", decoded.LID, node.LID)
	}
	if decoded.Name != node.Name {
		t.Errorf("Name: got %q, want %q", decoded.Name, node.Name)
	}
	if decoded.Type != node.Type {
		t.Errorf("Type: got %q, want %q", decoded.Type, node.Type)
	}
	if decoded.Program != node.Program {
		t.Errorf("Program: got %q, want %q", decoded.Program, node.Program)
	}
}
