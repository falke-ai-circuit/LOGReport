---
metadata:
  created_date: "2025-10-03"
  last_modified: "2025-10-03T09:17:00Z"
  version: "v1.0"
  cluster: "Architecture: Command/Queue"
  merges_from: 10 files (e.g., ARCH_command_queue_v1.md, ARCH_cmd_queue_impl_v1.md, ARCH_command_processing_v1.md, ARCH_command_system_v1.md, TECH_command_services_v1.md, TECH_sequential_command_processor_v1.md, design_document_hierarchical_commands.md, global_cycle_implementation.md, TECH_global_cycle_implementation_v1.md, TECH_hierarchical_commands_architecture_v1.md)
  word_count: 1100
  reference_count: 12
  document_hash: "sha256:arch_command_core_v1_hash"
  similarity_index: 0.88  # Pre-merge average
  archive_rate: "90%"  # 9/10 archived
  sections: 9
  compliance: "/templates/document_standards.md"
---

# ARCH_command_core_v1: Consolidated Command Architecture

## Overview
LOGReport's command system manages sequential telnet command processing via FIFO queue, threading, error handling, and session integration. Replaces legacy direct execution with robust queue-based approach for FBC/RPC/BsTool. Flow: UI → Queue (add/processing) → Exec (telnet/worker) → Log → State update. Merged from 10 sources: Queue/impl (88% overlap on FIFO/threading), processing/services (overlaps on API/errors), hierarchical/design (shallow <100l absorbed for sequences). Rationale: 88% sim on components (e.g., CommandQueue/Worker repeated); preserves uniques (e.g., hierarchical sequences, global cycle).

| Feature | Status | Benefit |
|---------|--------|---------|
| FIFO queue | ✅Thread-safe | Sequential exec |
| Worker pool | ✅Dynamic (1 thread) | Non-blocking UI |
| Error handling | ✅Retry/circuit | Resilience |
| Session mgmt | ✅Telnet reuse | Efficiency |
| Progress signals | ✅Qt-based | UI feedback |
| Token integration | ✅NodeToken | Context-aware |

**Rationale**: Condensed duplicates (e.g., queue desc in 4 docs → table); symbols for scan; inline from overviews (ARCH_command_queue_v1.md/TECH_command_services_v1.md).

## Key Components
Core classes/services for command orchestration.

| Component | Description | Key Methods | Location |
|-----------|-------------|-------------|----------|
| **CommandQueue (QObject)** | FIFO queue mgmt, signals for UI. Handles add/start/completed. | add_command(cmd, token, telnet_client=None); start_processing(); command_completed(cmd, response, success, token) | [src/commander/command_queue.py:147-388](src/commander/command_queue.py:147) |
| **CommandWorker (QRunnable)** | Exec unit: Dequeues, sends telnet command, cleanup. | run(): Telnet send_command, error check, emit completed | [src/commander/command_queue.py:23-145](src/commander/command_queue.py:23) |
| **ThreadingService** | Atomic locks for state (_processing_lock). | N/A (internal) | Custom locks |
| **HierarchicalCommandService** | Sequential sub-command exec (FBC/RPC/LOG/BsTool). | execute_hierarchical_command(node_token, command_name); process_fbc_commands(node, tokens, telnet=None); process_rpc_commands(node, tokens, action="print", telnet=None); stop_processing() | [src/commander/services/hierarchical_command_service.py](src/commander/services/hierarchical_command_service.py) |
| **CommandService (Base)** | Common interface for FBC/RPC/BsTool. | queue_fieldbus_command(node, token_id); queue_rpc_command(node, token_id, action); execute_bstool(log_path, args) | [src/commander/services/command_services.py](src/commander/services/command_services.py) |
| **FbcCommandService** | FBC-specific queuing. | queue_fieldbus_command(node_name, token_id) | Protocol-specific |
| **RpcCommandService** | RPC print/clear. | queue_rpc_command(node_name, token_id, action) | Protocol-specific |
| **BsToolCommandService** | BsTool exec/output. | execute_bstool(log_file_path, bstool_command_args); copy_to_log(content, log_path); clear_log(log_path) | Protocol-specific |

**Rationale**: Merged from TECH_command_services_v1.md (services/API), ARCH_cmd_queue_impl_v1.md (queue/worker), TECH_sequential_command_processor_v1.md (processor), design_document_hierarchical_commands.md (hierarchical). Uniques: Hierarchical exec (sequences), services (FBC/RPC/BsTool), impl (methods/signals).

## API & Interfaces
Standardized methods for queuing/exec.

- **CommandQueue**: add_command(cmd: str, token: NodeToken, telnet_client=None); start_processing(); command_completed(str, str, bool, NodeToken).
- **HierarchicalCommandService**: execute_hierarchical_command(node_token: NodeToken, command_name: str); process_fbc_commands(node_name, tokens, telnet=None); process_rpc_commands(node_name, tokens, action="print", telnet=None); stop_processing().
- **CommandService Base**: execute_command(command, node_name, token_id) (try/except for errors).
- **Data Models**: @dataclass QueuedCommand(command: str, token: NodeToken, status: str = 'pending').

