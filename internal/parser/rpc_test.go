package parser

import (
	"os"
	"testing"

	"github.com/falke-ai-circuit/LOGReport/internal/types"
)

// readTestdata reads a testdata fixture file.
func readTestdata(t *testing.T, name string) string {
	t.Helper()
	data, err := os.ReadFile("testdata/" + name)
	if err != nil {
		t.Fatalf("failed to read testdata/%s: %v", name, err)
	}
	return string(data)
}

// TestParseRPC_PICHeader validates parsing of PIC-format RPC output.
func TestParseRPC_PICHeader(t *testing.T) {
	output := readTestdata(t, "rpc_sample_pic.txt")

	modules, err := ParseRPC(output)
	if err != nil {
		t.Fatalf("ParseRPC: unexpected error: %v", err)
	}

	if len(modules) != 4 {
		t.Fatalf("expected 4 modules, got %d", len(modules))
	}

	// Module 0
	m0 := modules[0]
	if m0.Position != 0 {
		t.Errorf("module 0 position: got %d, want 0", m0.Position)
	}
	if !m0.Exists {
		t.Error("module 0 should exist")
	}
	if len(m0.Counters) != 4 {
		t.Errorf("module 0 counters: got %d, want 4", len(m0.Counters))
	}
	if m0.Counters[0].Name != "5" || m0.Counters[0].Value != 12 {
		t.Errorf("module 0 counter 0: name=%s value=%d, want name=5 value=12", m0.Counters[0].Name, m0.Counters[0].Value)
	}
	if m0.Counters[1].Name != "6" || m0.Counters[1].Value != 34 {
		t.Errorf("module 0 counter 1: name=%s value=%d, want name=6 value=34", m0.Counters[1].Name, m0.Counters[1].Value)
	}
	if m0.Counters[2].Name != "7" || m0.Counters[2].Value != 56 {
		t.Errorf("module 0 counter 2: name=%s value=%d, want name=7 value=56", m0.Counters[2].Name, m0.Counters[2].Value)
	}
	if m0.Counters[3].Name != "8" || m0.Counters[3].Value != 78 {
		t.Errorf("module 0 counter 3: name=%s value=%d, want name=8 value=78", m0.Counters[3].Name, m0.Counters[3].Value)
	}

	// Module 3 — verify larger values
	m3 := modules[3]
	if m3.Position != 3 {
		t.Errorf("module 3 position: got %d, want 3", m3.Position)
	}
	if m3.Counters[0].Value != 100 {
		t.Errorf("module 3 counter 0 value: got %d, want 100", m3.Counters[0].Value)
	}
	if m3.Counters[3].Value != 400 {
		t.Errorf("module 3 counter 3 value: got %d, want 400", m3.Counters[3].Value)
	}
}

// TestParseRPC_IBCHeader validates parsing of IBC-format RPC output.
func TestParseRPC_IBCHeader(t *testing.T) {
	output := readTestdata(t, "rpc_sample_ibc.txt")

	modules, err := ParseRPC(output)
	if err != nil {
		t.Fatalf("ParseRPC: unexpected error: %v", err)
	}

	if len(modules) != 3 {
		t.Fatalf("expected 3 modules, got %d", len(modules))
	}

	// Verify header type detection
	ht := ParseRPCHeaderType(output)
	if ht != types.IBC {
		t.Errorf("header type: got %s, want IBC", ht)
	}

	// Module 0 — IBC format
	m0 := modules[0]
	if m0.Position != 0 {
		t.Errorf("module 0 position: got %d, want 0", m0.Position)
	}
	if len(m0.Counters) != 4 {
		t.Errorf("module 0 counters: got %d, want 4", len(m0.Counters))
	}
	if m0.Counters[0].Name != "0" || m0.Counters[0].Value != 42 {
		t.Errorf("module 0 counter 0: name=%s value=%d, want name=0 value=42", m0.Counters[0].Name, m0.Counters[0].Value)
	}
	if m0.Counters[1].Name != "1" || m0.Counters[1].Value != 17 {
		t.Errorf("module 0 counter 1: name=%s value=%d, want name=1 value=17", m0.Counters[1].Name, m0.Counters[1].Value)
	}
	if m0.Counters[2].Name != "2" || m0.Counters[2].Value != 88 {
		t.Errorf("module 0 counter 2: name=%s value=%d, want name=2 value=88", m0.Counters[2].Name, m0.Counters[2].Value)
	}
	if m0.Counters[3].Name != "3" || m0.Counters[3].Value != 55 {
		t.Errorf("module 0 counter 3: name=%s value=%d, want name=3 value=55", m0.Counters[3].Name, m0.Counters[3].Value)
	}

	// Module 1
	m1 := modules[1]
	if m1.Counters[1].Value != 99 {
		t.Errorf("module 1 counter 1 value: got %d, want 99", m1.Counters[1].Value)
	}
}

