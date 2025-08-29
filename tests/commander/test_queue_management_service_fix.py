import unittest
from unittest.mock import patch, MagicMock
from PyQt6.QtCore import QCoreApplication
import sys

# Add the src directory to the path so we can import the modules
sys.path.insert(0, 'src')

from src.commander.models import NodeToken
from src.commander.command_queue import CommandQueue


class TestQueueManagementServiceFix(unittest.TestCase):
    """Focused test cases for validating the queue management service fix"""

    def setUp(self):
        """Set up test environment"""
        self.app = QCoreApplication(sys.argv) if not QCoreApplication.instance() else QCoreApplication.instance()
        
        # Create mock session manager
        self.mock_session_manager = MagicMock()
        
        # Create command queue instance
        self.queue = CommandQueue(self.mock_session_manager)
        
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

    def tearDown(self):
        """Clean up after tests"""
        # Ensure queue is not processing
        self.queue._is_processing = False

    def test_sequential_processing_of_multiple_commands(self):
        """Test that queue processes all commands sequentially with proper state management"""
        # Create mock telnet client
        mock_telnet_client = MagicMock()
        mock_telnet_client.is_connected = True
        
        # Add 3 commands to the queue
        self.queue.add_command("command1", self.token1, mock_telnet_client)
        self.queue.add_command("command2", self.token2, mock_telnet_client)
        self.queue.add_command("command3", self.token3, mock_telnet_client)
        
        # Verify commands were added to queue
        self.assertEqual(len(self.queue.queue), 3)
        
        # Verify processing state is active
        self.assertTrue(self.queue.is_processing)

    def test_processing_state_resets_after_all_commands_complete(self):
        """Test that processing state properly resets when all commands complete"""
        # Create mock workers
        mock_worker1 = MagicMock()
        mock_worker2 = MagicMock()
        
        # Configure mock workers
        mock_worker1.command = "command1"
        mock_worker1.success = True
        mock_worker1.result = "success"
        mock_worker1.token = self.token1
        
        mock_worker2.command = "command2"
        mock_worker2.success = True
        mock_worker2.result = "success"
        mock_worker2.token = self.token2
        
        # Disable auto cleanup to better observe state
        self.queue.set_auto_cleanup(False)
        
        # Add commands to queue
        mock_telnet_client = MagicMock()
        self.queue.add_command("command1", self.token1, mock_telnet_client)
        self.queue.add_command("command2", self.token2, mock_telnet_client)
        
        # Verify initial processing state
        self.assertTrue(self.queue.is_processing)
        
        # Simulate completion of first command
        self.queue._handle_worker_finished(mock_worker1)
        
        # Should still be processing as there's one more command
        self.assertTrue(self.queue.is_processing)
        
        # Simulate completion of second command
        self.queue._handle_worker_finished(mock_worker2)
        
        # Now all commands are done, processing state should reset to False
        self.assertFalse(self.queue.is_processing)
        
        # Clean up
        self.queue.manual_cleanup()

    @patch('src.commander.command_queue.QThreadPool.start')
    def test_auto_continuation_with_multiple_commands(self, mock_start):
        """Test that auto-continuation works with multiple queued commands"""
        # Mock session manager to return our telnet client
        mock_telnet_client = MagicMock()
        mock_telnet_client.is_connected = True
        self.mock_session_manager.get_or_create_session.return_value = mock_telnet_client
        self.mock_session_manager.get_debugger_session.return_value = None
        
        # Add 3 commands to the queue
        self.queue.add_command("command1", self.token1)
        self.queue.add_command("command2", self.token2)
        self.queue.add_command("command3", self.token3)
        
        # Verify all commands were added
        self.assertEqual(len(self.queue.queue), 3)
        
        # Verify thread pool start was called for each command
        self.assertEqual(mock_start.call_count, 3)
        
        # Verify processing state is active
        self.assertTrue(self.queue.is_processing)


if __name__ == '__main__':
    unittest.main()