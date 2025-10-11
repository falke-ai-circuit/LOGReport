"""
Session Presenter

This presenter handles the session view logic and clipboard functionality.
"""

from PyQt5.QtCore import QObject, pyqtSignal
from PyQt5.QtWidgets import QWidget

# from commander.presenters.commander_presenter import CommanderPresenter
from commander.ui.session_view import SessionView
from commander.ui.telnet_tab import TelnetTab
from commander.ui.bstool_tab import BsToolTab
from commander.services.clipboard_monitor import ClipboardMonitor
from commander.services.status_service import StatusService
from commander.log_writer import LogWriter
from commander.node_manager import NodeManager
from commander.session_manager import SessionManager, SessionType, SessionConfig
from commander.models import NodeToken
from commander.services.session_player import SessionPlayer


class SessionPresenter(QObject):
    """
    Presenter for the session view, handling clipboard integration.
    """
    
    def __init__(self, view: SessionView, commander_presenter: 'CommanderPresenter',
                 node_manager: NodeManager, log_writer: LogWriter,
                 status_service: StatusService):
        """
        Initialize the SessionPresenter.
        
        Args:
            view: SessionView instance
            commander_presenter: CommanderPresenter instance
            node_manager: NodeManager instance
            log_writer: LogWriter instance
            status_service: StatusService instance
        """
        super().__init__()
        self.view = view
        self.commander_presenter = commander_presenter
        self.node_manager = node_manager
        self.log_writer = log_writer
        self.status_service = status_service
        
        # Initialize session manager
        self.session_manager = SessionManager()
        
        # Initialize clipboard monitor
        self.clipboard_monitor = ClipboardMonitor(
            node_manager=self.node_manager,
            log_writer=self.log_writer,
            status_service=self.status_service
        )
        
        # Playback state
        self.session_player = None
        
        # Connect signals
        self._connect_signals()

    def _connect_signals(self):
        """Connect signals between view and presenter."""
        # Connect copy to log button signals
        self.view.copy_to_log_clicked.connect(self._on_copy_to_log_clicked)
        
        # Connect clipboard monitor manual copy callback
        self.clipboard_monitor.set_manual_copy_callback(self._manual_copy_callback)

    def _on_copy_to_log_clicked(self):
        """Handle copy to log button click."""
        # Get clipboard content
        from PyQt5.QtWidgets import QApplication
        clipboard = QApplication.clipboard()
        content = clipboard.text()
        
        if content.strip():
            # Use clipboard monitor to handle the copy operation
            self.clipboard_monitor.manual_copy_to_log(content)
        else:
            self.status_service.show_message("Clipboard is empty")

    def _manual_copy_callback(self, content: str):
        """
        Callback for manual copy operations.
        
        Args:
            content: Content being copied to log
        """
        # Log to application log as well
        try:
            self.log_writer.write_to_app_log(f"Manual copy to log: {content[:50]}...")
        except Exception as e:
            # Don't fail if app log write fails
            pass

    def get_clipboard_monitor(self) -> ClipboardMonitor:
        """
        Get the clipboard monitor instance.
        
        Returns:
            ClipboardMonitor instance
        """
        return self.clipboard_monitor
        
    def get_active_terminal_content(self, session_tabs):
        """Retrieve content from active terminal tab"""
        active_tab = session_tabs.currentWidget()
        if isinstance(active_tab, TelnetTab):
            return active_tab.output.toPlainText()
        elif isinstance(active_tab, BsToolTab):
            return active_tab.output.toPlainText()
        return None