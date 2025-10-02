# Logging Architecture

## Overview
The logging system in LOGReport handles creation, management, and writing of log files for different protocol types (FBC, RPC, LOG, LIS). It ensures proper separation and organization of logs while maintaining performance through efficient file handle management.

## Log Key Structure
The LogWriter uses token-based identification where possible, falling back to composite keys in the format `(token_id, protocol)` where:
- `token_id`: Numeric identifier from node configuration
- `protocol`: Lowercase string ("fbc", "rpc", etc.)

## Key Components

### LogWriter
Primary class responsible for:
- Writing content to appropriate log files
- Handling token-based log path resolution
- Managing application logging
- Handling file I/O operations

### LoggingService
Orchestrates the logging process:
- Coordinates between command execution and log writing
- Manages log lifecycle events
- Handles error conditions in logging

### FbcCommandService / RpcCommandService
Protocol-specific services that:
- Generate appropriate commands for their protocol
- Interface with LogWriter for log management
- Handle protocol-specific formatting and processing

## Log File Organization

### Directory Structure
- FBC logs: `{log_root}/FBC/{node}/`
- RPC logs: `{log_root}/RPC/{node}/`
- LOG files: `{log_root}/LOG/`
- LIS files: `{log_root}/LIS/{node}/`

### File Naming Convention
- FBC: `{node}_{ip}_{token}.fbc` (when token info available) or `{node}.{extension}`
- RPC: `{node}_{ip}_{token}.rpc` (when token info available) or `{node}.{extension}`
- LOG: `{node}_{ip}.log` (standard naming) or `{node}_{ip}_{token}.log` (when token info available)
- LIS: `{node}_{ip}_{token}.lis` (when token info available) or `{node}.{extension}`

## Token-Based Path Resolution
The system now implements token-based path resolution to determine appropriate log file paths:
1. If a token with a `log_path` attribute is provided, that path is used directly
2. If a token with `token_id` and `ip_address` attributes is provided, filenames are generated using these identifiers
3. If no token information is available, fallback naming conventions are used

This approach ensures that log files are consistently named and located based on the context in which they are created.

## Performance Considerations
- Direct file writing without keeping handles open
- Efficient path resolution using token attributes
- Memory-efficient handling of multiple concurrent logs

## Error Handling
- Graceful handling of file I/O errors
- Comprehensive logging of error conditions to application log
- Fallback behavior for inaccessible log directories