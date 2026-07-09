# LOGReport Commander Window — Full Application Review

**Date:** 2026-06-25
**Reviewer:** Reviewer subagent (delegated by Orchestrator)
**Scope:** FULL application — Report Window (previously reviewed) + Commander Window (newly implemented)
**Verdict:** **PASS WITH KNOWN ISSUES** — Commander Window is functionally complete. 1 critical pre-existing bug confirmed (RPC parser case sensitivity). Frontend production build has pre-existing TypeScript errors in test files only.

---

## 1. Build & Test Results

### 1.1 Go Backend

| Check | Result | Details |
|-------|--------|---------|
| `go build ./...` | ✅ PASS | Exit 0 — all packages compile |
| `go test ./internal/...` | ✅ PASS | 11/11 packages pass, all tests green |

All new packages build and test successfully:
- `internal/nodesconfig` — ✅
- `internal/telnet` (including session.go) — ✅
- `internal/commandqueue` — ✅
- `internal/logwriter` — ✅
- `internal/api` (including handlers_commander.go, handlers_websocket.go) — ✅

### 1.2 Frontend

| Check | Result | Details |
|-------|--------|---------|
| `npx vitest run` | ✅ PASS | 13 test files, 146 tests pass |
| `npm run build` (tsc + vite) | ❌ FAIL | Pre-existing TypeScript errors in **test files only** (not in production source) |

**Frontend build failure analysis:** The `tsc -b` step fails with `TS2304: Cannot find name 'global'` and `TS6133: unused import` errors in `__tests__/` files and `src/test/setup.ts`. These are **pre-existing issues in the test infrastructure**, not caused by the Commander implementation. The Commander components themselves (`CommanderLayout.tsx`, `NodeTree.tsx`, `TelnetTerminal.tsx`, `BsToolPanel.tsx`, `ScanTab.tsx`, `CommandQueueBar.tsx`, `NodeConfigDialog.tsx`) have **zero TypeScript errors**. The `vite build` step (which transpiles without type-checking) would succeed. This is a pre-existing test config issue (missing `@types/node` or `vitest/globals` in tsconfig).

**Recommendation:** Add `"vitest/globals"` to `types` in `tsconfig.json` or add `@types/node` to devDependencies. Not a release blocker — production code is clean.

---

## 2. Backend Go Package Review

### 2.1 `internal/nodesconfig/loader.go` — ✅ PASS

**Python parity:** Matches `node_manager.py` nodes.json loading.

- `LoadFromFile()` / `LoadFromBytes()` — correctly parses JSON array of `NodeConfig`
- `SaveToFile()` — writes back with `MarshalIndent` (4-space indent, matching original format)
- `BuildTree()` — correctly groups tokens by type (FBC, RPC, LOG, LIS, FTP) in canonical order, sorts tokens within groups
- Non-nil token slice guaranteed (AXON gotcha handled)
- `TreeNode` structure matches spec: root → node → group → token hierarchy

**No issues found.** Test coverage exists in `loader_test.go`.

### 2.2 `internal/telnet/session.go` — ✅ PASS (with notes)

**Python parity:** Matches `telnet_service.py` persistent session + `telnet_client.py` buffer clearing.

- `SessionManager` — thread-safe map of sessions keyed by random hex ID
- `Session` — wraps persistent `Client` with `Output` channel for streaming
- `Connect()` — dials telnet, starts background `readLoop()` goroutine
- `readLoop()` — continuously reads, filters via `FilterOutput()`, pushes to channel
- `SendCommand()` — **implements buffer clearing** (Ctrl+X + Ctrl+Z + drain) ✅
- `Disconnect()` — closes session, signals `Done`, closes `Output` channel
- `CloseAll()` — cleanup for server shutdown
- Mock server included for testing

**Bug #2 (Buffer Clearing) — FIXED:** The `SendCommand()` method at lines 151-177 implements the exact Python buffer clearing sequence:
1. Sends Ctrl+X (`0x18`) with 100ms delay
2. Sends Ctrl+Z (`0x1A`) with 100ms delay
3. Drains pending read data
4. Then sends the actual command

