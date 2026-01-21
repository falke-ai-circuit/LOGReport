"""
Unit tests for the NodeValidator and related validators.

Tests node validation, token validation, and configuration validation.
"""

import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', 'src'))

import pytest
from commander.models import Node, NodeToken
from commander.validators import (
    NodeValidator,
    NodeConfigValidator,
    ValidationResult,
    get_node_validator,
)
from commander.exceptions import ValidationError, ValidationException


class TestValidationResult:
    """Tests for ValidationResult class."""
    
    def test_empty_result_is_valid(self):
        """Test empty result is valid."""
        result = ValidationResult()
        assert result.is_valid is True
        assert bool(result) is True
    
    def test_result_with_errors_is_invalid(self):
        """Test result with errors is invalid."""
        result = ValidationResult()
        result.add_error("name", "Required")
        assert result.is_valid is False
        assert bool(result) is False
    
    def test_add_error(self):
        """Test adding errors."""
        result = ValidationResult()
        result.add_error("name", "Required", code="required", value="")
        assert len(result.errors) == 1
        assert result.errors[0].field == "name"
        assert result.errors[0].message == "Required"
        assert result.errors[0].code == "required"
    
    def test_add_warning(self):
        """Test adding warnings."""
        result = ValidationResult()
        result.add_warning("status", "Unknown status")
        assert len(result.warnings) == 1
        assert result.is_valid is True  # Warnings don't affect validity
    
    def test_get_errors_for_field(self):
        """Test getting errors for specific field."""
        result = ValidationResult()
        result.add_error("name", "Error 1")
        result.add_error("name", "Error 2")
        result.add_error("ip", "Error 3")
        
        name_errors = result.get_errors_for_field("name")
        assert len(name_errors) == 2
    
    def test_has_error(self):
        """Test checking for specific errors."""
        result = ValidationResult()
        result.add_error("name", "Required", code="required")
        
        assert result.has_error("name") is True
        assert result.has_error("name", "required") is True
        assert result.has_error("name", "pattern") is False
        assert result.has_error("ip") is False
    
    def test_merge_results(self):
        """Test merging validation results."""
        result1 = ValidationResult()
        result1.add_error("name", "Error 1")
        
        result2 = ValidationResult()
        result2.add_error("ip", "Error 2")
        result2.add_warning("status", "Warning")
        
        result1.merge(result2)
        assert len(result1.errors) == 2
        assert len(result1.warnings) == 1
    
    def test_raise_if_invalid(self):
        """Test raising exception when invalid."""
        result = ValidationResult()
        result.add_error("name", "Required")
        
        with pytest.raises(ValidationException):
            result.raise_if_invalid()
    
    def test_raise_if_invalid_no_error(self):
        """Test no exception when valid."""
        result = ValidationResult()
        result.raise_if_invalid()  # Should not raise


class TestNodeValidator:
    """Tests for NodeValidator class."""
    
    @pytest.fixture
    def validator(self):
        """Create a validator instance."""
        return NodeValidator()
    
    @pytest.fixture
    def valid_node(self):
        """Create a valid node."""
        return Node(name="AP01", ip_address="192.168.1.1")
    
    def test_validate_valid_node(self, validator, valid_node):
        """Test validating a valid node."""
        result = validator.validate(valid_node)
        assert result.is_valid is True
    
    def test_validate_empty_name(self, validator):
        """Test validation fails for empty name."""
        node = Node(name="", ip_address="192.168.1.1")
        result = validator.validate(node)
        assert result.has_error("name", "required") is True
    
    def test_validate_name_too_long(self, validator):
        """Test validation fails for name too long."""
        node = Node(name="a" * 60, ip_address="192.168.1.1")
        result = validator.validate(node)
        assert result.has_error("name", "max_length") is True
    
    def test_validate_invalid_name_pattern(self, validator):
        """Test validation fails for invalid name pattern."""
        node = Node(name="123invalid", ip_address="192.168.1.1")
        result = validator.validate(node)
        assert result.has_error("name", "pattern") is True
    
    def test_validate_empty_ip(self, validator):
        """Test validation fails for empty IP."""
        node = Node(name="AP01", ip_address="")
        result = validator.validate(node)
        assert result.has_error("ip_address", "required") is True
    
    def test_validate_invalid_ip(self, validator):
        """Test validation fails for invalid IP."""
        node = Node(name="AP01", ip_address="invalid")
        result = validator.validate(node)
        assert result.has_error("ip_address", "invalid_format") is True
    
    def test_validate_unknown_status_warning(self, validator):
        """Test warning for unknown status."""
        node = Node(name="AP01", ip_address="192.168.1.1", status="custom")
        result = validator.validate(node)
        assert result.is_valid is True  # Warnings don't fail validation
        assert len(result.warnings) > 0
    
    def test_strict_mode_converts_warnings(self):
        """Test strict mode converts warnings to errors."""
        validator = NodeValidator(strict_mode=True)
        node = Node(name="AP01", ip_address="192.168.1.1", status="custom")
        result = validator.validate(node)
        assert result.is_valid is False
    
    def test_custom_validator(self, valid_node):
        """Test adding custom validator."""
        def custom_check(node, result):
            if not node.name.startswith("AP"):
                result.add_error("name", "Must start with AP", "custom")
        
        validator = NodeValidator(custom_validators=[custom_check])
        
        # Valid node starts with AP
        result = validator.validate(valid_node)
        assert result.is_valid is True
        
        # Invalid node
        invalid_node = Node(name="Node01", ip_address="192.168.1.1")
        result = validator.validate(invalid_node)
        assert result.has_error("name", "custom") is True


