
import os
import sys
import pytest
from unittest.mock import MagicMock, patch, mock_open
from typing import Dict, List

# Add src directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'src')))

from commander.log_writer import LogWriter
from commander.node_manager import NodeManager
from commander.models import Node, NodeToken
from commander.presenters.commander_presenter_utils import CommanderPresenterUtils


class TestLogWriterClearLog:
    """Test suite for LogWriter.clear_log method"""
    
    @pytest.fixture
    def mock_node_manager(self):
        """Create a mock NodeManager"""
        mock_nm = MagicMock()
        return mock_nm
    
    @pytest.fixture
    def log_writer(self, mock_node_manager):
        """Create a LogWriter instance with mocked dependencies"""
        return LogWriter(mock_node_manager)
    
    def test_clear_log_with_valid_token_and_log_path(self, log_writer, mock_node_manager):
        """Test clearing log for a token with valid log_path"""
        # Setup
        token_id = "123"
        log_path = "/path/to/log/file.log"
        
        # Create mock nodes with tokens
        mock_token = MagicMock()
        mock_token.log_path = log_path
        
        mock_node = MagicMock()
        mock_node.tokens = {token_id: [mock_token]}
        
        mock_node_manager.get_all_nodes.return_value = [mock_node]
        
        # Mock file operations
        with patch("builtins.open", mock_open()) as mock_file:
            with patch.object(log_writer, 'write_to_app_log') as mock_write_to_app_log:
                # Execute
                log_writer.clear_log(token_id)
                
                # Verify
                mock_file.assert_called_once_with(log_path, 'w', encoding='utf-8')
                mock_write_to_app_log.assert_called_once_with(f"Successfully cleared log file: {log_path}")
    
    def test_clear_log_with_valid_token_no_log_path(self, log_writer, mock_node_manager):
        """Test clearing log for a token with no log_path"""
        # Setup
        token_id = "123"
        
        # Create mock nodes with tokens
        mock_token = MagicMock()
        mock_token.log_path = ""  # Empty log_path
        
        mock_node = MagicMock()
        mock_node.tokens = {token_id: [mock_token]}
        
        mock_node_manager.get_all_nodes.return_value = [mock_node]
        
        # Execute
        with patch.object(log_writer, 'write_to_app_log') as mock_write_to_app_log:
            log_writer.clear_log(token_id)
            
            # Verify
            mock_write_to_app_log.assert_called_once_with(f"Token {token_id} has no log_path attribute or it's empty")
    
    def test_clear_log_with_valid_token_none_log_path(self, log_writer, mock_node_manager):
        """Test clearing log for a token with None log_path"""
        # Setup
        token_id = "123"
        
        # Create mock nodes with tokens
        mock_token = MagicMock()
        mock_token.log_path = None  # None log_path
        
        mock_node = MagicMock()
        mock_node.tokens = {token_id: [mock_token]}
        
        mock_node_manager.get_all_nodes.return_value = [mock_node]
        
        # Execute
        with patch.object(log_writer, 'write_to_app_log') as mock_write_to_app_log:
            log_writer.clear_log(token_id)
            
            # Verify
            mock_write_to_app_log.assert_called_once_with(f"Token {token_id} has no log_path attribute or it's empty")
    
    def test_clear_log_with_nonexistent_token(self, log_writer, mock_node_manager):
        """Test clearing log for a token that doesn't exist"""
        # Setup
        token_id = "123"
        nonexistent_token_id = "456"
        
        # Create mock nodes with tokens
        mock_token = MagicMock()
        mock_token.log_path = "/path/to/log/file.log"
        
        mock_node = MagicMock()
        mock_node.tokens = {token_id: [mock_token]}  # Only token_id exists, not nonexistent_token_id
        
        mock_node_manager.get_all_nodes.return_value = [mock_node]
        
        # Execute
        with patch.object(log_writer, 'write_to_app_log') as mock_write_to_app_log:
            log_writer.clear_log(nonexistent_token_id)
            
            # Verify - No calls to write_to_app_log for success or failure since no tokens matched
            mock_write_to_app_log.assert_not_called()
    
    def test_clear_log_with_file_write_exception(self, log_writer, mock_node_manager):
        """Test clearing log when file write operation fails"""
        # Setup
        token_id = "123"
        log_path = "/path/to/log/file.log"
        
        # Create mock nodes with tokens
        mock_token = MagicMock()
        mock_token.log_path = log_path
        
        mock_node = MagicMock()
        mock_node.tokens = {token_id: [mock_token]}
        
        mock_node_manager.get_all_nodes.return_value = [mock_node]
        
        # Mock file operations to raise an exception
        with patch("builtins.open", mock_open()) as mock_file:
            mock_file.side_effect = Exception("Permission denied")
            
            with patch.object(log_writer, 'write_to_app_log') as mock_write_to_app_log:
                # Execute
                log_writer.clear_log(token_id)
                
                # Verify
                mock_write_to_app_log.assert_called_once_with(f"Failed to clear log file {log_path}: Permission denied")
    
    def test_clear_log_multiple_tokens_same_id(self, log_writer, mock_node_manager):
        """Test clearing log for multiple tokens with the same ID"""
        # Setup
        token_id = "123"
        log_path1 = "/path/to/log/file1.log"
        log_path2 = "/path/to/log/file2.log"
        
        # Create mock nodes with multiple tokens having the same ID
        mock_token1 = MagicMock()
        mock_token1.log_path = log_path1
        
        mock_token2 = MagicMock()
        mock_token2.log_path = log_path2
        
        mock_node = MagicMock()
        mock_node.tokens = {token_id: [mock_token1, mock_token2]}  # Multiple tokens with same ID
        
        mock_node_manager.get_all_nodes.return_value = [mock_node]
        
        # Mock file operations
        with patch("builtins.open", mock_open()) as mock_file:
            with patch.object(log_writer, 'write_to_app_log') as mock_write_to_app_log:
                # Execute
                log_writer.clear_log(token_id)
                
                # Verify - Should attempt to clear both log files
                assert mock_file.call_count == 2
                mock_write_to_app_log.assert_any_call(f"Successfully cleared log file: {log_path1}")
                mock_write_to_app_log.assert_any_call(f"Successfully cleared log file: {log_path2}")


