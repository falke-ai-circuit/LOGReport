"""
Custom Exception Hierarchy for LOGReport Commander Module

This module provides a structured exception hierarchy for consistent error handling
across the application, following Python best practices for exception design.

Usage:
    from commander.exceptions import ConfigurationError, CommandExecutionError
    
    try:
        config = load_config(path)
    except ConfigurationError as e:
        logger.error(f"Configuration failed: {e}")
"""

from typing import Optional, Any, Dict
from dataclasses import dataclass, field
from enum import Enum


class ErrorSeverity(Enum):
    """Severity levels for exceptions."""
    CRITICAL = "critical"
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


@dataclass
class ErrorContext:
    """Context information for exceptions."""
    source: str = ""
    details: Dict[str, Any] = field(default_factory=dict)
    recoverable: bool = True
    
    def __str__(self) -> str:
        parts = []
        if self.source:
            parts.append(f"source={self.source}")
        if self.details:
            details_str = ", ".join(f"{k}={v}" for k, v in self.details.items())
            parts.append(f"details={{{details_str}}}")
        return f"ErrorContext({', '.join(parts)})"


class LOGReportError(Exception):
    """
    Base exception for all LOGReport errors.
    
    Provides consistent error handling with context, severity, and recovery hints.
    
    Attributes:
        message: Human-readable error message
        context: Additional context about the error
        severity: Error severity level
        cause: Original exception that caused this error
    """
    
    def __init__(
        self,
        message: str,
        context: Optional[ErrorContext] = None,
        severity: ErrorSeverity = ErrorSeverity.ERROR,
        cause: Optional[Exception] = None
    ) -> None:
        super().__init__(message)
        self.message = message
        self.context = context or ErrorContext()
        self.severity = severity
        self.cause = cause
    
    def __str__(self) -> str:
        result = self.message
        if self.context.source:
            result = f"[{self.context.source}] {result}"
        if self.cause:
            result = f"{result} (caused by: {self.cause})"
        return result
    
    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}("
            f"message={self.message!r}, "
            f"severity={self.severity.value}, "
            f"context={self.context}"
            f")"
        )
    
    @property
    def is_recoverable(self) -> bool:
        """Check if the error is recoverable."""
        return self.context.recoverable


# ============================================================================
# Configuration Errors
# ============================================================================

class ConfigurationError(LOGReportError):
    """
    Configuration loading or parsing errors.
    
    Raised when configuration files cannot be loaded, parsed, or validated.
    
    Examples:
        - Missing configuration file
        - Invalid JSON syntax
        - Missing required configuration keys
        - Invalid configuration values
    """
    
    def __init__(
        self,
        message: str,
        config_path: Optional[str] = None,
        key: Optional[str] = None,
        **kwargs
    ) -> None:
        context = kwargs.pop('context', ErrorContext())
        if config_path:
            context.details['config_path'] = config_path
        if key:
            context.details['key'] = key
        super().__init__(message, context=context, **kwargs)
        self.config_path = config_path
        self.key = key


class MissingConfigurationError(ConfigurationError):
    """Raised when a required configuration file is missing."""
    
    def __init__(self, config_path: str, **kwargs) -> None:
        super().__init__(
            f"Configuration file not found: {config_path}",
            config_path=config_path,
            **kwargs
        )


class InvalidConfigurationError(ConfigurationError):
    """Raised when configuration content is invalid."""
    
    def __init__(
        self,
        message: str,
        config_path: Optional[str] = None,
        key: Optional[str] = None,
        expected_type: Optional[type] = None,
        actual_value: Any = None,
        **kwargs
    ) -> None:
        context = kwargs.pop('context', ErrorContext())
        if expected_type:
            context.details['expected_type'] = expected_type.__name__
        if actual_value is not None:
            context.details['actual_value'] = repr(actual_value)
        super().__init__(message, config_path=config_path, key=key, context=context, **kwargs)


# ============================================================================
# Command Execution Errors
# ============================================================================

class CommandExecutionError(LOGReportError):
    """
    Command execution errors.
    
    Raised when a command fails to execute, times out, or returns an error.
    
    Attributes:
        command: The command that failed
        return_code: Command return code if available
        output: Command output if available
    """
    
    def __init__(
        self,
        message: str,
        command: Optional[str] = None,
        return_code: Optional[int] = None,
        output: Optional[str] = None,
        **kwargs
    ) -> None:
        context = kwargs.pop('context', ErrorContext())
        if command:
            context.details['command'] = command
        if return_code is not None:
            context.details['return_code'] = return_code
        if output:
            context.details['output'] = output[:200]  # Truncate long output
        super().__init__(message, context=context, **kwargs)
        self.command = command
        self.return_code = return_code
        self.output = output


