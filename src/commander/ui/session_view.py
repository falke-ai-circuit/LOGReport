"""
Session View

This view provides the session interface with Telnet and BsTool tabs.
"""

from PyQt6.QtWidgets import QTabWidget, QTextEdit, QVBoxLayout, QWidget, QHBoxLayout, QPushButton, QLabel
from PyQt6.QtCore import pyqtSignal

from commander.ui.telnet_tab import TelnetTab  # Add import for TelnetTab
from commander.ui.bstool_tab import BsToolTab  # Import BsToolTab
from .theme import STYLESHEETS

class SessionView(QWidget):
    """
    View for the session interface.
    """
    
    # Signals
    copy_to_log_clicked = pyqtSignal()
    
    def __init__(self, bstool_path=None):
        """Initialize the SessionView."""
        super().__init__()
        self.bstool_path = bstool_path
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
        
        # Add tab widget to layout
        layout.addWidget(self.tab_widget)
        
        self.setLayout(layout)
        
        # Apply styling
        self.setStyleSheet(STYLESHEETS.get_application_stylesheet())
        
        # Connect signals
        self.telnet_tab.copy_to_log_clicked.connect(self.copy_to_log_clicked.emit)