class TestNodeTokenValidator:
    """Tests for token validation."""
    
    @pytest.fixture
    def validator(self):
        """Create a validator instance."""
        return NodeValidator()
    
    @pytest.fixture
    def valid_token(self):
        """Create a valid token."""
        return NodeToken(
            token_id="001",
            token_type="FBC",
            name="AP01",
            ip_address="192.168.1.1"
        )
    
    def test_validate_valid_token(self, validator, valid_token):
        """Test validating a valid token."""
        result = validator.validate_token(valid_token)
        assert result.is_valid is True
    
    def test_validate_empty_token_id(self, validator):
        """Test validation fails for empty token ID."""
        token = NodeToken(token_id="", token_type="FBC")
        result = validator.validate_token(token)
        assert result.has_error("token_id", "required") is True
    
    def test_validate_token_id_too_long(self, validator):
        """Test validation fails for token ID too long."""
        token = NodeToken(token_id="a" * 25, token_type="FBC")
        result = validator.validate_token(token)
        assert result.has_error("token_id", "max_length") is True
    
    def test_validate_empty_token_type(self, validator):
        """Test validation fails for empty token type."""
        token = NodeToken(token_id="001", token_type="")
        result = validator.validate_token(token)
        assert result.has_error("token_type", "required") is True
    
    def test_validate_unknown_token_type_warning(self, validator):
        """Test warning for unknown token type."""
        token = NodeToken(token_id="001", token_type="CUSTOM")
        result = validator.validate_token(token)
        assert result.is_valid is True
        assert len(result.warnings) > 0
    
    def test_validate_invalid_port(self, validator):
        """Test validation fails for invalid port."""
        token = NodeToken(token_id="001", token_type="FBC", port=0)
        result = validator.validate_token(token)
        assert result.has_error("port", "out_of_range") is True


class TestNodeConfigValidator:
    """Tests for configuration dictionary validation."""
    
    @pytest.fixture
    def validator(self):
        """Create a config validator instance."""
        return NodeConfigValidator()
    
    def test_validate_valid_config(self, validator):
        """Test validating a valid config."""
        config = {"name": "AP01", "ip_address": "192.168.1.1"}
        result = validator.validate_config(config)
        assert result.is_valid is True
    
    def test_validate_missing_required_field(self, validator):
        """Test validation fails for missing required field."""
        config = {"name": "AP01"}  # Missing ip_address
        result = validator.validate_config(config)
        assert result.has_error("ip_address", "required") is True
    
    def test_validate_empty_required_field(self, validator):
        """Test validation fails for empty required field."""
        config = {"name": "", "ip_address": "192.168.1.1"}
        result = validator.validate_config(config)
        assert result.has_error("name", "empty") is True
    
    def test_validate_unknown_field_warning(self, validator):
        """Test warning for unknown field."""
        config = {"name": "AP01", "ip_address": "192.168.1.1", "custom": "value"}
        result = validator.validate_config(config)
        assert result.is_valid is True
        assert len(result.warnings) > 0
    
    def test_validate_config_list(self, validator):
        """Test validating a list of configs."""
        configs = [
            {"name": "AP01", "ip_address": "192.168.1.1"},
            {"name": "AP02", "ip_address": "192.168.1.2"},
        ]
        result = validator.validate_config_list(configs)
        assert result.is_valid is True
    
    def test_validate_config_list_duplicates(self, validator):
        """Test detecting duplicate names in config list."""
        configs = [
            {"name": "AP01", "ip_address": "192.168.1.1"},
            {"name": "AP01", "ip_address": "192.168.1.2"},  # Duplicate
        ]
        result = validator.validate_config_list(configs)
        assert result.is_valid is False
        assert result.has_error("[1].name", "duplicate") is True
    
    def test_validate_empty_config_list_warning(self, validator):
        """Test warning for empty config list."""
        result = validator.validate_config_list([])
        assert result.is_valid is True
        assert len(result.warnings) > 0


class TestGetNodeValidator:
    """Tests for get_node_validator function."""
    
    def test_get_default_validator(self):
        """Test getting default validator."""
        validator = get_node_validator()
        assert isinstance(validator, NodeValidator)
    
    def test_get_strict_validator(self):
        """Test getting strict mode validator."""
        validator = get_node_validator(strict_mode=True)
        assert validator.strict_mode is True
