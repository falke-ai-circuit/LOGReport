# BsTool Sequential Processing - LOG File Integration

**Date**: 2025-10-11 | **Status**: ✅ Complete with File Highlighting & Tab Switching

## Enhancement Objectives

When executing "Print All Nodes" sequential workflow, Phase 3 (BsTool LOG processing) should:

1. ✅ **Highlight .log file** during execution (visual feedback like FBC/RPC)
2. ✅ **Switch to BsTool tab** automatically to show output
3. ✅ **Wait for completion** before proceeding to next node
4. ✅ **Change color** based on file content after writing (green/yellow/red)

## Implementation Changes

### 1. Added Tab Switching Signal ✅

**File**: `src/commander/presenters/node_tree_presenter.py`  
**Line**: 39

```python
# Signals for UI updates
status_message_signal = pyqtSignal(str, int)
node_tree_updated_signal = pyqtSignal()
log_file_selected_signal = pyqtSignal(str)
command_generated_signal = pyqtSignal(str, str)
switch_to_bstool_tab_signal = pyqtSignal()  # NEW: Switch to BsTool tab when execution starts
```

### 2. Enhanced Phase 3 Execution with File Highlighting ✅

**File**: `src/commander/presenters/node_tree_presenter.py`  
**Method**: `process_node_print_commands()` Phase 3  
**Lines**: 1016-1048

**Changes Made**:

```python
# Phase 3: Execute BsTool for LOG files (with -errlog parameter)
log_tokens = self._get_tokens_for_node(node, "LOG")
logging.debug(f"Phase 3 CHECK: Retrieved {len(log_tokens) if log_tokens else 0} LOG tokens")

if log_tokens:
    logging.info(f"Phase 3: Executing BsTool for node {node_name} ({len(log_tokens)} LOG files)")
    self.status_message_signal.emit(f"Phase 3/3: Executing BsTool -errlog {node_name}...", 0)
    
    # 🆕 Switch to BsTool tab to show output
    self.switch_to_bstool_tab_signal.emit()
    logging.debug("Phase 3: Emitted signal to switch to BsTool tab")
    
    # 🆕 Get the first LOG token for file operations
    log_token = log_tokens[0]
    log_file_path = log_token.log_path if hasattr(log_token, 'log_path') else None
    
    if log_file_path:
        # 🆕 Highlight the LOG file being processed (like FBC/RPC)
        self._highlight_current_file(node_name, log_token, log_file_path)
        
        # 🆕 Open/create log file for writing BsTool output
        self.log_writer.open_log_for_token(
            token_id=log_token.token_id,
            node_name=node_name,
            node_ip=node.ip_address,
            protocol="LOG",
            batch_id=f"bstool_{node_name}"
        )
        logging.debug(f"Phase 3: Opened log file for BsTool output: {log_file_path}")
    
    # Execute BsTool with -errlog parameter
    bstool_command_args = f"-errlog {node_name}"
    logging.debug(f"Phase 3: About to execute BsTool with args: {bstool_command_args}")
    self.bstool_service.execute_command(bstool_command_args)
    logging.info(f"Phase 3: BsTool command executed: {bstool_command_args}")
```

**What Changed**:
- **Switch to BsTool Tab**: Emits `switch_to_bstool_tab_signal` to make output visible
- **File Highlighting**: Calls `_highlight_current_file()` to expand tree and select .log file
- **Log Writer Integration**: Opens log file for writing so BsTool output triggers `log_write_completed` signal
- **Color Updates**: File color changes automatically via existing `handle_log_write_completed()` handler

### 3. Connected Tab Switching Signal ✅

**File**: `src/commander/ui/commander_window.py`  
**Line**: 179

```python
# Connect node tree presenter signals
self.node_tree_presenter.status_message_signal.connect(self.status_service.status_updated)
self.node_tree_presenter.node_tree_updated_signal.connect(self.on_node_tree_updated)
self.node_tree_presenter.log_file_selected_signal.connect(self.session_manager.ip_changed.emit)
self.node_tree_presenter.command_generated_signal.connect(self._handle_command_generated)
# 🆕 NEW: Switch to BsTool tab when BsTool execution starts
self.node_tree_presenter.switch_to_bstool_tab_signal.connect(
    lambda: self.session_tabs.setCurrentWidget(self.bstool_tab)
)
```

## Workflow Integration

### Existing Infrastructure Leveraged

**BsTool Output → Log Writer** (Already Implemented):
- `BsToolCommandService._run_bstool_process()` already writes output to log files
- Calls `self.log_writer.append_to_file(log_file_path, output_str)` for each output line
- Log writer emits `log_write_completed` signal with file stats

**Log Writer → Color Updates** (Already Implemented):
- `NodeTreePresenter.handle_log_write_completed()` receives signal
- Updates `node_status` dictionary with line counts
- Calls `_check_and_update_node_color()` to apply green/yellow/red colors
- Triggers hierarchical color aggregation (file → section → node)

### New Integration Points

**Phase 3 Execution Flow**:

```
[START] Phase 3: BsTool Execution
   ↓
[STEP 1] Emit switch_to_bstool_tab_signal
   └─> CommanderWindow switches to BsTool tab (user sees output)
   ↓
[STEP 2] Get LOG token and file path
   └─> log_token = log_tokens[0]
   └─> log_file_path = log_token.log_path
   ↓
[STEP 3] Highlight LOG file in tree
   └─> _highlight_current_file(node_name, log_token, log_file_path)
   └─> Expands node → Expands LOG section → Selects .log file
   ↓
[STEP 4] Open log file for writing
   └─> log_writer.open_log_for_token(...)
   └─> Creates/opens file, ready for BsTool output
   ↓
[STEP 5] Execute BsTool command
   └─> bstool_service.execute_command(f"-errlog {node_name}")
   └─> Sets is_executing = True
   ↓
[STEP 6] BsTool writes output to file
   └─> bstool_service._run_bstool_process()
   └─> log_writer.append_to_file() for each line
   └─> Emits log_write_completed(file_path, success, total_lines, ...)
   ↓
[STEP 7] Update file color
   └─> handle_log_write_completed() receives signal
   └─> _check_and_update_node_color() applies color
   └─> Green (>10 lines) | Yellow (<10 lines) | Red (0 lines)
   ↓
[STEP 8] Wait for BsTool completion
   └─> bstool_service sets is_executing = False
   └─> Emits bstool_execution_completed signal
   ↓
[STEP 9] Sequential processing continues
   └─> _check_sequential_processing_continuation() checks is_executing
   └─> Both command_queue and bstool_service idle → next node
```

## Visual User Experience

### Before Enhancement
- Phase 3 executed silently
- No visual feedback of .log file processing
- User stayed on current tab (might miss BsTool output)
- No color changes for LOG files

### After Enhancement ✅
1. **Tab Switches**: User automatically sees BsTool tab with real-time output
2. **File Highlighted**: .log file expands and highlights in tree (like FBC/RPC files)
3. **Color Feedback**: File changes color based on content:
   - 🔴 Red: No output (0 lines)
   - 🟡 Yellow: Minimal output (<10 lines)
   - 🟢 Green: Good output (≥10 lines)
4. **Progress Tracking**: Status bar shows "Phase 3/3: Executing BsTool -errlog AP01..."
5. **Smooth Workflow**: Waits for completion before next node

## Files Modified

| File | Changes | Purpose |
|------|---------|---------|
| `node_tree_presenter.py` (line 39) | Added `switch_to_bstool_tab_signal` | Signal to request tab switch |
| `node_tree_presenter.py` (lines 1016-1048) | Enhanced Phase 3 execution | File highlighting + log writer integration |
| `commander_window.py` (line 179) | Connected tab switch signal | Makes tab switching happen |

## Testing Checklist

### User Actions
1. **Load Configuration** → Set log root → Verify nodes loaded
2. **Click "Print All Nodes"** → Sequential processing starts

### Expected Behavior Per Node

**Phase 1: FBC** (existing behavior)
- ✅ Status: "Phase 1/3: Printing N FBC tokens..."
- ✅ FBC files highlight during processing
- ✅ Colors change: Red → Yellow → Green

**Phase 2: RPC** (existing behavior)
- ✅ Status: "Phase 2/3: Printing N RPC tokens..."
- ✅ RPC files highlight during processing
- ✅ Colors change: Red → Yellow → Green

**Phase 3: LOG** ✅ **NEW BEHAVIOR**
- ✅ Status: "Phase 3/3: Executing BsTool -errlog AP01..."
- ✅ **Tab switches to BsTool** automatically
- ✅ **.log file highlights** in tree (expands node → LOG section → selects file)
- ✅ **BsTool output appears** in BsTool tab
- ✅ **File color changes** based on output: Red → Yellow → Green
- ✅ **Waits for completion** before AP02

### Debug Log Verification

Check `debug.log` for:
```
INFO: Phase 3: Executing BsTool for node AP01 (1 LOG files)
DEBUG: Phase 3: Emitted signal to switch to BsTool tab
DEBUG: Phase 3: Opened log file for BsTool output: D:\_APP\LOGReport\logs\LOG\AP01_192-168-0-11.log
DEBUG: Phase 3: About to execute BsTool with args: -errlog AP01
INFO: Phase 3: BsTool command executed: -errlog AP01
DEBUG: BsToolCommandService: Writing bstool output to log file
DEBUG: LogWriter: Appended 1 lines to D:\_APP\LOGReport\logs\LOG\AP01_192-168-0-11.log
DEBUG: NodeTreePresenter: handle_log_write_completed - Log Path: ..., Total Lines: 15
DEBUG: _check_and_update_node_color: Applying green color (15 lines)
DEBUG: Sequential processing: BsTool is executing, waiting for completion
DEBUG: Sequential processing: Queue idle and BsTool complete, proceeding to next node
```

## Success Criteria

✅ **Tab Switching**: BsTool tab becomes active when Phase 3 starts  
✅ **File Highlighting**: .log file expands and selects in tree during execution  
✅ **Output Visible**: BsTool output appears in real-time on BsTool tab  
✅ **Color Updates**: File color changes from red → yellow/green based on content  
✅ **Sequential Wait**: Workflow waits for BsTool completion before next node  
✅ **No Manual Intervention**: Everything automatic during "Print All Nodes"  

## Benefits

1. **Better UX**: User sees what's happening without switching tabs manually
2. **Consistent Behavior**: LOG files now match FBC/RPC file workflow
3. **Visual Feedback**: Highlighting and colors provide progress indication
4. **Output Visibility**: BsTool results immediately visible in tab
5. **Integration**: Leverages existing log writer and color systems

## Related Documentation

- `IMPLEMENTATION_SUMMARY_bstool_sequential_processing_complete.md` - Initial sequential processing fix
- BsTool Command Service - External process execution
- Log Writer - File I/O and signal emissions
- Node Tree Presenter - Sequential workflow orchestration

---

**Status**: ✅ **COMPLETE** - LOG files now fully integrated with sequential workflow including tab switching, file highlighting, and color updates
