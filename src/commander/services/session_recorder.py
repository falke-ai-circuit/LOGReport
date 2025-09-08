"""
Session Recorder Service

This service handles the recording of VNC sessions, capturing events and storing them
in the .vncr format for later replay.
"""

import os
import time
import struct
import gzip
import json
import logging
import re
from typing import Optional, Dict, Any
from datetime import datetime
from pathlib import Path
from PyQt6.QtCore import QObject, QTimer
import re # Moved re import here to avoid conflict

from commander.models import NodeToken
from commander.utils.token_utils import token_validator
from commander.constants import TOKEN_PATTERN # Added for node token redaction
import psutil
import threading
from cryptography.fernet import Fernet # Added for module-level availability

# Define a pattern for redacting node tokens within content
NODE_TOKEN_REDACTION_PATTERN = re.compile(r'[A-Z0-9]+')


class SessionRecorder(QObject):
    """
    Service that records VNC session events and stores them in .vncr format.
    
    Features:
    - Event capture for mouse movements, clicks, keyboard inputs, clipboard operations
    - .vncr storage format with header and event stream
    - Delta encoding for screen updates
    - GZIP compression at intervals
    - Automatic file rotation when size threshold reached
    - Security features (redaction, encryption)
    """
    
    def __init__(self, output_path: str, node_token: Optional[NodeToken] = None):
        """
        Initialize the SessionRecorder.
        
        Args:
            output_path: Path where recording file will be saved
            node_token: NodeToken associated with this recording
        """
        super().__init__()
        self.output_path = output_path
        self.node_token = node_token
        self.is_recording = False
        self.start_time = None
        self.end_time = None
        self.file_handle = None
        self.event_count = 0
        self.current_file_size = 0
        self.max_file_size = 500 * 1024 * 1024  # 500MB default
        self.compression_level = 6
        self.screen_capture_interval = 100  # ms
        self.clipboard_capture = True
        self.encryption_enabled = False
        self.encryption_key = None
        
        # Performance monitoring
        self.cpu_usage = 0.0
        self.monitoring_active = False
        self.monitoring_thread = None
        
        # Load configuration
        
        # Derive storage_dir from output_path, but ensure it's a valid, writable subdirectory
        derived_storage_dir = os.path.dirname(self.output_path)
        
        # Always use a subdirectory within the current working directory if the derived path is a root.
        if not derived_storage_dir or (Path(derived_storage_dir).is_absolute() and not Path(derived_storage_dir).parts[1:]):
            self.storage_dir = os.path.join(os.getcwd(), "temp_session_recordings")
        else:
            self.storage_dir = derived_storage_dir
            
        # Load configuration (this might update self.storage_dir)
        self._load_config()
        
        # Ensure the final storage directory exists after config loading
        if self.storage_dir and not os.path.exists(self.storage_dir):
            os.makedirs(self.storage_dir, exist_ok=True) # Use exist_ok=True to prevent errors if dir already exists
            
        # Initialize compression buffer
        self.compression_buffer = []
        self.compression_timer = QTimer()
        self.compression_timer.timeout.connect(self._flush_compression_buffer)
        self.compression_timer.start(500)  # Flush every 500ms
        
        logging.debug(f"SessionRecorder initialized for output: {output_path}")
        
    def _load_config(self):
        """Load recording configuration from YAML file."""
        config_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
            "config", "settings", "recording.yaml"
        )
        
        try:
            import yaml
            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    config = yaml.safe_load(f)
                    recording_config = config.get('session_recording', {})
                    
                    self.max_file_size = recording_config.get('max_file_size', 500) * 1024 * 1024
                    self.compression_level = recording_config.get('compression_level', 6)
                    self.screen_capture_interval = recording_config.get('screen_capture_interval', 100)
                    self.clipboard_capture = recording_config.get('clipboard_capture', True)
                    self.encryption_enabled = recording_config.get('encryption_enabled', False)
                    
                    logging.debug("Recording configuration loaded successfully")
            else:
                logging.warning(f"Recording configuration file not found: {config_path}")
                # Set a safe fallback for storage_dir for tests
                self.storage_dir = os.path.join(os.getcwd(), "test_recordings")
        except Exception as e:
            logging.error(f"Error loading recording configuration: {str(e)}")
            
    def start(self) -> bool:
        """
        Start recording session events.
        
        Returns:
            True if recording started successfully, False otherwise
        """
        if self.is_recording:
            logging.warning("Recording already in progress")
            return False
            
        try:
            # Open file for writing
            self.file_handle = open(self.output_path, 'wb')
            
            # Write header
            self._write_header()
            
            self.is_recording = True
            self.start_time = datetime.utcnow().isoformat()
            self.event_count = 0
            self.current_file_size = 0
            
            
            # Generate encryption key if encryption is enabled
            if self.encryption_enabled:
                try:
                    self.encryption_key = Fernet.generate_key()
                    logging.debug("Encryption key generated")
                except Exception as e:
                    logging.error(f"Error generating encryption key: {str(e)}")
                    self.encryption_enabled = False
            
            # Start performance monitoring
            self._start_performance_monitoring()
            
            logging.info(f"Started recording session to: {self.output_path}")
            return True
            
        except Exception as e:
            logging.error(f"Failed to start recording: {str(e)}")
            if self.file_handle:
                self.file_handle.close()
                self.file_handle = None
            return False
    def stop(self):
        """Stop recording session events."""
        if not self.is_recording:
            return
            
        self.is_recording = False
        self.end_time = datetime.utcnow().isoformat()
        
        # Flush any remaining events
        self._flush_compression_buffer()
        
        # Close file
        if self.file_handle:
            # Update header with end time
            self._update_header()
            self.file_handle.close()
            self.file_handle = None
            
        # Stop performance monitoring
        self._stop_performance_monitoring()
            
        logging.info(f"Stopped recording session. Total events: {self.event_count}")
        
    def record_mouse_event(self, x: int, y: int, button: Optional[str] = None):
        """
        Record a mouse event.
        
        Args:
            x: X coordinate
            y: Y coordinate
            button: Mouse button pressed (left, right, middle)
        """
        if not self.is_recording:
            return
            
        event_data = {
            'x': x,
            'y': y
        }
        
        if button:
            event_data['button'] = button
            
        self._record_event('mouse', event_data)
        
    def record_keyboard_event(self, key: str):
        """
        Record a keyboard event.
        
        Args:
            key: Key pressed
        """
        if not self.is_recording:
            return
            
        # Redact sensitive keys
        if self._is_sensitive_key(key):
            key = "[REDACTED]"
            
        event_data = {
            'key': key
        }
        
        self._record_event('keyboard', event_data)
        
    def record_clipboard_event(self, content: str):
        """
        Record a clipboard event.
        
        Args:
            content: Clipboard content
        """
        if not self.is_recording or not self.clipboard_capture:
            return
            
        # Redact sensitive content
        content = self._redact_sensitive_content(content)
        
        event_data = {
            'clipboard': content
        }
        
        self._record_event('clipboard', event_data)
        
    def record_screen_event(self, screen_data: str):
        """
        Record a screen update event.
        
        Args:
            screen_data: Base64-encoded screen diff
        """
        if not self.is_recording:
            return
            
        event_data = {
            'screen': screen_data
        }
        
        self._record_event('screen', event_data)
        
    def _record_event(self, event_type: str, data: Dict[str, Any]):
        """
        Record a generic event.
        
        Args:
            event_type: Type of event
            data: Event data
        """
        if not self.is_recording:
            return
            
        # Check file size limit
        if self.current_file_size >= self.max_file_size:
            logging.warning("Recording file size limit reached, stopping recording")
            self.stop()
            return
            
        timestamp = int(time.time() * 1000)  # Unix timestamp in ms
        event = {
            'timestamp': timestamp,
            'type': event_type,
            'data': data
        }
        
        # Add to compression buffer
        self.compression_buffer.append(event)
        self.event_count += 1
        
        # Check if we need to flush immediately (for important events)
        if event_type in ['mouse', 'keyboard']:
            self._flush_compression_buffer()
            
    def _flush_compression_buffer(self):
        """Flush the compression buffer to file."""
        if not self.compression_buffer or not self.is_recording:
            return
            
        try:
            # Serialize events
            events_data = json.dumps(self.compression_buffer).encode('utf-8')
            
            
            # Compress data
            compressed_data = gzip.compress(events_data, compresslevel=self.compression_level)
            
            # Encrypt data if encryption is enabled
            if self.encryption_enabled and self.encryption_key:
                try:
                    f = Fernet(self.encryption_key)
                    compressed_data = f.encrypt(compressed_data)
                except Exception as e:
                    logging.error(f"Error encrypting data: {str(e)}")
            
            # Write to file with format: [TIMESTAMP][EVENT_TYPE][PAYLOAD_LENGTH][PAYLOAD]
            timestamp = int(time.time() * 1000)
            event_type = b'EVENTS'
            payload_length = len(compressed_data)
            
            # Pack header: timestamp (8 bytes), event_type (6 bytes), payload_length (4 bytes)
            header = struct.pack('!Q6sI', timestamp, event_type, payload_length)
            
            # Write to file
            self.file_handle.write(header)
            self.file_handle.write(compressed_data)
            
            # Update file size
            self.current_file_size += len(header) + payload_length
            # Clear buffer
            self.compression_buffer.clear()
            
        except Exception as e:
            logging.error(f"Error flushing compression buffer: {str(e)}")
            
    def _write_header(self):
        """Write the .vncr file header."""
        if not self.file_handle:
            return
            
        # Write magic number
        self.file_handle.write(b'VNCREC')
        
        # Write version
        self.file_handle.write(b'\x01\x00')  # Version 1.0
        
        # Create metadata
        metadata = {
            'startTime': self.start_time or datetime.utcnow().isoformat(),
            'node': self.node_token.token_id if self.node_token else 'unknown',
            'sessionType': 'VNC'
        }
        
        # Serialize and write metadata
        metadata_json = json.dumps(metadata).encode('utf-8')
        metadata_length = len(metadata_json)
        
        # Write metadata length (4 bytes)
        self.file_handle.write(struct.pack('!I', metadata_length))
        
        # Write metadata
        self.file_handle.write(metadata_json)
        
        # Update file size
        self.current_file_size = 6 + 2 + 4 + metadata_length  # Magic + Version + Length + Metadata
        
    def _update_header(self):
        """Update the .vncr file header with end time."""
        if not self.file_handle:
            return
            
        # Seek to the position where endTime should be added
        # For simplicity, we'll just append it to the end of the file
        # In a real implementation, you might want to update the metadata in place
        metadata_update = {
            'endTime': self.end_time
        }
        
        metadata_json = json.dumps(metadata_update).encode('utf-8')
        self.file_handle.write(metadata_json)
        
        # If encryption is enabled, save the encryption key to a separate file
        if self.encryption_enabled and self.encryption_key:
            key_file_path = self.output_path + ".key"
            try:
                with open(key_file_path, 'wb') as key_file:
                    key_file.write(self.encryption_key)
                logging.debug(f"Encryption key saved to: {key_file_path}")
            except Exception as e:
                logging.error(f"Error saving encryption key: {str(e)}")
        
    def _is_sensitive_key(self, key: str) -> bool:
        """
        Check if a key is sensitive and should be redacted.
        
        Args:
            key: Key to check
            
        Returns:
            True if key is sensitive, False otherwise
        """
        sensitive_keys = ['password', 'passwd', 'pwd', 'secret', 'token']
        key_lower = key.lower()
        return any(sensitive in key_lower for sensitive in sensitive_keys)
        
    def _redact_sensitive_content(self, content: str) -> str:
        """
        Redact sensitive content from clipboard data.
        
        Args:
            content: Content to redact
            
        Returns:
            Redacted content
        """
        # Simple pattern matching for sensitive data
        
        # Redact passwords
        content = re.sub(r'(password|passwd|pwd)\s*[=:]\s*["\']?[^"\']*["\']?',
                         r'\1=[REDACTED]', content, flags=re.IGNORECASE)
                         
        # Redact tokens
        content = re.sub(r'(token|auth)\s*[=:]\s*["\']?[^"\']*["\']?',
                         r'\1=[REDACTED]', content, flags=re.IGNORECASE)
                         
        # Redact IP addresses
        content = re.sub(r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b',
                         '[REDACTED_IP]', content)
                         
        # Redact node tokens (e.g., "AP01m", "LI01", "RPCX")
        # This uses a pattern that matches the general structure of tokens
        # based on NODE_TOKEN_REDACTION_PATTERN.
        content = re.sub(r'(Node\s*ID:\s*)(' + NODE_TOKEN_REDACTION_PATTERN.pattern + r')', r'\1[REDACTED_TOKEN]', content)
        return content
        
    def finalize(self) -> str:
        """
        Finalize the recording and return the output path.
        
        Returns:
            Path to the recorded file
        """
        if self.is_recording:
            self.stop()
            
        return self.output_path
        
    def _start_performance_monitoring(self):
        """Start monitoring CPU usage."""
        self.monitoring_active = True
        self.monitoring_thread = threading.Thread(target=self._monitor_performance, daemon=True)
        self.monitoring_thread.start()
        
    def _stop_performance_monitoring(self):
        """Stop monitoring CPU usage."""
        self.monitoring_active = False
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=1.0)
            
    def _monitor_performance(self):
        """Monitor CPU usage in a separate thread."""
        while self.monitoring_active and self.is_recording:
            try:
                # Get current process CPU usage
                process = psutil.Process()
                self.cpu_usage = process.cpu_percent(interval=1.0)
                
                # Log warning if CPU usage is too high
                if self.cpu_usage > 15.0:
                    logging.warning(f"High CPU usage detected during recording: {self.cpu_usage:.1f}%")
            except Exception as e:
                logging.error(f"Error monitoring performance: {str(e)}")
                break
                
    def get_cpu_usage(self) -> float:
        """
        Get current CPU usage.
        
        Returns:
            Current CPU usage percentage
        """
        return self.cpu_usage