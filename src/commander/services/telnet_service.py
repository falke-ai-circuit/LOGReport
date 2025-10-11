"""
Telnet Service - Handles Telnet connection management and command execution
"""
import logging
import socket
import time
from typing import Optional

from ..session_manager import SessionManager, SessionConfig, SessionType
from ..models import NodeToken
from ..widgets import ConnectionState
from ..commands.telnet_commands import CommandResolver
from ..services.threading_service import ThreadingService
from PyQt5.QtCore import QObject, pyqtSignal


class TelnetService(QObject):
    """Service for handling Telnet operations"""
    
    # Status message durations in milliseconds
    STATUS_MSG_SHORT = 3000    # 3 seconds
    STATUS_MSG_MEDIUM = 5000   # 5 seconds
    STATUS_MSG_LONG = 10000    # 10 seconds

    # Define signals as class attributes
    status_message_signal = pyqtSignal(str, int)  # Message and duration
    command_finished_signal = pyqtSignal(str, bool)
    update_connection_status_signal = pyqtSignal(ConnectionState)
    
    def __init__(self, session_manager: SessionManager):
        """
        Initialize the Telnet service.
        
        Args:
            session_manager: Manager for session operations
        """
        super().__init__()
        self.session_manager = session_manager
        self.command_resolver = CommandResolver()
        self.threading_service = ThreadingService()
        self.telnet_lock = self.threading_service.create_lock()
        self.active_telnet_client = None
        self.telnet_session = None
        self.current_token = None
        # Store connection parameters for auto-reconnect
        self.last_ip_address = None
        self.last_port = None
        # Store debugger connection parameters (from Telnet tab)
        self.debugger_ip_address = None
        self.debugger_port = None
        
        logging.debug("TelnetService initialized")
    
    def set_current_token(self, token: NodeToken):
        """
        Set the current token for command execution.
        
        Args:
            token: The token to set as current
        """
        self.current_token = token
        logging.debug(f"TelnetService: Current token set to {token.token_id if token else None}")
    
    def toggle_connection(self, connect: bool, ip_address: str, port: int, settings=None) -> bool:
        """
        Toggles connection/disconnection for Telnet.
        Uses retry logic (2 attempts with 5-second delay) for manual connections from GUI.
        
        Args:
            connect: True to connect, False to disconnect
            ip_address: IP address to connect to
            port: Port to connect to
            settings: Optional settings object to save connection parameters
            
        Returns:
            bool: True if operation succeeded, False otherwise
        """
        if connect:
            # Store connection parameters for auto-reconnect
            self.last_ip_address = ip_address
            self.last_port = port
            # Store as debugger IP (this is the Telnet tab connection)
            self.debugger_ip_address = ip_address
            self.debugger_port = port
            # Save connection parameters to settings if provided
            if settings:
                settings.setValue("telnet_ip", ip_address)
                settings.setValue("telnet_port", str(port))
            
            # Use retry logic for manual connections (same as auto-reconnect)
            return self._attempt_connection_with_retry(ip_address, port)
        else:
            return self.disconnect()
    
    def connect(self, ip_address: str, port: int) -> bool:
        """
        Connects to specified telnet server using provided IP and port.
        
        Args:
            ip_address: IP address to connect to
            port: Port to connect to
            
        Returns:
            bool: True if connection succeeded, False otherwise
        """
        # Store connection parameters for auto-reconnect
        self.last_ip_address = ip_address
        self.last_port = port
        
        # Configure telnet connection using the parameters
        config = SessionConfig(
            host=ip_address,
            port=port,
            session_type=SessionType.DEBUGGER,  # Use DEBUGGER session type for manual connections
            username="",   # No username by default
            password=""    # No password by default
        )
        
        try:
            self.update_connection_status_signal.emit(ConnectionState.CONNECTING)
            self.telnet_session = self.session_manager.create_session(config)
            
            # Attempt connection and get detailed result
            if self.telnet_session and self.telnet_session.is_connected:
                # Verify system mode after connection
                if hasattr(self.telnet_session, 'verify_system_mode'):
                    mode_ok = self.telnet_session.verify_system_mode()
                    if not mode_ok:
                        logging.warning("TelnetService.connect: System mode verification failed - disconnecting for retry")
                        # Close the failed connection so retry logic can reconnect
                        try:
                            self.session_manager.close_session(self.telnet_session)
                        except Exception as e:
                            logging.error(f"TelnetService.connect: Error closing failed session: {e}")
                        self.telnet_session = None
                        self.active_telnet_client = None
                        self.status_message_signal.emit("System mode verification failed", self.STATUS_MSG_SHORT)
                        self.update_connection_status_signal.emit(ConnectionState.ERROR)
                        return False
                    else:
                        logging.info("TelnetService.connect: System mode verified successfully")
                
                self.status_message_signal.emit(f"Connected to {ip_address}:{port}", self.STATUS_MSG_SHORT)
                self.update_connection_status_signal.emit(ConnectionState.CONNECTED)
                # Store active client for reuse in context commands
                self.active_telnet_client = self.telnet_session
                return True
            
            # Handle connection failure
            self.status_message_signal.emit("Connection failed", self.STATUS_MSG_SHORT)
            self.update_connection_status_signal.emit(ConnectionState.ERROR)
            return False
            
        except socket.timeout as e:
            self.status_message_signal.emit(f"Connection timed out: {str(e)}", self.STATUS_MSG_MEDIUM)
            self.update_connection_status_signal.emit(ConnectionState.ERROR)
            return False
        except ConnectionRefusedError as e:
            self.status_message_signal.emit(f"Connection refused: {str(e)}", self.STATUS_MSG_MEDIUM)
            self.update_connection_status_signal.emit(ConnectionState.ERROR)
            return False
        except Exception as e:
            self.status_message_signal.emit(f"Connection error: {str(e)}", self.STATUS_MSG_MEDIUM)
            self.update_connection_status_signal.emit(ConnectionState.ERROR)
            return False
    
    def disconnect(self) -> bool:
        """
        Disconnects from current telnet session.
        
        Returns:
            bool: True if disconnection succeeded, False otherwise
        """
        try:
            # Only close through session manager to avoid double disconnect
            self.session_manager.close_all_sessions()
            # Clear local reference AFTER session manager has closed sessions
            self.telnet_session = None
            # Clear active client reference
            self.active_telnet_client = None
            
            # Force UI update to disconnected state
            self.update_connection_status_signal.emit(ConnectionState.DISCONNECTED)
            return True
            
        except Exception as e:
            logging.error(f"Error disconnecting: {str(e)}")
            # Still reset UI state even if disconnection failed
            self.update_connection_status_signal.emit(ConnectionState.DISCONNECTED)
            return False
    
    def _ensure_debugger_connection(self) -> bool:
        """
        Ensure debugger connection is established. Uses debugger IP from Telnet tab.
        This is used for FBC/RPC/LOG commands that must go through the debugger session.
        Attempts connection 2 times with 15-second delay between attempts.
        
        Returns:
            bool: True if connected to debugger, False if connection failed after retries
        """
        # Prioritize active manual connection if available
        if hasattr(self, 'active_telnet_client') and self.active_telnet_client and self.active_telnet_client.is_connected:
            self.telnet_session = self.active_telnet_client
            return True
        
        # Check if we have a telnet session
        if not self.telnet_session:
            # Attempt auto-reconnect to DEBUGGER IP if available
            if self.debugger_ip_address and self.debugger_port:
                return self._attempt_debugger_connection_with_retry()
            else:
                logging.error("TelnetService._ensure_debugger_connection: No debugger IP configured in Telnet tab")
                self.status_message_signal.emit("No debugger IP configured. Please connect in Telnet tab first.", self.STATUS_MSG_MEDIUM)
                return False
        
        # Verify existing connection is still active
        if not self.telnet_session.is_connected:
            # Attempt reconnect to debugger
            if self.debugger_ip_address and self.debugger_port:
                logging.warning(f"TelnetService._ensure_debugger_connection: Session disconnected, reconnecting to debugger {self.debugger_ip_address}:{self.debugger_port}")
                return self._attempt_debugger_connection_with_retry()
            else:
                logging.error("TelnetService._ensure_debugger_connection: Session disconnected and no debugger IP available")
                self.status_message_signal.emit("Debugger connection lost. Please reconnect in Telnet tab.", self.STATUS_MSG_MEDIUM)
                return False
        
        return True
    
    def _attempt_debugger_connection_with_retry(self) -> bool:
        """
        Attempt debugger connection with retry logic.
        Makes 2 connection attempts with 10-second delay between attempts.
        Ensures complete socket cleanup between retries.
        Handles both connection failures and forced closures during initialization.
        
        Returns:
            bool: True if connection succeeded, False if all attempts failed
        """
        import time
        
        max_attempts = 2
        retry_delay = 10  # seconds - allow time for remote host to recover and socket cleanup
        
        for attempt in range(1, max_attempts + 1):
            logging.info(f"TelnetService: Debugger connection attempt {attempt}/{max_attempts} to {self.debugger_ip_address}:{self.debugger_port}")
            self.status_message_signal.emit(f"Connecting to debugger {self.debugger_ip_address}... (attempt {attempt}/{max_attempts})", self.STATUS_MSG_SHORT)
            
            success = self.connect(self.debugger_ip_address, self.debugger_port)
            
            if success:
                logging.info(f"TelnetService: Successfully connected to debugger on attempt {attempt}")
                self.status_message_signal.emit(f"Connected to debugger {self.debugger_ip_address}", self.STATUS_MSG_SHORT)
                return True
            
            # If this wasn't the last attempt, wait before retrying
            if attempt < max_attempts:
                logging.warning(f"TelnetService: Connection attempt {attempt} failed, retrying in {retry_delay} seconds...")
                self.status_message_signal.emit(f"Connection failed, retrying in {retry_delay}s... (attempt {attempt}/{max_attempts})", self.STATUS_MSG_MEDIUM)
                time.sleep(retry_delay)
        
        # All attempts failed
        logging.error(f"TelnetService: Failed to connect to debugger after {max_attempts} attempts")
        self.status_message_signal.emit(f"Failed to connect to debugger after {max_attempts} attempts", self.STATUS_MSG_MEDIUM)
        return False
    
    def _attempt_connection_with_retry(self, ip_address: str, port: int) -> bool:
        """
        Attempt manual connection with retry logic (for GUI connections).
        Makes 2 connection attempts with 10-second delay between attempts.
        Ensures complete socket cleanup between retries.
        Handles both connection failures and forced closures during initialization.
        
        Args:
            ip_address: IP address to connect to
            port: Port to connect to
            
        Returns:
            bool: True if connection succeeded, False if all attempts failed
        """
        import time
        
        max_attempts = 2
        retry_delay = 10  # seconds - allow time for remote host to recover and socket cleanup
        
        for attempt in range(1, max_attempts + 1):
            logging.info(f"TelnetService: Manual connection attempt {attempt}/{max_attempts} to {ip_address}:{port}")
            self.status_message_signal.emit(f"Connecting to {ip_address}... (attempt {attempt}/{max_attempts})", self.STATUS_MSG_SHORT)
            
            success = self.connect(ip_address, port)
            
            if success:
                logging.info(f"TelnetService: Successfully connected on attempt {attempt}")
                self.status_message_signal.emit(f"Connected to {ip_address}:{port}", self.STATUS_MSG_SHORT)
                return True
            
            # If this wasn't the last attempt, wait before retrying
            if attempt < max_attempts:
                logging.warning(f"TelnetService: Connection attempt {attempt} failed, retrying in {retry_delay} seconds...")
                self.status_message_signal.emit(f"Connection failed, retrying in {retry_delay}s... (attempt {attempt}/{max_attempts})", self.STATUS_MSG_MEDIUM)
                time.sleep(retry_delay)
        
        # All attempts failed
        logging.error(f"TelnetService: Failed to connect after {max_attempts} attempts")
        self.status_message_signal.emit(f"Failed to connect after {max_attempts} attempts", self.STATUS_MSG_MEDIUM)
        return False
    
    def _ensure_connection(self) -> bool:
        """
        Ensure telnet connection is established. Attempt auto-reconnect if disconnected.
        
        Returns:
            bool: True if connected, False if connection failed
        """
        # Prioritize active manual connection if available
        if hasattr(self, 'active_telnet_client') and self.active_telnet_client and self.active_telnet_client.is_connected:
            self.telnet_session = self.active_telnet_client
            return True
        
        # Check if we have a telnet session
        if not self.telnet_session:
            # Attempt auto-reconnect if we have stored connection parameters
            if self.last_ip_address and self.last_port:
                logging.info(f"TelnetService._ensure_connection: No session found, attempting auto-reconnect to {self.last_ip_address}:{self.last_port}")
                return self.connect(self.last_ip_address, self.last_port)
            else:
                logging.error("TelnetService._ensure_connection: No telnet session and no stored connection parameters")
                self.status_message_signal.emit("No telnet connection. Please connect first.", self.STATUS_MSG_MEDIUM)
                return False
        
        # Check if session is connected
        if not self.telnet_session.is_connected:
            # Attempt auto-reconnect
            if self.last_ip_address and self.last_port:
                logging.info(f"TelnetService._ensure_connection: Session disconnected, attempting auto-reconnect to {self.last_ip_address}:{self.last_port}")
                return self.connect(self.last_ip_address, self.last_port)
            else:
                logging.error("TelnetService._ensure_connection: Session disconnected and no stored connection parameters")
                self.status_message_signal.emit("Telnet connection lost. Please reconnect.", self.STATUS_MSG_MEDIUM)
                return False
        
        return True
    
    def execute_command(self, command: str, automatic=False) -> str:
        """
        Executes command in Telnet session using background thread.
        
        Args:
            command: Command to execute
            automatic: Whether command was triggered automatically
            
        Returns:
            str: Empty string (response will be handled asynchronously)
        """
        # Ensure connection before executing command
        if not self._ensure_connection():
            logging.error("TelnetService.execute_command: Connection check failed, aborting command execution")
            return ""
        
        command = command.strip()
        if not command:
            logging.debug("Empty command received in execute_command")
            return ""
        logging.debug(f"Executing telnet command: {command} (automatic={automatic})")
            
        logging.debug(f"Executing telnet command: {command}")
        logging.debug(f"DEBUG: Automatic={automatic}, Current token: {self.current_token.token_id if self.current_token else 'None'}")

        if not automatic:
            # Display user command in output
            self.command_finished_signal.emit(f"> {command}\n", automatic)
            
        # Start command execution in background thread
        self.threading_service.start_thread(
            target=self._run_command,
            args=(command, automatic),
            daemon=True
        )
        
        return ""  # Response will be handled asynchronously

    def _run_command(self, command, automatic):
        """
        Runs telnet command in background thread with improved error handling.
        
        Args:
            command: Command to execute
            automatic: Whether command was triggered automatically
        """
        with self.telnet_lock:
            try:
                token_id = self.current_token.token_id if self.current_token else ""
                resolved_cmd = self.command_resolver.resolve(command, token_id)
                response = self.telnet_session.send_command(resolved_cmd, timeout=5)
                
                self.update_connection_status_signal.emit(ConnectionState.CONNECTED)
            except (ConnectionRefusedError, TimeoutError, socket.timeout) as e:
                response = f"ERROR: {type(e).__name__} - {str(e)}"
                self._handle_connection_error(e)
            except Exception as e:
                response = f"ERROR: {type(e).__name__} - {str(e)}"
                logging.error(f"Telnet command failed: {command}", exc_info=True)
            
            logging.debug(f"Emitting command_finished signal for command: {command}")
            self.command_finished_signal.emit(response, automatic)
    
    def _handle_connection_error(self, error):
        """
        Centralized connection error handling.
        
        Args:
            error: The error that occurred
        """
        error_type = type(error).__name__
        if error_type in ["ConnectionRefusedError", "TimeoutError", "socket.timeout"]:
            self.update_connection_status_signal.emit(ConnectionState.ERROR)
            if self.status_message_signal:
                self.status_message_signal.emit(f"Connection error: {str(error)}", self.STATUS_MSG_MEDIUM)