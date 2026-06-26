package bstool

import (
	"testing"
)

// ─── CRC-16/MODBUS Tests ────────────────────────────────────────────────────

func TestCRC16Modbus_Empty(t *testing.T) {
	// CRC of empty data with init=0xFFFF should be 0xFFFF
	got := CRC16Modbus([]byte{})
	want := uint16(0xFFFF)
	if got != want {
		t.Errorf("CRC16Modbus([]) = 0x%04X, want 0x%04X", got, want)
	}
}

func TestCRC16Modbus_SingleByte(t *testing.T) {
	// Known MODBUS CRC values
	// CRC-16/MODBUS of [0x01] = 0xC0C1? No — let's verify with reference.
	// Standard test: "123456789" → CRC-16/MODBUS = 0x4B37
	got := CRC16Modbus([]byte("123456789"))
	want := uint16(0x4B37)
	if got != want {
		t.Errorf("CRC16Modbus(\"123456789\") = 0x%04X, want 0x%04X", got, want)
	}
}

func TestCRC16Modbus_KnownValues(t *testing.T) {
	tests := []struct {
		name  string
		data  []byte
		want  uint16
	}{
		{"empty", []byte{}, 0xFFFF},
		{"zero", []byte{0x00}, 0x40BF},
		{"one", []byte{0x01}, 0x807E},
		{"AB01", []byte("AB01"), 0xD861}, // our communication line
	}
	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			got := CRC16Modbus(tt.data)
			if got != tt.want {
				t.Errorf("CRC16Modbus(%v) = 0x%04X, want 0x%04X", tt.data, got, tt.want)
			}
		})
	}
}

func TestCRC16Modbus_TableMatchesStandard(t *testing.T) {
	// Verify our Go table matches the table extracted from BsTool.exe
	// First 16 entries from the binary (verified in RE report):
	expected := []uint16{
		0x0000, 0xC0C1, 0xC181, 0x0140,
		0xC301, 0x03C0, 0x0280, 0xC241,
		0xC601, 0x06C0, 0x0780, 0xC741,
		0x0500, 0xC5C1, 0xC481, 0x0440,
	}
	for i, want := range expected {
		if crcTable[i] != want {
			t.Errorf("crcTable[%d] = 0x%04X, want 0x%04X", i, crcTable[i], want)
		}
	}
}

// ─── Block Header Tests ─────────────────────────────────────────────────────

func TestBlockHeader_MarshalBigEndian(t *testing.T) {
	h := BlockHeader{
		Command:  0x48, // OPEN_ERRLOG
		Sequence: 0x01,
		Source:   0x41504F31, // "AP01" as uint32
		Param:    0x00000000,
		Size:     0x000001C0, // 448
		DataLen:  0x00000004,
	}

	data, err := h.MarshalBinary()
	if err != nil {
		t.Fatal(err)
	}
	if len(data) != HeaderSize {
		t.Errorf("marshaled header = %d bytes, want %d", len(data), HeaderSize)
	}

	// Verify big-endian encoding
	// Command at offset 0: 0x0048 in big-endian = [0x00, 0x48]
	if data[0] != 0x00 || data[1] != 0x48 {
		t.Errorf("Command bytes = [%02X, %02X], want [00, 48]", data[0], data[1])
	}

	// Sequence at offset 2: 0x0001 in big-endian = [0x00, 0x01]
	if data[2] != 0x00 || data[3] != 0x01 {
		t.Errorf("Sequence bytes = [%02X, %02X], want [00, 01]", data[2], data[3])
	}

	// DataLen at offset 16: 0x00000004 in big-endian = [0x00, 0x00, 0x00, 0x04]
	if data[16] != 0x00 || data[17] != 0x00 || data[18] != 0x00 || data[19] != 0x04 {
		t.Errorf("DataLen bytes = [%02X, %02X, %02X, %02X], want [00, 00, 00, 04]",
			data[16], data[17], data[18], data[19])
	}
}

func TestBlockHeader_UnmarshalRoundTrip(t *testing.T) {
	original := BlockHeader{
		Command:  0x001F,
		Sequence: 0x0000,
		Source:   0xDEADBEEF,
		Param:    0x00000100,
		Size:     0x00000200,
		DataLen:  0x00000010,
	}

	data, err := original.MarshalBinary()
	if err != nil {
		t.Fatal(err)
	}

	var parsed BlockHeader
	if err := parsed.UnmarshalBinary(data); err != nil {
		t.Fatal(err)
	}

	if parsed.Command != original.Command {
		t.Errorf("Command = 0x%04X, want 0x%04X", parsed.Command, original.Command)
	}
	if parsed.Sequence != original.Sequence {
		t.Errorf("Sequence = 0x%04X, want 0x%04X", parsed.Sequence, original.Sequence)
	}
	if parsed.Source != original.Source {
		t.Errorf("Source = 0x%08X, want 0x%08X", parsed.Source, original.Source)
	}
	if parsed.Param != original.Param {
		t.Errorf("Param = 0x%08X, want 0x%08X", parsed.Param, original.Param)
	}
	if parsed.Size != original.Size {
		t.Errorf("Size = 0x%08X, want 0x%08X", parsed.Size, original.Size)
	}
	if parsed.DataLen != original.DataLen {
		t.Errorf("DataLen = 0x%08X, want 0x%08X", parsed.DataLen, original.DataLen)
	}
}

