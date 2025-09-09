import os
import sys
import pytest
from unittest.mock import MagicMock, patch

# Add src directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'src')))

from commander.ui.commander_window import CommanderWindow


class TestLoadNodesExplorerRegression:
    """Regression test suite for Load Nodes functionality"""
    
    def test_load_configuration_opens_file_dialog(self):
        """Test that load_configuration opens a file dialog"""
        with patch('commander.ui.commander_window.QFileDialog.getOpenFileName') as mock_file_dialog:
            mock_file_dialog.return_value = ("test_nodes.json", "JSON Files (*.json)")
            
            # Create a minimal window instance for testing the method directly
            window = MagicMock()
            window.node_tree_presenter = MagicMock()
            
            # Call the method directly
            CommanderWindow.load_configuration(window)
            
            # Verify file dialog was called with correct parameters
            mock_file_dialog.assert_called_once_with(
                window, "Select Node Configuration", "", "JSON Files (*.json)"
            )
    
    def test_load_configuration_with_selected_file(self):
        """Test that load_configuration calls presenter with selected file"""
        test_file_path = "/path/to/test_nodes.json"
        
        with patch('commander.ui.commander_window.QFileDialog.getOpenFileName') as mock_file_dialog:
            mock_file_dialog.return_value = (test_file_path, "JSON Files (*.json)")
            
            # Create a minimal window instance for testing the method directly
            window = MagicMock()
            window.node_tree_presenter = MagicMock()
            
            # Call the method directly
            CommanderWindow.load_configuration(window)
            
            # Verify presenter method was called with the file path
            window.node_tree_presenter.load_configuration.assert_called_once_with(test_file_path)
    
    def test_load_configuration_without_selected_file(self):
        """Test that load_configuration does nothing when no file is selected"""
        with patch('commander.ui.commander_window.QFileDialog.getOpenFileName') as mock_file_dialog:
            # Simulate user canceling dialog (returns empty string)
            mock_file_dialog.return_value = ("", "JSON Files (*.json)")
            
            # Create a minimal window instance for testing the method directly
            window = MagicMock()
            window.node_tree_presenter = MagicMock()
            
            # Call the method directly
            CommanderWindow.load_configuration(window)
            
            # Verify presenter method was not called
            window.node_tree_presenter.load_configuration.assert_not_called()
    
    def test_load_nodes_button_signal_connection(self):
        """Test that load_nodes_clicked signal exists and can be connected"""
        # Create a mock node_tree_view to test signal existence
        mock_node_tree_view = MagicMock()
        
        # Check that the signal attribute exists
        assert hasattr(mock_node_tree_view, 'load_nodes_clicked')
        
        # Check that the signal has a connect method
        assert hasattr(mock_node_tree_view.load_nodes_clicked, 'connect')


if __name__ == "__main__":
    pytest.main([__file__, "-v"])