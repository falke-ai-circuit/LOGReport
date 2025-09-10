import pytest
from unittest.mock import MagicMock, patch
from src.commander.services.telnet_service import TelnetService
from src.commander.session_manager import SessionManager, SessionConfig, SessionType
from src.commander.widgets import ConnectionState


@pytest.fixture
def mock_session_manager():
    """Fixture for a mocked SessionManager."""
    return MagicMock(spec=SessionManager)


@pytest.fixture
def telnet_service(mock_session_manager):
    """Fixture for TelnetService with mocked dependencies."""
    service = TelnetService(mock_session_manager)
    # Mock the signals
    service.status_message_signal = MagicMock()
    service.command_finished_signal = MagicMock()
    service.update_connection_status_signal = MagicMock()
    return service


class TestTelnetConnectUnit:
    """Unit tests for Telnet connect functionality."""

    def test_connect_success_emits_correct_signals(self, telnet_service, mock_session_manager):
        """Test that successful connection emits correct signals with proper arguments."""
        # Setup
        host = "localhost"
        port = 23
        
        # Mock session
        mock_session = MagicMock()
        mock_session.is_connected = True
        mock_session_manager.create_session.return_value = mock_session
        
        # Execute
        result = telnet_service.connect(host, port)
        
        # Assert
        assert result is True
        mock_session_manager.create_session.assert_called_once()
        telnet_service.status_message_signal.emit.assert_called_once_with(
            f"Connected to {host}:{port}", 
            TelnetService.STATUS_MSG_MEDIUM
        )
        telnet_service.update_connection_status_signal.emit.assert_any_call(ConnectionState.CONNECTING)
        telnet_service.update_connection_status_signal.emit.assert_called_with(ConnectionState.CONNECTED)

    def test_connect_failure_emits_error_signals(self, telnet_service, mock_session_manager):
        """Test that connection failure emits error signals with proper arguments."""
        # Setup
        host = "badhost"
        port = 23
        
        # Mock session creation to raise an exception
        mock_session_manager.create_session.side_effect = Exception("Connection failed")
        
        # Execute
        result = telnet_service.connect(host, port)
        
        # Assert
        assert result is False
        telnet_service.status_message_signal.emit.assert_called_once_with(
            "Connection error: Connection failed", 
            TelnetService.STATUS_MSG_LONG
        )
        telnet_service.update_connection_status_signal.emit.assert_any_call(ConnectionState.CONNECTING)
        telnet_service.update_connection_status_signal.emit.assert_called_with(ConnectionState.ERROR)

    def test_connect_timeout_emits_timeout_signals(self, telnet_service, mock_session_manager):
        """Test that connection timeout emits timeout signals with proper arguments."""
        # Setup
        host = "slowhost"
        port = 23
        
        # Mock session creation to raise a timeout
        import socket
        mock_session_manager.create_session.side_effect = socket.timeout("Connection timed out")
        
        # Execute
        result = telnet_service.connect(host, port)
        
        # Assert
        assert result is False
        telnet_service.status_message_signal.emit.assert_called_once_with(
            "Connection timed out: Connection timed out", 
            TelnetService.STATUS_MSG_LONG
        )
        telnet_service.update_connection_status_signal.emit.assert_any_call(ConnectionState.CONNECTING)
        telnet_service.update_connection_status_signal.emit.assert_called_with(ConnectionState.ERROR)

    def test_connect_refused_emits_refused_signals(self, telnet_service, mock_session_manager):
        """Test that connection refused emits refused signals with proper arguments."""
        # Setup
        host = "refusedhost"
        port = 23
        
        # Mock session creation to raise connection refused
        import socket
        mock_session_manager.create_session.side_effect = ConnectionRefusedError("Connection refused")
        
        # Execute
        result = telnet_service.connect(host, port)
        
        # Assert
        assert result is False
        telnet_service.status_message_signal.emit.assert_called_once_with(
            "Connection refused: Connection refused", 
            TelnetService.STATUS_MSG_LONG
        )
        telnet_service.update_connection_status_signal.emit.assert_any_call(ConnectionState.CONNECTING)
        telnet_service.update_connection_status_signal.emit.assert_called_with(ConnectionState.ERROR)

    def test_toggle_connection_connect_saves_settings(self, telnet_service, mock_session_manager):
        """Test that toggle_connection saves connection parameters to settings."""
        # Setup
        host = "localhost"
        port = 23
        connect = True
        
        # Mock settings object
        mock_settings = MagicMock()
        
        # Mock session
        mock_session = MagicMock()
        mock_session.is_connected = True
        mock_session_manager.create_session.return_value = mock_session
        
        # Execute
        result = telnet_service.toggle_connection(connect, host, port, mock_settings)
        
        # Assert
        assert result is True
        mock_settings.setValue.assert_any_call("telnet_ip", host)
        mock_settings.setValue.assert_any_call("telnet_port", str(port))
        telnet_service.status_message_signal.emit.assert_called_once_with(
            f"Connected to {host}:{port}", 
            TelnetService.STATUS_MSG_MEDIUM
        )

    def test_toggle_connection_disconnect(self, telnet_service, mock_session_manager):
        """Test that toggle_connection disconnects when connect=False."""
        # Setup
        host = "localhost"
        port = 23
        connect = False
        
        # Execute
        result = telnet_service.toggle_connection(connect, host, port)
        
        # Assert
        assert result is True
        mock_session_manager.close_all_sessions.assert_called_once()