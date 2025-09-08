"""
Log Writer Service

This service handles writing to log files and application logs.
"""

import os
import logging
from datetime import datetime
from typing import Optional

from commander.node_manager import NodeManager


class LogWriter:
    """
    Service for writing to log files and application logs.
    """
    
    def __init__(self, node_manager: NodeManager, log_root: str = "logs"):
        """
        Initialize the LogWriter.
        
        Args:
            node_manager: NodeManager instance
            log_root: Root directory for logs
        """
        self.node_manager = node_manager
        self.log_root = log_root
        
        # Ensure log directory exists
        os.makedirs(log_root, exist_ok=True)
        
        # Set up application logger
        self.app_logger = logging.getLogger("commander_app")
        self.app_logger.setLevel(logging.INFO)
        
        # Create file handler for application log
        app_log_path = os.path.join(log_root, "application.log")
        file_handler = logging.FileHandler(app_log_path)
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(formatter)
        self.app_logger.addHandler(file_handler)

    def write_to_log(self, content: str, log_type: str, node_name: Optional[str] = None):
        """
        Write content to the appropriate log file.
        
        Args:
            content: Content to write to log
            log_type: Type of log (FBC, LIS, LOG, RPC)
            node_name: Optional node name, if not provided uses active node
        """
        if not content.strip():
            return
            
        # Get node name
        if not node_name:
            active_node = getattr(self.node_manager, 'active_node', None)
            if active_node:
                node_name = active_node.name
            else:
                # If no active node, write to application log
                self.write_to_app_log(f"No active node, writing {log_type} content to app log: {content[:100]}...")
                return
                
        # Determine log directory and filename
        log_dir = os.path.join("test_logs", log_type)
        if node_name:
            log_dir = os.path.join(log_dir, node_name)
            
        os.makedirs(log_dir, exist_ok=True)
        
        # Generate filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{node_name}_{timestamp}.{log_type.lower()}"
        filepath = os.path.join(log_dir, filename)
        
        # Write content to file
        try:
            with open(filepath, 'a', encoding='utf-8') as f:
                f.write(content + '\n')
        except Exception as e:
            self.write_to_app_log(f"Failed to write to {log_type} log: {str(e)}")
            raise

    def write_to_app_log(self, message: str, level: int = logging.INFO):
        """
        Write message to application log.
        
        Args:
            message: Message to log
            level: Logging level
        """
        self.app_logger.log(level, message)

    def write_clipboard_content(self, content: str, log_type: str):
        """
        Write clipboard content to the appropriate log file.
        
        Args:
            content: Clipboard content to write
            log_type: Type of log (FBC, LIS, LOG, RPC)
        """
        # This method is specifically for clipboard content
        self.write_to_log(content, log_type)