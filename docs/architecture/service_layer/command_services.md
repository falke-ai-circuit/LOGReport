# Command Services Documentation

## Service Architecture

### CommandService (Base Class)
- Abstract base class for all command services
- Defines common interface for command queuing and execution
- Standardizes error handling and response processing
- Provides dependency injection for command queue and log writer

### FBC Command Service
```python
class FbcCommandService(CommandService):
    def queue_fieldbus_command(self, node_name, token_id):
        """Queues FBC command for execution"""
        command = f"print from fbc io structure {token_id}0000"
        self.command_queue.add_command(command, node_name, token_id)
        
    def handle_response(self, response):
        """Processes FBC command response"""
        if "ERROR" in response:
            self.report_error(response)
        else:
            self.log_writer.write_to_log(response)
```

### RPC Command Service
```python
class RpcCommandService(CommandService):
    def queue_rpc_command(self, node_name, token_id, action):
        """Queues RPC print/clear command"""
        if action == "print":
            cmd = f"print from fbc rupi counters {token_id}0000"
        else:
            cmd = f"clear fbc rupi counters {token_id}0000"
        self.command_queue.add_command(cmd, node_name, token_id)
```

### BsTool Command Service
```python
import subprocess
import os
from PyQt5.QtCore import QObject, pyqtSignal
# Assuming CommandService is a base class for common interfaces
# from .command_service_base import CommandService

class BsToolCommandService(QObject):
    status_message_signal = pyqtSignal(str, int)
    bstool_output_signal = pyqtSignal(str, str)
    report_error = pyqtSignal(str)

    def __init__(self, log_writer, threading_service, parent=None):
        super().__init__(parent)
        self.log_writer = log_writer
        self.threading_service = threading_service

    def execute_bstool(self, log_file_path: str, bstool_command_args: str = ""):
        def _run_bstool():
            try:
                # Determine bstool.exe path (e.g., relative to the executable)
                bstool_path = os.path.join(os.path.dirname(sys.executable), '_internal', 'bstool.exe')
                command = [bstool_path] + shlex.split(bstool_command_args)

                env = os.environ.copy()
                env['COMMUNICATION_LINE'] = 'AB01'

                process = subprocess.Popen(
                    command,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    env=env
                )

                for line in iter(process.stdout.readline, ''):
                    self.bstool_output_signal.emit(line, log_file_path)
                process.stdout.close()

                stderr_output = process.stderr.read()
                if stderr_output:
                    self.report_error.emit(f"BsTool Error: {stderr_output}")

                process.wait()
                self.status_message_signal.emit("BsTool execution complete.", 3000)

            except FileNotFoundError:
                self.report_error.emit(f"Error: bstool.exe not found at {bstool_path}. Ensure it's bundled correctly.")
            except Exception as e:
                self.report_error.emit(f"Error executing BsTool: {e}")

        self.threading_service.run_in_thread(_run_bstool)

    def copy_to_log(self, content: str, log_file_path: str):
        self.log_writer.write_to_log(content, log_file_path)

    def clear_terminal(self):
        # This would typically involve emitting a signal to the UI to clear its display
        pass

    def clear_log(self, log_file_path: str):
        with open(log_file_path, 'w') as f:
            f.truncate(0)
        self.status_message_signal.emit(f"Log file {log_file_path} cleared.", 3000)
```

## Usage Examples

### Executing FBC Command
```python
# From CommanderWindow context menu
fbc_service.queue_fieldbus_command("AP01m", "12345")

# Manually via queue
command_queue.add_command(
    "print from fbc io structure 123450000",
    node="AP01m",
    token="12345"
)
```

### Executing BsTool Command
```python
# From CommanderWindow context menu or directly
bstool_service.execute_bstool("path/to/selected_log.log", "-errlog AP01")
```

### Handling Command Results
```python
# Example response handler
def on_command_complete(response):
    if "structure" in response:
        parse_fieldbus_structure(response)
    elif "counters" in response:
        parse_rupi_counters(response)
```

## Common Patterns

### Adding New Command Type
1. Create new CommandService subclass
2. Implement command formatting
3. Add response handling
4. Register with CommanderWindow

### Standardized Error Handling
```python
# Base CommandService error handling
def execute_command(self, command, node_name, token_id):
    try:
        response = self.telnet_session.send_command(command)
        if "ERROR" in response:
            self.handle_error(response, node_name, token_id)
            return None
        return response
    except ConnectionError as e:
        self.logger.error(f"Connection failed for {node_name}: {e}")
        self.reconnect()
        raise
    except TimeoutError as e:
        self.logger.error(f"Command timeout for {node_name}: {e}")
        self.handle_timeout(command, node_name)
        raise
```

## Integration Points

### With CommanderWindow
- Updates status bar messages
- Provides context menu actions
- Manages command input/output

### With LogWriter
- Appends all successful command outputs
- Includes metadata in log entries
- Handles log file rotation