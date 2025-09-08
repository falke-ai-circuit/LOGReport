"""
Session Manager
Handles Telnet, VNC, and FTP session connections
"""
import telnetlib
import socket
import time
import re
import logging
import os
from enum import Enum
from dataclasses import dataclass
from typing import Optional
from PyQt6.QtCore import QObject, pyqtSignal
from .models import NodeToken

class SessionType(Enum):
    TELNET = "TELNET"
    VNC = "VNC"
    FTP = "FTP"
    DEBUGGER = "DEBUGGER"  # Manually established sessions

@dataclass
class SessionConfig:
    host: str
    port: int
    session_type: SessionType
    username: str = ""
    password: str = ""
    timeout: int = 15

class BaseSession(QObject):
    """Abstract base class for session connections"""
    
    # Signal for connection state changes
    connection_state_changed = pyqtSignal(bool)  # True for connected, False for disconnected
    
    def __init__(self, config: SessionConfig):
        super().__init__()
        self.config = config
        self.connection = None
        self.is_connected = False
        
    def connect(self):
        raise NotImplementedError("Subclasses must implement connect()")
    
    def disconnect(self):
        if self.is_connected:
            try:
                self._disconnect_impl()
            finally:
                # Ensure state is reset even if disconnection fails
                self.is_connected = False
        self.connection = None
    
    def _disconnect_impl(self):
        """Implementation-specific disconnect logic"""
        raise NotImplementedError("Subclasses must implement _disconnect_impl()")
    
    def send_command(self, command: str) -> str:
        raise NotImplementedError("Subclasses must implement send_command()")
    
    def get_current_state(self) -> str:
        """Returns a string representation of connection state"""
        return f"{self.config.session_type.name} - {'Connected' if self.is_connected else 'Disconnected'}"

