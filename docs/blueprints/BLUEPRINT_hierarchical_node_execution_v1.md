# BLUEPRINT Hierarchical Node Execution v1

## Overview
Extend existing subgroup batch processing (FBC/RPC via process_all_*_subgroup_commands) to full node-level recursion, enabling one-click execution of all FBC + RPC (print) + LOG (clear batch) subcommands sequentially via CommandQueue. Addresses user efficiency for hierarchical nodes (e.g., AP01m → all children). Reuses SequentialCommandProcessor, services (Fbc/Rpc/BsToolCommandService), NodeTreePresenter traversal. Constraints: No new deps, <5s/node perf, error isolation per token. Non-goals: VNC/OCR integration.

## Architecture
### Components
- **NodeTreePresenter** (`src/commander/presenters/node_tree_presenter.py`): Add recursive traversal `get_all_node_tokens(node_item: QTreeWidgetItem) → List[NodeToken]` (filter FBC/RPC/LOG children via item.data(0, Qt.UserRole)['type']).
- **SequentialCommandProcessor** (`src/commander/services/sequential_command_processor.py`): Extend `process_all_node_commands(tokens: List[NodeToken], node_name: str)` - group by type (FBC/RPC/LOG), queue via services (fbc_service.queue_fieldbus_command, rpc_service.queue_rpc_command('print'), bstool_service.batch_clear_logs for LOG paths).
- **ContextMenuService** (`src/commander/services/context_menu_service.py`): In `show_context_menu`, for node items (`item_data['type'] == 'node'`): Add QAction('Execute All Node Commands') → connect to presenter.process_all_node_commands(node_name). Emit progress via status_message_signal.
- **ContextMenuFilterService** (`src/commander/services/context_menu_filter.py`): Evaluate new rule for `command_type='all_node'`, `command_category='node'`.
- **BsToolCommandService** (`src/commander/services/bstool_command_service.py`): Add `batch_clear_logs(paths: List[str])` - loop `clear_log(path)` with queue isolation.

### Flow
1. Right-click node (e.g., AP01m) → ContextMenuService adds 'Execute All' (filtered).
2. Trigger → NodeTreePresenter.get_all_node_tokens (recursive: loop childCount(), collect tokens by section_type).
3. Group tokens (FBC/RPC/LOG) → SequentialCommandProcessor.process_all_node_commands (queue FBC → RPC print → LOG clear).
4. CommandQueue executes sequentially, emit signals for progress (per token status/error).
5. LogWriter appends outputs; error isolation (continue on failure).

| Integration Point | Description | Ref |
|-------------------|-------------|-----|
| Traversal | Recursive QTreeWidgetItem loop, max_depth=10 | [node_tree_presenter.py](src/commander/presenters/node_tree_presenter.py) |
| Queuing | Grouped service calls, atomic queue.add | [sequential_command_processor.py](src/commander/services/sequential_command_processor.py:248) |
| Filtering | should_show_command(node_name, 'ALL', 'all_node', 'node') | [context_menu_filter.py](src/commander/services/context_menu_filter.py:84) |
| LOG Batch | bstool_service.batch_clear_logs (reuse clear_log) | [bstool_command_service.py](src/commander/services/bstool_command_service.py) |

## Implementation Plan
### Phase 1: Traversal (1-2 days)
- Add `get_all_node_tokens` in NodeTreePresenter (recursive collect, filter types).
- Milestone: Unit test mock tree → assert tokens list (FBC/RPC/LOG, empty/leaf edges).
- Deliverable: Updated presenter.py, test_node_traversal.py.

### Phase 2: Batch Processing (2-3 days)
- Extend SequentialCommandProcessor.process_all_node_commands (group/queue by type; LOG via new BsTool batch_clear).
- Integrate services (reuse queue_fieldbus_command etc.).
- Milestone: Unit tests 80% (grouping, queuing order, error isolation via mock failures).
- Deliverable: Updated processor.py, bstool_service.py, test_batch_commands.py.

### Phase 3: Menu Integration (1 day)
- ContextMenuService: Add QAction for nodes, connect to presenter.process_all_node_commands.
- Emit progress signals (status_message for start/per-token/end).
- Milestone: Integration test menu trigger → verify signal emission/queue add.
- Deliverable: Updated context_menu_service.py, test_menu_node_action.py.

### Phase 4: Filtering & Validation (1 day)
- Add rule example to menu_filter_rules.json (command_type='all_node').
- E2E: Load nodes.json, right-click AP01m → assert sequential FBC→RPC→LOG queue, progress logs.
- Milestone: E2E test full flow (<5s, no overlap, user-visible status).
- Deliverable: Updated filter rules example, test_e2e_node_execution.py.

Risks: Recursion depth (>10) → max_depth param; UI block → async signals; LOG batch perf → queue limits. Mitigation: Tests enforce.

## Test Strategy
- **Unit (80% coverage)**: Traversal (mock tree recursion), batch (group/queue mocks, error continue), filter (rule eval).
- **Integration (60%)**: Menu→presenter→processor chain (mock Qt, assert signals/queue state).
- **E2E (40%)**: Full flow on sample nodes.json (pytest-qt, assert logs/queue execution order, perf <5s).
- Tools: pytest, mock (Qt items/services), nodes_test.json. Oracles: O1 sequential no-overlap (queue order), O2 filtering/integration (visible actions), O3 progress/status (signals emitted).

## Cross-References
- [Service Layer #Overview](docs/technical/TECH_command_services_v1.md#Overview) 🔗 [Queue #Overview](docs/architecture/ARCH_command_system_v1.md#Overview)
- [Menu Filtering #Overview](docs/blueprints/BLUEPRINT_context_menu_v1.md#Overview) 🔗 [Traversal #Overview](docs/technical/TECH_node_resolution_v1.md#Overview)

Metadata: {type: BLUEPRINT, created: 2025-10-01, updated: 2025-10-01, word_count: 450, similarity_hash: SHA256:abc123, obsolete_check: false}