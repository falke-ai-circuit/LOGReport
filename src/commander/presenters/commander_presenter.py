"""
Commander Presenter

This presenter coordinates the main application functionality, including
clipboard integration.
"""

import os
from PyQt5.QtWidgets import (
    QTreeWidget, QTreeWidgetItem, QTabWidget, QTextEdit, 
    QVBoxLayout, QWidget, QPushButton, QFileDialog
)
from PyQt5.QtCore import QObject, pyqtSignal, Qt

from commander.ui.commander_ui_factory import CommanderUIFactory
from commander.presenters.session_presenter import SessionPresenter
from commander.presenters.node_tree_presenter import NodeTreePresenter
from commander.services.clipboard_monitor import ClipboardMonitor
from commander.ui.telnet_tab import TelnetTab
from commander.ui.bstool_tab import BsToolTab
from commander.services.status_service import StatusService
from commander.log_writer import LogWriter
from commander.node_manager import NodeManager
from commander.presenters.commander_presenter_utils import CommanderPresenterUtils


class CommanderPresenter(QObject):
    """
    Main presenter that coordinates application functionality.
    """
    
    # Signal definitions
    status_message_signal = pyqtSignal(str, int)
    set_cmd_input_text_signal = pyqtSignal(str)
    update_connection_status_signal = pyqtSignal(object)  # ConnectionState
    switch_to_telnet_tab_signal = pyqtSignal()
    set_cmd_focus_signal = pyqtSignal()
    
    def __init__(self, ui_factory: CommanderUIFactory, node_manager: NodeManager,
                 log_writer: LogWriter, status_service: StatusService,
                 session_manager, command_queue, fbc_service, rpc_service,
                 context_menu_service, bstool_service):
        """
        Initialize the CommanderPresenter.
        
        Args:
            ui_factory: UI factory for creating views
            node_manager: NodeManager instance
            log_writer: LogWriter instance
            status_service: StatusService instance
            session_manager: SessionManager instance
            command_queue: CommandQueue instance
            fbc_service: FbcCommandService instance
            rpc_service: RpcCommandService instance
            context_menu_service: ContextMenuService instance
            bstool_service: BsToolCommandService instance
        """
        super().__init__()
        self.ui_factory = ui_factory
        self.node_manager = node_manager
        self.log_writer = log_writer
        self.status_service = status_service
        self.session_manager = session_manager
        self.command_queue = command_queue
        self.fbc_service = fbc_service
        self.rpc_service = rpc_service
        self.context_menu_service = context_menu_service
        self.bstool_service = bstool_service
        self.utils = CommanderPresenterUtils(node_manager=self.node_manager, log_writer=self.log_writer)
        
        # Create presenters
        self.node_tree_presenter = NodeTreePresenter(
            view=self.ui_factory.node_tree_view,
            node_manager=self.node_manager,
            session_manager=self.session_manager,
            log_writer=self.log_writer,
            command_queue=self.command_queue,
            fbc_service=self.fbc_service,
            rpc_service=self.rpc_service,
            context_menu_service=self.context_menu_service,
            bstool_service=self.bstool_service
        )
        self.session_presenter = SessionPresenter(
            view=self.ui_factory.session_view,
            commander_presenter=self,
            node_manager=self.node_manager,
            log_writer=self.log_writer,
            status_service=self.status_service
        )
        
        # Connect signals
        self._connect_signals()
        
        # Sync initial BsTool path from UI to service
        # BsToolTab auto-detects on __init__, but signal may emit before connection
        # so we explicitly sync the initial path here
        self._sync_initial_bstool_path()

    def _connect_signals(self):
        """Connect signals between components."""
        # Connect session view signals to session presenter
        self.ui_factory.session_view.copy_to_log_clicked.connect(
            self.session_presenter._on_copy_to_log_clicked
        )
        
        # Connect BsTool tab signals
        self.ui_factory.bstool_tab.execute_clicked.connect(
            self.handle_bstool_execute
        )
        self.ui_factory.bstool_tab.bstool_path_changed.connect(
            self.handle_bstool_path_changed
        )
        
        # BsTool service connections are handled in CommanderWindow
        # to avoid duplicate connections
    
    def _sync_initial_bstool_path(self):
        """
        Sync the initial auto-detected BsTool path from UI to service.
        
        BsToolTab auto-detects BsTool.exe path on initialization and populates
        the path field. However, the bstool_path_changed signal may emit before
        the presenter connects to it. This method explicitly syncs the initial
        path after signal connections are established.
        """
        initial_path = self.ui_factory.bstool_tab.get_bstool_path()
        if initial_path:
            self.bstool_service.set_bstool_path(initial_path)
    
    def handle_bstool_path_changed(self, path: str):
        """
        Handle BsTool path changes from the UI.
        Updates the centralized path in the BsToolCommandService.
        
        Args:
            path: New BsTool.exe path from UI
        """
        self.bstool_service.set_bstool_path(path)

    def get_clipboard_monitor(self) -> ClipboardMonitor:
        """
        Get the clipboard monitor instance.
        
        Returns:
            ClipboardMonitor instance
        """
        return self.session_presenter.get_clipboard_monitor()
    
    def clear_node_log(self, selected_items):
        """
        Clear the log for the selected node.
        
        Args:
            selected_items: Selected items from the view
        """
        self.utils.clear_node_log(selected_items, self.status_message_signal)
    
    def clear_terminal(self):
        """
        Clear the output of the currently active terminal tab.
        """
        active_tab = self.ui_factory.session_view.tab_widget.currentWidget()
        if isinstance(active_tab, TelnetTab):
            active_tab.output.clear()
        elif isinstance(active_tab, BsToolTab):
            active_tab.clear_output()
    
    def handle_queue_processed(self, success_count, total_count, status_service):
        """
        Handle queue processing completion and update UI status.
        
        Args:
            success_count: Number of successfully processed commands
            total_count: Total number of commands in the queue
            status_service: StatusService instance for UI updates
        """
        if success_count == total_count:
            self.status_message_signal.emit(f"Successfully processed {success_count} commands", 3000)
        else:
            self.status_message_signal.emit(f"Processed {success_count}/{total_count} commands successfully", 5000)
    
    def copy_to_log(self, selected_items, session_tabs):
        """Copy terminal content to selected log file"""
        if not selected_items:
            self.status_message_signal.emit("No log file selected in node tree", 3000)
            return

        # Get first valid log path from selection
        log_path = None
        for item in selected_items:
            item_data = item.data(0, Qt.ItemDataRole.UserRole)
            if item_data and 'log_path' in item_data:
                log_path = item_data['log_path']
                break
        
        if not log_path:
            self.status_message_signal.emit("Selected item is not a valid log file", 3000)
            return

        # Get content from active terminal tab
        content = self.session_presenter.get_active_terminal_content(session_tabs)
        if not content:
            self.status_message_signal.emit("No terminal content available", 3000)
            return

        # Write to file through service
        try:
            self.log_writer.append_to_file(log_path, content)
            self.status_message_signal.emit(f"Content saved to {os.path.basename(log_path)}", 3000)
        except Exception as e:
            self.status_message_signal.emit(f"Error saving content: {str(e)}", 5000)
            
    def handle_bstool_execute(self, command: str):
        """
        Handle BsTool command execution from the BsTool tab.
        
        The BsTool path is managed centrally by the BsToolCommandService,
        which uses the path set from the UI via handle_bstool_path_changed().
        
        Args:
            command: Command string to execute
        """
        try:
            # Service will use centralized path (set from UI or auto-detected)
            self.bstool_service.execute_command(command)
            self.status_message_signal.emit(f"Executing BsTool command: {command}", 3000)
        except Exception as e:
            error_msg = f"Error executing BsTool command: {str(e)}"
            self.status_message_signal.emit(error_msg, 5000)