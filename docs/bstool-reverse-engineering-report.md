# BsTool.exe Reverse-Engineering Report

**Date**: 2026-06-25  
**Analyst**: coder  
**Binary**: BsTool.exe v9.29 (MD5: bac442f181de5564ea5d73de30657ca2, 468,480 bytes)  
**Sources**: PE binary analysis (objdump, strings), valmet knowledge report, Python wrapper source, captured help output

---

## 1. Binary Identity

| Property | Value |
|----------|-------|
| File | BsTool_9.29.exe |
| Version | 9.29 (MajorImageVersion=9, MinorImageVersion=2900) |
| Format | PE32 (32-bit x86) |
| Subsystem | Windows Console (CUI) |
| Compiler | MSVCR120 (Visual Studio 2013) |
| Linked | Mon May 24 12:19:14 2021 |
| PDB Path | `D:\svn\DNA\CA\BU\BsTool\tags\DNA_CA_BSTOOL_9.29\win12\BsTool_9.29.pdb` |
| SVN Source | `D:\svn\DNA\CA\BU\BsTool\tags\DNA_CA_BSTOOL_9.29\win12\` |
| Sections | 5 (.text, .rdata, .data, .rsrc, .reloc) |
| Code size | 0x5B400 (373KB) |
| Exports | 232 functions (0xE8) |

### Section Layout

| Section | VAddr | VSize | RawSize | Flags |
|---------|-------|-------|---------|-------|
| .text | 0x00001000 | 0x0005B372 | 0x0005B400 | CODE+EXEC+READ |
| .rdata | 0x0005D000 | 0x00002210 | 0x00002400 | DATA+READ |
| .data | 0x00060000 | 0x00048814 | 0x0000F800 | DATA+READ+WRITE |
| .rsrc | 0x000A9000 | 0x00000508 | 0x00000600 | DATA+READ |
| .reloc | 0x000AA000 | 0x00004BD8 | 0x00004C00 | DATA+DISCARD+READ |

---

## 2. Import Analysis — Communication Stack

### 2.1 KERNEL32.dll — Serial Port + File I/O

**Serial communication APIs (critical — RS-232 line):**
- `SetupComm` — initializes serial port communications parameters
- `GetCommState` / `SetCommState` — gets/sets serial port DCB (baud, parity, etc.)
- `GetCommTimeouts` / `SetCommTimeouts` — serial port timeout control

**File I/O:**
- `CreateFileA`, `ReadFile`, `WriteFile`, `CloseHandle` — file/device I/O
- `FindFirstFileA`, `FindNextFileA`, `FindClose` — directory enumeration
- `GetTempPathA`, `GetTempFileNameA` — temp file management
- `CompareFileTime`, `GetLocalTime`, `SystemTimeToFileTime` — time/date

**Synchronization:**
- `CreateMutexA`, `ReleaseMutex`, `WaitForSingleObject` — single-instance enforcement
- `Sleep` — timing/delays

**Dynamic loading:**
- `LoadLibraryA`, `GetProcAddress`, `FreeLibrary` — runtime DLL loading (magic.dll, zzCrIOL.dll, iphlpapi.dll, icmp.dll)

### 2.2 WS2_32.dll — Winsock (TCP/UDP)

16 socket functions imported by ordinal. From strings analysis, used for:
- TCP block communication (`zzSendTcpBlk`, `zzRcvTcpBlk`, `zzInitTcpLineIO`)
- UDP communication (XD_UDP_PORT, multicast for NCU2)
- Network discovery (`zzGetHWAddressByIP`)

### 2.3 MSVCR120.dll — C Runtime

Standard C library: stdio (printf, fprintf, fopen, fclose), string ops (strstr, strncmp, memcpy), memory (malloc, calloc, free), math (_libm_sse2_log10_precise), threading (_beginthread), signal handling.

### 2.4 Dynamically Loaded DLLs

| DLL | Functions | Purpose |
|-----|-----------|---------|
| `magic.dll` | `GetMagicNumberEx`, `ReverseMagicNumber`, `GetLicenseKey` | License/encryption — type system protection |
| `zzCrIOL.dll` | `zzEncryptBuf`, `zzDecryptBuf` | Communication encryption |
| `iphlpapi.dll` | (IP Helper API) | Network interface lookup |
| `icmp.dll` | `IcmpCreateFile`, `IcmpSendEcho`, `IcmpCloseHandle` | Ping (NCU2 network setup) |

---

## 3. Export Analysis — Internal Library API

BsTool exports 232 functions, organized into three major families:

### 3.1 `zz*` Functions — Communication & File System Library (~80 functions)

**Transport layer:**
- `zzInitRsLineIO` — Initialize RS-232 serial line communication
- `zzInitTcpLineIO`, `zzInitTcpLineIO2` — Initialize TCP communication
- `zzClearRsLineIO`, `zzClearTcpLineIO` — Cleanup
- `zzSendRsBlk`, `zzRcvRsBlk` — Send/receive blocks over RS-232
- `zzSendTcpBlk`, `zzRcvTcpBlk`, `zzSendTcpBlk2`, `zzRcvTcpBlk2` — Send/receive blocks over TCP
- `zzSendTcpBlkSec`, `zzRcvTcpBlkSec` — Secure (encrypted) TCP blocks

**Protocol "2111" — handshake/init sequence:**
- `zzInit2111`, `zzSend2111`, `zzRcv2111`, `zzAck2111` — Protocol negotiation/acknowledgment

**Command layer:**
- `zzSendCmd` — Send command to BU server
- `zzSendRemoteCommand` — Send remote command
- `zzSendValCmd` — Send value command
- `zzSendConf` — Send configuration command
- `zzSendDbCmd` — Send database command
- `zzSendScript` — Send script for execution
- `zzSendFile`, `zzSendNFile`, `zzRcvFile` — File transfer
- `zzSendPnetCmd` — PROFINET command
- `zzGetPnetCmdResult` — Get PROFINET result

**Error log retrieval (the -errlog pathway):**
- `zzOpenErrLog` — Open error log stream from a node
- `zzGetLog` — Retrieve log messages

**File system operations:**
- `zzInitFileIO`, `zzInitFileIO2`, `zzInitFileIO3`, `zzClearFileIO` — File I/O lifecycle
- `zzFormatDisk`, `zzFormatFS`, `zzFormatFSF`, `zzFormatFSFC` — Format filesystem
- `zzReadDir`, `zzGetDirEntry`, `zzFreeDir` — Directory operations
- `zzReadPhySec`, `zzWritePhySec` — Physical sector read/write
- `zzPackFsys`, `zzFixFsys` — Pack/fix filesystem
- `zzBackup`, `zzRestore` — Partition backup/restore
- `zzRelocateFile`, `zzCompFile`, `zzDecompFile` — File compression/relocation

**Data compression:**
- `zzCompress`, `zzUncompress`, `zzUncompressRemove` — LZRW3-A compression
- `zzDpack`, `zzDunpack` — Data packing/unpacking

**CRC/checksum:**
- `zzInicrc`, `zzUpdcrc`, `zzUpdblkcrc`, `zzCrcFile`, `zzCrcCheckFile` — CRC calculation

**Diagnostics:**
- `zzMsgTest` — Message test
- `zzErrHandler`, `zzErrno`, `zzWSAErrno` — Error handling
- `zzFlushIn`, `zzFlushOut` — I/O buffer flush
- `zzResync` — Communication resynchronization
- `zzDuplCheck`, `zzDuplCmp`, `zzDuplCopy`, `zzDuplPartition` — Duplication management

**Network:**
- `zzGetHWAddressByIP` — Hardware address lookup by IP
- `zzSetEthGateway` — Set Ethernet gateway
- `zzNTtelnet` — Built-in telnet client
- `zzLoadIoUnit` — Load I/O unit
- `zzGetGrpMembers` — Get group members
- `zzRenamePnetDevice`, `zzRenumPfbSlave` — Device configuration
- `zzDrvOnOff` — Driver on/off
- `zzShutDown` — Shutdown
- `zzRefWatch` — Reference watch
- `zzTestFileServer` — Test file server

### 3.2 `dc*` Functions — DNA Type System (~90 functions)

The `dc` (DNA Class/Collection) system is the type framework for Valmet DNA data structures:
- `dcCreate`, `dcInit`, `dcInitColl`, `dcDeleteColl` — Type lifecycle
- `dcAdd*` / `dcGet*` / `dcPut*` — Member/type manipulation
- `dcSearch`, `dcLink`, `dcReloc`, `dcRelocate` — Type resolution
- `dcGetDim`, `dcGetDim32`, `dcCheckDim`, `dcCheckDim32` — Array dimensions
- `dcGetClass`, `dcGetType`, `dcGetVersion` — Type metadata
- `dcGetName`, `dcGetRole`, `dcGetFlags` — Member properties
- `dcRecaddr`, `dcRecpos`, `dcTbladdr`, `dcTbladdr32` — Record/table addressing
- `dcIsBasic`, `dcIsStruct` — Type classification
- `dc_swap_type` — Endian swapping

Both camelCase (`dcBasicType`) and snake_case (`dc_basictype`) variants exist — legacy C API + newer wrapper API.

### 3.3 Other Internal Symbols

- `LZWdone` — LZW compression cleanup
- `xd_crypt`, `xd_decrypt` — XD (external data) encryption
- `pred_cm`, `putc_cm` — Communication predicates
- `ktyLuokT`, `ktyPalT`, `ktySeurT` — Finnish type names (luokka=class, palvelu=service, seuraaja=follower)

---

## 4. Communication Architecture

### 4.1 Two Transport Modes

BsTool supports two communication transports with DNA nodes:

**RS-232 Serial Line (primary):**
- Selected via `COMMUNICATION_LINE` environment variable (e.g., `AB01`)
- Uses Windows serial port APIs (SetupComm, GetCommState, SetCommState)
- Block-based protocol: `zzSendRsBlk` / `zzRcvRsBlk`
- Serial port speed configurable via `COMMUNICATION_SPEED`
- `@@\\.\` string indicates Windows device namespace (e.g., `\\.\COM1`)

**TCP/IP (secondary/modern):**
- Uses Winsock (WS2_32.dll)
- Block-based protocol: `zzSendTcpBlk` / `zzRcvTcpBlk`
- Secure variant: `zzSendTcpBlkSec` / `zzRcvTcpBlkSec` (encrypted via zzCrIOL.dll)
- XD_IP_ADDR, XD_UDP_PORT, XD_HW_ADDR, XD_HW_TOKEN env vars for NCU2 network config
- UDP port 2517 (default) for NCU2 communication
- Multicast support (IP_MULTICAST_IF, IP_MULTICAST_TTL)

### 4.2 Environment Variables

| Variable | Purpose | Example |
|----------|---------|---------|
| `COMMUNICATION_LINE` | RS-line identifier | `AB01` |
| `COMMUNICATION_TYPES` | Type configuration file | (path) |
| `COMMUNICATION_TIMEOUT` | Operation timeout | (seconds) |
| `COMMUNICATION_PASSWD` | Authentication password | (string) |
| `COMMUNICATION_ID` | Session identifier | (string) |
| `COMMUNICATION_SPEED` | Serial port baud rate | (numeric) |
| `COMMUNICATION_TERMPROG` | Terminal program | `telnet` |
| `BSTOOL_LICENCE` | License key | (string) |
| `BSTOOL_FLOAT_CMP_MASK` | Float comparison mask | (mask) |
| `XD_IP_ADDR` | XD network IP address | `a.b.c.d` |
| `XD_UDP_PORT` | XD UDP port | `2517` |
| `XD_HW_ADDR` | XD hardware address | (hex) |
| `XD_HW_TOKEN` | XD hardware token | `1-50` |
| `XD_NCUS_DEBUG` | NCU2 debug flag | (flag) |

### 4.3 Protocol Structure — Block-Based Communication

From the strings and export analysis, the communication protocol is **block-based**:

1. **Initialization**: `zzInitRsLineIO` or `zzInitTcpLineIO` — open the transport
2. **Handshake**: `zzInit2111` → `zzSend2111` → `zzRcv2111` → `zzAck2111` — protocol negotiation
3. **Command**: `zzSendCmd` / `zzSendRemoteCommand` / `zzSendDbCmd` — send command block
4. **Data**: `zzSendRsBlk` / `zzRcvRsBlk` — block-level data transfer
5. **CRC**: `zzUpdcrc` / `zzUpdblkcrc` — CRC verification per block
6. **Resync**: `zzResync` / `zzFlushIn` / `zzFlushOut` — error recovery

**Message counters** (from strings, line 574-595):
```
MESSAGE COUNTERS
    Total   Corrupted   CRC   Retrans   Timeout   uid   Fatal
