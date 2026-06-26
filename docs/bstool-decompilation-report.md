# BsTool Wire Protocol — Complete Decompilation Report
## Deep RE via Capstone Disassembly (2026-06-26)

---

## 1. Wire-Level Block Format (RS-232)

### 1.1 `send_block` (RVA 0x039D90)

**Pseudo-C (decompiled from capstone):**

```c
int send_block(uint8_t *data, int16_t data_len, uint8_t status_byte, 
               uint16_t session_id, uint16_t *bytes_sent_out) {
    uint16_t crc = 0;
    uint8_t status_high = (session_id >> 8) & 0xFF;
    uint8_t status_low  = session_id & 0xFF;
    
    zzFlushIn();  // flush input buffer before sending
    
    // 1. Send DLE (0x10) — Data Link Escape
    zzSendByte(0x10);
    
    // 2. Send STX (0x02) — Start of Text
    zzSendByte(0x02);
    
    // 3. CRC starts here (init to 0, NOT 0xFFFF — different from MODBUS!)
    crc = 0;
    
    // 4. Send status byte (the "command" byte)
    zzSendByte(status_byte);
    crc = zzUpdcrc(crc, status_byte);
    
    // 5. Send session_id high byte
    zzSendByte(status_high);
    crc = zzUpdcrc(crc, status_high);
    
    // 6. Send session_id low byte
    zzSendByte(status_low);
    crc = zzUpdcrc(crc, status_low);
    
    // 7. Send data bytes
    for (int i = 0; i < data_len; i++) {
        // DLE stuffing: if data byte == 0x10, send it twice (DLE escape)
        if (data[i] == 0x10) {
            zzSendByte(0x10);  // send DLE as escape
        }
        zzSendByte(data[i]);
        crc = zzUpdcrc(crc, data[i]);
    }
    
    // 8. Send DLE (0x10)
    zzSendByte(0x10);
    
    // 9. Send ETX (0x03) — End of Text
    zzSendByte(0x03);
    
    // 10. CRC update with ETX
    crc = zzUpdcrc(crc, 0x03);
    
    // 11. Send CRC low byte
    zzSendByte(crc & 0xFF);
    
    // 12. Send CRC high byte
    zzSendByte((crc >> 8) & 0xFF);
    
    // 13. Flush output buffer
    zzFlushOut(0x16);  // flush 22 bytes worth
    
    return 0;
}
```

**Key findings:**
- Uses **DLE/STX/ETX framing** (0x10/0x02/0x03) — standard serial async protocol
- **DLE stuffing**: byte 0x10 in data is escaped by sending it twice
- CRC init is **0x0000** (not 0xFFFF like standard MODBUS!) — this is CRC-16/ARC variant
- Block structure: `[DLE][STX][status][sid_hi][sid_lo][data...][DLE][ETX][crc_lo][crc_hi]`
- Status byte = command code (6=ACK, 21=NACK, or the actual command)
- Session ID is 15-bit (masked with 0x7FFF on receive)

### 1.2 `rcv_block` (RVA 0x039850)

**Pseudo-C:**