func TestBlockHeader_UnmarshalTooShort(t *testing.T) {
	var h BlockHeader
	err := h.UnmarshalBinary([]byte{0x00, 0x01, 0x02})
	if err == nil {
		t.Error("expected error for short input, got nil")
	}
}

// ─── Block Tests ────────────────────────────────────────────────────────────

func TestBlock_MarshalAndUnmarshal(t *testing.T) {
	original := Block{
		Header: BlockHeader{
			Command: CmdOpenErrLog,
			DataLen: 5,
		},
		Data: []byte("AP01\x00"),
	}

	data, err := original.MarshalBinary()
	if err != nil {
		t.Fatal(err)
	}

	expectedLen := HeaderSize + 5
	if len(data) != expectedLen {
		t.Fatalf("marshaled block = %d bytes, want %d", len(data), expectedLen)
	}

	var parsed Block
	consumed, err := parsed.UnmarshalBinary(data)
	if err != nil {
		t.Fatal(err)
	}
	if consumed != expectedLen {
		t.Errorf("consumed = %d, want %d", consumed, expectedLen)
	}
	if parsed.Header.Command != CmdOpenErrLog {
		t.Errorf("Command = 0x%04X, want 0x%04X", parsed.Header.Command, CmdOpenErrLog)
	}
	if string(parsed.Data) != "AP01\x00" {
		t.Errorf("Data = %q, want %q", parsed.Data, "AP01\x00")
	}
}

func TestBlock_TotalSize(t *testing.T) {
	b := Block{
		Header: BlockHeader{DataLen: 100},
		Data:   make([]byte, 100),
	}
	if b.TotalSize() != HeaderSize+100 {
		t.Errorf("TotalSize = %d, want %d", b.TotalSize(), HeaderSize+100)
	}
}

// ─── Session Tests ──────────────────────────────────────────────────────────

func TestSession_ToggleSequence(t *testing.T) {
	s := NewSession()
	if s.Sequence != 0 {
		t.Errorf("initial Sequence = %d, want 0", s.Sequence)
	}
	s.ToggleSequence()
	if s.Sequence != 1 {
		t.Errorf("after first toggle, Sequence = %d, want 1", s.Sequence)
	}
	s.ToggleSequence()
	if s.Sequence != 0 {
		t.Errorf("after second toggle, Sequence = %d, want 0", s.Sequence)
	}
}

func TestSession_SessionID(t *testing.T) {
	s1 := NewSession()
	s2 := NewSession()
	// Session IDs should be random (15-bit, 0-0x7FFF)
	if s1.SessionID > 0x7FFF {
		t.Errorf("SessionID = 0x%04X, should be <= 0x7FFF", s1.SessionID)
	}
	if s2.SessionID > 0x7FFF {
		t.Errorf("SessionID = 0x%04X, should be <= 0x7FFF", s2.SessionID)
	}
	// Very unlikely to be the same (1 in 32768)
	if s1.SessionID == s2.SessionID {
		t.Logf("warning: two session IDs are the same (0x%04X) — unlikely but not a bug", s1.SessionID)
	}
}

func TestSession_NextBlock(t *testing.T) {
	s := NewSession()
	s.Sequence = 1
	data := []byte("AP01")
	b := s.NextBlock(CmdOpenErrLog, data)
	if b.Header.Command != CmdOpenErrLog {
		t.Errorf("Command = 0x%04X, want 0x%04X", b.Header.Command, CmdOpenErrLog)
	}
	if b.Header.Sequence != 1 {
		t.Errorf("Sequence = %d, want 1", b.Header.Sequence)
	}
	if b.Header.DataLen != uint32(len(data)) {
		t.Errorf("DataLen = %d, want %d", b.Header.DataLen, len(data))
	}
	if string(b.Data) != "AP01" {
		t.Errorf("Data = %q, want %q", b.Data, "AP01")
	}
}

// ─── Protocol Constants Tests ───────────────────────────────────────────────

func TestProtocolConstants(t *testing.T) {
	// Verify constants match RE findings
	if CmdOpenErrLog != 0x48 {
		t.Errorf("CmdOpenErrLog = 0x%02X, want 0x48", CmdOpenErrLog)
	}
	if CmdGetLogData != 0x1F {
		t.Errorf("CmdGetLogData = 0x%02X, want 0x1F", CmdGetLogData)
	}
	if ACKStatus != 6 {
		t.Errorf("ACKStatus = %d, want 6", ACKStatus)
	}
	if NACKStatus != 21 {
		t.Errorf("NACKStatus = %d, want 21", NACKStatus)
	}
	if DefaultChunkSize != 448 {
		t.Errorf("DefaultChunkSize = %d, want 448", DefaultChunkSize)
	}
	if MaxSendRetries != 21 {
		t.Errorf("MaxSendRetries = %d, want 21", MaxSendRetries)
	}
	if MaxRecvRetries != 5 {
		t.Errorf("MaxRecvRetries = %d, want 5", MaxRecvRetries)
	}
	if HeaderSize != 20 {
		t.Errorf("HeaderSize = %d, want 20", HeaderSize)
	}
}