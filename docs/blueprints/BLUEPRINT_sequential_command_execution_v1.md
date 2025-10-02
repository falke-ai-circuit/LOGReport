# 📐 Blueprint: Sequential Command Execution for Context Menu v1

## Overview
This blueprint details the design for integrating sequential command execution for FBC, RPC, and LOG subgroups via a new context menu action on node names. It adheres to MVP principles and leverages existing `CommandQueue` and `MockItem` patterns.

## Phases & Milestones
| Phase | Milestone | Deliverables | Status |
|---|---|---|---|
| **1. Data Structure Definition** | Define `MockItem` structure | `MockItem.data` schema | ✅ |
| **2. Context Menu Integration** | Add new context menu action | `ContextMenuService` modifications | ✅ |
| **3. Presenter Orchestration** | Implement `process_all_node_subgroup_commands` | `NodeTreePresenter` modifications | ✅ |
| **4. LOG Subgroup Processing** | Implement `process_all_log_subgroup_commands` | `NodeTreePresenter` new method | ✅ |
| **5. Testing & Validation** | Unit & Integration Tests | Test specifications | ⏳ |

## Design Details

### 1. MockItem Data Structure
The `MockItem.data` will encapsulate all `NodeToken` objects for the selected node, grouped by `token_type`.
```python
{
    "node_name": "AP01m",
    "node_ip": "192.168.0.1",
    "fbc_tokens": [NodeToken(...), ...],
    "rpc_tokens": [NodeToken(...), ...],
    "log_tokens": [NodeToken(...), ...]
}
```

### 2. ContextMenuService Modifications
*   **New QAction:** Add "Execute All Subgroup Commands (FBC, RPC, LOG)" to node context menus.
*   **`_get_current_item_from_data` Adaptation:** Modify to collect all FBC, RPC, and LOG `NodeToken`s from the selected node's children and populate the `MockItem.data` structure.
*   **Connection:** Connect the new QAction to `NodeTreePresenter.process_all_node_subgroup_commands`.

### 3. NodeTreePresenter Modifications
*   **`process_all_node_subgroup_commands(self, item_data: MockItem)`:**
    *   Receives `MockItem` with grouped `NodeToken`s.
    *   Calls `self.process_all_fbc_subgroup_commands(item_data.data[\"fbc_tokens\"])`.
    *   Calls `self.process_all_rpc_subgroup_commands(item_data.data[\"rpc_tokens\"])`.
    *   Calls `self.process_all_log_subgroup_commands(item_data.data[\"log_tokens\"])`.
*   **`process_all_log_subgroup_commands(self, log_tokens: List[NodeToken])`:**
    *   Iterates `log_tokens`.
    *   Extracts `node_id` (e.g., truncating 'm'/'r' from `token.name`).
    *   Constructs `bstool.exe` command: `f\"bstool.exe -errlog {node_id}\"`.
    *   Creates `QueuedCommand` and adds to `self.command_queue`.

## Execution Flow
`User Right-Clicks Node` → `NodeTreePresenter.show_context_menu` → `ContextMenuService.show_context_menu` → `_get_current_item_from_data` (Populates MockItem) → `MockItem with Grouped NodeTokens` → `ContextMenuService.add_QAction` → `User Clicks QAction` → `NodeTreePresenter.process_all_node_subgroup_commands(MockItem)` → `Call subgroup processing methods` → `Generate Commands` → `Add to CommandQueue` → `CommandQueue Processes Sequentially` → `Command Execution`.

## Architectural Adherence
*   **MVP:** Strict separation of concerns: `ContextMenuService` (View), `NodeTreePresenter` (Presenter), `CommandQueue`/Services (Model).
*   **Reusability:** Leverages existing `CommandQueue`, `NodeToken`, and `MockItem` patterns.
*   **Modularity:** New methods are encapsulated and consistent with existing command processing.

## Test Strategy
*   **Unit Tests:** Verify `_get_current_item_from_data` correctly populates `MockItem`. Test `process_all_node_subgroup_commands` orchestrates calls correctly. Test `process_all_log_subgroup_commands` generates correct `bstool.exe` commands and adds to `CommandQueue`.
*   **Integration Tests:** Simulate context menu interaction and verify sequential command execution through `CommandQueue` and `BsToolCommandService` (for LOG).