This matches `telnet_client.py:82-89` behavior. ✅

**Bug #3 (System Mode Initialization) — NOT IMPLEMENTED (known):** The session manager does NOT implement `verify_system_mode()` (send `yes\r\n`, Ctrl+Z, `systemmode\r\n` after connect). This is documented in TESTING_SPEC.md as a known gap. The Python code sends this after connecting to handle "someone else is connected" prompts and ensure system mode. **Impact:** On real DNA nodes, the first FBC/RPC command may fail if the node is in application mode or has a conflict prompt. **Recommendation:** Add a `verifySystemMode()` call after `Connect()` in the session manager. Not a blocker for development/testing with mock servers, but **required for real field deployment**.

**Potential issue — double close on concurrent Disconnect:** `Disconnect()` closes `sess.Output` at line 203 or 206. If `Disconnect()` is called twice for the same session (e.g., WebSocket cleanup + explicit REST call), the second `close(sess.Output)` will panic. The session is removed from the map on first call, so the second call returns "not found" error before reaching the close. This is **safe in practice** due to the map delete guard. However, `CloseAll()` does NOT delete from the map before closing channels — if `CloseAll()` runs concurrently with a `Disconnect()` call, there's a theoretical race. Low risk in production (shutdown is sequential).

### 2.3 `internal/commandqueue/queue.go` — ✅ PASS

**Python parity:** Matches `command_queue.py` + `sequential_command_processor.py`.

- `Queue` struct with `sync.Mutex`, state machine (idle → running → paused/done)
- `Add()` / `AddMultiple()` — append commands with pending status
- `Start(executor)` — sequential execution, blocks until done/paused/cancelled
- `Pause()` — sets paused flag, stops after current command
- `Resume()` — clears paused flag, sets state to idle (caller re-calls `Start()`)
- `Cancel()` — marks remaining commands as cancelled
- `Status()` — returns current index, total, state
- `Commands()` — returns copy of all commands
- `Reset()` — clears queue
- `AddBatchFromNodes()` — generates FBC/RPC/LOG commands for all nodes (matches "Print All Nodes")

**Command generation verified:**
- FBC tokens → `telnet.FBCPrint(token)` → `print from fbc io structure {token}0000` ✅
- RPC tokens → `telnet.RPCPrint(token)` → `print from fbc rupi counters {token}0000` ✅
- LOG tokens → `print from log structure {token}0000` (reasonable, though Python uses file access not telnet for LOG)
- LIS/FTP tokens → skipped (correct — these are FTP, not telnet)

**Note on Resume:** `Resume()` sets state to `QueueIdle` but does NOT auto-restart `Start()`. The caller (API handler) must call `Start()` again. The frontend `CommandQueueBar` sends a `resume` POST which calls `Resume()` but does NOT call `Start()`. **This means resume doesn't actually continue execution** — it just unpauses the flag but nobody calls `Start()` again. **This is a bug.** The `handleQueueResume` handler should also call `Start()` after `Resume()`.

**Issue — Resume doesn't restart execution:**
- `handlers_commander.go:327-329`: `handleQueueResume` calls `s.commandQueue.Resume()` but does NOT call `s.commandQueue.Start(executor)`.
- `queue.go:192-197`: `Resume()` only clears `paused` and sets `state = QueueIdle`.
- **Fix needed:** `handleQueueResume` should also kick off `Start()` in a goroutine, same as `handleQueueStart`.

### 2.4 `internal/logwriter/writer.go` — ✅ PASS

**Python parity:** Matches `log_writer.py`.

- `New(logRoot)` — creates LogWriter with root directory
- `WriteOutput()` — appends to `{logRoot}/{nodeName}/{tokenType}_{tokenID}.log`
  - Creates directories with `MkdirAll`
  - Opens in append mode (`O_APPEND|O_CREATE|O_WRONLY`)
  - Prepends timestamp header (RFC3339 UTC)
  - Ensures trailing newline
- `ReadLog()` — reads file content, returns "not found" error for missing files
- `ListLogs()` — lists `.log` files in node directory, sorted by name
- `ClearLog()` — truncates file to 0 bytes
- `LogRoot()` — returns configured root

