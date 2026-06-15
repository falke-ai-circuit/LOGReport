package types

import (
	"encoding/json"
	"testing"
	"time"
)

func TestNodeJSONRoundTrip(t *testing.T) {
	now := time.Date(2026, 6, 15, 12, 0, 0, 0, time.UTC)
	node := Node{
		Address:  "192.168.1.40",
		Name:     "AL01",
		Type:     LIS,
		Status:   StatusConnected,
		TokenID:  "501",
		Port:     23,
		Username: "engineer",
		Password: "secret",
		LastSeen: now,
	}

	data, err := json.Marshal(node)
	if err != nil {
		t.Fatalf("marshal: %v", err)
	}

	var decoded Node
	if err := json.Unmarshal(data, &decoded); err != nil {
		t.Fatalf("unmarshal: %v", err)
	}

	if decoded.Address != node.Address {
		t.Errorf("Address: got %q, want %q", decoded.Address, node.Address)
	}
	if decoded.Name != node.Name {
		t.Errorf("Name: got %q, want %q", decoded.Name, node.Name)
	}
	if decoded.Type != node.Type {
		t.Errorf("Type: got %q, want %q", decoded.Type, node.Type)
	}
	if decoded.Status != node.Status {
		t.Errorf("Status: got %q, want %q", decoded.Status, node.Status)
	}
	if decoded.TokenID != node.TokenID {
		t.Errorf("TokenID: got %q, want %q", decoded.TokenID, node.TokenID)
	}
	if decoded.Port != node.Port {
		t.Errorf("Port: got %d, want %d", decoded.Port, node.Port)
	}
	if decoded.Username != node.Username {
		t.Errorf("Username: got %q, want %q", decoded.Username, node.Username)
	}
	if decoded.Password != node.Password {
		t.Errorf("Password: got %q, want %q", decoded.Password, node.Password)
	}
	if !decoded.LastSeen.Equal(now) {
		t.Errorf("LastSeen: got %v, want %v", decoded.LastSeen, now)
	}
}

func TestNodeJSONSnakeCase(t *testing.T) {
	node := Node{
		Address: "192.168.1.100",
		Name:    "AP01",
		Type:    PCS,
		Status:  StatusDisconnected,
		TokenID: "262",
		Port:    23,
	}

	data, err := json.Marshal(node)
	if err != nil {
		t.Fatalf("marshal: %v", err)
	}

	var raw map[string]interface{}
	if err := json.Unmarshal(data, &raw); err != nil {
		t.Fatalf("unmarshal to map: %v", err)
	}

	// Verify all keys are snake_case
	expectedKeys := []string{"address", "name", "type", "status", "token_id", "port", "last_seen"}
	for _, k := range expectedKeys {
		if _, ok := raw[k]; !ok {
			t.Errorf("missing key %q in JSON output", k)
		}
	}

	// omitempty fields should be absent when empty
	if _, ok := raw["username"]; ok {
		t.Error("username should be omitted when empty")
	}
	if _, ok := raw["password"]; ok {
		t.Error("password should be omitted when empty")
	}
}

func TestNodeTypeConstants(t *testing.T) {
	types := []NodeType{ACN, ACN_S, DIA, CIS, NETWATCH, MAINT, LIS, PCS, OPS, ALP, HISTORY}
	for _, nt := range types {
		if nt == "" {
			t.Error("NodeType constant must not be empty")
		}
	}
}

func TestNodeStatusConstants(t *testing.T) {
	statuses := []NodeStatus{StatusUnknown, StatusConnected, StatusDisconnected, StatusError}
	for _, s := range statuses {
		if s == "" {
			t.Error("NodeStatus constant must not be empty")
		}
	}
}
