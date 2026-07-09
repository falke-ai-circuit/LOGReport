# LOGReport Commander Window — Valmet DNA Testing Specification

**Date:** 2026-06-25
**Author:** Valmet (DNA domain specialist)
**Scope:** Testing the Commander window features being added to the Go/React LOGReport refactor

---

## 1. Valmet DNA Domain Primer for Testers

### 1.1 What is a DNA Node?

A Valmet DNA node is an industrial automation controller running on a ship or industrial plant. The nodes referenced in this project are from Costa Favolosa and Costa Fascinosa cruise ships. Each node is a physical controller accessible via TCP/telnet on the vessel's control network.

**Node naming convention:**
- `AP01m` — Application Processor 01, main (m = main/master)
- `AP01r` — Application Processor 01, redundant (r = redundant/backup)
- `AL01` — Alarm Logger 01
- `AP02m`, `AP03m` — more AP nodes
- The `m`/`r` suffix matters: BsTool.exe strips it (AP01m → AP01), but telnet uses the full name for display

### 1.2 What is a Token?

A "token" in DNA terminology is a logical communication endpoint on a node. Each node has multiple tokens, each identified by a 3-character token ID. Token types:

| Type | Full Name | Purpose | Protocol |
|------|-----------|---------|----------|
| **FBC** | FieldBus Controller | I/O module configuration — which I/O cards are in which slots | telnet |
| **RPC** | RUPI Counters | Communication error counters between fieldbus agents | telnet |
| **LOG** | Log access | Access to node's log files | telnet |
| **LIS** | Local Information Server | Ship information system data | FTP (port 2121) |
| **FTP** | File Transfer | Direct file access to node filesystem | FTP (port 2121) |

**Token ID format:** 3 characters, can be numeric (`162`, `363`) or hex-like (`1a2`, `1af`, `18f`). The token ID is appended with `0000` to form the full agent address in DNA commands: `162` → `1620000`.

### 1.3 The DNA Debugger

The DNA debugger is a telnet-accessible command interface running on each node. When you telnet to a DNA node, you get the debugger prompt — a distinctive format:

```
<token_id><single_letter>%<space>
```

Examples: `162a% `, `1a2b% `, `999z% `

The number part is the token ID of the session you're connected to. The letter is a session identifier (a-z). The prompt always ends with `% ` (percent + space).

**CRITICAL:** The prompt regex must match `<digits><letter>%<optional_whitespace>` at end-of-line. The Go prompt patterns are:
```
\n\d+[a-z]%\s*$    — prompt after newline
^\d+[a-z]%\s*$     — prompt at very beginning
\r\n\d+[a-z]%\s*$  — prompt after CR+LF
```

### 1.4 System Mode vs Application Mode

DNA nodes have two modes:
- **System mode** (`%s` prompt suffix) — for diagnostic commands like FBC/RPC print
- **Application mode** (`%a` prompt suffix) — normal operation

The Python code sends `systemmode\r\n` after connecting to ensure system mode is active. The `verify_system_mode()` method does:
1. Send `yes\r\n` (to handle "someone else is connected" prompts)
2. Send Ctrl+Z (`\x1a`) to clear terminal
3. Send `systemmode\r\n` to switch to system mode

**GOTCHA for testing:** The Go client currently does NOT implement `verify_system_mode()`. Tests for the session manager MUST account for this initialization sequence. A mock DNA server should expect and respond to these commands during connection setup.

---

## 2. Exact DNA Debugger Command Sequences

### 2.1 Full Command Reference

All commands are sent as ASCII text terminated with `\r\n` (CRLF).

| Shorthand | Full Command | Purpose |
|-----------|-------------|---------|
| `ps` | `show all` | Show all processes/status on the node |
| `fis` | `print_fieldbus {token}0000` | Print FBC I/O structure (shorthand version) |
| `rc` | `print_fieldbus_rupi_counters {token}0000` | Print RPC counters (shorthand version) |
| — | `print from fbc io structure {token}0000` | Print FBC I/O structure (full version) |
| — | `clear fbc io structure {token}0000` | Clear FBC I/O structure |
| — | `print from fbc rupi counters {token}0000` | Print RPC counters (full version) |
| — | `clear fbc rupi counters {token}0000` | Clear RPC counters |
| — | `systemmode` | Switch to system mode |

**IMPORTANT discrepancy:** The Go `commands.go` has TWO different command formats:
- `FBCPrint(token)` → `print from fbc io structure {token}0000` (full form)
- `CommandResolver["fis"](token)` → `print_fieldbus {token}0000` (shorthand form)

These are BOTH valid DNA commands. The full form (`print from fbc io structure`) is used in the FBC/RPC command services and the sequential processor. The shorthand form (`print_fieldbus`) is used in the interactive telnet tab when the user types `fis`. **Tests must verify both forms produce correct output.**

### 2.2 Command Sequences for Test Scenarios

#### Scenario A: Connect and Show All
```
Client connects to 192.168.1.101:23
[server sends banner]
Client sends: "show all\r\n"
[server responds with process list + prompt]
```

#### Scenario B: FBC Print (token 162)
```
Client sends: "print from fbc io structure 1620000\r\n"
[server responds with FBC table + prompt]
```

#### Scenario C: RPC Print (token 363)
```
Client sends: "print from fbc rupi counters 3630000\r\n"
[server responds with RPC counter table + prompt]
```

#### Scenario D: System Mode Initialization (CRITICAL)
```
Client connects
[server sends banner + possibly "someone else is connected" prompt]
Client sends: "yes\r\n"
Client sends: \x1a (Ctrl+Z, ASCII 26)
Client sends: "systemmode\r\n"
[server now in system mode, prompt has %s suffix]
Client sends: "print from fbc io structure 1620000\r\n"
[server responds with FBC data]
```

