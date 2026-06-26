package bstool

import (
	"testing"
)

// ─── DLE/STX/ETX Framing Tests ──────────────────────────────────────────────

func TestFrameBlock_BasicStructure(t *testing.T) {
	data := []byte("AP01")
	frame := FrameBlock(0x48, 0x1234, data)

	// Expected: DLE + STX + status + sid_hi + sid_lo + data + DLE + ETX + crc_lo + crc_hi
	// = 2 + 1 + 1 + 1 + 4 + 2 + 2 = 13 bytes
	expectedLen := 2 + 1 + 1 + 1 + len(data) + 2 + 2
	if len(frame) != expectedLen {
		t.Errorf("frame length = %d, want %d", len(frame), expectedLen)
	}

	// Check DLE+STX prefix
	if frame[0] != DLE || frame[1] != STX {
		t.Errorf("frame start = [0x%02X, 0x%02X], want [0x%02X, 0x%02X]",
			frame[0], frame[1], DLE, STX)
	}

	// Check status byte
	if frame[2] != 0x48 {
		t.Errorf("status = 0x%02X, want 0x48", frame[2])
	}

	// Check session ID (big-endian)
	if frame[3] != 0x12 || frame[4] != 0x34 {
		t.Errorf("session ID bytes = [0x%02X, 0x%02X], want [0x12, 0x34]",
			frame[3], frame[4])
	}

	// Check DLE+ETX before CRC
	dleEtxPos := 5 + len(data)
	if frame[dleEtxPos] != DLE || frame[dleEtxPos+1] != ETX {
		t.Errorf("DLE+ETX at pos %d = [0x%02X, 0x%02X], want [0x%02X, 0x%02X]",
			dleEtxPos, frame[dleEtxPos], frame[dleEtxPos+1], DLE, ETX)
	}
}

func TestFrameBlock_DLEStuffing(t *testing.T) {
	// Data containing DLE (0x10) should be stuffed
	data := []byte{0x41, 0x10, 0x42} // "A" + DLE + "B"
	frame := FrameBlock(0x06, 0x0001, data)

	// The DLE in data should be doubled: 0x10 → 0x10 0x10
	// Frame: DLE + STX + status + sid_hi + sid_lo + 0x41 + 0x10 + 0x10 + 0x42 + DLE + ETX + crc_lo + crc_hi
	// Length: 2 + 1 + 1 + 1 + 1 + 1 + 1 + 1 + 2 + 2 = 13 (one extra for stuffed DLE)
	if len(frame) != 13 {
		t.Errorf("stuffed frame length = %d, want 13", len(frame))
	}

	// Check that the DLE in data was stuffed (position 5+1=6 should be 0x10)
	if frame[6] != DLE || frame[7] != DLE {
		t.Errorf("stuffed DLE at pos 6,7 = [0x%02X, 0x%02X], want [0x10, 0x10]",
			frame[6], frame[7])
	}
}

func TestFrameBlock_CRCCorrectness(t *testing.T) {
	// Verify the CRC in the frame matches CRC-16/ARC (init=0)
	data := []byte("test")
	frame := FrameBlock(0x48, 0x0001, data)

	// Reconstruct CRC input: status + sid_hi + sid_lo + data + ETX
	crcInput := []byte{0x48, 0x00, 0x01}
	crcInput = append(crcInput, data...)
	crcInput = append(crcInput, ETX)

	expectedCRC := CRC16(crcInput)

	// CRC is last 2 bytes (low first, then high)
	crcPos := len(frame) - 2
	recvCRC := uint16(frame[crcPos]) | uint16(frame[crcPos+1])<<8

	if recvCRC != expectedCRC {
		t.Errorf("frame CRC = 0x%04X, want 0x%04X", recvCRC, expectedCRC)
	}
}

