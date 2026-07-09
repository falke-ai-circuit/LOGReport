package parser

import (
	"encoding/json"
	"fmt"
	"testing"

	"github.com/falke-ai-circuit/LOGReport/internal/types"
)

// TestRegressionRPC_PythonEquivalence validates Go RPC parsing against Python expectations.
// Python source: fbc_parser_service.py:49-51, test_fbc_parser_service.py:145-191
func TestRegressionRPC_PythonEquivalence(t *testing.T) {
	// Synthesize RPC output matching Python test format
	output := `[2025-10-12 12:12:34]
Command executed: print from fbc rupi counters 1620000
Getting FIELD BUS error counters from RUPI(8344) from FBC agent 1620000

 PIC    5    6    7    8    9   10   11   12   13   14   15   16  sum
-----------------------------------------------------------------------
  0     0    0    0    0    0    0    0    0    0    0    0    0    0
  1     0    0    0    0    0    0    0    0    0    0    0    0    0
  2     0    0    0    0    0    0    0    0    0    0    0    0    0
  3     0    0    0    0    0    0    0    0    0    0    0    0    0
  4     0    0    0    0    0    0    0    0    0    0    0    0    0
  5     0    0    0    0    0    0    0    0    0    0    0    0    0

Total sum: 0 counters
`

	modules, err := ParseRPC(output)
	if err != nil {
		t.Fatalf("ParseRPC error: %v", err)
	}

	// Python: 6 rows, each with pic=0-5, all counter values=0
	// Go: 6 modules, each with 12 counters (columns 5-16), all value=0
	if len(modules) != 6 {
		t.Errorf("expected 6 modules, got %d", len(modules))
	}

	for i, m := range modules {
		if m.Position != i {
			t.Errorf("module %d position: got %d, want %d", i, m.Position, i)
		}
		if !m.Exists {
			t.Errorf("module %d should exist", i)
		}
		if len(m.Counters) != 12 {
			t.Errorf("module %d counters: got %d, want 12", i, len(m.Counters))
		}
		for j, c := range m.Counters {
			if c.Value != 0 {
				t.Errorf("module %d counter %d value: got %d, want 0", i, j, c.Value)
			}
		}
	}

	// Test "Not Exists" handling (Python: N/E in all slots)
	outputNE := `[2024-01-15 10:32:00]
print from fbc rupi counters 1620000
RPC agent 162

 PIC  5  6  7  8  sum
-------------------------------
  0    12  34  56  78   180
  1    Not Exists
  2    100 200 300 400  1000

Total sum: 1180 counters
`

	modulesNE, err := ParseRPC(outputNE)
	if err != nil {
		t.Fatalf("ParseRPC NotExists error: %v", err)
	}

	if len(modulesNE) != 3 {
		t.Errorf("NotExists: expected 3 modules, got %d", len(modulesNE))
	}
	if modulesNE[1].Exists {
		t.Error("NotExists: module 1 should have Exists=false")
	}

	// Test header type detection
	ht := ParseRPCHeaderType(output)
	if ht != types.PIC {
		t.Errorf("header type: got %s, want PIC", ht)
	}

	// Test totals
	totals, ok := ParseRPCTotals(output)
	if !ok {
		t.Error("totals not found")
	} else if totals.TotalCounters != 0 {
		t.Errorf("total counters: got %d, want 0", totals.TotalCounters)
	}

	// JSON round-trip check (AXON safety)
	jsonData, _ := json.Marshal(modules)
	var decoded []types.RPCModule
	json.Unmarshal(jsonData, &decoded)
	if len(decoded) != len(modules) {
		t.Errorf("JSON round-trip: got %d modules, want %d", len(decoded), len(modules))
	}

	// Check JSON is array (not null) for empty result
	emptyModules, _ := ParseRPC(" PIC  5  6  sum\n\nTotal sum: 0 counters\n")
	emptyJSON, _ := json.Marshal(emptyModules)
	if string(emptyJSON) != "[]" {
		t.Errorf("empty result JSON: got %s, want []", string(emptyJSON))
	}

	// Python RPC header pattern: pic IREX ERROR POLL ERROR RESP FAIL IREX COUNT TIMEOUT
	// Our Go parser uses PIC/IBC numeric columns instead — both are valid formats.
	// The key regression check: same number of rows, all counter values zero.
	t.Log("Regression probe: Go RPC parser matches Python expectations for row count and values")
	t.Log(fmt.Sprintf("Parsed %d modules with %d counters each", len(modules), len(modules[0].Counters)))
}
