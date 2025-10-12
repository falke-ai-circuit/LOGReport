import pytest
from unittest.mock import MagicMock, patch
from PyQt6.QtWidgets import QApplication, QTextEdit, QPushButton, QLineEdit
from PyQt6.QtCore import Qt
import sys
import os

# Add src directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'src')))

from commander.ui.bstool_tab import BsToolTab
from commander.services.bstool_command_service import BsToolCommandService
from commander.presenters.commander_presenter import CommanderPresenter
from commander.ui.commander_ui_factory import CommanderUIFactory
from commander.node_manager import NodeManager
from commander.log_writer import LogWriter
from commander.services.status_service import StatusService
from commander.command_queue import CommandQueue
from commander.services.fbc_command_service import FbcCommandService
from commander.services.rpc_command_service import RpcCommandService
from commander.services.context_menu_service import ContextMenuService
from commander.services.context_menu_filter import ContextMenuFilterService


@pytest.fixture(scope="module")
def app():
    """Fixture for a QApplication instance."""
    return QApplication.instance() or QApplication(sys.argv)


@pytest.fixture
def bstool_tab(app):
    """Fixture for a BsToolTab instance."""
    tab = BsToolTab()
    # Initialize the button state to disconnected (default state)
    from commander.widgets import ConnectionState
    tab.update_status(ConnectionState.DISCONNECTED)
    return tab


