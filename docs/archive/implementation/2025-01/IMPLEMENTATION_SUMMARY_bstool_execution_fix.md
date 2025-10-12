# BsTool Context Menu & Execution Fixes - Phase 2

**Date**: 2025-10-11 (Continued)

## Issues Fixed

### Issue 1: Log Writer Error ✅
**Problem**: `append_to_file` method had undefined `log_success` variable before try block, causing "Failed to write to log file" errors with "signal has 5 argument(s) but 4 provided"

**Root Cause**: 
- Variable `log_success` was only defined inside the try block
- Signal emission expected 5 arguments but only 4 were provided

**Solution**:
- Initialize `log_success = False` before try block
- Fixed signal emission to include all 5 arguments: `filepath, success, total_line_count, lines_written, content`

**File**: `src/commander/log_writer.py` (line 197-222)

---

### Issue 2: Right-Click on .log File Not Executing BsTool ✅
**Problem**: Right-clicking individual .log file and selecting "Run BsTool on this file" only generated command text but didn't execute it

**Root Cause**:
- `process_bstool_command` method only emitted `command_generated_signal` which populated the UI input field
- No actual execution of the BsTool command

**Solution**:
- Modified `process_bstool_command` to directly execute BsTool via `bstool_service.execute_command()`
- Removed signal emission that only generated text
- Now properly extracts node ID and executes `-errlog NODEID` command immediately

**File**: `src/commander/presenters/node_tree_presenter.py` (line 1462-1485)

---

### Issue 3: LOG Subgroup Menu Confusion ✅
**Problem**: LOG subgroup had TWO actions:
1. "Print All LOG Tokens for {node_name}" - only displayed files
2. "Run BsTool for {node_name}" - executed BsTool

User expected ONLY ONE action that executes BsTool with `-errlog` parameter.

**Solution**:
- Removed the duplicate "Print All LOG Tokens" action that called `process_all_log_subgroup_commands`
- Kept ONLY the BsTool execution action but renamed it to "Print All LOG Tokens for {node_name}"
- This single action now executes BsTool with `-errlog NODENAME` parameter (same as clicking Execute button with that command)
- For FBC and RPC subgroups, kept the original "Print All" behavior

**File**: `src/commander/services/context_menu_service.py` (line 118-151)

---

## Code Changes Summary

### 1. `src/commander/log_writer.py`
```python
# BEFORE (line 197)
def append_to_file(self, filepath: str, content: str, token=None):
    if not content.strip():
        return
    try:
        with open(filepath, 'a', encoding='utf-8') as f:
            f.write(content + '\n')
        log_success = True  # ❌ Defined INSIDE try block
    # ...
    self.log_write_completed.emit("N/A", log_success, ...)  # ❌ 4 args only

# AFTER
def append_to_file(self, filepath: str, content: str, token=None):
    if not content.strip():
        return
    log_success = False  # ✅ Defined BEFORE try block
    try:
        with open(filepath, 'a', encoding='utf-8') as f:
            f.write(content + '\n')
        log_success = True
    # ...
    self.log_write_completed.emit(filepath_to_emit, log_success, line_count_to_emit, line_count_to_emit, content)  # ✅ 5 args
```

### 2. `src/commander/presenters/node_tree_presenter.py`
```python
# BEFORE (line 1462)
def process_bstool_command(self, log_file_path: str):
    node_id = self._extract_node_id_from_log_path(log_file_path)
    bstool_command_args = f"-errlog {node_id}" if node_id else ""
    # ❌ Only generates command text, doesn't execute
    self.command_generated_signal.emit(bstool_command_args, "BSTOOL")

# AFTER
def process_bstool_command(self, log_file_path: str):
    node_id = self._extract_node_id_from_log_path(log_file_path)
    if not node_id:
        self._report_error("Could not extract node ID from log file path", None)
        return
    bstool_command_args = f"-errlog {node_id}"
    # ✅ Executes BsTool command directly
    self.bstool_service.execute_command(bstool_command_args)
    self.status_message_signal.emit(f"Executing BsTool with -errlog {node_id}", 3000)
```

### 3. `src/commander/services/context_menu_service.py`
```python
# BEFORE (line 118)
# Create action for printing all tokens (simplified to only this command)
print_action = QAction(f"Print All {section_type} Tokens for {node_name}", menu)
if self.presenter:
    # Connect action to presenter method
    if section_type == "FBC":
        print_action.triggered.connect(...)
    elif section_type == "RPC":
        print_action.triggered.connect(...)
    elif section_type == "LOG":
        print_action.triggered.connect(
            lambda: self.presenter.process_all_log_subgroup_commands(...)  # ❌ Only displays
        )
menu.addAction(print_action)

# Add BsTool action for LOG subgroups
if section_type == "LOG":
    bstool_action = QAction(f"Run BsTool for {node_name}", menu)  # ❌ Second action
    # ...

# AFTER
# For LOG subgroup, ONLY show BsTool execution action
if section_type == "LOG":
    # ✅ Single action with user-friendly name that executes BsTool
    bstool_action = QAction(f"Print All LOG Tokens for {node_name}", menu)
    if self.presenter:
        bstool_action.triggered.connect(
            lambda: self._handle_bstool_node_action(node_name)  # ✅ Executes -errlog
        )
    menu.addAction(bstool_action)
else:
    # For FBC and RPC, keep original behavior
    print_action = QAction(f"Print All {section_type} Tokens for {node_name}", menu)
    # ...
```

---

## Verification Steps

### 1. Log Writer Fix
✅ BsTool output now writes to log files without errors
✅ No "signal has 5 argument(s) but 4 provided" errors

### 2. Right-Click Individual .log File
✅ Right-click any .log file → "Run BsTool on this file" → BsTool executes immediately
✅ Command `-errlog NODEID` is executed (where NODEID is extracted from filename)
✅ For "AP01m_192-168-0-11.log" → executes `-errlog AP01` (trailing 'm' removed)

### 3. Right-Click LOG Subgroup
✅ Right-click LOG subgroup → Shows ONLY "Print All LOG Tokens for {node_name}"
✅ Clicking this action executes BsTool with `-errlog NODENAME`
✅ Same behavior as manually typing `-errlog AP01` and clicking Execute button
✅ FBC and RPC subgroups unchanged (still show "Print All FBC/RPC Tokens")

---

## Behavior Summary

| Context | Action | Behavior |
|---------|--------|----------|
| **Individual .log file** | "Run BsTool on this file" | Executes `-errlog NODEID` immediately |
| **LOG subgroup** | "Print All LOG Tokens for {node}" | Executes `-errlog NODENAME` immediately |
| **BsTool Tab Execute button** | Click with `-errlog AP01` | Executes `-errlog AP01` immediately |
| **FBC subgroup** | "Print All FBC Tokens for {node}" | Prints all FBC structures (no change) |
| **RPC subgroup** | "Print All RPC Tokens for {node}" | Prints all RPC counters (no change) |

All three LOG-related actions now have **identical behavior**: Execute BsTool with `-errlog` parameter.

---

## Files Modified

1. `src/commander/log_writer.py` - Fixed undefined variable and signal arguments
2. `src/commander/presenters/node_tree_presenter.py` - Changed from command generation to command execution
3. `src/commander/services/context_menu_service.py` - Simplified LOG subgroup to single action

---

## Related Documentation

See also:
- `logs/workflow_bstool_fix_20251011.md` - Initial encoding and parameter extraction fixes
- `tests/test_bstool_context_menu_fix.py` - Test suite for encoding and parameters
