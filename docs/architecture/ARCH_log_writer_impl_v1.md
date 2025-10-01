---
metadata:
  created_date: "2025-10-01_075300"
  last_modified: "2025-10-01T07:53:00Z"
  last_accessed: "2025-10-01T07:53:00Z"
  word_count: 280
  reference_count: 8
  document_hash: "sha256:arch_log_writer_impl_v1_hash"
  similarity_index: 0.85
  obsolete_check_date: "2025-10-01"
---

# ARCH_log_writer_impl_v1

## Overview
Implements log writing service for LOGReport commander. Handles file writes, app logging, clipboard appends, clears. Thread-safe via Qt signals. Integrates NodeManager for token paths. Constraints: UTF-8, timestamped entries, error emission.

## Components
| Component | Description | Key Methods | Refs |
|-----------|-------------|-------------|------|
| **LogWriter (QObject)** | Core service: writes to node/token logs, app.log. Emits log_write_completed (path, success, total_lines, lines_written). | `__init__(node_manager, log_root="logs")`: Setup dirs, app_logger (INFO, application.log). | [src/commander/log_writer.py:16-245](src/commander/log_writer.py:16) |
| **write_to_log** | Main write: content to FBC/LIS/LOG/RPC files. Uses token.log_path or derives from node_name/log_type. Timestamps, appends UTF-8. Counts lines pre/post. | `write_to_log(content, log_type, node_name=None, token=None)`: Derives filepath (e.g., test_logs/LOG/node_ip.log), emits signal. Handles no active node → app log. | [src/commander/log_writer.py:51-142](src/commander/log_writer.py:51) |
| **write_to_app_log** | App-level logging: INFO default to application.log. | `write_to_app_log(message, level=logging.INFO)`: Logs via app_logger. | [src/commander/log_writer.py:143-151](src/commander/log_writer.py:143) |
| **write_clipboard_content** | Clipboard → log: Delegates to write_to_log. | `write_clipboard_content(content, log_type)`: For paste ops. | [src/commander/log_writer.py:152-163](src/commander/log_writer.py:152) |
| **clear_log** | Clears token log: Writes empty file. | `clear_log(token_id)`: Finds tokens by ID, clears log_path if set. | [src/commander/log_writer.py:164-194](src/commander/log_writer.py:164) |
| **append_to_file** | Direct append: To any filepath, emits signal. | `append_to_file(filepath, content, token=None)`: UTF-8 append, line count emit. | [src/commander/log_writer.py:196-222](src/commander/log_writer.py:196) |
| **get_file_line_count** | Efficient line count: For pre/post metrics. | `get_file_line_count(filepath)`: Sums lines, errors→0. | [src/commander/log_writer.py:223-245](src/commander/log_writer.py:223) |

## Integration
- **NodeManager**: Derives paths from active_node/tokens.
- **Signals**: log_write_completed → UI updates (e.g., line counts in views).
- **Error Handling**: Exceptions → app log + re-raise; validates paths/IPs.
- **File Naming**: LOG: {node}_{ip}.log; FBC/RPC: {node}_{ip}_{token}.{type}; Fallback: {node}.{type}.

## Decisions
- UTF-8 only: Handles emojis/Unicode (fixes EncodeError).
- Timestamp: [%Y-%m-%d %H:%M:%S] prefix all entries.
- No rotation: Handled externally; focus append/clear.
- Metrics: Pre/post line counts for command tracking.

## Examples
```python
# Write FBC log
writer.write_to_log("FBC response data", "FBC", token=token_obj)

# Clear token log
writer.clear_log("12345")

# App log error
writer.write_to_app_log("Connection failed", logging.ERROR)
```

## References
- [ARCH_logging_system_v1.md](ARCH_logging_system_v1.md)
- [TECH_logging_v1.md](technical/TECH_logging_v1.md)
- [src/commander/node_manager.py](src/commander/node_manager.py)