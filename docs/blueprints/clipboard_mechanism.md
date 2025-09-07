# Clipboard to Log Mechanism Blueprint

## Overview
This blueprint defines the clipboard interaction pattern that enables users to copy text from the VNC session and write it directly to log files. The mechanism integrates with existing logging infrastructure while providing user feedback and validation.

## Interaction Flow

```
1. User copies text to system clipboard
2. User selects target log type (FBC/LIS/LOG/RPC)
3. User clicks 'Copy to Log' button
4. System validates clipboard content format
5. System determines target node directory
6. System writes content to appropriate log file
7. System provides success/error feedback
```

## Component Specifications

### Clipboard Access
- **Implementation**: System clipboard API via Qt's `QApplication.clipboard()`
- **Automatic Clipboard-to-Logfile**:
  - Triggered when active log file changes
  - Implemented in [`ClipboardMonitor`](src/commander/services/clipboard_monitor.py:1)
  - Uses `NodeManager.active_log_file` to determine target
- **Validation**:
  - FBC: Matches `^[A-Z0-9]{3,4}\s+\d{2}:\d{2}:\d{2}\.\d{3}\s+.*$`
  - LIS: Matches `^LIS\s+\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}\s+.*$`
  - LOG: Standard log format validation
  - RPC: XML/JSON structure validation
- **Ctrl+C Implementation**:
  - Text selection in VNC viewer copies to system clipboard
  - Notification shown via `StatusService.show_message("Copied to clipboard")`
  - Implemented via `VNCSession.text_selected` signal
- **Error Cases**:
  - "Invalid format" for non-matching content
  - "Node not selected" when no active node context

### Log Routing
- **Directory Structure**: `test_logs/[type]/[node_token]/`
- **Filename Format**: `[node_token]_[timestamp]_[type].ext`
  - Example: `AP01m_20250906_185714.fbc`
- **Node Context**: Uses current node token from `NodeManager.active_node`
- **File Handling**: Appends to existing file or creates new with timestamp

### User Feedback
- **Success Message**: "Copied to [type] log" (2 seconds duration)
- **Error Message**: Specific error with context (2 seconds duration)
- **Implementation**: `StatusService.show_message()` with `STATUS_MSG_SHORT` duration
- **Visual Indicators**: Status bar updates with color-coded feedback

## Integration Points

- **Node Context**: [`NodeManager`](src/commander/node_manager.py:1) provides active node token
- **Clipboard Access**: Qt clipboard API integration in `SessionPresenter`
- **Log Writing**: [`LogWriter`](src/commander/services/log_writer.py:1) handles file operations
- **Validation**: [`TokenUtils`](src/commander/utils/token_utils.py:1) provides format validation
- **Status Feedback**: [`StatusService`](src/commander/services/status_service.py:1) manages UI feedback

## Error Handling Strategy

| Error Condition | Response | Recovery Path |
|----------------|----------|---------------|
| Empty clipboard | "Clipboard empty" | User re-copies content |
| Invalid format | "Invalid [type] format" | User corrects content |
| No active node | "Node not selected" | User selects node first |
| File write error | "Log write failed" | Check permissions/disk space |

## Design Rationale

- **Consistency**: Matches existing log writing patterns used in Telnet implementation
- **Validation**: Prevents malformed entries from corrupting log analysis
- **User Guidance**: Clear error messages help users understand required formats
- **Traceability**: Timestamped filenames enable correlation with session timelines
- **Extensibility**: New log types can be added by extending validation rules