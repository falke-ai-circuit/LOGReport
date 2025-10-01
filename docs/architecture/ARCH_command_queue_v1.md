---
metadata:
  created_date: "2025-09-01_000000"
  last_modified: "2025-10-01T06:00:00Z"
  last_accessed: "2025-10-01T06:00:00Z"
  word_count: 25
  reference_count: 2
  document_hash: "sha256:computed_hash_queue"
  similarity_index: 0.95
  obsolete_check_date: "2025-10-01"
---

# 🏗️ Cmd Queue (Merged System)

Flow: UI→Queue{IDLE→CreateWrk|PROC→Reuse|BACK→Throttle}→Exec→Log→State ✅ThreadSafe

Comp/State/Metric | Det | Symbol |
|-------------------|-----|--------|
Queue | FIFO/lock/max1000 | ✅FIFO |
Worker | Deq→Exec→Cleanup | ✅DynPool |
Trans | Idle→Proc(Cmds)|Proc→Back>800 | ⚠️<200→Proc |
Perf | 1500/s<50ms|1000depth<2MB | ✅Scale |
Fail | Retry/Dead/Circuit | ✅Recovery |
FBC | No write/start→Remove/Align RPC | ✅Consist |
RPC Out | No logs/path→Populate NodeMgr | ✅Trace |

Future: Async→Unified→Timeout

Refs: [Queue](src/commander/command_queue.py) [NodeMgr](src/commander/node_manager.py) [Proc](docs/architecture/ARCH_command_processing_v1.md)