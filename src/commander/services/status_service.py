"""
Status Service

This service handles status messages and notifications to the user.
"""

from PyQt6.QtCore import QObject, pyqtSignal
from typing import Optional


class StatusService(QObject):
    """
    Service for displaying status messages to the user.
    """
    
    # Signal for status messages
    status_message = pyqtSignal(str)
    
    def __init__(self):
        """Initialize the StatusService."""
        super().__init__()
        
    def show_message(self, message: str, timeout: int = 5000):
        """
        Show a status message to the user.
        
        Args:
            message: Message to display
            timeout: Timeout in milliseconds (0 for no timeout)
        """
        self.status_message.emit(message)
        
    def show_error(self, message: str):
        """
        Show an error message to the user.
        
        Args:
            message: Error message to display
        """
        self.status_message.emit(f"Error: {message}")
        
    def show_warning(self, message: str):
        """
        Show a warning message to the user.
        
        Args:
            message: Warning message to display
        """
        self.status_message.emit(f"Warning: {message}")
        
    def show_info(self, message: str):
        """
        Show an info message to the user.
        
        Args:
            message: Info message to display
        """
        self.status_message.emit(f"Info: {message}")