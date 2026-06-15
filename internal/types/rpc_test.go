package types

import (
	"encoding/json"
	"testing"
)

func TestRPCModuleJSONRoundTrip(t *testing.T) {
	mod := RPCModule{
		Position: 0,
		Counters: []RPCCounter{
			{Name: "IREX ERROR", Value: 0},
			{Name: "POLL ERROR", Value: 2},
			{Name: "RESP FAIL", Value: 1},
			{Name: "IREX COUNT", Value: 150},
			{Name: "TIMEOUT", Value: 3},
		},
		Exists: true,
	}

	data, err := json.Marshal(mod)
	if err != nil {
		t.Fatalf("marshal: %v", err)
	}

	var decoded RPCModule
	if err := json.Unmarshal(data, &decoded); err != nil {
		t.Fatalf("unmarshal: %v", err)
	}

	if decoded.Position != mod.Position {
		t.Errorf("Position: got %d, want %d", decoded.Position, mod.Position)
	}
	if len(decoded.Counters) != len(mod.Counters) {
		t.Errorf("Counters len: got %d, want %d", len(decoded.Counters), len(mod.Counters))
	}
	if decoded.Exists != mod.Exists {
		t.Errorf("Exists: got %v, want %v", decoded.Exists, mod.Exists)
	}

	for i, c := range decoded.Counters {
		if c.Name != mod.Counters[i].Name {
			t.Errorf("Counter[%d].Name: got %q, want %q", i, c.Name, mod.Counters[i].Name)
		}
		if c.Value != mod.Counters[i].Value {
			t.Errorf("Counter[%d].Value: got %d, want %d", i, c.Value, mod.Counters[i].Value)
		}
	}
}

func TestRPCModuleNilSliceSafety(t *testing.T) {
	// nil slice → JSON null (AXON gotcha)
	modNil := RPCModule{
		Position: 1,
		Counters: nil,
		Exists:   true,
	}
	dataNil, err := json.Marshal(modNil)
	if err != nil {
		t.Fatalf("marshal nil: %v", err)
	}
	var rawNil map[string]interface{}
	if err := json.Unmarshal(dataNil, &rawNil); err != nil {
		t.Fatalf("unmarshal nil: %v", err)
	}
	ctNil := rawNil["counters"]
	if ctNil != nil {
		t.Errorf("nil slice should marshal to null, got %v", ctNil)
	}

	// empty initialized slice → JSON [] (correct)
	modEmpty := RPCModule{
		Position: 1,
		Counters: []RPCCounter{},
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
	ctEmpty := rawEmpty["counters"]
	arr, isArr := ctEmpty.([]interface{})
	if !isArr {
		t.Errorf("empty initialized slice should marshal to [], got %T: %v", ctEmpty, ctEmpty)
	}
	if len(arr) != 0 {
		t.Errorf("empty slice array should have 0 elements, got %d", len(arr))
	}
}

func TestRPCCounterJSONRoundTrip(t *testing.T) {
	ct := RPCCounter{
		Name:  "IREX ERROR",
		Value: 42,
	}

	data, err := json.Marshal(ct)
	if err != nil {
		t.Fatalf("marshal: %v", err)
	}

	var decoded RPCCounter
	if err := json.Unmarshal(data, &decoded); err != nil {
		t.Fatalf("unmarshal: %v", err)
	}

	if decoded.Name != ct.Name {
		t.Errorf("Name: got %q, want %q", decoded.Name, ct.Name)
	}
	if decoded.Value != ct.Value {
		t.Errorf("Value: got %d, want %d", decoded.Value, ct.Value)
	}
}
