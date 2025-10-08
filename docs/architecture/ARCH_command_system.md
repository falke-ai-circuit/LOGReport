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