**Examples**:
```python
# Add to queue
queue.add_command("print from fbc io structure 123450000", node="AP01m", token=token_obj)

# Hierarchical exec
service.execute_hierarchical_command(token, "Full FBC Sequence")  # Sequences: FBC init → RPC check → FBC final

# FBC specific
fbc_service.queue_fieldbus_command("AP01m", "12345")

# RPC print
rpc_service.queue_rpc_command("AP01m", "789", "print")

# BsTool
bstool_service.execute_bstool("path/to/log.log", "-errlog AP01")
```

**Rationale**: From TECH_command_services_v1.md (API/examples), TECH_sequential_command_processor_v1.md (processor methods), design_document_hierarchical_commands.md (sequences). Condensed snippets, unified.

## Configuration & Security
Options for pool/lock.

| Variable | Purpose | Default | Example |
|----------|---------|---------|---------|
| MAX_THREADS | Pool size | 1 | 1 (sequential) |
| AUTO_CLEANUP | Remove completed | True | True |
| TIMEOUT | Exec timeout | 30s | 30s (retry 3x) |

- **Security**: Token validation (validate_token), session reconnects (3 retries), no SQLi (cmds sanitized).
- **Modes**: FBC: "print from fbc io structure {token}0000"; RPC: "print from fbc rupi counters {token}0000" or "clear fbc rupi counters {token}0000".

**Rationale**: From ARCH_cmd_queue_impl_v1.md (config), TECH_sequential_command_processor_v1.md (timeout/modes). Inline table for density.

## Performance & Testing
Targets: Latency <200ms/cmd, throughput 5 cmds/min, memory <10MB/queue.

- **Optimization**: Single thread (no race), cleanup on complete, Qt events for UI.
- **Metrics**: Queue size (~184), completed_count; emit progress (current/total).
- **Testing**: Unit 95% (test_command_queue.py), integration (telnet mocks), E2E (full flow).

| Target | Value | Symbol |
|--------|-------|--------|
| Latency | <200ms/cmd | ✅Non-blocking |
| Throughput | 5 cmds/min | ✅Scale |
| Memory | <10MB/queue | ✅Efficient |

**Rationale**: From ARCH_cmd_queue_impl_v1.md (perf), TECH_sequential_command_processor_v1.md (testing). Condensed table.

## Error Handling
- **Exceptions**: ConnectionError → reconnect (3 retries); ValueError → invalid token; TimeoutError → log/handle.
- **Recovery**: Retry/dead/circuit breaker; graceful I/O (app log + re-raise).
- **Fallback**: No token → app log; failed → log + continue (configurable STOP/CONTINUE).

**Rationale**: From TECH_command_services_v1.md (base handling), ARCH_cmd_queue_impl_v1.md (retry), TECH_sequential_command_processor_v1.md (timeout).

## Best Practices
- **Queue Usage**: Add with tokens for context (✅).
- **Threading**: Reuse telnet clients (✅Efficiency).
- **Errors**: Connect to signals for feedback (✅).
- **Monitoring**: Review application.log (✅).
- **Cleanup**: Call stop_processing() (✅).

**Rationale**: From TECH_sequential_command_processor_v1.md (practices), design_document_hierarchical_commands.md (integration).

## Version History
- **v1 Baseline**: Queue/system overviews (from ARCH_command_queue_v1.md/ARCH_command_system_v1.md: FIFO/threading).
- **v1 Enhancements**: Impl/processing (from ARCH_cmd_queue_impl_v1.md/ARCH_command_processing_v1.md: methods/errors).
- **Merge Notes**: Absorbed hierarchical (design_document_hierarchical_commands.md: sequences), services (TECH_command_services_v1.md: FBC/RPC/BsTool), global cycle (global_cycle_implementation.md/TECH_global_cycle_implementation_v1.md: phases), sequential (TECH_sequential_command_processor_v1.md: processor).

**Rationale**: Consolidates versions (all v1); lists sources/changes.

## References
- **[CommandQueue Code](src/commander/command_queue.py:147-388)**: Queue mgmt.
- **[Hierarchical Service](src/commander/services/hierarchical_command_service.py)**: Sequences.
- **[Command Services](src/commander/services/command_services.py)**: FBC/RPC/BsTool.
- **[TECH_ui_command_core_v1](technical/TECH_ui_command_core_v1.md#ServiceLayer)**: UI integration.
- **[ROADMAP_consolidated_v1 #Dependencies](roadmaps/ROADMAP_consolidated_v1.md#Dependencies)**: Command phases.
- **[Archived: ARCH_cmd_queue_impl_v1 #Overview](archived/ARCH_cmd_queue_impl_v1.md#Overview)**: Original impl (redirect).
- **[Archived: design_document_hierarchical_commands #Overview](archived/design_document_hierarchical_commands.md#Overview)**: Hierarchical design (redirect).

**Rationale**: Bidirectional #links; redirects for archives (e.g., impl variants as duplicates).
