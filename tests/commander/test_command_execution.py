import os
import sys
import pytest
from unittest.mock import MagicMock, patch, call

# Add src directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'src')))

from commander.node_manager import NodeManager
from commander.models import Node, NodeToken
from commander.services.fbc_command_service import FbcCommandService
from commander.services.rpc_command_service import RpcCommandService
from commander.command_queue import CommandQueue
from commander.log_writer import LogWriter
from commander.services.context_menu_service import ContextMenuService
from commander.services.context_menu_filter import ContextMenuFilterService


class TestCommandExecution:
    """Test suite for command execution validation"""
    
    @pytest.fixture
    def node_manager(self):
        """Create a node manager with test configuration"""
        manager = NodeManager()
        # Set test configuration path
        test_config_path = os.path.join(os.path.dirname(__file__), '..', 'test_nodes.json')
        manager.set_config_path(test_config_path)
        # Load configuration
        manager.load_configuration()
        # Set log root to test logs directory
        test_logs_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'test_logs')
        manager.set_log_root(test_logs_dir)
        return manager
    
    @pytest.fixture
    def mock_session_manager(self):
        """Mock SessionManager for CommandQueue"""
        mock_sm = MagicMock()
        mock_sm.get_debugger_session.return_value = None
        mock_sm.get_or_create_session.return_value = MagicMock(is_connected=True, connect=MagicMock())
        return mock_sm

    @pytest.fixture
    def command_queue(self, mock_session_manager):
        """Create a command queue with a mocked session manager"""
        return CommandQueue(session_manager=mock_session_manager)
    
    @pytest.fixture
    def mock_log_writer(self):
        """Mock LogWriter for FbcCommandService"""
        mock_lw = MagicMock()
        mock_lw.loggers = {}
        mock_lw.get_node_log_path.return_value = "/tmp/test.log"
        mock_lw.open_log.return_value = None
        return mock_lw
    
    @pytest.fixture
    def fbc_service(self, node_manager, command_queue, mock_log_writer):
        """Create an FBC command service with a mocked log writer"""
        # Create a mock parent with active_telnet_client
        mock_parent = MagicMock()
        mock_parent.active_telnet_client = MagicMock()
        
        service = FbcCommandService(node_manager, command_queue, mock_log_writer)
        # Explicitly set log_writer on the service, as it might try to get it from parent
        service.log_writer = mock_log_writer
        # Mock the parent if active_telnet_client is accessed
        service.parent = lambda: mock_parent
        return service
    
    @pytest.fixture
    def rpc_service(self, node_manager, command_queue):
        """Create an RPC command service"""
        service = RpcCommandService(node_manager, command_queue)
        return service
    
    @pytest.fixture
    def context_menu_service(self, node_manager):
        """Create a context menu service"""
        context_menu_filter = ContextMenuFilterService()
        service = ContextMenuService(node_manager, context_menu_filter)
        return service
    
    def test_fbc_command_execution(self, node_manager, fbc_service, command_queue):
        """Test FBC command execution for a specific token"""
        # Scan log files
        node_manager.scan_log_files()
        
        # Get AP01m node
        node = node_manager.get_node("AP01m")
        assert node is not None, "AP01m node should exist"
        
        # Mock command queue to capture commands
        with patch.object(command_queue, 'add_command') as mock_add_command:
            # Execute FBC command for token "162"
            fbc_service.queue_fieldbus_command("AP01m", "162")
            
            # Verify that command was queued
            mock_add_command.assert_called_once()
            
            # Verify that command was queued
            # Since we're not providing a telnet client, the service will try to get/create one
            # Let's check if the method was called at all
            assert mock_add_command.called, "add_command should have been called"
            
            # Get the call arguments
            call_args = mock_add_command.call_args[0]
            command, token, _ = call_args
            assert command == "print from fbc io structure 1620000", \
                f"Expected FBC command format, got {command}"
            assert token.token_id == "162", f"Expected token ID 162, got {token.token_id}"
            assert token.token_type == "FBC", f"Expected FBC token type, got {token.token_type}"
    
    def test_rpc_command_execution(self, node_manager, rpc_service, command_queue):
        """Test RPC command execution for a specific token"""
        # Scan log files
        node_manager.scan_log_files()
        
        # Get AP01m node
        node = node_manager.get_node("AP01m")
        assert node is not None, "AP01m node should exist"
        
        # Mock command queue to capture commands
        with patch.object(command_queue, 'add_command') as mock_add_command:
            # Execute RPC command for token "162"
            rpc_service.queue_rpc_command("AP01m", "162", "print")
            
            # Verify that command was queued
            mock_add_command.assert_called_once()
            
            # Verify command format
            call_args = mock_add_command.call_args[0]
            command, token, _ = call_args
            assert command == "print from fbc rupi counters 1620000", \
                f"Expected RPC print command format, got {command}"
            assert token.token_id == "162", f"Expected token ID 162, got {token.token_id}"
            assert token.token_type == "RPC", f"Expected RPC token type, got {token.token_type}"
            
            # Test RPC clear command
            mock_add_command.reset_mock()
            rpc_service.queue_rpc_command("AP01m", "162", "clear")
            
            # Verify that clear command was queued
            mock_add_command.assert_called_once()
            
            # Verify clear command format
            call_args = mock_add_command.call_args[0]
            command, token, _ = call_args
            assert command == "clear fbc rupi counters 1620000", \
                f"Expected RPC clear command format, got {command}"
    
    def test_context_menu_individual_fbc_command_execution(self, node_manager, context_menu_service, fbc_service):
        """Test individual FBC command execution from context menu"""
        # Scan log files
        node_manager.scan_log_files()
        
        # Get AP01m node
        node = node_manager.get_node("AP01m")
        assert node is not None, "AP01m node should exist"
        
        # Mock presenter to capture command execution
        mock_presenter = MagicMock()
        context_menu_service.set_presenter(mock_presenter)
        
        # Test individual FBC token action
        context_menu_service._handle_fbc_token_action("AP01m", "162")
        
        # Verify that the presenter method was called
        mock_presenter.process_fieldbus_command.assert_called_once_with("162", "AP01m")
    
    def test_context_menu_individual_rpc_command_execution(self, node_manager, context_menu_service, rpc_service):
        """Test individual RPC command execution from context menu"""
        # Scan log files
        node_manager.scan_log_files()
        
        # Get AP01m node
        node = node_manager.get_node("AP01m")
        assert node is not None, "AP01m node should exist"
        
        # Mock presenter to capture command execution
        mock_presenter = MagicMock()
        context_menu_service.set_presenter(mock_presenter)
        
        # Test individual RPC print action
        context_menu_service._handle_rpc_token_action("AP01m", "162", "print")
        
        # Verify that the presenter method was called
        mock_presenter.process_rpc_command.assert_called_once_with("AP01m", "162", "print")
        
        # Test individual RPC clear action
        mock_presenter.reset_mock()
        context_menu_service._handle_rpc_token_action("AP01m", "162", "clear")
        
        # Verify that the presenter method was called
        mock_presenter.process_rpc_command.assert_called_once_with("AP01m", "162", "clear")
    
    def test_same_token_id_different_types_command_execution(self, node_manager, fbc_service, rpc_service, command_queue):
        """Test command execution when both FBC and RPC tokens exist with the same token ID"""
        # Scan log files
        node_manager.scan_log_files()
        
        # Get AP01m node
        node = node_manager.get_node("AP01m")
        assert node is not None, "AP01m node should exist"
        
        # Check that both FBC and RPC tokens with ID "162" exist
        assert "162" in node.tokens, "Token ID 162 should exist in node tokens"
        
        # Filter tokens by type
        fbc_tokens = [t for t in node.tokens["162"] if t.token_type == "FBC"]
        rpc_tokens = [t for t in node.tokens["162"] if t.token_type == "RPC"]
        
        # Verify we have at least one FBC token and one RPC token with the same ID
        assert len(fbc_tokens) >= 1, f"Should have at least one FBC token with ID 162"
        assert len(rpc_tokens) >= 1, f"Should have at least one RPC token with ID 162"
        
        # Mock command queue to capture commands
        with patch.object(command_queue, 'add_command') as mock_add_command:
            # Execute FBC command for token "162"
            fbc_service.queue_fieldbus_command("AP01m", "162")
            
            # Verify that command was queued
            assert mock_add_command.called, "add_command should have been called for FBC"
            
            # Get the call arguments
            fbc_call_args = mock_add_command.call_args[0]
            fbc_command, fbc_token, _ = fbc_call_args
            assert fbc_command == "print from fbc io structure 1620000", \
                f"Expected FBC command format, got {fbc_command}"
            assert fbc_token.token_id == "162", f"Expected token ID 162, got {fbc_token.token_id}"
            assert fbc_token.token_type == "FBC", f"Expected FBC token type, got {fbc_token.token_type}"
            
            # Reset mock and execute RPC command for the same token ID
            mock_add_command.reset_mock()
            rpc_service.queue_rpc_command("AP01m", "162", "print")
            
            # Verify that command was queued
            assert mock_add_command.called, "add_command should have been called for RPC"
            
            # Get the call arguments
            rpc_call_args = mock_add_command.call_args[0]
            rpc_command, rpc_token, _ = rpc_call_args
            assert rpc_command == "print from fbc rupi counters 1620000", \
                f"Expected RPC command format, got {rpc_command}"
            assert rpc_token.token_id == "162", f"Expected token ID 162, got {rpc_token.token_id}"
            assert rpc_token.token_type == "RPC", f"Expected RPC token type, got {rpc_token.token_type}"
            
            # Verify that the tokens are different objects with different types
            assert fbc_token is not rpc_token, "FBC and RPC tokens should be different objects"
            assert fbc_token.token_type != rpc_token.token_type, "FBC and RPC tokens should have different types"

    def test_sequential_command_execution(self, node_manager, fbc_service, command_queue):
        """Test that commands are executed sequentially from the CommandQueue."""
        node_manager.scan_log_files()
        node = node_manager.get_node("AP01m")
        assert node is not None, "AP01m node should exist"

        # Mock the telnet session to avoid actual network calls
        mock_telnet_client = MagicMock()
        mock_telnet_client.is_connected = True
        mock_telnet_client.send_command.side_effect = ["response1", "response2", "response3"]

        # Add multiple commands to the queue
        fbc_service.queue_fieldbus_command("AP01m", "162", telnet_client=mock_telnet_client)
        fbc_service.queue_fieldbus_command("AP01m", "163", telnet_client=mock_telnet_client)
        fbc_service.queue_fieldbus_command("AP01m", "164", telnet_client=mock_telnet_client)


        # Wait for commands to complete (simulate event loop)
        command_queue.thread_pool.waitForDone(5000)  # Wait up to 5 seconds
        
        # Process any pending Qt events to ensure signals are handled
        from PyQt5.QtCore import QCoreApplication
        app = QCoreApplication.instance()
        if app is None:
            app = QCoreApplication([])
        app.processEvents()

        # Assert that send_command was called for each command
        assert mock_telnet_client.send_command.call_count == 3, "send_command should be called for each command"
        mock_telnet_client.send_command.assert_has_calls([
            call("print from fbc io structure 1620000"),
            call("print from fbc io structure 1630000"),
            call("print from fbc io structure 1640000")
        ])

        # Assert that all commands are marked as completed in the queue
        # The queue should be empty if auto_cleanup is enabled and all commands are processed
        assert len(command_queue.queue) == 0, "Queue should be empty after cleanup"
        assert command_queue.completed_count == 3, "All 3 commands should have been completed"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])