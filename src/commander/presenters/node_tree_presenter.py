"""
Node Tree Presenter - Handles presentation logic for the node tree within the commander window
"""

from abc import ABC, abstractmethod
import logging
import os
import glob
from typing import Optional
from PyQt5.QtCore import QObject, pyqtSignal, Qt, QTimer
from PyQt5.QtWidgets import QTreeWidgetItem

from ..models import NodeToken
from ..node_manager import NodeManager
from ..session_manager import SessionManager
from ..log_writer import LogWriter
from ..command_queue import CommandQueue
from ..services.fbc_command_service import FbcCommandService
from ..services.rpc_command_service import RpcCommandService
from ..services.sequential_command_processor import SequentialCommandProcessor
from ..icons import get_node_online_icon, get_node_offline_icon, get_token_icon
import os
import re
import subprocess
from PyQt5.QtGui import QColor


class NodeTreePresenter(QObject):
    """
    Presenter for the Node Tree, handling presentation logic related to node tree operations
    """
    
    # Signals for UI updates
    status_message_signal = pyqtSignal(str, int)  # message, duration
    node_tree_updated_signal = pyqtSignal()  # emitted when node tree is updated
    log_file_selected_signal = pyqtSignal(str)  # emitted when log file is selected, carries filename
    command_generated_signal = pyqtSignal(str, str) # emitted when a command is generated, carries command string and token type
    switch_to_bstool_tab_signal = pyqtSignal()  # emitted when BsTool execution starts, to switch to BsTool tab
    switch_to_telnet_tab_signal = pyqtSignal()  # emitted when FBC/RPC command output is displayed, to switch to Telnet tab
    command_output_display_signal = pyqtSignal(str, str)  # emitted when command output needs to be displayed, carries output text and token type
    
    def __init__(self, view, node_manager: NodeManager, session_manager: SessionManager,
                 log_writer: LogWriter, command_queue: CommandQueue,
                 fbc_service: FbcCommandService, rpc_service: RpcCommandService,
                 context_menu_service, bstool_service, telnet_service=None, get_connection_info_callback=None):
        """
        Initialize the NodeTreePresenter.

        Args:
            view: The view component (UI) this presenter is associated with
            node_manager: Manager for node operations
            session_manager: Manager for session operations
            log_writer: Writer for log operations
            command_queue: Queue for command execution
            fbc_service: Service for FBC command operations
            rpc_service: Service for RPC command operations
            context_menu_service: Service for context menu operations
            bstool_service: Service for BsTool command operations
            telnet_service: Service for Telnet connection management (optional, for auto-connect)
        """
        super().__init__()
        self.view = view
        self.node_manager = node_manager
        self.session_manager = session_manager
        self.log_writer = log_writer
        self.command_queue = command_queue
        self.fbc_service = fbc_service
        self.rpc_service = rpc_service
        self.context_menu_service = context_menu_service
        self.bstool_service = bstool_service
        self.telnet_service = telnet_service  # For auto-connect functionality
        self.get_connection_info_callback = get_connection_info_callback  # Callback to get IP/port from telnet_tab
        
        # Initialize sequential processor
        self.sequential_processor = SequentialCommandProcessor(
            command_queue=command_queue,
            fbc_service=fbc_service,
            rpc_service=rpc_service,
            session_manager=session_manager,
            logging_service=log_writer,
            parent=self
        )
        
        # Connect sequential processor signals
        self.sequential_processor.status_message.connect(self.status_message_signal.emit)
        self.sequential_processor.execution_state_changed.connect(self.view.update_control_buttons)
        self.sequential_processor.current_file_processing.connect(self._highlight_current_file)
        
        # Connect view signals to presenter methods
        self.view.item_expanded.connect(self.handle_item_expanded)
        
        # Connect control button signals
        self.view.pause_clicked.connect(self._handle_pause)
        self.view.resume_clicked.connect(self._handle_resume)
        self.view.cancel_clicked.connect(self._handle_cancel)
        
        # Dictionary to track command and log write status for each node
        # Key: node_name, Value: {"command_success": Optional[bool], "log_success": Optional[bool], "line_count": Optional[int]}
        self.node_status = {}
        self.file_item_map = {} # Map log_path to QTreeWidgetItem
        
        # Workflow control flags for Print All Nodes
        self._workflow_paused = False
        self._workflow_cancelled = False
        
        # Connect signals from CommandQueue and LogWriter
        self.command_queue.command_completed.connect(self.handle_command_completed)
        self.log_writer.log_write_completed.connect(self.handle_log_write_completed)
        
        logging.debug("NodeTreePresenter initialized")
    
    def _report_error(self, message: str, exception: Optional[Exception] = None, duration: int = 5000):
        """
        Report an error to the UI.

        Args:
            message: Error message to display
            exception: Optional exception that occurred
            duration: Duration to display the message in milliseconds
        """
        error_msg = f"{message}: {str(exception)}" if exception else message
        logging.error(error_msg)
        self.status_message_signal.emit(error_msg, duration)
        
    def populate_node_tree(self):
        """Lazy-loading tree population - only loads top-level nodes initially"""
        self.view.clear()
        
        # Connect the item expanded signal if not already connected
        # This should be handled by the view, but we'll ensure it here
        self.node_tree_updated_signal.emit()
        
        for node in self.node_manager.get_all_nodes():
            node_item = self._create_node_item(node)
            if node_item:
                # Add placeholder child that will trigger loading when expanded
                placeholder = QTreeWidgetItem(["Click to load..."])
                placeholder.setData(0, Qt.ItemDataRole.UserRole, {"node": node.name, "type": "placeholder"})
                node_item.addChild(placeholder)
                self.view.add_top_level_item(node_item)
                logging.debug(f"Added node with placeholder: {node.name}")
    
    def _create_node_item(self, node):
        """Create node tree item with status icon"""
        node_item = QTreeWidgetItem([f"{node.name} ({node.ip_address})"])
        node_item.setIcon(0, get_node_online_icon() if node.status == "online"
                         else get_node_offline_icon())
        # Store node name in user data for later retrieval
        node_item.setData(0, Qt.ItemDataRole.UserRole, {
            "type": "node",
            "node_name": node.name
        })
        
        # Check log root
        log_root = self.node_manager.log_root
        if not log_root or not os.path.isdir(log_root):
            no_folder = QTreeWidgetItem(["Please set log root folder"])
            no_folder.setIcon(0, get_token_icon())  # Using token icon as warning icon
            node_item.addChild(no_folder)
            return node_item
            
        return node_item
        
    def handle_item_expanded(self, item):
        """Handle lazy loading of node children when expanded"""
        logging.debug(f"Item expanded: {item.text(0)}")
        data = item.data(0, Qt.ItemDataRole.UserRole)
        # Check if expanded item is a node with placeholder child
        if data and data.get("type") == "node":
            # Find placeholder child (if exists)
            for i in range(item.childCount()):
                child = item.child(i)
                child_data = child.data(0, Qt.ItemDataRole.UserRole)
                if child_data and child_data.get("type") == "placeholder":
                    item.removeChild(child)
                    logging.debug(f"Removed placeholder for node: {item.text(0)}")
                    self._load_node_children(item)
                    break  # Only remove first placeholder found
        else:
            logging.debug("Expanded item is not a node or has no placeholder")
    
    def _load_node_children(self, node_item):
        """Load actual children for a node"""
        # Get node name from stored user data
        data = node_item.data(0, Qt.ItemDataRole.UserRole)
        if not data or data.get("type") != "node":
            logging.debug("_load_node_children: Item is not a node")
            return
            
        node_name = data["node_name"]
        logging.debug(f"_load_node_children: Loading children for node: {node_name}")
        node = self.node_manager.get_node(node_name)
        if not node:
            logging.debug(f"_load_node_children: Node {node_name} not found")
            return
            
        added_sections = False
        
        # Create sections for each token type
        sections = [
            ("FBC", self._add_section("FBC", node, "FBC", ['.fbc', '.log', '.txt'])),
            ("RPC", self._add_section("RPC", node, "RPC", ['.rpc', '.log', '.txt'])),
            ("LOG", self._add_section("LOG", node, "LOG", ['.log'])),
            ("LIS", self._add_section("LIS", node, "LIS", ['.lis']))
        ]
        
        logging.debug(f"_load_node_children: Processing sections for node: {node.name}")
        for section_type, section_data in sections:
            logging.debug(f"_load_node_children: Processing {section_type} section")
            logging.debug(f"_load_node_children: Section data: items={len(section_data['items'])}")
            
            # Always create the section item even if no files are found
            section = QTreeWidgetItem([section_type])
            section.setIcon(0, get_token_icon() if section_type in ("FBC", "RPC")
                           else get_token_icon())
            # Store node name in section item's user data for reliable access
            section.setData(0, Qt.ItemDataRole.UserRole, {
                "node": node.name,
                "type": "section",
                "section_type": section_type
            })
            
            if section_data["items"]:
                logging.debug(f"_load_node_children: Adding {len(section_data['items'])} files to {section_type} section")
                for item in section_data["items"]:
                    section.addChild(item)
                logging.debug(f"_load_node_children: Added {section_type} section with {section_data['count']} items")
            else:
                # Add placeholder text if no files found
                placeholder = QTreeWidgetItem(["No files found"])
                placeholder.setIcon(0, get_token_icon())
                section.addChild(placeholder)
                logging.debug(f"_load_node_children: No items found for {section_type} section")
            
            node_item.addChild(section)
            added_sections = True
            logging.debug(f"_load_node_children: Added {section_type} subsection to node tree")
            
            # Aggregate colors for this section after all files are added
            if section_data["items"]:
                self._aggregate_section_color(section)
        
        if not added_sections:
            no_files = QTreeWidgetItem(["No files found for this node"])
            no_files.setIcon(0, get_token_icon())
            node_item.addChild(no_files)
            logging.debug(f"_load_node_children: No files found for node: {node_name}")
        else:
            # Aggregate node color after all sections are loaded
            self._aggregate_node_color(node_item)
        
    def _add_section(self, section_type, node, dir_name, extensions):
        """Add file items to section using glob patterns for efficiency"""
        # For LOG files, directory is <log_root>/LOG/<node.name>
        # For others, it's <log_root>/<dir_name>/<node.name>
        if section_type == "LOG":
            section_dir = os.path.join(self.node_manager.log_root, "LOG")
        else:
            section_dir = os.path.join(self.node_manager.log_root, dir_name, node.name)
            
        items = []
        
        if not os.path.isdir(section_dir):
            logging.debug(f"Directory not found: {section_dir}")
            return {"items": items, "count": 0}
            
        # Process files matching patterns
        for ext in extensions:
            if section_type == "LOG":
                pattern = os.path.join(section_dir, f"{node.name}_*.log")
                logging.debug(f"LOG SECTION DEBUG: Scanning directory: {section_dir}")
                logging.debug(f"LOG SECTION DEBUG: Using pattern: {pattern}")
            else:
                pattern = os.path.join(section_dir, f"{node.name}_*{ext}")
                
            logging.debug(f"Scanning for {section_type} files with pattern: {pattern}")
            files_found = glob.glob(pattern)
            logging.debug(f"Found {len(files_found)} files matching pattern")
            
            for file_path in files_found:
                filename = os.path.basename(file_path)
                token_id = self._extract_token_id(filename, node.name, section_type)
                
                logging.debug(f"LOG SECTION DEBUG: Processing file: {filename} | Extracted token: {token_id}")
                
                if not token_id and section_type != "LOG":
                    continue  # Skip invalid tokens except for LOG
                
                file_item = self._create_file_item(
                    filename, file_path, node,
                    token_id, section_type
                )
                items.append(file_item)
                logging.debug(f"Found {section_type} file: {filename}")
                
        logging.debug(f"Total {section_type} files found: {len(items)}")
        if section_type == "LOG" and len(items) == 0:
            logging.warning("No LOG files found! Possible causes:")
            logging.warning(f"1. Directory doesn't exist: {section_dir}")
            logging.warning(f"2. Pattern mismatch: {pattern}")
            logging.warning(f"3. Token extraction failed for existing files")
        return {"items": items, "count": len(items)}
        
    def _extract_token_id(self, filename, node_name, section_type):
        """Extract token ID from filename based on section type"""
        # These patterns should match the ones in CommanderWindow
        FBC_TOKEN_PATTERN = r"^([\w-]+)_[\d\.-]+_([\w-]+)\."
        RPC_TOKEN_PATTERN = r"_([\d\w-]+)\.[^.]*$"  # Matches last _token.extension
        LIS_TOKEN_PATTERN = r"^([\w-]+)_[\d-]+_(.+)\.lis$"
        
        if section_type == "LOG":
            # Use the filename without extension as token ID
            return os.path.splitext(filename)[0]
            
        try:
            import re
            if section_type == "FBC":
                match = re.match(FBC_TOKEN_PATTERN, filename)
                return match.group(2) if match and match.group(1) == node_name else None
            elif section_type == "RPC":
                match = re.search(RPC_TOKEN_PATTERN, filename)
                return match.group(1) if match else None
            elif section_type == "LIS":
                match = re.match(LIS_TOKEN_PATTERN, filename)
                return match.group(2) if match and match.group(1) == node_name else None
        except (IndexError, AttributeError):
            return None
            
        return None
        
    def _create_file_item(self, filename, file_path, node, token_id, token_type):
        """Create standardized file tree item"""
        file_item = QTreeWidgetItem([f" {filename}"])
        file_extension = os.path.splitext(file_path)[1][1:].upper()
        resolved_type = file_extension if file_extension in {'FBC','RPC','LOG','LIS'} else token_type
        
        normalized_file_path = os.path.normpath(file_path)
        file_item.setData(0, Qt.ItemDataRole.UserRole, {
            "log_path": normalized_file_path,
            "token": token_id,
            "token_type": resolved_type,
            "node": node.name,
            "ip_address": node.ip_address
        })
        file_item.setIcon(0, get_token_icon())
        self.file_item_map[normalized_file_path] = file_item
        logging.debug(f"_create_file_item: Added {normalized_file_path} to file_item_map. Current map size: {len(self.file_item_map)}")
        
        # Check file content on startup and apply persistent color
        self._check_file_color_on_startup(normalized_file_path, file_item)
        
        return file_item
        
    def _check_file_color_on_startup(self, file_path: str, file_item: QTreeWidgetItem):
        """
        Check file content on startup and apply persistent color.
        
        This method is called when files are loaded into the tree to apply colors
        based on existing file content, providing color persistence across application restarts.
        
        Args:
            file_path: The normalized path to the log file
            file_item: The QTreeWidgetItem representing the file in the tree
        """
        # Check if file exists
        if not os.path.exists(file_path):
            logging.debug(f"_check_file_color_on_startup: File does not exist yet: {file_path}")
            return  # File doesn't exist yet, no color to apply
        
        # Get line count from the file
        line_count = self.log_writer.get_file_line_count(file_path)
        
        # Apply color based on content only (no command execution status needed)
        if line_count == 0:
            color = "red"  # No content
        elif line_count < 10:
            color = "yellow"  # Minimal content
        else:
            color = "green"  # Sufficient content
        
        self.view.update_node_color(file_item, color)
        logging.debug(f"_check_file_color_on_startup: Applied {color} color to {file_path} ({line_count} lines)")
        
    def handle_command_completed(self, command: str, result: str, success: bool, token: NodeToken):
        """
        Handle the command_completed signal from CommandQueue.
        
        Args:
            command: The command that was executed
            result: The result of the command
            success: True if the command was successful, False otherwise
            token: The NodeToken associated with the command
        """
        log_path = token.log_path # Use log_path from token
        if log_path not in self.node_status:
            self.node_status[log_path] = {"command_success": None, "log_success": None, "line_count": None}
        self.node_status[log_path]["command_success"] = success
        logging.debug(f"handle_command_completed: Log Path: {log_path}, Command Success: {success}, Token Type: {token.token_type}")
        self._check_and_update_node_color(log_path)
        
        # Emit signal to display command output in appropriate tab (Telnet for FBC/RPC, BsTool already handles LOG)
        # This ensures sequential execution shows output just like manual execution
        if result and token.token_type in ["FBC", "RPC"]:
            logging.debug(f"handle_command_completed: Emitting command_output_display_signal for {token.token_type} token with result length: {len(result)}")
            self.command_output_display_signal.emit(result, token.token_type)
            
            # FIX: Switch to Telnet tab during sequential execution to show FBC/RPC output as it happens
            # This allows users to see each command's output in real-time
            self.switch_to_telnet_tab_signal.emit()
            logging.debug("handle_command_completed: Emitted switch_to_telnet_tab_signal for FBC/RPC output")
        
        elif result and token.token_type == "LOG":
            # For LOG tokens (BsTool), switch to BsTool tab to show output
            logging.debug(f"handle_command_completed: LOG token completed, switching to BsTool tab")
            self.switch_to_bstool_tab_signal.emit()
        
        # Check if we're in sequential node processing mode and queue is idle
        # This triggers processing of the next node when all commands for current node are done
        if hasattr(self, '_nodes_to_process') and self._nodes_to_process:
            logging.debug(f"handle_command_completed: In sequential mode, scheduling continuation check (nodes remaining: {len(self._nodes_to_process) - self._current_node_index})")
            # Use QTimer to check processing state after a short delay
            # This ensures the command_queue has time to update its _is_processing flag
            from PyQt5.QtCore import QTimer
            QTimer.singleShot(100, self._check_sequential_processing_continuation)
        else:
            logging.debug(f"handle_command_completed: NOT in sequential mode (has _nodes_to_process: {hasattr(self, '_nodes_to_process')})")
            
    def handle_log_write_completed(self, log_path: str, success: bool, total_line_count: int, lines_written_by_command: int, content_written: str):
        """
        Handle the log_write_completed signal from LogWriter.
        
        Args:
            log_path: The path to the log file
            success: True if the log write was successful, False otherwise
            total_line_count: The total number of lines in the log file
            lines_written_by_command: The number of lines written by the current command
            content_written: The actual content that was written (not used for color logic)
        """
        if log_path not in self.node_status:
            self.node_status[log_path] = {"command_success": None, "log_success": None, "total_line_count": None, "lines_written_by_command": None}
        
        self.node_status[log_path]["log_success"] = success
        self.node_status[log_path]["total_line_count"] = total_line_count
        self.node_status[log_path]["lines_written_by_command"] = lines_written_by_command
        logging.debug(f"handle_log_write_completed: Log Path: {log_path}, Log Success: {success}, Total Line Count: {total_line_count}, Lines Written by Command: {lines_written_by_command}")
        self._check_and_update_node_color(log_path)
        
        # Trigger auto-expansion and highlighting for this file
        # Extract node name and token from file_item_map
        normalized_path = os.path.normpath(log_path)
        file_item = self.file_item_map.get(normalized_path)
        if file_item:
            item_data = file_item.data(0, Qt.ItemDataRole.UserRole)
            if item_data:
                node_name = item_data.get("node")
                token_id = item_data.get("token")
                token_type = item_data.get("token_type")
                ip_address = item_data.get("ip_address")
                
                # Create a minimal token object for highlighting
                if node_name and token_id and token_type:
                    # Create NodeToken-like object with necessary attributes
                    class TokenInfo:
                        def __init__(self, token_id, token_type, log_path):
                            self.token_id = token_id
                            self.token_type = token_type
                            self.log_path = log_path
                    
                    token_info = TokenInfo(token_id, token_type, log_path)
                    
                    # Emit signal to trigger auto-expansion and highlighting
                    self._highlight_current_file(node_name, token_info, log_path)
                    logging.debug(f"handle_log_write_completed: Triggered auto-expansion for {log_path}")
        else:
            logging.debug(f"handle_log_write_completed: File item not found in map for {normalized_path}")
    
    def _check_and_update_node_color(self, log_path: str):
        """
        Check if both command and log write were successful for a node and update its color.
        Updates BOTH text color (content-based) AND icon color (execution-based).
        
        Args:
            log_path: The log_path of the file item to check and update
        """
        if log_path not in self.node_status:
            self.node_status[log_path] = {"command_success": None, "log_success": None, "total_line_count": None, "lines_written_by_command": None}
        command_success = self.node_status[log_path].get("command_success")
        log_success = self.node_status[log_path].get("log_success")
        total_line_count = self.node_status[log_path].get("total_line_count")
        lines_written_by_command = self.node_status[log_path].get("lines_written_by_command")
        logging.debug(f"_check_and_update_node_color: Log Path: {log_path}, Command Success: {command_success}, Log Success: {log_success}, Total Line Count: {total_line_count}, Lines Written by Command: {lines_written_by_command}")

        # Only update color if both statuses have been set (are not None)
        if command_success is not None and log_success is not None:
            # Use lines_written_by_command for FBC coloring logic
            # For other types, we might still use total_line_count or a different metric
            # For now, apply this logic to FBC files as per user request
            file_item_data = self.file_item_map.get(os.path.normpath(log_path))
            token_type = file_item_data.data(0, Qt.ItemDataRole.UserRole).get("token_type") if file_item_data else None

            normalized_log_path = os.path.normpath(log_path)
            file_item = self.file_item_map.get(normalized_log_path)
            if file_item:
                # Determine icon color based on COMMAND EXECUTION STATUS
                if command_success and log_success:
                    if token_type in ["FBC", "RPC"]: # Apply to both FBC and RPC
                        if lines_written_by_command is None or lines_written_by_command == 0:
                            icon_color = "red"
                        elif lines_written_by_command < 10:
                            icon_color = "yellow"
                        else: # lines_written_by_command >= 10
                            icon_color = "green"
                    else: # LOG and other file types - check actual file content
                        # For LOG files, read actual file content to determine icon color
                        # This ensures we get the correct count after BsTool finishes writing
                        if os.path.exists(normalized_log_path):
                            actual_line_count = self.log_writer.get_file_line_count(normalized_log_path)
                            if actual_line_count == 0:
                                icon_color = "red"
                            elif actual_line_count < 10:
                                icon_color = "yellow"
                            else: # actual_line_count >= 10
                                icon_color = "green"
                        else:
                            # File doesn't exist yet, use total_line_count as fallback
                            if total_line_count is None or total_line_count == 0:
                                icon_color = "red"
                            elif total_line_count < 10:
                                icon_color = "yellow"
                            else:
                                icon_color = "green"
                else:
                    icon_color = "red"
                
                logging.debug(f"_check_and_update_node_color: Set ICON to {icon_color} for {normalized_log_path}")
                
                # Update rectangle icon color (command execution status)
                self.view.update_node_icon(file_item, icon_color)
                
                # Store icon_color in item data for aggregation
                file_item_data = file_item.data(0, Qt.ItemDataRole.UserRole)
                if file_item_data:
                    file_item_data["icon_color"] = icon_color
                    file_item.setData(0, Qt.ItemDataRole.UserRole, file_item_data)
                
                # Update TEXT color based on ACTUAL FILE CONTENT (independent from icon color)
                # Check the file and count lines to determine text color
                if os.path.exists(normalized_log_path):
                    content_line_count = self.log_writer.get_file_line_count(normalized_log_path)
                    
                    # Determine text color based on content
                    if content_line_count == 0:
                        text_color = "red"  # No content
                    elif content_line_count < 10:
                        text_color = "yellow"  # Minimal content
                    else:
                        text_color = "green"  # Sufficient content
                    
                    self.view.update_node_color(file_item, text_color)
                    logging.debug(f"_check_and_update_node_color: Set TEXT to {text_color} for {os.path.basename(normalized_log_path)} ({content_line_count} lines)")
                else:
                    logging.debug(f"_check_and_update_node_color: File does not exist yet, skipping text color update")
            else:
                logging.warning(f"_check_and_update_node_color: file_item not found for log_path: {normalized_log_path}")

            # Reset status after update
            self.node_status[log_path] = {"command_success": None, "log_success": None, "total_line_count": None, "lines_written_by_command": None}
            
            # Trigger hierarchical icon color aggregation (file → section → node)
            if file_item:
                self._aggregate_hierarchical_colors(file_item)
    
    def _aggregate_hierarchical_colors(self, file_item):
        """
        Aggregate colors hierarchically from file → section → node.
        
        When a file color changes, check if all sibling files in the section have the same color,
        then update the section. If all sections in a node have the same color, update the node.
        
        Args:
            file_item: The file item that just had its color updated
        """
        # Get the section (parent) of this file item
        section_item = file_item.parent()
        if not section_item:
            return
            
        # Aggregate section color from all child files
        self._aggregate_section_color(section_item)
        
        # Get the node (parent of section)
        node_item = section_item.parent()
        if not node_item:
            return
            
        # Aggregate node color from all child sections
        self._aggregate_node_color(node_item)
    
    def _aggregate_section_color(self, section_item):
        """
        Aggregate ICON color for a section (FBC/RPC/LOG/LIS) based on all child file ICON colors.
        This affects rectangle icons, not text color.
        
        Logic:
        - All files green → section green
        - Any file red → section red
        - All files yellow or mix of yellow/green → section yellow
        - No files or placeholder → no color change
        
        Args:
            section_item: The section QTreeWidgetItem
        """
        child_count = section_item.childCount()
        if child_count == 0:
            return
        
        # Check if the only child is a placeholder (e.g., "No files found")
        if child_count == 1:
            first_child = section_item.child(0)
            child_data = first_child.data(0, Qt.ItemDataRole.UserRole)
            if not child_data or "log_path" not in child_data:
                return
        
        # Collect ICON colors from all child files
        # We need to extract icon color, not text color (foreground)
        # Since QIcon doesn't expose color directly, we'll track icon colors via a separate mechanism
        # For now, we'll use a workaround: store icon_color in item data
        colors = []
        for i in range(child_count):
            child = section_item.child(i)
            child_data = child.data(0, Qt.ItemDataRole.UserRole)
            if child_data and "log_path" in child_data:
                # Get icon_color from UserRole data (we'll need to store it there)
                icon_color = child_data.get("icon_color")
                if icon_color:
                    colors.append(QColor(icon_color).name())
        
        if not colors:
            return
        
        # Determine aggregated color
        unique_colors = set(colors)
        green_hex = QColor("green").name()
        yellow_hex = QColor("yellow").name()
        red_hex = QColor("red").name()
        
        if red_hex in unique_colors:
            # Any red file makes the section red
            aggregated_color = "red"
        elif unique_colors == {green_hex}:
            # All files green
            aggregated_color = "green"
        elif unique_colors == {yellow_hex} or unique_colors == {green_hex, yellow_hex}:
            # All yellow or mix of yellow/green
            aggregated_color = "yellow"
        else:
            # Default to yellow for mixed states
            aggregated_color = "yellow"
        
        # Update section ICON color
        self.view.update_node_icon(section_item, aggregated_color)
        
        # Store icon color in section data for node aggregation
        section_data = section_item.data(0, Qt.ItemDataRole.UserRole)
        if section_data:
            section_data["icon_color"] = aggregated_color
            section_item.setData(0, Qt.ItemDataRole.UserRole, section_data)
    
    def _aggregate_node_color(self, node_item):
        """
        Aggregate ICON color for a node based on all child section ICON colors.
        This affects rectangle icons (circles for nodes), not text color.
        
        Logic:
        - All sections green → node green
        - Any section red → node red
        - All sections yellow or mix of yellow/green → node yellow
        - No sections → no color change
        
        Args:
            node_item: The node QTreeWidgetItem
        """
        child_count = node_item.childCount()
        if child_count == 0:
            return
        
        # Collect ICON colors from all child sections
        colors = []
        for i in range(child_count):
            child = node_item.child(i)
            child_data = child.data(0, Qt.ItemDataRole.UserRole)
            # Only aggregate from section items (FBC, RPC, LOG, LIS)
            if child_data and child_data.get("type") == "section":
                icon_color = child_data.get("icon_color")
                if icon_color:
                    colors.append(QColor(icon_color).name())
        
        if not colors:
            return
        
        # Determine aggregated color (same logic as sections)
        unique_colors = set(colors)
        green_hex = QColor("green").name()
        yellow_hex = QColor("yellow").name()
        red_hex = QColor("red").name()
        
        if red_hex in unique_colors:
            # Any red section makes the node red
            aggregated_color = "red"
        elif unique_colors == {green_hex}:
            # All sections green
            aggregated_color = "green"
        elif unique_colors == {yellow_hex} or unique_colors == {green_hex, yellow_hex}:
            # All yellow or mix of yellow/green
            aggregated_color = "yellow"
        else:
            # Default to yellow for mixed states
            aggregated_color = "yellow"
        
        # Update node ICON color
        # For nodes, we might want to keep the circle icon or create colored circle icons
        self.view.update_node_icon(node_item, aggregated_color)
        
        # Store icon color in node data
        node_data = node_item.data(0, Qt.ItemDataRole.UserRole)
        if node_data:
            node_data["icon_color"] = aggregated_color
            node_item.setData(0, Qt.ItemDataRole.UserRole, node_data)
        
        self.view.update_node_color(node_item, aggregated_color)
                
    def set_log_root_folder(self, folder_path):
        """Set the root folder for log files"""
        # This method is called by the view when the user selects a folder
        if folder_path:
            self.node_manager.set_log_root(folder_path)
            self.node_manager.scan_log_files()
            self.populate_node_tree()
            self.status_message_signal.emit("Log root folder set successfully", 3000)
        
    def load_configuration(self, file_path):
        """Load node configuration from selected file"""
        # This method is called by the view when the user selects a configuration file
        if file_path:
            self.node_manager.set_config_path(file_path)
            if self.node_manager.load_configuration():
                self.node_manager.scan_log_files()
                self.populate_node_tree()
                self.status_message_signal.emit("Configuration loaded successfully", 3000)
            else:
                self.status_message_signal.emit("Error loading node configuration", 5000)
        
    def show_context_menu(self, position):
        """
        Show context menu for the selected item in the node tree.

        Args:
            position: Position where the context menu should be shown
        """
        # Get the item at the mouse position
        item = self.view.itemAt(position)
        if not item:
            return
            
        # Get item data
        item_data = item.data(0, Qt.ItemDataRole.UserRole)
        if not item_data:
            return
            
        # Create menu
        from PyQt5.QtWidgets import QMenu
        menu = QMenu()
        
        # Use context menu service to populate and show menu
        global_pos = self.view.viewport().mapToGlobal(position)
        self.context_menu_service.show_context_menu(menu, item_data, global_pos)
        
    def process_all_fbc_subgroup_commands(self, item):
        """
        Process all FBC commands for a subgroup.

        Args:
            item: The tree item representing the subgroup
        """
        if not item:
            self._report_error("No item selected for FBC subgroup processing")
            return
            
        # Get node name from item hierarchy
        section_item = item.parent()
        if not section_item:
            self._report_error("FBC subgroup has no parent section")
            return
        node_item = section_item.parent()
        if not node_item:
            self._report_error(f"Section {section_item.text(0)} has no parent node")
            return
        node_name = node_item.text(0).split(' ', 1)[0].strip()

        # Get tokens from item if available
        tokens = getattr(item, 'tokens', None)
        if not tokens:
            # Fallback to getting all FBC tokens from node
            node = self.node_manager.get_node(node_name)
            if not node:
                self.status_message_signal.emit(f"Node {node_name} not found", 3000)
                return
                
            # Find all FBC tokens in the node
            # node.tokens is Dict[str, List[NodeToken]], so we need to flatten the lists
            all_tokens = []
            for token_list in node.tokens.values():
                # Ensure token_list is actually a list before extending
                if isinstance(token_list, list):
                    # Only add NodeToken objects to all_tokens
                    for token in token_list:
                        if isinstance(token, NodeToken):
                            all_tokens.append(token)
                else:
                    # If it's not a list but is a NodeToken, add it
                    if isinstance(token_list, NodeToken):
                        all_tokens.append(token_list)
            tokens = [t for t in all_tokens if t.token_type == "FBC"]
        if not tokens:
            self.status_message_signal.emit(f"No FBC tokens found in node {node_name}", 3000)
            return
            
        logging.info(f"Processing {len(tokens)} FBC tokens in node {node_name}...")
        self.status_message_signal.emit(f"Processing {len(tokens)} FBC tokens in node {node_name}...", 0)
        
        # Process each FBC token
        for token in tokens:
            # Pass active telnet client for reuse if available
            telnet_client = getattr(self, 'active_telnet_client', None)
            self.fbc_service.queue_fieldbus_command(node_name, token.token_id, telnet_client)
            # Initialize node status for this node
            self.node_status[node_name] = {"command_success": False, "log_success": False}
        # Start processing the queue
        self.command_queue.start_processing()
        self.status_message_signal.emit(f"Queued {len(tokens)} commands for node {node_name}", 3000)
            
    def process_all_rpc_subgroup_commands(self, item):
        """
        Process all RPC commands for a subgroup.

        Args:
            item: The tree item representing the subgroup
        """
        if not item:
            self._report_error("No item selected for RPC subgroup processing")
            return
            
        # Get node name from item hierarchy
        section_item = item.parent()
        if not section_item:
            self._report_error("RPC subgroup has no parent section")
            return
        node_item = section_item.parent()
        if not node_item:
            self._report_error(f"Section {section_item.text(0)} has no parent node")
            return
        node_name = node_item.text(0).split(' ', 1)[0].strip()

        # Get tokens from item if available
        tokens = getattr(item, 'tokens', None)
        if not tokens:
            # Fallback to getting all RPC tokens from node
            node = self.node_manager.get_node(node_name)
            if not node:
                self.status_message_signal.emit(f"Node {node_name} not found", 3000)
                return
                
            # Find all RPC tokens in the node
            # node.tokens is Dict[str, List[NodeToken]], so we need to flatten the lists
            all_tokens = []
            for token_list in node.tokens.values():
                # Ensure token_list is actually a list before extending
                if isinstance(token_list, list):
                    # Only add NodeToken objects to all_tokens
                    for token in token_list:
                        if isinstance(token, NodeToken):
                            all_tokens.append(token)
                else:
                    # If it's not a list but is a NodeToken, add it
                    if isinstance(token_list, NodeToken):
                        all_tokens.append(token_list)
            tokens = [t for t in all_tokens if t.token_type == "RPC"]
        if not tokens:
            self.status_message_signal.emit(f"No RPC tokens found in node {node_name}", 3000)
            return
            
        logging.info(f"Processing {len(tokens)} RPC tokens in node {node_name}...")
        self.status_message_signal.emit(f"Processing {len(tokens)} RPC tokens in node {node_name}...", 0)
        
        # Pass active telnet client for reuse if available
        telnet_client = getattr(self, 'active_telnet_client', None)
        
        # Queue commands for all RPC tokens using service method
        for token in tokens:
            self.rpc_service.queue_rpc_command(node_name, token.token_id, "print", telnet_client)
            
        self.status_message_signal.emit(f"Queued {len(tokens)} commands for node {node_name}", 3000)
    
    def process_all_log_subgroup_commands(self, item):
        """
        Process all LOG subgroup commands by printing/displaying all LOG files.
        This method mirrors process_all_fbc_subgroup_commands and process_all_rpc_subgroup_commands
        but for LOG files (no BsTool execution, just display).

        Args:
            item: The tree item representing the LOG subgroup
        """
        if not item:
            self._report_error("No item selected for LOG subgroup processing")
            return
        
        # If item is a MockItem (from ContextMenuService), its data is directly accessible
        if hasattr(item, 'data') and isinstance(item.data, dict):
            item_data = item.data
        else:
            # Assume it's a QTreeWidgetItem and extract data
            item_data = item.data(0, Qt.ItemDataRole.UserRole)
        
        if not item_data or item_data.get("type") != "section":
            self._report_error("Selected item is not a subgroup section")
            return

        section_type = item_data.get("section_type")
        node_name = item_data.get("node")

        if not node_name or section_type != "LOG":
            self._report_error("Could not determine node or LOG section type")
            return
        
        logging.info(f"Processing LOG subgroup for node {node_name}...")
        self.status_message_signal.emit(f"Printing all LOG files for node {node_name}...", 0)
        
        # Get tokens from item_data or from node
        tokens = item_data.get("tokens", [])
        
        # If no tokens in item_data, retrieve from node
        if not tokens:
            node = self.node_manager.get_node(node_name)
            if not node:
                self._report_error(f"Node {node_name} not found")
                return
                
            # Find all LOG tokens in the node
            all_tokens = []
            for token_list in node.tokens.values():
                if isinstance(token_list, list):
                    for token in token_list:
                        if isinstance(token, NodeToken):
                            all_tokens.append(token)
                else:
                    if isinstance(token_list, NodeToken):
                        all_tokens.append(token_list)
            tokens = [t for t in all_tokens if t.token_type == "LOG"]
        
        if not tokens:
            self.status_message_signal.emit(f"No LOG files found in node {node_name}", 3000)
            return
            
        logging.info(f"Printing {len(tokens)} LOG files for node {node_name}...")
        
        # Process all LOG tokens by emitting log file selected signal (display)
        printed_count = 0
        for token in tokens:
            if hasattr(token, 'log_path') and token.log_path:
                try:
                    filename = os.path.basename(token.log_path)
                    self.log_file_selected_signal.emit(filename)
                    printed_count += 1
                    logging.debug(f"Printed LOG file: {filename}")
                except Exception as e:
                    logging.error(f"Error printing LOG file {token.log_path}: {str(e)}")
            else:
                logging.warning(f"Token object {token} does not have a valid log_path")
        
        self.status_message_signal.emit(
            f"Printed {printed_count} LOG files for node {node_name}", 
            3000
        )
    
    def process_node_print_commands(self, node_name: str):
        """
        Execute only PRINT commands hierarchically for a node.
        This method orchestrates Print-based subgroup commands:
        - Phase 1: Print All FBC Tokens
        - Phase 2: Print All RPC Tokens
        - Phase 3: Execute BsTool for LOG (with -errlog parameter)

        Args:
            node_name: Name of the node to process print commands for
        """
        logging.info(f"Starting print command execution for node {node_name}...")
        self.status_message_signal.emit(f"Starting print command execution for node {node_name}...", 0)
        
        try:
            # Get the node
            node = self.node_manager.get_node(node_name)
            if not node:
                self._report_error(f"Node {node_name} not found for print command processing")
                return
            
            # Phase 1: Execute all FBC print commands
            fbc_tokens = self._get_tokens_for_node(node, "FBC")
            if fbc_tokens:
                logging.info(f"Phase 1: Processing {len(fbc_tokens)} FBC tokens for node {node_name}")
                self.status_message_signal.emit(f"Phase 1/3: Printing {len(fbc_tokens)} FBC tokens...", 0)
                
                telnet_client = getattr(self, 'active_telnet_client', None)
                for token in fbc_tokens:
                    self.fbc_service.queue_fieldbus_command(node_name, token.token_id, telnet_client)
                    self.node_status[node_name] = {"command_success": False, "log_success": False}
                
                # Start processing FBC commands
                self.command_queue.start_processing()
            else:
                logging.info(f"No FBC tokens found for node {node_name}")
            
            # Phase 2: Execute all RPC print commands
            rpc_tokens = self._get_tokens_for_node(node, "RPC")
            if rpc_tokens:
                logging.info(f"Phase 2: Processing {len(rpc_tokens)} RPC tokens for node {node_name}")
                self.status_message_signal.emit(f"Phase 2/3: Printing {len(rpc_tokens)} RPC tokens...", 0)
                
                telnet_client = getattr(self, 'active_telnet_client', None)
                for token in rpc_tokens:
                    self.rpc_service.queue_rpc_command(node_name, token.token_id, "print", telnet_client)
            else:
                logging.info(f"No RPC tokens found for node {node_name}")
            
            # Phase 3: Execute BsTool for LOG files (with -errlog parameter)
            log_tokens = self._get_tokens_for_node(node, "LOG")
            logging.debug(f"Phase 3 CHECK: Retrieved {len(log_tokens) if log_tokens else 0} LOG tokens for node {node_name}")
            
            if log_tokens:
                # Strip 'm' or 'r' suffix from node name for -errlog parameter
                errlog_node_name = self._strip_node_suffix(node_name)
                
                # Switch to BsTool tab to show output
                self.switch_to_bstool_tab_signal.emit()
                logging.debug("Phase 3: Emitted signal to switch to BsTool tab")
                
                # Use the first LOG token's log_path for output destination
                log_token = log_tokens[0]
                log_file_path = log_token.log_path if hasattr(log_token, 'log_path') else None
                
                if log_file_path:
                    logging.debug(f"Phase 3: LOG file path from token: {log_file_path}")
                    # NOTE: DO NOT highlight here - it causes premature visual jump during sequential execution
                    # Highlighting now moved to _check_sequential_processing_continuation() after queue is truly idle
                    # self._highlight_current_file(node_name, log_token, log_file_path)  # REMOVED - timing issue fix
                    
                    bstool_command_args = f"-errlog {errlog_node_name}"
                    
                    # NEW APPROACH: Queue BsTool command through CommandQueue (same as FBC/RPC)
                    # This ensures proper synchronization - BsTool will execute sequentially with other commands
                    logging.info(f"Phase 3: Queuing BsTool command for node {node_name} through CommandQueue")
                    self.status_message_signal.emit(f"Phase 3/3: BsTool -errlog {errlog_node_name}...", 0)
                    self.bstool_service.queue_bstool_command(
                        log_file_path=log_file_path,
                        bstool_command_args=bstool_command_args,
                        token=log_token
                    )
                else:
                    logging.warning(f"Phase 3: LOG token has no log_path attribute, cannot execute BsTool")
            else:
                logging.info(f"Phase 3: No LOG tokens found for node {node_name}, skipping BsTool execution")
            
            # Completion message
            total_commands = len(fbc_tokens) + len(rpc_tokens)
            if log_tokens:
                total_commands += 1  # BsTool command counts as one command
            
            self.status_message_signal.emit(
                f"Print command execution complete for {node_name}: {total_commands} commands processed", 
                5000
            )
            logging.info(f"Print command execution completed for node {node_name}: {total_commands} total commands")
            
        except Exception as e:
            self._report_error(f"Error in print command execution for node {node_name}", e)
    
    def process_all_nodes_print_commands(self):
        """
        Execute print commands for all nodes sequentially.
        Calls process_node_print_commands() for each node, just like right-click.
        Monitors command_queue.is_processing to chain node processing.
        Automatically establishes Telnet debugger connection if not connected.
        """
        logging.info("Starting print command execution for ALL nodes...")
        self.status_message_signal.emit("Starting print command execution for ALL nodes...", 0)
        
        try:
            # CRITICAL: Check/establish Telnet debugger connection before starting workflow
            # Uses same retry logic (2 attempts, 10s delay) as manual Connect button
            # Includes system mode verification (%s prompt) and automatic "systemmode" command
            if self.telnet_service:
                logging.info("Checking Telnet debugger connection before Print All Nodes execution...")
                
                # Initialize debugger IP/port from telnet_tab UI if not already set
                # This handles first auto-connect before any manual connection
                if not self.telnet_service.debugger_ip_address and self.get_connection_info_callback:
                    ip, port = self.get_connection_info_callback()
                    if ip and port:
                        logging.info(f"NodeTreePresenter: Initializing debugger IP/port from UI: {ip}:{port}")
                        self.telnet_service.debugger_ip_address = ip
                        self.telnet_service.debugger_port = port
                
                if not self.telnet_service._ensure_debugger_connection():
                    error_msg = "Failed to establish Telnet debugger connection. Please connect manually in Telnet tab."
                    logging.error(f"Print All Nodes aborted: {error_msg}")
                    self.status_message_signal.emit(error_msg, 8000)
                    # Don't enable any buttons - workflow cannot start without connection
                    return
                logging.info("Telnet debugger connection verified, proceeding with Print All Nodes workflow")
            else:
                logging.warning("TelnetService not available in NodeTreePresenter, skipping connection check")
            
            # Reset workflow control flags at the start
            self._workflow_paused = False
            self._workflow_cancelled = False
            
            # Enable pause and cancel buttons when workflow starts (RUNNING state)
            self.view.pause_btn.setEnabled(True)
            self.view.resume_btn.setEnabled(False)
            self.view.cancel_btn.setEnabled(True)
            logging.debug("Print All Nodes: Enabled pause and cancel buttons")
            
            # CRITICAL: Ensure log files are scanned to populate node.tokens with LOG tokens
            if hasattr(self.node_manager, 'log_root') and self.node_manager.log_root:
                logging.info("Scanning log files to ensure LOG tokens are available...")
                self.node_manager.scan_log_files()
                logging.info("Log file scan complete")
            
            # FIRST: Expand entire tree to show all files and their status
            self._expand_entire_tree()
            
            # Get all nodes
            all_nodes = self.node_manager.get_all_nodes()
            
            if not all_nodes:
                self._report_error("No nodes available to process")
                # Disable all buttons on error
                self.view.pause_btn.setEnabled(False)
                self.view.resume_btn.setEnabled(False)
                self.view.cancel_btn.setEnabled(False)
                return
            
            # Store nodes to process
            self._nodes_to_process = list(all_nodes)
            self._current_node_index = 0
            self._total_nodes_to_process = len(self._nodes_to_process)
            
            # Start processing first node
            # Subsequent nodes will be triggered by _check_sequential_processing_continuation
            # called from handle_command_completed when queue becomes idle
            self._process_next_node_in_sequence()
            
        except Exception as e:
            self._report_error("Error in bulk print command execution for all nodes", e)
            # Disable all buttons on error
            self.view.pause_btn.setEnabled(False)
            self.view.resume_btn.setEnabled(False)
            self.view.cancel_btn.setEnabled(False)
    
    def _process_next_node_in_sequence(self):
        """
        Process the next node in the all-nodes sequence.
        Called after each node's command queue finishes processing.
        Executes process_node_print_commands() for each node sequentially.
        """
        # Check if workflow was cancelled
        if self._workflow_cancelled:
            logging.info("NodeTreePresenter: Workflow cancelled, finishing processing")
            self.status_message_signal.emit("Print All Nodes workflow cancelled", 5000)
            # Clear processing flags
            self._nodes_to_process = []
            self._workflow_cancelled = False  # Reset for next run
            self._workflow_paused = False  # Reset for next run
            # Disable all buttons on cancel (IDLE state)
            self.view.pause_btn.setEnabled(False)
            self.view.resume_btn.setEnabled(False)
            self.view.cancel_btn.setEnabled(False)
            logging.debug("Print All Nodes: Disabled all buttons (workflow cancelled)")
            return
        
        # Check if workflow is paused
        if self._workflow_paused:
            logging.info("NodeTreePresenter: Workflow paused, waiting for resume")
            self.status_message_signal.emit("Print All Nodes workflow paused", 3000)
            # Don't process next node, wait for resume
            return
        
        if self._current_node_index >= len(self._nodes_to_process):
            # All nodes processed
            self.status_message_signal.emit(
                f"Print all nodes complete: {self._total_nodes_to_process} nodes processed",
                8000
            )
            logging.info(f"Print all nodes complete: {self._total_nodes_to_process} nodes processed")
            # Clear processing flags
            self._nodes_to_process = []
            self._workflow_cancelled = False  # Reset for next run
            self._workflow_paused = False  # Reset for next run
            # Disable all buttons on completion (IDLE state)
            self.view.pause_btn.setEnabled(False)
            self.view.resume_btn.setEnabled(False)
            self.view.cancel_btn.setEnabled(False)
            logging.debug("Print All Nodes: Disabled all buttons (workflow completed)")
            return
        
        node = self._nodes_to_process[self._current_node_index]
        node_name = node.name
        
        logging.info(f"Processing node {self._current_node_index + 1}/{self._total_nodes_to_process}: {node_name}")
        self.status_message_signal.emit(
            f"Processing node {self._current_node_index + 1}/{self._total_nodes_to_process}: {node_name}...",
            0
        )
        
        # Increment index for next iteration
        self._current_node_index += 1
        
        # Execute the same logic as right-click "Execute All Print Commands"
        # This properly queues FBC, RPC, and LOG commands through the command queue
        self.process_node_print_commands(node_name)
    
    def _check_sequential_processing_continuation(self):
        """
        Check if sequential node processing should continue to the next node.
        Called via QTimer after each command completes to allow command_queue to update state.
        Respects workflow pause/cancel state.
        """
        logging.debug(f"_check_sequential_processing_continuation: Called")
        
        # Only proceed if we're in sequential processing mode
        if not hasattr(self, '_nodes_to_process') or not self._nodes_to_process:
            logging.debug(f"_check_sequential_processing_continuation: NOT in sequential mode, exiting")
            return
        
        logging.debug(f"_check_sequential_processing_continuation: Sequential mode active, current_index={self._current_node_index}, total={self._total_nodes_to_process}")
        
        # Check if workflow is paused - don't continue if paused
        if self._workflow_paused:
            logging.debug(f"_check_sequential_processing_continuation: Workflow PAUSED, not continuing")
            return
        
        # Check if workflow was cancelled - don't continue if cancelled
        if self._workflow_cancelled:
            logging.debug(f"_check_sequential_processing_continuation: Workflow CANCELLED, not continuing")
            return
        
        # Check if command queue is idle (all commands for current node are done)
        # With unified queue architecture, BsTool commands are now synchronous via CommandQueue
        is_processing = self.command_queue.is_processing
        logging.debug(f"_check_sequential_processing_continuation: command_queue.is_processing={is_processing}")
        
        if not is_processing:
            logging.debug(f"Sequential processing: Queue IDLE, proceeding to next node")
            
            # TIMING FIX: Highlight current node's file NOW (after queue is truly idle)
            # This ensures the highlight stays on the current node until all commands complete
            # Previously this was called prematurely in process_node_print_commands()
            if self._current_node_index > 0:  # Don't highlight before first node starts
                prev_node_index = self._current_node_index - 1
                if prev_node_index < len(self._nodes_to_process):
                    prev_node = self._nodes_to_process[prev_node_index]
                    # Try to find and highlight a LOG file for the completed node
                    log_tokens = self._get_tokens_for_node(prev_node, "LOG")
                    if log_tokens:
                        log_token = log_tokens[0]
                        log_file_path = log_token.log_path if hasattr(log_token, 'log_path') else None
                        if log_file_path:
                            logging.debug(f"Highlighting completed node {prev_node.name} LOG file: {log_file_path}")
                            self._highlight_current_file(prev_node.name, log_token, log_file_path)
            
            self._process_next_node_in_sequence()
        else:
            logging.debug(f"Sequential processing: Queue still PROCESSING, not proceeding yet")
        
    def process_node_hierarchical_commands(self, node_name: str):
        """
        Execute all commands hierarchically for a node.
        This method orchestrates FBC commands, then RPC commands, then LOG/BsTool commands.

        Args:
            node_name: Name of the node to process hierarchically
        """
        logging.info(f"Starting hierarchical command execution for node {node_name}...")
        self.status_message_signal.emit(f"Starting hierarchical execution for node {node_name}...", 0)
        
        try:
            # Get the node
            node = self.node_manager.get_node(node_name)
            if not node:
                self._report_error(f"Node {node_name} not found for hierarchical processing")
                return
            
            # Phase 1: Execute all FBC commands
            fbc_tokens = self._get_tokens_for_node(node, "FBC")
            if fbc_tokens:
                logging.info(f"Phase 1: Processing {len(fbc_tokens)} FBC tokens for node {node_name}")
                self.status_message_signal.emit(f"Phase 1/3: Executing {len(fbc_tokens)} FBC commands...", 0)
                
                telnet_client = getattr(self, 'active_telnet_client', None)
                for token in fbc_tokens:
                    self.fbc_service.queue_fieldbus_command(node_name, token.token_id, telnet_client)
                    self.node_status[node_name] = {"command_success": False, "log_success": False}
                
                # Start processing FBC commands
                self.command_queue.start_processing()
            else:
                logging.info(f"No FBC tokens found for node {node_name}")
            
            # Phase 2: Execute all RPC commands
            rpc_tokens = self._get_tokens_for_node(node, "RPC")
            if rpc_tokens:
                logging.info(f"Phase 2: Processing {len(rpc_tokens)} RPC tokens for node {node_name}")
                self.status_message_signal.emit(f"Phase 2/3: Executing {len(rpc_tokens)} RPC commands...", 0)
                
                telnet_client = getattr(self, 'active_telnet_client', None)
                for token in rpc_tokens:
                    self.rpc_service.queue_rpc_command(node_name, token.token_id, "print", telnet_client)
            else:
                logging.info(f"No RPC tokens found for node {node_name}")
            
            # Phase 3: Process LOG files with BsTool (optional)
            log_tokens = self._get_tokens_for_node(node, "LOG")
            if log_tokens:
                logging.info(f"Phase 3: Processing {len(log_tokens)} LOG files with BsTool for node {node_name}")
                self.status_message_signal.emit(f"Phase 3/3: Processing {len(log_tokens)} LOG files...", 0)
                
                for token in log_tokens:
                    if hasattr(token, 'log_path') and token.log_path:
                        try:
                            # Generate BsTool command for this log file
                            node_id = self._extract_node_id_from_log_path(token.log_path)
                            if node_id:
                                # Strip 'm' or 'r' suffix from node_id for -errlog parameter
                                errlog_node_id = self._strip_node_suffix(node_id)
                                bstool_command_args = f"-errlog {errlog_node_id}"
                                self.command_generated_signal.emit(bstool_command_args, "BSTOOL")
                        except Exception as e:
                            logging.error(f"Error processing LOG file {token.log_path}: {str(e)}")
            else:
                logging.info(f"No LOG tokens found for node {node_name}")
            
            # Completion message
            total_commands = len(fbc_tokens) + len(rpc_tokens) + len(log_tokens)
            self.status_message_signal.emit(
                f"Hierarchical execution complete for {node_name}: {total_commands} commands processed", 
                5000
            )
            logging.info(f"Hierarchical command execution completed for node {node_name}: {total_commands} total commands")
            
        except Exception as e:
            self._report_error(f"Error in hierarchical command execution for node {node_name}", e)
    
    def _strip_node_suffix(self, node_name: str) -> str:
        """
        Strip 'm' or 'r' suffix from node name for BsTool -errlog parameter.
        
        Examples:
            AP01m → AP01
            AP02r → AP02
            AP01 → AP01 (unchanged)
            
        Args:
            node_name: Original node name (may have 'm' or 'r' suffix)
            
        Returns:
            Node name without 'm' or 'r' suffix
        """
        if node_name.endswith('m') or node_name.endswith('r'):
            return node_name[:-1]
        return node_name
    
    def _get_tokens_for_node(self, node, token_type: str):
        """
        Get all tokens of a specific type for a node.
        
        Args:
            node: Node object
            token_type: Type of tokens to retrieve (FBC, RPC, LOG, etc.)
            
        Returns:
            List of tokens of the specified type
        """
        try:
            logging.debug(f"_get_tokens_for_node: Getting {token_type} tokens for node {node.name}")
            # node.tokens is Dict[str, List[NodeToken]], so we need to flatten the lists
            all_tokens = []
            for token_list in node.tokens.values():
                # Ensure token_list is actually a list before extending
                if isinstance(token_list, list):
                    # Only add NodeToken objects to all_tokens
                    for token in token_list:
                        if isinstance(token, NodeToken):
                            all_tokens.append(token)
                else:
                    # If it's not a list but is a NodeToken, add it
                    if isinstance(token_list, NodeToken):
                        all_tokens.append(token_list)
            
            logging.debug(f"_get_tokens_for_node: Found {len(all_tokens)} total tokens for node {node.name}")
            
            # Filter tokens by type
            filtered_tokens = [t for t in all_tokens if t.token_type == token_type]
            logging.debug(f"_get_tokens_for_node: Filtered to {len(filtered_tokens)} {token_type} tokens for node {node.name}")
            return filtered_tokens
        except Exception as e:
            logging.error(f"Error getting {token_type} tokens for node {node.name}: {str(e)}")
            return []
        
    def _extract_node_id_from_log_path(self, log_file_path: str) -> str:
        """
        Extract node ID from log file path.
        
        Args:
            log_file_path (str): Path to the log file
            
        Returns:
            str: Extracted node ID or empty string if not found
        """
        try:
            # Get filename from path
            filename = os.path.basename(log_file_path)
            
            # Remove extension
            name_without_ext = os.path.splitext(filename)[0]
            
            # Handle special case where filename might have additional extensions
            # like "AP01m_192-168-0-11_162.rpc.log"
            if '.' in name_without_ext:
                name_without_ext = name_without_ext.split('.')[0]
            
            # Extract node ID using regex pattern
            # Pattern matches: NODEID_IPADDRESS or NODEID_IPADDRESS_TOKEN
            pattern = r'^([a-zA-Z0-9]+[a-zA-Z]?)_'  # Capture node ID part before first underscore
            match = re.match(pattern, name_without_ext)
            
            if match:
                node_id = match.group(1)
            else:
                # Fallback: try to extract first part before first underscore
                parts = name_without_ext.split('_')
                if parts:
                    node_id = parts[0]
                else:
                    node_id = "" # No node ID found
            # Apply nodename truncation logic for '.log' files
            if log_file_path.lower().endswith('.log') and len(node_id) > 3 and node_id[-1].lower() in ['r', 'm']:
                node_id = node_id[:-1]
            
            return node_id
        except Exception as e:
            logging.error(f"Error extracting node ID from log path {log_file_path}: {str(e)}")
            
        return ""
        
    def process_fieldbus_command(self, token_id, node_name):
        """
        Process a single fieldbus command.

        Args:
            token_id: ID of the token to process
            node_name: Name of the node containing the token
        """
        logging.debug(f"Processing Fieldbus command: token_id={token_id}, node_name={node_name}")
        try:
            # Get token first to validate node exists before generating command
            token = self.fbc_service.get_token(node_name, token_id)
            
            # Emit status message before processing
            command = self.fbc_service.generate_fieldbus_command(token_id)
            self.status_message_signal.emit(f"Executing: {command}...", 3000)
            
            # Pass active telnet client for reuse
            telnet_client = getattr(self, 'active_telnet_client', None)
            self.fbc_service.queue_fieldbus_command(node_name, token_id, telnet_client)
            self.command_queue.start_processing()
        except ValueError as e:
            # Handle specific ValueError cases like "Node not found"
            if "not found" in str(e).lower():
                self.status_message_signal.emit(str(e), 3000)
            else:
                self._report_error("Error processing Fieldbus command", e)
        except Exception as e:
            self._report_error("Error processing Fieldbus command", e)
            
    def process_rpc_command(self, node_name, token_id, action_type):
        """
        Process RPC commands with token validation and auto-execute.

        Args:
            node_name: Name of the node containing the token
            token_id: ID of the token to process
            action_type: Type of action (print, clear)
        """
        if action_type not in ["print", "clear"]:
            return
            
        try:
            if not token_id or not isinstance(token_id, str):
                raise ValueError("Invalid token ID")
                
            # Extract token part from token_id (format: NODE_TOKEN)
            token_part = token_id.split('_')[-1] if '_' in token_id else token_id
            
            # Validate token
            token = self.rpc_service.get_token(node_name, token_part)
            if not self.session_manager.validate_token(token):
                self.status_message_signal.emit(f"Invalid token: {token_id}", 5000)
                return
            
            # Pass active telnet client for reuse
            telnet_client = getattr(self, 'active_telnet_client', None)
            
            # Queue command through service
            self.rpc_service.queue_rpc_command(node_name, token_part, action_type, telnet_client)
            self.command_queue.start_processing()
            
        except ValueError as e:
            self._report_error("Invalid RPC command parameters", e)
        except AttributeError as e:
            self._report_error("UI component access error", e)
        except Exception as e:
            logging.error(f"Unexpected error in RPC command setup: {str(e)}")
            self._report_error("RPC command setup failed", e)
            
    def clear_subgroup_log_files(self, item):
        """
        Clear all log files associated with a subgroup.

        Args:
            item: The tree item representing the subgroup (e.g., FBC, RPC, LOG, LIS section)
        """
        if not item:
            self._report_error("No item selected for clearing subgroup log files")
            return
        
        # If item is a MockItem (from ContextMenuService), its data is directly accessible
        if hasattr(item, 'data') and isinstance(item.data, dict):
            item_data = item.data
        else:
            # Assume it's a QTreeWidgetItem and extract data
            item_data = item.data(0, Qt.ItemDataRole.UserRole)
        
        if not item_data or item_data.get("type") != "section":
            self._report_error("Selected item is not a subgroup section")
            return

        section_type = item_data.get("section_type")
        node_name = item_data.get("node")

        if not node_name or not section_type:
            self._report_error("Could not determine node or section type for clearing log files")
            return

        logging.info(f"Clearing all {section_type} log files for node {node_name}...")
        self.status_message_signal.emit(f"Clearing all {section_type} log files for node {node_name}...", 0)

        # Iterate through the tokens in item_data
        cleared_count = 0
        tokens_to_clear = item_data.get("tokens", [])
        
        if not tokens_to_clear:
            self._report_error(f"No tokens found to clear for {section_type} subgroup of node {node_name}")
            return

        for token_obj in tokens_to_clear:
            if hasattr(token_obj, "log_path") and token_obj.log_path:
                log_path = token_obj.log_path
                try:
                    self.bstool_service.clear_log(log_path)
                    cleared_count += 1
                    logging.debug(f"Cleared log file: {log_path}")
                except Exception as e:
                    self._report_error(f"Failed to clear log file {log_path}", e)
            else:
                logging.warning(f"Token object {token_obj} in section {section_type} does not have a valid log_path.")

        self.status_message_signal.emit(f"Cleared {cleared_count} {section_type} log files for node {node_name}", 3000)
            
    def process_bstool_command(self, log_file_path: str):
        """
        Process BsTool command for a log file.
        Executes BsTool with -errlog parameter using the extracted node ID.
        
        Args:
            log_file_path: Path to the log file to process with BsTool
        """
        try:
            # Extract node ID from log file path
            node_id = self._extract_node_id_from_log_path(log_file_path)
            
            if not node_id:
                self._report_error("Could not extract node ID from log file path", None)
                return
            
            # Strip 'm' or 'r' suffix from node_id for -errlog parameter
            errlog_node_id = self._strip_node_suffix(node_id)
            
            # Construct bstool command arguments
            bstool_command_args = f"-errlog {errlog_node_id}"
            
            # Execute the BsTool command directly via bstool_service
            self.bstool_service.execute_command(bstool_command_args)
            
            self.status_message_signal.emit(f"Executing BsTool with -errlog {errlog_node_id}", 3000)
        except Exception as e:
            self._report_error("Error processing BsTool command", e)
            
    def on_node_selected(self, item):
        """
        Handle node/token selection in the view.
        
        Args:
            item: Selected item from the view
        """
        # Check if the selected item is a log file
        if item:
            item_data = item.data(0, Qt.ItemDataRole.UserRole)
            if item_data and "log_path" in item_data:
                filename = os.path.basename(item_data["log_path"])
                token_id = item_data.get("token")
                token_type = item_data.get("token_type")
                node_name = item_data.get("node")

                # Emit log_file_selected_signal for all log files
                self.log_file_selected_signal.emit(filename)

                command = ""
                if token_type == "FBC":
                    command = self.fbc_service.generate_fieldbus_command(token_id)
                elif token_type == "RPC":
                    command = self.rpc_service.generate_rpc_command(token_id, "print")
                elif token_type == "BSTOOL":
                    # For BSTOOL, construct the command manually
                    node_id = self._extract_node_id_from_log_path(item_data["log_path"])
                    bstool_path = self.bstool_service._get_bstool_path()
                    if node_id and bstool_path:
                        command = f"{bstool_path} -errlog {node_id}"
                    else:
                        logging.warning(f"Could not generate BSTOOL command for {filename}: node_id={node_id}, bstool_path={bstool_path}")
                elif token_type == "LOG":
                    # For LOG files, generate BsTool command
                    node_id = self._extract_node_id_from_log_path(item_data["log_path"])
                    if node_id:
                        command = f"-errlog {node_id}"
                        token_type = "BSTOOL"
                    else:
                        logging.warning(f"Could not extract node ID for LOG file: {filename}")
                elif token_type == "LIS":
                    # For LIS, no command is generated, only the log file is selected
                    pass
                else:
                    logging.warning(f"Unknown token type for command generation: {token_type}")

                if command:
                    self.command_generated_signal.emit(command, token_type)
                    logging.debug(f"Emitted command_generated_signal: {command}, {token_type}")

    def open_log_file(self, item, column: int):
        """
        Open log file associated with the tree item.
        
        Args:
            item: Tree item representing the log file
            column: Column index (unused)
        """
        data = item.data(0, Qt.ItemDataRole.UserRole)
        if not data or "log_path" not in data:
            return
            
        log_path = data["log_path"]
        if not os.path.exists(log_path):
            self.status_message_signal.emit(f"Log file not found: {log_path}", 5000)
            return
            
        try:
            # Open file with default application
            import subprocess
            if os.name == 'nt':  # Windows
                os.startfile(log_path)
            else:  # macOS and Linux
                subprocess.call(('open', log_path) if sys.platform == 'darwin'
                              else ('xdg-open', log_path))
        except Exception as e:
            self.status_message_signal.emit(f"Error opening log file: {str(e)}", 5000)
    
    def _handle_pause(self):
        """Handle pause button click - pauses Print All Nodes workflow."""
        # Set workflow pause flag
        self._workflow_paused = True
        
        # Update button states for PAUSED state (disable pause, enable resume/cancel)
        self.view.pause_btn.setEnabled(False)
        self.view.resume_btn.setEnabled(True)
        self.view.cancel_btn.setEnabled(True)
        logging.debug("Print All Nodes: Updated buttons for PAUSED state")
        
        # Also pause sequential processor (for context menu operations)
        self.sequential_processor.pause()
        
        # Emit status message
        self.status_message_signal.emit("Workflow paused - will pause after current node completes", 3000)
        logging.info("NodeTreePresenter: Workflow paused by user")
    
    def _handle_resume(self):
        """Handle resume button click - resumes Print All Nodes workflow."""
        # Clear workflow pause flag
        self._workflow_paused = False
        
        # Update button states for RUNNING state (enable pause/cancel, disable resume)
        self.view.pause_btn.setEnabled(True)
        self.view.resume_btn.setEnabled(False)
        self.view.cancel_btn.setEnabled(True)
        logging.debug("Print All Nodes: Updated buttons for RUNNING state (resumed)")
        
        # Also resume sequential processor (for context menu operations)
        self.sequential_processor.resume()
        
        # Emit status message
        self.status_message_signal.emit("Workflow resumed", 3000)
        logging.info("NodeTreePresenter: Workflow resumed by user")
        
        # Resume processing if we're in the middle of Print All Nodes
        if hasattr(self, '_nodes_to_process') and self._nodes_to_process:
            self._check_sequential_processing_continuation()
    
    def _handle_cancel(self):
        """Handle cancel button click - cancels Print All Nodes workflow."""
        # Set workflow cancel flag
        self._workflow_cancelled = True
        
        # Update button states for CANCELLED/IDLE state (disable all buttons)
        self.view.pause_btn.setEnabled(False)
        self.view.resume_btn.setEnabled(False)
        self.view.cancel_btn.setEnabled(False)
        logging.debug("Print All Nodes: Updated buttons for CANCELLED state")
        
        # Also cancel sequential processor (for context menu operations)
        self.sequential_processor.cancel()
        
        # Clear the nodes to process list to stop workflow
        if hasattr(self, '_nodes_to_process'):
            remaining_nodes = len(self._nodes_to_process) - getattr(self, '_current_node_index', 0)
            self._nodes_to_process = []
            self.status_message_signal.emit(f"Workflow cancelled - {remaining_nodes} remaining nodes skipped", 5000)
            logging.info(f"NodeTreePresenter: Workflow cancelled by user, {remaining_nodes} nodes skipped")
        else:
            self.status_message_signal.emit("Workflow cancelled", 3000)
            logging.info("NodeTreePresenter: Workflow cancelled by user")
    
    def _highlight_current_file(self, node_name: str, token, file_path: str):
        """
        Highlight the currently processing file in the tree.
        
        Args:
            node_name: Name of the node being processed
            token: Token object being processed
            file_path: Path to the log file being created
        """
        try:
            logging.debug(f"_highlight_current_file: node={node_name}, token={token.token_id}, path={file_path}")
            
            # First, ensure the entire node is expanded
            self._expand_entire_node(node_name)
            
            # Normalize the file path
            normalized_path = os.path.normpath(file_path)
            
            # Look up the item in file_item_map (should be available after expansion)
            file_item = self.file_item_map.get(normalized_path)
                
            if file_item:
                # Set as current item and scroll to it
                self.view.setCurrentItem(file_item)
                self.view.scrollToItem(file_item)
                
                logging.debug(f"_highlight_current_file: Successfully highlighted {normalized_path}")
            else:
                logging.warning(f"_highlight_current_file: Could not find tree item for {normalized_path}")
                logging.debug(f"_highlight_current_file: Available keys: {list(self.file_item_map.keys())}")
                
        except Exception as e:
            logging.error(f"_highlight_current_file: Error highlighting file: {str(e)}")
    
    def _expand_entire_tree(self):
        """
        Expand ALL nodes in the tree and all their subgroups.
        Called when "Print All Nodes" is clicked to make all files visible.
        """
        try:
            logging.info("_expand_entire_tree: Expanding entire node tree...")
            self.status_message_signal.emit("Expanding tree to show all files...", 2000)
            
            # CRITICAL: Clear and rebuild file_item_map to ensure consistency
            logging.debug(f"_expand_entire_tree: Clearing file_item_map (was {len(self.file_item_map)} entries)")
            self.file_item_map = {}
            
            root = self.view.node_tree
            expanded_count = 0
            
            # Iterate through all top-level nodes
            for i in range(root.topLevelItemCount()):
                node_item = root.topLevelItem(i)
                item_data = node_item.data(0, Qt.ItemDataRole.UserRole)
                
                if item_data and item_data.get("type") == "node":
                    node_name = item_data.get("node_name", "")
                    
                    # Always force reload of children to rebuild file_item_map
                    # Remove all existing children first
                    while node_item.childCount() > 0:
                        node_item.removeChild(node_item.child(0))
                    
                    # Reload children (this populates file_item_map)
                    self._load_node_children(node_item)
                    
                    # Expand the node
                    self.view.expandItem(node_item)
                    
                    # Expand ALL section items (FBC, RPC, LOG, LIS)
                    for j in range(node_item.childCount()):
                        section_item = node_item.child(j)
                        section_type = section_item.text(0)
                        self.view.expandItem(section_item)
                    
                    expanded_count += 1
                    logging.debug(f"_expand_entire_tree: Expanded node {node_name} ({expanded_count}/{root.topLevelItemCount()})")
            
            logging.info(f"_expand_entire_tree: Successfully expanded {expanded_count} nodes with all subgroups")
            logging.info(f"_expand_entire_tree: file_item_map now contains {len(self.file_item_map)} files")
            logging.debug(f"_expand_entire_tree: file_item_map keys: {list(self.file_item_map.keys())}")
            
        except Exception as e:
            logging.error(f"_expand_entire_tree: Error expanding tree: {str(e)}")
    
    def _expand_entire_node(self, node_name: str):
        """
        Fully expand a node and all its subgroups (FBC, RPC, LOG, LIS).
        This ensures all children are loaded into file_item_map.
        
        Args:
            node_name: Name of the node to expand
        """
        try:
            logging.debug(f"_expand_entire_node: Expanding node {node_name} and all subgroups")
            
            # Find the node item in the tree
            root = self.view.node_tree
            for i in range(root.topLevelItemCount()):
                node_item = root.topLevelItem(i)
                item_data = node_item.data(0, Qt.ItemDataRole.UserRole)
                
                if item_data and item_data.get("type") == "node":
                    item_node_name = item_data.get("node_name", "")
                    
                    # Match the node name exactly (case-insensitive)
                    if item_node_name.lower() == node_name.lower():
                        logging.debug(f"_expand_entire_node: Found node item for {node_name}")
                        
                        # Expand the node to load children if not already loaded
                        if not node_item.isExpanded():
                            logging.debug(f"_expand_entire_node: Expanding node {node_name}")
                            self.view.expandItem(node_item)
                            # Trigger lazy loading
                            self.handle_item_expanded(node_item)
                        
                        # Expand ALL section items (FBC, RPC, LOG, LIS)
                        for j in range(node_item.childCount()):
                            section_item = node_item.child(j)
                            section_type = section_item.text(0)
                            
                            if not section_item.isExpanded():
                                logging.debug(f"_expand_entire_node: Expanding section {section_type} for {node_name}")
                                self.view.expandItem(section_item)
                        
                        logging.debug(f"_expand_entire_node: Fully expanded node {node_name} with all subgroups")
                        break
                        
        except Exception as e:
            logging.error(f"_expand_entire_node: Error expanding node: {str(e)}")