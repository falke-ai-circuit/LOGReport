"""
Session Presenter

This presenter handles the session view logic, including VNC tab integration
and clipboard functionality.
"""

from PyQt6.QtCore import QObject, pyqtSignal
from PyQt6.QtWidgets import QWidget

# from commander.presenters.commander_presenter import CommanderPresenter
from commander.ui.session_view import SessionView
from commander.ui.vnc_tab import VNCTab
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
    Presenter for the session view, handling VNC tab and clipboard integration.
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
        
        # Recording state
        self.active_vnc_session = None
        self.is_recording = False
        
        # Playback state
        self.session_player = None
        
        # Connect signals
        self._connect_signals()

    def _connect_signals(self):
        """Connect signals between view and presenter."""
        # Connect copy to log button signals
        self.view.copy_to_log_clicked.connect(self._on_copy_to_log_clicked)
        
        # Connect VNC tab signals
        self.view.vnc_tab.connect_clicked.connect(self._on_vnc_connect_clicked)
        self.view.vnc_tab.disconnect_clicked.connect(self._on_vnc_disconnect_clicked)
        
        # Connect recording signals
        self.view.record_clicked.connect(self._on_record_clicked)
        self.view.stop_record_clicked.connect(self._on_stop_record_clicked)
        self.view.play_clicked.connect(self._on_play_clicked)
        self.view.pause_clicked.connect(self._on_pause_clicked)
        self.view.speed_changed.connect(self._on_speed_changed)
        
        # Connect clipboard monitor manual copy callback
        self.clipboard_monitor.set_manual_copy_callback(self._manual_copy_callback)

    def _on_copy_to_log_clicked(self):
        """Handle copy to log button click."""
        # Get clipboard content
        from PyQt6.QtWidgets import QApplication
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
            
        # Record clipboard event if recording is active
        if self.is_recording and self.active_vnc_session:
            self.active_vnc_session.recorder.record_clipboard_event(content)

    def handle_vnc_text_selection(self, content: str):
        """
        Handle text selection in VNC viewer (Ctrl+C equivalent).
        
        Args:
            content: Selected text content
        """
        # Use clipboard monitor to handle the text selection
        self.clipboard_monitor.handle_vnc_text_selection(content)
        
        # Record clipboard event if recording is active
        if self.is_recording and self.active_vnc_session:
            self.active_vnc_session.recorder.record_clipboard_event(content)

    def get_clipboard_monitor(self) -> ClipboardMonitor:
        """
        Get the clipboard monitor instance.
        
        Returns:
            ClipboardMonitor instance
        """
        return self.clipboard_monitor
        
    def set_active_vnc_session(self, session):
        """
        Set the active VNC session for recording.
        
        Args:
            session: VNCSession instance
        """
        self.active_vnc_session = session
        
    def _on_record_clicked(self):
        """Handle record button click."""
        if not self.active_vnc_session:
            self.status_service.show_message("No active VNC session to record")
            return
            
        # Generate recording path
        import os
        from datetime import datetime
        
        # Get node token if available
        node_token = None
        active_node = self.node_manager.get_selected_node()
        if active_node and active_node.tokens:
            # Get first token for this node
            for token_list in active_node.tokens.values():
                if token_list:
                    node_token = token_list[0]
                    break
                    
        # Create recordings directory if it doesn't exist
        recordings_dir = "test_logs/recordings"
        os.makedirs(recordings_dir, exist_ok=True)
        
        # Generate filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        node_name = active_node.name if active_node else "unknown"
        filename = f"{node_name}_{timestamp}.vncr"
        recording_path = os.path.join(recordings_dir, filename)
        
        # Start recording
        if self.active_vnc_session.start_recording(recording_path, node_token):
            self.is_recording = True
            self.view.set_recording_state(True)
            self.status_service.show_message(f"Started recording to: {filename}")
            
            # Start performance monitoring timer
            self._start_performance_monitoring()
        else:
            self.status_service.show_message("Failed to start recording")
            
    def _on_stop_record_clicked(self):
        """Handle stop record button click."""
        if not self.is_recording or not self.active_vnc_session:
            return
            
        # Stop recording
        recording_path = self.active_vnc_session.stop_recording()
        if recording_path:
            self.is_recording = False
            self.view.set_recording_state(False)
            filename = os.path.basename(recording_path)
            self.status_service.show_message(f"Stopped recording: {filename}")
            
            # Stop performance monitoring
            self._stop_performance_monitoring()
        else:
            self.status_service.show_message("Failed to stop recording")
            
    def _on_play_clicked(self):
        """Handle play button click."""
        # For now, just show a message that playback is not fully implemented
        self.status_service.show_message("Playback functionality is being developed")
        self.view.set_playback_state(False)
        
    def _on_pause_clicked(self):
        """Handle pause button click."""
        self.status_service.show_message("Playback functionality is being developed")
        self.view.set_playback_state(False, True)
        
    def _on_speed_changed(self, speed: float):
        """Handle speed change."""
        self.status_service.show_message(f"Playback speed set to {speed}x")
        
    def _start_performance_monitoring(self):
        """Start monitoring performance metrics."""
        # This would be implemented in a more complete version
        pass
        
    def _stop_performance_monitoring(self):
        """Stop monitoring performance metrics."""
        # This would be implemented in a more complete version
        pass
        
    def _on_vnc_connect_clicked(self):
        """Handle VNC connect button click."""
        host = self.view.vnc_tab.get_host()
        port = self.view.vnc_tab.get_port()
        
        if not host:
            self.status_service.show_message("Please enter a host address")
            return
            
        # Create session config
        config = SessionConfig(
            host=host,
            port=port,
            session_type=SessionType.VNC
        )
        
        # Create VNC session
        session = self.session_manager.create_session(config)
        if session:
            self.active_vnc_session = session
            self.view.vnc_tab.set_connection_status(True)
            self.status_service.show_message(f"Connected to VNC server at {host}:{port}")
            
            # Connect session state change signal
            session.connection_state_changed.connect(self._on_vnc_connection_state_changed)
        else:
            self.status_service.show_message(f"Failed to connect to VNC server at {host}:{port}")
            
    def get_active_terminal_content(self, session_tabs):
        """Retrieve content from active terminal tab"""
        active_tab = session_tabs.currentWidget()
        if isinstance(active_tab, TelnetTab):
            return active_tab.output.toPlainText()
        elif isinstance(active_tab, VNCTab):
            return active_tab.get_selected_text()
        elif isinstance(active_tab, BsToolTab):
            return active_tab.output.toPlainText()
        return None
            
    def _on_vnc_disconnect_clicked(self):
        """Handle VNC disconnect button click."""
        if self.active_vnc_session:
            # Stop recording if active
            if self.is_recording:
                self._on_stop_record_clicked()
                
            # Disconnect session
            self.active_vnc_session.disconnect()
            self.active_vnc_session = None
            self.view.vnc_tab.set_connection_status(False)
            self.status_service.show_message("Disconnected from VNC server")
            
    def _on_vnc_connection_state_changed(self, connected: bool):
        """
        Handle VNC connection state change.
        
        Args:
            connected: Whether VNC is connected
        """
        self.view.vnc_tab.set_connection_status(connected)
        if not connected:
            # Stop recording if active
            if self.is_recording:
                self._on_stop_record_clicked()
            self.status_service.show_message("VNC connection lost")