class CommandTimeoutError(CommandExecutionError):
    """Raised when a command execution times out."""
    
    def __init__(
        self,
        command: str,
        timeout: float,
        **kwargs
    ) -> None:
        context = kwargs.pop('context', ErrorContext())
        context.details['timeout'] = timeout
        super().__init__(
            f"Command timed out after {timeout}s",
            command=command,
            context=context,
            **kwargs
        )
        self.timeout = timeout


class CommandCancelledError(CommandExecutionError):
    """Raised when a command execution is cancelled by the user."""
    
    def __init__(self, command: Optional[str] = None, **kwargs) -> None:
        context = kwargs.pop('context', ErrorContext())
        context.recoverable = True
        super().__init__(
            "Command execution was cancelled",
            command=command,
            context=context,
            **kwargs
        )


# ============================================================================
# Node and Token Errors
# ============================================================================

class NodeError(LOGReportError):
    """
    Node-related errors.
    
    Base class for errors related to node operations.
    
    Attributes:
        node_name: Name of the node involved
    """
    
    def __init__(
        self,
        message: str,
        node_name: Optional[str] = None,
        **kwargs
    ) -> None:
        context = kwargs.pop('context', ErrorContext())
        if node_name:
            context.details['node_name'] = node_name
        super().__init__(message, context=context, **kwargs)
        self.node_name = node_name


class NodeNotFoundError(NodeError):
    """Raised when a requested node cannot be found."""
    
    def __init__(self, node_name: str, **kwargs) -> None:
        super().__init__(
            f"Node not found: {node_name}",
            node_name=node_name,
            **kwargs
        )


class NodeConnectionError(NodeError):
    """Raised when connection to a node fails."""
    
    def __init__(
        self,
        node_name: str,
        ip_address: Optional[str] = None,
        port: Optional[int] = None,
        **kwargs
    ) -> None:
        context = kwargs.pop('context', ErrorContext())
        if ip_address:
            context.details['ip_address'] = ip_address
        if port:
            context.details['port'] = port
        super().__init__(
            f"Failed to connect to node: {node_name}",
            node_name=node_name,
            context=context,
            **kwargs
        )
        self.ip_address = ip_address
        self.port = port


class TokenError(LOGReportError):
    """
    Token-related errors.
    
    Base class for errors related to token operations.
    
    Attributes:
        token_id: Token identifier involved
        token_type: Type of token (FBC, RPC, etc.)
    """
    
    def __init__(
        self,
        message: str,
        token_id: Optional[str] = None,
        token_type: Optional[str] = None,
        **kwargs
    ) -> None:
        context = kwargs.pop('context', ErrorContext())
        if token_id:
            context.details['token_id'] = token_id
        if token_type:
            context.details['token_type'] = token_type
        super().__init__(message, context=context, **kwargs)
        self.token_id = token_id
        self.token_type = token_type


class InvalidTokenError(TokenError):
    """Raised when a token is invalid."""
    
    def __init__(
        self,
        token_id: str,
        reason: str = "Invalid token format",
        **kwargs
    ) -> None:
        super().__init__(
            f"Invalid token '{token_id}': {reason}",
            token_id=token_id,
            **kwargs
        )
        self.reason = reason


class TokenNotFoundError(TokenError):
    """Raised when a token cannot be found."""
    
    def __init__(
        self,
        token_id: str,
        node_name: Optional[str] = None,
        **kwargs
    ) -> None:
        context = kwargs.pop('context', ErrorContext())
        if node_name:
            context.details['node_name'] = node_name
        message = f"Token not found: {token_id}"
        if node_name:
            message = f"Token '{token_id}' not found in node '{node_name}'"
        super().__init__(message, token_id=token_id, context=context, **kwargs)


# ============================================================================
# Network Errors
# ============================================================================

class NetworkError(LOGReportError):
    """
    Network-related errors.
    
    Base class for network communication errors.
    """
    
    def __init__(
        self,
        message: str,
        host: Optional[str] = None,
        port: Optional[int] = None,
        **kwargs
    ) -> None:
        context = kwargs.pop('context', ErrorContext())
        if host:
            context.details['host'] = host
        if port:
            context.details['port'] = port
        super().__init__(message, context=context, **kwargs)
        self.host = host
        self.port = port


