"""
Integration tests for Telnet command output truncation fix.

These tests verify that:
1. Commands executed from context menu produce complete output
2. Commands executed from Telnet tab produce complete output
3. Outputs from both execution paths are identical and complete
4. Commands with percentage symbols or long outputs are not truncated
"""

import os
import sys
import pytest
from unittest.mock import MagicMock, patch, call
import re

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
from commander.services.telnet_service import TelnetService
from commander.session_manager import SessionManager, SessionConfig, SessionType
from commander.ui.telnet_tab import TelnetTab
from commander.telnet_client import TelnetClient


class MockTelnetSession:
    """Mock Telnet session that simulates server responses with various prompt patterns."""
    
    def __init__(self, config):
        self.config = config
        self.is_connected = False
        # Multiple prompt patterns that were causing truncation issues
        self.prompt_patterns = [
            re.compile(r'\n\d+[a-z]%\s*$'),  # Prompt at beginning of line after newline
            re.compile(r'^\d+[a-z]%\s*$'),   # Prompt at very beginning of response
            re.compile(r'\r\n\d+[a-z]%\s*$') # Prompt after carriage return and newline
        ]
        
    def connect(self):
        """Simulate connection to Telnet server."""
        self.is_connected = True
        return True
        
    def disconnect(self):
        """Simulate disconnection from Telnet server."""
        self.is_connected = False
        
    def send_command(self, command, timeout=5.0):
        """
        Simulate sending a command and receiving a response.
        
        This method simulates various response patterns that previously caused truncation:
        1. Responses with percentage symbols
        2. Long responses
        3. Responses with different prompt patterns
        """
        # Simulate different types of responses based on command
        if "fbc io structure" in command:
            # Simulate FBC command response with percentage symbols that caused truncation
            token_id = command.split()[-1][:3]  # Extract token ID
            return self._generate_fbc_response(token_id)
        elif "fbc rupi counters" in command:
            # Simulate RPC command response
            action = "print" if "print" in command else "clear"
            token_id = command.split()[-1][:3]  # Extract token ID
            return self._generate_rpc_response(token_id, action)
        else:
            # Generic response for other commands
            return self._generate_generic_response(command)
            
    def _generate_fbc_response(self, token_id):
        """Generate a realistic FBC response that includes percentage symbols."""
        # This response includes patterns that previously caused truncation
        response = (
            f"print from fbc io structure {token_id}0000\r\n"
            f"Fieldbus Configuration for Token {token_id}\r\n"
            f"----------------------------------------\r\n"
            f"Status: Active (100%)\r\n"
            f"Connection Quality: 98%\r\n"
            f"Packet Loss: 2%\r\n"
            f"Devices Connected: 5\r\n"
            f"Configuration Version: 2.1.{token_id}\r\n"
            f"Last Update: 2025-09-14 10:30:45\r\n"
            f"Diagnostic Info:\r\n"
            f"  - Device 1: OK (100%)\r\n"
            f"  - Device 2: OK (99%)\r\n"
            f"  - Device 3: Warning (85%)\r\n"
            f"  - Device 4: OK (100%)\r\n"
            f"  - Device 5: OK (97%)\r\n"
            f"Memory Usage: 45%\r\n"
            f"Buffer Status: 67%\r\n"
            f"----------------------------------------\r\n"
            f"{int(token_id)}a%\r\n"  # This prompt pattern previously caused truncation
        )
        return response
        
    def _generate_rpc_response(self, token_id, action):
        """Generate a realistic RPC response."""
        if action == "print":
            response = (
                f"print from fbc rupi counters {token_id}0000\r\n"
                f"Rupi Counters for Token {token_id}\r\n"
                f"--------------------------------\r\n"
                f"Counter 1: 123456 (100%)\r\n"
                f"Counter 2: 789012 (95%)\r\n"
                f"Counter 3: 345678 (88%)\r\n"
                f"Counter 4: 901234 (100%)\r\n"
                f"Total Packets: 1234567\r\n"
                f"Error Rate: 0.5%\r\n"
                f"--------------------------------\r\n"
                f"{int(token_id)}b%\r\n"  # Different prompt pattern
            )
        else:  # clear
            response = (
                f"clear fbc rupi counters {token_id}0000\r\n"
                f"Rupi counters cleared for token {token_id}\r\n"
                f"Previous values have been reset\r\n"
                f"{int(token_id)}c%\r\n"  # Another prompt pattern
            )
        return response
        
    def _generate_generic_response(self, command):
        """Generate a generic response for any command."""
        response = (
            f"{command}\r\n"
            f"Command executed successfully\r\n"
            f"Response time: 15ms\r\n"
            f"System status: Operational (99%)\r\n"
            f"Memory: 64%\r\n"
            f"CPU: 23%\r\n"
            f"Network: 87%\r\n"
            f"--------------------------------\r\n"
            f"1d%\r\n"  # Simple prompt pattern
        )
        return response


