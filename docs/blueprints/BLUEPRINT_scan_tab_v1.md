# BLUEPRINT: Scan Tab Implementation v1.0

**Status**: Draft - Awaiting User Approval  
**Date**: 2025-10-14  
**Feature**: Scan Tab for FBC File Content Analysis and Live Comparison

---

## Executive Summary

The Scan Tab will add a new fourth tab to the Commander Center's session interface (alongside Telnet and BsTool tabs). It provides:

1. **Multi-Node Display**: Subtabs organized by node name (AP01m, AP02r, etc.)
2. **FBC Table Rendering**: Parsed .fbc file content displayed in tabular format
3. **Live Comparison**: Select FBC files and compare stored values against live telnet debugger data
4. **Visual Feedback**: Highlighted differences between file content and live system values

---

## Current System Analysis

### Existing Architecture

**Tab Structure** (`src/commander/ui/session_view.py`):
```
SessionView (QWidget)
  └── QTabWidget
       ├── TelnetTab (index 0)
       └── BsToolTab (index 1)
```

**FBC File Structure** (from `_DIA/FBC/AP01/AP01_192-168-0-11_162.fbc`):
```
Header:
  - Timestamp
  - Command executed: "print from fbc io structure {token}"
  
Content:
  - FBC Utilization Rate
  - Field Bus Configuration Table:
      PIC | 5 | 6 | 7 | 8 | ... | 20 | sum
      ----|---|---|---|---|-----|----|----- 
       0  | AI8 | BI8 | BO8 | ... |    | 15
       1  | AI8 | BI8 | BI8 | ... |    | 15
      ...
  - Total summary statistics
```

**RPC File Structure** (from `_DIA/RPC/AP01/AP01_192-168-0-11_162.rpc`):
```
Header:
  - Timestamp
  - Command executed: "print from fbc rupi counters {token}"
  
Content:
  - FIELD BUS error counters from RUPI(8344) from FBC agent {token}
  - Error Counters Table:
      pic | IREX ERROR | POLL ERROR | RESP FAIL | IREX COUNT | TIMEOUT
      ----|-----------|-----------|----------|-----------|--------
       0  |     0     |     0     |    0     |     0     |   14
       1  |     0     |     0     |    0     |     0     |   69
      ...
  - Unknown command count
```

**FBC Command Service** (`src/commander/services/fbc_command_service.py`):
- Generates command: `print from fbc io structure {token}0000`
- Queues commands via `CommandQueue`
- Routes output to files via `LogWriter`

**RPC Command Service** (`src/commander/services/rpc_command_service.py`):
- Generates command: `print from fbc rupi counters {token}0000`
- Queues commands via `CommandQueue`
- Routes output to files via `LogWriter`

**Telnet Service** (`src/commander/services/telnet_service.py`):
- Manages debugger connection
- Executes commands and returns output
- Handles system mode verification

---

## Requirements

### Functional Requirements

**FR1 - Node-Based Subtabs**
- Display one subtab per node (AP01m, AP02r, AL01, etc.)
- Auto-detect nodes from loaded configuration
- Support dynamic addition/removal as config changes

**FR2 - FBC/RPC Table Display**
- Parse .fbc and .rpc files and extract table structure
- Display Field Bus Configuration (FBC) or Error Counters (RPC) in tabular QTableWidget
- FBC: Show PIC numbers, I/O unit types (AI8, BI8, etc.), sum column
- RPC: Show PIC numbers, IREX ERROR, POLL ERROR, RESP FAIL, IREX COUNT, TIMEOUT columns
- Preserve original formatting and alignment
- Adapt table columns dynamically based on file type

**FR3 - File Selection**
- Dropdown to select .fbc or .rpc file for the current node
- Show all token files for selected node (162.fbc, 163.fbc, 182.rpc, etc.)
- Auto-load most recent file on node tab open
- Display currently loaded file metadata (timestamp, token, file type)
- File selection immediately loads and displays table (no separate "Load" button)

**FR4 - Live Comparison**
- Button: "Compare with Live System"
- Execute FBC/RPC command via telnet debugger for selected file
- Parse live output and compare with displayed table
- Highlight cells with differences (color-coded)
- Always compare entire table (all cells)

