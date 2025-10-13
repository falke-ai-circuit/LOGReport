"""
Test SequentialCommandProcessor guard condition fix.
Verifies that sequential processor ignores commands when not actively processing.
"""

import pytest
from unittest.mock import Mock, MagicMock
from src.commander.services.sequential_command_processor import SequentialCommandProcessor, ExecutionState
from src.commander.models import NodeToken


@pytest.fixture
def mock_dependencies():
    """Create mock dependencies for SequentialCommandProcessor."""
    command_queue = Mock()
    command_queue.command_completed = Mock()
    command_queue.progress_updated = Mock()
    command_queue.set_auto_cleanup = Mock()
    
    fbc_service = Mock()
    rpc_service = Mock()
    session_manager = Mock()
    logging_service = Mock()
    logging_service.write_to_app_log = Mock()
    
    return {
        'command_queue': command_queue,
        'fbc_service': fbc_service,
        'rpc_service': rpc_service,
        'session_manager': session_manager,
        'logging_service': logging_service
    }


@pytest.fixture
def processor(mock_dependencies):
    """Create SequentialCommandProcessor instance with mocked dependencies."""
    return SequentialCommandProcessor(
        command_queue=mock_dependencies['command_queue'],
        fbc_service=mock_dependencies['fbc_service'],
        rpc_service=mock_dependencies['rpc_service'],
        session_manager=mock_dependencies['session_manager'],
        logging_service=mock_dependencies['logging_service']
    )


class TestSequentialProcessorGuard:
    """Test guard condition that prevents processing unowned commands."""
    
    def test_ignores_commands_when_not_processing(self, processor):
        """Test that _on_command_completed ignores commands when _is_processing is False."""
        # Arrange
        token = NodeToken(
            token_id="1234",
            token_type="FBC",
            node_name="AP01m",
            node_ip="192.168.0.1"
        )
        token.log_path = "/path/to/log.fbc"
        
        # Ensure processor is NOT processing
        processor._is_processing = False
        processor._total_commands = 0
        processor._completed_commands = 0
        processor._current_token_index = 0
        initial_execution_state = processor._execution_state
        
        # Act
        processor._on_command_completed("test_command", "result", True, token)
        
        # Assert - State should be unchanged
        assert processor._completed_commands == 0, "Completed commands should not increment when not processing"
        assert processor._current_token_index == 0, "Token index should not increment when not processing"
        assert processor._execution_state == initial_execution_state, "Execution state should remain unchanged"
        
    def test_processes_commands_when_actively_processing(self, processor):
        """Test that _on_command_completed processes commands when _is_processing is True."""
        # Arrange
        token = NodeToken(
            token_id="1234",
            token_type="FBC",
            node_name="AP01m",
            node_ip="192.168.0.1"
        )
        token.log_path = "/path/to/log.fbc"
        
        # Set up processor as actively processing
        processor._is_processing = True
        processor._total_commands = 3
        processor._completed_commands = 0
        processor._current_token_index = 0
        processor._execution_state = ExecutionState.RUNNING
        processor._tokens = [token, token, token]  # 3 tokens
        processor._batch_id = "test_batch"
        
        # Mock _process_next_token to avoid side effects
        processor._process_next_token = Mock()
        
        # Act
        processor._on_command_completed("test_command", "result", True, token)
        
        # Assert - State should be updated
        assert processor._completed_commands == 1, "Completed commands should increment when processing"
        assert processor._current_token_index == 1, "Token index should increment when processing"
        assert processor._process_next_token.called, "Should process next token when not finished"
        
    def test_finishes_when_all_commands_complete(self, processor):
        """Test that processor calls _finish_processing when all commands complete."""
        # Arrange
        token = NodeToken(
            token_id="1234",
            token_type="FBC",
            node_name="AP01m",
            node_ip="192.168.0.1"
        )
        token.log_path = "/path/to/log.fbc"
        
        # Set up processor as actively processing, last command
        processor._is_processing = True
        processor._total_commands = 1
        processor._completed_commands = 0
        processor._current_token_index = 0
        processor._execution_state = ExecutionState.RUNNING
        processor._tokens = [token]
        processor._batch_id = "test_batch"
        
        # Mock _finish_processing to verify it's called
        processor._finish_processing = Mock()
        
        # Act
        processor._on_command_completed("test_command", "result", True, token)
        
        # Assert
        assert processor._completed_commands == 1, "Should increment completed commands"
        assert processor._current_token_index == 1, "Should increment token index"
        assert processor._finish_processing.called, "Should call _finish_processing when all commands complete"
    
    def test_guard_prevents_premature_finish(self, processor):
        """
        Test that guard prevents Print All Nodes commands from triggering _finish_processing.
        This is the specific bug fix validation.
        """
        # Arrange - Simulate Print All Nodes scenario
        # Sequential processor is idle, but Print All Nodes queues commands via command_queue
        token = NodeToken(
            token_id="5678",
            token_type="LOG",
            node_name="AP02m",
            node_ip="192.168.0.2"
        )
        token.log_path = "/path/to/log.log"
        
        # Sequential processor NOT processing (Print All Nodes uses different workflow)
        processor._is_processing = False
        processor._total_commands = 0  # Not set by Print All Nodes
        processor._completed_commands = 0
        processor._current_token_index = 0
        processor._execution_state = ExecutionState.IDLE
        
        # Mock _finish_processing to ensure it's NOT called
        processor._finish_processing = Mock()
        
        # Act - Simulate command_queue emitting command_completed for Print All Nodes command
        processor._on_command_completed("print_command", "result", True, token)
        
        # Assert - Guard should prevent any state changes or _finish_processing call
        assert processor._completed_commands == 0, "Should NOT increment when not processing"
        assert processor._current_token_index == 0, "Should NOT increment when not processing"
        assert not processor._finish_processing.called, "Should NOT call _finish_processing when not processing"
        assert processor._execution_state == ExecutionState.IDLE, "Should remain IDLE"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