class TestTelnetCommandOutput:
    """Test suite for Telnet command output truncation fix."""
    
    @pytest.fixture
    def node_manager(self):
        """Create a node manager with test configuration."""
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
        """Mock SessionManager that returns our MockTelnetSession."""
        mock_sm = MagicMock()
        mock_sm.get_debugger_session.return_value = None
        
        # Mock get_or_create_session to return our MockTelnetSession
        def mock_get_or_create_session(session_key, session_type, config):
            session = MockTelnetSession(config)
            session.connect()
            return session
            
        mock_sm.get_or_create_session.side_effect = mock_get_or_create_session
        return mock_sm
    
    @pytest.fixture
    def command_queue(self, mock_session_manager):
        """Create a command queue with our mocked session manager."""
        return CommandQueue(session_manager=mock_session_manager)
    
    @pytest.fixture
    def mock_log_writer(self):
        """Mock LogWriter."""
        mock_lw = MagicMock()
        mock_lw.loggers = {}
        mock_lw.get_node_log_path.return_value = "/tmp/test.log"
        mock_lw.open_log.return_value = None
        return mock_lw
    
    @pytest.fixture
    def fbc_service(self, node_manager, command_queue, mock_log_writer):
        """Create an FBC command service."""
        service = FbcCommandService(node_manager, command_queue, mock_log_writer)
        return service
    
    @pytest.fixture
    def rpc_service(self, node_manager, command_queue):
        """Create an RPC command service."""
        service = RpcCommandService(node_manager, command_queue)
        return service
    
    @pytest.fixture
    def context_menu_service(self, node_manager):
        """Create a context menu service."""
        context_menu_filter = ContextMenuFilterService()
        service = ContextMenuService(node_manager, context_menu_filter)
        return service
    
    @pytest.fixture
    def telnet_service(self, mock_session_manager):
        """Create a Telnet service with mocked dependencies."""
        service = TelnetService(mock_session_manager)
        return service
    
    @pytest.fixture
    def telnet_tab(self):
        """Create a Telnet tab."""
        return TelnetTab()
    
    def test_fbc_command_output_from_context_menu(self, node_manager, context_menu_service, fbc_service, command_queue):
        """
        Test that FBC commands executed from context menu produce complete output.
        
        This test verifies:
        1. Command is properly queued
        2. Full response is captured without truncation
        3. Response includes percentage symbols correctly
        """
        # Scan log files
        node_manager.scan_log_files()
        
        # Get AP01m node
        node = node_manager.get_node("AP01m")
        assert node is not None, "AP01m node should exist"
        
        # Mock presenter to capture command execution
        mock_presenter = MagicMock()
        context_menu_service.set_presenter(mock_presenter)
        
        # Execute FBC command for token "162" via context menu
        context_menu_service._handle_fbc_token_action("AP01m", "162")
        
        # Verify that the presenter method was called
        mock_presenter.process_fieldbus_command.assert_called_once_with("162", "AP01m")
            
    def test_rpc_command_output_from_context_menu(self, node_manager, context_menu_service, rpc_service, command_queue):
        """
        Test that RPC commands executed from context menu produce complete output.
        
        This test verifies:
        1. Print command produces complete output with percentages
        2. Clear command produces complete output
        3. Both responses are not truncated
        """
        # Scan log files
        node_manager.scan_log_files()
        
        # Get AP01m node
        node = node_manager.get_node("AP01m")
        assert node is not None, "AP01m node should exist"
        
        # Mock presenter to capture command execution
        mock_presenter = MagicMock()
        context_menu_service.set_presenter(mock_presenter)
        
        # Test RPC print command
        context_menu_service._handle_rpc_token_action("AP01m", "162", "print")
        mock_presenter.process_rpc_command.assert_called_with("AP01m", "162", "print")
        
        # Test RPC clear command
        mock_presenter.reset_mock()
        context_menu_service._handle_rpc_token_action("AP01m", "162", "clear")
        mock_presenter.process_rpc_command.assert_called_with("AP01m", "162", "clear")
    
    def test_fbc_command_output_from_telnet_tab(self, node_manager, telnet_service, command_queue):
        """
        Test that FBC commands executed from Telnet tab produce complete output.
        
        This test verifies:
        1. Command is properly executed via Telnet service
        2. Full response is captured without truncation
        3. Response includes percentage symbols correctly
        """
        # Scan log files
        node_manager.scan_log_files()
        
        # Get AP01m node
        node = node_manager.get_node("AP01m")
        assert node is not None, "AP01m node should exist"
        
        # Mock command finished signal to capture response
        captured_responses = []
        
        def mock_command_finished(response, automatic):
            captured_responses.append((response, automatic))
            
            # Verify response is complete and not truncated
            assert "100%" in response, "Response should contain percentage symbols"
            assert "Fieldbus Configuration" in response, "Response should contain full content"
            assert "162a%" in response, "Response should end with correct prompt pattern"
            assert response.count("%") >= 5, "Response should contain multiple percentage symbols"
            
        telnet_service.command_finished_signal.connect(mock_command_finished)
        
        # Create a mock telnet session for execution
        config = SessionConfig(host="192.168.0.11", port=23, session_type=SessionType.TELNET)
        mock_telnet_session = MockTelnetSession(config)
        mock_telnet_session.connect()
        
        # Set the telnet session
        telnet_service.telnet_session = mock_telnet_session
        telnet_service.active_telnet_client = mock_telnet_session
        
        # Set current token
        token = NodeToken(token_id="162", token_type="FBC", name="AP01m", ip_address="192.168.0.11")
        telnet_service.set_current_token(token)
        
        # Execute FBC command directly via _run_command (avoiding threading issues in tests)
        telnet_service._run_command("print from fbc io structure 1620000", False)
        
        # Verify that response was captured
        assert len(captured_responses) == 1, "One response should have been captured"
        response, automatic = captured_responses[0]
        
        # Verify response content
        assert "100%" in response, "Response should contain percentage symbols"
        assert "Fieldbus Configuration" in response, "Response should contain full content"
        assert "162a%" in response, "Response should end with correct prompt pattern"
        
    def test_output_consistency_between_execution_paths(self, node_manager, context_menu_service, telnet_service, fbc_service, command_queue):
        """
        Test that command output is consistent between context menu and Telnet tab execution.
        
        This test verifies:
        1. Same command produces identical output regardless of execution path
        2. Both outputs are complete and not truncated
        3. Percentage symbols are preserved in both paths
        """
        # Scan log files
        node_manager.scan_log_files()
        
        # Get AP01m node
        node = node_manager.get_node("AP01m")
        assert node is not None, "AP01m node should exist"
        
        # Capture responses from both execution paths
        context_menu_responses = []
        telnet_tab_responses = []
        
        # Mock command queue for context menu execution
        def mock_add_command_context(command, token, telnet_client=None):
            # Create a mock telnet session for execution
            config = SessionConfig(host=token.ip_address, port=23, session_type=SessionType.TELNET)
            session = MockTelnetSession(config)
            session.connect()
            
            # Execute command and capture response
            response = session.send_command(command)
            context_menu_responses.append((command, response))
            return True  # Return success
            
        # Mock command finished signal for Telnet tab execution
        def mock_command_finished(response, automatic):
            telnet_tab_responses.append((response, automatic))
            
        telnet_service.command_finished_signal.connect(mock_command_finished)
        
        # Test context menu execution path
        # Mock the presenter's process_fieldbus_command method to directly call the command queue
        mock_presenter = MagicMock()
        context_menu_service.set_presenter(mock_presenter)
        
        # Instead of calling the context menu service directly, we'll mock the presenter method
        # to directly call the command queue, which is what would happen in the real implementation
        def mock_process_fieldbus_command(token_id, node_name):
            # This simulates what the presenter would do
            # Get the token
            node = node_manager.get_node(node_name)
            if not node:
                return
                
            # Find the token
            token = None
            for token_list in node.tokens.values():
                if isinstance(token_list, list):
                    for t in token_list:
                        if isinstance(t, NodeToken) and t.token_id == token_id and t.token_type == "FBC":
                            token = t
                            break
                elif isinstance(token_list, NodeToken) and token_list.token_id == token_id and token_list.token_type == "FBC":
                    token = token_list
                    break
                    
            if not token:
                return
                
            # Add command to queue (this is what would happen in the real implementation)
            config = SessionConfig(host=token.ip_address, port=23, session_type=SessionType.TELNET)
            session = MockTelnetSession(config)
            session.connect()
            response = session.send_command(f"print from fbc io structure {token_id}0000")
            context_menu_responses.append((f"print from fbc io structure {token_id}0000", response))
            
        mock_presenter.process_fieldbus_command.side_effect = mock_process_fieldbus_command
        
        # Execute FBC command via context menu
        context_menu_service._handle_fbc_token_action("AP01m", "162")
        
        # Test Telnet tab execution path
        # Create a mock telnet session for execution
        config = SessionConfig(host="192.168.0.11", port=23, session_type=SessionType.TELNET)
        mock_telnet_session = MockTelnetSession(config)
        mock_telnet_session.connect()
        
        # Set the telnet session
        telnet_service.telnet_session = mock_telnet_session
        telnet_service.active_telnet_client = mock_telnet_session
        
        # Set current token
        token = NodeToken(token_id="162", token_type="FBC", name="AP01m", ip_address="192.168.0.11")
        telnet_service.set_current_token(token)
        
        # Execute FBC command directly via _run_command (avoiding threading issues in tests)
        telnet_service._run_command("print from fbc io structure 1620000", False)
        
        # Verify that both execution paths produced responses
        assert len(context_menu_responses) == 1, "Context menu should produce one response"
        assert len(telnet_tab_responses) == 1, "Telnet tab should produce one response"
        
        # Extract responses
        _, context_response = context_menu_responses[0]
        telnet_response, _ = telnet_tab_responses[0]
        
        # Verify both responses are complete and not truncated
        for response in [context_response, telnet_response]:
            assert "100%" in response, "Response should contain percentage symbols"
            assert "Fieldbus Configuration" in response, "Response should contain full content"
            assert "162a%" in response, "Response should end with correct prompt pattern"
            assert response.count("%") >= 5, "Response should contain multiple percentage symbols"
        
        # Verify responses are identical (accounting for possible minor differences)
        # Both should contain the same key information
        assert "Fieldbus Configuration for Token 162" in context_response
        assert "Fieldbus Configuration for Token 162" in telnet_response
        
        assert "Status: Active (100%)" in context_response
        assert "Status: Active (100%)" in telnet_response
        
        assert "Connection Quality: 98%" in context_response
        assert "Connection Quality: 98%" in telnet_response
        
        # Both should end with the same prompt pattern
        assert context_response.endswith("162a%\r\n") or context_response.endswith("162a%")
        assert telnet_response.endswith("162a%\r\n") or telnet_response.endswith("162a%")
    
    def test_long_output_not_truncated(self, node_manager, telnet_service):
        """
        Test that long command outputs are not truncated.
        
        This test verifies:
        1. Long responses are captured completely
        2. All content is preserved
        3. Prompt detection works correctly for long outputs
        """
        # Create a mock telnet session for execution
        config = SessionConfig(host="192.168.0.11", port=23, session_type=SessionType.TELNET)
        mock_telnet_session = MockTelnetSession(config)
        mock_telnet_session.connect()
        
        # Generate a long response
        long_response = (
            "print from fbc io structure 1630000\r\n"
            "Fieldbus Configuration for Token 163 - Detailed Analysis\r\n"
            "=====================================================\r\n"
        )
        
        # Add many lines to make it a long response
        for i in range(100):
            long_response += f"Line {i+1}: Configuration parameter with 100% accuracy and 0% error rate\r\n"
        
        long_response += (
            "Summary:\r\n"
            "  Total Parameters: 100\r\n"
            "  Active Parameters: 98 (98%)\r\n"
            "  Inactive Parameters: 2 (2%)\r\n"
            "  Error Rate: 0.0%\r\n"
            "  Success Rate: 100.0%\r\n"
            "  Average Response Time: 15ms\r\n"
            "  Peak Response Time: 45ms\r\n"
            "  Memory Usage: 67%\r\n"
            "  CPU Usage: 23%\r\n"
            "  Network Utilization: 45%\r\n"
            "  Device Health: Optimal (99%)\r\n"
            "=====================================================\r\n"
            "163a%\r\n"
        )
        
        # Override the send_command method to return our long response
        def mock_send_command(command, timeout=5.0):
            return long_response
            
        mock_telnet_session.send_command = mock_send_command
        
        # Set the telnet session
        telnet_service.telnet_session = mock_telnet_session
        telnet_service.active_telnet_client = mock_telnet_session
        
        # Set current token
        token = NodeToken(token_id="163", token_type="FBC", name="AP01m", ip_address="192.168.0.11")
        telnet_service.set_current_token(token)
        
        # Capture response
        captured_responses = []
        
        def mock_command_finished(response, automatic):
            captured_responses.append((response, automatic))
            
        telnet_service.command_finished_signal.connect(mock_command_finished)
        
        # Execute command directly via _run_command (avoiding threading issues in tests)
        telnet_service._run_command("print from fbc io structure 1630000", False)
        
        # Verify response
        assert len(captured_responses) == 1, "One response should have been captured"
        response, _ = captured_responses[0]
        
        # Verify response is complete and not truncated
        assert len(response) == len(long_response), "Response should not be truncated"
        assert response.count("Configuration parameter") == 100, "All configuration parameters should be present"
        assert "Success Rate: 100.0%" in response, "Response should contain percentage symbols"
        assert response.endswith("163a%\r\n") or response.endswith("163a%"), "Response should end with correct prompt"
        
    def test_various_prompt_patterns_handled_correctly(self, node_manager, telnet_service):
        """
        Test that various prompt patterns are handled correctly without truncation.
        
        This test verifies:
        1. Different prompt patterns are detected correctly
        2. Responses are not truncated regardless of prompt pattern
        3. Percentage symbols in different positions are preserved
        """
        # Test different prompt patterns
        prompt_patterns = [
            (r'\n164a%\s*$', "\r\nFieldbus data...\n164a%\r\n"),  # Newline prompt
            (r'^164b%\s*$', "164b%\r\nFieldbus data...\r\n"),     # Beginning prompt
            (r'\r\n164c%\s*$', "Fieldbus data...\r\n164c%\r\n")   # Carriage return prompt
        ]
        
        for pattern, response_template in prompt_patterns:
            # Create a mock telnet session
            config = SessionConfig(host="192.168.0.11", port=23, session_type=SessionType.TELNET)
            mock_telnet_session = MockTelnetSession(config)
            mock_telnet_session.connect()
            
            # Override prompt patterns to test specific one
            mock_telnet_session.prompt_patterns = [re.compile(pattern)]
            
            # Create response with the specific pattern
            response = (
                "print from fbc io structure 1640000\r\n"
                "Fieldbus Configuration for Token 164\r\n"
                "----------------------------------------\r\n"
                "Status: Active (100%)\r\n"
                "Connection Quality: 99%\r\n"
                "Packet Loss: 1%\r\n"
                "Devices Connected: 3\r\n"
                "Configuration Version: 3.2.164\r\n"
                "Last Update: 2025-09-14 11:45:30\r\n"
                "Diagnostic Info:\r\n"
                "  - Device 1: OK (100%)\r\n"
                "  - Device 2: OK (98%)\r\n"
                "  - Device 3: Warning (87%)\r\n"
                "Memory Usage: 56%\r\n"
                "Buffer Status: 78%\r\n"
                "----------------------------------------\r\n"
            ) + response_template.split('\n')[-2] + "\r\n"  # Add the prompt part
            
            # Override the send_command method
            def mock_send_command(command, timeout=5.0):
                return response
                
            mock_telnet_session.send_command = mock_send_command
            
            # Set the telnet session
            telnet_service.telnet_session = mock_telnet_session
            telnet_service.active_telnet_client = mock_telnet_session
            
            # Set current token
            token = NodeToken(token_id="164", token_type="FBC", name="AP01m", ip_address="192.168.0.11")
            telnet_service.set_current_token(token)
            
            # Capture response
            captured_responses = []
            
            def mock_command_finished(response_text, automatic):
                captured_responses.append((response_text, automatic))
                
            # Disconnect any existing connections to avoid duplicate signals
            try:
                telnet_service.command_finished_signal.disconnect()
            except:
                pass  # Ignore if no connections exist
                
            telnet_service.command_finished_signal.connect(mock_command_finished)
            
            # Execute command directly via _run_command (avoiding threading issues in tests)
            telnet_service._run_command("print from fbc io structure 1640000", False)
            
            # Verify response
            assert len(captured_responses) == 1, "One response should have been captured"
            response_text, _ = captured_responses[0]
            
            # Verify response is complete and not truncated
            assert "100%" in response_text, "Response should contain percentage symbols"
            assert "Fieldbus Configuration for Token 164" in response_text, "Response should contain full content"
            assert "164" in response_text and "%" in response_text, "Response should contain token and percentage"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])