// TestParseRPC_NotExists validates "Not Exists" row handling.
func TestParseRPC_NotExists(t *testing.T) {
	output := readTestdata(t, "rpc_sample_notexists.txt")

	modules, err := ParseRPC(output)
	if err != nil {
		t.Fatalf("ParseRPC: unexpected error: %v", err)
	}

	if len(modules) != 4 {
		t.Fatalf("expected 4 modules, got %d", len(modules))
	}

	// Module 1 should be "Not Exists"
	m1 := modules[1]
	if m1.Position != 1 {
		t.Errorf("not-exists module position: got %d, want 1", m1.Position)
	}
	if m1.Exists {
		t.Error("not-exists module should have Exists=false")
	}
	if len(m1.Counters) != 0 {
		t.Errorf("not-exists module should have 0 counters, got %d", len(m1.Counters))
	}
	// AXON safety: counters must be empty slice, not nil
	if m1.Counters == nil {
		t.Error("not-exists module counters must be empty slice ([]RPCCounter{}), not nil (AXON gotcha)")
	}

	// Module 2 should also be "Not Exists"
	m2 := modules[2]
	if m2.Position != 2 {
		t.Errorf("not-exists module 2 position: got %d, want 2", m2.Position)
	}
	if m2.Exists {
		t.Error("not-exists module 2 should have Exists=false")
	}

	// Module 0 and 3 should exist normally
	if !modules[0].Exists {
		t.Error("module 0 should exist")
	}
	if !modules[3].Exists {
		t.Error("module 3 should exist")
	}
}

// TestParseRPC_EmptyOutput validates that empty/missing-header output returns error.
func TestParseRPC_EmptyOutput(t *testing.T) {
	// Empty string — no header, should error
	_, err := ParseRPC("")
	if err == nil {
		t.Error("expected error for empty output, got nil")
	}

	// Output with no PIC/IBC header
	output := `[2024-01-15 10:30:00]
Some random content
No table here
`
	_, err = ParseRPC(output)
	if err == nil {
		t.Error("expected error for output without PIC/IBC header, got nil")
	}
}

// TestParseRPC_MalformedHeader validates error on malformed header.
func TestParseRPC_MalformedHeader(t *testing.T) {
	output := readTestdata(t, "rpc_sample_malformed.txt")

	_, err := ParseRPC(output)
	if err == nil {
		t.Fatal("expected error for malformed header (XYZ instead of PIC/IBC), got nil")
	}
}

// TestParseRPC_MissingCounterColumns validates error when header has no content after PIC.
func TestParseRPC_MissingCounterColumns(t *testing.T) {
	// Header with just "PIC" and no column names — should fail
	output := `[2024-01-15 10:30:00]
PIC
-------------------------------
  0    12   1
`

	_, err := ParseRPC(output)
	if err == nil {
		t.Fatal("expected error for header with no counter columns, got nil")
	}
}

