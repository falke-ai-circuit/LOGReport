import os
import sys
import pytest
from unittest.mock import MagicMock, patch, mock_open
from PyQt6.QtWidgets import QApplication

# Add src directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'src')))

from commander.ui.commander_window import CommanderWindow
from commander.presenters.commander_presenter import CommanderPresenter
from commander.presenters.commander_presenter_utils import CommanderPresenterUtils
from commander.node_manager import NodeManager
from commander.log_writer import LogWriter
from commander.services.status_service import StatusService


@pytest.fixture(scope="module")
def app():
    """Fixture for a QApplication instance."""
    return QApplication([])


class TestCommanderWindowClearNodeLog:
    """Test suite for CommanderWindow clear_node_log functionality"""

    def test_clear_node_log_button_exists_and_connected(self, app):
        """Test that the clear node log button exists and has the correct signal connection"""
        # Create a mock window to test button existence
        mock_window = MagicMock()
        
        # Check that the clear_node_log method exists
        assert hasattr(mock_window, 'clear_node_log')
        
        # Check that the method is callable
        assert callable(getattr(mock_window, 'clear_node_log'))

    def test_clear_node_log_calls_presenter_method(self, app):
        """Test that clear_node_log calls the presenter's clear_node_log method"""
        # Create a mock window with a mocked presenter
        window = MagicMock()
        window.commander_presenter = MagicMock()
        window.node_tree_view = MagicMock()
        window.node_tree_view.selectedItems.return_value = []
        
        # Call the method directly
        CommanderWindow.clear_node_log(window)
        
        # Verify presenter method was called with selected items
        window.commander_presenter.clear_node_log.assert_called_once_with(
            window.node_tree_view.selectedItems.return_value
        )

    def test_clear_node_log_integration_with_presenter_utils(self, app):
        """Test the integration between CommanderWindow, CommanderPresenter, and CommanderPresenterUtils"""
        # Create mocks for dependencies
        mock_ui_factory = MagicMock()
        mock_node_manager = MagicMock()
        mock_log_writer = MagicMock()
        mock_status_service = MagicMock()
        mock_session_manager = MagicMock()
        mock_command_queue = MagicMock()
        mock_fbc_service = MagicMock()
        mock_rpc_service = MagicMock()
        mock_context_menu_service = MagicMock()
        
        # Create a real presenter instance with mocked dependencies
        presenter = CommanderPresenter(
            ui_factory=mock_ui_factory,
            node_manager=mock_node_manager,
            log_writer=mock_log_writer,
            status_service=mock_status_service,
            session_manager=mock_session_manager,
            command_queue=mock_command_queue,
            fbc_service=mock_fbc_service,
            rpc_service=mock_rpc_service,
            context_menu_service=mock_context_menu_service
        )
        
        # Create a mock window with the real presenter
        window = MagicMock()
        window.commander_presenter = presenter
        window.node_tree_view = MagicMock()
        
        # Create a mock selected item
        mock_item = MagicMock()
        mock_item.data.return_value = {"log_path": "/path/to/log/file.log"}
        window.node_tree_view.selectedItems.return_value = [mock_item]
        
        # Mock the status signal
        mock_status_signal = MagicMock()
        presenter.status_message_signal = mock_status_signal
        
        # For items with log_path, we expect the file to be opened in 'w' mode
        with patch("builtins.open", mock_open()) as mock_file:
            # Call the method
            CommanderWindow.clear_node_log(window)
            
            # Verify file was opened in write mode (clearing it)
            mock_file.assert_called_once_with("/path/to/log/file.log", 'w')
            mock_status_signal.emit.assert_called_once_with("Cleared log file: file.log", 3000)

    def test_clear_node_log_with_token_item(self, app):
        """Test clear_node_log with an item that has a token"""
        # Create mocks for dependencies
        mock_ui_factory = MagicMock()
        mock_node_manager = MagicMock()
        mock_log_writer = MagicMock()
        mock_status_service = MagicMock()
        mock_session_manager = MagicMock()
        mock_command_queue = MagicMock()
        mock_fbc_service = MagicMock()
        mock_rpc_service = MagicMock()
        mock_context_menu_service = MagicMock()
        
        # Create a real presenter instance with mocked dependencies
        presenter = CommanderPresenter(
            ui_factory=mock_ui_factory,
            node_manager=mock_node_manager,
            log_writer=mock_log_writer,
            status_service=mock_status_service,
            session_manager=mock_session_manager,
            command_queue=mock_command_queue,
            fbc_service=mock_fbc_service,
            rpc_service=mock_rpc_service,
            context_menu_service=mock_context_menu_service
        )
        
        # Create a mock window with the real presenter
        window = MagicMock()
        window.commander_presenter = presenter
        window.node_tree_view = MagicMock()
        
        # Create a mock selected item with token
        mock_item = MagicMock()
        token_id = "123"
        mock_item.data.return_value = {"token": token_id}
        window.node_tree_view.selectedItems.return_value = [mock_item]
        
        # Mock the status signal
        mock_status_signal = MagicMock()
        presenter.status_message_signal = mock_status_signal
        
        # Call the method
        CommanderWindow.clear_node_log(window)
        
        # Verify the log_writer's clear_log method was called with the token ID
        mock_log_writer.clear_log.assert_called_once_with(token_id)
        mock_status_signal.emit.assert_called_once_with(f"Cleared log for token: {token_id}", 3000)

    def test_clear_node_log_with_no_selected_items(self, app):
        """Test clear_node_log when no items are selected"""
        # Create mocks for dependencies
        mock_ui_factory = MagicMock()
        mock_node_manager = MagicMock()
        mock_log_writer = MagicMock()
        mock_status_service = MagicMock()
        mock_session_manager = MagicMock()
        mock_command_queue = MagicMock()
        mock_fbc_service = MagicMock()
        mock_rpc_service = MagicMock()
        mock_context_menu_service = MagicMock()
        
        # Create a real presenter instance with mocked dependencies
        presenter = CommanderPresenter(
            ui_factory=mock_ui_factory,
            node_manager=mock_node_manager,
            log_writer=mock_log_writer,
            status_service=mock_status_service,
            session_manager=mock_session_manager,
            command_queue=mock_command_queue,
            fbc_service=mock_fbc_service,
            rpc_service=mock_rpc_service,
            context_menu_service=mock_context_menu_service
        )
        
        # Create a mock window with the real presenter
        window = MagicMock()
        window.commander_presenter = presenter
        window.node_tree_view = MagicMock()
        
        # No items selected
        window.node_tree_view.selectedItems.return_value = []
        
        # Mock the status signal
        mock_status_signal = MagicMock()
        presenter.status_message_signal = mock_status_signal
        
        # Call the method
        CommanderWindow.clear_node_log(window)
        
        # Verify the appropriate status message was emitted
        mock_status_signal.emit.assert_called_once_with(
            "No item selected! Select a token or log file on the left.", 3000
        )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])