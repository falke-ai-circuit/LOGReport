package parser

import (
	"testing"

	"github.com/falke-ai-circuit/LOGReport/internal/types"
)

// TestParseFBC_PICHeader validates parsing of PIC-format FBC output.
func TestParseFBC_PICHeader(t *testing.T) {
	output := `[2024-01-15 10:30:00]
print from fbc io structure 1620000
FBC agent 162

 PIC    5    6    7    8  sum
-------------------------------
  0   AI8  BI8  BO8  BI8   4
  1   AI8  BI8N BI8  BO8   4
  2   AI8  BI8  BO8  BI8   4

Total sum: 12 I/O-units, 48 Channels (24 input, 24 output)
`

	modules, err := ParseFBC(output)
	if err != nil {
		t.Fatalf("ParseFBC: unexpected error: %v", err)
	}

	if len(modules) != 3 {
		t.Fatalf("expected 3 modules, got %d", len(modules))
	}

	// Module 0
	m0 := modules[0]
	if m0.Position != 0 {
		t.Errorf("module 0 position: got %d, want 0", m0.Position)
	}
	if !m0.Exists {
		t.Error("module 0 should exist")
	}
	if len(m0.Channels) != 4 {
		t.Errorf("module 0 channels: got %d, want 4", len(m0.Channels))
	}
	if m0.Channels[0].Position != 5 || m0.Channels[0].Type != types.AI8 {
		t.Errorf("module 0 channel 0: pos=%d type=%s, want pos=5 type=AI8", m0.Channels[0].Position, m0.Channels[0].Type)
	}
	if m0.Channels[1].Position != 6 || m0.Channels[1].Type != types.BI8 {
		t.Errorf("module 0 channel 1: pos=%d type=%s, want pos=6 type=BI8", m0.Channels[1].Position, m0.Channels[1].Type)
	}
	if m0.Channels[2].Position != 7 || m0.Channels[2].Type != types.BO8 {
		t.Errorf("module 0 channel 2: pos=%d type=%s, want pos=7 type=BO8", m0.Channels[2].Position, m0.Channels[2].Type)
	}
	if m0.Channels[3].Position != 8 || m0.Channels[3].Type != types.BI8 {
		t.Errorf("module 0 channel 3: pos=%d type=%s, want pos=8 type=BI8", m0.Channels[3].Position, m0.Channels[3].Type)
	}

	// Module 1 — verify BI8N
	m1 := modules[1]
	if m1.Channels[1].Type != types.BI8N {
		t.Errorf("module 1 channel 1: got %s, want BI8N", m1.Channels[1].Type)
	}
}

// TestParseFBC_IBCHeader validates parsing of IBC-format FBC output.
func TestParseFBC_IBCHeader(t *testing.T) {
	output := `[2024-01-15 10:31:00]
print from fbc io structure 1630000
FBC agent 163

 IBC    0    1    2    3  sum
-------------------------------
  0   Di16 Do16 Ai8  Ao4   4
  1   Di16 Do16 Ai8  Ao4   4

Total sum: 8 I/O-units, 44 Channels (24 input, 20 output)
`

	modules, err := ParseFBC(output)
	if err != nil {
		t.Fatalf("ParseFBC: unexpected error: %v", err)
	}

	if len(modules) != 2 {
		t.Fatalf("expected 2 modules, got %d", len(modules))
	}

	// Verify header type detection
	ht := ParseFBCHeaderType(output)
	if ht != types.IBC {
		t.Errorf("header type: got %s, want IBC", ht)
	}

	// Module 0 — IBC format with mixed-case unit codes
	m0 := modules[0]
	if m0.Position != 0 {
		t.Errorf("module 0 position: got %d, want 0", m0.Position)
	}
	if len(m0.Channels) != 4 {
		t.Errorf("module 0 channels: got %d, want 4", len(m0.Channels))
	}
	if m0.Channels[0].Position != 0 || m0.Channels[0].Type != types.DI16 {
		t.Errorf("module 0 channel 0: pos=%d type=%s, want pos=0 type=DI16", m0.Channels[0].Position, m0.Channels[0].Type)
	}
	if m0.Channels[1].Position != 1 || m0.Channels[1].Type != types.DO16 {
		t.Errorf("module 0 channel 1: pos=%d type=%s, want pos=1 type=DO16", m0.Channels[1].Position, m0.Channels[1].Type)
	}
	if m0.Channels[2].Position != 2 || m0.Channels[2].Type != types.AI8 {
		t.Errorf("module 0 channel 2: pos=%d type=%s, want pos=2 type=AI8", m0.Channels[2].Position, m0.Channels[2].Type)
	}
	if m0.Channels[3].Position != 3 || m0.Channels[3].Type != types.AO4 {
		t.Errorf("module 0 channel 3: pos=%d type=%s, want pos=3 type=AO4", m0.Channels[3].Position, m0.Channels[3].Type)
	}
}

