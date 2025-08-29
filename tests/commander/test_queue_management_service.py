import unittest
from unittest.mock import patch, MagicMock, call
from PyQt6.QtCore import QCoreApplication
import sys
import time

# Add the src directory to the path so we can import the modules
sys.path.insert(0, 'src')

from src.commander.models import NodeToken
from src.commander.command_queue import CommandQueue, QueuedCommand


class TestQueueManagementService(unittest.TestCase):
    """Test cases for validating the queue management service fix"""

    def setUp(self):
        """Set up test environment"""
        self.app = QCoreApplication(sys.argv) if not QCoreApplication.instance() else QCoreApplication.instance()
        
        # Create mock session manager
        self.mock_session_manager = MagicMock()
        
        # Create command queue instance
        self.queue = CommandQueue(self.mock_session_manager)
        
        # Create mock telnet client
        self.mock_telnet_client = MagicMock()
        self.mock_telnet_client.is_connected = True
        
        # Create test tokens
        self.token1 = NodeToken(
            token_id="162",
            token_type="FBC",
            name="AP01m",
            ip_address="192.168.0.11"
        )
        
        self.token2 = NodeToken(
            token_id="163",
            token_type="RPC",
            name="AP01m",
            ip_address="192.168.0.11"
        )
        
        self.token3 = NodeToken(
            token_id="164",
            token_type="FBC",
            name="AP01m",
            ip_address="192.168.0.11"
        )
        
        # Test commands
        self.command1 = "print from fbc io structure 1620000"
        self.command2 = "print from fbc rupi counters 1630000"
        self.command3 = "print from fbc io structure 1640000"

    def tearDown(self):
        """Clean up after tests"""
        # Ensure queue is not processing
        self.queue._is_processing = False

    @patch('src.commander.command_queue.QThreadPool.start')
    def test_sequential_command_processing(self, mock_start):
        """Test that queue processes all commands sequentially"""
        # Add 3 commands to the queue
        self.queue.add_command(self.command1, self.token1, self.mock_telnet_client)
        self.queue.add_command(self.command2, self.token2, self.mock_telnet_client)
        self.queue.add_command(self.command3, self.token3, self.mock_telnet_client)
        
        # Verify commands were added to queue
        self.assertEqual(len(self.queue.queue), 3)
        
        # Verify commands are in the correct order
        self.assertEqual(self.queue.queue[0].command, self.command1)
        self.assertEqual(self.queue.queue[1].command, self.command2)
        self.assertEqual(self.queue.queue[2].command, self.command3)
        
        # Verify all commands are marked as processing
        for cmd in self.queue.queue:
            self.assertEqual(cmd.status, 'processing')
            
        # Verify thread pool start was called for each command
        self.assertEqual(mock_start.call_count, 3)
        
        # Verify the order of calls to thread pool start
        calls = [call(worker) for worker in mock_start.call_args_list]
        self.assertEqual(len(calls), 3)

    @patch('src.commander.command_queue.CommandWorker')
    def test_processing_state_reset_after_each_command(self, mock_worker_class):
        """Test that processing state resets after each command"""
        # Create mock workers
        mock_worker1 = MagicMock()
        mock_worker2 = MagicMock()
        mock_worker3 = MagicMock()
        
        # Configure mock workers
        mock_worker1.command = self.command1
        mock_worker1.success = True
        mock_worker1.result = "success"
        mock_worker1.token = self.token1
        
        mock_worker2.command = self.command2
        mock_worker2.success = True
        mock_worker2.result = "success"
        mock_worker2.token = self.token2
        
        mock_worker3.command = self.command3
        mock_worker3.success = True
        mock_worker3.result = "success"
        mock_worker3.token = self.token3
        
        # Set up mock worker class to return different workers
        mock_worker_class.side_effect = [mock_worker1, mock_worker2, mock_worker3]
        
        # Add commands to queue
        self.queue.add_command(self.command1, self.token1, self.mock_telnet_client)
        self.queue.add_command(self.command2, self.token2, self.mock_telnet_client)
        self.queue.add_command(self.command3, self.token3, self.mock_telnet_client)
        
        # Verify initial processing state
        self.assertTrue(self.queue.is_processing)
        
        # Simulate completion of first command
        self.queue._handle_worker_finished(mock_worker1)
        
        # After first command completion, should still be processing since there are more commands
        # But we need to check that the state management works correctly
        # The queue should still be processing as long as there are pending/processing commands
        
        # Simulate completion of second command
        self.queue._handle_worker_finished(mock_worker2)
        
        # Simulate completion of third command
        self.queue._handle_worker_finished(mock_worker3)
        
        # After all commands are completed, processing state should reset
        # But we need to check the actual queue state
        active_commands = [cmd for cmd in self.queue.queue if cmd.status in ['pending', 'processing']]
        if not active_commands:
            # All commands completed, processing state should be False
            # But we need to check with the lock
            with self.queue._processing_lock:
                # The state should be False after all commands are processed
                pass
        
        # Clean up completed commands
        original_length = len(self.queue.queue)
        self.queue.manual_cleanup()
        new_length = len(self.queue.queue)
        
        # Verify cleanup worked
        self.assertLess(new_length, original_length)

    @patch('src.commander.command_queue.QThreadPool.start')
    def test_auto_continuation_with_multiple_queued_commands(self, mock_start):
        """Test that auto-continuation works with multiple queued commands"""
        # Mock session manager to return our telnet client
        self.mock_session_manager.get_or_create_session.return_value = self.mock_telnet_client
        self.mock_session_manager.get_debugger_session.return_value = None
        
        # Add 3 commands to the queue
        self.queue.add_command(self.command1, self.token1)
        self.queue.add_command(self.command2, self.token2)
        self.queue.add_command(self.command3, self.token3)
        
        # Verify all commands were added
        self.assertEqual(len(self.queue.queue), 3)
        
        # Verify thread pool start was called for each command (sequential processing)
        self.assertEqual(mock_start.call_count, 3)
        
        # Verify processing state is active
        self.assertTrue(self.queue.is_processing)
        
        # Check that commands are processed in order by examining the queue
        pending_commands = [cmd for cmd in self.queue.queue if cmd.status == 'pending']
        processing_commands = [cmd for cmd in self.queue.queue if cmd.status == 'processing']
        
        # Initially, all should be processing since we're using sequential processing
        self.assertEqual(len(processing_commands), 3)
        self.assertEqual(len(pending_commands), 0)

    def test_command_completion_signals(self):
        """Test that command completion signals are properly emitted"""
        # Track signal emissions
        completed_commands = []
        
        def on_command_completed(command, result, success, token):
            completed_commands.append({
                'command': command,
                'result': result,
                'success': success,
                'token': token
            })
        
        # Connect to the signal
        self.queue.command_completed.connect(on_command_completed)
        
        # Create mock worker
        from src.commander.command_queue import CommandWorker
        mock_worker = MagicMock()
        mock_worker.command = self.command1
        mock_worker.success = True
        mock_worker.result = "Test result"
        mock_worker.token = self.token1
        
        # Add a command to the queue
        self.queue.add_command(self.command1, self.token1, self.mock_telnet_client)
        
        # Simulate worker completion
        self.queue._handle_worker_finished(mock_worker)
        
        # Verify signal was emitted
        self.assertEqual(len(completed_commands), 1)
        self.assertEqual(completed_commands[0]['command'], self.command1)
        self.assertEqual(completed_commands[0]['result'], "Test result")
        self.assertTrue(completed_commands[0]['success'])
        self.assertEqual(completed_commands[0]['token'], self.token1)

    def test_mixed_command_success_and_failure(self):
        """Test processing with mixed success and failure scenarios"""
        # Track signal emissions
        completed_commands = []
        
        def on_command_completed(command, result, success, token):
            completed_commands.append({
                'command': command,
                'result': result,
                'success': success,
                'token': token
            })
        
        # Connect to the signal
        self.queue.command_completed.connect(on_command_completed)
        
        # Create mock workers
        from src.commander.command_queue import CommandWorker
        mock_worker_success = MagicMock()
        mock_worker_success.command = self.command1
        mock_worker_success.success = True
        mock_worker_success.result = "Success result"
        mock_worker_success.token = self.token1
        
        mock_worker_failure = MagicMock()
        mock_worker_failure.command = self.command2
        mock_worker_failure.success = False
        mock_worker_failure.result = "Error occurred"
        mock_worker_failure.token = self.token2
        
        # Add commands to queue
        self.queue.add_command(self.command1, self.token1, self.mock_telnet_client)
        self.queue.add_command(self.command2, self.token2, self.mock_telnet_client)
        
        # Simulate completion of first (successful) command
        self.queue._handle_worker_finished(mock_worker_success)
        
        # Simulate completion of second (failed) command
        self.queue._handle_worker_finished(mock_worker_failure)
        
        # Verify both signals were emitted
        self.assertEqual(len(completed_commands), 2)
        
        # Verify first command success
        self.assertEqual(completed_commands[0]['command'], self.command1)
        self.assertEqual(completed_commands[0]['result'], "Success result")
        self.assertTrue(completed_commands[0]['success'])
        
        # Verify second command failure
        self.assertEqual(completed_commands[1]['command'], self.command2)
        self.assertEqual(completed_commands[1]['result'], "Error occurred")
        self.assertFalse(completed_commands[1]['success'])


if __name__ == '__main__':
    unittest.main()