**File naming:** `{tokenType}_{tokenID}.log` with lowercase token type (e.g., `fbc_162.log`). The Python original uses `{tokenType}_{tokenID}.log` with uppercase. **Minor discrepancy** — the read handler in `handlers_commander.go:441` uppercases the parsed token type, so this is handled correctly in practice.

**No critical issues.** Test coverage exists in `writer_test.go`.

### 2.5 `internal/api/handlers_commander.go` — ✅ PASS (with resume bug noted above)

**Endpoint count:** 17 endpoints implemented, matching the spec:

| # | Method | Path | Handler | Status |
|---|--------|------|---------|--------|
| 1 | GET | `/api/v1/nodesconfig` | `handleGetNodesConfig` | ✅ |
| 2 | POST | `/api/v1/nodesconfig` | `handleSaveNodesConfig` | ✅ |
| 3 | PUT | `/api/v1/nodesconfig/load` | `handleLoadNodesConfig` | ✅ |
| 4 | GET | `/api/v1/nodesconfig/tree` | `handleGetNodesConfigTree` | ✅ |
| 5 | POST | `/api/v1/telnet/connect` | `handleTelnetConnect` | ✅ |
| 6 | POST | `/api/v1/telnet/{sessionID}/command` | `handleTelnetCommand` | ✅ |
| 7 | DELETE | `/api/v1/telnet/{sessionID}` | `handleTelnetDisconnect` | ✅ |
| 8 | GET | `/api/v1/telnet/sessions` | `handleListTelnetSessions` | ✅ |
| 9 | POST | `/api/v1/commandqueue/add` | `handleQueueAdd` | ✅ |
| 10 | POST | `/api/v1/commandqueue/start` | `handleQueueStart` | ✅ |
| 11 | POST | `/api/v1/commandqueue/pause` | `handleQueuePause` | ✅ |
| 12 | POST | `/api/v1/commandqueue/resume` | `handleQueueResume` | ⚠️ (resume bug) |
| 13 | POST | `/api/v1/commandqueue/cancel` | `handleQueueCancel` | ✅ |
| 14 | GET | `/api/v1/commandqueue/status` | `handleQueueStatus` | ✅ |
| 15 | POST | `/api/v1/commandqueue/batch` | `handleQueueBatch` | ✅ |
| 16 | GET/POST | `/api/v1/logs/{nodeName}` | `handleListLogs` / `handleWriteLog` | ✅ |
| 17 | GET | `/api/v1/logs/{nodeName}/{fileName}` | `handleReadLog` | ✅ |
| — | POST | `/api/v1/scan/compare` | `handleScanCompare` | ✅ |

All 17 endpoints + scan compare = 18 total new endpoints registered in `server.go:154-187`.

**Scan compare:** Correctly parses file FBC data, connects to live node, sends FBC print, parses live output, builds cell-by-cell comparison with match/mismatch/file_only/live_only statuses. Color coding handled in frontend.

**Queue executor design note:** The `handleQueueStart` executor (lines 292-305) finds the first active session and sends commands through it. It waits 500ms for output then returns "command sent". This is a simplified approach — the Python original reads until prompt and captures full output. The Go approach relies on the WebSocket streaming output to the frontend, which is architecturally sound for a web app but means the queue's `QueuedCommand.Output` field will just contain "command sent" rather than the actual telnet response. **Not a bug** — output is streamed via WebSocket, not captured in the queue.

### 2.6 `internal/api/handlers_websocket.go` — ✅ PASS

**Python parity:** Replaces Python's direct Qt signal/slot with WebSocket JSON protocol.

**Telnet WebSocket (`/api/v1/telnet/ws`):**
- Client messages: `{action: "connect", host, port}`, `{action: "command", command}`, `{action: "disconnect"}`
- Server messages: `{type: "output", data}`, `{type: "status", connected, session_id}`, `{type: "error", message}`, `{type: "prompt", data}`
- Ping/pong at 30s interval (60s read deadline) ✅
- Output streaming via `streamTelnetOutput()` goroutine reading from `Session.Output` channel ✅
- Prompt detection via `telnet.IsPrompt()` ✅
- Session cleanup on WebSocket disconnect ✅
- Concurrent write safety: `writeTelnetWS()` uses direct `WriteMessage` — **potential race** if `streamTelnetOutput` goroutine and the main read loop both write simultaneously. Gorilla WebSocket requires a mutex for concurrent writes. **This is a bug** — though in practice the read loop only writes on errors/status, and the output goroutine writes output/prompt, so collisions are rare. **Recommendation:** Add a `sync.Mutex` to protect WebSocket writes.

