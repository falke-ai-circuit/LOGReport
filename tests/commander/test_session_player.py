import os
import sys
import json
import struct
import gzip
import tempfile
from unittest.mock import MagicMock, patch, mock_open
from datetime import datetime

# Add src directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'src')))

import pytest
from commander.services.session_player import SessionPlayer
from commander.ui.session_view import SessionView


class TestSessionPlayer:
    """Test suite for SessionPlayer service"""
    
    @pytest.fixture
    def mock_session_view(self):
        """Create a mock SessionView"""
        mock_view = MagicMock()
        return mock_view
    
    @pytest.fixture
    def temp_recording_file(self):
        """Create a temporary recording file for testing"""
        # Create a valid .vncr file structure
        with tempfile.NamedTemporaryFile(suffix='.vncr', delete=False) as f:
            temp_path = f.name
            
            # Write header
            f.write(b'VNCREC')  # Magic number
            f.write(b'\x01\x00')  # Version
            
            # Write metadata
            metadata = {
                "startTime": "2023-01-01T00:00:00Z",
                "endTime": "2023-01-01T00:01:00Z",
                "node": "AP01m",
                "sessionType": "VNC"
            }
            metadata_bytes = json.dumps(metadata).encode('utf-8')
            f.write(struct.pack('!I', len(metadata_bytes)))  # Metadata length
            f.write(metadata_bytes)
            
            # Write a sample event
            events = [
                {
                    "timestamp": 1672531200000,  # Jan 1, 2023 00:00:00 UTC
                    "type": "mouse",
                    "data": {"x": 100, "y": 200, "button": "left"}
                },
                {
                    "timestamp": 1672531201000,  # Jan 1, 2023 00:00:01 UTC
                    "type": "keyboard",
                    "data": {"key": "a"}
                }
            ]
            
            # Compress events
            events_bytes = json.dumps(events).encode('utf-8')
            compressed_events = gzip.compress(events_bytes)
            
            # Write event header and data
            timestamp = 1672531200000
            event_type = b'mouse\0\0'  # 6 bytes with padding
            payload_length = len(compressed_events)
            f.write(struct.pack('!Q6sI', timestamp, event_type, payload_length))
            f.write(compressed_events)
            
        yield temp_path
        # Cleanup
        if os.path.exists(temp_path):
            os.unlink(temp_path)
    
    @pytest.fixture
    def session_player(self, mock_session_view):
        """Create a SessionPlayer instance"""
        player = SessionPlayer(mock_session_view)
        return player
    
    def test_initialization(self, session_player, mock_session_view):
        """Test SessionPlayer initialization"""
        assert session_player.vnc_view == mock_session_view
        assert session_player.file_path is None
        assert session_player.is_playing is False
        assert session_player.is_paused is False
        assert session_player.playback_speed == 1.0
        assert session_player.events == []
        assert session_player.current_event_index == 0
        assert session_player.start_time is None
        assert session_player.last_event_time == 0
        assert session_player.total_duration == 0
    
    def test_load_recording_success(self, session_player, temp_recording_file):
        """Test successful loading of a recording file"""
        result = session_player.load_recording(temp_recording_file)
        
        assert result is True
        assert session_player.file_path == temp_recording_file
        assert len(session_player.events) > 0
        assert session_player.total_duration > 0
    
    def test_load_recording_file_not_found(self, session_player):
        """Test loading a recording file that doesn't exist"""
        result = session_player.load_recording("nonexistent.vncr")
        
        assert result is False
        assert session_player.events == []
    
    def test_load_recording_invalid_format(self, session_player):
        """Test loading a file with invalid format"""
        with tempfile.NamedTemporaryFile(suffix='.vncr', delete=False) as f:
            temp_path = f.name
            f.write(b'INVALID')  # Invalid magic number
        
        try:
            result = session_player.load_recording(temp_path)
            assert result is False
            assert session_player.events == []
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)
    
    def test_play_success(self, session_player, temp_recording_file):
        """Test successful playback start"""
        # Load a recording first
        session_player.load_recording(temp_recording_file)
        
        # Mock the timer
        with patch.object(session_player.timer, 'start') as mock_start:
            session_player.play()
            
            assert session_player.is_playing is True
            assert session_player.is_paused is False
            assert session_player.playback_speed == 1.0
            assert session_player.current_event_index == 0
            mock_start.assert_called_once_with(10)
    
    def test_play_no_events(self, session_player):
        """Test playing when no events are loaded"""
        with patch.object(session_player.timer, 'start') as mock_start:
            session_player.play()
            
            # Should not start timer when no events
            mock_start.assert_not_called()
            assert session_player.is_playing is False
    
    def test_play_already_playing(self, session_player, temp_recording_file):
        """Test playing when already playing"""
        # Load and start playing
        session_player.load_recording(temp_recording_file)
        with patch.object(session_player.timer, 'start'):
            session_player.play()
        
        # Try to play again
        with patch.object(session_player.timer, 'start') as mock_start:
            session_player.play()
            
            # Should not start timer again
            mock_start.assert_not_called()
    
    def test_pause(self, session_player, temp_recording_file):
        """Test pausing playback"""
        # Load and start playing
        session_player.load_recording(temp_recording_file)
        with patch.object(session_player.timer, 'start'):
            session_player.play()
        
        # Pause playback
        with patch.object(session_player.timer, 'stop') as mock_stop:
            session_player.pause()
            
            assert session_player.is_paused is True
            mock_stop.assert_called_once()
    
    def test_pause_not_playing(self, session_player):
        """Test pausing when not playing"""
        with patch.object(session_player.timer, 'stop') as mock_stop:
            session_player.pause()
            
            # Should not stop timer when not playing
            mock_stop.assert_not_called()
    
    def test_stop(self, session_player, temp_recording_file):
        """Test stopping playback"""
        # Load and start playing
        session_player.load_recording(temp_recording_file)
        with patch.object(session_player.timer, 'start'):
            session_player.play()
        
        # Stop playback
        with patch.object(session_player.timer, 'stop') as mock_stop:
            session_player.stop()
            
            assert session_player.is_playing is False
            assert session_player.is_paused is False
            assert session_player.current_event_index == 0
            assert session_player.start_time is None
            mock_stop.assert_called_once()
    
    def test_set_speed(self, session_player):
        """Test setting playback speed"""
        # Test normal speed
        session_player.set_speed(1.5)
        assert session_player.playback_speed == 1.5
        
        # Test clamping of speed (max 2.0)
        session_player.set_speed(3.0)
        assert session_player.playback_speed == 2.0
        
        # Test clamping of speed (min 0.5)
        session_player.set_speed(0.1)
        assert session_player.playback_speed == 0.5
    
    def test_get_duration(self, session_player, temp_recording_file):
        """Test getting recording duration"""
        # Before loading
        assert session_player.get_duration() == 0
        
        # After loading
        session_player.load_recording(temp_recording_file)
        assert session_player.get_duration() > 0
    
    def test_get_position(self, session_player, temp_recording_file):
        """Test getting current playback position"""
        # Before loading
        assert session_player.get_position() == 0
        
        # After loading
        session_player.load_recording(temp_recording_file)
        assert session_player.get_position() == 0
        
        # After moving to first event
        session_player.current_event_index = 1
        position = session_player.get_position()
        assert position > 0
    
    def test_set_position(self, session_player, temp_recording_file):
        """Test setting playback position"""
        # Load recording
        session_player.load_recording(temp_recording_file)
        
        # Set position to middle of recording
        duration = session_player.get_duration()
        session_player.set_position(duration // 2)
        
        # Position should have changed
        assert session_player.current_event_index > 0
    
    def test_handle_mouse_event(self, session_player):
        """Test handling mouse events"""
        mock_vnc_view = session_player.vnc_view
        event_data = {"x": 100, "y": 200, "button": "left"}
        
        session_player._handle_mouse_event(event_data)
        
        # In the current implementation, this just logs the event
        # In a real implementation, it would update visual indicators
    
    def test_handle_keyboard_event(self, session_player):
        """Test handling keyboard events"""
        event_data = {"key": "a"}
        
        session_player._handle_keyboard_event(event_data)
        
        # In the current implementation, this just logs the event
        # In a real implementation, it would simulate key presses
    
    def test_handle_clipboard_event(self, session_player):
        """Test handling clipboard events"""
        event_data = {"clipboard": "test content"}
        
        session_player._handle_clipboard_event(event_data)
        
        # In the current implementation, this just logs the event
        # In a real implementation, it would update clipboard content display
    
    def test_handle_screen_event(self, session_player):
        """Test handling screen events"""
        event_data = {"screen": "base64encodeddata"}
        
        session_player._handle_screen_event(event_data)
        
        # In the current implementation, this just logs the event
        # In a real implementation, it would update the VNC view
    
    def test_process_next_event_end_of_recording(self, session_player, temp_recording_file):
        """Test processing when at end of recording"""
        # Load recording
        session_player.load_recording(temp_recording_file)
        
        # Add a dummy event to ensure session_player.events is not empty
        session_player.events = [{'timestamp': 1, 'type': 'dummy', 'data': {}}]
        
        # Start playback so is_playing is True
        session_player.play()

        # Move to end of events (which is now after the dummy event)
        session_player.current_event_index = len(session_player.events)
        
        # Process next event (should stop playback)
        with patch.object(session_player, 'stop') as mock_stop:
            # Directly call _process_next_event to simulate timer timeout
            session_player._process_next_event()
            mock_stop.assert_called_once()
            assert session_player.is_playing is False # Assert after the mock is out of scope



if __name__ == "__main__":
    pytest.main([__file__, "-v"])