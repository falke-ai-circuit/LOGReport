"""
Node Validator - Comprehensive validation for node configurations

This module provides validation functionality for node configurations,
with detailed error reporting and support for custom validation rules.

Usage:
    from commander.validators.node_validator import NodeValidator, ValidationResult
    
    validator = NodeValidator()
    result = validator.validate(node_config)
    if not result.is_valid:
        for error in result.errors:
            print(f"{error.field}: {error.message}")
"""

import re
import logging
from dataclasses import dataclass, field
from typing import Any, Callable, Optional, Protocol, Sequence
from ipaddress import ip_address, AddressValueError

from ..models import Node, NodeToken
from ..exceptions import ValidationError, ValidationException


@dataclass
class ValidationResult:
    """
    Result of a validation operation.
    
    Contains all validation errors found during validation,
    along with helper methods for checking validity and retrieving errors.
    
    Attributes:
        errors: List of validation errors found
        warnings: List of non-critical validation warnings
    """
    
    errors: list[ValidationError] = field(default_factory=list)
    warnings: list[ValidationError] = field(default_factory=list)
    
    @property
    def is_valid(self) -> bool:
        """Check if validation passed (no errors)."""
        return len(self.errors) == 0
    
    def add_error(
        self,
        field: str,
        message: str,
        code: str = "invalid",
        value: Any = None
    ) -> None:
        """Add a validation error."""
        self.errors.append(ValidationError(
            field=field,
            message=message,
            code=code,
            value=value
        ))
    
    def add_warning(
        self,
        field: str,
        message: str,
        code: str = "warning",
        value: Any = None
    ) -> None:
        """Add a validation warning."""
        self.warnings.append(ValidationError(
            field=field,
            message=message,
            code=code,
            value=value
        ))
    
    def get_errors_for_field(self, field: str) -> list[ValidationError]:
        """Get all errors for a specific field."""
        return [e for e in self.errors if e.field == field]
    
    def has_error(self, field: str, code: Optional[str] = None) -> bool:
        """Check if a field has a specific error."""
        for error in self.errors:
            if error.field == field:
                if code is None or error.code == code:
                    return True
        return False
    
    def merge(self, other: "ValidationResult") -> "ValidationResult":
        """Merge another validation result into this one."""
        self.errors.extend(other.errors)
        self.warnings.extend(other.warnings)
        return self
    
    def raise_if_invalid(self) -> None:
        """Raise ValidationException if there are any errors."""
        if not self.is_valid:
            raise ValidationException(self.errors)
    
    def __bool__(self) -> bool:
        """Boolean evaluation returns validity status."""
        return self.is_valid


# Type for custom validation functions
ValidatorFunc = Callable[[Any, ValidationResult], None]


class INodeValidator(Protocol):
    """Interface for node validators."""
    
    def validate(self, node: Node) -> ValidationResult:
        """Validate a node configuration."""
        ...
    
    def validate_token(self, token: NodeToken) -> ValidationResult:
        """Validate a token configuration."""
        ...


