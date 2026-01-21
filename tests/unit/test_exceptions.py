"""
Unit tests for the custom exception hierarchy.

Tests exception creation, inheritance, context handling, and error information.
"""

import pytest
from commander.exceptions import (
    LOGReportError,
    ErrorContext,
    ErrorSeverity,
    ConfigurationError,
    MissingConfigurationError,
    InvalidConfigurationError,
    CommandExecutionError,
    CommandTimeoutError,
    CommandCancelledError,
    NodeError,
    NodeNotFoundError,
    NodeConnectionError,
    TokenError,
    InvalidTokenError,
    TokenNotFoundError,
    NetworkError,
    SessionError,
    ValidationError,
    ValidationException,
    FileOperationError,
    LogFileError,
    ProcessingError,
    BatchProcessingError,
    CircuitBreakerOpenError,
)


class TestErrorContext:
    """Tests for ErrorContext dataclass."""
    
    def test_empty_context(self):
        """Test creating empty context."""
        ctx = ErrorContext()
        assert ctx.source == ""
        assert ctx.details == {}
        assert ctx.recoverable is True
    
    def test_context_with_values(self):
        """Test creating context with values."""
        ctx = ErrorContext(
            source="test_module",
            details={"key": "value"},
            recoverable=False
        )
        assert ctx.source == "test_module"
        assert ctx.details == {"key": "value"}
        assert ctx.recoverable is False
    
    def test_context_str(self):
        """Test context string representation."""
        ctx = ErrorContext(source="test", details={"a": 1})
        str_repr = str(ctx)
        assert "source=test" in str_repr
        assert "a=1" in str_repr


class TestLOGReportError:
    """Tests for base LOGReportError exception."""
    
    def test_basic_error(self):
        """Test creating basic error."""
        error = LOGReportError("Test error")
        assert error.message == "Test error"
        assert str(error) == "Test error"
        assert error.severity == ErrorSeverity.ERROR
    
    def test_error_with_context(self):
        """Test error with context."""
        ctx = ErrorContext(source="test_module")
        error = LOGReportError("Test error", context=ctx)
        assert "[test_module]" in str(error)
    
    def test_error_with_cause(self):
        """Test error with cause."""
        cause = ValueError("Original error")
        error = LOGReportError("Wrapper error", cause=cause)
        assert "caused by" in str(error)
        assert error.cause == cause
    
    def test_error_severity(self):
        """Test error severity levels."""
        error = LOGReportError("Critical", severity=ErrorSeverity.CRITICAL)
        assert error.severity == ErrorSeverity.CRITICAL
    
    def test_is_recoverable(self):
        """Test recoverable property."""
        error = LOGReportError("Recoverable")
        assert error.is_recoverable is True
        
        ctx = ErrorContext(recoverable=False)
        error = LOGReportError("Not recoverable", context=ctx)
        assert error.is_recoverable is False


class TestConfigurationErrors:
    """Tests for configuration-related exceptions."""
    
    def test_configuration_error(self):
        """Test basic configuration error."""
        error = ConfigurationError("Config failed", config_path="/etc/config.json")
        assert error.config_path == "/etc/config.json"
        assert "config_path" in error.context.details
    
    def test_missing_configuration_error(self):
        """Test missing configuration error."""
        error = MissingConfigurationError("/etc/missing.json")
        assert "not found" in str(error).lower()
        assert error.config_path == "/etc/missing.json"
    
    def test_invalid_configuration_error(self):
        """Test invalid configuration error."""
        error = InvalidConfigurationError(
            "Invalid value",
            config_path="/etc/config.json",
            key="port",
            expected_type=int,
            actual_value="abc"
        )
        assert "expected_type" in error.context.details
        assert error.context.details["expected_type"] == "int"


