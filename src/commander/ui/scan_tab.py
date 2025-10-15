"""
Scan Tab

Main tab widget for FBC/RPC file scanning and comparison functionality.
Hosts per-node subtabs for displaying parsed file content and live system comparisons.
"""

from PyQt5.QtWidgets import QWidget, QTabWidget, QVBoxLayout
from PyQt5.QtCore import pyqtSignal
from commander.services.fbc_parser_service import FbcParserService
from commander.node_manager import NodeManager
import logging


class ScanTab(QWidget):
    """Main Scan tab widget hosting per-node subtabs"""
    
    # Signals
    comparison_started = pyqtSignal(str)  # node_name
    comparison_completed = pyqtSignal(str, dict)  # node_name, results
    status_message = pyqtSignal(str, int)  # message, duration
    
    def __init__(self, node_manager: NodeManager, telnet_service=None, parent=None):
        super().__init__(parent)
        self.node_manager = node_manager
        self.telnet_service = telnet_service
        self.parser_service = FbcParserService()
        self.node_widgets = {}  # {node_name: NodeScanWidget}
        self.logger = logging.getLogger(__name__)
        
        self._setup_ui()
    
    def _setup_ui(self):
        """Create main tab widget and initialize node subtabs"""
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Create tab widget for node subtabs
        self.node_tabs = QTabWidget()
        layout.addWidget(self.node_tabs)
        
        self.setLayout(layout)
    
    def populate_nodes(self):
        """Create subtab for each configured node"""
        print(f"[SCAN_TAB DEBUG] populate_nodes() called")
        self.logger.info("populate_nodes() method called")
        
        # Clear existing tabs
        self.node_tabs.clear()
        self.node_widgets.clear()
        
        # Get all nodes from node manager (returns List[Node])
        nodes = self.node_manager.get_all_nodes()
        print(f"[SCAN_TAB DEBUG] Found {len(nodes) if nodes else 0} nodes from node_manager")
        self.logger.info(f"Node manager returned {len(nodes) if nodes else 0} nodes")
        
        if not nodes:
            self.logger.warning("No nodes available to populate Scan tab")
            self.status_message.emit("No nodes configured. Load configuration first.", 5000)
            return
        
        self.logger.info(f"Populating Scan tab with {len(nodes)} nodes")
        print(f"[SCAN_TAB DEBUG] log_root = {self.node_manager.log_root}")
        
        # Create a subtab for each node (nodes is a List[Node])
        for node in sorted(nodes, key=lambda n: n.name):
            node_name = node.name
            
            # Import here to avoid circular dependency
            from commander.ui.node_scan_widget import NodeScanWidget
            
            # Get token files for this node
            token_files = self._get_node_token_files(node_name)
            print(f"[SCAN_TAB DEBUG] Node {node_name}: Found {len(token_files)} token files")
            
            if not token_files:
                self.logger.debug(f"No FBC/RPC files found for node {node_name}, skipping")
                continue
            
            # Create widget for this node with staggered load delay (100ms per widget)
            # This prevents all widgets from loading files simultaneously
            load_delay_ms = len(self.node_widgets) * 100
            node_widget = NodeScanWidget(
                node_name=node_name,
                token_files=token_files,
                parser_service=self.parser_service,
                telnet_service=self.telnet_service,
                parent=self,
                load_delay_ms=load_delay_ms
            )
            
            # Connect signals
            node_widget.status_message.connect(self.status_message.emit)
            node_widget.comparison_started.connect(lambda n=node_name: self.comparison_started.emit(n))
            node_widget.comparison_completed.connect(lambda r, n=node_name: self.comparison_completed.emit(n, r))
            
            # Add to tabs
            self.node_tabs.addTab(node_widget, node_name)
            self.node_widgets[node_name] = node_widget
            
            self.logger.debug(f"Added Scan subtab for node {node_name} with {len(token_files)} files")
        
        self.status_message.emit(f"Loaded {len(self.node_widgets)} nodes in Scan tab", 3000)
    
    def _get_node_token_files(self, node_name: str) -> list:
        """Get list of FBC/RPC files for a node"""
        from pathlib import Path
        
        files = []
        
        # Get node configuration
        node = self.node_manager.get_node(node_name)
        if not node:
            print(f"[SCAN_TAB DEBUG] Node {node_name} not found in node_manager")
            return files
        
        # Determine base directory path
        log_root = self.node_manager.log_root
        if not log_root:
            self.logger.warning("Log root not configured")
            print(f"[SCAN_TAB DEBUG] log_root is None!")
            return files
        
        # Extract base node name (before space)
        base_node_name = node_name.split()[0] if " " in node_name else node_name
        print(f"[SCAN_TAB DEBUG] Node {node_name} -> base_node_name: {base_node_name}")
        
        # Check FBC directory (log_root already points to _DIA)
        fbc_dir = Path(log_root) / "FBC" / base_node_name
        print(f"[SCAN_TAB DEBUG] Checking FBC dir: {fbc_dir} (exists: {fbc_dir.exists()})")
        if fbc_dir.exists():
            fbc_files = list(fbc_dir.glob("*.fbc"))
            files.extend([str(f) for f in fbc_files])
            self.logger.debug(f"Found {len(fbc_files)} FBC files for {node_name}")
            print(f"[SCAN_TAB DEBUG] Found {len(fbc_files)} FBC files")
        
        # Check RPC directory (log_root already points to _DIA)
        rpc_dir = Path(log_root) / "RPC" / base_node_name
        print(f"[SCAN_TAB DEBUG] Checking RPC dir: {rpc_dir} (exists: {rpc_dir.exists()})")
        if rpc_dir.exists():
            rpc_files = list(rpc_dir.glob("*.rpc"))
            files.extend([str(f) for f in rpc_files])
            self.logger.debug(f"Found {len(rpc_files)} RPC files for {node_name}")
            print(f"[SCAN_TAB DEBUG] Found {len(rpc_files)} RPC files")
        
        print(f"[SCAN_TAB DEBUG] Total files for {node_name}: {len(files)}")
        return sorted(files)
    
    def refresh_node_data(self, node_name: str):
        """Reload FBC files for specific node"""
        if node_name not in self.node_widgets:
            self.logger.warning(f"Node {node_name} not found in Scan tab")
            return
        
        # Get updated file list
        token_files = self._get_node_token_files(node_name)
        
        # Update node widget
        widget = self.node_widgets[node_name]
        widget.update_file_list(token_files)
        
        self.logger.info(f"Refreshed files for node {node_name}: {len(token_files)} files")

    def select_file_and_compare(self, node_name: str, file_path: str):
        """
        Select node subtab, select file from dropdown, and trigger comparison.
        
        Args:
            node_name: Name of the node to select
            file_path: Path to the .fbc or .rpc file to select and compare
        """
        from pathlib import Path
        
        self.logger.info(f"select_file_and_compare called: node={node_name}, file={Path(file_path).name}")
        
        # Step 1: Find and switch to node subtab
        if node_name not in self.node_widgets:
            self.logger.warning(f"Node {node_name} not found in Scan tab widgets")
            self.status_message.emit(f"Node {node_name} not found in Scan tab", 5000)
            return
        
        # Find node tab index
        for i in range(self.node_tabs.count()):
            if self.node_tabs.tabText(i) == node_name:
                self.node_tabs.setCurrentIndex(i)
                self.logger.info(f"Switched to node tab: {node_name} (index {i})")
                break
        
        # Step 2: Get node widget and trigger file selection + comparison
        node_widget = self.node_widgets[node_name]
        
        # Delegate to NodeScanWidget for file selection and comparison
        success = node_widget.select_file_and_compare(file_path)
        
        if success:
            self.logger.info(f"File selection and comparison triggered for {Path(file_path).name}")
        else:
            self.logger.warning(f"Failed to select file {Path(file_path).name} in node {node_name}")
            self.status_message.emit(f"File not found: {Path(file_path).name}", 5000)