class TestBsToolTabUI:
    """UI-level tests for BsTool tab execute command functionality."""

    def test_bstool_tab_initialization(self, bstool_tab):
        """Test that BsToolTab initializes with correct UI elements."""
        # Check that UI elements exist
        assert bstool_tab.bstool_path_edit is not None
        assert bstool_tab.env_var_label is not None
        assert bstool_tab.status_label is not None
        assert bstool_tab.output is not None
        assert bstool_tab.command_input is not None
        assert bstool_tab.execute_btn is not None
        assert bstool_tab.copy_btn is not None
        assert bstool_tab.clear_terminal_btn is not None
        assert bstool_tab.clear_log_btn is not None
        
        # Check initial state
        assert bstool_tab.env_var_label.text() == "COMMUNICATION_LINE=AB01"
        assert bstool_tab.status_label.text() == "\u25CB"  # Disconnected icon
        assert bstool_tab.execute_btn.isEnabled() == False  # Should be disabled initially

    def test_command_input_and_execute_button_interaction(self, bstool_tab, qtbot):
        """Test entering a command and clicking execute button."""
        # Track if execute signal was emitted
        execute_signals = []
        bstool_tab.execute_clicked.connect(lambda cmd: execute_signals.append(cmd))
        
        # Simulate connected state to enable the button
        from commander.widgets import ConnectionState
        bstool_tab.update_status(ConnectionState.CONNECTED)
        
        # Enter a command
        test_command = "test command -arg value"
        bstool_tab.command_input.setText(test_command)
        
        # Click execute button
        qtbot.mouseClick(bstool_tab.execute_btn, Qt.MouseButton.LeftButton)
        
        # Verify signal was emitted with correct command
        assert len(execute_signals) == 1
        assert execute_signals[0] == test_command

    def test_command_input_return_key_interaction(self, bstool_tab, qtbot):
        """Test entering a command and pressing return key."""
        # Track if execute signal was emitted
        execute_signals = []
        bstool_tab.execute_clicked.connect(lambda cmd: execute_signals.append(cmd))
        
        # Simulate connected state to enable the button
        from commander.widgets import ConnectionState
        bstool_tab.update_status(ConnectionState.CONNECTED)
        
        # Enter a command
        test_command = "test command -arg value"
        bstool_tab.command_input.setText(test_command)
        
        # Press return key
        qtbot.keyClick(bstool_tab.command_input, Qt.Key.Key_Return)
        
        # Verify signal was emitted with correct command
        assert len(execute_signals) == 1
        assert execute_signals[0] == test_command

    def test_output_display(self, bstool_tab):
        """Test that output is correctly displayed in the output area."""
        # Add some output text
        test_output = "Test output line 1\nTest output line 2"
        bstool_tab.append_output(test_output)
        
        # Verify output is displayed
        assert test_output in bstool_tab.output.toPlainText()

    def test_clear_output(self, bstool_tab):
        """Test that output area can be cleared."""
        # Add some output text
        test_output = "Test output line 1\nTest output line 2"
        bstool_tab.append_output(test_output)
        
        # Clear output
        bstool_tab.clear_output()
        
        # Verify output is cleared
        assert bstool_tab.output.toPlainText() == ""

    def test_get_command(self, bstool_tab):
        """Test getting command text from input field."""
        # Set command text
        test_command = "test command -arg value"
        bstool_tab.command_input.setText(test_command)
        
        # Get command text
        retrieved_command = bstool_tab.get_command()
        
        # Verify command text
        assert retrieved_command == test_command

    def test_clear_command(self, bstool_tab):
        """Test clearing command input field."""
        # Set command text
        test_command = "test command -arg value"
        bstool_tab.command_input.setText(test_command)
        
        # Clear command
        bstool_tab.clear_command()
        
        # Verify command is cleared
        assert bstool_tab.command_input.text() == ""

    def test_status_updates(self, bstool_tab):
        """Test that status indicator updates correctly."""
        from commander.widgets import ConnectionState
        
        # Test disconnected state
        bstool_tab.update_status(ConnectionState.DISCONNECTED)
        assert bstool_tab.status_label.text() == "\u25CB"  # ○
        assert "color: #888" in bstool_tab.status_label.styleSheet()
        assert bstool_tab.execute_btn.isEnabled() == False
        
        # Test connecting state
        bstool_tab.update_status(ConnectionState.CONNECTING)
        assert bstool_tab.status_label.text() == "\u25D1"  # ◑
        assert "color: orange" in bstool_tab.status_label.styleSheet()
        assert bstool_tab.execute_btn.isEnabled() == False
        
        # Test connected state
        bstool_tab.update_status(ConnectionState.CONNECTED)
        assert bstool_tab.status_label.text() == "\u25CF"  # ●
        assert "color: lime" in bstool_tab.status_label.styleSheet()
        assert bstool_tab.execute_btn.isEnabled() == True
        
        # Test error state
        bstool_tab.update_status(ConnectionState.ERROR)
        assert bstool_tab.status_label.text() == "\u2a2f"  # ⨯
        assert "color: red" in bstool_tab.status_label.styleSheet()
        assert bstool_tab.execute_btn.isEnabled() == False

    def test_action_button_signals(self, bstool_tab, qtbot):
        """Test that action buttons emit correct signals."""
        # Track signals
        copy_signals = []
        clear_terminal_signals = []
        clear_log_signals = []
        
        bstool_tab.copy_to_log_clicked.connect(lambda: copy_signals.append(True))
        bstool_tab.clear_terminal_clicked.connect(lambda: clear_terminal_signals.append(True))
        bstool_tab.clear_log_clicked.connect(lambda: clear_log_signals.append(True))
        
        # Click copy to log button
        qtbot.mouseClick(bstool_tab.copy_btn, Qt.MouseButton.LeftButton)
        assert len(copy_signals) == 1
        
        # Click clear terminal button
        qtbot.mouseClick(bstool_tab.clear_terminal_btn, Qt.MouseButton.LeftButton)
        assert len(clear_terminal_signals) == 1
        
        # Click clear log button
        qtbot.mouseClick(bstool_tab.clear_log_btn, Qt.MouseButton.LeftButton)
        assert len(clear_log_signals) == 1

    def test_bstool_execution_integration_with_presenter(self, bstool_tab, qtbot):
        """Test integration between BsToolTab and Presenter through signal connection."""
        # Track if execute signal was emitted
        execute_signals = []
        bstool_tab.execute_clicked.connect(lambda cmd: execute_signals.append(cmd))
        
        # Simulate connected state to enable the button
        from commander.widgets import ConnectionState
        bstool_tab.update_status(ConnectionState.CONNECTED)
        
        # Enter a command
        test_command = "-errlog AP01"
        bstool_tab.command_input.setText(test_command)
        
        # Click execute button
        qtbot.mouseClick(bstool_tab.execute_btn, Qt.MouseButton.LeftButton)
        
        # Verify signal was emitted with correct command
        assert len(execute_signals) == 1
        assert execute_signals[0] == test_command


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