**FR5 - Auto-Refresh Monitoring**
- Checkbox: "Auto-refresh" to enable periodic comparison
- Dropdown: Selectable intervals (5s, 10s, 30s, 60s, 5min)
- Timer display showing next refresh countdown
- Pause/resume auto-refresh without disabling
- Visual indicator when auto-refresh is active

**FR6 - Visual Feedback**
- Green cells: Values match between file and live system
- Yellow cells: Values differ (show both values in tooltip)
- Red cells: Parse error or unavailable data
- White/default cells: Not yet compared
- Legend explaining color codes
- Match percentage indicator (e.g., "✓ 92% match")

### Non-Functional Requirements

**NFR1 - Performance**
- Parse .fbc files < 500ms
- Table rendering < 1s for typical FBC output
- Comparison execution < 5s (depends on telnet response)

**NFR2 - Usability**
- Consistent UI styling with existing tabs
- Clear error messages for parse failures
- Tooltips showing full cell values

**NFR3 - Maintainability**
- Modular parser for .fbc format
- Service-based architecture matching existing patterns
- Comprehensive unit tests (>80% coverage)

---

## Proposed Architecture

### Component Diagram

```
ScanTab (QWidget)
  ├── QTabWidget (node_subtabs)
  │    ├── NodeScanWidget (AP01m)
  │    │    ├── File Selection (QComboBox)
  │    │    ├── QTableWidget (fbc_table_view)
  │    │    ├── Compare Button (QPushButton)
  │    │    └── Status Label (QLabel)
  │    ├── NodeScanWidget (AP02r)
  │    └── ... (one per node)
  │
  └── Services (injected dependencies)
       ├── FbcParserService
       ├── FbcComparisonService
       └── TelnetService (existing)
```

### Class Structure

#### 1. **ScanTab** (Main UI Component)
```python
# src/commander/ui/scan_tab.py

class ScanTab(QWidget):
    """Main Scan tab widget hosting per-node subtabs"""
    
    # Signals
    comparison_started = pyqtSignal(str)  # node_name
    comparison_completed = pyqtSignal(str, dict)  # node_name, results
    status_message = pyqtSignal(str, int)  # message, duration
    
    def __init__(self, node_manager, telnet_service, parent=None):
        self.node_manager = node_manager
        self.telnet_service = telnet_service
        self.parser_service = FbcParserService()
        self.comparison_service = FbcComparisonService(telnet_service)
        self.node_widgets = {}  # {node_name: NodeScanWidget}
        
    def _setup_ui(self):
        """Create main tab widget and initialize node subtabs"""
        
    def populate_nodes(self):
        """Create subtab for each configured node"""
        
    def refresh_node_data(self, node_name: str):
        """Reload FBC files for specific node"""
```

#### 2. **NodeScanWidget** (Per-Node UI)
```python
# src/commander/ui/node_scan_widget.py

class NodeScanWidget(QWidget):
    """Widget displaying FBC/RPC data for a single node"""
    
    # Signals
    file_selected = pyqtSignal(str)  # file_path
    compare_requested = pyqtSignal()
    auto_refresh_toggled = pyqtSignal(bool)  # enabled
    refresh_interval_changed = pyqtSignal(int)  # seconds
    
    def __init__(self, node_name, token_files, parser_service):
        self.node_name = node_name
        self.token_files = token_files  # List of .fbc/.rpc file paths for this node
        self.parser_service = parser_service
        self.current_data = None  # Parsed FbcTableData
        self.auto_refresh_timer = QTimer()
        self.refresh_intervals = [5, 10, 30, 60, 300]  # seconds
        
    def _setup_ui(self):
        """Create file selector, table view, compare button, auto-refresh controls"""
        
    def load_token_file(self, file_path: str):
        """Parse and display .fbc or .rpc file in table"""
        
    def apply_comparison_results(self, results: Dict):
        """Highlight table cells based on comparison"""
        
    def start_auto_refresh(self, interval_seconds: int):
        """Start periodic comparison with selected interval"""
        
    def stop_auto_refresh(self):
        """Stop auto-refresh timer"""
        
    def _create_table_from_data(self, data: FbcTableData):
        """Populate QTableWidget from parsed data"""
```

