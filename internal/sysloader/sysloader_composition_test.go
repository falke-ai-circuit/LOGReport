package sysloader

import (
	"os"
	"path/filepath"
	"testing"

	"github.com/falke-ai-circuit/LOGReport/internal/types"
)

// writeSysFile creates a temporary .sys file and returns its path.
func writeSysFile(t *testing.T, name, content string) string {
	t.Helper()
	dir := t.TempDir()
	path := filepath.Join(dir, name)
	if err := os.WriteFile(path, []byte(content), 0644); err != nil {
		t.Fatal(err)
	}
	return path
}

// TestVE_Era_101_WithLIS tests that AL01 in slot 2 of 101.SYS gets correct LIS token.
// 101.SYS: hw_addr=101, token=8, ip=192.168.1.171
// Slot 1: AP01 (PCS_CODE) → LOG-only (CPU slot)
// Slot 2: AL01 (PCS_CODE) → LIS token (token ID = 101 + 1 = 102)
func TestVE_Era_101_WithLIS(t *testing.T) {
	content := `set XD_HW_ADDR=101
set XD_HW_TOKEN=8
set XD_IP_ADDR=192.168.1.171

NCU2
AUTOSTART=YES
TITLE=NCU2
PROGRAM=<NCU2_CODE>

Slot 1
TITLE=AP01
PROGRAM=D:/dna/CA/pcs/program/<PCS_PROGRAM>
PARAMETERS=-cpu ../AP01_10.1_cpu

Slot 2
TITLE=AL01
PROGRAM=D:/dna/CA/pcs/program/<PCS_PROGRAM>
PARAMETERS=-cpu ../AL01_10.1_cpu
`
	path := writeSysFile(t, "101.SYS", content)
	configs, err := LoadSysFilesFromPaths([]string{path})
	if err != nil {
		t.Fatal(err)
	}

	// Should have 2 nodes: AP01 (LOG only) and AL01 (LIS)
	if len(configs) != 2 {
		t.Fatalf("config count: got %d, want 2", len(configs))
		for _, c := range configs {
			t.Logf("  config: Name=%s IP=%s Tokens=%v", c.Name, c.IPAddress, c.Tokens)
		}
	}

	// Find AL01
	var al01 *types.NodeConfig
	for i := range configs {
		if configs[i].Name == "AL01" {
			al01 = &configs[i]
			break
		}
	}
	if al01 == nil {
		t.Fatal("AL01 node not found")
	}
	t.Logf("AL01: IP=%s Tokens=%v", al01.IPAddress, al01.Tokens)

	// AL01 should have a LIS token
	hasLIS := false
	for _, tok := range al01.Tokens {
		if tok.TokenType == types.TokenLIS {
			hasLIS = true
			// Token ID should be base(101) + slot_offset(2-1=1) = 102
			if tok.TokenID != "102" {
				t.Errorf("AL01 LIS token ID: got %s, want 102", tok.TokenID)
			}
		}
	}
	if !hasLIS {
		t.Error("AL01 should have a LIS token")
	}

	// IP should be from .sys file
	if al01.IPAddress != "192.168.1.171" {
		t.Errorf("AL01 IP: got %s, want 192.168.1.171", al01.IPAddress)
	}
}

// TestVE_Era_501_SeparateMachine tests AL01 on a separate machine (501.SYS).
// 501.SYS: hw_addr=501, token=40, ip=192.168.1.40
// Slot 1: AL01 (PCS_CODE) → LIS token (token ID = 501, no offset since slot 1)
func TestVE_Era_501_SeparateMachine(t *testing.T) {
	content := `set XD_HW_ADDR=501

set XD_HW_TOKEN=***
set XD_IP_ADDR=192.168.1.40

NCU2
AUTOSTART=YES
TITLE=NCU2
PROGRAM=<NCU2_CODE>

Slot 1
TITLE=AL01
PROGRAM=D:/dna/CA/pcs/program/<PCS_PROGRAM>
PARAMETERS=-cpu ../AL01_10.1_cpu
`
	path := writeSysFile(t, "501.SYS", content)
	configs, err := LoadSysFilesFromPaths([]string{path})
	if err != nil {
		t.Fatal(err)
	}

	if len(configs) != 1 {
		t.Fatalf("config count: got %d, want 1", len(configs))
		for _, c := range configs {
			t.Logf("  config: Name=%s IP=%s Tokens=%v", c.Name, c.IPAddress, c.Tokens)
		}
	}

	if configs[0].Name != "AL01" {
		t.Fatalf("node name: got %s, want AL01", configs[0].Name)
	}

	// AL01 should have a LIS token with ID = 501 (slot 1, no offset)
	hasLIS := false
	for _, tok := range configs[0].Tokens {
		if tok.TokenType == types.TokenLIS {
			hasLIS = true
			if tok.TokenID != "501" {
				t.Errorf("AL01 LIS token ID: got %s, want 501", tok.TokenID)
			}
		}
	}
	if !hasLIS {
		t.Error("AL01 should have a LIS token")
	}
}

