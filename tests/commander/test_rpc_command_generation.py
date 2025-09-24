import pytest
from unittest.mock import Mock, MagicMock

# Add src directory to path
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'src')))

from commander.services.rpc_command_service import RpcCommandService
from commander.node_manager import NodeManager
from commander.command_queue import CommandQueue


class TestRpcCommandGeneration:
    @pytest.fixture
    def mock_node_manager(self):
        return Mock(spec=NodeManager)

    @pytest.fixture
    def mock_command_queue(self):
        return Mock(spec=CommandQueue)

    @pytest.fixture
    def rpc_service(self, mock_node_manager, mock_command_queue):
        return RpcCommandService(mock_node_manager, mock_command_queue)

    def test_generate_rpc_command_with_ip_prefix_stripped(self, rpc_service):
        """Test that generate_rpc_command strips IP prefix from token_id."""
        # Token with IP prefix
        token_with_ip = "AP01m_192-168-0-11_162"
        command = rpc_service.generate_rpc_command(token_with_ip, "print")
        expected = "print from fbc rupi counters 1620000"
        assert command == expected

    def test_generate_rpc_command_without_ip(self, rpc_service):
        """Test generate_rpc_command with clean token_id."""
        clean_token = "162"
        command = rpc_service.generate_rpc_command(clean_token, "print")
        expected = "print from fbc rupi counters 1620000"
        assert command == expected

    def test_generate_rpc_command_clear_action(self, rpc_service):
        """Test clear action generates correct command."""
        token = "AP01m_192-168-0-11_162"
        command = rpc_service.generate_rpc_command(token, "clear")
        expected = "clear fbc rupi counters 1620000"
        assert command == expected

    def test_normalize_token_strips_ip(self, rpc_service):
        """Test normalize_token strips IP prefix."""
        token_with_ip = "AP01m_192-168-0-11_162"
        normalized = rpc_service.normalize_token(token_with_ip)
        assert normalized == "162"

    def test_normalize_token_handles_no_underscore(self, rpc_service):
        """Test normalize_token with no underscore (no IP)."""
        clean_token = "162"
        normalized = rpc_service.normalize_token(clean_token)
        assert normalized == "162"

    def test_normalize_token_pads_digits(self, rpc_service):
        """Test normalize_token pads single digit to 3 digits."""
        single_digit = "5"
        normalized = rpc_service.normalize_token(single_digit)
        assert normalized == "005"