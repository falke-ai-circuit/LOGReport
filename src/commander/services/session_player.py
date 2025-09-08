"""
Session Player Service

This service handles the replay of VNC session recordings stored in .vncr format.
"""

import os
import struct
import gzip
import json
import logging
import time
from typing import Optional, Dict, Any, List
from datetime import datetime
from PyQt6.QtCore import QObject, QTimer, pyqtSignal

from typing import Protocol

class ViewProtocol(Protocol):
    def set_vnc_content(self, content: str) -> None: ...
    def get_selected_text(self) -> str: ...
    def handle_text_selection(self, text: str) -> None: ...
    def set_recording_state(self, is_recording: bool) -> None: ...
    def set_playback_state(self, is_playing: bool, is_paused: bool = False) -> None: ...

class SessionPlayer(QObject):
    """
    Service that replays VNC session recordings from .vncr files.
    
    Features:
    - Event queue processor with adjustable speed
    - Synchronization with original timing or accelerated mode
    - Visual indicators for mouse movements and clicks
    - Integration with existing session view components
    """
    
    # Signals
    playback_started = pyqtSignal()
    playback_paused = pyqtSignal()
    playback_stopped = pyqtSignal()
    playback_finished = pyqtSignal()
    position_changed = pyqtSignal(int)  # Position in milliseconds

    def __init__(self, vnc_view: ViewProtocol):
        """
        Initialize the SessionPlayer.
        
        Args:
            vnc_view: An object implementing the ViewProtocol interface
        """
        super().__init__()
        self.vnc_view = vnc_view
        self.file_path = None
        self.is_playing = False
        self.is_paused = False
        self.playback_speed = 1.0
        self.events = []  # List of all events
        self.current_event_index = 0
        self.start_time = None
        self.timer = QTimer()
        self.timer.timeout.connect(self._process_next_event)
        self.last_event_time = 0
        self.total_duration = 0
        
        logging.debug("SessionPlayer initialized")
        
    def load_recording(self, file_path: str) -> bool:
        """
        Load a .vncr recording file and parse its events.
        
        Args:
            file_path: Path to the .vncr file
            
        Returns:
            True if file loaded successfully, False otherwise
        """
        if not os.path.exists(file_path):
            logging.error(f"Recording file not found: {file_path}")
            return False
            
        try:
            self.file_path = file_path
            self.events = []
            self.current_event_index = 0
            
            with open(file_path, 'rb') as f:
                # Read header
                magic = f.read(6)
                if magic != b'VNCREC':
                    logging.error("Invalid file format: Missing VNCREC magic number")
                    return False
                    
                # Read version
                version = f.read(2)
                logging.debug(f"File version: {version}")
                
                # Read metadata length
                metadata_length_bytes = f.read(4)
                metadata_length = struct.unpack('!I', metadata_length_bytes)[0]
                
                # Read metadata
                metadata_bytes = f.read(metadata_length)
                metadata = json.loads(metadata_bytes.decode('utf-8'))
                logging.debug(f"Metadata: {metadata}")
                
                # Read events
                while True:
                    # Try to read event header
                    header_data = f.read(18)  # 8 + 6 + 4 bytes
                    if len(header_data) < 18:
                        break  # End of file
                        
                    # Parse header
                    timestamp, event_type, payload_length = struct.unpack('!Q6sI', header_data)
                    event_type = event_type.rstrip(b'\x00').decode('utf-8')  # Remove padding
                    
                    # Read payload
                    payload_data = f.read(payload_length)
                    if len(payload_data) < payload_length:
                        logging.warning("Incomplete payload data")
                        break
                        
                    # Check if data is encrypted
                    is_encrypted = False
                    try:
                        # Try to decompress first - if it fails, it might be encrypted
                        gzip.decompress(payload_data)
                    except:
                        is_encrypted = True
                    
                    # Decrypt if needed
                    if is_encrypted:
                        try:
                            # Try to find encryption key file
                            key_file_path = file_path + ".key"
                            if os.path.exists(key_file_path):
                                with open(key_file_path, 'rb') as key_file:
                                    encryption_key = key_file.read()
                                
                                from cryptography.fernet import Fernet
                                f = Fernet(encryption_key)
                                payload_data = f.decrypt(payload_data)
                            else:
                                logging.warning("Encryption key file not found, cannot decrypt recording")
                                continue
                        except Exception as e:
                            logging.error(f"Error decrypting payload: {str(e)}")
                            continue
                    
                    # Decompress data
                    try:
                        decompressed_data = gzip.decompress(payload_data)
                        events_batch = json.loads(decompressed_data.decode('utf-8'))
                        
                        # Add events to list
                        self.events.extend(events_batch)
                        
                    except Exception as e:
                        logging.error(f"Error decompressing payload: {str(e)}")
                        continue
                        
            # Sort events by timestamp
            self.events.sort(key=lambda x: x['timestamp'])
            
            # Calculate total duration
            if self.events:
                self.total_duration = self.events[-1]['timestamp'] - self.events[0]['timestamp']
                
            logging.info(f"Loaded {len(self.events)} events from recording")
            return True
            
        except Exception as e:
            logging.error(f"Error loading recording: {str(e)}")
            return False
            
    def play(self, speed: float = 1.0):
        """
        Start playing the loaded recording.
        
        Args:
            speed: Playback speed multiplier (0.5x-2.0x)
        """
        if not self.events:
            logging.warning("No events to play")
            return
            
        if self.is_playing and not self.is_paused:
            logging.warning("Already playing")
            return
            
        self.playback_speed = max(0.5, min(2.0, speed))  # Clamp between 0.5x and 2.0x
        self.is_playing = True
        self.is_paused = False
        self.current_event_index = 0
        
        if not self.start_time:
            self.start_time = time.time()
            
        self.timer.start(10)  # Process events every 10ms
        self.playback_started.emit()
        logging.info(f"Started playback at {self.playback_speed}x speed")
        
    def pause(self):
        """Pause playback."""
        if not self.is_playing:
            return
            
        self.is_paused = True
        self.timer.stop()
        self.playback_paused.emit()
        logging.info("Playback paused")
        
    def stop(self):
        """Stop playback."""
        self.is_playing = False
        self.is_paused = False
        self.timer.stop()
        self.current_event_index = 0
        self.start_time = None
        self.playback_stopped.emit()
        logging.info("Playback stopped")
        
    def set_position(self, position_ms: int):
        """
        Set playback position.
        
        Args:
            position_ms: Position in milliseconds from start
        """
        if not self.events:
            return
            
        # Find the event closest to the requested position
        target_timestamp = self.events[0]['timestamp'] + position_ms
        
        for i, event in enumerate(self.events):
            if event['timestamp'] >= target_timestamp:
                self.current_event_index = i
                break
        else:
            # If we didn't break, we're at the end
            self.current_event_index = len(self.events) - 1
            
        self.position_changed.emit(position_ms)
        
    def set_speed(self, speed: float):
        """
        Set playback speed.
        
        Args:
            speed: Playback speed multiplier (0.5x-2.0x)
        """
        self.playback_speed = max(0.5, min(2.0, speed))  # Clamp between 0.5x and 2.0x
        logging.info(f"Playback speed set to {self.playback_speed}x")
        
    def get_duration(self) -> int:
        """
        Get the total duration of the recording in milliseconds.
        
        Returns:
            Duration in milliseconds
        """
        return self.total_duration
        
    def get_position(self) -> int:
        """
        Get the current playback position in milliseconds.
        
        Returns:
            Position in milliseconds
        """
        if not self.events or self.current_event_index >= len(self.events):
            return 0
            
        if self.current_event_index == 0:
            return 0
            
        return self.events[self.current_event_index]['timestamp'] - self.events[0]['timestamp']
        
    def _process_next_event(self):
        """Process the next event in the queue."""
        if not self.is_playing or self.is_paused or not self.events:
            return
            
        if self.current_event_index >= len(self.events):
            # End of recording
            self.stop()
            self.playback_finished.emit()
            return
            
        current_event = self.events[self.current_event_index]
        current_timestamp = current_event['timestamp']
        
        # Calculate time difference from last event
        if self.last_event_time > 0:
            time_diff = (current_timestamp - self.last_event_time) / 1000.0  # Convert to seconds
            adjusted_time_diff = time_diff / self.playback_speed
            
            # If we're behind schedule, process immediately
            elapsed_time = time.time() - self.start_time
            if elapsed_time < adjusted_time_diff:
                # Wait for the right time
                return
                
        # Process the event
        self._handle_event(current_event)
        
        # Update last event time
        self.last_event_time = current_timestamp
        
        # Move to next event
        self.current_event_index += 1
        
        # Emit position change
        position = self.get_position()
        self.position_changed.emit(position)
        
    def _handle_event(self, event: Dict[str, Any]):
        """
        Handle a single event during playback.
        
        Args:
            event: Event data to handle
        """
        event_type = event['type']
        data = event['data']
        
        try:
            if event_type == 'mouse':
                self._handle_mouse_event(data)
            elif event_type == 'keyboard':
                self._handle_keyboard_event(data)
            elif event_type == 'clipboard':
                self._handle_clipboard_event(data)
            elif event_type == 'screen':
                self._handle_screen_event(data)
            else:
                logging.warning(f"Unknown event type: {event_type}")
                
        except Exception as e:
            logging.error(f"Error handling event {event_type}: {str(e)}")
            
    def _handle_mouse_event(self, data: Dict[str, Any]):
        """
        Handle a mouse event during playback.
        
        Args:
            data: Mouse event data
        """
        x = data.get('x', 0)
        y = data.get('y', 0)
        button = data.get('button')
        
        # Update VNC view with mouse position
        # In a real implementation, you would update a visual indicator
        logging.debug(f"Mouse event: x={x}, y={y}, button={button}")
        
        # For now, just log the event
        # In a full implementation, you would update visual indicators in the VNC view
        
    def _handle_keyboard_event(self, data: Dict[str, Any]):
        """
        Handle a keyboard event during playback.
        
        Args:
            data: Keyboard event data
        """
        key = data.get('key', '')
        
        # Log the event
        logging.debug(f"Keyboard event: key={key}")
        
        # In a full implementation, you would simulate key presses in the VNC view
        
    def _handle_clipboard_event(self, data: Dict[str, Any]):
        """
        Handle a clipboard event during playback.
        
        Args:
            data: Clipboard event data
        """
        clipboard_content = data.get('clipboard', '')
        
        # Log the event
        logging.debug(f"Clipboard event: content length={len(clipboard_content)}")
        
        # In a full implementation, you would update the clipboard content display
        
    def _handle_screen_event(self, data: Dict[str, Any]):
        """
        Handle a screen event during playback.
        
        Args:
            data: Screen event data
        """
        screen_data = data.get('screen', '')
        
        # Log the event
        logging.debug(f"Screen event: data length={len(screen_data)}")
        
        # In a full implementation, you would update the VNC view with the screen data
        if hasattr(self.vnc_view, 'set_vnc_content') and screen_data:
            # This is a simplified implementation
            # In a real implementation, you would decode the screen data and update the display
            pass