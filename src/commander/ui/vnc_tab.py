"""
VNC Tab Widget

This widget provides the VNC viewer interface with clipboard integration.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFrame, QTextEdit,
    QPushButton, QLabel, QLineEdit, QComboBox, QToolBar, QSizePolicy
)
from PyQt6.QtCore import pyqtSignal


class VNCTab(QWidget):
    """
    VNC Tab widget with clipboard integration.
    """
    
    # Signals
    connect_clicked = pyqtSignal()
    disconnect_clicked = pyqtSignal()
    copy_to_log_clicked = pyqtSignal()
    text_selected = pyqtSignal(str)  # Signal for text selection (Ctrl+C)
    
    # Recording signals
    record_clicked = pyqtSignal()
    stop_record_clicked = pyqtSignal()
    play_clicked = pyqtSignal()
    pause_clicked = pyqtSignal()
    speed_changed = pyqtSignal(float)  # Signal for playback speed change
    
    def __init__(self):
        """Initialize the VNC Tab."""
        super().__init__()
        self._setup_ui()
        
    def _setup_ui(self):
        """Set up the user interface."""
        layout = QVBoxLayout()
        
        # Create toolbar for recording controls
        self.toolbar = QToolBar()
        self.toolbar.setToolButtonStyle(3)  # ToolButtonTextBesideIcon
        layout.addWidget(self.toolbar)
        
        # Recording controls
        self.record_btn = QPushButton("● Record")
        self.record_btn.setStyleSheet("color: red; font-weight: bold;")
        self.record_btn.setCheckable(True)
        
        self.stop_btn = QPushButton("Stop")
        self.stop_btn.setEnabled(False)
        
        self.play_btn = QPushButton("▶ Play")
        self.play_btn.setEnabled(False)
        
        self.pause_btn = QPushButton("⏸ Pause")
        self.pause_btn.setEnabled(False)
        
        # Speed selector
        self.speed_combo = QComboBox()
        self.speed_combo.addItems(["0.5x", "1.0x", "1.5x", "2.0x"])
        self.speed_combo.setCurrentText("1.0x")
        self.speed_combo.setEnabled(False)
        
        # Add recording controls to toolbar
        self.toolbar.addWidget(self.record_btn)
        self.toolbar.addWidget(self.stop_btn)
        self.toolbar.addWidget(self.play_btn)
        self.toolbar.addWidget(self.pause_btn)
        self.toolbar.addWidget(QLabel("Speed:"))
        self.toolbar.addWidget(self.speed_combo)
        
        # Connection controls
        connection_frame = QFrame()
        connection_layout = QHBoxLayout()
        
        self.host_input = QLineEdit()
        self.host_input.setPlaceholderText("Host")
        
        self.port_input = QLineEdit()
        self.port_input.setPlaceholderText("Port")
        self.port_input.setText("5900")
        
        self.connect_btn = QPushButton("Connect")
        self.disconnect_btn = QPushButton("Disconnect")
        self.disconnect_btn.setEnabled(False)
        
        connection_layout.addWidget(QLabel("Host:"))
        connection_layout.addWidget(self.host_input)
        connection_layout.addWidget(QLabel("Port:"))
        connection_layout.addWidget(self.port_input)
        connection_layout.addWidget(self.connect_btn)
        connection_layout.addWidget(self.disconnect_btn)
        
        connection_frame.setLayout(connection_layout)
        layout.addWidget(connection_frame)
        
        # VNC viewer placeholder
        self.vnc_viewer = QTextEdit()
        self.vnc_viewer.setPlaceholderText("VNC Viewer Placeholder")
        self.vnc_viewer.setReadOnly(True)
        layout.addWidget(self.vnc_viewer)
        
        # Clipboard controls
        clipboard_frame = QFrame()
        clipboard_layout = QHBoxLayout()
        
        self.copy_to_log_btn = QPushButton("Copy to Logfile")
        self.log_type_combo = QComboBox()
        self.log_type_combo.addItems(["FBC", "LIS", "LOG", "RPC"])
        
        clipboard_layout.addWidget(self.copy_to_log_btn)
        clipboard_layout.addWidget(QLabel("Log Type:"))
        clipboard_layout.addWidget(self.log_type_combo)
        clipboard_layout.addStretch()
        
        clipboard_frame.setLayout(clipboard_layout)
        layout.addWidget(clipboard_frame)
        
        self.setLayout(layout)
        
        # Connect signals
        self.connect_btn.clicked.connect(self.connect_clicked.emit)
        self.disconnect_btn.clicked.connect(self.disconnect_clicked.emit)
        self.copy_to_log_btn.clicked.connect(self.copy_to_log_clicked.emit)
        
        # Connect recording signals
        self.record_btn.clicked.connect(self._on_record_clicked)
        self.stop_btn.clicked.connect(self._on_stop_clicked)
        self.play_btn.clicked.connect(self._on_play_clicked)
        self.pause_btn.clicked.connect(self._on_pause_clicked)
        self.speed_combo.currentTextChanged.connect(self._on_speed_changed)
        
        # Set up styling
        self._setup_styling()
        
    def _setup_styling(self):
        """Set up widget styling."""
        self.setStyleSheet(
            """
            QWidget {
                background-color: #2D2D30;
                color: #DCDCDC;
                font-family: Segoe UI;
            }
            QPushButton {
                background-color: #3D3D3D;
                border: 1px solid #555;
                padding: 5px 15px;
                min-width: 80px;
                color: #DCDCDC;
            }
            QPushButton:hover {
                background-color: #4D4D4D;
            }
            QPushButton:pressed {
                background-color: #2D2D2D;
            }
            QPushButton:checked {
                background-color: #5D5D5D;
                font-weight: bold;
            }
            QLineEdit, QComboBox {
                background-color: #252526;
                color: #DCDCDC;
                border: 1px solid #3E3E42;
                padding: 4px;
            }
            QTextEdit {
                background-color: #1E1E1E;
                color: #DCDCDC;
                border: 1px solid #3E3E42;
                selection-background-color: #007ACC;
            }
            QFrame {
                border: 1px solid #3E3E42;
            }
            QToolBar {
                background-color: #2D2D30;
                border: none;
                spacing: 10px;
            }
            """
        )

    def set_connection_status(self, connected: bool):
        """
        Set the connection status and update UI accordingly.
        
        Args:
            connected: Whether VNC is connected
        """
        self.connect_btn.setEnabled(not connected)
        self.disconnect_btn.setEnabled(connected)
        self.host_input.setEnabled(not connected)
        self.port_input.setEnabled(not connected)
        
    def get_host(self) -> str:
        """
        Get the host input value.
        
        Returns:
            Host value
        """
        return self.host_input.text().strip()
        
    def get_port(self) -> int:
        """
        Get the port input value.
        
        Returns:
            Port value as integer
        """
        try:
            return int(self.port_input.text().strip())
        except ValueError:
            return 5900
            
    def set_vnc_content(self, content: str):
        """
        Set the VNC viewer content.
        
        Args:
            content: Content to display in VNC viewer
        """
        self.vnc_viewer.setPlainText(content)
        
    def get_selected_text(self) -> str:
        """
        Get the currently selected text in the VNC viewer.
        
        Returns:
            Selected text
        """
        return self.vnc_viewer.textCursor().selectedText()
        
    def handle_text_selection(self, text: str):
        """
        Handle text selection in VNC viewer (emulates Ctrl+C).
        
        Args:
            text: Selected text
        """
        if text.strip():
            self.text_selected.emit(text)
            
    def _on_record_clicked(self):
        """Handle record button click."""
        if self.record_btn.isChecked():
            self.record_clicked.emit()
            self.stop_btn.setEnabled(True)
            self.play_btn.setEnabled(False)
            self.pause_btn.setEnabled(False)
            self.speed_combo.setEnabled(False)
        else:
            self.stop_record_clicked.emit()
            self.stop_btn.setEnabled(False)
            self.play_btn.setEnabled(True)
            self.speed_combo.setEnabled(True)
            
    def _on_stop_clicked(self):
        """Handle stop button click."""
        self.record_btn.setChecked(False)
        self.stop_record_clicked.emit()
        self.stop_btn.setEnabled(False)
        self.play_btn.setEnabled(True)
        self.pause_btn.setEnabled(False)
        self.speed_combo.setEnabled(True)
        
    def _on_play_clicked(self):
        """Handle play button click."""
        self.play_clicked.emit()
        self.play_btn.setEnabled(False)
        self.pause_btn.setEnabled(True)
        
    def _on_pause_clicked(self):
        """Handle pause button click."""
        self.pause_clicked.emit()
        self.play_btn.setEnabled(True)
        self.pause_btn.setEnabled(False)
        
    def _on_speed_changed(self, text):
        """Handle speed combo box change."""
        try:
            speed = float(text.replace('x', ''))
            self.speed_changed.emit(speed)
        except ValueError:
            pass
            
    def set_recording_state(self, is_recording: bool):
        """
        Set the recording state and update UI accordingly.
        
        Args:
            is_recording: Whether recording is active
        """
        self.record_btn.setChecked(is_recording)
        self.stop_btn.setEnabled(is_recording)
        self.play_btn.setEnabled(not is_recording)
        self.speed_combo.setEnabled(not is_recording)
        
    def set_playback_state(self, is_playing: bool, is_paused: bool = False):
        """
        Set the playback state and update UI accordingly.
        
        Args:
            is_playing: Whether playback is active
            is_paused: Whether playback is paused
        """
        self.play_btn.setEnabled(not is_playing or is_paused)
        self.pause_btn.setEnabled(is_playing and not is_paused)
        self.record_btn.setEnabled(not is_playing)
        self.stop_btn.setEnabled(not is_playing)