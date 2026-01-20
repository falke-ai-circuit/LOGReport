"""
Test telnet connection management system integration
"""
import pytest
from unittest.mock import Mock, patch, MagicMock

def test_verify_system_mode_already_in_system(telnet_session):
        """Test verification when already in system mode"""
        # Mock responses: yes response, clear response, then System Commands
        telnet_session.connection.read_very_eager.side_effect = [
            b'',  # Yes response
            b'',  # CTRL+Z clear response
            b'System Commands\r\n123s% '  # First toggle: System Commands
        ]
        
        result = telnet_session.verify_system_mode()
        
        assert result is True
        assert telnet_session.current_mode == 'system'
        assert telnet_session.connection.write.call_count == 3  # yes + CTRL+Z + 1 toggles:
- Connection state gating
- Auto-reconnect with stored config
- Debugger prompt handling
- System mode verification
"""
import pytest
from unittest.mock import Mock, MagicMock, patch, call
import time
import re

from src.commander.session_manager import TelnetSession, SessionConfig, SessionType
from src.commander.services.telnet_service import TelnetService
from src.commander.command_queue import CommandQueue
from src.commander.models import NodeToken


class TestSystemModeVerification:
    """Test system mode verification and toggle functionality"""
    
    @pytest.fixture
    def telnet_session(self):
        config = SessionConfig(
            host="192.168.0.11",
            port=23,
            session_type=SessionType.TELNET
        )
        session = TelnetSession(config)
        session.connection = Mock()
        session.is_connected = True
        return session
    
    def test_verify_system_mode_already_in_system(self, telnet_session):
        """Test verification when already in system mode (System Commands)"""
        # Mock response showing System Commands after yes and toggle
        telnet_session.connection.read_very_eager.side_effect = [
            b'',  # Yes response
            b'System Commands\r\n123s% '  # First toggle shows System Commands
        ]
        
        result = telnet_session.verify_system_mode()
        
        assert result is True
        assert telnet_session.current_mode == 'system'
        assert telnet_session.connection.write.call_count == 2  # yes + 1 toggle
    
    def test_verify_system_mode_switch_from_appl(self, telnet_session):
        """Test switching from Application Commands to System Commands"""
        # Mock responses: yes, then Application Commands, then System Commands
        telnet_session.connection.read_very_eager.side_effect = [
            b'',  # Yes response
            b'Application Commands\r\n123a%a ',  # First toggle: Application Commands
            b'System Commands\r\n123s% '  # Second toggle: System Commands
        ]
        
        result = telnet_session.verify_system_mode()
        
        assert result is True
        assert telnet_session.current_mode == 'system'
        # Should write 3 times: yes + 2 toggles
        assert telnet_session.connection.write.call_count == 3
        # Verify toggle commands were sent
        calls = telnet_session.connection.write.call_args_list
        assert calls[0] == call(b'yes\r\n')
        assert calls[1] == call(b'toggle\r\n')
        assert calls[2] == call(b'toggle\r\n')
    
    def test_verify_system_mode_toggle_fails(self, telnet_session):
        """Test when toggle fails to reach System Commands after max attempts"""
        # Mock responses: always returns Application Commands
        telnet_session.connection.read_very_eager.side_effect = [
            b'',  # Yes response
            b'Application Commands\r\n',  # Toggle 1
            b'Application Commands\r\n',  # Toggle 2
            b'Application Commands\r\n',  # Toggle 3
            b'Application Commands\r\n',  # Toggle 4
            b'Application Commands\r\n'   # Toggle 5 (max)
        ]
        
        result = telnet_session.verify_system_mode()
        
        assert result is False
        assert telnet_session.current_mode == 'appl'
    
    def test_verify_system_mode_not_connected(self, telnet_session):
        """Test verification when not connected"""
        telnet_session.is_connected = False
        
        result = telnet_session.verify_system_mode()
        
        assert result is False
        assert telnet_session.connection.write.call_count == 0


class TestDebuggerPromptHandling:
    """Test debugger session conflict prompt detection and handling"""
    
    @pytest.fixture
    def telnet_session(self):
        config = SessionConfig(
            host="192.168.0.11",
            port=23,
            session_type=SessionType.DEBUGGER
        )
        session = TelnetSession(config)
        session.connection = Mock()
        session.is_connected = True
        return session
    
    def test_handle_debugger_prompt_detected(self, telnet_session):
        """Test detection and automatic 'yes' response to debugger conflict"""
        prompt_text = "someone else is connected to this debugger, do you want to connect?"
        telnet_session.connection.read_very_eager.return_value = b'debugger session started'
        
        result = telnet_session._handle_debugger_prompts(prompt_text)
        
        # Should send 'yes' response
        telnet_session.connection.write.assert_called_once_with(b'yes\r\n')
        # Should return confirmation response
        assert result == 'debugger session started'
    
    def test_handle_debugger_prompt_not_detected(self, telnet_session):
        """Test normal response without debugger prompt"""
        normal_text = "normal command response"
        
        result = telnet_session._handle_debugger_prompts(normal_text)
        
        # Should not write anything
        telnet_session.connection.write.assert_not_called()
        # Should return original response
        assert result == normal_text
    
    def test_handle_debugger_prompt_pattern_variations(self, telnet_session):
        """Test various debugger prompt patterns"""
        prompts = [
            "someone else is connected, want to connect?",
            "ALREADY CONNECTED. Do you want to connect?",
            "Debugger session active. Connect?"
        ]
        telnet_session.connection.read_very_eager.return_value = b'ok'
        
        for prompt in prompts:
            result = telnet_session._handle_debugger_prompts(prompt)
            assert telnet_session.connection.write.called


class TestAutoReconnect:
    """Test automatic reconnection functionality"""
    
    @pytest.fixture
    def session_manager(self):
        from src.commander.session_manager import SessionManager
        return SessionManager()
    
    @pytest.fixture
    def telnet_service(self, session_manager):
        return TelnetService(session_manager)
    
    def test_ensure_connection_with_active_session(self, telnet_service):
        """Test _ensure_connection with active connected session"""
        mock_session = Mock()
        mock_session.is_connected = True
        telnet_service.telnet_session = mock_session
        
        result = telnet_service._ensure_connection()
        
        assert result is True
    
    def test_ensure_connection_auto_reconnect(self, telnet_service):
        """Test auto-reconnect when session is disconnected"""
        telnet_service.last_ip_address = "192.168.0.11"
        telnet_service.last_port = 23
        telnet_service.telnet_session = None
        
        with patch.object(telnet_service, 'connect', return_value=True) as mock_connect:
            result = telnet_service._ensure_connection()
            
            assert result is True
            mock_connect.assert_called_once_with("192.168.0.11", 23)
    
    def test_ensure_connection_no_stored_params(self, telnet_service):
        """Test when no stored connection parameters available"""
        telnet_service.last_ip_address = None
        telnet_service.last_port = None
        telnet_service.telnet_session = None
        
        result = telnet_service._ensure_connection()
        
        assert result is False
    
    def test_execute_command_with_connection_check(self, telnet_service):
        """Test execute_command performs connection check before queueing"""
        telnet_service.telnet_session = None
        telnet_service.last_ip_address = None
        
        # Should fail connection check and abort
        result = telnet_service.execute_command("test command", automatic=False)
        
        assert result == ""  # Empty string indicates command was not executed


class TestConnectionStateGating:
    """Test connection state gating in command queue"""
    
    @pytest.fixture
    def command_queue(self):
        mock_session_manager = Mock()
        return CommandQueue(session_manager=mock_session_manager)
    
    @pytest.fixture
    def mock_token(self):
        return NodeToken(
            token_id="162",
            token_type="FBC",
            name="AP01m",
            ip_address="192.168.0.11",
            port=23
        )
    
    def test_add_command_with_disconnected_client_warns(self, command_queue, mock_token):
        """Test adding command with disconnected telnet client logs warning"""
        mock_client = Mock()
        mock_client.is_connected = False
        
        with patch('logging.warning') as mock_warning:
            command_queue.add_command("test command", mock_token, mock_client)
            
            # Should warn about disconnected client
            assert mock_warning.called
            assert "not connected" in mock_warning.call_args[0][0].lower()
    
    def test_add_command_with_connected_client(self, command_queue, mock_token):
        """Test adding command with connected telnet client"""
        mock_client = Mock()
        mock_client.is_connected = True
        
        command_queue.add_command("test command", mock_token, mock_client)
        
        # Command should be added
        assert len(command_queue.queue) == 1
        assert command_queue.queue[0].command == "test command"


class TestIntegrationFlow:
    """Test full integration flow from command to execution"""
    
    def test_full_connection_management_flow(self):
        """Test complete flow: connect → verify mode → handle prompts → execute"""
        # This test would require more extensive mocking and is better suited for manual testing
        # Documenting the expected flow:
        # 1. User calls TelnetService.connect(ip, port)
        # 2. TelnetSession establishes connection
        # 3. verify_system_mode() called automatically
        # 4. If %a detected, toggle sent to switch to %s
        # 5. User executes command via TelnetService.execute_command()
        # 6. _ensure_connection() checks is_connected
        # 7. If disconnected, auto-reconnect attempted
        # 8. Command sent via TelnetSession.send_command()
        # 9. _handle_debugger_prompts() checks response for conflicts
        # 10. If prompt detected, "yes" sent automatically
        # 11. Processed response returned
        pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
