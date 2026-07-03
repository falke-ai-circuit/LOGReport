package parser

import (
	"testing"
	"strings"
)

// TestSysFileCompositions tests parser against real .sys file compositions
// from different eras: VE-era (101.SYS, 501.SYS), DNA System Configurator (21.sys),
// and ACN-era (161.sys, 1a1.sys).

func TestVE_Era_101_Sys(t *testing.T) {
	// 101.SYS: VE-era, hw_addr=101, token=8, ip=192.168.1.171
	// Slot 1: AP01 (PCS_CODE) — PCS CPU
	// Slot 2: AL01 (PCS_CODE) — LIS station running PCS code
	// Slot 5: AC01 (PCS_CODE) — CIS
	// Slot 6: A1A1 — ALP
	// Slot 10: AD00 — DIA
	content := `set XD_HW_ADDR=101
set XD_HW_TOKEN=8
set XD_IP_ADDR=192.168.1.171

NCU2
AUTOSTART=YES
PROGRAM=D:/dna/Shared/ncu2/<NCU2_PROGRAM>
TITLE=NCU2

Slot 1
PRIORITY=REALTIME
TITLE=AP01
PROGRAM=D:/dna/CA/pcs/program/<PCS_PROGRAM>
PARAMETERS=-cpu ../AP01_10.1_cpu
DEPENDENCIES=2

Slot 2
TITLE=AL01
PROGRAM=D:/dna/CA/pcs/program/<PCS_PROGRAM>
PARAMETERS=-cpu ../AL01_10.1_cpu

Slot 5
TITLE=AC01
PROGRAM=D:/dna/CA/pcs/program/<PCS_PROGRAM>

Slot 6
TITLE=A1A1
PROGRAM=D:\dna\OA\alp\program\<ALP_PROGRAM>

Slot 10
TITLE=AD00
PROGRAM=D:/dna/CA/dia/<DIA_PROGRAM>
`
	result := ParseSysFileString(content)
	if result == nil {
		t.Fatal("ParseSysFileString returned nil")
	}

	// Parser returns all nodes including NCU2 (sysloader filters it later)
	expected := map[string]string{
		"NCU2": "UNKNOWN",
		"AP01": "PCS",
		"AL01": "LIS",
		"AC01": "CIS",
		"A1A1": "ALP",
		"AD00": "DIA",
	}
	if len(result.Nodes) != len(expected) {
		t.Errorf("node count: got %d, want %d", len(result.Nodes), len(expected))
		for _, n := range result.Nodes {
			t.Logf("  got node: LID=%s Type=%s Program=%s", n.LID, n.Type, n.Program)
		}
	}
	for _, n := range result.Nodes {
		expType, ok := expected[n.LID]
		if !ok {
			t.Errorf("unexpected node LID=%s Type=%s", n.LID, n.Type)
			continue
		}
		if n.Type != expType {
			t.Errorf("node %s type: got %s, want %s", n.LID, n.Type, expType)
		}
	}
	if result.IPAddr != "192.168.1.171" {
		t.Errorf("IPAddr: got %q, want %q", result.IPAddr, "192.168.1.171")
	}
}