#### Scenario E: Print All Nodes (batch)
```
For each node in nodes.json:
  For each FBC token:
    send "print from fbc io structure {token_id}0000\r\n"
    read response until prompt
    write to log file {log_root}/{node_name}/FBC_{token_id}.log
  For each RPC token:
    send "print from fbc rupi counters {token_id}0000\r\n"
    read response until prompt
    write to log file {log_root}/{node_name}/RPC_{token_id}.log
  For each LOG token:
    open log file (no telnet command — just file access)
```

### 2.3 Pre-Command Buffer Clearing

**GOTCHA:** The Python telnet client clears the input buffer BEFORE every command:
```python
self.connection.read_very_eager()    # drain pending data
self.connection.write(b'\x18')       # Ctrl+X
time.sleep(0.1)
self.connection.write(b'\x1A')       # Ctrl+Z
time.sleep(0.1)
cleared = self.connection.read_very_eager()  # drain clearing artifacts
```

The Go client does NOT do this. This is a potential source of test failures if the mock server sends unexpected data between commands. Tests should verify that:
1. The Go session manager (when implemented) clears the buffer before sending commands
2. Or, the mock server does not send unsolicited data between commands

---

## 3. Expected Prompt/Response Patterns

### 3.1 FBC Response Format

The FBC (FieldBus Configuration) response shows the I/O module layout for a fieldbus agent:

```
FBC agent 162
PIC  5  6  7  8  sum
0    AI8  BI8  BO8      3
1    AO4  DI16 DO16     3
2    Not Exists
3    TI6               1
Total sum: 7 I/O-units, 48 Channels (32 input, 16 output)
162a%
```

**Format details:**
- `FBC agent {token_id}` — header line identifying the agent
- `PIC` or `IBC` — header type (PIC = standard, IBC = alternate format)
- Column numbers (5, 6, 7, 8...) — physical card slot positions
- `sum` — total I/O units in that row
- Row data: position number, then I/O unit codes, then sum
- **Empty slots:** detected by 4+ consecutive spaces (no card in slot)
- **"Not Exists":** the entire PIC row is not populated — must be displayed as N/E
- **I/O unit codes:** `AI8`, `AO4`, `AO8`, `DI16`, `DO16`, `BI8`, `BI8N`, `BO8`, `TI6`, `TO6`, `PI4`, `PO4`, `SI8`, `SO8`, `CI4`, `CO4`, `RI4`, `RO4`, `II4`, `IO4`
- **N suffix:** `BI8N` means Binary Input 8-channel with N variant (different hardware revision)
- `Total sum:` footer with I/O unit count, channel count, input/output breakdown
- Response ends with DNA prompt: `162a% `

### 3.2 RPC Response Format

The RPC (RUPI Counters) response shows communication error counters:

```
FBC agent 363
pic  IREX ERROR  POLL ERROR  RESP FAIL  IREX COUNT  TIMEOUT
0    0  0  0  0  0
1    0  2  0  145  0
2    0  0  0  0  0
Unknown command: 0
363b%
```

**Format details:**
- `FBC agent {token_id}` — same header as FBC (RPC is a subcommand of FBC)
- Fixed header: `pic  IREX ERROR  POLL ERROR  RESP FAIL  IREX COUNT  TIMEOUT`
- Row data: position, then 5 counter values
- `Unknown command: N` — footer showing count of unrecognized commands
- Response ends with DNA prompt

**GOTCHA:** The RPC parser in Go (`rpc.go`) uses the FBC `headerPattern` (PIC/IBC) to find the header line, but the actual RPC header is `pic  IREX ERROR  POLL ERROR...` which starts with lowercase `pic`. The regex `(PIC|IBC)` is case-sensitive. **This is a potential bug — verify that the RPC parser can actually find the header in real RPC output.** The Python parser has a separate `RPC_HEADER_PATTERN = re.compile(r'pic\s+IREX ERROR...')` (case-insensitive lowercase). The Go parser reuses the FBC pattern which expects uppercase `PIC` — this will FAIL on real RPC output.

### 3.3 Show All Response Format

```
Process list:
  PID  NAME              STATUS    CPU
  1    system            running   2%
  2    application       running   15%
  3    fieldbus          running   8%
  4    alarm             running   3%
162a%
```

The `show all` command returns a process/status list. Format varies by node type.

### 3.4 DNA Prompt Detection

The prompt regex patterns (from Go `client.go`):
```go
\n\d+[a-z]%\s*$     // "...\n162a% " or "...\n162a%"
^\d+[a-z]%\s*$      // "162a% " at start of response
\r\n\d+[a-z]%\s*$   // "...\r\n162a% "
```

**Test cases for prompt detection:**
| Input | IsPrompt? | Notes |
|-------|-----------|-------|
| `"data\n162a% "` | true | standard case |
| `"162a% "` | true | prompt only |
| `"data\r\n162a% "` | true | CRLF variant |
| `"162a%"` | true | no trailing space (`\s*` allows zero) |
| `"data\n999z%  "` | true | multiple trailing spaces |
| `"no prompt here"` | false | no prompt |
| `"162a% data"` | false | prompt not at end |
| `"data\n1a2b% \nmore"` | false | prompt not at end (text follows) |

---

## 4. BsTool.exe Testing Approach

### 4.1 What BsTool.exe Does

BsTool.exe is a Windows-only proprietary Valmet tool that extracts error logs (RS logs) from DNA system nodes. It is executed as a subprocess:

```
BsTool.exe -errlog AP01
```

**Environment variable:** `COMMUNICATION_LINE=AB01` (default) — specifies the communication line/segment to query.

