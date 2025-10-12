# ⚙️ Command System Architecture

<!-- METADATA -->
metadata: {
  created_date: "2025-10-08_165200",
  last_modified: "2025-10-08_165200",
  last_accessed: "2025-10-08_165200",
  word_count: 3847,
  reference_count: 5,
  document_hash: "command_system_arch_consolidated",
  obsolete_check_date: "2025-10-08",
  section_count: 9,
  internal_link_count: 24
}
<!-- /METADATA -->

## 📑 Table of Contents

- [Overview](#overview)
- [System Architecture](#system-architecture)
- [Command Queue System](#command-queue-system)
- [Sequential Command Processor](#sequential-command-processor)
- [Command Services](#command-services)
- [Hierarchical Command Execution](#hierarchical-command-execution)
- [Integration Points](#integration-points)
- [Error Handling & Recovery](#error-handling--recovery)
- [Performance & Optimization](#performance--optimization)

---

## 🎯 Overview

The Command System provides comprehensive command execution infrastructure for the LOGReport application, including queuing, sequential processing, protocol-specific services (FBC/RPC/BsTool), hierarchical execution, and resource management. The system is designed for reliability, supporting both single command execution and batch processing with proper error isolation.

### Key Features

| Feature | Description | Benefit |
|---------|-------------|---------|
| **Command Queue** | Thread-safe FIFO queue with priorities | Organized execution |
| **Sequential Processing** | Memory-optimized iterative execution | Prevents overload |
| **Protocol Services** | FBC/RPC/BsTool command handlers | Protocol abstraction |
| **Hierarchical Execution** | Nested sub-command workflows | Complex operations |
| **Error Isolation** | Per-command failure handling | Reliability |
| **Resource Management** | Connection pooling, cleanup | Efficiency |
| **Circuit Breaker** | Automatic failure detection | System protection |

### System Scope

- **Primary Use**: Command execution and orchestration
- **Secondary Use**: Batch processing and workflow management
- **Integration**: Works with [Node System](ARCH_node_system.md#command-integration), [Token Management](../technical/TECH_token_management.md#command-service-integration), and [Logging System](ARCH_logging_system.md#command-based-logging)

---

## 🏗️ System Architecture

The Command System follows a layered architecture with clear separation between queuing, processing, and execution:

```
┌─────────────────────────────────────────────────────┐
│               UI Layer                               │
│  Context Menu | Commander Window | Buttons          │
└─────────────────────┬───────────────────────────────┘
                      │
         ┌────────────▼────────────┐
         │  Command Orchestration  │
         │  - Hierarchical Service │
         │  - Sequential Processor │
         └────────────┬────────────┘
                      │
         ┌────────────▼────────────┐
         │    Command Queue        │
         │  - Priority Queue       │
         │  - Thread-safe FIFO     │
         │  - Signal Emitters      │
         └────────────┬────────────┘
                      │
         ┌────────────▼─────────────────────┐
         │    Protocol Services              │
         │  ┌──────────┬──────────┬────────┐│
         │  │   FBC    │   RPC    │ BsTool ││
         │  │ Service  │ Service  │ Service││
         │  └──────────┴──────────┴────────┘│
         └───────────────┬──────────────────┘
                         │
         ┌───────────────▼──────────────┐
         │   Execution Layer             │
         │  Telnet | SSH | Process      │
         └───────────────┬──────────────┘
                         │
         ┌───────────────▼──────────────┐
         │   Logging & Results           │
         │  Token Logs | Status Updates │
         └──────────────────────────────┘
```

### Component Responsibilities

| Component | Responsibility | Output |
|-----------|----------------|--------|
| **UI Layer** | User interaction, command initiation | Command requests |
| **Hierarchical Service** | Complex workflows, sub-commands | Execution plans |
| **Sequential Processor** | Memory-optimized batch processing | Execution results |
| **Command Queue** | Thread-safe queuing, prioritization | Command streams |
| **Protocol Services** | Protocol-specific execution | Command results |
| **Execution Layer** | Low-level communication | Raw responses |
| **Logging Layer** | Result persistence, status updates | Log files, UI updates |

---

## 📋 Command Queue System

The `CommandQueue` provides thread-safe, signal-based command queuing with automatic completion tracking.

### Queue Architecture

```python
from PyQt6.QtCore import QObject, pyqtSignal, QMutex, QMutexLocker
from typing import List, Optional, Tuple
from collections import deque

class CommandQueue(QObject):
    """
    Thread-safe FIFO command queue with signal-based notifications.
    
    Signals:
        command_completed(node_name, token_id, success): Emitted when command finishes
        progress_updated(current, total): Emitted for progress tracking
        all_commands_completed(): Emitted when queue is empty
    """
    
    # Signals
    command_completed = pyqtSignal(str, str, bool)  # node_name, token_id, success
    progress_updated = pyqtSignal(int, int)  # current, total
    all_commands_completed = pyqtSignal()
    
    def __init__(self, parent=None):
        """Initialize command queue."""
        super().__init__(parent)
        self._queue = deque()
        self._mutex = QMutex()
        self._total_commands = 0
        self._completed_commands = 0
        self._auto_cleanup = False  # Manual cleanup by default
    
    def add_command(self, command: str, token: 'NodeToken', 
                   telnet_client: Optional[object] = None) -> None:
        """
        Add command to queue.
        
        Args:
            command: Command string to execute
            token: NodeToken with execution context
            telnet_client: Optional telnet client to reuse
        """
        with QMutexLocker(self._mutex):
            self._queue.append((command, token, telnet_client))
            self._total_commands += 1
            logging.debug(f"Command queued: {command} for token {token.token_id}")
    
    def get_next_command(self) -> Optional[Tuple[str, 'NodeToken', Optional[object]]]:
        """
        Retrieve next command from queue (FIFO).
        
        Returns:
            Tuple of (command, token, telnet_client) or None if empty
        """
        with QMutexLocker(self._mutex):
            if self._queue:
                return self._queue.popleft()
            return None
    
    def mark_command_completed(self, node_name: str, token_id: str, 
                              success: bool) -> None:
        """
        Mark command as completed and emit signals.
        
        Args:
            node_name: Node name for status updates
            token_id: Token ID that completed
            success: Whether command succeeded
        """
        self._completed_commands += 1
        
        # Emit completion signal
        self.command_completed.emit(node_name, token_id, success)
        
        # Emit progress signal
        self.progress_updated.emit(self._completed_commands, self._total_commands)
        
        # Check if all commands completed
        if self._completed_commands >= self._total_commands:
            self.all_commands_completed.emit()
            if self._auto_cleanup:
                self.reset()
    
    def set_auto_cleanup(self, enabled: bool) -> None:
        """Enable/disable automatic queue cleanup after completion."""
        self._auto_cleanup = enabled
    
    def manual_cleanup(self) -> None:
        """Manually reset queue state."""
        with QMutexLocker(self._mutex):
            self._queue.clear()
            self._total_commands = 0
            self._completed_commands = 0
    
    def is_empty(self) -> bool:
        """Check if queue is empty."""
        with QMutexLocker(self._mutex):
            return len(self._queue) == 0
    
    def size(self) -> int:
        """Get current queue size."""
        with QMutexLocker(self._mutex):
            return len(self._queue)
```

### Queue Usage

```python
# Initialize queue
command_queue = CommandQueue()

# Connect signals
command_queue.command_completed.connect(handle_completion)
command_queue.progress_updated.connect(update_progress_bar)
command_queue.all_commands_completed.connect(show_completion_message)

# Add commands
for token in tokens:
    command = f"print from fbc io structure {token.token_id}0000"
    command_queue.add_command(command, token, None)

# Process commands
while not command_queue.is_empty():
    cmd, token, client = command_queue.get_next_command()
    success = execute_command(cmd, token, client)
    command_queue.mark_command_completed(token.node_name, token.token_id, success)
```

---

## 🔄 Sequential Command Processor

The `SequentialCommandProcessor` handles memory-optimized, iterative batch processing with per-token error isolation.

### Processor Architecture

```python
class SequentialCommandProcessor(QObject):
    """Processor for sequential execution of FBC/RPC commands with resource management."""
    
    # Signals
    status_message = pyqtSignal(str, int)  # message, duration
    progress_updated = pyqtSignal(int, int)  # current, total
    processing_finished = pyqtSignal(int, int)  # success_count, total_count
    
    def __init__(self, command_queue: CommandQueue, 
                 fbc_service: 'FbcCommandService',
                 rpc_service: 'RpcCommandService', 
                 session_manager: 'SessionManager',
                 logging_service: 'LoggingService',
                 parent=None):
        """
        Initialize sequential processor.
        
        Args:
            command_queue: Command queue for execution
            fbc_service: FBC command service
            rpc_service: RPC command service
            session_manager: Session management
            logging_service: Logging service for token logs
        """
        super().__init__(parent)
        self.command_queue = command_queue
        self.fbc_service = fbc_service
        self.rpc_service = rpc_service
        self.session_manager = session_manager
        self.logging_service = logging_service
        
        # Disable auto cleanup - use manual control
        self.command_queue.set_auto_cleanup(False)
        
        # Connect signals
        self.command_queue.command_completed.connect(self._on_command_completed)
        self.command_queue.progress_updated.connect(self._on_progress_updated)
        
        # Processing state
        self._is_processing = False
        self._total_commands = 0
        self._completed_commands = 0
        self._success_count = 0
        self._current_token_index = 0
        self._tokens = []
        self._node_name = ""
        self._batch_id = ""
```

### Sequential Processing Methods

```python
def process_tokens_sequentially(self, node_name: str, 
                               tokens: List['NodeToken'],
                               action: str = "print") -> None:
    """
    Process multiple tokens sequentially with individual context.
    
    This method simulates user-initiated right-click execution for each token,
    maintaining individual context and error isolation. Each token gets its own
    log file and error handling, ensuring failures don't prevent subsequent
    token processing.
    
    Args:
        node_name: Name of node containing tokens
        tokens: List of NodeToken objects to process
        action: Action for RPC tokens ("print" or "clear")
    
    Example:
        >>> processor.process_tokens_sequentially(
        ...     node_name="AP01m",
        ...     tokens=[
        ...         NodeToken(token_id="162", token_type="FBC"),
        ...         NodeToken(token_id="163", token_type="RPC")
        ...     ]
        ... )
        # Processes 162_FBC.log then 163_RPC.log with individual contexts
    """
    if self._is_processing:
        self.logger.warning("Already processing commands")
        self.status_message.emit("Already processing commands", 3000)
        return
    
    self._is_processing = True
    self._total_commands = len(tokens)
    self._completed_commands = 0
    self._success_count = 0
    self._current_token_index = 0
    self._tokens = list(tokens)
    self._node_name = node_name
    self._action = action
    self._batch_id = self._generate_batch_id()
    
    if not tokens:
        self.logger.info("No tokens to process")
        self._finish_processing()
        return
    
    self.status_message.emit(f"Processing {len(tokens)} commands...", 0)
    self.logger.info(f"Starting sequential processing of {len(tokens)} tokens for node {node_name}")
    
    # Start batch logging
    self.logging_service.start_batch_logging(
        batch_id=self._batch_id,
        node_name=node_name,
        token_count=len(tokens)
    )
    
    # Process first token to start the chain
    self._process_next_token()

def _process_next_token(self) -> None:
    """Process the next token in sequence."""
    if self._current_token_index >= len(self._tokens):
        # All tokens processed
        self._finish_processing()
        return
    
    token = self._tokens[self._current_token_index]
    
    # Prepare token context
    context = self._prepare_token_context(token, self._batch_id)
    
    # Execute token command
    try:
        success, error = self._execute_token(token, context)
        
        if success:
            self._success_count += 1
        else:
            self.logger.error(f"Token {token.token_id} failed: {error}")
    
    except Exception as e:
        self.logger.error(f"Exception processing token {token.token_id}: {str(e)}")
    
    # Move to next token
    self._current_token_index += 1
    self._completed_commands += 1
    
    # Update progress
    self.progress_updated.emit(self._completed_commands, self._total_commands)
    
    # Continue with next token (small delay for UI updates)
    QTimer.singleShot(50, self._process_next_token)

def _prepare_token_context(self, token: 'NodeToken', batch_id: str) -> dict:
    """
    Prepare execution context for token.
    
    Returns:
        Dict with normalized_token, log_path, batch_id, action
    """
    # Normalize token ID
    normalized_token = self._normalize_token(token.token_id, token.token_type)
    
    # Open log file for this token
    log_path = self.logging_service.open_log_for_token(
        token.token_id,
        token.token_type,
        batch_id
    )
    
    return {
        'normalized_token': normalized_token,
        'log_path': log_path,
        'batch_id': batch_id,
        'action': getattr(self, '_action', 'print')
    }

def _execute_token(self, token: 'NodeToken', context: dict) -> Tuple[bool, Optional[str]]:
    """
    Execute token command with proper error handling.
    
    Args:
        token: Token to execute
        context: Execution context from _prepare_token_context
    
    Returns:
        Tuple of (success, error_message)
    """
    try:
        if token.token_type == "FBC":
            self.fbc_service.queue_fieldbus_command(
                self._node_name,
                context['normalized_token'],
                telnet_client=None
            )
            return True, None
        
        elif token.token_type == "RPC":
            self.rpc_service.queue_rpc_command(
                self._node_name,
                context['normalized_token'],
                context.get('action', 'print'),
                telnet_client=None
            )
            return True, None
        
        else:
            error_msg = f"Unknown token type: {token.token_type}"
            return False, error_msg
    
    except Exception as e:
        error_msg = f"Error executing {token.token_type} command: {str(e)}"
        self.logger.error(error_msg)
        return False, error_msg

def _finish_processing(self) -> None:
    """Finish processing and cleanup."""
    self._is_processing = False
    
    # Close batch logging
    self.logging_service.end_batch_logging(self._batch_id)
    
    # Manual cleanup
    self.command_queue.manual_cleanup()
    
    # Emit completion signal
    self.processing_finished.emit(self._success_count, self._total_commands)
    
    # Status message
    self.status_message.emit(
        f"Processing complete: {self._success_count}/{self._total_commands} succeeded",
        5000
    )
    
    self.logger.info(f"Sequential processing complete: {self._success_count}/{self._total_commands} succeeded")
```

### Circuit Breaker Integration

```python
from ..utils.circuit_breaker import CircuitBreaker

def process_sequential_batch(self, tokens: List['NodeToken'],
                            protocol: str,
                            command_spec: dict) -> List['CommandResult']:
    """
    Process tokens with circuit breaker protection.
    
    Circuit breaker triggers after 3 consecutive failures,
    preventing cascade failures.
    """
    results = []
    consecutive_failures = 0
    batch_id = self._generate_batch_id()
    
    for i, token in enumerate(tokens):
        # Check circuit breaker
        if consecutive_failures >= 3:
            self.logger.error("Circuit breaker triggered after 3 consecutive failures")
            break
        
        # Process token
        context = self._prepare_token_context(token, batch_id)
        success, error = self._execute_token(token, context)
        
        # Track failures
        if success:
            consecutive_failures = 0
        else:
            consecutive_failures += 1
        
        # Record result
        results.append(CommandResult(
            token=token.token_id,
            success=success,
            error=error,
            log_path=context['log_path']
        ))
        
        # Periodic cleanup
        if (i + 1) % 10 == 0:
            self._perform_periodic_cleanup()
    
    return results
```

---

## ⚡ Advanced Execution Patterns

**Purpose**: Advanced command execution strategies for complex workflows  
**Scope**: Deferred execution, system mode validation, memory optimization

### Deferred BsTool Execution

**Problem**: BsTool commands executing in parallel with FBC/RPC instead of sequentially

**Pattern**: Store execution info when queuing, trigger when queue idle

#### Implementation

**Pending Execution Tracker** (`node_tree_presenter.py` line 101):
```python
self._pending_bstool = None  # Dict: {node_name, log_file_path, bstool_command_args, log_token}
```

**Smart Execution Decision** (Phase 3 of `process_node_print_commands()`):
```python
# Phase 3: Execute BsTool for LOG files
log_tokens = self._get_tokens_for_node(node, "LOG")

if log_tokens:
    # Check if FBC or RPC commands exist
    fbc_tokens = self._get_tokens_for_node(node, "FBC")
    rpc_tokens = self._get_tokens_for_node(node, "RPC")
    
    has_queue_commands = (fbc_tokens and len(fbc_tokens) > 0) or (rpc_tokens and len(rpc_tokens) > 0)
    
    if has_queue_commands:
        # DEFER: FBC/RPC commands exist, wait for queue to complete
        self._pending_bstool = {
            'node_name': node_name,
            'log_file_path': log_file_path,
            'bstool_command_args': bstool_command_args,
            'log_token': log_token
        }
        logging.info(f"DEFERRED BsTool execution for {node_name} (waiting for FBC/RPC queue)")
    else:
        # IMMEDIATE: No FBC/RPC commands, execute BsTool now
        logging.info(f"Executing BsTool IMMEDIATELY for {node_name} (no queue commands)")
        self.bstool_service.execute_bstool(log_file_path, bstool_command_args)
```

**Execution Trigger** (`handle_command_completed()` lines 400-405):
```python
def handle_command_completed(self, node_name: str, token_id: str, success: bool):
    """Handle command completion from queue."""
    # ... existing completion logic ...
    
    # Check if BsTool execution was deferred and queue is now idle
    if self._pending_bstool is not None and not self.command_queue.is_processing:
        logging.info("Queue idle and pending BsTool detected - executing now")
        self._execute_pending_bstool()
```

**Execution Flow**:
```
process_node_print_commands(node_A)
    ↓
Phase 1: Queue FBC commands (if exist)
    ↓
Phase 2: Queue RPC commands (if exist)
    ↓
Phase 3: Check FBC/RPC exist?
    ↓ (Yes - commands queued)
Store in _pending_bstool
    ↓
CommandQueue processes FBC commands
    ↓ (each completion)
handle_command_completed() checks:
    - _pending_bstool not None?
    - command_queue.is_processing == False?
    ↓ (Both True)
_execute_pending_bstool()
    ↓
Extract pending info → Clear _pending_bstool → Execute BsTool
```

**Benefits**:
- True sequential execution (FBC → RPC → BsTool)
- No race conditions between queue and BsTool
- Proper cleanup on workflow cancellation
- Memory-efficient (single pending dict, not queue)

**Related**: See [IMPL_bstool_evolution.md#phase-5](../implementation/IMPL_bstool_evolution.md#phase-5-complete-integration) for complete implementation history

---

### System Mode Validation

**Problem**: Telnet commands require system mode, but verifying mode with toggle loop was unreliable

**Pattern**: Guaranteed single `systemmode` command for debugger initialization

#### Implementation

**Session Initialization Sequence** (`session_manager.py` lines 165-200):
```python
def _initialize_session(self) -> bool:
    """
    Initialize telnet session with guaranteed system mode entry.
    
    Sequence:
        1. Send 'yes' + wait 1.0s + clear buffer
        2. Send CTRL+Z + wait 0.5s + clear buffer
        3. Send 'systemmode' + wait 0.5s + set mode
    
    Returns:
        True if initialization successful
    """
    try:
        # Step 1: Accept license
        self.connection.write(b'yes\r\n')
        time.sleep(1.0)
        self.connection.read_very_eager()  # Clear buffer
        
        # Step 2: Exit any active mode
        self.connection.write(b'\x1a')  # CTRL+Z
        time.sleep(0.5)
        self.connection.read_very_eager()  # Clear buffer
        
        # Step 3: Enter system mode (guaranteed single command)
        self.connection.write(b'systemmode\r\n')
        time.sleep(0.5)
        self.current_mode = 'system'
        
        return True
    except Exception as e:
        self.logger.error(f"Session initialization failed: {e}")
        return False
```

**Before** (40+ lines of toggle loop):
```python
# Complex loop with response checking
for attempt in range(max_toggles):
    self.connection.write(b'toggle\r\n')
    time.sleep(2.0)
    toggle_response = self.connection.read_very_eager().decode('ascii', 'ignore')
    if 'System Commands' in toggle_response:
        self.current_mode = 'system'
        return True
    # ... pattern matching for %s, %a, etc.
```

**After** (3 lines):
```python
# Single guaranteed command
self.connection.write(b'systemmode\r\n')
time.sleep(0.5)
self.current_mode = 'system'
return True
```

**Benefits**:
- Reliable initialization (no pattern matching failures)
- Faster connection (no 5+ toggle attempts)
- Simpler code (3 lines vs 40+ lines)
- Predictable behavior (always enters system mode)

**Test Results**: 21/21 tests passed (previously had intermittent failures)

**Related**: See [IMPLEMENTATION_SUMMARY_systemmode_command.md](../implementation/IMPLEMENTATION_SUMMARY_systemmode_command.md) for original implementation

---

### Memory-Optimized Cleanup

**Problem**: Project memory cluttered with organizational metadata and low-value entities

**Pattern**: Intelligent cleanup phase removing meta entities without workflow value

#### Cleanup Categories

**Always Remove**:
1. **MemoryType entities** (e.g., `Project.MemoryType.UI`) - organizational metadata
2. **Cluster/Domain/Type meta entities** (e.g., `Project.System.Project_Cluster`) - hierarchy represented via relations
3. **Generic documentation** (README/TODO extracts without unique insights)
4. **Low-value entities** (<2 observations or all <25 chars)
5. **Obsolete entities** (no refs 90+ days)

**Conditionally Process**:
- **Verbose entities** (>500 chars) - CONDENSE
- **Disconnected entities** - REVIEW (may have value)

#### Implementation

**Cleanup Phase in Workflow** (`update_memory.md`):
```
PRE-PHASE: INVENTORY→VALIDATION
    ↓
CLEANUP PHASE (NEW):
    1. Analyze removal candidates (analyze_memory_cleanup.py)
    2. Categorize entities by removal reason
    3. Automated cleanup (Phase 1 of unified_memory_optimizer.py)
    4. Manual review for disconnected entities
    5. Output cleanup report with reasons + backup
    ↓
PROJECT PHASES (1-8): Analysis→Implementation
    ↓
GLOBAL PHASES (9-16): Analysis→Implementation
    ↓
POST-PHASE: VERIFICATION→COMPARISON
```

**Analysis Script** (`scripts/analyze_memory_cleanup.py`):
```python
# Standalone analysis tool (does NOT modify memory)
python scripts/analyze_memory_cleanup.py

# Output Example:
# META TYPES: 33 entities
# CLUSTER META: 37 entities
# DOMAIN META: 2 entities
# GENERIC DOCUMENTATION: 6 entities
# LOW VALUE: 2 entities
# DISCONNECTED: 6 entities
# VERBOSE: 10 entities
#
# TOTAL REMOVAL CANDIDATES: 97 / 250 (38.8%)
```

**Automated Cleanup** (Phase 1 of `unified_memory_optimizer.py`):
```python
def cleanup_phase(memory_data: dict) -> dict:
    """
    Remove organizational metadata and low-value entities.
    
    Returns:
        Cleaned memory data with removal report
    """
    removed = {
        'meta_types': [],
        'cluster_meta': [],
        'low_value': [],
        'obsolete': []
    }
    
    for entity in memory_data['entities']:
        # Remove MemoryType entities
        if 'MemoryType' in entity['name']:
            removed['meta_types'].append(entity['name'])
            continue
        
        # Remove Cluster meta entities
        if '_Cluster' in entity['name'] or '_Domain' in entity['name']:
            removed['cluster_meta'].append(entity['name'])
            continue
        
        # Remove low-value entities
        obs_count = len(entity.get('observations', []))
        if obs_count < 2:
            removed['low_value'].append(entity['name'])
            continue
    
    # Generate cleanup report
    return {
        'cleaned_data': memory_data,
        'removed': removed,
        'stats': {
            'before': len(memory_data['entities']),
            'after': len(memory_data['entities']) - sum(len(v) for v in removed.values()),
            'reduction': f"{sum(len(v) for v in removed.values()) / len(memory_data['entities']) * 100:.1f}%"
        }
    }
```

**Results** (LOGReport project):
- Before: 250 entities
- After: 193 entities  
- Reduction: 22.4% (57 entities removed)
- Categories: 33 MemoryType + 37 Cluster meta + 6 generic docs + 2 low-value

**Benefits**:
- Cleaner memory queries (no meta entity noise)
- Better signal-to-noise ratio (high-value entities only)
- Faster memory loading (22% fewer entities)
- Easier maintenance (less clutter to review)

**Related**: See [IMPLEMENTATION_SUMMARY_memory_cleanup.md](../implementation/IMPLEMENTATION_SUMMARY_memory_cleanup.md) for detailed analysis

---

### Sequential Command Queue Fix

**Problem**: Command queue processed all commands in parallel instead of sequentially

**Pattern**: Process one command at a time, trigger next only after current completes

#### Key Changes

**Before** (`command_queue.py` `start_processing()`):
```python
# Marked ALL commands as processing
for idx, item in enumerate(pending_commands):
    item.status = 'processing'

# Started ALL workers
for idx, item in enumerate(pending_commands):
    worker = CommandWorker(...)
    self.thread_pool.start(worker)
```

**After** (Sequential Fix):
```python
# SEQUENTIAL EXECUTION FIX: Only process the FIRST pending command
logging.info(f"Sequential processing - starting first of {total} pending commands")

# Get only the first pending command
item = pending_commands[0]

# Mark only this command as processing
item.status = 'processing'

# Create and start worker for ONLY the first pending command
worker = CommandWorker(item.command, item.token, telnet_session)
self.thread_pool.start(worker)
```

**Continuation Logic** (`_handle_worker_finished()`):
```python
def _handle_worker_finished(self, command: str, success: bool):
    """Handle worker completion and trigger next command."""
    # Mark current command as completed
    self._mark_command_completed(command, success)
    
    # Check for more pending commands
    pending = self._get_pending_commands()
    
    if pending:
        # Trigger next command
        self.start_processing()
    else:
        # All commands completed
        self.all_commands_completed.emit()
```

**Flow**:
```
start_processing()
    ↓
Process FIRST command only
    ↓
Worker executes → completes
    ↓
_handle_worker_finished() called
    ↓
Check for pending commands
    ↓ (If pending)
call start_processing() again
    ↓
Repeat until no pending commands
```

**Test Results**: 3/3 tests passed in 15.44s (previously had race conditions)

**Benefits**:
- Guaranteed sequential execution
- Proper wait-for-completion between commands
- No race conditions with shared resources
- Predictable command order

**Related**: See [IMPLEMENTATION_SUMMARY_sequential_command_execution.md](../implementation/IMPLEMENTATION_SUMMARY_sequential_command_execution.md) for complete fix details

---

## 🔧 Command Services

Protocol-specific command services handle the details of FBC, RPC, and BsTool execution.

### FBC Command Service

```python
class FbcCommandService(QObject):
    """Service for FBC (Fieldbus Command) execution."""
    
    command_completed = pyqtSignal(str, str, bool)  # node_name, token_id, success
    
    def __init__(self, command_queue: CommandQueue, 
                 node_manager: 'NodeManager',
                 telnet_service: 'TelnetService'):
        super().__init__()
        self.command_queue = command_queue
        self.node_manager = node_manager
        self.telnet_service = telnet_service
    
    def queue_fieldbus_command(self, node_name: str, token_id: str,
                               telnet_client: Optional[object] = None) -> None:
        """
        Queue FBC command for execution.
        
        Args:
            node_name: Name of node containing token
            token_id: FBC token ID to execute
            telnet_client: Optional reusable telnet client
        """
        # Get node and token
        node = self.node_manager.get_node(node_name)
        if not node:
            raise ValueError(f"Node not found: {node_name}")
        
        token = node.get_token('FBC', token_id)
        if not token:
            # Create temporary token
            token = NodeToken(
                token_id=token_id,
                token_type='FBC',
                name=node_name,
                ip_address=node.ip_address
            )
        
        # Generate FBC command
        command = f"print from fbc io structure {token_id}0000"
        
        # Add to queue
        self.command_queue.add_command(command, token, telnet_client)
        
        logging.info(f"FBC command queued: {command} for node {node_name}")
```

### RPC Command Service

```python
class RpcCommandService(QObject):
    """Service for RPC (Remote Procedure Call) execution."""
    
    command_completed = pyqtSignal(str, str, bool, str)  # node_name, token_id, success, action
    
    def __init__(self, command_queue: CommandQueue,
                 node_manager: 'NodeManager',
                 telnet_service: 'TelnetService'):
        super().__init__()
        self.command_queue = command_queue
        self.node_manager = node_manager
        self.telnet_service = telnet_service
    
    def queue_rpc_command(self, node_name: str, token_id: str, 
                         action: str = "print",
                         telnet_client: Optional[object] = None) -> None:
        """
        Queue RPC command for execution.
        
        Args:
            node_name: Name of node containing token
            token_id: RPC token ID to execute
            action: "print" or "clear"
            telnet_client: Optional reusable telnet client
        """
        # Resolve token (with FBC→RPC hybrid support)
        token = self._resolve_token(node_name, token_id)
        
        # Generate RPC command
        action_map = {
            "print": "print from fbc rupi counters",
            "clear": "clear fbc rupi counters"
        }
        command = f"{action_map[action]} {token_id}0000"
        
        # Add to queue
        self.command_queue.add_command(command, token, telnet_client)
        
        logging.info(f"RPC command queued: {command} ({action}) for node {node_name}")
    
    def _resolve_token(self, node_name: str, token_id: str) -> 'NodeToken':
        """
        Resolve RPC token with FBC→RPC hybrid fallback.
        
        See: [Token Management](../technical/TECH_token_management.md#hybrid-token-resolution)
        """
        node = self.node_manager.get_node(node_name)
        if not node:
            raise ValueError(f"Node not found: {node_name}")
        
        # Try RPC token first
        token = node.get_token('RPC', token_id)
        if token:
            return token
        
        # Hybrid: Try FBC token
        fbc_token = node.get_token('FBC', token_id)
        if fbc_token:
            logging.info(f"Using FBC token {token_id} for RPC command (hybrid resolution)")
            return NodeToken(
                token_id=fbc_token.token_id,
                token_type='RPC',
                name=node_name,
                ip_address=fbc_token.ip_address or node.ip_address,
                metadata={'source': 'hybrid_fbc_to_rpc'}
            )
        
        # Fallback: Create temporary token
        return NodeToken(
            token_id=token_id,
            token_type='RPC',
            name=node_name,
            ip_address=node.ip_address,
            metadata={'source': 'fallback_temporary'}
        )
```

---

## 🌲 Hierarchical Command Execution

The `HierarchicalCommandService` orchestrates complex multi-step workflows with nested sub-commands.

### Hierarchical Architecture

The LOGReport system supports hierarchical command execution at multiple levels:

1. **Token Level**: Individual token commands (FBC, RPC)
2. **Subgroup Level**: All tokens within a subgroup (e.g., all FBC tokens)
3. **Node Level**: All subgroups within a node (FBC → RPC → LOG)

### Node-Level Hierarchical Execution

Right-clicking on a node provides the option to **Execute All Commands Hierarchically**, which orchestrates a complete command workflow:

```
Node (AP01m) Right-Click
    ↓
Execute All Commands Hierarchically
    ↓
Phase 1: FBC Subgroup Commands
    ├─→ Process token 162.fbc
    ├─→ Process token 163.fbc
    └─→ ... (all FBC tokens)
    ↓
Phase 2: RPC Subgroup Commands
    ├─→ Process token 162.rpc
    ├─→ Process token 163.rpc
    └─→ ... (all RPC tokens)
    ↓
Phase 3: LOG/BsTool Commands
    └─→ Process log files with BsTool
```

### Implementation

```python
class NodeTreePresenter:
    """Presenter handling node-level hierarchical command execution."""
    
    def process_node_hierarchical_commands(self, node_name: str):
        """
        Execute all commands hierarchically for a node.
        
        This method orchestrates a three-phase execution:
        1. Execute all FBC commands for the node
        2. Execute all RPC commands for the node
        3. Process all LOG files with BsTool
        
        Args:
            node_name: Name of the node to process hierarchically
        
        Example:
            >>> presenter.process_node_hierarchical_commands("AP01m")
            # Phase 1/3: Executing 5 FBC commands...
            # Phase 2/3: Executing 5 RPC commands...
            # Phase 3/3: Processing 3 LOG files...
            # Hierarchical execution complete for AP01m: 13 commands processed
        """
        logging.info(f"Starting hierarchical command execution for node {node_name}...")
        self.status_message_signal.emit(f"Starting hierarchical execution for node {node_name}...", 0)
        
        try:
            # Get the node
            node = self.node_manager.get_node(node_name)
            if not node:
                self._report_error(f"Node {node_name} not found")
                return
            
            # Phase 1: Execute all FBC commands
            fbc_tokens = self._get_tokens_for_node(node, "FBC")
            if fbc_tokens:
                self.status_message_signal.emit(
                    f"Phase 1/3: Executing {len(fbc_tokens)} FBC commands...", 0
                )
                for token in fbc_tokens:
                    self.fbc_service.queue_fieldbus_command(
                        node_name, token.token_id
                    )
                self.command_queue.start_processing()
            
            # Phase 2: Execute all RPC commands
            rpc_tokens = self._get_tokens_for_node(node, "RPC")
            if rpc_tokens:
                self.status_message_signal.emit(
                    f"Phase 2/3: Executing {len(rpc_tokens)} RPC commands...", 0
                )
                for token in rpc_tokens:
                    self.rpc_service.queue_rpc_command(
                        node_name, token.token_id, "print"
                    )
            
            # Phase 3: Process LOG files with BsTool
            log_tokens = self._get_tokens_for_node(node, "LOG")
            if log_tokens:
                self.status_message_signal.emit(
                    f"Phase 3/3: Processing {len(log_tokens)} LOG files...", 0
                )
                for token in log_tokens:
                    if hasattr(token, 'log_path') and token.log_path:
                        node_id = self._extract_node_id_from_log_path(token.log_path)
                        if node_id:
                            bstool_command_args = f"-errlog {node_id}"
                            self.command_generated_signal.emit(
                                bstool_command_args, "BSTOOL"
                            )
            
            # Completion message
            total_commands = len(fbc_tokens) + len(rpc_tokens) + len(log_tokens)
            self.status_message_signal.emit(
                f"Hierarchical execution complete for {node_name}: {total_commands} commands processed",
                5000
            )
            
        except Exception as e:
            self._report_error(f"Error in hierarchical execution for {node_name}", e)
    
    def _get_tokens_for_node(self, node, token_type: str):
        """
        Get all tokens of a specific type for a node.
        
        Args:
            node: Node object
            token_type: Type of tokens to retrieve (FBC, RPC, LOG, etc.)
            
        Returns:
            List of tokens of the specified type
        """
        all_tokens = []
        for token_list in node.tokens.values():
            if isinstance(token_list, list):
                for token in token_list:
                    if isinstance(token, NodeToken):
                        all_tokens.append(token)
            else:
                if isinstance(token_list, NodeToken):
                    all_tokens.append(token_list)
        
        # Filter tokens by type
        return [t for t in all_tokens if t.token_type == token_type]
```

### Context Menu Integration

The hierarchical command option is available through the node context menu:

```python
class ContextMenuService:
    """Service for handling context menu operations."""
    
    def show_context_menu(self, menu: QMenu, item_data: Dict[str, Any], position) -> bool:
        """Show context menu for a tree item."""
        
        # Handle node items (hierarchical execution)
        if item_data and item_data.get('type') == 'node':
            node_name = item_data.get('node_name')
            
            if self.context_menu_filter.should_show_command(
                node_name=node_name,
                section_type=None,
                command_type="execute_all_hierarchical",
                command_category="node"
            ):
                hierarchical_action = QAction(
                    f"Execute All Commands Hierarchically for {node_name}", 
                    menu
                )
                hierarchical_action.triggered.connect(
                    lambda: self.presenter.process_node_hierarchical_commands(node_name)
                )
                menu.addAction(hierarchical_action)
                
        return True
```

### Configuration

The hierarchical command visibility can be controlled through `config/menu_filter_rules.json`:

```json
{
  "rules": [
    {
      "description": "Show 'Execute All Commands Hierarchically' for all nodes",
      "action": "show",
      "command_type": "execute_all_hierarchical",
      "command_category": "node"
    },
    {
      "description": "Hide hierarchical commands for specific nodes",
      "node_name": "TestNode",
      "action": "hide",
      "command_type": "execute_all_hierarchical",
      "command_category": "node"
    }
  ]
}
```

### Benefits

1. **Efficiency**: Execute all node commands with a single action
2. **Consistency**: Ensures commands execute in proper order (FBC → RPC → LOG)
3. **Automation**: Reduces manual effort for multi-protocol testing
4. **Error Isolation**: Each phase handles errors independently
5. **Progress Tracking**: Clear status messages for each phase

See: [Context Menu System](../blueprints/BLUEPRINT_context_menu.md#node-level-commands)

---

## 🌲 Hierarchical Command Execution (Legacy)

The `HierarchicalCommandService` orchestrates complex multi-step workflows with nested sub-commands.

### Legacy Hierarchical Architecture (Pre-v1.1)

```python
class HierarchicalCommandService(QObject):
    """Execute hierarchical commands with FBC/RPC/LOG/BsTool sub-commands."""
    
    def execute_hierarchical_command(self, node_token: 'NodeToken', 
                                    command_name: str) -> dict:
        """
        Execute hierarchical command with sub-commands.
        
        Args:
            node_token: Primary node token
            command_name: Name of hierarchical command to execute
        
        Returns:
            Dict with execution results per sub-command
        
        Example Workflow:
            1. Execute FBC commands for token group
            2. Wait for FBC completion
            3. Execute RPC commands for same token group
            4. Wait for RPC completion
            5. Run BsTool on generated logs
            6. Return combined results
        """
        results = {
            'command': command_name,
            'node': node_token.node_name,
            'fbc_results': [],
            'rpc_results': [],
            'bstool_results': [],
            'success': False
        }
        
        try:
            # Step 1: Execute FBC sub-commands
            fbc_tokens = self._get_fbc_tokens(node_token)
            if fbc_tokens:
                self.processor.process_fbc_commands(
                    node_token.node_name,
                    fbc_tokens
                )
                results['fbc_results'] = self._wait_for_completion()
            
            # Step 2: Execute RPC sub-commands
            rpc_tokens = self._get_rpc_tokens(node_token)
            if rpc_tokens:
                self.processor.process_rpc_commands(
                    node_token.node_name,
                    rpc_tokens,
                    action="print"
                )
                results['rpc_results'] = self._wait_for_completion()
            
            # Step 3: Execute BsTool on logs
            log_files = self._get_generated_logs(node_token)
            if log_files:
                results['bstool_results'] = self._execute_bstool_batch(log_files)
            
            results['success'] = True
            return results
        
        except Exception as e:
            logging.error(f"Hierarchical command failed: {str(e)}")
            results['error'] = str(e)
            return results
```

---

## 🔗 Integration Points

### UI Integration

```python
# Context Menu Integration
def handle_context_menu_command(node_name: str, token_id: str, protocol: str):
    """Handle command from context menu."""
    if protocol == 'FBC':
        fbc_service.queue_fieldbus_command(node_name, token_id)
    elif protocol == 'RPC':
        rpc_service.queue_rpc_command(node_name, token_id, action="print")

# Commander Window Integration
def handle_batch_command(node_name: str, tokens: List['NodeToken']):
    """Handle batch command from commander window."""
    processor.process_tokens_sequentially(node_name, tokens)
```

### Node System Integration

See: [Node System - Command Integration](ARCH_node_system.md#command-integration)

### Logging System Integration

See: [Logging System - Command-Based Logging](ARCH_logging_system.md#command-based-logging)

---

## ⚠️ Error Handling & Recovery

### Error Classification

| Error Type | Handling Strategy | Recovery Action |
|------------|------------------|-----------------|
| **Network Timeout** | Retry with exponential backoff | Reconnect telnet |
| **Invalid Token** | Skip token, continue batch | Log warning |
| **Node Unreachable** | Fail entire node batch | Mark node offline |
| **Circuit Breaker** | Stop processing | Report to user |
| **Resource Exhaustion** | Cleanup and retry | Garbage collection |

### Error Isolation Pattern

```python
def _execute_token_with_isolation(token: 'NodeToken', context: dict) -> Tuple[bool, Optional[str]]:
    """Execute token with full error isolation."""
    try:
        # Execute command
        success, error = self._execute_token(token, context)
        return success, error
    
    except NetworkTimeout as e:
        logging.warning(f"Network timeout for token {token.token_id}: {str(e)}")
        return False, f"Network timeout: {str(e)}"
    
    except InvalidTokenError as e:
        logging.error(f"Invalid token {token.token_id}: {str(e)}")
        return False, f"Invalid token: {str(e)}"
    
    except Exception as e:
        logging.error(f"Unexpected error for token {token.token_id}: {str(e)}")
        return False, f"Unexpected error: {str(e)}"
```

---

## ⚡ Performance & Optimization

### Resource Management

- **Connection Pooling**: Reuse telnet clients across commands
- **Memory Optimization**: Process tokens iteratively (not all at once)
- **Garbage Collection**: Periodic cleanup every 10 commands
- **Circuit Breaker**: Stop processing after 3 consecutive failures

### Performance Metrics

```python
def _collect_performance_metrics() -> dict:
    """Collect command execution metrics."""
    return {
        'total_commands': self._total_commands,
        'completed_commands': self._completed_commands,
        'success_rate': self._success_count / self._total_commands,
        'avg_execution_time': sum(self._execution_times) / len(self._execution_times),
        'commands_per_second': self._total_commands / self._total_elapsed_time
    }
```

---

## 📚 References

### Related Documentation

- **[Node System](ARCH_node_system.md)** - Node and token management
- **[Token Management](../technical/TECH_token_management.md)** - Token resolution and utilities
- **[Logging System](ARCH_logging_system.md)** - Command-based log generation
- **[Sequential Processor](../technical/TECH_sequential_command_processor_v1.md)** - Detailed processor documentation
- **[Command Services](service_layer/command_services.md)** - Service layer details

### Source Code

- **Command Queue**: `src/commander/command_queue.py`
- **Sequential Processor**: `src/commander/services/sequential_command_processor.py`
- **FBC Service**: `src/commander/services/fbc_command_service.py`
- **RPC Service**: `src/commander/services/rpc_command_service.py`
- **Hierarchical Service**: `src/commander/services/hierarchical_command_service.py`

---

**Document Status**: ✅ **COMPLETE** - Consolidated from 15 source documents
**Last Updated**: 2025-10-08
**Consolidation**: sequential_command_processor.md + command_queue_system.md + fbc_service.md + rpc_service.md + hierarchical_execution.md + 10 others
**Next Review**: 2026-01-08 (90 days)