func TestVE_Era_501_Sys(t *testing.T) {
	// 501.SYS: VE-era, hw_addr=501, token=40, ip=192.168.1.40
	// Slot 1: AL01 (PCS_CODE) — LIS station on separate machine
	// Slot 2: AC01 (PCS_CODE) — CIS
	// Slot 3: A1O6 — OPS
	// Slot 10: AD06 — DIA
	content := `set XD_HW_ADDR=501
set XD_HW_TOKEN=40
set XD_IP_ADDR=192.168.1.40

NCU2
AUTOSTART=YES
PROGRAM=D:/dna/Shared/ncu2/<NCU2_PROGRAM>
TITLE=NCU2

Slot 1
TITLE=AL01
PROGRAM=D:/dna/CA/pcs/program/<PCS_PROGRAM>
PARAMETERS=-cpu ../AL01_10.1_cpu

Slot 2
TITLE=AC01
PROGRAM=D:/dna/CA/pcs/program/<PCS_PROGRAM>

Slot 3
TITLE=A1O6
PROGRAM=D:\dna\OA\use\program\<CDMGR_PROGRAM>

Slot 10
TITLE=AD06
PROGRAM=D:/dna/CA/dia/<DIA_PROGRAM>
`
	result := ParseSysFileString(content)
	if result == nil {
		t.Fatal("ParseSysFileString returned nil")
	}

	expected := map[string]string{
		"NCU2": "UNKNOWN",
		"AL01": "LIS",
		"AC01": "CIS",
		"A1O6": "OPS",
		"AD06": "DIA",
	}
	if len(result.Nodes) != len(expected) {
		t.Errorf("node count: got %d, want %d", len(result.Nodes), len(expected))
		for _, n := range result.Nodes {
			t.Logf("  got node: LID=%s Type=%s", n.LID, n.Type)
		}
	}
	for _, n := range result.Nodes {
		expType, ok := expected[n.LID]
		if !ok {
			t.Errorf("unexpected node LID=%s", n.LID)
			continue
		}
		if n.Type != expType {
			t.Errorf("node %s type: got %s, want %s", n.LID, n.Type, expType)
		}
	}
}

func TestDNAConfigurator_21_Sys(t *testing.T) {
	// 21.sys: DNA System Configurator generated, hw_addr=21, token=1, ip=127.0.0.1
	// Slot 1: AB01 (BU_PROGRAM) — UNKNOWN, should be skipped
	// Slot 2: AP01 (PCS_CODE) — PCS
	// Slot 3: A1O1 (cdmgr.exe) — OPS
	// Slot 6: A1A1 (als.exe) — ALP
	// Slot 10: AD01 — DIA
	// Other infrastructure slots (XComServer, Web Diagnostics, etc.) — UNKNOWN
	content := `set XD_HW_ADDR=21
set XD_HW_TOKEN=1
set XD_IP_ADDR=127.0.0.1

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
	result := ParseSysFileString(content)
	if result == nil {
		t.Fatal("ParseSysFileString returned nil")
	}

	// Should have: AP01(PCS), A1O1(OPS), A1A1(ALP), AD01(DIA),
	// AB01 and XComServer should be UNKNOWN → skipped in sysloader,
	// NCU2 = UNKNOWN (filtered by sysloader)
	expectedTypes := map[string]string{
		"NCU2":                   "UNKNOWN",
		"AP01":                   "PCS",
		"A1O1":                   "OPS",
		"A1A1":                   "ALP",
		"AD01":                   "DIA",
		"AB01":                   "UNKNOWN", // BU program, not in LIDMapping
		"XComServer":             "UNKNOWN",
		"Web Diagnostics Java Server": "UNKNOWN",
	}
	for _, n := range result.Nodes {
		expType, ok := expectedTypes[n.LID]
		if !ok {
			t.Errorf("unexpected node LID=%s Type=%s", n.LID, n.Type)
			continue
		}
		if n.Type != expType {
			t.Errorf("node %s type: got %s, want %s", n.LID, n.Type, expType)
		}
	}
}

func TestACNEra_1a1_Sys_WithLIS(t *testing.T) {
	// 1a1.sys: ACN-era, hw_addr NOT in set lines (only in filename)
	// ip=192.168.1.13
	// Slot 1: AP03_main (PCS_CODE) — PCS CPU
	// Slot 2: AP03_m2 (FBC_CODE) — FBC
	// Slot 3: AP03_m3 (FBC_CODE) — FBC
	// Slot 14: AL03_Remote_monitor (LISDIAG_CODE) — LIS diagnostic monitor
	// Slot 15: AL03 (PCS_CODE) — LIS link station
	content := `set XD_HW_BUS=0
set XD_HW_SWITCH=0
set XD_MCLOCK=XD
set XD_IP_ADDR=192.168.1.13

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
	result := ParseSysFileString(content)
	if result == nil {
		t.Fatal("ParseSysFileString returned nil")
	}

	// Debug: print all nodes
	for _, n := range result.Nodes {
		t.Logf("node: LID=%s Type=%s Program=%s IsFieldbus=%v SlotNum=%d", n.LID, n.Type, n.Program, n.IsFieldbus, n.SlotNum)
	}

	// Expected: NCU2(UNKNOWN), AP03_main(PCS), AP03_m2(PCS/FBC), AP03_m3(PCS/FBC),
	// AL03_Remote_monitor(LIS), AL03(LIS)
	expectedTypes := map[string]string{
		"NCU2":                 "UNKNOWN",
		"AP03_main":            "PCS",
		"AP03_m2":              "PCS",
		"AP03_m3":              "PCS",
		"AL03_Remote_monitor":  "LIS",
		"AL03":                 "LIS",
	}
	for _, n := range result.Nodes {
		expType, ok := expectedTypes[n.LID]
		if !ok {
			t.Errorf("unexpected node LID=%s Type=%s", n.LID, n.Type)
			continue
		}
		if n.Type != expType {
			t.Errorf("node %s type: got %s, want %s", n.LID, n.Type, expType)
		}
	}

	// Verify fieldbus detection
	for _, n := range result.Nodes {
		if strings.Contains(n.Program, "FBC_CODE") && !n.IsFieldbus {
			t.Errorf("node %s has FBC_CODE but IsFieldbus=false", n.LID)
		}
	}

	// Verify slot numbers are tracked
	slotNums := map[string]int{}
	for _, n := range result.Nodes {
		slotNums[n.LID] = n.SlotNum
	}
	if slotNums["AL03"] != 15 {
		t.Errorf("AL03 SlotNum: got %d, want 15", slotNums["AL03"])
	}
	if slotNums["AL03_Remote_monitor"] != 14 {
		t.Errorf("AL03_Remote_monitor SlotNum: got %d, want 14", slotNums["AL03_Remote_monitor"])
	}
	if slotNums["AP03_m2"] != 2 {
		t.Errorf("AP03_m2 SlotNum: got %d, want 2", slotNums["AP03_m2"])
	}
}