#### 3. **FbcParserService** (Business Logic)
```python
# src/commander/services/fbc_parser_service.py

@dataclass
class FbcTableData:
    """Structured representation of FBC/RPC table"""
    timestamp: str
    command: str
    agent_id: str
    file_type: str  # 'FBC' or 'RPC'
    headers: List[str]  # Column headers: PIC, 5, 6, ...
    rows: List[Dict[str, str]]  # [{PIC: 0, 5: 'AI8', ...}]
    totals: Dict[str, Any]  # Summary statistics
    raw_content: str

class FbcParserService:
    """Service for parsing .fbc and .rpc file content"""
    
    def parse_file(self, file_path: str) -> FbcTableData:
        """Parse .fbc or .rpc file and extract structured data"""
        
    def parse_content(self, content: str, file_type: str = 'FBC') -> FbcTableData:
        """Parse FBC/RPC output string (from file or telnet)"""
        
    def _parse_table_section(self, lines: List[str]) -> List[Dict]:
        """Extract table rows with regex patterns"""
        
    def _parse_header(self, header_line: str) -> List[str]:
        """Extract column headers from table header line"""
        
    def _detect_file_type(self, file_path: str) -> str:
        """Determine file type from extension (.fbc or .rpc)"""
```

#### 4. **FbcComparisonService** (Comparison Logic)
```python
# src/commander/services/fbc_comparison_service.py

@dataclass
class CellComparison:
    """Result of comparing a single table cell"""
    row: int
    column: str
    file_value: str
    live_value: str
    matches: bool
    error: Optional[str] = None

class ComparisonResult:
    """Complete comparison result for a node"""
    node_name: str
    token_id: str
    timestamp: str
    comparisons: List[CellComparison]
    match_percentage: float
    
class FbcComparisonService(QObject):
    """Service for comparing FBC file data with live system"""
    
    # Signals
    comparison_progress = pyqtSignal(int, int)  # current, total
    
    def __init__(self, telnet_service, fbc_command_service):
        self.telnet_service = telnet_service
        self.fbc_command_service = fbc_command_service
        self.parser = FbcParserService()
        
    async def compare_with_live(
        self, 
        file_data: FbcTableData, 
        node_name: str, 
        token_id: str
    ) -> ComparisonResult:
        """Execute live FBC command and compare with file data"""
        
    def _execute_live_fbc_command(self, token_id: str) -> str:
        """Execute FBC command via telnet and return output"""
        
    def _compare_tables(
        self, 
        file_data: FbcTableData, 
        live_data: FbcTableData
    ) -> List[CellComparison]:
        """Cell-by-cell comparison of two FBC tables"""
```

---

## Data Flow

### Scenario 1: Loading FBC Files on Tab Open

```
User clicks "Scan" tab
    │
    ├─> ScanTab.populate_nodes()
    │    ├─> node_manager.get_all_nodes()
    │    └─> For each node:
    │         ├─> Scan _DIA/FBC/{node}/ for .fbc files
    │         ├─> Scan _DIA/RPC/{node}/ for .rpc files
    │         ├─> Create NodeScanWidget(node, token_files)
    │         └─> Add as subtab
    │
    └─> User selects node subtab (e.g., AP01m)
         │
         ├─> Auto-load most recent file from token_files
         │
         └─> NodeScanWidget.load_token_file(most_recent_file)
              ├─> FbcParserService.parse_file(path)
              ├─> Create QTableWidget with parsed data
              └─> Display in UI (cells default white/uncompared)
```

### Scenario 2: Comparing with Live System

