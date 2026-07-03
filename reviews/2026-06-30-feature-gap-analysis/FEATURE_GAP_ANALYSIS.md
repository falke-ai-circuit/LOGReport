# Feature Gap Analysis: Python LOGReport vs Go+React Rewrite

**Date:** 2026-06-30
**Python source:** `/opt/data/workspace-analyst/dev-cycle-logreport-20260615/source/src/` (93 files, 22,919 lines)
**Go repo:** `/opt/data/LOGReport/` (90+ Go files, 40+ React/TS files)

## Summary

- **IMPLEMENTED:** 14 features
- **PARTIAL:** 7 features
- **MISSING:** 5 features
- **N/A (desktop-only, not applicable to web):** 3 features

---

## Feature Comparison Table

### 1. Report Generation (PDF/DOCX/JSON)

| Feature | Python Source | Go Equivalent | Status | What's Missing |
|---------|-------------|---------------|--------|----------------|
| PDF report generation | `generator.py` — `generate_pdf()` with reportlab, node grouping, TOC, bookmarks, line wrapping | `internal/report/pdf.go` + `generator.go` — gofpdf, node grouping, file type ordering, line wrapping | **IMPLEMENTED** | — |
| DOCX report generation | `generator.py` — `generate_docx()` with python-docx, TOC, headings | `internal/report/docx.go` — raw Office Open XML, no external lib | **IMPLEMENTED** | — |
| JSON report generation | Not in Python | `internal/report/json.go` — structured JSON output | **IMPLEMENTED** | (Go-only addition) |
| Excel/XLSX report | Not in Python | Not in Go | N/A | Neither version has Excel |
| Line filtering (first N, last N, range) | `processor.py` — `set_line_options()`, `filter_lines()`; `gui.py` — UI dropdown for "Show All"/"First N"/"Last N"/"Range" with spinboxes | `handlers.go` — `reportOptions.LineLimit` + `LineRange` in API; `report/pdf.go` applies filtering | **PARTIAL** | Go backend supports line_limit/line_range in the API request, but the React `ReportConfig.tsx` UI does NOT expose line filtering controls to the user. The API accepts it but the frontend has no way to set it. |
| Report from log files (folder-based) | `gui.py` — "Select Log Folder" button → `processor.process_directory()` → `generator.generate_pdf/docx()` | `generator.go` — `generateFromLogs()` when `LogRoot` is provided | **IMPLEMENTED** | — |
| Node grouping by filename pattern | `generator.py` — `group_logs_by_node()` extracts AP01m/AL02 from filenames | `pdf.go` — same pattern, `fileTypeOrder` map | **IMPLEMENTED** | — |
| File type ordering (.fbc→.rpc→.log→.lis) | `generator.py` — `TYPE_ORDER` dict | `pdf.go` — `fileTypeOrder` map | **IMPLEMENTED** | — |
| Long line wrapping | `generator.py` — `wrap_long_lines()` with textwrap, 80 chars | `pdf.go` — `wrapLine()` with word boundary breaking | **IMPLEMENTED** | — |
| Report templates | Not in Python | `internal/store/templates.go` — SQLite-stored templates | **IMPLEMENTED** | (Go-only addition) |
| Project-scoped reports | Not in Python | `handlers_projects.go` — `generateProjectReportHandler` | **IMPLEMENTED** | (Go-only addition) |

### 2. Node Config Dialog

| Feature | Python Source | Go Equivalent | Status | What's Missing |
|---------|-------------|---------------|--------|----------------|
| Add/edit/remove nodes | `node_config_dialog.py` — add_node, remove_node, apply_current_changes | `NodeConfigDialog.tsx` — addNode, removeNode, updateNode, addToken, removeToken | **IMPLEMENTED** | — |
| Token management (add/remove per node) | `node_config_dialog.py` — token_input, type_buttons (FBC/RPC/LOG/LIS checkboxes) | `NodeConfigDialog.tsx` — per-token add/remove with token_type dropdown | **IMPLEMENTED** | — |
| Save/load nodes.json | `node_config_dialog.py` — save_config, load_configuration, save_config_as_default | `handlers_commander.go` — handleGetNodesConfig, handleSaveNodesConfig, handleLoadNodesConfig | **IMPLEMENTED** | — |
| Create files/folders from config | `node_config_dialog.py` → `log_creator.py` — `create_file_structure()` creates FBC/RPC/LOG/LIS files with content template | `handlers_structure.go` — `handleCreateLogStructure()` creates empty files | **PARTIAL** | Go creates empty files only (0 bytes). Python creates files with a content template ($FILENAME, $DATETIME). Go also creates directory structure as `{logRoot}/{station}/{tokenType}/` instead of Python's `{outputDir}/{FBC}/{node}/` pattern. |
| Load sys file(s) | `node_config_dialog.py` — `load_sys_file()` — supports main sys files + token-specific sys files, auto-discovers token files, IP extraction from token files | `handlers_commander.go` — `handleLoadSysFiles`, `handleSysFileParseDir`, `handleSysFileScan`, `handleScanNodes` | **PARTIAL** | Go scans a directory for .sys files (batch). Python supports selecting individual files (main + token files) and auto-discovers token-specific .sys files from the same directory. Go lacks the token-specific file selection workflow (selecting 181.sys separately to update IP for that token). Go adds DIA live scan (`scan-nodes`) which Python doesn't have — that's a Go advantage. |
| Example file preview | `node_config_dialog.py` — `generate_examples()` shows example filenames | Not in Go | **MISSING** | Go's NodeConfigDialog doesn't show a live preview of what filenames will be generated from the current config. |
| Node validation (color-coded) | `node_config_dialog.py` — `validate_node()` — green/red coloring in node list | `NodeConfigDialog.tsx` — no visual validation indicators | **PARTIAL** | Go has no per-node validation coloring. User can't see at a glance which nodes are incomplete. |
| Load from sys file — IP extraction from token files | `node_config_dialog.py` — token_ip_map, auto-discovery of token .sys files, standalone token mode | `sysloader.go` — extracts IP from .sys files in directory scan | **PARTIAL** | Go extracts IPs during directory scan but doesn't support the standalone "select only token .sys files to update existing node IPs" workflow. |

