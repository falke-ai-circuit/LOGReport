"""
Node Scan Widget

Per-node UI component for displaying FBC/RPC file content in table format.
Supports file selection, live comparison, and auto-refresh monitoring.
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, 
    QPushButton, QTableWidget, QTableWidgetItem, QCheckBox,
    QHeaderView
)
from PyQt5.QtCore import pyqtSignal, QTimer, Qt, QRunnable, QThreadPool, QObject
from PyQt5.QtGui import QColor, QFont
from pathlib import Path
import logging

from ..services.fbc_comparison_service import FbcComparisonService, ComparisonResult


class ComparisonWorkerSignals(QObject):
    """Signals for ComparisonWorker"""
    finished = pyqtSignal(object)  # ComparisonResult
    error = pyqtSignal(str)  # Error message


class ComparisonWorker(QRunnable):
    """Worker thread for executing comparison asynchronously"""
    
    def __init__(self, comparison_service, node_name, token_id, file_data):
        super().__init__()
        self.comparison_service = comparison_service
        self.node_name = node_name
        self.token_id = token_id
        self.file_data = file_data
        self.signals = ComparisonWorkerSignals()
    
    def run(self):
        """Execute comparison in background thread"""
        try:
            result = self.comparison_service.compare_with_live(
                self.node_name,
                self.token_id,
                self.file_data
            )
            self.signals.finished.emit(result)
        except Exception as e:
            self.signals.error.emit(str(e))


class NodeScanWidget(QWidget):
    """Widget displaying FBC/RPC data for a single node"""
    
    # Signals
    file_selected = pyqtSignal(str)  # file_path
    compare_requested = pyqtSignal()
    comparison_started = pyqtSignal()
    comparison_completed = pyqtSignal(dict)  # results
    auto_refresh_toggled = pyqtSignal(bool)  # enabled
    refresh_interval_changed = pyqtSignal(int)  # seconds
    status_message = pyqtSignal(str, int)  # message, duration
    
    def __init__(self, node_name, token_files, parser_service, telnet_service=None, parent=None):
        super().__init__(parent)
        self.node_name = node_name
        self.token_files = token_files
        self.parser_service = parser_service
        self.telnet_service = telnet_service
        self.current_data = None  # Parsed FbcTableData
        self.current_file = None
        self.logger = logging.getLogger(__name__)
        
        # Comparison service (only if telnet_service provided)
        self.comparison_service = None
        if self.telnet_service:
            self.comparison_service = FbcComparisonService(
                telnet_service=self.telnet_service,
                fbc_parser_service=self.parser_service
            )
        
        # Thread pool for async comparison
        self.thread_pool = QThreadPool()
        self.thread_pool.setMaxThreadCount(1)  # Sequential execution
        
        # Auto-refresh configuration
        self.auto_refresh_timer = QTimer()
        self.auto_refresh_timer.timeout.connect(self._on_auto_refresh_timeout)
        self.refresh_intervals = [5, 10, 30, 60, 300]  # seconds
        self.countdown_timer = QTimer()
        self.countdown_timer.timeout.connect(self._update_countdown)
        self.remaining_seconds = 0
        
        self._setup_ui()
        
        # Auto-load most recent file
        if self.token_files:
            self._load_most_recent_file()
    
    def _setup_ui(self):
        """Create file selector, table view, compare button, auto-refresh controls"""
        layout = QVBoxLayout()
        
        # Top control bar
        control_layout = QHBoxLayout()
        
        # File selector
        control_layout.addWidget(QLabel("File:"))
        self.file_selector = QComboBox()
        self.file_selector.addItems([Path(f).name for f in self.token_files])
        self.file_selector.currentIndexChanged.connect(self._on_file_selected)
        control_layout.addWidget(self.file_selector, stretch=2)
        
        # Compare button
        self.compare_btn = QPushButton("Compare Live")
        self.compare_btn.clicked.connect(self._on_compare_clicked)
        self.compare_btn.setEnabled(False)  # Enable after file loads
        control_layout.addWidget(self.compare_btn)
        
        # Match percentage label
        self.match_label = QLabel("")
        self.match_label.setStyleSheet("font-weight: bold; color: #4CAF50;")
        control_layout.addWidget(self.match_label)
        
        control_layout.addStretch()
        layout.addLayout(control_layout)
        
        # Auto-refresh controls
        refresh_layout = QHBoxLayout()
        
        self.auto_refresh_checkbox = QCheckBox("Auto-refresh")
        self.auto_refresh_checkbox.toggled.connect(self._on_auto_refresh_toggled)
        self.auto_refresh_checkbox.setStyleSheet("""
            QCheckBox {
                color: #DCDCDC;
                background-color: transparent;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                background-color: #252526;
                border: 1px solid #3E3E42;
            }
            QCheckBox::indicator:checked {
                background-color: #007ACC;
                border: 1px solid #007ACC;
            }
            QCheckBox::indicator:hover {
                border: 1px solid #007ACC;
            }
        """)
        refresh_layout.addWidget(self.auto_refresh_checkbox)
        
        refresh_layout.addWidget(QLabel("Interval:"))
        self.interval_selector = QComboBox()
        self.interval_selector.addItems(["5s", "10s", "30s", "60s", "5min"])
        self.interval_selector.setCurrentIndex(2)  # Default: 30s
        self.interval_selector.currentIndexChanged.connect(self._on_interval_changed)
        refresh_layout.addWidget(self.interval_selector)
        
        self.countdown_label = QLabel("")
        self.countdown_label.setStyleSheet("color: #888;")
        refresh_layout.addWidget(self.countdown_label)
        
        refresh_layout.addStretch()
        layout.addLayout(refresh_layout)
        
        # Metadata display
        self.metadata_label = QLabel("")
        self.metadata_label.setStyleSheet("color: #888; font-size: 9pt;")
        layout.addWidget(self.metadata_label)
        
        # Table widget
        self.table_widget = QTableWidget()
        self.table_widget.setAlternatingRowColors(True)
        
        # Set monospace font for proper alignment
        monospace_font = QFont("Courier New", 9)
        monospace_font.setStyleHint(QFont.Monospace)
        monospace_font.setFixedPitch(True)
        self.table_widget.setFont(monospace_font)
        
        # Apply dark theme styling to table
        self.table_widget.setStyleSheet("""
            QTableWidget {
                background-color: #1E1E1E;
                alternate-background-color: #252526;
                color: #DCDCDC;
                gridline-color: #3E3E42;
                border: 1px solid #3E3E42;
            }
            QTableWidget::item {
                padding: 4px;
            }
            QTableWidget::item:selected {
                background-color: #5D5D5D;
            }
            QHeaderView::section {
                background-color: #3D3D3D;
                color: #DCDCDC;
                padding: 6px;
                border: 1px solid #3E3E42;
                font-weight: bold;
            }
            QTableCornerButton::section {
                background-color: #3D3D3D;
                border: 1px solid #3E3E42;
            }
        """)
        
        layout.addWidget(self.table_widget)
        
        # Legend (Phase 3 comparison colors)
        legend_layout = QHBoxLayout()
        legend_layout.addWidget(QLabel("Legend:"))
        
        legend_items = [
            ("🟢", "Match", "#4CAF50"),
            ("🟡", "Difference", "#FFC107"),
            ("🔴", "Error", "#F44336")
        ]
        
        for icon, text, color in legend_items:
            label = QLabel(f"{icon} {text}")
            label.setStyleSheet(f"color: {color};")
            legend_layout.addWidget(label)
        
        legend_layout.addStretch()
        layout.addLayout(legend_layout)
        
        # Status bar
        self.status_label = QLabel("")
        self.status_label.setStyleSheet("color: #888; font-size: 9pt;")
        layout.addWidget(self.status_label)
        
        self.setLayout(layout)
    
    def _load_most_recent_file(self):
        """Load the most recent file based on filename timestamp"""
        if not self.token_files:
            return
        
        # Sort files by modification time (most recent first)
        sorted_files = sorted(self.token_files, key=lambda f: Path(f).stat().st_mtime, reverse=True)
        most_recent = sorted_files[0]
        
        # Find index in combobox
        filename = Path(most_recent).name
        index = self.file_selector.findText(filename)
        if index >= 0:
            self.file_selector.setCurrentIndex(index)
    
    def _on_file_selected(self, index):
        """Handle file selection change"""
        if index < 0 or index >= len(self.token_files):
            return
        
        file_path = self.token_files[index]
        self.load_token_file(file_path)
    
    def load_token_file(self, file_path: str):
        """Parse and display .fbc or .rpc file in table"""
        try:
            self.logger.info(f"Loading file: {file_path}")
            
            # Parse file
            self.current_data = self.parser_service.parse_file(file_path)
            self.current_file = file_path
            
            # Display metadata
            file_type_label = "FBC (I/O Configuration)" if self.current_data.file_type == 'FBC' else "RPC (Error Counters)"
            metadata_text = (
                f"<b>{file_type_label}</b> | "
                f"Timestamp: {self.current_data.timestamp} | "
                f"Agent: {self.current_data.agent_id} | "
                f"Command: {self.current_data.command}"
            )
            self.metadata_label.setText(metadata_text)
            
            # Create table
            self._create_table_from_data(self.current_data)
            
            # Enable compare button
            self.compare_btn.setEnabled(True)
            
            # Update status
            file_name = Path(file_path).name
            row_count = len(self.current_data.rows)
            self.status_label.setText(f"Loaded {file_name}: {row_count} rows")
            
            # Emit signal
            self.file_selected.emit(file_path)
            
            # Restart auto-refresh if enabled
            if self.auto_refresh_checkbox.isChecked():
                self._restart_auto_refresh()
            
        except Exception as e:
            self.logger.error(f"Failed to load file {file_path}: {e}")
            self.status_message.emit(f"Error loading file: {e}", 5000)
    
    def _create_table_from_data(self, data):
        """Populate QTableWidget from parsed data"""
        # Clear existing table
        self.table_widget.clear()
        self.table_widget.setRowCount(0)
        self.table_widget.setColumnCount(0)
        
        if not data.headers or not data.rows:
            self.table_widget.setRowCount(1)
            self.table_widget.setColumnCount(1)
            self.table_widget.setItem(0, 0, QTableWidgetItem("No data available"))
            return
        
        # Set table dimensions
        self.table_widget.setRowCount(len(data.rows))
        self.table_widget.setColumnCount(len(data.headers))
        self.table_widget.setHorizontalHeaderLabels(data.headers)
        
        # Populate table cells
        for row_idx, row_data in enumerate(data.rows):
            for col_idx, header in enumerate(data.headers):
                value = row_data.get(header, '')
                item = QTableWidgetItem(str(value))
                
                # Center alignment for better readability
                item.setTextAlignment(Qt.AlignCenter)
                
                # Default background (dark theme, not compared state)
                # Use alternating row colors for better readability
                if row_idx % 2 == 0:
                    item.setBackground(QColor("#1E1E1E"))  # Dark background
                else:
                    item.setBackground(QColor("#252526"))  # Slightly lighter alternate
                
                self.table_widget.setItem(row_idx, col_idx, item)
        
        # Resize columns to content
        self.table_widget.resizeColumnsToContents()
        
        # Adjust column widths for better display
        header = self.table_widget.horizontalHeader()
        for col in range(len(data.headers)):
            header.setSectionResizeMode(col, QHeaderView.Interactive)
        
        # Display totals if available
        if data.totals:
            self._display_totals(data)
    
    def _display_totals(self, data):
        """Display totals information below table"""
        if data.file_type == 'FBC':
            totals = data.totals
            total_text = ""
            if 'total_units' in totals:
                total_text = (
                    f"Total: {totals['total_units']} I/O-units, "
                    f"{totals['total_channels']} Channels "
                    f"({totals['input_channels']} in, {totals['output_channels']} out)"
                )
            self.status_label.setText(total_text)
        elif data.file_type == 'RPC':
            totals = data.totals
            if 'unknown_command' in totals:
                self.status_label.setText(f"Unknown command: {totals['unknown_command']}")
    
    def _on_compare_clicked(self):
        """Handle Compare Live button click"""
        if not self.current_data or not self.comparison_service:
            self.status_message.emit("Cannot compare: no data or comparison service", 3000)
            return
        
        # Auto-connect to telnet if not connected
        if self.telnet_service:
            is_connected = (hasattr(self.telnet_service, 'telnet_session') and 
                          self.telnet_service.telnet_session and 
                          self.telnet_service.telnet_session.is_connected)
            
            if not is_connected:
                self.logger.info("Telnet not connected, attempting auto-connect...")
                self.status_message.emit("Connecting to telnet debugger...", 3000)
                
                # Use existing auto-connect method
                success = self.telnet_service._ensure_debugger_connection()
                if not success:
                    self.status_message.emit("✗ Failed to connect to telnet debugger", 5000)
                    return
                
                self.logger.info("Auto-connect successful")
                self.status_message.emit("Connected to telnet debugger", 2000)
        
        # Extract token ID from file or command
        token_id = self._extract_token_id()
        if not token_id:
            self.status_message.emit("Cannot extract token ID from file", 3000)
            return
        
        self.logger.info(f"Compare requested for {self.node_name}, token {token_id}, file type: {self.current_data.file_type}")
        
        # Disable button during comparison
        self.compare_btn.setEnabled(False)
        self.compare_btn.setText("Comparing...")
        self.match_label.setText("⏳")
        
        # Emit signal
        self.comparison_started.emit()
        
        # Create worker for async comparison
        worker = ComparisonWorker(
            self.comparison_service,
            self.node_name,
            token_id,
            self.current_data
        )
        
        # Connect signals
        worker.signals.finished.connect(self._on_comparison_finished)
        worker.signals.error.connect(self._on_comparison_error)
        
        # Start worker in thread pool
        self.thread_pool.start(worker)
    
    def _extract_token_id(self) -> str:
        """Extract token ID from current file or data"""
        if not self.current_data:
            return ""
        
        # Try to extract from command
        if self.current_data.command:
            # FBC: "print from fbc io structure 0010000" -> "001"
            # RPC: "print from fbc rupi counters 0010000" -> "001"
            import re
            match = re.search(r'(\d{3})\d{4}$', self.current_data.command)
            if match:
                return match.group(1)
        
        # Try to extract from filename
        if self.current_file:
            # AP01m_FBC_001_20251014_103000.fbc -> "001"
            filename = Path(self.current_file).stem
            parts = filename.split('_')
            for part in parts:
                if part.isdigit() and len(part) == 3:
                    return part
        
        return ""
    
    def _on_comparison_finished(self, result: ComparisonResult):
        """Handle comparison completion"""
        self.logger.info(f"Comparison finished: success={result.success}, match={result.match_percentage:.1f}%")
        
        # Re-enable button
        self.compare_btn.setEnabled(True)
        self.compare_btn.setText("Compare Live")
        
        if result.success:
            # Apply color coding to table
            self.apply_comparison_results(result.to_dict())
            
            # Update match label
            self.match_label.setText(f"✓ {result.match_percentage:.0f}%")
            
            # Status message
            self.status_message.emit(
                f"Comparison complete: {result.match_percentage:.1f}% match "
                f"({len(result.matches)} matches, {len(result.differences)} differences, {len(result.errors)} errors)",
                5000
            )
        else:
            # Show error
            self.match_label.setText("✗")
            self.status_message.emit(f"Comparison failed: {result.error_message}", 5000)
    
    def _on_comparison_error(self, error_msg: str):
        """Handle comparison error"""
        self.logger.error(f"Comparison error: {error_msg}")
        
        # Re-enable button
        self.compare_btn.setEnabled(True)
        self.compare_btn.setText("Compare Live")
        self.match_label.setText("✗")
        
        # Show error
        self.status_message.emit(f"Comparison error: {error_msg}", 5000)
    
    def _on_auto_refresh_toggled(self, checked):
        """Handle auto-refresh checkbox toggle"""
        if checked:
            self._start_auto_refresh()
        else:
            self._stop_auto_refresh()
        
        self.auto_refresh_toggled.emit(checked)
    
    def _on_interval_changed(self, index):
        """Handle refresh interval change"""
        if index >= 0 and index < len(self.refresh_intervals):
            interval_seconds = self.refresh_intervals[index]
            self.refresh_interval_changed.emit(interval_seconds)
            
            # Restart auto-refresh if enabled
            if self.auto_refresh_checkbox.isChecked():
                self._restart_auto_refresh()
    
    def _start_auto_refresh(self):
        """Start periodic comparison with selected interval"""
        interval_index = self.interval_selector.currentIndex()
        interval_seconds = self.refresh_intervals[interval_index]
        
        self.auto_refresh_timer.start(interval_seconds * 1000)
        self.remaining_seconds = interval_seconds
        self.countdown_timer.start(1000)  # Update every second
        
        self.logger.info(f"Auto-refresh started with {interval_seconds}s interval")
        self._update_countdown()
    
    def _stop_auto_refresh(self):
        """Stop auto-refresh timer"""
        self.auto_refresh_timer.stop()
        self.countdown_timer.stop()
        self.countdown_label.setText("")
        self.logger.info("Auto-refresh stopped")
    
    def _restart_auto_refresh(self):
        """Restart auto-refresh with current settings"""
        if self.auto_refresh_checkbox.isChecked():
            self._stop_auto_refresh()
            self._start_auto_refresh()
    
    def _on_auto_refresh_timeout(self):
        """Triggered when auto-refresh interval elapses"""
        self.logger.debug("Auto-refresh timeout - triggering comparison")
        self._on_compare_clicked()
        
        # Reset countdown
        interval_index = self.interval_selector.currentIndex()
        self.remaining_seconds = self.refresh_intervals[interval_index]
    
    def _update_countdown(self):
        """Update countdown display"""
        if self.remaining_seconds > 0:
            self.countdown_label.setText(f"Next: {self.remaining_seconds}s")
            self.remaining_seconds -= 1
        else:
            self.countdown_label.setText("Next: 0s")
    
    def apply_comparison_results(self, results: dict):
        """
        Highlight table cells based on comparison results.
        Changes text color only (not cell background) for inner table values.
        
        Args:
            results: Dictionary from ComparisonResult.to_dict()
                {
                    'matches': [(row, col), ...],
                    'differences': [(row, col, file_val, live_val), ...],
                    'errors': [(row, col, error_msg), ...]
                }
        """
        self.logger.debug(f"Applying comparison results: {len(results.get('matches', []))} matches, "
                         f"{len(results.get('differences', []))} differences, {len(results.get('errors', []))} errors")
        
        matches = results.get('matches', [])
        differences = results.get('differences', [])
        errors = results.get('errors', [])
        
        # Get headers to identify PIC column
        headers = []
        if self.current_data and self.current_data.headers:
            headers = [h.upper() for h in self.current_data.headers]
        
        # Color text based on comparison (skip PIC column)
        for row, col in matches:
            item = self.table_widget.item(row, col)
            if item:
                # Check if this is PIC column (should not be colored)
                header = self.table_widget.horizontalHeaderItem(col)
                if header and header.text().upper() != 'PIC':
                    item.setForeground(QColor("#4CAF50"))  # Green text
                    item.setToolTip("Match: File and live data are identical")
        
        for row, col, file_val, live_val in differences:
            item = self.table_widget.item(row, col)
            if item:
                # Check if this is PIC column (should not be colored)
                header = self.table_widget.horizontalHeaderItem(col)
                if header and header.text().upper() != 'PIC':
                    item.setForeground(QColor("#FFC107"))  # Yellow text
                    item.setToolTip(f"Difference:\nFile: {file_val}\nLive: {live_val}")
        
        for row, col, error_msg in errors:
            item = self.table_widget.item(row, col)
            if item:
                # Check if this is PIC column (should not be colored)
                header = self.table_widget.horizontalHeaderItem(col)
                if header and header.text().upper() != 'PIC':
                    item.setForeground(QColor("#F44336"))  # Red text
                    item.setToolTip(f"Error: {error_msg}")
        
        # Calculate and display match percentage
        total_cells = len(matches) + len(differences) + len(errors)
        if total_cells > 0:
            match_pct = (len(matches) / total_cells) * 100
            self.match_label.setText(f"✓ {match_pct:.0f}%")
        
        # Emit signal
        self.comparison_completed.emit(results)
    
    def update_file_list(self, token_files):
        """Update available file list"""
        self.token_files = token_files
        
        # Update combobox
        current_file = self.current_file
        self.file_selector.clear()
        self.file_selector.addItems([Path(f).name for f in token_files])
        
        # Restore selection if file still exists
        if current_file and current_file in token_files:
            filename = Path(current_file).name
            index = self.file_selector.findText(filename)
            if index >= 0:
                self.file_selector.setCurrentIndex(index)
        elif token_files:
            self._load_most_recent_file()
    
    def select_file_and_compare(self, file_path: str) -> bool:
        """
        Select file from dropdown and trigger immediate comparison.
        Called from context menu "Scan FieldBus structure" action.
        
        Args:
            file_path: Full path to the .fbc or .rpc file
            
        Returns:
            bool: True if file was found and comparison triggered, False otherwise
        """
        from pathlib import Path
        import logging
        
        logger = logging.getLogger(__name__)
        filename = Path(file_path).name
        
        # Find file in combobox
        index = self.file_selector.findText(filename)
        if index == -1:
            logger.warning(f"File {filename} not found in file selector dropdown")
            return False
        
        # Select file in dropdown
        self.file_selector.setCurrentIndex(index)
        logger.info(f"Selected file {filename} in dropdown (index {index})")
        
        # Trigger file load (this calls _on_file_selected)
        # _on_file_selected will load the file content into the table
        self._on_file_selected(index)
        
        # Trigger comparison immediately
        self._on_compare_clicked()
        logger.info(f"Triggered comparison for {filename}")
        
        return True
