# BsTool Integration Implementation Roadmap

## 1. Introduction
This document outlines the phased implementation roadmap for integrating `bstool.exe` into the LOGReport application. It builds upon the architectural blueprint defined in `docs/architecture/bstool_tab_blueprint.md` and aims to provide a structured approach for development, testing, and integration, focusing on bundling `bstool.exe`, a right-click context menu trigger, and output redirection to log files.

## 2. Phases and Milestones

### Phase 1: Core Service Development (BsToolCommandService)

**Objective:** Implement the core logic for managing the `bstool.exe` process, including execution with a fixed environment variable and output capture.

**Milestones:**
-   **M1.1: `BsToolCommandService` Class Definition:** Create the `BsToolCommandService` class with basic structure, signals, and slots.
-   **M1.2: Process Launch & Termination:** Implement `execute_bstool(log_file_path: str, bstool_command_args: str = "")` method, including `subprocess` calls, setting the fixed `COMMUNICATION_LINE=AB01` environment variable, and process management.
-   **M1.3: Output Capture & Redirection:** Implement logic to capture `stdout` and `stderr` from `bstool.exe` in real-time and integrate with the `LogWriter` to append output to the specified log file.
-   **M1.4: UI Action Implementations:** Implement `copy_to_log()`, `clear_terminal()`, and `clear_log()` methods within the service.
-   **M1.5: Asynchronous Execution:** Integrate `ThreadingService` for non-blocking process management.
-   **M1.6: Unit Tests for `BsToolCommandService`:** Develop comprehensive unit tests covering all core functionalities, environment variable setting, output capture, and error handling, as well as the new UI action methods.

**Deliverables:**
-   `src/commander/services/bstool_command_service.py` (initial version)
-   Updated `src/commander/services/__init__.py`
-   Unit tests for `BsToolCommandService` in `tests/commander/unit/test_bstool_command_service.py`

### Phase 2: Context Menu Integration and Build Process

**Objective:** Integrate `bstool.exe` into the application's build, and enable its execution via a right-click context menu action on `.log` files.

**Milestones:**
-   **M2.1: PyInstaller Spec File Modification:** Update `LOGReporter.spec` to include `bstool.exe` as a data file, ensuring it's bundled correctly with the main executable.
-   **M2.2: `ContextMenuService` Extension:** Modify `src/commander/services/context_menu_service.py` to detect `.log` files and add a new `QAction` for "Run BsTool on this file", including dynamic command argument construction (e.g., `bstool -errlog AP01`).
-   **M2.3: Presenter Integration:** Implement a new method in the main presenter (e.g., `process_bstool_command`) to receive the `log_file_path` and `bstool_command_args` from the `ContextMenuService` and trigger `BsToolCommandService.execute_bstool()`.
-   **M2.4: Integration Tests:** Conduct comprehensive integration tests to verify the end-to-end flow from right-click to `bstool.exe` execution and output writing.

**Deliverables:**
-   Modified `LOGReporter.spec`
-   Modified `src/commander/services/context_menu_service.py`
-   Modified `src/commander/presenters/commander_presenter.py` (or relevant presenter)
-   Integration tests in `tests/commander/integration/test_bstool_context_menu_integration.py`

### Phase 3: Documentation and Refinement

**Objective:** Finalize documentation, perform necessary refinements, and prepare for deployment.

**Milestones:**
-   **M3.1: User Guide Update:** Add a section to the user guide (`docs/user/user_guide.md`) on how to use the "Run BsTool" context menu action for `.log` files.
-   **M3.2: Technical Documentation:** Update relevant technical documentation with implementation details for `bstool.exe` bundling, context menu integration, `BsToolCommandService`, and the new UI actions.
-   **M3.3: System Tests:** Perform a full build and verify the right-click action on a `.log` file correctly triggers `bstool.exe` with the environment variable and appends its output.
-   **M3.4: Performance Optimization:** Identify and address any performance bottlenecks related to `bstool.exe` execution and output handling.

**Deliverables:**
-   Updated `docs/user/user_guide.md`
-   Updated `docs/architecture/bstool_tab_blueprint.md` (already done in previous step)
-   Updated `docs/technical/` documentation (new or existing files)
-   Finalized code with any necessary refinements
-   Updated build scripts/configuration

## 3. Dependencies
-   Completion of `BsTool Integration Blueprint` (`docs/architecture/bstool_tab_blueprint.md`).
-   Availability of `bstool.exe` for bundling and testing.
-   Existing `ThreadingService` and `LogWriter` components.

## 4. Risks and Mitigation
-   **Risk:** `bstool.exe` bundling issues with PyInstaller (e.g., incorrect path resolution, missing dependencies).
    -   **Mitigation:** Thorough testing of the PyInstaller spec file; use PyInstaller hooks if necessary.
-   **Risk:** Environment variable `COMMUNICATION_LINE` not correctly propagated to `bstool.exe`.
    -   **Mitigation:** Verify subprocess environment setup in unit and integration tests.
-   **Risk:** `bstool.exe` compatibility issues (e.g., unexpected output formats, non-standard input/output).
    -   **Mitigation:** Implement flexible output parsing in `BsToolCommandService`; provide clear error messages.
-   **Risk:** Performance degradation due to frequent `bstool.exe` execution or large output.
    -   **Mitigation:** Optimize `subprocess` calls; consider buffering output before writing to log.
-   **Risk:** Security vulnerabilities from executing external commands.
    -   **Mitigation:** Ensure `bstool.exe` is a trusted executable; restrict execution to internal, controlled paths.

## 5. Future Enhancements (Post-Roadmap)
-   Allow configuration of the `COMMUNICATION_LINE` environment variable through a secure settings mechanism (if requirements change).
-   Implement progress indication for long-running `bstool.exe` executions.
-   Advanced output parsing and syntax highlighting for `bstool.exe` output within the log file.