func TestUnframeBlock_RoundTrip(t *testing.T) {
	originalData := []byte("AP01")
	originalStatus := uint8(0x48)
	originalSID := uint16(0x1234)

	frame := FrameBlock(originalStatus, originalSID, originalData)

	status, sid, data, err := UnframeBlock(frame)
	if err != nil {
		t.Fatalf("UnframeBlock failed: %v", err)
	}

	if status != originalStatus {
		t.Errorf("status = 0x%02X, want 0x%02X", status, originalStatus)
	}
	if sid != originalSID&0x7FFF {
		t.Errorf("session ID = 0x%04X, want 0x%04X", sid, originalSID&0x7FFF)
	}
	if string(data) != string(originalData) {
		t.Errorf("data = %q, want %q", data, originalData)
	}
}

func TestUnframeBlock_DLEUnstuffing(t *testing.T) {
	// Data with embedded DLE
	originalData := []byte{0x41, 0x10, 0x42} // A + DLE + B
	frame := FrameBlock(0x06, 0x0001, originalData)

	_, _, data, err := UnframeBlock(frame)
	if err != nil {
		t.Fatalf("UnframeBlock with DLE stuffing failed: %v", err)
	}

	if len(data) != 3 {
		t.Fatalf("unstuffed data length = %d, want 3", len(data))
	}
	if data[0] != 0x41 || data[1] != 0x10 || data[2] != 0x42 {
		t.Errorf("unstuffed data = %v, want [0x41, 0x10, 0x42]", data)
	}
}

func TestUnframeBlock_CRCError(t *testing.T) {
	// Create a valid frame, then corrupt the CRC
	data := []byte("test")
	frame := FrameBlock(0x48, 0x0001, data)
	frame[len(frame)-1] ^= 0xFF // corrupt CRC high byte

	_, _, _, err := UnframeBlock(frame)
	if err == nil {
		t.Error("expected CRC error, got nil")
	}
}

func TestUnframeBlock_InvalidHeader(t *testing.T) {
	// No DLE/STX
	_, _, _, err := UnframeBlock([]byte{0x00, 0x01, 0x02, 0x03})
	if err == nil {
		t.Error("expected header error, got nil")
	}
}

// ─── CRC-16/ARC Tests ────────────────────────────────────────────────────────

func TestCRC16_InitZero(t *testing.T) {
	// CRC-16/ARC of empty data = 0x0000 (init=0, no data)
	got := CRC16([]byte{})
	want := uint16(0x0000)
	if got != want {
		t.Errorf("CRC16([]) = 0x%04X, want 0x%04X", got, want)
	}
}

func TestCRC16_DiffersFromModbus(t *testing.T) {
	// CRC-16/ARC (init=0) and CRC-16/MODBUS (init=0xFFFF) should differ
	data := []byte("123456789")
	arc := CRC16(data)
	modbus := CRC16Modbus(data)
	if arc == modbus {
		t.Errorf("CRC16 and CRC16Modbus are the same (0x%04X) — they should differ", arc)
	}
}

// ─── TCP Transport Constants Tests ──────────────────────────────────────────

func TestTCPConstants(t *testing.T) {
	if DefaultTCPPort != 1516 {
		t.Errorf("DefaultTCPPort = %d, want 1516", DefaultTCPPort)
	}
	if TCPBufferSize != 2048 {
		t.Errorf("TCPBufferSize = %d, want 2048", TCPBufferSize)
	}
	if MaxTCPRetries != 5 {
		t.Errorf("MaxTCPRetries = %d, want 5", MaxTCPRetries)
	}
}

// ─── StripNodeSuffix Tests ───────────────────────────────────────────────────

func TestStripNodeSuffix_TCP(t *testing.T) {
	cases := []struct {
		input, want string
	}{
		{"AP01m", "AP01"},
		{"BP01r", "BP01"},
		{"AP01", "AP01"},
		{"APm", "AP"},
		{"", ""},
	}
	for _, tc := range cases {
		got := stripNodeSuffix(tc.input)
		if got != tc.want {
			t.Errorf("stripNodeSuffix(%q) = %q, want %q", tc.input, got, tc.want)
		}
	}
}