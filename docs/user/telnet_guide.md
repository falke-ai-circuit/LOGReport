# Telnet Client Usage Guide

## NetworkSession Pattern
- Base class for all network operations
- Provides standardized interface for command execution
- Implements robust connection management with retry logic
- Centralized error handling for all network operations
- Enforces consistent logging and monitoring

## TelnetOperations
- Consolidated module for all Telnet functionality
- Implements connection health checks and automatic recovery
- Standardized prompt pattern matching across all sessions
- Unified response parsing and filtering
- Centralized configuration for timeouts and retries

## Recent Fixes
- Fixed SyntaxError in command processing
- Corrected output redirection (responses now go to terminal instead of files)
- Improved error handling for malformed commands
- **Telnet Command Output Truncation Fix**:
  - **Root Cause**: An overly broad regex pattern `\d+[a-z]\%\s*$` in `TelnetClient._read_response` led to premature truncation of command output.
  - **Solution**: Implemented multiple, more robust regex patterns with newline anchors in `TelnetClient` and `TelnetSession` to ensure accurate prompt detection and prevent output truncation.
  - **Verification**: All integration tests in `tests/commander/test_telnet_command_output.py` passed, confirming full and consistent output from both context menu and Telnet tab executions.
  - **Learnings**: Emphasized the importance of precise regex for protocol parsing, dynamic test creation to unblock workflows, and iterative debugging of tests.

## Basic Usage
```python
from commander.telnet_client import TelnetClient

client = TelnetClient(host='192.168.1.1', port=23)
response = client.send_command('status')
print(response)
```

## Command Processing
1. Commands are queued for sequential execution
2. Responses are displayed in the terminal
3. Supports both synchronous and asynchronous modes

## Best Practices
- Always validate commands before sending
- Use the command queue for bulk operations
- Handle connection errors gracefully
## Codebase Sync
- Command Queue: [src/commander/services/queue_management_service.py:1](src/commander/services/queue_management_service.py:1) (thread-safe queue, progress tracking)
- LogWriter: [src/commander/log_writer.py:51](src/commander/log_writer.py:51) (write_to_log for responses)