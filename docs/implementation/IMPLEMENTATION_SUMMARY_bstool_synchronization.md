# Implementation Summary: BsTool Command Synchronization

**Date**: 2025-10-12  
**Phase**: IMPLEMENT (Phase 5)  
**Feature**: Unified queue-based command execution for BsTool synchronization  
**Status**: Implementation Complete

---

## Problem Statement

### Original Issues
1. **UI Highlight Jumping**: During sequential node processing, Commander window briefly highlighted BsTool command (.log file) first, then jumped back to .fbc command, causing visual confusion
2. **Independent BsTool Execution**: BsTool commands executed independently of FBC/RPC commands, not all .log commands were processed
3. **Legacy Warning Spam**: Constant "BsTool is currently executing, deferring node X processing" warnings every 100ms when BsTool was running

### Root Cause Analysis
Threading model mismatch between command types:
- **FBC/RPC Commands**: Used `CommandQueue` with `QRunnable` workers → **synchronous blocking** via `QThreadPool.start()`
- **BsTool Commands**: Used `threading_service.start_thread()` → **asynchronous** daemon threads that returned immediately
- **Legacy Gate Logic**: `try_acquire_execution()` used simple boolean flag with QTimer retries, flag never cleared after queue integration

This mismatch caused:
1. BsTool subprocess spawned in thread → returned immediately → next FBC file highlighted before BsTool completed → UI jump
2. `_check_sequential_processing_continuation()` checked `is_executing` flag (set/cleared in <1ms) instead of actual subprocess.wait() time (up to 10s)
3. Deferred execution via `_pending_bstool` attempted coordination but timing gaps remained
4. After queue integration, legacy `try_acquire_execution()` check blocked all BsTool commands because flag was never cleared

---

## BsTool Execution Model

### How BsTool Works
BsTool.exe is an **interactive shell application** that displays results and waits for user input:

```python
# BsToolWorker.run() implementation (FIXED - v2)
process = subprocess.Popen([bstool_path] + args, stdin=DEVNULL, stdout=tempfile, stderr=tempfile)
# DO NOT write to stdin - BsTool is interactive and will wait indefinitely
try:
    return_code = process.wait(timeout=10)  # Normal completion
except subprocess.TimeoutExpired:
    # TIMEOUT IS EXPECTED - BsTool displays list and waits for user input
    process.terminate()  # Force close
    return_code = -1
# SUCCESS = tempfile has content (not return_code == 0)
```

**Key Characteristics**:
1. **Interactive shell** - displays list and waits for user input (like a menu)
2. **Timeout is expected behavior** - we force-close it after 10s
3. **Success criteria**: Tempfile has content (not return_code == 0)
4. **stdin=DEVNULL** - prevents BsTool from blocking indefinitely
5. **Output captured to temporary files** during 10s window
6. **Sequential processing continues** even if no output captured

### Debug Session 2 Discovery (2025-10-12)
Initial implementation used `stdin=PIPE` with `write('\n')` + `close()`, expecting BsTool to exit gracefully. This caused:
- Process blocked waiting for more stdin input
- Timeout after 10s → success=False
- Sequential processing stopped at first LOG file

**Root cause**: BsTool is interactive - doesn't exit on `\n`, expects user to manually close it.

**Solution**: Use `stdin=DEVNULL` to signal non-interactive execution + check tempfile content for success (not return_code).

---

## Solution Architecture

### Unified Queue-Based Execution Model

**Core Principle**: All commands (FBC, RPC, BsTool) execute through single `CommandQueue` with `QThreadPool(maxThreadCount=1)` for sequential ordering.

#### Component Changes

##### 1. BsToolWorker (NEW)
**File**: `src/commander/services/bstool_worker.py` (~200 lines)

```python
class BsToolWorker(QRunnable):
    """QRunnable worker for synchronous BsTool execution"""
    
    def run(self):
        # CRITICAL: Synchronous blocking execution
        process = subprocess.Popen(...)
        self.return_code = process.wait(timeout=10)  # Blocks here
        
        # Read tempfiles, write to log_file_path
        # Emit signals: finished, command_completed
```

**Design Decisions**:
- Matches `CommandWorker` pattern used by FBC/RPC
- `run()` method blocks on `subprocess.wait()` → natural synchronization
- Uses `CommandWorkerSignals` for consistency
- Handles tempfile I/O for BsTool's interactive shell output

##### 2. BsToolCommandService (MODIFIED)
**File**: `src/commander/services/bstool_command_service.py`

**Added**:
```python
def __init__(self, log_writer, command_queue, parent=None):
    self.command_queue = command_queue  # Injected dependency
    
def queue_bstool_command(self, log_file_path, bstool_command_args, token):
    """NEW PREFERRED METHOD for BsTool execution"""
    worker = BsToolWorker(bstool_path, bstool_command_args, log_file_path, token, env)
    worker.signals.finished.connect(self._handle_worker_finished)
    worker.signals.command_completed.connect(self._handle_worker_completed)
    self.command_queue.thread_pool.start(worker)  # Submit to queue
```

