# LOGReport Scope Gap Analysis — Commander Window Missing

**Date:** 2026-06-25  
**Analyst:** Orchestrator  
**Trigger:** GR15 — "original python gui had report window + commander window, refactor only did report window"

---

## Executive Summary

The original Python LOGReport application had **two major windows**:

1. **Report Window** (`gui.py`) — File selection, format choice (PDF/DOCX), line count, generate button → produces Excel/PDF/DOCX reports from structured logs. **THIS WAS REFACTORED TO GO.** ✅

2. **Commander Window** (`commander_window.py`) — Interactive command center with:
   - Node tree populated from `nodes.json` (hierarchical: node → FBC/RPC/LOG/LIS groups → token leaves)
   - Live telnet session to Valmet DNA debugger (connect, send commands, see output in terminal)
   - BsTool.exe integration (subprocess execution for error log extraction)
   - Scan tab with per-node FBC/RPC table display + live comparison + auto-refresh
   - Command queue with sequential execution, pause/resume/cancel
   - Log file writing (command output → per-node log files)
   - "Print All Nodes" batch execution
   - Context menu (right-click node → FBC print, RPC print, BsTool errlog, etc.)

**The Go refactor explicitly excluded the Commander window.** The architecture blueprint states: "Scope: Report-generation pipeline only (Commander/BsTool excluded)." The functionality transfer map lists 15 components as "OUT OF SCOPE" — all Commander functionality.

**The reviewer passed because the scope was defined incorrectly.** The review verified the report pipeline against a limited scope, not against the full original application.

---

## Detailed Gap Map

### 1. Commander Window — Interactive Command Center (MISSING)

**Python source:** `src/commander/ui/commander_window.py` (686 lines)  
**Go equivalent:** NONE  
**React equivalent:** NONE (current app has Dashboard/Nodes/Reports/SysFile — all report-focused)

The Commander window was a separate QMainWindow opened from the Report window's "Operations → Command Center" menu. It had:

- **Left panel:** Node tree (QTreeWidget)
- **Right panel:** Tab widget with 3 tabs:
  - Telnet Tab (interactive terminal)
  - BsTool Tab (BsTool.exe interface)
  - Scan Tab (per-node FBC/RPC comparison tables)

### 2. Node Tree View (MISSING)

**Python source:** `src/commander/ui/node_tree_view.py` (254 lines)  
**Python presenter:** `src/commander/presenters/node_tree_presenter.py` (1904 lines!)  
**Go equivalent:** NONE (current `NodeBrowser.tsx` is a flat list, not a tree)

**Original functionality:**
- Hierarchical tree: Root nodes (AP01m, AL01) → Token groups (FBC, RPC, LOG, LIS) → Leaf files
- Color-coded status: green (ok), yellow (warning), red (error) — based on content + execution status
- Buttons: "Load Nodes" (file dialog), "Set Log Root" (folder dialog), "Print All Nodes"
- Control: Pause, Resume, Cancel for sequential processing
- Context menu: right-click → FBC print command, RPC print command, BsTool errlog, etc.
- Auto-expand on first load, lazy-loading of children
- Double-click → open log file in associated tab

**nodes.json structure** (original, 20+ nodes):
```json
[
  {
    "name": "AP01m",
    "ip_address": "192.168.1.101",
    "tokens": [
      {"token_id": "162", "token_type": "FBC", "port": 2077, "protocol": "telnet"},
      {"token_id": "163", "token_type": "FBC", "port": 5901, "protocol": "telnet"}
    ]
  }
]
```

### 3. Interactive Telnet Tab (MISSING)

**Python source:** `src/commander/ui/telnet_tab.py` (186 lines)  
**Python service:** `src/commander/services/telnet_service.py` (416 lines)  
**Go equivalent:** `internal/telnet/client.go` exists but is one-shot (dial → send → read → close). No persistent session, no interactive mode.