// TestParseFBC_NotExists validates "Not Exists" row handling.
func TestParseFBC_NotExists(t *testing.T) {
	output := `[2024-01-15 10:32:00]
print from fbc io structure 1620000
FBC agent 162

 PIC    5    6    7    8  sum
-------------------------------
  0   AI8  BI8  BO8  BI8   4
  1   Not Exists
  2   AI8  BI8  BO8  BI8   4

Total sum: 8 I/O-units, 32 Channels (16 input, 16 output)
`

	modules, err := ParseFBC(output)
	if err != nil {
		t.Fatalf("ParseFBC: unexpected error: %v", err)
	}

	if len(modules) != 3 {
		t.Fatalf("expected 3 modules, got %d", len(modules))
	}

	// Module 1 should be "Not Exists"
	m1 := modules[1]
	if m1.Position != 1 {
		t.Errorf("not-exists module position: got %d, want 1", m1.Position)
	}
	if m1.Exists {
		t.Error("not-exists module should have Exists=false")
	}
	if len(m1.Channels) != 0 {
		t.Errorf("not-exists module should have 0 channels, got %d", len(m1.Channels))
	}
	// AXON safety: channels must be empty slice, not nil
	if m1.Channels == nil {
		t.Error("not-exists module channels must be empty slice ([]FBCChannel{}), not nil (AXON gotcha)")
	}
}

// TestParseFBC_EmptyOutput validates that empty output returns an empty slice (not nil).
func TestParseFBC_EmptyOutput(t *testing.T) {
	// Empty string — no header, should error
	_, err := ParseFBC("")
	if err == nil {
		t.Error("expected error for empty output, got nil")
	}

	// Output with no PIC/IBC header
	output := `[2024-01-15 10:30:00]
Some random content
No table here
`
	_, err = ParseFBC(output)
	if err == nil {
		t.Error("expected error for output without PIC/IBC header, got nil")
	}
}

// TestParseFBC_MalformedHeader validates error on malformed header.
func TestParseFBC_MalformedHeader(t *testing.T) {
	output := `[2024-01-15 10:30:00]
print from fbc io structure 1620000

 XYZ    5    6    7    8  sum
-------------------------------
  0   AI8  BI8  BO8  BI8   4
`

	_, err := ParseFBC(output)
	if err == nil {
		t.Fatal("expected error for malformed header (XYZ instead of PIC/IBC), got nil")
	}
}

// TestParseFBC_MissingChannelColumns validates error when header has no column numbers.
func TestParseFBC_MissingChannelColumns(t *testing.T) {
	output := `[2024-01-15 10:30:00]
 PIC  sum
-------------------------------
  0   AI8   1
`

	_, err := ParseFBC(output)
	if err == nil {
		t.Fatal("expected error for header with no channel columns, got nil")
	}
}

// TestParseFBC_EncodingEdgeCases validates handling of extra whitespace and non-ASCII.
func TestParseFBC_EncodingEdgeCases(t *testing.T) {
	// Extra whitespace between columns (2-3 spaces, not 4+ which indicates empty slots)
	output := `[2024-01-15 10:30:00]
 PIC    5    6    7    8  sum
--------------------------------
  0   AI8   BI8   BO8   BI8   4

Total sum: 4 I/O-units, 16 Channels (8 input, 8 output)
`

	modules, err := ParseFBC(output)
	if err != nil {
		t.Fatalf("ParseFBC with extra whitespace: %v", err)
	}
	if len(modules) != 1 {
		t.Fatalf("expected 1 module, got %d", len(modules))
	}
	if len(modules[0].Channels) != 4 {
		t.Errorf("expected 4 channels, got %d", len(modules[0].Channels))
	}

	// Trailing whitespace on lines
	output2 := `[2024-01-15 10:30:00]  
 PIC    5    6  sum  
  0   AI8  BI8   2  

Total sum: 2 I/O-units, 16 Channels (8 input, 8 output)  
`
	modules2, err := ParseFBC(output2)
	if err != nil {
		t.Fatalf("ParseFBC with trailing whitespace: %v", err)
	}
	if len(modules2) != 1 {
		t.Fatalf("expected 1 module, got %d", len(modules2))
	}
}

