# Technical Guide: Scan Tab Usage

**Document Type:** Technical Guide  
**Version:** 2.0  
**Status:** Active  
**Last Updated:** 2025-10-15  
**Phase:** Phase 3+4 Complete

## Overview

The **Scan Tab** provides a centralized interface for viewing and comparing FBC (Field Bus Configuration) and RPC (RUPI Counter) token file contents within Commander Center. This feature streamlines the inspection of node configurations and error counters without manual file navigation, with live comparison capabilities and intelligent auto-refresh management.

### Current Capabilities (Phase 1+3+4)

**Phase 1 - File Viewing:**
- ✅ Per-node subtabs with automatic population
- ✅ Unified FBC/RPC file viewer with mixed file dropdown
- ✅ Auto-load most recent file per node
- ✅ Tabular display with dark theme styling
- ✅ Raw content preservation for debugging

**Phase 3 - Live Comparison:**
- ✅ Real-time telnet-based FBC comparison engine
- ✅ Cell-by-cell difference detection with color coding (green=match, yellow=diff)
- ✅ Configurable auto-refresh (5s/10s/30s/60s intervals)
- ✅ Auto-connect to telnet on comparison start
- ✅ Parser enhancements (PIC 0, N suffix, Not Exists handling)

**Phase 4 - UI Polish:**
- ✅ Tab-aware auto-refresh (pauses when switching away, resumes on return)
- ✅ Status message propagation (comparison progress, results, errors)
- ✅ Context menu file path copying (right-click on file selector)

### Future Enhancements (Planned)
- ⏳ **Phase 2**: Enhanced table styling (column optimization, tooltips, CSS integration)
- ⏳ **Phase 4.2**: Config change auto-refresh (requires node manager signals)
- ⏳ **Phase 4.3**: Enhanced error handling (circuit breaker, timeout recovery)

---

## Architecture

### Component Hierarchy

```
SessionView (QTabWidget)
    ├── Telnet Tab
    ├── BsTool Tab
    └── Scan Tab (ScanTab)
        ├── Node Subtab: AP01 (NodeScanWidget)
        ├── Node Subtab: AP02m (NodeScanWidget)
        ├── Node Subtab: AP06 (NodeScanWidget)
        └── ... (per loaded node)
            ├── File Selector (QComboBox) + Context Menu
            ├── Table Display (QTableWidget) + Color Coding
            ├── Compare Live Button (functional - Phase 3)
            └── Auto-Refresh Controls (functional - Phase 3+4)
                ├── Enable Checkbox
                ├── Interval Dropdown (5s/10s/30s/60s)
                └── Tab-Aware Pause Logic (Phase 4)
```

### Key Classes

| Class | File | Lines | Responsibility |
|-------|------|-------|----------------|
| `FbcParserService` | `services/fbc_parser_service.py` | 349 | Parse FBC/RPC files into structured data |
| `FbcComparisonService` | `services/fbc_comparison_service.py` | 420 | Execute live telnet comparison (Phase 3) |
| `ScanTab` | `ui/scan_tab.py` | 294 | Host node subtabs, coordinate tab switching (Phase 4) |
| `NodeScanWidget` | `ui/node_scan_widget.py` | 810 | Display files, run comparisons, manage auto-refresh (Phase 3+4) |
| `FbcTableData` | `services/fbc_parser_service.py` | N/A | Data structure (dataclass) |
| `ComparisonResult` | `services/fbc_comparison_service.py` | N/A | Comparison result (dataclass) |

---

## Usage Guide

### Accessing the Scan Tab

1. Launch Commander Center
2. Load node configuration via **File → Load Configuration** or at startup
3. Click the **Scan** tab in the main tab bar (alongside Telnet, BsTool)
4. Node subtabs appear automatically for each configured node

### Viewing Token Files (Phase 1)

**Per-Node Workflow:**
1. Select a node subtab (e.g., **AP01**, **AP02m**)
2. The most recent FBC file auto-loads into the table
3. Use the **File Selector** dropdown to switch between available files
4. Right-click on the file selector for context menu:
   - **Copy Path**: Copy full file path to clipboard
