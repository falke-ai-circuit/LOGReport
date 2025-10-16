# TODO List

This file contains a list of pending tasks and improvements for the LOGReport project.
Each entry is condensed to maximum 5 lines for readability.

---

[X] **Qt6Qt5 Migration** (2025-01-11)
- Migrated from PyQt6 6.4.2 to PyQt5 5.15.11 for Windows Server 2012 compatibility
- Changed 169+ files (80+ src, 89+ tests) with 5-step pattern (importsenumsmethodsQActionruntime)
- Updated requirements.txt, runtime_hook.py, LOGReporter_PyQt5.spec for Server 2012 deployment
- All PyQt imports working, 23 PyQt tests passing, visual style preserved

[X] **VNC Tab Removal** (2025-01-10)
- Deleted vnc_tab.py (272 lines), test_vnc_connection.py (193 lines) per user request
- Modified 8 files removing VNC imports, classes, methods, signal connections
- Application maintains Telnet and BsTool functionality
- Verified with pytest: 488/489 tests collected (1 VNC test properly excluded), 26 tests passed

[X] **Icon Color System - Execution Status** (2025-10-10)
- Implemented dual color system: icon rectangles/circles change by execution status (green=success, yellow=partial, red=failed)
- Text color remains independent based on file content; hierarchical aggregation (filessectionsnodes)
- Added 9 icon generator functions, separated update_node_icon (execution) from update_node_color (content)
- Both colors update after command execution with red-priority logic

[X] **Telnet Tab - Show File Content** (2025-01-10)
- Actual file content now displays in Telnet tab with headers showing destination file and statistics
- Users can compare displayed content with saved files for verification

[X] **Node Tree - Left Click Auto-Command** (Completed)
- When left-clicking node in tree, corresponding command appears in command pane automatically
- Implemented for both Telnet and BsTool tabs with corresponding command formatting
- Users can now execute commands by pressing Execute button after single click

[X] **Node Tree - File Color Coding** (Completed)
- Added color change on .rpc .fbc .log .lis files based on content and execution status
- Green: command executed AND content >5 lines; Red: executed but <5 lines; Yellow: no execution and <5 lines
- Hierarchical coloring: filessubgroupsnodes (all green = parent green)

[X] **BsTool - Reduced Timeout** (Completed)
- Added 10-second timeout for BsTool commands before reading from temporary output file
- Improves responsiveness for BsTool operations

[X] **Hierarchical Color Persistence** (Completed)
- Color persistence on .fbc .rpc .log .lis files maintained across sessions
- Same coloring system applied to FBC/RPC/LIS/LOG subgroups and parent nodes
- Green propagates hierarchically: all files green  subgroup green  all subgroups green  node green

[X] **Bulk Clear Commands** (Completed)
- Added "Clear All" command to each subgroup (FBC, RPC, LIS, LOG) for batch file clearing
- Node right-click triggers all subgroup clear commands sequentially
- Users no longer need to clear each log file individually

[X] **Node Configurator - Auto Token Detection** (Completed)
- Node colors: green (all info complete), red (missing info)
- Auto-detect tokenid.sys files in same directory when loading AB01_sys
- Auto-load IP address from tokenid.sys files; supports loading single tokenid.sys to export IP for matching node

[X] **Report Generation - All File Types** (Completed)
- Adjusted report generation to scan for .log .lis .fbc .rpc files in selected log folder subfolders
- All file types now included in generated reports (previously only .log files)
- File content from all types visible in final PDF/DOC reports

[X] **Startup Color Persistence & Auto-Expansion** (2025-10-10)
- Implemented startup color checking file content (red=0 lines, yellow<10 lines, green>=10 lines)
- Auto-expansion: entire tree expands when "Print All Nodes" clicked, making all files visible
- Files highlight and scroll into view as processed during command execution

[X] **Print All Nodes - Pause/Resume/Cancel Fix** (2025-01-10)
- Fixed buttons not enabling during workflow; root cause: buttons initially disabled and never re-enabled
- Manual button state management at workflow lifecycle points (process_all_nodes, _process_next, pause, resume, cancel)
- State transitions: IDLERUNNING (pause+cancel)PAUSED (resume+cancel)IDLE; added state flags (_workflow_paused, _workflow_cancelled)
- Modified 6 locations in node_tree_presenter.py (~30 lines) with debug logging

[X] **Telnet Auto-Connect & System Mode** (Completed)
- Execution stops if telnet debugger disconnected; auto-connects to defined IP/port before commands
- Auto-responds "yes" when another user connected to same debugger session
- Ensures system mode (%s prompt) by typing "toggle" if needed; validates mode before command execution