class TelnetSession(BaseSession):
    def __init__(self, config: SessionConfig):
        super().__init__(config)
        self.buffer = b""
        self.prompt_pattern = re.compile(r'\d+[a-z]\%\s*$')
        
    def connect(self) -> bool:
        try:
            # Log connection parameters
            logging.debug(f"TelnetSession.connect: Connecting to {self.config.host}:{self.config.port} with timeout={self.config.timeout}")
            
            # Establish connection with increased timeout
            self.connection = telnetlib.Telnet(
                self.config.host,
                self.config.port,
                self.config.timeout
            )
            
            # Detailed socket info
            sock = self.connection.get_socket()
            logging.debug(f"TelnetSession.connect: Socket created: {sock}")
            logging.debug(f"TelnetSession.connect: Socket timeout: {sock.gettimeout()}")
            
            # Wait for initial connection and read any banner
            time.sleep(1.0)  # Increased for Windows compatibility
            
            # Read initial banner/response
            initial_response = self.connection.read_very_eager()
            logging.debug(f"TelnetSession.connect: Initial response (hex): {initial_response.hex()}")
            logging.debug(f"TelnetSession.connect: Initial response (text): {initial_response.decode('ascii', 'ignore')}")
            
            # Skip artifact clearing for now to isolate connection issue
            logging.debug("TelnetSession.connect: Skipping artifact clearing for debug")
            
            self.is_connected = True
            logging.info("TelnetSession: Connection established successfully")
            return True
            
        except socket.timeout as e:
            logging.error("Telnet connection timed out", exc_info=True)
            return False
        except ConnectionRefusedError as e:
            logging.error("Telnet connection refused", exc_info=True)
            return False
        except Exception as e:
            logging.error(f"Telnet connection failed: {str(e)}", exc_info=True)
            return False
    
    def _disconnect_impl(self):
        if self.connection:
            try:
                # Properly close and terminate the telnet connection
                self.connection.close()
                # Additional cleanup to ensure complete disconnection
                if hasattr(self.connection, 'get_socket'):
                    sock = self.connection.get_socket()
                    if sock:
                        sock.shutdown(socket.SHUT_RDWR)
                        sock.close()
            except Exception as e:
                print(f"Error closing telnet connection: {str(e)}")
            finally:
                self.connection = None
    
    def send_command(self, command: str, timeout: float = 5.0) -> str:
        """Standardized command sending matching TelnetClient implementation"""
        if not self.is_connected:
            error_msg = "TelnetSession.send_command: Not connected to Telnet session"
            logging.error(error_msg)
            raise ConnectionError(error_msg)

        logging.debug(f"TelnetSession.send_command: Sending command: {command}")
        try:
            # Clear input buffer and console artifacts
            logging.debug("TelnetSession.send_command: Clearing input buffer")
            self.connection.read_very_eager()
            self.connection.write(b'\x18')  # Ctrl+X
            time.sleep(0.1)
            self.connection.write(b'\x1A')  # Ctrl+Z
            time.sleep(0.1)
            cleared = self.connection.read_very_eager()
            logging.debug(f"TelnetSession.send_command: Cleared {len(cleared)} bytes from buffer")

            # Send command with proper termination
            cmd_bytes = command.encode('ascii')
            # Ensure proper Telnet line endings (RFC 854)
            if not cmd_bytes.endswith(b'\r\n'):
                cmd_bytes = cmd_bytes.rstrip(b'\n') + b'\r\n'
            
            logging.debug(f"TelnetSession.send_command: Sending {len(cmd_bytes)} bytes: {cmd_bytes}")
            try:
                # telnetlib.write() returns None, so we don't check bytes_sent
                self.connection.write(cmd_bytes)
                logging.debug(f"TelnetSession.send_command: Command sent successfully")
            except (OSError, AttributeError) as e:
                error_msg = f"TelnetSession.send_command: Write failed: {str(e)}"
                logging.error(error_msg)
                raise ConnectionError(error_msg) from e
            
            # Get and process response using same method as TelnetClient
            response = self._read_response(timeout)
            logging.debug(f"TelnetSession.send_command: Received {len(response)} chars of raw response")
            
            processed = self._process_response(response, command)
            logging.debug(f"TelnetSession.send_command: Processed response length: {len(processed)}")
            return processed
            
        except socket.timeout as e:
            error = f"Error: Command timed out - {str(e)}"
            logging.error(f"TelnetSession.send_command: {error}")
            return error
        except Exception as e:
            error = f"Error: {str(e)}"
            logging.error(f"TelnetSession.send_command: {error}", exc_info=True)
            return error

    def _read_response(self, timeout: float) -> str:
        """Read telnet response with prompt detection"""
        response = b""
        start_time = time.time()
        last_data_time = time.time()
        
        logging.debug(f"TelnetSession._read_response: Starting read with timeout={timeout}s")
        
        while (time.time() - start_time) < timeout:
            chunk = self.connection.read_very_eager()
            if chunk:
                response += chunk
                last_data_time = time.time()
                decoded = response.decode('ascii', 'ignore')
                logging.debug(f"TelnetSession._read_response: Received {len(chunk)} bytes, total {len(response)}")
                
                if self.prompt_pattern.search(decoded):
                    logging.debug("TelnetSession._read_response: Detected prompt pattern")
                    break
                    
            # Use non-blocking wait instead of sleep
            self.connection.get_socket().settimeout(0.05)
            try:
                test_byte = self.connection.get_socket().recv(1)
                if test_byte == b'':
                    logging.debug("TelnetSession._read_response: Socket closed by remote")
                    break
            except socket.timeout:
                # Check if we've had no data for too long
                if (time.time() - last_data_time) > (timeout / 2):
                    logging.warning("TelnetSession._read_response: No data received for half of timeout period")
                    break
                continue
            except EOFError as e:
                logging.error(f"TelnetSession._read_response: EOFError - {str(e)}")
                break
            except Exception as e:
                logging.error(f"TelnetSession._read_response: Error reading socket - {str(e)}")
                break
                
        result = response.decode('ascii', 'ignore') if response else ""
        logging.debug(f"TelnetSession._read_response: Returning {len(result)} chars")
        return result

    def _process_response(self, response: str, command: str) -> str:
        """Process and clean the telnet response"""
        # Remove command echo
        clean = response.replace(f"{command}\r\n", "")
        # Remove prompt and extra whitespace
        clean = re.sub(r'\d+[a-z]\%\s*$', '', clean).strip()
        return clean

