package types

import (
	"encoding/json"
	"testing"
)

func TestFBCToIOPoints(t *testing.T) {
	t.Run("converts modules to IO points", func(t *testing.T) {
		modules := []FBCModule{
			{
				Position: 0,
				Exists:   true,
				Channels: []FBCChannel{
					{Position: 5, Type: AI8, Sum: 8},
					{Position: 6, Type: BI8, Sum: 8},
				},
			},
			{
				Position: 1,
				Exists:   true,
				Channels: []FBCChannel{
					{Position: 1, Type: DI16, Sum: 16},
				},
			},
		}

		points := FBCToIOPoints("10.0.0.1", modules)

		if len(points) != 3 {
			t.Errorf("expected 3 points, got %d", len(points))
		}

		for _, p := range points {
			if p.NodeAddress != "10.0.0.1" {
				t.Errorf("expected NodeAddress 10.0.0.1, got %s", p.NodeAddress)
			}
			if p.ModuleType != ModuleFBC {
				t.Errorf("expected ModuleType fbc, got %s", p.ModuleType)
			}
		}
	})

	t.Run("skips non-existent modules", func(t *testing.T) {
		modules := []FBCModule{
			{
				Position: 0,
				Exists:   false,
				Channels: []FBCChannel{
					{Position: 5, Type: AI8, Sum: 8},
				},
			},
			{
				Position: 1,
				Exists:   true,
				Channels: []FBCChannel{
					{Position: 1, Type: DI16, Sum: 16},
				},
			},
		}

		points := FBCToIOPoints("10.0.0.1", modules)

		if len(points) != 1 {
			t.Errorf("expected 1 point (skipping non-existent), got %d", len(points))
		}
		if points[0].ModulePosition != 1 {
			t.Errorf("expected ModulePosition 1, got %d", points[0].ModulePosition)
		}
	})

	t.Run("empty modules returns nil", func(t *testing.T) {
		points := FBCToIOPoints("10.0.0.1", nil)
		if points != nil {
			t.Errorf("expected nil for nil input, got %v", points)
		}
	})

	t.Run("all non-existent returns empty", func(t *testing.T) {
		modules := []FBCModule{
			{Position: 0, Exists: false, Channels: []FBCChannel{{Position: 1, Type: AI8}}},
			{Position: 1, Exists: false, Channels: []FBCChannel{{Position: 1, Type: DI16}}},
		}
		points := FBCToIOPoints("10.0.0.1", modules)
		if len(points) != 0 {
			t.Errorf("expected 0 points, got %d", len(points))
		}
	})
}

func TestRPCToIOPoints(t *testing.T) {
	t.Run("converts modules to IO points", func(t *testing.T) {
		modules := []RPCModule{
			{
				Position: 0,
				Exists:   true,
				Counters: []RPCCounter{
					{Name: "ERR_TX", Value: 42},
					{Name: "ERR_RX", Value: 7},
				},
			},
			{
				Position: 1,
				Exists:   true,
				Counters: []RPCCounter{
					{Name: "TIMEOUT", Value: 3},
				},
			},
		}

		points := RPCToIOPoints("10.0.0.1", modules)

		if len(points) != 3 {
			t.Errorf("expected 3 points, got %d", len(points))
		}

		for _, p := range points {
			if p.NodeAddress != "10.0.0.1" {
				t.Errorf("expected NodeAddress 10.0.0.1, got %s", p.NodeAddress)
			}
			if p.ModuleType != ModuleRPC {
				t.Errorf("expected ModuleType rpc, got %s", p.ModuleType)
			}
			if p.ChannelPosition != 0 {
				t.Errorf("expected ChannelPosition 0 for RPC, got %d", p.ChannelPosition)
			}
		}

		// Verify specific counter
		found := false
		for _, p := range points {
			if p.CounterName == "ERR_TX" && p.CounterValue == 42 {
				found = true
				break
			}
		}
		if !found {
			t.Error("ERR_TX counter with value 42 not found")
		}
	})

	t.Run("skips non-existent modules", func(t *testing.T) {
		modules := []RPCModule{
			{
				Position: 0,
				Exists:   false,
				Counters: []RPCCounter{
					{Name: "ERR_TX", Value: 42},
				},
			},
			{
				Position: 1,
				Exists:   true,
				Counters: []RPCCounter{
					{Name: "TIMEOUT", Value: 3},
				},
			},
		}

		points := RPCToIOPoints("10.0.0.1", modules)

		if len(points) != 1 {
			t.Errorf("expected 1 point, got %d", len(points))
		}
		if points[0].ModulePosition != 1 {
			t.Errorf("expected ModulePosition 1, got %d", points[0].ModulePosition)
		}
	})

	t.Run("empty modules returns nil", func(t *testing.T) {
		points := RPCToIOPoints("10.0.0.1", nil)
		if points != nil {
			t.Errorf("expected nil for nil input, got %v", points)
		}
	})

	t.Run("all non-existent returns empty", func(t *testing.T) {
		modules := []RPCModule{
			{Position: 0, Exists: false, Counters: []RPCCounter{{Name: "X", Value: 1}}},
			{Position: 1, Exists: false, Counters: []RPCCounter{{Name: "Y", Value: 2}}},
		}
		points := RPCToIOPoints("10.0.0.1", modules)
		if len(points) != 0 {
			t.Errorf("expected 0 points, got %d", len(points))
		}
	})
}

