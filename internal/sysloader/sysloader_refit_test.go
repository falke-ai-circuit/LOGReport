package sysloader

import (
	"testing"

	"github.com/falke-ai-circuit/LOGReport/internal/types"
)

// TestSolstice_BeforeRefit_SameHardware tests the pre-refit composition where
// AP (PCS) and AL (LIS) stations run on the SAME hardware — both in one .sys file.
// This is the old VME-era pattern: one machine runs PCS in slot 1, LIS in slot 2,
// FBC cards in slots 3-4.
//
// Example: Solstice before refit — AP01 + AL01 on hw_addr=161 (one ACN node)
// Slot 1: AP01_main (PCS_CODE) — process control
// Slot 2: AL01 (PCS_CODE) — link station (LIS), same machine
// Slot 3: AP01_m2 (FBC_CODE) — fieldbus card
// Slot 4: AP01_m3 (FBC_CODE) — fieldbus card
func TestSolstice_BeforeRefit_SameHardware(t *testing.T) {
	content := `set XD_HW_BUS=0
set XD_HW_SWITCH=0
set XD_MCLOCK=XD
set XD_IP_ADDR=192.168.1.11

NCU2
AUTOSTART=YES
TITLE=NCU2
PROGRAM=<NCU2_CODE>

Slot 1
TITLE=AP01_main
PROGRAM=<PCS_CODE>
PARAMETERS=-cpu :s:<bu>:AP01_10.1_cpu
DEPENDENCIES=3,4

Slot 2
TITLE=AL01
PROGRAM=<PCS_CODE>
PARAMETERS=-cpu :s:<bu>:AL01_10.1_cpu

Slot 3
TITLE=AP01_m2
PROGRAM=<FBC_CODE>
PARAMETERS=-fixed_eth
DEPENDENCIES=1

Slot 4
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

	t.Logf("Before refit — same hardware (161.sys):")
	for _, c := range configs {
		t.Logf("  Name=%s IP=%s Tokens=%v", c.Name, c.IPAddress, c.Tokens)
	}

	// Should have 4 nodes: AP01_main, AL01, AP01_m2, AP01_m3
	if len(configs) != 4 {
		t.Errorf("config count: got %d, want 4", len(configs))
	}

	// AL01 should have LIS token with ID = 161 + 1 = 162 (slot 2)
	var al01 *types.NodeConfig
	for i := range configs {
		if configs[i].Name == "AL01" {
			al01 = &configs[i]
			break
		}
	}
	if al01 == nil {
		t.Fatal("AL01 not found")
	}

	hasLIS := false
	for _, tok := range al01.Tokens {
		if tok.TokenType == types.TokenLIS {
			hasLIS = true
			if tok.TokenID != "162" {
				t.Errorf("AL01 LIS token ID: got %s, want 162 (161 + slot_offset 1)", tok.TokenID)
			}
		}
	}
	if !hasLIS {
		t.Error("AL01 should have LIS token")
	}

	// AL01 and AP01_main should have SAME IP (same machine)
	var ap01 *types.NodeConfig
	for i := range configs {
		if configs[i].Name == "AP01_main" {
			ap01 = &configs[i]
			break
		}
	}
	if ap01 != nil && al01 != nil {
		if ap01.IPAddress != al01.IPAddress {
			t.Errorf("AP01 IP (%s) != AL01 IP (%s) — should be same machine",
				ap01.IPAddress, al01.IPAddress)
		}
		t.Logf("  ✓ AP01 and AL01 on same machine: IP=%s", ap01.IPAddress)
	}
}

// TestSolstice_AfterRefit_SeparateHardware tests the post-refit composition where
// AP (PCS) and AL (LIS) stations run on SEPARATE hardware — different .sys files.
// The AL station was moved to its own dedicated machine.
//
// Example: Solstice after refit — AP01 on hw_addr=161, AL01 on hw_addr=501
// 161.sys: AP01_main (slot 1), AP01_m2 (slot 2 FBC), AP01_m3 (slot 3 FBC)
// 501.sys: AL01 (slot 1), AC01 (slot 2)
func TestSolstice_AfterRefit_SeparateHardware(t *testing.T) {
	content161 := `set XD_IP_ADDR=192.168.1.11

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
	content501 := `set XD_HW_ADDR=501
set XD_HW_TOKEN=40
set XD_IP_ADDR=192.168.1.40

NCU2
AUTOSTART=YES
TITLE=NCU2
PROGRAM=<NCU2_CODE>

Slot 1
TITLE=AL01
PROGRAM=<PCS_CODE>
PARAMETERS=-cpu ../AL01_10.1_cpu

Slot 2
TITLE=AC01
PROGRAM=<PCS_CODE>
`

	path161 := writeSysFile(t, "161.sys", content161)
	path501 := writeSysFile(t, "501.SYS", content501)
	configs, err := LoadSysFilesFromPaths([]string{path161, path501})
	if err != nil {
		t.Fatal(err)
	}

	t.Logf("After refit — separate hardware (161.sys + 501.SYS):")
	for _, c := range configs {
		t.Logf("  Name=%s IP=%s Tokens=%v", c.Name, c.IPAddress, c.Tokens)
	}

	// Should have: AP01_main, AP01_m2, AP01_m3, AL01, AC01
	if len(configs) != 5 {
		t.Errorf("config count: got %d, want 5", len(configs))
	}

	// AL01 should be on different IP than AP01_main
	var al01, ap01 *types.NodeConfig
	for i := range configs {
		if configs[i].Name == "AL01" {
			al01 = &configs[i]
		}
		if configs[i].Name == "AP01_main" {
			ap01 = &configs[i]
		}
	}
	if al01 == nil {
		t.Fatal("AL01 not found")
	}
	if ap01 == nil {
		t.Fatal("AP01_main not found")
	}

	if al01.IPAddress == ap01.IPAddress {
		t.Errorf("AL01 IP (%s) == AP01 IP (%s) — should be different machines",
			al01.IPAddress, ap01.IPAddress)
	} else {
		t.Logf("  ✓ AP01 on %s, AL01 on %s — separate machines", ap01.IPAddress, al01.IPAddress)
	}

	// AL01 LIS token ID should be 501 (slot 1, no offset)
	for _, tok := range al01.Tokens {
		if tok.TokenType == types.TokenLIS {
			if tok.TokenID != "501" {
				t.Errorf("AL01 LIS token ID: got %s, want 501", tok.TokenID)
			} else {
				t.Logf("  ✓ AL01 LIS token = 501 (separate hardware)")
			}
		}
	}
}

