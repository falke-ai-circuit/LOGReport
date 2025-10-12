"""
BsTool Worker Module

Provides QRunnable-based worker for BsTool command execution that integrates
with the CommandQueue system for proper synchronization.
"""

import subprocess
import os
import tempfile
import logging
from PyQt5.QtCore import QRunnable
from commander.command_queue import CommandWorkerSignals
from commander.models import NodeToken


class BsToolWorker(QRunnable):
    """
    QRunnable worker for executing BsTool commands synchronously.
    
    This worker integrates BsTool execution into the CommandQueue system,
    ensuring proper synchronization with FBC/RPC commands. The run() method
    blocks until the subprocess completes, maintaining sequential execution order.
    """
    
    def __init__(self, bstool_path: str, bstool_args: str, log_file_path: str, token: NodeToken, env: dict = None):
        """
        Initialize BsTool worker.
        
        Args:
            bstool_path: Full path to BsTool.exe
            bstool_args: Command arguments for BsTool
            log_file_path: Destination log file path
            token: NodeToken associated with this command
            env: Environment variables for subprocess
        """
        super().__init__()
        self.bstool_path = bstool_path
        self.bstool_args = bstool_args
        self.log_file_path = log_file_path
        self.token = token
        self.env = env or os.environ.copy()
        self.result = None
        self.success = False
        self.return_code = -1
        self.signals = CommandWorkerSignals()
        self.logger = logging.getLogger(__name__)
        
        # Build command string for logging/display
        import shlex
        self.command = f"{self.bstool_path} {self.bstool_args}"
        
    def run(self):
        """
        Execute BsTool command synchronously.
        
        This method blocks until the subprocess completes, ensuring
        sequential execution when managed by QThreadPool with maxThreadCount=1.
        """
        self.logger.info(f"BsToolWorker.run: Starting BsTool execution")
        self.logger.debug(f"BsToolWorker.run: Command: {self.command}")
        self.logger.debug(f"BsToolWorker.run: Log file: {self.log_file_path}")
        self.logger.debug(f"BsToolWorker.run: Token: {self.token.token_id} ({self.token.token_type})")
        
        stdout_temp_file = None
        stderr_temp_file = None
        process = None
        
        try:
            # Verify BsTool.exe exists
            if not os.path.exists(self.bstool_path):
                raise FileNotFoundError(f"BsTool.exe not found at {self.bstool_path}")
            
            # Create temporary files for stdout and stderr with encoding error handling
            stdout_temp_file = tempfile.NamedTemporaryFile(mode='w+', encoding='utf-8', errors='replace', delete=False)
            stderr_temp_file = tempfile.NamedTemporaryFile(mode='w+', encoding='utf-8', errors='replace', delete=False)
            
            self.logger.debug(f"BsToolWorker.run: Created temp files - stdout: {stdout_temp_file.name}, stderr: {stderr_temp_file.name}")
            
            # Build command list
            import shlex
            command_list = [self.bstool_path] + shlex.split(self.bstool_args)
            
            self.logger.debug(f"BsToolWorker.run: Executing command: {' '.join(command_list)}")
            
            # Start subprocess
            # NOTE: stdin=subprocess.DEVNULL indicates non-interactive execution
            # BsTool should exit automatically after processing -errlog command
            process = subprocess.Popen(
                command_list,
                env=self.env,
                stdin=subprocess.DEVNULL,  # No interactive input - BsTool should exit automatically
                stdout=stdout_temp_file,
                stderr=stderr_temp_file,
                text=True,
                bufsize=1,
                universal_newlines=True
            )
            
            self.logger.info(f"BsToolWorker.run: Subprocess started with PID: {process.pid}")
            
            # NOTE: BsTool.exe appears to be designed to run with arguments and exit automatically
            # Do NOT write to stdin or close it - let BsTool complete naturally
            # The command-line arguments (-errlog) should be sufficient for execution
            
            # CRITICAL: Block here until process completes (synchronous execution)
            # NOTE: BsTool is interactive and will timeout - this is EXPECTED behavior
            # We force-close it after timeout and check if output was written to tempfile
            try:
                self.return_code = process.wait(timeout=10)  # 10 second timeout for interactive tool
                self.logger.info(f"BsToolWorker.run: Process completed naturally with return code: {self.return_code}")
            except subprocess.TimeoutExpired:
                # TIMEOUT IS EXPECTED - BsTool displays list and waits for user input
                self.logger.info("BsToolWorker.run: Process timed out (expected for interactive tool), terminating...")
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait()
                self.return_code = -1  # Return code doesn't matter, check tempfile content instead
            
            # Read output from temporary files
            stdout_temp_file.seek(0)
            stdout_output = stdout_temp_file.read()
            stderr_temp_file.seek(0)
            stderr_output = stderr_temp_file.read()
            
            # SUCCESS = tempfile has content (not return_code == 0)
            # BsTool is interactive, so timeout is expected behavior
            has_output = bool(stdout_output and stdout_output.strip())
            self.logger.debug(f"BsToolWorker.run: Output check - has_output={has_output}, stdout_length={len(stdout_output) if stdout_output else 0}")
            
            # Write output to log file
            output_lines = []
            if stdout_output:
                for line in stdout_output.splitlines():
                    if line.strip():
                        output_lines.append(line.strip())
            
            if stderr_output:
                output_lines.append(f"ERROR: {stderr_output.strip()}")
                self.logger.error(f"BsToolWorker.run: stderr captured: {stderr_output.strip()}")
            
            # Write all output to log file
            if output_lines and self.log_file_path:
                try:
                    with open(self.log_file_path, 'a', encoding='utf-8') as f:
                        for line in output_lines:
                            f.write(line + '\n')
                    self.logger.info(f"BsToolWorker.run: Wrote {len(output_lines)} lines to {self.log_file_path}")
                except Exception as e:
                    self.logger.error(f"BsToolWorker.run: Failed to write to log file: {str(e)}")
            
            # Set success based on tempfile content (NOT return_code)
            # BsTool is interactive - timeout is expected, what matters is whether output was generated
            self.success = has_output and len(output_lines) > 0
            if self.success:
                # Store the actual output content in self.result for UI display
                self.result = '\n'.join(output_lines)
                self.logger.info(f"BsToolWorker.run: SUCCESS - captured {len(output_lines)} lines of output")
            else:
                self.result = "BsTool execution failed: no output captured"
                self.logger.warning(f"BsToolWorker.run: FAILED - no output captured from BsTool")

            
        except FileNotFoundError as e:
            error_msg = f"BsTool.exe not found: {str(e)}"
            self.logger.error(error_msg)
            self.result = error_msg
            self.success = False
            self.return_code = -1
            
        except Exception as e:
            error_msg = f"BsTool execution error: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            self.result = error_msg
            self.success = False
            self.return_code = -1
            
        finally:
            # Clean up temporary files
            if stdout_temp_file:
                try:
                    stdout_temp_file.close()
                    os.unlink(stdout_temp_file.name)
                except Exception as e:
                    self.logger.warning(f"BsToolWorker.run: Failed to cleanup stdout temp file: {str(e)}")
                    
            if stderr_temp_file:
                try:
                    stderr_temp_file.close()
                    os.unlink(stderr_temp_file.name)
                except Exception as e:
                    self.logger.warning(f"BsToolWorker.run: Failed to cleanup stderr temp file: {str(e)}")
            
            # Emit completion signals
            result_str = str(self.result) if self.result is not None else ""
            self.logger.debug(f"BsToolWorker.run: Emitting finished signal")
            self.signals.finished.emit(self, result_str)
            self.logger.debug(f"BsToolWorker.run: Emitting command_completed signal")
            self.signals.command_completed.emit(self.command, result_str, self.success, self.token)
            self.logger.debug(f"BsToolWorker.run: Done emitting signals")
