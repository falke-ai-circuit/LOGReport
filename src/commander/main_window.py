"""
Main Window

This is the main application window that hosts all UI components.
"""

from PyQt5.QtWidgets import (
    QMainWindow, QSplitter, QVBoxLayout, QWidget, QHBoxLayout,
    QStatusBar, QFileDialog, QApplication
)
from PyQt5.QtCore import Qt

from commander.ui.commander_ui_factory import CommanderUIFactory
from commander.presenters.commander_presenter import CommanderPresenter
from commander.services.status_service import StatusService
from commander.node_manager import NodeManager
from commander.services.log_writer import LogWriter


class MainWindow(QMainWindow):
    """
    Main application window.
    """
    
    def __init__(self):
        """Initialize the main window."""
        super().__init__()
        self._setup_services()
        self._setup_ui()
        self._setup_presenter()
        self._connect_signals()
        self._setup_window()
        
    def _setup_services(self):
        """Set up application services."""
        self.node_manager = NodeManager()
        self.log_writer = LogWriter(self.node_manager)
        self.status_service = StatusService()
        
    def _setup_ui(self):
        """Set up the user interface."""
        self.ui_factory = CommanderUIFactory()
        central_widget = self.ui_factory.get_main_widget()
        self.setCentralWidget(central_widget)
        
        # Set up status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
    def _setup_presenter(self):
        """Set up the main presenter."""
        self.presenter = CommanderPresenter(
            ui_factory=self.ui_factory,
            node_manager=self.node_manager,
            log_writer=self.log_writer,
            status_service=self.status_service
        )
        
    def _connect_signals(self):
        """Connect signals between components."""
        # Connect status service to status bar
        self.status_service.status_message.connect(self._show_status_message)
        
    def _show_status_message(self, message: str):
        """
        Show a status message in the status bar.
        
        Args:
            message: Message to display
        """
        self.status_bar.showMessage(message, 5000)  # Show for 5 seconds
        
    def _setup_window(self):
        """Set up window properties."""
        self.setWindowTitle("LOGReport Commander")
        self.setGeometry(100, 100, 1200, 800)
        
    def closeEvent(self, event):
        """
        Handle window close event.
        
        Args:
            event: Close event
        """
        # Clean up resources if needed
        super().closeEvent(event)