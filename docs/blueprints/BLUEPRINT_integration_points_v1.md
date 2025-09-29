# VNC Tab Integration Points

## Overview
This document details all integration points between the VNC tab implementation and existing system components. Each integration follows the established architecture patterns while introducing minimal new dependencies.

## 🔗 Core Integration Points

| Integration Point | Source | Integration Details | Pattern | Validation |
|---|---|---|---|---|
| **Node Selection** | [`NodeManager`](src/commander/node_manager.py:1) | `active_log_file` (context), `log_file_selected` (IP extraction), `get_node_token()` (path), `get_log_filename()` (parsing) | Observer (signals/slots) | UI updates <100ms, empty state handled |
| **Session Management** | [`SessionPresenter`](src/commander/presenters/session_presenter.py:1) | `connect_vnc()`, `disconnect_vnc()`, `connection_state` (UI indicators) | Presenter (UI logic separation) | State transitions verified, errors propagate to `StatusService` |
| **Log Writing** | [`LogWriter`](src/commander/services/log_writer.py:1) | `write_to_log()` (file ops), `validate_log_content()` (format), `get_log_path()` (directory) | Service (reusable logic) | File permissions, atomic writes |
| **Clipboard** | Qt Clipboard API | `QApplication.clipboard()`, `dataChanged` (validation), MIME type handling, `textSelected` (copy/notify) | Adapter (API abstraction) | Empty clipboard, non-text rejected, Ctrl+C notification |
| **Status Feedback** | [`StatusService`](src/commander/services/status_service.py:1) | `show_message()` (results), `STATUS_MSG_SHORT` (2000ms), color-coded | Singleton (global status) | Message queue, accessibility |

## Cross-Component Workflows

### Connection Sequence
1. Log file selection → NodeManager emits `log_file_selected` signal
2. Log filename parsing extracts IP
3. SessionPresenter receives IP → updates ConnectionBar
4. User clicks Connect → SessionPresenter initiates connection
5. VNC client establishes connection → SessionPresenter updates state
6. StatusService shows "Connected" message

### Log Writing Sequence
1. User copies text → System clipboard updated
2. User selects log type → SessionPresenter stores selection
3. User clicks 'Copy to Log' → SessionPresenter validates content
4. LogWriter processes request → writes to appropriate file
5. StatusService shows result message

### Automatic Clipboard-to-Logfile
1. Log file selected → NodeManager sets active log context
2. ClipboardMonitor detects clipboard change
3. Content validated against log type
4. LogWriter appends to active log file
5. StatusService shows "Auto-copied to log" message

### Session Recording Sequence
1. User clicks "Record" → SessionRecorder starts capturing
2. Mouse movements/clicks timestamped and stored
3. User stops recording → data saved to `.vncr` file
4. Replay functionality loads event sequence

## Error Handling Integration

| Error Condition | Component | Handling Mechanism | User Feedback |
|----------------|-----------|---------------------|---------------|
| Connection timeout | SessionPresenter | Retry with backoff (3 attempts) | "Connection failed - retrying" |
| Invalid clipboard format | LogWriter | Format validation failure | "Invalid FBC format" |
| Missing node context | NodeManager | State check before operation | "Node not selected" |
| File write error | LogWriter | Error code analysis | "Log write failed (code 12)" |

### Session Recording Integration
- **Source**: [`SessionRecorder`](src/commander/services/session_recorder.py:1)
- **Integration**:
  - Captures mouse movements and clicks with timestamps
  - Stores events in structured format
  - Provides replay functionality via `SessionPlayer`
  - File format: `recordings/vnc/[node_token]_[timestamp].vncr`
- **Pattern**: Command pattern (recorded actions as executable commands)
- **Validation**:
  - Recording stops automatically on session disconnect
  - File integrity verified on save/load

## Design Compliance

- **Project Structure**: All new components follow `src/commander/` organization
- **Naming Conventions**: Consistent with existing patterns (e.g., `*_presenter.py`)
- **Tool Integration**: pytest tests added to `tests/commander/` directory
- **Documentation**: Blueprints updated in `docs/blueprints/` per standards

## Validation Checklist

- [x] All integration points documented with source references
- [x] Error handling paths fully specified
- [x] Cross-component workflows validated
- [x] Compliance with project structure rules confirmed
- [x] Naming conventions consistent with existing codebase