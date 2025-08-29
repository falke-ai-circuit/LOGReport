import pytest
from unittest.mock import MagicMock, patch
from PyQt6.QtCore import QObject, pyqtSignal
from src.commander.command_queue import CommandQueue, QueuedCommand
from src.commander.models import NodeToken
from src.commander.session_manager import SessionManager

@pytest.fixture
def command_queue():
    """Fixture providing a configured CommandQueue with mock session manager"""
    session_mgr = MagicMock(spec=SessionManager)
    session_mgr.get_debugger_session.return_value = MagicMock(is_connected=True)
    queue = CommandQueue(session_manager=session_mgr)
    queue.thread_pool.setMaxThreadCount(1)  # Ensure sequential processing
    return queue

class TestCommandQueueSequentialProcessing:
    def test_processes_multiple_commands_in_order(self, command_queue):
        """Verify the queue processes all commands sequentially"""
        # Setup
        commands_executed = []
        test_token = NodeToken(token_id="test123", token_type="FBC", name="TestNode", ip_address="192.168.0.1")
        
        # Create mock worker completion handler with proper typing
        def mock_worker_finished(command: str, result: str, success: bool, token: NodeToken):
            nonlocal commands_executed
            commands_executed.append(command)
            if len(commands_executed) < 3:
                command_queue.add_command(f"command_{len(commands_executed)+1}", test_token)
        
        # Connect mock handler with proper signal signature
        command_queue.command_completed.connect(
            lambda command, result, success, token: mock_worker_finished(command, result, success, token)
        )
        
        # Add initial commands
        command_queue.add_command("command_1", test_token)
        command_queue.add_command("command_2", test_token)
        command_queue.add_command("command_3", test_token)
        
        # Start processing
        command_queue.start_processing()
        
        # Use QTest for reliable event processing
        from PyQt6.QtTest import QTest
        
        # Trigger processing and wait with event handling
        command_queue.start_processing()
        QTest.qWait(3000)  # 3 seconds with event processing
        
        # Verify execution sequence
        expected_commands = ["command_1", "command_2", "command_3"]
        assert commands_executed == expected_commands, \
            f"Execution order mismatch\nExpected: {expected_commands}\nActual: {commands_executed}"
        
        # Verify queue cleanup
        assert len(command_queue.queue) == 0, f"Queue not empty: {len(command_queue.queue)} items remaining"
        
        # Verify
        assert len(commands_executed) == 3
        assert commands_executed == ["command_1", "command_2", "command_3"]
        
    def test_maintains_processing_state_until_completion(self, command_queue):
        """Ensure processing state remains active until last command completes"""
        test_token = NodeToken(token_id="test456", token_type="RPC", name="TestNode2", ip_address="192.168.0.2")
        
        # Add 3 commands
        for i in range(3):
            command_queue.add_command(f"cmd_{i+1}", test_token)
            
        command_queue.start_processing()
        
        # Verify processing state stays active
        assert command_queue.is_processing is True
        
        # Simulate command completions
        while command_queue.queue:
            cmd = command_queue.queue[0]
            # Create properly typed mock worker with string result
            mock_worker = MagicMock()
            mock_worker.command = cmd.command
            mock_worker.success = True
            mock_worker.token = test_token
            mock_worker.result = "mocked result"
            command_queue._handle_worker_finished(mock_worker)
            
        # Final state check
        assert command_queue.is_processing is False
        assert len(command_queue.queue) == 0