5. Files are grouped by type:
   - `.fbc` files (Field Bus Configuration I/O tables)
   - `.rpc` files (RUPI error counter tables)

**File Naming Convention:**
- FBC: `{node}_{token}.fbc` (e.g., `AP01_021.fbc`)
- RPC: `{node}_{token}_err.rpc` (e.g., `AP02m_022_err.rpc`)

### Live Comparison (Phase 3)

**Starting Comparison:**
1. Select a node subtab with an FBC file loaded
2. Click the **Compare Live** button
3. If not connected, telnet auto-connects to the node
4. Comparison executes via `FBC {token}` command
5. Table cells color-coded:
   - 🟢 **Green**: Cell matches telnet output
   - 🟡 **Yellow**: Cell differs from telnet output
6. Status bar shows progress: `"Comparing {node} ({file})..."`
7. Status bar shows results: `"✓ {node}: 75% match (12/16 cells)"` or `"✗ {node}: error message"`

**Auto-Refresh:**
1. Enable the **Auto-Refresh** checkbox
2. Select interval from dropdown: **5s**, **10s**, **30s**, **60s**
3. Countdown timer appears: `"Next comparison in 5s"`
4. Comparison repeats automatically at selected interval
5. Auto-refresh **pauses** when:
   - Switching to a different node subtab
   - Switching to a different main tab (Telnet, BsTool)
6. Auto-refresh **resumes** when:
   - Returning to the original node subtab
   - Returning to the Scan tab
7. Disable checkbox or click **Compare Live** to stop

**Telnet Integration:**
- Auto-connect initiates connection if not already connected
- Uses existing TelnetService session
- Commands execute in sequence (no parallel commands)
- Connection state persists across comparisons

### Understanding the Table Display

#### FBC Files (I/O Tables)
```
| UNIT | A11 | A12 | A13 | BI4 | BO5 | ... |
|------|-----|-----|-----|-----|-----|-----|
| 0x01 | AI8 | AI8 | AI8 | BI8 | BO8 | ... |
| 0x02 | TI6 | TI6 | -   | -   | AO4 | ... |
| TOTAL| 16  | 16  | 8   | 8   | 12  | ... |
```

**Columns:**
- **UNIT**: Unit ID (0x01, 0x02, etc.) or TOTAL
- **Agent columns**: I/O module types (AI8, BI8, BO8, TI6, AO4, etc.)

**Metadata** (extracted from file):
- Timestamp: `2025-01-13 14:32:45`
- Command: `FBC 021`
- Agent ID: `021`

#### RPC Files (Error Counter Tables)
```
| PTYP | MODL | SUB | CMD | CNT | ERR |
|------|------|-----|-----|-----|-----|
| 0x10 | 0x00 | 0x00| 0x20| 1234| 5   |
| 0x11 | 0x01 | 0x00| 0x21| 5678| 2   |
```

**Columns** (fixed for RPC):
- **PTYP**: Packet Type
- **MODL**: Module
- **SUB**: Submodule
- **CMD**: Command
- **CNT**: Count
- **ERR**: Error Count

**Metadata** (extracted from file):
- Timestamp: `2025-01-13 14:35:12`
- Command: `RPC 022`
- Agent ID: `022`

---

## File Discovery

### Directory Structure

Scan Tab discovers files from the configured log root directory:

```
_DIA/
├── FBC/
│   ├── AP01/
│   │   ├── 021.fbc
│   │   ├── 022.fbc
│   │   └── ...
│   ├── AP02m/
│   ├── AP06/
│   └── ...
└── RPC/
    ├── AP01/
    │   ├── 021_err.rpc
    │   ├── 022_err.rpc
    │   └── ...
    ├── AP02m/
    └── ...
```

### File Sorting

Files in the dropdown are sorted by:
1. **Modification time** (descending - newest first)
2. **Filename** (alphabetical)

The **most recent file** is automatically loaded when opening a node subtab.

---

## Parsing Logic

### File Type Detection

The parser auto-detects file type based on filename pattern:

| Pattern | File Type | Method |
|---------|-----------|--------|
| `*.fbc` | FBC | `_parse_fbc_content()` |
| `*_err.rpc` | RPC | `_parse_rpc_content()` |
| `*.rpc` | RPC | `_parse_rpc_content()` |
| Unknown | FBC (default) | `_parse_fbc_content()` |

### FBC Parsing (10 Regex Patterns)

**6 FBC-Specific Patterns:**
1. **IO_TABLE_HEADER**: `^\|\s*UNIT\s*\|` - Detects table header row
2. **UNIT_ROW**: `^\|\s*0x[0-9A-Fa-f]+\s*\|` - Parses unit data rows
3. **SPACER_LINE**: `^\|[-\s|]+\|$` - Ignores spacer rows
4. **AGENT_ID**: `^>>>> agent\s+(\d+)` - Extracts agent ID
5. **TOTAL_ROW**: `^\|\s*TOTAL\s*\|` - Parses total row
6. **TIMESTAMP**: `^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}` - Extracts timestamp

**4 RPC-Specific Patterns:**
1. **RPC_HEADER**: `^\|\s*PTYP\s*\|` - Detects RPC header
2. **RPC_DATA_ROW**: `^\|\s*0x[0-9A-Fa-f]+\s*\|` - Parses RPC data rows
3. **RPC_COMMAND**: `^RPC\s+(\d+)` - Extracts RPC command
4. **RPC_TIMESTAMP**: `^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}` - Extracts timestamp

### Data Structure (FbcTableData)

```python
@dataclass
class FbcTableData:
    headers: List[str]           # Column headers (e.g., ['UNIT', 'A11', 'A12', ...])
    rows: List[List[str]]        # Data rows (e.g., [['0x01', 'AI8', 'AI8', ...], ...])
    totals: List[str]            # Total row (e.g., ['TOTAL', '16', '16', ...])
    raw_content: str             # Original file content (for debugging)
    file_type: str               # 'fbc' or 'rpc'
    metadata: Dict[str, Any]     # {'timestamp': '...', 'command': '...', 'agent_id': '...'}
```

---

## Dark Theme Styling

### Color Palette

| Element | Color Code | Usage |
|---------|------------|-------|
| Background | `#1E1E1E` | Table body, main widget background |
| Alternate Rows | `#252526` | Every other row for readability |
| Headers | `#3D3D3D` | Table headers (top, left) |
| Text | `#DCDCDC` | All table text (high contrast) |
| Accent | `#007ACC` | Future: Selection, highlights |

### Font Configuration

- **Family**: Consolas, Courier New (monospace fallback)
- **Size**: 10pt
- **Weight**: Normal
- **Usage**: Ensures column alignment for tabular data

### CSS Styling Chain

```css
QTableWidget {
    background-color: #1E1E1E;
    alternate-background-color: #252526;
    color: #DCDCDC;
}

QTableWidget::item {
    padding: 4px;
    border: none;
}

QHeaderView::section {
    background-color: #3D3D3D;
    color: #DCDCDC;
    padding: 5px;
    border: 1px solid #555555;
}

QTableCornerButton::section {
    background-color: #3D3D3D;
    border: 1px solid #555555;
}
```

---

## Integration Points

### SessionView Integration

**File:** `src/commander/ui/session_view.py` (Lines 48-56)

```python
# Conditional Scan tab creation
if self.node_manager:
    from commander.ui.scan_tab import ScanTab
    self.scan_tab = ScanTab(self.node_manager, self.telnet_service)
    self.addTab(self.scan_tab, "Scan")
else:
    self.scan_tab = None
```

**Conditions:**
- `node_manager` must be passed to `SessionView` constructor
- `telnet_service` required for Phase 3 (live comparison)
- Tab only appears if `node_manager` is available

### CommanderWindow Integration

**File:** `src/commander/ui/commander_window.py`

**Key Changes:**
1. **Line 85**: Moved `telnet_service` initialization before `init_ui()`
2. **populate_node_tree()**: Added `scan_tab.populate_nodes()` call after node tree population