**Node name stripping:** BsTool receives the stripped node name (without `m`/`r` suffix):
- `AP01m` → `AP01`
- `BP01r` → `BP01`
- `AP01` → `AP01` (unchanged)

**Output format:** BsTool produces CP1252-encoded text (Windows-1252) with:
1. Status messages: `Writing to RS log for AP01...`, `Content written to output file`, `Now the future log is ready`, lines starting with ✔ or ✓
2. Actual RS log messages: `2024-03-15 08:12:34.567 [ERR] Module M01: Channel 3 overrange`
3. The output may contain Windows-1252 characters: ° (0xB0), ± (0xB1), µ (0xB5), Ø (0xD8), € (0x80)

The Go `filter.go` filters status messages and splits remaining lines into individual log messages.

### 4.2 Testing BsTool on Linux (Windows-only tool)

Since BsTool.exe cannot run on Linux, the testing strategy is:

#### 4.2.1 Unit Tests (Linux-safe)
Test the Go BsTool client logic WITHOUT executing BsTool.exe:

- **`stripNodeSuffix()`**: verify `AP01m` → `AP01`, `BP01r` → `BP01`, `AP01` → `AP01`
- **`filterStatusMessages()`**: verify status lines are filtered, real messages are kept
- **`splitMessages()`**: verify output is split into individual messages correctly
- **`decodeWindows1252()`**: verify CP1252 byte sequences decode to correct UTF-8
- **Error types**: verify `ErrUnsupportedPlatform`, `ErrNotFound`, `ErrTimeout`, `ErrExecution`, `ErrInvalidServer` all return correct codes and messages
- **Platform check**: verify `ErrLog()` returns `ErrUnsupportedPlatform` on Linux when `skipPlatformCheck=false`

#### 4.2.2 Mock Executor Tests
The Go code has an `executor` interface with `execute(ctx, exePath, args, env)` method. For testing, inject a mock executor:

```go
type mockExecutor struct {
    stdout   []byte
    stderr   []byte
    exitCode int
    err      error
}

func (m *mockExecutor) execute(ctx context.Context, exePath string, args []string, env []string) ([]byte, []byte, int, error) {
    return m.stdout, m.stderr, m.exitCode, m.err
}
```

Test scenarios with mock executor:
- **Success**: mock returns CP1252-encoded output with status + real messages → verify filtered messages
- **Exit code 1**: mock returns exit code 1 → verify `ErrExecution`
- **Timeout**: mock checks context and returns `context.DeadlineExceeded` → verify `ErrTimeout` or partial result with `TimedOut=true`
- **Not found**: mock returns "executable file not found" error → verify `ErrNotFound`
- **Partial output on timeout**: mock returns some stdout before timeout → verify result with `TimedOut=true` and partial messages

**To inject the mock:** The `Client.exec` field is unexported. The test must either:
1. Use the `skipPlatformCheck` field (set to true) and inject a mock executor via a test helper
2. Or add a `WithExecutor()` option for test injection (recommended)

#### 4.2.3 Integration Tests (Windows only)
On Windows CI (if available), test with a fake `BsTool.exe` stub:
- Create a batch file that outputs known CP1252 text
- Set it as the BsTool path via `WithPath()`
- Verify full ErrLog flow

### 4.3 BsTool Test Fixtures

#### CP1252 Raw Output Fixture
```go
// Bytes: "Writing to RS log for AP01...\r\n" +
// "2024-03-15 08:12:34.567 [ERR] Module M01: Channel 3 overrange\r\n" +
// "2024-03-15 08:12:35.001 [WRN] Temp: 25°C ± 0.5\r\n" +  // ° = 0xB0, ± = 0xB1
// "Content written to output\r\n" +
// "✔ Done\r\n"
rawOutput := []byte{
    'W','r','i','t','i','n','g',' ','t','o',' ','R','S',' ','l','o','g',' ','f','o','r',' ','A','P','0','1','.','.','.','\r','\n',
    '2','0','2','4','-','0','3','-','1','5',' ','0','8',':','1','2',':','3','4','.','5','6','7',' ','[','E','R','R',']',' ','M','o','d','u','l','e',' ','M','0','1',':',' ','C','h','a','n','n','e','l',' ','3',' ','o','v','e','r','r','a','n','g','e','\r','\n',
    '2','0','2','4','-','0','3','-','1','5',' ','0','8',':','1','2',':','3','5','.','0','0','1',' ','[','W','R','N',']',' ','T','e','m','p',':',' ','2','5',0xB0,'C',' ',0xB1,' ','0','.','5','\r','\n',
    'C','o','n','t','e','n','t',' ','w','r','i','t','t','e','n',' ','t','o',' ','o','u','t','p','u','t','\r','\n',
    0xE2,0x9C,0x94,' ','D','o','n','e','\r','\n',  // ✔ in UTF-8 (BsTool on modern Windows may output UTF-8)
}
```

**Expected filtered messages after decode + filter:**
1. `2024-03-15 08:12:34.567 [ERR] Module M01: Channel 3 overrange`
2. `2024-03-15 08:12:35.001 [WRN] Temp: 25°C ± 0.5`

---

## 5. nodes.json Test Fixtures

### 5.1 Minimal Test Fixture (3 nodes, mixed token types)

