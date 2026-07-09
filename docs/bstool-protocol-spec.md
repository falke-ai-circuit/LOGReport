# BsTool Wire Protocol Specification
## Reverse-Engineered from BsTool.exe v9.29 (2026-06-25)

**Method**: Capstone disassembly of PE32 binary, export table analysis, 
strings extraction, cross-referencing with Python wrapper source and 
valmet agent knowledge report.

---

## 1. CRC-16/ARC (Verified)

**Algorithm**: CRC-16/ARC (variant of CRC-16/MODBUS with different init value)
- **Polynomial**: 0xA001 (reversed 0x8005) — same as MODBUS
- **Initial value**: 0x0000 — **NOT 0xFFFF like MODBUS!** This is the critical distinction.
- **Table-driven**: 256-entry 16-bit lookup table at RVA 0x069BF8
- **Verification**: Binary table extracted and compared — polynomial matches MODBUS, but `send_block` (RVA 0x039D90) initializes CRC to 0 before the loop.

```go
// Go implementation (verified against binary: init=0, poly=0xA001)
func CRC16(data []byte) uint16 {
    crc := uint16(0x0000) // ARC: init=0, NOT 0xFFFF
    for _, b := range data {
        crc = (crc >> 8) ^ crcTable[(crc^uint16(b))&0xFF]
    }
    return crc
}
```

**Functions**:
- `zzInicrc()` — Populates 256-entry table at 0x469BF8 (called once at init)
- `zzUpdcrc(crc, byte)` — Single-byte update: `(crc>>8) ^ table[(crc^byte)&0xFF]`
- `zzUpdblkcrc(crc, data, len)` — Block update: loops `zzUpdcrc` over buffer

---

## 2. Block Header Structure (20 bytes / 0x14)

All block transfers (RS-232 and TCP) use this header:

```
Offset  Size    Type      Description
------  ----    ----      -----------
+0x00   2       uint16    block_type / command code
+0x02   2       uint16    sequence / flags
+0x04   4       uint32    field_2 (source/dest identifier)
+0x08   4       uint32    field_3 (parameter/offset)
+0x0C   4       uint32    field_4 (parameter/size)
+0x10   4       uint32    data_length (payload size following header)
```

**Total block size** = 20 (header) + `data_length` (payload)

**Evidence**: `zzSendRsBlk` at 0x438290:
```
eax = &block + 0x14  // header end
eax -= &block        // = 0x14 (20)
eax += block[0x10]   // += data_length field
```

---

## 3. Byte Order — Big-Endian on Wire

The `send16` function at 0x4380B0 swaps bytes before sending:
```c
// send16: swaps to big-endian before transmission
void send16(uint16_t *val) {
    uint16_t swapped = (*val >> 8) | (*val << 8);
    *val = swapped;  // write back swapped value
}
```

The `send32` function at 0x4380E0 performs full 32-bit byte swap:
```c
// send32: swaps to big-endian before transmission
void send32(uint32_t *val) {
    uint32_t swapped = ((*val >> 24) & 0xFF) |
                       ((*val >> 8)  & 0xFF00) |
                       ((*val << 8)  & 0xFF0000) |
                       ((*val << 24) & 0xFF000000);
    *val = swapped;
}
```

**Wire format = Big-Endian (network byte order)**. The x86 host is little-endian, so all multi-byte fields are swapped before transmission.

---

## 4. RS-232 Block Send Protocol (`zzSendRsBlk`)

```
1. Calculate total_size = 0x14 + block.data_length
2. Byte-swap all header fields to big-endian (send16 for 2-byte, send32 for 4-byte)
3. Call zzSend2111 (handshake) with block pointer + total_size
   - This computes CRC over the block and sends it
4. Re-send all 6 header fields (redundant transmission for reliability)
5. If CRC result != 0, call zzFlushIn (flush input buffer on error)
6. Return CRC status
```

The **redundant header re-send** is a reliability mechanism — the header is transmitted twice over the serial line. The receiver can compare both copies to detect corruption.

---

## 5. TCP Block Send Protocol (`zzSendTcpBlk`)

```
1. Calculate total_size = 0x14 + block.data_length
2. Byte-swap all header fields to big-endian in place (send16 for 2-byte, send32 for 4-byte)
3. Send entire block (header + data) in ONE send() call
   - Uses socket from global 0x46A28C
   - Calls tcp_send_wrapper (0x43A610) which loops send() until all bytes sent
4. Compare sent bytes == total_size
5. Return 0 on success, -1 on failure
```

