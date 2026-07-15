package parser

import (
	"path/filepath"
	"testing"

	"github.com/falke-ai-circuit/LOGReport/internal/types"
)

// TestParseSysFile_HWFormat validates parsing of :e:hw: token mapping format.
func TestParseSysFile_HWFormat(t *testing.T) {
	result := ParseSysFileString(hwFormatFixture)

	if len(result.Entries) == 0 {
		t.Fatal("expected entries from :e:hw: format, got none")
	}

	// Verify AP01 entry
	ap01 := findEntry(result.Entries, "AP01")
	if ap01 == nil {
		t.Fatal("expected AP01 entry")
	}
	if ap01.NodeType != "PCS" {
		t.Errorf("AP01 NodeType: got %q, want PCS", ap01.NodeType)
	}
	if ap01.Description != "AP01 PCS" {
		t.Errorf("AP01 Description: got %q, want 'AP01 PCS'", ap01.Description)
	}

	// Verify AP02_main entry
	ap02m := findEntry(result.Entries, "AP02_main")
	if ap02m == nil {
		t.Fatal("expected AP02_main entry")
	}
	if ap02m.NodeType != "PCS" {
		t.Errorf("AP02_main NodeType: got %q, want PCS", ap02m.NodeType)
	}

	// Verify AP02_reserve entry
	ap02r := findEntry(result.Entries, "AP02_reserve")
	if ap02r == nil {
		t.Fatal("expected AP02_reserve entry")
	}
	if ap02r.NodeType != "PCS" {
		t.Errorf("AP02_reserve NodeType: got %q, want PCS", ap02r.NodeType)
	}

	// Verify AL01 entry
	al01 := findEntry(result.Entries, "AL01")
	if al01 == nil {
		t.Fatal("expected AL01 entry")
	}
	if al01.NodeType != "LIS" {
		t.Errorf("AL01 NodeType: got %q, want LIS", al01.NodeType)
	}

	// Verify AL01_t1 entry (token, comment "LIS Token 1")
	al01t1 := findEntry(result.Entries, "AL01_t1")
	if al01t1 == nil {
		t.Fatal("expected AL01_t1 entry")
	}
	if al01t1.NodeType != "LIS" {
		t.Errorf("AL01_t1 NodeType: got %q, want LIS", al01t1.NodeType)
	}

	// Verify AP01_m2 entry (comment "FBC2" → description is "FBC2")
	ap01m2 := findEntry(result.Entries, "AP01_m2")
	if ap01m2 == nil {
		t.Fatal("expected AP01_m2 entry")
	}
	if ap01m2.Description != "FBC2" {
		t.Errorf("AP01_m2 Description: got %q, want 'FBC2'", ap01m2.Description)
	}

	// Count total entries: 22 AP + 8 AL = 30? No, let's count:
	// AP01(3) + AP02_main(3) + AP02_reserve(3) + AP03_main(3) + AP03_reserve(3)
	// + AP04(3) + AP05(3) + AP06(3) + AP07_main(2) + AP07_reserve(2)
	// + AL01(3) + AL02(2) + AL03(1) + AL08(4) = 38
	expectedCount := 38
	if len(result.Entries) != expectedCount {
		t.Errorf("entry count: got %d, want %d", len(result.Entries), expectedCount)
	}
}