**Kept for Backward Compatibility**:
- `execute_bstool()` - Used by UI tab for manual commands
- `is_executing` / `try_acquire_execution()` / `release_execution()` - Marked as LEGACY

##### 3. NodeTreePresenter (MODIFIED)
**File**: `src/commander/presenters/node_tree_presenter.py`

**Removed** (~90 lines):
- `_pending_bstool` instance variable and deferred execution mechanism
- `bstool_execution_completed` signal connection
- `_handle_bstool_completed()`, `_check_and_execute_pending_bstool()`, `_execute_pending_bstool()` methods
- `try_acquire_execution()` / `release_execution()` calls throughout
- BsTool-specific `is_executing` checks in `_check_sequential_processing_continuation()`
- Legacy gate-keeping logic in `process_node_print_commands()` (lines 977-981)
- `_pending_bstool` cleanup in `_handle_cancel()`

**Updated**:
```python
def process_node_print_commands(self, node_name):
    # Phase 1: FBC commands
    self.fbc_service.queue_fieldbus_command(...)
    
    # Phase 2: RPC commands
    self.rpc_service.queue_rpc_command(...)
    
    # Phase 3: BsTool command - NOW QUEUED (not threaded)
    self.bstool_service.queue_bstool_command(
        log_file_path=log_file_path,
        bstool_command_args=bstool_command_args,
        token=log_token
    )
    # NO MORE: try_acquire_execution(), QTimer retries, _pending_bstool

def _check_sequential_processing_continuation(self):
    # SIMPLIFIED: Single source of truth for execution state
    if not self.command_queue.is_processing:
        self._process_next_node_in_sequence()
    # NO MORE: self.bstool_service.is_executing checks, QTimer retries
```

##### 4. CommanderWindow (MODIFIED)
**File**: `src/commander/ui/commander_window.py`

```python
# Inject command_queue dependency
self.bstool_service = BsToolCommandService(
    self.log_writer, 
    self.command_queue,  # NEW: Pass queue instance
    self
)
```

---

## Implementation Details

### Signal Flow (New Architecture)

```
User Action → NodeTreePresenter.process_node_print_commands()
    ↓
Phase 1: FBC commands → CommandQueue (QRunnable workers)
    ↓
Phase 2: RPC commands → CommandQueue (QRunnable workers)
    ↓
Phase 3: BsTool command → CommandQueue (BsToolWorker)
    ↓
BsToolWorker.run() → subprocess.wait(timeout=10) [BLOCKS HERE]
    ↓
BsToolWorker signals → finished, command_completed
    ↓
BsToolCommandService._handle_worker_completed() → relays signals
    ↓
NodeTreePresenter.handle_command_completed() → checks queue state
    ↓
QTimer.singleShot(50ms) → _check_sequential_processing_continuation()
    ↓
if not command_queue.is_processing → _process_next_node_in_sequence()
```

### Synchronization Mechanism

**Single Source of Truth**: `CommandQueue._is_processing` (thread-safe with `threading.Lock`)

```python
# CommandQueue manages all commands
class CommandQueue:
    def __init__(self):
        self.thread_pool = QThreadPool()
        self.thread_pool.setMaxThreadCount(1)  # Sequential execution
        self._is_processing = False
        self._lock = threading.Lock()
    
    def start_processing(self):
        with self._lock:
            self._is_processing = True
    
    # Workers emit finished signal when done
    # Last worker calls _on_queue_finished()
    def _on_queue_finished(self):
        with self._lock:
            self._is_processing = False
```

**Benefits**:
- `maxThreadCount=1` guarantees sequential execution order
- No explicit coordination needed between command types
- Natural blocking via `QRunnable.run()` method
- Thread-safe state management via `threading.Lock`

---

## Code Changes Summary

### Files Created
1. **src/commander/services/bstool_worker.py** (200 lines)
   - BsToolWorker(QRunnable) class
   - Synchronous subprocess execution with 10s timeout
   - Tempfile I/O handling for interactive shell output

### Files Modified
1. **src/commander/services/bstool_command_service.py**
   - Added `command_queue` parameter to `__init__`
   - Added `queue_bstool_command()` method (~60 lines)
   - Added `_handle_worker_finished()` and `_handle_worker_completed()` signal handlers
   - Marked legacy methods with comments

2. **src/commander/ui/commander_window.py**
   - Line 88: Injected `command_queue` to BsToolCommandService constructor

3. **src/commander/presenters/node_tree_presenter.py**
   - Removed `_pending_bstool` instance variable (line 99)
   - Removed `bstool_execution_completed` signal connection (line 105)
   - Removed legacy gate-keeping logic in `process_node_print_commands()` (lines 977-981)
   - Simplified `handle_command_completed()` - removed `_pending_bstool` checks
   - Deleted 3 legacy methods: `_handle_bstool_completed()`, `_check_and_execute_pending_bstool()`, `_execute_pending_bstool()` (~85 lines)
   - Updated `process_node_print_commands()` Phase 3 to use `queue_bstool_command()`
   - Simplified `_check_sequential_processing_continuation()` - removed `is_executing` checks and QTimer retries
   - Removed `_pending_bstool` cleanup in `_handle_cancel()`