// TestParseFBC_RealisticSample validates parsing of a realistic FBC output sample.
func TestParseFBC_RealisticSample(t *testing.T) {
	output := `[2025-10-12 12:12:08]
Command executed: print from fbc io structure 1620000
Getting FIELD BUS configuration from FBC agent 1620000

FBC Utilization Rate: 92%

 PIC    5    6    7    8    9   10   11   12   13   14   15   16   17   18   19   20  sum
----------------------------------------------------------------------------------------------
  0   AI8  BI8  BO8  BI8  BI8  BI8  BO8  BI8  BI8  BI8  BI8  BI8  BI8  BI8  TI6  AO4   15
  1   AI8  BI8  BI8  BI8  BO8  BI8  BO8  BI8  BI8  BI8  BI8  BI8  BI8  BI8  TI6  BI8   15
  2   AI8  BI8  BI8  BI8  BO8  BI8  BO8  BI8  BI8  BI8  BI8  BI8  BI8  BI8  BI8  BI8   15
  3   AI8  BI8  BO8  BI8  BO8  BI8  BO8  BI8  BI8  BI8  BI8  BI8  BI8  BI8  TI6  BI8   15

Total sum: 238 I/O-units, 1843 Channels (1323 input, 520 output)
AIU8: 15, AOU4: 4, BIU8: 131, BI8N: 6, BOU8: 63, FIU1: 2, AIU4: 1, TIU6: 16
`

	modules, err := ParseFBC(output)
	if err != nil {
		t.Fatalf("ParseFBC realistic sample: %v", err)
	}

	if len(modules) != 4 {
		t.Fatalf("expected 4 modules, got %d", len(modules))
	}

	// Verify first row
	m0 := modules[0]
	if m0.Position != 0 {
		t.Errorf("module 0 position: got %d, want 0", m0.Position)
	}
	if len(m0.Channels) != 16 {
		t.Errorf("module 0 channels: got %d, want 16", len(m0.Channels))
	}
	// Check specific channels
	expected := []struct {
		pos  int
		ct   types.ChannelType
	}{
		{5, types.AI8}, {6, types.BI8}, {7, types.BO8}, {8, types.BI8},
		{9, types.BI8}, {10, types.BI8}, {11, types.BO8}, {12, types.BI8},
		{13, types.BI8}, {14, types.BI8}, {15, types.BI8}, {16, types.BI8},
		{17, types.BI8}, {18, types.BI8}, {19, types.TI6}, {20, types.AO4},
	}
	for i, exp := range expected {
		if m0.Channels[i].Position != exp.pos {
			t.Errorf("module 0 channel %d position: got %d, want %d", i, m0.Channels[i].Position, exp.pos)
		}
		if m0.Channels[i].Type != exp.ct {
			t.Errorf("module 0 channel %d type: got %s, want %s", i, m0.Channels[i].Type, exp.ct)
		}
	}

	// Verify totals
	totals, ok := ParseFBCTotals(output)
	if !ok {
		t.Fatal("totals not found in realistic sample")
	}
	if totals.TotalUnits != 238 {
		t.Errorf("total units: got %d, want 238", totals.TotalUnits)
	}
	if totals.TotalChannels != 1843 {
		t.Errorf("total channels: got %d, want 1843", totals.TotalChannels)
	}
	if totals.InputChannels != 1323 {
		t.Errorf("input channels: got %d, want 1323", totals.InputChannels)
	}
	if totals.OutputChannels != 520 {
		t.Errorf("output channels: got %d, want 520", totals.OutputChannels)
	}
}

// TestParseFBC_HeaderTypeDetection validates PIC vs IBC detection.
func TestParseFBC_HeaderTypeDetection(t *testing.T) {
	picOut := ` PIC    5    6  sum
  0   AI8  BI8   2
`
	ht := ParseFBCHeaderType(picOut)
	if ht != types.PIC {
		t.Errorf("PIC header type: got %s, want PIC", ht)
	}

	ibcOut := ` IBC    0    1  sum
  0   Di16 Do16   2
`
	ht = ParseFBCHeaderType(ibcOut)
	if ht != types.IBC {
		t.Errorf("IBC header type: got %s, want IBC", ht)
	}

	noHeader := `some random text`
	ht = ParseFBCHeaderType(noHeader)
	if ht != "" {
		t.Errorf("no-header type: got %s, want empty", ht)
	}
}

// TestParseFBC_ChannelSum validates channel sum extraction from type codes.
func TestParseFBC_ChannelSum(t *testing.T) {
	tests := []struct {
		ct   types.ChannelType
		want int
	}{
		{types.AI8, 8},
		{types.AO4, 4},
		{types.AO8, 8},
		{types.DI16, 16},
		{types.DO16, 16},
		{types.BI8, 8},
		{types.BI8N, 8},
		{types.BO8, 8},
		{types.TI6, 6},
		{types.TO6, 6},
		{types.PI4, 4},
		{types.PO4, 4},
		{types.SI8, 8},
		{types.SO8, 8},
		{types.CI4, 4},
		{types.CO4, 4},
		{types.RI4, 4},
		{types.RO4, 4},
		{types.II4, 4},
		{types.IO4, 4},
		{types.NotExists, 0},
	}
	for _, tc := range tests {
		got := channelSum(tc.ct)
		if got != tc.want {
			t.Errorf("channelSum(%s): got %d, want %d", tc.ct, got, tc.want)
		}
	}
}

