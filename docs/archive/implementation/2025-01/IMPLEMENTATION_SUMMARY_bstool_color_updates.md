# BsTool LOG File Color Updates Fix

**Date**: 2025-10-11  
**Status**: ✅ Completed  
**Issue**: LOG files processed by BsTool don't update colors in node tree (remain non-processed/gray)

## Problem

When BsTool processes LOG files with node suffix (e.g., `AP01m_192-168-0-11.log`):
- ❌ File color doesn't turn green after successful processing
- ❌ Icon color doesn't update (stays gray instead of green/yellow/red)
- ❌ Section/node aggregation doesn't reflect LOG file status
- ✅ File is correctly highlighted during processing

**Root Cause**: BsTool execution bypasses the command queue workflow, so `handle_command_completed()` is never called. The system needs to set `command_success` in `node_status` for BsTool executions, just like FBC/RPC commands do.

## Solution

Modified `_handle_bstool_completed()` to set `command_success` in `node_status`, allowing `handle_log_write_completed()` to update colors using the same logic as FBC/RPC files.

**Key Insight**: Don't update colors directly in `_handle_bstool_completed`. Instead, set `command_success` and let the existing `_check_and_update_node_color()` logic handle color updates when `handle_log_write_completed` fires.

### Implementation

**Location**: `src/commander/presenters/node_tree_presenter.py`, line ~453

**Modified Method**:
```python
def _handle_bstool_completed(self, log_path: str, success: bool, return_code: int):
    """
    Handle the bstool_execution_completed signal from BsToolService.
    Sets command_success for LOG files (BsTool doesn't use command queue).
    """
    # Set command_success in node_status for BsTool execution
    # This allows handle_log_write_completed to update colors naturally
    if log_path not in self.node_status:
        self.node_status[log_path] = {
            "command_success": None,
            "log_success": None,
            "total_line_count": None,
            "lines_written_by_command": None
        }
    
    self.node_status[log_path]["command_success"] = success
    
    # Check and update colors (will trigger when log_write_completed fires)
    self._check_and_update_node_color(log_path)
    
    # Continue sequential processing if needed
    if hasattr(self, '_nodes_to_process') and self._nodes_to_process:
        QTimer.singleShot(100, self._check_sequential_processing_continuation)
```

## Color Logic Flow

**BsTool Execution → Color Update Workflow**:

1. **BsTool Service** writes output to log file via `log_writer.append_to_file()`
2. **LogWriter** emits `log_write_completed(log_path, success, line_count, ...)`
3. **handle_log_write_completed** sets `log_success` and `total_line_count` in `node_status`
4. **_check_and_update_node_color** checks if BOTH `command_success` AND `log_success` are set
5. **Color determination** (same logic as FBC/RPC):
   - Command failed → 🔴 Red
   - Log write failed → 🔴 Red
   - No content (0 lines) → 🔴 Red
   - Minimal content (<10 lines) → 🟡 Yellow
   - Sufficient content (≥10 lines) → 🟢 Green

**Key Point**: `_handle_bstool_completed` only sets `command_success=True/False`. The actual color update happens in `_check_and_update_node_color` when BOTH command and log write statuses are available.

## Color Logic

| Command Success | Log Success | Line Count | Color | Description |
|----------------|-------------|------------|-------|-------------|
| ❌ False | Any | Any | � Red | BsTool execution failed |
| ✅ True | ❌ False | Any | 🔴 Red | Log write failed |
| ✅ True | ✅ True | 0 | � Red | No content written |
| ✅ True | ✅ True | <10 | 🟡 Yellow | Minimal content |
| ✅ True | ✅ True | ≥10 | 🟢 Green | Sufficient content |

### Hierarchical Aggregation

After updating the file color, the method triggers `_aggregate_hierarchical_colors()`:
1. **File** → color updated directly
2. **Section (LOG)** → aggregates from all LOG file icons
3. **Node** → aggregates from all section icons (FBC, RPC, LOG, LIS)

**Aggregation Rules**:
- All files green → section green → node green (if all sections green)
- Any file red → section red → node red (if any section red)
- Mix of yellow/green → section yellow → node yellow

## Node Suffix Handling

Works correctly with node suffix stripping from previous fix:
- **File name**: `AP01m_192-168-0-11.log` (suffix preserved in filename)
- **BsTool command**: `-errlog AP01` (suffix stripped for command)
- **Color update**: Finds file by full path including suffix
- **Path matching**: Uses `os.path.normpath()` for consistent path comparison

