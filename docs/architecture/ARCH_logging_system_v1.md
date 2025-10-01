# Unified Logging System Architecture

## Overview
The logging system manages creation, writing, and organization of log files for protocols (FBC, RPC, LOG, LIS). It uses token-based path resolution, standardized naming, and efficient I/O without persistent handles. Integrates with NodeManager for context-aware logging.

Key Features:
- Creates standardized log files
- Appends command outputs to logs
- Handles file rotation
- Supports multiple log types (FBC, RPC, LOG, LIS)
- Uses token-based log path resolution when available
- Direct file writing without keeping handles open for better resource management
- Enhanced error handling with detailed application logging

## Directory Structure
- FBC logs: `{log_root}/FBC/{node}/`
- RPC logs: `{log_root}/RPC/{node}/`
- LOG files: `{log_root}/LOG/`
- LIS files: `{log_root}/LIS/{node}/`

## File Naming Conventions
| Protocol | Format (with Token) | Format (Fallback) | Example |
|----------|---------------------|-------------------|---------|
| FBC | `{node}_{ip}_{token}.fbc` | `{node}.{extension}` | AP01m_192-168-0-11_162.fbc |
| RPC | `{node}_{ip}_{token}.rpc` | `{node}.{extension}` | AP01r_192-168-0-27_363.rpc |
| LOG | `{node}_{ip}_{token}.log` | `{node}_{ip}.log` | AL01_186_LOG.log |
| LIS | `{node}_{ip}_{token}.lis` | `{node}.{extension}` | AL01_186_LIS.lis |

## Token-Based Path Resolution
The system implements token-based path resolution to determine appropriate log file paths:
1. If a token with a `log_path` attribute is provided, that path is used directly
2. If a token with `token_id` and `ip_address` attributes is provided, filenames are generated using these identifiers
3. If no token information is available, fallback naming conventions are used

This approach ensures that log files are consistently named and located based on the context in which they are created.

## Key Methods (LogWriter)

### `LogWriter(node_manager, log_root="logs")`
Initializes the LogWriter with a NodeManager and optional log root directory.

### `write_to_log(content, log_type, node_name=None, token=None)`
Writes content to the appropriate log file.
- `content`: Content to write to log
- `log_type`: Type of log (FBC, LIS, LOG, RPC)
- `node_name`: Optional node name, if not provided uses active node
- `token`: Optional token with log_path attribute

### `write_to_app_log(message, level=logging.INFO)`
Writes messages to the application log.

### `write_clipboard_content(content, log_type)`
Writes clipboard content to logs.

### `clear_log(token_id)`
Clears log files associated with a token.

## Processing Rules
1. Tokens from filename pre-extension
2. Node: [A-Z0-9]+
3. IP: dotted/dashed
4. Port: numeric

## Debugging Strategy
1. Check application.log for detailed error messages
2. Verify token attributes are correctly set
3. Confirm log directory permissions
4. Review file naming patterns in test_logs directory

## Best Practices
- Always pass token objects when available for proper log path resolution.
- Handle exceptions appropriately when writing to logs.
- Use `write_to_app_log` for debugging and error reporting.
- Regularly check `application.log` for issues.

## LogReportGUI Logging Setup
The `LogReportGUI` class (`src/gui.py`) initializes the core logging system during its `__init__` method. This setup includes:
- Defining a standard log format: `%(asctime)s - %(name)s - %(levelname)s - %(message)s`
- Creating a dedicated `logs` directory at the project root if it doesn't exist.
- Configuring a root logger to capture messages at `DEBUG` level and above.
- Adding a console handler to display log messages in `sys.stdout`.
- Adding a file handler to persist log messages to `application.log` within the `logs` directory.

This ensures that all application-level events, including those from `LogProcessor` and `ReportGenerator`, are consistently logged to both the console and a file, providing comprehensive traceability for debugging and operational monitoring.
## Codebase Sync
- LogWriter: [src/commander/log_writer.py:16-245](src/commander/log_writer.py:16) (full impl: __init__ setup [22-50], write_to_log timestamp/UTF-8/rotation [51-142], signals log_write_completed [20], get_file_line_count [223-245])
- Queue Integration: command_completed_with_log_status → log_write_completed [src/commander/command_queue.py:148](src/commander/command_queue.py:148)
- App Logging: application.log handler [src/commander/log_writer.py:39-49](src/commander/log_writer.py:39)
## Codebase Sync
- LogWriter: [src/commander/log_writer.py:51](src/commander/log_writer.py:51)
- CommandQueue: [src/commander/command_queue.py:1](src/commander/command_queue.py:1)
- Recent Changes: [docs/roadmaps/ROADMAP_recent_changes_v1.md](docs/roadmaps/ROADMAP_recent_changes_v1.md)