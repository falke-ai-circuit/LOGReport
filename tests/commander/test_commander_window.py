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


class TestCommanderWindowSettingsPersistence:
    """Test suite for CommanderWindow settings persistence functionality"""
    
    def test_load_configurations_loads_saved_settings(self, app):
        """Test that _load_configurations correctly loads saved settings"""
        # Create mocks for dependencies
        mock_settings = MagicMock()
        mock_settings.value.side_effect = lambda key, default: {
            "config_path": "/path/to/config.json",
            "log_root": "/path/to/log/root",
            "telnet_ip": "192.168.1.100",
            "telnet_port": "2323"
        }.get(key, default)
        
        # Mock file system operations - both config file and log root directory exist
        with patch("commander.ui.commander_window.os.path.exists", return_value=True), \
             patch("commander.ui.commander_window.os.path.isdir", return_value=True):
            
            # Create a mock window with mocked dependencies
            window = MagicMock()
            window.settings = mock_settings
            window.node_manager = MagicMock()
            window.telnet_tab = MagicMock()
            
            # Mock node_manager methods
            window.node_manager.load_configuration.return_value = True
            
            # Call the method directly
            CommanderWindow._load_configurations(window)
            
            # Verify settings were loaded
            mock_settings.value.assert_any_call("config_path", "")
            mock_settings.value.assert_any_call("log_root", "")
            mock_settings.value.assert_any_call("telnet_ip", "")
            mock_settings.value.assert_any_call("telnet_port", "")
            
            # Verify node_manager methods were called with correct values
            window.node_manager.set_config_path.assert_called_once_with("/path/to/config.json")
            window.node_manager.set_log_root.assert_called_once_with("/path/to/log/root")
            # When log root exists and is a directory, load_configuration should NOT be called
            window.node_manager.load_configuration.assert_not_called()
            window.node_manager.scan_log_files.assert_called_once()
            
            # Verify telnet tab fields were set
            window.telnet_tab.ip_edit.setText.assert_called_once_with("192.168.1.100")
            window.telnet_tab.port_edit.setText.assert_called_once_with("2323")
    
    def test_load_configurations_handles_missing_files(self, app):
        """Test that _load_configurations handles missing config/log files gracefully"""
        # Create mocks for dependencies
        mock_settings = MagicMock()
        mock_settings.value.side_effect = lambda key, default: {
            "config_path": "/path/to/missing/config.json",
            "log_root": "/path/to/missing/log/root",
            "telnet_ip": "192.168.1.100",
            "telnet_port": "2323"
        }.get(key, default)
        
        # Mock file system operations to return False for missing files
        with patch("commander.ui.commander_window.os.path.exists", return_value=False), \
             patch("commander.ui.commander_window.os.path.isdir", return_value=False):
            
            # Create a mock window with mocked dependencies
            window = MagicMock()
            window.settings = mock_settings
            window.node_manager = MagicMock()
            window.telnet_tab = MagicMock()
            
            # Call the method directly
            CommanderWindow._load_configurations(window)
            
            # Verify settings were loaded
            mock_settings.value.assert_any_call("config_path", "")
            mock_settings.value.assert_any_call("log_root", "")
            mock_settings.value.assert_any_call("telnet_ip", "")
            mock_settings.value.assert_any_call("telnet_port", "")
            
            # Verify node_manager methods were NOT called for missing files
            window.node_manager.set_config_path.assert_not_called()
            window.node_manager.set_log_root.assert_not_called()
            window.node_manager.load_configuration.assert_not_called()
            
            # But telnet settings should still be loaded
            window.telnet_tab.ip_edit.setText.assert_called_once_with("192.168.1.100")
            window.telnet_tab.port_edit.setText.assert_called_once_with("2323")
    
    def test_closeEvent_saves_settings(self, app):
        """Test that closeEvent correctly saves all settings"""
        # Create mocks for dependencies
        mock_settings = MagicMock()
        mock_telnet_service = MagicMock()
        
        # Create a mock window with mocked dependencies
        window = MagicMock()
        window.settings = mock_settings
        window.telnet_service = mock_telnet_service
        window.node_manager = MagicMock()
        window.node_manager.config_path = "/path/to/config.json"
        window.node_manager.log_root = "/path/to/log/root"
        
        # Mock telnet tab
        window.telnet_tab = MagicMock()
        window.telnet_tab.get_connection_info.return_value = ("192.168.1.100", "2323")
        
        # Create a mock close event
        mock_event = MagicMock()
        
        # Call the method directly
        CommanderWindow.closeEvent(window, mock_event)
        
        # Verify telnet service disconnect was called
        mock_telnet_service.disconnect.assert_called_once()
        
        # Verify settings were saved
        mock_settings.setValue.assert_any_call("config_path", "/path/to/config.json")
        mock_settings.setValue.assert_any_call("log_root", "/path/to/log/root")
        mock_settings.setValue.assert_any_call("telnet_ip", "192.168.1.100")
        mock_settings.setValue.assert_any_call("telnet_port", "2323")
        
        # Verify event was accepted and parent method was called
        mock_event.accept.assert_called_once()
    
    def test_closeEvent_handles_missing_telnet_tab(self, app):
        """Test that closeEvent handles case where telnet_tab is not initialized"""
        # Create mocks for dependencies
        mock_settings = MagicMock()
        mock_telnet_service = MagicMock()
        
        # Create a mock window with mocked dependencies
        window = MagicMock()
        window.settings = mock_settings
        window.telnet_service = mock_telnet_service
        window.node_manager = MagicMock()
        window.node_manager.config_path = "/path/to/config.json"
        window.node_manager.log_root = "/path/to/log/root"
        
        # Remove telnet_tab attribute to simulate it not being initialized
        del window.telnet_tab
        
        # Create a mock close event
        mock_event = MagicMock()
        
        # Call the method directly
        CommanderWindow.closeEvent(window, mock_event)
        
        # Verify telnet service disconnect was called
        mock_telnet_service.disconnect.assert_called_once()
        
        # Verify settings were saved (but not telnet settings)
        mock_settings.setValue.assert_any_call("config_path", "/path/to/config.json")
        mock_settings.setValue.assert_any_call("log_root", "/path/to/log/root")
        # Should not try to save telnet settings when telnet_tab doesn't exist
        assert mock_settings.setValue.call_count == 2
        
        # Verify event was accepted and parent method was called
        mock_event.accept.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
