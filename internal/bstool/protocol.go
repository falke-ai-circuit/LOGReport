package bstool

// protocol.go — BsTool wire protocol structures (reverse-engineered from BsTool.exe v9.29)
//
// Evidence: capstone disassembly of zzSendRsBlk (0x438290), zzSendTcpBlk (0x438B570),
// zzInicrc (0x4378D0), zzUpdcrc (0x4379C0), zzInit2111 (0x439BE0), zzSend2111 (0x43A1A0),
// zzOpenErrLog (0x430940), zzGetLog (0x42EBA0).
//
// Protocol spec: docs/bstool-protocol-spec.md

import (
	"encoding/binary"
	"fmt"
	"math/rand"
	"time"
)

// ─── Block Header (20 bytes / 0x14) ──────────────────────────────────────────

// BlockHeader is the 20-byte header preceding every protocol block.
// All fields are transmitted big-endian on the wire (x86 host is little-endian,
// so send16/send32 byte-swap before transmission — verified in disassembly).
//
// Evidence: zzSendRsBlk sends fields at offsets +0, +2 (16-bit) and +4, +8, +0xC,
// +0x10 (32-bit). Total = 2+2+4+4+4+4 = 20 = 0x14.
type BlockHeader struct {
	Command  uint16 // +0x00: command code (e.g., 0x48=OPEN_ERRLOG, 0x1F=GET_LOG_DATA)
	Sequence uint16 // +0x02: sequence number (toggles 0↔1 during handshake)
	Source   uint32 // +0x04: source/destination identifier
	Param    uint32 // +0x08: parameter (offset for GET_LOG_DATA)
	Size     uint32 // +0x0C: size parameter (chunk size for GET_LOG_DATA)
	DataLen  uint32 // +0x10: payload length following header
}

// HeaderSize is the fixed size of the block header.
const HeaderSize = 20

// MarshalBinary serializes the header to 20 bytes in big-endian (wire) order.
func (h *BlockHeader) MarshalBinary() ([]byte, error) {
	buf := make([]byte, HeaderSize)
	binary.BigEndian.PutUint16(buf[0:], h.Command)
	binary.BigEndian.PutUint16(buf[2:], h.Sequence)
	binary.BigEndian.PutUint32(buf[4:], h.Source)
	binary.BigEndian.PutUint32(buf[8:], h.Param)
	binary.BigEndian.PutUint32(buf[12:], h.Size)
	binary.BigEndian.PutUint32(buf[16:], h.DataLen)
	return buf, nil
}

// UnmarshalBinary parses a 20-byte big-endian header from the wire.
func (h *BlockHeader) UnmarshalBinary(data []byte) error {
	if len(data) < HeaderSize {
		return fmt.Errorf("bstool: header requires %d bytes, got %d", HeaderSize, len(data))
	}
	h.Command = binary.BigEndian.Uint16(data[0:])
	h.Sequence = binary.BigEndian.Uint16(data[2:])
	h.Source = binary.BigEndian.Uint32(data[4:])
	h.Param = binary.BigEndian.Uint32(data[8:])
	h.Size = binary.BigEndian.Uint32(data[12:])
	h.DataLen = binary.BigEndian.Uint32(data[16:])
	return nil
}

// Block is a complete protocol block (header + payload).
type Block struct {
	Header BlockHeader
	Data   []byte
}

// MarshalBinary serializes the full block (header + data) to wire format.
func (b *Block) MarshalBinary() ([]byte, error) {
	hdr, err := b.Header.MarshalBinary()
	if err != nil {
		return nil, err
	}
	result := make([]byte, 0, HeaderSize+len(b.Data))
	result = append(result, hdr...)
	result = append(result, b.Data...)
	return result, nil
}

// UnmarshalBinary parses a block from wire data (at least HeaderSize bytes).
// Returns the number of bytes consumed (HeaderSize + DataLen) and any error.
func (b *Block) UnmarshalBinary(data []byte) (int, error) {
	if len(data) < HeaderSize {
		return 0, fmt.Errorf("bstool: need at least %d bytes for header", HeaderSize)
	}
	if err := b.Header.UnmarshalBinary(data[:HeaderSize]); err != nil {
		return 0, err
	}
	total := HeaderSize + int(b.Header.DataLen)
	if len(data) < total {
		return 0, fmt.Errorf("bstool: need %d bytes (header+%d data), got %d",
			total, b.Header.DataLen, len(data))
	}
	b.Data = make([]byte, b.Header.DataLen)
	copy(b.Data, data[HeaderSize:total])
	return total, nil
}

