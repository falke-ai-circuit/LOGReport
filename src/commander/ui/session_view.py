"""
Session View

This view provides the session interface, including VNC tab and clipboard controls.
"""

from PyQt6.QtWidgets import QTabWidget, QTextEdit, QVBoxLayout, QWidget, QHBoxLayout, QPushButton, QLabel
from PyQt6.QtCore import pyqtSignal

from commander.ui.vnc_tab import VNCTab
from commander.ui.telnet_tab import TelnetTab  # Add import for TelnetTab
from commander.ui.bstool_tab import BsToolTab  # Import BsToolTab
from .theme import STYLESHEETS

class SessionView(QWidget):
    """
    View for the session interface.
    """
    
    # Signals
    copy_to_log_clicked = pyqtSignal()
    
    # Recording signals
    record_clicked = pyqtSignal()
    stop_record_clicked = pyqtSignal()
    play_clicked = pyqtSignal()
    pause_clicked = pyqtSignal()
    speed_changed = pyqtSignal(float)
    
    def __init__(self):
        """Initialize the SessionView."""
        super().__init__()
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
        self.tab_widget.addTab(self.bstool_tab, "BsTool")

        # Create VNC tab
        self.vnc_tab = VNCTab()
        self.tab_widget.addTab(self.vnc_tab, "VNC")
        
        # Add tab widget to layout
        layout.addWidget(self.tab_widget)
        
        self.setLayout(layout)
        
        # Apply styling
        self.setStyleSheet(STYLESHEETS.get_application_stylesheet())
        
        # Connect signals
        self.vnc_tab.copy_to_log_clicked.connect(self.copy_to_log_clicked.emit)
        self.telnet_tab.copy_to_log_clicked.connect(self.copy_to_log_clicked.emit)
        
        # Connect recording signals
        self.vnc_tab.record_clicked.connect(self.record_clicked.emit)
        self.vnc_tab.stop_record_clicked.connect(self.stop_record_clicked.emit)
        self.vnc_tab.play_clicked.connect(self.play_clicked.emit)
        self.vnc_tab.pause_clicked.connect(self.pause_clicked.emit)
        self.vnc_tab.speed_changed.connect(self.speed_changed.emit)
        
    def set_vnc_content(self, content: str):
        """
        Set the VNC viewer content.
        
        Args:
            content: Content to display in VNC viewer
        """
        self.vnc_tab.set_vnc_content(content)
        
    def get_selected_text(self) -> str:
        """
        Get the currently selected text in the VNC viewer.
        
        Returns:
            Selected text
        """
        return self.vnc_tab.get_selected_text()
        
    def handle_vnc_text_selection(self, text: str):
        """
        Handle text selection in VNC viewer.
        
        Args:
            text: Selected text
        """
        self.vnc_tab.handle_text_selection(text)
        
    def set_recording_state(self, is_recording: bool):
        """
        Set the recording state and update UI accordingly.
        
        Args:
            is_recording: Whether recording is active
        """
        self.vnc_tab.set_recording_state(is_recording)
        
    def set_playback_state(self, is_playing: bool, is_paused: bool = False):
        """
        Set the playback state and update UI accordingly.
        
        Args:
            is_playing: Whether playback is active
            is_paused: Whether playback is paused
        """
        self.vnc_tab.set_playback_state(is_playing, is_paused)