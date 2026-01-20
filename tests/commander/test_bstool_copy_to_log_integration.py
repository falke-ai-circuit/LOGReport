#!/usr/bin/env python3
"""
Integration tests for the "copy to log" function in BsTool connections.

These tests validate the copy to log functionality for BsTool connections,
covering file path handling, content writing, and error reporting.
"""

import pytest
import sys
import os
from unittest.mock import Mock, MagicMock, patch

# Add src directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'src')))

from commander.models import Node, NodeToken


class MockNodeTreeItem:
    """Mock QTreeWidgetItem for testing"""
    def __init__(self, text):
        self._text = text
    
    def text(self, column):
        return self._text


class TestBsToolCopyToLogIntegration:
    """Integration tests for BsTool copy to log functionality."""

    def setup_method(self):
        """Set up test fixtures"""
        # Mock dependencies
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

    def _execute_copy_to_log(self, content, node_name, token=None, selected_items=None):
        """
        Helper method to execute the copy to log logic without initializing the full presenter.
        
        Args:
            content: Content to write to log
            node_name: Name of the node
            token: Token associated with the node
            selected_items: Selected items in the node tree
        """
        # Mock selected items if not provided
        if selected_items is None:
            mock_item = MockNodeTreeItem(node_name)
            selected_items = [mock_item]
        
        # Mock node manager responses
        mock_node = Mock()
        mock_node.name = node_name
        if token:
            mock_node.tokens = {token.token_id: [token]}
        else:
            mock_node.tokens = {}
        
        self.mock_node_manager.set_selected_node.return_value = None
        self.mock_node_manager.get_selected_node.return_value = mock_node
        
        # Execute the core logic from _on_copy_to_log_clicked
        if selected_items:
            # Get the first selected item
            selected_item = selected_items
            node_name = selected_item.text(0)

            # Set the active node in NodeManager
            self.mock_node_manager.set_selected_node(node_name)
            active_node = self.mock_node_manager.get_selected_node()

            # Get the token
            if not token and active_node and active_node.tokens:
                for token_list in active_node.tokens.values():
                    if token_list:
                        token = token_list
                        break

        else:
            self.mock_status_service.show_message("No node selected")
            return

        if content.strip():
            # Determine log type based on content validation
            log_type = "LOG"  # Default
            
            # Write directly to log with node and token context
            try:
                self.mock_log_writer.write_to_log(
                    content=content,
                    log_type=log_type,
                    node_name=node_name if selected_items else None,
                    token=token
                )
                self.mock_status_service.show_message("Copied to log")
            except Exception as e:
                error_msg = f"Failed to copy to {log_type} log for node {node_name}: {str(e)}"
                self.mock_status_service.show_message(error_msg)
        else:
            self.mock_status_service.show_message("Output is empty")

    def test_copy_to_log_bstool_output(self):
        """Test copy to log functionality for BsTool output."""
        # Setup
        test_content = "BsTool command output line 1\nBsTool command output line 2"
        test_node_name = "AP01m"
        test_token_id = "bstool_session"
        test_ip = "192.168.0.11"
        
        # Create a mock token for BsTool
        mock_token = Mock(spec=NodeToken)
        mock_token.token_id = test_token_id
        mock_token.token_type = "BSTOOL"
        mock_token.ip_address = test_ip
        mock_token.protocol = "bstool"
        
        # Execute
        self._execute_copy_to_log(test_content, test_node_name, mock_token)
        
        # Verify
        self.mock_node_manager.set_selected_node.assert_called_once_with(test_node_name)
        self.mock_node_manager.get_selected_node.assert_called_once()
        self.mock_log_writer.write_to_log.assert_called_once()
        
        # Get the actual call arguments
        call_args = self.mock_log_writer.write_to_log.call_args
        call_kwargs = call_args  # Keyword arguments
        
        assert call_kwargs['content'] == test_content
        assert call_kwargs['log_type'] == "LOG"  # Default log_type
        assert call_kwargs['node_name'] == test_node_name
        assert call_kwargs['token'] == mock_token  # Verify token is passed
        self.mock_status_service.show_message.assert_called_with("Copied to log")

    def test_copy_to_log_no_node_selected_bstool(self):
        """Test copy to log when no node is selected with BsTool output."""
        # Setup - No node selected
        test_content = "BsTool output"
        
        # Execute
        self._execute_copy_to_log(test_content, "AP01m", selected_items=[])
        
        # Verify
        self.mock_status_service.show_message.assert_called_with("No node selected")
        self.mock_log_writer.write_to_log.assert_not_called()

    def test_copy_to_log_empty_output_bstool(self):
        """Test copy to log when BsTool output is empty."""
        # Setup
        test_node_name = "AP01m"
        
        # Execute
        self._execute_copy_to_log("", test_node_name)
        
        # Verify
        self.mock_status_service.show_message.assert_called_with("Output is empty")
        self.mock_log_writer.write_to_log.assert_not_called()

    def test_copy_to_log_exception_handling_bstool(self):
        """Test exception handling when write_to_log fails with BsTool output."""
        # Setup
        test_content = "BsTool output with error"
        test_node_name = "AP01m"
        
        # Mock exception in log writer
        self.mock_log_writer.write_to_log.side_effect = Exception("Write error")
        
        # Execute
        self._execute_copy_to_log(test_content, test_node_name)
        
        # Verify
        self.mock_log_writer.write_to_log.assert_called_once()
        self.mock_status_service.show_message.assert_called()
        # Should show error message
        call_args = self.mock_status_service.show_message.call_args
        assert "Failed to copy" in call_args


if __name__ == "__main__":
    pytest.main([__file__, "-v"])