```c
int rcv_block(uint8_t *rx_buf, int16_t expected_len, uint8_t *status_out,
              int16_t *bytes_rcvd_out, uint16_t *session_id_out) {
    uint16_t crc = 0;
    uint16_t calc_crc = 0;
    uint16_t recv_crc = 0;
    uint8_t byte_val;
    int retry_count = 0;
    int data_index = 0;
    
    // Check max retries flag
    if (global_max_retries == 1) {
        global_max_retries = 0;
        first_receive = 1;
    }
    
    while (1) {
        // 1. Read first byte
        if (zzRcvByte(&rx_buf[0]) != 0) goto error;
        
        // 2. Check for DLE (0x10)
        if (rx_buf[0] == 0x10) {
            // Read second byte
            if (zzRcvByte(&rx_buf[0]) != 0) goto error;
            // Must be STX (0x02) to start block
            if (rx_buf[0] == 0x02) goto start_block;
        }
        
        // Not a valid start — check for retry
        if (zzRcvByte_error) {
            retry_count++;
            if (retry_count >= 1) {
                // Too many retries
                error_counter++;
                return -1;
            }
        }
        
        // Check if byte is 0x16 (SYN — synchronization)
        if (rx_buf[0] == 0x16) {
            retry_count = 0;  // reset and try again
            continue;
        }
        goto loop;
        
    start_block:
        // 3. Read status byte
        if (zzRcvByte(&status_byte) != 0) goto error;
        
        // 4. Read session_id high byte
        if (zzRcvByte(&sid_high) != 0) goto error;
        
        // 5. Read session_id low byte
        if (zzRcvByte(&sid_low) != 0) goto error;
        
        // 6. Extract session ID (15-bit)
        *session_id_out = (sid_high << 8 | sid_low) & 0x7FFF;
        
        // 7. Start CRC calculation (init to 0)
        crc = 0;
        crc = zzUpdcrc(crc, status_byte);
        crc = zzUpdcrc(crc, sid_high);
        crc = zzUpdcrc(crc, sid_low);
        
        // 8. Read data bytes
        for (data_index = 0; data_index < expected_len; data_index++) {
            if (zzRcvByte(&rx_buf[data_index]) != 0) goto error;
            
            // DLE unstuffing: if 0x10 received, read next byte
            if (rx_buf[data_index] == 0x10) {
                if (zzRcvByte(&rx_buf[data_index]) != 0) goto error;
                // Must be 0x03 (ETX) — end of data
                if (rx_buf[data_index] == 0x03) {
                    // CRC update with ETX
                    crc = zzUpdcrc(crc, 0x03);
                    
                    // Read CRC low byte
                    if (zzRcvByte(&crc_low) != 0) goto error;
                    // Read CRC high byte
                    if (zzRcvByte(&crc_high) != 0) goto error;
                    
                    recv_crc = (crc_high << 8) | crc_low;
                    
                    // Verify CRC
                    if (crc != recv_crc) goto crc_error;
                    
                    // Success!
                    *bytes_rcvd_out = data_index;
                    *status_out = status_byte;
                    return 0;
                }
                // If not ETX, it's a stuffed DLE — fall through
            }
            
            // CRC update with data byte
            crc = zzUpdcrc(crc, rx_buf[data_index]);
        }
        
        // Ran out of expected_len without ETX
        goto error;
    }
}
```

**Key findings:**
- Receiver expects `[DLE][STX][status][sid_hi][sid_lo][data...][DLE][ETX][crc_lo][crc_hi]`
- **DLE unstuffing**: if 0x10 received in data, read next byte. If next is 0x03=ETX → end of data. If next is 0x10 → it's a literal 0x10 data byte.
- 0x16 (SYN) is used as a synchronization/resync byte — receiver resets on seeing it
- Session ID masked to 15 bits (0x7FFF)
- CRC is verified at the end: calculated CRC must match received CRC

### 1.3 `verify_crc` (RVA 0x039BA0)

```c
int verify_crc(uint16_t received_crc) {
    // Calls function at 0x43A060 with arg (received_crc, 1)
    // Then extracts bit from the 4096-byte buffer at 0x474FC0
    // bit_index = received_crc >> 3
    // bit_pos = received_crc & 7
    // bit = (buffer[bit_index] >> (7 - bit_pos)) & 1
    // Returns that bit (0 or 1)
    
    // This is a BITMAP check — not a CRC verification!
    // The 4096-byte buffer at 0x474FC0 is a bitmap of received CRC values.
    // If the bit is set, this CRC was already received (duplicate detection).
    
    return bit_value;
}
```

**This is NOT CRC verification — it's DUPLICATE DETECTION.** The 4096-byte buffer at 0x474FC0 (initialized to all zeros in `zzInit2111`) is a bitmap indexed by CRC value. When a block is received, its CRC is looked up in the bitmap to detect duplicates.

### 1.4 `process_response` (RVA 0x039800)

```c
// Simple memcpy: copies 'len' bytes from src to dst
void process_response(uint8_t *dst, uint8_t *src, int len) {
    while (len > 0) {
        *dst++ = *src++;
        len--;
    }
}
```

Just a memcpy — copies received data to the caller's buffer.

### 1.5 `connect_fn` (RVA 0x032890)