**CRITICAL: TCP does NOT use DLE/STX/ETX framing. No CRC. No handshake. No byte stuffing.**
The raw 20-byte big-endian header + raw data payload is sent directly over TCP.
TCP's own reliability guarantees replace the serial-level error detection.

This was confirmed by deep disassembly (2026-06-26):
- `zzSendTcpBlk` (0x43B570) calls `send16`/`send32` then `tcp_send_wrapper` — NO call to `send_block`
- `zzRcvTcpBlk` (0x43ABF0) reads 20-byte header then data — NO DLE unstuffing, NO CRC check
- Only `zzSendRsBlk` (0x438290) calls `zzSend2111` → `send_block` (DLE/STX/ETX framing)

---

## 6. "2111" Handshake Protocol

### 6.1 Initialization (`zzInit2111`)

```
1. Clear 0x1000 (4096) byte receive buffer at 0x474FC0
2. Reset sequence counter at 0x473F54 = 0
3. Reset block counter at 0x474FBC = 0
4. Reset retry counter at 0x476FC0 = 0
5. Set max retries at 0x476FC4 = 1
6. Call zzInicrc() — initialize CRC table
7. Generate random session ID: rand() & 0x7FFF → stored at 0x473F50
```

### 6.2 Send Handshake (`zzSend2111`)

**Retry loop**: Up to 21 attempts (0x15)

Each attempt:
```
1. Increment total_tx counter (0x4A86A0)
2. Increment total_tx_retrans counter (0x4A86F4)
3. Call send_block(socket, session_id, sequence, block_size, block_ptr)
4. Wait for response (timeout 0x1064 = 4196ms)
5. Read response: status byte, response_size (2 bytes), response_data
6. If status == 6 (ACK):
   a. Toggle sequence: sequence = 1 - sequence
   b. Process response (call 0x439800 = process_response)
   c. Store response_size in 0x474FBC
   d. Return 0 (success)
7. If status != 6 (NACK/error):
   a. Increment CRC error counter (0x4A86AC)
   b. Increment timeout counter (0x4A8700)
   c. Loop back (retry)
8. After 21 failures:
   a. Call zzFlushIn (flush input)
   b. Increment fatal timeout counter (0x4A86B8)
   c. Return -1 (failure)
```

### 6.3 Receive Handshake (`zzRcv2111`)

**Retry loop**: Up to 5 attempts

Each attempt:
```
1. Increment total_rx counter
2. Read block: wait for status byte, size (2 bytes), data
3. Verify CRC of received block (call 0x439BA0)
4. Compare received status with expected:
   a. If mismatch: increment CRC error counter, send NACK (status=6, current_size)
   b. If match: toggle sequence, process block, return 0
5. On failure: call zzFlushIn, send NACK (status=0x15=21, size=0)
6. After 5 failures: return -1
```

### 6.4 Acknowledge (`zzAck2111`)

```
1. Clamp size to max 0x1064 (4196 bytes)
2. Process received block (call 0x439800)
3. Store size in 0x474FBC
4. Send ACK: status=6, current_size, session_id, block_ptr
```

### 6.5 Message Counters

Global counters track protocol health (at 0x4A86A0+):
- `0x4A86A0`: Total TX messages
- `0x4A86AC`: CRC errors
- `0x4A86B4`: CRC errors (RX side)
- `0x4A86B8`: Fatal timeouts
- `0x4A86F4`: TX retransmissions
- `0x4A8700`: RX timeouts
- `0x4A8708`: RX CRC failures
- `0x4A870C`: RX fatal timeouts

Output format (from strings):
```
MESSAGE COUNTERS
    Total   Corrupted   CRC   Retrans   Timeout   uid   Fatal
```

---

## 7. RS-232 Serial Line Initialization (`zzInitRsLineIO`)

```
1. Read COMMUNICATION_LINE env var (e.g., "AB01")
2. If starts with "@@\\" prefix, strip it (Windows device namespace \\.\)
3. Read COMMUNICATION_SPEED env var → default 0x4B00 (19200 baud)
4. Build device path: prefix + port_name
5. Open serial port: CreateFileA(device, GENERIC_READ|GENERIC_WRITE, 0, NULL, OPEN_EXISTING, 0, NULL)
   - Store handle at 0x473EA8
6. SetupComm(handle, 0x800, 0x800) — set buffer sizes (2048/2048)
7. GetCommState(handle, &dcb) — get current DCB
8. Configure DCB:
   - BaudRate = COMMUNICATION_SPEED (19200 default)
   - ByteSize = 8
   - fBinary = TRUE (binary mode)
   - fParity = TRUE (parity checking)
   - Parity = ... (configured)
   - fOutxCtsFlow, fOutxDsrFlow, fDtrControl, fRtsControl = configured
9. SetCommState(handle, &dcb) — apply settings
10. SetCommTimeouts(handle, &timeouts) — set read/write timeouts
```