// TestParseRPC_EncodingEdgeCases validates handling of extra whitespace and edge cases.
func TestParseRPC_EncodingEdgeCases(t *testing.T) {
	// Extra whitespace between columns
	output := `[2024-01-15 10:30:00]
 PIC    5    6    7    8  sum
--------------------------------
  0    12   34   56   78   180

Total sum: 180 counters
`

	modules, err := ParseRPC(output)
	if err != nil {
		t.Fatalf("ParseRPC with extra whitespace: %v", err)
	}
	if len(modules) != 1 {
		t.Fatalf("expected 1 module, got %d", len(modules))
	}
	if len(modules[0].Counters) != 4 {
		t.Errorf("expected 4 counters, got %d", len(modules[0].Counters))
	}

	// Trailing whitespace on lines
	output2 := `[2024-01-15 10:30:00]  
 PIC    5    6  sum  
  0    12  34   46  

Total sum: 46 counters  
`
	modules2, err := ParseRPC(output2)
	if err != nil {
		t.Fatalf("ParseRPC with trailing whitespace: %v", err)
	}
	if len(modules2) != 1 {
		t.Fatalf("expected 1 module, got %d", len(modules2))
	}
	if modules2[0].Counters[0].Value != 12 {
		t.Errorf("counter 0 value: got %d, want 12", modules2[0].Counters[0].Value)
	}
}

// TestParseRPC_RealisticSample validates parsing of a realistic RPC output sample.
func TestParseRPC_RealisticSample(t *testing.T) {
	output := readTestdata(t, "rpc_sample_realistic.txt")

	modules, err := ParseRPC(output)
	if err != nil {
		t.Fatalf("ParseRPC realistic sample: %v", err)
	}

	if len(modules) != 6 {
		t.Fatalf("expected 6 modules, got %d", len(modules))
	}

	// Verify first row
	m0 := modules[0]
	if m0.Position != 0 {
		t.Errorf("module 0 position: got %d, want 0", m0.Position)
	}
	if len(m0.Counters) != 12 {
		t.Errorf("module 0 counters: got %d, want 12", len(m0.Counters))
	}
	// Check specific counters
	expected := []struct {
		name  string
		value int
	}{
		{"5", 0}, {"6", 0}, {"7", 0}, {"8", 0},
		{"9", 0}, {"10", 0}, {"11", 0}, {"12", 0},
		{"13", 0}, {"14", 0}, {"15", 0}, {"16", 0},
	}
	for i, exp := range expected {
		if m0.Counters[i].Name != exp.name {
			t.Errorf("module 0 counter %d name: got %s, want %s", i, m0.Counters[i].Name, exp.name)
		}
		if m0.Counters[i].Value != exp.value {
			t.Errorf("module 0 counter %d value: got %d, want %d", i, m0.Counters[i].Value, exp.value)
		}
	}

	// Verify totals
	totals, ok := ParseRPCTotals(output)
	if !ok {
		t.Fatal("totals not found in realistic sample")
	}
	if totals.TotalCounters != 0 {
		t.Errorf("total counters: got %d, want 0", totals.TotalCounters)
	}
}

// TestParseRPC_HeaderTypeDetection validates PIC vs IBC detection for RPC.
func TestParseRPC_HeaderTypeDetection(t *testing.T) {
	picOut := ` PIC    5    6  sum
  0    12  34   46
`
	ht := ParseRPCHeaderType(picOut)
	if ht != types.PIC {
		t.Errorf("PIC header type: got %s, want PIC", ht)
	}

	ibcOut := ` IBC    0    1  sum
  0    42  17   59
`
	ht = ParseRPCHeaderType(ibcOut)
	if ht != types.IBC {
		t.Errorf("IBC header type: got %s, want IBC", ht)
	}

	noHeader := `some random text`
	ht = ParseRPCHeaderType(noHeader)
	if ht != "" {
		t.Errorf("no-header type: got %s, want empty", ht)
	}
}

// TestParseRPC_EmptySliceNotNil validates AXON safety: empty result is []RPCModule{}, not nil.
func TestParseRPC_EmptySliceNotNil(t *testing.T) {
	// Output with header but no data rows
	output := ` PIC    5    6  sum
-------------------------------

Total sum: 0 counters
`
	modules, err := ParseRPC(output)
	if err != nil {
		t.Fatalf("ParseRPC: %v", err)
	}
	if modules == nil {
		t.Error("AXON gotcha: empty result must be []RPCModule{}, not nil")
	}
	if len(modules) != 0 {
		t.Errorf("expected 0 modules, got %d", len(modules))
	}
}

