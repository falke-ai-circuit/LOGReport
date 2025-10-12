"""
Test suite for sequential command execution output display.

Validates that sequential execution (Print All Nodes) displays command output
in appropriate tabs just like manual execution.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from PyQt5.QtWidgets import QApplication
import sys

# Ensure QApplication exists for PyQt tests
app = QApplication.instance()
if app is None:
    app = QApplication(sys.argv)

from src.commander.presenters.node_tree_presenter import NodeTreePresenter
from src.commander.ui.commander_window import CommanderWindow
from src.commander.models import NodeToken


class TestSequentialOutputDisplay:
    """Test sequential execution output display functionality"""
    
    def test_node_tree_presenter_has_output_signal(self):
        """Verify NodeTreePresenter has command_output_display_signal"""
        # Create mock dependencies
        view = Mock()
        view.update_control_buttons = Mock()
        node_manager = Mock()
        session_manager = Mock()
        log_writer = Mock()
        command_queue = Mock()
        command_queue.command_completed = Mock()
        command_queue.command_completed.connect = Mock()
        fbc_service = Mock()
        rpc_service = Mock()
        context_menu_service = Mock()
        bstool_service = Mock()
        
        # Create presenter
        presenter = NodeTreePresenter(
            view, node_manager, session_manager, log_writer,
            command_queue, fbc_service, rpc_service,
            context_menu_service, bstool_service
        )
        
        # Verify signal exists
        assert hasattr(presenter, 'command_output_display_signal')
    
    def test_handle_command_completed_emits_output_for_fbc(self):
        """Verify handle_command_completed emits output signal for FBC tokens"""
        # Create mock dependencies
        view = Mock()
        view.update_control_buttons = Mock()
        node_manager = Mock()
        session_manager = Mock()
        log_writer = Mock()
        command_queue = Mock()
        command_queue.command_completed = Mock()
        command_queue.command_completed.connect = Mock()
        fbc_service = Mock()
        rpc_service = Mock()
        context_menu_service = Mock()
        bstool_service = Mock()
        
        # Create presenter
        presenter = NodeTreePresenter(
            view, node_manager, session_manager, log_writer,
            command_queue, fbc_service, rpc_service,
            context_menu_service, bstool_service
        )
        
        # Connect signal to mock slot
        signal_emitted = []
        presenter.command_output_display_signal.connect(lambda output, token_type: signal_emitted.append((output, token_type)))
        
        # Create FBC token
        token = NodeToken(
            node_name="AP01m",
            token_id="162",
            token_type="FBC",
            ip_address="192.168.0.11",
            log_path="D:/logs/AP01m_162.fbc"
        )
        
        # Call handle_command_completed with FBC token and result
        result_text = "FBC command output with data\nLine 2\nLine 3"
        presenter.handle_command_completed("print from fbc io structure 1620000", result_text, True, token)
        
        # Verify signal was emitted
        assert len(signal_emitted) == 1
        assert signal_emitted[0][0] == result_text
        assert signal_emitted[0][1] == "FBC"
    
    def test_handle_command_completed_emits_output_for_rpc(self):
        """Verify handle_command_completed emits output signal for RPC tokens"""
        # Create mock dependencies
        view = Mock()
        view.update_control_buttons = Mock()
        node_manager = Mock()
        session_manager = Mock()
        log_writer = Mock()
        command_queue = Mock()
        command_queue.command_completed = Mock()
        command_queue.command_completed.connect = Mock()
        fbc_service = Mock()
        rpc_service = Mock()
        context_menu_service = Mock()
        bstool_service = Mock()
        
        # Create presenter
        presenter = NodeTreePresenter(
            view, node_manager, session_manager, log_writer,
            command_queue, fbc_service, rpc_service,
            context_menu_service, bstool_service
        )
        
        # Connect signal to mock slot
        signal_emitted = []
        presenter.command_output_display_signal.connect(lambda output, token_type: signal_emitted.append((output, token_type)))
        
        # Create RPC token
        token = NodeToken(
            node_name="AP01m",
            token_id="162",
            token_type="RPC",
            ip_address="192.168.0.11",
            log_path="D:/logs/AP01m_162.rpc.log"
        )
        
        # Call handle_command_completed with RPC token and result
        result_text = "RPC command output\nStatus: OK"
        presenter.handle_command_completed("ps io rpc 162", result_text, True, token)
        
        # Verify signal was emitted
        assert len(signal_emitted) == 1
        assert signal_emitted[0][0] == result_text
        assert signal_emitted[0][1] == "RPC"
    
    def test_handle_command_completed_no_output_for_log(self):
        """Verify handle_command_completed does NOT emit output signal for LOG tokens (BsTool handles separately)"""
        # Create mock dependencies
        view = Mock()
        view.update_control_buttons = Mock()
        node_manager = Mock()
        session_manager = Mock()
        log_writer = Mock()
        command_queue = Mock()
        command_queue.command_completed = Mock()
        command_queue.command_completed.connect = Mock()
        fbc_service = Mock()
        rpc_service = Mock()
        context_menu_service = Mock()
        bstool_service = Mock()
        
        # Create presenter
        presenter = NodeTreePresenter(
            view, node_manager, session_manager, log_writer,
            command_queue, fbc_service, rpc_service,
            context_menu_service, bstool_service
        )
        
        # Connect signal to mock slot
        signal_emitted = []
        presenter.command_output_display_signal.connect(lambda output, token_type: signal_emitted.append((output, token_type)))
        
        # Create LOG token
        token = NodeToken(
            node_name="AP01m",
            token_id="",
            token_type="LOG",
            ip_address="192.168.0.11",
            log_path="D:/logs/AP01m.log"
        )
        
        # Call handle_command_completed with LOG token
        result_text = "LOG output from BsTool"
        presenter.handle_command_completed("-errlog AP01m", result_text, True, token)
        
        # Verify signal was NOT emitted (LOG handled by BsTool service)
        assert len(signal_emitted) == 0
    
    def test_handle_sequential_output_routes_to_telnet_for_fbc(self):
        """Verify _handle_sequential_output routes FBC output to Telnet tab"""
        with patch('src.commander.ui.commander_window.initialize_qt'):
            with patch('src.commander.ui.commander_window.CommanderUIFactory'):
                with patch('src.commander.ui.commander_window.CommanderPresenter'):
                    with patch('src.commander.ui.commander_window.NodeTreePresenter'):
                        # Create commander window with mocked dependencies
                        window = CommanderWindow()
                        
                        # Mock telnet tab
                        window.telnet_tab = Mock()
                        window.telnet_tab.append_output = Mock()
                        
                        # Call handler with FBC output
                        output_text = "FBC sequential output"
                        window._handle_sequential_output(output_text, "FBC")
                        
                        # Verify telnet tab received output
                        window.telnet_tab.append_output.assert_called_once_with(output_text)
    
    def test_handle_sequential_output_routes_to_telnet_for_rpc(self):
        """Verify _handle_sequential_output routes RPC output to Telnet tab"""
        with patch('src.commander.ui.commander_window.initialize_qt'):
            with patch('src.commander.ui.commander_window.CommanderUIFactory'):
                with patch('src.commander.ui.commander_window.CommanderPresenter'):
                    with patch('src.commander.ui.commander_window.NodeTreePresenter'):
                        # Create commander window with mocked dependencies
                        window = CommanderWindow()
                        
                        # Mock telnet tab
                        window.telnet_tab = Mock()
                        window.telnet_tab.append_output = Mock()
                        
                        # Call handler with RPC output
                        output_text = "RPC sequential output"
                        window._handle_sequential_output(output_text, "RPC")
                        
                        # Verify telnet tab received output
                        window.telnet_tab.append_output.assert_called_once_with(output_text)
    
    def test_handle_sequential_output_no_action_for_log(self):
        """Verify _handle_sequential_output does nothing for LOG (BsTool handles it)"""
        with patch('src.commander.ui.commander_window.initialize_qt'):
            with patch('src.commander.ui.commander_window.CommanderUIFactory'):
                with patch('src.commander.ui.commander_window.CommanderPresenter'):
                    with patch('src.commander.ui.commander_window.NodeTreePresenter'):
                        # Create commander window with mocked dependencies
                        window = CommanderWindow()
                        
                        # Mock telnet tab
                        window.telnet_tab = Mock()
                        window.telnet_tab.append_output = Mock()
                        
                        # Call handler with LOG output
                        output_text = "LOG output from BsTool"
                        window._handle_sequential_output(output_text, "LOG")
                        
                        # Verify telnet tab was NOT called (BsTool handles LOG separately)
                        window.telnet_tab.append_output.assert_not_called()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
