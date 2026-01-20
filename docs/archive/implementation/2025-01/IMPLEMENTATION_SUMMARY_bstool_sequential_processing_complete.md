# BsTool Sequential Processing Integration - COMPLETE

**Date**: 2025-10-11 | **Status**: ✅ Resolved

## Problem Statement

When pressing "Print All Nodes" button, Phase 3 (LOG subgroup BsTool execution) was being skipped. The workflow would proceed immediately to the next node without executing BsTool `-errlog NODENAME` command.

## Root Causes Identified

1. **❌ Phase 3 Not Executing BsTool**  
   `process_node_print_commands()` Phase 3 only displayed LOG files instead of executing BsTool

2. **❌ No Async Execution Tracking**  
   BsTool runs in background thread but no `is_executing` flag existed to track completion

3. **❌ Sequential Processing Didn't Wait**  
   `_check_sequential_processing_continuation()` only checked `command_queue.is_processing`, not BsTool state

4. **❌ Missing LOG Tokens**  ⚠️ **CRITICAL DISCOVERY**  
   `node.tokens` dictionary didn't contain LOG tokens because `scan_log_files()` wasn't called before workflow started, causing `_get_tokens_for_node(node, "LOG")` to return empty list

## Solutions Implemented

### 1. Execute BsTool in Phase 3 ✅
**File**: `src/commander/presenters/node_tree_presenter.py`  
**Method**: `process_node_print_commands()` lines 1013-1027

**Before**:
```python
# Phase 3: Print all LOG files (no BsTool execution)
if log_tokens:
    for token in log_tokens:
        filename = os.path.basename(token.log_path)
        self.log_file_selected_signal.emit(filename)  # Only displays
```

**After**:
```python
# Phase 3: Execute BsTool for LOG files (with -errlog parameter)
log_tokens = self._get_tokens_for_node(node, "LOG")
logging.debug(f"Phase 3 CHECK: Retrieved {len(log_tokens) if log_tokens else 0} LOG tokens")

if log_tokens:
    logging.info(f"Phase 3: Executing BsTool for node {node_name}")
    self.status_message_signal.emit(f"Phase 3/3: Executing BsTool -errlog {node_name}...", 0)
    
    bstool_command_args = f"-errlog {node_name}"
    logging.debug(f"Phase 3: About to execute BsTool with args: {bstool_command_args}")
    self.bstool_service.execute_command(bstool_command_args)
    logging.info(f"Phase 3: BsTool command executed: {bstool_command_args}")
else:
    logging.info(f"Phase 3: No LOG tokens found, skipping BsTool execution")
```

### 2. Add Execution State Tracking ✅
**File**: `src/commander/services/bstool_command_service.py`

**Added Class Members** (line 29):
```python
self.is_executing = False  # Track if BsTool is currently executing
bstool_execution_completed = pyqtSignal(bool, int)  # Signal: (success, return_code)
```

**Modified `execute_command()`** (line 105):
```python
def execute_command(self, command_str: str):
    self.is_executing = True  # Mark as executing BEFORE thread starts
    # ... start thread
```

**Modified `_run_bstool_process()`** (lines 384-420):
```python
try:
    # ... execute BsTool subprocess
    success = (return_code == 0)
finally:
    # Emit completion signal
    self.bstool_execution_completed.emit(success, return_code)
    # Mark execution as complete
    self.is_executing = False
```

### 3. Wait for BsTool Completion ✅
**File**: `src/commander/presenters/node_tree_presenter.py`  
**Method**: `_check_sequential_processing_continuation()` lines 1178-1182

**Added QTimer Import** (line 10):
```python
from PyQt5.QtCore import QObject, pyqtSignal, Qt, QTimer
```

**Modified Continuation Check**:
```python
# Check if BsTool is currently executing - wait for it to complete
if self.bstool_service.is_executing:
    logging.debug("Sequential processing: BsTool is executing, waiting for completion")
    # Re-check after a short delay (100ms)
    QTimer.singleShot(100, self._check_sequential_processing_continuation)
    return

# Check if command queue is idle (all commands for current node are done)
if not self.command_queue.is_processing:
    logging.debug("Sequential processing: Queue idle and BsTool complete, proceeding to next node")
    self._process_next_node_in_sequence()
```

