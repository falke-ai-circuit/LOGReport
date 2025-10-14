# Technical Guide: Scan Tab Usage

**Document Type:** Technical Guide  
**Version:** 1.0  
**Status:** Active  
**Last Updated:** 2025-10-14  
**Phase:** Phase 1 Complete

## Overview

The **Scan Tab** provides a centralized interface for viewing and comparing FBC (Field Bus Configuration) and RPC (RUPI Counter) token file contents within Commander Center. This feature streamlines the inspection of node configurations and error counters without manual file navigation.

### Phase 1 Capabilities (Current)
- ✅ Per-node subtabs with automatic population
- ✅ Unified FBC/RPC file viewer with mixed file dropdown
- ✅ Auto-load most recent file per node
- ✅ Tabular display with dark theme styling
- ✅ Raw content preservation for debugging

### Future Phases (Planned)
- ⏳ **Phase 2**: Enhanced table styling (column optimization, tooltips, CSS integration)
- ⏳ **Phase 3**: Live comparison engine (telnet integration, cell-by-cell comparison, color coding)
- ⏳ **Phase 4**: Error handling polish (connection recovery, timeout handling)

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
            ├── File Selector (QComboBox)
            ├── Table Display (QTableWidget)
            ├── Compare Live Button (disabled - Phase 3)
            └── Auto-Refresh Controls (disabled - Phase 2)
```

### Key Classes

| Class | File | Lines | Responsibility |
|-------|------|-------|----------------|
| `FbcParserService` | `services/fbc_parser_service.py` | 349 | Parse FBC/RPC files into structured data |
| `ScanTab` | `ui/scan_tab.py` | 161 | Host node subtabs, coordinate population |
| `NodeScanWidget` | `ui/node_scan_widget.py` | 455 | Display files for single node |
| `FbcTableData` | `services/fbc_parser_service.py` | N/A | Data structure (dataclass) |

---

## Usage Guide

### Accessing the Scan Tab

1. Launch Commander Center
2. Load node configuration via **File → Load Configuration** or at startup
3. Click the **Scan** tab in the main tab bar (alongside Telnet, BsTool)
4. Node subtabs appear automatically for each configured node

### Viewing Token Files

**Per-Node Workflow:**
1. Select a node subtab (e.g., **AP01**, **AP02m**)
2. The most recent FBC file auto-loads into the table
3. Use the **File Selector** dropdown to switch between available files
4. Files are grouped by type:
   - `.fbc` files (Field Bus Configuration I/O tables)
   - `.rpc` files (RUPI error counter tables)

**File Naming Convention:**
- FBC: `{node}_{token}.fbc` (e.g., `AP01_021.fbc`)
- RPC: `{node}_{token}_err.rpc` (e.g., `AP02m_022_err.rpc`)

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

### ScanTab

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

### NodeScanWidget

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

---

## Testing

### Unit Tests

**File:** `tests/test_fbc_parser_service.py` (338 lines, 29 tests)

**Coverage:**
- ✅ File type detection (3 tests)
- ✅ FBC parsing (6 tests)
- ✅ RPC parsing (5 tests)
- ✅ Metadata extraction (5 tests)
- ✅ Edge cases (6 tests)
- ✅ Real file integration (2 tests)
- ✅ Raw content preservation (2 tests)

**Run Tests:**
```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_fbc_parser_service.py -v
```

**Expected Output:**
```
29 passed, 1 warning in 0.21s
```

### Manual Testing Checklist

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
- [ ] Compare Live button disabled (Phase 3 placeholder)
- [ ] Auto-refresh checkbox disabled (Phase 2 placeholder)

---

## Future Enhancements (Phases 2-4)

### Phase 2: Enhanced Table Styling
- Column width optimization for I/O unit names (resize to content)
- Tooltip support for truncated cell values
- Improved header styling (bold fonts, better spacing)
- CSS integration with existing Commander theme

### Phase 3: Live Comparison Engine
- `FbcComparisonService` class for telnet-based comparison
- Command execution loop based on scan interval (5s, 10s, 30s, 60s)
- Cell-by-cell comparison with color coding:
  - 🟢 Green: Match
  - 🟡 Yellow: Difference
  - 🔴 Red: Error
- Auto-refresh countdown timer with pause/resume
- Enable "Compare Live" button functionality

### Phase 4: Error Handling Polish
- Connection failure recovery (circuit breaker pattern)
- Command timeout handling (30s default)
- Malformed response parsing (graceful degradation)
- User feedback improvements (status messages, progress indicators)

---

## Related Documentation

- **Architecture:** `docs/architecture/ARCH_commander_architecture.md`
- **Blueprint:** `docs/blueprints/BLUEPRINT_scan_tab_v1.md`
- **Changelog:** `CHANGELOG.md` (Section: Scan Tab Phase 1)
- **API Reference:** `docs/technical/TECH_commander_architecture.md` (Services section)

---

## Metadata

```yaml
document_type: technical_guide
version: 1.0
status: active
phase: phase_1_complete
word_count: 2847
last_updated: 2025-10-14
contributors:
  - DevTeam (Phase 1 implementation)
review_status: pending_peer_review
```

---

**End of Document**