// TotalSize returns the total block size (header + data).
func (b *Block) TotalSize() int {
	return HeaderSize + len(b.Data)
}

// ─── CRC-16/ARC ──────────────────────────────────────────────────────────────

// CRC-16/ARC: polynomial=0xA001 (reversed 0x8005), initial=0x0000.
// Same polynomial as MODBUS but with init=0x0000 instead of 0xFFFF.
//
// IMPORTANT: BsTool's send_block initializes CRC to 0x0000, NOT 0xFFFF.
// The lookup table is identical to MODBUS (poly 0xA001), but the init value
// differs. This makes it CRC-16/ARC, not CRC-16/MODBUS.
//
// Evidence: send_block (RVA 0x039D90) does `xor edx,edx; mov word ptr [ebp-8], dx`
// before the CRC loop, initializing to 0. zzInicrc populates the table with poly
// 0xA001. zzUpdcrc does: crc = (crc >> 8) ^ table[(crc ^ byte) & 0xFF].

var crcTable [256]uint16

func init() {
	for i := 0; i < 256; i++ {
		crc := uint16(i)
		for j := 0; j < 8; j++ {
			if crc&1 != 0 {
				crc = (crc >> 1) ^ 0xA001
			} else {
				crc >>= 1
			}
		}
		crcTable[i] = crc
	}
}

// CRC16 computes the CRC-16/ARC checksum of data (init=0x0000, poly=0xA001).
// This is the variant used by BsTool's wire protocol.
func CRC16(data []byte) uint16 {
	crc := uint16(0x0000) // BsTool uses init=0, NOT 0xFFFF
	for _, b := range data {
		crc = (crc >> 8) ^ crcTable[(crc^uint16(b))&0xFF]
	}
	return crc
}

// CRC16Modbus computes the standard CRC-16/MODBUS (init=0xFFFF).
// Kept for backward compatibility with the initial RE report.
func CRC16Modbus(data []byte) uint16 {
	crc := uint16(0xFFFF)
	for _, b := range data {
		crc = (crc >> 8) ^ crcTable[(crc^uint16(b))&0xFF]
	}
	return crc
}

// ─── Protocol Constants ──────────────────────────────────────────────────────

// DLE/STX/ETX framing bytes (from send_block and rcv_block disassembly).
const (
	DLE = 0x10 // Data Link Escape — used for byte stuffing
	STX = 0x02 // Start of Text — marks block beginning
	ETX = 0x03 // End of Text — marks block end
	SYN = 0x16 // Synchronization — receiver resets on this byte
)

// "2111" Handshake constants (from disassembly of zzInit2111, zzSend2111, zzRcv2111).
const (
	MaxSendRetries   = 21   // 0x15 — max TX attempts in zzSend2111
	MaxRecvRetries   = 5    // max RX attempts in zzRcv2111
	HandshakeTimeout = 4196 // 0x1064 ms — response timeout in zzSend2111
	MaxResponseSize  = 4196 // 0x1064 — max block size for handshake
	ACKStatus        = 6    // status byte value for ACK
	NACKStatus       = 21   // 0x15 — status byte value for NACK
	DefaultChunkSize = 448  // 0x1C0 — default log data chunk size in zzGetLog
)

// TCP transport constants (from tcp_init_impl disassembly).
const (
	DefaultTCPPort    = 1516 // 0x5EC — default TCP port in tcp_init_impl
	TCPRetryDelay     = 2    // seconds between TCP connection retries
	MaxTCPRetries     = 5    // max TCP connection attempts
	TCPBufferSize     = 2048 // 0x800 — TX/RX buffer sizes
	TCPDefaultTimeout = 1516 // 0x5EC ms — default socket timeout
)