**Key globals**:
- `0x473EA8`: Serial port handle (HANDLE)
- `0x473EAC`: Write handle (for WriteFile)
- `0x473EA0`: Receive buffer count
- `0x473E9C`: Receive read position
- `0x473E74`: Receive buffer (20 bytes)
- `0x473E88`: Send buffer (20 bytes)
- `0x473EA4`: Send buffer position

---

## 8. Error Log Retrieval (`-errlog` pathway)

### 8.1 `zzOpenErrLog` (0x430940)

```
Purpose: Open error log stream from a DNA node
Input: server_name (string), result_ptr (int*)
Stack: 0x840 bytes (large local buffer)

1. Check if reconnect needed (state 0x4A87E0 == 3)
   - If so: close existing connection, call cleanup, reconnect
2. Check connection state (0x473508)
   - If not connected: return -1
3. Copy server_name to local buffer (up to 0x808 bytes)
4. Calculate name length
5. Check name fits in communication buffer (0x47351C)
6. Build request block:
   - command = 0x48 ('H' = "Help/Host" command)
   - field_2 = 0 (reserved)
   - field_3 = 0 (reserved)
   - Copy server name into block data area
7. Call transport_send (via function pointer at 0x473514)
8. Call transport_receive (via function pointer at 0x473518)
9. Check result:
   - If error: set state = 3 (needs reconnect), return -1
   - If field_2 == -1: set state = 0x16 (22 = "no such server"), return -1
   - On success: store result, return 0
```

### 8.2 `zzGetLog` (0x42EBA0)

```
Purpose: Retrieve log messages from an opened error log stream
Input: buffer_ptr (struct with data area)
Stack: 0x840 bytes

1. Check reconnect state (same as zzOpenErrLog)
2. Initialize:
   - remaining = 0x1C0 (448 bytes) — total to retrieve
   - offset = 0
   - total_received = 0
3. Loop while remaining > 0:
   a. Calculate chunk size = min(remaining, max_buffer_size)
   b. Build request block:
      - command = 0x1F (31 = "get log data")
      - field_2 = offset (current read position)
      - field_3 = chunk_size (bytes to read)
   c. If offset == 0: use initial data pointer from 0x473E6C
   d. Call transport_send (0x473514)
   e. Call transport_receive (0x473518)
   f. If error: set state = 3, return -1
   g. If first read (offset == 0):
      - Check field_2 (result) == -1 → error 0x19 (25 = "log empty")
      - Check field_3 (total_size) == 0 → error 0x14 (20 = "no data")
      - Store total_size as new remaining
   h. Copy received data to output buffer
   i. Advance: remaining -= chunk_size, offset += chunk_size, ptr += chunk_size
4. After all data received:
   - Byte-swap 4 trailing 32-bit fields at block+0x48, +0x4C, +0x50, +0x54
   - These are metadata: timestamp, count, etc.
5. Check if more data remaining → error 0x1A (26 = "incomplete")
6. Return 0 on success
```

### 8.3 Transport Abstraction

Both `zzOpenErrLog` and `zzGetLog` use **function pointers** for transport:
- `0x473514` → transport_send (points to RS-232 or TCP send function)
- `0x473518` → transport_receive (points to RS-232 or TCP receive function)
- `0x47350C` → transport_connect
- `0x473510` → transport_disconnect
- `0x473508` → connection state (0 = disconnected, non-zero = connected)

This is a **transport abstraction layer** — the same protocol logic works over RS-232 or TCP depending on which function pointers are installed.

---

## 9. TCP Block Receive (`zzRcvTcpBlk`)

TCP receive reads the full block in one `recv()` call (or chunked if partial):
- Reads 20-byte header first
- Extracts `data_length` from header field at +0x10
- Reads `data_length` more bytes
- Verifies CRC over header + data
- Returns block to caller

---

## 10. Command Codes

From disassembly and string analysis:

| Code | Hex | Command | Description |
|------|-----|---------|-------------|
| 0x48 | 72 | OPEN_ERRLOG | Open error log stream for a server |
| 0x1F | 31 | GET_LOG_DATA | Retrieve log data chunk |
| 0x06 | 6 | ACK | Acknowledge (handshake) |
| 0x15 | 21 | NACK | Negative acknowledge (handshake retry) |

