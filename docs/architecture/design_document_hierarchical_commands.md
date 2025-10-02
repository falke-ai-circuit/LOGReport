# 🏗️ Architecture: Hierarchical Command Execution Design

## 🎯 Objective
To design a robust mechanism for defining, presenting, and executing hierarchical commands within the LOGReport application, ensuring proper identification, sequencing, error handling, and UI integration.

## 💡 Design Rationale
Extending existing structures (`nodes.json`) and introducing a dedicated service (`HierarchicalCommandService`) minimizes disruption while providing clear separation of concerns for managing complex command workflows. Dynamic menu generation ensures flexibility and scalability.

## 🏛️ Architectural Decisions

### 1. Structured Definition of Hierarchical Commands
- **Decision**: Extend `nodes.json` to include a `hierarchical_commands` section for each node/token type.
- **Details**:
    - Each node/token entry in `nodes.json` will have an optional `hierarchical_commands` field.
    - This field will be a dictionary: `{"Hierarchical Command Name": [command_definition_1, command_definition_2, ...]}`.
    - Each `command_definition` will be an object specifying `type` (FBC, RPC, LOG, BSTool) and `parameters`, mirroring existing command structures.
- **Example `nodes.json` Snippet**:
    ```json
    {
      "FBC_NODE_TYPE": {
        "commands": [
          {"type": "FBC", "command": "fbc_command_1"},
          ...
        ],
        "hierarchical_commands": {
          "Full FBC Sequence": [
            {"type": "FBC", "command": "fbc_init"},
            {"type": "RPC", "command": "rpc_status_check", "args": ["status"]},
            {"type": "FBC", "command": "fbc_final_step"}
          ],
          "Another Sequence": [
            {"type": "LOG", "command": "log_start"},
            {"type": "BSTool", "command": "bstool_diag"}
          ]
        }
      }
    }
    ```

### 2. ContextMenuService Presentation
- **Decision**: Modify `ContextMenuService` to dynamically generate submenus for hierarchical commands.
- **Details**:
    - `ContextMenuService` will detect the `hierarchical_commands` field in a selected node's configuration.
    - For each entry in `hierarchical_commands`, it will create a top-level `QAction` (menu item).
    - Clicking this top-level `QAction` will dynamically generate and display a `QMenu` (submenu) containing individual `QAction`s for each command within that hierarchical sequence.
    - The `triggered` signal of the top-level `QAction` will be connected to a new method in `CommanderPresenter` to initiate the hierarchical execution.

### 3. Sequential Execution Logic, Error Handling, and Progress Reporting
- **Decision**: Introduce a new `HierarchicalCommandService` (or enhance `SequentialCommandProcessor` if suitable) to manage execution.
- **Details**:
    - **`HierarchicalCommandService`**:
        - Takes a `NodeToken` and the name of the hierarchical command as input.
        - Retrieves the sequence of command definitions from the `NodeToken`'s `hierarchical_commands`.
        - Iterates through each command definition:
            - Constructs a `QueuedCommand` object for each sub-command.
            - Enqueues the `QueuedCommand` into the existing `CommandQueue`.
            - Waits for the completion of each sub-command before proceeding to the next.
        - **Error Handling**:
            - Configurable behavior: `STOP_ON_ERROR` (default) or `CONTINUE_ON_ERROR`.
            - If `STOP_ON_ERROR`, the sequence halts, and an error message is reported.
            - If `CONTINUE_ON_ERROR`, errors are logged, and the sequence proceeds.
        - **Progress Reporting**:
            - Emits signals (e.g., `command_started`, `command_completed`, `sequence_progress`, `sequence_finished`, `sequence_error`).
            - Signals will carry information like current command index, total commands, command status, and overall sequence status.

### 4. Updates to NodeToken and CommanderPresenter
- **Decision**: Update `NodeToken` data model and `CommanderPresenter` for integration.
- **Details**:
    - **`NodeToken`**:
        - The `NodeToken` dataclass (or equivalent) will be extended to include an optional `hierarchical_commands: Dict[str, List[Dict]]` field. This ensures the command definitions are directly associated with the node.
    - **`CommanderPresenter`**:
        - Add a new public method: `execute_hierarchical_command(node_token: NodeToken, command_name: str)`.
        - This method will be called by `ContextMenuService` when a hierarchical command is selected.
        - It will instantiate `HierarchicalCommandService` (or call its static method) and pass the `node_token` and `command_name`.
        - It will subscribe to the `HierarchicalCommandService`'s progress and status signals to update the main UI (e.g., status bar, dedicated progress indicator, log output).

## 🚧 Risks & Mitigations
- **Design Complexity**: Modular design with clear interfaces for `HierarchicalCommandService` and `ContextMenuService` modifications.
- **Tight Coupling**: Ensure `HierarchicalCommandService` interacts with `CommandQueue` via its public API, and `ContextMenuService` interacts with `CommanderPresenter` via defined interfaces.
- **Performance Impact**: Sequential execution is inherent. For very long sequences, consider adding a confirmation dialog or a background worker with cancellable operations.

## 🛣️ Roadmap & Implementation Phases
1. **Phase 1: Data Model & Service Definition**
    - Update `NodeToken` to include `hierarchical_commands`.
    - Implement `HierarchicalCommandService` with core sequential execution and basic error handling.
2. **Phase 2: UI Integration**
    - Modify `ContextMenuService` to generate hierarchical menus.
    - Update `CommanderPresenter` to initiate hierarchical command execution and display progress.
3. **Phase 3: Robustness & Refinements**
    - Enhance error handling (e.g., retry logic, detailed error messages).
    - Implement comprehensive progress reporting in the UI.
    - Add unit and integration tests for all new components.

## ✅ Test Strategy
- **Unit Tests**: For `HierarchicalCommandService` (sequential execution, error handling, signal emission), `ContextMenuService` (menu generation logic), `CommanderPresenter` (delegation, UI updates).
- **Integration Tests**: End-to-end tests simulating user interaction with context menus, triggering hierarchical commands, and verifying sequential execution, error handling, and UI feedback.
- **Edge Cases**: Test empty sequences, sequences with invalid commands, commands that fail, and long-running sequences.