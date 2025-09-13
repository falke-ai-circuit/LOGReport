# Log Writer Documentation

## Overview
Manages creation and writing to log files with standardized formats.

## Key Features
- Creates standardized log files
- Appends command outputs to logs
- Handles file rotation
- Supports multiple log types (FBC, RPC, LOG, LIS)
- Uses token-based log path resolution when available

## Log File Naming
- FBC: `{node}_{ip}_{token}.fbc`
- RPC: `{node}_{ip}_{token}.rpc`
- LOG: `{node}_{ip}.log` or `{node}_{ip}_{token}.log`
- LIS: `{node}_{ip}_{token}.lis`

## Directory Structure
- FBC logs: `{log_root}/FBC/{node}/`
- RPC logs: `{log_root}/RPC/{node}/`
- LOG files: `{log_root}/LOG/`
- LIS files: `{log_root}/LIS/{node}/`

## Important Methods
- `write_to_log()`: Writes content to the appropriate log file, using token log_path when available
- `write_to_app_log()`: Writes messages to the application log
- `write_clipboard_content()`: Writes clipboard content to logs
- `clear_log()`: Clears log files associated with a token

## Log Formatting
- Includes timestamp for each entry
- Preserves original command output
- Enforces consistent line endings
- Adds metadata headers when appropriate

## Token Integration
The LogWriter now integrates with the token system to determine appropriate log file paths:
- When a token with a `log_path` attribute is provided, that path is used directly
- When a token with `token_id` and `ip_address` attributes is provided, filenames are generated using these identifiers
- When no token information is available, fallback naming conventions are used