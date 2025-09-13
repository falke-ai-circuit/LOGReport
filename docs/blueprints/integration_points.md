# VNC Tab Integration Points

## Overview
This document details all integration points between the VNC tab implementation and existing system components. Each integration follows the established architecture patterns while introducing minimal new dependencies.

## Core Integration Points

### Node Selection Integration
- **Source**: [`NodeManager`](src/commander/node_manager.py:1)
- **Integration**:
  - `active_log_file` property provides current log context
  - `log_file_selected` signal triggers IP extraction in ConnectionBar
  - `get_node_token()` method returns directory path component
  - `get_log_filename()` returns full log filename for parsing
- **Pattern**: Observer pattern (signals/slots)
- **Validation**:
  - ConnectionBar updates within 100ms of log file selection
  - Empty state handled when no log file selected

### Session Management Integration
- **Source**: [`SessionPresenter`](src/commander/presenters/session_presenter.py:1)
- **Integration**:
  - `connect_vnc()` method initiates VNC connection sequence
  - `disconnect_vnc()` terminates active session
  - `connection_state` property drives UI indicators
- **Pattern**: Presenter pattern (separation of UI logic)
- **Validation**:
  - Connection state transitions verified through state machine
  - Error states propagate to StatusService

### Log Writing Integration
- **Source**: [`LogWriter`](src/commander/services/log_writer.py:1)
- **Integration**:
  - `write_to_log()` handles file operations with node context
  - `validate_log_content()` enforces format rules
  - `get_log_path()` determines target directory structure
- **Pattern**: Service pattern (reusable business logic)
- **Validation**:
  - File permissions checked before write operations
  - Atomic writes prevent log corruption

### Clipboard Integration
- **Source**: System clipboard API via Qt
- **Integration**:
  - `QApplication.clipboard()` access in SessionPresenter
  - `dataChanged` signal triggers validation checks
  - MIME type handling for text content
  - `textSelected` signal triggers clipboard copy with notification
- **Pattern**: Adapter pattern (system API abstraction)
- **Validation**:
  - Empty clipboard state handled gracefully
  - Non-text content rejected with clear message
  - Ctrl+C operation shows "Copied to clipboard" notification

### Status Feedback Integration
- **Source**: [`StatusService`](src/commander/services/status_service.py:1)
- **Integration**:
  - `show_message()` displays operation results
  - `STATUS_MSG_SHORT` duration (2000ms) used consistently
  - Color-coded messages match system theme
- **Pattern**: Singleton pattern (global status management)
- **Validation**:
  - Message queue prevents overlapping displays
  - Accessibility requirements met (contrast ratios)

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