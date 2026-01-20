"""
Test suite for log write notification display in Telnet tab.

This test verifies that when log files (.lis, .fbc, .log, .rpc) are written,
notifications are displayed in the Telnet tab window showing what content
was received and written to the files.
"""

import pytest
import os
from unittest.mock import MagicMock, patch
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QSettings

from commander.ui.commander_window import CommanderWindow


@pytest.fixture(scope="module")
def qapp():
    """Create QApplication instance for testing"""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app


@pytest.fixture
def commander_window(qapp, tmp_path):
    """Create CommanderWindow instance for testing"""
    # Mock QSettings to avoid persistent settings during tests
    with patch.object(QSettings, 'value', return_value=None):
        with patch.object(QSettings, 'setValue'):
            with patch.object(QSettings, 'sync'):
                window = CommanderWindow()
                yield window
                window.close()


class TestLogWriteNotificationDisplay:
    """Test suite for log write notification display feature."""

    def test_signal_connection_exists(self, commander_window):
        """Verify that log_write_completed signal is connected to on_log_write_notification handler."""
        # Check that the signal connection exists
        assert hasattr(commander_window.log_writer, 'log_write_completed')
        assert hasattr(commander_window, 'on_log_write_notification')
        
        # Verify signal can be emitted (no exception)
        try:
            commander_window.log_writer.log_write_completed.emit("test.log", True, 10, 5, "Test content")
        except Exception as e:
            pytest.fail(f"Signal emission failed: {str(e)}")

    def test_successful_write_with_content_display(self, commander_window):
        """Test that successful file write displays actual content in Telnet tab."""
        # Clear telnet output before test
        commander_window.telnet_tab.output.clear()
        
        # Emit log_write_completed signal simulating successful write with actual content
        log_path = "test_logs/FBC/AP01m/AP01m_192-168-0-11_162.fbc"
        test_content = "> print from fbc io structure 1620000\n[2025-01-10 14:30:00] FBC Output Data\nValue: 1234"
        commander_window.log_writer.log_write_completed.emit(log_path, True, 50, 25, test_content)
        
        # Process Qt events to ensure signal is handled
        QApplication.processEvents()
        
        # Verify actual content appears in Telnet tab output
        output_text = commander_window.telnet_tab.output.toPlainText()
        assert "📝 Writing to:" in output_text
        assert "AP01m_192-168-0-11_162.fbc" in output_text
        assert "25 new line(s)" in output_text
        assert "Total: 50 lines" in output_text
        # Verify actual content is displayed
        assert "FBC Output Data" in output_text
        assert "Value: 1234" in output_text
        assert "Content written to" in output_text

    def test_successful_write_without_new_content_display(self, commander_window):
        """Test that successful file write without new content displays appropriate notification."""
        # Clear telnet output before test
        commander_window.telnet_tab.output.clear()
        
        # Emit log_write_completed signal simulating successful write with no new content
        log_path = "test_logs/RPC/AP01m/AP01m_192-168-0-11_163.rpc"
        commander_window.log_writer.log_write_completed.emit(log_path, True, 10, 0, "")
        
        # Process Qt events
        QApplication.processEvents()
        
        # Verify notification shows no new content
        output_text = commander_window.telnet_tab.output.toPlainText()
        assert "📝" in output_text
        assert "AP01m_192-168-0-11_163.rpc" in output_text
        assert "No new content written" in output_text
        assert "Total: 10 lines" in output_text

    def test_failed_write_display(self, commander_window):
        """Test that failed file write displays error notification."""
        # Clear telnet output before test
        commander_window.telnet_tab.output.clear()
        
        # Emit log_write_completed signal simulating failed write
        log_path = "test_logs/LOG/AL01/AL01_192-168-0-12.log"
        commander_window.log_writer.log_write_completed.emit(log_path, False, 0, 0, "")
        
        # Process Qt events
        QApplication.processEvents()
        
        # Verify error notification appears
        output_text = commander_window.telnet_tab.output.toPlainText()
        assert "❌ Failed to write to" in output_text
        assert "AL01_192-168-0-12.log" in output_text

    def test_multiple_writes_display_sequentially(self, commander_window):
        """Test that multiple file writes display content in sequence."""
        # Clear telnet output before test
        commander_window.telnet_tab.output.clear()
        
        # Emit multiple log_write_completed signals with different content
        files = [
            ("test_logs/FBC/AP01m/file1.fbc", True, 20, 10, "Content for file1"),
            ("test_logs/RPC/AP01m/file2.rpc", True, 15, 5, "Content for file2"),
            ("test_logs/LIS/AL01/file3.lis", True, 30, 15, "Content for file3"),
        ]
        
        for log_path, success, total, written, content in files:
            commander_window.log_writer.log_write_completed.emit(log_path, success, total, written, content)
            QApplication.processEvents()
        
        # Verify all content appears
        output_text = commander_window.telnet_tab.output.toPlainText()
        assert "file1.fbc" in output_text
        assert "file2.rpc" in output_text
        assert "file3.lis" in output_text
        assert "Content for file1" in output_text
        assert "Content for file2" in output_text
        assert "Content for file3" in output_text
        assert output_text.count("📝 Writing to:") == 3

    def test_notification_format_different_file_types(self, commander_window):
        """Test content display format for different file types (.lis, .fbc, .log, .rpc)."""
        # Clear telnet output before test
        commander_window.telnet_tab.output.clear()
        
        # Test different file types with actual content
        file_types = [
            ("test_logs/FBC/node/test.fbc", True, 10, 5, "FBC test content"),
            ("test_logs/RPC/node/test.rpc", True, 20, 8, "RPC test content"),
            ("test_logs/LOG/node/test.log", True, 15, 3, "LOG test content"),
            ("test_logs/LIS/node/test.lis", True, 25, 12, "LIS test content"),
        ]
        
        for log_path, success, total, written, content in file_types:
            commander_window.telnet_tab.output.clear()
            commander_window.log_writer.log_write_completed.emit(log_path, success, total, written, content)
            QApplication.processEvents()
            
            output_text = commander_window.telnet_tab.output.toPlainText()
            filename = os.path.basename(log_path)
            
            # Verify format is consistent across file types
            assert "📝 Writing to:" in output_text
            assert filename in output_text
            assert f"{written} new line(s)" in output_text
            assert f"Total: {total} lines" in output_text
            # Verify actual content is displayed
            assert content in output_text

    def test_notification_with_na_log_path(self, commander_window):
        """Test notification when log_path is 'N/A' (fallback case)."""
        # Clear telnet output before test
        commander_window.telnet_tab.output.clear()
        
        # Emit signal with N/A log_path (fallback scenario)
        commander_window.log_writer.log_write_completed.emit("N/A", False, 0, 0, "")
        
        # Process Qt events
        QApplication.processEvents()
        
        # Verify notification handles N/A gracefully
        output_text = commander_window.telnet_tab.output.toPlainText()
        assert "❌ Failed to write to unknown file" in output_text

    def test_notification_does_not_interfere_with_command_output(self, commander_window):
        """Test that log write content display doesn't interfere with command response display."""
        # Clear telnet output before test
        commander_window.telnet_tab.output.clear()
        
        # Simulate command response
        command_response = "> print from fbc io structure 1620000\nFBC Output Data..."
        commander_window.telnet_tab.append_output(command_response)
        
        # Emit log write notification with actual content
        log_path = "test_logs/FBC/AP01m/AP01m_192-168-0-11_162.fbc"
        test_content = "> print from fbc io structure 1620000\n[2025-01-10] FBC Output Data"
        commander_window.log_writer.log_write_completed.emit(log_path, True, 50, 25, test_content)
        QApplication.processEvents()
        
        # Verify both command output and log write content are present
        output_text = commander_window.telnet_tab.output.toPlainText()
        assert "FBC Output Data" in output_text
        assert "📝 Writing to:" in output_text
        assert "AP01m_192-168-0-11_162.fbc" in output_text
        assert "Content written to" in output_text


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