**Original functionality:**
- IP address + port input fields (defaults: localhost:1234)
- Connect/Disconnect buttons with status indicator (○ disconnected, ● connected)
- Monospace terminal output (Courier New 10pt, read-only QTextEdit)
- Command input field + Execute button (Enter to execute)
- "Copy to Log" — append output to current node's log file
- "Clear Terminal" / "Clear Log" buttons
- Command history navigation (up/down arrows)
- Command resolver: `ps`→`show all`, `fis`→`print_fieldbus {token}0000`, `rc`→`print_fieldbus_rupi_counters {token}0000`
- Auto-reconnect with retry (2 attempts, 5-second delay)
- Connection state persistence (QSettings: telnet_ip, telnet_port)

**Critical for Go/React:** This needs WebSocket support. The current HTTP request/response model cannot support an interactive terminal. The Go backend needs a WebSocket endpoint that maintains a persistent telnet connection and streams output to the React frontend.

### 4. BsTool Tab (MISSING UI — backend partially exists)

**Python source:** `src/commander/ui/bstool_tab.py` (231 lines)  
**Python service:** `src/commander/services/bstool_command_service.py` (690 lines)  
**Go equivalent:** `internal/bstool/client.go` exists (ErrLog, path management, COMMUNICATION_LINE env var) — but no UI.

**Original functionality:**
- BsTool.exe path input (auto-detect from common Windows locations)
- COMMUNICATION_LINE env var display (default: "AB01")
- Command input + Execute button
- Output display (read-only)
- "Copy to Log" / "Clear Terminal" / "Clear Log"
- Connection state indicator
- Sequential execution lock (prevent parallel BsTool runs)
- Node suffix stripping ("AP01m" → "AP01" for BsTool.exe)

**Note:** The Go `internal/bstool/` package already has:
- `Client` with `ErrLog()` method
- `WithCommunicationLine("AB01")` option
- `stripNodeSuffix()` function
- Windows/Linux executor (platform-specific)
- `POST /api/v1/bstool/errlog` endpoint exists

What's missing is the **interactive UI** and the **BsTool command execution from node tree context menu**.

### 5. Scan Tab — FBC/RPC Comparison (MISSING)

**Python source:** `src/commander/ui/node_scan_widget.py` (1006 lines!)  
**Python service:** `src/commander/services/fbc_comparison_service.py` (441 lines)  
**Go equivalent:** NONE (current FBCView/RPCView are read-only display, no live comparison)

**Original functionality:**
- Per-node subtabs (one tab per node in the tree)
- QTableWidget displaying FBC/RPC file content in table format
- **Live comparison:** Compare file FBC data with live telnet FBC scan
  - FbcComparisonService.compare_with_live() — scans via telnet, parses, compares with file
  - Color-coded cells: match=green, mismatch=red, file-only=blue, live-only=amber
- **Auto-refresh timer:** 5/10/30/60/300 second intervals
- Cell selection tracking for detailed comparison view
- Async comparison worker (QRunnable + QThreadPool)
- Countdown timer display

### 6. Command Queue + Sequential Processing (MISSING)

**Python source:** `src/commander/command_queue.py`  
**Python service:** `src/commander/services/sequential_command_processor.py`  
**Go equivalent:** NONE

**Original functionality:**
- Queue commands for sequential execution
- Pause/Resume/Cancel controls
- "Print All Nodes" — batch execute FBC → RPC → LOG for every node in tree
- Hierarchical command execution (node → tokens → commands)
- Output routing: telnet output → telnet tab, BsTool output → BsTool tab
- Progress tracking (current file, success/failure counts)

### 7. Log Writer (MISSING)

**Python source:** `src/commander/log_writer.py` (247 lines)  
**Go equivalent:** NONE

**Original functionality:**
- Write command output to per-node log files
- Log directory structure: `{log_root}/{node_name}/{token_type}_{token_id}.log`
- "Copy to Log" button appends current terminal output to log file
- Log file path tracking per node

### 8. Node Configuration Dialog (MISSING)

**Python source:** `src/node_config_dialog.py` (793 lines)  
**Go equivalent:** NONE