[X] **LOG File Color BsTool Bug** (Fixed)
- Fixed LOG file colors staying red after successful BsTool execution despite file content
- Root cause: file_item_map path mismatch between normalized paths (tree population) and lookup paths (_check_and_update_node_color)
- Path format inconsistency (forward/backslashes) resolved with consistent normalization

[X] **Sequential Execution - UI Highlight Timing** (2025-10-12)
- Fixed premature UI highlight jump to next AP token before previous AP processing finishes
- Deferred highlight to queue idle state (removed from process_node_print_commands Phase 3, moved to _check_sequential_processing_continuation)
- Fixed BsTool tab showing no content by storing actual output in BsToolWorker.self.result with separator headers
- Added dynamic tab switching (Telnet for FBC/RPC, BsTool for LOG) for real-time output visibility; user validated: "now its perfect"

[X] **Sequential Output Display** (2025-10-12)
- Implemented command output display for Print All Nodes sequential execution (FBC/RPC command results)
- Added command_output_display_signal to NodeTreePresenter, routes output to appropriate tabs via _handle_sequential_output
- Telnet tab auto-switches when FBC/RPC output displays; BsTool output via bstool_output_signal (reads temp file)
- Modified 2 files: node_tree_presenter.py (+9 lines signal + switch), commander_window.py (+23 lines routing handler)

[X] **Print All Nodes - Auto-Connect Check** (2025-10-12)
- Added auto-connect check before Print All Nodes workflow starts; calls telnet_service._ensure_debugger_connection() with 2 retries + 10s delay
- System mode verification and graceful abort with error message if connection fails
- **BUGFIX**: Fixed initialization bug on fresh startup (debugger_ip_address not initialized); added get_connection_info_callback to read IP/port from telnet_tab UI
- Created 10/10 passing tests (test_print_all_nodes_auto_connect.py + test_auto_connect_initialization.py); user validated working immediately on fresh startup

[ ] **Telnet Tab - ASCII Table Alignment Issue**
- FBC command output ASCII tables don't align properly in Telnet tab (vertical columns like 'sum' misaligned with headers)
- Despite monospace font and tab-to-space conversion, displays correctly in log files but not in Telnet tab widget
- Need to investigate: alternative fonts (Liberation Mono, DejaVu Sans Mono), content pre-processing, different widget (QPlainTextEdit, custom table)

[X] **BsTool.exe Bundling** (2025-10-13)
- Implemented BsTool.exe bundling with automatic path detection via bstool_path_resolver (sys._MEIPASS  sys.executable dir  project root)
- BsTool.exe bundled via LOGReporter_PyQt5.spec binaries section, extracted to temp _MEIPASS at runtime (onefile mode)
- Path auto-populated on initialization in both dev and packaged modes; user tested by renaming source (bundled exe still worked)
- Created test scripts (quick_test_bstool.ps1, test_bundled_exe.ps1) and documentation (docs/TESTING_BSTOOL_BUNDLING.md)

[X] **Scan Tab - FBC/RPC Live Comparison & Auto-Refresh** (2025-10-15)
- Implemented complete Scan tab with FBC/RPC file comparison against live telnet data (FbcComparisonService 387 lines)
- Cell-by-cell comparison with color-coded results (green=match, yellow=difference, red=error); ComparisonWorker for async execution
- Auto-refresh system: 5s/10s/30s/60s/5min intervals with countdown timer; tab-aware (pauses when switching away, resumes on return)
- Status message propagation to main window status bar; 33/33 tests passing; Parser fixes (empty slots, 'N' suffix, Not Exists, IBC format, mixed-case units)
- Auto-load file on tab open (QTimer 100ms); prevent tab switch when clicking .fbc/.rpc from node tree; PIC 0 parser fix (intelligent separator detection); 2-retry auto-connect when Compare Live clicked

[X] **Sequential Workflow - Button State Bug** (2025-10-13)
- Fixed pause/resume/cancel buttons becoming disabled immediately after first command completion during Print All Nodes
- Root cause: SequentialCommandProcessor incorrectly responding to Print All Nodes commands (premature ExecutionState.IDLE emission)
- Solution: Added guard condition checking _is_processing flag at start of _on_command_completed() (line 628)
- Created test_sequential_processor_guard.py (4 tests, 100% pass); buttons now remain enabled throughout Print All Nodes execution