// TestCostaAtlantica_OldVME_System tests old VME-era .sys file format.
// VME systems used the :e:hw: token mapping format instead of Slot definitions.
// Each node has a hardware address that serves as both the VME bus address
// and the token ID for FBC/RPC commands.
//
// Example composition:
// :e:hw:161 AP01 pxe:AP01      — PCS, hw_addr=161
// :e:hw:162 AP01_m2 pxe:AP01m2  — FBC, hw_addr=162 (161+1)
// :e:hw:163 AP01_m3 pxe:AP01m3  — FBC, hw_addr=163 (161+2)
// :e:hw:164 AL01 pxe:AL01       — LIS, hw_addr=164 (161+3, same VME crate)
func TestCostaAtlantica_OldVME_System(t *testing.T) {
	content := `// Old VME-era sys file with :e:hw: token mapping
set XD_HW_ADDR=161
set XD_HW_TOKEN=10
set XD_IP_ADDR=192.168.0.11

:e:hw:161 AP01 pxe:AP01
:e:hw:162 AP01_m2 pxe:AP01m2
:e:hw:163 AP01_m3 pxe:AP01m3
:e:hw:164 AL01 pxe:AL01
`
	path := writeSysFile(t, "161.sys", content)
	configs, err := LoadSysFilesFromPaths([]string{path})
	if err != nil {
		t.Fatal(err)
	}

	t.Logf("Costa Atlantica — old VME format (:e:hw: entries):")
	for _, c := range configs {
		t.Logf("  Name=%s IP=%s Tokens=%v", c.Name, c.IPAddress, c.Tokens)
	}

	// Should have 4 nodes: AP01, AP01_m2, AP01_m3, AL01
	if len(configs) != 4 {
		t.Errorf("config count: got %d, want 4", len(configs))
	}

	// AL01 should have LIS token with hw_addr=164
	var al01 *types.NodeConfig
	for i := range configs {
		if configs[i].Name == "AL01" {
			al01 = &configs[i]
			break
		}
	}
	if al01 == nil {
		t.Fatal("AL01 not found")
	}
	t.Logf("  AL01: IP=%s Tokens=%v", al01.IPAddress, al01.Tokens)

	hasLIS := false
	for _, tok := range al01.Tokens {
		if tok.TokenType == types.TokenLIS {
			hasLIS = true
			if tok.TokenID != "164" {
				t.Errorf("AL01 LIS token ID: got %s, want 164", tok.TokenID)
			}
		}
	}
	if !hasLIS {
		t.Error("AL01 should have LIS token")
	}

	// AP01_m2 should have FBC+RPC tokens with hw_addr=162
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
				}
			}
			if !hasFBC || !hasRPC {
				t.Errorf("AP01_m2 should have FBC+RPC, got FBC=%v RPC=%v", hasFBC, hasRPC)
			}
		}
	}

	// All nodes should have the same IP (same VME crate, same machine)
	for _, c := range configs {
		if c.IPAddress != "192.168.0.11" {
			t.Errorf("node %s IP: got %s, want 192.168.0.11", c.Name, c.IPAddress)
		}
	}
}