class NodeValidator:
    """
    Comprehensive validator for node configurations.
    
    Validates node names, IP addresses, tokens, and other configuration
    properties according to defined rules.
    
    Attributes:
        strict_mode: If True, treats warnings as errors
        custom_validators: List of custom validation functions
    
    Example:
        >>> validator = NodeValidator()
        >>> node = Node(name="", ip_address="invalid")
        >>> result = validator.validate(node)
        >>> result.is_valid
        False
        >>> for error in result.errors:
        ...     print(f"{error.field}: {error.message}")
        name: Node name is required
        ip_address: Invalid IP address format
    """
    
    # Validation patterns
    NAME_PATTERN = re.compile(r'^[a-zA-Z][a-zA-Z0-9_-]*$')
    NAME_MAX_LENGTH = 50
    NAME_MIN_LENGTH = 1
    
    TOKEN_ID_PATTERN = re.compile(r'^[a-zA-Z0-9]+$')
    TOKEN_ID_MAX_LENGTH = 20
    
    VALID_TOKEN_TYPES = frozenset({"FBC", "RPC", "LOG", "LIS"})
    VALID_PROTOCOLS = frozenset({"telnet", "ssh", "http", "https"})
    
    DEFAULT_PORT_RANGES = {
        "telnet": (1, 65535),
        "ssh": (1, 65535),
        "http": (1, 65535),
        "https": (1, 65535),
    }
    
    def __init__(
        self,
        strict_mode: bool = False,
        custom_validators: Optional[list[ValidatorFunc]] = None
    ) -> None:
        """
        Initialize the node validator.
        
        Args:
            strict_mode: If True, treats warnings as errors
            custom_validators: Additional validation functions to apply
        """
        self.strict_mode = strict_mode
        self.custom_validators = custom_validators or []
        self.logger = logging.getLogger(__name__)
    
    def validate(self, node: Node) -> ValidationResult:
        """
        Validate a complete node configuration.
        
        Validates all aspects of the node including name, IP address,
        status, and all contained tokens.
        
        Args:
            node: Node configuration to validate
        
        Returns:
            ValidationResult containing any errors found
        """
        result = ValidationResult()
        
        # Validate node name
        self._validate_name(node.name, result)
        
        # Validate IP address
        self._validate_ip_address(node.ip_address, result)
        
        # Validate status
        self._validate_status(node.status, result)
        
        # Validate tokens
        self._validate_tokens(node.tokens, result)
        
        # Run custom validators
        for validator in self.custom_validators:
            try:
                validator(node, result)
            except Exception as e:
                self.logger.warning(f"Custom validator failed: {e}")
        
        # In strict mode, convert warnings to errors
        if self.strict_mode:
            result.errors.extend(result.warnings)
            result.warnings = []
        
        return result
    
    def validate_token(self, token: NodeToken) -> ValidationResult:
        """
        Validate a single token configuration.
        
        Args:
            token: Token to validate
        
        Returns:
            ValidationResult containing any errors found
        """
        result = ValidationResult()
        
        # Validate token ID
        self._validate_token_id(token.token_id, result)
        
        # Validate token type
        self._validate_token_type(token.token_type, result)
        
        # Validate IP address if present
        if token.ip_address and token.ip_address != "0.0.0.0":
            self._validate_ip_address(token.ip_address, result, field_name="token.ip_address")
        
        # Validate port
        self._validate_port(token.port, token.protocol, result)
        
        # Validate protocol
        self._validate_protocol(token.protocol, result)
        
        return result
    
    def _validate_name(self, name: str, result: ValidationResult) -> None:
        """Validate node name."""
        if not name or not name.strip():
            result.add_error(
                field="name",
                message="Node name is required",
                code="required"
            )
            return
        
        name = name.strip()
        
        # Check length
        if len(name) < self.NAME_MIN_LENGTH:
            result.add_error(
                field="name",
                message=f"Node name must be at least {self.NAME_MIN_LENGTH} characters",
                code="min_length",
                value=name
            )
        elif len(name) > self.NAME_MAX_LENGTH:
            result.add_error(
                field="name",
                message=f"Node name must not exceed {self.NAME_MAX_LENGTH} characters",
                code="max_length",
                value=name
            )
        
        # Check pattern
        if not self.NAME_PATTERN.match(name):
            result.add_error(
                field="name",
                message="Node name must start with a letter and contain only letters, numbers, underscores, and hyphens",
                code="pattern",
                value=name
            )
    
    def _validate_ip_address(
        self,
        ip: str,
        result: ValidationResult,
        field_name: str = "ip_address"
    ) -> None:
        """Validate IP address format."""
        if not ip or not ip.strip():
            result.add_error(
                field=field_name,
                message="IP address is required",
                code="required"
            )
            return
        
        ip = ip.strip()
        
        try:
            # Use Python's ipaddress module for validation
            ip_address(ip)
        except ValueError:
            result.add_error(
                field=field_name,
                message=f"Invalid IP address format: {ip}",
                code="invalid_format",
                value=ip
            )
    
    def _validate_status(self, status: str, result: ValidationResult) -> None:
        """Validate node status."""
        valid_statuses = {"online", "offline", "unknown", "error", "connecting"}
        
        if status and status.lower() not in valid_statuses:
            result.add_warning(
                field="status",
                message=f"Unknown status value: {status}",
                code="unknown_value",
                value=status
            )
    
    def _validate_tokens(
        self,
        tokens: dict[str, list[NodeToken]],
        result: ValidationResult
    ) -> None:
        """Validate all tokens in a node."""
        if not tokens:
            # Tokens are optional
            return
        
        token_ids_seen = set()
        
        for token_id, token_list in tokens.items():
            # Check for duplicate token IDs
            if token_id in token_ids_seen:
                result.add_error(
                    field=f"tokens.{token_id}",
                    message=f"Duplicate token ID: {token_id}",
                    code="duplicate",
                    value=token_id
                )
            token_ids_seen.add(token_id)
            
            # Validate each token
            for idx, token in enumerate(token_list):
                token_result = self.validate_token(token)
                
                # Prefix field names with token location
                for error in token_result.errors:
                    error.field = f"tokens.{token_id}[{idx}].{error.field}"
                    result.errors.append(error)
                
                for warning in token_result.warnings:
                    warning.field = f"tokens.{token_id}[{idx}].{warning.field}"
                    result.warnings.append(warning)
    
    def _validate_token_id(self, token_id: str, result: ValidationResult) -> None:
        """Validate token ID format."""
        if not token_id or not token_id.strip():
            result.add_error(
                field="token_id",
                message="Token ID is required",
                code="required"
            )
            return
        
        token_id = token_id.strip()
        
        if len(token_id) > self.TOKEN_ID_MAX_LENGTH:
            result.add_error(
                field="token_id",
                message=f"Token ID must not exceed {self.TOKEN_ID_MAX_LENGTH} characters",
                code="max_length",
                value=token_id
            )
        
        if not self.TOKEN_ID_PATTERN.match(token_id):
            result.add_error(
                field="token_id",
                message="Token ID must contain only letters and numbers",
                code="pattern",
                value=token_id
            )
    
    def _validate_token_type(self, token_type: str, result: ValidationResult) -> None:
        """Validate token type."""
        if not token_type:
            result.add_error(
                field="token_type",
                message="Token type is required",
                code="required"
            )
            return
        
        token_type_upper = token_type.upper()
        if token_type_upper not in self.VALID_TOKEN_TYPES:
            result.add_warning(
                field="token_type",
                message=f"Unknown token type: {token_type}. Valid types are: {', '.join(sorted(self.VALID_TOKEN_TYPES))}",
                code="unknown_type",
                value=token_type
            )
    
    def _validate_port(
        self,
        port: int,
        protocol: str,
        result: ValidationResult
    ) -> None:
        """Validate port number."""
        if not isinstance(port, int):
            result.add_error(
                field="port",
                message="Port must be an integer",
                code="invalid_type",
                value=port
            )
            return
        
        # Get port range for protocol
        port_range = self.DEFAULT_PORT_RANGES.get(protocol, (1, 65535))
        min_port, max_port = port_range
        
        if port < min_port or port > max_port:
            result.add_error(
                field="port",
                message=f"Port must be between {min_port} and {max_port}",
                code="out_of_range",
                value=port
            )
    
    def _validate_protocol(self, protocol: str, result: ValidationResult) -> None:
        """Validate protocol type."""
        if not protocol:
            # Protocol is optional, defaults to telnet
            return
        
        if protocol.lower() not in self.VALID_PROTOCOLS:
            result.add_warning(
                field="protocol",
                message=f"Unknown protocol: {protocol}. Valid protocols are: {', '.join(sorted(self.VALID_PROTOCOLS))}",
                code="unknown_protocol",
                value=protocol
            )
    
    def add_custom_validator(self, validator: ValidatorFunc) -> None:
        """Add a custom validation function."""
        self.custom_validators.append(validator)
    
    def remove_custom_validator(self, validator: ValidatorFunc) -> bool:
        """Remove a custom validation function."""
        try:
            self.custom_validators.remove(validator)
            return True
        except ValueError:
            return False