class TestIntegrationClearNodeLog:
    """Integration tests for clear_node_log functionality"""
    
    @pytest.fixture
    def mock_node_manager(self):
        """Create a mock NodeManager"""
        mock_nm = MagicMock()
        return mock_nm
    
    @pytest.fixture
    def mock_log_writer(self):
        """Create a mock LogWriter"""
        mock_lw = MagicMock()
        return mock_lw
    
    @pytest.fixture
    def commander_presenter_utils(self, mock_node_manager, mock_log_writer):
        """Create a CommanderPresenterUtils instance with mocked dependencies"""
        return CommanderPresenterUtils(mock_node_manager, mock_log_writer)
    
    def test_clear_node_log_with_log_path_item(self, commander_presenter_utils, mock_log_writer):
        """Test clear_node_log with an item that has a log_path"""
        # Setup
        mock_item = MagicMock()
        log_path = "/path/to/log/file.log"
        mock_item.data.return_value = {"log_path": log_path}
        
        mock_status_signal = MagicMock()
        
        # Execute
        with patch("builtins.open", mock_open()) as mock_file:
            commander_presenter_utils.clear_node_log([mock_item], mock_status_signal)
            
            # Verify
            mock_file.assert_called_once_with(log_path, 'w')
            mock_status_signal.emit.assert_called_once_with(f"Cleared log file: {os.path.basename(log_path)}", 3000)
    
    def test_clear_node_log_with_token_item(self, commander_presenter_utils, mock_log_writer):
        """Test clear_node_log with an item that has a token"""
        # Setup
        mock_item = MagicMock()
        token_id = "123"
        mock_item.data.return_value = {"token": token_id}
        
        mock_status_signal = MagicMock()
        
        # Execute
        commander_presenter_utils.clear_node_log([mock_item], mock_status_signal)
        
        # Verify
        mock_log_writer.clear_log.assert_called_once_with(token_id)
        mock_status_signal.emit.assert_called_once_with(f"Cleared log for token: {token_id}", 3000)
    
    def test_clear_node_log_with_no_selected_items(self, commander_presenter_utils):
        """Test clear_node_log with no selected items"""
        # Setup
        mock_status_signal = MagicMock()
        
        # Execute
        commander_presenter_utils.clear_node_log([], mock_status_signal)
        
        # Verify
        mock_status_signal.emit.assert_called_once_with("No item selected! Select a token or log file on the left.", 3000)
    
    def test_clear_node_log_with_unsupported_item(self, commander_presenter_utils, mock_log_writer):
        """Test clear_node_log with an item that has unsupported data"""
        # Setup
        mock_item = MagicMock()
        mock_item.data.return_value = {"unsupported_key": "some_value"}
        
        mock_status_signal = MagicMock()
        
        # Execute
        commander_presenter_utils.clear_node_log([mock_item], mock_status_signal)
        
        # Verify
        mock_log_writer.clear_log.assert_not_called()
        mock_status_signal.emit.assert_called_once_with("Unsupported item type", 3000)
    
    def test_clear_node_log_with_exception(self, commander_presenter_utils, mock_log_writer):
        """Test clear_node_log when an exception occurs"""
        # Setup
        mock_item = MagicMock()
        token_id = "123"
        mock_item.data.return_value = {"token": token_id}
        
        mock_status_signal = MagicMock()
        
        # Mock the log_writer to raise an exception
        mock_log_writer.clear_log.side_effect = Exception("Test exception")
        
        # Execute
        commander_presenter_utils.clear_node_log([mock_item], mock_status_signal)
        
        # Verify
        mock_log_writer.clear_log.assert_called_once_with(token_id)
        mock_status_signal.emit.assert_called_once_with("Error clearing log: Test exception", 5000)