// TestSplitHardware_TwoMachines tests a project where AP and AL are split across
// two separate machines (ACN nodes). This represents a refit where the LIS station
// was moved from the PCS cabinet to its own dedicated ACN cabinet.
//
// Machine A (161.sys): AP01_main + FBC cards
// Machine B (181.sys): AL02 + its own FBC card (if any)
// Machine C (501.sys): AL01 standalone (no FBC, just LIS)
func TestSplitHardware_ThreeMachines(t *testing.T) {
	content161 := `set XD_IP_ADDR=192.168.1.11

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
	content181 := `set XD_IP_ADDR=192.168.1.12

NCU2
AUTOSTART=YES
TITLE=NCU2
PROGRAM=<NCU2_CODE>

Slot 1
TITLE=AP02_main
PROGRAM=<PCS_CODE>
PARAMETERS=-cpu :s:<bu>:AP02_10.1_cpu
DEPENDENCIES=2

Slot 2
TITLE=AP02_m2
PROGRAM=<FBC_CODE>
PARAMETERS=-fixed_eth
DEPENDENCIES=1

Slot 14
TITLE=AL02_Remote_monitor
PROGRAM=<LISDIAG_CODE>

Slot 15
TITLE=AL02
PROGRAM=<PCS_CODE>
`
	content501 := `set XD_HW_ADDR=501
set XD_HW_TOKEN=40
set XD_IP_ADDR=192.168.1.40

NCU2
AUTOSTART=YES
TITLE=NCU2
PROGRAM=<NCU2_CODE>

Slot 1
TITLE=AL01
PROGRAM=<PCS_CODE>
PARAMETERS=-cpu ../AL01_10.1_cpu
`

	path161 := writeSysFile(t, "161.sys", content161)
	path181 := writeSysFile(t, "181.sys", content181)
	path501 := writeSysFile(t, "501.SYS", content501)

	configs, err := LoadSysFilesFromPaths([]string{path161, path181, path501})
	if err != nil {
		t.Fatal(err)
	}

	t.Logf("Split hardware — 3 machines (161 + 181 + 501):")
	for _, c := range configs {
		t.Logf("  Name=%s IP=%s Tokens=%v", c.Name, c.IPAddress, c.Tokens)
	}

	// Expected nodes:
	// Machine A (161): AP01_main(LOG), AP01_m2(FBC+RPC), AP01_m3(FBC+RPC)
	// Machine B (181): AP02_main(LOG), AP02_m2(FBC+RPC), AL02(LIS)
	// Machine C (501): AL01(LIS)
	// AL02_Remote_monitor EXCLUDED (LISDIAG_CODE — diagnostic slot)

	// Verify AL01 is standalone (only LIS token, no FBC/RPC)
	for _, c := range configs {
		if c.Name == "AL01" {
			if len(c.Tokens) != 1 {
				t.Errorf("AL01 should have exactly 1 token (LIS only), got %d", len(c.Tokens))
			}
			if c.Tokens[0].TokenType != types.TokenLIS {
				t.Errorf("AL01 token should be LIS, got %s", c.Tokens[0].TokenType)
			}
			if c.IPAddress != "192.168.1.40" {
				t.Errorf("AL01 IP: got %s, want 192.168.1.40", c.IPAddress)
			}
			t.Logf("  ✓ AL01 standalone: IP=%s token=%s", c.IPAddress, c.Tokens[0].TokenID)
		}
	}

	// Verify AL02 has LIS token (AL02_Remote_monitor is EXCLUDED — LISDIAG_CODE)
	var al02 *types.NodeConfig
	for i := range configs {
		if configs[i].Name == "AL02" {
			al02 = &configs[i]
		}
	}
	if al02 != nil {
		for _, tok := range al02.Tokens {
			if tok.TokenType == types.TokenLIS {
				// 181 + 14 = 18f (slot 15 → offset 14)
				if tok.TokenID != "18f" {
					t.Errorf("AL02 LIS token: got %s, want 18f (181 + 14)", tok.TokenID)
				} else {
					t.Logf("  ✓ AL02 LIS token = 18f")
				}
			}
		}
	}
	// AL02_Remote_monitor should NOT be present
	for i := range configs {
		if configs[i].Name == "AL02_Remote_monitor" {
			t.Fatal("AL02_Remote_monitor should be excluded (LISDIAG_CODE)")
		}
	}

	// Verify AP01 and AP02 have different IPs
	var ap01, ap02 *types.NodeConfig
	for i := range configs {
		if configs[i].Name == "AP01_main" {
			ap01 = &configs[i]
		}
		if configs[i].Name == "AP02_main" {
			ap02 = &configs[i]
		}
	}
	if ap01 != nil && ap02 != nil {
		if ap01.IPAddress == ap02.IPAddress {
			t.Errorf("AP01 (%s) and AP02 (%s) should have different IPs", ap01.IPAddress, ap02.IPAddress)
		}
	}
}

// TestDNASystemConfigurator_GeneratedFile tests a DNA System Configurator
// auto-generated .sys file. These files have a different header format and
// may include infrastructure slots (XComServer, Web Diagnostics, BU, etc.)
// that should be filtered as UNKNOWN type.
func TestDNASystemConfigurator_GeneratedFile(t *testing.T) {
	content := `// #CNC-GENERATED#
// THIS FILE IS AUTOMATICALLY GENERATED BY DNA SYSTEM CONFIGURATOR.
// Generated: 2023:02:27 13:48:51 on EAS-C2022 by user Administrator
// DNA System Configurator version 2.3.11841

set STARTER_NO_WINDOWS_MODE=1
set XD_HW_BUS=A
set XD_HW_ADDR=21
set XD_HW_TOKEN=1
set XD_IP_ADDR=127.0.0.1
set XD_HW_MCAST=239.0.171.0
set XD_MCLOCK=MASTER!

NCU2
AUTOSTART=YES
PROGRAM=C:\dna\Shared\ncu2\<NCU2_PROGRAM>
TITLE=NCU2

Slot 6
TITLE=A1A1
PROGRAM=C:\dna\OA\alp\program\als.exe

Slot 1
TITLE=AB01
PROGRAM=C:\dna\CA\BU\<BU_PROGRAM>

Slot 10
TITLE=AD01
PROGRAM=C:\dna\CA\dia\<DIA_PROGRAM>

Slot 2
TITLE=AP01
PROGRAM=C:\dna\CA\pcs\program\<PCS_PROGRAM>

Slot 3
TITLE=A1O1
PROGRAM=C:\dna\OA\use\program\cdmgr.exe

Slot 11
TITLE=XComServer
PROGRAM=C:\dna\EA\web\diagnostics\programs\rmixcom.exe

Slot 17
TITLE=Web Diagnostics Java Server
PROGRAM=%XD_WEBTOOLS_JAVA%\bin\java.exe
`
	path := writeSysFile(t, "21.sys", content)
	configs, err := LoadSysFilesFromPaths([]string{path})
	if err != nil {
		t.Fatal(err)
	}

	t.Logf("DNA System Configurator generated file:")
	for _, c := range configs {
		t.Logf("  Name=%s IP=%s Tokens=%v", c.Name, c.IPAddress, c.Tokens)
	}

	// Should have: AP01(PCS/LOG), A1O1(OPS/LOG), A1A1(ALP/LOG), AD01(DIA/LOG)
	// AB01, XComServer, Web Diagnostics = UNKNOWN → filtered
	if len(configs) != 4 {
		t.Errorf("config count: got %d, want 4 (UNKNOWN types should be filtered)", len(configs))
	}

	// Verify AP01 gets LOG-only (CPU slot with PCS_CODE)
	// Note: AP01 is in Slot 2 (after AB01 in Slot 1), so token = 21 + 1 = 22
	for _, c := range configs {
		if c.Name == "AP01" {
			for _, tok := range c.Tokens {
				if tok.TokenType != types.TokenLOG {
					t.Errorf("AP01 should only have LOG token (CPU slot), got %s", tok.TokenType)
				}
			}
			if len(c.Tokens) > 0 && c.Tokens[0].TokenID != "22" {
				t.Errorf("AP01 token ID: got %s, want 22 (21 + slot_offset 1, slot 2)", c.Tokens[0].TokenID)
			}
		}
	}

	// Verify IP is 127.0.0.1 (VM test config)
	for _, c := range configs {
		if c.IPAddress != "127.0.0.1" {
			t.Errorf("node %s IP: got %s, want 127.0.0.1", c.Name, c.IPAddress)
		}
	}
}