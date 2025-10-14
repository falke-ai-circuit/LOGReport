"""
Commander UI Factory

This factory creates and manages the main UI components.
"""

from PyQt5.QtWidgets import (
    QSplitter, QTreeWidget, QTreeWidgetItem, QTabWidget, QTextEdit, 
    QVBoxLayout, QWidget, QHBoxLayout, QPushButton, QLabel
)

from commander.ui.node_tree_view import NodeTreeView
from commander.ui.session_view import SessionView
from commander.ui.bstool_tab import BsToolTab
from .theme import STYLESHEETS

class CommanderUIFactory:
    """
    Factory for creating and managing UI components.
    """
    
    def __init__(self, bstool_path=None, node_manager=None, telnet_service=None):
        """Initialize the UI factory."""
        self.bstool_path = bstool_path
        self.node_manager = node_manager
        self.telnet_service = telnet_service
        self._create_components()
        
    def _create_components(self):
        """Create UI components."""
        # Create main views
        self.node_tree_view = NodeTreeView()
        self.session_view = SessionView(
            bstool_path=self.bstool_path,
            node_manager=self.node_manager,
            telnet_service=self.telnet_service
        )
        
        # Access tabs through session view
        self.bstool_tab = self.session_view.bstool_tab
        
    def get_main_widget(self) -> QWidget:
        """
        Get the main application widget.
        
        Returns:
            Main application widget
        """
        # Create splitter for main layout
        splitter = QSplitter()
        splitter.addWidget(self.node_tree_view)
        splitter.addWidget(self.session_view)
        splitter.setSizes([300, 700])
        
        # Create main widget
        main_widget = QWidget()
        layout = QVBoxLayout()
        layout.addWidget(splitter)
        main_widget.setLayout(layout)
        
        # Apply styling
        main_widget.setStyleSheet(STYLESHEETS.get_application_stylesheet())
        
        return main_widget
        
    def get_node_tree_view(self) -> NodeTreeView:
        """
        Get the node tree view.
        
        Returns:
            NodeTreeView instance
        """
        return self.node_tree_view
        
    def get_session_view(self) -> SessionView:
        """
        Get the session view.
        
        Returns:
            SessionView instance
        """
        return self.session_view
        
    def get_bstool_tab(self) -> BsToolTab:
        """
        Get the BsTool tab.
        
        Returns:
            BsToolTab instance
        """
        return self.bstool_tab