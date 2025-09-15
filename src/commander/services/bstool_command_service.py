import subprocess
import os
import sys
import logging
import threading
from PyQt6.QtCore import QObject, pyqtSignal
from .threading_service import ThreadingService


class BsToolCommandService(QObject):
    """Service for handling BsTool operations"""
    
    # Define signals for communication
    status_message_signal = pyqtSignal(str, int)  # message, duration
    bstool_output_signal = pyqtSignal(str)        # output from bstool
    report_error = pyqtSignal(str)                # error message
    
    def __init__(self, log_writer=None, parent=None):
        super().__init__(parent)
        self.process = None
        self.threading_service = ThreadingService()
        self.process_lock = self.threading_service.create_lock()
        self.log_writer = log_writer
        self.logger = logging.getLogger(__name__)
        
    def execute_bstool(self, log_file_path: str, bstool_command_args: str = ""):
        """
        Execute bstool.exe with the specified log file path and command arguments.
        
        Args:
            log_file_path (str): Path to the log file
            bstool_command_args (str): Additional command arguments for bstool
        """
        self.logger.info(f"Executing bstool with log file: {log_file_path}")
        
        # Emit status message
        self.status_message_signal.emit("Starting bstool execution...", 3000)
        
        # Get the path to bstool.exe
        bstool_path = self._get_bstool_path()
        if not bstool_path:
            error_msg = "Could not locate bstool.exe"
            self.logger.error(error_msg)
            self.report_error.emit(error_msg)
            self.status_message_signal.emit(error_msg, 5000)
            return
            
        # Verify bstool.exe exists
        if not os.path.exists(bstool_path):
            error_msg = f"bstool.exe not found at {bstool_path}"
            self.logger.error(error_msg)
            self.report_error.emit(error_msg)
            self.status_message_signal.emit(error_msg, 5000)
            return
            
        # Set up environment with fixed COMMUNICATION_LINE variable
        env = os.environ.copy()
        env["COMMUNICATION_LINE"] = "AB01"
        
        # Construct command
        command = [bstool_path]
        if bstool_command_args:
            command.extend(bstool_command_args.split())
            
        self.logger.debug(f"Executing command: {' '.join(command)}")
        
        try:
            # Start the process in a separate thread to avoid blocking UI
            self.threading_service.start_thread(
                target=self._run_bstool_process,
                args=(command, env, log_file_path),
                daemon=True
            )
            
        except Exception as e:
            error_msg = f"Failed to start bstool process: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            self.report_error.emit(error_msg)
            self.status_message_signal.emit(error_msg, 5000)
            
    def _get_bstool_path(self) -> str:
        """
        Get the path to bstool.exe, handling both development and bundled environments.
        
        Returns:
            str: Path to bstool.exe or empty string if not found
        """
        # Check if running in a bundled environment (PyInstaller)
        if getattr(sys, 'frozen', False):
            # In bundled app, bstool.exe should be in the same directory as the executable
            bstool_path = os.path.join(os.path.dirname(sys.executable), "BsTool.exe")
        else:
            # In development, bstool.exe should be in the project root
            bstool_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "BsTool.exe")
            
        self.logger.debug(f"Looking for bstool.exe at: {bstool_path}")
        return bstool_path
        
    def _run_bstool_process(self, command: list, env: dict, log_file_path: str):
        """
        Run the bstool process in a separate thread.
        
        Args:
            command (list): Command to execute
            env (dict): Environment variables
            log_file_path (str): Path to the log file
        """
        try:
            # Emit status message
            self.status_message_signal.emit("bstool process started", 3000)
            
            # Start the subprocess
            with self.process_lock:
                self.process = subprocess.Popen(
                    command,
                    env=env,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    bufsize=1,
                    universal_newlines=True
                )
                
            self.logger.info(f"bstool process started with PID: {self.process.pid}")
            
            # Read output in real-time
            while True:
                output = self.process.stdout.readline()
                if output == '' and self.process.poll() is not None:
                    break
                if output:
                    output_str = output.strip()
                    # Emit the output signal
                    self.bstool_output_signal.emit(output_str)
                    self.logger.debug(f"bstool output: {output_str}")
                    
                    # Write to log file using LogWriter if available
                    if self.log_writer:
                        try:
                            self.log_writer.append_to_file(log_file_path, output_str)
                        except Exception as e:
                            self.logger.error(f"Failed to write to log file: {str(e)}")
                    
            # Check for any remaining stderr output
            stderr_output = self.process.stderr.read()
            if stderr_output:
                error_str = f"ERROR: {stderr_output.strip()}"
                self.bstool_output_signal.emit(error_str)
                self.logger.error(f"bstool stderr: {stderr_output.strip()}")
                
                # Write error to log file using LogWriter if available
                if self.log_writer:
                    try:
                        self.log_writer.append_to_file(log_file_path, error_str)
                    except Exception as e:
                        self.logger.error(f"Failed to write error to log file: {str(e)}")
                
            # Wait for process to complete
            return_code = self.process.wait()
            
            with self.process_lock:
                self.process = None
                
            if return_code == 0:
                self.status_message_signal.emit("bstool execution completed successfully", 3000)
                self.logger.info("bstool execution completed successfully")
            else:
                error_msg = f"bstool process exited with code {return_code}"
                self.logger.error(error_msg)
                self.report_error.emit(error_msg)
                self.status_message_signal.emit(error_msg, 5000)
                
        except FileNotFoundError as e:
            error_msg = f"bstool.exe not found: {str(e)}"
            self.logger.error(error_msg)
            self.report_error.emit(error_msg)
            self.status_message_signal.emit(error_msg, 5000)
        except Exception as e:
            error_msg = f"Error during bstool execution: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            self.report_error.emit(error_msg)
            self.status_message_signal.emit(error_msg, 5000)
        finally:
            with self.process_lock:
                self.process = None
                
    def terminate_bstool(self):
        """Terminate the currently running bstool process if any."""
        with self.process_lock:
            if self.process and self.process.poll() is None:
                try:
                    self.process.terminate()
                    self.process.wait(timeout=5)  # Wait up to 5 seconds for graceful termination
                    self.logger.info("bstool process terminated gracefully")
                except subprocess.TimeoutExpired:
                    self.process.kill()
                    self.process.wait()
                    self.logger.warning("bstool process killed forcefully")
                except Exception as e:
                    self.logger.error(f"Error terminating bstool process: {str(e)}")
                finally:
                    self.process = None
                    self.status_message_signal.emit("bstool process terminated", 3000)
            elif self.process:
                # Process already finished
                self.process = None
            else:
                # No process running
                self.status_message_signal.emit("No bstool process running", 3000)
                
    def copy_to_log(self, content: str, log_file_path: str):
        """
        Copy provided content to the specified log file.
        
        Args:
            content (str): Content to write to the log file
            log_file_path (str): Path to the log file
        """
        try:
            with open(log_file_path, 'a', encoding='utf-8') as f:
                f.write(content + '\n')
            self.status_message_signal.emit(f"Content copied to {log_file_path}", 3000)
            self.logger.info(f"Content copied to {log_file_path}")
        except Exception as e:
            error_msg = f"Failed to copy content to log: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            self.report_error.emit(error_msg)
            self.status_message_signal.emit(error_msg, 5000)
            
    def clear_terminal(self):
        """Clear the output display in the UI."""
        # This method would typically emit a signal to clear the UI terminal display
        # For now, we'll just emit an empty string to indicate clearing
        self.bstool_output_signal.emit("")
        self.status_message_signal.emit("Terminal cleared", 3000)
        
    def clear_log(self, log_file_path: str):
        """
        Clear the content of the specified log file.
        
        Args:
            log_file_path (str): Path to the log file to clear
        """
        try:
            with open(log_file_path, 'w', encoding='utf-8') as f:
                f.write("")
            self.status_message_signal.emit(f"Log file {log_file_path} cleared", 3000)
            self.logger.info(f"Log file {log_file_path} cleared")
        except Exception as e:
            error_msg = f"Failed to clear log file: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            self.report_error.emit(error_msg)
            self.status_message_signal.emit(error_msg, 5000)