class TestCommandErrors:
    """Tests for command execution exceptions."""
    
    def test_command_execution_error(self):
        """Test command execution error."""
        error = CommandExecutionError(
            "Command failed",
            command="ls -la",
            return_code=1,
            output="Permission denied"
        )
        assert error.command == "ls -la"
        assert error.return_code == 1
        assert error.output == "Permission denied"
    
    def test_command_timeout_error(self):
        """Test command timeout error."""
        error = CommandTimeoutError("slow_command", timeout=30.0)
        assert "timed out" in str(error).lower()
        assert error.timeout == 30.0
    
    def test_command_cancelled_error(self):
        """Test command cancelled error."""
        error = CommandCancelledError("cancelled_cmd")
        assert "cancelled" in str(error).lower()
        assert error.is_recoverable is True


class TestNodeErrors:
    """Tests for node-related exceptions."""
    
    def test_node_not_found_error(self):
        """Test node not found error."""
        error = NodeNotFoundError("AP01")
        assert "not found" in str(error).lower()
        assert error.node_name == "AP01"
    
    def test_node_connection_error(self):
        """Test node connection error."""
        error = NodeConnectionError(
            "AP01",
            ip_address="192.168.1.1",
            port=23
        )
        assert error.ip_address == "192.168.1.1"
        assert error.port == 23
        assert "ip_address" in error.context.details


class TestTokenErrors:
    """Tests for token-related exceptions."""
    
    def test_invalid_token_error(self):
        """Test invalid token error."""
        error = InvalidTokenError("abc", reason="Too short")
        assert "abc" in str(error)
        assert error.reason == "Too short"
    
    def test_token_not_found_error(self):
        """Test token not found error."""
        error = TokenNotFoundError("001", node_name="AP01")
        assert "001" in str(error)
        assert "AP01" in str(error)


class TestValidationErrors:
    """Tests for validation exceptions."""
    
    def test_validation_error_dataclass(self):
        """Test ValidationError dataclass."""
        error = ValidationError(
            field="name",
            message="Name is required",
            code="required"
        )
        assert str(error) == "name: Name is required"
    
    def test_validation_exception(self):
        """Test ValidationException with multiple errors."""
        errors = [
            ValidationError("name", "Required", "required"),
            ValidationError("ip", "Invalid format", "format"),
        ]
        exception = ValidationException(errors)
        assert len(exception.errors) == 2
        assert exception.has_errors() is True
    
    def test_get_errors_for_field(self):
        """Test getting errors for specific field."""
        errors = [
            ValidationError("name", "Too short", "min_length"),
            ValidationError("name", "Invalid chars", "pattern"),
            ValidationError("ip", "Invalid", "format"),
        ]
        exception = ValidationException(errors)
        name_errors = exception.get_errors_for_field("name")
        assert len(name_errors) == 2


class TestProcessingErrors:
    """Tests for processing exceptions."""
    
    def test_batch_processing_error(self):
        """Test batch processing error."""
        error = BatchProcessingError(
            "Batch failed",
            completed_count=5,
            total_count=10,
            failed_items=["item1", "item2"]
        )
        assert error.completed_count == 5
        assert error.total_count == 10
        assert len(error.failed_items) == 2
    
    def test_circuit_breaker_open_error(self):
        """Test circuit breaker open error."""
        error = CircuitBreakerOpenError("telnet_service", reset_time=30.0)
        assert "circuit breaker" in str(error).lower()
        assert error.service_name == "telnet_service"
        assert error.reset_time == 30.0


class TestExceptionInheritance:
    """Tests for exception inheritance hierarchy."""
    
    def test_all_inherit_from_base(self):
        """Test all exceptions inherit from LOGReportError."""
        exceptions = [
            ConfigurationError("test"),
            CommandExecutionError("test"),
            NodeError("test"),
            TokenError("test"),
            NetworkError("test"),
            ProcessingError("test"),
            FileOperationError("test"),
        ]
        for exc in exceptions:
            assert isinstance(exc, LOGReportError)
            assert isinstance(exc, Exception)
    
    def test_catch_by_base_class(self):
        """Test catching exceptions by base class."""
        try:
            raise NodeNotFoundError("AP01")
        except LOGReportError as e:
            assert isinstance(e, NodeNotFoundError)
            assert isinstance(e, NodeError)