```
User clicks "Compare with Live System" (or auto-refresh triggers)
    │
    ├─> NodeScanWidget.compare_requested signal
    │    │
    │    └─> FbcComparisonService.compare_with_live(file_data, node, token)
    │         │
    │         ├─> Check telnet connection
    │         │    └─> telnet_service._ensure_debugger_connection()
    │         │
    │         ├─> Execute command based on file type
    │         │    ├─> If .fbc: fbc_command_service.generate_fieldbus_command(token)
    │         │    ├─> If .rpc: rpc_command_service.generate_rpc_command(token)
    │         │    └─> telnet_service.execute_command(cmd)
    │         │
    │         ├─> Parse live output
    │         │    └─> parser.parse_content(live_output, file_type)
    │         │
    │         ├─> Compare ALL table cells (entire table)
    │         │    └─> _compare_tables(file_data, live_data)
    │         │
    │         └─> Return ComparisonResult
    │
    └─> NodeScanWidget.apply_comparison_results(results)
         ├─> For each cell in table:
         │    ├─> If matches: Set green background
         │    ├─> If differs: Set yellow background + tooltip (File: X, Live: Y)
         │    └─> If error: Set red background + error tooltip
         └─> Display match percentage in status (e.g., "✓ 92% match")
         
### Scenario 3: Auto-Refresh Monitoring

```
User enables "Auto-refresh" checkbox and selects interval (e.g., 30s)
    │
    ├─> NodeScanWidget.start_auto_refresh(30)
    │    ├─> Start QTimer with 30-second interval
    │    └─> Display countdown: "Next: 30s"
    │
    └─> Every 30 seconds:
         │
         ├─> Trigger comparison (same as Scenario 2)
         ├─> Update countdown display: "Next: 30s... 29s... 28s..."
         ├─> Apply comparison results to table
         └─> Repeat until user disables auto-refresh or switches tabs
         
User changes file selection:
    │
    ├─> Stop current auto-refresh timer
    ├─> Load new file and display table
    └─> If auto-refresh was enabled, restart with selected interval
```

---

## UI Mockup

### FBC File Display:
```
┌─────────────────────────────────────────────────────────────────┐
│  Commander Center                                                │
├─────────────────────────────────────────────────────────────────┤
│  Tabs: [Telnet] [BsTool] [Scan] ←── NEW TAB                    │
├─────────────────────────────────────────────────────────────────┤
│  Node Tabs: [AP01m] [AP02r] [AP03m] [AL01] ...                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  File: [AP01m_192-168-0-11_162.fbc ▼] [Compare Live] ✓92%      │
│  [✓] Auto-refresh  Interval: [30s ▼]  Next: 24s                │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ PIC │ 5   │ 6   │ 7   │ 8   │ 9   │ ... │ 20  │ sum │      │ │
│  ├─────┼─────┼─────┼─────┼─────┼─────┼─────┼─────┼─────┤      │ │
│  │  0  │ AI8 │ BI8 │ BO8 │ BI8 │ BI8 │ ... │ AO4 │ 15  │      │ │
│  │  1  │ AI8 │ BI8 │ BI8 │ BI8 │ BO8 │ ... │ TI6 │ 15  │      │ │
│  │  2  │ AI8 │ BI8 │ BI8 │ BI8 │ BO8 │ ... │ BI8 │ 15  │      │ │
│  │  3  │ AI8 │ BI8*│ BO8 │ BI8 │ BO8 │ ... │ TI6 │ 15  │      │ │
│  │ ... │ ... │ ... │ ... │ ... │ ... │ ... │ ... │ ... │      │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                  │
│  Legend: ⬜ Not compared  🟢 Match  🟡 Difference  🔴 Error     │
│  *Yellow cell = File: BI8, Live: AI8 (hover for details)       │
│                                                                  │
│  Total: 238 I/O-units, 1843 Channels (1323 in, 520 out)        │
│                                                                  │
│  Node Files Available: 3 FBC files, 2 RPC files                 │
└─────────────────────────────────────────────────────────────────┘
```

### RPC File Display:
```
┌─────────────────────────────────────────────────────────────────┐
│  Commander Center                                                │
├─────────────────────────────────────────────────────────────────┤
│  Tabs: [Telnet] [BsTool] [Scan] ←── NEW TAB                    │
├─────────────────────────────────────────────────────────────────┤
│  Node Tabs: [AP01m] [AP02r] [AP03m] [AL01] ...                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  File: [AP01m_192-168-0-11_162.rpc ▼] [Compare Live] ✓100%     │
│  [✓] Auto-refresh  Interval: [10s ▼]  Next: 7s                 │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ pic │ IREX ERROR │ POLL ERROR │ RESP FAIL │ IREX COUNT │... │ │
│  ├─────┼────────────┼────────────┼───────────┼────────────┼────┤ │
│  │  0  │     0      │     0      │     0     │     0      │ 14 │ │
│  │  1  │     0      │     0      │     0     │     0      │ 69 │ │
│  │  2  │     0      │     0      │     0     │     0      │138 │ │
│  │  3  │     0      │     0*     │     0     │     0      │ 95 │ │
│  │ ... │    ...     │    ...     │    ...    │    ...     │... │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                  │
│  Legend: ⬜ Not compared  🟢 Match  🟡 Difference  🔴 Error     │
│  *Yellow cell = File: 0, Live: 1 (hover for details)           │
│                                                                  │
│  Unknown command: 0                                              │
│                                                                  │
│  Node Files Available: 3 FBC files, 2 RPC files                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## FBC File Parsing Strategy

