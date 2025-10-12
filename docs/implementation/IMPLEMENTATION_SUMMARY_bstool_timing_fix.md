# Implementation Summary: BsTool Timing Fix

**Date**: 2025-10-12  
**Feature**: Deferred BsTool Execution Timing Fix  
**Status**: ✅ Completed  
**Files Modified**: `src/commander/presenters/node_tree_presenter.py`

---

## Problem Statement

BsTool commands were not executing in sequential workflows after FBC/RPC commands completed. The workflow would stop at the point where BsTool should execute, with logs showing the queue appeared busy when it should have been idle.

**User Report**: "now bstool doesnt run at all (once we get to bstool command sequence stops)"

---

## Root Cause Analysis

**Signal Timing Race Condition** in `command_queue.py`:

1. **Line 372**: `command_completed` signal emitted after FBC/RPC command finishes
2. **Lines 373-400**: 28 lines of code execute (progress updates, active command checks, pending command checks)
3. **Lines 401-404**: `_is_processing` flag reset to `False` (29 lines after signal emission)

**The Problem**: `handle_command_completed()` in `node_tree_presenter.py` immediately checked `command_queue.is_processing` upon receiving the signal, but the flag hadn't been reset yet because 29 lines of code were still executing. The check saw `_is_processing=True` (stale state) and decided not to execute the pending BsTool command.

**Timeline**:
```
T+0ms:   Signal emitted (line 372)
T+0ms:   handle_command_completed() receives signal
T+0ms:   Checks is_processing → TRUE (premature check)
T+Xms:   29 lines execute
T+Xms:   Flag resets to FALSE (too late)
```

---

## Solution Architecture

**QTimer Event Loop Delay Pattern**

Instead of immediately checking queue state, schedule a delayed check to allow async state transitions to complete:

```python
# OLD (immediate check - sees stale state)
if self._pending_bstool and not self.command_queue.is_processing:
    self._execute_pending_bstool()

# NEW (delayed check - sees fresh state)
if self._pending_bstool:
    QTimer.singleShot(50, self._check_and_execute_pending_bstool)
```

**Why This Works**:
1. Signal emits → `handle_command_completed()` called
2. QTimer schedules callback 50ms in future
3. Function returns, allowing event loop to continue
4. 29 lines of code execute in `command_queue._handle_worker_finished()`
5. `_is_processing` flag resets to `False`
6. Event loop processes pending signals/slots
7. 50ms later, QTimer fires → `_check_and_execute_pending_bstool()` called
8. Check sees `is_processing=False` (correct state)
9. BsTool execution proceeds

---

## Implementation Details

### Modified File: `src/commander/presenters/node_tree_presenter.py`

#### Change 1: Modified `handle_command_completed()` (lines 403-409)

Added QTimer delay before checking queue state:

```python
# After sequential processing check, schedule deferred BsTool check if pending
# NOTE: Use QTimer delay to allow command_queue's _is_processing flag to reset
# The flag is set in _handle_worker_finished() 29 lines AFTER command_completed signal
# emits (line 372 signal, lines 401-404 flag reset). Without delay, we check too early.
if self._pending_bstool:
    logging.debug("handle_command_completed: Pending BsTool found, scheduling delayed check")
    QTimer.singleShot(50, self._check_and_execute_pending_bstool)
```

#### Change 2: Added `_check_and_execute_pending_bstool()` helper (lines 506-524)

New method performs delayed validation:

```python
def _check_and_execute_pending_bstool(self):
    """
    Delayed check for pending BsTool execution after queue becomes idle.
    Called via QTimer.singleShot to allow async state transitions to complete.
    """
    if not self._pending_bstool:
        logging.debug("_check_and_execute_pending_bstool: No pending BsTool (already executed or cleared)")
        return
    
    is_busy = self.command_queue.is_processing
    logging.debug(f"_check_and_execute_pending_bstool: Queue state check - is_processing={is_busy}")
    
    if not is_busy:
        logging.info("_check_and_execute_pending_bstool: Queue idle, executing pending BsTool")
        self._execute_pending_bstool()
    else:
        logging.warning("_check_and_execute_pending_bstool: Queue still busy after delay, will retry on next completion")
```

