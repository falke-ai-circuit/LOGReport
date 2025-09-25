"""
Node Tree Presenter - Handles presentation logic for the node tree within the commander window
"""

from abc import ABC, abstractmethod
import logging
import os
import glob
from typing import Optional
from PyQt6.QtCore import QObject, pyqtSignal, Qt
from PyQt6.QtWidgets import QTreeWidgetItem

from ..models import NodeToken
from ..node_manager import NodeManager
from ..session_manager import SessionManager
from ..log_writer import LogWriter
from ..command_queue import CommandQueue
from ..services.fbc_command_service import FbcCommandService
from ..services.rpc_command_service import RpcCommandService
from ..icons import get_node_online_icon, get_node_offline_icon, get_token_icon
import os
import re
import subprocess
from PyQt6.QtGui import QColor


class NodeTreePresenter(QObject):
    """
    Presenter for the Node Tree, handling presentation logic related to node tree operations
    """
    
    # Signals for UI updates
    status_message_signal = pyqtSignal(str, int)  # message, duration
    node_tree_updated_signal = pyqtSignal()  # emitted when node tree is updated
    log_file_selected_signal = pyqtSignal(str)  # emitted when log file is selected, carries filename
    command_generated_signal = pyqtSignal(str, str) # emitted when a command is generated, carries command string and token type
    
    def __init__(self, view, node_manager: NodeManager, session_manager: SessionManager,
                 log_writer: LogWriter, command_queue: CommandQueue,
                 fbc_service: FbcCommandService, rpc_service: RpcCommandService,
                 context_menu_service, bstool_service):
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
        
        # Connect view signals to presenter methods
        self.view.item_expanded.connect(self.handle_item_expanded)
        
        # Dictionary to track command and log write status for each node
        # Key: node_name, Value: {"command_success": Optional[bool], "log_success": Optional[bool], "line_count": Optional[int]}
        self.node_status = {}
        self.file_item_map = {} # Map log_path to QTreeWidgetItem
        
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
        
        if not added_sections:
            no_files = QTreeWidgetItem(["No files found for this node"])
            no_files.setIcon(0, get_token_icon())
            node_item.addChild(no_files)
            logging.debug(f"_load_node_children: No files found for node: {node_name}")
        
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
        return file_item
        
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
            
    def handle_log_write_completed(self, log_path: str, success: bool, total_line_count: int, lines_written_by_command: int):
        """
        Handle the log_write_completed signal from LogWriter.
        
        Args:
            log_path: The path to the log file
            success: True if the log write was successful, False otherwise
            total_line_count: The total number of lines in the log file
            lines_written_by_command: The number of lines written by the current command
        """
        if log_path not in self.node_status:
            self.node_status[log_path] = {"command_success": None, "log_success": None, "total_line_count": None, "lines_written_by_command": None}
        
        self.node_status[log_path]["log_success"] = success
        self.node_status[log_path]["total_line_count"] = total_line_count
        self.node_status[log_path]["lines_written_by_command"] = lines_written_by_command
        logging.debug(f"handle_log_write_completed: Log Path: {log_path}, Log Success: {success}, Total Line Count: {total_line_count}, Lines Written by Command: {lines_written_by_command}")
        self._check_and_update_node_color(log_path)
            
    def _check_and_update_node_color(self, log_path: str):
        """
        Check if both command and log write were successful for a node and update its color.
        
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
            logging.debug(f"_check_and_update_node_color: Looking for normalized_log_path: {normalized_log_path} in file_item_map. Map keys: {list(self.file_item_map.keys())}")
            file_item = self.file_item_map.get(normalized_log_path)
            if file_item:
                if command_success and log_success:
                    if token_type in ["FBC", "RPC"]: # Apply to both FBC and RPC
                        if lines_written_by_command is None or lines_written_by_command == 0:
                            logging.debug(f"_check_and_update_node_color: Setting color for {normalized_log_path} to red (no new content for {token_type})")
                            self.view.update_node_color(file_item, "red")
                        elif lines_written_by_command < 10:
                            logging.debug(f"_check_and_update_node_color: Setting color for {normalized_log_path} to yellow (new content < 10 lines for {token_type})")
                            self.view.update_node_color(file_item, "yellow")
                        else: # lines_written_by_command >= 10
                            logging.debug(f"_check_and_update_node_color: Setting color for {normalized_log_path} to green (new content >= 10 lines for {token_type})")
                            self.view.update_node_color(file_item, "green")
                    else: # Existing logic for other file types (e.g., LOG)
                        if total_line_count is None or total_line_count == 0:
                            logging.debug(f"_check_and_update_node_color: Setting color for {normalized_log_path} to red (no content)")
                            self.view.update_node_color(file_item, "red")
                        elif total_line_count < 10: # Example threshold, adjust as needed
                            logging.debug(f"_check_and_update_node_color: Setting color for {normalized_log_path} to yellow (total_line_count < 10)")
                            self.view.update_node_color(file_item, "yellow")
                        else: # total_line_count >= 10
                            logging.debug(f"_check_and_update_node_color: Setting color for {normalized_log_path} to green (total_line_count >= 10)")
                            self.view.update_node_color(file_item, "green")
                else:
                    logging.debug(f"_check_and_update_node_color: Setting color for {normalized_log_path} to red (command/log failed)")
                    self.view.update_node_color(file_item, "red")
            else:
                logging.warning(f"_check_and_update_node_color: file_item not found for log_path: {normalized_log_path}")

            # Reset status after update
            self.node_status[log_path] = {"command_success": None, "log_success": None, "total_line_count": None, "lines_written_by_command": None}
                
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
        from PyQt6.QtWidgets import QMenu
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
            
    def process_bstool_command(self, log_file_path: str):
        """
        Process BsTool command for a log file.
        
        Args:
            log_file_path: Path to the log file to process with BsTool
        """
        try:
            # Extract node ID from log file path
            node_id = self._extract_node_id_from_log_path(log_file_path)
            
            # Construct bstool command arguments
            bstool_command_args = f"-errlog {node_id}" if node_id else ""
            
            # Emit the command to UI instead of executing directly
            self.command_generated_signal.emit(bstool_command_args, "BSTOOL")
            self.status_message_signal.emit(f"Generated BsTool command for {os.path.basename(log_file_path)}", 3000)
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