class ConnectionError(NetworkError):
    """Raised when a network connection fails."""
    pass


class SessionError(NetworkError):
    """Raised when a session operation fails."""
    
    def __init__(
        self,
        message: str,
        session_id: Optional[str] = None,
        **kwargs
    ) -> None:
        context = kwargs.pop('context', ErrorContext())
        if session_id:
            context.details['session_id'] = session_id
        super().__init__(message, context=context, **kwargs)
        self.session_id = session_id


# ============================================================================
# Validation Errors
# ============================================================================

@dataclass
class ValidationError:
    """Represents a single validation error."""
    field: str
    message: str
    code: str = "invalid"
    value: Any = None
    
    def __str__(self) -> str:
        return f"{self.field}: {self.message}"


class ValidationException(LOGReportError):
    """
    Validation exception containing multiple validation errors.
    
    Used when input validation fails and multiple errors need to be reported.
    
    Attributes:
        errors: List of validation errors
    """
    
    def __init__(
        self,
        errors: list[ValidationError],
        message: Optional[str] = None,
        **kwargs
    ) -> None:
        if message is None:
            error_count = len(errors)
            message = f"Validation failed with {error_count} error(s)"
        
        context = kwargs.pop('context', ErrorContext())
        context.details['error_count'] = len(errors)
        context.details['fields'] = [e.field for e in errors]
        
        super().__init__(message, context=context, **kwargs)
        self.errors = errors
    
    def get_errors_for_field(self, field: str) -> list[ValidationError]:
        """Get all errors for a specific field."""
        return [e for e in self.errors if e.field == field]
    
    def has_errors(self) -> bool:
        """Check if there are any validation errors."""
        return len(self.errors) > 0


# ============================================================================
# File and I/O Errors
# ============================================================================

class FileOperationError(LOGReportError):
    """
    File operation errors.
    
    Raised when file operations fail.
    
    Attributes:
        file_path: Path to the file involved
        operation: The operation that failed (read, write, delete, etc.)
    """
    
    def __init__(
        self,
        message: str,
        file_path: Optional[str] = None,
        operation: Optional[str] = None,
        **kwargs
    ) -> None:
        context = kwargs.pop('context', ErrorContext())
        if file_path:
            context.details['file_path'] = file_path
        if operation:
            context.details['operation'] = operation
        super().__init__(message, context=context, **kwargs)
        self.file_path = file_path
        self.operation = operation


class LogFileError(FileOperationError):
    """Raised when log file operations fail."""
    
    def __init__(
        self,
        message: str,
        log_path: Optional[str] = None,
        **kwargs
    ) -> None:
        super().__init__(message, file_path=log_path, **kwargs)
        self.log_path = log_path


# ============================================================================
# Processing Errors
# ============================================================================

class ProcessingError(LOGReportError):
    """
    Processing errors.
    
    Base class for errors during data processing operations.
    """
    pass


class BatchProcessingError(ProcessingError):
    """
    Raised when batch processing fails.
    
    Attributes:
        completed_count: Number of items successfully processed
        total_count: Total number of items to process
        failed_items: List of items that failed
    """
    
    def __init__(
        self,
        message: str,
        completed_count: int = 0,
        total_count: int = 0,
        failed_items: Optional[list] = None,
        **kwargs
    ) -> None:
        context = kwargs.pop('context', ErrorContext())
        context.details['completed_count'] = completed_count
        context.details['total_count'] = total_count
        context.details['failed_count'] = len(failed_items) if failed_items else 0
        
        super().__init__(message, context=context, **kwargs)
        self.completed_count = completed_count
        self.total_count = total_count
        self.failed_items = failed_items or []


class CircuitBreakerOpenError(ProcessingError):
    """Raised when circuit breaker is open and rejects operations."""
    
    def __init__(
        self,
        service_name: str,
        reset_time: Optional[float] = None,
        **kwargs
    ) -> None:
        context = kwargs.pop('context', ErrorContext())
        context.details['service_name'] = service_name
        if reset_time:
            context.details['reset_time'] = reset_time
        
        message = f"Circuit breaker is open for service: {service_name}"
        if reset_time:
            message += f" (resets in {reset_time:.1f}s)"
        
        super().__init__(message, context=context, **kwargs)
        self.service_name = service_name
        self.reset_time = reset_time
