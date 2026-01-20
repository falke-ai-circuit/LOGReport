# BsTool Node Name Suffix Stripping

**Date**: 2025-10-11  
**Status**: ✅ Completed  
**Issue**: BsTool `-errlog` parameter fails with node names that have 'm' or 'r' suffix

## Problem

BsTool's `-errlog` parameter does not accept node names with suffix letters:
- ❌ `BsTool.exe -errlog AP01m` → **FAILS**
- ✅ `BsTool.exe -errlog AP01` → **WORKS**

Node names in the system can have 'm' (master) or 'r' (redundant) suffixes:
- AP01m → needs to become AP01
- AP02r → needs to become AP02
- BP01m → needs to become BP01

## Solution

Created a helper method `_strip_node_suffix()` that removes 'm' or 'r' suffix from node names before constructing the `-errlog` parameter.

### Implementation

**Location**: `src/commander/presenters/node_tree_presenter.py`

**New Method**:
```python
def _strip_node_suffix(self, node_name: str) -> str:
    """
    Strip 'm' or 'r' suffix from node name for BsTool -errlog parameter.
    
    Examples:
        AP01m → AP01
        AP02r → AP02
        AP01 → AP01 (unchanged)
        
    Args:
        node_name: Original node name (may have 'm' or 'r' suffix)
        
    Returns:
        Node name without 'm' or 'r' suffix
    """
    if node_name.endswith('m') or node_name.endswith('r'):
        return node_name[:-1]
    return node_name
```

### Updated Locations

Applied suffix stripping in **3 locations** where `-errlog` parameter is constructed:

#### 1. `process_node_print_commands()` - Line ~1059
**Context**: Sequential "Print All Nodes" workflow, Phase 3 (BsTool execution)

**Before**:
```python
bstool_command_args = f"-errlog {node_name}"
```

**After**:
```python
errlog_node_name = self._strip_node_suffix(node_name)
bstool_command_args = f"-errlog {errlog_node_name}"
```

#### 2. `process_node_hierarchical_commands()` - Line ~1315
**Context**: Hierarchical command execution for individual nodes

**Before**:
```python
node_id = self._extract_node_id_from_log_path(token.log_path)
if node_id:
    bstool_command_args = f"-errlog {node_id}"
```

**After**:
```python
node_id = self._extract_node_id_from_log_path(token.log_path)
if node_id:
    errlog_node_id = self._strip_node_suffix(node_id)
    bstool_command_args = f"-errlog {errlog_node_id}"
```

#### 3. `process_bstool_command()` - Line ~1563
**Context**: Individual BsTool command execution from context menu

**Before**:
```python
node_id = self._extract_node_id_from_log_path(log_file_path)
if not node_id:
    return
bstool_command_args = f"-errlog {node_id}"
```

**After**:
```python
node_id = self._extract_node_id_from_log_path(log_file_path)
if not node_id:
    return
errlog_node_id = self._strip_node_suffix(node_id)
bstool_command_args = f"-errlog {errlog_node_id}"
```

## Testing

**Test File**: `tests/test_node_suffix_stripping.py`

### Test Cases
✅ Strip 'm' suffix: `AP01m → AP01`, `BP01m → BP01`  
✅ Strip 'r' suffix: `AP01r → AP01`, `BP01r → BP01`  
✅ No suffix: `AP01 → AP01` (unchanged)  
✅ Edge cases: Single character, empty string, other suffixes  
✅ Command construction: Verify full `-errlog` commands are correct

### Test Results
```
tests/test_node_suffix_stripping.py::test_strip_node_suffix PASSED                    [ 50%]
tests/test_node_suffix_stripping.py::test_bstool_command_construction PASSED          [100%]

============================================= 2 passed in 0.07s ===========================================
```

## Verification

Run the application and test with nodes that have suffixes:

1. **Setup**: Ensure you have nodes with 'm' or 'r' suffixes (e.g., AP01m, AP02r)
2. **Test**: Click "Print All Nodes" or right-click node → "Execute All Print Commands"
3. **Expected**: BsTool should execute successfully with stripped node names
4. **Logs**: Check debug.log for lines like:
   ```
   Phase 3: Executing BsTool with args: -errlog AP01, output to: D:/path/LOG/AP01m_192-168-0-1.log
   ```
   Note: Status message shows `AP01` (stripped), but file path keeps `AP01m` (original)

## Impact

- ✅ **All BsTool executions** now use stripped node names for `-errlog` parameter
- ✅ **No breaking changes** to existing functionality
- ✅ **File paths unchanged** - only the BsTool command parameter is affected
- ✅ **Consistent behavior** across all execution paths (sequential, hierarchical, context menu)

## Files Modified

- `src/commander/presenters/node_tree_presenter.py` - Added `_strip_node_suffix()`, updated 3 locations
- `tests/test_node_suffix_stripping.py` - New test file

## Related

- **BsTool Documentation**: BsTool.exe does not accept node names with suffix letters
- **Node Naming Convention**: 'm' = master, 'r' = redundant (used in deployment, not in BsTool commands)