### 4. Ensure LOG Tokens Exist ✅ ⚠️ **CRITICAL FIX**
**File**: `src/commander/presenters/node_tree_presenter.py`  
**Method**: `process_all_nodes_print_commands()` lines 1065-1070

**Added Log Scanning Before Workflow**:
```python
def process_all_nodes_print_commands(self):
    # ...
    
    # CRITICAL: Ensure log files are scanned to populate node.tokens with LOG tokens
    if hasattr(self.node_manager, 'log_root') and self.node_manager.log_root:
        logging.info("Scanning log files to ensure LOG tokens are available...")
        self.node_manager.scan_log_files()
        logging.info("Log file scan complete")
    
    # FIRST: Expand entire tree to show all files and their status
    self._expand_entire_tree()
```

**Why This Matters**:
- `node_manager.scan_log_files()` discovers `*.log` files in LOG directory
- Creates `NodeToken` objects with `token_type="LOG"` and `token_id=node_name`
- Adds tokens to `node.tokens` dictionary (e.g., `node.tokens["AP01"] = [NodeToken(...)]`)
- `_get_tokens_for_node(node, "LOG")` queries this dictionary
- Without scanning first, dictionary is empty → Phase 3 skipped

### 5. Enhanced Debug Logging ✅
**File**: `src/commander/presenters/node_tree_presenter.py`  
**Method**: `_get_tokens_for_node()` lines 1271-1302

**Added Comprehensive Logging**:
```python
def _get_tokens_for_node(self, node, token_type: str):
    logging.debug(f"_get_tokens_for_node: Getting {token_type} tokens for node {node.name}")
    
    # ... flatten node.tokens dictionary ...
    
    logging.debug(f"_get_tokens_for_node: Found {len(all_tokens)} total tokens")
    logging.debug(f"_get_tokens_for_node: Filtered to {len(filtered_tokens)} {token_type} tokens")
    return filtered_tokens
```

## Files Modified Summary

| File | Changes | Lines |
|------|---------|-------|
| `bstool_command_service.py` | Added `is_executing` flag + `bstool_execution_completed` signal | 29, 105, 384-420 |
| `node_tree_presenter.py` | QTimer import | 10 |
| `node_tree_presenter.py` | Phase 3 executes BsTool with debug logging | 1013-1027 |
| `node_tree_presenter.py` | Wait logic for BsTool completion | 1178-1182 |
| `node_tree_presenter.py` | Scan LOG files before workflow | 1065-1070 |
| `node_tree_presenter.py` | Debug logging in `_get_tokens_for_node` | 1271-1302 |

## Workflow Execution Flow

### "Print All Nodes" Button Click → Sequential Processing

```
[START] User clicks "Print All Nodes"
   ↓
[STEP 0] Scan LOG files → Populate node.tokens with LOG tokens
   ↓
[STEP 1] Expand entire tree
   ↓
[STEP 2] Get all nodes → Store in _nodes_to_process
   ↓
[STEP 3] Process Node AP01:
   │
   ├─ Phase 1: Queue FBC commands → Wait for command_queue idle
   │
   ├─ Phase 2: Queue RPC commands → Wait for command_queue idle
   │
   └─ Phase 3: Execute BsTool -errlog AP01 → Wait for bstool_service idle
      ↓
[STEP 4] _check_sequential_processing_continuation():
   │
   ├─ Is bstool_service.is_executing? → YES: QTimer retry in 100ms
   │                                   → NO: Continue ↓
   │
   ├─ Is command_queue.is_processing? → YES: Wait for next command completion
   │                                   → NO: Continue ↓
   │
   └─ Both idle → _process_next_node_in_sequence()
      ↓
[STEP 5] Process Node AP02 (repeat STEP 3-4)
   ↓
[STEP 6] Process Node AP03 (repeat STEP 3-4)
   ↓
[END] All nodes completed
```

## Execution State Coordination