class NodeConfigValidator:
    """
    Validator for node configuration dictionaries (from JSON).
    
    This validator works with raw configuration data before it's
    converted to Node/NodeToken objects.
    """
    
    REQUIRED_FIELDS = {"name", "ip_address"}
    OPTIONAL_FIELDS = {"status", "tokens", "port", "protocol"}
    
    def __init__(self) -> None:
        """Initialize the config validator."""
        self.logger = logging.getLogger(__name__)
    
    def validate_config(self, config: dict[str, Any]) -> ValidationResult:
        """
        Validate a node configuration dictionary.
        
        Args:
            config: Dictionary containing node configuration
        
        Returns:
            ValidationResult with any validation errors
        """
        result = ValidationResult()
        
        # Check required fields
        for field in self.REQUIRED_FIELDS:
            if field not in config:
                result.add_error(
                    field=field,
                    message=f"Required field '{field}' is missing",
                    code="required"
                )
            elif not config[field]:
                result.add_error(
                    field=field,
                    message=f"Field '{field}' cannot be empty",
                    code="empty"
                )
        
        # Check for unknown fields
        known_fields = self.REQUIRED_FIELDS | self.OPTIONAL_FIELDS
        for field in config:
            if field not in known_fields:
                result.add_warning(
                    field=field,
                    message=f"Unknown field '{field}' will be ignored",
                    code="unknown_field"
                )
        
        return result
    
    def validate_config_list(
        self,
        configs: Sequence[dict[str, Any]]
    ) -> ValidationResult:
        """
        Validate a list of node configurations.
        
        Args:
            configs: List of configuration dictionaries
        
        Returns:
            ValidationResult with all validation errors
        """
        result = ValidationResult()
        
        if not configs:
            result.add_warning(
                field="configurations",
                message="Empty configuration list",
                code="empty_list"
            )
            return result
        
        seen_names = set()
        
        for idx, config in enumerate(configs):
            config_result = self.validate_config(config)
            
            # Prefix field names with index
            for error in config_result.errors:
                error.field = f"[{idx}].{error.field}"
                result.errors.append(error)
            
            for warning in config_result.warnings:
                warning.field = f"[{idx}].{warning.field}"
                result.warnings.append(warning)
            
            # Check for duplicate names
            if "name" in config:
                name = config["name"]
                if name in seen_names:
                    result.add_error(
                        field=f"[{idx}].name",
                        message=f"Duplicate node name: {name}",
                        code="duplicate",
                        value=name
                    )
                seen_names.add(name)
        
        return result


# Singleton instance for global use
_default_validator: Optional[NodeValidator] = None


def get_node_validator(
    strict_mode: bool = False,
    custom_validators: Optional[list[ValidatorFunc]] = None
) -> NodeValidator:
    """
    Get the default node validator instance.
    
    Args:
        strict_mode: If True, creates validator in strict mode
        custom_validators: Optional custom validators to add
    
    Returns:
        NodeValidator instance
    """
    global _default_validator
    
    if _default_validator is None or strict_mode or custom_validators:
        _default_validator = NodeValidator(strict_mode, custom_validators)
    
    return _default_validator
