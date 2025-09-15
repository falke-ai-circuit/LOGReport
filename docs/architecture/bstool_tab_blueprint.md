# BsTool Integration Blueprint

## 1. Introduction
This document outlines the blueprint for integrating `bstool.exe` into the LOGReport application. The integration will focus on bundling `bstool.exe` with the main executable, providing a right-click context menu action on `.log` files to execute `bstool.exe` with a fixed environment variable, and capturing its output to the selected log file. This design aims to leverage existing UI patterns and service integration mechanisms within the application.

## 2. Goals
- Integrate `bstool.exe` directly into the LOGReport application's build process.
- Enable execution of `bstool.exe` via a right-click context menu action on `.log` files, passing dynamic arguments (e.g., `bstool -errlog AP01`).
- Provide UI buttons for 'Execute', 'Copy to Log', 'Clear Terminal', and 'Clear Log' within the BsTool tab.
- Ensure `bstool.exe` is executed with the fixed environment variable `COMMUNICATION_LINE=AB01`.
- Capture and write the console output of `bstool.exe` to the selected `.log` file.
- Maintain UI/UX consistency with existing command execution patterns (e.g., FBC/RPC).
- Utilize a dedicated `BsToolCommandService` for backend logic and process management.

## 3. Architectural Decisions

### 3.1. Build Process Integration
`bstool.exe` will be bundled with the main `LOGReporter.exe` executable using PyInstaller.
- **PyInstaller Spec File Modification**: The `LOGReporter.spec` file will be updated to include `bstool.exe` as a data file. This will ensure `bstool.exe` is placed in a predictable location within the bundled application's directory structure (e.g., `dist/LOGReporter/_internal/bstool.exe`).
- **Access Path**: The `BsToolCommandService` will use a relative path to locate `bstool.exe` within the bundled application, ensuring it works correctly after deployment.

#### PyInstaller Spec File Details
The `LOGReporter.spec` file is modified to include `bstool.exe` in the `datas` array. This ensures that `bstool.exe` is copied to the `_internal` directory within the bundled application.

```python
# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

added_files = [
    ('path/to/bstool.exe', 'bstool.exe') # Example: Adjust 'path/to/bstool.exe' as needed
]

a = Analysis(
    ['src/main.py'],
    pathex=['.'],
    binaries=[],
    datas=added_files,
    hiddenimports=[],
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='LOGReporter',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_info=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
```
After bundling, `bstool.exe` will be accessible at `_internal/bstool.exe` relative to the main executable.

### 3.2. Context Menu Integration (`ContextMenuService`)
The existing `ContextMenuService` (`src/commander/services/context_menu_service.py`) will be extended to provide a new right-click action for `.log` files.
- **File Type Detection**: The `ContextMenuService` will identify when a `.log` file is selected in the file explorer or relevant UI component.
-   **New Menu Action**: A `QAction` named "Run BsTool on this file" (or similar) will be added to the context menu for `.log` files.
-   **Context Menu Command Construction**: The context menu action will construct a command for `bstool.exe` dynamically, for example, `bstool -errlog AP01`, where `AP01` is derived from the selected `.log` file's name (e.g., `AP01m_192-168-0-11.log` -> `AP01`).
-   **Presenter Integration**: This action will trigger a new method in the main presenter (e.g., `self.presenter.process_bstool_command(log_file_path, bstool_command_args)`), passing the full path of the selected `.log` file and the constructed `bstool` command arguments.

#### Context Menu Action Implementation
The `ContextMenuService` is responsible for dynamically adding the "Run BsTool on this file" action. When a `.log` file is detected, a `QAction` is created and connected to a presenter method. The `APxx` identifier is extracted from the log file name using regular expressions or string manipulation.

### 3.3. Service Component (`BsToolCommandService`)
A new `BsToolCommandService` (or an extension to an existing service if applicable) will be created as a QObject, responsible for managing the `bstool.exe` process and its interaction. This service will be analogous to `FbcCommandService` and `RpcCommandService`.

#### BsToolCommandService Class Structure
The `BsToolCommandService` inherits from `QObject` and manages the execution of `bstool.exe`.

```python
import subprocess
import os
from PyQt5.QtCore import QObject, pyqtSignal
from src.commander.services.threading_service import ThreadingService # Assuming this path

class BsToolCommandService(QObject):
    status_message_signal = pyqtSignal(str, int)
    bstool_output_signal = pyqtSignal(str, str)
    report_error = pyqtSignal(str)

    def __init__(self, log_writer, parent=None):
        super().__init__(parent)
        self.log_writer = log_writer
        self.threading_service = ThreadingService(parent=self) # Initialize ThreadingService

    def execute_bstool(self, log_file_path: str, bstool_command_args: str = ""):
        def _run_bstool():
            try:
                bstool_path = os.path.join(os.path.dirname(sys.executable), '_internal', 'bstool.exe') # Adjust path as needed
                command = [bstool_path] + shlex.split(bstool_command_args)

                env = os.environ.copy()
                env['COMMUNICATION_LINE'] = 'AB01'

                process = subprocess.Popen(
                    command,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    env=env
                )

                for line in iter(process.stdout.readline, ''):
                    self.bstool_output_signal.emit(line, log_file_path)
                process.stdout.close()

                stderr_output = process.stderr.read()
                if stderr_output:
                    self.report_error.emit(f"BsTool Error: {stderr_output}")

                process.wait()
                self.status_message_signal.emit("BsTool execution complete.", 3000)

            except FileNotFoundError:
                self.report_error.emit(f"Error: bstool.exe not found at {bstool_path}. Ensure it's bundled correctly.")
            except Exception as e:
                self.report_error.emit(f"Error executing BsTool: {e}")

        self.threading_service.run_in_thread(_run_bstool)

    def copy_to_log(self, content: str, log_file_path: str):
        self.log_writer.write_to_log(content, log_file_path)

    def clear_terminal(self):
        # This would typically involve emitting a signal to the UI to clear its display
        pass

    def clear_log(self, log_file_path: str):
        with open(log_file_path, 'w') as f:
            f.truncate(0)
        self.status_message_signal.emit(f"Log file {log_file_path} cleared.", 3000)
```

#### Signals and Slots
The `BsToolCommandService` communicates with the UI and other components via signals:
- `status_message_signal(message: str, duration: int)`: Emitted for displaying transient status messages in the main application status bar.
- `bstool_output_signal(output: str, log_file_path: str)`: Emitted with the console output from `bstool.exe` and the target log file path. A slot in the presenter or a dedicated log handling component receives this signal and uses the `LogWriter` to append the output to the specified `log_file_path`.
- `report_error(error_message: str)`: Emitted for reporting errors during execution to the UI.

### 3.4. Interaction Flow
1.  User right-clicks a `.log` file.
2.  `ContextMenuService` detects the `.log` file and adds "Run BsTool on this file" action.
3.  User selects the action.
4.  `ContextMenuService` triggers `self.presenter.process_bstool_command(log_file_path)`.
5.  The presenter calls `BsToolCommandService.execute_bstool(log_file_path, bstool_command_args)`.
6.  `BsToolCommandService` executes `bstool.exe` with `COMMUNICATION_LINE=AB01`, the `log_file_path`, and any provided `bstool_command_args`.
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