// TestParseRPC_MalformedRowSkip validates that malformed rows are skipped.
func TestParseRPC_MalformedRowSkip(t *testing.T) {
	output := ` PIC    5    6  sum
-------------------------------
  0    12  34   46
malformed row without proper format
  1    56  78   134
`
	modules, err := ParseRPC(output)
	if err != nil {
		t.Fatalf("ParseRPC: %v", err)
	}
	if len(modules) != 2 {
		t.Fatalf("expected 2 valid modules (malformed row skipped), got %d", len(modules))
	}
}

// TestParseRPC_EmptySlots validates that all counter digits are captured
// and mapped to column positions in order.
func TestParseRPC_EmptySlots(t *testing.T) {
	// Row with 3 counter values for 4 columns — the 4th column gets no counter
	output := ` PIC    5    6    7    8  sum
-------------------------------
  0    12  34  78   124
`
	modules, err := ParseRPC(output)
	if err != nil {
		t.Fatalf("ParseRPC: %v", err)
	}
	if len(modules) != 1 {
		t.Fatalf("expected 1 module, got %d", len(modules))
	}
	// Should have 3 counters (12 at 5, 34 at 6, 78 at 7) — column 8 has no value
	if len(modules[0].Counters) != 3 {
		t.Errorf("expected 3 counters, got %d", len(modules[0].Counters))
	}
	if modules[0].Counters[0].Name != "5" || modules[0].Counters[0].Value != 12 {
		t.Errorf("counter 0: name=%s value=%d, want name=5 value=12", modules[0].Counters[0].Name, modules[0].Counters[0].Value)
	}
	if modules[0].Counters[1].Name != "6" || modules[0].Counters[1].Value != 34 {
		t.Errorf("counter 1: name=%s value=%d, want name=6 value=34", modules[0].Counters[1].Name, modules[0].Counters[1].Value)
	}
	if modules[0].Counters[2].Name != "7" || modules[0].Counters[2].Value != 78 {
		t.Errorf("counter 2: name=%s value=%d, want name=7 value=78", modules[0].Counters[2].Name, modules[0].Counters[2].Value)
	}
}

// TestParseRPC_NoFooter validates parsing when no Total sum footer is present.
func TestParseRPC_NoFooter(t *testing.T) {
	output := ` PIC    5    6  sum
  0    12  34   46
  1    56  78   134
`
	modules, err := ParseRPC(output)
	if err != nil {
		t.Fatalf("ParseRPC without footer: %v", err)
	}
	if len(modules) != 2 {
		t.Fatalf("expected 2 modules, got %d", len(modules))
	}

	// Totals should not be found
	_, ok := ParseRPCTotals(output)
	if ok {
		t.Error("totals should not be found when footer is absent")
	}
}

// TestParseRPC_TotalsExtraction validates totals footer parsing.
func TestParseRPC_TotalsExtraction(t *testing.T) {
	output := readTestdata(t, "rpc_sample_pic.txt")

	totals, ok := ParseRPCTotals(output)
	if !ok {
		t.Fatal("totals not found")
	}
	if totals.TotalCounters != 1410 {
		t.Errorf("total counters: got %d, want 1410", totals.TotalCounters)
	}

	// IBC sample
	output2 := readTestdata(t, "rpc_sample_ibc.txt")
	totals2, ok2 := ParseRPCTotals(output2)
	if !ok2 {
		t.Fatal("totals not found in IBC sample")
	}
	if totals2.TotalCounters != 587 {
		t.Errorf("total counters (IBC): got %d, want 587", totals2.TotalCounters)
	}
}

// TestParseRPC_CountersNeverNil validates AXON safety: counters slice is never nil.
func TestParseRPC_CountersNeverNil(t *testing.T) {
	output := readTestdata(t, "rpc_sample_pic.txt")

	modules, err := ParseRPC(output)
	if err != nil {
		t.Fatalf("ParseRPC: %v", err)
	}

	for i, m := range modules {
		if m.Counters == nil {
			t.Errorf("module %d: counters must be []RPCCounter{}, not nil (AXON gotcha)", i)
		}
	}
}