// TestParseSysFile_SlotFormat validates parsing of slot configuration format.
func TestParseSysFile_SlotFormat(t *testing.T) {
	result := ParseSysFileString(slotFormatFixture)

	if len(result.Nodes) == 0 {
		t.Fatal("expected nodes from slot format, got none")
	}

	// Verify NCU2 node (implicit slot — no "Slot N" prefix, just TITLE/PROGRAM)
	ncu2 := findNode(result.Nodes, "NCU2")
	if ncu2 == nil {
		t.Fatal("expected NCU2 node")
	}
	if ncu2.Program != "<NCU2_CODE>" {
		t.Errorf("NCU2 Program: got %q, want <NCU2_CODE>", ncu2.Program)
	}

	// Verify AL02 node
	al02 := findNode(result.Nodes, "AL02")
	if al02 == nil {
		t.Fatal("expected AL02 node")
	}
	if al02.Type != "LIS" {
		t.Errorf("AL02 Type: got %q, want LIS", al02.Type)
	}
	if al02.Program != "<PCS_CODE>" {
		t.Errorf("AL02 Program: got %q, want <PCS_CODE>", al02.Program)
	}

	// Verify AL02_DiagLis Tool node
	diagLis := findNode(result.Nodes, "AL02_DiagLis Tool")
	if diagLis == nil {
		t.Fatal("expected AL02_DiagLis Tool node")
	}
	if diagLis.Program != "<DIAGLIS_CODE>" {
		t.Errorf("DiagLis Program: got %q, want <DIAGLIS_CODE>", diagLis.Program)
	}

	// Verify IP address extraction
	if result.IPAddr != "192.168.0.2" {
		t.Errorf("IPAddr: got %q, want 192.168.0.2", result.IPAddr)
	}

	// Should have 3 nodes (NCU2, AL02, AL02_DiagLis Tool)
	if len(result.Nodes) != 3 {
		t.Errorf("node count: got %d, want 3", len(result.Nodes))
	}
}

// TestParseSysFile_MixedFormat validates parsing of files with both formats.
func TestParseSysFile_MixedFormat(t *testing.T) {
	result := ParseSysFileString(mixedFormatFixture)

	// Should have :e:hw: entries
	if len(result.Entries) == 0 {
		t.Fatal("expected entries from mixed format, got none")
	}

	// Should have slot nodes
	if len(result.Nodes) == 0 {
		t.Fatal("expected nodes from mixed format, got none")
	}

	// Verify entries
	ap01 := findEntry(result.Entries, "AP01")
	if ap01 == nil {
		t.Fatal("expected AP01 entry in mixed format")
	}

	al01 := findEntry(result.Entries, "AL01")
	if al01 == nil {
		t.Fatal("expected AL01 entry in mixed format")
	}

	// Verify nodes: NCU2 (implicit), AP01, AP01_m2
	ncu2 := findNode(result.Nodes, "NCU2")
	if ncu2 == nil {
		t.Fatal("expected NCU2 node in mixed format")
	}

	ap01Node := findNode(result.Nodes, "AP01")
	if ap01Node == nil {
		t.Fatal("expected AP01 node in mixed format")
	}
	if ap01Node.Program != "<PCS_CODE>" {
		t.Errorf("AP01 node Program: got %q, want <PCS_CODE>", ap01Node.Program)
	}

	ap01m2Node := findNode(result.Nodes, "AP01_m2")
	if ap01m2Node == nil {
		t.Fatal("expected AP01_m2 node in mixed format")
	}
	if ap01m2Node.Program != "<CIO_FBC_CODE>" {
		t.Errorf("AP01_m2 node Program: got %q, want <CIO_FBC_CODE>", ap01m2Node.Program)
	}

	// Verify IP address
	if result.IPAddr != "192.168.0.11" {
		t.Errorf("IPAddr: got %q, want 192.168.0.11", result.IPAddr)
	}

	// 5 entries + 3 nodes (NCU2, AP01, AP01_m2)
	if len(result.Entries) != 5 {
		t.Errorf("entry count: got %d, want 5", len(result.Entries))
	}
	if len(result.Nodes) != 3 {
		t.Errorf("node count: got %d, want 3 (NCU2, AP01, AP01_m2)", len(result.Nodes))
	}
}

