"""
Integration Test for Sequential Command Processor with Pause/Resume/Cancel

This test simulates realistic command execution scenarios including:
- Starting sequential processing for multiple tokens
- Pausing execution mid-stream
- Resuming from paused state
- Cancelling operations
- Visual tracking signals
"""

import pytest
import logging
from unittest.mock import Mock, MagicMock, patch, call
from PyQt5.QtCore import QObject, pyqtSignal
from src.commander.services.sequential_command_processor import SequentialCommandProcessor, ExecutionState
from src.commander.models import NodeToken


class MockCommandQueue(QObject):
    """Mock command queue with signals"""
    command_completed = pyqtSignal(str, str, bool, object)  # command, result, success, token
    progress_updated = pyqtSignal(int, int)  # current, total
    
    def __init__(self):
        super().__init__()
        self.is_processing_flag = False
        self.auto_cleanup = True
        
    @property
    def is_processing(self):
        return self.is_processing_flag
        
    def set_auto_cleanup(self, enabled):
        self.auto_cleanup = enabled
        
    def add_command(self, command, token, telnet_session=None, timeout=30):
        pass
        
    def start_processing(self):
        self.is_processing_flag = True
        
    def clear(self):
        pass
        
    def manual_cleanup(self):
        """Mock manual cleanup - returns number of commands cleaned"""
        return 0


class MockFbcService:
    """Mock FBC command service"""
    def __init__(self):
        self.node_manager = Mock()
        self.node_manager.get_node.return_value = None


class MockRpcService:
    """Mock RPC command service"""
    pass


class MockSessionManager:
    """Mock session manager"""
    def get_or_create_session(self, ip, timeout=30):
        return Mock()
        
    def release_session(self, ip):
        pass


class MockLogWriter:
    """Mock log writer with correct API"""
    def __init__(self):
        self.app_log_messages = []
        
    def write_to_app_log(self, message, level=logging.INFO):
        """Record log messages"""
        self.app_log_messages.append((message, level))


