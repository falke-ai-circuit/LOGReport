# BsTool Deep RE — Corrected Findings (2026-06-26)

## CRITICAL CORRECTIONS to previous analysis

### 1. TCP transport does NOT use DLE/STX/ETX framing

**Previous (wrong):** TCP wraps the same DLE/STX/ETX framed block in one `send()` call.

**Actual (verified by disassembly):**

`zzSendTcpBlk` (0x43B570):
```
1. Calculate total_size = 0x14 + block.data_length  (same as RS-232)
2. send16(block+0)     — byte-swap command field to big-endian IN PLACE
3. send16(block+2)     — byte-swap sequence field IN PLACE
4. send32(block+4)     — byte-swap source field IN PLACE
5. send32(block+8)     — byte-swap param field IN PLACE
6. send32(block+0xC)   — byte-swap size field IN PLACE
7. send32(block+0x10)  — byte-swap data_length field IN PLACE
8. tcp_send_wrapper(socket_global_0x46A28C, block, total_size) — ONE raw send()
9. Compare sent == total_size → return 0 or -1
```

**NO call to send_block. NO DLE/STX/ETX. NO CRC. NO DLE stuffing. NO handshake.**
The raw 20-byte big-endian header + raw data payload is sent directly over TCP.

`zzRcvTcpBlk` (0x43ABF0):
```
1. Calculate total_size = 0x14 + block.data_length
2. Read header (20 bytes) via tcp_recv_wrapper(socket, block, 20)
3. send16/send32 — byte-swap header fields BACK to host order (little-endian)
4. Extract data_length from header[0x10]
5. Read data (data_length bytes) via tcp_recv_wrapper(socket, block+0x14, data_length)
6. Return 0 on success, -1 on failure
```

**NO DLE unstuffing. NO CRC verification. NO framing markers.**
TCP reliability guarantees replace serial-level error detection.

### 2. The "2111" handshake (DLE/STX/ETX) is RS-232 ONLY

`zzSendRsBlk` (0x438290):
```
1. Calculate total_size = 0x14 + block.data_length
2. send16/send32 — byte-swap header fields
3. call zzSend2111(block, &total_size)
   → zzSend2111 calls send_block(data, data_len, status_byte, session_id)
   → send_block does: DLE STX status sid data... DLE ETX crc_lo crc_hi
4. send16/send32 AGAIN (redundant re-send of header for reliability)
5. If result != 0, call zzFlushIn
6. Return result
```

Only the RS-232 path goes through `zzSend2111` → `send_block` (DLE/STX/ETX framing).
The TCP path bypasses all of this.

### 3. Hostname comes from COMMUNICATION_LINE env var (confirmed by GR15)

Flow:
```
getenv("COMMUNICATION_LINE")  →  hostname string (e.g., "AB01" or an IP address)
    ↓
tcp_init_impl(hostname, &rx_buf_size, &tx_buf_size, &port, flags)
    ↓
gethostbyname(hostname)  →  struct hostent (DNS/hosts file resolution)
    ↓ (if NULL)
sub_0003A6C0(hostname, &addr)  →  manual dotted-quad IP parser
    (uses isdigit() + atoi() + strchr('.') to parse "a.b.c.d" → 4-byte IP)
    ↓
connect(socket, &addr, sizeof(addr))
```

So `COMMUNICATION_LINE` is the hostname/IP of the DNA node, NOT a serial line identifier.
The same env var serves both transports:
- RS-232: `COMMUNICATION_LINE` = serial port name (e.g., "COM1" or "\\\\\.\\COM1")
- TCP: `COMMUNICATION_LINE` = hostname or IP address (e.g., "AB01" resolved via DNS, or "192.168.1.100")

### 4. Transport abstraction (function pointers)

`zzOpenErrLog` and `zzGetLog` use function pointers for transport:
- `0x47350C` → transport_connect (RS-232: zzInitRsLineIO, TCP: tcp_init_impl)
- `0x473510` → transport_disconnect
- `0x473514` → transport_send (RS-232: zzSendRsBlk, TCP: zzSendTcpBlk)
- `0x473518` → transport_receive (RS-232: zzRcvRsBlk, TCP: zzRcvTcpBlk)
- `0x473508` → connection state (0 = disconnected, non-zero = connected)