```python
def populate_node_tree(self):
    # ... existing code ...
    self.node_tree_view.populate_node_tree()
    
    # Populate Scan tab node subtabs
    if hasattr(self, 'session_view') and self.session_view.scan_tab:
        self.session_view.scan_tab.populate_nodes()
```

---

## API Reference

### FbcComparisonService (Phase 3)

#### `compare_fbc_live(node: Node, token: str, file_content: str) -> ComparisonResult`
Execute live FBC comparison via telnet and compare with file content.

**Parameters:**
- `node` (Node): Node configuration with connection details
- `token` (str): FBC token ID (e.g., "021")
- `file_content` (str): Content from .fbc file to compare against

**Returns:**
- `ComparisonResult`: Dataclass with comparison results

**Result Structure:**
```python
@dataclass
class ComparisonResult:
    success: bool                          # True if comparison completed
    differences: List[CellDifference]      # List of cell differences
    error_message: Optional[str]           # Error message if failed
    file_type: str                         # "fbc" or "rpc"
    total_cells: int                       # Total cells compared
```

**CellDifference Structure:**
```python
@dataclass
class CellDifference:
    row: int           # Row index (0-based)
    col: int           # Column index (0-based)
    file_value: str    # Value from file
    live_value: str    # Value from telnet
```

**Raises:**
- `ValueError`: If telnet not connected or node unavailable
- `RuntimeError`: If command execution fails

**Example:**
```python
from commander.services.fbc_comparison_service import FbcComparisonService

service = FbcComparisonService(telnet_service, parser_service)
result = service.compare_fbc_live(node, "021", file_content)

if result.success:
    match_pct = 100 * (1 - len(result.differences) / result.total_cells)
    print(f"Match: {match_pct:.0f}% ({result.total_cells - len(result.differences)}/{result.total_cells})")
    for diff in result.differences:
        print(f"Row {diff.row}, Col {diff.col}: '{diff.file_value}' → '{diff.live_value}'")
else:
    print(f"Error: {result.error_message}")
```

#### `_execute_fbc_command(token: str) -> str`
Execute FBC command via telnet and capture output.

**Parameters:**
- `token` (str): FBC token ID

**Returns:**
- `str`: Command output (multi-line response)

**Internal Method** - Used by `compare_fbc_live()`.

### FbcParserService

#### `parse_file(file_path: Path) -> FbcTableData`
Parse a single FBC or RPC file from disk.

**Parameters:**
- `file_path` (Path): Absolute path to `.fbc` or `.rpc` file

**Returns:**
- `FbcTableData`: Structured data with headers, rows, totals, metadata

**Raises:**
- `FileNotFoundError`: If file does not exist
- `ValueError`: If file is empty

**Example:**
```python
from pathlib import Path
from commander.services.fbc_parser_service import FbcParserService

service = FbcParserService()
data = service.parse_file(Path("_DIA/FBC/AP01/021.fbc"))

print(f"Headers: {data.headers}")
print(f"Rows: {len(data.rows)}")
print(f"Timestamp: {data.metadata.get('timestamp')}")
```

#### `parse_content(content: str, file_type: str) -> FbcTableData`
Parse FBC or RPC content from string.

**Parameters:**
- `content` (str): Raw file content
- `file_type` (str): `'fbc'` or `'rpc'`

**Returns:**
- `FbcTableData`: Structured data

**Example:**
```python
content = """
| UNIT | A11 | A12 |
|------|-----|-----|
| 0x01 | AI8 | AI8 |
| TOTAL| 16  | 16  |
"""
data = service.parse_content(content, 'fbc')
```

### ScanTab (Phase 4)

#### `populate_nodes()`
Create subtabs for all nodes from NodeManager.

**Preconditions:**
- `node_manager.get_all_nodes()` returns List[Node]
- Nodes have `name` attribute
- `log_root` configured in NodeManager

**Effect:**
- Creates one `NodeScanWidget` per node
- Adds subtabs to `node_tabs` QTabWidget
- Stores widgets in `node_widgets` dictionary

