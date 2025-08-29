import sys
import os
import logging
from unittest.mock import MagicMock
from PyQt6.QtCore import QObject

# Add src directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from commander.command_queue import CommandQueue, CommandWorker, QueuedCommand

class TestCommandQueueFix:
    def setup_method(self):
        # Setup logging
        logging.basicConfig(level=logging.DEBUG)
        self.logger = logging.getLogger(__name__)
        
        # Create mock session manager
        self.session_manager = MagicMock()
        
        # Create command queue
        self.queue = CommandQueue(session_manager=self.session_manager)
        self.queue.threading_service = MagicMock()
        self.queue._auto_cleanup = True
        
        # Mock worker signals
        self.worker_signals = MagicMock()

    def test_deadlock_fix(self):
        """Test that processing restarts when pending commands exist"""
        self.logger.info("Starting simplified deadlock fix test...")
        
        # Add 3 commands to the queue
        tokens = []
        for i in range(3):
            cmd = f"command_{i+1}"
            token = MagicMock()
            token.token_id = f"token_{i+1}"
            tokens.append(token)
            self.queue.add_command(cmd, token)
        
        # Mark first command as processing
        self.queue.queue[0].status = 'processing'
        
        # Simulate worker finishing for first command
        # Create mock telnet session
        mock_telnet = MagicMock()
        mock_telnet.is_connected = True
        mock_telnet.send_command.return_value = "mocked_response"
        
        worker1 = CommandWorker("command_1", tokens[0], mock_telnet)
        worker1.success = True
        worker1.result = "result_1"
        self.queue._handle_worker_finished(worker1)
        
        # Verify processing was restarted
        pending_commands = [cmd for cmd in self.queue.queue if cmd.status == 'pending']
        assert len(pending_commands) == 2, "Should have 2 pending commands"
        assert self.queue._is_processing, "Processing should be active"
        
        # Mark second command as processing
        self.queue.queue[0].status = 'processing'
        
        # Simulate worker finishing for second command
        worker2 = CommandWorker("command_2", tokens[1], mock_telnet)
        worker2.success = True
        worker2.result = "result_2"
        self.queue._handle_worker_finished(worker2)
        
        # Verify processing was restarted
        pending_commands = [cmd for cmd in self.queue.queue if cmd.status == 'pending']
        assert len(pending_commands) == 1, "Should have 1 pending command"
        assert self.queue._is_processing, "Processing should be active"
        
        # Mark third command as processing
        self.queue.queue[0].status = 'processing'
        
        # Simulate worker finishing for third command
        worker3 = CommandWorker("command_3", tokens[2], mock_telnet)
        worker3.success = True
        worker3.result = "result_3"
        self.queue._handle_worker_finished(worker3)
        
        # Verify queue is empty and processing stopped
        assert len(self.queue.queue) == 0, "Queue should be empty"
        assert not self.queue._is_processing, "Processing should have stopped"
        
        self.logger.info("✅ Simplified deadlock fix test passed successfully!")

if __name__ == "__main__":
    test = TestCommandQueueFix()
    test.setup_method()
    test.test_deadlock_fix()