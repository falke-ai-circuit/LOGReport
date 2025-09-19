import os
import sys
import pytest
from unittest.mock import MagicMock, patch, mock_open
from datetime import datetime

# Add src directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'src')))


class TestLogWriterWriteToLog:
    """Test suite for LogWriter.write_to_log method"""
    
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
    
    def test_write_to_log_with_active_node(self, log_writer, mock_node_manager):
        """Test writing to log with active node"""
        # Setup
        content = "Test log content"
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
                    
                    # Verify signal emission
                    log_writer.log_write_completed.emit.assert_called_once_with(node_name, mock_token.token_id, True)
    
    def test_write_to_log_with_explicit_node_name(self, log_writer, mock_node_manager):
        """Test writing to log with explicit node name"""
        # Setup
        content = "Test log content"
        log_type = "RPC"
        node_name = "AP02r"
        timestamp = "2025-09-11 12:00:01"
        
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
                    
                    # Verify signal emission
                    log_writer.log_write_completed.emit.assert_called_once_with(node_name, mock_token.token_id, True)
    
    def test_write_to_log_with_empty_content(self, log_writer, mock_node_manager):
        """Test writing to log with empty content"""
        # Setup
        content = ""
        log_type = "LIS"
        node_name = "AL01"
        
        # Create mock active node
        mock_active_node = MagicMock()
        mock_active_node.name = node_name
        mock_node_manager.active_node = mock_active_node
        
        # Execute
        with patch.object(log_writer, 'write_to_app_log') as mock_write_to_app_log:
            log_writer.write_to_log(content, log_type)
            
            # Verify - should return early without writing
            mock_write_to_app_log.assert_not_called()
            log_writer.log_write_completed.emit.assert_not_called()
    
    def test_write_to_log_with_whitespace_only_content(self, log_writer, mock_node_manager):
        """Test writing to log with whitespace-only content"""
        # Setup
        content = "   \n\t  "
        log_type = "LOG"
        node_name = "AL02"
        
        # Create mock active node
        mock_active_node = MagicMock()
        mock_active_node.name = node_name
        mock_node_manager.active_node = mock_active_node
        
        # Execute
        with patch.object(log_writer, 'write_to_app_log') as mock_write_to_app_log:
            log_writer.write_to_log(content, log_type)
            
            # Verify - should return early without writing
            mock_write_to_app_log.assert_not_called()
            log_writer.log_write_completed.emit.assert_not_called()
    
    def test_write_to_log_file_write_exception(self, log_writer, mock_node_manager):
        """Test writing to log when file write operation fails"""
        # Setup
        content = "Test log content"
        log_type = "FBC"
        node_name = "AP03m"
        timestamp = "2025-09-11 12:00:02"
        
        # Create mock active node
        mock_active_node = MagicMock()
        mock_active_node.name = node_name
        mock_node_manager.active_node = mock_active_node
        
        # Mock datetime to return consistent timestamp
        with patch("commander.log_writer.datetime") as mock_datetime:
            mock_datetime.now.return_value.strftime.return_value = timestamp
            
            # Mock file operations to raise an exception
            with patch("builtins.open", mock_open()) as mock_file:
                mock_file.side_effect = Exception("Permission denied")
                
                with patch.object(log_writer, 'write_to_app_log') as mock_write_to_app_log:
                    # Execute and verify exception is raised
                    with pytest.raises(Exception, match="Permission denied"):
                        log_writer.write_to_log(content, log_type)
                    
                    # Verify app log was written with error message
                    mock_write_to_app_log.assert_called_once_with(f"Failed to write to {log_type} log: Permission denied")
                    # Verify signal emission with failure
                    log_writer.log_write_completed.emit.assert_called_once_with("N/A", "N/A", False)
    
    def test_write_to_log_no_active_node_fallback(self, log_writer, mock_node_manager):
        """Test writing to log when no active node exists - should fallback to app log"""
        # Setup
        content = "Test log content"
        log_type = "RPC"
        
        # No active node
        mock_node_manager.active_node = None
        
        # Execute
        with patch.object(log_writer, 'write_to_app_log') as mock_write_to_app_log:
            log_writer.write_to_log(content, log_type)
            
            # Verify - should write to app log with fallback message
            expected_message = f"No active node, writing {log_type} content to app log: {content[:100]}..."
            mock_write_to_app_log.assert_called_once_with(expected_message)
            log_writer.log_write_completed.emit.assert_called_once_with("N/A", "N/A", False)
    
    def test_write_to_log_no_active_node_and_no_node_name(self, log_writer, mock_node_manager):
        """Test writing to log with no active node and no explicit node name"""
        # Setup
        content = "Test log content"
        log_type = "LIS"
        
        # No active node
        mock_node_manager.active_node = None
        
        # Execute
        with patch.object(log_writer, 'write_to_app_log') as mock_write_to_app_log:
            log_writer.write_to_log(content, log_type)
            
            # Verify - should write to app log with fallback message
            expected_message = f"No active node, writing {log_type} content to app log: {content[:100]}..."
            mock_write_to_app_log.assert_called_once_with(expected_message)
            log_writer.log_write_completed.emit.assert_called_once_with("N/A", "N/A", False)
    
    def test_write_to_log_creates_directories(self, log_writer, mock_node_manager):
        """Test that write_to_log creates necessary directories"""
        # Setup
        content = "Test log content"
        log_type = "FBC"
        node_name = "AP01m"
        timestamp = "2025-09-11 12:00:03"
        
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
                    log_writer.write_to_log(content, log_type)
                    
                    # Verify directories were created
                    expected_dir = os.path.join("test_logs", log_type, node_name)
                    mock_makedirs.assert_called_once_with(expected_dir, exist_ok=True)
                    log_writer.log_write_completed.emit.assert_called_once_with(node_name, "N/A", True)
                    
    def test_write_to_log_with_token_log_path(self, log_writer, mock_node_manager):
        """Test writing to log with token that has log_path"""
        # Setup
        content = "Test log content"
        log_type = "FBC"
        node_name = "AP01m"
        log_path = "test_logs/FBC/AP01m/AP01m_192-168-0-11_162.fbc"
        timestamp = "2025-09-11 12:00:04"
        
        # Create mock token with log_path
        mock_token = MagicMock()
        mock_token.log_path = log_path
        mock_token.token_type = log_type
        mock_token.name = node_name
        
        # Mock datetime to return consistent timestamp
        with patch("commander.log_writer.datetime") as mock_datetime:
            mock_datetime.now.return_value.strftime.return_value = timestamp
            
            # Mock file operations
            with patch("builtins.open", mock_open()) as mock_file:
                # Execute
                log_writer.write_to_log(content, log_type, node_name, mock_token)
                
                # Verify
                mock_file.assert_called_once_with(log_path, 'a', encoding='utf-8')
                expected_content = f"[{timestamp}] {content}"
                mock_file().write.assert_called_once_with(expected_content + '\n')
                log_writer.log_write_completed.emit.assert_called_once_with(node_name, token_id, True)
                log_writer.log_write_completed.emit.assert_called_once_with(node_name, "N/A", True)
                
    def test_write_to_log_with_token_and_identifiers(self, log_writer, mock_node_manager):
        """Test writing to log with token that has token_id and ip_address"""
        # Setup
        content = "Test log content"
        log_type = "RPC"
        node_name = "AP01m"
        token_id = "162"
        ip_address = "192.168.0.11"
        timestamp = "2025-09-11 12:00:05"
        
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