```json
[
  {
    "name": "AP01m",
    "ip_address": "192.168.1.11",
    "tokens": [
      {"token_id": "162", "token_type": "FBC", "port": 23, "protocol": "telnet"},
      {"token_id": "163", "token_type": "FBC", "port": 23, "protocol": "telnet"},
      {"token_id": "162", "token_type": "RPC", "port": 23, "protocol": "telnet"},
      {"token_id": "163", "token_type": "RPC", "port": 23, "protocol": "telnet"},
      {"token_id": "162", "token_type": "LOG", "port": 23, "protocol": "telnet"}
    ]
  },
  {
    "name": "AP01r",
    "ip_address": "192.168.1.27",
    "tokens": [
      {"token_id": "362", "token_type": "FBC", "port": 23, "protocol": "telnet"},
      {"token_id": "363", "token_type": "RPC", "port": 23, "protocol": "telnet"}
    ]
  },
  {
    "name": "AL03",
    "ip_address": "192.168.1.13",
    "tokens": [
      {"token_id": "1af", "token_type": "LOG", "port": 23, "protocol": "telnet"},
      {"token_id": "default_lis_token", "token_type": "LIS", "port": 2121, "protocol": "ftp"}
    ]
  }
]
```

### 5.2 Edge Case Fixture

```json
[
  {
    "name": "AP01m",
    "ip_address": "192.168.1.11",
    "tokens": [
      {"token_id": "162", "token_type": "FBC", "port": 2077, "protocol": "telnet"},
      {"token_id": "163", "token_type": "FBC", "port": 5901, "protocol": "telnet"}
    ]
  },
  {
    "name": "NODE_WITH_NO_TOKENS",
    "ip_address": "192.168.1.99",
    "tokens": []
  },
  {
    "name": "HEX_TOKEN_NODE",
    "ip_address": "192.168.1.55",
    "tokens": [
      {"token_id": "1a2", "token_type": "FBC", "port": 23, "protocol": "telnet"},
      {"token_id": "1a3", "token_type": "RPC", "port": 23, "protocol": "telnet"}
    ]
  }
]
```

### 5.3 nodes.json Structure Notes

**Key observations from real field data:**
- Token IDs can be numeric (`162`, `363`) or hex-like (`1a2`, `1af`, `18f`, `20f`)
- The same token ID can appear multiple times for different token types on the same node (e.g., `162` for FBC, RPC, and LOG on AP01m)
- Port is usually 23 (standard telnet) but can be custom (2077, 5901, 2121)
- Protocol is `"telnet"` for FBC/RPC/LOG and `"ftp"` for LIS/FTP
- Some nodes have `default_lis_token` as token ID for LIS type
- The `protocol` field may be absent in some nodes.json versions — the loader should default to `"telnet"`
- Node names with `m`/`r` suffix: AP01m, AP01r, AP02m, AP02r, AP03m, AP03r
- Node names without suffix: AL01, AL02, AL03...AL16
- IP addresses are in 192.168.1.x range (ship control network)

**BuildTree test expectations:**
```
AP01m (node, 192.168.1.11)
├── FBC (group)
│   ├── 162 (token, port 23, telnet)
│   └── 163 (token, port 23, telnet)
├── RPC (group)
│   ├── 162 (token, port 23, telnet)
│   └── 163 (token, port 23, telnet)
└── LOG (group)
    └── 162 (token, port 23, telnet)

AL03 (node, 192.168.1.13)
├── LOG (group)
│   └── 1af (token, port 23, telnet)
└── LIS (group)
    └── default_lis_token (token, port 2121, ftp)
```

---

## 6. E2E Test Scenarios with Mock DNA Server

### 6.1 Mock DNA Server Pattern

The existing test file (`client_test.go`) has a `mockDNAServer` helper. Extend this pattern for Commander tests:

```go
// mockDNAServer starts a TCP listener that mimics a Valmet DNA node.
// The behavior function controls how the server responds.
func mockDNAServer(t *testing.T, behavior func(conn net.Conn)) (addr string, stop func())
```

### 6.2 Scenario: Connect → FBC Print → Parse → Compare

**Mock server behavior:**
```go
func fbcPrintBehavior(conn net.Conn) {
    buf := make([]byte, 4096)
    
    // Send banner with prompt
    conn.Write([]byte("Welcome to Valmet DNA debugger\r\n162a% "))
    
    // Read command
    n, _ := conn.Read(buf)
    cmd := strings.TrimSpace(string(buf[:n]))
    
    if strings.Contains(cmd, "print from fbc io structure 1620000") {
        response := "FBC agent 162\r\n" +
            "PIC  5  6  7  8  sum\r\n" +
            "0    AI8  BI8  BO8      3\r\n" +
            "1    AO4  DI16 DO16     3\r\n" +
            "2    Not Exists\r\n" +
            "3    TI6               1\r\n" +
            "Total sum: 7 I/O-units, 48 Channels (32 input, 16 output)\r\n" +
            "162a% "
        conn.Write([]byte(response))
    } else {
        conn.Write([]byte("Unknown command\r\n162a% "))
    }
}
```

**Test flow:**
1. Start mock DNA server with `fbcPrintBehavior`
2. `telnet.Dial(host, port, timeout)`
3. `client.SendCommand(FBCPrint("162"))`
4. `response, _ = client.ReadUntilPrompt()`
5. `modules, err := parser.ParseFBC(response)`
6. Assert:
   - `len(modules) == 4` (positions 0, 1, 2, 3)
   - `modules[0].Channels` has 3 entries: AI8, BI8, BO8 (position 5, 6, 7)
   - `modules[1].Channels` has 3 entries: AO4, DI16, DO16
   - `modules[2].Exists == false` (Not Exists row)
   - `modules[3].Channels` has 1 entry: TI6 (position 5 only, others empty)
   - `modules[3].Channels[0].Sum == 6`

### 6.3 Scenario: Connect → RPC Print → Parse