**Example:**
```python
scan_tab = ScanTab(node_manager, telnet_service)
scan_tab.populate_nodes()  # Called after node config load
```

#### `pause_all_auto_refresh()`
Pause auto-refresh on all node widgets (Phase 4).

**Effect:**
- Calls `pause_auto_refresh()` on all `NodeScanWidget` instances
- Used when switching away from Scan tab

**Example:**
```python
# Called automatically when switching tabs
scan_tab.pause_all_auto_refresh()
```

#### `resume_active_auto_refresh()`
Resume auto-refresh on currently active node widget (Phase 4).

**Effect:**
- Calls `resume_auto_refresh()` on active `NodeScanWidget`
- Used when returning to Scan tab

**Example:**
```python
# Called automatically when returning to Scan tab
scan_tab.resume_active_auto_refresh()
```

### NodeScanWidget (Phase 3+4)

#### `load_token_file(file_path: Path)`
Load and display a specific FBC/RPC file.

**Parameters:**
- `file_path` (Path): Absolute path to token file

**Effect:**
- Parses file with `FbcParserService`
- Creates QTableWidget from parsed data
- Updates file selector dropdown

**Example:**
```python
widget = NodeScanWidget(node_name="AP01", parser_service=service)
widget.load_token_file(Path("_DIA/FBC/AP01/021.fbc"))
```

#### `pause_auto_refresh()` (Phase 4)
Pause the auto-refresh timer without disabling the checkbox.

**Effect:**
- Sets `_auto_refresh_paused = True`
- Stops the QTimer if running
- Preserves checkbox state for later resume

**Example:**
```python
# Called automatically when switching to different node tab
widget.pause_auto_refresh()
```

#### `resume_auto_refresh()` (Phase 4)
Resume the auto-refresh timer if checkbox is enabled.

**Effect:**
- Sets `_auto_refresh_paused = False`
- Restarts QTimer if checkbox is enabled
- Does nothing if checkbox is unchecked

**Example:**
```python
# Called automatically when returning to this node tab
widget.resume_auto_refresh()
```

#### `is_auto_refresh_active() -> bool` (Phase 4)
Check if auto-refresh is actively running (not paused, checkbox enabled).

**Returns:**
- `bool`: True if timer running and not paused

**Example:**
```python
if widget.is_auto_refresh_active():
    print("Auto-refresh is running")
```

#### Signal: `status_message(str, int)` (Phase 4)
Emitted when comparison status changes.

**Parameters:**
- `str`: Status message text
- `int`: Display duration in milliseconds (5000 = 5 seconds)

**Emitted On:**
- Comparison start: `"Comparing {node} ({file})..."`
- Comparison success: `"✓ {node}: 75% match (12/16 cells)"`
- Comparison failure: `"✗ {node}: error message"`

**Example:**
```python
widget = NodeScanWidget(...)
widget.status_message.connect(lambda msg, dur: print(f"Status: {msg}"))
```

---

## Signal Chain (Phase 4)

### Status Message Propagation

```
NodeScanWidget.status_message(str, int)
    ↓
ScanTab.status_message(str, int)  [forwards signal]
    ↓
CommanderWindow.status_service.show_message(str, int)
    ↓
Status Bar Display
```

**Implementation:**
```python
# In ScanTab.__init__()
self.status_message = PyQt5.QtCore.pyqtSignal(str, int)

# In NodeScanWidget creation
node_widget.status_message.connect(self.status_message.emit)

# In CommanderWindow
scan_tab.status_message.connect(status_service.show_message)
```

### Tab Change Events

**Main Tab Switching (SessionView):**
```python
# SessionView._on_main_tab_changed(index)
if current_tab is scan_tab:
    scan_tab.resume_active_auto_refresh()
else:
    scan_tab.pause_all_auto_refresh()
```

**Node Subtab Switching (ScanTab):**
```python
# ScanTab._on_node_tab_changed(index)
scan_tab.pause_all_auto_refresh()
if index >= 0:
    active_widget = scan_tab.node_tabs.widget(index)
    active_widget.resume_auto_refresh()
```