func TestACNEra_161_Sys_NoLIS(t *testing.T) {
	// 161.sys: ACN-era, no LIS nodes
	// Slot 1: AP01_main (PCS_CODE)
	// Slot 2: AP01_m2 (FBC_CODE)
	// Slot 3: AP01_m3 (FBC_CODE)
	content := `set XD_HW_BUS=0
set XD_IP_ADDR=192.168.1.11

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
	result := ParseSysFileString(content)
	if result == nil {
		t.Fatal("ParseSysFileString returned nil")
	}

	for _, n := range result.Nodes {
		t.Logf("node: LID=%s Type=%s Program=%s IsFieldbus=%v SlotNum=%d", n.LID, n.Type, n.Program, n.IsFieldbus, n.SlotNum)
	}

	// Should have 4 nodes including NCU2 (sysloader filters it later)
	if len(result.Nodes) != 4 {
		t.Errorf("node count: got %d, want 4", len(result.Nodes))
	}

	// AP01_m2 and AP01_m3 should be fieldbus
	fbcCount := 0
	for _, n := range result.Nodes {
		if n.IsFieldbus {
			fbcCount++
		}
	}
	if fbcCount != 2 {
		t.Errorf("fieldbus count: got %d, want 2", fbcCount)
	}
}

func TestACNEra_ReserveNodes(t *testing.T) {
	// 361.sys: ACN-era reserve node
	// Slot 1: AP01_reserve (PCS_CODE) — PCS reserve
	// Slot 2: AP01_r2 (FBC_CODE) — FBC reserve
	// Slot 3: AP01_r3 (FBC_CODE) — FBC reserve
	content := `set XD_IP_ADDR=192.168.1.27

NCU2
AUTOSTART=YES
TITLE=NCU2
PROGRAM=<NCU2_CODE>

Slot 1
TITLE=AP01_reserve
PROGRAM=<PCS_CODE>
PARAMETERS=-cpu :s:<bu>:AP01_reserve_cpu
DEPENDENCIES=2,3

Slot 2
TITLE=AP01_r2
PROGRAM=<FBC_CODE>
PARAMETERS=-fixed_eth

Slot 3
TITLE=AP01_r3
PROGRAM=<FBC_CODE>
PARAMETERS=-fixed_eth
`
	result := ParseSysFileString(content)
	if result == nil {
		t.Fatal("ParseSysFileString returned nil")
	}

	for _, n := range result.Nodes {
		t.Logf("node: LID=%s Type=%s SlotNum=%d", n.LID, n.Type, n.SlotNum)
	}

	// Verify slot tracking
	for _, n := range result.Nodes {
		if n.LID == "AP01_reserve" && n.SlotNum != 1 {
			t.Errorf("AP01_reserve SlotNum: got %d, want 1", n.SlotNum)
		}
		if n.LID == "AP01_r2" && n.SlotNum != 2 {
			t.Errorf("AP01_r2 SlotNum: got %d, want 2", n.SlotNum)
		}
		if n.LID == "AP01_r3" && n.SlotNum != 3 {
			t.Errorf("AP01_r3 SlotNum: got %d, want 3", n.SlotNum)
		}
	}
}

func TestMixedEra_BU_Nodes(t *testing.T) {
	// 5a1.sys: BU node with multiple infrastructure programs
	// Slot 3: A1O1 — OPS
	// Slot 8: XNTP — UNKNOWN (not in LIDMapping)
	// Slot 10: AD01 — DIA
	// Slot 14: AM01 — MAINT
	// Slot 15: AB01 — UNKNOWN (BU program)
	content := `set XD_HW_ADDR=5a1
set XD_HW_TOKEN=45
set XD_IP_ADDR=192.168.1.45

NCU2
AUTOSTART=YES
TITLE=NCU2
PROGRAM=<NCU2_CODE>

Slot 3
TITLE=A1O1
PROGRAM=D:\dna\OA\use\program\<CDMGR_PROGRAM>

Slot 8
TITLE=XNTP
PROGRAM=D:/dna/CA/XDNTP/<XDNTP_PROGRAM>

Slot 10
TITLE=AD01
PROGRAM=D:/dna/CA/dia/<DIA_PROGRAM>

Slot 14
TITLE=AM01
PROGRAM=D:\DNA\EA\Web\Maintenance/bin/webxcom.exe

Slot 15
TITLE=AB01
PROGRAM=D:/dna/CA/bu/<BU_PROGRAM>
`
	result := ParseSysFileString(content)
	if result == nil {
		t.Fatal("ParseSysFileString returned nil")
	}

	for _, n := range result.Nodes {
		t.Logf("node: LID=%s Type=%s", n.LID, n.Type)
	}

	// XNTP and AB01 should be UNKNOWN
	typeMap := map[string]string{}
	for _, n := range result.Nodes {
		typeMap[n.LID] = n.Type
	}
	if typeMap["XNTP"] != "UNKNOWN" {
		t.Errorf("XNTP type: got %s, want UNKNOWN", typeMap["XNTP"])
	}
	if typeMap["AB01"] != "UNKNOWN" {
		t.Errorf("AB01 type: got %s, want UNKNOWN", typeMap["AB01"])
	}
	if typeMap["AD01"] != "DIA" {
		t.Errorf("AD01 type: got %s, want DIA", typeMap["AD01"])
	}
}