class VNCSession(BaseSession):
    """VNC Session implementation with connection management and recording"""
    
    def __init__(self, config: SessionConfig):
        super().__init__(config)
        self.max_retries = 3
        self.retry_count = 0
        self.client = None
        self.recorder = None
        self.is_recording = False
        self.recording_path = None
        
    def connect(self) -> bool:
        """Connect to VNC server with retry logic"""
        logging.debug(f"VNCSession.connect: Connecting to {self.config.host}:{self.config.port}")
        
        # Reset retry count for new connection attempts
        if self.retry_count == 0:
            self.retry_count = 0
            
        try:
            from vncdotool import api
            
            # Create VNC client
            vnc_url = f"vnc://{self.config.host}:{self.config.port}"
            self.client = api.connect(vnc_url, password=self.config.password)
            
            # Test connection
            self.client.refreshScreen()
            
            self.is_connected = True
            self.retry_count = 0  # Reset retry count on successful connection
            self.connection_state_changed.emit(True)
            logging.info(f"VNCSession: Connected to {self.config.host}:{self.config.port}")
            return True
            
        except Exception as e:
            logging.error(f"VNC connection failed: {str(e)}")
            self.is_connected = False
            self.connection_state_changed.emit(False)
            
            # Handle retry logic
            if self.retry_count < self.max_retries:
                self.retry_count += 1
                logging.info(f"VNCSession: Retrying connection ({self.retry_count}/{self.max_retries})")
                # Add a small delay before retrying
                import time
                time.sleep(1)
                return self.connect()  # Recursive retry
            else:
                logging.error("VNCSession: Max retry attempts reached")
                return False
    
    def _disconnect_impl(self):
        """Implementation-specific disconnect logic"""
        logging.debug("VNCSession: Disconnecting")
        if self.client:
            try:
                self.client.disconnect()
            except Exception as e:
                logging.error(f"Error disconnecting VNC client: {str(e)}")
            finally:
                self.client = None
        self.is_connected = False
        self.connection_state_changed.emit(False)
        
        # Stop recording if active
        if self.is_recording:
            self.stop_recording()
    
    def send_command(self, command: str) -> str:
        """Send command to VNC session as keyboard input"""
        if not self.is_connected or not self.client:
            return "Error: Not connected to VNC session"
            
        # Record keyboard event if recording is active
        if self.is_recording and self.recorder:
            self.recorder.record_keyboard_event(command)
            
        try:
            # Send command as keyboard input
            self.client.keyPress(command)
            logging.debug(f"VNCSession: Sent keyboard sequence: {command}")
            return f"VNC command '{command}' sent as keyboard sequence"
        except Exception as e:
            error_msg = f"Error sending VNC command: {str(e)}"
            logging.error(error_msg)
            return error_msg
    
    def start_recording(self, output_path: str, node_token: Optional[NodeToken] = None) -> bool:
        """
        Start recording the VNC session.
        
        Args:
            output_path: Path where recording file will be saved
            node_token: NodeToken associated with this recording
            
        Returns:
            True if recording started successfully, False otherwise
        """
        try:
            from .services.session_recorder import SessionRecorder
            self.recorder = SessionRecorder(output_path, node_token)
            success = self.recorder.start()
            if success:
                self.is_recording = True
                self.recording_path = output_path
                logging.info(f"Started recording VNC session to: {output_path}")
            return success
        except Exception as e:
            logging.error(f"Error starting recording: {str(e)}")
            return False
    
    def stop_recording(self) -> Optional[str]:
        """
        Stop recording the VNC session.
        
        Returns:
            Path to the recorded file, or None if not recording
        """
        if not self.is_recording or not self.recorder:
            return None
            
        try:
            self.recorder.stop()
            recording_path = self.recorder.finalize()
            self.is_recording = False
            self.recorder = None
            logging.info(f"Stopped recording VNC session")
            return recording_path
        except Exception as e:
            logging.error(f"Error stopping recording: {str(e)}")
            return None
    
    def is_recording_active(self) -> bool:
        """
        Check if recording is currently active.
        
        Returns:
            True if recording is active, False otherwise
        """
        return self.is_recording and self.recorder is not None
    
    def get_recording_path(self) -> Optional[str]:
        """
        Get the current recording path.
        
        Returns:
            Path to the recording file, or None if not recording
        """
        return self.recording_path if self.is_recording else None