### Regex Patterns

```python
# Header extraction (common for FBC and RPC)
TIMESTAMP_PATTERN = r'\[(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\]'
COMMAND_FBC_PATTERN = r'print from fbc io structure (\d+)'
COMMAND_RPC_PATTERN = r'print from fbc rupi counters (\d+)'
AGENT_PATTERN = r'FBC agent (\d+)'

# FBC Table structure
FBC_HEADER_PATTERN = r'\s*PIC\s+(\d+.*?)sum\s*'
FBC_ROW_PATTERN = r'\s*(\d+)\s+([\w\s]+?)\s+(\d+)\s*$'
FBC_TOTAL_PATTERN = r'Total sum: (\d+) I/O-units, (\d+) Channels'

# RPC Table structure
RPC_HEADER_PATTERN = r'pic\s+IREX ERROR\s+POLL ERROR\s+RESP FAIL\s+IREX COUNT\s+TIMEOUT'
RPC_ROW_PATTERN = r'^\s*(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s*$'
RPC_UNKNOWN_CMD_PATTERN = r'Unknown command:\s+(\d+)'
```

### Parsing Algorithm

```python
def parse_content(self, content: str, file_type: str = 'FBC') -> FbcTableData:
    lines = content.split('\n')
    
    # 1. Extract metadata from header
    timestamp = self._extract_timestamp(lines[0:5])
    command = self._extract_command(lines[0:10], file_type)
    agent_id = self._extract_agent(lines[0:15])
    
    if file_type == 'FBC':
        return self._parse_fbc_content(lines, timestamp, command, agent_id)
    elif file_type == 'RPC':
        return self._parse_rpc_content(lines, timestamp, command, agent_id)
    else:
        raise ValueError(f"Unknown file type: {file_type}")

def _parse_fbc_content(self, lines, timestamp, command, agent_id):
    # 2. Find table section
    table_start = self._find_line_matching(r'^\s*PIC\s+', lines)
    table_end = self._find_line_matching(r'^\s*Total sum:', lines)
    
    # 3. Parse header row
    headers = self._parse_header(lines[table_start])
    
    # 4. Parse data rows
    rows = []
    for line in lines[table_start+2:table_end]:  # Skip separator
        if match := FBC_ROW_PATTERN.match(line):
            row_data = self._parse_row(line, headers)
            rows.append(row_data)
    
    # 5. Parse totals
    totals = self._parse_totals(lines[table_end])
    
    return FbcTableData(
        timestamp=timestamp,
        command=command,
        agent_id=agent_id,
        file_type='FBC',
        headers=headers,
        rows=rows,
        totals=totals,
        raw_content=content
    )

def _parse_rpc_content(self, lines, timestamp, command, agent_id):
    # 2. Find RPC table section
    table_start = self._find_line_matching(r'pic\s+IREX ERROR', lines)
    table_end = self._find_line_matching(r'Unknown command:', lines)
    
    # 3. Fixed RPC headers
    headers = ['pic', 'IREX ERROR', 'POLL ERROR', 'RESP FAIL', 'IREX COUNT', 'TIMEOUT']
    
    # 4. Parse RPC data rows
    rows = []
    for line in lines[table_start+2:table_end]:  # Skip separator (---)
        if match := RPC_ROW_PATTERN.match(line):
            row_data = {
                'pic': match.group(1),
                'IREX ERROR': match.group(2),
                'POLL ERROR': match.group(3),
                'RESP FAIL': match.group(4),
                'IREX COUNT': match.group(5),
                'TIMEOUT': match.group(6)
            }
            rows.append(row_data)
    
    # 5. Parse unknown command count
    unknown_cmd = self._extract_unknown_command(lines[table_end:])
    
    return FbcTableData(
        timestamp=timestamp,
        command=command,
        agent_id=agent_id,
        file_type='RPC',
        headers=headers,
        rows=rows,
        totals={'unknown_command': unknown_cmd},
        raw_content=content
    )
```