```
This indicates the protocol tracks: total messages, corrupted messages, CRC failures, retransmissions, timeouts, unique IDs, and fatal errors.

### 4.4 The `-errlog` Command Pathway

The critical command for LOGReport:

```
BsTool.exe -errlog <server> [cont] [mask <mask>]
```

Internal flow (inferred from exports):
1. Parse `-errlog` command and server name (lid or hw-addr)
2. Strip `m`/`r` suffix from node name (e.g., `AP01m` → `AP01`)
3. Initialize communication (`zzInitRsLineIO` with `COMMUNICATION_LINE=AB01`)
4. Connect to target node via `zzSendCmd` / `zzSendRsBlk`
5. `zzOpenErrLog` — open error log stream from the node
6. `zzGetLog` — retrieve RS log messages
7. Output messages to stdout (Windows-1252/CP1252 encoding)
8. Interactive wait (stdin) — displays results and waits for user input

### 4.5 Encryption and Licensing

- `magic.dll`: `GetMagicNumberEx`, `ReverseMagicNumber`, `GetLicenseKey` — type system encryption/licensing
- `zzCrIOL.dll`: `zzEncryptBuf`, `zzDecryptBuf` — communication buffer encryption
- `dbgchk.lic`: License file checked at startup
- `BSTOOL_LICENCE` env var: Alternative license key
- `xd_crypt` / `xd_decrypt`: External data encryption

---

## 5. Data Formats

### 5.1 DNA File Format

- **cpio archives**: Standard Unix cpio format with DNA extensions (`TRAILER!!!` marker)
- **Module format**: Binary structure with Finnish variable names (from strings):
  - `modtyyppi` (module type), `versio` (version), `modluokka` (module class)
  - `nimiso` (name index), `statso` (status offset), `sijainti` (location)
  - `avainso` (key offset), `suorvali` (execution interval), `modsij` (module position)
  - `suojaus` (protection), `crc`, `aikaleima` (timestamp)
  - `modkoko` (module size), `edellinen` (previous), `seuraava` (next)
  - Data/BSS/Code sections: `kadatalkm`, `likoko`, `takoko`, etc.

### 5.2 Compression

- **LZRW3-A** (Lempel-Ziv-Ross Williams, variant A)
- Public Domain algorithm by Ross N. Williams, Renaissance Software, 15-Jul-1990
- Used for: file compression (`-COMPRESS`/`-UNCOMPRESS`), code packing (`-CODEPACK`/`-CODEUNPACK`), database compression (`-lz`/`-unlz`)

### 5.3 Code Package Format

From strings (lines 1673-1715):
```
bhd.tstart  = 0x%08x   (text start)
bhd.tlimit  = 0x%08x   (text limit)
bhd.dstart  = 0x%08x   (data start)
bhd.dlimit  = 0x%08x   (data limit)
bhd.bstart  = 0x%08x   (BSS start)
bhd.blimit  = 0x%08x   (BSS limit)
xorstamp[0] = 0x%08x   (checksum)
xorstamp[1] = 0x%08x   (checksum)
cstamp[0]   = 0x%08x   (TAG)
cstamp[1]   = 0x%08x   (tstart)
cstamp[2]   = 0x%08x   (csize - compressed size)
cstamp[3]   = 0x%08x   (abs_sz - absolute size)
```

### 5.4 Type System

DNA types (from strings, lines 1324-1353):
- `char`, `int8`, `uns8`, `bool8`, `int16`, `uns16`, `bool16`
- `int32`, `uns32`, `int64`, `uns64`, `float`, `double`, `voidptr`
- `bin`, `ana`, `ints`, `intsev`, `intlev`, `binev`
- Type classes: `DC_FREE`, `DC_SINGLE`, `DC_STRUCT`, `DC_MEMBER`
- Data access: `DC_PTR`, `DC_DATA`
- Roles: `DC_UNDEF`, `DC_INPUT`, `DC_OUTPUT`
- Continuity: `DC_CONTIN`, `DC_BROKEN`

---

## 6. Error Message Catalog

BsTool contains a comprehensive error message catalog (strings lines 1359-1528), covering:
- Module errors (1-22)
- Type errors (22-25)
- Resource errors (26-38)
- Usage errors (39-49)
- System errors (50-55)
- I/O connection errors (56-66)
- Backup server notices/errors (72-120)
- Database notices (151-170)
- Application server messages (151-165)

Key error patterns for `-errlog`:
- `"error: operation fails"` — generic operation failure
- `"error: file error"` — file I/O failure
- `"error: illegal command"` — invalid command syntax
- `"error: out of memory"` — memory allocation failure
- `"error: insufficient priviledge"` — authentication failure
- `"error: can't free directory on backup server"` — directory cleanup failure
- `"error: no TEMP defined"` — temp directory missing
- `"Timeout."` — communication timeout
- `"BS log empty"` — no log messages available
- `"BS lost some log messages"` — log buffer overflow

---

## 7. Full Command Reference (from binary help strings)

### 7.1 Primary Commands (~50)

| Command | Description |
|---------|-------------|
| `-tx` | Transfer file to BU |
| `-txc` | Transfer with compression |
| `-txg` | Transfer to group |
| `-rx` | Receive file from BU |
| `-move` | Transfer dbfile to BU |
| `-cat` | Display file from BU |
| `-ls` | BU directory listing |
| `-rm` | Delete file(s) |
| `-mv` | Rename file |
| `-crc` | File CRC calculation |
| `-crcg` | CRC in multiple BUs |
| `-exec` | Execute script (find -exec style) |
| `-pexec` | Execute for modules in package |
| `-gexec` | Execute for group members |
| `-pextr` | Extract module from package |
| `-piolst` | List I/O module addresses |
| `-connlst` | List module connections |
| `-cmiolst` | List CMIO addresses |
| `-pmodinfo` | Module info (interval, size) |
| `-pgen` | Generate application server package |
| `-cpio` | cpio DNA files |
| `-cp` | Copy DNA file |
| `-cpd` | Copy DNA files to directory |
| `-cpdir` | Copy files recursively |
| `-typechk` | Print type information |
| `-lgmbr` | List group members |
| `-cmd` | Send command to application server (start/stop/reset) |
| `-cnf` | Send configuration command (add/del/swap/updval/accept/reclaim) |
| `-db` | Database tools (put/get/del/list/pack/chk/crc/move/erase/append/lz/unlz/extract) |
| `-err` | Diagnostics control |
| `-rd` | Read disk sectors |
| `-wr` | Write disk sectors |
| `-f` | Format filesystem |
| `-ff` | Format (full) filesystem |
| `-ffc` | Format (full/compressed) |
| `-F` | Format disk |
| **`-errlog`** | **Display RS log messages** |
| `-log` | Display BU log messages |
| `-partition` | Select active partition |
| `-backup` | Backup primary partition |
| `-restore` | Restore primary partition |
| `-mastercopy` | Make master copy |
| `-mastercmp` | Compare master and slave |
| `-backupcmp` | Compare with backup |
| `-check` | Check filesystem |

### 7.2 Extended/Test Commands

`-HELP`, `-COMPRESS`, `-UNCOMPRESS`, `-LZ`, `-UNLZ`, `-COMMTX`, `-MSGTEST`, `-MASTERCOPY`, `-RUNSTATE`, `-FCLOSE`, `-RM`, `-FIXFSYS`, `-PACKFSYS`, `-CODEPACK`, `-CODEUNPACK`, `-NT_TELNET`, `-MODTUL`, `-STATCOM`

### 7.3 Batch Commands

`-buffered`, `-modvers`, `-getval`, `-putval`, `-refval`, `-refvaldiff`, `-cnfval`, `-getmod`, `-getabs`, `-getip`

### 7.4 Network Commands

`-io_reload`, `-gateway`, `-telnet`, `-crypt`, `-decrypt`, `-ncu2cnf`, `-rcmd`, `-macroread`, `-syslog`, `-renum_pfb_slave`, `-makezip`, `-unzip`, `-send_pnet_cmd`, `-rename_pnet_dev`, `-enableMDR`

### 7.5 I/O Redirection & Flags

`-noconn`, `-stdin`, `-stdout`, `-stderr`, `-verbose`, `-usesci`, `-repeat`, `-interval`, `-timeout`, `-date`, `-time`, `-secure`, `-noretries`, `-onebreak`, `-blkcnt`

---

## 8. Existing Go Wrapper Assessment

The LOGReport repo (`/opt/data/LOGReport/internal/bstool/`) already contains a Go wrapper:

### 8.1 What's Implemented

| File | Purpose | Status |
|------|---------|--------|
| `client.go` | Client with functional options, ErrLog method | ✅ Complete |
| `encoding.go` | CP1252 → UTF-8 decoding | ✅ Complete |
| `filter.go` | Status message filtering, message splitting | ✅ Complete |
| `errors.go` | Typed errors (NotFound, Timeout, UnsupportedPlatform, etc.) | ✅ Complete |
| `executor.go` | Executor interface | ✅ Complete |
| `executor_windows.go` | Windows subprocess executor with CREATE_NO_WINDOW | ✅ Complete |
| `executor_linux.go` | Linux stub (returns ErrUnsupportedPlatform) | ✅ Complete |
| `client_test.go` | Unit tests | ✅ Complete |
| `integration_test.go` | Integration tests | ✅ Complete |
| `handlers_bstool_test.go` | API handler tests | ✅ Complete |

### 8.2 What the Go Wrapper Does

The Go wrapper is a **subprocess wrapper** — it executes `BsTool.exe -errlog <server>` as a child process and parses the output. It does NOT reimplement the protocol.

**Flow:**
1. Strip `m`/`r` suffix from server name
2. Set `COMMUNICATION_LINE=AB01` environment variable
3. Execute `BsTool.exe -errlog <server>` via subprocess
4. Wait with context-based timeout (default 15s)
5. Decode stdout from CP1252 to UTF-8
6. Filter status messages ("Writing to", "Content written to", etc.)
7. Split into individual log message lines
8. Return structured `ErrLogResult`

### 8.3 API Endpoint

The handler at `/api/v1/bstool/errlog` accepts:
```json
{
  "server_name": "AP01m",
  "timeout": 15,
  "mask": "ERR"
}
```

Returns:
```json
{
  "server_name": "AP01",
  "messages": ["...", "..."],
  "raw_output": "...",
  "stderr": "...",
  "duration_ms": 10234,
  "exit_code": -1,
  "timed_out": true
}
```

---

## 9. Incorporation Recommendations

### 9.1 Current State: Subprocess Wrapper (Working)

The existing Go wrapper is a solid subprocess wrapper that correctly handles:
- ✅ CLI interface (`-errlog <server>`)
- ✅ Environment setup (`COMMUNICATION_LINE=AB01`)
- ✅ Node name suffix stripping
- ✅ CP1252 encoding
- ✅ Status message filtering
- ✅ Timeout handling with partial output recovery
- ✅ Platform-specific execution (Windows/Linux stub)
- ✅ API endpoint with validation

### 9.2 Short-Term Improvements (Days)

**SSH Remote Execution** — Add a remote executor that runs BsTool.exe on a Windows host via SSH:
- `executor_ssh.go` — SSH-based executor for Linux servers
- Execute `BsTool.exe` on a Windows jump host via SSH command
- Parse stdout/stderr from SSH session
- This bridges the Linux LOGReport server → Windows BsTool.exe gap

**Additional Commands** — Extend beyond `-errlog`:
- `-log` — BU log messages (different from RS error log)
- `-db list` — Database module listing
- `-getip` — Get server IP address
- `-lgmbr` — List group members

**Better Error Mapping** — Map BsTool error strings to structured Go errors:
- `"error: operation fails"` → `ErrOperationFailed`
- `"Timeout."` → `ErrCommunicationTimeout`
- `"BS log empty"` → `ErrLogEmpty`
- `"error: insufficient priviledge"` → `ErrAuthentication`

### 9.3 Medium-Term: Protocol-Level Reimplementation (Weeks-Months)

Based on the binary analysis, a protocol-level Go reimplementation is theoretically possible but requires:

1. **RS-232 serial protocol** — Implement block-based communication using Go serial libraries (`go.bug.st/serial`)
   - Replicate `zzSendRsBlk` / `zzRcvRsBlk` block format
   - Implement CRC calculation (`zzUpdcrc`)
   - Implement "2111" handshake sequence
   
2. **TCP protocol** — Implement TCP block communication
   - Replicate `zzSendTcpBlk` / `zzRcvTcpBlk` block format
   - Implement secure variant if encryption is required
   
3. **Encryption** — Reverse-engineer `zzCrIOL.dll` (zzEncryptBuf/zzDecryptBuf) and `magic.dll`

**Critical blocker**: The exact wire format of the blocks (header structure, CRC algorithm, handshake sequence) is not fully recoverable from strings alone. It would require:
- Serial port sniffing while BsTool runs against a live DNA node
- Disassembly of the `zzSendRsBlk`/`zzRcvRsBlk` functions (requires Ghidra/IDA)
- Or access to Valmet internal documentation

### 9.4 What We Can Extract Now Without Hardware

From the binary analysis, we can implement **without** hardware access:

| Component | Feasibility | Evidence |
|-----------|-------------|---------|
| CLI parsing | ✅ Trivial | Full command reference from strings |
| Environment setup | ✅ Complete | All env vars identified |
| Output parsing | ✅ Complete | CP1252 encoding, filter patterns, error strings |
| Error catalog | ✅ Complete | 170+ error messages extracted |
| Type system names | ✅ Complete | All DNA types and classes identified |
| LZRW3-A compression | ✅ Possible | Public domain algorithm, reference implementation available |
| cpio format | ✅ Standard | Unix cpio with TRAILER!!! marker |
| RS-232 block protocol | ❌ Needs RE | Block format unknown, needs disassembly |
| TCP block protocol | ❌ Needs RE | Block format unknown, needs disassembly |
| "2111" handshake | ❌ Needs RE | Sequence known, message format unknown |
| Encryption | ❌ Needs RE | zzCrIOL.dll and magic.dll are proprietary |

---

## 10. Summary

**BsTool.exe is a 32-bit Windows console application (457KB, VS2013/C) that serves as the Valmet DNA Backup Server operator utility.** It communicates with DNA nodes via RS-232 serial lines or TCP/IP using a block-based protocol with CRC verification, encryption (zzCrIOL.dll), and a "2111" handshake sequence. The binary exports 232 internal functions covering communication (zz*), type system (dc*), and file operations.

**For LOGReport incorporation**, the existing Go subprocess wrapper at `/opt/data/LOGReport/internal/bstool/` is the correct approach. It correctly wraps `BsTool.exe -errlog` with proper encoding, filtering, timeout, and error handling. The key improvement needed is **SSH-based remote execution** so the Linux LOGReport server can trigger BsTool.exe on a Windows host.

**Full protocol reimplementation** is blocked by the unknown wire format of the RS-232/TCP block protocol. The binary analysis reveals the function names and overall architecture, but the actual byte-level protocol requires disassembly (Ghidra/IDA) or hardware-level sniffing.