**Mock server behavior:**
```go
func rpcPrintBehavior(conn net.Conn) {
    buf := make([]byte, 4096)
    conn.Write([]byte("Welcome to Valmet DNA debugger\r\n363b% "))
    n, _ := conn.Read(buf)
    cmd := strings.TrimSpace(string(buf[:n]))
    
    if strings.Contains(cmd, "print from fbc rupi counters 3630000") {
        response := "FBC agent 363\r\n" +
            "pic  IREX ERROR  POLL ERROR  RESP FAIL  IREX COUNT  TIMEOUT\r\n" +
            "0    0  0  0  0  0\r\n" +
            "1    0  2  0  145  0\r\n" +
            "2    0  0  0  0  0\r\n" +
            "Unknown command: 0\r\n" +
            "363b% "
        conn.Write([]byte(response))
    }
}
```

**Test flow:**
1. Start mock server with `rpcPrintBehavior`
2. `telnet.Dial(...)`, `client.SendCommand(RPCPrint("363"))`
3. `response, _ = client.ReadUntilPrompt()`
4. `modules, err := parser.ParseRPC(response)`
5. Assert:
   - `len(modules) == 3` (positions 0, 1, 2)
   - `modules[1].Counters` has values: IREX_ERROR=0, POLL_ERROR=2, RESP_FAIL=0, IREX_COUNT=145, TIMEOUT=0

**CRITICAL BUG TO TEST:** The Go `rpc.go` parser uses `headerPattern` (which matches uppercase `PIC` or `IBC`) to find the header line. But real RPC output has lowercase `pic  IREX ERROR...`. **This means `ParseRPC()` will FAIL on real RPC output with "no PIC/IBC header found" error.** The test should:
1. First test with uppercase `PIC  IREX ERROR...` (will pass with current code)
2. Then test with lowercase `pic  IREX ERROR...` (will FAIL — this is a known bug)
3. File a bug report: RPC parser needs a case-insensitive header pattern or a separate RPC-specific pattern

### 6.4 Scenario: Persistent Session (WebSocket)

**Mock server behavior for interactive session:**
```go
func interactiveSessionBehavior(conn net.Conn) {
    buf := make([]byte, 4096)
    conn.Write([]byte("162a% "))
    
    for {
        n, err := conn.Read(buf)
        if err != nil {
            return
        }
        cmd := strings.TrimSpace(string(buf[:n]))
        
        // Respond to different commands
        switch {
        case strings.Contains(cmd, "show all"):
            conn.Write([]byte("Process list:\r\n  1 system running\r\n162a% "))
        case strings.Contains(cmd, "print from fbc"):
            conn.Write([]byte("FBC agent 162\r\nPIC  5  6  sum\r\n0    AI8  BI8  2\r\n162a% "))
        case strings.Contains(cmd, "print from fbc rupi"):
            conn.Write([]byte("FBC agent 162\r\npic  IREX ERROR  POLL ERROR  RESP FAIL  IREX COUNT  TIMEOUT\r\n0    0  0  0  0  0\r\n162a% "))
        default:
            conn.Write([]byte("Unknown command\r\n162a% "))
        }
    }
}
```

**Test flow for session manager (when implemented):**
1. Start mock server with `interactiveSessionBehavior`
2. `sm.Connect("session-1", host, port, timeout)`
3. `sm.SendCommand("session-1", "show all")`
4. Read from `session.Output` channel — assert response contains "Process list"
5. `sm.SendCommand("session-1", FBCPrint("162"))`
6. Read from channel — assert response contains "FBC agent 162"
7. `sm.SendCommand("session-1", RPCPrint("162"))`
8. Read from channel — assert response contains "IREX ERROR"
9. `sm.Disconnect("session-1")`
10. Assert session is removed from `sm.ListSessions()`

### 6.5 Scenario: Connection Retry (2 attempts, 10s delay)

**Test:**
1. Start a server that refuses first connection, accepts second
2. Call connect with retry logic
3. Assert: 2 attempts made, second succeeds

**Simplified (no real 10s wait):**
```go
func TestConnectionRetry(t *testing.T) {
    attempts := 0
    behavior := func(conn net.Conn) {
        attempts++
        if attempts == 1 {
            conn.Close() // refuse first
            return
        }
        conn.Write([]byte("162a% "))
        buf := make([]byte, 4096)
        conn.Read(buf)
        conn.Write([]byte("ok\r\n162a% "))
    }
    // ... test retry logic
}
```

### 6.6 Scenario: "Print All Nodes" Batch Execution

**Test setup:**
1. Create a nodes.json fixture with 2 nodes, 3 FBC tokens, 2 RPC tokens
2. Start mock DNA server that responds to FBC/RPC commands
3. Load nodes via `nodesconfig.LoadFromFile()`
4. Build command queue via `queue.AddBatchFromNodes(configs, sessionID, sm)`
5. Start queue execution
6. Assert:
   - 5 commands executed (3 FBC + 2 RPC)
   - Each command has output
   - Log files created at `{log_root}/{node_name}/{token_type}_{token_id}.log`
   - Queue status: current=5, total=5, paused=false

### 6.7 Scenario: FBC Live Comparison (File vs Telnet)

**Test:**
1. Prepare file FBC data (parsed from a .fbc file fixture)
2. Start mock DNA server that returns FBC data with one difference
3. Call scan compare endpoint: `POST /api/v1/scan/compare`
4. Assert comparison result:
   - `matching` count correct
   - `mismatched` cells identified (RED — file had value, live different)
   - `file_only` cells identified (BLUE — file had value, live empty)
   - `live_only` cells identified (AMBER — file empty, live has value)

**Comparison color logic (from Python `fbc_comparison_service.py`):**
- **GREEN (match):** file value == live value (normalized, case-insensitive for text)
- **RED (difference):** file had a value → live is different or missing (actual problem)
- **YELLOW (value_appeared):** file was empty/N/E → live has a value (new data appeared)
- Empty/N/E values: empty string, `N/E`, `N`, `NOT EXISTS`, whitespace

### 6.8 Scenario: Command Queue Pause/Resume/Cancel

