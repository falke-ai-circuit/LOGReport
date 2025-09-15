import pytest
from unittest.mock import MagicMock, patch
from PyQt6.QtWidgets import QApplication, QMenu
from PyQt6.QtCore import Qt, QPoint
from PyQt6.QtGui import QAction
import os
import tempfile
import sys
import logging

# Add src directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'src')))

from commander.main_window import CommanderWindow
from commander.services.bstool_command_service import BsToolCommandService
from commander.services.context_menu_service import ContextMenuService
from commander.services.context_menu_filter import ContextMenuFilterService
from commander.node_manager import NodeManager
from commander.log_writer import LogWriter
from commander.presenters.commander_presenter import CommanderPresenter
from commander.presenters.node_tree_presenter import NodeTreePresenter
from commander.ui.commander_ui_factory import CommanderUIFactory
from commander.services.status_service import StatusService
from commander.command_queue import CommandQueue
from commander.services.fbc_command_service import FbcCommandService
from commander.services.rpc_command_service import RpcCommandService


# Ensure QApplication is initialized only once
app = None

def get_app():
    global app
    if app is None:
        app = QApplication.instance() or QApplication(sys.argv)
    return app


class TestBsToolContextMenuIntegration:
    """Integration tests for BsTool context menu action."""

    def setup_method(self):
        """Set up test environment."""
        self.app = get_app()
        self.temp_dir = tempfile.mkdtemp()
        self.log_file_path = os.path.join(self.temp_dir, "test.log")
        with open(self.log_file_path, 'w') as f:
            f.write("Sample log content\n")
        
        # Initialize components
        self.node_manager = NodeManager()
        self.log_writer = LogWriter()
        self.context_menu_filter = ContextMenuFilterService()
        self.context_menu_service = ContextMenuService(self.node_manager, self.context_menu_filter)
        self.bstool_service = BsToolCommandService(self.log_writer)
        self.status_service = StatusService()
        self.command_queue = CommandQueue(None)  # Mock session manager
        self.fbc_service = FbcCommandService(self.node_manager, self.command_queue, self.log_writer)
        self.rpc_service = RpcCommandService(self.node_manager, self.command_queue, self.log_writer)
        
        # Create a mock UI factory
        self.ui_factory = MagicMock()
        self.ui_factory.node_tree_view = MagicMock()
        self.ui_factory.session_view = MagicMock()
        self.ui_factory.vnc_tab = MagicMock()
        
        # Create the presenter
        self.presenter = CommanderPresenter(
            ui_factory=self.ui_factory,
            node_manager=self.node_manager,
            log_writer=self.log_writer,
            status_service=self.status_service,
            session_manager=None,  # Mock session manager
            command_queue=self.command_queue,
            fbc_service=self.fbc_service,
            rpc_service=self.rpc_service,
            context_menu_service=self.context_menu_service,
            bstool_service=self.bstool_service
        )
        
        # Set the presenter in the context menu service
        self.context_menu_service.set_presenter(self.presenter)
        
        # Mock status bar update
        self.status_messages = []
        def status_handler(msg, duration):
            self.status_messages.append((msg, duration))
        self.presenter.status_message_signal.connect(status_handler)

    def teardown_method(self):
        """Clean up test environment."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_bstool_context_menu_action_integration(self, qtbot):
        """Test the end-to-end flow of the BsTool context menu action."""
        # Create a mock menu
        menu = QMenu()
        
        # Create item data for a .log file
        item_data = {
            "log_path": self.log_file_path
        }
        
        # Mock the position
        position = QPoint(100, 100)
        
        # Track if the action was triggered
        action_triggered = False
        def mock_handle_bstool_action(log_path):
            nonlocal action_triggered
            action_triggered = True
            assert log_path == self.log_file_path
        
        # Patch the _handle_bstool_action method
        with patch.object(self.context_menu_service, '_handle_bstool_action', side_effect=mock_handle_bstool_action):
            # Show the context menu
            self.context_menu_service.show_context_menu(menu, item_data, position)
            
            # Find the "Run BsTool on this file" action
            bstool_action = None
            for action in menu.actions():
                if action.text() == "Run BsTool on this file":
                    bstool_action = action
                    break
            
            assert bstool_action is not None, "BsTool action not found in context menu"
            
            # Trigger the action
            bstool_action.trigger()
            
            # Process Qt events
            qtbot.wait(100)
            
            # Verify the action was triggered
            assert action_triggered, "BsTool action was not triggered"

    def test_bstool_context_menu_action_with_mocked_process(self, qtbot):
        """Test the end-to-end flow with mocked bstool process."""
        # Mock the subprocess.Popen to simulate bstool execution
        with patch('commander.services.bstool_command_service.subprocess.Popen') as mock_popen:
            # Mock the process
            mock_process = MagicMock()
            mock_process.pid = 12345
            mock_process.poll.return_value = None  # Process is running
            mock_process.stdout.readline.side_effect = ["Output line 1\n", "Output line 2\n", ""]
            mock_process.stderr.read.return_value = ""
            mock_process.wait.return_value = 0
            mock_popen.return_value = mock_process
            
            # Mock _get_bstool_path to return a valid path
            with patch.object(self.bstool_service, '_get_bstool_path', return_value='/path/to/BsTool.exe'):
                with patch('commander.services.bstool_command_service.os.path.exists', return_value=True):
                    # Track signals
                    output_messages = []
                    def output_handler(output):
                        output_messages.append(output)
                    
                    # Connect to bstool output signal
                    self.bstool_service.bstool_output_signal.connect(output_handler)
                    
                    # Execute bstool through the presenter
                    self.presenter.process_bstool_command(self.log_file_path)
                    
                    # Process Qt events to allow signals to be emitted
                    qtbot.wait(100)
                    
                    # Verify output was received
                    assert "Output line 1" in output_messages
                    assert "Output line 2" in output_messages
                    
                    # Verify status message was emitted
                    assert len(self.status_messages) >= 1
                    assert any("Started BsTool processing" in msg for msg, _ in self.status_messages)
                    
                    # Verify output was written to the log file
                    with open(self.log_file_path, 'r') as f:
                        content = f.read()
                        assert "Output line 1" in content
                        assert "Output line 2" in content

    def test_bstool_status_bar_updates(self, qtbot):
        """Test that status bar updates are correctly emitted during BsTool execution."""
        # Mock the subprocess.Popen to simulate bstool execution
        with patch('commander.services.bstool_command_service.subprocess.Popen') as mock_popen:
            # Mock the process
            mock_process = MagicMock()
            mock_process.pid = 12345
            mock_process.poll.return_value = None  # Process is running
            mock_process.stdout.readline.side_effect = ["Output line 1\n", "Output line 2\n", ""]
            mock_process.stderr.read.return_value = ""
            mock_process.wait.return_value = 0
            mock_popen.return_value = mock_process
            
            # Mock _get_bstool_path to return a valid path
            with patch.object(self.bstool_service, '_get_bstool_path', return_value='/path/to/BsTool.exe'):
                with patch('commander.services.bstool_command_service.os.path.exists', return_value=True):
                    # Clear previous status messages
                    self.status_messages.clear()
                    
                    # Execute bstool through the presenter
                    self.presenter.process_bstool_command(self.log_file_path)
                    
                    # Process Qt events to allow signals to be emitted
                    qtbot.wait(100)
                    
                    # Verify status messages
                    assert len(self.status_messages) >= 1
                    # Check for initial status message
                    assert any("Started BsTool processing" in msg for msg, _ in self.status_messages)
                    # Check for completion status message (from BsToolCommandService)
                    assert any("bstool execution completed successfully" in msg for msg, _ in self.status_messages)


if __name__ == "__main__":
    pytest.main([__file__])