// Session represents a "2111" protocol session.
type Session struct {
	SessionID uint16 // random 15-bit ID (0x473F50)
	Sequence  uint16 // toggles 0↔1 (0x473F54)
	BlockNum  uint16 // block counter (0x474FBC)
}

// NewSession creates a new session with a random session ID.
func NewSession() *Session {
	return &Session{
		SessionID: uint16(rand.Intn(0x8000)),
		Sequence:  0,
	}
}

// ToggleSequence flips the sequence bit (0↔1).
func (s *Session) ToggleSequence() {
	s.Sequence = 1 - s.Sequence
}

// NextBlock builds a block for this session with the current sequence number.
func (s *Session) NextBlock(cmd uint16, data []byte) *Block {
	return &Block{
		Header: BlockHeader{
			Command:  cmd,
			Sequence: s.Sequence,
			DataLen:  uint32(len(data)),
		},
		Data: data,
	}
}

// ─── Command Codes ───────────────────────────────────────────────────────────

// Command codes identified from disassembly of zzOpenErrLog and zzGetLog.
const (
	CmdOpenErrLog uint16 = 0x48 // 'H' — open error log stream for a server
	CmdGetLogData uint16 = 0x1F // 31  — retrieve log data chunk
	CmdACK        uint16 = 0x06 // 6   — acknowledge (handshake)
	CmdNACK       uint16 = 0x15 // 21  — negative acknowledge (handshake retry)

	// File system commands (from BsTool.exe disassembly + live BU verification 2026-06-30)
	CmdHandshake  uint16 = 0x000C // handshake — send 3x, BU responds param=0x02CC
	CmdFileOpen   uint16 = 0x0000 // open file on remote BU
	CmdFileClose  uint16 = 0x0001 // close file handle
	CmdFileRead   uint16 = 0x0002 // read file chunk (param=chunk size, default 448)
	CmdReadDir    uint16 = 0x0014 // open directory listing (returns dir context handle in param)
	CmdGetDirEntry uint16 = 0x0016 // get next directory entry (pass response param as cursor; stop when param=0)
	CmdGetHWByIP  uint16 = 0x0066 // get hardware info by IP address
	CmdSendCmd    uint16 = 0x000A // zzSendCmd — generic command send
	CmdFileInit   uint16 = 0x0005 // file system init
)

// ─── Error State Codes ───────────────────────────────────────────────────────

// Error state codes from zzOpenErrLog and zzGetLog disassembly.
const (
	StateReconnect    = 3  // 0x4A87E0 == 3 → need reconnect
	StateNoSuchServer = 22 // 0x16 → server name not found
	StateNoData       = 20 // 0x14 → no log data available
	StateLogEmpty     = 25 // 0x19 → log is empty
	StateIncomplete   = 26 // 0x1A → incomplete transfer
)

// ─── RS-232 Wire Block Framing (DLE/STX/ETX) ──────────────────────────────────
// These functions implement the RS-232 serial line framing used by send_block
// (RVA 0x039D90) and rcv_block (RVA 0x039850).
// TCP transport does NOT use this framing — it sends raw binary blocks.
// These are kept for RS-232 transport implementation and protocol testing.

// FrameBlock wraps a protocol block in DLE/STX/ETX framing with byte stuffing.
//
// Wire format: [DLE][STX][status][sid_hi][sid_lo][data...][DLE][ETX][crc_lo][crc_hi]
//
// DLE (0x10) in data is escaped: each 0x10 in data → 0x10 0x10 (DLE stuffing).
// CRC is computed over: status + sid_hi + sid_lo + data + ETX (NOT the DLE/STX prefix).
// CRC is CRC-16/ARC: poly=0xA001, init=0x0000.
//
// Evidence: send_block (RVA 0x039D90) decompiled in bstool-decompilation-report.md §1.1
// NOTE: This is RS-232 ONLY. TCP transport uses raw binary blocks (no framing).
func FrameBlock(status uint8, sessionID uint16, data []byte) []byte {
	var buf []byte

	// 1. DLE + STX (start of block)
	buf = append(buf, DLE, STX)

	// 2. Status byte
	buf = append(buf, status)

	// 3. Session ID (big-endian: high byte first, then low byte)
	sidHigh := uint8((sessionID >> 8) & 0xFF)
	sidLow := uint8(sessionID & 0xFF)
	buf = append(buf, sidHigh, sidLow)

	// 4. Data with DLE stuffing
	for _, b := range data {
		if b == DLE {
			buf = append(buf, DLE) // escape: send DLE twice
		}
		buf = append(buf, b)
	}

	// 5. DLE + ETX (end of block)
	buf = append(buf, DLE, ETX)

	// 6. CRC over: status + sid_hi + sid_lo + data (unstuffed) + ETX
	crcData := make([]byte, 0, 3+len(data)+1)
	crcData = append(crcData, status, sidHigh, sidLow)
	crcData = append(crcData, data...)
	crcData = append(crcData, ETX)
	crc := CRC16(crcData)

	// 7. CRC (low byte first, then high byte — little-endian on wire)
	buf = append(buf, uint8(crc&0xFF), uint8((crc>>8)&0xFF))

	return buf
}