// TestParseFBC_ResolveChannelType validates channel type resolution.
func TestParseFBC_ResolveChannelType(t *testing.T) {
	tests := []struct {
		raw  string
		want types.ChannelType
	}{
		{"AI8", types.AI8},
		{"ai8", types.AI8},
		{"BI8N", types.BI8N},
		{"bi8n", types.BI8N},
		{"Di16", types.DI16},
		{"DI16", types.DI16},
		{"Do16", types.DO16},
		{"N/E", types.NotExists},
		{"UNKNOWN", types.NotExists},
		{"", types.NotExists},
	}
	for _, tc := range tests {
		got := resolveChannelType(tc.raw)
		if got != tc.want {
			t.Errorf("resolveChannelType(%q): got %s, want %s", tc.raw, got, tc.want)
		}
	}
}

// TestParseFBC_EmptySliceNotNil validates AXON safety: empty result is []FBCModule{}, not nil.
func TestParseFBC_EmptySliceNotNil(t *testing.T) {
	// Output with header but no data rows
	output := ` PIC    5    6  sum
-------------------------------

Total sum: 0 I/O-units, 0 Channels (0 input, 0 output)
`
	modules, err := ParseFBC(output)
	if err != nil {
		t.Fatalf("ParseFBC: %v", err)
	}
	if modules == nil {
		t.Error("AXON gotcha: empty result must be []FBCModule{}, not nil")
	}
	if len(modules) != 0 {
		t.Errorf("expected 0 modules, got %d", len(modules))
	}
}

// TestParseFBC_MalformedRowSkip validates that malformed rows are skipped.
func TestParseFBC_MalformedRowSkip(t *testing.T) {
	output := ` PIC    5    6  sum
-------------------------------
  0   AI8  BI8   2
malformed row without proper format
  1   AI8  BI8   2
`
	modules, err := ParseFBC(output)
	if err != nil {
		t.Fatalf("ParseFBC: %v", err)
	}
	if len(modules) != 2 {
		t.Fatalf("expected 2 valid modules (malformed row skipped), got %d", len(modules))
	}
}

// TestParseFBC_EmptySlots validates that empty I/O slots (4+ spaces) are handled correctly.
func TestParseFBC_EmptySlots(t *testing.T) {
	// Row with an empty slot between columns 6 and 8 (4+ spaces where column 7 would be)
	output := ` PIC    5    6    7    8  sum
-------------------------------
  0   AI8  BI8       BO8   3
`
	modules, err := ParseFBC(output)
	if err != nil {
		t.Fatalf("ParseFBC: %v", err)
	}
	if len(modules) != 1 {
		t.Fatalf("expected 1 module, got %d", len(modules))
	}
	// Should have 3 channels (AI8 at 5, BI8 at 6, BO8 at 8) — empty slot at 7 is skipped
	if len(modules[0].Channels) != 3 {
		t.Errorf("expected 3 channels (empty slot skipped), got %d", len(modules[0].Channels))
	}
	if modules[0].Channels[0].Position != 5 || modules[0].Channels[0].Type != types.AI8 {
		t.Errorf("channel 0: pos=%d type=%s, want pos=5 type=AI8", modules[0].Channels[0].Position, modules[0].Channels[0].Type)
	}
	if modules[0].Channels[1].Position != 6 || modules[0].Channels[1].Type != types.BI8 {
		t.Errorf("channel 1: pos=%d type=%s, want pos=6 type=BI8", modules[0].Channels[1].Position, modules[0].Channels[1].Type)
	}
	if modules[0].Channels[2].Position != 8 || modules[0].Channels[2].Type != types.BO8 {
		t.Errorf("channel 2: pos=%d type=%s, want pos=8 type=BO8", modules[0].Channels[2].Position, modules[0].Channels[2].Type)
	}
}

// TestParseFBC_NoFooter validates parsing when no Total sum footer is present.
func TestParseFBC_NoFooter(t *testing.T) {
	output := ` PIC    5    6  sum
  0   AI8  BI8   2
  1   AI8  BI8   2
`
	modules, err := ParseFBC(output)
	if err != nil {
		t.Fatalf("ParseFBC without footer: %v", err)
	}
	if len(modules) != 2 {
		t.Fatalf("expected 2 modules, got %d", len(modules))
	}

	// Totals should not be found
	_, ok := ParseFBCTotals(output)
	if ok {
		t.Error("totals should not be found when footer is absent")
	}
}