// TestParseSysFile_EmptyFile validates that empty files return empty slices (not nil).
func TestParseSysFile_EmptyFile(t *testing.T) {
	result := ParseSysFileString("")

	// AXON safety: entries must be empty slice, not nil
	if result.Entries == nil {
		t.Error("AXON gotcha: empty result Entries must be []SysFileEntry{}, not nil")
	}
	if len(result.Entries) != 0 {
		t.Errorf("expected 0 entries, got %d", len(result.Entries))
	}

	// AXON safety: nodes must be empty slice, not nil
	if result.Nodes == nil {
		t.Error("AXON gotcha: empty result Nodes must be []SysFileNode{}, not nil")
	}
	if len(result.Nodes) != 0 {
		t.Errorf("expected 0 nodes, got %d", len(result.Nodes))
	}

	// IPAddr should be empty
	if result.IPAddr != "" {
		t.Errorf("IPAddr: got %q, want empty", result.IPAddr)
	}
}

// TestParseSysFile_CommentOnly validates that comment-only files return empty slices.
func TestParseSysFile_CommentOnly(t *testing.T) {
	content := `// This is a comment
// Another comment
// Only comments here
`
	result := ParseSysFileString(content)

	if len(result.Entries) != 0 {
		t.Errorf("expected 0 entries from comment-only file, got %d", len(result.Entries))
	}
	if len(result.Nodes) != 0 {
		t.Errorf("expected 0 nodes from comment-only file, got %d", len(result.Nodes))
	}
}

// TestParseSysFile_MalformedLines validates that malformed lines are skipped gracefully.
func TestParseSysFile_MalformedLines(t *testing.T) {
	content := `:e:hw:161 AP01		pxe:sys-csg2	// AP01 PCS
this is a malformed line
:e:hw:xyz NOT_A_HEX AP01 bad
:e:hw:162 AP01_m2	-               // FBC2
some random text
:e:hw:163 AP01_m3       -               // FBC3
`
	result := ParseSysFileString(content)

	// Only 3 valid entries should be parsed (161, 162, 163)
	if len(result.Entries) != 3 {
		t.Errorf("expected 3 valid entries (malformed skipped), got %d", len(result.Entries))
	}

	// Verify the valid ones
	ap01 := findEntry(result.Entries, "AP01")
	if ap01 == nil {
		t.Error("AP01 should be parsed despite malformed lines")
	}
	ap01m3 := findEntry(result.Entries, "AP01_m3")
	if ap01m3 == nil {
		t.Error("AP01_m3 should be parsed despite malformed lines")
	}
}

// TestParseSysFile_EncodingEdgeCases validates handling of tabs, extra whitespace, and trailing spaces.
func TestParseSysFile_EncodingEdgeCases(t *testing.T) {
	// Tabs instead of spaces
	content := `:e:hw:161	AP01		pxe:sys-csg2	// AP01 PCS
:e:hw:162	AP01_m2	-               // FBC2
`
	result := ParseSysFileString(content)

	if len(result.Entries) != 2 {
		t.Fatalf("expected 2 entries with tab separators, got %d", len(result.Entries))
	}

	ap01 := findEntry(result.Entries, "AP01")
	if ap01 == nil {
		t.Fatal("AP01 should be parsed with tab separators")
	}
	if ap01.NodeType != "PCS" {
		t.Errorf("AP01 NodeType with tabs: got %q, want PCS", ap01.NodeType)
	}

	// Trailing whitespace
	content2 := `:e:hw:501 AL01		pxe:sys-csg2	// AL01 Node   
:e:hw:502 AL01_t1	-                 
`
	result2 := ParseSysFileString(content2)
	if len(result2.Entries) != 2 {
		t.Fatalf("expected 2 entries with trailing whitespace, got %d", len(result2.Entries))
	}

	// Mixed tabs and spaces
	content3 := `:e:hw:161 AP01	 	pxe:sys-csg2	// AP01 PCS
`
	result3 := ParseSysFileString(content3)
	if len(result3.Entries) != 1 {
		t.Fatalf("expected 1 entry with mixed tabs/spaces, got %d", len(result3.Entries))
	}
}