class FTPSession(BaseSession):
    def connect(self):
        # Will be implemented in Phase 2
        self.is_connected = True
        return True
    
    def _disconnect_impl(self):
        pass
    
    def send_command(self, command: str) -> str:
        # FTP commands are handled directly via protocol
        return "FTP commands not supported in this way"

class SessionManager(QObject):
    """Creates and manages active sessions"""
    
    # Signal for IP changes
    ip_changed = pyqtSignal(str)  # Emits new IP address
    
    session_types = {
        SessionType.TELNET: TelnetSession,
        SessionType.VNC: VNCSession,
        SessionType.FTP: FTPSession,
        SessionType.DEBUGGER: TelnetSession  # Use TelnetSession for DEBUGGER sessions
    }

    def validate_token(self, token: NodeToken) -> bool:
        """Validate token structure and permissions"""
        if not token or not token.token_id:
            return False
        if len(token.token_id) != 3 or not token.token_id.isdigit():
            return False
        return True
    
    def __init__(self):
        super().__init__()
        self.active_sessions = {}  # session_key -> session
        self.session_counter = 0
        self.session_cache = {}  # (host, port, session_type) -> session
        
        
    def create_session(self, config: SessionConfig, auto_connect=True) -> Optional[BaseSession]:
        """Creates a new session, optionally connecting immediately"""
        logging.debug(f"SessionManager.create_session: Creating session for {config.session_type.name} to {config.host}:{config.port}")

        # Check cache for existing session
        cache_key = (config.host, config.port, config.session_type)
        if cache_key in self.session_cache:
            existing = self.session_cache[cache_key]
            if existing.is_connected:
                logging.debug(f"Reusing existing session for {cache_key}")
                return existing
            else:
                # Remove stale session
                del self.session_cache[cache_key]
        
        session_class = self.session_types.get(config.session_type)
        if not session_class:
            raise ValueError(f"Unsupported session type: {config.session_type}")
        
        session = session_class(config)
        session_key = f"{config.session_type.name}_{self.session_counter}"
        self.session_counter += 1
        
        if auto_connect:
            if session.connect():
                self.active_sessions[session_key] = session
                self.session_cache[cache_key] = session
                logging.debug(f"SessionManager.create_session: Session created and connected: {session_key}")
                return session
            logging.error(f"SessionManager.create_session: Failed to connect session: {session_key}")
            return None
        
        # Not auto-connect - just store it
        self.active_sessions[session_key] = session
        logging.debug(f"SessionManager.create_session: Session created (not auto-connected): {session_key}")
        return session
    
    def get_debugger_session(self) -> Optional[BaseSession]:
        """Get the active debugger session if it exists and is connected"""
        for session in self.active_sessions.values():
            if session.config.session_type == SessionType.DEBUGGER and session.is_connected:
                return session
        return None
    
    def get_or_create_session(self, session_key: str, session_type: SessionType, config: SessionConfig) -> Optional[BaseSession]:
        """Get existing session or create a new one if it doesn't exist"""
        if existing := self.get_session(session_key):
            return existing
            
        return self.create_session(config, auto_connect=True)
    
    def get_session(self, session_key: str) -> Optional[BaseSession]:
        """Retrieves an active session"""
        return self.active_sessions.get(session_key)
    
    def close_session(self, session_key: str):
        """Closes a specific session"""
        if session := self.active_sessions.get(session_key):
            session.disconnect()
            del self.active_sessions[session_key]
    
    def close_all_sessions(self):
        """Closes all active sessions"""
        for session in list(self.active_sessions.values()):
            session.disconnect()
        self.active_sessions = {}
        
    def get_all_sessions(self) -> dict:
        """Returns all active sessions"""
        return self.active_sessions.copy()
        
    def get_active_sessions(self) -> list:
        """Returns all currently connected sessions"""
        return [session for session in self.active_sessions.values() if session.is_connected]