---

## Implementation Phases

### Phase 1: Core Infrastructure (3-4 days)
**Goal**: Basic tab structure and file parsing for FBC/RPC

- [ ] Create `ScanTab` widget with placeholder UI
- [ ] Integrate into `SessionView` as third tab
- [ ] Implement `FbcParserService` with regex-based parsing for both .fbc and .rpc files
- [ ] Unit tests for parser (15+ test cases: FBC files, RPC files, edge cases)
- [ ] Create `NodeScanWidget` with file selector dropdown (shows both .fbc and .rpc)
- [ ] Implement auto-load most recent file on node tab selection

**Deliverables**:
- `src/commander/ui/scan_tab.py`
- `src/commander/ui/node_scan_widget.py`
- `src/commander/services/fbc_parser_service.py`
- `tests/test_fbc_parser_service.py` (FBC + RPC tests)

**Verification**:
- Parse sample .fbc and .rpc files without errors
- Display table in QTableWidget
- Switch between files in dropdown (FBC/RPC mixed list)
- Most recent file auto-loads when node tab opened

### Phase 2: Table Display (2-3 days)
**Goal**: Render parsed FBC data in tabular format

- [ ] Create QTableWidget with proper styling
- [ ] Implement column resizing and header alignment
- [ ] Add tooltip support for truncated values
- [ ] Format cells with monospace font for alignment
- [ ] Display metadata (timestamp, agent ID) above table

**Deliverables**:
- Enhanced `NodeScanWidget._create_table_from_data()`
- CSS styling for table widget
- `tests/test_node_scan_widget.py`

**Verification**:
- Table columns aligned properly
- All FBC file content visible
- Tooltips show full values

### Phase 3: Live Comparison & Auto-Refresh (4-5 days)
**Goal**: Compare file data with live telnet output and implement auto-refresh

- [ ] Implement `FbcComparisonService` with support for FBC and RPC commands
- [ ] Add "Compare with Live" button to UI
- [ ] Execute appropriate command (FBC or RPC) via telnet service based on file type
- [ ] Cell-by-cell comparison algorithm (always compare ALL cells)
- [ ] Visual feedback (color-coded cells: green=match, yellow=diff, red=error, white=not compared)
- [ ] Add auto-refresh checkbox and interval dropdown (5s, 10s, 30s, 60s, 5min)
- [ ] Implement QTimer for periodic comparison
- [ ] Countdown display showing next refresh time
- [ ] Auto-refresh pause/resume on file selection change

**Deliverables**:
- `src/commander/services/fbc_comparison_service.py`
- Comparison result data structures
- UI highlighting logic with full-table comparison
- Auto-refresh timer management
- `tests/test_fbc_comparison_service.py`
- `tests/test_auto_refresh_functionality.py`

**Verification**:
- Compare button triggers correct telnet command (FBC or RPC)
- All cells highlighted (not just differences) after comparison
- Match percentage displayed accurately
- Tooltips show both values for differences
- Auto-refresh triggers comparison at selected interval
- Countdown updates every second
- Timer stops when file selection changes

### Phase 4: Integration & Polish (2 days)
**Goal**: Full integration with Commander Center

- [ ] Connect to existing node manager for node list
- [ ] Scan both _DIA/FBC/ and _DIA/RPC/ directories for files
- [ ] Auto-refresh on configuration changes
- [ ] Error handling (connection failures, parse errors, timer conflicts)
- [ ] Status messages and progress indicators
- [ ] Stop auto-refresh when switching tabs or nodes
- [ ] Documentation and user guide

**Deliverables**:
- Signal connections to `CommanderWindow`
- Error handling and recovery
- User documentation: `docs/technical/TECH_scan_tab_usage.md`
- Integration tests (FBC and RPC workflows)

