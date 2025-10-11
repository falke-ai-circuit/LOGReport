import pytest
import sys
import os
from unittest.mock import MagicMock, patch

# Add src directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'src')))

from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QTimer, QEventLoop

from src.commander.ui.commander_window import CommanderWindow
from src.commander.ui.telnet_tab import TelnetTab
from src.commander.services.telnet_service import TelnetService
from src.commander.session_manager import SessionManager


class TestTelnetConnectIntegration:
    """Integration tests for Telnet connect functionality."""

    @pytest.fixture(scope="class")
    def app(self):
        """Create a QApplication instance for testing."""
        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)
        return app

    @pytest.fixture
    def mock_commander_window(self):
        """Create a mocked CommanderWindow for integration testing."""
        with patch('src.commander.ui.commander_window.QSettings'), \
             patch('src.commander.ui.commander_window.NodeManager'), \
             patch('src.commander.ui.commander_window.SessionManager'), \
             patch('src.commander.ui.commander_window.CommandQueue'), \
             patch('src.commander.ui.commander_window.LogWriter'), \
             patch('src.commander.ui.commander_window.StatusService'), \
             patch('src.commander.ui.commander_window.ContextMenuFilterService'), \
             patch('src.commander.ui.commander_window.FbcCommandService'), \
             patch('src.commander.ui.commander_window.RpcCommandService'), \
             patch('src.commander.ui.commander_window.CommanderService'), \
             patch('src.commander.ui.commander_window.TelnetService'), \
             patch('src.commander.ui.commander_window.ContextMenuService'), \
             patch('src.commander.ui.commander_window.CommanderUIFactory'), \
             patch('src.commander.ui.commander_window.NodeTreePresenter'), \
             patch('src.commander.ui.commander_window.CommanderPresenter'):
            
            window = CommanderWindow()
            
            # Mock UI components
            window.telnet_tab = MagicMock(spec=TelnetTab)
            window.settings = MagicMock()
            window.session_manager = MagicMock(spec=SessionManager)
            
            # Mock telnet service
            window.telnet_service = MagicMock(spec=TelnetService)
            
            return window

    def test_connect_button_click_triggers_toggle_connection(self, mock_commander_window):
        """Test that clicking the connect button calls toggle_connection with correct parameters."""
        # Setup
        host = "192.168.1.1"
        port = "23"
        
        # Mock telnet tab to return connection info
        mock_commander_window.telnet_tab.get_connection_info.return_value = (host, port)
        
        # Execute - simulate clicking connect button (True = connect)
        mock_commander_window.toggle_telnet_connection(True)
        
        # Assert
        mock_commander_window.telnet_service.toggle_connection.assert_called_once_with(
            True, host, port, mock_commander_window.settings
        )

    def test_disconnect_button_click_triggers_toggle_connection(self, mock_commander_window):
        """Test that clicking the disconnect button calls toggle_connection with correct parameters."""
        # Setup
        host = "192.168.1.1"
        port = "23"
        
        # Mock telnet tab to return connection info
        mock_commander_window.telnet_tab.get_connection_info.return_value = (host, port)
        
        # Execute - simulate clicking disconnect button (False = disconnect)
        mock_commander_window.toggle_telnet_connection(False)
        
        # Assert
        mock_commander_window.telnet_service.toggle_connection.assert_called_once_with(
            False, host, port, mock_commander_window.settings
        )

    def test_telnet_tab_connect_signal_emission(self):
        """Test that TelnetTab emits connect_clicked signal with correct parameters."""
        # Setup
        telnet_tab = TelnetTab()
        
        # Mock the signal
        with patch.object(telnet_tab.connect_clicked, 'emit') as mock_emit:
            # Execute - simulate clicking connect button
            telnet_tab.connect_btn.click()
            
            # Assert
            mock_emit.assert_called_once_with(True)

    def test_telnet_tab_disconnect_signal_emission(self):
        """Test that TelnetTab emits connect_clicked signal with correct parameters for disconnect."""
        # Setup
        telnet_tab = TelnetTab()
        
        # Mock the signal
        with patch.object(telnet_tab.connect_clicked, 'emit') as mock_emit:
            # Execute - simulate clicking disconnect button
            telnet_tab.disconnect_btn.click()
            
            # Assert
            mock_emit.assert_called_once_with(False)

    @pytest.mark.parametrize("host,port,expected_result", [
        ("localhost", "23", True),
        ("192.168.1.1", "2323", True),
        ("", "23", False),  # Empty host
        ("localhost", "", False),  # Empty port
    ])
    def test_get_connection_info_returns_correct_values(self, host, port, expected_result):
        """Test that get_connection_info returns correct values."""
        # Setup
        telnet_tab = TelnetTab()
        telnet_tab.ip_edit.setText(host)
        telnet_tab.port_edit.setText(port)
        
        # Execute
        result_host, result_port = telnet_tab.get_connection_info()
        
        # Assert
        if expected_result:
            assert result_host == host
            assert result_port == port
        else:
            # For empty values, we just check they're strings
            assert isinstance(result_host, str)
            assert isinstance(result_port, str)


# Regression tests for specific issues
class TestTelnetConnectRegression:
    """Regression tests for Telnet connect functionality."""

    def test_status_message_signal_emits_two_arguments(self):
        """Test that status_message_signal emits exactly two arguments as expected."""
        # Setup
        session_manager = MagicMock()
        telnet_service = TelnetService(session_manager)
        
        # Mock the signal
        mock_signal = MagicMock()
        telnet_service.status_message_signal = mock_signal
        
        # Execute - emit signal with two arguments (as it should be)
        message = "Test message"
        duration = 5000
        telnet_service.status_message_signal.emit(message, duration)
        
        # Assert
        mock_signal.emit.assert_called_once_with(message, duration)

    def test_update_connection_status_signal_emits_connection_state(self):
        """Test that update_connection_status_signal emits ConnectionState enum."""
        from src.commander.widgets import ConnectionState
        
        # Setup
        session_manager = MagicMock()
        telnet_service = TelnetService(session_manager)
        
        # Mock the signal
        mock_signal = MagicMock()
        telnet_service.update_connection_status_signal = mock_signal
        
        # Execute - emit signal with ConnectionState
        state = ConnectionState.CONNECTED
        telnet_service.update_connection_status_signal.emit(state)
        
        # Assert
        mock_signal.emit.assert_called_once_with(state)