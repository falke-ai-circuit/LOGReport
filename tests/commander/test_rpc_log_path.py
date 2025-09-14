import os
import sys
import tempfile
import shutil
from unittest.mock import MagicMock

# Add src directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'src')))

import pytest
from commander.node_manager import NodeManager
from commander.models import Node, NodeToken
from commander.services.rpc_command_service import RpcCommandService
from commander.command_queue import CommandQueue
from commander.log_writer import LogWriter
from commander.services.logging_service import LoggingService


class TestRpcLogPath:
    """Test suite for verifying RPC command output is written to the correct log file"""
    
    @pytest.fixture
    def temp_log_dir(self):
        """Create a temporary directory for log files"""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        # Cleanup after test
        shutil.rmtree(temp_dir, ignore_errors=True)
    
    @pytest.fixture
    def mock_node_manager(self, temp_log_dir):
        """Create a mock NodeManager with a test node and token"""
        mock_nm = MagicMock()
        
        # Create a mock node
        mock_node = MagicMock()
        mock_node.name = "AP01m"
        mock_node.ip_address = "192.168.0.11"
        
        # Create a mock token with a predefined log_path
        log_filename = "AP01m_192-168-0-11_162.rpc"
        log_path = os.path.join(temp_log_dir, "RPC", "AP01m", log_filename)
        
        mock_token = NodeToken(
            token_id="162",
            token_type="RPC",
            name="AP01m",
            ip_address="192.168.0.11",
            port=23
        )
        mock_token.log_path = log_path
        
        # Setup mock node manager methods
        mock_nm.get_node.return_value = mock_node
        mock_nm._generate_log_path.return_value = log_path
        
        return mock_nm, mock_node, mock_token, log_path
    
    def test_rpc_command_output_written_to_log_file(self, mock_node_manager, temp_log_dir):
        """Test that RPC command output is written to the correct log file when signal is emitted"""
        # Unpack fixtures
        mock_nm, mock_node, mock_token, expected_log_path = mock_node_manager
        
        # Create services with mocked dependencies
        command_queue = CommandQueue()
        command_queue.session_manager = MagicMock()
        
        rpc_service = RpcCommandService(mock_nm, command_queue)
        
        # Create log writer with temp directory
        log_writer = LogWriter(mock_nm, temp_log_dir)
        
        # Create the directory structure manually to ensure it exists
        log_dir = os.path.dirname(expected_log_path)
        os.makedirs(log_dir, exist_ok=True)
        
        # Create logging service
        logging_service = LoggingService(mock_nm, log_writer)
        
        # Connect command queue completion signal to logging service
        command_queue.command_completed.connect(logging_service.log_command_result)
        
        # Get token with correct log_path
        token = rpc_service.get_token("AP01m", "162")
        
        # Emit the signal directly to test the logging service
        # This simulates what would happen when a command worker completes successfully
        command_queue.command_completed.emit(
            "print from fbc rupi counters 1620000",  # command
            "RPC command output for token 162",      # result
            True,                                    # success
            token                                    # token
        )
        
        # Verify the log file was created at the expected path
        assert os.path.exists(expected_log_path), f"Log file was not created at {expected_log_path}"
        
        # Verify the log file contains the expected RPC output
        with open(expected_log_path, 'r', encoding='utf-8') as f:
            log_content = f.read()
            
        # Check that the log content contains the RPC command output
        assert "RPC command output for token 162" in log_content, "Log file does not contain expected RPC output"
        
        # Check that the log content contains the command
        assert "print from fbc rupi counters 1620000" in log_content, "Log file does not contain the executed command"