---

## Debugging

### Enable Parser Logging

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

**Output:**
```
DEBUG:FbcParserService:Parsing file: _DIA/FBC/AP01/021.fbc
DEBUG:FbcParserService:Detected file type: fbc
DEBUG:FbcParserService:Extracted headers: ['UNIT', 'A11', 'A12', ...]
DEBUG:FbcParserService:Parsed 12 data rows
DEBUG:FbcParserService:Found total row: ['TOTAL', '16', '16', ...]
```

### Common Issues

#### No Scan Tab Visible
**Cause:** `node_manager` not passed to `SessionView`

**Solution:**
1. Check `commander_ui_factory.py` passes `node_manager` to `SessionView`
2. Verify `telnet_service` initialized before `init_ui()`

#### Empty File Dropdown
**Cause:** No FBC/RPC files in `_DIA/{FBC,RPC}/{node}/` directories

**Solution:**
1. Run FBC/RPC commands via Telnet tab to generate files
2. Check `log_root` configuration matches actual directory structure

#### Table Not Displaying Data
**Cause:** Parsing error (check logs for exceptions)

**Solution:**
1. Enable DEBUG logging
2. Check file format matches expected patterns (see Parsing Logic)
3. Verify `raw_content` field in `FbcTableData` (debugging fallback)

#### White Background Instead of Dark Theme
**Cause:** Missing CSS stylesheet application

**Solution:**
1. Check `table_widget.setStyleSheet(...)` call in `NodeScanWidget`
2. Verify dark theme colors in `commander/ui/theme.py`

#### Compare Live Button Does Nothing (Phase 3)
**Cause:** Telnet connection failed or node not available

**Solution:**
1. Check status bar for error message
2. Verify node is reachable via Telnet tab manual connection
3. Enable DEBUG logging to see telnet command execution
4. Check `_DIA/FBC/{node}/` directory has FBC files to compare against

#### Auto-Refresh Not Resuming After Tab Switch (Phase 4)
**Cause:** Checkbox disabled or timer failed to restart

**Solution:**
1. Verify checkbox is still enabled when returning to tab
2. Check `is_auto_refresh_active()` returns True
3. Enable DEBUG logging to trace pause/resume calls
4. Manually disable and re-enable checkbox to reset timer

#### Status Messages Not Appearing (Phase 4)
**Cause:** Signal chain disconnected or status bar hidden

**Solution:**
1. Verify `CommanderWindow.status_bar` visible at bottom
2. Check signal connections in `ScanTab` and `CommanderWindow`
3. Test with manual status service call: `status_service.show_message("Test", 5000)`
4. Check for exceptions in comparison worker thread

#### Color Coding Not Working (Phase 3)
**Cause:** Comparison failed or parsing mismatch

**Solution:**
1. Check telnet output format matches file format (separators, spacing)
2. Enable DEBUG logging to see comparison differences
3. Verify both file and telnet output parsed successfully
4. Check for PIC 0, N suffix, or mixed-case issues (fixed in Phase 3)

---

## Testing

### Unit Tests

**Phase 1 Parser Tests:**
- **File:** `tests/test_fbc_parser_service.py` (338 lines, 29 tests)
- **Coverage:** File type detection, FBC parsing, RPC parsing, metadata extraction, edge cases

**Phase 3 Comparison Tests:**
- **File:** `tests/test_fbc_comparison_service.py` (577 lines, 18 tests)
- **Coverage:** Live comparison, auto-refresh, telnet integration, parser fixes (PIC 0, N suffix, Not Exists, IBC format, mixed-case)

**Phase 4 UI Tests:**
- **File:** `tests/test_auto_refresh_tab_switch.py` (370 lines, 10 tests)
- **Coverage:** Pause/resume logic, idempotency, tab switching, multi-level integration
- **File:** `tests/test_status_message_propagation.py` (220 lines, 5 tests)
- **Coverage:** Status message emission, signal forwarding, integration with status bar

