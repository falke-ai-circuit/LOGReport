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

### 📋 Clipboard Access & Log Routing
| Feature | Detail | Implementation/Pattern | Validation/Example | Error Cases |
|---|---|---|---|---|
| **Clipboard Access** | System Clipboard API | `QApplication.clipboard()` | N/A | N/A |
| **Auto Clipboard-to-Log** | Triggered by active log file change | [`ClipboardMonitor`](src/commander/services/clipboard_monitor.py:1) uses `NodeManager.active_log_file` | N/A | N/A |
| **Validation** | FBC | `^[A-Z0-9]{3,4}\s+\d{2}:\d{2}:\d{2}\.\d{3}\s+.*$` ✅ | "Invalid format" ❌ |
| | LIS | `^LIS\s+\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}\s+.*$` ✅ | "Invalid format" ❌ |
| | LOG | Standard log format ✅ | "Invalid format" ❌ |
| | RPC | XML/JSON structure ✅ | "Invalid format" ❌ |
| **Ctrl+C Impl.** | VNC text selection copies to clipboard | `VNCSession.text_selected` signal ��� `StatusService.show_message("Copied to clipboard")` | N/A | N/A |
| **Log Directory** | `test_logs/[type]/[node_token]/` | N/A | N/A | "Node not selected" ⚠️ |
| **Log Filename** | `[node_token]_[timestamp]_[type].ext` | Example: `AP01m_20250906_185714.fbc` | N/A | N/A |
| **Node Context** | Uses `NodeManager.active_node` | N/A | N/A | N/A |
| **File Handling** | Appends to existing / creates new | N/A | N/A | "Log write failed" ❌ |

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

## 🧠 Design Rationale
| Aspect | Rationale | Benefit |
|---|---|---|
| **Consistency** | Matches existing Telnet log patterns | Streamlined integration & user experience |
| **Validation** | Prevents malformed log entries | Ensures data integrity for analysis |
| **User Guidance** | Clear error messages | Improves usability & reduces errors |
| **Traceability** | Timestamped filenames | Facilitates session correlation & debugging |
| **Extensibility** | Modular validation rules | Supports future log type additions |