**Test:**
1. Queue 5 commands
2. Start execution
3. After command 2 completes, call `Pause()`
4. Assert: queue stops, current=2
5. Call `Resume()`
6. Assert: execution continues from command 3
7. After command 3, call `Cancel()`
8. Assert: remaining commands (4, 5) are cancelled, status shows cancelled

### 6.9 Scenario: Log Writer

**Test:**
1. Create temp directory as log root
2. `lw := logwriter.New(tmpDir)`
3. `lw.WriteOutput("AP01m", "FBC", "162", "FBC agent 162\n...")`
4. Assert file exists at `{tmpDir}/AP01m/FBC_162.log`
5. `content, _ := lw.ReadLog("AP01m", "FBC", "162")`
6. Assert content contains "FBC agent 162"
7. `logs, _ := lw.ListLogs("AP01m")`
8. Assert `len(logs) == 1`

---

## 7. DNA Telnet Protocol Gotchas That Cause Test Failures

### 7.1 CRITICAL: No Buffer Clearing in Go Client

The Python `send_command()` clears the buffer before each command:
```python
self.connection.read_very_eager()
self.connection.write(b'\x18')  # Ctrl+X
self.connection.write(b'\x1A')  # Ctrl+Z
cleared = self.connection.read_very_eager()
```

The Go `SendCommand()` does NOT do this. If a mock server sends data between commands (banner, prompt echo, mode messages), the Go client will read that stale data as part of the next command's response.

**Test implication:** Mock servers should NOT send unsolicited data between commands, OR the session manager must implement buffer clearing.

### 7.2 CRITICAL: System Mode Initialization Not Implemented

The Python `verify_system_mode()` sends `yes\r\n`, Ctrl+Z, `systemmode\r\n` after connecting. The Go client has no equivalent. Real DNA nodes may:
1. Show "someone else is connected, want to connect?" prompt
2. Be in application mode (not system mode) — FBC/RPC commands won't work

**Test implication:** Mock servers should simulate the connection prompt scenario. The session manager must handle it.

### 7.3 CRITICAL: RPC Parser Header Case Sensitivity

The Go `rpc.go` reuses `headerPattern = ^\s*(PIC|IBC)\s+(.+?)\s*sum\s*$` which requires uppercase `PIC`. Real RPC output has lowercase `pic  IREX ERROR  POLL ERROR...`. **This WILL fail on real DNA nodes.**

The Python parser has a separate case-insensitive pattern:
```python
self.RPC_HEADER_PATTERN = re.compile(r'pic\s+IREX ERROR\s+POLL ERROR\s+RESP FAIL\s+IREX COUNT\s+TIMEOUT')
```

**Test implication:** Write a test that feeds real-format RPC output (lowercase `pic`) to `ParseRPC()`. It will fail. File a bug.

### 7.4 Command Echo

The Python `_process_response()` removes the command echo from the response:
```python
clean = response.replace(f"{command}\r\n", "")
```

The Go client does NOT remove the command echo. If the DNA node echoes the command back (which it does), the Go response will start with the command text.

**Test implication:** Mock servers should echo the command. Tests should verify that either:
1. The parser can handle command echo in the response, OR
2. The session manager strips the echo before returning

### 7.5 Prompt Removal

The Python `_process_response()` removes the trailing prompt:
```python
clean = re.sub(r'\d+[a-z]\%\s*$', '', clean).strip()
```

The Go `ReadUntilPrompt()` returns the response INCLUDING the prompt. The caller must strip it.

**Test implication:** Tests should verify that `FilterOutput()` or the parser can handle a trailing prompt in the response. The FBC parser looks for `PIC`/`IBC` header and `Total sum:` footer — it will ignore the prompt line. But other consumers may not.

### 7.6 FilterOutput Whitespace Normalization Destroys Empty Slots

**CRITICAL for FBC parsing:** `FilterOutput()` collapses multiple spaces to single space:
```go
filtered = multiSpacePattern.ReplaceAllString(filtered, " ")
```

This DESTROYS the 4+ space pattern that indicates empty I/O slots. The FBC parser relies on 4+ spaces to detect empty slots. **ParseFBC must be called with RAW (unfiltered) output, NOT filtered output.**

The Go code documents this: "The input is raw telnet output (before FilterOutput whitespace normalization)". **Tests must verify that the pipeline does NOT filter output before passing to ParseFBC.**

### 7.7 "Not Exists" Row Handling

FBC rows can contain "Not Exists" instead of I/O unit codes:
```
2    Not Exists
```

The parser must detect this and create a module with `Exists=false` and no channels. The Go parser handles this via `notExistsPattern`.

**Test case:**
```
0    AI8  BI8  BO8      3
1    Not Exists
2    TI6               1
```
Expected: 3 modules, module[1].Exists=false, module[1].Channels=[] (empty but not nil).

### 7.8 Token ID Normalization

The Python `CommandGenerator.normalize_token_id()` pads numeric tokens to 3 digits: `"5"` → `"005"`, `"162"` → `"162"`. Non-numeric tokens are left as-is: `"1a2"` → `"1a2"`.

The Go `FBCPrint(token)` does NOT normalize — it just appends `0000`: `FBCPrint("5")` → `"print from fbc io structure 50000"` (not `"0050000"`).

**Test implication:** This is a behavioral difference. Tests should verify whether normalization is needed. The Python code uses `zfill(3)` — if the DNA debugger requires 3-digit tokens, the Go code has a bug for short numeric tokens.

### 7.9 ANSI Escape Codes in Response

Real DNA nodes send ANSI escape codes (color, cursor movement) in their responses. The Go `FilterOutput()` handles:
- `\x1b[...m` — color codes
- `\x1b[...K` — clear line
- Control characters (except newline)