class TestSequentialIntegration:
    """Integration tests for sequential command processing with pause/resume/cancel"""
    
    @pytest.fixture
    def setup_processor(self):
        """Setup processor with all dependencies"""
        command_queue = MockCommandQueue()
        fbc_service = MockFbcService()
        rpc_service = MockRpcService()
        session_manager = MockSessionManager()
        log_writer = MockLogWriter()
        
        processor = SequentialCommandProcessor(
            command_queue=command_queue,
            fbc_service=fbc_service,
            rpc_service=rpc_service,
            session_manager=session_manager,
            logging_service=log_writer,
            parent=None
        )
        
        return processor, command_queue, log_writer
    
    def test_realistic_sequential_execution(self, setup_processor):
        """Test realistic sequential execution of multiple tokens"""
        processor, command_queue, log_writer = setup_processor
        
        # Create realistic tokens simulating AP01 node
        tokens = [
            NodeToken(token_id="162", token_type="FBC", name="AP01", ip_address="192.168.0.11"),
            NodeToken(token_id="163", token_type="FBC", name="AP01", ip_address="192.168.0.11"),
            NodeToken(token_id="164", token_type="RPC", name="AP01", ip_address="192.168.0.11"),
            NodeToken(token_id="165", token_type="RPC", name="AP01", ip_address="192.168.0.11"),
        ]
        
        # Connect signal spy
        status_messages = []
        progress_updates = []
        
        def capture_status(msg, duration):
            status_messages.append(msg)
            
        def capture_progress(current, total):
            progress_updates.append((current, total))
        
        processor.status_message.connect(capture_status)
        processor.progress_updated.connect(capture_progress)
        
        # Start processing
        processor.process_tokens_sequentially(
            node_name="AP01",
            tokens=tokens,
            action="print"
        )
        
        # Verify state
        assert processor._execution_state == ExecutionState.RUNNING
        assert processor._node_name == "AP01"
        assert len(processor._tokens) == 4
        
        # Verify batch logging
        assert len(log_writer.app_log_messages) > 0
        first_log = log_writer.app_log_messages[0]
        assert "Batch" in first_log[0]
        assert "Starting sequential processing" in first_log[0]
        assert "AP01" in first_log[0]
        assert "Tokens: 4" in first_log[0]
        assert first_log[1] == logging.INFO
    
    def test_pause_during_execution(self, setup_processor):
        """Test pausing during active sequential execution"""
        processor, command_queue, log_writer = setup_processor
        
        tokens = [
            NodeToken(token_id="162", token_type="FBC", name="AP01", ip_address="192.168.0.11"),
            NodeToken(token_id="163", token_type="FBC", name="AP01", ip_address="192.168.0.11"),
        ]
        
        # Track state changes
        state_changes = []
        processor.execution_state_changed.connect(lambda s: state_changes.append(s))
        
        # Start processing
        processor.process_tokens_sequentially("AP01", tokens, "print")
        assert processor._execution_state == ExecutionState.RUNNING
        assert ExecutionState.RUNNING in state_changes
        
        # Pause
        processor.pause()
        assert processor._execution_state == ExecutionState.PAUSED
        assert ExecutionState.PAUSED in state_changes
        
        # Verify pause signal emitted
        assert len(state_changes) >= 2
        assert state_changes[-1] == ExecutionState.PAUSED
    
    def test_resume_after_pause(self, setup_processor):
        """Test resuming after pausing"""
        processor, command_queue, log_writer = setup_processor
        
        tokens = [
            NodeToken(token_id="162", token_type="FBC", name="AP01", ip_address="192.168.0.11"),
        ]
        
        # Track state changes
        state_changes = []
        processor.execution_state_changed.connect(lambda s: state_changes.append(s))
        
        # Start, pause, resume
        processor.process_tokens_sequentially("AP01", tokens, "print")
        processor.pause()
        processor.resume()
        
        # Verify state progression
        assert ExecutionState.RUNNING in state_changes
        assert ExecutionState.PAUSED in state_changes
        assert state_changes[-1] == ExecutionState.RUNNING  # Final state is RUNNING
        assert processor._execution_state == ExecutionState.RUNNING
    
    def test_cancel_during_execution(self, setup_processor):
        """Test cancelling during execution"""
        processor, command_queue, log_writer = setup_processor
        
        tokens = [
            NodeToken(token_id="162", token_type="FBC", name="AP01", ip_address="192.168.0.11"),
            NodeToken(token_id="163", token_type="FBC", name="AP01", ip_address="192.168.0.11"),
        ]
        
        # Track signals
        state_changes = []
        finished_signals = []
        
        processor.execution_state_changed.connect(lambda s: state_changes.append(s))
        processor.processing_finished.connect(lambda s, t: finished_signals.append((s, t)))
        
        # Start processing
        processor.process_tokens_sequentially("AP01", tokens, "print")
        
        # Cancel
        processor.cancel()
        
        # Verify cancelled state
        assert ExecutionState.CANCELLED in state_changes
        # After cancel, processing should finish
        assert len(finished_signals) > 0
    
    def test_visual_tracking_signal(self, setup_processor):
        """Test that current_file_processing signal is emitted"""
        processor, command_queue, log_writer = setup_processor
        
        tokens = [
            NodeToken(token_id="162", token_type="FBC", name="AP01", ip_address="192.168.0.11"),
        ]
        
        # Track file processing signals
        file_signals = []
        
        def capture_file(node_name, token, file_path):
            file_signals.append((node_name, token.token_id, file_path))
        
        processor.current_file_processing.connect(capture_file)
        
        # Start processing
        processor.process_tokens_sequentially("AP01", tokens, "print")
        
        # Simulate command completion to trigger file processing
        processor._on_command_completed("print 162", "Success", True, tokens[0])
        
        # Verify signal was emitted
        assert len(file_signals) > 0
        assert file_signals[0][0] == "AP01"
        assert file_signals[0][1] == "162"
    
    def test_batch_completion_logging(self, setup_processor):
        """Test that batch completion is logged correctly"""
        processor, command_queue, log_writer = setup_processor
        
        tokens = [
            NodeToken(token_id="162", token_type="FBC", name="AP01", ip_address="192.168.0.11"),
        ]
        
        # Start processing
        processor.process_tokens_sequentially("AP01", tokens, "print")
        
        # Simulate completion
        processor._on_command_completed("print 162", "Success", True, tokens[0])
        
        # Force finish
        processor._finish_processing()
        
        # Verify completion logging
        completion_logs = [msg for msg, level in log_writer.app_log_messages if "Completed processing" in msg]
        assert len(completion_logs) > 0
        assert "AP01" in completion_logs[0]
        assert "Success:" in completion_logs[0]
    
    def test_error_logging_level(self, setup_processor):
        """Test that errors are logged with ERROR level"""
        processor, command_queue, log_writer = setup_processor
        
        tokens = [
            NodeToken(token_id="162", token_type="FBC", name="AP01", ip_address="192.168.0.11"),
        ]
        
        # Start processing
        processor.process_tokens_sequentially("AP01", tokens, "print")
        
        # Simulate failure
        processor._on_command_completed("print 162", "Connection failed", False, tokens[0])
        
        # Verify ERROR level logging
        error_logs = [(msg, level) for msg, level in log_writer.app_log_messages if level == logging.ERROR]
        assert len(error_logs) > 0
        assert "Failure" in error_logs[0][0] or "Error" in error_logs[0][0]
    
    def test_multiple_pause_resume_cycles(self, setup_processor):
        """Test multiple pause/resume cycles"""
        processor, command_queue, log_writer = setup_processor
        
        tokens = [
            NodeToken(token_id="162", token_type="FBC", name="AP01", ip_address="192.168.0.11"),
            NodeToken(token_id="163", token_type="FBC", name="AP01", ip_address="192.168.0.11"),
            NodeToken(token_id="164", token_type="FBC", name="AP01", ip_address="192.168.0.11"),
        ]
        
        # Track state changes
        state_changes = []
        processor.execution_state_changed.connect(lambda s: state_changes.append(s))
        
        # Start processing
        processor.process_tokens_sequentially("AP01", tokens, "print")
        
        # First pause/resume cycle
        processor.pause()
        processor.resume()
        
        # Second pause/resume cycle
        processor.pause()
        processor.resume()
        
        # Verify state sequence
        assert ExecutionState.RUNNING in state_changes
        assert state_changes.count(ExecutionState.PAUSED) >= 2
        assert state_changes.count(ExecutionState.RUNNING) >= 3  # Initial + 2 resumes
        assert processor._execution_state == ExecutionState.RUNNING
    
    def test_cancel_then_new_execution(self, setup_processor):
        """Test starting new execution after cancelling"""
        processor, command_queue, log_writer = setup_processor
        
        tokens1 = [
            NodeToken(token_id="162", token_type="FBC", name="AP01", ip_address="192.168.0.11"),
        ]
        tokens2 = [
            NodeToken(token_id="163", token_type="FBC", name="AP01", ip_address="192.168.0.11"),
        ]
        
        # First execution
        processor.process_tokens_sequentially("AP01", tokens1, "print")
        processor.cancel()
        
        # Clear log for new execution
        log_writer.app_log_messages.clear()
        
        # Second execution
        processor.process_tokens_sequentially("AP01", tokens2, "print")
        
        # Verify new execution started
        assert processor._execution_state == ExecutionState.RUNNING
        assert processor._current_token_index == 0
        assert len(processor._tokens) == 1
        
        # Verify new batch logged
        batch_logs = [msg for msg, level in log_writer.app_log_messages if "Batch" in msg and "Starting" in msg]
        assert len(batch_logs) == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
