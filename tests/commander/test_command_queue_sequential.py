import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src')))

import unittest
from unittest.mock import MagicMock
from commander.command_queue import CommandQueue, QueuedCommand
from commander.models import NodeToken
from PyQt6.QtCore import QCoreApplication
import logging
import time

# Disable logging during tests
logging.disable(logging.CRITICAL)

class TestCommandQueueSequential(unittest.TestCase):
    def setUp(self):
        self.app = QCoreApplication.instance() or QCoreApplication([])
        self.session_manager = MagicMock()
        self.queue = CommandQueue(session_manager=self.session_manager)
        
        # Create test tokens
        self.token1 = NodeToken(token_id="001", token_type="FBC", name="Node1", ip_address="192.168.1.1")
        self.token2 = NodeToken(token_id="002", token_type="FBC", name="Node2", ip_address="192.168.1.2")
        self.token3 = NodeToken(token_id="003", token_type="FBC", name="Node3", ip_address="192.168.1.3")
        
        # Mock telnet session
        self.telnet_session = MagicMock()
        self.telnet_session.is_connected = True
        self.telnet_session.send_command.return_value = "OK"

    def test_sequential_processing(self):
        """Test that commands are processed sequentially one after another"""
        # Add commands to queue
        self.queue.add_command("command1", self.token1, self.telnet_session)
        self.queue.add_command("command2", self.token2, self.telnet_session)
        self.queue.add_command("command3", self.token3, self.telnet_session)
        
        # Process events until all commands complete
        start_time = time.time()
        while self.queue.active_workers > 0 and time.time() - start_time < 5:
            self.app.processEvents()
            time.sleep(0.1)
            
        # Verify all commands were processed
        self.assertEqual(len(self.queue.queue), 0)
        self.assertEqual(self.queue.completed_count, 3)
        self.assertFalse(self.queue.is_processing)
        
    def test_auto_continuation(self):
        """Test that new commands added during processing are handled"""
        # Add initial command
        self.queue.add_command("command1", self.token1, self.telnet_session)
        
        # Add another command after a delay
        def add_second_command():
            self.queue.add_command("command2", self.token2, self.telnet_session)
        QCoreApplication.instance().postEvent(self.app, add_second_command)
        
        # Process events until all commands complete
        start_time = time.time()
        while self.queue.active_workers > 0 and time.time() - start_time < 5:
            self.app.processEvents()
            time.sleep(0.1)
            
        # Verify both commands were processed
        self.assertEqual(len(self.queue.queue), 0)
        self.assertEqual(self.queue.completed_count, 2)
        self.assertFalse(self.queue.is_processing)

if __name__ == '__main__':
    unittest.main()