When TCP mode is selected, `0x473514` points to `zzSendTcpBlk` which sends RAW binary blocks.
When RS-232 mode is selected, `0x473514` points to `zzSendRsBlk` which uses DLE/STX/ETX framing.

### 5. zzSendTcpBlk2 / zzRcvTcpBlk2 — different protocol variant

`zzSendTcpBlk2` (0x43B610) uses:
- Mutex synchronization (WaitForSingleObject/ReleaseMutex via 0x476FDC)
- Magic number 0x15A71234 prepended to the block (byte-swapped via send32)
- Larger stack frame (0x1098 bytes vs 0x8 bytes for zzSendTcpBlk)
- Dynamic DLL loading (LoadLibraryA/GetProcAddress for something)

`zzRcvTcpBlk2` (0x43AD30):
- Also uses mutex (0x476FDC)
- Reads 4 bytes first (the magic number?), then byte-swaps via send32
- Uses 0x476FD4 (different mutex/handle from zzRcvTcpBlk)

These "2" variants appear to be a newer protocol version with synchronization and a magic header.
The standard `-errlog` pathway likely uses the original `zzSendTcpBlk`/`zzRcvTcpBlk`.

### 6. send16 / send32 — byte-swap in place

`send16` (0x4380B0): Swaps a 16-bit value in place (host LE → wire BE):
```c
void send16(uint16_t *val) {
    *val = (*val >> 8) | (*val << 8);
}
```

`send32` (0x4380E0): Swaps a 32-bit value in place:
```c
void send32(uint32_t *val) {
    *val = ((*val >> 24) & 0xFF) | ((*val >> 8) & 0xFF00) |
           ((*val << 8) & 0xFF0000) | ((*val << 24) & 0xFF000000);
}
```

IMPORTANT: These modify the block IN PLACE. After sending, the header is in big-endian.
The receiver calls send16/send32 again to swap back to host order.

### 7. Corrected TCP wire format

```
TCP sends RAW binary (no framing):

┌─────────────────────────────────────────────────────────────┐
│                    20-byte header (big-endian)                │
├──────┬──────┬──────┬──────┬──────┬──────┬──────────────────────┤
│ cmd  │ seq  │src/dst│param │ size │dlen  │  data (dlen bytes)  │
│ 2B BE│ 2B BE│ 4B BE│ 4B BE│ 4B BE│ 4B BE│  raw payload        │
├──────┴──────┴──────┴──────┴──────┴──────┴──────────────────────┤
│                     sent in ONE tcp send() call              │
└─────────────────────────────────────────────────────────────┘

No DLE/STX/ETX.
No CRC.
No byte stuffing.
No handshake protocol.
No session ID.
No sequence toggle.
Just: byte-swap header → send → recv → byte-swap back.
```

### 8. zzSendByte (sub_38220) — RS-232 only

`sub_38220` (zzSendByte) writes to a 20-byte send buffer at 0x473E88.
When the buffer fills (position >= 0x14 = 20), it flushes via `WriteFile` through
the handle at 0x473EAC. This is the serial port write path.
TCP does NOT use this function at all.

### Summary of corrections needed in Go code

| Component | Previous (wrong) | Corrected |
|-----------|------------------|-----------|
| TCP block format | DLE/STX/ETX framed | Raw binary (20B header + data) |
| TCP CRC | CRC-16/ARC computed | No CRC on TCP |
| TCP handshake | 2111 protocol (21 retries, ACK/NACK) | No handshake on TCP |
| TCP DLE stuffing | Implemented | Not needed |
| TCP send | FrameBlock → write | Block.MarshalBinary → write |
| TCP recv | Read framed bytes → UnframeBlock | Read 20B header → read data |
| Hostname source | Server name (AP01) | COMMUNICATION_LINE env var |
| CRC init | 0x0000 (ARC) | Correct for RS-232, but TCP has no CRC |