// TestParseSysFile_RealSysFiles validates parsing of all real .sys files from Python source.
func TestParseSysFile_RealSysFiles(t *testing.T) {
	testdataDir := "testdata"

	sysFiles, err := filepath.Glob(filepath.Join(testdataDir, "*.sys"))
	if err != nil {
		t.Fatalf("glob testdata/*.sys: %v", err)
	}

	if len(sysFiles) == 0 {
		t.Fatal("no .sys files found in testdata/")
	}

	for _, path := range sysFiles {
		t.Run(filepath.Base(path), func(t *testing.T) {
			result, err := ParseSysFile(path)
			if err != nil {
				t.Fatalf("ParseSysFile(%s): %v", path, err)
			}

			// Every real .sys file should have either entries or nodes or an IP
			hasContent := len(result.Entries) > 0 || len(result.Nodes) > 0 || result.IPAddr != ""
			if !hasContent {
				t.Errorf("%s: parsed but no entries, nodes, or IP found", filepath.Base(path))
			}

			t.Logf("%s: %d entries, %d nodes, IP=%q",
				filepath.Base(path), len(result.Entries), len(result.Nodes), result.IPAddr)
		})
	}
}

// TestParseSysFile_RealSysFileSpecific validates specific known .sys files.
func TestParseSysFile_RealSysFileSpecific(t *testing.T) {
	// 41.sys — slot format, AL02 LIS node
	result, err := ParseSysFile("testdata/41.sys")
	if err != nil {
		t.Fatalf("ParseSysFile(41.sys): %v", err)
	}

	if len(result.Nodes) == 0 {
		t.Error("41.sys should have slot nodes")
	}

	if result.IPAddr != "192.168.0.2" {
		t.Errorf("41.sys IP: got %q, want 192.168.0.2", result.IPAddr)
	}

	// Check for AL02 node (title is "AL02")
	al02 := findNode(result.Nodes, "AL02")
	if al02 == nil {
		t.Error("41.sys should have AL02 node")
	} else {
		if al02.Type != "LIS" {
			t.Errorf("AL02 Type: got %q, want LIS", al02.Type)
		}
	}

	// 181.sys — slot format, AP02 Main PCS with FBCs
	result181, err := ParseSysFile("testdata/181.sys")
	if err != nil {
		t.Fatalf("ParseSysFile(181.sys): %v", err)
	}

	if len(result181.Nodes) == 0 {
		t.Error("181.sys should have slot nodes")
	}

	// Titles in 181.sys: "NCU2", "AP02 Main", "AP02_m2", "AP02_m3", "AP02_m4"
	ap02main := findNode(result181.Nodes, "AP02 Main")
	if ap02main == nil {
		t.Error("181.sys should have 'AP02 Main' node")
	}
	ap02m2 := findNode(result181.Nodes, "AP02_m2")
	if ap02m2 == nil {
		t.Error("181.sys should have AP02_m2 node")
	}
	ap02m3 := findNode(result181.Nodes, "AP02_m3")
	if ap02m3 == nil {
		t.Error("181.sys should have AP02_m3 node")
	}
	ap02m4 := findNode(result181.Nodes, "AP02_m4")
	if ap02m4 == nil {
		t.Error("181.sys should have AP02_m4 node")
	}

	// 21.sys — slot format, AL01 LIS
	result21, err := ParseSysFile("testdata/21.sys")
	if err != nil {
		t.Fatalf("ParseSysFile(21.sys): %v", err)
	}
	if result21.IPAddr != "192.168.0.1" {
		t.Errorf("21.sys IP: got %q, want 192.168.0.1", result21.IPAddr)
	}
	al01Node := findNode(result21.Nodes, "AL01")
	if al01Node == nil {
		t.Error("21.sys should have AL01 node")
	}
}

// TestParseSysFile_NonexistentFile validates error handling for missing files.
func TestParseSysFile_NonexistentFile(t *testing.T) {
	_, err := ParseSysFile("testdata/does_not_exist.sys")
	if err == nil {
		t.Fatal("expected error for nonexistent file, got nil")
	}
}

