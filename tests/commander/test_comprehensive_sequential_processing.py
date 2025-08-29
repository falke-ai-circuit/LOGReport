import pytest
from unittest.mock import MagicMock, patch
from src.commander.services.sequential_command_processor import SequentialCommandProcessor
from src.commander.command_queue import CommandQueue
from src.commander.contracts import Command, CommandType, CommandStatus
import time

@pytest.fixture
def processor():
    queue = CommandQueue()
    return SequentialCommandProcessor(queue)

class TestSequentialProcessing:
    """Comprehensive tests for FBC token 162 sequential command execution"""
    
    # Delay functionality tests
    def test_zero_delay_execution(self, processor):
        """Verify immediate execution with 0ms delay"""
        cmd = Command(
            type=CommandType.FBC,
            token="162",
            payload="TEST",
            delay_ms=0
        )
        processor.queue.add(cmd)
        
        start_time = time.time()
        processor.process_next()
        elapsed = time.time() - start_time
        
        assert elapsed < 0.01  # Should execute immediately
        assert cmd.status == CommandStatus.COMPLETED

    def test_100ms_delay_execution(self, processor):
        """Verify proper 100ms delay execution"""
        cmd = Command(
            type=CommandType.FBC,
            token="162",
            payload="TEST",
            delay_ms=100
        )
        processor.queue.add(cmd)
        
        start_time = time.time()
        processor.process_next()
        elapsed = time.time() - start_time
        
        assert 0.1 <= elapsed < 0.15
        assert cmd.status == CommandStatus.COMPLETED

    def test_500ms_delay_execution(self, processor):
        """Verify proper 500ms delay execution"""
        cmd = Command(
            type=CommandType.FBC,
            token="162",
            payload="TEST",
            delay_ms=500
        )
        processor.queue.add(cmd)
        
        start_time = time.time()
        processor.process_next()
        elapsed = time.time() - start_time
        
        assert 0.5 <= elapsed < 0.55
        assert cmd.status == CommandStatus.COMPLETED

    # Sequential execution tests
    def test_sequential_execution_order(self, processor):
        """Verify commands execute in FIFO order"""
        commands = [
            Command(CommandType.FBC, "162", "CMD1", 100),
            Command(CommandType.RPC, "163", "CMD2", 50),
            Command(CommandType.FBC, "162", "CMD3", 200)
        ]
        
        for cmd in commands:
            processor.queue.add(cmd)
            
        execution_order = []
        with patch.object(processor, '_execute_command') as mock_execute:
            mock_execute.side_effect = lambda cmd: execution_order.append(cmd.payload)
            while not processor.queue.is_empty():
                processor.process_next()
                
        assert execution_order == ["CMD1", "CMD2", "CMD3"]

    def test_queue_completion(self, processor):
        """Verify queue fully processes without getting stuck"""
        for i in range(10):
            processor.queue.add(Command(
                CommandType.FBC, 
                "162", 
                f"CMD{i}", 
                delay_ms=10
            ))
            
        processed = 0
        with patch.object(processor, '_execute_command'):
            while not processor.queue.is_empty():
                processor.process_next()
                processed += 1
                
        assert processed == 10

    # Mixed command tests
    def test_mixed_command_types(self, processor):
        """Verify FBC and RPC commands execute correctly in sequence"""
        commands = [
            Command(CommandType.FBC, "162", "FBC1", 100),
            Command(CommandType.RPC, "163", "RPC1", 50),
            Command(CommandType.FBC, "162", "FBC2", 200)
        ]
        
        results = []
        def execute_side_effect(cmd):
            results.append((cmd.type, cmd.payload))
            return True
            
        with patch.object(processor, '_execute_command', side_effect=execute_side_effect):
            for cmd in commands:
                processor.queue.add(cmd)
            while not processor.queue.is_empty():
                processor.process_next()
                
        assert results == [
            (CommandType.FBC, "FBC1"),
            (CommandType.RPC, "RPC1"),
            (CommandType.FBC, "FBC2")
        ]

    # Error condition tests
    def test_error_recovery(self, processor):
        """Verify queue continues after failed command"""
        commands = [
            Command(CommandType.FBC, "162", "GOOD1", 10),
            Command(CommandType.FBC, "INVALID", "BAD", 10),
            Command(CommandType.FBC, "162", "GOOD2", 10)
        ]
        
        def execute_side_effect(cmd):
            if "BAD" in cmd.payload:
                raise Exception("Simulated error")
            return True
            
        with patch.object(processor, '_execute_command', side_effect=execute_side_effect):
            for cmd in commands:
                processor.queue.add(cmd)
                
            processor.process_next()  # GOOD1
            with pytest.raises(Exception):
                processor.process_next()  # BAD
            processor.process_next()  # GOOD2
            
        assert commands[0].status == CommandStatus.COMPLETED
        assert commands[1].status == CommandStatus.FAILED
        assert commands[2].status == CommandStatus.COMPLETED

    def test_command_timeout(self, processor):
        """Verify timeout handling for stuck commands"""
        cmd = Command(
            CommandType.FBC,
            "162",
            "TIMEOUT_TEST",
            delay_ms=100,
            timeout_ms=50
        )
        
        processor.queue.add(cmd)
        
        with patch.object(processor, '_execute_command', side_effect=lambda x: time.sleep(0.2)):
            processor.process_next()
            
        assert cmd.status == CommandStatus.TIMEOUT

    # Edge case tests
    def test_consecutive_failures(self, processor):
        """Verify queue handles multiple consecutive failures"""
        commands = [
            Command(CommandType.FBC, "INVALID", "FAIL1", 10),
            Command(CommandType.FBC, "INVALID", "FAIL2", 10),
            Command(CommandType.FBC, "162", "SUCCESS", 10)
        ]
        
        with patch.object(processor, '_execute_command', side_effect=Exception("Failed")):
            for cmd in commands:
                processor.queue.add(cmd)
                
            processor.process_next()
            processor.process_next()
            processor.process_next()
            
        assert commands[0].status == CommandStatus.FAILED
        assert commands[1].status == CommandStatus.FAILED
        assert commands[2].status == CommandStatus.FAILED  # Should fail due to mock

    def test_empty_queue_handling(self, processor):
        """Verify graceful handling of empty queue"""
        with pytest.raises(RuntimeError, match="Queue is empty"):
            processor.process_next()