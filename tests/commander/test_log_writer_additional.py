import os
import sys
import pytest
from unittest.mock import MagicMock, patch, mock_open
from datetime import datetime

# Add src directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'src')))


class TestLogWriterWriteToLogAdditional:
    """Additional test suite for LogWriter.write_to_log method"""
    
    @pytest.fixture
    def mock_node_manager(self):
        """Create a mock NodeManager"""
        mock_nm = MagicMock()
        return mock_nm
    
    @pytest.fixture
    def log_writer(self, mock_node_manager):
        """Create a LogWriter instance with mocked dependencies"""
        # Mock the LogWriter class directly to avoid import issues
        with patch('commander.log_writer.logging'):
            with patch('commander.log_writer.os.makedirs'):
                # Import after patching to avoid issues
                from commander.log_writer import LogWriter
                return LogWriter(mock_node_manager)
    
    def test_write_to_log_with_unicode_content(self, log_writer, mock_node_manager):
        """Test writing to log with Unicode content"""
        # Setup
        content = "Test log content with Unicode: 你好世界 🌍 Привет мир"
        log_type = "FBC"
        node_name = "AP01m"
        timestamp = "2025-09-11 12:00:00"
        
        # Create mock active node
        mock_active_node = MagicMock()
        mock_active_node.name = node_name
        
        # Set active node on node manager
        mock_node_manager.active_node = mock_active_node
        
        # Create mock token with token_id and ip_address
        mock_token = MagicMock()
        mock_token.token_id = "FBC"
        mock_token.ip_address = "192.168.0.11"
        mock_token.token_type = log_type
        mock_token.name = node_name
        mock_token.log_path = None
        
        # Mock datetime to return consistent timestamp
        with patch("commander.log_writer.datetime") as mock_datetime:
            mock_datetime.now.return_value.strftime.return_value = timestamp
            
            # Mock file operations
            with patch("builtins.open", mock_open()) as mock_file:
                with patch("commander.log_writer.os.makedirs") as mock_makedirs:
                    # Execute
                    log_writer.write_to_log(content, log_type, None, mock_token)
                    
                    # Verify
                    expected_dir = os.path.join("test_logs", log_type, node_name)
                    mock_makedirs.assert_called_once_with(expected_dir, exist_ok=True)
                    
                    expected_filepath = os.path.join(expected_dir, f"{node_name}_192-168-0-11_FBC.{log_type.lower()}")
                    mock_file.assert_called_once_with(expected_filepath, 'a', encoding='utf-8')
                    expected_content = f"[{timestamp}] {content}"
                    mock_file().write.assert_called_once_with(expected_content + '\n')
    
    def test_write_to_log_with_special_characters(self, log_writer, mock_node_manager):
        """Test writing to log with special characters"""
        # Setup
        content = "Test content with special chars: \n\t\r\\\"'@#$%^&*()_+-=[]{}|;':,./<>?"
        log_type = "RPC"
        node_name = "AP02r"
        timestamp = "2025-09-11 12:00:01"
        
        # Create mock active node
        mock_active_node = MagicMock()
        mock_active_node.name = node_name
        
        # Set active node on node manager
        mock_node_manager.active_node = mock_active_node
        
        # Create mock token with token_id and ip_address
        mock_token = MagicMock()
        mock_token.token_id = "RPC"
        mock_token.ip_address = "192.168.0.11"
        mock_token.token_type = log_type
        mock_token.name = node_name
        mock_token.log_path = None
        
        # Mock datetime to return consistent timestamp
        with patch("commander.log_writer.datetime") as mock_datetime:
            mock_datetime.now.return_value.strftime.return_value = timestamp
            
            # Mock file operations
            with patch("builtins.open", mock_open()) as mock_file:
                with patch("commander.log_writer.os.makedirs") as mock_makedirs:
                    # Execute
                    log_writer.write_to_log(content, log_type, node_name, mock_token)
                    
                    # Verify
                    expected_dir = os.path.join("test_logs", log_type, node_name)
                    mock_makedirs.assert_called_once_with(expected_dir, exist_ok=True)
                    
                    expected_filepath = os.path.join(expected_dir, f"{node_name}_192-168-0-11_RPC.{log_type.lower()}")
                    mock_file.assert_called_once_with(expected_filepath, 'a', encoding='utf-8')
                    expected_content = f"[{timestamp}] {content}"
                    mock_file().write.assert_called_once_with(expected_content + '\n')
    
    def test_write_to_log_with_multiline_content(self, log_writer, mock_node_manager):
        """Test writing to log with multiline content"""
        # Setup
        content = "Line 1\nLine 2\nLine 3\n"
        log_type = "LIS"
        node_name = "AL01"
        timestamp = "2025-09-11 12:00:02"
        
        # Create mock active node
        mock_active_node = MagicMock()
        mock_active_node.name = node_name
        
        # Set active node on node manager
        mock_node_manager.active_node = mock_active_node
        
        # Create mock token with token_id and ip_address
        mock_token = MagicMock()
        mock_token.token_id = "LIS"
        mock_token.ip_address = "192.168.0.11"
        mock_token.token_type = log_type
        mock_token.name = node_name
        mock_token.log_path = None
        
        # Mock datetime to return consistent timestamp
        with patch("commander.log_writer.datetime") as mock_datetime:
            mock_datetime.now.return_value.strftime.return_value = timestamp
            
            # Mock file operations
            with patch("builtins.open", mock_open()) as mock_file:
                with patch("commander.log_writer.os.makedirs") as mock_makedirs:
                    # Execute
                    log_writer.write_to_log(content, log_type, None, mock_token)
                    
                    # Verify
                    expected_dir = os.path.join("test_logs", log_type, node_name)
                    mock_makedirs.assert_called_once_with(expected_dir, exist_ok=True)
                    
                    expected_filepath = os.path.join(expected_dir, f"{node_name}_192-168-0-11_LIS.{log_type.lower()}")
                    mock_file.assert_called_once_with(expected_filepath, 'a', encoding='utf-8')
                    expected_content = f"[{timestamp}] {content}"
                    mock_file().write.assert_called_once_with(expected_content + '\n')
    
    def test_write_to_log_all_log_types(self, log_writer, mock_node_manager):
        """Test writing to log with all supported log types"""
        # Setup
        content = "Test content"
        log_types = ["FBC", "RPC", "LIS", "LOG"]
        node_name = "TEST_NODE"
        timestamp = "2025-09-11 12:00:03"
        
        # Create mock active node
        mock_active_node = MagicMock()
        mock_active_node.name = node_name
        
        # Set active node on node manager
        mock_node_manager.active_node = mock_active_node
        
        # Mock datetime to return consistent timestamp
        with patch("commander.log_writer.datetime") as mock_datetime:
            mock_datetime.now.return_value.strftime.return_value = timestamp
            
            for log_type in log_types:
                # Create mock token with token_id and ip_address
                mock_token = MagicMock()
                mock_token.token_id = "TEST"
                mock_token.ip_address = "192.168.0.11"
                mock_token.token_type = log_type
                mock_token.name = node_name
                mock_token.log_path = None
                # Mock file operations for each log type
                with patch("builtins.open", mock_open()) as mock_file:
                    with patch("commander.log_writer.os.makedirs") as mock_makedirs:
                        # Execute
                        log_writer.write_to_log(content, log_type, None, mock_token)
                        
                        # Verify
                        expected_dir = os.path.join("test_logs", log_type, node_name)
                        mock_makedirs.assert_called_with(expected_dir, exist_ok=True)
                        
                        if log_type.upper() == "LOG":
                            expected_filepath = os.path.join(expected_dir, f"{node_name}_192-168-0-11.log")
                        elif log_type.upper() == "RPC":
                            expected_filepath = os.path.join(expected_dir, f"{node_name}_192-168-0-11_TEST.{log_type.lower()}")
                        else:
                            expected_filepath = os.path.join(expected_dir, f"{node_name}_192-168-0-11_TEST.{log_type.lower()}")
                        mock_file.assert_called_with(expected_filepath, 'a', encoding='utf-8')
                        expected_content = f"[{timestamp}] {content}"
                        mock_file().write.assert_called_with(expected_content + '\n')
    
    def test_write_to_log_with_very_long_content(self, log_writer, mock_node_manager):
        """Test writing to log with very long content"""
        # Setup
        content = "A" * 10000  # 10KB of content
        log_type = "FBC"
        node_name = "AP01m"
        timestamp = "2025-09-11 12:00:04"
        
        # Create mock active node
        mock_active_node = MagicMock()
        mock_active_node.name = node_name
        
        # Set active node on node manager
        mock_node_manager.active_node = mock_active_node
        
        # Create mock token with token_id and ip_address
        mock_token = MagicMock()
        mock_token.token_id = "FBC"
        mock_token.ip_address = "192.168.0.11"
        mock_token.token_type = log_type
        mock_token.name = node_name
        mock_token.log_path = None
        
        # Mock datetime to return consistent timestamp
        with patch("commander.log_writer.datetime") as mock_datetime:
            mock_datetime.now.return_value.strftime.return_value = timestamp
            
            # Mock file operations
            with patch("builtins.open", mock_open()) as mock_file:
                with patch("commander.log_writer.os.makedirs") as mock_makedirs:
                    # Execute
                    log_writer.write_to_log(content, log_type, None, mock_token)
                    
                    # Verify
                    expected_dir = os.path.join("test_logs", log_type, node_name)
                    mock_makedirs.assert_called_once_with(expected_dir, exist_ok=True)
                    
                    expected_filepath = os.path.join(expected_dir, f"{node_name}_192-168-0-11_FBC.{log_type.lower()}")
                    mock_file.assert_called_once_with(expected_filepath, 'a', encoding='utf-8')
                    expected_content = f"[{timestamp}] {content}"
                    mock_file().write.assert_called_once_with(expected_content + '\n')
    
    def test_write_to_log_with_timestamp_format(self, log_writer, mock_node_manager):
        """Test that timestamp format is correct in content"""
        # Setup
        content = "Test content"
        log_type = "FBC"
        node_name = "AP01m"
        timestamp = "2025-09-11 12:00:05"
        
        # Create mock active node
        mock_active_node = MagicMock()
        mock_active_node.name = node_name
        
        # Set active node on node manager
        mock_node_manager.active_node = mock_active_node
        
        # Create mock token with token_id and ip_address
        mock_token = MagicMock()
        mock_token.token_id = "FBC"
        mock_token.ip_address = "192.168.0.11"
        mock_token.token_type = log_type
        mock_token.name = node_name
        mock_token.log_path = None
        
        # Mock datetime to return consistent timestamp
        with patch("commander.log_writer.datetime") as mock_datetime:
            mock_datetime.now.return_value.strftime.return_value = timestamp
            
            # Mock file operations
            with patch("builtins.open", mock_open()) as mock_file:
                with patch("commander.log_writer.os.makedirs") as mock_makedirs:
                    # Execute
                    log_writer.write_to_log(content, log_type, None, mock_token)
                    
                    # Verify
                    expected_dir = os.path.join("test_logs", log_type, node_name)
                    expected_filepath = os.path.join(expected_dir, f"{node_name}_192-168-0-11_FBC.{log_type.lower()}")
                    mock_file.assert_called_with(expected_filepath, 'a', encoding='utf-8')
                    expected_content = f"[{timestamp}] {content}"
                    mock_file().write.assert_called_with(expected_content + '\n')
    
    def test_write_to_log_file_permissions_error(self, log_writer, mock_node_manager):
        """Test writing to log when file write fails"""
        # Setup
        content = "Test content"
        log_type = "FBC"
        node_name = "AP01m"
        timestamp = "2025-09-11 12:00:06"
        
        # Create mock active node
        mock_active_node = MagicMock()
        mock_active_node.name = node_name
        
        # Set active node on node manager
        mock_node_manager.active_node = mock_active_node
        
        # Mock datetime to return consistent timestamp
        with patch("commander.log_writer.datetime") as mock_datetime:
            mock_datetime.now.return_value.strftime.return_value = timestamp
            
            # Mock file operations to raise PermissionError
            with patch("builtins.open", mock_open()) as mock_file:
                mock_file.side_effect = PermissionError("Permission denied")
                
                with patch.object(log_writer, 'write_to_app_log') as mock_write_to_app_log:
                    # Execute and verify exception is raised
                    with pytest.raises(PermissionError, match="Permission denied"):
                        log_writer.write_to_log(content, log_type)
                    
                    # Verify app log was written with error message
                    mock_write_to_app_log.assert_called_once_with(f"Failed to write to {log_type} log: Permission denied")
    
    def test_write_to_log_with_none_content(self, log_writer, mock_node_manager):
        """Test writing to log with None content"""
        # Setup
        content = None
        log_type = "FBC"
        node_name = "AP01m"
        
        # Create mock active node
        mock_active_node = MagicMock()
        mock_active_node.name = node_name
        
        # Set active node on node manager
        mock_node_manager.active_node = mock_active_node
        
        # Execute - should raise AttributeError because None doesn't have strip() method
        with pytest.raises(AttributeError):
            log_writer.write_to_log(content, log_type)
    
    def test_write_to_log_with_numeric_content(self, log_writer, mock_node_manager):
        """Test writing to log with numeric content"""
        # Setup
        content = 12345
        log_type = "FBC"
        node_name = "AP01m"
        
        # Create mock active node
        mock_active_node = MagicMock()
        mock_active_node.name = node_name
        
        # Set active node on node manager
        mock_node_manager.active_node = mock_active_node
        
        # Execute - should raise AttributeError because int doesn't have strip() method
        with pytest.raises(AttributeError):
            log_writer.write_to_log(content, log_type)
            
    def test_write_to_log_with_token_and_identifiers(self, log_writer, mock_node_manager):
        """Test writing to log with token that has token_id and ip_address"""
        # Setup
        content = "Test log content"
        log_type = "FBC"
        node_name = "AP01m"
        token_id = "162"
        ip_address = "192.168.0.11"
        timestamp = "2025-09-11 12:00:07"
        
        # Create mock token with token_id and ip_address
        mock_token = MagicMock()
        mock_token.token_id = token_id
        mock_token.ip_address = ip_address
        mock_token.token_type = log_type
        mock_token.name = node_name
        mock_token.log_path = None
        
        # Create mock active node
        mock_active_node = MagicMock()
        mock_active_node.name = node_name
        mock_node_manager.active_node = mock_active_node
        
        # Mock datetime to return consistent timestamp
        with patch("commander.log_writer.datetime") as mock_datetime:
            mock_datetime.now.return_value.strftime.return_value = timestamp
            
            # Mock file operations
            with patch("builtins.open", mock_open()) as mock_file:
                with patch("commander.log_writer.os.makedirs") as mock_makedirs:
                    # Execute
                    log_writer.write_to_log(content, log_type, node_name, mock_token)
                    
                    # Verify
                    expected_dir = os.path.join("test_logs", log_type, node_name)
                    mock_makedirs.assert_called_once_with(expected_dir, exist_ok=True)
                    
                    # Expected filename with identifiers: {node_name}_{formatted_ip}_{token_id}.{extension}
                    formatted_ip = ip_address.replace('.', '-')
                    expected_filename = f"{node_name}_{formatted_ip}_{token_id}.{log_type.lower()}"
                    expected_filepath = os.path.join(expected_dir, expected_filename)
                    mock_file.assert_called_once_with(expected_filepath, 'a', encoding='utf-8')
                    expected_content = f"[{timestamp}] {content}"
                    mock_file().write.assert_called_once_with(expected_content + '\n')