// TestACNEra_1a1_WithLIS tests the ACN-era composition with both PCS and LIS.
// 1a1.sys: ip=192.168.1.13, file stem = 1a1
// Slot 1: AP03_main (PCS_CODE) → LOG-only (CPU)
// Slot 2: AP03_m2 (FBC_CODE) → FBC + RPC (token = 1a1 + 1 = 1a2)
// Slot 3: AP03_m3 (FBC_CODE) → FBC + RPC (token = 1a1 + 2 = 1a3)
// Slot 14: AL03_Remote_monitor (LISDIAG_CODE) → LIS token (token = 1a1 + 13 = 1ae)
// Slot 15: AL03 (PCS_CODE) → LIS token (token = 1a1 + 14 = 1af)
func TestACNEra_1a1_WithLIS(t *testing.T) {
	content := `set XD_IP_ADDR=192.168.1.13

NCU2
AUTOSTART=YES
TITLE=NCU2
PROGRAM=<NCU2_CODE>

Slot 1
TITLE=AP03_main
PROGRAM=<PCS_CODE>
PARAMETERS=-cpu :s:<bu>:AP03_10.1_cpu
DEPENDENCIES=2,3

Slot 2
TITLE=AP03_m2
PROGRAM=<FBC_CODE>
PARAMETERS=-fixed_eth
DEPENDENCIES=1

Slot 3
TITLE=AP03_m3
PROGRAM=<FBC_CODE>
PARAMETERS=-fixed_eth
DEPENDENCIES=1

Slot 14
TITLE=AL03_Remote_monitor
PROGRAM=<LISDIAG_CODE>

Slot 15
TITLE=AL03
PROGRAM=<PCS_CODE>
`
	path := writeSysFile(t, "1a1.sys", content)
	configs, err := LoadSysFilesFromPaths([]string{path})
	if err != nil {
		t.Fatal(err)
	}

	t.Logf("configs: %d", len(configs))
	for _, c := range configs {
		t.Logf("  Name=%s IP=%s Tokens=%v", c.Name, c.IPAddress, c.Tokens)
	}

	// Should have: AP03_main, AP03_m2, AP03_m3, AL03_Remote_monitor, AL03
	// (NCU2 filtered)
	if len(configs) != 5 {
		t.Errorf("config count: got %d, want 5", len(configs))
	}

	// Find AL03 (the actual LIS link station, not the monitor)
	var al03 *types.NodeConfig
	var al03Mon *types.NodeConfig
	for i := range configs {
		if configs[i].Name == "AL03" {
			al03 = &configs[i]
		}
		if configs[i].Name == "AL03_Remote_monitor" {
			al03Mon = &configs[i]
		}
	}

	if al03 == nil {
		t.Fatal("AL03 node not found")
	}
	if al03Mon == nil {
		t.Fatal("AL03_Remote_monitor node not found")
	}

	// AL03 (slot 15) should have LIS token with ID = 1a1 + 14 = 1af
	for _, tok := range al03.Tokens {
		t.Logf("AL03 token: type=%s id=%s", tok.TokenType, tok.TokenID)
		if tok.TokenType == types.TokenLIS {
			if tok.TokenID != "1af" {
				t.Errorf("AL03 LIS token ID: got %s, want 1af (1a1 + 14)", tok.TokenID)
			}
		}
	}

	// AL03_Remote_monitor (slot 14) should have LIS token with ID = 1a1 + 13 = 1ae
	for _, tok := range al03Mon.Tokens {
		t.Logf("AL03_Remote_monitor token: type=%s id=%s", tok.TokenType, tok.TokenID)
		if tok.TokenType == types.TokenLIS {
			if tok.TokenID != "1ae" {
				t.Errorf("AL03_Remote_monitor LIS token ID: got %s, want 1ae (1a1 + 13)", tok.TokenID)
			}
		}
	}

	// AP03_m2 (slot 2) should have FBC token with ID = 1a1 + 1 = 1a2
	for _, c := range configs {
		if c.Name == "AP03_m2" {
			for _, tok := range c.Tokens {
				if tok.TokenType == types.TokenFBC {
					if tok.TokenID != "1a2" {
						t.Errorf("AP03_m2 FBC token ID: got %s, want 1a2 (1a1 + 1)", tok.TokenID)
					}
				}
			}
		}
	}
}

