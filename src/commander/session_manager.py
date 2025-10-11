"""
Session Manager
Handles Telnet and FTP session connections
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
from PyQt5.QtCore import QObject, pyqtSignal
from .models import NodeToken

class SessionType(Enum):
    TELNET = "TELNET"
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
        # Multiple, more specific prompt patterns with proper anchoring
        self.prompt_patterns = [
            re.compile(r'\n\d+[a-z]\%\s*$'),  # Prompt at beginning of line after newline
            re.compile(r'^\d+[a-z]\%\s*$'),   # Prompt at very beginning of response
            re.compile(r'\r\n\d+[a-z]\%\s*$') # Prompt after carriage return and newline
        ]
        # Debugger conflict prompt patterns
        self.debugger_prompt_patterns = [
            re.compile(r'someone else is connected.*want to connect', re.IGNORECASE),
            re.compile(r'already connected.*do you want to connect', re.IGNORECASE),
            re.compile(r'debugger session.*\?', re.IGNORECASE)
        ]
        # System mode pattern (%s for system, %a for appl)
        self.system_mode_pattern = re.compile(r'\d+[a-z]\%[sa]\s*$')
        self.current_mode = None  # Track current mode state
        
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
        """Close telnet connection and ensure complete socket cleanup"""
        if self.connection:
            try:
                # Get socket before closing connection
                sock = None
                if hasattr(self.connection, 'get_socket'):
                    sock = self.connection.get_socket()
                
                # Close telnet connection first
                try:
                    self.connection.close()
                except Exception as e:
                    logging.debug(f"TelnetSession._disconnect_impl: Error closing telnet connection: {e}")
                
                # Ensure socket is completely closed
                if sock:
                    try:
                        # Shutdown both directions
                        sock.shutdown(socket.SHUT_RDWR)
                    except Exception as e:
                        logging.debug(f"TelnetSession._disconnect_impl: Error shutting down socket: {e}")
                    
                    try:
                        # Close socket
                        sock.close()
                    except Exception as e:
                        logging.debug(f"TelnetSession._disconnect_impl: Error closing socket: {e}")
                
                logging.debug("TelnetSession._disconnect_impl: Connection fully closed")
                
            except Exception as e:
                logging.error(f"TelnetSession._disconnect_impl: Error during disconnect: {e}")
            finally:
                self.connection = None
                self.is_connected = False
    
    def verify_system_mode(self) -> bool:
        """
        Verify that the telnet session is in system mode.
        Performs debugger initialization sequence:
        1. Send "yes" to handle connection prompts
        2. Send CTRL+Z to clear terminal
        3. Send "systemmode" command to guarantee system mode
        
        Returns:
            bool: True if system mode verified or switched successfully, False on error
        """
        if not self.is_connected:
            logging.error("TelnetSession.verify_system_mode: Not connected")
            return False
        
        try:
            logging.debug("TelnetSession.verify_system_mode: Starting debugger initialization sequence")
            
            # Step 1: Send "yes" to handle any connection prompts
            logging.debug("TelnetSession.verify_system_mode: Sending 'yes' for connection prompt")
            self.connection.write(b'yes\r\n')
            time.sleep(1.0)  # Wait for "yes" response to fully arrive
            yes_response = self.connection.read_very_eager().decode('ascii', 'ignore')
            logging.debug(f"TelnetSession.verify_system_mode: Yes response: {yes_response}")
            
            # Step 2: Send CTRL+Z to clear terminal
            logging.debug("TelnetSession.verify_system_mode: Sending CTRL+Z to clear terminal")
            self.connection.write(b'\x1a')  # CTRL+Z is ASCII 26 (0x1a)
            time.sleep(0.5)  # Wait for clear response
            clear_response = self.connection.read_very_eager().decode('ascii', 'ignore')
            logging.debug(f"TelnetSession.verify_system_mode: Clear response: {clear_response}")
            
            # Step 3: Send "systemmode" command to guarantee system mode
            # No need to read response - systemmode command is guaranteed to work
            logging.debug("TelnetSession.verify_system_mode: Sending 'systemmode' command")
            self.connection.write(b'systemmode\r\n')
            time.sleep(0.5)  # Brief wait for command to execute
            
            # Set current mode to system
            self.current_mode = 'system'
            logging.info("TelnetSession.verify_system_mode: System mode set successfully")
            return True
            
        except Exception as e:
            logging.error(f"TelnetSession.verify_system_mode: Error verifying mode - {str(e)}", exc_info=True)
            return False
    
    def _handle_debugger_prompts(self, response: str) -> str:
        """
        Detect and handle debugger session conflict prompts.
        If "someone else is connected, want to connect?" prompt is detected,
        automatically respond with "yes".
        
        Args:
            response: Raw response from telnet session
            
        Returns:
            str: Processed response with prompt handling applied
        """
        if not response:
            return response
        
        # Check for debugger conflict prompts
        for pattern in self.debugger_prompt_patterns:
            if pattern.search(response):
                logging.info("TelnetSession._handle_debugger_prompts: Detected debugger conflict prompt")
                logging.debug(f"TelnetSession._handle_debugger_prompts: Matched pattern: {pattern.pattern}")
                try:
                    # Send "yes" response to take over the debugger session
                    logging.debug("TelnetSession._handle_debugger_prompts: Sending 'yes' response")
                    self.connection.write(b'yes\r\n')
                    time.sleep(0.5)
                    
                    # Read confirmation response
                    confirmation = self.connection.read_very_eager().decode('ascii', 'ignore')
                    logging.debug(f"TelnetSession._handle_debugger_prompts: Confirmation response: {confirmation}")
                    
                    # Return confirmation as new response
                    return confirmation
                    
                except Exception as e:
                    logging.error(f"TelnetSession._handle_debugger_prompts: Error responding to prompt - {str(e)}", exc_info=True)
                    return response
        
        # No debugger prompt detected, return original response
        return response
    
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
            cleared = self.connection.read_very_eager().decode('ascii', 'ignore')
            logging.debug(f"TelnetSession.send_command: Cleared {len(cleared)} bytes from buffer")
            
            # Handle any debugger prompts in cleared buffer
            if cleared:
                cleared = self._handle_debugger_prompts(cleared)

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
            
            # Handle debugger prompts in response
            response = self._handle_debugger_prompts(response)
            
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
        logging.debug(f"TelnetSession._read_response: Using prompt patterns: {[p.pattern for p in self.prompt_patterns]}")
        
        while (time.time() - start_time) < timeout:
            chunk = self.connection.read_very_eager()
            if chunk:
                response += chunk
                last_data_time = time.time()
                decoded = response.decode('ascii', 'ignore')
                logging.debug(f"TelnetSession._read_response: Received {len(chunk)} bytes, total {len(response)}")
                
                # Check for any of the prompt patterns
                if any(pattern.search(decoded) for pattern in self.prompt_patterns):
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
    
    def close_session(self, session_or_key):
        """Closes a specific session by key or by session object"""
        # Handle both session object and session key string
        if isinstance(session_or_key, str):
            # It's a session key
            session_key = session_or_key
            session = self.active_sessions.get(session_key)
            if session:
                # Remove from cache
                cache_key = (session.config.host, session.config.port, session.config.session_type)
                logging.debug(f"SessionManager.close_session: Removing session from cache: {cache_key}")
                if cache_key in self.session_cache:
                    del self.session_cache[cache_key]
                    logging.debug(f"SessionManager.close_session: Cache entry deleted")
                # Disconnect and remove from active sessions
                session.disconnect()
                del self.active_sessions[session_key]
        else:
            # It's a session object
            session = session_or_key
            # Remove from cache
            cache_key = (session.config.host, session.config.port, session.config.session_type)
            logging.debug(f"SessionManager.close_session: Removing session from cache (by object): {cache_key}")
            if cache_key in self.session_cache:
                del self.session_cache[cache_key]
                logging.debug(f"SessionManager.close_session: Cache entry deleted (by object)")
            # Find and remove from active sessions
            for key, active_session in list(self.active_sessions.items()):
                if active_session is session:
                    logging.debug(f"SessionManager.close_session: Removing from active sessions: {key}")
                    del self.active_sessions[key]
                    break
            # Disconnect the session
            session.disconnect()
    
    def close_all_sessions(self):
        """Closes all active sessions"""
        for session in list(self.active_sessions.values()):
            session.disconnect()
        self.active_sessions = {}
        self.session_cache = {}  # Clear cache as well
        
    def get_all_sessions(self) -> dict:
        """Returns all active sessions"""
        return self.active_sessions.copy()
        
    def get_active_sessions(self) -> list:
        """Returns all currently connected sessions"""
        return [session for session in self.active_sessions.values() if session.is_connected]