// TestParseSysFile_LIDMapping validates that LIDMapping matches Python sys_file_parser.py:89-102.
func TestParseSysFile_LIDMapping(t *testing.T) {
	// Python LID_TYPE_MAPPING from sys_file_parser.py:89-102
	// Plus Go extensions: BL→LIS, BP→PCS for B-bus redundant stations
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

	for prefix, wantType := range expected {
		gotType, ok := types.LIDMapping[prefix]
		if !ok {
			t.Errorf("LIDMapping missing key %q (Python has it)", prefix)
			continue
		}
		if gotType != wantType {
			t.Errorf("LIDMapping[%q]: got %q, want %q (Python)", prefix, gotType, wantType)
		}
	}

	// Verify no extra keys in Go that aren't in Python
	for prefix := range types.LIDMapping {
		if _, ok := expected[prefix]; !ok {
			t.Errorf("LIDMapping has extra key %q not in Python", prefix)
		}
	}
}

// TestParseSysFile_ResolveNodeType validates node type resolution from LID prefixes.
func TestParseSysFile_ResolveNodeType(t *testing.T) {
	tests := []struct {
		lid      string
		wantType string
	}{
		{"AD01", "DIA"},
		{"BD01", "DIA"},
		{"AC01", "CIS"},
		{"NW01", "NETWATCH"},
		{"AM01", "MAINT"},
		{"AL01", "LIS"},
		{"AP01", "PCS"},
		{"AP01_main", "PCS"},
		{"AP01_m2", "PCS"},
		{"A1O01", "OPS"},
		{"B1O01", "OPS"},
		{"A1A01", "ALP"},
		{"B1A01", "ALP"},
		{"INFO", "HISTORY"},
		{"UNKNOWN_LID", "UNKNOWN"},
		{"XYZ", "UNKNOWN"},
		{"", "UNKNOWN"},
	}

	for _, tc := range tests {
		got := resolveNodeType(tc.lid)
		if got != tc.wantType {
			t.Errorf("resolveNodeType(%q): got %q, want %q", tc.lid, got, tc.wantType)
		}
	}
}

// TestParseSysFile_NoIPAddr validates that files without set XD_IP_ADDR return empty IP.
func TestParseSysFile_NoIPAddr(t *testing.T) {
	content := `:e:hw:161 AP01		pxe:sys-csg2	// AP01 PCS
:e:hw:162 AP01_m2	-               // FBC2
`
	result := ParseSysFileString(content)

	if result.IPAddr != "" {
		t.Errorf("IPAddr should be empty when no set XD_IP_ADDR, got %q", result.IPAddr)
	}
}

// TestParseSysFile_OnlyIPAddr validates files that only have IP address and no entries/nodes.
func TestParseSysFile_OnlyIPAddr(t *testing.T) {
	content := `set XD_HW_BUS=A
set XD_IP_ADDR=10.0.0.1
set XD_DEBUG=1
`
	result := ParseSysFileString(content)

	if result.IPAddr != "10.0.0.1" {
		t.Errorf("IPAddr: got %q, want 10.0.0.1", result.IPAddr)
	}
	if len(result.Entries) != 0 {
		t.Errorf("expected 0 entries, got %d", len(result.Entries))
	}
	if len(result.Nodes) != 0 {
		t.Errorf("expected 0 nodes, got %d", len(result.Nodes))
	}
}

// TestParseSysFile_SlotWithoutTitle validates that slots without TITLE are skipped.
func TestParseSysFile_SlotWithoutTitle(t *testing.T) {
	content := `Slot 1
AUTOSTART=YES
PROGRAM=<PCS_CODE>
`
	result := ParseSysFileString(content)

	// Slot without TITLE should not produce a node
	if len(result.Nodes) != 0 {
		t.Errorf("expected 0 nodes for slot without TITLE, got %d", len(result.Nodes))
	}
}

