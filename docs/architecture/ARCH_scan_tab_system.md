# 🔍 Scan Tab System Architecture

<!-- METADATA -->
metadata: {
  created_date: "2025-10-15",
  last_modified: "2025-10-15",
  last_accessed: "2025-10-15",
  word_count: 2100,
  reference_count: 3,
  document_hash: "scan_tab_system_arch",
  obsolete_check_date: "2025-10-15",
  section_count: 8,
  internal_link_count: 6,
  phase: "3+4_complete"
}
<!-- /METADATA -->

## 📑 Table of Contents

- [Overview](#overview)
- [System Architecture](#system-architecture)
- [Component Design](#component-design)
- [Live Comparison Engine](#live-comparison-engine)
- [Auto-Refresh Management](#auto-refresh-management)
- [Tab-Aware Pause System](#tab-aware-pause-system)
- [Status Message Propagation](#status-message-propagation)
- [Data Flow](#data-flow)

---

## 🎯 Overview

The Scan Tab System provides real-time FBC/RPC file viewing and live telnet-based comparison within Commander Center. Implemented across Phase 1 (file viewing), Phase 3 (live comparison), and Phase 4 (UI polish), the system enables operators to compare saved configurations with live device state without leaving the application.

### Key Capabilities

| Capability | Phase | Description |
|------------|-------|-------------|
| **File Viewing** | 1 | Tabular display of FBC/RPC files with dark theme styling |
| **Live Comparison** | 3 | Cell-by-cell comparison with telnet-based FBC command execution |
| **Color Coding** | 3 | Visual difference detection (green=match, yellow=diff) |
| **Auto-Refresh** | 3 | Configurable periodic comparison (5s/10s/30s/60s) |
| **Tab-Aware Pause** | 4 | Intelligent auto-refresh suspension during tab switches |
| **Status Messages** | 4 | Real-time progress and result feedback via status bar |
| **Context Menu** | 4 | File path copying and quick actions |

---

## 🏗️ System Architecture

The Scan Tab System follows a layered architecture with clear separation of concerns.

**Layered Architecture**:
```
┌─────────────────────────────────────────────────────────────┐
│                   Presentation Layer                         │
│  ┌─────────────┐  ┌──────────────┐  ┌──────────────┐       │
│  │ SessionView │  │   ScanTab    │  │ NodeScanWidget│       │
│  │  (Container)│→ │  (Coordinator)│→ │  (Per-Node UI)│       │
│  └─────────────┘  └──────────────┘  └──────────────┘       │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                      Service Layer                           │
│  ┌──────────────────┐  ┌─────────────────────────┐          │
│  │ FbcComparison    │  │   FbcParserService      │          │
│  │    Service       │→ │  (File/Content Parsing) │          │
│  │ (Live Compare)   │  └─────────────────────────┘          │
│  └──────────────────┘                                        │
│         ↓                                                    │
│  ┌──────────────────┐                                        │
│  │  TelnetService   │                                        │
│  │ (Command Exec)   │                                        │
│  └──────────────────┘                                        │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                       Data Layer                             │
│  ┌──────────────┐  ┌─────────────┐  ┌──────────────┐       │
│  │ NodeManager  │  │ File System │  │ Telnet Device│       │
│  │  (Config)    │  │   (_DIA/)   │  │  (Live FBC)  │       │
│  └──────────────┘  └─────────────┘  └──────────────┘       │
└─────────────────────────────────────────────────────────────┘
```

**Design Patterns**:
- **MVP (Model-View-Presenter)**: Separates UI from business logic
- **Service Layer**: Centralizes comparison and parsing logic
- **Observer Pattern**: Qt signals for status updates and tab changes
- **Command Pattern**: Telnet command execution with async worker threads
- **State Machine**: Auto-refresh pause/resume state management

See: [Node System](ARCH_node_system.md) | [Command System](ARCH_command_system.md)

---

## 🧩 Component Design

### ScanTab (Coordinator)

**Responsibilities**:
- Create per-node subtabs from NodeManager configuration
- Forward signals between NodeScanWidget and CommanderWindow
- Coordinate tab switching and auto-refresh pause/resume

**Key Methods**:
```python
populate_nodes()                 # Create NodeScanWidget for each node
pause_all_auto_refresh()         # Pause all widgets (Phase 4)
resume_active_auto_refresh()     # Resume active widget (Phase 4)
_on_node_tab_changed(index)      # Handle subtab switching (Phase 4)
```

**Signals**:
- `status_message(str, int)` - Forwards status from NodeScanWidget to CommanderWindow

### NodeScanWidget (Per-Node UI)

**Responsibilities**:
- Display FBC/RPC files in tabular format
- Execute live comparison via FbcComparisonService
- Manage auto-refresh timer with tab-aware pause logic
- Emit status messages for progress and results

**Key Methods**:
```python
load_token_file(file_path)       # Load and display file
_on_compare_clicked()            # Start live comparison
_on_comparison_finished(result)  # Handle comparison result
_on_auto_refresh_triggered()     # Periodic refresh callback
pause_auto_refresh()             # Pause timer (Phase 4)
resume_auto_refresh()            # Resume timer (Phase 4)
is_auto_refresh_active()         # Check timer state (Phase 4)
```

**State Variables**:
- `_auto_refresh_enabled` - Checkbox state (user control)
- `_auto_refresh_paused` - Tab switching pause flag (Phase 4)
- `_comparison_worker` - QThread for async comparison
- `_auto_refresh_timer` - QTimer for periodic refresh

**Signals**:
- `status_message(str, int)` - Emitted on comparison start/success/failure

### FbcComparisonService (Live Comparison Engine)

**Responsibilities**:
- Execute FBC commands via telnet
- Parse live telnet output
- Compare file content with live output cell-by-cell
- Return structured comparison results

**Key Methods**:
```python
compare_fbc_live(node, token, file_content) -> ComparisonResult
_execute_fbc_command(token) -> str
_parse_telnet_output(output) -> FbcTableData
```

**Data Structures**:
```python
@dataclass
class ComparisonResult:
    success: bool
    differences: List[CellDifference]
    error_message: Optional[str]
    file_type: str
    total_cells: int

@dataclass
class CellDifference:
    row: int
    col: int
    file_value: str
    live_value: str
```

### FbcParserService (File Parsing)

**Responsibilities**:
- Parse FBC and RPC files from disk or string content
- Extract metadata (timestamp, command, agent ID)
- Handle edge cases (PIC 0, N suffix, Not Exists, IBC format, mixed-case)

**Key Methods**:
```python
parse_file(file_path) -> FbcTableData
parse_content(content, file_type) -> FbcTableData
```

**Parser Enhancements (Phase 3)**:
- **PIC 0 Separator Fix**: Detects `| 0 |` separator in TOTAL row
- **N Suffix Handling**: Strips trailing 'N' from agent columns (A11N → A11)
- **Not Exists Support**: Handles "Not Exists" in TOTAL row cells
- **IBC Format Support**: Parses `>>>IBC` command format (alternative to FBC)
- **Mixed-Case Robustness**: Case-insensitive regex for all patterns

---

## 🔄 Live Comparison Engine

### Comparison Workflow

```
┌──────────────────────────────────────────────────────────────────┐
│ 1. User Clicks "Compare Live" or Auto-Refresh Triggers          │
└──────────────────────────────────────────────────────────────────┘
                            ↓
┌──────────────────────────────────────────────────────────────────┐
│ 2. NodeScanWidget Creates ComparisonWorker (QThread)            │
│    - Passes: node, token, file_content, services                │
│    - Emits: status_message("Comparing {node} ({file})...", 5000)│
└──────────────────────────────────────────────────────────────────┘
                            ↓
┌──────────────────────────────────────────────────────────────────┐
│ 3. ComparisonWorker.run() in Background Thread                  │
│    a. Check telnet connection (auto-connect if needed)          │
│    b. Execute FBC command: "FBC {token}\n"                       │
│    c. Wait for command completion (max 30s timeout)             │
│    d. Parse telnet output with FbcParserService                  │
│    e. Compare file vs live cell-by-cell                          │
│    f. Emit finished(ComparisonResult)                            │
└──────────────────────────────────────────────────────────────────┘
                            ↓
┌──────────────────────────────────────────────────────────────────┐
│ 4. NodeScanWidget._on_comparison_finished(result)               │
│    a. Update table cell colors (green/yellow)                    │
│    b. Calculate match percentage                                 │
│    c. Emit status_message:                                       │
│       - Success: "✓ {node}: 75% match (12/16 cells)"            │
│       - Failure: "✗ {node}: {error_message}"                     │
└──────────────────────────────────────────────────────────────────┘
```

### Telnet Integration

**Auto-Connect Logic**:
- Check `telnet_service.is_connected()` before comparison
- If disconnected, call `telnet_service.connect(node.ip, node.port)`
- Wait for connection establishment (max 10s timeout)
- Proceed with FBC command execution

**Command Execution**:
- Send command: `telnet_service.send_command(f"FBC {token}\n")`
- Wait for completion: Poll for ">" prompt or timeout (30s)
- Capture output: Multi-line response buffer
- Parse response: Extract table content between header and prompt

**Error Handling**:
- Connection timeout → `ComparisonResult(success=False, error_message="Connection timeout")`
- Command timeout → `ComparisonResult(success=False, error_message="Command timeout")`
- Parse error → `ComparisonResult(success=False, error_message="Parse error: {details}")`

---

## ⏱️ Auto-Refresh Management

### Configuration

**User Controls**:
- **Enable Checkbox**: Master switch for auto-refresh
- **Interval Dropdown**: 5s, 10s, 30s, 60s options
- **Compare Live Button**: Manual trigger (disables auto-refresh temporarily)

**Timer Mechanism**:
- `QTimer` with interval from dropdown selection
- Countdown display: "Next comparison in 5s"
- Resets after each comparison completion
- Stops when disabled or manual compare clicked

### State Transitions

```
[Disabled] ──checkbox→ [Enabled] ──manual compare→ [Disabled]
     ↑                      ↓
     └─────uncheck──────────┘

[Enabled] ──tab switch away→ [Paused] ──tab switch back→ [Enabled]
     ↑                           ↓
     └───────manual stop─────────┘
```

**State Variables**:
- `_auto_refresh_enabled`: Checkbox state (user-controlled)
- `_auto_refresh_paused`: Tab switching flag (Phase 4, system-controlled)

---

## 🔀 Tab-Aware Pause System (Phase 4)

### Problem

Auto-refresh continues executing telnet commands even when user switches to different tabs, causing:
- Unnecessary network traffic
- Command queue congestion
- Confusing status messages (comparisons happening off-screen)

### Solution

**Two-Level Pause Logic**:

**Level 1: Main Tab Switching (SessionView)**
```python
def _on_main_tab_changed(index):
    if current_tab is scan_tab:
        scan_tab.resume_active_auto_refresh()  # Returning to Scan tab
    else:
        scan_tab.pause_all_auto_refresh()      # Leaving Scan tab
```

**Level 2: Node Subtab Switching (ScanTab)**
```python
def _on_node_tab_changed(index):
    self.pause_all_auto_refresh()              # Pause all widgets
    if index >= 0:
        active_widget = self.node_tabs.widget(index)
        active_widget.resume_auto_refresh()    # Resume only active widget
```

### Implementation Details

**pause_auto_refresh()**:
- Sets `_auto_refresh_paused = True`
- Stops QTimer (if running)
- Preserves `_auto_refresh_enabled` (checkbox state)
- Idempotent (safe to call multiple times)

**resume_auto_refresh()**:
- Sets `_auto_refresh_paused = False`
- Restarts QTimer (if checkbox enabled)
- Does nothing if checkbox unchecked
- Idempotent (safe to call multiple times)

**is_auto_refresh_active()**:
- Returns `_auto_refresh_enabled and not _auto_refresh_paused`
- Used for UI state checks and debugging

---

## 📢 Status Message Propagation (Phase 4)

### Signal Chain

```
NodeScanWidget
    ↓ (emit status_message)
ScanTab
    ↓ (forward status_message via signal)
CommanderWindow
    ↓ (connect to status_service.show_message)
Status Bar
    ↓ (display message with timeout)
User Sees Message
```

### Message Types

| Event | Message Format | Duration |
|-------|---------------|----------|
| Comparison Start | `"Comparing {node} ({file})..."` | 5000ms |
| Comparison Success | `"✓ {node}: 75% match (12/16 cells)"` | 5000ms |
| Comparison Failure | `"✗ {node}: {error_message}"` | 5000ms |

**Implementation**:
```python
# In NodeScanWidget
self.status_message = pyqtSignal(str, int)

# On comparison start
self.status_message.emit(f"Comparing {node_name} ({filename})...", 5000)

# On comparison success
match_pct = 100 * (1 - len(differences) / total_cells)
matched = total_cells - len(differences)
self.status_message.emit(f"✓ {node_name}: {match_pct:.0f}% match ({matched}/{total_cells} cells)", 5000)

# On comparison failure
self.status_message.emit(f"✗ {node_name}: {error_message}", 5000)
```

**Signal Forwarding (ScanTab)**:
```python
# In ScanTab.__init__()
self.status_message = pyqtSignal(str, int)

# When creating NodeScanWidget
node_widget.status_message.connect(self.status_message.emit)
```

**Signal Connection (CommanderWindow)**:
```python
# In CommanderWindow.init_ui()
self.session_view.scan_tab.status_message.connect(
    self.status_service.show_message
)
```

---

## 📊 Data Flow

### File Loading Flow

```
User Selects File
    ↓
NodeScanWidget.load_token_file(path)
    ↓
FbcParserService.parse_file(path)
    ↓
FbcTableData (headers, rows, totals, metadata)
    ↓
QTableWidget Population (with dark theme styling)
    ↓
Display to User
```

### Live Comparison Flow

```
User Clicks Compare / Auto-Refresh Triggers
    ↓
NodeScanWidget._on_compare_clicked()
    ↓
ComparisonWorker (QThread)
    ├─→ TelnetService.connect(node) [if needed]
    ├─→ TelnetService.send_command(f"FBC {token}")
    ├─→ FbcParserService.parse_content(telnet_output)
    └─→ FbcComparisonService.compare_fbc_live(...)
            ↓
        ComparisonResult
            ↓
NodeScanWidget._on_comparison_finished(result)
    ├─→ Update table colors (green/yellow)
    ├─→ Calculate match percentage
    └─→ Emit status_message
            ↓
        Status Bar Display
```

### Auto-Refresh Flow

```
User Enables Auto-Refresh + Selects Interval
    ↓
NodeScanWidget._on_auto_refresh_toggled(checked=True)
    ↓
QTimer.start(interval_ms)
    ↓
[Wait interval seconds]
    ↓
QTimer.timeout() → _on_auto_refresh_triggered()
    ↓
_on_compare_clicked() [same as manual compare]
    ↓
[Comparison executes]
    ↓
QTimer.restart() [cycle repeats]
```

### Tab Switching Flow

```
User Switches to Different Tab (Telnet/BsTool)
    ↓
SessionView._on_main_tab_changed(new_index)
    ↓
scan_tab.pause_all_auto_refresh()
    ↓
For each NodeScanWidget:
    widget.pause_auto_refresh()
        ↓
    _auto_refresh_paused = True
    QTimer.stop()
    [Preserves checkbox state]

User Returns to Scan Tab
    ↓
SessionView._on_main_tab_changed(scan_index)
    ↓
scan_tab.resume_active_auto_refresh()
    ↓
active_widget.resume_auto_refresh()
    ↓
_auto_refresh_paused = False
QTimer.start() [if checkbox enabled]
```

---

## 🧪 Testing Coverage

### Test Suites

| Test File | Tests | Coverage |
|-----------|-------|----------|
| `test_fbc_parser_service.py` | 29 | File parsing, metadata, edge cases |
| `test_fbc_comparison_service.py` | 18 | Live comparison, auto-refresh, parser fixes |
| `test_auto_refresh_tab_switch.py` | 10 | Pause/resume logic, tab switching |
| `test_status_message_propagation.py` | 5 | Signal chain, message forwarding |

**Total**: 62 tests, 100% passing

### Test Categories

**Unit Tests**:
- Parser regex patterns (FBC/RPC formats)
- Comparison result calculation
- Auto-refresh state transitions
- Signal emission verification

**Integration Tests**:
- Multi-level tab switching (main tabs + node subtabs)
- End-to-end signal propagation (NodeScanWidget → Status Bar)
- Telnet command execution with live parsing
- Auto-connect on comparison start

**Edge Cases**:
- PIC 0 separator handling
- N suffix stripping
- Not Exists cell values
- IBC format parsing
- Mixed-case robustness

---

## 📚 Related Documentation

- **Technical Guide**: [TECH_scan_tab_usage.md](../technical/TECH_scan_tab_usage.md) - Detailed API reference and usage guide
- **Blueprints**: [BLUEPRINT_scan_tab_v1.md](../blueprints/BLUEPRINT_scan_tab_v1.md), [BLUEPRINT_scan_tab_phase3.md](../blueprints/BLUEPRINT_scan_tab_phase3.md)
- **Node System**: [ARCH_node_system.md](ARCH_node_system.md) - Node management and configuration
- **Command System**: [ARCH_command_system.md](ARCH_command_system.md) - Telnet command execution
- **Changelog**: [CHANGELOG.md](../../CHANGELOG.md) - Phase 1, 3+4 release notes

---

## 🔮 Future Enhancements

### Phase 2: Enhanced Table Styling (Deferred)
- Column width optimization for I/O unit names
- Tooltip support for truncated cell values
- Improved header styling (bold fonts, better spacing)

### Phase 4.2: Config Change Auto-Refresh (Blocked)
- Auto-refresh when node configuration changes
- **Blocker**: NodeManager lacks change notification signals
- **Workaround**: Manual re-scan or restart required

### Phase 4.3: Enhanced Error Handling (Sufficient)
- Connection failure recovery (circuit breaker pattern)
- Command timeout handling (30s default with retries)
- Malformed response parsing (graceful degradation to raw display)
- **Status**: Basic error handling sufficient for current usage

---

**Document Version**: 2.0  
**Status**: Active  
**Last Updated**: 2025-10-15  
**Phase**: 3+4 Complete
