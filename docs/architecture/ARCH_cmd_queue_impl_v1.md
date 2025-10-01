---
metadata:
  created_date: "2025-10-01_080100"
  last_modified: "2025-10-01T08:01:00Z"
  last_accessed: "2025-10-01T08:01:00Z"
  word_count: 280
  reference_count: 5
  document_hash: "sha256:arch_cmd_queue_impl_hash"
  similarity_index: 0.08
  obsolete_check_date: "2025-10-01"
---

# 🏗️ ARCH Command Queue Implementation v1

> **Purpose:** Detailed implementation of CommandQueue service for sequential processing in LOGReport.

## 📋 Overview
**What:** FIFO queue with threading for telnet commands | **Audience:** Architects/Developers | **Solves:** Concurrent command execution, error handling, session management.

## 🎯 Scope & Requirements
| Type | Requirement | Target | Constraint |
|------|-------------|--------|------------|
| Functional | Thread-safe add/process/clear | 1 max thread, auto-cleanup | PyQt6 signals, <500ms latency |
| Performance | Queue ops O(1) | Handle 50+ cmds | Lock-free where possible |
| Security | Validate tokens/sessions | No SQLi in cmds | Token auth via NodeManager |

## 🔧 Architecture & Stack
```
[NodeManager] → [CommandQueue (QObject)] → [ThreadPool (1 thread)] → [CommandWorker (QRunnable)]
                          ↓
[SessionManager] ← TelnetSession → Error Detection (utils/error_detection.py)
```
| Component | Role | Technology | Version | Purpose |
|-----------|------|------------|---------|---------|
| CommandQueue | Core queue mgmt | PyQt6.QtCore.QObject | 6.x | FIFO processing, signals |
| CommandWorker | Exec unit | QRunnable | - | Telnet send_command, error check |
| ThreadingService | Locks | Custom | - | Atomic _processing_lock |

**Patterns:** Observer (pyqtSignal) → UI feedback | Worker Thread → Non-blocking UI.

## 🌐 API & Interfaces
```python
add_command(cmd: str, token: NodeToken, telnet_client=None)  # Queue cmd
start_processing()  # Process pending
command_completed(str, str, bool, NodeToken)  # Emit result
```

**Data Models:**
```python
@dataclass
class QueuedCommand:
    command: str
    token: NodeToken
    status: str = 'pending'  # pending/processing/completed/failed
```

**Errors:** ConnectionError → Reconnect (3 retries) • ValueError → Invalid token.

## ⚙️ Configuration & Security
| Variable | Purpose | Default | Required | Example |
|----------|---------|---------|----------|---------|
| MAX_THREADS | Pool size | 1 | ❌ | 1 |
| AUTO_CLEANUP | Remove completed | True | ❌ | True |

**Security:** Token validation [validate_token](src/commander/command_queue.py:374) • Session reconnects secure.

## ⚡ Performance & Testing
**Targets:** Latency <200ms/cmd • Throughput 5 cmds/min • Memory <10MB/queue.
**Optimization:** Single thread → No race conditions • Cleanup on complete.

**Testing:** Unit 95% (test_command_queue.py) • Integration (telnet mocks) • E2E (full queue flow).

## 🚀 Deployment & Operations
```bash
# Init in MainWindow
self.command_queue = CommandQueue(session_manager)
self.command_queue.command_completed.connect(self.handle_completion)
```

**Environments:** Dev (mock telnet) • Prod (real sessions).

## 📊 Monitoring & Maintenance
**Logging:** DEBUG queue contents [src/commander/command_queue.py:212](src/commander/command_queue.py:212) → Retention 7d.
**Metrics:** Queue size [184](src/commander/command_queue.py:184), completed_count.
**Alerts:** _is_processing lock fail → Critical.

## 🛠️ Troubleshooting
| Issue | Symptoms | Solution | Tools |
|-------|----------|----------|-------|
| Queue stuck | _is_processing True, no progress | Manual cleanup [382](src/commander/command_queue.py:382) | Logs/debug.log |
| Connection fail | Retries exhausted | Check telnet [47-97](src/commander/command_queue.py:47) | netstat/telnet test |

**Debug:** Logs → application.log • Profile → Queue len emit.

---
**📚 Refs:** ROADMAP_recent_changes_v1.md, src/commander/command_queue.py, Phase7 Report.