**BsTool WebSocket (`/api/v1/bstool/ws`):**
- Client messages: `{action: "execute", server_name}`
- Server messages: `{type: "output", data}`, `{type: "done", exit_code}`, `{type: "error", message}`
- Ping/pong at 30s interval (120s read deadline) ✅
- Executes `s.bstoolClient.ErrLog()` and streams result ✅
- On Linux, returns `ErrUnsupportedPlatform` (expected — BsTool is Windows-only)

---

## 3. Frontend React Component Review

### 3.1 `CommanderLayout.tsx` — ✅ PASS

**Python parity:** Matches `commander_window.py` split-panel layout.

- Left panel (40% width): `NodeTree` ✅
- Right panel (60% width): Tabbed interface (Telnet | BsTool | Scan) ✅
- Bottom: `CommandQueueBar` ✅
- Header with Config button → `NodeConfigDialog` ✅
- Context menu actions: FBC Print, RPC Print, BsTool ErrLog, Copy to Log ✅
- Node suffix stripping for BsTool: `stripNodeSuffix("AP01m")` → `"AP01"` ✅
- Tab switching on context action ✅
- Pending command propagation to TelnetTerminal ✅

### 3.2 `NodeTree.tsx` — ✅ PASS

**Python parity:** Matches `node_tree_view.py` hierarchical tree.

- Fetches tree from `GET /api/v1/nodesconfig/tree` ✅
- Recursive `TreeBranch` component with expand/collapse ✅
- Node icons: Server (node), Folder/FolderOpen (group), Circle (token) ✅
- Status colors: idle (gray), connected (green), error (red), running (accent), warning (amber) ✅
- Auto-expand root children on first load ✅
- "Load Nodes" button (reload tree) ✅
- "Print All Nodes" button → POST batch + POST start ✅
- Pause/Resume/Cancel buttons (shown when queue active) ✅
- Queue status polling (1s interval when active) ✅
- Context menu (right-click on token): FBC Print, RPC Print, BsTool ErrLog, Copy to Log ✅
- Token selection → passes token_id to parent ✅
- IP address display on node row ✅
- Port/protocol display on token row ✅

**Note:** "Set Log Root" button from the spec is not implemented — log root is hardcoded to `"logs"` in `handlers.go:179`. Not critical — log root can be configured via environment or config in future.

### 3.3 `TelnetTerminal.tsx` — ✅ PASS

**Python parity:** Matches `telnet_tab.py` interactive terminal.

- Connection bar: IP input, Port input, Connect/Disconnect buttons ✅
- Status indicator (green/gray dot) ✅
- Terminal output: monospace `<pre>`, auto-scroll ✅
- Command input + Send button, Enter to execute ✅
- Command history (up/down arrow navigation) ✅
- "Copy to Log" button → POST to log writer ✅
- "Clear Terminal" button ✅
- "Clear Log" button ✅
- WebSocket connection to `/api/v1/telnet/ws` ✅
- Command resolver (client-side): `ps`→`show all`, `fis`→`print_fieldbus {token}0000`, `rc`→`print_fieldbus_rupi_counters {token}0000` ✅
- Pending command from context menu (auto-send when connected) ✅
- Error display ✅

**Command resolver verified:** `resolveCommand("fis", "162")` → `"print_fieldbus 1620000"` (shorthand form, matching `telnet_commands.py`). `resolveCommand("ps")` → `"show all"`. ✅

### 3.4 `BsToolPanel.tsx` — ✅ PASS

**Python parity:** Matches `bstool_tab.py`.

