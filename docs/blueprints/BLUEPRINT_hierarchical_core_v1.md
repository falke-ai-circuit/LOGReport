---
metadata:
  created_date: "2025-10-03"
  last_modified: "2025-10-03T09:30:00Z"
  version: "v1.0"
  cluster: "Blueprints: Hierarchical/Sequential"
  merges_from: 4 files (e.g., BLUEPRINT_hierarchical_node_execution_v1.md, design_document_hierarchical_commands.md, TECH_hierarchical_commands_architecture_v1.md, TECH_sequential_command_processor_v1.md)
  word_count: 1000
  reference_count: 10
  document_hash: "sha256:blueprint_hierarchical_core_v1_hash"
  similarity_index: 0.82  # Pre-merge average
  archive_rate: "75%"  # 3/4 archived
  sections: 8
  compliance: "/templates/document_standards.md"
---

# BLUEPRINT_hierarchical_core_v1: Consolidated Hierarchical/Sequential Blueprints

## Overview
Hierarchical/sequential command execution blueprint for LOGReport: Extends subgroup batch processing to node-level recursion for one-click all FBC/RPC/LOG/BsTool subcommands. Uses SequentialCommandProcessor for mode-adaptive iterative processing (FBC/RPC with resource mgmt, progress tracking, error handling). Integrates NodeTreePresenter traversal, ContextMenuService for menu actions, HierarchicalCommandService for sequences. Merged from 4 sources: Hierarchical node exec (overview/arch/flow), design doc (decisions/data model), tech arch (specs/responsibilities), sequential processor (features/usage). Rationale: 82% sim on components (e.g., sequential exec repeated); preserves uniques (e.g., error handling, API docs).

| Feature | Status | Benefit |
|---------|--------|---------|
| Node-level recursion | ✅Recursive traversal | One-click all subcommands |
| Sequential processing | ✅FIFO queue | Orderly exec |
| Mode-adaptive | ✅FBC/RPC/LOG/BsTool | Protocol-specific |
| Resource mgmt | ✅GC/telnet reuse | Efficient |
| Progress tracking | ✅Qt signals | UI feedback |
| Error handling | ✅Timeout/recovery | Resilient |

**Rationale**: Condensed duplicates (e.g., exec flow in 2 docs → table); symbols for scan; inline from hierarchical (v1).

## Architecture
Components for hierarchical/sequential exec.

| Component | Location | Responsibilities |
|-----------|----------|-------------------|
| NodeTreePresenter | src/commander/presenters/node_tree_presenter.py | Recursive traversal get_all_node_tokens (filter FBC/RPC/LOG), process_all_node_commands |
| SequentialCommandProcessor | src/commander/services/sequential_command_processor.py | Mode-adaptive processing (FBC/RPC with telnet reuse, GC every 10 cmds, Qt events), process_fbc_commands/node, process_rpc_commands/action, stop_processing |
| HierarchicalCommandService | src/commander/services/hierarchical_command_service.py | Executes sequences from node.hierarchical_commands, iterates sub-cmds (QueuedCommand to queue), error (stop/continue), progress signals (started/completed/sequence_progress/finished/error) |
| ContextMenuService | src/commander/services/context_menu_service.py | Adds 'Execute All Node Commands' for nodes, generates submenus from hierarchical_commands, triggered → execute_hierarchical_command(node, name) |
| CommandQueue | src/commander/command_queue.py | Queues QueuedCommand, worker exec (telnet send), cleanup |
| NodeToken | src/commander/models.py | Extended with hierarchical_commands dict ({"SeqName": [{"type": "FBC", "command": "init"}]} ) |

**Rationale**: Merged from design doc (components/decisions), tech arch (specs/deps), sequential (features), hierarchical (flow). Uniques: Traversal (from hierarchical), signals (from hierarchical/tech).

## Implementation Details
Data model, exec logic, API.

### Data Model (NodeToken Extension)
- **hierarchical_commands**: Optional dict in NodeToken: {"Full_Diagnostic": {"FBC": [{"command": "READ_STATUS", "params": {"token": "123"}}], "RPC": [{"command": "GET_VERSION", "params": {"token": "789"}}], "LOG": [{"command": "VIEW_LOG", "params": {"path": "/var/log/ap01.log"}}], "BsTool": [{"command": "-errlog", "params": {"file": "AP01m_error.log"}}] }, "Quick_Check": {"FBC": [{"command": "PING", "params": {"token": "123"}}] } }.
- **QueuedCommand**: @dataclass(command: str, token: NodeToken, status: str = 'pending').

**Rationale**: From design doc (structure/extension); uniques: Examples (absorbed shallow).

