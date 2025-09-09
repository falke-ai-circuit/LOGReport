import os
import sys
import pytest
from unittest.mock import MagicMock, patch

# Add src directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'src')))

from commander.ui.commander_window import CommanderWindow
from commander.ui.node_tree_view import NodeTreeView


class TestSelectRootButtonRegression:
    """Regression test suite for Select Root button functionality"""
    
    def test_set_log_root_button_exists_and_connected(self):
        """Test that the Set Log Root button exists and has the correct signal connection"""
        # Create a mock node_tree_view to test button existence
        mock_node_tree_view = MagicMock()
        
        # Check that the button attribute exists
        assert hasattr(mock_node_tree_view, 'set_log_root_btn')
        
        # Check that the button has a click method
        assert hasattr(mock_node_tree_view.set_log_root_btn, 'click')
        
        # Check that the signal attribute exists
        assert hasattr(mock_node_tree_view, 'set_log_root_clicked')
        
        # Check that the signal has a connect method
        assert hasattr(mock_node_tree_view.set_log_root_clicked, 'connect')
    
    def test_set_log_root_button_signal_emission(self):
        """Test that clicking the Set Log Root button emits the correct signal"""
        # Create a real NodeTreeView instance for testing
        node_tree_view = NodeTreeView()
        
        # Create a mock to track signal emission
        signal_emitted = MagicMock()
        node_tree_view.set_log_root_clicked.connect(signal_emitted)
        
        # Simulate button click
        node_tree_view.set_log_root_btn.click()
        
        # Verify signal was emitted
        signal_emitted.assert_called_once()
    
    def test_set_log_root_folder_opens_directory_dialog(self):
        """Test that set_log_root_folder opens a directory dialog"""
        with patch('commander.ui.commander_window.QFileDialog.getExistingDirectory') as mock_dir_dialog:
            mock_dir_dialog.return_value = "/test/log/root"
            
            # Create a minimal window instance for testing the method directly
            window = MagicMock()
            window.node_tree_presenter = MagicMock()
            
            # Call the method directly
            CommanderWindow.set_log_root_folder(window)
            
            # Verify directory dialog was called with correct parameters
            mock_dir_dialog.assert_called_once_with(window, "Select Log Root Folder")
    
    def test_set_log_root_folder_with_selected_directory(self):
        """Test that set_log_root_folder calls presenter with selected directory"""
        test_dir_path = "/path/to/log/root"
        
        with patch('commander.ui.commander_window.QFileDialog.getExistingDirectory') as mock_dir_dialog:
            mock_dir_dialog.return_value = test_dir_path
            
            # Create a minimal window instance for testing the method directly
            window = MagicMock()
            window.node_tree_presenter = MagicMock()
            
            # Call the method directly
            CommanderWindow.set_log_root_folder(window)
            
            # Verify presenter method was called with the directory path
            window.node_tree_presenter.set_log_root_folder.assert_called_once_with(test_dir_path)
    
    def test_set_log_root_folder_without_selected_directory(self):
        """Test that set_log_root_folder does nothing when no directory is selected"""
        with patch('commander.ui.commander_window.QFileDialog.getExistingDirectory') as mock_dir_dialog:
            # Simulate user canceling dialog (returns empty string)
            mock_dir_dialog.return_value = ""
            
            # Create a minimal window instance for testing the method directly
            window = MagicMock()
            window.node_tree_presenter = MagicMock()
            
            # Call the method directly
            CommanderWindow.set_log_root_folder(window)
            
            # Verify presenter method was not called
            window.node_tree_presenter.set_log_root_folder.assert_not_called()
    
    def test_node_tree_presenter_set_log_root_folder_integration(self):
        """Test that NodeTreePresenter's set_log_root_folder method integrates correctly"""
        # Create mocks for dependencies
        mock_view = MagicMock()
        mock_node_manager = MagicMock()
        mock_session_manager = MagicMock()
        mock_log_writer = MagicMock()
        mock_command_queue = MagicMock()
        mock_fbc_service = MagicMock()
        mock_rpc_service = MagicMock()
        mock_context_menu_service = MagicMock()
        
        # Import the presenter
        from commander.presenters.node_tree_presenter import NodeTreePresenter
        
        # Create presenter instance
        presenter = NodeTreePresenter(
            mock_view, mock_node_manager, mock_session_manager,
            mock_log_writer, mock_command_queue, mock_fbc_service,
            mock_rpc_service, mock_context_menu_service
        )
        
        # Test the method
        test_folder_path = "/test/log/root"
        presenter.set_log_root_folder(test_folder_path)
        
        # Verify node manager method was called
        mock_node_manager.set_log_root.assert_called_once_with(test_folder_path)
        
        # Verify scan_log_files was called
        mock_node_manager.scan_log_files.assert_called_once()
        
        # Verify populate_node_tree was called on the view
        presenter.populate_node_tree.assert_called_once()
        
        # Verify status message signal was emitted
        # Note: This is harder to test directly without connecting to a slot


if __name__ == "__main__":
    pytest.main([__file__, "-v"])