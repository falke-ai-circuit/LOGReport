"""
Log Command Service - Handles batch operations for LOG files, such as opening all log files for a node sequentially.
"""

from PyQt6.QtCore import QObject, pyqtSignal
from PyQt6.QtGui import QDesktopServices
from PyQt6.QtCore import QUrl
import os

class LogCommandService(QObject):
    status_message = pyqtSignal(str)

    def __init__(self):
        super().__init__()

    def process_all_log_commands(self, log_paths: list):
        """
        Process all LOG commands by opening all log files sequentially.
        
        Args:
            log_paths: List of log file paths to open.
        """
        for i, path in enumerate(log_paths, 1):
            self.status_message.emit(f"Opening log {i}/{len(log_paths)}: {os.path.basename(path)}")
            QDesktopServices.openUrl(QUrl.fromLocalFile(path))