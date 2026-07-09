package types

import (
	"encoding/json"
	"testing"
)

func TestFBCModuleJSONRoundTrip(t *testing.T) {
	mod := FBCModule{
		Position: 0,
		Channels: []FBCChannel{
			{Position: 5, Type: AI8, Sum: 8},
			{Position: 6, Type: BI8, Sum: 8},
			{Position: 7, Type: BO8, Sum: 8},
		},
		Exists: true,
	}

	data, err := json.Marshal(mod)
	if err != nil {
		t.Fatalf("marshal: %v", err)
	}

	var decoded FBCModule
	if err := json.Unmarshal(data, &decoded); err != nil {
		t.Fatalf("unmarshal: %v", err)
	}

	if decoded.Position != mod.Position {
		t.Errorf("Position: got %d, want %d", decoded.Position, mod.Position)
	}
	if len(decoded.Channels) != len(mod.Channels) {
		t.Errorf("Channels len: got %d, want %d", len(decoded.Channels), len(mod.Channels))
	}
	if decoded.Exists != mod.Exists {
		t.Errorf("Exists: got %v, want %v", decoded.Exists, mod.Exists)
	}
}

func TestFBCModuleNilSliceSafety(t *testing.T) {
	// AXON gotcha: Go nil slice marshals to JSON null, not [].
	// We must ensure empty slices are initialized as []FBCChannel{} not nil.

	// Case 1: nil slice (bad — produces null)
	modNil := FBCModule{
		Position: 1,
		Channels: nil,
		Exists:   true,
	}
	dataNil, err := json.Marshal(modNil)
	if err != nil {
		t.Fatalf("marshal nil: %v", err)
	}
	if string(dataNil) == "" {
		t.Fatal("nil slice marshal produced empty output")
	}
	// Verify it contains "null" for channels (the gotcha)
	var rawNil map[string]interface{}
	if err := json.Unmarshal(dataNil, &rawNil); err != nil {
		t.Fatalf("unmarshal nil: %v", err)
	}
	chNil, ok := rawNil["channels"]
	if !ok {
		t.Fatal("channels key missing from nil slice output")
	}
	if chNil != nil {
		t.Errorf("nil slice should marshal to null, got %v (this is the AXON gotcha)", chNil)
	}

	// Case 2: empty initialized slice (good — produces [])
	modEmpty := FBCModule{
		Position: 1,
		Channels: []FBCChannel{},
		Exists:   true,
	}
	dataEmpty, err := json.Marshal(modEmpty)
	if err != nil {
		t.Fatalf("marshal empty: %v", err)
	}
	var rawEmpty map[string]interface{}
	if err := json.Unmarshal(dataEmpty, &rawEmpty); err != nil {
		t.Fatalf("unmarshal empty: %v", err)
	}
	chEmpty, ok := rawEmpty["channels"]
	if !ok {
		t.Fatal("channels key missing from empty slice output")
	}
	// Should be an empty array, not null
	arr, isArr := chEmpty.([]interface{})
	if !isArr {
		t.Errorf("empty initialized slice should marshal to [], got %T: %v", chEmpty, chEmpty)
	}
	if len(arr) != 0 {
		t.Errorf("empty slice array should have 0 elements, got %d", len(arr))
	}
}

func TestFBCChannelJSONRoundTrip(t *testing.T) {
	ch := FBCChannel{
		Position: 5,
		Type:     AI8,
		Sum:      8,
	}

	data, err := json.Marshal(ch)
	if err != nil {
		t.Fatalf("marshal: %v", err)
	}

	var decoded FBCChannel
	if err := json.Unmarshal(data, &decoded); err != nil {
		t.Fatalf("unmarshal: %v", err)
	}

	if decoded.Position != ch.Position {
		t.Errorf("Position: got %d, want %d", decoded.Position, ch.Position)
	}
	if decoded.Type != ch.Type {
		t.Errorf("Type: got %q, want %q", decoded.Type, ch.Type)
	}
	if decoded.Sum != ch.Sum {
		t.Errorf("Sum: got %d, want %d", decoded.Sum, ch.Sum)
	}
}

func TestChannelTypeConstants(t *testing.T) {
	types := []ChannelType{
		AI8, AO4, AO8, DI16, DO16, BI8, BI8N, BO8,
		TI6, TO6, PI4, PO4, SI8, SO8, CI4, CO4,
		RI4, RO4, II4, IO4, NotExists,
	}
	for _, ct := range types {
		if ct == "" {
			t.Error("ChannelType constant must not be empty")
		}
	}
}

func TestHeaderTypeConstants(t *testing.T) {
	if PIC == "" {
		t.Error("PIC HeaderType must not be empty")
	}
	if IBC == "" {
		t.Error("IBC HeaderType must not be empty")
	}
}

func TestNotExistsChannelType(t *testing.T) {
	// Verify NotExists is "N/E" as expected by the Python parser
	if NotExists != "N/E" {
		t.Errorf("NotExists: got %q, want %q", NotExists, "N/E")
	}
}
