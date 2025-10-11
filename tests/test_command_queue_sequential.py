"""
Test for Command Queue Sequential Execution

This test verifies that commands are executed one at a time, not in parallel.
"""

import pytest
import time
import logging
from unittest.mock import Mock, MagicMock, patch
from src.commander.command_queue import CommandQueue, QueuedCommand
from src.commander.models import NodeToken
from src.commander.session_manager import SessionManager


class TestCommandQueueSequential:
    """Test sequential command execution in CommandQueue"""
    
    @pytest.fixture
    def mock_session_manager(self):
        """Create a mock session manager"""
        manager = Mock(spec=SessionManager)
        mock_session = Mock()
        mock_session.is_connected = True
        mock_session.send_command = Mock(side_effect=lambda cmd: f"Response to {cmd}")
        manager.get_debugger_session.return_value = mock_session
        manager.get_or_create_session.return_value = mock_session
        return manager
    
    @pytest.fixture
    def command_queue(self, mock_session_manager):
        """Create a command queue with mocked dependencies"""
        queue = CommandQueue(session_manager=mock_session_manager)
        return queue
    
    def test_sequential_execution_order(self, command_queue):
        """Test that commands execute in order, one at a time"""
        # Track execution order and timing
        execution_log = []
        
        def track_execution(cmd):
            """Track when each command executes"""
            execution_log.append({
                'command': cmd,
                'time': time.time(),
                'active_count': command_queue.thread_pool.activeThreadCount()
            })
            time.sleep(0.1)  # Simulate command execution time
            return f"Response to {cmd}"
        
        # Setup mock session with tracking
        mock_session = command_queue.session_manager.get_debugger_session()
        mock_session.send_command = Mock(side_effect=track_execution)
        
        # Create test tokens
        tokens = [
            NodeToken(token_id=f"TOKEN{i}", token_type="FBC", name="TestNode", ip_address="192.168.1.1")
            for i in range(3)
        ]
        
        # Add commands to queue
        for i, token in enumerate(tokens):
            command_queue.add_command(f"command{i}", token)
        
        # Wait for all commands to complete
        max_wait = 5  # 5 seconds timeout
        start_time = time.time()
        while command_queue.is_processing and (time.time() - start_time) < max_wait:
            time.sleep(0.1)
        
        # Verify sequential execution
        assert len(execution_log) == 3, f"Expected 3 commands executed, got {len(execution_log)}"
        
        # Verify commands executed in order
        for i in range(3):
            assert execution_log[i]['command'] == f"command{i}", \
                f"Command {i} executed out of order: {execution_log[i]['command']}"
        
        # Verify no parallel execution (active_count should be <= 1)
        for entry in execution_log:
            assert entry['active_count'] <= 1, \
                f"Parallel execution detected: {entry['active_count']} threads active for {entry['command']}"
        
        logging.info(f"Sequential execution verified: {len(execution_log)} commands in order")
    
    def test_next_command_starts_after_previous_completes(self, command_queue):
        """Test that next command only starts after previous completes"""
        completion_times = {}
        start_times = {}
        
        def track_timing(cmd):
            """Track start and completion times"""
            start_times[cmd] = time.time()
            time.sleep(0.15)  # Simulate command execution
            completion_times[cmd] = time.time()
            return f"Response to {cmd}"
        
        # Setup mock session
        mock_session = command_queue.session_manager.get_debugger_session()
        mock_session.send_command = Mock(side_effect=track_timing)
        
        # Create test tokens
        tokens = [
            NodeToken(token_id=f"TOKEN{i}", token_type="FBC", name="TestNode", ip_address="192.168.1.1")
            for i in range(3)
        ]
        
        # Add commands
        for i, token in enumerate(tokens):
            command_queue.add_command(f"cmd{i}", token)
        
        # Wait for completion
        max_wait = 5
        start_time = time.time()
        while command_queue.is_processing and (time.time() - start_time) < max_wait:
            time.sleep(0.1)
        
        # Verify timing: each command should start after previous completes
        assert len(start_times) == 3, f"Expected 3 commands started, got {len(start_times)}"
        assert len(completion_times) == 3, f"Expected 3 commands completed, got {len(completion_times)}"
        
        # Check that cmd1 starts after cmd0 completes
        if 'cmd0' in completion_times and 'cmd1' in start_times:
            assert start_times['cmd1'] >= completion_times['cmd0'], \
                "Command 1 started before Command 0 completed (parallel execution)"
        
        # Check that cmd2 starts after cmd1 completes
        if 'cmd1' in completion_times and 'cmd2' in start_times:
            assert start_times['cmd2'] >= completion_times['cmd1'], \
                "Command 2 started before Command 1 completed (parallel execution)"
        
        logging.info("Sequential timing verified: commands execute one after another")
    
    def test_failed_command_triggers_next(self, command_queue):
        """Test that a failed command still triggers the next command"""
        execution_order = []
        
        def command_with_simulated_error(cmd):
            """First command returns error, others succeed"""
            execution_order.append(cmd)
            time.sleep(0.05)  # Small delay to simulate execution
            if cmd == "failing_cmd":
                # Return error response (will be detected by error_detection.py)
                return "ERROR: Command execution failed"
            return f"Success: {cmd}"
        
        # Setup mock session
        mock_session = command_queue.session_manager.get_debugger_session()
        mock_session.send_command = Mock(side_effect=command_with_simulated_error)
        
        # Create tokens
        tokens = [
            NodeToken(token_id=f"TOKEN{i}", token_type="FBC", name="TestNode", ip_address="192.168.1.1")
            for i in range(3)
        ]
        
        # Add commands (first will return error)
        command_queue.add_command("failing_cmd", tokens[0])
        command_queue.add_command("success_cmd1", tokens[1])
        command_queue.add_command("success_cmd2", tokens[2])
        
        # Wait for completion
        max_wait = 5
        start_time = time.time()
        while command_queue.is_processing and (time.time() - start_time) < max_wait:
            time.sleep(0.1)
        
        # Give a bit more time for final command to complete
        time.sleep(0.2)
        
        # Verify all commands attempted (including after error)
        assert len(execution_order) == 3, \
            f"Expected 3 commands executed after error, got {len(execution_order)}: {execution_order}"
        
        # Verify failing command was first
        assert execution_order[0] == "failing_cmd", \
            f"First command should be failing_cmd, got {execution_order[0]}"
        
        # Verify subsequent commands executed
        assert execution_order[1] == "success_cmd1", \
            f"Second command should be success_cmd1, got {execution_order[1]}"
        assert execution_order[2] == "success_cmd2", \
            f"Third command should be success_cmd2, got {execution_order[2]}"
        
        logging.info(f"Error handling verified: {len(execution_order)} commands executed, first returned error")


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    pytest.main([__file__, "-v", "-s"])