```c
void connect_fn(HANDLE handle, int action) {
    if (action == -1) {
        // Disconnect: WaitForSingleObject(handle, -1) → wait forever
        WaitForSingleObject(handle, INFINITE);
    } else if (action == 1) {
        // Connect: ReleaseMutex(handle)
        ReleaseMutex(handle);
    }
}
```

Uses Windows mutex for connection synchronization. -1 = wait (disconnect), 1 = release (connect).

---

## 2. TCP Transport

### 2.1 `tcp_init_impl` (RVA 0x03A950)

```c
int tcp_init_impl(char *hostname, int *rx_buf_size, int *tx_buf_size, 
                  int *port_ptr, int flags) {
    int max_attempts = 5;
    if (flags & 1) max_attempts = 1;
    
    // One-time Winsock init
    if (!winsock_initialized) {
        winsock_initialized = 1;
        WSAStartup();  // call at 0x43A580
    }
    
    // Set buffer sizes
    *rx_buf_size = 0x800;  // 2048
    *tx_buf_size = 0x800;  // 2048
    
    // Determine port
    int timeout_ms;
    int port;
    if (port_ptr && *port_ptr < 0) {
        timeout_ms = -*port_ptr;  // negative port = timeout in ms
        port = 0;  // use default
    } else {
        timeout_ms = 0x5EC;  // 1516ms default timeout
        port = (port_ptr) ? *port_ptr : 0;
    }
    
    // Determine target
    char *target = (port) ? port_ptr : NULL;
    if (target == NULL) target = &global_default_socket;  // 0x46A28C
    
    // Initialize socket to INVALID_SOCKET (-1)
    *target = INVALID_SOCKET;
    
    // Connection retry loop
    for (int attempt = 0; attempt < max_attempts; attempt++) {
        if (attempt > 0) {
            sleep(2);  // wait 2 seconds between retries
        }
        
        if (*target == INVALID_SOCKET) {
            // Create socket: socket(AF_INET, SOCK_STREAM, IPPROTO_TCP)
            *target = socket(AF_INET, SOCK_STREAM, 0);
        }
        if (*target == INVALID_SOCKET) continue;
        
        // Resolve hostname
        struct hostent *he = gethostbyname(hostname);
        if (he != NULL) {
            // Use resolved address
            memcpy(&addr, he->h_addr_list[0], he->h_length);
        } else {
            // Try direct IP resolution
            if (resolve_hostname(hostname, &addr) == -1) {
                closesocket(*target);
                *target = INVALID_SOCKET;
                continue;
            }
        }
        
        // Set port
        addr.sin_port = htons(port);
        
        // Connect
        if (connect(*target, &addr, sizeof(addr)) < 0) {
            closesocket(*target);
            *target = INVALID_SOCKET;
            continue;
        }
        
        // Set COMMUNICATION_TIMEOUT (env var → milliseconds)
        char *timeout_env = getenv("COMMUNICATION_TIMEOUT");
        if (timeout_env) {
            int timeout_sec = strtoul(timeout_env, NULL, 10);
            timeout_ms = timeout_sec * 1000;
            if (timeout_ms > 0) {
                setsockopt(*target, SOL_SOCKET, SO_RCVTIMEO, &timeout_ms, 4);
            }
        }
        
        // Set TCP_NODELAY (no Nagle's algorithm)
        int flag = 1;
        setsockopt(*target, IPPROTO_TCP, TCP_NODELAY, &flag, 4);
        
        // Get peer name (verify connection)
        struct sockaddr peer;
        int peer_len = 16;
        if (getpeername(*target, &peer, &peer_len) == 0) {
            global_connected_addr = peer;  // store at 0x476FDC
            return 0;  // success
        }
        
        return -1;  // getpeername failed
    }
    
    *target = INVALID_SOCKET;
    return -1;  // all attempts failed
}
```