But the Python `telnet_filters.py` also handles:
- `~\d+~\d+~` — terminal mode artifacts
- `texitoggleure` — specific artifact string
- Character repeats (`(\w)\1{2,}` → `\1`)
- Empty brackets `[]` and `()`

**Test implication:** Mock servers should include ANSI codes in responses. Tests should verify FilterOutput handles them. Consider adding test cases for the Python-specific artifacts that the Go filter does NOT handle.

### 7.10 "Editor changed to INSERT/REPLACE mode" Messages

The DNA debugger may send mode change messages:
```
Editor changed to INSERT mode
Editor changed to REPLACE mode
```

The Python client detects and removes these. The Go filter does NOT specifically handle them (they would survive as regular text).

**Test implication:** Mock server should send mode change messages. Tests should verify they are either filtered or don't break the parser.

### 7.11 Connection Drops

DNA nodes on ships can drop connections due to:
- Network interference
- Node reboot
- Another user connecting (single-session limit)

The Python client has retry logic (2 attempts, 10s delay). The Go one-shot client has no retry.

**Test implication:** Test connection drop mid-command, verify error handling, verify retry logic in session manager.

### 7.12 Single-Session Conflict Prompts

When connecting to a DNA node that already has a debugger session active, the node sends:
```
someone else is connected, want to connect?
```
or
```
already connected, do you want to connect?
```

The Python `_handle_debugger_prompts()` detects these and auto-responds with `yes\r\n`.

**Test implication:** Mock server should send conflict prompts. Tests should verify the session manager handles them (when implemented).

---

## 8. Test Matrix: Component → Test Cases

### 8.1 Telnet Client (`internal/telnet/`)

| Test | What | Status |
|------|------|--------|
| Dial + SendCommand + ReadUntilPrompt | Basic flow | ✅ exists |
| FBC command → ParseFBC | End-to-end FBC | needs test |
| RPC command → ParseRPC | End-to-end RPC | needs test (will fail on lowercase `pic`) |
| Prompt detection variants | All prompt regexes | ✅ exists |
| FilterOutput | ANSI, control chars, artifacts | ✅ exists |
| Connection drop mid-operation | Partial response | ✅ exists |
| Chunked response | Multi-chunk read | ✅ exists |
| Non-ASCII bytes | Encoding edge cases | ✅ exists |
| Session manager (new) | Persistent session, multi-command | needs implementation + tests |
| Buffer clearing (new) | Pre-command buffer drain | needs implementation + tests |
| System mode init (new) | yes → Ctrl+Z → systemmode | needs implementation + tests |
| Debug conflict prompt (new) | Auto-respond "yes" | needs implementation + tests |

### 8.2 BsTool Client (`internal/bstool/`)

| Test | What | Status |
|------|------|--------|
| NewClient defaults | AB01, 15s, empty path | ✅ exists |
| NewClient with options | Custom path, line, timeout | ✅ exists |
| stripNodeSuffix | m/r stripping | ✅ exists |
| ErrLog empty server | ErrInvalidServer | ✅ exists |
| ErrLog only suffix | ErrInvalidServer | ✅ exists |
| ErrLog Linux unsupported | ErrUnsupportedPlatform | ✅ exists |
| Filter status messages | Writing to, Content written, etc | ✅ exists |
| Filter checkmarks | ✔ ✓ | ✅ exists |
| Real log message not filtered | | ✅ exists |
| Full output filter + split | | ✅ exists |
| CP1252 decode | °, ±, µ, Ø, € | ✅ exists |
| Error codes | All error types | ✅ exists |
| Mock executor success | Full flow with mock | needs test |
| Mock executor timeout | Partial output + TimedOut | needs test |
| Mock executor not found | ErrNotFound | needs test |
| Mock executor exit code | ErrExecution | needs test |

### 8.3 Parsers (`internal/parser/`)

| Test | What | Status |
|------|------|--------|
| ParseFBC standard | PIC header + data rows | needs test |
| ParseFBC with IBC header | Alternate header format | needs test |
| ParseFBC Not Exists row | Exists=false | needs test |
| ParseFBC empty slots | 4+ spaces → no channel | needs test |
| ParseFBC N suffix | BI8N handling | needs test |
| ParseFBC totals | Total sum footer | needs test |
| ParseRPC standard | **WILL FAIL on lowercase `pic`** | needs test + bug fix |
| ParseFBCHeaderType | PIC vs IBC detection | needs test |
| ParseFBCTotals | Footer parsing | needs test |

### 8.4 New Packages (To Be Implemented)

| Package | Test Cases |
|---------|-----------|
| `nodesconfig` | LoadFromFile, LoadFromBytes, SaveToFile, BuildTree (hierarchical), empty tokens, hex token IDs, missing protocol field |
| `telnet/session.go` | Connect, SendCommand (persistent), Disconnect, ListSessions, multiple concurrent sessions, buffer clearing, system mode init, debug conflict prompt |
| `commandqueue` | Add, Start, Pause, Resume, Cancel, Status, AddBatchFromNodes, sequential execution order, failure isolation |
| `logwriter` | WriteOutput, ReadLog, ListLogs, directory creation, append mode, non-existent node |
| `api/handlers_websocket.go` | WebSocket connect/command/disconnect, JSON message format, output streaming, error handling |
| `api/handlers_commander.go` | All new REST endpoints: nodesconfig CRUD, telnet session management, command queue, logs, scan compare |

### 8.5 Integration / E2E

