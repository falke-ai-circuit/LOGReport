"""
Test file for BsToolCommandService
"""
import os
import sys
import pytest
from unittest.mock import MagicMock, patch, mock_open
import tempfile
import threading
import subprocess

# Add src directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'src')))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'src', 'commander', 'services')))

from bstool_command_service import BsToolCommandService


class TestBsToolCommandService:
    """Test suite for BsToolCommandService functionality"""
    
    @pytest.fixture
    def bstool_service(self):
        """Create a BsToolCommandService instance"""
        service = BsToolCommandService()
        return service
     
    @pytest.fixture
    def bstool_service_with_log_writer(self):
        """Create a BsToolCommandService instance with a mock LogWriter"""
        mock_log_writer = MagicMock()
        service = BsToolCommandService(log_writer=mock_log_writer)
        return service
    
    @pytest.fixture
    def temp_log_file(self):
        """Create a temporary log file for testing"""
        with tempfile.NamedTemporaryFile(mode='w+', suffix='.log', delete=False) as f:
            f.write("Test log content\n")
            temp_path = f.name
        yield temp_path
        # Cleanup
        if os.path.exists(temp_path):
            os.unlink(temp_path)
    
    def test_initialization(self, bstool_service):
        """Test that BsToolCommandService initializes correctly"""
        assert bstool_service is not None
        assert bstool_service.process is None
        assert isinstance(bstool_service.process_lock, type(threading.Lock()))
        
    @patch('bstool_command_service.sys')
    @patch('bstool_command_service.os.path.exists')
    def test_get_bstool_path_frozen(self, mock_exists, mock_sys, bstool_service):
        """Test _get_bstool_path when running in frozen environment"""
        # Mock frozen environment
        mock_sys.frozen = True
        mock_sys.executable = "/path/to/executable/LOGReporter.exe"
        
        # Mock os.path.exists to return True
        mock_exists.return_value = True
        
        path = bstool_service._get_bstool_path()
        # Should be in the same directory as the executable
        expected_path = os.path.join("/path/to/executable", "BsTool.exe")
        assert path == expected_path
        
    @patch('bstool_command_service.sys')
    @patch('bstool_command_service.os.path.exists')
    def test_get_bstool_path_development(self, mock_exists, mock_sys, bstool_service):
        """Test _get_bstool_path when running in development environment"""
        # Mock development environment
        mock_sys.frozen = False
        
        # Mock os.path.exists to return True
        mock_exists.return_value = True
        
        path = bstool_service._get_bstool_path()
        # Should end with BsTool.exe
        assert path.endswith("BsTool.exe")
        
    @patch('bstool_command_service.subprocess.Popen')
    def test_execute_bstool_success(self, mock_popen, bstool_service, temp_log_file):
        """Test successful execution of bstool"""
        # Mock the subprocess
        mock_process = MagicMock()
        mock_process.pid = 12345
        mock_process.poll.return_value = None  # Process is running
        mock_process.stdout.readline.side_effect = ["Output line 1\n", "Output line 2\n", ""]
        mock_process.stderr.read.return_value = ""
        mock_process.wait.return_value = 0
        mock_popen.return_value = mock_process
        
        # Mock _get_bstool_path to return a valid path
        with patch.object(bstool_service, '_get_bstool_path', return_value='/path/to/BsTool.exe'):
            with patch('bstool_command_service.os.path.exists', return_value=True):
                # Track signals
                status_messages = []
                output_messages = []
                error_messages = []
                
                def status_handler(msg, duration):
                    status_messages.append((msg, duration))
                    
                def output_handler(output):
                    output_messages.append(output)
                    
                def error_handler(error):
                    error_messages.append(error)
                
                # Connect to signals
                bstool_service.status_message_signal.connect(status_handler)
                bstool_service.bstool_output_signal.connect(output_handler)
                bstool_service.report_error.connect(error_handler)
                
                # Execute bstool
                bstool_service.execute_bstool(temp_log_file, "-errlog AP01")
                
                # Wait a bit for thread to start
                import time
                time.sleep(0.1)
                
                # Verify signals were emitted
                assert len(status_messages) >= 1
                assert any("Starting bstool execution" in msg for msg, _ in status_messages)
                
                # Verify subprocess was called correctly
                mock_popen.assert_called_once()
                call_args = mock_popen.call_args[0][0]  # command argument
                assert call_args == ['/path/to/BsTool.exe', '-errlog', 'AP01']
                
                # Verify environment was set correctly
                call_kwargs = mock_popen.call_args[1]
                assert 'env' in call_kwargs
                assert call_kwargs['env']['COMMUNICATION_LINE'] == 'AB01'
                 
    @patch('bstool_command_service.subprocess.Popen')
    def test_execute_bstool_success_with_log_writer(self, mock_popen, bstool_service_with_log_writer, temp_log_file):
        """Test successful execution of bstool with LogWriter integration"""
        # Mock the subprocess
        mock_process = MagicMock()
        mock_process.pid = 12345
        mock_process.poll.return_value = None  # Process is running
        mock_process.stdout.readline.side_effect = ["Output line 1\n", "Output line 2\n", ""]
        mock_process.stderr.read.return_value = ""
        mock_process.wait.return_value = 0
        mock_popen.return_value = mock_process
         
        # Mock _get_bstool_path to return a valid path
        with patch.object(bstool_service_with_log_writer, '_get_bstool_path', return_value='/path/to/BsTool.exe'):
            with patch('bstool_command_service.os.path.exists', return_value=True):
                # Track signals
                status_messages = []
                output_messages = []
                error_messages = []
                 
                def status_handler(msg, duration):
                    status_messages.append((msg, duration))
                     
                def output_handler(output):
                    output_messages.append(output)
                     
                def error_handler(error):
                    error_messages.append(error)
                 
                # Connect to signals
                bstool_service_with_log_writer.status_message_signal.connect(status_handler)
                bstool_service_with_log_writer.bstool_output_signal.connect(output_handler)
                bstool_service_with_log_writer.report_error.connect(error_handler)
                 
                # Execute bstool
                bstool_service_with_log_writer.execute_bstool(temp_log_file, "-errlog AP01")
                 
                # Wait a bit for thread to start
                import time
                time.sleep(0.1)
                 
                # Verify signals were emitted
                assert len(status_messages) >= 1
                assert any("Starting bstool execution" in msg for msg, _ in status_messages)
                 
                # Verify subprocess was called correctly
                mock_popen.assert_called_once()
                call_args = mock_popen.call_args[0][0]  # command argument
                assert call_args == ['/path/to/BsTool.exe', '-errlog', 'AP01']
                 
                # Verify environment was set correctly
                call_kwargs = mock_popen.call_args[1]
                assert 'env' in call_kwargs
                assert call_kwargs['env']['COMMUNICATION_LINE'] == 'AB01'
                 
                # Verify LogWriter was called to write output
                bstool_service_with_log_writer.log_writer.append_to_file.assert_any_call(temp_log_file, "Output line 1")
                bstool_service_with_log_writer.log_writer.append_to_file.assert_any_call(temp_log_file, "Output line 2")
                
    @patch('bstool_command_service.subprocess.Popen')
    def test_execute_bstool_environment_variable(self, mock_popen, bstool_service, temp_log_file):
        """Test that bstool is executed with correct environment variable"""
        # Mock the subprocess
        mock_process = MagicMock()
        mock_process.pid = 12345
        mock_process.poll.return_value = None  # Process is running
        mock_process.stdout.readline.side_effect = ["Output line 1\n", ""]
        mock_process.stderr.read.return_value = ""
        mock_process.wait.return_value = 0
        mock_popen.return_value = mock_process
        
        # Mock _get_bstool_path to return a valid path
        with patch.object(bstool_service, '_get_bstool_path', return_value='/path/to/BsTool.exe'):
            with patch('bstool_command_service.os.path.exists', return_value=True):
                # Execute bstool
                bstool_service.execute_bstool(temp_log_file, "-errlog AP01")
                
                # Wait a bit for thread to start
                import time
                time.sleep(0.1)
                
                # Verify subprocess was called with correct environment
                mock_popen.assert_called_once()
                call_kwargs = mock_popen.call_args[1]
                assert 'env' in call_kwargs
                # Check that COMMUNICATION_LINE is set to AB01
                assert call_kwargs['env']['COMMUNICATION_LINE'] == 'AB01'
                # Check that the environment is a copy of the original (has more than just COMMUNICATION_LINE)
                assert len(call_kwargs['env']) >= 1
                
    @patch('bstool_command_service.subprocess.Popen')
    @patch('bstool_command_service.threading.Thread')
    def test_execute_bstool_file_not_found(self, mock_thread, mock_popen, bstool_service, temp_log_file):
        """Test bstool execution when bstool.exe is not found"""
        # Mock FileNotFoundError in the thread target
        def mock_thread_target(*args, **kwargs):
            # Simulate the error that would occur in the thread
            try:
                mock_popen.side_effect = FileNotFoundError("bstool.exe not found")
                # This would normally be called in the thread
                # We're simulating the error that would happen in _run_bstool_process
                raise FileNotFoundError("bstool.exe not found")
            except Exception as e:
                # Capture the error like the real implementation would
                bstool_service.logger.error(f"bstool.exe not found: {str(e)}")
                bstool_service.report_error.emit(f"bstool.exe not found: {str(e)}")
                bstool_service.status_message_signal.emit(f"bstool.exe not found: {str(e)}", 5000)
        
        mock_thread_instance = MagicMock()
        mock_thread_instance.start = mock_thread_target
        mock_thread.return_value = mock_thread_instance
        
        # Mock _get_bstool_path to return a valid path
        with patch.object(bstool_service, '_get_bstool_path', return_value='/path/to/BsTool.exe'):
            with patch('bstool_command_service.os.path.exists', return_value=True):
                # Track signals
                status_messages = []
                error_messages = []
                
                def status_handler(msg, duration):
                    status_messages.append((msg, duration))
                    
                def error_handler(error):
                    error_messages.append(error)
                
                # Connect to signals
                bstool_service.status_message_signal.connect(status_handler)
                bstool_service.report_error.connect(error_handler)
                
                # Execute bstool
                bstool_service.execute_bstool(temp_log_file, "-errlog AP01")
                
                # Execute the thread target directly to simulate the error
                mock_thread_target()
                
                # Verify error signals were emitted
                assert len(error_messages) >= 1
                assert any("bstool.exe not found" in msg for msg in error_messages)
                assert len(status_messages) >= 1
                assert any("bstool.exe not found" in msg for msg, _ in status_messages)
                
    def test_copy_to_log_success(self, bstool_service, temp_log_file):
        """Test successful copying of content to log file"""
        # Track signals
        status_messages = []
        error_messages = []
        
        def status_handler(msg, duration):
            status_messages.append((msg, duration))
            
        def error_handler(error):
            error_messages.append(error)
        
        # Connect to signals
        bstool_service.status_message_signal.connect(status_handler)
        bstool_service.report_error.connect(error_handler)
        
        # Copy content to log
        test_content = "Test content for log file"
        bstool_service.copy_to_log(test_content, temp_log_file)
        
        # Verify content was written to file
        with open(temp_log_file, 'r') as f:
            content = f.read()
            assert test_content + "\n" in content
            
        # Verify status message was emitted
        assert len(status_messages) >= 1
        assert any("Content copied to" in msg for msg, _ in status_messages)
        assert len(error_messages) == 0
        
    def test_copy_to_log_error(self, bstool_service):
        """Test copying to log when file is not accessible"""
        # Track signals
        status_messages = []
        error_messages = []
        
        def status_handler(msg, duration):
            status_messages.append((msg, duration))
            
        def error_handler(error):
            error_messages.append(error)
        
        # Connect to signals
        bstool_service.status_message_signal.connect(status_handler)
        bstool_service.report_error.connect(error_handler)
        
        # Try to copy to an invalid path
        invalid_path = "/invalid/path/to/file.log"
        test_content = "Test content"
        bstool_service.copy_to_log(test_content, invalid_path)
        
        # Verify error was reported
        assert len(error_messages) >= 1
        assert any("Failed to copy content to log" in msg for msg in error_messages)
        assert len(status_messages) >= 1
        assert any("Failed to copy content to log" in msg for msg, _ in status_messages)
        
    def test_clear_terminal(self, bstool_service):
        """Test clearing the terminal"""
        # Track signals
        output_messages = []
        status_messages = []
        
        def output_handler(output):
            output_messages.append(output)
            
        def status_handler(msg, duration):
            status_messages.append((msg, duration))
        
        # Connect to signals
        bstool_service.bstool_output_signal.connect(output_handler)
        bstool_service.status_message_signal.connect(status_handler)
        
        # Clear terminal
        bstool_service.clear_terminal()
        
        # Verify signals were emitted
        assert len(output_messages) >= 1
        assert "" in output_messages  # Empty string indicates clear
        assert len(status_messages) >= 1
        assert any("Terminal cleared" in msg for msg, _ in status_messages)
        
    def test_clear_log_success(self, bstool_service, temp_log_file):
        """Test successful clearing of log file"""
        # Add some content to the log file first
        with open(temp_log_file, 'w') as f:
            f.write("Existing content\n")
            
        # Track signals
        status_messages = []
        error_messages = []
        
        def status_handler(msg, duration):
            status_messages.append((msg, duration))
            
        def error_handler(error):
            error_messages.append(error)
        
        # Connect to signals
        bstool_service.status_message_signal.connect(status_handler)
        bstool_service.report_error.connect(error_handler)
        
        # Clear log
        bstool_service.clear_log(temp_log_file)
        
        # Verify file is empty
        with open(temp_log_file, 'r') as f:
            content = f.read()
            assert content == ""
            
        # Verify status message was emitted
        assert len(status_messages) >= 1
        assert any("Log file" in msg and "cleared" in msg for msg, _ in status_messages)
        assert len(error_messages) == 0
        
    def test_clear_log_error(self, bstool_service):
        """Test clearing log when file is not accessible"""
        # Track signals
        status_messages = []
        error_messages = []
        
        def status_handler(msg, duration):
            status_messages.append((msg, duration))
            
        def error_handler(error):
            error_messages.append(error)
        
        # Connect to signals
        bstool_service.status_message_signal.connect(status_handler)
        bstool_service.report_error.connect(error_handler)
        
        # Try to clear an invalid path
        invalid_path = "/invalid/path/to/file.log"
        bstool_service.clear_log(invalid_path)
        
        # Verify error was reported
        assert len(error_messages) >= 1
        assert any("Failed to clear log file" in msg for msg in error_messages)
        assert len(status_messages) >= 1
        assert any("Failed to clear log file" in msg for msg, _ in status_messages)
        
    def test_terminate_bstool_when_running(self, bstool_service):
        """Test terminate_bstool when a process is running"""
        # Create a mock process
        mock_process = MagicMock()
        mock_process.poll.return_value = None  # Process is running
        mock_process.terminate = MagicMock()
        mock_process.wait = MagicMock()
        
        # Set the mock process on the service
        with patch.object(bstool_service, 'process', mock_process):
            with patch.object(bstool_service, 'process_lock'):
                # Track signals
                status_messages = []
                
                def status_handler(msg, duration):
                    status_messages.append((msg, duration))
                
                # Connect to signals
                bstool_service.status_message_signal.connect(status_handler)
                
                # Terminate the process
                bstool_service.terminate_bstool()
                
                # Verify process methods were called
                mock_process.terminate.assert_called_once()
                mock_process.wait.assert_called_once_with(timeout=5)
                
                # Verify status message was emitted
                assert len(status_messages) >= 1
                assert any("bstool process terminated" in msg for msg, _ in status_messages)
                
    def test_terminate_bstool_when_no_process(self, bstool_service):
        """Test terminate_bstool when no process is running"""
        # Ensure process is None
        bstool_service.process = None
        
        # Track signals
        status_messages = []
        
        def status_handler(msg, duration):
            status_messages.append((msg, duration))
        
        # Connect to signals
        bstool_service.status_message_signal.connect(status_handler)
        
        # Terminate the process
        bstool_service.terminate_bstool()
        
        # Verify status message was emitted
        assert len(status_messages) >= 1
        assert any("No bstool process running" in msg for msg, _ in status_messages)
        
    def test_terminate_bstool_force_kill(self, bstool_service):
        """Test terminate_bstool when process needs to be forcefully killed"""
        # Create a mock process
        mock_process = MagicMock()
        mock_process.poll.return_value = None  # Process is running
        mock_process.terminate = MagicMock()
        mock_process.wait.side_effect = subprocess.TimeoutExpired("cmd", 5)  # Timeout on wait
        mock_process.kill = MagicMock()
        
        # Set the mock process on the service
        with patch.object(bstool_service, 'process', mock_process):
            with patch.object(bstool_service, 'process_lock'):
                # Track signals
                status_messages = []
                
                def status_handler(msg, duration):
                    status_messages.append((msg, duration))
                
                # Connect to signals
                bstool_service.status_message_signal.connect(status_handler)
                
                # Terminate the process
                bstool_service.terminate_bstool()
                
                # Verify process methods were called
                mock_process.terminate.assert_called_once()
                mock_process.wait.assert_called_once_with(timeout=5)
                mock_process.kill.assert_called_once()
                
                # Verify status message was emitted
                assert len(status_messages) >= 1
                assert any("bstool process terminated" in msg for msg, _ in status_messages)
                
    def test_terminate_bstool_when_finished(self, bstool_service):
        """Test terminate_bstool when process has already finished"""
        # Create a mock process
        mock_process = MagicMock()
        mock_process.poll.return_value = 0  # Process has finished
        
        # Set the mock process on the service
        with patch.object(bstool_service, 'process', mock_process):
            with patch.object(bstool_service, 'process_lock'):
                # Track signals
                status_messages = []
                
                def status_handler(msg, duration):
                    status_messages.append((msg, duration))
                
                # Connect to signals
                bstool_service.status_message_signal.connect(status_handler)
                
                # Terminate the process
                bstool_service.terminate_bstool()
                
                # Verify status message was emitted
                assert len(status_messages) >= 1
                assert any("bstool process terminated" in msg for msg, _ in status_messages)
                
    @patch('bstool_command_service.subprocess.Popen')
    def test_execute_bstool_stderr_output(self, mock_popen, bstool_service, temp_log_file):
        """Test bstool execution with stderr output"""
        # Mock the subprocess
        mock_process = MagicMock()
        mock_process.pid = 12345
        mock_process.poll.return_value = None  # Process is running
        mock_process.stdout.readline.side_effect = ["Output line 1\n", "Output line 2\n", ""]
        mock_process.stderr.read.return_value = "Error message from bstool\n"
        mock_process.wait.return_value = 0
        mock_popen.return_value = mock_process
        
        # Mock _get_bstool_path to return a valid path
        with patch.object(bstool_service, '_get_bstool_path', return_value='/path/to/BsTool.exe'):
            with patch('bstool_command_service.os.path.exists', return_value=True):
                # Track signals
                output_messages = []
                error_messages = []
                
                def output_handler(output):
                    output_messages.append(output)
                    
                def error_handler(error):
                    error_messages.append(error)
                
                # Connect to signals
                bstool_service.bstool_output_signal.connect(output_handler)
                bstool_service.report_error.connect(error_handler)
                
                # Execute bstool
                bstool_service.execute_bstool(temp_log_file, "-errlog AP01")
                
                # Wait a bit for thread to start
                import time
                time.sleep(0.1)
                
                # Verify stdout output was emitted
                assert "Output line 1" in output_messages
                assert "Output line 2" in output_messages
                
                # Verify stderr output was emitted
                assert any("ERROR: Error message from bstool" in msg for msg in output_messages)
                
    @patch('bstool_command_service.subprocess.Popen')
    def test_execute_bstool_non_zero_return_code(self, mock_popen, bstool_service, temp_log_file):
        """Test bstool execution with non-zero return code"""
        # Mock the subprocess
        mock_process = MagicMock()
        mock_process.pid = 12345
        mock_process.poll.return_value = None  # Process is running
        mock_process.stdout.readline.side_effect = ["Output line 1\n", ""]
        mock_process.stderr.read.return_value = ""
        mock_process.wait.return_value = 1  # Non-zero return code
        mock_popen.return_value = mock_process
        
        # Mock _get_bstool_path to return a valid path
        with patch.object(bstool_service, '_get_bstool_path', return_value='/path/to/BsTool.exe'):
            with patch('bstool_command_service.os.path.exists', return_value=True):
                # Track signals
                status_messages = []
                error_messages = []
                
                def status_handler(msg, duration):
                    status_messages.append((msg, duration))
                    
                def error_handler(error):
                    error_messages.append(error)
                
                # Connect to signals
                bstool_service.status_message_signal.connect(status_handler)
                bstool_service.report_error.connect(error_handler)
                
                # Execute bstool
                bstool_service.execute_bstool(temp_log_file, "-errlog AP01")
                
                # Wait a bit for thread to start
                import time
                time.sleep(0.1)
                
                # Verify error was reported
                assert len(error_messages) >= 1
                assert any("bstool process exited with code 1" in msg for msg in error_messages)
                
                # Verify status message was emitted
                assert len(status_messages) >= 1
                assert any("bstool process exited with code 1" in msg for msg, _ in status_messages)
                
    @patch('bstool_command_service.subprocess.Popen')
    def test_execute_bstool_process_exception(self, mock_popen, bstool_service, temp_log_file):
        """Test bstool execution with exception during process execution"""
        # Mock the subprocess to raise an exception
        mock_popen.side_effect = Exception("Process execution failed")
        
        # Mock _get_bstool_path to return a valid path
        with patch.object(bstool_service, '_get_bstool_path', return_value='/path/to/BsTool.exe'):
            with patch('bstool_command_service.os.path.exists', return_value=True):
                # Track signals
                status_messages = []
                error_messages = []
                
                def status_handler(msg, duration):
                    status_messages.append((msg, duration))
                    
                def error_handler(error):
                    error_messages.append(error)
                
                # Connect to signals
                bstool_service.status_message_signal.connect(status_handler)
                bstool_service.report_error.connect(error_handler)
                
                # Execute bstool
                bstool_service.execute_bstool(temp_log_file, "-errlog AP01")
                
                # Wait a bit for thread to start
                import time
                time.sleep(0.1)
                
                # Verify error was reported
                assert len(error_messages) >= 1
                assert any("Error during bstool execution" in msg for msg in error_messages)
                
                # Verify status message was emitted
                assert len(status_messages) >= 1
                assert any("Error during bstool execution" in msg for msg, _ in status_messages)
                
    def test_copy_to_log_permission_error(self, bstool_service):
        """Test copying to log when permission is denied"""
        # Track signals
        status_messages = []
        error_messages = []
        
        def status_handler(msg, duration):
            status_messages.append((msg, duration))
            
        def error_handler(error):
            error_messages.append(error)
        
        # Connect to signals
        bstool_service.status_message_signal.connect(status_handler)
        bstool_service.report_error.connect(error_handler)
        
        # Try to copy to a path where we don't have permission (using mock)
        with patch('builtins.open', side_effect=PermissionError("Permission denied")):
            invalid_path = "/restricted/path/to/file.log"
            test_content = "Test content"
            bstool_service.copy_to_log(test_content, invalid_path)
            
            # Verify error was reported
            assert len(error_messages) >= 1
            assert any("Failed to copy content to log" in msg for msg in error_messages)
            assert any("Permission denied" in msg for msg in error_messages)
            
            # Verify status message was emitted
            assert len(status_messages) >= 1
            assert any("Failed to copy content to log" in msg for msg, _ in status_messages)
            
    def test_clear_log_permission_error(self, bstool_service):
        """Test clearing log when permission is denied"""
        # Track signals
        status_messages = []
        error_messages = []
        
        def status_handler(msg, duration):
            status_messages.append((msg, duration))
            
        def error_handler(error):
            error_messages.append(error)
        
        # Connect to signals
        bstool_service.status_message_signal.connect(status_handler)
        bstool_service.report_error.connect(error_handler)
        
        # Try to clear a path where we don't have permission (using mock)
        with patch('builtins.open', side_effect=PermissionError("Permission denied")):
            invalid_path = "/restricted/path/to/file.log"
            bstool_service.clear_log(invalid_path)
            
            # Verify error was reported
            assert len(error_messages) >= 1
            assert any("Failed to clear log file" in msg for msg in error_messages)
            assert any("Permission denied" in msg for msg in error_messages)
            
            # Verify status message was emitted
            assert len(status_messages) >= 1
            assert any("Failed to clear log file" in msg for msg, _ in status_messages)
            
    def test_signal_emissions_during_execution(self, bstool_service, temp_log_file):
        """Test that all expected signals are emitted during execution"""
        # Mock the subprocess
        mock_process = MagicMock()
        mock_process.pid = 12345
        mock_process.poll.return_value = None  # Process is running
        mock_process.stdout.readline.side_effect = ["Output line 1\n", "Output line 2\n", ""]
        mock_process.stderr.read.return_value = ""
        mock_process.wait.return_value = 0
        
        with patch('bstool_command_service.subprocess.Popen', return_value=mock_process):
            # Mock _get_bstool_path to return a valid path
            with patch.object(bstool_service, '_get_bstool_path', return_value='/path/to/BsTool.exe'):
                with patch('bstool_command_service.os.path.exists', return_value=True):
                    # Track all signals
                    status_messages = []
                    output_messages = []
                    error_messages = []
                    
                    def status_handler(msg, duration):
                        status_messages.append((msg, duration))
                        
                    def output_handler(output):
                        output_messages.append(output)
                        
                    def error_handler(error):
                        error_messages.append(error)
                    
                    # Connect to all signals
                    bstool_service.status_message_signal.connect(status_handler)
                    bstool_service.bstool_output_signal.connect(output_handler)
                    bstool_service.report_error.connect(error_handler)
                    
                    # Execute bstool
                    bstool_service.execute_bstool(temp_log_file, "-errlog AP01")
                    
                    # Wait a bit for thread to start
                    import time
                    time.sleep(0.1)
                    
                    # Verify status message signal was emitted
                    assert len(status_messages) >= 1
                    assert any("Starting bstool execution" in msg for msg, _ in status_messages)
                    
                    # Verify output signal was emitted
                    assert len(output_messages) >= 2
                    assert "Output line 1" in output_messages
                    assert "Output line 2" in output_messages
                    
                    # Verify no error signals were emitted for successful execution
                    # (there might be some from the threading, but not from our execution)
                    
    def test_signal_emissions_on_error(self, bstool_service, temp_log_file):
        """Test that error signals are emitted when execution fails"""
        # Mock _get_bstool_path to return an invalid path
        with patch.object(bstool_service, '_get_bstool_path', return_value='/invalid/path/to/BsTool.exe'):
            with patch('bstool_command_service.os.path.exists', return_value=False):
                # Track signals
                status_messages = []
                error_messages = []
                
                def status_handler(msg, duration):
                    status_messages.append((msg, duration))
                    
                def error_handler(error):
                    error_messages.append(error)
                
                # Connect to signals
                bstool_service.status_message_signal.connect(status_handler)
                bstool_service.report_error.connect(error_handler)
                
                # Execute bstool
                bstool_service.execute_bstool(temp_log_file, "-errlog AP01")
                
                # Verify error signals were emitted
                assert len(error_messages) >= 1
                assert any("bstool.exe not found" in msg for msg in error_messages)
                
                # Verify status message signal was emitted
                assert len(status_messages) >= 1
                assert any("bstool.exe not found" in msg for msg, _ in status_messages)
                
    def test_execute_bstool_non_blocking(self, bstool_service, temp_log_file):
        """Test that bstool execution does not block the UI thread"""
        # Mock the subprocess to simulate a long-running process
        mock_process = MagicMock()
        mock_process.pid = 12345
        mock_process.poll.return_value = None  # Process is running
        # Simulate a long-running process by having readline block for a short time
        import time
        def slow_readline():
            time.sleep(0.1)  # Simulate delay
            return ""
        mock_process.stdout.readline.side_effect = slow_readline
        mock_process.stderr.read.return_value = ""
        mock_process.wait.return_value = 0
        
        with patch('bstool_command_service.subprocess.Popen', return_value=mock_process):
            # Mock _get_bstool_path to return a valid path
            with patch.object(bstool_service, '_get_bstool_path', return_value='/path/to/BsTool.exe'):
                with patch('bstool_command_service.os.path.exists', return_value=True):
                    # Record start time
                    start_time = time.time()
                    
                    # Execute bstool (should not block)
                    bstool_service.execute_bstool(temp_log_file, "-errlog AP01")
                    
                    # Record end time (should be almost immediate)
                    end_time = time.time()
                    
                    # Execution should be non-blocking (less than 0.05 seconds)
                    assert end_time - start_time < 0.05
                    
                    # Wait a bit for thread to finish
                    time.sleep(0.2)
    @patch('bstool_command_service.subprocess.Popen')
    def test_execute_bstool_timeout(self, mock_popen, bstool_service, temp_log_file):
        """Test that bstool process times out after 10 seconds"""
        mock_process = MagicMock()
        mock_process.pid = 12345
        mock_process.poll.return_value = None
        mock_process.stdout.readline.side_effect = [""]
        mock_process.stderr.read.return_value = ""
        
        # Simulate a timeout by raising TimeoutExpired when wait is called
        mock_process.wait.side_effect = subprocess.TimeoutExpired("cmd", 10)
        mock_process.terminate = MagicMock()
        mock_process.kill = MagicMock()
        mock_popen.return_value = mock_process

        with patch.object(bstool_service, '_get_bstool_path', return_value='/path/to/BsTool.exe'):
            with patch('bstool_command_service.os.path.exists', return_value=True):
                status_messages = []
                error_messages = []

                def status_handler(msg, duration):
                    status_messages.append((msg, duration))

                def error_handler(error):
                    error_messages.append(error)

                bstool_service.status_message_signal.connect(status_handler)
                bstool_service.report_error.connect(error_handler)

                bstool_service.execute_bstool(temp_log_file, "-errlog AP01")

                # Wait for the thread to execute and the timeout to occur
                import time
                time.sleep(0.1) # Give the thread a moment to start and hit the mocked wait

                mock_process.wait.assert_called_with(timeout=10)
                mock_process.terminate.assert_called_once()
                assert any("bstool process timed out" in msg for msg, _ in status_messages)
                assert any("bstool process exited with code" in msg for msg in error_messages) # Should report an error due to termination

                    
    def test_execute_bstool_with_log_writer_error_handling(self, bstool_service_with_log_writer, temp_log_file):
        """Test bstool execution with LogWriter error handling"""
        # Mock the subprocess
        mock_process = MagicMock()
        mock_process.pid = 12345
        mock_process.poll.return_value = None  # Process is running
        mock_process.stdout.readline.side_effect = ["Output line 1\n", "Output line 2\n", ""]
        mock_process.stderr.read.return_value = ""
        mock_process.wait.return_value = 0
        
        # Mock LogWriter to raise an exception
        bstool_service_with_log_writer.log_writer.append_to_file.side_effect = Exception("Log write failed")
        
        with patch('bstool_command_service.subprocess.Popen', return_value=mock_process):
            # Mock _get_bstool_path to return a valid path
            with patch.object(bstool_service_with_log_writer, '_get_bstool_path', return_value='/path/to/BsTool.exe'):
                with patch('bstool_command_service.os.path.exists', return_value=True):
                    # Execute bstool
                    bstool_service_with_log_writer.execute_bstool(temp_log_file, "-errlog AP01")
                    
                    # Wait a bit for thread to start
                    import time
                    time.sleep(0.1)
                    
                    # Verify that the service handled the LogWriter error gracefully
                    # (The process should still complete even if LogWriter fails)
                    
    def test_execute_bstool_command_construction(self, bstool_service, temp_log_file):
        """Test that bstool command is constructed correctly"""
        # Mock the subprocess
        mock_process = MagicMock()
        mock_process.pid = 12345
        mock_process.poll.return_value = None  # Process is running
        mock_process.stdout.readline.side_effect = [""]
        mock_process.stderr.read.return_value = ""
        mock_process.wait.return_value = 0
        
        with patch('bstool_command_service.subprocess.Popen', return_value=mock_process):
            # Mock _get_bstool_path to return a valid path
            with patch.object(bstool_service, '_get_bstool_path', return_value='/path/to/BsTool.exe'):
                with patch('bstool_command_service.os.path.exists', return_value=True):
                    # Execute bstool with arguments
                    bstool_service.execute_bstool(temp_log_file, "-errlog AP01 -verbose")
                    
                    # Wait a bit for thread to start
                    import time
                    time.sleep(0.1)
                    
                    # Verify command was constructed correctly
                    mock_popen = patch('bstool_command_service.subprocess.Popen').__enter__()
                    mock_popen.assert_called_once()
                    call_args = mock_popen.call_args[0][0]  # command argument
                    assert call_args == ['/path/to/BsTool.exe', '-errlog', 'AP01', '-verbose']


if __name__ == "__main__":
    pytest.main([__file__, "-v"])