- BsTool path input ✅
- COMMUNICATION_LINE display (default "AB01") ✅
- Server name input + Execute button ✅
- Output display (monospace, read-only) ✅
- "Copy to Log" button ✅
- "Clear Terminal" button ✅
- WebSocket to `/api/v1/bstool/ws` with REST fallback ✅
- Pending server name from context menu ✅

**Note:** BsTool path input is display-only — it doesn't actually set the path on the backend. The backend `bstoolClient` is initialized once with defaults. To change the path, the user would need to restart the server with a different config. The Python original had a file dialog for path selection. **Minor gap** — not a blocker for Linux deployment (BsTool is Windows-only anyway).

### 3.5 `ScanTab.tsx` — ✅ PASS

**Python parity:** Matches `node_scan_widget.py` comparison tables.

- Per-node subtabs (one tab per node) ✅
- File data textarea (paste FBC file data) ✅
- "Compare with Live" button → POST `/api/v1/scan/compare` ✅
- Auto-refresh dropdown: Off, 5s, 10s, 30s, 60s, 300s ✅
- Countdown timer display ✅
- FBC comparison table with color coding:
  - match=green, mismatch=red, file_only=blue, live_only=amber ✅
- Cell selection → detail view (file value vs live value) ✅
- Summary stats: Total, Match, Mismatch, File Only, Live Only ✅
- Finds first FBC token for the selected node ✅

**Note:** The Python original had separate FBC and RPC tables. The Go version only implements FBC comparison. RPC comparison is not implemented in the scan endpoint (it only does FBC print + ParseFBC). **Minor gap** — FBC comparison is the primary use case. RPC comparison can be added later.

### 3.6 `CommandQueueBar.tsx` — ✅ PASS

**Python parity:** Matches command queue controls from `commander_window.py`.

- Progress display: "Command X/Y: FBC Print AP01m token 162..." ✅
- Progress bar (percentage) ✅
- State indicator: running (green), paused (amber), done/idle (gray) ✅
- Start/Pause/Resume/Cancel buttons (context-appropriate) ✅
- 1s polling for status ✅
- External status prop support (from NodeTree) ✅
- Hidden when no queue activity ✅

### 3.7 `NodeConfigDialog.tsx` — ✅ PASS (bonus)

**Python parity:** Matches `node_config_dialog.py` basic functionality.

- Modal dialog with node list ✅
- Add/Remove nodes ✅
- Per-node: name, IP address, token list ✅
- Per-token: token_id, token_type (FBC/RPC/LOG/LIS/FTP), port, protocol ✅
- Add/Remove tokens ✅
- Save → POST `/api/v1/nodesconfig` ✅
- Load → GET `/api/v1/nodesconfig` (on dialog open) ✅

**Note:** "Load SysFile" and "Create Files" features from the Python original are not implemented. These are secondary features. Not a blocker.

---

## 4. Critical Bugs from TESTING_SPEC.md

### Bug #1: RPC Parser Case Sensitivity — ❌ CONFIRMED BUG (pre-existing)

**File:** `internal/parser/rpc.go:100` and `internal/parser/fbc.go:20`

**Issue:** The `ParseRPC()` function reuses the FBC `headerPattern` regex:
```go
headerPattern = regexp.MustCompile(`^\s*(PIC|IBC)\s+(.+?)\s*sum\s*$`)
```

This pattern requires **uppercase** `PIC` or `IBC`. Real DNA RPC output has **lowercase** `pic`:
```
FBC agent 363
pic  IREX ERROR  POLL ERROR  RESP FAIL  IREX COUNT  TIMEOUT
0    0  0  0  0  0
```

The Python parser has a separate case-insensitive pattern:
```python
RPC_HEADER_PATTERN = re.compile(r'pic\s+IREX ERROR\s+POLL ERROR...')
```

**Impact:** `ParseRPC()` will return `"rpc parser: no PIC/IBC header found in output"` when fed real DNA RPC output with lowercase `pic`. **This WILL fail on real DNA nodes.**

**Test verification:** All existing RPC tests in `rpc_test.go` use uppercase `PIC`/`IBC` in their fixtures — the bug is not caught by tests. The `regression_rpc_test.go` file also does not test lowercase `pic`.

