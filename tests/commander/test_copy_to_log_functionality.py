#!/usr/bin/env python3
"""
Test for the modified _on_copy_to_log_clicked method in session_presenter.py
Tests the functionality to set active node and pass token to log_writer
"""

import pytest
from unittest.mock import Mock, MagicMock
import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from commander.presenters.session_presenter import SessionPresenter


class MockNodeTreeItem:
    """Mock QTreeWidgetItem for testing"""
    def __init__(self, text):
        self._text = text
    
    def text(self, column):
        return self._text


class TestCopyToLogFunctionality:
    
    def setup_method(self):
        """Set up test fixtures"""
        # Mock dependencies
        self.mock_clipboard_monitor = Mock()
        self.mock_status_service = Mock()
        self.mock_node_manager = Mock()
        self.mock_log_writer = Mock()
        
        # Mock UI factory and views
        self.mock_ui_factory = Mock()
        self.mock_node_tree_view = Mock()
        self.mock_ui_factory.node_tree_view = self.mock_node_tree_view
        
        # Mock commander presenter
        self.mock_commander_presenter = Mock()
        self.mock_commander_presenter.ui_factory = self.mock_ui_factory
        
        # Create presenter instance
        self.presenter = SessionPresenter(
            commander_presenter=self.mock_commander_presenter,
            clipboard_monitor=self.mock_clipboard_monitor,
            status_service=self.mock_status_service,
            node_manager=self.mock_node_manager,
            log_writer=self.mock_log_writer
        )
    
    def test_copy_to_log_with_selected_node(self):
        """Test copy to log with a selected node and valid token"""
        # Setup
        mock_node = Mock()
        mock_token = Mock()
        mock_token.token_id = "test_token_1"
        mock_token.token_type = "RPC"
        mock_token.log_path = "/test/path/test.fbc"
        mock_node.tokens = {"RPC": [mock_token]}
        
        # Mock selected items
        mock_item = MockNodeTreeItem("AP01m")
        self.mock_node_tree_view.selectedItems.return_value = [mock_item]
        
        # Mock node manager responses
        self.mock_node_manager.set_selected_node.return_value = None
        self.mock_node_manager.get_selected_node.return_value = mock_node
        
        # Execute
        self.presenter._on_copy_to_log_clicked()
        
        # Verify
        self.mock_node_manager.set_selected_node.assert_called_once_with("AP01m")
        self.mock_node_manager.get_selected_node.assert_called_once()
        self.mock_log_writer.write_to_log.assert_called_once()
        
        # Get the actual call arguments
        call_args = self.mock_log_writer.write_to_log.call_args
        assert call_args is not None
        # Check that token parameter was passed
        assert 'token' in str(call_args)
        self.mock_status_service.show_message.assert_called()
    
    def test_copy_to_log_no_node_selected(self):
        """Test copy to log when no node is selected"""
        # Setup
        self.mock_node_tree_view.selectedItems.return_value = []
        
        # Execute
        self.presenter._on_copy_to_log_clicked()
        
        # Verify
        self.mock_status_service.show_message.assert_called_with("No node selected")
        self.mock_log_writer.write_to_log.assert_not_called()
    
    def test_copy_to_log_no_tokens(self):
        """Test copy to log when node has no tokens"""
        # Setup
        mock_node = Mock()
        mock_node.tokens = {}
        
        mock_item = MockNodeTreeItem("AP01m")
        self.mock_node_tree_view.selectedItems.return_value = [mock_item]
        
        self.mock_node_manager.set_selected_node.return_value = None
        self.mock_node_manager.get_selected_node.return_value = mock_node
        
        # Execute
        self.presenter._on_copy_to_log_clicked()
        
        # Verify
        self.mock_log_writer.write_to_log.assert_called_once()
        call_args = self.mock_log_writer.write_to_log.call_args
        assert call_args is not None
        # Check that token=None was passed
        call_kwargs = call_args.kwargs
        assert 'token' in call_kwargs
    
    def test_copy_to_log_exception_handling(self):
        """Test exception handling when write_to_log fails"""
        # Setup
        mock_node = Mock()
        mock_node.tokens = {}
        
        mock_item = MockNodeTreeItem("AP01m")
        self.mock_node_tree_view.selectedItems.return_value = [mock_item]
        
        self.mock_node_manager.set_selected_node.return_value = None
        self.mock_node_manager.get_selected_node.return_value = mock_node
        
        # Mock exception
        self.mock_log_writer.write_to_log.side_effect = Exception("Write error")
        
        # Execute
        self.presenter._on_copy_to_log_clicked()
        
        # Verify
        self.mock_status_service.show_message.assert_called()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])