**Verification**:
- Works with real node configuration
- Both .fbc and .rpc files detected and displayed
- Graceful error handling
- No memory leaks during repeated comparisons
- Auto-refresh stops when tab inactive
- Timer properly cleaned up on widget destruction

---

## Technical Considerations

### 1. **FBC File Format Variations**

**Challenge**: FBC output may vary based on:
- Different field bus configurations
- Various I/O unit types (AI8, BI8, BO8, TI6, etc.)
- Empty cells or missing data

**Solution**:
- Flexible regex patterns with optional groups
- Whitespace-tolerant parsing
- Fallback to raw text display if parsing fails
- Warning messages for unrecognized formats

### 2. **Performance with Large Tables**

**Challenge**: Some nodes may have 20+ rows and 15+ columns

**Solution**:
- Lazy loading: Parse on-demand when subtab selected
- Cache parsed data to avoid re-parsing
- QTableWidget native performance (handles thousands of cells)
- Async comparison to avoid UI freezing

### 3. **Telnet Command Synchronization**

**Challenge**: Comparison requires exclusive telnet access during execution; auto-refresh may conflict with manual operations

**Solution**:
- Check `command_queue.is_processing()` before comparison
- Disable "Compare" button during active sequential execution
- Auto-pause auto-refresh when telnet busy or other tab active
- Use existing `telnet_service._ensure_debugger_connection()`
- Display "Telnet busy, retrying..." message during conflicts
- Resume auto-refresh when telnet becomes available

### 4. **File Selection Logic**

**Challenge**: Multiple FBC files per node, how to determine which to load?

**Solution**:
- Default: Most recent file (by timestamp in filename/content)
- Dropdown shows all available files with metadata
- Remember last selected file per node (user preference)
- Option: "Load All" to compare multiple files in separate tabs

---

## Dependencies

### Required Services (Already Available)
- `NodeManager`: Get node list, tokens
- `TelnetService`: Execute live FBC commands
- `FbcCommandService`: Generate FBC command strings
- `StatusService`: Display status messages
- `LogWriter`: Access to .fbc file paths

### New Services (To Be Created)
- `FbcParserService`: Parse .fbc file format
- `FbcComparisonService`: Compare and highlight differences

### UI Components
- `ScanTab`: Main tab widget
- `NodeScanWidget`: Per-node subtab widget

---

## Testing Strategy

### Unit Tests (80% coverage target)

**FbcParserService** (15+ tests):
- Parse valid FBC file with all fields
- Handle missing headers
- Parse empty table
- Handle malformed rows
- Extract timestamp from various formats
- Parse totals section
- Handle files with extra whitespace
- Validate error handling for corrupted files

**FbcComparisonService** (12+ tests):
- Compare identical tables (100% match)
- Detect single cell difference
- Handle different table dimensions
- Parse live telnet output
- Handle connection failures
- Handle parse errors in live data
- Performance test (large tables)

**NodeScanWidget** (10+ tests):
- Load and display FBC file
- Switch between multiple files
- Apply comparison results
- Handle empty file list
- UI state management
- Signal emission verification

### Integration Tests (5+ tests)

- Load Scan tab with real node configuration
- Execute full comparison workflow
- Handle telnet connection errors
- Verify data consistency across tabs
- Memory leak detection (repeated operations)

### Manual Testing Checklist

- [ ] All nodes display correctly in subtabs
- [ ] File dropdown shows all .fbc files
- [ ] Table alignment matches file content
- [ ] Compare button executes command successfully
- [ ] Differences highlighted correctly
- [ ] Works with debugger disconnected (shows error)
- [ ] Performance acceptable with 10+ nodes
- [ ] No UI freezing during comparison
- [ ] Styling consistent with other tabs

---

## Risk Assessment

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| FBC format inconsistencies | High | Medium | Flexible parser, fallback display, comprehensive tests |
| Telnet conflicts during comparison | Medium | Medium | Check queue status, disable during busy, user messaging |
| Performance with many nodes | Low | Medium | Lazy loading, caching, async operations |
| Table alignment issues | Medium | Low | Monospace fonts, CSS styling, column width management |
| Parse failures on edge cases | Medium | Medium | Extensive test suite, error recovery, raw text fallback |

