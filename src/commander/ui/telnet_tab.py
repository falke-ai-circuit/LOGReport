"""
Telnet Tab - UI for Telnet sessions
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QTextEdit, QHBoxLayout, 
    QPushButton, QLineEdit, QLabel
)
from PyQt6.QtCore import pyqtSignal
from PyQt6.QtGui import QFont

from .theme import STYLESHEETS

class TelnetTab(QWidget):
    """
    Tab for Telnet session management
    """
    # Signals
    execute_clicked = pyqtSignal()
    connect_clicked = pyqtSignal(bool)  # True=connect, False=disconnect
    copy_to_log_clicked = pyqtSignal()
    clear_terminal_clicked = pyqtSignal()
    clear_log_clicked = pyqtSignal()

    def __init__(self):
        super().__init__()
        self._setup_ui()

    def _setup_ui(self):
        """Set up the Telnet tab UI"""
        layout = QVBoxLayout()

        # Connection bar
        connection_layout = QHBoxLayout()
        connection_layout.addWidget(QLabel("IP:"))
        self.ip_edit = QLineEdit()
        self.ip_edit.setPlaceholderText("IP Address")
        connection_layout.addWidget(self.ip_edit)
        
        connection_layout.addWidget(QLabel("Port:"))
        self.port_edit = QLineEdit()
        self.port_edit.setPlaceholderText("Port")
        self.port_edit.setText("23")
        connection_layout.addWidget(self.port_edit)
        
        self.connect_btn = QPushButton("Connect")
        self.connect_btn.clicked.connect(lambda: self.connect_clicked.emit(True))
        connection_layout.addWidget(self.connect_btn)
        
        self.disconnect_btn = QPushButton("Disconnect")
        self.disconnect_btn.clicked.connect(lambda: self.connect_clicked.emit(False))
        connection_layout.addWidget(self.disconnect_btn)
        
        # Status indicator
        self.status_label = QLabel("\u25CB")  # Default disconnected icon
        self.status_label.setStyleSheet("font-size: 16pt; color: #888;")
        connection_layout.addWidget(self.status_label)
        
        layout.addLayout(connection_layout)

        # Telnet output
        self.output = QTextEdit()
        self.output.setReadOnly(True)
        
        # Set monospace font for proper ASCII table formatting
        monospace_font = QFont("Courier New", 10)  # Use Courier New as primary font
        monospace_font.setStyleHint(QFont.StyleHint.Monospace)
        monospace_font.setFixedPitch(True)  # Ensure fixed-pitch rendering
        self.output.setFont(monospace_font)
        
        layout.addWidget(self.output)

        # Command input
        command_layout = QHBoxLayout()
        self.command_input = QLineEdit()
        self.command_input.setPlaceholderText("Enter command...")
        command_layout.addWidget(self.command_input)
        
        self.execute_btn = QPushButton("Execute")
        self.execute_btn.clicked.connect(self.execute_clicked.emit)
        command_layout.addWidget(self.execute_btn)
        
        layout.addLayout(command_layout)

        # Action buttons
        button_layout = QHBoxLayout()
        self.copy_btn = QPushButton("Copy to Log")
        self.copy_btn.clicked.connect(self.copy_to_log_clicked.emit)
        button_layout.addWidget(self.copy_btn)
        
        self.clear_terminal_btn = QPushButton("Clear Terminal")
        self.clear_terminal_btn.clicked.connect(self.clear_terminal_clicked.emit)
        button_layout.addWidget(self.clear_terminal_btn)
        
        self.clear_log_btn = QPushButton("Clear Log")
        self.clear_log_btn.clicked.connect(self.clear_log_clicked.emit)
        button_layout.addWidget(self.clear_log_btn)
        
        layout.addLayout(button_layout)

        self.setLayout(layout)
        
        # Apply styling
        self.setStyleSheet(STYLESHEETS.get_telnet_tab_stylesheet())

    def append_output(self, text):
        """
        Append text to the telnet output with preserved formatting.
        
        Uses plain text insertion to preserve whitespace and monospace formatting
        for ASCII tables and structured command output.
        """
        # Convert tabs to spaces (8 spaces per tab) for consistent alignment
        text_with_spaces = text.replace('\t', ' ' * 8)
        
        # Move cursor to end
        cursor = self.output.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        self.output.setTextCursor(cursor)
        
        # Insert as plain text to preserve all whitespace and formatting
        self.output.insertPlainText(text_with_spaces + "\n")
        
        # Scroll to bottom to show new content
        self.output.ensureCursorVisible()
        
    def get_command(self):
        """Get the current command text"""
        return self.command_input.text().strip()
        
    def clear_command(self):
        """Clear the command input"""
        self.command_input.clear()
        
    def get_connection_info(self):
        """Get IP and port for connection"""
        return self.ip_edit.text().strip(), self.port_edit.text().strip()
        
    def update_connection_status(self, state):
        """Update UI based on connection status"""
        from ..widgets import ConnectionState
        
        # Update status indicator
        icons = {
            ConnectionState.DISCONNECTED: "\u25CB",  # ○
            ConnectionState.CONNECTING: "\u25D1",    # ◑
            ConnectionState.CONNECTED: "\u25CF",    # ●
            ConnectionState.ERROR: "\u2a2f",       # ⨯
        }
        colors = {
            ConnectionState.DISCONNECTED: "#888",   # Gray
            ConnectionState.CONNECTING: "orange",  # Orange
            ConnectionState.CONNECTED: "lime",     # Green
            ConnectionState.ERROR: "red",         # Red
        }
        self.status_label.setText(icons[state])
        self.status_label.setStyleSheet(f"font-size: 16pt; color: {colors[state]};")
        
        # Update button states
        connected = state == ConnectionState.CONNECTED
        self.connect_btn.setEnabled(not connected)
        self.disconnect_btn.setEnabled(connected)
        self.ip_edit.setEnabled(not connected)
        self.port_edit.setEnabled(not connected)