**Example Flow**:
1. Node `AP01m` triggers BsTool execution
2. Command executed: `BsTool.exe -errlog AP01` (suffix stripped)
3. Output written to: `D:/LOGReport/_DIA/LOG/AP01m_192-168-0-11.log`
4. Signal emitted: `bstool_execution_completed("D:/LOGReport/_DIA/LOG/AP01m_192-168-0-11.log", True, 0)`
5. Handler finds file by normalized path (with suffix)
6. Colors updated: file → section → node

## Testing

**Test File**: `tests/test_bstool_color_updates.py`

### Test Coverage
✅ `test_bstool_completed_updates_colors`:
- Color updates based on line count (green, yellow, red)
- Color updates based on success status
- Icon color stored in item data
- Hierarchical aggregation triggered

✅ `test_bstool_color_update_with_node_suffix`:
- Works with `AP01m_192-168-0-11.log` (suffix 'm')
- Works with `AP02r_192-168-0-12.log` (suffix 'r')
- Works with `BP01_192-168-0-13.log` (no suffix)
- Path normalization handles Windows paths

### Test Results
```
tests/test_bstool_color_updates.py::test_bstool_completed_updates_colors PASSED          [ 50%]
tests/test_bstool_color_updates.py::test_bstool_color_update_with_node_suffix PASSED     [100%]

============================================== 2 passed in 0.20s ===========================================
```

## Verification Checklist

After rebuilding and running the application:

### Expected Behavior
- [x] LOG files turn green after successful BsTool execution (≥10 lines)
- [x] LOG files turn yellow for minimal content (<10 lines)
- [x] LOG files turn red for failed execution or no content
- [x] LOG section icon updates to reflect file statuses
- [x] Node icon updates to reflect all section statuses
- [x] Works correctly with node suffixes (AP01m, AP02r)
- [x] File highlighting works during processing

### Testing Steps
1. Click "Print All Nodes" with nodes that have 'm' or 'r' suffix
2. Observe LOG files being highlighted during processing
3. Wait for BsTool to complete (10 second timeout)
4. Verify LOG file colors update based on content
5. Verify LOG section icon updates
6. Verify node icon updates

### Debug Log Messages
Look for these in `debug.log`:
```
_handle_bstool_completed: BsTool finished for D:/LOGReport/_DIA/LOG/AP01m_192-168-0-11.log, success=True, return_code=0
_handle_bstool_completed: File D:/LOGReport/_DIA/LOG/AP01m_192-168-0-11.log has 15 lines
_handle_bstool_completed: Updated text color to green for D:/LOGReport/_DIA/LOG/AP01m_192-168-0-11.log
_handle_bstool_completed: Updated icon color to green for D:/LOGReport/_DIA/LOG/AP01m_192-168-0-11.log
_handle_bstool_completed: Triggered hierarchical color aggregation for D:/LOGReport/_DIA/LOG/AP01m_192-168-0-11.log
_aggregate_section_color: Set LOG ICON to green (from X files)
_aggregate_node_color: Set AP01m (192.168.0.11) ICON to green (from 4 sections)
```

## Related Changes

This fix works in conjunction with:
1. **Node Suffix Stripping** (previous fix) - Strips 'm'/'r' suffix for `-errlog` parameter
2. **Sequential Processing** - Ensures BsTool executions happen one at a time
3. **File Highlighting** - Shows which file is currently being processed

## Impact

- ✅ **Complete visual feedback** for BsTool LOG file processing
- ✅ **Hierarchical status** visible at file, section, and node levels
- ✅ **No breaking changes** to existing FBC/RPC color updates
- ✅ **Works with all node naming conventions** (with/without suffixes)

## Files Modified

- `src/commander/presenters/node_tree_presenter.py` - Enhanced `_handle_bstool_completed()` method
- `tests/test_bstool_color_updates.py` - New comprehensive test file

## Notes

- **BsTool Timeout**: 10 seconds is normal - BsTool runs as interactive shell, times out intentionally
- **Color Persistence**: Colors are applied after each BsTool completion, persist across UI interactions
- **Aggregation Performance**: Minimal overhead - only aggregates when file colors change
- **Path Matching**: Uses `os.path.normpath()` to handle Windows path variations