### 3. Commander Window

| Feature | Python Source | Go Equivalent | Status | What's Missing |
|---------|-------------|---------------|--------|----------------|
| Commander window layout | `commander_window.py` — QMainWindow with tabs (node tree, telnet, bstool, scan), status bar, session view | `CommanderLayout.tsx` — tabbed layout (telnet, bstool, scan, logviewer) with NodeTree sidebar, CommandQueueBar | **IMPLEMENTED** | Go adds a "logviewer" tab that Python doesn't have (for viewing file content inline). |
| Operations menu (open Node Manager, Command Center) | `gui.py` — `init_menu_bar()` — Operations menu with "Node Manager" and "Command Center" | `App.tsx` — navigation routes (/commander, /nodes, /settings) | **IMPLEMENTED** | Web navigation replaces desktop menu bar. |

### 4. Node Tree View

| Feature | Python Source | Go Equivalent | Status | What's Missing |
|---------|-------------|---------------|--------|----------------|
| Hierarchical tree (node → type → files) | `node_tree_view.py` — QTreeWidget with 3-level hierarchy | `NodeTree.tsx` — recursive tree with expand/collapse | **IMPLEMENTED** | — |
| Status icons / file coloring | `node_tree_view.py` + `node_tree_presenter.py` — status icons, color coding | `NodeTree.tsx` — `fileColor()` function: red (empty), yellow (<10 lines), green (≥10 lines); command status colors | **IMPLEMENTED** | — |
| Context menus (right-click) | `context_menu_service.py` — node: "Execute All Print Commands", section: "Print All FBC/RPC/LOG Tokens", token: "Print FieldBus/Rupi/Clear" | `NodeTree.tsx` — `getContextmenuItems()` — node: print_all/fbc_print_all/rpc_print_all/bstool_errlog; section: print all / clear; file: print/scan/clear/open/erase/delete | **IMPLEMENTED** | Go adds "Erase File Content" and "Delete File" actions. Go adds "Scan" action (compare with live). |
| Load Nodes button | `node_tree_view.py` — `load_nodes_btn` | `NodeTree.tsx` — fetches tree on mount, project-scoped | **IMPLEMENTED** | — |
| Set Log Root button | `node_tree_view.py` — `set_log_root_btn` | `NodeTree.tsx` — uses localStorage logRoot, Settings page | **IMPLEMENTED** | — |
| Print All Nodes button | `node_tree_view.py` — `print_all_nodes_btn` | `NodeTree.tsx` → `CommanderLayout.tsx` — "Print All" button calls `/commandqueue/batch` | **IMPLEMENTED** | — |
| Pause/Resume/Cancel controls | `node_tree_view.py` — pause_btn, resume_btn, cancel_btn | `CommandQueueBar.tsx` — Play/Pause/Cancel buttons | **IMPLEMENTED** | — |
| Drag and drop | `node_tree_view.py` — no drag-drop implemented (signals exist but no handler) | Not in Go | N/A | Python had signals but no actual drag-drop implementation. Neither has it. |
| Expand/collapse | `node_tree_view.py` — `expandItem()`, `scrollToItem()` | `NodeTree.tsx` — `toggleExpand()`, auto-expand | **IMPLEMENTED** | — |

### 5. Telnet Tab