// TestACNEra_161_NoLIS tests a pure ACN PCS+FBC node without LIS.
func TestACNEra_161_NoLIS(t *testing.T) {
	content := `set XD_IP_ADDR=192.168.1.11

NCU2
AUTOSTART=YES
TITLE=NCU2
PROGRAM=<NCU2_CODE>

Slot 1
TITLE=AP01_main
PROGRAM=<PCS_CODE>
PARAMETERS=-cpu :s:<bu>:AP01_10.1_cpu
DEPENDENCIES=2,3

Slot 2
TITLE=AP01_m2
PROGRAM=<FBC_CODE>
PARAMETERS=-fixed_eth
DEPENDENCIES=1

Slot 3
TITLE=AP01_m3
PROGRAM=<FBC_CODE>
PARAMETERS=-fixed_eth
DEPENDENCIES=1
`
	path := writeSysFile(t, "161.sys", content)
	configs, err := LoadSysFilesFromPaths([]string{path})
	if err != nil {
		t.Fatal(err)
	}

	t.Logf("configs: %d", len(configs))
	for _, c := range configs {
		t.Logf("  Name=%s IP=%s Tokens=%v", c.Name, c.IPAddress, c.Tokens)
	}

	// Should have 3 nodes: AP01_main, AP01_m2, AP01_m3
	if len(configs) != 3 {
		t.Errorf("config count: got %d, want 3", len(configs))
	}

	// AP01_main should have LOG-only token (CPU slot, PROGRAM=PCS_CODE)
	for _, c := range configs {
		if c.Name == "AP01_main" {
			if len(c.Tokens) != 1 || c.Tokens[0].TokenType != types.TokenLOG {
				t.Errorf("AP01_main should have LOG-only token, got %v", c.Tokens)
			}
		}
	}

	// AP01_m2 should have FBC + RPC tokens
	for _, c := range configs {
		if c.Name == "AP01_m2" {
			hasFBC, hasRPC := false, false
			for _, tok := range c.Tokens {
				if tok.TokenType == types.TokenFBC {
					hasFBC = true
					if tok.TokenID != "162" {
						t.Errorf("AP01_m2 FBC token: got %s, want 162", tok.TokenID)
					}
				}
				if tok.TokenType == types.TokenRPC {
					hasRPC = true
					if tok.TokenID != "162" {
						t.Errorf("AP01_m2 RPC token: got %s, want 162", tok.TokenID)
					}
				}
			}
			if !hasFBC || !hasRPC {
				t.Errorf("AP01_m2 should have FBC+RPC, got FBC=%v RPC=%v", hasFBC, hasRPC)
			}
		}
	}
}

// TestMultiFileImport tests loading multiple .sys files that contain the same
// LIS node name on different hardware.
// 101.SYS has AL01 in slot 2 (co-located with PCS), 501.SYS has AL01 in slot 1
// (separate machine). The sysloader should merge these as separate nodes since
// they have different IPs and tokens.
func TestMultiFileImport_SameNodeDifferentMachine(t *testing.T) {
	content101 := `set XD_HW_ADDR=101

set XD_HW_TOKEN=***
set XD_IP_ADDR=192.168.1.171

NCU2
AUTOSTART=YES
TITLE=NCU2
PROGRAM=<NCU2_CODE>

Slot 1
TITLE=AP01
PROGRAM=<PCS_CODE>

Slot 2
TITLE=AL01
PROGRAM=<PCS_CODE>
`
	content501 := `set XD_HW_ADDR=501

set XD_HW_TOKEN=***
set XD_IP_ADDR=192.168.1.40

NCU2
AUTOSTART=YES
TITLE=NCU2
PROGRAM=<NCU2_CODE>

Slot 1
TITLE=AL01
PROGRAM=<PCS_CODE>
`
	path101 := writeSysFile(t, "101.SYS", content101)
	path501 := writeSysFile(t, "501.SYS", content501)
	configs, err := LoadSysFilesFromPaths([]string{path101, path501})
	if err != nil {
		t.Fatal(err)
	}

	t.Logf("configs: %d", len(configs))
	for _, c := range configs {
		t.Logf("  Name=%s IP=%s Tokens=%v", c.Name, c.IPAddress, c.Tokens)
	}

	// AL01 appears in both files with different IPs/tokens — they should merge
	// into ONE node with multiple LIS tokens (one per .sys file)
	var al01 *types.NodeConfig
	for i := range configs {
		if configs[i].Name == "AL01" {
			al01 = &configs[i]
			break
		}
	}
	if al01 == nil {
		t.Fatal("AL01 node not found")
	}
	t.Logf("AL01 merged: IP=%s Tokens=%v", al01.IPAddress, al01.Tokens)

	// Should have 2 LIS tokens: 102 (from 101.SYS slot 2) and 501 (from 501.SYS slot 1)
	lisCount := 0
	for _, tok := range al01.Tokens {
		if tok.TokenType == types.TokenLIS {
			lisCount++
		}
	}
	if lisCount != 2 {
		t.Errorf("AL01 should have 2 LIS tokens (one per .sys file), got %d", lisCount)
	}
}