// UnframeBlock parses a DLE/STX/ETX framed block from raw received bytes.
// Returns status, sessionID, data, and error.
//
// Evidence: rcv_block (RVA 0x039850) decompiled in bstool-decompilation-report.md §1.2
// NOTE: This is RS-232 ONLY. TCP transport uses raw binary blocks (no framing).
func UnframeBlock(raw []byte) (status uint8, sessionID uint16, data []byte, err error) {
	if len(raw) < 8 { // minimum: DLE+STX+status+sid_hi+sid_lo+DLE+ETX+CRC(2)
		return 0, 0, nil, fmt.Errorf("bstool: frame too short (%d bytes)", len(raw))
	}

	pos := 0

	// 1. Expect DLE
	if raw[pos] != DLE {
		return 0, 0, nil, fmt.Errorf("bstool: expected DLE(0x10), got 0x%02X", raw[pos])
	}
	pos++

	// 2. Expect STX
	if raw[pos] != STX {
		return 0, 0, nil, fmt.Errorf("bstool: expected STX(0x02), got 0x%02X", raw[pos])
	}
	pos++

	// 3. Status byte
	status = raw[pos]
	pos++

	// 4. Session ID (high byte, low byte)
	sidHigh := raw[pos]
	sidLow := raw[pos+1]
	pos += 2
	sessionID = (uint16(sidHigh)<<8 | uint16(sidLow)) & 0x7FFF // 15-bit mask

	// 5. Data with DLE unstuffing
	var unstuffed []byte
	crcData := make([]byte, 0, 64)
	crcData = append(crcData, status, sidHigh, sidLow)

	for pos < len(raw) {
		b := raw[pos]
		pos++

		if b == DLE {
			if pos >= len(raw) {
				return 0, 0, nil, fmt.Errorf("bstool: DLE at end of frame")
			}
			next := raw[pos]
			pos++

			if next == ETX {
				// End of data
				crcData = append(crcData, ETX)
				break
			}
			if next == DLE {
				// Stuffed DLE — literal 0x10 in data
				unstuffed = append(unstuffed, DLE)
				crcData = append(crcData, DLE)
				continue
			}
			// Unexpected byte after DLE
			return 0, 0, nil, fmt.Errorf("bstool: unexpected byte 0x%02X after DLE", next)
		}

		unstuffed = append(unstuffed, b)
		crcData = append(crcData, b)
	}

	// 6. Read CRC (low byte, high byte)
	if pos+1 >= len(raw) {
		return 0, 0, nil, fmt.Errorf("bstool: missing CRC at pos %d", pos)
	}
	recvCRC := uint16(raw[pos]) | uint16(raw[pos+1])<<8

	// 7. Verify CRC
	calcCRC := CRC16(crcData)
	if calcCRC != recvCRC {
		return 0, 0, nil, fmt.Errorf("bstool: CRC mismatch (recv=0x%04X, calc=0x%04X)", recvCRC, calcCRC)
	}

	return status, sessionID, unstuffed, nil
}

// ─── Timer ───────────────────────────────────────────────────────────────────

// initRand seeds the math/rand source for session IDs.
// Called once at package init.
func init() {
	// In Go 1.20+, the global rand source is automatically seeded.
	// For older versions, we seed manually.
	rand.Seed(time.Now().UnixNano())
}
