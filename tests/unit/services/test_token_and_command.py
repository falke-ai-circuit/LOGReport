"""
Tests for TokenPreparationService and CommandGenerator.
"""

import pytest
from src.commander.services.token_preparation_service import (
    TokenPreparationService, PreparedToken
)
from src.commander.services.command_generator import (
    CommandGenerator, GeneratedCommand, CommandAction
)


class TestTokenPreparationService:
    """Test suite for TokenPreparationService."""
    
    @pytest.fixture
    def service(self):
        """Create a TokenPreparationService instance."""
        return TokenPreparationService()
    
    def test_normalize_token_id_numeric(self, service):
        """Should pad numeric tokens to 3 digits."""
        assert service.normalize_token_id("1", "FBC") == "001"
        assert service.normalize_token_id("12", "FBC") == "012"
        assert service.normalize_token_id("123", "FBC") == "123"
        assert service.normalize_token_id("1234", "FBC") == "1234"  # Keep as-is if > 3 digits
    
    def test_normalize_token_id_non_numeric(self, service):
        """Should preserve non-numeric token IDs."""
        assert service.normalize_token_id("abc", "FBC") == "abc"
        assert service.normalize_token_id("test123", "FBC") == "test123"
    
    def test_is_valid_ip_valid(self, service):
        """Should validate correct IP addresses."""
        assert service.is_valid_ip("192.168.1.1") is True
        assert service.is_valid_ip("0.0.0.0") is True
        assert service.is_valid_ip("255.255.255.255") is True
        assert service.is_valid_ip("10.0.0.1") is True
    
    def test_is_valid_ip_invalid(self, service):
        """Should reject invalid IP addresses."""
        assert service.is_valid_ip("") is False
        assert service.is_valid_ip(None) is False
        assert service.is_valid_ip("not.an.ip") is False
        assert service.is_valid_ip("256.1.1.1") is False
        assert service.is_valid_ip("1.1.1") is False
        assert service.is_valid_ip("1.1.1.1.1") is False
    
    def test_get_base_node_name_simple(self, service):
        """Should return simple node name unchanged."""
        assert service.get_base_node_name("AP01m") == "AP01m"
        assert service.get_base_node_name("NODE1") == "NODE1"
    
    def test_get_base_node_name_with_spaces(self, service):
        """Should extract first word from node name with spaces."""
        assert service.get_base_node_name("AP01m description") == "AP01m"
        assert service.get_base_node_name("NODE1 some text here") == "NODE1"
    
    def test_prepare_fbc_token(self, service):
        """Should create valid FBC token."""
        result = service.prepare_fbc_token("162", "AP01m", "192.168.1.1")
        
        assert result.is_valid is True
        assert result.normalized_id == "162"
        assert result.token.token_type == "FBC"
        assert result.token.name == "AP01m"
        assert result.token.ip_address == "192.168.1.1"
    
    def test_prepare_fbc_token_invalid_ip(self, service):
        """Should use default IP for invalid IP address."""
        result = service.prepare_fbc_token("162", "AP01m", "invalid")
        
        assert result.is_valid is True
        assert result.token.ip_address == "0.0.0.0"
    
    def test_prepare_rpc_token(self, service):
        """Should create valid RPC token."""
        result = service.prepare_rpc_token("162", "AP01m", "192.168.1.1")
        
        assert result.is_valid is True
        assert result.normalized_id == "162"
        assert result.token.token_type == "RPC"
        assert result.token.name == "AP01m"
        assert result.token.port == 23
        assert result.token.protocol == "telnet"
    
    def test_prepare_token_fbc(self, service):
        """Should dispatch to prepare_fbc_token for FBC tokens."""
        from src.commander.models import NodeToken
        token = NodeToken(token_id="162", token_type="FBC", name="test")
        
        result = service.prepare_token(token, "AP01m", "192.168.1.1")
        
        assert result.is_valid is True
        assert result.token.token_type == "FBC"
    
    def test_prepare_token_rpc(self, service):
        """Should dispatch to prepare_rpc_token for RPC tokens."""
        from src.commander.models import NodeToken
        token = NodeToken(token_id="162", token_type="RPC", name="test")
        
        result = service.prepare_token(token, "AP01m", "192.168.1.1")
        
        assert result.is_valid is True
        assert result.token.token_type == "RPC"
    
    def test_prepare_token_unknown_type(self, service):
        """Should return invalid result for unknown token type."""
        from src.commander.models import NodeToken
        token = NodeToken(token_id="162", token_type="UNKNOWN", name="test")
        
        result = service.prepare_token(token, "AP01m", "192.168.1.1")
        
        assert result.is_valid is False
        assert "Unknown token type" in result.error_message


class TestCommandGenerator:
    """Test suite for CommandGenerator."""
    
    @pytest.fixture
    def generator(self):
        """Create a CommandGenerator instance."""
        return CommandGenerator()
    
    def test_normalize_token_id(self, generator):
        """Should normalize token IDs to 3 digits."""
        assert generator.normalize_token_id("1") == "001"
        assert generator.normalize_token_id("12") == "012"
        assert generator.normalize_token_id("123") == "123"
    
    def test_generate_fbc_command_print(self, generator):
        """Should generate correct FBC print command."""
        result = generator.generate_fbc_command("162", "print")
        
        assert result.is_valid is True
        assert result.command == "print from fbc io structure 1620000"
        assert result.action == CommandAction.PRINT
        assert result.protocol == "FBC"
    
    def test_generate_fbc_command_clear(self, generator):
        """Should generate correct FBC clear command."""
        result = generator.generate_fbc_command("162", "clear")
        
        assert result.is_valid is True
        assert result.command == "clear fbc io structure 1620000"
        assert result.action == CommandAction.CLEAR
    
    def test_generate_fbc_command_invalid_action(self, generator):
        """Should return invalid result for unknown action."""
        result = generator.generate_fbc_command("162", "unknown")
        
        assert result.is_valid is False
        assert "Unknown action" in result.error_message
    
    def test_generate_rpc_command_print(self, generator):
        """Should generate correct RPC print command."""
        result = generator.generate_rpc_command("162", "print")
        
        assert result.is_valid is True
        assert result.command == "print from fbc rupi counters 1620000"
        assert result.action == CommandAction.PRINT
        assert result.protocol == "RPC"
    
    def test_generate_rpc_command_clear(self, generator):
        """Should generate correct RPC clear command."""
        result = generator.generate_rpc_command("162", "clear")
        
        assert result.is_valid is True
        assert result.command == "clear fbc rupi counters 1620000"
        assert result.action == CommandAction.CLEAR
    
    def test_generate_command_fbc(self, generator):
        """Should dispatch to generate_fbc_command for FBC protocol."""
        result = generator.generate_command("162", "FBC", "print")
        
        assert result.is_valid is True
        assert result.protocol == "FBC"
    
    def test_generate_command_rpc(self, generator):
        """Should dispatch to generate_rpc_command for RPC protocol."""
        result = generator.generate_command("162", "RPC", "print")
        
        assert result.is_valid is True
        assert result.protocol == "RPC"
    
    def test_generate_command_unknown_protocol(self, generator):
        """Should return invalid result for unknown protocol."""
        result = generator.generate_command("162", "UNKNOWN", "print")
        
        assert result.is_valid is False
        assert "Unknown protocol" in result.error_message
    
    def test_generate_command_case_insensitive(self, generator):
        """Should accept protocol in any case."""
        result_upper = generator.generate_command("162", "FBC", "print")
        result_lower = generator.generate_command("162", "fbc", "print")
        
        assert result_upper.is_valid is True
        assert result_lower.is_valid is True
