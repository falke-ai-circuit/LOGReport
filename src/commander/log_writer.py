"""
Log Writer Service

This service handles writing to log files and application logs.
"""

import os
import logging
from datetime import datetime
from typing import Optional

from commander.node_manager import NodeManager
from PyQt6.QtCore import QObject, pyqtSignal


class LogWriter(QObject):
    """
    Service for writing to log files and application logs.
    """
    log_write_completed = pyqtSignal(str, bool, int, int, str) # log_path, success, total_line_count, lines_written_by_command, content_written
    
    def __init__(self, node_manager: NodeManager, log_root: str = "logs", parent=None):
        """
        Initialize the LogWriter.
        
        Args:
            node_manager: NodeManager instance
            log_root: Root directory for logs
            parent: Parent QObject
        """
        super().__init__(parent)
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

    def write_to_log(self, content: str, log_type: str, node_name: Optional[str] = None, token=None):
        """
        Write content to the appropriate log file.
        
        Args:
            content: Content to write to log
            log_type: Type of log (FBC, LIS, LOG, RPC)
            node_name: Optional node name, if not provided uses active node
            token: Optional token with log_path attribute
        """
        if not content.strip():
            return
            
        # Check if token has a log_path attribute and use it directly
        if token and hasattr(token, 'log_path') and token.log_path:
            filepath = token.log_path
        else:
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
                # For node-specific logs, create subdirectory
                log_dir = os.path.join(log_dir, node_name)
                
            os.makedirs(log_dir, exist_ok=True)
            
            # Generate consistent filename without timestamp
            if log_type.upper() == "LOG":
                # LOG files use naming: {node_name}_{formatted_ip}.log
                if token and hasattr(token, 'ip_address'):
                    formatted_ip = token.ip_address.replace('.', '-')
                    filename = f"{node_name}_{formatted_ip}.log"
                else:
                    # Fallback to simple naming: {node_name}.log
                    filename = f"{node_name}.log"
            else:
                # For FBC, LIS, RPC files, if we have a token, use proper naming pattern
                # Otherwise, use simple naming like before
                if token and hasattr(token, 'token_id') and hasattr(token, 'ip_address'):
                    # Format IP address: 192.168.0.11 -> 192-168-0-11
                    formatted_ip = token.ip_address.replace('.', '-')
                    # Generate filename with identifiers based on log type
                    if log_type.upper() == "RPC":
                        # RPC pattern: {node_name}_{formatted_ip}_{token_id}.{extension}
                        filename = f"{node_name}_{formatted_ip}_{token.token_id}.{log_type.lower()}"
                    elif log_type.upper() == "FBC":
                        # FBC pattern: {node_name}_{formatted_ip}_{token_id}.{extension}
                        filename = f"{node_name}_{formatted_ip}_{token.token_id}.{log_type.lower()}"
                    else:
                        # LIS and other types: {node_name}_{formatted_ip}_{token_id}.{extension}
                        filename = f"{node_name}_{formatted_ip}_{token.token_id}.{log_type.lower()}"
                else:
                    # Fallback to simple naming: {node_name}.{extension}
                    filename = f"{node_name}.{log_type.lower()}"
                
            filepath = os.path.join(log_dir, filename)
        
        initial_line_count = self.get_file_line_count(filepath) if os.path.exists(filepath) else 0
        
        # Add timestamp to the content
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        timestamped_content = f"[{timestamp}] {content}"
        
        # Write content to file
        log_success = False
        try:
            with open(filepath, 'a', encoding='utf-8') as f:
                f.write(timestamped_content + '\n')
            log_success = True
        except Exception as e:
            self.write_to_app_log(f"Failed to write to {log_type} log: {str(e)}")
            logging.error(f"Error writing to log file {filepath}: {str(e)}") # Added logging for error
            raise
        finally:
            filepath_to_emit = filepath if log_success else "N/A"
            final_line_count = self.get_file_line_count(filepath) if log_success else 0
            lines_written_by_command = final_line_count - initial_line_count
            
            # Emit signal with the actual content being written (for display in Telnet tab)
            if token and hasattr(token, 'log_path'):
                self.log_write_completed.emit(token.log_path, log_success, final_line_count, lines_written_by_command, content)
            else:
                self.log_write_completed.emit("N/A", log_success, final_line_count, lines_written_by_command, content)

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

    def clear_log(self, token_id: str):
        """
        Clear the log file associated with a token.
        
        Args:
            token_id: ID of the token whose log should be cleared
        """
        # Find the token with the given ID
        token_found = False
        for node in self.node_manager.get_all_nodes():
            # In the real Node class, node.tokens is a dict where keys are token IDs
            # and values are lists of tokens with that ID
            if token_id in node.tokens:
                token_found = True
                token_list = node.tokens[token_id]
                for token in token_list:
                    # Check if the token has a log_path
                    log_path = getattr(token, 'log_path', None)
                    if log_path:
                        try:
                            # Clear the file by opening in write mode and writing nothing
                            with open(log_path, 'w', encoding='utf-8') as f:
                                f.write("")
                            self.write_to_app_log(f"Successfully cleared log file: {log_path}")
                        except Exception as e:
                            self.write_to_app_log(f"Failed to clear log file {log_path}: {str(e)}")
                    else:
                        self.write_to_app_log(f"Token {token_id} has no log_path attribute or it's empty")
        
        # If we didn't find the token, we don't write to app log as it's not necessarily an error
        # The test expects that we process all tokens with the same ID, so we don't return early
         
    def append_to_file(self, filepath: str, content: str, token=None):
        """
        Append content to a file.
        
        Args:
            filepath: Path to the file to append to
            content: Content to append to the file
        """
        if not content.strip():
            return
            
        try:
            with open(filepath, 'a', encoding='utf-8') as f:
                f.write(content + '\n')
            log_success = True
        except Exception as e:
            self.write_to_app_log(f"Failed to append to file {filepath}: {str(e)}")
            raise
        finally:
            filepath_to_emit = filepath if log_success else "N/A"
            line_count_to_emit = self.get_file_line_count(filepath) if log_success else 0
            
            if token and hasattr(token, 'log_path'):
                self.log_write_completed.emit(token.log_path, log_success, line_count_to_emit, line_count_to_emit) # Emit log_path, total_line_count, lines_written_by_command (for append, assume all lines are new)
            else:
                self.log_write_completed.emit("N/A", log_success, line_count_to_emit, line_count_to_emit) # Fallback if log_path not available

    def get_file_line_count(self, filepath: str) -> int:
        """
        Efficiently counts the number of lines in a given file.
        
        Args:
            filepath: Path to the file.
            
        Returns:
            The total number of lines in the file.
        """
        if not os.path.exists(filepath):
            logging.debug(f"get_file_line_count: File not found: {filepath}, returning 0 lines.")
            return 0
        
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                line_count = sum(1 for line in f)
                logging.debug(f"get_file_line_count: File: {filepath}, Line Count: {line_count}")
                return line_count
        except Exception as e:
            self.write_to_app_log(f"Error counting lines in file {filepath}: {str(e)}")
            logging.error(f"get_file_line_count: Error counting lines in file {filepath}: {str(e)}")
            return 0