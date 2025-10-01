---
title: 'BLUEPRINT Clipboard Mechanism'
version: 'v2'
refs: ['Phase4_merge']
updated: '2025-10-01'
created_date: '2025-09-01'
word_count: 650
reference_count: 8
document_hash: "sha256_placeholder"
similarity_index: 0.10
obsolete_check_date: '2025-10-01'
---

# Clipboard to Log Mechanism Blueprint

## Overview
This blueprint defines the clipboard interaction pattern that enables users to copy text from various sources (including VNC sessions) and write it directly to log files. The mechanism integrates with existing logging infrastructure while providing user feedback and validation, ensuring data integrity and traceability.

## 1. Interaction Flow

### 1.1. Manual Clipboard-to-Log Sequence
```
1. User copies text to system clipboard
2. User selects target log type (FBC/LIS/LOG/RPC)
3. User clicks 'Copy to Log' button (e.g., in SessionPresenter)
4. System validates clipboard content format
5. System determines target node directory
6. System writes content to appropriate log file
7. System provides success/error feedback
```

### 1.2. Automatic Clipboard-to-Logfile Sequence (VNC Context)
```
1. Log file selected → NodeManager sets active log context
2. ClipboardMonitor detects clipboard change (e.g., from VNC text selection)
3. Content validated against active log type
4. LogWriter appends to active log file
5. StatusService shows "Auto-copied to log" message
```

## 2. Component Specifications

### 📋 Clipboard Access & Log Routing
| Feature | Detail | Implementation/Pattern | Validation/Example | Error Cases |
|---------|--------|------------------------|--------------------|-------------|
| **Clipboard Access** | System Clipboard API | `QApplication.clipboard()` | N/A | N/A |
| **Auto Clipboard-to-Log** | Triggered by active log file change | [`ClipboardMonitor`](src/commander/services/clipboard_monitor.py:1) uses `NodeManager.active_log_file` | N/A | N/A |
| **Validation** | FBC | `^[A-Z0-9]{3,4}\s+\d{2}:\d{2}:\d{2}\.\d{3}\s+.*$` ✅ | "Invalid format" ❌ | N/A |
| | LIS | `^LIS\s+\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}\s+.*$` ✅ | "Invalid format" ❌ | N/A |
| | LOG | Standard log format ✅ | "Invalid format" ❌ | N/A |
| | RPC | XML/JSON structure ✅ | "Invalid format" ❌ | N/A |
| **Ctrl+C Impl.** | VNC text selection copies to clipboard | `VNCSession.text_selected` signal → `StatusService.show_message("Copied to clipboard")` | N/A | N/A |
| **Log Directory** | `test_logs/[type]/[node_token]/` | N/A | N/A | "Node not selected" ⚠️ |
| **Log Filename** | `[node_token]_[timestamp]_[type].ext` | Example: `AP01m_20250906_185714.fbc` | N/A | N/A |
| **Node Context** | Uses `NodeManager.active_node` | N/A | N/A | N/A |
| **File Handling** | Appends to existing / creates new | N/A | N/A | "Log write failed" ❌ |

### 2.1. User Feedback
- **Success Message**: "Copied to [type] log" (2 seconds duration)
- **Error Message**: Specific error with context (2 seconds duration)
- **Implementation**: `StatusService.show_message()` with `STATUS_MSG_SHORT` duration
- **Visual Indicators**: Status bar updates with color-coded feedback

## 3. Integration Points
- **Node Context**: [`NodeManager`](src/commander/node_manager.py:1) provides active node token and `active_log_file` (context), `log_file_selected` (IP extraction), `get_node_token()` (path), `get_log_filename()` (parsing).
- **Clipboard Access**: Qt clipboard API integration in `SessionPresenter` (`QApplication.clipboard()`, `dataChanged` for validation, MIME type handling, `textSelected` for copy/notify).
- **Log Writing**: [`LogWriter`](src/commander/services/log_writer.py:1) handles file operations (`write_to_log()`), content validation (`validate_log_content()`), and directory pathing (`get_log_path()`).
- **Validation**: [`TokenUtils`](src/commander/utils/token_utils.py:1) provides format validation.
- **Status Feedback**: [`StatusService`](src/commander/services/status_service.py:1) manages UI feedback (`show_message()`, `STATUS_MSG_SHORT`, color-coded).

## 4. Error Handling Strategy

| Error Condition | Component | Handling Mechanism | User Feedback | Recovery Path |
|-----------------|-----------|---------------------|---------------|---------------|
| Empty clipboard | SessionPresenter/ClipboardMonitor | State check before operation | "Clipboard empty" | User re-copies content |
| Invalid format | LogWriter | Format validation failure | "Invalid [type] format" | User corrects content |
| No active node | NodeManager | State check before operation | "Node not selected" | User selects node first |
| File write error | LogWriter | Error code analysis | "Log write failed (code 12)" | Check permissions/disk space |
| Non-text clipboard content | Qt Clipboard API | MIME type handling | "Non-text content rejected" | User copies text content |

## 5. Design Rationale
| Aspect | Rationale | Benefit |
|--------|-----------|---------|
| **Consistency** | Matches existing Telnet log patterns | Streamlined integration & user experience |
| **Validation** | Prevents malformed log entries | Ensures data integrity for analysis |
| **User Guidance** | Clear error messages | Improves usability & reduces errors |
| **Traceability** | Timestamped filenames | Facilitates session correlation & debugging |
| **Extensibility** | Modular validation rules | Supports future log type additions |
| **Modularity** | Decoupled components | Easier maintenance and testing |

## 6. Validation Checklist
- [x] All integration points documented with source references
- [x] Error handling paths fully specified
- [x] Cross-component workflows validated
- [x] Compliance with project structure rules confirmed
- [x] Naming conventions consistent with existing codebase
- [x] Empty clipboard, non-text rejected, Ctrl+C notification handled