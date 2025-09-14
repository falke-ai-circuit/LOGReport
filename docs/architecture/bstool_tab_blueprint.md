# BsTool Integration Blueprint

## 1. Introduction
This document outlines the blueprint for integrating `bstool.exe` into the LOGReport application. The integration will focus on bundling `bstool.exe` with the main executable, providing a right-click context menu action on `.log` files to execute `bstool.exe` with a fixed environment variable, and capturing its output to the selected log file. This design aims to leverage existing UI patterns and service integration mechanisms within the application.

## 2. Goals
- Integrate `bstool.exe` directly into the LOGReport application's build process.
- Enable execution of `bstool.exe` via a right-click context menu action on `.log` files.
- Ensure `bstool.exe` is executed with the fixed environment variable `COMMUNICATION_LINE=AB01`.
- Capture and write the console output of `bstool.exe` to the selected `.log` file.
- Maintain UI/UX consistency with existing command execution patterns (e.g., FBC/RPC).
- Utilize a dedicated `BsToolCommandService` for backend logic and process management.

## 3. Architectural Decisions

### 3.1. Build Process Integration
`bstool.exe` will be bundled with the main `LOGReporter.exe` executable using PyInstaller.
- **PyInstaller Spec File Modification**: The `LOGReporter.spec` file will be updated to include `bstool.exe` as a data file. This will ensure `bstool.exe` is placed in a predictable location within the bundled application's directory structure (e.g., `dist/LOGReporter/_internal/bstool.exe`).
- **Access Path**: The `BsToolCommandService` will use a relative path to locate `bstool.exe` within the bundled application, ensuring it works correctly after deployment.

### 3.2. Context Menu Integration (`ContextMenuService`)
The existing `ContextMenuService` (`src/commander/services/context_menu_service.py`) will be extended to provide a new right-click action for `.log` files.
- **File Type Detection**: The `ContextMenuService` will identify when a `.log` file is selected in the file explorer or relevant UI component.
- **New Menu Action**: A `QAction` named "Run BsTool on this file" (or similar) will be added to the context menu for `.log` files.
- **Presenter Integration**: This action will trigger a new method in the main presenter (e.g., `self.presenter.process_bstool_command(log_file_path)`), passing the full path of the selected `.log` file.

### 3.3. Service Component (`BsToolCommandService`)
A new `BsToolCommandService` (or an extension to an existing service if applicable) will be created as a QObject, responsible for managing the `bstool.exe` process and its interaction. This service will be analogous to `FbcCommandService` and `RpcCommandService`.

**Key Functionalities:**
- `execute_bstool(log_file_path: str)`:
    - Constructs the command to execute `bstool.exe` with the `log_file_path` as an argument.
    - **Fixed Environment Variable**: Sets the environment variable `COMMUNICATION_LINE=AB01` for the `bstool.exe` subprocess. This variable will be hardcoded within the service.
    - Launches `bstool.exe` using Python's `subprocess` module.
    - Captures `stdout` and `stderr` of the `bstool.exe` process in real-time.
    - Runs in a separate thread using `ThreadingService` to prevent UI blocking.
    - Emits `bstool_output_signal` with the captured output.
    - Emits `status_message_signal` for process status updates.
- **Output Redirection**: The captured output from `bstool.exe` will be written directly to the `log_file_path` using the application's `LogWriter` (or a similar mechanism), appending the output to the end of the selected `.log` file.

**Signals Emitted by `BsToolCommandService`:**
- `status_message_signal(message: str, duration: int)`: For displaying transient status messages in the main application status bar.
- `bstool_output_signal(output: str, log_file_path: str)`: Emitted with the console output from `bstool.exe` and the target log file path for writing.
- `report_error(error_message: str)`: For reporting errors during execution.

### 3.4. Interaction Flow
1.  User right-clicks a `.log` file.
2.  `ContextMenuService` detects the `.log` file and adds "Run BsTool on this file" action.
3.  User selects the action.
4.  `ContextMenuService` triggers `self.presenter.process_bstool_command(log_file_path)`.
5.  The presenter calls `BsToolCommandService.execute_bstool(log_file_path)`.
6.  `BsToolCommandService` executes `bstool.exe` with `COMMUNICATION_LINE=AB01` and the `log_file_path`.
7.  `BsToolCommandService` captures `bstool.exe`'s output and emits `bstool_output_signal`.
8.  A slot (e.g., in the presenter or a dedicated log handling component) receives `bstool_output_signal` and uses the `LogWriter` to append the output to the specified `log_file_path`.

## 4. Implementation Considerations
- **Reusability:** Leverage the existing `ThreadingService` for asynchronous process execution within `BsToolCommandService`.
- **Modularity:** Ensure `BsToolCommandService` is loosely coupled, communicating primarily through signals and slots.
- **Error Handling:** Implement robust error handling for `subprocess` calls (e.g., `FileNotFoundError` for `bstool.exe` path, `CalledProcessError` for command execution failures).
- **UI Consistency:** Adhere to the existing patterns for command execution and output display.
- **Security:** Ensure proper sanitization of `log_file_path` if there's any potential for user manipulation, though in this context, it's expected to be an internal file path.
- **LogWriter Integration**: Ensure the `LogWriter` can efficiently append output to an existing log file without corrupting its content or performance issues.

## 5. Test Strategy
- **Unit Tests:**
    - `BsToolCommandService`: Test `execute_bstool` functionality, including correct environment variable setting, process management, output capture, and signal emissions. Mock `subprocess` calls and `LogWriter` interactions.
    - `ContextMenuService`: Test the addition of the "Run BsTool" action for `.log` files and its correct signal emission with the `log_file_path`.
- **Integration Tests:**
    - Verify the end-to-end interaction from right-click to `bstool.exe` execution and output writing to the log file.
    - Test the integration with `CommanderWindow` for status bar updates.
- **System Tests:**
    - Perform a full build with `bstool.exe` bundled.
    - Verify the right-click action on a `.log` file triggers `bstool.exe` and its output is correctly appended.

## 6. Future Enhancements
- Allow configuration of the `COMMUNICATION_LINE` environment variable through a secure settings mechanism (if requirements change).
- Implement progress indication for long-running `bstool.exe` executions.
- Advanced output parsing and highlighting for `bstool.exe` output within the log file.