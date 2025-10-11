"""
Test Pause/Resume/Cancel functionality for sequential command processing.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch, call
from PyQt5.QtCore import QObject, pyqtSignal
from src.commander.services.sequential_command_processor import SequentialCommandProcessor, ExecutionState
from src.commander.models import NodeToken


@pytest.fixture
def mock_services():
    """Create mock services for SequentialCommandProcessor."""
    command_queue = Mock()
    command_queue.set_auto_cleanup = Mock()
    command_queue.command_completed = MagicMock()
    command_queue.progress_updated = MagicMock()
    command_queue.add_command = Mock()
    
    fbc_service = Mock()
    fbc_service.node_manager = Mock()
    fbc_service.node_manager.get_node = Mock(return_value=None)
    
    rpc_service = Mock()
    rpc_service.node_manager = Mock()
    rpc_service.node_manager.get_node = Mock(return_value=None)
    
    session_manager = Mock()
    
    logging_service = Mock()
    logging_service.open_log_for_token = Mock(return_value="/tmp/test.log")
    logging_service.log = Mock()
    logging_service.start_batch_logging = Mock()
    logging_service.end_batch_logging = Mock()
    
    return {
        'command_queue': command_queue,
        'fbc_service': fbc_service,
        'rpc_service': rpc_service,
        'session_manager': session_manager,
        'logging_service': logging_service
    }


@pytest.fixture
def processor(mock_services):
    """Create SequentialCommandProcessor instance with mock services."""
    return SequentialCommandProcessor(
        command_queue=mock_services['command_queue'],
        fbc_service=mock_services['fbc_service'],
        rpc_service=mock_services['rpc_service'],
        session_manager=mock_services['session_manager'],
        logging_service=mock_services['logging_service'],
        parent=None
    )


@pytest.fixture
def sample_tokens():
    """Create sample tokens for testing."""
    return [
        NodeToken(token_id="162", token_type="FBC", name="AP01m", ip_address="192.168.0.11", node_ip="192.168.0.11"),
        NodeToken(token_id="163", token_type="RPC", name="AP01m", ip_address="192.168.0.11", node_ip="192.168.0.11"),
        NodeToken(token_id="164", token_type="FBC", name="AP01m", ip_address="192.168.0.11", node_ip="192.168.0.11"),
    ]


class TestExecutionState:
    """Test ExecutionState enum."""
    
    def test_execution_state_values(self):
        """Test that ExecutionState has correct values."""
        assert ExecutionState.IDLE.value == "idle"
        assert ExecutionState.RUNNING.value == "running"
        assert ExecutionState.PAUSED.value == "paused"
        assert ExecutionState.CANCELLED.value == "cancelled"


class TestStateTransitions:
    """Test state machine transitions."""
    
    def test_initial_state_is_idle(self, processor):
        """Test that processor starts in IDLE state."""
        assert processor._execution_state == ExecutionState.IDLE
    
    def test_pause_from_running(self, processor):
        """Test pausing from RUNNING state."""
        processor._execution_state = ExecutionState.RUNNING
        processor._is_processing = True
        
        state_changed_signal = Mock()
        processor.execution_state_changed.connect(state_changed_signal)
        
        processor.pause()
        
        assert processor._execution_state == ExecutionState.PAUSED
        state_changed_signal.assert_called_once()
    
    def test_pause_from_idle_does_nothing(self, processor):
        """Test that pausing from IDLE state has no effect."""
        processor._execution_state = ExecutionState.IDLE
        
        processor.pause()
        
        assert processor._execution_state == ExecutionState.IDLE
    
    def test_resume_from_paused(self, processor, sample_tokens):
        """Test resuming from PAUSED state."""
        # Setup paused state
        processor._execution_state = ExecutionState.PAUSED
        processor._is_processing = True
        processor._tokens = sample_tokens
        processor._current_token_index = 1
        processor._total_commands = len(sample_tokens)
        
        state_changed_signal = Mock()
        processor.execution_state_changed.connect(state_changed_signal)
        
        # Resume (will try to process next token, which will fail gracefully in test)
        with patch.object(processor, '_process_next_token'):
            processor.resume()
        
        assert processor._execution_state == ExecutionState.RUNNING
        state_changed_signal.assert_called_once()
    
    def test_resume_from_running_does_nothing(self, processor):
        """Test that resuming from RUNNING state has no effect."""
        processor._execution_state = ExecutionState.RUNNING
        
        processor.resume()
        
        assert processor._execution_state == ExecutionState.RUNNING
    
    def test_cancel_from_running(self, processor):
        """Test cancelling from RUNNING state."""
        processor._execution_state = ExecutionState.RUNNING
        processor._is_processing = True
        processor._batch_id = "test123"
        processor._node_name = "TestNode"
        processor._total_commands = 3
        processor._success_count = 0
        
        state_changed_signal = Mock()
        processor.execution_state_changed.connect(state_changed_signal)
        
        # Don't mock _finish_processing, let it actually run
        processor.cancel()
        
        # State should be IDLE after finish_processing is called
        assert processor._execution_state == ExecutionState.IDLE
    
    def test_cancel_from_paused(self, processor):
        """Test cancelling from PAUSED state."""
        processor._execution_state = ExecutionState.PAUSED
        processor._is_processing = True
        processor._batch_id = "test123"
        processor._node_name = "TestNode"
        processor._total_commands = 3
        processor._success_count = 0
        
        # Don't mock _finish_processing, let it actually run
        processor.cancel()
        
        assert processor._execution_state == ExecutionState.IDLE
    
    def test_state_changes_to_running_on_start(self, processor, sample_tokens):
        """Test that state changes to RUNNING when processing starts."""
        state_changed_signal = Mock()
        processor.execution_state_changed.connect(state_changed_signal)
        
        with patch.object(processor, '_process_next_token'):
            processor.process_tokens_sequentially("TestNode", sample_tokens, "print")
        
        assert processor._execution_state == ExecutionState.RUNNING
        state_changed_signal.assert_called()
    
    def test_state_changes_to_idle_on_finish(self, processor):
        """Test that state changes to IDLE when processing finishes."""
        processor._execution_state = ExecutionState.RUNNING
        processor._is_processing = True
        processor._total_commands = 3
        processor._success_count = 3
        processor._batch_id = "test123"
        processor._node_name = "TestNode"
        
        state_changed_signal = Mock()
        processor.execution_state_changed.connect(state_changed_signal)
        
        processor._finish_processing()
        
        assert processor._execution_state == ExecutionState.IDLE
        assert not processor._is_processing


class TestProcessControl:
    """Test process control (pause/resume/cancel) during execution."""
    
    def test_process_next_token_stops_when_paused(self, processor, sample_tokens):
        """Test that _process_next_token returns early when PAUSED."""
        processor._execution_state = ExecutionState.PAUSED
        processor._current_token_index = 0
        processor._total_commands = len(sample_tokens)
        processor._tokens = sample_tokens
        
        # Should return early without processing
        processor._process_next_token()
        
        # Token index should not advance
        assert processor._current_token_index == 0
    
    def test_process_next_token_finishes_when_cancelled(self, processor, sample_tokens):
        """Test that _process_next_token calls finish_processing when CANCELLED."""
        processor._execution_state = ExecutionState.CANCELLED
        processor._current_token_index = 0
        processor._total_commands = len(sample_tokens)
        processor._tokens = sample_tokens
        processor._is_processing = True
        processor._batch_id = "test123"
        processor._node_name = "TestNode"
        
        with patch.object(processor, '_finish_processing') as mock_finish:
            processor._process_next_token()
        
        mock_finish.assert_called_once()


class TestSignalEmission:
    """Test that signals are emitted correctly."""
    
    def test_current_file_processing_signal_emitted(self, processor, sample_tokens):
        """Test that current_file_processing signal is emitted when processing starts."""
        signal_mock = Mock()
        processor.current_file_processing.connect(signal_mock)
        
        processor._execution_state = ExecutionState.RUNNING
        processor._is_processing = True
        processor._tokens = sample_tokens
        processor._current_token_index = 0
        processor._total_commands = len(sample_tokens)
        processor._node_name = "TestNode"
        processor._batch_id = "test123"
        
        # Mock the command queue add_command to prevent actual command execution
        with patch.object(processor.command_queue, 'add_command'):
            processor._process_next_token()
        
        # Signal should be emitted with node_name, token, log_path
        signal_mock.assert_called_once()
        call_args = signal_mock.call_args[0]
        assert call_args[0] == "TestNode"  # node_name
        assert call_args[1].token_id == "162"  # token
        # Verify log_path contains expected elements (path format may vary)
        assert "TestNode" in call_args[2]  # log_path contains node name
        assert "162" in call_args[2]  # log_path contains token ID
    
    def test_execution_state_changed_signal_on_pause(self, processor):
        """Test execution_state_changed signal emitted on pause."""
        processor._execution_state = ExecutionState.RUNNING
        
        signal_mock = Mock()
        processor.execution_state_changed.connect(signal_mock)
        
        processor.pause()
        
        signal_mock.assert_called_once_with(ExecutionState.PAUSED)
    
    def test_execution_state_changed_signal_on_resume(self, processor):
        """Test execution_state_changed signal emitted on resume."""
        processor._execution_state = ExecutionState.PAUSED
        processor._is_processing = True
        processor._tokens = []
        processor._current_token_index = 0
        processor._total_commands = 0
        
        signal_mock = Mock()
        processor.execution_state_changed.connect(signal_mock)
        
        with patch.object(processor, '_process_next_token'):
            processor.resume()
        
        signal_mock.assert_called_once_with(ExecutionState.RUNNING)


class TestEdgeCases:
    """Test edge cases and error conditions."""
    
    def test_pause_during_last_token(self, processor, sample_tokens):
        """Test pausing during the last token."""
        processor._execution_state = ExecutionState.RUNNING
        processor._current_token_index = len(sample_tokens) - 1
        processor._total_commands = len(sample_tokens)
        processor._tokens = sample_tokens
        
        processor.pause()
        
        assert processor._execution_state == ExecutionState.PAUSED
    
    def test_cancel_with_no_active_processing(self, processor):
        """Test cancel when not processing."""
        processor._execution_state = ExecutionState.IDLE
        
        processor.cancel()
        
        # Should stay IDLE
        assert processor._execution_state == ExecutionState.IDLE
    
    def test_multiple_pause_calls(self, processor):
        """Test multiple pause calls in succession."""
        processor._execution_state = ExecutionState.RUNNING
        
        processor.pause()
        first_state = processor._execution_state
        
        processor.pause()  # Second pause
        second_state = processor._execution_state
        
        assert first_state == ExecutionState.PAUSED
        assert second_state == ExecutionState.PAUSED


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
