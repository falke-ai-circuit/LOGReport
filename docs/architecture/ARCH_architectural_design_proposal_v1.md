# 🏗️ Architectural Design Proposal: Telnet Command Population

## 🎯 Objective
Evaluate the architectural design for command population in the Telnet tab and propose a solution for the signal emission discrepancy in `NodeTreePresenter.on_node_selected`.

## 💡 Architectural Decision
**Chosen Hypothesis: H2** - The command population logic in the Telnet tab should be decoupled from `NodeTreePresenter` and instead listen to `log_file_selected_signal`, then derive and generate commands, requiring changes in an intermediary component (e.g., `CommanderPresenter` or a dedicated service).

**Rationale:**
*   **Separation of Concerns (MVP Pattern)**: `NodeTreePresenter`'s primary responsibility is managing the node tree UI. Generating specific Telnet commands from log file data is a business logic concern, not a UI presentation concern for the node tree itself. Decoupling this logic maintains a clean MVP architecture.
*   **Flexibility and Reusability (Service Layer Pattern)**: Centralizing command generation in a service or a higher-level presenter (like `CommanderPresenter`) allows for more flexible command generation rules and easier integration with other parts of the application that might also need to generate Telnet commands.
*   **Maintainability**: Changes to command generation logic will be isolated to the dedicated component, reducing the impact on `NodeTreePresenter` and `TelnetTab`.
*   **Consistency**: Aligns with the existing pattern where `CommanderPresenter` mediates updates to `TelnetTab` (e.g., `set_cmd_input_text_signal`).

## 📐 Design Blueprint: High-Level Implementation Plan

### Phase 1: Signal Rerouting and Command Generation
1.  **Modify `CommanderWindow._connect_signals`**:
    *   **Current**: The `node_tree_presenter.log_file_selected_signal` is connected to `session_manager.ip_changed.emit`.
    *   **Proposed**: Disconnect the existing connection. Connect `self.node_tree_presenter.log_file_selected_signal` to a new method in `CommanderPresenter`, for example, `self.commander_presenter.on_log_file_selected`.
2.  **Modify `NodeTreePresenter.on_node_selected`**:
    *   **Current**: Emits `filename: str`.
    *   **Proposed**: Emit a more comprehensive data structure (e.g., the `item_data` dictionary) to `CommanderPresenter.on_log_file_selected`. This `item_data` should contain all necessary context such as `log_path`, `token`, `token_type`, `node`, and `ip_address`.
3.  **Implement `CommanderPresenter.on_log_file_selected`**:
    *   This new method in `CommanderPresenter` will receive the `item_data` dictionary.
    *   It will extract `token`, `token_type`, and `node` information from `item_data`.
    *   Based on the `token_type`, it will utilize the appropriate command service (e.g., `fbc_service` or `rpc_service`) to generate the relevant Telnet command string.
    *   Finally, it will emit `self.set_cmd_input_text_signal.emit(generated_command)` to populate the Telnet tab's command input field. Optionally, it can also emit `self.switch_to_telnet_tab_signal.emit()` to switch to the Telnet tab and `self.set_cmd_focus_signal.emit()` to set focus on the command input.

### Phase 2: Refinement and Testing
1.  **Update `CommanderPresenter` `__init__`**: Ensure `CommanderPresenter` is initialized with `fbc_service` and `rpc_service` (these dependencies are already present).
2.  **Review `FbcCommandService` and `RpcCommandService`**: Confirm or add methods within these services for generating command strings from `token_id` and `node_name`. These methods should encapsulate the logic for constructing the actual Telnet commands.
3.  **Test Strategy**:
    *   **Unit Tests**: Create or update unit tests specifically for `CommanderPresenter.on_log_file_selected` to verify that it correctly generates commands for various `token_type`s and `item_data` inputs.
    *   **Integration Tests**: Update existing integration tests, such as `tests/commander/test_node_click_telnet_command_input.py`, to validate the end-to-end flow from node selection in the `NodeTreeView` to the correct command population in the `TelnetTab`'s input field.
    *   **Regression Tests**: Implement regression tests to ensure that existing functionalities, particularly any other connections to `log_file_selected_signal` (e.g., for `SessionManager.ip_changed.emit`), remain intact and are not adversely affected by these changes.

## 🗺️ Roadmap: Implementation Phases
*   **Phase 1 (Immediate)**: Implement signal rerouting and basic command generation within `CommanderPresenter`. This phase focuses on establishing the core communication flow.
*   **Phase 2 (Short-term)**: Refine the command generation logic within the respective services (`FbcCommandService`, `RpcCommandService`), update `NodeTreePresenter` to emit the richer `item_data`, and develop comprehensive unit and integration tests for the new functionality.
*   **Phase 3 (Future)**: If the command generation logic becomes significantly complex or requires broader sharing across the application, consider introducing a dedicated `TelnetCommandGeneratorService` to further encapsulate this responsibility.

## ⚙️ Technology Strategy
*   **PyQt6 Signals/Slots**: Continue to adhere to the established PyQt6 signal/slot mechanisms for robust and decoupled inter-component communication.
*   **Python Type Hinting**: Maintain and enhance Python type hinting throughout the codebase for improved code clarity, maintainability, and static analysis.
*   **Logging**: Fully utilize the existing logging framework for detailed debugging, operational insights, and error tracking during development and runtime.

## ✅ Test Strategy
*   **Unit Tests**: Focus on isolated testing of `CommanderPresenter.on_log_file_selected` and the command generation methods within `FbcCommandService` and `RpcCommandService`.
*   **Integration Tests**: Verify the complete end-to-end flow, starting from a node selection in the `NodeTreeView` and culminating in the accurate command population in the `TelnetTab`.
*   **Regression Tests**: Ensure that all existing functionalities, especially those related to node selection and log file handling, continue to operate as expected after the proposed changes.