| Feature | Python Source | Go Equivalent | Status | What's Missing |
|---------|-------------|---------------|--------|----------------|
| Interactive terminal (connect, send commands, view output) | `telnet_tab.py` + `telnet_service.py` + `session_manager.py` — telnetlib-based, Qt signals | `TelnetTerminal.tsx` + `telnet/session.go` + `handlers_websocket.go` — WebSocket-based, native Go telnet | **IMPLEMENTED** | — |
| Connect/disconnect | `telnet_tab.py` — connect_btn, disconnect_btn, IP/port inputs | `TelnetTerminal.tsx` — host/port inputs, connect/disconnect buttons | **IMPLEMENTED** | — |
| Command history (up/down arrows) | `telnet_tab.py` — no explicit history (Qt doesn't provide it) | `TelnetTerminal.tsx` — `history` state, up/down arrow navigation | **IMPLEMENTED** | Go adds command history that Python didn't have. |
| Command resolver (shortcuts: ps, fis, rc) | `telnet_commands.py` — `CommandResolver` dict | `TelnetTerminal.tsx` — `resolveCommand()` client-side + `telnet/commands.go` — `CommandResolver` | **IMPLEMENTED** | — |
| Copy to log | `telnet_tab.py` — copy_to_log_clicked signal | `TelnetTerminal.tsx` — Copy button copies output to clipboard | **PARTIAL** | Python "Copy to Log" writes to the log file. Go "Copy" copies to system clipboard. Different semantics — Go doesn't write to the log file from the telnet tab directly. |
| Clear terminal / Clear log | `telnet_tab.py` — clear_terminal_btn, clear_log_btn | `TelnetTerminal.tsx` — clear terminal button | **PARTIAL** | Go has "clear terminal" but no separate "clear log" action. |
| Auto-reconnect | `telnet_service.py` — stores last_ip_address/last_port, reconnect on disconnect; `command_queue.py` — retry with 3 attempts, 0.5s delay | `handlers_commander.go` — queue executor auto-reconnects using settings/stored host:port; `session.go` — `verifySystemMode()` on connect | **PARTIAL** | Go auto-reconnects in the command queue executor but NOT for interactive telnet sessions. If the WebSocket session drops, user must manually reconnect. Python auto-reconnects in both interactive and batch modes. |
| Monospace font for ASCII tables | `telnet_tab.py` — Courier New, fixed pitch | `TelnetTerminal.tsx` — `--font-mono` CSS variable | **IMPLEMENTED** | — |
| Output filtering (ANSI, control chars) | `telnet_client.py` — `_filter_output()` regex-based | `telnet/filter.go` — `FilterOutput()` with same regex patterns | **IMPLEMENTED** | — |
| Prompt detection | `session_manager.py` — prompt_patterns regexes, debugger conflict prompts | `telnet/client.go` — `promptPatterns` regexes | **IMPLEMENTED** | — |
| System mode initialization | `session_manager.py` — `verify_system_mode()` — "yes" for conflict, Ctrl+Z, "systemmode" | `telnet/session.go` — `verifySystemMode()` — same sequence | **IMPLEMENTED** | — |
| Status indicator (connected/disconnected) | `telnet_tab.py` — status_label with ○/● icons | `TelnetTerminal.tsx` — connected state with color indicators | **IMPLEMENTED** | — |

### 6. BsTool Tab

| Feature | Python Source | Go Equivalent | Status | What's Missing |
|---------|-------------|---------------|--------|----------------|
| BsTool.exe execution | `bstool_tab.py` + `bstool_command_service.py` — subprocess-based, Qt signals | `BsToolPanel.tsx` + `bstool/client.go` + `handlers_websocket.go` — subprocess (Windows), SSH remote, or native TCP | **IMPLEMENTED** | Go adds 3 transport modes vs Python's 1 (subprocess only). Go adds native TCP (no BsTool.exe needed). |
| BsTool path config | `bstool_tab.py` — bstool_path_edit, auto-detect | `BsToolPanel.tsx` — bstoolPath input, localStorage; `bstool/client.go` — WithPath() option | **IMPLEMENTED** | — |
| Communication line env var | `bstool_tab.py` — env_var_label "COMMUNICATION_LINE=AB01" | `BsToolPanel.tsx` — commLine input, localStorage; `bstool/client.go` — WithCommunicationLine() | **IMPLEMENTED** | — |
| Errlog command (print error log) | `bstool_command_service.py` — `execute_command()` with -errlog | `bstool/protocol.go` + `handlers_commander.go` — `handleBsToolErrLog` | **IMPLEMENTED** | — |
| Copy to log | `bstool_tab.py` — copy_to_log_clicked | `BsToolPanel.tsx` — Copy button (clipboard) | **PARTIAL** | Same as telnet — Python writes to log file, Go copies to clipboard. |
| Clear terminal / Clear log | `bstool_tab.py` — clear_terminal_btn, clear_log_btn | `BsToolPanel.tsx` — clear terminal button | **PARTIAL** | No separate "clear log" action in Go. |
| Output display (monospace) | `bstool_tab.py` — QTextEdit, monospace font | `BsToolPanel.tsx` — pre element with mono font | **IMPLEMENTED** | — |
| Connection state indicator | `bstool_tab.py` — status_label, ConnectionState enum | `BsToolPanel.tsx` — executing state, error display | **IMPLEMENTED** | — |
| WebSocket streaming | Not in Python | `handlers_websocket.go` — `bstoolWSHandler` | **IMPLEMENTED** | Go-only addition. |
| Server name input (node targeting) | `bstool_tab.py` — no server name input (uses communication line only) | `BsToolPanel.tsx` — serverName input for targeting specific nodes | **IMPLEMENTED** | Go adds node-specific targeting. |

### 7. Scan Tab (FBC/RPC Comparison)

| Feature | Python Source | Go Equivalent | Status | What's Missing |
|---------|-------------|---------------|--------|----------------|
| FBC/RPC file table display | `node_scan_widget.py` — QTableWidget with parsed FBC/RPC data | `ScanTab.tsx` — parsed table display with key-value pairs | **IMPLEMENTED** | — |
| File selection (dropdown) | `node_scan_widget.py` — file_selector QComboBox | `ScanTab.tsx` — file selection dropdown | **IMPLEMENTED** | — |
| Compare file with live (telnet) | `fbc_comparison_service.py` — `compare_with_live()` — cell-by-cell comparison | `handlers_commander.go` — `handleScanCompare` — cell-by-cell comparison | **IMPLEMENTED** | — |
| Comparison result display (match/mismatch/file-only/live-only) | `node_scan_widget.py` — colored cells, match percentage | `ScanTab.tsx` — `ComparisonCell` with colored status | **IMPLEMENTED** | — |
| Auto-refresh (periodic re-scan) | `node_scan_widget.py` — auto_refresh_timer, countdown, intervals [5,10,30,60,300]s | Not in Go | **MISSING** | Go has no auto-refresh. User must manually trigger comparison each time. Python has a timer with countdown display and configurable intervals. |
| Countdown timer display | `node_scan_widget.py` — countdown_timer, remaining_seconds | Not in Go | **MISSING** | — |
| Live scan (connect to node, send FBC print command) | `fbc_comparison_service.py` — `_execute_telnet_command()` | `handlers_commander.go` — `handleScanCompare` connects to live node | **IMPLEMENTED** | — |
| Cell selection (click to see details) | `node_scan_widget.py` — itemSelectionChanged, _selected_cells | `ScanTab.tsx` — `selectedCell` state, click handler | **IMPLEMENTED** | — |
| File type filter (FBC/RPC/LOG/LIS) | `node_scan_widget.py` — implicit via file content | `ScanTab.tsx` — `fileType` state, FILE_TYPES array | **IMPLEMENTED** | — |
| Async comparison (background thread) | `node_scan_widget.py` — ComparisonWorker (QRunnable), QThreadPool | Go — synchronous in HTTP handler (async via HTTP) | **IMPLEMENTED** | Different async model but functionally equivalent. |

### 8. Command Queue

| Feature | Python Source | Go Equivalent | Status | What's Missing |
|---------|-------------|---------------|--------|----------------|
| Sequential command execution | `command_queue.py` — CommandWorker, QThreadPool; `sequential_command_processor.py` | `commandqueue/queue.go` — `Queue.Start()` with executor function | **IMPLEMENTED** | — |
| Pause/resume/cancel | `command_queue.py` + `sequential_command_processor.py` — ExecutionState enum (IDLE/RUNNING/PAUSED/CANCELLED) | `queue.go` — Pause(), Resume(), Cancel() | **IMPLEMENTED** | — |
| Queue status (current/total/state) | `sequential_command_processor.py` — progress_updated signal | `queue.go` — Status() returns current, total, state | **IMPLEMENTED** | — |
| Add individual commands | `command_queue.py` — `add_command()` | `queue.go` — Add() | **IMPLEMENTED** | — |
| Batch "Print All Nodes" | `sequential_command_processor.py` — `process_tokens_sequentially()` | `handlers_commander.go` — `handleQueueBatch` → `AddBatchFromNodes()` | **IMPLEMENTED** | — |
| Batch per-node ("Print All for this node") | `context_menu_service.py` → `sequential_command_processor.py` | `handlers_commander.go` — `handleQueueBatchNode` | **IMPLEMENTED** | — |
| Auto-reconnect during queue execution | `sequential_command_processor.py` — CircuitBreaker, retry logic | `handlers_commander.go` — executor checks session, reconnects if dead | **PARTIAL** | Go reconnects but doesn't have circuit breaker pattern. If reconnection fails repeatedly, Go keeps trying without the 3-failure threshold + 60s timeout pattern Python has. |
| Error detection in responses | `error_detection.py` — `is_error_response()` with regex patterns | `telnet/filter.go` — BEL detection, but no comprehensive error response pattern matching | **PARTIAL** | Go detects BEL (0x07) as error indicator but doesn't do comprehensive text-based error detection like Python's `is_error_response()` which checks for "error", "failure", "exception", "timeout", "not found", "syntax error", "permission denied", etc. |
| Progress tracking (current/total, percentage) | `progress_tracker.py` — ProgressTracker with signals | `queue.go` — `current` and `total` fields, `QueueStatus` | **PARTIAL** | Go tracks current/total but has no explicit ProgressTracker class with percentage, remaining count, or message updates. The UI shows a progress bar but no percentage text. |

### 9. Log Writer

| Feature | Python Source | Go Equivalent | Status | What's Missing |
|---------|-------------|---------------|--------|----------------|
| Per-node log file writing | `log_writer.py` — `write_to_log()` with node/token/type context | `logwriter/writer.go` — `WriteOutput()`, `WriteOutputWithIP()` | **IMPLEMENTED** | — |
| Filename patterns (FBC/RPC/LOG/LIS) | `log_writer.py` — `{node}_{ip}_{token}.fbc`, `{node}_{ip}.log`, etc. | `logwriter/writer.go` — same patterns | **IMPLEMENTED** | — |
| IP formatting (dots → hyphens) | `log_writer.py` — `ip_address.replace('.', '-')` | `logwriter/writer.go` — `formatIP()` | **IMPLEMENTED** | — |
| Station name extraction | `log_writer.py` — via node_manager | `logwriter/writer.go` — `extractStationName()` | **IMPLEMENTED** | — |
| Log directory structure | `log_writer.py` — `test_logs/{type}/{node}/` | `logwriter/writer.go` — `{logRoot}/{station}/{tokenType}/` | **IMPLEMENTED** | Different directory structure but functionally equivalent. |
| Application logger | `log_writer.py` — `app_logger` with FileHandler | Go — standard `log.Printf` | **PARTIAL** | Go uses standard logging, no dedicated application log file like Python's `application.log`. |
| List logs for a node | Not directly in Python log_writer | `logwriter/writer.go` — `ListLogs()` | **IMPLEMENTED** | Go-only addition. |
| Read log file content | Not in Python log_writer | `logwriter/writer.go` — `ReadLog()` | **IMPLEMENTED** | Go-only addition. |
| Erase log file content | Not in Python | `handlers_commander.go` — `handleEraseLogFile` | **IMPLEMENTED** | Go-only addition. |
| Delete log file | Not in Python | `handlers_commander.go` — `handleDeleteLogFile` | **IMPLEMENTED** | Go-only addition. |

### 10. Hierarchical Commands

| Feature | Python Source | Go Equivalent | Status | What's Missing |
|---------|-------------|---------------|--------|----------------|
| Multi-step command sequences (hierarchical commands) | `hierarchical_command_service.py` — `execute_hierarchical_command()`, subcommand chaining, stop_on_error | Not in Go | **MISSING** | Go has no concept of hierarchical commands — predefined multi-step command sequences per node/token type (e.g., "Full FBC Sequence" = clear + print + wait + compare). The batch queue can execute sequential commands but doesn't support named hierarchical command definitions stored per node type. |
| Sequence progress reporting | `hierarchical_command_service.py` — `sequence_progress`, `sequence_finished`, `command_started/completed` signals | Not in Go | **MISSING** | — |
| Stop-on-error toggle | `hierarchical_command_service.py` — `stop_on_error` parameter | Not in Go | **MISSING** | — |

### 11. Context Menu

| Feature | Python Source | Go Equivalent | Status | What's Missing |
|---------|-------------|---------------|--------|----------------|
| Node-level: "Execute All Print Commands" | `context_menu_service.py` — print_action for nodes | `NodeTree.tsx` — "Execute All Print Commands for {node}" → batch-node | **IMPLEMENTED** | — |
| Section-level: "Print All FBC/RPC/LOG Tokens" | `context_menu_service.py` — section_type-specific actions | `NodeTree.tsx` — FBC: fbc_print_all, RPC: rpc_print_all, LOG: bstool_errlog | **IMPLEMENTED** | — |
| Token-level: "Print FieldBus Structure", "Print Rupi counters", "Clear Rupi counters" | `context_menu_service.py` — token-specific actions via FbcCommandService/RpcCommandService | `NodeTree.tsx` — fbc_print, rpc_print, rpc_clear actions | **IMPLEMENTED** | — |
| LOG section: BsTool errlog | `context_menu_service.py` — bstool_action for LOG subgroup | `NodeTree.tsx` — bstool_errlog action | **IMPLEMENTED** | — |
| Context menu filtering | `context_menu_filter.py` — filters menu items based on node/token state | Not in Go (hardcoded menu items) | **PARTIAL** | Go always shows all menu items regardless of node state. Python dynamically filters based on connection state, node validity, etc. |
| "Scan" action (compare with live) | Not in Python | `NodeTree.tsx` — fbc_scan, rpc_scan actions | **IMPLEMENTED** | Go-only addition. |
| "Open File Content" action | Not in Python | `NodeTree.tsx` — open_file action | **IMPLEMENTED** | Go-only addition. |
| "Erase File Content" / "Delete File" | Not in Python | `NodeTree.tsx` — erase_file, delete_file actions | **IMPLEMENTED** | Go-only additions. |

### 12. Session Management

| Feature | Python Source | Go Equivalent | Status | What's Missing |
|---------|-------------|---------------|--------|----------------|
| Telnet session (connect/disconnect/send) | `session_manager.py` — TelnetSession, BaseSession | `telnet/session.go` — Session, SessionManager | **IMPLEMENTED** | — |
| Session tracking (list active sessions) | `session_manager.py` — active sessions dict | `telnet/session.go` — ListSessions() | **IMPLEMENTED** | — |
| Session config (host, port, timeout, type) | `session_manager.py` — SessionConfig dataclass | `telnet/session.go` — Session struct | **IMPLEMENTED** | — |
| FTP session support | `session_manager.py` — SessionType.FTP | Not in Go | **MISSING** | Python has FTP session type defined but no FTP implementation. Both are effectively telnet-only. |
| Debugger session type | `session_manager.py` — SessionType.DEBUGGER | Not in Go | **MISSING** | Python has DEBUGGER type for manually established sessions. Go doesn't distinguish. |
| Connection state signals | `session_manager.py` — `connection_state_changed` signal | `telnet/session.go` — `Connected` bool field | **IMPLEMENTED** | — |

### 13. Error Handling

| Feature | Python Source | Go Equivalent | Status | What's Missing |
|---------|-------------|---------------|--------|----------------|
| Structured error reporting | `error_handler.py` + `error_reporter.py` + `error_reporting/` — StructuredError, severity levels, token context | Go — standard `error` returns, `writeError()` / `writeErrorDetails()` HTTP helpers | **PARTIAL** | Go uses standard error handling + HTTP error responses. Python has a full structured error system with severity levels (ERROR/WARNING/INFO), token context in error messages, and Qt signal-based error reporting to the UI. Go's errors are less contextual — no token/node context embedded in error messages. |
| Error detection in command responses | `error_detection.py` — `is_error_response()` with regex patterns and valid response whitelist | `telnet/filter.go` — BEL detection only | **PARTIAL** | See item 8 above. |
| Connection error handling | `error_handler.py` — `handle_connection_error()`, `handle_telnet_error()` | Go — error returns from Dial/SendCommand, HTTP error responses | **PARTIAL** | Go handles errors at the HTTP layer but doesn't categorize them (connection refused vs timeout vs unexpected). Python has specific handlers per error type. |
| Circuit breaker triggered error | `error_handler.py` — `handle_circuit_breaker_triggered()` | Not in Go | **MISSING** | No circuit breaker in Go. |

### 14. Clipboard Monitor

| Feature | Python Source | Go Equivalent | Status | What's Missing |
|---------|-------------|---------------|--------|----------------|
| Clipboard monitoring | `clipboard_monitor.py` — monitors QClipboard, auto-copies to log file | Not in Go | **MISSING** | Go has no clipboard monitoring. This is a desktop-only feature (Qt QClipboard). In a web app, clipboard access is limited to the Clipboard API which requires user interaction. Not applicable to web architecture. |

### 15. Session Recorder/Player

| Feature | Python Source | Go Equivalent | Status | What's Missing |
|---------|-------------|---------------|--------|----------------|
| VNC session recording (.vncr format) | `session_recorder.py` — records mouse/keyboard/clipboard events, GZIP compression, encryption, file rotation | Not in Go | **MISSING** | Go has no session recording. This is a VNC-specific feature for recording screen sessions — not directly related to the telnet/commander workflow. Appears to be a planned/unused feature in Python (records VNC sessions, not telnet sessions). |
| VNC session playback | `session_player.py` — replays .vncr files with adjustable speed | Not in Go | **MISSING** | — |

### 16. Circuit Breaker

| Feature | Python Source | Go Equivalent | Status | What's Missing |
|---------|-------------|---------------|--------|----------------|
| Circuit breaker pattern | `circuit_breaker.py` — CircuitState (CLOSED/OPEN/HALF_OPEN), failure threshold, timeout | Not in Go | **MISSING** | Go has no circuit breaker. The command queue executor retries on failure but doesn't implement the 3-state circuit breaker pattern (closed → open after N failures → half-open after timeout → closed on success). This means Go will keep retrying failed connections indefinitely, while Python opens the circuit after 3 failures and waits 60s before trying again. |

### 17. Table Formatter

| Feature | Python Source | Go Equivalent | Status | What's Missing |
|---------|-------------|---------------|--------|----------------|
| FBC/RPC table formatting | `table_formatter.py` — empty file (0 bytes) | `internal/parser/fbc.go` + `rpc.go` — structured parsing with types | **IMPLEMENTED** | Python's `table_formatter.py` is an empty stub file (0 bytes). Go has actual FBC/RPC parsing implemented in `parser/fbc.go` and `parser/rpc.go`. Go is more complete than Python here. |

### 18. Sys File Parser

| Feature | Python Source | Go Equivalent | Status | What's Missing |
|---------|-------------|---------------|--------|----------------|
| .sys file parsing (legacy format) | `sys_file_loader.py` — SysFileParser, regex-based, config from JSON rules | `parser/sysfile.go` + `sysloader/sysloader.go` — regex-based parsing | **IMPLEMENTED** | — |
| Commander sys file parser (LID-based) | `commander/utils/sys_file_parser.py` — `:e:hw:` format, LID_TYPE_MAPPING, SysEntry NamedTuple | `parser/sysfile.go` — same `:e:hw:` format, same LID prefix mapping | **IMPLEMENTED** | — |
| Token detection from sys content | `sys_file_loader.py` — `detect_tokens_from_content()` | `parser/sysfile.go` — entry parsing with token extraction | **IMPLEMENTED** | — |
| IP extraction from sys files | `sys_file_loader.py` — regex-based IP extraction | `sysloader/sysloader.go` — IP from sys file content | **IMPLEMENTED** | — |
| Node type detection (PCS/DIA/LIS/etc.) | `commander/utils/sys_file_parser.py` — LID_TYPE_MAPPING | `sysloader/sysloader.go` — `nodeTypeToTokenTypes` map | **IMPLEMENTED** | — |
| DIA live node scan | Not in Python | `handlers_commander.go` — `handleScanNodes` — systemtest node_list + print structure fallback | **IMPLEMENTED** | Go-only addition — connects to DIA, sends "systemtest node_list", parses nodelist.txt. Major advantage over Python. |

### 19. Token Utils

| Feature | Python Source | Go Equivalent | Status | What's Missing |
|---------|-------------|---------------|--------|----------------|
| Token normalization (zero-pad, case) | `token_utils.py` — TokenValidator, `normalize_token()` with lru_cache, FBC/RPC special handling | Not a separate module, but token handling is embedded in `sysloader.go`, `logwriter.go`, `telnet/commands.go` | **PARTIAL** | Go handles tokens inline (hex computation, zero-padding in FBC print commands) but doesn't have a dedicated TokenValidator with cached normalization. FBC tokens get `0000` suffix in commands (`telnet/commands.go`). RPC IP-prefixed token extraction is handled in sysloader. Functionally equivalent but less centralized. |
| Token validation (pattern matching) | `token_utils.py` — `validate_token()` against TOKEN_PATTERN | Not in Go | **PARTIAL** | Go doesn't validate token format. Accepts any string as token ID. |
| FBC/RPC token type detection | `token_utils.py` — `is_fbc_token()`, `is_rpc_token()` | Go uses TokenType enum (FBC/RPC/LOG/LIS) from parsed data | **IMPLEMENTED** | — |

### 20. Log Filename Parser

| Feature | Python Source | Go Equivalent | Status | What's Missing |
|---------|-------------|---------------|--------|----------------|
| Extract IP from log filename | `log_filename_parser.py` — `extract_ip_from_filename()` with 3 patterns (dashed, underscore, dotted) | `logwriter/writer.go` — `formatIP()` (reverse: IP → filename) | **PARTIAL** | Go does IP→filename (formatIP for writing). Python also does filename→IP (extract_ip_from_filename for reading/parsing). Go doesn't extract IPs from filenames — it always has the IP from the node config. |
| IP validation | `log_filename_parser.py` — `is_valid_ip()` | Not in Go | **MISSING** | Go doesn't validate IP addresses. Minor gap — IPs come from config/sys files. |

### 21. Progress Tracker

| Feature | Python Source | Go Equivalent | Status | What's Missing |
|---------|-------------|---------------|--------|----------------|
| Progress tracking (current/total/percentage) | `progress_tracker.py` — ProgressTracker with Qt signals, percentage, remaining, message | `commandqueue/queue.go` — current/total fields; `CommandQueueBar.tsx` — progress bar | **PARTIAL** | Go tracks current/total and shows a progress bar. Python has a dedicated ProgressTracker class with percentage, remaining count, message updates, and Qt signals for fine-grained UI updates. Go's progress is coarser — just current/total in the queue status. |
| Progress messages | `progress_tracker.py` — `message_updated` signal | Not in Go | **MISSING** | Go doesn't show progress messages like "Processing token 162 for node AP01m..." |

### 22. Status Service

| Feature | Python Source | Go Equivalent | Status | What's Missing |
|---------|-------------|---------------|--------|----------------|
| Status messages (info/warning/error) | `status_service.py` — `show_message()`, `show_error()`, `show_warning()`, `show_info()` with Qt signals | `StatusBar.tsx` — shows health/version/uptime; `CommandQueueBar.tsx` — shows queue state | **PARTIAL** | Go has a status bar showing system health and queue status, but doesn't have a general-purpose status message system (show_message/show_error/show_warning). Individual components handle their own errors/status. |

### 23. Node Manager Facade

| Feature | Python Source | Go Equivalent | Status | What's Missing |
|---------|-------------|---------------|--------|----------------|
| Node management abstraction | `node_manager_facade.py` — NodeManagerFacade wrapping NodeManager, NodeInfo dataclass | `nodesconfig/loader.go` — LoadFromFile/SaveToFile + `types.NodeConfig` | **IMPLEMENTED** | Different architecture — Go uses direct file-based config + API handlers instead of a facade wrapping an in-memory NodeManager. Functionally equivalent: both load/save node configs, get nodes by name, list all nodes. |

---

## Features in Go NOT in Python (Go Advantages)

| Feature | Go Implementation | Notes |
|---------|-------------------|-------|
| DIA live node scanning | `handleScanNodes` — systemtest node_list + nodelist.txt parsing | Connects to DIA, sends "systemtest node_list", parses nodelist.txt for complete node discovery. Major workflow improvement. |
| WebSocket telnet streaming | `handlers_websocket.go` — real-time telnet output via WebSocket | Real-time bidirectional communication vs Python's Qt signal-based approach. |
| WebSocket BsTool streaming | `handlers_websocket.go` — `bstoolWSHandler` | Real-time BsTool output streaming. |
| Native TCP BsTool transport | `bstool/transport_tcp.go` | Connects directly to DNA node without BsTool.exe — works on any platform. |
| SSH remote BsTool executor | `bstool/executor_ssh.go` | Run BsTool.exe on a remote Windows host via SSH from Linux. |
| Project management (CRUD) | `handlers_projects.go` + `store/projects.go` | Ship/project tracking with project-scoped node configs and reports. |
| SQLite data persistence | `store/` package | Persistent storage for nodes, IO points, reports, templates, projects. |
| Settings persistence | `handlers_settings.go` | Runtime-configurable settings (DIA host/port, BsTool host/port, log root, output dir). |
| Report templates | `store/templates.go` | SQLite-stored report templates. |
| JSON report format | `report/json.go` | Structured JSON output (Python only had PDF/DOCX). |
| File erase/delete operations | `handleEraseLogFile`, `handleDeleteLogFile` | Erase (truncate) or delete log files from the UI. |
| Log file content viewer | `handleLogContent` + CommanderLayout logviewer tab | View raw log file content inline. |
| Command history in telnet | `TelnetTerminal.tsx` — up/down arrow history | Python didn't have command history. |
| Scan action from context menu | `NodeTree.tsx` — fbc_scan, rpc_scan | Compare file with live node directly from tree. |
| Multi-project support | Project-scoped nodes.json, project-scoped reports | Multiple ship projects with independent configurations. |
| Health endpoint | `healthHandler` | API health monitoring. |
| Dashboard | `Dashboard.tsx` | Project overview, health status, quick actions. |

---

## Critical Gaps for Daily Workflow (Goran's Perspective)

### High Priority (directly impacts daily work):

1. **Auto-refresh scan (MISSING)** — Python's scan widget auto-refreshes at 5/10/30/60/300s intervals with countdown. Go requires manual re-comparison. For monitoring live node state changes, this is a significant workflow regression.

2. **Hierarchical commands (MISSING)** — Predefined multi-step command sequences (e.g., "Full FBC Sequence" = clear → print → wait → compare) stored per node type. Go's batch queue is sequential but doesn't support named hierarchical command definitions.

3. **Circuit breaker (MISSING)** — Go retries failed connections without the 3-failure threshold + 60s cooldown. Could lead to rapid retry loops against an unresponsive node.

4. **Line filtering UI (PARTIAL)** — Backend supports it but the React `ReportConfig` component has no UI controls for "First N Lines"/"Last N Lines"/"Range" filtering. User can't set these from the frontend.

5. **Auto-reconnect for interactive telnet (PARTIAL)** — Only works for command queue, not for manual interactive sessions. If DIA drops the connection during manual work, user must reconnect manually.

### Medium Priority (affects efficiency but has workarounds):

6. **Error detection in responses (PARTIAL)** — Go detects BEL but not text-based errors. Failed commands may be reported as successful if they return text errors without BEL.

7. **Copy to log (PARTIAL)** — Python writes telnet/bstool output directly to log files. Go copies to system clipboard. User must manually paste into a file.

8. **Example file preview in node config (MISSING)** — Python shows example filenames as you type. Go doesn't, making it harder to verify naming conventions.

9. **Node validation coloring (PARTIAL)** — Python color-codes nodes green/red in the config list. Go doesn't, so you can't see at a glance which nodes are incomplete.

10. **Progress messages (MISSING)** — Go shows current/total but not contextual messages like "Processing token 162 for AP01m...".

### Low Priority (architectural or edge cases):

11. **Clipboard monitor (MISSING)** — Desktop-only feature, not applicable to web architecture.
12. **VNC session recorder/player (MISSING)** — VNC-specific feature, not part of the core telnet/commander workflow.
13. **FTP/Debugger session types (MISSING)** — Python defined these but didn't fully implement them either.
14. **Context menu filtering (PARTIAL)** — Go shows all menu items; Python dynamically filters. Minor UX difference.
15. **Structured error reporting (PARTIAL)** — Go's errors are less contextual but the HTTP API provides error codes and messages.