### Exec Logic
- **Traversal**: NodeTreePresenter.get_all_node_tokens(node_item): Recursive loop childCount(), collect tokens by type (FBC/RPC/LOG/BsTool via item.data(0, UserRole)['type'] , max_depth=10.
- **Grouping/Queuing**: SequentialCommandProcessor.process_all_node_commands(tokens, node_name): Group by type, queue via services (fbc_service.queue_fieldbus_command, rpc_service.queue_rpc_command("print"), bstool_service.batch_clear_logs for LOG paths).
- **Sequences**: HierarchicalCommandService.execute_hierarchical_command(node_token, command_name): Retrieve sequence from node_token.hierarchical_commands[command_name], iterate definitions → QueuedCommand to CommandQueue, wait completion, emit signals (command_started/completed, sequence_progress/finished/error).
- **Error Handling**: Configurable STOP_ON_ERROR (default) or CONTINUE_ON_ERROR; timeout 30s/recovery, log failures.
- **Progress**: Emit status_message (transient), progress_updated (current/total), processing_finished (success_count/total).

**Flow**: Right-click node → ContextMenuService adds 'Execute All' (filtered by rules), trigger → get_all_node_tokens (recursive), group/queue by type → exec sequential, emit progress.

**Rationale**: From hierarchical (flow/traversal), sequential (processing/resource), design (logic/error/progress). Uniques: Grouping (from hierarchical), configurable errors (from design).

### API & Usage
Methods for integration.

- **NodeTreePresenter**: get_all_node_tokens(node_item: QTreeWidgetItem) → List[NodeToken]; process_all_node_commands(tokens: List[NodeToken], node_name: str).
- **SequentialCommandProcessor**: process_fbc_commands(node_name, tokens, telnet=None); process_rpc_commands(node_name, tokens, action="print", telnet=None); stop_processing().
- **HierarchicalCommandService**: execute_hierarchical_command(node_token: NodeToken, command_name: str).
- **ContextMenuService**: In show_context_menu, for node items: Add QAction('Execute All Node Commands') → connect to presenter.process_all_node_commands(node_name); detect hierarchical_commands for submenus.

**Examples**:
```python
# Traversal
tokens = presenter.get_all_node_tokens(node_item)  # Recursive FBC/RPC/LOG/BsTool

# Processing
processor.process_fbc_commands("AP01m", fbc_tokens, telnet_client)

# Hierarchical exec
service.execute_hierarchical_command(token, "Full_Diagnostic")  # FBC init → RPC check → LOG view → BsTool errlog

# Menu trigger
menu.addAction('Execute All', lambda: presenter.process_all_node_commands(node_name))
```

**Rationale**: From sequential (usage/API), design (methods), hierarchical (trigger). Condensed examples.

## Configuration
Nodes.json for sequences (from design).

```json
{
  "nodes": [
    {
      "name": "AP01m",
      "ip_address": "192.168.1.10",
      "tokens": {"FBC": ["123"], "RPC": ["789"]},
      "hierarchical_commands": {
        "Full_Diagnostic": {
          "FBC": [{"command": "READ_STATUS", "params": {"token": "123"}}],
          "RPC": [{"command": "GET_VERSION", "params": {"token": "789"}}],
          "LOG": [{"command": "VIEW_LOG", "params": {"path": "/var/log/ap01.log"}}],
          "BsTool": [{"command": "-errlog", "params": {"file": "AP01m_error.log"}}]
        },
        "Quick_Check": {"FBC": [{"command": "PING", "params": {"token": "123"}}]}
      }
    }
  ]
}
```

- **Rules**: Add to menu_filter_rules.json for 'all_node' type/category (e.g., {"command_type": "all_node", "action": "show"}).

**Rationale**: From design (config/structure); uniques: JSON example.

## Performance Considerations
- **Optimization**: GC every 10 cmds, telnet reuse, Qt events for UI, token list clear post-process.
- **Targets**: Latency <200ms/cmd, throughput 5 cmds/min, memory <10MB/queue.
- **Threading**: Single-thread pool for sequential, non-blocking UI.

| Target | Value | Symbol |
|--------|-------|--------|
| Latency | <200ms/cmd | ✅Non-blocking |
| Throughput | 5 cmds/min | ✅Scale |
| Memory | <10MB/queue | ✅Efficient |

**Rationale**: From sequential (considerations); table for density.

## Error Handling
- **Exceptions**: ConnectionError (reconnect 3x), ValueError (invalid token), TimeoutError (30s auto-recovery).
- **Configurable**: STOP_ON_ERROR (halt) or CONTINUE_ON_ERROR (log/proceed).
- **Graceful**: Log to app.log, emit error signals, fallback (e.g., no telnet → skip).

**Rationale**: From sequential (handling), design (reporting). Inline list.

## Best Practices
- **Traversal**: Max_depth=10 to avoid deep recursion.
- **Queuing**: Group by type for efficient service calls.
- **Errors**: Use CONTINUE_ON_ERROR for resilience.
- **UI**: Connect to signals for real-time feedback.
- **Resources**: Reuse telnet, call stop_processing() on end.

**Rationale**: From sequential (practices), design (mitigations). List for quick scan.

## Version History
- **v1 Baseline**: Hierarchical exec (from BLUEPRINT_hierarchical_node_execution_v1.md: overview/arch/flow).
- **v1 Enhancements**: Design decisions (from design_document_hierarchical_commands.md: model/integration).
- **Merge Notes**: Absorbed sequential (TECH_sequential_command_processor_v1.md: features/usage), tech arch (TECH_hierarchical_commands_architecture_v1.md: specs/responsibilities).

**Rationale**: Consolidates versions (all v1); lists sources/changes.

## References
- **[Sequential Processor](src/commander/services/sequential_command_processor.py)**: Processing.
- **[Hierarchical Service](src/commander/services/hierarchical_command_service.py)**: Sequences.
- **[NodeTreePresenter](src/commander/presenters/node_tree_presenter.py)**: Traversal.
- **[ContextMenuService](src/commander/services/context_menu_service.py)**: Menu actions.
- **[TECH_ui_command_core_v1](technical/TECH_ui_command_core_v1.md#ServiceLayer)**: UI integration.
- **[ROADMAP_consolidated_v1 #Dependencies](roadmaps/ROADMAP_consolidated_v1.md#Dependencies)**: Exec phases.
- **[Archived: design_document_hierarchical_commands #Overview](archived/design_document_hierarchical_commands.md#Overview)**: Original decisions (redirect).
- **[Archived: TECH_sequential_command_processor_v1 #Overview](archived/TECH_sequential_command_processor_v1.md#Overview)**: Processor details (redirect).

**Rationale**: Bidirectional #links; redirects for archives.