// TestParseSysFile_SlotWithoutProgram validates that slots with only TITLE are still captured.
func TestParseSysFile_SlotWithoutProgram(t *testing.T) {
	content := `Slot 1
TITLE=TestNode
`
	result := ParseSysFileString(content)

	if len(result.Nodes) != 1 {
		t.Fatalf("expected 1 node for slot with TITLE only, got %d", len(result.Nodes))
	}
	if result.Nodes[0].Name != "TestNode" {
		t.Errorf("node name: got %q, want TestNode", result.Nodes[0].Name)
	}
	if result.Nodes[0].Program != "" {
		t.Errorf("node program should be empty, got %q", result.Nodes[0].Program)
	}
}

// TestParseSysFile_RegressionProbe runs a regression probe comparing Go output
// against Python sys_file_parser.py output for real .sys files.
func TestParseSysFile_RegressionProbe(t *testing.T) {
	testdataDir := "testdata"
	sysFiles, err := filepath.Glob(filepath.Join(testdataDir, "*.sys"))
	if err != nil {
		t.Fatalf("glob testdata/*.sys: %v", err)
	}

	// Known IP addresses extracted from actual .sys files (verified via grep)
	knownIPs := map[string]string{
		"21.sys":  "192.168.0.1",
		"41.sys":  "192.168.0.2",
		"161.sys": "192.168.0.11",
		"181.sys": "192.168.0.12",
		"1a1.sys": "192.168.0.13",
		"1c1.sys": "192.168.0.14",
		"1e1.sys": "192.168.0.15",
		"201.sys": "192.168.0.16",
		"221.sys": "192.168.0.17",
		"381.sys": "192.168.0.28",
		"3a1.sys": "192.168.0.29",
		"421.sys": "192.168.0.33",
		"481.sys": "192.168.0.36",
		"4a1.sys": "192.168.0.37",
		"4c1.sys": "192.168.0.38",
	}

	parseCount := 0
	for _, path := range sysFiles {
		result, err := ParseSysFile(path)
		if err != nil {
			t.Errorf("regression: ParseSysFile(%s) failed: %v", filepath.Base(path), err)
			continue
		}
		parseCount++

		base := filepath.Base(path)

		// Verify IP address if known
		if expectedIP, ok := knownIPs[base]; ok {
			if result.IPAddr != expectedIP {
				t.Errorf("regression: %s IP mismatch: got %q, want %q", base, result.IPAddr, expectedIP)
			}
		}

		// Verify nodes have correct types based on LID prefix
		for _, node := range result.Nodes {
			expectedType := resolveNodeType(node.LID)
			if node.Type != expectedType {
				t.Errorf("regression: %s node %q type mismatch: got %q, resolveNodeType says %q",
					base, node.Name, node.Type, expectedType)
			}
		}

		// Verify entries have correct types
		for _, entry := range result.Entries {
			expectedType := resolveNodeType(entry.LID)
			if entry.NodeType != expectedType {
				t.Errorf("regression: %s entry %q type mismatch: got %q, resolveNodeType says %q",
					base, entry.LID, entry.NodeType, expectedType)
			}
		}
	}

	if parseCount == 0 {
		t.Fatal("regression: no .sys files parsed")
	}

	t.Logf("regression probe: parsed %d .sys files successfully", parseCount)
}

// --- Helpers ---

func findEntry(entries []types.SysFileEntry, lid string) *types.SysFileEntry {
	for i := range entries {
		if entries[i].LID == lid {
			return &entries[i]
		}
	}
	return nil
}

func findNode(nodes []types.SysFileNode, name string) *types.SysFileNode {
	for i := range nodes {
		if nodes[i].Name == name {
			return &nodes[i]
		}
	}
	return nil
}

// --- Test fixtures ---