| Test | What |
|------|------|
| Full FBC scan flow | Load nodes.json → connect → FBC print → parse → write log |
| Full RPC scan flow | Load nodes.json → connect → RPC print → parse → write log |
| Print All Nodes | Load nodes → batch queue → sequential execute → verify all logs |
| Live comparison | File FBC vs live FBC → comparison result with color coding |
| Pause/Resume mid-batch | Queue 5 commands → pause after 2 → resume → verify 5 complete |
| Cancel mid-batch | Queue 5 commands → cancel after 2 → verify 3 cancelled |
| WebSocket telnet | Connect via WS → send command → receive streamed output → disconnect |
| BsTool mock | Mock executor → ErrLog → filtered messages → verify CP1252 decode |

---

## 9. Valmet DNA Domain Knowledge Summary for Testers

### 9.1 Key Concepts

1. **DNA nodes are real industrial controllers** on cruise ships — they are not web servers. They speak a custom telnet protocol, not HTTP.

2. **The prompt is the signal.** DNA commands don't have a "done" response. The prompt (`162a% `) appearing at the end of output means the command is complete. This is why prompt detection is critical.

3. **FBC = physical I/O card layout.** The FBC print shows which I/O cards (AI8, DI16, etc.) are plugged into which slots (PIC positions 5, 6, 7, 8...). Empty slots = no card. "Not Exists" = the whole row is unused.

4. **RPC = communication error counters.** The RPC print shows error counts for fieldbus communication. Non-zero values indicate communication problems.

5. **Token IDs are NOT unique per node.** The same token ID (e.g., `162`) can be FBC, RPC, and LOG on the same node. The token TYPE determines what command to send.

6. **BsTool is Windows-only.** It extracts RS logs (Valmet's internal error logs) from the DNA system. On Linux, it cannot run — the Go client correctly returns `ErrUnsupportedPlatform`.

7. **COMMUNICATION_LINE=AB01** is the default communication segment. This is a Valmet DNA network segmentation concept — different segments (AB01, CD02, etc.) connect to different node groups.

8. **The `m`/`r` suffix on node names** indicates main vs redundant controller. BsTool doesn't understand the suffix — it needs the base name (`AP01`). The telnet debugger doesn't care about the suffix.

9. **"Print All Nodes" is the main field workflow.** An engineer connects to the ship's network, loads nodes.json, and clicks "Print All Nodes" to scan every FBC and RPC token on every node. The output is written to log files for offline analysis.

10. **Ship network = 192.168.1.x.** All DNA nodes are on a private ship control network. Tests use localhost (127.0.0.1) with mock servers.

### 9.2 What a Non-Valmet Tester Would Miss

1. **The prompt format is non-obvious.** `<number><letter>%<space>` — the number is the token ID, the letter is a session identifier. A tester might not realize this is the command-completion signal.

2. **Empty I/O slots are indicated by spaces, not by a placeholder.** 4+ consecutive spaces in an FBC row = empty slot. If FilterOutput collapses spaces, the empty slot information is LOST.

3. **"Not Exists" is a valid row state, not an error.** It means the PIC position is not physically populated. The parser must handle it as N/E, not as a parse failure.

4. **The `N` suffix on I/O units** (BI8N, BO8N) is a hardware variant, not a typo. The parser must accept it.

5. **Token ID `0000` suffix.** The DNA command uses `{token_id}0000` — this is the full agent address. Token `162` → agent `1620000`. A tester might think this is a formatting error.

6. **System mode is required for FBC/RPC commands.** Without `systemmode` command, the node may be in application mode and reject diagnostic commands.

7. **The connection conflict prompt.** DNA nodes allow only one debugger session at a time. The "someone else is connected" prompt must be auto-answered with "yes".

8. **CP1252 encoding from BsTool.** Windows-specific characters (°, ±, µ, Ø, €) appear in RS logs. UTF-8 decoding will produce mojibake — CP1252 decoding is required.

9. **The same token ID for different types.** A node can have token `162` as FBC, RPC, and LOG — these are different endpoints that happen to share an ID. The command depends on the TYPE, not just the ID.

10. **`show all` / `ps` is the "are you alive?" command.** It's used to verify the connection is working before sending FBC/RPC commands.

---

## 10. Recommended Test File Structure

```
internal/telnet/
├── client_test.go          # existing — extend with session tests
├── session_test.go         # new — SessionManager tests
├── commands_test.go        # new — command generation edge cases
└── filter_test.go          # new — extended filter tests (mode messages, artifacts)

internal/bstool/
├── client_test.go          # existing — extend with mock executor tests
├── mock_executor_test.go   # new — mock executor injection tests
└── filter_test.go          # new — if not already in client_test.go

internal/parser/
├── fbc_test.go             # new — FBC parser tests with real DNA output
├── rpc_test.go             # new — RPC parser tests (will expose lowercase bug)
└── fixtures/
    ├── fbc_standard.txt    # real FBC output fixture
    ├── fbc_not_exists.txt  # FBC with Not Exists rows
    ├── fbc_empty_slots.txt # FBC with empty slots
    └── rpc_standard.txt    # real RPC output fixture

internal/nodesconfig/
├── loader_test.go          # new — nodes.json loading
└── tree_test.go            # new — BuildTree hierarchical structure

internal/commandqueue/
├── queue_test.go           # new — queue operations
└── batch_test.go           # new — AddBatchFromNodes

internal/logwriter/
└── writer_test.go          # new — log file writing

testdata/
├── nodes_minimal.json      # 3-node fixture
├── nodes_edge_cases.json   # edge case fixture
├── nodes_real.json         # real field data (from source/nodes.json)
└── fbc_sample.txt          # sample FBC output for comparison tests
```

---

**END OF TESTING SPECIFICATION**

This document provides the Valmet DNA domain knowledge and specific testing procedures needed to write meaningful tests for the Commander window features. The tester must understand that DNA nodes are industrial controllers with a custom telnet protocol — standard web/HTTP testing assumptions do not apply.