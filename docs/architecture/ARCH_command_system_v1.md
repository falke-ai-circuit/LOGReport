---
metadata:
  created_date: "2025-09-01_000000"
  last_modified: "2025-10-01T06:00:00Z"
  last_accessed: "2025-10-01T06:00:00Z"
  word_count: 8
  reference_count: 1
  document_hash: "sha256:computed_hash_system"
  similarity_index: 0.10
  obsolete_check_date: "2025-10-01"
---

# 🏗️ Command System Architecture v1 (Integrated Queue)

## Overview
Integrated Command Queue system for sequential telnet command processing. Uses FIFO queue with threading, error handling, and session management. Replaces legacy direct execution with robust queue-based approach.

## Key Components
| Component | Description | Refs |
|-----------|-------------|------|
| CommandQueue | FIFO queue, thread-safe add/process [src/commander/command_queue.py:147-388](src/commander/command_queue.py:147) | add_command, start_processing |
| CommandWorker | QRunnable for telnet exec, error detection [src/commander/command_queue.py:23-145](src/commander/command_queue.py:23) | run, signals.finished |
| SessionManager | Telnet session handling [src/commander/session_manager.py:1](src/commander/session_manager.py:1) | get_or_create_session |

## Flow
UI Action → add_command(cmd, token) → start_processing() → Worker.run() → telnet.send_command → log_write_completed → UI Update.

**Patterns:** Observer (pyqtSignal command_completed [148](src/commander/command_queue.py:148)) | Thread Pool (max 1 thread [165](src/commander/command_queue.py:165)).

## Integration
- NodeTreePresenter: Connects signals for node color updates post-command.
- LogWriter: Handles output append [src/commander/log_writer.py:51](src/commander/log_writer.py:51).
- Error Detection: utils/error_detection.py for response validation.

See ARCH_cmd_queue_impl_v1.md for full details.