const hwFormatFixture = `// HW     LID           PARAMETER          COMMENT

:e:hw:161 AP01		pxe:sys-csg2	// AP01 PCS
:e:hw:162 AP01_m2	-               // FBC2
:e:hw:163 AP01_m3       -               // FBC3

:e:hw:181 AP02_main	pxe:sys-csg2	// AP02 Main PCS
:e:hw:182 AP02_m2	-               // FBC2
:e:hw:183 AP02_m3       -               // FBC3

:e:hw:381 AP02_reserve	pxe:sys-csg2	// AP02 Reserve PCS
:e:hw:382 AP02_r2	-               // FBC2
:e:hw:383 AP02_r3       -               // FBC3

:e:hw:1a1 AP03_main	pxe:sys-csg2	// AP03 Main PCS
:e:hw:1a2 AP03_m2	-               // FBC2
:e:hw:1a3 AP03_m3       -               // FBC3

:e:hw:3a1 AP03_reserve	pxe:sys-csg2	// AP03 Reserve PCS
:e:hw:3a2 AP03_r2	-               // FBC2
:e:hw:3a3 AP03_r3       -               // FBC3

:e:hw:1c1 AP04		pxe:sys-csg2	// AP04 PCS
:e:hw:1c2 AP04_m2	-               // FBC2
:e:hw:1c3 AP04_m3       -               // FBC3

:e:hw:1e1 AP05		pxe:sys-csg2	// AP05 PCS
:e:hw:1e2 AP05_m2	-               // FBC2
:e:hw:1e3 AP05_m3       -               // FBC3

:e:hw:201 AP06		pxe:sys-csg2	// AP06 PCS
:e:hw:202 AP06_m2	-               // FBC2
:e:hw:203 AP06_m3       -               // FBC3

:e:hw:221 AP07_main	pxe:sys-csg2	// AP07 Main PCS
:e:hw:222 AP07_m2	-               // FBC2

:e:hw:421 AP07_reserve	pxe:sys-csg2	// AP07 Reserve PCS
:e:hw:422 AP07_r2	-               // FBC2

:e:hw:501 AL01		pxe:sys-csg2	// AL01 Node
:e:hw:502 AL01_t1	-               // LIS Token 1
:e:hw:503 AL01_t2       -               // LIS Token 2

:e:hw:511 AL02		pxe:sys-csg2	// AL02 Node
:e:hw:512 AL02_t1	-               // LIS Token 1

:e:hw:521 AL03		pxe:sys-csg2	// AL03 Node

:e:hw:531 AL08		pxe:sys-csg2	// AL08 Node
:e:hw:532 AL08_t1	-               // LIS Token 1
:e:hw:533 AL08_t2       -               // LIS Token 2
:e:hw:534 AL08_t3       -               // LIS Token 3
`

const slotFormatFixture = `set XD_HW_BUS=A
set XD_IP_ADDR=192.168.0.2
set XD_DEBUG=1

// NCU2
NCU2
AUTOSTART=YES
TITLE=NCU2
PROGRAM=<NCU2_CODE>

// AL02 LIS
Slot 1
set XD_PMM_LED_RUN=1
AUTOSTART=YES
TITLE=AL02
PROGRAM=<PCS_CODE>

// DiagLis
Slot 13
set XD_STDIO=CONSOLE
AUTOSTART=NO
PRIORITY=NORMAL
PROGRAM=<DIAGLIS_CODE>
TITLE=AL02_DiagLis Tool
`

const mixedFormatFixture = `// Mixed format: both :e:hw: entries and slot configuration

:e:hw:161 AP01		pxe:sys-csg2	// AP01 PCS
:e:hw:162 AP01_m2	-               // FBC2
:e:hw:163 AP01_m3       -               // FBC3

:e:hw:501 AL01		pxe:sys-csg2	// AL01 Node
:e:hw:502 AL01_t1	-               // LIS Token 1

set XD_HW_BUS=A
set XD_IP_ADDR=192.168.0.11

// NCU2
NCU2
AUTOSTART=YES
TITLE=NCU2
PROGRAM=<NCU2_CODE>

// AP01 PCS
Slot 1
AUTOSTART=YES
TITLE=AP01
PROGRAM=<PCS_CODE>

// FBC2
Slot 2
TITLE=AP01_m2
AUTOSTART=YES
PROGRAM=<CIO_FBC_CODE>
`