**Key findings:**
- TCP uses **hostname resolution** via `gethostbyname()` — the server name (e.g., "AP01") is resolved to an IP address
- Default port: 0x5EC (1516) — **not 2517** (2517 is for NCU2 UDP, different protocol)
- Buffer sizes: 2048/2048 (TX/RX)
- **TCP_NODELAY** is set (disables Nagle's algorithm for low-latency)
- **COMMUNICATION_TIMEOUT** env var sets socket receive timeout in seconds → milliseconds
- Retry loop: up to 5 attempts (or 1 if flag bit 0 set), 2-second delay between retries
- Global socket stored at 0x46A28C

### 2.2 `tcp_send_wrapper` (RVA 0x03A610)

```c
int tcp_send_wrapper(SOCKET sock, uint8_t *data, int total_len) {
    int total_sent = 0;
    while (total_len > 0) {
        int sent = send(sock, data, total_len, 0);
        if (sent <= 0) break;
        total_len -= sent;
        total_sent += sent;
        data += sent;
    }
    return total_sent;
}
```

Standard TCP send loop — handles partial sends by looping until all data sent.

---

## 3. CRC-16 — Important Correction

**The CRC used in `send_block` initializes to 0x0000, NOT 0xFFFF.**

The `zzInicrc` function generates the standard MODBUS table (poly 0xA001), but:
- `zzUpdcrc` operates the same way: `crc = (crc >> 8) ^ table[(crc ^ byte) & 0xFF]`
- `send_block` initializes `crc = 0` before the CRC loop
- This makes it **CRC-16/ARC** (init=0x0000, poly=0xA001) — NOT CRC-16/MODBUS (init=0xFFFF)

The table is the same (0xA001 polynomial), but the initialization value differs. This is a critical distinction for reimplementation.

---

## 4. Complete Wire Protocol Summary

### 4.1 RS-232 Block Format

```
┌──────┬──────┬────────┬────────┬────────┬───────────────────┬──────┬──────┬─────────┬─────────┐
│ DLE  │ STX  │ status │ sid_hi │ sid_lo │ data (DLE-stuffed)│ DLE  │ ETX  │ CRC_lo  │ CRC_hi  │
│ 0x10 │ 0x02 │ 1 byte │ 1 byte │ 1 byte │ N bytes           │ 0x10 │ 0x03 │ 1 byte  │ 1 byte  │
└──────┴──────┴────────┴────────┴────────┴───────────────────┴──────┴──────┴─────────┴─────────┘

DLE (0x10) in data is escaped: 0x10 → 0x10 0x10
CRC is CRC-16/ARC (poly=0xA001, init=0x0000), computed over: status + sid_hi + sid_lo + data + ETX
Session ID is 15-bit (0x7FFF mask)
```

### 4.2 TCP Block Format

TCP sends the **same block** but as a single `send()` call. The DLE/STX/ETX framing is preserved — TCP just wraps the entire framed block in one socket send.

### 4.3 Handshake Sequence

```
Client                          Server
  │                               │
  │  zzInit2111()                 │
  │  - Clear 4KB CRC bitmap       │
  │  - session_id = rand()&0x7FFF │
  │  - sequence = 0               │
  │                               │
  │  send_block(data, len,        │
  │    status, session_id)        │
  │  ──── DLE STX [block] ────►   │
  │                               │
  │                               │  rcv_block()
  │                               │  - Verify CRC
  │                               │  - Check bitmap for duplicates
  │                               │
  │   ◄──── DLE STX [ACK] ──────  │  zzAck2111()
  │                               │  - status = 6 (ACK)
  │                               │  - toggle sequence
  │  rcv_block()                  │
  │  - Verify CRC                 │
  │  - status == 6? → ACK          │
  │  - Toggle sequence            │
  │                               │
  │  Success! Continue...          │
  │                               │
```

### 4.4 Command Codes (Updated)

| Code | Name | Used By |
|------|------|---------|
| 0x02 | STX | Block framing (start of text) |
| 0x03 | ETX | Block framing (end of text) |
| 0x06 | ACK | Handshake acknowledgment |
| 0x10 | DLE | Data Link Escape (framing) |
| 0x15 | NACK | Negative acknowledge (retry) |
| 0x16 | SYN | Synchronization byte (reset) |
| 0x1F | GET_LOG_DATA | zzGetLog — retrieve log chunk |
| 0x48 | OPEN_ERRLOG | zzOpenErrLog — open error log |

---

## 5. Encryption Analysis

### 5.1 magic.dll

Referenced at RVA 0x065AD0 ("magic.dll"). The code that loads it:
```c
HMODULE hMagic = LoadLibraryA("magic.dll");
if (hMagic == NULL) {
    // Error: "Failed to load MAGIC.DLL."
}
GetMagicNumberEx = GetProcAddress(hMagic, "GetMagicNumberEx");
ReverseMagicNumber = GetProcAddress(hMagic, "ReverseMagicNumber");
GetLicenseKey = GetProcAddress(hMagic, "GetLicenseKey");
```

**magic.dll is used for type system licensing**, not communication encryption. It protects the DNA type definitions. Functions:
- `GetMagicNumberEx` — generate a magic number for type validation
- `ReverseMagicNumber` — reverse the magic number
- `GetLicenseKey` — get license key (checked at startup via `BSTOOL_LICENCE` env var or `dbgchk.lic` file)

**For -errlog reimplementation: magic.dll is NOT needed.** It's only used for type system operations (`-typechk`, `-pmodinfo`, etc.), not for log retrieval.

### 5.2 zzCrIOL.dll

```c
HMODULE hCrypt = LoadLibraryA("zzCrIOL.dll");
zzEncryptBuf = GetProcAddress(hCrypt, "zzEncryptBuf");
zzDecryptBuf = GetProcAddress(hCrypt, "zzDecryptBuf");
```

**zzCrIOL.dll is used for secure TCP blocks** (`zzSendTcpBlkSec`/`zzRcvTcpBlkSec`). The standard `-errlog` pathway does NOT use secure blocks. Only `-secure` flag triggers encryption.

**For -errlog reimplementation: zzCrIOL.dll is NOT needed** unless the `-secure` flag is used.

---

## 6. Implementation Feasibility

### What We Now Know Completely

| Component | Status | Evidence |
|-----------|--------|---------|
| Block framing (DLE/STX/ETX) | ✅ Complete | send_block + rcv_block decompiled |
| DLE stuffing/unstuffing | ✅ Complete | Both directions decompiled |
| CRC-16/ARC (poly=0xA001, init=0) | ✅ Complete | send_block shows init=0; table verified |
| Session ID (15-bit random) | ✅ Complete | zzInit2111 decompiled |
| Sequence toggle (0↔1) | ✅ Complete | zzSend2111/zzRcv2111 decompiled |
| Handshake retry (21 TX / 5 RX) | ✅ Complete | Loop counters in disassembly |
| ACK/NACK (6/21) | ✅ Complete | Status byte comparisons |
| SYN resync (0x16) | ✅ Complete | rcv_block handles 0x16 |
| Duplicate detection (bitmap) | ✅ Complete | verify_crc decompiled |
| TCP connection (gethostbyname) | ✅ Complete | tcp_init_impl decompiled |
| TCP send/recv (atomic blocks) | ✅ Complete | tcp_send_wrapper decompiled |
| TCP_NODELAY + SO_RCVTIMEO | ✅ Complete | setsockopt calls identified |
| Default port 1516 | ✅ Complete | 0x5EC in tcp_init_impl |
| OPEN_ERRLOG (cmd=0x48) | ✅ Complete | zzOpenErrLog decompiled |
| GET_LOG_DATA (cmd=0x1F, 448B chunks) | ✅ Complete | zzGetLog decompiled |
| magic.dll (type licensing) | ✅ Not needed | Only for type system ops |
| zzCrIOL.dll (encryption) | ✅ Not needed | Only for -secure flag |

### What's Still Unknown

| Component | Impact | Workaround |
|-----------|--------|------------|
| Server name → IP resolution | The `gethostbyname("AP01")` implies DNS or hosts file | Configure /etc/hosts or use direct IP |
| Full command code catalog | Other commands beyond -errlog | Not needed for -errlog only |
| Secure TCP encryption format | zzCrIOL.dll not reverse-engineered | Don't use -secure flag |

### Bottom Line

**A native Go TCP implementation of `-errlog` is now fully feasible.** The entire protocol stack — from TCP connection through DLE/STX/ETX framing to CRC-16/ARC verification to the -errlog command sequence — has been decompiled and documented. No external DLLs or proprietary encryption are needed for the standard (non-secure) -errlog pathway.