func TestIOPointJSONRoundTrip(t *testing.T) {
	point := IOPoint{
		NodeAddress:     "10.0.0.1",
		ModulePosition:  0,
		ChannelPosition: 5,
		ChannelType:     AI8,
		ModuleType:      ModuleFBC,
	}

	data, err := json.Marshal(point)
	if err != nil {
		t.Fatalf("marshal: %v", err)
	}

	var decoded IOPoint
	if err := json.Unmarshal(data, &decoded); err != nil {
		t.Fatalf("unmarshal: %v", err)
	}

	if decoded.NodeAddress != point.NodeAddress {
		t.Errorf("NodeAddress: got %q, want %q", decoded.NodeAddress, point.NodeAddress)
	}
	if decoded.ModulePosition != point.ModulePosition {
		t.Errorf("ModulePosition: got %d, want %d", decoded.ModulePosition, point.ModulePosition)
	}
	if decoded.ChannelPosition != point.ChannelPosition {
		t.Errorf("ChannelPosition: got %d, want %d", decoded.ChannelPosition, point.ChannelPosition)
	}
	if decoded.ChannelType != point.ChannelType {
		t.Errorf("ChannelType: got %q, want %q", decoded.ChannelType, point.ChannelType)
	}
	if decoded.ModuleType != point.ModuleType {
		t.Errorf("ModuleType: got %q, want %q", decoded.ModuleType, point.ModuleType)
	}
}

func TestIOPointRPCJSONRoundTrip(t *testing.T) {
	point := IOPoint{
		NodeAddress:    "10.0.0.1",
		ModulePosition: 0,
		ModuleType:     ModuleRPC,
		CounterName:    "ERR_TX",
		CounterValue:   42,
	}

	data, err := json.Marshal(point)
	if err != nil {
		t.Fatalf("marshal: %v", err)
	}

	var decoded IOPoint
	if err := json.Unmarshal(data, &decoded); err != nil {
		t.Fatalf("unmarshal: %v", err)
	}

	if decoded.CounterName != "ERR_TX" {
		t.Errorf("CounterName: got %q, want ERR_TX", decoded.CounterName)
	}
	if decoded.CounterValue != 42 {
		t.Errorf("CounterValue: got %d, want 42", decoded.CounterValue)
	}
}

func TestModuleTypeConstants(t *testing.T) {
	if ModuleFBC != "fbc" {
		t.Errorf("ModuleFBC: got %q, want fbc", ModuleFBC)
	}
	if ModuleRPC != "rpc" {
		t.Errorf("ModuleRPC: got %q, want rpc", ModuleRPC)
	}
}
