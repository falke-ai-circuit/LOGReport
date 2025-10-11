import os
import sys
import pytest
from unittest.mock import MagicMock, patch, call
from PyQt5.QtCore import QTimer
from PyQt5.QtGui import QClipboard
from PyQt5.QtWidgets import QApplication

# Add src directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'src')))

from commander.services.clipboard_monitor import ClipboardMonitor
from commander.node_manager import Node, NodeToken
from commander.log_writer import LogWriter
from commander.services.status_service import StatusService


class TestClipboardMonitor:
    """Test suite for ClipboardMonitor service"""
    
    @pytest.fixture
    def mock_node_manager(self):
        """Create a mock NodeManager"""
        mock_nm = MagicMock()
        mock_nm.active_log_file = "test_log_file"
        mock_nm.active_node = MagicMock()
        mock_nm.active_node.name = "AP01m"
        return mock_nm
    
    @pytest.fixture
    def mock_log_writer(self):
        """Create a mock LogWriter"""
        mock_lw = MagicMock()
        return mock_lw
    
    @pytest.fixture
    def mock_status_service(self):
        """Create a mock StatusService"""
        mock_ss = MagicMock()
        return mock_ss
    
    @pytest.fixture
    def clipboard_monitor(self, mock_node_manager, mock_log_writer, mock_status_service):
        """Create a ClipboardMonitor instance with mocked dependencies"""
        # Mock QApplication.clipboard() to avoid Qt initialization issues
        with patch('PyQt5.QtWidgets.QApplication.clipboard') as mock_clipboard_method:
            mock_clipboard = MagicMock()
            mock_clipboard_method.return_value = mock_clipboard
            
            # Create ClipboardMonitor instance
            monitor = ClipboardMonitor(mock_node_manager, mock_log_writer, mock_status_service)
            
            # Set the mock clipboard directly
            monitor.clipboard = mock_clipboard
            
            return monitor
    
    def test_initialization(self, clipboard_monitor, mock_node_manager, mock_log_writer, mock_status_service):
        """Test ClipboardMonitor initialization"""
        assert clipboard_monitor.node_manager == mock_node_manager
        assert clipboard_monitor.log_writer == mock_log_writer
        assert clipboard_monitor.status_service == mock_status_service
        assert clipboard_monitor.last_clipboard_content == ""
        assert clipboard_monitor.operation_count == 0
        assert clipboard_monitor.manual_copy_callback is None
        
        # Check that rate limit timer is set up
        assert isinstance(clipboard_monitor.rate_limit_timer, QTimer)
        
        # Check that clipboard dataChanged signal is connected
        clipboard_monitor.clipboard.dataChanged.connect.assert_called_once_with(clipboard_monitor._on_clipboard_changed)
        
        # Check validation patterns
        assert any(p[0] == 'FBC' for p in clipboard_monitor.patterns)
        assert any(p[0] == 'LIS' for p in clipboard_monitor.patterns)
        
        assert any(p[0] == 'RPC' for p in clipboard_monitor.patterns)
    
    def test_validate_content_fbc_valid(self, clipboard_monitor):
        """Test validation of valid FBC content"""
        # Valid FBC content
        content = "AP01m 12:34:56.789 Some FBC data here"
        result = clipboard_monitor._validate_content(content)
        assert result == "FBC"
    
    def test_validate_content_fbc_invalid(self, clipboard_monitor):
        """Test validation of invalid FBC content"""
        # Invalid FBC content
        content = "Invalid FBC content"
        result = clipboard_monitor._validate_content(content)
        assert result is None
    
    def test_validate_content_lis_valid(self, clipboard_monitor):
        """Test validation of valid LIS content"""
        # Valid LIS content
        content = "LIS 2025-09-07 12:34:56 Some LIS data here"
        result = clipboard_monitor._validate_content(content)
        assert result == "LIS"
    
    def test_validate_content_lis_invalid(self, clipboard_monitor):
        """Test validation of invalid LIS content"""
        # Invalid LIS content
        content = "Invalid LIS content"
        result = clipboard_monitor._validate_content(content)
        assert result is None
    
    def test_validate_content_log_valid(self, clipboard_monitor):
        """Test validation of valid LOG content"""
        # LOG pattern accepts any content
        content = "Any log content is valid"
        result = clipboard_monitor._validate_content(content)
        assert result == "LOG"
    
    def test_validate_content_rpc_valid_json(self, clipboard_monitor):
        """Test validation of valid RPC JSON content"""
        # Valid RPC JSON content
        content = '{"key": "value"}'
        result = clipboard_monitor._validate_content(content)
        assert result == "RPC"
    
    def test_validate_content_rpc_valid_xml(self, clipboard_monitor):
        """Test validation of valid RPC XML content"""
        # Valid RPC XML content
        content = "<root><element>value</element></root>"
        result = clipboard_monitor._validate_content(content)
        assert result == "RPC"
    
    def test_validate_content_rpc_invalid(self, clipboard_monitor):
        """Test validation of invalid RPC content"""
        # Invalid RPC content
        content = "Invalid RPC content"
        result = clipboard_monitor._validate_content(content)
        assert result is None
    
    def test_check_rate_limit_within_limit(self, clipboard_monitor):
        """Test rate limit check when within limit"""
        clipboard_monitor.operation_count = 3
        result = clipboard_monitor._check_rate_limit()
        assert result is True
    
    def test_check_rate_limit_exceeded(self, clipboard_monitor):
        """Test rate limit check when exceeded"""
        clipboard_monitor.operation_count = 5
        result = clipboard_monitor._check_rate_limit()
        assert result is False
    
    def test_reset_operation_count(self, clipboard_monitor):
        """Test resetting operation count"""
        clipboard_monitor.operation_count = 3
        clipboard_monitor._reset_operation_count()
        assert clipboard_monitor.operation_count == 0
    
    def test_set_manual_copy_callback(self, clipboard_monitor):
        """Test setting manual copy callback"""
        def test_callback(content):
            pass
        
        clipboard_monitor.set_manual_copy_callback(test_callback)
        assert clipboard_monitor.manual_copy_callback == test_callback
    
    @patch.object(ClipboardMonitor, '_auto_copy_to_log')
    def test_on_clipboard_changed_no_content_change(self, mock_auto_copy_to_log, clipboard_monitor):
        """Test clipboard change handler when content hasn't changed"""
        clipboard_monitor.last_clipboard_content = "test content"
        clipboard_monitor.clipboard.text.return_value = "test content"

        clipboard_monitor._on_clipboard_changed()

        # Should not call auto_copy_to_log
        mock_auto_copy_to_log.assert_not_called()
    
    @patch.object(ClipboardMonitor, '_auto_copy_to_log')
    def test_on_clipboard_changed_empty_content(self, mock_auto_copy_to_log, clipboard_monitor):
        """Test clipboard change handler when content is empty"""
        clipboard_monitor.last_clipboard_content = ""
        clipboard_monitor.clipboard.text.return_value = ""

        clipboard_monitor._on_clipboard_changed()

        # Should not call auto_copy_to_log
        mock_auto_copy_to_log.assert_not_called()
    
    @patch.object(ClipboardMonitor, '_auto_copy_to_log')
    def test_on_clipboard_changed_with_active_log(self, mock_auto_copy_to_log, clipboard_monitor):
        """Test clipboard change handler with active log file"""
        clipboard_monitor.last_clipboard_content = ""
        clipboard_monitor.clipboard.text.return_value = "test content"

        clipboard_monitor._on_clipboard_changed()

        # Should call auto_copy_to_log
        mock_auto_copy_to_log.assert_called_once_with("test content")
    
    @patch.object(ClipboardMonitor, '_check_rate_limit', return_value=False)
    def test_auto_copy_to_log_rate_limit_exceeded(self, mock_check_rate_limit, clipboard_monitor, mock_status_service):
        """Test auto copy to log when rate limit is exceeded"""
        clipboard_monitor._auto_copy_to_log("test content")
        
        # Should show rate limit message
        mock_status_service.show_message.assert_called_once_with("Rate limit exceeded (5 operations/minute)")
    
    @patch.object(ClipboardMonitor, '_validate_content', return_value=None)
    @patch.object(ClipboardMonitor, '_check_rate_limit', return_value=True)
    def test_auto_copy_to_log_invalid_content(self, mock_check_rate_limit, mock_validate_content, clipboard_monitor, mock_status_service):
        """Test auto copy to log with invalid content"""
        clipboard_monitor.operation_count = 0
        clipboard_monitor._auto_copy_to_log("invalid content")
            
        # Should not call log_writer.write_to_log
        clipboard_monitor.log_writer.write_to_log.assert_not_called()
    
    @patch.object(ClipboardMonitor, '_validate_content', return_value="FBC")
    @patch.object(ClipboardMonitor, '_check_rate_limit', return_value=True)
    def test_auto_copy_to_log_valid_content(self, mock_check_rate_limit, mock_validate_content, clipboard_monitor, mock_log_writer, mock_status_service):
        """Test auto copy to log with valid content"""
        clipboard_monitor.operation_count = 0
        clipboard_monitor._auto_copy_to_log("AP01m 12:34:56.789 test")
            
        # Should call log_writer.write_to_log
        mock_log_writer.write_to_log.assert_called_once_with("AP01m 12:34:56.789 test", "FBC")
            
        # Should show success message
        mock_status_service.show_message.assert_called_once_with("Auto-copied to log")
            
        # Should increment operation count
        assert clipboard_monitor.operation_count == 1
    
    @patch.object(ClipboardMonitor, '_validate_content', return_value="FBC")
    @patch.object(ClipboardMonitor, '_check_rate_limit', return_value=True)
    def test_auto_copy_to_log_write_exception(self, mock_check_rate_limit, mock_validate_content, clipboard_monitor, mock_log_writer, mock_status_service):
        """Test auto copy to log when write operation fails"""
        clipboard_monitor.operation_count = 0
        mock_log_writer.write_to_log.side_effect = Exception("Write error")
        
        clipboard_monitor._auto_copy_to_log("AP01m 12:34:56.789 test")
            
        # Should show error message
        mock_status_service.show_message.assert_called_once_with("Failed to auto-copy: Write error")
    
    def test_manual_copy_to_log_rate_limit_exceeded(self, clipboard_monitor, mock_status_service):
        """Test manual copy to log when rate limit is exceeded"""
        clipboard_monitor.operation_count = 5  # Exceed rate limit
        
        clipboard_monitor.manual_copy_to_log("test content")
        
        # Should show rate limit message
        mock_status_service.show_message.assert_called_once_with("Rate limit exceeded (5 operations/minute)")
    
    def test_manual_copy_to_log_invalid_content(self, clipboard_monitor, mock_status_service):
        """Test manual copy to log with invalid content"""
        clipboard_monitor.operation_count = 0
        with patch.object(clipboard_monitor, '_validate_content', return_value=None):
            clipboard_monitor.manual_copy_to_log("invalid content")
            
            # Should show invalid format message
            mock_status_service.show_message.assert_called_once_with("Invalid format for log type")
            
            # Should not call log_writer.write_to_log
            clipboard_monitor.log_writer.write_to_log.assert_not_called()
    
    def test_manual_copy_to_log_valid_content_no_callback(self, clipboard_monitor, mock_log_writer, mock_status_service):
        """Test manual copy to log with valid content and no callback"""
        clipboard_monitor.operation_count = 0
        clipboard_monitor.manual_copy_callback = None
        
        with patch.object(clipboard_monitor, '_validate_content', return_value="FBC"):
            clipboard_monitor.manual_copy_to_log("AP01m 12:34:56.789 test")
            
            # Should call log_writer.write_to_log
            mock_log_writer.write_to_log.assert_called_once_with("AP01m 12:34:56.789 test", "FBC")
            
            # Should show success message
            mock_status_service.show_message.assert_called_once_with("Copied to log")
            
            # Should increment operation count
            assert clipboard_monitor.operation_count == 1
    
    def test_manual_copy_to_log_valid_content_with_callback(self, clipboard_monitor, mock_log_writer, mock_status_service):
        """Test manual copy to log with valid content and callback"""
        clipboard_monitor.operation_count = 0
        callback = MagicMock()
        clipboard_monitor.set_manual_copy_callback(callback)
        
        with patch.object(clipboard_monitor, '_validate_content', return_value="FBC"):
            clipboard_monitor.manual_copy_to_log("AP01m 12:34:56.789 test")
            
            # Should call the callback
            callback.assert_called_once_with("AP01m 12:34:56.789 test")
            
            # Should call log_writer.write_to_log
            mock_log_writer.write_to_log.assert_called_once_with("AP01m 12:34:56.789 test", "FBC")
            
            # Should show success message
            mock_status_service.show_message.assert_called_once_with("Copied to log")
            
            # Should increment operation count
            assert clipboard_monitor.operation_count == 1
    
    def test_manual_copy_to_log_write_exception(self, clipboard_monitor, mock_log_writer, mock_status_service):
        """Test manual copy to log when write operation fails"""
        clipboard_monitor.operation_count = 0
        mock_log_writer.write_to_log.side_effect = Exception("Write error")
        
        with patch.object(clipboard_monitor, '_validate_content', return_value="FBC"):
            clipboard_monitor.manual_copy_to_log("AP01m 12:34:56.789 test")
            
            # Should show error message
            mock_status_service.show_message.assert_called_once_with("Failed to copy: Write error")
    
    def test_handle_vnc_text_selection(self, clipboard_monitor, mock_status_service):
        """Test handling VNC text selection"""
        test_content = "VNC selected text"
        
        clipboard_monitor.handle_vnc_text_selection(test_content)
        
        # Should set text to clipboard
        clipboard_monitor.clipboard.setText.assert_called_once_with(test_content)
        
        # Should show notification
        mock_status_service.show_message.assert_called_once_with("Copied to clipboard")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])