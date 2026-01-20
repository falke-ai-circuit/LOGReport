"""
Clipboard Monitor Service

This service monitors the system clipboard for changes and handles automatic
clipboard-to-logfile functionality, content validation, and rate limiting.
"""

import re
import time
from typing import Optional, Callable
from PyQt5.QtCore import QObject, QTimer
from PyQt5.QtGui import QClipboard
from PyQt5.QtWidgets import QApplication

from commander.services.status_service import StatusService
from commander.log_writer import LogWriter
from commander.node_manager import NodeManager


class ClipboardMonitor(QObject):
    """
    Service that monitors clipboard changes and handles clipboard-to-log operations.
    
    Features:
    - Automatic clipboard monitoring
    - Content validation for FBC/LIS/LOG/RPC types
    - Rate limiting (5 operations/minute)
    - Integration with NodeManager for active log context
    """
    
    def __init__(self, node_manager: NodeManager, log_writer: LogWriter, 
                 status_service: StatusService):
        """
        Initialize the ClipboardMonitor.
        
        Args:
            node_manager: NodeManager instance for active log context
            log_writer: LogWriter instance for writing to log files
            status_service: StatusService instance for user notifications
        """
        super().__init__()
        self.node_manager = node_manager
        self.log_writer = log_writer
        self.status_service = status_service
        
        # Clipboard monitoring
        self.clipboard = QApplication.clipboard()
        self.clipboard.dataChanged.connect(self._on_clipboard_changed)
        self.last_clipboard_content = ""
        
        # Rate limiting
        self.operation_count = 0
        self.rate_limit_timer = QTimer()
        self.rate_limit_timer.timeout.connect(self._reset_operation_count)
        self.rate_limit_timer.start(60000)  # 1 minute
        
        # Content validation patterns
        self.patterns = [
            ('FBC', re.compile(r'^[A-Z0-9]{3,4}[mr]?\s+\d{2}:\d{2}:\d{2}\.\d{3}\s+.*')),
            ('LIS', re.compile(r'^LIS\s+\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z\s+.*')),
            ('RPC', re.compile(r'^[\{\[].*[\}\]]$|^<.*>.*</.*>$')),  # JSON or XML
        ]
        
        # Manual copy callback
        self.manual_copy_callback: Optional[Callable[[str], None]] = None

    def _on_clipboard_changed(self):
        """Handle clipboard content changes."""
        content = self.clipboard.text()
        
        # Skip if content hasn't changed or is empty
        if content == self.last_clipboard_content or not content.strip():
            return
            
        self.last_clipboard_content = content
        
        # Check if we should auto-copy to log
        active_log_file = getattr(self.node_manager, 'active_log_file', None)
        if active_log_file:
            self._auto_copy_to_log(content)

    def _auto_copy_to_log(self, content: str):
        """
        Automatically copy validated clipboard content to the active log file.
        
        Args:
            content: Clipboard content to validate and write
        """
        # Check rate limit
        if not self._check_rate_limit():
            self.status_service.show_message("Rate limit exceeded (5 operations/minute)")
            return
            
        # Validate content
        log_type = self._validate_content(content)
        if not log_type:
            return
            
        # Write to log file
        try:
            self.log_writer.write_to_log(content, log_type)
            self.status_service.show_message("Auto-copied to log")
            self.operation_count += 1
        except Exception as e:
            self.status_service.show_message(f"Failed to auto-copy: {str(e)}")

    def _validate_content(self, content: str) -> Optional[str]:
        """
        Validate clipboard content against log type patterns.
        
        Args:
            content: Content to validate
            
        Returns:
            Log type if valid, None otherwise
        """
        content = content.strip()
        if not content:
            return None
            
        for log_type, pattern in self.patterns:
            if pattern.match(content):
                return log_type

        # If no specific pattern matches, and content is not empty, it's a generic LOG
        
        
        
        return None

    def _check_rate_limit(self) -> bool:
        """
        Check if we're within the rate limit (5 operations/minute).
        
        Returns:
            True if within limit, False otherwise
        """
        return self.operation_count < 5

    def _reset_operation_count(self):
        """Reset the operation count every minute."""
        self.operation_count = 0

    def set_manual_copy_callback(self, callback: Callable[[str], None]):
        """
        Set callback for manual copy operations.
        
        Args:
            callback: Function to call when manual copy is requested
        """
        self.manual_copy_callback = callback

    def manual_copy_to_log(self, content: str):
        """
        Manually copy content to log with validation.
        
        Args:
            content: Content to copy to log
        """
        # Check rate limit
        if not self._check_rate_limit():
            self.status_service.show_message("Rate limit exceeded (5 operations/minute)")
            return
            
        # Validate content
        log_type = self._validate_content(content)
        if not log_type:
            self.status_service.show_message("Invalid format for log type")
            return
            
        # Execute callback if set
        if self.manual_copy_callback:
            self.manual_copy_callback(content)
            
        # Write to log file
        try:
            self.log_writer.write_to_log(content, log_type)
            self.status_service.show_message("Copied to log")
            self.operation_count += 1
        except Exception as e:
            self.status_service.show_message(f"Failed to copy: {str(e)}")

    def handle_vnc_text_selection(self, content: str):
        """
        Handle text selection in VNC viewer (Ctrl+C equivalent).
        
        Args:
            content: Selected text content
        """
        # Copy to system clipboard
        self.clipboard.setText(content)
        
        # Show notification
        self.status_service.show_message("Copied to clipboard")