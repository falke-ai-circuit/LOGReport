"""
Session View

The SessionView provides the session interface with Telnet and BsTool tabs.
"""

from PyQt5.QtWidgets import QTabWidget, QTextEdit, QVBoxLayout, QWidget, QHBoxLayout, QPushButton, QLabel
from PyQt5.QtCore import pyqtSignal

from commander.ui.telnet_tab import TelnetTab  # Add import for TelnetTab
from commander.ui.bstool_tab import BsToolTab  # Import BsToolTab
from commander.ui.scan_tab import ScanTab  # Import ScanTab
from .theme import STYLESHEETS

class SessionView(QWidget):
    """
    View for the session interface.
    """
    
    # Signals
    copy_to_log_clicked = pyqtSignal()
    
    def __init__(self, bstool_path=None, node_manager=None, telnet_service=None, get_connection_info_callback=None):
        """Initialize the SessionView."""
        super().__init__()
        self.bstool_path = bstool_path
        self.node_manager = node_manager
        self.telnet_service = telnet_service
        self.get_connection_info_callback = get_connection_info_callback
        self._setup_ui()
        
    def _setup_ui(self):
        """Set up the user interface."""
        layout = QVBoxLayout()
        
        # Create tab widget
        self.tab_widget = QTabWidget()
        
        # Create Telnet tab (should be first tab)
        self.telnet_tab = TelnetTab()
        self.tab_widget.addTab(self.telnet_tab, "Telnet")

        # Create BsTool tab
        self.bstool_tab = BsToolTab()
        if self.bstool_path:
            self.bstool_tab.bstool_path_edit.setText(self.bstool_path)
        self.tab_widget.addTab(self.bstool_tab, "BsTool")
        
        # Create Scan tab (Phase 1 implementation)
        if self.node_manager:
            self.scan_tab = ScanTab(
                node_manager=self.node_manager,
                telnet_service=self.telnet_service,
                parent=self,
                get_connection_info_callback=self.get_connection_info_callback
            )
            self.tab_widget.addTab(self.scan_tab, "Scan")
        else:
            self.scan_tab = None
        
        # Add tab widget to layout
        layout.addWidget(self.tab_widget)
        
        self.setLayout(layout)
        
        # Apply styling
        self.setStyleSheet(STYLESHEETS.get_application_stylesheet())
        
        # Connect signals
        self.telnet_tab.copy_to_log_clicked.connect(self.copy_to_log_clicked.emit)
        
        # Connect main tab change signal to pause/resume auto-refresh
        self.tab_widget.currentChanged.connect(self._on_main_tab_changed)
    
    def _on_main_tab_changed(self, index):
        """
        Handle main tab change - pause/resume auto-refresh on Scan tab.
        
        When user switches to/from Scan tab, pause auto-refresh on inactive tabs
        and resume on the active tab to avoid unnecessary background comparisons.
        """
        if not self.scan_tab:
            return
        
        # Get current tab name
        current_tab = self.tab_widget.widget(index)
        
        if current_tab == self.scan_tab:
            # Switched TO Scan tab - resume auto-refresh on active node
            self.scan_tab.resume_active_auto_refresh()
        else:
            # Switched AWAY from Scan tab - pause all auto-refresh
            self.scan_tab.pause_all_auto_refresh()