**Total Changes**: +280 lines added, ~90 lines removed, 4 files modified

---

## Testing Requirements

### Unit Tests Needed
1. **test_bstool_worker.py**
   - Verify `run()` blocks until subprocess completes
   - Test 10-second timeout handling
   - Verify tempfile cleanup on success/failure
   - Test signal emission order (finished → command_completed)

2. **test_sequential_command_synchronization.py**
   - Multi-node workflow with FBC + RPC + BsTool commands
   - Verify sequential execution order (no parallelism)
   - Test UI highlight stability during node transitions
   - Verify `command_queue.is_processing` state management

3. **test_bstool_integration.py**
   - Test BsToolCommandService.queue_bstool_command()
   - Verify signal relay from worker to service
   - Test backward compatibility with execute_bstool() (UI tab)

### Integration Tests
1. **Manual Test: Print All Nodes**
   - Load multi-node configuration (3+ nodes with FBC, RPC, LOG tokens)
   - Execute "Print All Nodes" workflow
   - Verify Commander window highlight stays on current file (no jumping)
   - Verify logs show sequential execution: FBC → RPC → BsTool → next node
   - Verify no "BsTool is currently executing, deferring" warnings

2. **Manual Test: BsTool Tab**
   - Execute manual BsTool command from UI tab
   - Verify backward compatibility (execute_bstool() still works)
   - Verify output appears in BsTool tab console

---

## Legacy Code Cleanup

### Removed Mechanisms
1. **Deferred Execution** (`_pending_bstool`)
   - QTimer.singleShot(50ms) delays with retry logic
   - Node/token storage for deferred processing
   - `_check_and_execute_pending_bstool()` polling

2. **Async Threading** (`threading_service.start_thread()`)
   - Daemon threads that returned immediately
   - No natural synchronization point
   - Race conditions with UI updates

3. **Legacy Gate-Keeping** (`try_acquire_execution()`)
   - Simple boolean flag with threading.Lock
   - QTimer.singleShot(100ms) retries causing spam warnings
   - Flag never cleared after queue integration

### Kept for Backward Compatibility
1. **BsToolCommandService.execute_bstool()**
   - Used by BsTool UI tab for manual commands
   - Still uses threading model for non-queue execution
   - NOT used by sequential processing workflow

2. **Legacy State Methods**
   - `is_executing` property
   - `try_acquire_execution()` method
   - `release_execution()` method
   - Marked with comments: "LEGACY - kept for backward compatibility"

---

## Migration Notes

### Breaking Changes
**None** - Backward compatibility maintained for UI tab usage.

### Behavioral Changes
1. BsTool commands now execute **synchronously** (blocking) via CommandQueue
2. Sequential processing no longer shows "deferring" warnings
3. UI highlight remains stable during node transitions (no jumping)
4. All commands respect `maxThreadCount=1` sequential order

### Configuration Changes
**None** - No config file updates required.

---

## Future Improvements

### Phase 1 Enhancements (Optional)
1. Remove legacy `execute_bstool()` method after UI tab refactored to use queue
2. Delete `is_executing`, `try_acquire_execution()`, `release_execution()` methods
3. Simplify `BsToolCommandService` to single execution model

### Phase 2 Enhancements (Performance)
1. Increase `maxThreadCount` for parallel FBC/RPC execution (keep BsTool sequential)
2. Add priority queue for urgent commands
3. Implement command cancellation support

### Phase 3 Enhancements (Observability)
1. Add metrics: command execution times, queue depth, success rates
2. Enhanced logging: execution traces with correlation IDs
3. UI progress indicator showing command queue position

---

## References

### Related Documents
- `docs/architecture/ARCH_command_queue.md` - CommandQueue design patterns
- `docs/blueprints/BLUEPRINT_sequential_processing.md` - Multi-node workflow architecture
- `logs/workflow_sequential_command_sync_20251012_*.md` - Complete workflow reconstruction

### Memory Entities
- `Project.Commander.Command.Method_queue_bstool_command` - New preferred BsTool execution method
- `Project.Commander.Command.Feature_BsToolWorker` - QRunnable-based synchronous worker
- `Global.Architecture.Patterns.Pattern_UnifiedQueueExecution` - Single execution model pattern

### Code References
- `src/commander/services/bstool_worker.py` - BsToolWorker implementation
- `src/commander/services/bstool_command_service.py` - Service layer integration
- `src/commander/presenters/node_tree_presenter.py` - Orchestration logic
- `src/commander/command_queue.py` - Queue infrastructure

---

**Implementation Status**: ✅ Complete  
**Tests Status**: ⏳ Pending (Phase 7)  
**Documentation Status**: ✅ Complete  
**Memory Persistence**: ⏳ Pending (Phase 8)
