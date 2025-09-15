"""
BsTool Tab - UI for BsTool operations
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QTextEdit, QHBoxLayout, 
    QPushButton, QLineEdit, QLabel
)
from PyQt6.QtCore import pyqtSignal
from enum import Enum

from .theme import STYLESHEETS
from ..widgets import ConnectionState


class BsToolTab(QWidget):
    """
    Tab for BsTool operations
    """
    # Signals
    execute_clicked = pyqtSignal(str)  # Command to execute
    bstool_path_changed = pyqtSignal(str)  # BsTool path
    copy_to_log_clicked = pyqtSignal()
    clear_terminal_clicked = pyqtSignal()
    clear_log_clicked = pyqtSignal()

    def __init__(self):
        super().__init__()
        self._setup_ui()

    def _setup_ui(self):
        """Set up the BsTool tab UI"""
        layout = QVBoxLayout()

        # Connection/Execution Bar
        connection_layout = QHBoxLayout()
        
        # BsTool Path
        connection_layout.addWidget(QLabel("BsTool Path:"))
        self.bstool_path_edit = QLineEdit()
        self.bstool_path_edit.setPlaceholderText("e.g., C:\\Program Files\\BsTool\\bstool.exe")
        self.bstool_path_edit.textChanged.connect(self.bstool_path_changed.emit)
        connection_layout.addWidget(self.bstool_path_edit)
        
        # Environment Variable Display
        connection_layout.addWidget(QLabel("Env Var:"))
        self.env_var_label = QLabel("COMMUNICATION_LINE=AB01")
        connection_layout.addWidget(self.env_var_label)
        
        # Status indicator
        self.status_label = QLabel("\u25CB")  # Default stopped icon
        self.status_label.setStyleSheet("font-size: 16pt; color: #888;")
        connection_layout.addWidget(self.status_label)
        
        layout.addLayout(connection_layout)

        # Output Display
        self.output = QTextEdit()
        self.output.setReadOnly(True)
        self.output.setPlaceholderText("BsTool output will appear here...")
        layout.addWidget(self.output)

        # Command Input
        command_layout = QHBoxLayout()
        self.command_input = QLineEdit()
        self.command_input.setPlaceholderText("Enter command...")
        self.command_input.returnPressed.connect(self._on_execute_clicked)
        command_layout.addWidget(self.command_input)
        
        self.execute_btn = QPushButton("Execute")
        self.execute_btn.clicked.connect(self._on_execute_clicked)
        command_layout.addWidget(self.execute_btn)
        
        layout.addLayout(command_layout)

        # Action Buttons
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

    def _on_execute_clicked(self):
        """Handle execute button click"""
        command = self.command_input.text().strip()
        if command:
            self.execute_clicked.emit(command)

    def append_output(self, text):
        """Append text to the output display"""
        self.output.append(text)
        
    def clear_output(self):
        """Clear the output display"""
        self.output.clear()
        
    def get_bstool_path(self):
        """Get the current BsTool path"""
        return self.bstool_path_edit.text().strip()
        
    def get_command(self):
        """Get the current command text"""
        return self.command_input.text().strip()
        
    def clear_command(self):
        """Clear the command input"""
        self.command_input.clear()
        
    def update_status(self, state: ConnectionState):
        """Update UI based on BsTool process status"""
        # Update status indicator
        icons = {
            ConnectionState.DISCONNECTED: "\u25CB",  # ○
            ConnectionState.CONNECTING: "\u25D1",    # ◑
            ConnectionState.CONNECTED: "\u25CF",     # ●
            ConnectionState.ERROR: "\u2a2f",         # ⨯
        }
        colors = {
            ConnectionState.DISCONNECTED: "#888",   # Gray
            ConnectionState.CONNECTING: "orange",   # Orange
            ConnectionState.CONNECTED: "lime",      # Green
            ConnectionState.ERROR: "red",           # Red
        }
        self.status_label.setText(icons[state])
        self.status_label.setStyleSheet(f"font-size: 16pt; color: {colors[state]};")
        
        # Update button states
        connected = state == ConnectionState.CONNECTED
        self.execute_btn.setEnabled(connected)