"""
Commander Window - Main UI view for the Commander application
"""
from PyQt6.QtWidgets import QMainWindow, QStatusBar, QFileDialog
from PyQt6.QtCore import QSettings, pyqtSignal

from ..services.context_menu_service import ContextMenuService
from ..services.context_menu_filter import ContextMenuFilterService
from ..services.fbc_command_service import FbcCommandService
from ..services.rpc_command_service import RpcCommandService
from ..services.commander_service import CommanderService
from ..services.telnet_service import TelnetService
from ..services.status_service import StatusService
from ..services.bstool_command_service import BsToolCommandService
from ..presenters.commander_presenter import CommanderPresenter
from ..presenters.node_tree_presenter import NodeTreePresenter

import sys
import os
import logging

# Import our components
from ..node_manager import NodeManager
from ..session_manager import SessionManager
from ..log_writer import LogWriter
from ..command_queue import CommandQueue

# Centralized Qt application initialization
from ..qt_init import initialize_qt

# Centralized theme
from .theme import STYLESHEETS

class CommanderWindow(QMainWindow):
    """Main Commander window view."""
    
    # Signal for status messages
    status_message_signal = pyqtSignal(str, int)
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Commander LogCreator v1.0")
        self.setMinimumSize(1200, 800)
        
        # Configure logging
        logging.basicConfig(
            level=logging.DEBUG,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            encoding='utf-8'
        )
        
        # Load application settings
        self.settings = QSettings("CommanderLogCreator", "Settings")
        
        # Core components
        self.node_manager = NodeManager()
        self.session_manager = SessionManager()
        self.command_queue = CommandQueue(self.session_manager, parent=self)
        self.log_writer = LogWriter(self.node_manager)
        self.current_token = None
        
        # Initialize all components
        # Initialize all components
        print("[DEBUG] Starting component initialization")
        self._initialize_components()
        print("[DEBUG] Component initialization complete")
        self._initialize_components()
    
    def _initialize_components(self):
        """Initialize all services and presenters"""
        # Initialize Status Service
        self.status_service = StatusService()
        
        # Initialize context menu filter service
        self.context_menu_filter = ContextMenuFilterService()
        
        # Initialize FBC and RPC services
        self.fbc_service = FbcCommandService(self.node_manager, self.command_queue, self.log_writer, self)
        self.rpc_service = RpcCommandService(self.node_manager, self.command_queue, self)
        
        # Initialize BsTool service
        self.bstool_service = BsToolCommandService(self.log_writer, self)
        
        # Initialize services through commander service
        self.commander_service = CommanderService(
            self.node_manager,
            self.session_manager,
            self.command_queue,
            self.log_writer,
            self.fbc_service,
            self.rpc_service
        )
        
        # Initialize Telnet Service
        self.telnet_service = TelnetService(self.session_manager)
        
        # Initialize context menu service
        self.context_menu_service = ContextMenuService(self.node_manager, self.context_menu_filter)
        
        # Setup UI first
        self.init_ui()
        
        # Connect status service AFTER UI is created
        self.status_service.status_updated.connect(self.statusBar().showMessage)
        
        # Initialize presenters after UI is created
        self.commander_presenter = CommanderPresenter(
            self.ui_factory,
            self.node_manager,
            self.log_writer,
            self.status_service,
            self.session_manager,
            self.command_queue,
            self.fbc_service,
            self.rpc_service,
            self.context_menu_service,
            self.bstool_service
        )
        
        self.node_tree_presenter = NodeTreePresenter(
            self.node_tree_view,
            self.node_manager,
            self.session_manager,
            self.log_writer,
            self.command_queue,
            self.fbc_service,
            self.rpc_service,
            self.context_menu_service,
            self.bstool_service
        )
        
        # Set presenter in context menu service
        self.context_menu_service.set_presenter(self.node_tree_presenter)
        
        # Connect VNC tab signals
        self._connect_vnc_signals()
        
        # Connect all signals
        self._connect_signals()
        
        # Load configurations
        self._load_configurations()
    
    def _connect_signals(self):
        """Connect all signals"""
        # Connect commander service signals to presenter
        self.commander_service.set_cmd_input_text.connect(self.set_cmd_input_text_signal)
        self.commander_service.switch_to_telnet_tab.connect(self.switch_to_telnet_tab_signal)
        self.commander_service.focus_command_input.connect(self.set_cmd_focus_signal)
        self.commander_service.status_message.connect(self.status_service.status_updated)
        self.commander_service.report_error.connect(lambda msg: self.status_service.show_error("Commander Service Error: " + msg))
        self.commander_service.command_finished.connect(self.on_telnet_command_finished)
        self.commander_service.queue_processed.connect(self.on_queue_processed)
        
        # Connect presenter signals
        self.commander_presenter.status_message_signal.connect(self.status_service.status_updated)
        self.commander_presenter.set_cmd_input_text_signal.connect(self.telnet_tab.command_input.setText)
        self.commander_presenter.update_connection_status_signal.connect(self.telnet_tab.update_connection_status)
        self.commander_presenter.switch_to_telnet_tab_signal.connect(lambda: self.session_tabs.setCurrentWidget(self.telnet_tab))
        self.commander_presenter.set_cmd_focus_signal.connect(self.telnet_tab.command_input.setFocus)
        
        # Connect node tree presenter signals
        self.node_tree_presenter.status_message_signal.connect(self.status_service.status_updated)
        self.node_tree_presenter.node_tree_updated_signal.connect(self.on_node_tree_updated)
        self.node_tree_presenter.log_file_selected_signal.connect(self.session_manager.ip_changed.emit)
        
        # Connect view signals to window methods
        self.command_finished.connect(self.on_telnet_command_finished)
        self.set_cmd_input_text_signal.connect(self.telnet_tab.command_input.setText)
        self.update_connection_status_signal.connect(self.telnet_tab.update_connection_status)
        self.switch_to_telnet_tab_signal.connect(lambda: self.session_tabs.setCurrentWidget(self.telnet_tab))
        self.status_message_signal.connect(self.status_service.status_updated)
        
        # Connect telnet service signals properly
        self.telnet_service.status_message_signal.connect(self.status_service.status_updated)
        self.telnet_service.command_finished_signal.connect(self.command_finished)
        self.telnet_service.update_connection_status_signal.connect(self.telnet_tab.update_connection_status)
        
        # Connect Telnet tab signals
        self.telnet_tab.execute_clicked.connect(self.execute_telnet_command)
        self.telnet_tab.connect_clicked.connect(self.toggle_telnet_connection)
        self.telnet_tab.copy_to_log_clicked.connect(self.copy_to_log)
        self.telnet_tab.clear_terminal_clicked.connect(self.clear_terminal)
        self.telnet_tab.clear_log_clicked.connect(self.clear_node_log)
        
        # Connect UI component signals
        self._connect_ui_signals()
        
    def _connect_vnc_signals(self):
        """Connect VNC tab signals to session manager"""
        # Connect VNC tab connect signal to session manager
        self.vnc_tab.connect_clicked.connect(self.toggle_vnc_connection)
        
        # TODO: Re-implement this when VNC tab has update_log_filename method
        # self.session_manager.ip_changed.connect(self.vnc_tab.update_log_filename)
    
    def _connect_ui_signals(self):
        """Connect UI component signals"""
        # Node tree view signals
        self.node_tree_view.load_nodes_clicked.connect(self.load_configuration)
        self.node_tree_view.set_log_root_clicked.connect(self.set_log_root_folder)
        self.node_tree_view.node_selected.connect(self.on_node_selected)
        self.node_tree_view.node_double_clicked.connect(self._on_node_double_clicked)
        self.node_tree_view.context_menu_requested.connect(self.show_context_menu)
        
        # TODO: Re-implement when UI buttons are available
        # self.execute_btn.clicked.connect(self.execute_telnet_command)
        # self.telnet_connection_bar.connection_requested.connect(self.toggle_telnet_connection)
        # self.copy_to_log_btn.clicked.connect(self.copy_to_log)
        # self.clear_terminal_btn.clicked.connect(self.clear_terminal)
        # self.clear_node_log_btn.clicked.connect(self.clear_node_log)
    
    def _load_configurations(self):
        """Load all configurations"""
        try:
            # Load saved configuration path if exists
            saved_config = self.settings.value("config_path", "")
            if saved_config and os.path.exists(saved_config):
                self.node_manager.set_config_path(saved_config)
            
            # Load saved log root if exists
            saved_log_root = self.settings.value("log_root", "")
            if saved_log_root and os.path.isdir(saved_log_root):
                self.node_manager.set_log_root(saved_log_root)
                # Scan for log files and populate node tree when log root is loaded
                self.node_manager.scan_log_files()
                self.populate_node_tree()
            elif os.path.exists(self.node_manager.config_path):
                # Only load configuration if no saved log root or log root is invalid
                if self.node_manager.load_configuration():
                    self.node_manager.scan_log_files()
                    self.populate_node_tree()
        except Exception as e:
            logging.error(f"Error loading default configuration: {e}")
            
        # Load saved Telnet IP and port if they exist
        telnet_ip = self.settings.value("telnet_ip", "")
        telnet_port = self.settings.value("telnet_port", "")
        if telnet_ip:
            self.telnet_tab.ip_edit.setText(telnet_ip)
        if telnet_port:
            self.telnet_tab.port_edit.setText(telnet_port)
    
    def init_ui(self):
        """Initialize the main UI components"""
        # Create main layout
        from commander.ui.commander_ui_factory import CommanderUIFactory
        self.ui_factory = CommanderUIFactory()
        main_widget = self.ui_factory.get_main_widget()
        self.setCentralWidget(main_widget)
        
        # Get references to UI components
        self.node_tree_view = self.ui_factory.node_tree_view
        self.session_view = self.ui_factory.session_view
        self.vnc_tab = self.ui_factory.vnc_tab
        
        # Access components from session_view
        self.session_tabs = self.session_view.tab_widget
        self.telnet_tab = self.session_view.telnet_tab
        self.vnc_tab = self.session_view.vnc_tab
        
        # Status Bar
        self.setStatusBar(QStatusBar())
        self.status_service.show_message("Welcome to Commander LogCreator")
    
    # Signal definitions (to be connected by presenter)
    set_cmd_input_text_signal = pyqtSignal(str)
    update_connection_status_signal = pyqtSignal(object)  # ConnectionState
    switch_to_telnet_tab_signal = pyqtSignal()
    set_cmd_focus_signal = pyqtSignal()
    command_finished = pyqtSignal(str, bool)
    queue_processed = pyqtSignal(int, int)  # Success count, total
    
    # Delegated methods to presenter
    # TODO: Implement in CommanderPresenter
    def load_configuration(self):
        """Open file dialog to select node configuration and load it"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Node Configuration", "", "JSON Files (*.json)"
        )
        if file_path:
            self.node_tree_presenter.load_configuration(file_path)
    
    def set_log_root_folder(self):
        """Set the root folder for log files"""
        folder_path = QFileDialog.getExistingDirectory(self, "Select Log Root Folder")
        if folder_path:
            self.node_tree_presenter.set_log_root_folder(folder_path)
    
    def show_context_menu(self, position):
        """Show context menu for the selected item in the node tree"""
        self.node_tree_presenter.show_context_menu(position)
    
    def populate_node_tree(self):
        """Lazy-loading tree population - only loads top-level nodes initially"""
        self.node_tree_presenter.populate_node_tree()
    
    def _on_node_double_clicked(self, item):
        """Wrapper method to handle node double-click events"""
        self.node_tree_presenter.open_log_file(item, 0)
    
    def on_node_selected(self, item):
        """Handles node/token selection in left pane"""
        self.node_tree_presenter.on_node_selected(item)
    
    def toggle_telnet_connection(self, connect: bool):
        """Toggles connection/disconnection for Telnet tab"""
        ip, port = self.telnet_tab.get_connection_info()
        self.telnet_service.toggle_connection(connect, ip, port, self.settings)
    
    def toggle_vnc_connection(self, connect: bool):
        """Toggles connection/disconnection for VNC tab"""
        if connect:
            # Get IP and port from VNC tab
            ip = self.vnc_tab.ip_edit.text()
            port_text = self.vnc_tab.port_edit.text()
            
            try:
                port = int(port_text) if port_text else 5900
            except ValueError:
                self.vnc_tab.add_log_message("Error: Invalid port number")
                return
            
            # Create session config
            from ..session_manager import SessionConfig, SessionType
            config = SessionConfig(
                host=ip,
                port=port,
                session_type=SessionType.VNC
            )
            
            # Create VNC session
            session = self.session_manager.create_session(config, auto_connect=True)
            if session:
                self.vnc_tab.add_log_message(f"Connected to VNC server at {ip}:{port}")
                self.vnc_tab.update_connection_status("Connected", True)
                
                # Connect session state change signal to VNC tab
                session.connection_state_changed.connect(
                    lambda connected: self.vnc_tab.update_connection_status(
                        "Connected" if connected else "Disconnected", connected
                    )
                )
            else:
                self.vnc_tab.add_log_message(f"Failed to connect to VNC server at {ip}:{port}")
                self.vnc_tab.update_connection_status("Connection Failed", False)
        else:
            # Disconnect all VNC sessions
            from ..session_manager import SessionType
            for session_key, session in list(self.session_manager.active_sessions.items()):
                if session.config.session_type == SessionType.VNC:
                    session.disconnect()
                    self.session_manager.close_session(session_key)
            
            self.vnc_tab.add_log_message("Disconnected from VNC server")
            self.vnc_tab.update_connection_status("Disconnected", False)
    
    def execute_telnet_command(self, automatic=False):
        """Executes command in Telnet session using background thread"""
        self.telnet_service.set_current_token(self.current_token)
        return self.telnet_service.execute_command(self.telnet_tab.get_command(), automatic)
    
    def on_telnet_command_finished(self, response, automatic):
        """Handles the completion of a telnet command run in a background thread"""
        # Append response to telnet output
        self.telnet_tab.append_output(response)
        
        # Clear command input if not automatic
        if not automatic:
            self.telnet_tab.clear_command()
        
        # Delegate logging to commander service
        self.commander_service.log_telnet_command_finished(
            response, automatic, self.current_token, self.node_manager,
            self.status_service.status_updated, self.log_writer,
            self.telnet_tab.command_input, self.telnet_tab.execute_btn
        )
    
    def copy_to_log(self):
        """Copies current session content to selected token or log file"""
        self.commander_presenter.copy_to_log(self.node_tree_view.selectedItems(), self.session_tabs)
    
    def clear_terminal(self):
        """Clear the telnet output area"""
        self.commander_presenter.clear_terminal()
    
    def clear_node_log(self):
        """Clear the currently selected node's log file"""
        self.commander_presenter.clear_node_log(self.node_tree_view.selectedItems())
    
    # This method is no longer needed - functionality moved to NodeTreePresenter
    
    def process_fieldbus_command(self, token_id, node_name):
        """Process fieldbus command with optimized error handling"""
        self.commander_service.process_fieldbus_command(token_id, node_name)
    
    def process_rpc_command(self, node_name, token_id, action_type):
        """Process RPC commands with token validation and auto-execute"""
        self.commander_service.process_rpc_command(node_name, token_id, action_type)
    
    def on_node_tree_updated(self):
        """Handle node tree updates from presenter"""
        pass
    
    def on_queue_processed(self, success_count, total_count):
        """Handle queue processing completion"""
        self.commander_presenter.handle_queue_processed(success_count, total_count, self.status_service)
    
    def closeEvent(self, event):
        """Cleanup on window close"""
        self.telnet_service.disconnect()
        # TODO: Implement LogWriter.close_all_logs
        # self.log_writer.close_all_logs()
        
        # Save application state
        self.settings.setValue("config_path", self.node_manager.config_path)
        self.settings.setValue("log_root", self.node_manager.log_root)
        
        # Save telnet connection state
        if hasattr(self, 'telnet_tab'):
            ip, port = self.telnet_tab.get_connection_info()
            self.settings.setValue("telnet_ip", ip)
            self.settings.setValue("telnet_port", port)

        # Call parent closeEvent, handling both real instances and mocks
        try:
            super().closeEvent(event)
        except TypeError:
            # This can happen in tests with mock objects
            # In a real application, this shouldn't occur
            event.accept() if hasattr(event, 'accept') else None


def run():
    # Initialize Qt application safely
    app = initialize_qt() or QApplication(sys.argv)
    
    # Apply dark theme styling with custom button colors
    app.setStyle("Fusion")
    app.setStyleSheet(STYLESHEETS.get_application_stylesheet())
    
    # Create main window instance
    window = CommanderWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    from PyQt6.QtWidgets import QApplication
    run()