Additional commands inferred from `zzSendCmd`, `zzSendDbCmd`, `zzSendRemoteCommand`:
- File transfer, database operations, configuration commands all use the same block format with different command codes in field_0.

---

## 11. Protocol Summary Diagram

```
┌─────────────────────────────────────────────────────┐
│                  BsTool Protocol Stack               │
├─────────────────────────────────────────────────────┤
│                                                      │
│  Application Layer                                   │
│  ├── -errlog: zzOpenErrLog (cmd=0x48) → zzGetLog    │
│  │            (cmd=0x1F, chunks of 448 bytes)        │
│  ├── -db: zzSendDbCmd                               │
│  ├── -cmd: zzSendCmd                                │
│  └── -cnf: zzSendConf                               │
│                                                      │
│  Transport Abstraction (function pointers)           │
│  ├── 0x473514 → send (RS-232 or TCP)                │
│  ├── 0x473518 → receive (RS-232 or TCP)             │
│  ├── 0x47350C → connect                             │
│  └── 0x473510 → disconnect                          │
│                                                      │
│  Protocol Layer                                      │
│  ├── "2111" Handshake (zzSend2111/zzRcv2111)        │
│  │   ├── 21 retries (TX), 5 retries (RX)            │
│  │   ├── Session ID (random, 15-bit)                │
│  │   ├── Sequence toggle (0↔1)                      │
│  │   └── ACK (status=6) / NACK (status=21)          │
│  │                                                   │
│  ├── Block Format (20-byte header + payload)        │
│  │   ┌──────┬──────┬──────┬──────┬──────┬──────┐   │
│  │   │ cmd  │ seq  │src/dst│param│ size │dlen  │   │
│  │   │ 2B   │ 2B   │ 4B   │ 4B  │ 4B   │ 4B   │   │
│  │   └──────┴──────┴──────┴──────┴──────┴──────┘   │
│  │   ┌─────────────────────────────────────────┐    │
│  │   │           data (dlen bytes)             │    │
│  │   └─────────────────────────────────────────┘    │
│  │                                                   │
│  └── CRC-16/ARC (poly=0xA001, init=0x0000)      │
│                                                      │
│  Physical Layer                                      │
│  ├── RS-232: SetupComm/SetCommState (19200 8N1)     │
│  │   ├── Redundant header send (2x for reliability) │
│  │   └── 20-byte buffered I/O                       │
│  └── TCP/IP: Winsock send/recv (raw binary blocks)  │
│      ├── NO DLE/STX/ETX framing (RS-232 only)        │
│      ├── NO CRC (TCP reliability suffices)           │
│      ├── NO "2111" handshake (RS-232 only)           │
│      ├── 20-byte BE header + raw data in one send() │
│      └── Optional encryption (zzCrIOL.dll)           │
│                                                      │
│  Byte Order: Big-Endian on wire (all fields swapped) │
│                                                      │
└─────────────────────────────────────────────────────┘
```

---

## 12. What We Can Now Implement in Go (Without BsTool.exe)

Based on this RE (corrected 2026-06-26), a Go-native TCP implementation is feasible:

1. **TCP connection** — `net.DialTimeout`, host from `COMMUNICATION_LINE` env var, port 1516
2. **Block header** — 20-byte struct, big-endian encoding. Go: `encoding/binary`
3. **TCP send** — `Block.MarshalBinary()` → `conn.Write()` (raw binary, no framing)
4. **TCP recv** — Read 20-byte header → parse → read data payload (raw binary)
5. **-errlog command** — cmd=0x48 to open, cmd=0x1F to retrieve in 448-byte chunks
6. **CP1252 decoding** — Already implemented
7. **RS-232 transport** (if needed) — `go.bug.st/serial` with DLE/STX/ETX framing + CRC-16/ARC

**NOT needed for TCP (RS-232 only):**
- DLE/STX/ETX framing (FrameBlock/UnframeBlock) — only for serial
- CRC-16/ARC — only for serial
- "2111" handshake — only for serial
- Session ID, sequence toggle — only for serial

**Still unknown** (would need live hardware or deeper RE):
- Exact encryption format of `zzCrIOL.dll` (for secure TCP blocks via `zzSendTcpBlk2`/`zzRcvTcpBlk2`)
- `magic.dll` licensing algorithm
- Server name resolution: `COMMUNICATION_LINE` provides hostname, resolved via `gethostbyname()` (DNS/hosts) or manual dotted-quad parser. Need to know if "AB01" is in DNS or if it's an IP.

**Recommended approach**: Implement TCP transport with raw binary blocks (now done), configure `COMMUNICATION_LINE` with the DNA node's IP address. Test against a real node to validate.