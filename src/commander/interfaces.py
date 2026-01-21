"""
Service Interfaces (Protocols) for LOGReport Commander

This module defines Protocol classes (interfaces) for service dependencies,
enabling dependency injection and improving testability.

Usage:
    from commander.contracts import ICommandExecutor, INodeRepository
    
    class MyService:
        def __init__(self, executor: ICommandExecutor, repo: INodeRepository):
            self.executor = executor
            self.repo = repo
"""

from typing import Protocol, Optional, List, Dict, Any, runtime_checkable
from dataclasses import dataclass
from pathlib import Path
from enum import Enum


# ============================================================================
# Execution Types
# ============================================================================

class ExecutionState(Enum):
    """Execution states for command processing."""
    IDLE = "idle"
    RUNNING = "running"
    PAUSED = "paused"
    CANCELLED = "cancelled"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class ExecutionContext:
    """Context for command execution."""
    node_name: str
    ip_address: str
    action: str = "print"
    timeout: float = 30.0
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class CommandResult:
    """Result of a command execution."""
    success: bool
    token_id: str
    log_path: Optional[str] = None
    error: Optional[str] = None
    duration: float = 0.0
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


# ============================================================================
# Service Protocols (Interfaces)
# ============================================================================

@runtime_checkable
class ICommandExecutor(Protocol):
    """
    Interface for executing individual commands.
    
    Implementations handle the low-level command execution
    with proper error handling and resource management.
    """
    
    def execute(
        self,
        token_id: str,
        token_type: str,
        context: ExecutionContext
    ) -> CommandResult:
        """
        Execute a single command.
        
        Args:
            token_id: Token identifier to execute
            token_type: Type of token (FBC, RPC, etc.)
            context: Execution context with node info
        
        Returns:
            CommandResult with execution outcome
        """
        ...
    
    def can_execute(self, token_type: str) -> bool:
        """Check if this executor can handle a token type."""
        ...


@runtime_checkable
class IProgressTracker(Protocol):
    """
    Interface for tracking execution progress.
    
    Implementations handle progress updates and notifications.
    """
    
    def start(self, total: int) -> None:
        """Start tracking progress for N items."""
        ...
    
    def update(self, current: int, message: str = "") -> None:
        """Update current progress."""
        ...
    
    def complete(self) -> None:
        """Mark progress as complete."""
        ...
    
    def cancel(self) -> None:
        """Cancel progress tracking."""
        ...


@runtime_checkable
class IStateManager(Protocol):
    """
    Interface for managing execution state.
    
    Implementations handle state transitions and notifications.
    """
    
    @property
    def current_state(self) -> ExecutionState:
        """Get current execution state."""
        ...
    
    def transition_to(self, state: ExecutionState) -> bool:
        """
        Attempt to transition to a new state.
        
        Returns True if transition was successful.
        """
        ...
    
    def can_transition_to(self, state: ExecutionState) -> bool:
        """Check if transition to state is valid."""
        ...


@runtime_checkable
class INodeRepository(Protocol):
    """
    Interface for node data access.
    
    Implementations handle loading, saving, and querying nodes.
    """
    
    def get(self, name: str) -> Optional[Any]:
        """Get a node by name."""
        ...
    
    def get_all(self) -> List[Any]:
        """Get all nodes."""
        ...
    
    def save(self, node: Any) -> bool:
        """Save a node."""
        ...
    
    def delete(self, name: str) -> bool:
        """Delete a node by name."""
        ...
    
    def exists(self, name: str) -> bool:
        """Check if a node exists."""
        ...


@runtime_checkable
class IConfigurationLoader(Protocol):
    """
    Interface for loading configuration files.
    
    Implementations handle parsing and validation of config files.
    """
    
    def load(self, path: Path) -> Dict[str, Any]:
        """Load configuration from file."""
        ...
    
    def save(self, config: Dict[str, Any], path: Path) -> bool:
        """Save configuration to file."""
        ...
    
    def validate(self, config: Dict[str, Any]) -> bool:
        """Validate configuration structure."""
        ...


