import unittest
from unittest.mock import patch, MagicMock
from PyQt6.QtCore import QCoreApplication, QTimer
from src.commander.command_queue import CommandQueue, CommandWorker
from src.commander.models import NodeToken
from src.commander.session_manager import SessionManager
import time

class TestCommandQueueFix(unittest.TestCase):
    def setUp(self):
        self.app = QCoreApplication([])
        
        # Create mock session manager
        self.mock_session_manager = MagicMock(spec=SessionManager)
        mock_session = MagicMock()
        mock_session.is_connected = True
        mock_session.send_command.return_value = "OK"
        self.mock_session_manager.get_or_create_session.return_value = mock_session
        
        self.queue = CommandQueue(self.mock_session_manager)
        
        # Create test tokens
        self.tokens = [
            NodeToken(token_id="162", token_type="FBC", name="AP01m", ip_address="192.168.0.11"),
            NodeToken(token_id="163", token_type="FBC", name="AP01m", ip_address="192.168.0.11"),
            NodeToken(token_id="164", token_type="FBC", name="AP01m", ip_address="192.168.0.11"),
            NodeToken(token_id="182", token_type="FBC", name="AP02m", ip_address="192.168.0.12"),
            NodeToken(token_id="362", token_type="FBC", name="AP01r", ip_address="192.168.0.27")
        ]
        
        # Sample FBC commands
        self.commands = [
            "print from fbc io structure 1620000",
            "print from fbc io structure 1630000",
            "print from fbc io structure 1640000",
            "print from fbc io structure 1820000",
            "print from fbc io structure 3620000"
        ]

    def test_multi_command_processing(self):
        """Test processing 5 FBC commands sequentially"""
        # Track execution order
        execution_order = []
        
        # Create mock workers that will emit finished signal
        def create_mock_worker(cmd, token):
            worker = CommandWorker(cmd, token, None)
            worker.success = True
            worker.result = "OK"
            worker.signals = MagicMock()
            
            # Simulate worker completion after delay
            QTimer.singleShot(100, lambda:
                worker.signals.finished.emit(worker, worker.result)
            )
            return worker
            
        # Mock worker creation
        with patch('src.commander.command_queue.CommandWorker') as mock_worker:
            mock_worker.side_effect = create_mock_worker
            
            # Add commands to queue
            for cmd, token in zip(self.commands, self.tokens):
                self.queue.add_command(cmd, token)
                
            # Verify all commands were added
            self.assertEqual(len(self.queue.queue), 5)
            
            # Process commands
            start_time = time.time()
            timeout = 5  # seconds
            
            # Use QTimer to simulate Qt event loop
            timer = QTimer()
            timer.setSingleShot(True)
            timer.timeout.connect(lambda: None)
            timer.start(timeout * 1000)
            
            while (time.time() - start_time) < timeout and self.queue.is_processing:
                QCoreApplication.processEvents()
                time.sleep(0.01)
                
            # Verify all commands completed
            completed = [cmd for cmd in self.queue.queue if cmd.status == 'completed']
            self.assertEqual(len(completed), 5)
            self.assertFalse(self.queue.is_processing)

    def tearDown(self):
        self.app.quit()

if __name__ == '__main__':
    unittest.main()