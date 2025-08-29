import unittest
from unittest.mock import patch, MagicMock
from PyQt6.QtCore import QCoreApplication
from src.commander.command_queue import CommandQueue
from src.commander.models import NodeToken
import time


class TestCommandQueueDelay(unittest.TestCase):
    def setUp(self):
        self.app = QCoreApplication([])
        # Create a mock session manager for testing
        self.mock_session_manager = MagicMock()
        # Create a queue with a small delay for testing
        self.queue = CommandQueue(self.mock_session_manager, inter_command_delay=0.1)
        # Mock the threading service
        self.queue.threading_service = MagicMock()
        
        self.valid_token = NodeToken(
            token_id="123",
            token_type="admin",
            node_ip="192.168.1.1"
        )

    def test_delay_parameter_default_value(self):
        """Test that the default delay value is 0.2 seconds"""
        queue = CommandQueue(self.mock_session_manager)
        self.assertEqual(queue._inter_command_delay, 0.2)

    def test_delay_parameter_custom_value(self):
        """Test that a custom delay value is properly set"""
        queue = CommandQueue(self.mock_session_manager, inter_command_delay=0.5)
        self.assertEqual(queue._inter_command_delay, 0.5)

    def test_set_inter_command_delay(self):
        """Test that the delay can be updated after initialization"""
        self.queue.set_inter_command_delay(0.3)
        self.assertEqual(self.queue._inter_command_delay, 0.3)

    def test_delay_applied_between_commands(self):
        """Test that delay is applied between commands"""
        # Mock the thread pool start method to avoid actual thread execution
        with patch.object(self.queue.thread_pool, 'start'):
            # Add multiple commands to the queue directly
            self.queue.add_command("cmd1", self.valid_token)
            self.queue.add_command("cmd2", self.valid_token)
            self.queue.add_command("cmd3", self.valid_token)
            
            # Manually set all commands to pending status
            for cmd in self.queue.queue:
                cmd.status = 'pending'
            
            # Mock time.sleep to verify it's called
            with patch('src.commander.command_queue.time.sleep') as mock_sleep:
                # Call start_processing directly
                self.queue.start_processing()
                
                # Verify that sleep was called for the second and third commands
                # (not for the first one)
                self.assertEqual(mock_sleep.call_count, 2)
                # Verify that sleep was called with the correct delay value
                mock_sleep.assert_called_with(0.1)

    @patch('src.commander.command_queue.time.sleep')
    def test_no_delay_when_value_is_zero(self, mock_sleep):
        """Test that no delay is applied when delay value is zero"""
        # Create a queue with zero delay
        queue = CommandQueue(self.mock_session_manager, inter_command_delay=0.0)
        queue.threading_service = MagicMock()
        
        # Mock the thread pool start method to avoid actual thread execution
        with patch.object(queue.thread_pool, 'start'):
            # Add multiple commands
            queue.add_command("cmd1", self.valid_token)
            queue.add_command("cmd2", self.valid_token)
            queue.add_command("cmd3", self.valid_token)
            
            # Verify that sleep was not called
            mock_sleep.assert_not_called()

    def test_delay_not_applied_for_single_command(self):
        """Test that no delay is applied for a single command"""
        # Mock the thread pool start method to avoid actual thread execution
        with patch.object(self.queue.thread_pool, 'start'):
            self.queue.add_command("cmd1", self.valid_token)
            
            # Manually set command to pending status
            self.queue.queue[0].status = 'pending'
            
            # Mock time.sleep to verify it's called
            with patch('src.commander.command_queue.time.sleep') as mock_sleep:
                # Call start_processing directly
                self.queue.start_processing()
                
                # Verify that sleep was not called
                mock_sleep.assert_not_called()

    def test_backward_compatibility(self):
        """Test that the queue works correctly without specifying delay parameter"""
        # Create queue without specifying delay (should use default)
        queue = CommandQueue(self.mock_session_manager)
        queue.threading_service = MagicMock()
        
        # Verify default delay is set
        self.assertEqual(queue._inter_command_delay, 0.2)
        
        # Test that basic functionality still works
        self.assertEqual(len(queue.queue), 0)


if __name__ == '__main__':
    unittest.main()