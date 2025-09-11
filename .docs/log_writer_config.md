# LogWriter Configuration Guide

## Recent Enhancements
- Added token-based log path resolution
- Improved file naming conventions with IP address and token ID integration
- Enhanced error handling with detailed application logging
- Direct file writing without keeping handles open for better resource management

## Configuration Options
The LogWriter is initialized with a NodeManager and optional log root directory:
```python
# Example configuration
writer = LogWriter(
    node_manager=node_manager,
    log_root="logs"
)
```

## Key Methods

### write_to_log()
Writes content to the appropriate log file:
```python
writer.write_to_log(content, log_type, node_name=None, token=None)
```

Parameters:
- `content`: Content to write to log
- `log_type`: Type of log (FBC, LIS, LOG, RPC)
- `node_name`: Optional node name, if not provided uses active node
- `token`: Optional token with log_path attribute

The method uses the following path resolution logic:
1. If token has a `log_path` attribute, use it directly
2. If token has `token_id` and `ip_address` attributes, generate filename using these
3. Otherwise, use fallback naming conventions

### write_to_app_log()
Writes messages to the application log:
```python
writer.write_to_app_log(message, level=logging.INFO)
```

### write_clipboard_content()
Writes clipboard content to logs:
```python
writer.write_clipboard_content(content, log_type)
```

### clear_log()
Clears log files associated with a token:
```python
writer.clear_log(token_id)
```

## Debugging Strategy
1. Check application.log for detailed error messages
2. Verify token attributes are correctly set
3. Confirm log directory permissions
4. Review file naming patterns in test_logs directory

## Best Practices
- Always pass token objects when available for proper log path resolution
- Handle exceptions appropriately when writing to logs
- Use write_to_app_log for debugging and error reporting
- Regularly check application.log for issues