@runtime_checkable
class ILogScanner(Protocol):
    """
    Interface for scanning log directories.
    
    Implementations handle finding and categorizing log files.
    """
    
    def scan(self, directory: Path) -> List[Path]:
        """Scan directory for log files."""
        ...
    
    def categorize(self, files: List[Path]) -> Dict[str, List[Path]]:
        """Categorize log files by type."""
        ...


@runtime_checkable
class ITokenValidator(Protocol):
    """
    Interface for token validation.
    
    Implementations validate token IDs and types.
    """
    
    def validate(self, token_id: str) -> bool:
        """Validate a token ID."""
        ...
    
    def normalize(self, token_id: str) -> str:
        """Normalize a token ID to standard format."""
        ...
    
    def is_fbc_token(self, token_id: str) -> bool:
        """Check if token is FBC type."""
        ...
    
    def is_rpc_token(self, token_id: str) -> bool:
        """Check if token is RPC type."""
        ...


@runtime_checkable
class ILogPathService(Protocol):
    """
    Interface for log path generation.
    
    Implementations generate consistent log file paths.
    """
    
    def get_log_path(
        self,
        token: Any,
        node_name: str,
        action: str = "print"
    ) -> Path:
        """Generate log file path for a token."""
        ...
    
    def get_log_directory(
        self,
        protocol: str,
        node_name: Optional[str] = None
    ) -> Path:
        """Get directory for log files."""
        ...


@runtime_checkable  
class ISessionManager(Protocol):
    """
    Interface for managing telnet sessions.
    
    Implementations handle session lifecycle and communication.
    """
    
    def connect(self, host: str, port: int = 23) -> bool:
        """Establish a session connection."""
        ...
    
    def disconnect(self) -> None:
        """Close the session connection."""
        ...
    
    def send(self, data: str) -> bool:
        """Send data through the session."""
        ...
    
    def receive(self, timeout: float = 5.0) -> str:
        """Receive data from the session."""
        ...
    
    @property
    def is_connected(self) -> bool:
        """Check if session is connected."""
        ...


@runtime_checkable
class IEventPublisher(Protocol):
    """
    Interface for event publishing.
    
    Implementations handle broadcasting events to subscribers.
    """
    
    def publish(self, event_type: str, data: Dict[str, Any]) -> None:
        """Publish an event."""
        ...
    
    def subscribe(self, event_type: str, handler: Any) -> None:
        """Subscribe to an event type."""
        ...
    
    def unsubscribe(self, event_type: str, handler: Any) -> None:
        """Unsubscribe from an event type."""
        ...


# ============================================================================
# Composite Interfaces
# ============================================================================

@runtime_checkable
class IBatchProcessor(Protocol):
    """
    Interface for batch command processing.
    
    Coordinates execution of multiple commands with progress tracking.
    """
    
    def process_batch(
        self,
        tokens: List[Any],
        context: ExecutionContext
    ) -> List[CommandResult]:
        """Process a batch of tokens."""
        ...
    
    def pause(self) -> bool:
        """Pause batch processing."""
        ...
    
    def resume(self) -> bool:
        """Resume batch processing."""
        ...
    
    def cancel(self) -> bool:
        """Cancel batch processing."""
        ...
    
    @property
    def state(self) -> ExecutionState:
        """Get current processing state."""
        ...


@runtime_checkable
class INodeManager(Protocol):
    """
    Interface for node management (facade).
    
    Coordinates node operations across multiple components.
    """
    
    def load_configuration(self, path: Optional[Path] = None) -> bool:
        """Load node configuration."""
        ...
    
    def get_node(self, name: str) -> Optional[Any]:
        """Get a node by name."""
        ...
    
    def get_all_nodes(self) -> List[Any]:
        """Get all nodes."""
        ...
    
    def select_node(self, name: str) -> bool:
        """Select a node as active."""
        ...
    
    def scan_log_files(self) -> None:
        """Scan for log files."""
        ...
    
    @property
    def selected_node(self) -> Optional[Any]:
        """Get the currently selected node."""
        ...