#### Change 3: Fixed API signature in `_execute_pending_bstool()` (lines 542-544)

Removed incorrect callback parameters (completion handled via signal):

```python
# Execute BsTool command
# Note: Completion is handled via bstool_execution_completed signal connected in __init__
logging.info(f"_execute_pending_bstool: Executing BsTool for node {node_name} (deferred execution triggered)")
self.bstool_service.execute_bstool(
    log_file_path=log_file_path,
    bstool_command_args=bstool_command_args
)
```

**API Correction**: `execute_bstool()` accepts only 2 parameters (`log_file_path`, `bstool_command_args`). Completion notification happens via `bstool_execution_completed` signal connected at line 108.

---

## Testing & Validation

### User Manual Test
**Result**: ✅ SUCCESS

User executed full sequential workflow (FBC → RPC → BsTool). Logs confirmed:
- **Timing Fix Works**: Queue reset at `.007s`, delayed check at `.055s` (48ms later)
- **Queue Idle Detected**: "Queue idle, executing pending BsTool" logged correctly
- **BsTool Executed**: Command processed successfully

### Syntax Validation
**Tool**: `python -m py_compile`  
**Result**: ✅ SUCCESS (no syntax errors)

---

## Key Learnings

### Pattern: Event Loop Delay for Async State
Use `QTimer.singleShot(delay_ms, callback)` when:
- Signal emission and state transition are separated by code execution
- Immediate checks would see stale state
- Need to guarantee async state synchronization

**Empirical Validation**: 50ms delay sufficient (user test showed 48ms actual delay)

### Pattern: Signal-Based Completion
PyQt services should use signals for async completion, not callbacks:
- **Signals**: Decouple caller from handler, cleaner API, multiple handlers possible
- **Callbacks**: Pollute method signatures, tight coupling, single handler

### Anti-Pattern Caught
Passing `callback=` and `log_token=` parameters to `execute_bstool()` caused `TypeError`. The signal connection already existed - callback parameters were redundant.

---

## Future Considerations

### Known Issues (Added to TODO.md)
1. **LOG File Color Persistence**: Path normalization mismatch prevents color updates
2. **UI Highlight Jump**: Visual glitch shows BsTool .log file before FBC command during node transitions (cosmetic only)

### Delay Tuning
50ms empirically works but could be optimized:
- **Too Short**: Might miss flag reset on slower systems
- **Too Long**: Unnecessary delay in workflow
- **Alternative**: Subscribe to dedicated "queue_idle" signal instead of polling

---

## Artifacts

**Modified Files**:
- `src/commander/presenters/node_tree_presenter.py` (+30 lines, 3 changes)

**Added to Memory**:
- `Project.Commander.BsTool.Feature_DeferredExecutionTimingFix`
- `Project.Commander.BsTool.Method_CheckAndExecutePendingBstool`
- `Global.PyQt5.Pattern_EventLoopDelayForAsyncState`
- `Project.Commander.BsTool.Pattern_SignalBasedCompletion`

**Documentation**:
- `TODO.md` updated with UI highlight jump bugfix entry

**Workflow Log**: `logs/workflow_bstool_timing_fix_20251012_[timestamp].md` (pending)

---

## Completion Checklist

- [x] Root cause identified (29-line timing gap)
- [x] Solution designed (QTimer delay pattern)
- [x] Implementation complete (3 changes in node_tree_presenter.py)
- [x] Syntax validated (py_compile)
- [x] User tested (manual workflow validation)
- [x] Learnings persisted (project_memory.json +13 lines)
- [x] Documentation created (this file)
- [x] TODO.md updated (UI bug documented)
- [ ] Workflow log complete (Phase 10: LOG)

---

**Status**: Feature complete and validated. Workflow transitions smoothly from FBC/RPC to BsTool execution without stopping.
