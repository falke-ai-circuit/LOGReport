---
metadata:
  created_date: "2025-09-01_000000"
  last_modified: "2025-10-02T17:17:00Z"  # Post-merge
  word_count: 750  # Combined estimate
  reference_count: 8  # Aggregated
  document_hash: "sha256:command_queue_merged_hash"
  similarity_index: 0.70  # Post-merge
  obsolete_check_date: "2025-10-02"
  merge_sources: ["ARCH_cmd_queue_impl_v1.md", "ARCH_command_processing_v1.md", "ARCH_command_system_v1.md", "ARCH_batch_operations_v1.md"]  # Queue variants uniques preserved
---

# ARCH_command_queue_v1 (Merged Queue System + Impl + Processing + Batch) ✅Unified

## Overview (Merged from ARCH_command_system_v1.md + ARCH_command_queue_v1.md)
Integrated Command Queue system for sequential telnet command processing. Uses FIFO queue with threading, error handling, and session management. Replaces legacy direct execution with robust queue-based approach. Flow: UI→Queue{IDLE→CreateWrk|PROC→Reuse|BACK→Throttle}→Exec→Log→State ✅ThreadSafe

Comp/State/Metric | Det | Symbol |
|-------------------|-----|--------|
| Queue | FIFO/lock/max1000 | ✅FIFO |
| Worker | Deq→Exec→Cleanup | ✅DynPool |
| Trans | Idle→Proc(Cmds)|Proc→Back>800 | ⚠️<200→Proc |
| Perf | 1500/s<50ms|1000depth<2MB | ✅Scale |
| Fail | Retry/Dead/Circuit | ✅Recovery |
| FBC | No write/start→Remove/Align RPC | ✅Consist |
| RPC Out | No logs/path→Populate NodeMgr | ✅Trace |

## Key Components (Merged Impl Details)
| Component | Description | Key Methods | Refs |
|-----------|-------------|-------------|------|
| CommandQueue | Core queue mgmt | PyQt6.QtCore.QObject | 6.x | FIFO processing, signals |
| CommandWorker | Exec unit | QRunnable | - | Telnet send_command, error check |
| ThreadingService | Locks | Custom | - | Atomic _processing_lock |

**Patterns:** Observer (pyqtSignal) → UI feedback | Worker Thread → Non-blocking UI.

## API & Interfaces (From Impl)
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

## Configuration & Security (Merged)
| Variable | Purpose | Default | Required | Example |
|----------|---------|---------|----------|---------|
| MAX_THREADS | Pool size | 1 | ❌ | 1 |
| AUTO_CLEANUP | Remove completed | True | ❌ | True |

**Security:** Token validation [validate_token](src/commander/command_queue.py:374) • Session reconnects secure.

## Performance & Testing (From Impl + Batch)
**Targets:** Latency <200ms/cmd • Throughput 5 cmds/min • Memory <10MB/queue.
**Optimization:** Single thread → No race conditions • Cleanup on complete.

**Testing:** Unit 95% (test_command_queue.py) • Integration (telnet mocks) • E2E (full queue flow).

Ben/Sign/Pract | Desc | Symbol |
|---------------|------|--------|
| Consist/Err/UseServ | Format/Recovery/Exec | ✅Central |
| Log/Queue/Type | Mon/Auto/Inputs | ✅Safe |
| Direct/String/MVP | UI start/build/Present | ❌Couple (Consol High 7%)

## Deployment & Operations (From Impl)
```bash
# Init in MainWindow
self.command_queue = CommandQueue(session_manager)
self.command_queue.command_completed.connect(self.handle_completion)
```

**Environments:** Dev (mock telnet) • Prod (real sessions).

## Monitoring & Maintenance (From Impl)
**Logging:** DEBUG queue contents [src/commander/command_queue.py:212](src/commander/command_queue.py:212) → Retention 7d.
**Metrics:** Queue size [184](src/commander/command_queue.py:184), completed_count.
**Alerts:** _is_processing lock fail → Critical.

## Troubleshooting (Merged from Impl)
| Issue | Symptoms | Solution | Tools |
|-------|----------|----------|-------|
| Queue stuck | _is_processing True, no progress | Manual cleanup [382](src/commander/command_queue.py:382) | Logs/debug.log |
| Connection fail | Retries exhausted | Check telnet [47-97](src/commander/command_queue.py:47) | netstat/telnet test |

**Debug:** Logs → application.log • Profile → Queue len emit.

## Future (Preserved)
Future: Async→Unified→Timeout

## Codebase Sync (Aggregated Refs)
- CommandQueue: [src/commander/command_queue.py:147-388](src/commander/command_queue.py:147)
- CommandWorker: [src/commander/command_queue.py:23-145](src/commander/command_queue.py:23)
- SessionManager: [src/commander/session_manager.py:1](src/commander/session_manager.py:1)
- NodeManager: [src/commander/node_manager.py:1](src/commander/node_manager.py:1)
- Services: [src/commander/services/](src/commander/services/)
- Recent Changes: [ROADMAP_recent_changes_v1 #Overview](docs/roadmaps/ROADMAP_recent_changes_v1.md#Overview)