**Fix:** Add a case-insensitive RPC-specific header pattern:
```go
var rpcHeaderPattern = regexp.MustCompile(`(?i)^\s*(PIC|IBC)\s+(.+?)\s*sum\s*$`)
```
Or add `(?i)` flag to the existing pattern (but this would affect FBC parser too, which may not be desired). Best approach: create a separate `rpcHeaderPattern` in `rpc.go` and use it instead of the shared `headerPattern`.

**Severity:** CRITICAL for field deployment. Does not affect development/testing with uppercase fixtures.

### Bug #2: Buffer Clearing in SessionManager — ✅ FIXED

**File:** `internal/telnet/session.go:151-177`

The `SendCommand()` method now implements buffer clearing before each command:
1. Sends Ctrl+X (`0x18`) with 100ms delay
2. Sends Ctrl+Z (`0x1A`) with 100ms delay
3. Drains pending read data
4. Then sends the actual command

This matches the Python `telnet_client.py:82-89` behavior. ✅

### Bug #3: System Mode Initialization — ❌ NOT IMPLEMENTED (known)

**File:** `internal/telnet/session.go`

The `Connect()` method does NOT call `verify_system_mode()` after connecting. The Python code sends:
1. `yes\r\n` (to handle "someone else is connected" prompts)
2. Ctrl+Z (`\x1a`) to clear terminal
3. `systemmode\r\n` to switch to system mode

**Impact:** On real DNA nodes:
- If another debugger session is active, the "someone else is connected" prompt will not be answered → connection may hang
- If the node is in application mode, FBC/RPC commands will be rejected

**Severity:** HIGH for field deployment. Not a blocker for development/testing with mock servers that don't simulate these prompts.

**Fix:** Add a `verifySystemMode()` method to `Session` and call it after `Dial()` in `Connect()`:
```go
func (s *Session) verifySystemMode() error {
    s.Client.SendCommand("yes")
    time.Sleep(200 * time.Millisecond)
    s.Client.conn.Write([]byte{0x1A}) // Ctrl+Z
    time.Sleep(200 * time.Millisecond)
    return s.Client.SendCommand("systemmode")
}
```

---

## 5. Integration Verification

### 5.1 Route Registration — ✅ PASS

All 18 new endpoints registered in `server.go:154-187`:
- 4 nodesconfig routes
- 4 telnet session routes + 2 WebSocket routes
- 7 commandqueue routes
- 3 log routes
- 1 scan compare route

### 5.2 Server Struct — ✅ PASS

`handlers.go:158-166` — Server struct includes:
- `telnetSM *telnet.SessionManager` — initialized in `NewServer()` at line 177
- `commandQueue *commandqueue.Queue` — initialized in `NewServer()` at line 178
- `logRootDir string` — initialized to `"logs"` at line 179

### 5.3 Frontend Routes — ✅ PASS

- `App.tsx:10` — imports `CommanderLayout`
- `App.tsx:81` — route `<Route path="/commander" element={<CommanderLayout />} />`
- `Layout.tsx:81-85` — Commander NavLink in sidebar

### 5.4 TypeScript Types — ✅ PASS

`types/api.ts` includes all Commander types:
- `NodeConfig`, `Token`, `TreeNodeData`
- `NodesConfigResponse`, `NodesConfigTreeResponse`
- `TelnetWSMessage`, `TelnetWSResponse`
- `BsToolWSMessage`, `BsToolWSResponse`
- `QueueStatusResponse`
- `ScanCompareRequest`, `ComparisonCell`, `ScanCompareResponse`

### 5.5 Report Window Regression — ✅ PASS (no regressions)

- All 12 original Report Window endpoints still registered (lines 127-152)
- All existing Go tests pass (11/11 packages)
- All existing frontend tests pass (146/146 tests)
- Report Window components unchanged (`ReportConfig.tsx`, `ReportList.tsx`, `ReportDetail.tsx`, etc.)
- No imports or dependencies broken

---

## 6. Additional Issues Found

### 6.1 Queue Resume Bug — ⚠️ MEDIUM

**File:** `internal/api/handlers_commander.go:327-329`

