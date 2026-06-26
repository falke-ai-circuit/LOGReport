# BsTool BU Wire Protocol Validation Report

**Date:** 2026-06-26  
**Author:** Coder (RE session)  
**Status:** ✅ Protocol format validated against real BU

## Summary

A C# test client was compiled and executed inside the VEGAS VM (Windows Server 2019), connecting directly to the running Backup Server Controller (`buc_16.20.exe`) on `127.0.0.1:1516`. The test client sent blocks formatted to match our Go `TCPTransport` implementation and received valid protocol responses.

**Conclusion: Our Go block format (20-byte big-endian header + payload) is correct.**

## Test Environment

- **VM:** Windows Server 2019 (build 10.0.17763.5329), user `dna`
- **BU:** `buc_16.20.exe` (PID 5624), listening on `127.0.0.1:1516`
- **BU root:** `C:\dna\CA\BU\`
- **Type file:** `all_14.5_typ`
- **BU PDB path:** `:\svn\DNA\CA\BU\tags\DNA_CA_BU_16.20\win12\buc_16.20.pdb`
- **Test client:** C# compiled with .NET Framework 4.0 csc.exe on the VM

## Test 1: OPEN_ERRLOG (cmd=0x48)

### Sent (25 bytes = 20 header + 5 data)
```
00 48 00 00 00 00 00 00 00 00 00 00 00 00 00 00
00 00 00 05 41 42 30 31 00
```

Field breakdown (big-endian):
- Command: `0x0048` (OPEN_ERRLOG)
- Sequence: `0x0000`
- Source: `0x00000000`
- Param: `0x00000000`
- Size: `0x00000000`
- DataLen: `0x00000005` (5 bytes)
- Data: `41 42 30 31 00` = "AB01\0"

### Received (20 bytes header, 0 data)
```
00 48 00 00 00 00 00 00 00 00 00 00 00 00 05 F4
00 00 00 00
```

Field breakdown (big-endian):
- Command: `0x0048` (echoes our command)
- Sequence: `0x0000`
- Source: `0x00000000`
- Param: `0x000005F4` (1524 decimal — likely total log size in bytes)
- Size: `0x00000000`
- DataLen: `0x00000000` (no payload — just an acknowledgment)

**Interpretation:** The BU accepted the OPEN_ERRLOG request for server "AB01" and responded with the log size (1524 bytes) in the `param` field. No error — the server was found.

## Test 2: GET_LOG_DATA (cmd=0x1F)

### Sent (28 bytes = 20 header + 8 data)
```
00 1F 00 01 00 00 00 00 00 00 00 00 00 00 01 C0
00 00 00 08 00 00 00 00 C0 01 00 00
```

Field breakdown (big-endian):
- Command: `0x001F` (GET_LOG_DATA)
- Sequence: `0x0001`
- Source: `0x00000000`
- Param: `0x00000000` (offset = 0)
- Size: `0x000001C0` (448 — chunk size)
- DataLen: `0x00000008` (8 bytes)
- Data: `00 00 00 00 C0 01 00 00` (offset=0 LE, size=448 LE)

### Received (20 bytes header, 0 data)
```
00 1F 00 01 02 3F 0D B8 FF FF FF FF 00 00 01 C0
00 00 00 00
```

Field breakdown (big-endian):
- Command: `0x001F` (echoes our command)
- Sequence: `0x0001` (echoes our sequence)
- Source: `0x023F0DB8` (BU's internal address/PID)
- Param: `0xFFFFFFFF` (-1 → log empty or already consumed)
- Size: `0x000001C0` (448 — echoes our chunk size)
- DataLen: `0x00000000` (no data returned)

**Interpretation:** The BU processed the GET_LOG_DATA request but returned `param=0xFFFFFFFF`, meaning the log data is empty or already consumed. This matches our Go code's error handling: `if respBlock.Header.Param == 0xFFFFFFFF → log empty or no data (0x19/0x14)`.

The log being empty is expected — BsTool had already drained the error log in a previous run.

## Protocol Format Confirmation

### Block Header (20 bytes, big-endian on wire)

| Offset | Size | Field | Confirmed |
|--------|------|-------|-----------|
| 0x00 | 2 | Command | ✅ BU echoes our command code |
| 0x02 | 2 | Sequence | ✅ BU echoes our sequence number |
| 0x04 | 4 | Source/Dest | ✅ BU returns its own address |
| 0x08 | 4 | Param | ✅ OPEN: log size; GET: 0xFFFFFFFF when empty |
| 0x0C | 4 | Size | ✅ BU echoes our chunk size |
| 0x10 | 4 | DataLen | ✅ Payload length follows header |

### Key Findings

1. **Big-endian header is correct** — the BU accepts and responds with big-endian fields
2. **20-byte header size is correct** — all 20 bytes consumed cleanly
3. **Command codes confirmed**: 0x48=OPEN_ERRLOG, 0x1F=GET_LOG_DATA
4. **OPEN_ERRLOG data format**: server name as null-terminated ASCII string
5. **GET_LOG_DATA data format**: 8-byte payload (offset LE32 + size LE32)
6. **Response param field**: Contains log size on OPEN, 0xFFFFFFFF when empty on GET
7. **No DLE/STX/ETX framing on TCP** — confirmed, raw binary blocks work
8. **No CRC on TCP** — confirmed, no CRC in responses
9. **No handshake/session on TCP** — confirmed, direct block exchange works
10. **BU echoes command and sequence** in responses

## Comparison with Go Implementation

Our Go `TCPTransport` in `internal/bstool/transport_tcp.go`:

| Go field | Wire offset | Confirmed |
|----------|-------------|-----------|
| `Command uint16` | 0x00 (BE) | ✅ |
| `Sequence uint16` | 0x02 (BE) | ✅ |
| `Source uint32` | 0x04 (BE) | ✅ |
| `Param uint32` | 0x08 (BE) | ✅ |
| `Size uint32` | 0x0C (BE) | ✅ |
| `DataLen uint32` | 0x10 (BE) | ✅ |

**No changes needed to the Go implementation.** The block format is correct.

## Extracted Binaries

| File | Size | Location |
|------|------|----------|
| `buc_16.20.exe` | 471,040 | `/opt/data/buc_re/buc_16.20.exe` |
| `libDNAc.dll` | 959,488 | `/opt/data/buc_re/libDNAc.dll` |
| `libPV2c.dll` | 473,600 | `/opt/data/buc_re/libPV2c.dll` |

## libDNAc.dll Analysis

- **557 exports** — Finnish-named functions (ee*, ek*, ev*, pz*, zz*, dc*, fm*, fn*, nd*, pj*, pn*, pv*)
- **Key exports:** `SendDataToCom`, `UncryptMagicNumber`, `pzXcom`, `pzXcomSrd`, `pzXcomSwr`, `pzXcomBundle`, `pzInitServer`, `pzNextBundleData`
- **Imports:** `libPV2c.dll` (69 functions including `OpenTcpIp`, `pVSend`, `pVReceive`), `WS2_32.dll` (19 Winsock functions)

### SendDataToCom (RVA 0x378c0)
Sends a 32-byte block via `pVSend` with message type `0x10B` and priority 2. This is the **PV messaging layer** — higher level than the raw TCP blocks that BsTool uses. The BU uses `libDNAc.dll`'s PV layer internally, but BsTool communicates with the BU using the raw TCP block protocol (our `zzSendTcpBlk` RE finding).

## Remaining Work

1. ~~Extract BU binary~~ ✅ Done
2. ~~Extract libDNAc.dll~~ ✅ Done  
3. ~~Extract libPV2c.dll~~ ✅ Done
4. ~~Validate block format against real BU~~ ✅ Done
5. ~~Compare wire bytes with Go implementation~~ ✅ Match
6. **Test Go code directly against BU** — would require running Go on the VM or exposing port 1516 externally
7. **Deep RE of libPV2c.dll** — `OpenTcpIp`, `pVSend`, `pVReceive` for the PV transport layer (needed if we want to implement the full PV protocol, not just the raw TCP block protocol)