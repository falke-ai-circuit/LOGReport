import pytest
from unittest.mock import MagicMock, patch
from src.commander.services.telnet_service import TelnetService
from src.commander.telnet_client import TelnetClient
from src.commander.models import SessionConfig, NodeToken, Node

@pytest.fixture
def mock_session_manager():
    """Fixture for a mocked SessionManager."""
    return MagicMock()

@pytest.fixture
def mock_telnet_client():
    """Fixture for a mocked TelnetClient."""
    return MagicMock(spec=TelnetClient)

@pytest.fixture
def telnet_service(mock_session_manager):
    """Fixture for TelnetService with mocked dependencies."""
    service = TelnetService(mock_session_manager)
    service.status_message_signal = MagicMock()
    service.command_finished_signal = MagicMock()
    service.update_connection_status_signal = MagicMock()
    
    mock_telnet_session = MagicMock()
    mock_telnet_session.is_connected = True
    mock_session_manager.create_session.return_value = mock_telnet_session
    
    return service

class TestTelnetConnection:
    """Tests for Telnet connection functionality."""

    def test_connect_success(self, telnet_service, mock_telnet_client, mock_session_manager):
        """Verify successful Telnet connection."""
        config = SessionConfig(host="localhost", port=23)
        telnet_service.connect(config.host, config.port)

        mock_telnet_client.connect.assert_called_once_with(config.host, config.port)
        mock_session_manager.create_session.assert_called_once()
        telnet_service.status_message_signal.emit.assert_called_with("Connected to localhost:23", TelnetService.STATUS_MSG_MEDIUM)

    def test_connect_failure(self, telnet_service, mock_telnet_client, mock_session_manager):
        """Verify Telnet connection failure handling."""
        config = SessionConfig(host="badhost", port=23)
        mock_telnet_client.connect.side_effect = Exception("Connection error")

        telnet_service.connect(config.host, config.port)

        mock_telnet_client.connect.assert_called_once_with(config.host, config.port)
        mock_session_manager.create_session.assert_called_once()
        telnet_service.status_message_signal.emit.assert_called_with("Connection error: Connection error", TelnetService.STATUS_MSG_LONG)

    def test_disconnect_success(self, telnet_service, mock_telnet_client, mock_session_manager):
        """Verify successful Telnet disconnection."""
        telnet_service.disconnect()

        mock_session_manager.close_all_sessions.assert_called_once()
        # No specific assertion for status message on disconnect success in current implementation

    def test_disconnect_failure(self, telnet_service, mock_telnet_client, mock_session_manager):
        """Verify Telnet disconnection failure handling."""
        mock_telnet_client.disconnect.side_effect = Exception("Disconnection error")

        telnet_service.disconnect()

        mock_session_manager.close_all_sessions.assert_called_once()
        # No specific assertion for status message on disconnect failure in current implementation

    def test_toggle_connection_connects_when_disconnected(self, telnet_service, mock_telnet_client, mock_session_manager):
        """Verify toggle_connection connects when no active session."""
        mock_session_manager.is_session_active.return_value = False
        config = SessionConfig(host="localhost", port=23)
        mock_session_manager.get_active_session_config.return_value = config

        telnet_service.toggle_connection(True, config.host, config.port)

        mock_telnet_client.connect.assert_called_once_with(config.host, config.port)
        mock_session_manager.start_session.assert_called_once()

    def test_toggle_connection_disconnects_when_connected(self, telnet_service, mock_telnet_client, mock_session_manager):
        """Verify toggle_connection disconnects when an active session exists."""
        mock_session_manager.is_session_active.return_value = True
        config = SessionConfig(host="localhost", port=23)
        telnet_service.toggle_connection(False, config.host, config.port)

        mock_telnet_client.disconnect.assert_called_once()
        mock_session_manager.stop_session.assert_called_once()

    def test_execute_command_success(self, telnet_service, mock_telnet_client, mock_session_manager):
        """Verify command execution success."""
        mock_telnet_client.send_command.return_value = "Command output"
        telnet_service.execute_command("test command")

        mock_telnet_client.send_command.assert_called_once_with("test command")
        mock_session_manager.append_to_log.assert_called_once_with("Command output")

    def test_execute_command_failure(self, telnet_service, mock_telnet_client, mock_session_manager):
        """Verify command execution failure handling."""
        mock_telnet_client.send_command.side_effect = Exception("Command execution error")
        telnet_service.execute_command("test command")

        mock_telnet_client.send_command.assert_called_once_with("test command")
        mock_session_manager.append_to_log.assert_not_called()
        mock_session_manager.update_status.assert_called_with("Command execution failed: Command execution error", TelnetService.STATUS_MSG_LONG)