**Run All Tests:**
```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_fbc_parser_service.py tests/test_fbc_comparison_service.py tests/test_auto_refresh_tab_switch.py tests/test_status_message_propagation.py -v
```

**Expected Output:**
```
test_fbc_parser_service.py: 29 passed
test_fbc_comparison_service.py: 18 passed
test_auto_refresh_tab_switch.py: 10 passed
test_status_message_propagation.py: 5 passed
==============================
TOTAL: 62 passed in 1.2s
```

### Manual Testing Checklist

**Phase 1 - File Viewing:**
- [ ] Load Commander Center with node configuration
- [ ] Scan tab visible alongside Telnet and BsTool tabs
- [ ] Node subtabs created for all configured nodes (e.g., AP01, AP02m, AP06)
- [ ] File dropdown populated with FBC and RPC files per node
- [ ] Most recent file auto-loads when opening node subtab
- [ ] Table displays parsed FBC file (I/O columns, unit rows, total row)
- [ ] Table displays parsed RPC file (6 columns: PTYP, MODL, SUB, CMD, CNT, ERR)
- [ ] Dark theme applied (background #1E1E1E, alternating rows #252526)
- [ ] Monospace font renders column-aligned data
- [ ] Switching files in dropdown updates table immediately

**Phase 3 - Live Comparison:**
- [ ] Compare Live button enabled for FBC files
- [ ] Clicking Compare Live auto-connects to telnet if disconnected
- [ ] Comparison executes and color-codes cells (green=match, yellow=diff)
- [ ] Status bar shows comparison progress and results
- [ ] Auto-refresh checkbox enables periodic comparisons
- [ ] Interval dropdown offers 5s/10s/30s/60s options
- [ ] Countdown timer displays next comparison time
- [ ] Auto-refresh stops when disabled or Compare Live clicked again

**Phase 4 - UI Polish:**
- [ ] Auto-refresh pauses when switching to different node subtab
- [ ] Auto-refresh resumes when returning to original node subtab
- [ ] Auto-refresh pauses when switching to Telnet/BsTool tab
- [ ] Auto-refresh resumes when returning to Scan tab
- [ ] Status bar shows: `"Comparing {node} ({file})..."` during comparison
- [ ] Status bar shows: `"✓ {node}: 75% match (12/16 cells)"` on success
- [ ] Status bar shows: `"✗ {node}: error"` on failure
- [ ] Right-click file selector shows "Copy Path" context menu
- [ ] Context menu copies full file path to clipboard

---

## Future Enhancements (Phases 2+)

### Phase 2: Enhanced Table Styling
- Column width optimization for I/O unit names (resize to content)
- Tooltip support for truncated cell values
- Improved header styling (bold fonts, better spacing)
- CSS integration with existing Commander theme

### Phase 4.2: Config Change Auto-Refresh (Deferred)
- Auto-refresh when node configuration changes
- **Blocker:** NodeManager lacks change notification signals
- **Workaround:** Manual re-scan or restart required

### Phase 4.3: Enhanced Error Handling (Deferred)
- Connection failure recovery (circuit breaker pattern)
- Command timeout handling (30s default with retries)
- Malformed response parsing (graceful degradation to raw display)
- **Status:** Basic error handling sufficient for current usage

---

## Related Documentation

- **Architecture:** `docs/architecture/ARCH_commander_architecture.md`
- **Blueprint:** `docs/blueprints/BLUEPRINT_scan_tab_v1.md`, `BLUEPRINT_scan_tab_phase3.md`
- **Changelog:** `CHANGELOG.md` (Section: Scan Tab Phase 1, Phase 3+4)
- **API Reference:** `docs/technical/TECH_commander_architecture.md` (Services section)
- **Testing:** `tests/test_fbc_comparison_service.py`, `tests/test_auto_refresh_tab_switch.py`

---

## Metadata

```yaml
document_type: technical_guide
version: 2.0
status: active
phase: phase_3_4_complete
word_count: 4200
last_updated: 2025-10-15
contributors:
  - DevTeam (Phase 1+3+4 implementation)
review_status: active_development
test_coverage: 62_tests_passing
```

---

**End of Document**