[X] **Smart Tab Switching** (2025-10-12)
- Implemented smart tab switching with scroll position detection during sequential workflow execution
- Only auto-switch to BsTool/Telnet if user at bottom (following live output); if scrolled up (reviewing earlier logs), keep on current tab
- Added is_user_at_bottom() helpers (5px tolerance), _smart_switch_to_tab wrapper, scroll position preservation in append_output
- File extension routing (.fbc/.rpc/.listelnet, .logbstool); 11/11 passing tests; user validated

[X] **PDF/DOC Report - Node Grouping & Line Wrapping** (2025-10-13)
- Implemented node-based report organization: .fbc.rpc.log.lis order per node before proceeding to next node
- Added clickable Table of Contents with href anchors (PDF) / automatic TOC generation (DOCX); node chapters + file subheadings + PageBreak
- Intelligent line wrapping with textwrap at 80 chars (A4 page 210mm width - 40mm margins = 170mm usable, Courier 10pt verified)
- Created extract_node_from_filename() regex (AP\d{2}[mr]?|AL\d{2}), group_logs_by_node() Dict structure; 24/24 tests passing

[X] **Scan Tab - Implementation** (Completed)
- Implemented Scan tab with node-based subtabs showing .fbc/.rpc file contents in table style
- Each subtab displays table of file content under correct node
- Scanning functionality: select file, compare table values from file against live telnet debugger session data

[X] **Context Menu - Scan FieldBus Structure** (Completed)
- Added "Scan FieldBus structure (token)" command to .fbc/.rpc file right-click context menu
- Opens Scan tab, auto-selects matching file from list, executes "compare live single" command
- Example: AP01m_192-168-0-11.fbc right-click  opens Scan tab  selects file  gets telnet data  compares  changes colors

[X] **Scan Tab - Auto-Generate Tables & Prevent Tab Switch** (Completed)
- Fixed: Tables now generated at beginning (or auto-generated when file selected)
- Fixed: Disabled automatic switching from Scan to Telnet when clicking .fbc file from nodes tree; instead auto-selects same file in Scan tab
- Fixed: First PIC/IBC entry now compared correctly (was skipped previously); all rows now detected and compared

[X] **PIC-12 Queue Reprocessing Fix** (2024-10-10)
- Fixed PIC-12 token queue reprocessing by removing deduplication bug in Commander._process_queue line 1278 (removed set() cast clearing queue)
- Restored original deque implementation for token queue with comprehensive logging to track queue state changes
- Created test suite: 20/20 tests passing (basic queue operations, PIC-12 token workflow simulation, real-world scenario validation)
- User confirmed fix working in production; queue correctly maintains tokens between processing cycles

[X] **Hexadecimal Token Parsing in Node Configurator** (2025-10-15)
- Fixed bare hex token ID recognition (1a1, 3a1, 1c1, 1e1) for AP03m/AP03r nodes
- Enhanced detection: decimal (181)  prefixed hex (0x1a1)  bare hex (1a1) with length constraints (max 5 chars bare, 7 chars prefixed)
- Modified: node_config_dialog.py, file_utils.py (2 locations); created 18/18 passing test suite (test_hexadecimal_token_parsing.py)
- User verified working in production with _DIA/_SYS/AB01_sys test files; AP03m/AP03r now correctly load IPs from hex token files

---

## Pending Tasks

[]We need to add when we click on table value cell in Scan tab that when highlighted it will show valur from log file not the value from telnet ( that way we can highlight multiple values and see the old value from log file, also when highlighted we should retain colour change from comparison ( so when selected if value was red after scan keep value red and if it was yellow keep it yellow ))

---

## Completed Infrastructure Improvements

[X] **Scan Tab - Color Logic Swap** (2025-10-16)
- Swapped RED and YELLOW color meanings: RED now indicates value changes (file had value → live different/missing), YELLOW indicates new data (file empty/N/E → live has value)
- Added CellValueAppeared dataclass to track cells where values appeared in live data
- Modified FbcComparisonService._compare_tables() to categorize differences using _is_empty_value() helper
- Updated node_scan_widget._apply_comparison_colors() to apply new color scheme with updated tooltips
- All ComparisonResult instantiations updated with value_appeared=[] parameter

[X] **Incremental Documentation Update System** (2025-10-16)
- Implemented tracking system to process only documents changed since last update (94% efficiency gain)
- Created `logs/.last_document_update.json` tracker with timestamps, workflow history, and document metadata
- Updated Phase 9 DOCUMENT workflow with decision matrix (Feature/Bug/API/Architecture/Config routing)
- Comprehensive documentation in `.github/instructions/document_update_system.md` with examples
- Reduces DOCUMENT phase from 15 minutes to 3 minutes average (50 docs → 3 docs typical)