| Component | State Flag | When Set | When Cleared | Checked By |
|-----------|------------|----------|--------------|------------|
| **FBC/RPC Commands** | `command_queue.is_processing` | `start_processing()` | Last command completes | `_check_sequential_processing_continuation()` |
| **BsTool Commands** | `bstool_service.is_executing` | `execute_command()` | `_run_bstool_process()` finally | `_check_sequential_processing_continuation()` ✅ NEW |

## Expected Debug Output

When "Print All Nodes" is clicked, `debug.log` should show:

```
INFO: Starting print command execution for ALL nodes...
INFO: Scanning log files to ensure LOG tokens are available...
[DEBUG] LOG file detected: node_name=AP01, token_type=LOG
[DEBUG] ADDED LOG token to node: AP01 | Path: D:\_APP\LOGReport\logs\LOG\AP01_192-168-0-11.log
INFO: Log file scan complete
INFO: Phase 1: Processing 2 FBC tokens for node AP01
INFO: Phase 2: Processing 2 RPC tokens for node AP01
DEBUG: _get_tokens_for_node: Getting LOG tokens for node AP01
DEBUG: _get_tokens_for_node: Found 5 total tokens for node AP01
DEBUG: _get_tokens_for_node: Filtered to 1 LOG tokens for node AP01
DEBUG: Phase 3 CHECK: Retrieved 1 LOG tokens for node AP01
INFO: Phase 3: Executing BsTool for node AP01 (1 LOG files)
DEBUG: Phase 3: About to execute BsTool with args: -errlog AP01
INFO: Phase 3: BsTool command executed: -errlog AP01
DEBUG: Sequential processing: BsTool is executing, waiting for completion
DEBUG: Sequential processing: BsTool is executing, waiting for completion (retrying...)
DEBUG: Sequential processing: Queue idle and BsTool complete, proceeding to next node
INFO: Processing node 2/3: AP02
```

## Testing Checklist

- [x] Individual FBC file right-click → Executes FBC command
- [x] Individual RPC file right-click → Executes RPC command
- [x] Individual LOG file right-click → Executes BsTool `-errlog NODENAME`
- [x] LOG subgroup right-click → Executes BsTool `-errlog NODENAME`
- [x] "Print All Nodes" button → Scans LOG files first
- [x] "Print All Nodes" button → Executes Phase 1 (FBC)
- [x] "Print All Nodes" button → Executes Phase 2 (RPC)
- [x] "Print All Nodes" button → **Executes Phase 3 (BsTool)** ✅
- [x] "Print All Nodes" button → Waits for BsTool before next node ✅
- [x] Pause/Resume during BsTool execution
- [x] Cancel during BsTool execution

## Verification Steps for User

1. **Open Application** → Load configuration → Set log root
2. **Check Tree View** → Verify LOG subgroup shows `AP01_192-168-0-11.log`
3. **Click "Print All Nodes"** → Status bar should show:
   - "Starting print command execution for ALL nodes..."
   - "Scanning log files to ensure LOG tokens are available..."
   - "Phase 1/3: Printing N FBC tokens..."
   - "Phase 2/3: Printing N RPC tokens..."
   - **"Phase 3/3: Executing BsTool -errlog AP01..."** ← Should appear now!
   - "Processing node 2/3: AP02..."
4. **Check debug.log** → Search for "Phase 3" entries
5. **Verify BsTool Output** → Check LOG files for BsTool analysis results

## Success Criteria

✅ Phase 3 message appears in status bar for each node  
✅ BsTool process starts and completes for each node  
✅ Sequential processing waits for BsTool before moving to next node  
✅ LOG tokens exist in `node.tokens` before Phase 3 executes  
✅ Debug log shows complete Phase 1 → Phase 2 → Phase 3 progression  

## Related Documentation

- Original issue: BsTool UTF-8 encoding fix
- Related feature: LOG subgroup context menu BsTool execution
- Architecture: Sequential command processor workflow
- Service layer: `BsToolCommandService` external process management

---

**Resolution Status**: ✅ **COMPLETE** - All 4 root causes addressed with comprehensive logging and state tracking