---

## Requirements Confirmed by User ✅

1. **File Selection Default**: ✅ Auto-load most recent .fbc file for each node on tab open
2. **Comparison Scope**: ✅ Always compare entire table (all cells)
3. **Historical Comparison**: ❌ NOT NEEDED - Only compare file vs. live system
4. **Export Functionality**: ❌ NOT NEEDED - No CSV/report export
5. **Real-time Monitoring**: ✅ Auto-refresh with user-selectable interval (5s, 10s, 30s, 60s options)
6. **Multiple Token Display**: ✅ File selection dropdown shows all .fbc files for node; selecting displays that file's table
7. **Color Scheme**: ✅ Yellow/Green/Red color scheme approved
8. **Notification System**: ❌ NOT NEEDED - No desktop notifications
9. **File Type Scope**: ✅ Show both .fbc AND .rpc files for selected node (dual support)
10. **Scan Trigger**: ✅ User manually triggers scan/comparison for selected node

---

## Success Criteria

- ✅ Scan tab successfully integrated as third tab in SessionView
- ✅ All configured nodes display as subtabs
- ✅ FBC files parse correctly (>95% success rate on real data)
- ✅ Tables render with proper alignment and readability
- ✅ Live comparison executes and highlights differences
- ✅ No crashes or memory leaks during extended use
- ✅ Unit test coverage >80%
- ✅ User documentation complete
- ✅ Performance: Comparison completes <5s for typical node

---

## Next Steps (Awaiting User Approval)

1. **Review this blueprint** - User feedback on design approach
2. **Answer open questions** - Clarify requirements and preferences
3. **Approve Phase 1 start** - Begin implementation of core infrastructure
4. **Schedule progress reviews** - After each phase completion

---

## Appendix A: Regex Pattern Reference

```python
# Timestamp patterns
TIMESTAMP_ISO = r'\[(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\]'
TIMESTAMP_ALT = r'Generated on (\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})'

# Command patterns
CMD_FBC_FULL = r'print from\s*fbc\s+io structure\s+(\d+)'
CMD_FBC_SHORT = r'print.*?(\d{3,7})0000'

# Table structure
TABLE_HEADER = r'^\s*PIC\s+([\d\s]+)\s*sum\s*$'
TABLE_SEPARATOR = r'^\s*[-─]+\s*$'
TABLE_ROW = r'^\s*(\d+)\s+((?:[\w\d]+\s*)+?)\s+(\d+)\s*$'

# I/O unit types
IO_UNIT_TYPE = r'([A-Z]{2}\d)N?'  # Matches AI8, BI8, BO8, TI6, AO4, FI1, etc.

# Totals section
TOTAL_SUMMARY = r'Total sum:\s*(\d+)\s*I/O-units,\s*(\d+)\s*Channels\((\d+)\s*input,\s*(\d+)\s*output\)'
UNIT_BREAKDOWN = r'([A-Z]{3}\d):\s*(\d+)'
```

---

## Appendix B: Example Parsed Data Structure

```python
FbcTableData(
    timestamp='2025-10-12 12:12:08',
    command='print from fbc io structure 1620000',
    agent_id='1620000',
    headers=['PIC', '5', '6', '7', '8', '9', '10', '11', '12', '13', '14', '15', '16', '17', '18', '19', '20', 'sum'],
    rows=[
        {'PIC': '0', '5': 'AI8', '6': 'BI8', '7': 'BO8', ..., 'sum': '15'},
        {'PIC': '1', '5': 'AI8', '6': 'BI8', '7': 'BI8', ..., 'sum': '15'},
        # ... more rows
    ],
    totals={
        'total_units': 238,
        'total_channels': 1843,
        'input_channels': 1323,
        'output_channels': 520,
        'unit_breakdown': {
            'AIU8': 15, 'AOU4': 4, 'BIU8': 131,
            'BI8N': 6, 'BOU8': 63, 'FIU1': 2,
            'AIU4': 1, 'TIU6': 16
        }
    },
    raw_content='...'  # Full original file content
)
```

---

**End of Blueprint - Awaiting User Confirmation**
