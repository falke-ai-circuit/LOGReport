"""
Test debugger connection management for FBC/RPC/LOG commands.
Ensures these commands always use the debugger IP from Telnet tab, not node IPs.
"""
import pytest
from unittest.mock import Mock, MagicMock, patch

from src.commander.services.telnet_service import TelnetService
from src.commander.services.fbc_command_service import FbcCommandService
from src.commander.services.rpc_command_service import RpcCommandService
from src.commander.session_manager import SessionManager, TelnetSession, SessionConfig, SessionType
from src.commander.node_manager import NodeManager
from src.commander.command_queue import CommandQueue
from src.commander.models import NodeToken


class TestDebuggerConnectionManagement:
    """Test that FBC/RPC commands use debugger IP instead of node IP"""
    
    @pytest.fixture
    def session_manager(self):
        return SessionManager()
    
    @pytest.fixture
    def telnet_session(self):
        """Create a TelnetSession instance for testing"""
        config = SessionConfig(
            host="192.168.0.100",
            port=23,
            session_type=SessionType.TELNET,
            timeout=5,
            username="",
            password=""
        )
        return TelnetSession(config)
    
    @pytest.fixture
    def telnet_service(self, session_manager):
        service = TelnetService(session_manager)
        # Simulate debugger IP set from Telnet tab
        service.debugger_ip_address = "192.168.0.100"
        service.debugger_port = 23
        return service
    
    @pytest.fixture
    def node_manager(self):
        manager = NodeManager()
        # Add a test node with different IP than debugger
        from src.commander.models import Node
        node = Node(name="TestNode", ip_address="192.168.0.50", status="online")
        manager.nodes["TestNode"] = node
        return manager
    
    @pytest.fixture
    def command_queue(self, session_manager):
        return CommandQueue(session_manager=session_manager)
    
    @pytest.fixture
    def fbc_service(self, node_manager, command_queue):
        service = FbcCommandService(node_manager, command_queue)
        return service
    
    @pytest.fixture
    def rpc_service(self, node_manager, command_queue):
        service = RpcCommandService(node_manager, command_queue)
        return service
    
    def test_telnet_service_stores_debugger_ip(self, telnet_service):
        """Test that TelnetService correctly stores debugger IP from Telnet tab"""
        assert telnet_service.debugger_ip_address == "192.168.0.100"
        assert telnet_service.debugger_port == 23
    
    def test_telnet_service_updates_debugger_ip_on_connect(self, telnet_service):
        """Test that toggle_connection updates debugger IP"""
        with patch.object(telnet_service, 'connect', return_value=True):
            telnet_service.toggle_connection(True, "192.168.0.200", 2323)
            
            assert telnet_service.debugger_ip_address == "192.168.0.200"
            assert telnet_service.debugger_port == 2323
    
    def test_ensure_debugger_connection_with_active_session(self, telnet_service):
        """Test _ensure_debugger_connection with active session"""
        mock_session = Mock()
        mock_session.is_connected = True
        telnet_service.active_telnet_client = mock_session
        
        result = telnet_service._ensure_debugger_connection()
        
        assert result is True
        assert telnet_service.telnet_session == mock_session
    
    def test_ensure_debugger_connection_auto_reconnect(self, telnet_service):
        """Test _ensure_debugger_connection attempts auto-reconnect to debugger IP"""
        telnet_service.telnet_session = None
        telnet_service.debugger_ip_address = "192.168.0.100"
        telnet_service.debugger_port = 23
        
        with patch.object(telnet_service, 'connect', return_value=True) as mock_connect:
            result = telnet_service._ensure_debugger_connection()
            
            assert result is True
            # Should connect to debugger IP, not any other IP
            mock_connect.assert_called_once_with("192.168.0.100", 23)
    
    def test_ensure_debugger_connection_no_debugger_ip(self, telnet_service):
        """Test _ensure_debugger_connection fails when no debugger IP configured"""
        telnet_service.telnet_session = None
        telnet_service.debugger_ip_address = None
        telnet_service.debugger_port = None
        
        result = telnet_service._ensure_debugger_connection()
        
        assert result is False
    
    def test_fbc_service_uses_debugger_connection(self, fbc_service, telnet_service, node_manager):
        """Test that FBC service ensures debugger connection before queueing"""
        fbc_service.set_telnet_service(telnet_service)
        
        # Mock the debugger connection check
        with patch.object(telnet_service, '_ensure_debugger_connection', return_value=True) as mock_ensure:
            mock_session = Mock()
            mock_session.is_connected = True
            telnet_service.telnet_session = mock_session
            
            # Mock command queue to prevent actual execution
            with patch.object(fbc_service.command_queue, 'add_command') as mock_add:
                fbc_service.queue_fieldbus_command("TestNode", "162")
                
                # Should have called _ensure_debugger_connection
                mock_ensure.assert_called_once()
                # Should have queued command with debugger session
                mock_add.assert_called_once()
                call_args = mock_add.call_args
                telnet_client_arg = call_args[0][2]  # Third positional argument
                assert telnet_client_arg == mock_session
    
    def test_fbc_service_fails_without_debugger_connection(self, fbc_service, telnet_service):
        """Test that FBC service aborts if debugger connection fails"""
        fbc_service.set_telnet_service(telnet_service)
        telnet_service.debugger_ip_address = None  # No debugger IP
        
        with patch.object(fbc_service.command_queue, 'add_command') as mock_add:
            fbc_service.queue_fieldbus_command("TestNode", "162")
            
            # Should NOT queue command if connection failed
            mock_add.assert_not_called()
    
    def test_rpc_service_uses_debugger_connection(self, rpc_service, telnet_service, node_manager):
        """Test that RPC service ensures debugger connection before queueing"""
        rpc_service.set_telnet_service(telnet_service)
        
        # Mock the debugger connection check
        with patch.object(telnet_service, '_ensure_debugger_connection', return_value=True) as mock_ensure:
            mock_session = Mock()
            mock_session.is_connected = True
            telnet_service.telnet_session = mock_session
            
            # Mock command queue to prevent actual execution
            with patch.object(rpc_service.command_queue, 'add_command') as mock_add:
                rpc_service.queue_rpc_command("TestNode", "162", "print")
                
                # Should have called _ensure_debugger_connection
                mock_ensure.assert_called_once()
                # Should have queued command with debugger session
                mock_add.assert_called_once()
                call_args = mock_add.call_args
                telnet_client_arg = call_args[0][2]  # Third positional argument
                assert telnet_client_arg == mock_session
    
    def test_rpc_service_fails_without_debugger_connection(self, rpc_service, telnet_service):
        """Test that RPC service aborts if debugger connection fails"""
        rpc_service.set_telnet_service(telnet_service)
        telnet_service.debugger_ip_address = None  # No debugger IP
        
        with patch.object(rpc_service.command_queue, 'add_command') as mock_add:
            rpc_service.queue_rpc_command("TestNode", "162", "print")
            
            # Should NOT queue command if connection failed
            mock_add.assert_not_called()
    
    def test_fbc_service_uses_provided_telnet_client(self, fbc_service, telnet_service):
        """Test that FBC service uses provided telnet_client without checking debugger"""
        fbc_service.set_telnet_service(telnet_service)
        
        mock_client = Mock()
        mock_client.is_connected = True
        
        with patch.object(telnet_service, '_ensure_debugger_connection') as mock_ensure:
            with patch.object(fbc_service.command_queue, 'add_command'):
                fbc_service.queue_fieldbus_command("TestNode", "162", telnet_client=mock_client)
                
                # Should NOT call _ensure_debugger_connection when telnet_client is provided
                mock_ensure.assert_not_called()
    
    def test_node_ip_not_used_for_fbc_commands(self, fbc_service, telnet_service, node_manager):
        """Test that node IP (192.168.0.50) is NOT used, only debugger IP (192.168.0.100)"""
        fbc_service.set_telnet_service(telnet_service)
        telnet_service.debugger_ip_address = "192.168.0.100"
        
        with patch.object(telnet_service, 'connect') as mock_connect:
            mock_connect.return_value = True
            telnet_service.telnet_session = None
            
            # Try to queue FBC command for node with IP 192.168.0.50
            with patch.object(fbc_service.command_queue, 'add_command'):
                fbc_service.queue_fieldbus_command("TestNode", "162")
            
            # Should have connected to debugger IP (192.168.0.100), NOT node IP (192.168.0.50)
            if mock_connect.called:
                call_args = mock_connect.call_args[0]
                assert call_args[0] == "192.168.0.100", f"Expected debugger IP 192.168.0.100, got {call_args[0]}"
                assert call_args[0] != "192.168.0.50", "Should NOT use node IP"


    def test_verify_system_mode_initialization_sequence(self, telnet_session):
        """Test complete debugger initialization: yes→CTRL+Z→systemmode"""
        # Setup mock connection
        mock_connection = Mock()
        mock_connection.read_very_eager = Mock()
        
        # Mock responses for each step
        mock_connection.read_very_eager.side_effect = [
            b'[Connected]\r\n',  # yes response
            b'\x1a\r\n'  # CTRL+Z clear response
        ]
        
        telnet_session.connection = mock_connection
        telnet_session.is_connected = True
        
        result = telnet_session.verify_system_mode()
        
        assert result is True
        assert telnet_session.current_mode == 'system'
        
        # Verify the 3-step sequence was executed
        calls = mock_connection.write.call_args_list
        assert len(calls) >= 3
        assert calls[0][0][0] == b'yes\r\n'  # Step 1: yes
        assert calls[1][0][0] == b'\x1a'  # Step 2: CTRL+Z
        assert calls[2][0][0] == b'systemmode\r\n'  # Step 3: systemmode
    
    def test_verify_system_mode_ctrl_z_sent(self, telnet_session):
        """Test that CTRL+Z (0x1a) is sent after yes"""
        mock_connection = Mock()
        mock_connection.read_very_eager = Mock(side_effect=[
            b'yes response',
            b'clear response'
        ])
        
        telnet_session.connection = mock_connection
        telnet_session.is_connected = True
        
        telnet_session.verify_system_mode()
        
        # Find CTRL+Z in write calls
        writes = [call[0][0] for call in mock_connection.write.call_args_list]
        assert b'\x1a' in writes, "CTRL+Z should be sent"
        
        # Verify order: yes, then CTRL+Z, then systemmode
        yes_index = writes.index(b'yes\r\n')
        ctrl_z_index = writes.index(b'\x1a')
        systemmode_index = writes.index(b'systemmode\r\n')
        
        assert yes_index < ctrl_z_index < systemmode_index, "Order should be: yes→CTRL+Z→systemmode"
    
    def test_verify_system_mode_uses_systemmode_command(self, telnet_session):
        """Test that systemmode command is used to guarantee system mode"""
        mock_connection = Mock()
        mock_connection.read_very_eager = Mock(side_effect=[
            b'yes response',
            b'clear response'
        ])
        
        telnet_session.connection = mock_connection
        telnet_session.is_connected = True
        
        result = telnet_session.verify_system_mode()
        
        assert result is True
        assert telnet_session.current_mode == 'system'
        
        # Should have sent systemmode command exactly once
        systemmode_calls = [call for call in mock_connection.write.call_args_list if call[0][0] == b'systemmode\r\n']
        assert len(systemmode_calls) == 1
    
    def test_verify_system_mode_no_toggle_loop(self, telnet_session):
        """Test that systemmode command is used instead of toggle loop"""
        mock_connection = Mock()
        mock_connection.read_very_eager = Mock(side_effect=[
            b'yes response',
            b'clear response'
        ])
        
        telnet_session.connection = mock_connection
        telnet_session.is_connected = True
        
        result = telnet_session.verify_system_mode()
        
        # Should succeed
        assert result is True
        
        # Should NOT have sent any toggle commands
        toggle_calls = [call for call in mock_connection.write.call_args_list if call[0][0] == b'toggle\r\n']
        assert len(toggle_calls) == 0, "Should not use toggle command anymore"
    
    def test_debugger_connection_retry_success_first_attempt(self, telnet_service):
        """Test that connection succeeds on first attempt without retry"""
        telnet_service.debugger_ip_address = "192.168.0.100"
        telnet_service.debugger_port = 23
        telnet_service.telnet_session = None
        
        with patch.object(telnet_service, 'connect', return_value=True) as mock_connect:
            result = telnet_service._ensure_debugger_connection()
            
            assert result is True
            # Should only call connect once (no retry needed)
            assert mock_connect.call_count == 1
            mock_connect.assert_called_with("192.168.0.100", 23)
    
    def test_debugger_connection_retry_success_second_attempt(self, telnet_service):
        """Test that connection retries and succeeds on second attempt"""
        telnet_service.debugger_ip_address = "192.168.0.100"
        telnet_service.debugger_port = 23
        telnet_service.telnet_session = None
        
        # Mock time.sleep to avoid actual 15s delay
        with patch('time.sleep') as mock_sleep:
            # First attempt fails, second succeeds
            with patch.object(telnet_service, 'connect', side_effect=[False, True]) as mock_connect:
                result = telnet_service._ensure_debugger_connection()
                
                assert result is True
                # Should have called connect twice
                assert mock_connect.call_count == 2
                # Should have slept 10 seconds between attempts
                mock_sleep.assert_called_once_with(10)
    
    def test_debugger_connection_retry_fails_both_attempts(self, telnet_service):
        """Test that connection fails after 2 attempts"""
        telnet_service.debugger_ip_address = "192.168.0.100"
        telnet_service.debugger_port = 23
        telnet_service.telnet_session = None
        
        # Mock time.sleep to avoid actual 15s delay
        with patch('time.sleep') as mock_sleep:
            # Both attempts fail
            with patch.object(telnet_service, 'connect', return_value=False) as mock_connect:
                result = telnet_service._ensure_debugger_connection()
                
                assert result is False
                # Should have called connect exactly 2 times
                assert mock_connect.call_count == 2
                # Should have slept once (between attempt 1 and 2)
                mock_sleep.assert_called_once_with(10)
    
    def test_debugger_connection_retry_delay_is_10_seconds(self, telnet_service):
        """Test that retry delay is exactly 10 seconds"""
        telnet_service.debugger_ip_address = "192.168.0.100"
        telnet_service.debugger_port = 23
        telnet_service.telnet_session = None
        
        with patch('time.sleep') as mock_sleep:
            with patch.object(telnet_service, 'connect', side_effect=[False, True]):
                telnet_service._ensure_debugger_connection()
                
                # Verify delay is 10 seconds
                mock_sleep.assert_called_once_with(10)

    def test_verify_system_mode_failure_triggers_disconnect_and_retry(self, telnet_service):
        """Test that verify_system_mode failure causes disconnect and retry"""
        telnet_service.debugger_ip_address = "192.168.0.100"
        telnet_service.debugger_port = 23
        telnet_service.telnet_session = None
        
        # Create mock session that connects but fails verification on first attempt
        mock_session_fail = Mock()
        mock_session_fail.is_connected = True
        mock_session_fail.verify_system_mode = Mock(return_value=False)  # Verification fails
        
        # Create mock session that connects and verifies successfully on second attempt
        mock_session_success = Mock()
        mock_session_success.is_connected = True
        mock_session_success.verify_system_mode = Mock(return_value=True)  # Verification succeeds
        
        with patch('time.sleep') as mock_sleep:
            # First create_session returns failing session, second returns successful session
            with patch.object(telnet_service.session_manager, 'create_session', side_effect=[mock_session_fail, mock_session_success]):
                with patch.object(telnet_service.session_manager, 'close_session') as mock_close:
                    result = telnet_service._ensure_debugger_connection()
                    
                    # Should succeed on second attempt
                    assert result is True
                    # Should have closed the failed session
                    mock_close.assert_called_once_with(mock_session_fail)
                    # Should have slept once (10 seconds between attempts)
                    mock_sleep.assert_called_once_with(10)
                    # Verification should have been called twice (once per attempt)
                    assert mock_session_fail.verify_system_mode.call_count == 1
                    assert mock_session_success.verify_system_mode.call_count == 1

    def test_manual_connection_retry_on_verification_failure(self, telnet_service):
        """Test that manual connection (from GUI) retries on verify_system_mode failure"""
        # Create mock session that connects but fails verification on first attempt
        mock_session_fail = Mock()
        mock_session_fail.is_connected = True
        mock_session_fail.verify_system_mode = Mock(return_value=False)  # Verification fails
        
        # Create mock session that connects and verifies successfully on second attempt
        mock_session_success = Mock()
        mock_session_success.is_connected = True
        mock_session_success.verify_system_mode = Mock(return_value=True)  # Verification succeeds
        
        with patch('time.sleep') as mock_sleep:
            # First create_session returns failing session, second returns successful session
            with patch.object(telnet_service.session_manager, 'create_session', side_effect=[mock_session_fail, mock_session_success]):
                with patch.object(telnet_service.session_manager, 'close_session') as mock_close:
                    # Call toggle_connection (manual connection from GUI)
                    result = telnet_service.toggle_connection(True, "192.168.0.100", 23, settings=None)
                    
                    # Should succeed on second attempt
                    assert result is True
                    # Should have closed the failed session
                    mock_close.assert_called_once_with(mock_session_fail)
                    # Should have slept once (10 seconds between attempts)
                    mock_sleep.assert_called_once_with(10)
                    # Verification should have been called twice (once per attempt)
                    assert mock_session_fail.verify_system_mode.call_count == 1
                    assert mock_session_success.verify_system_mode.call_count == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