**Original functionality:**
- Add/Remove/Edit nodes
- Token management (add FBC/RPC/LOG/LIS tokens with port + protocol)
- Load from nodes.json, Save to nodes.json
- "Create Files" — generate log file structure for nodes
- "Load Sys File" — parse .sys file and extract node definitions

### 9. Session Management (MISSING)

**Python source:** `src/commander/session_manager.py`  
**Go equivalent:** NONE

**Original functionality:**
- Track active sessions (telnet, BsTool)
- Session type enumeration (telnet, bstool, ftp)
- IP change signaling
- Session state persistence

---

## What Already Exists in Go (Can Be Reused)

| Component | Go File | Status | Reusable for Commander? |
|-----------|---------|--------|------------------------|
| Telnet client | `internal/telnet/client.go` | ✅ One-shot | Needs WebSocket wrapper for interactive mode |
| Telnet commands | `internal/telnet/commands.go` | ✅ Complete | Yes — FBC/RPC print/clear, CommandResolver |
| Telnet filter | `internal/telnet/filter.go` | ✅ Complete | Yes — ANSI strip, control char removal |
| FBC parser | `internal/parser/fbc.go` | ✅ Complete | Yes — parse FBC output from telnet |
| RPC parser | `internal/parser/rpc.go` | ✅ Complete | Yes — parse RPC output |
| SysFile parser | `internal/parser/sysfile.go` | ✅ Complete | Yes — parse .sys files |
| SQLite store | `internal/store/` | ✅ Complete | Yes — nodes, iopoints, modules |
| BsTool client | `internal/bstool/client.go` | ✅ Partial | Yes — ErrLog, path, suffix stripping |
| API server | `internal/api/server.go` | ✅ 12 endpoints | Needs WebSocket + Commander endpoints |
| Node types | `internal/types/node.go` | ✅ Complete | Needs token type expansion |

## What Needs To Be Built

### Backend (Go):
1. **WebSocket telnet session manager** — persistent telnet connections with real-time output streaming
2. **Command queue** — sequential execution with pause/resume/cancel
3. **Log writer service** — write command output to per-node log files
4. **nodes.json loader** — parse original nodes.json format (nodes + tokens + ports + protocols)
5. **Batch scan endpoint** — "Print All Nodes" sequential execution
6. **BsTool interactive endpoint** — WebSocket or SSE for BsTool output streaming
7. **Scan comparison endpoint** — compare file data with live telnet scan
8. **Node config CRUD endpoints** — add/remove/edit nodes and tokens
9. **Log file endpoints** — list/read/write per-node log files

### Frontend (React):
1. **Commander layout** — new route `/commander` with tree + tabs layout
2. **NodeTree component** — hierarchical tree with color-coded status, context menu, buttons
3. **TelnetTerminal component** — interactive terminal (xterm.js or monospace pre + WebSocket)
4. **BsToolPanel component** — BsTool path, command, output, execute
5. **ScanTab component** — per-node FBC/RPC comparison tables with auto-refresh
6. **CommandQueue indicator** — pause/resume/cancel controls, progress display
7. **NodeConfigDialog component** — add/edit/remove nodes and tokens
8. **LogViewer component** — view per-node log files

---

## Impact on Review

The previous reviewer passed the Go refactor because the scope was defined as "report-generation pipeline only." The functionality transfer map explicitly excluded 15 Commander components as "OUT OF SCOPE."

**The correct scope is the full LOGReport application** — both the Report window AND the Commander window. The reviewer needs to verify against the full original application functionality, not just the report pipeline.

---

## Recommended Approach

1. **Phase 1: Backend Commander APIs** — WebSocket telnet, command queue, log writer, nodes.json loader, batch scan, BsTool interactive
2. **Phase 2: Frontend Commander UI** — Commander layout, NodeTree, TelnetTerminal, BsToolPanel, ScanTab
3. **Phase 3: Integration** — Connect tree to telnet, context menu commands, "Print All Nodes" batch
4. **Phase 4: Review with correct scope** — Verify against FULL original app (report + commander)