import pytest
from unittest.mock import MagicMock, patch
from src.commander.services.sequential_command_processor import SequentialCommandProcessor
from src.commander.services import fbc_command_service, rpc_command_service
from src.commander.services.session_manager import SessionManager

@pytest.fixture
def mock_fbc_service():
    return MagicMock(spec=fbc_command_service.FBCCommandService)

@pytest.fixture
def mock_rpc_service():
    return MagicMock(spec=rpc_command_service.RPCCommandService)

@pytest.fixture
def mock_session_manager():
    return MagicMock(spec=SessionManager)

@pytest.fixture
def command_processor(mock_fbc_service, mock_rpc_service, mock_session_manager):
    return SequentialCommandProcessor(
        command_queue=MagicMock(),
        fbc_service=mock_fbc_service,
        rpc_service=mock_rpc_service,
        session_manager=mock_session_manager
    )
def test_fbc_token_162_sequence(command_processor, mock_fbc_service):
    """Test processing of FBC token 162 sequence"""
    # Setup test data
    tokens = ["162"]
    node_name = "AP01m"
    expected_command = "print from fbc io structure 1620000"
    
    # Mock telnet client and session manager
    mock_telnet = MagicMock()
    command_processor.session_manager.get_telnet_client.return_value = mock_telnet
    
    # Execute processing
    command_processor.process_fbc_commands(node_name, tokens)
    
    # Verify command execution
    mock_fbc_service.generate_fbc_command.assert_called_once_with(
        token="162",
        node_name=node_name
    )
    mock_telnet.write.assert_called_once_with(expected_command.encode('ascii') + b"\r\n")
    
    # Verify resource cleanup
    command_processor.session_manager.release_telnet_client.assert_called_once_with(node_name, mock_telnet)
@pytest.mark.parametrize("token_count", [1, 3, 5])
def test_command_timing(command_processor, mock_fbc_service, token_count):
    """Validate 100ms delay between command executions"""
    # Setup test data
    tokens = [str(162 + i) for i in range(token_count)]
    node_name = "AP01m"
    
    # Mock telnet client and time functions
    mock_telnet = MagicMock()
    command_processor.session_manager.get_telnet_client.return_value = mock_telnet
    
    with patch('time.time') as mock_time, \
         patch('time.sleep') as mock_sleep:
        
        # Simulate time progression
        mock_time.side_effect = [i * 0.1 for i in range(20)]
        
        # Execute processing
        command_processor.process_fbc_commands(node_name, tokens)
        
        # Verify sleep calls between commands
        assert mock_sleep.call_count == token_count - 1
        for call in mock_sleep.call_args_list:
            assert call[0][0] == pytest.approx(0.1, abs=0.01)
def test_empty_queue_handling(command_processor, mock_fbc_service):
    """Test processor behavior with empty token list"""
    # Execute processing with empty tokens
    command_processor.process_fbc_commands("AP01m", [])
    
    # Verify no commands were executed
    mock_fbc_service.generate_fbc_command.assert_not_called()
    command_processor.session_manager.get_telnet_client.assert_not_called()

def test_mixed_command_types(command_processor, mock_fbc_service, mock_rpc_service):
    """Test handling of mixed FBC/RPC commands"""
    # Setup test data
    fbc_tokens = ["162", "163"]
    rpc_tokens = ["360", "361"]
    node_name = "AP01m"
    
    # Mock telnet client
    mock_telnet = MagicMock()
    command_processor.session_manager.get_telnet_client.return_value = mock_telnet
    
    # Execute mixed processing
    command_processor.process_fbc_commands(node_name, fbc_tokens)
    command_processor.process_rpc_commands(node_name, rpc_tokens, action="print")
    
    # Verify FBC commands
    assert mock_fbc_service.generate_fbc_command.call_count == len(fbc_tokens)
    for token in fbc_tokens:
        mock_fbc_service.generate_fbc_command.assert_any_call(
            token=token,
            node_name=node_name
        )
    
    # Verify RPC commands
    assert mock_rpc_service.generate_rpc_command.call_count == len(rpc_tokens)
    for token in rpc_tokens:
        mock_rpc_service.generate_rpc_command.assert_any_call(
            token=token,
            node_name=node_name,
            action="print"
        )