`handleQueueResume` calls `s.commandQueue.Resume()` which only clears the `paused` flag and sets state to `QueueIdle`. It does NOT restart `Start()`. The queue will remain idle until someone calls `Start()` again.

**Fix:** Add executor call after resume:
```go
func (s *Server) handleQueueResume(w http.ResponseWriter, r *http.Request) {
    s.commandQueue.Resume()
    // Re-start execution
    go func() {
        executor := func(cmd commandqueue.QueuedCommand) (string, error) {
            // same executor as handleQueueStart
        }
        s.commandQueue.Start(executor)
    }()
    writeJSON(w, http.StatusOK, map[string]interface{}{"resumed": true})
}
```

### 6.2 WebSocket Concurrent Write Race — ⚠️ LOW

**File:** `internal/api/handlers_websocket.go:192-199`

`writeTelnetWS()` writes to the WebSocket connection without a mutex. The `streamTelnetOutput` goroutine and the main read loop can both call `writeTelnetWS()` concurrently. Gorilla WebSocket requires a mutex for concurrent writes.

**Fix:** Add a `sync.Mutex` to protect WebSocket writes, or use a channel-based write pump.

### 6.3 LOG Token Command — ℹ️ INFO

**File:** `internal/commandqueue/queue.go:250`

The LOG token command is `print from log structure {token}0000`. The Python original uses file access (not telnet) for LOG tokens — it opens log files directly rather than sending a telnet command. The Go implementation sends a telnet command which may not be a valid DNA debugger command. **Low impact** — LOG tokens are less common and the command will simply return "Unknown command" from the DNA node.

### 6.4 Token ID Normalization — ℹ️ INFO (pre-existing)

**File:** `internal/telnet/commands.go:8`

`FBCPrint("5")` produces `print from fbc io structure 50000` instead of `print from fbc io structure 0050000` (Python uses `zfill(3)`). For tokens with <3 digits, this may cause issues on real DNA nodes. Not a blocker — most field tokens are already 3 characters.

---

## 7. Summary

### Verdict: PASS WITH KNOWN ISSUES

The Commander Window implementation is **functionally complete** and covers all major features from the original Python application:

- ✅ Node tree from nodes.json (hierarchical)
- ✅ Interactive telnet terminal (WebSocket-based)
- ✅ BsTool panel (WebSocket + REST)
- ✅ Scan tab with FBC comparison + auto-refresh
- ✅ Command queue with sequential execution, pause/cancel
- ✅ "Print All Nodes" batch execution
- ✅ Log file writing (per-node)
- ✅ Context menu (right-click → FBC/RPC/BsTool)
- ✅ Node config dialog (add/edit/remove)
- ✅ All 18 new API endpoints
- ✅ No Report Window regressions

### Issues to Fix Before Field Deployment

| Priority | Issue | File | Fix |
|----------|-------|------|-----|
| **CRITICAL** | RPC parser case sensitivity | `parser/rpc.go:100` | Add case-insensitive `rpcHeaderPattern` |
| **HIGH** | System mode initialization | `telnet/session.go` | Add `verifySystemMode()` after connect |
| **MEDIUM** | Queue resume doesn't restart | `handlers_commander.go:327` | Call `Start()` after `Resume()` |
| **LOW** | WebSocket concurrent write race | `handlers_websocket.go:192` | Add write mutex |
| **LOW** | Frontend build (test TS errors) | `tsconfig.json` | Add `vitest/globals` to types |

### Issues That Can Wait

- LOG token command (uses telnet instead of file access — minor)
- Token ID normalization (no `zfill(3)` — most tokens are 3 chars)
- BsTool path input (display-only, no backend connection)
- RPC comparison in scan tab (only FBC comparison implemented)
- "Set Log Root" button (log root is hardcoded)
- "Load SysFile" in NodeConfigDialog (not implemented)

---

**Review complete.** The Commander Window is a solid implementation that faithfully reproduces the Python application's functionality in Go/React. The critical RPC parser bug is pre-existing (not introduced by the Commander implementation) but must be fixed before real DNA node deployment. The system mode initialization gap is the most significant new-code issue for field use.