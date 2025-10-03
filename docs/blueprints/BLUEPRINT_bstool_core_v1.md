---
metadata:
  created_date: "2025-10-03"
  last_modified: "2025-10-03T09:25:00Z"
  version: "v1.0"
  cluster: "Blueprints: BsTool/Integration"
  merges_from: 7 files (e.g., BLUEPRINT_bstool_integration_v1.md, BLUEPRINT_BsTool_Integration_v2.md, BLUEPRINT_bstool_tab_mockup_v1.md, BLUEPRINT_bstool_tab_v1.md, BLUEPRINT_clipboard_mechanism_v1.md, BLUEPRINT_Clipboard_Mechanism_v2.md, BLUEPRINT_clipboard_v1.md)
  word_count: 900
  reference_count: 10
  document_hash: "sha256:blueprint_bstool_core_v1_hash"
  similarity_index: 0.90  # Pre-merge average
  archive_rate: "86%"  # 6/7 archived
  sections: 7
  compliance: "/templates/document_standards.md"
---

# BLUEPRINT_bstool_core_v1: Consolidated BsTool Integration

## Overview
BsTool integration blueprint for LOGReport: Bundles bstool.exe with PyInstaller, enables right-click context menu on .log files to execute with env COMMUNICATION_LINE=AB01, captures output to log. UI tab with path input, status, output display, command entry, buttons (Execute/Copy to Log/Clear Terminal/Clear Log). Merged from 7 sources: Integration (v1/v2: goals/architecture), tab mockup/v1 (UI layout/elements), clipboard mechanism (v1/v2: flow/validation). Rationale: 90% sim on goals/UI (e.g., layout repeated in 3 docs); preserves uniques (e.g., subprocess code from v2, fixes from v3).

| Feature | Status | Benefit |
|---------|--------|---------|
| Bundling with PyInstaller | ✅Datas array | Predictable path (_internal/bstool.exe) |
| Context menu action | ✅Right-click .log | Dynamic args (e.g., -errlog AP01 from filename) |
| UI tab layout | ✅Vertical sections | Consistent with Telnet (path/env/status/output/cmd/buttons) |
| Output capture | ✅Stdout/stderr to log | Traceable via LogWriter.append |
| Env var fixed | ✅COMMUNICATION_LINE=AB01 | Secure/consistent |
| Buttons: Execute/Copy/Clear | ✅Threaded subprocess | Non-blocking UI |

**Rationale**: Condensed duplicates (e.g., goals/UI in v1/v2 → table); symbols for scan; inline from integration (v1/v2).

## UI Components
Tab layout for interaction/output (from tab mockup/v1 uniques).

### Layout Structure
Vertical sections: Connection/Execution Bar (top), Output Display (middle), Command Input (lower-middle), Action Buttons (bottom).

| Element | Type | Description | State/Content |
|---------|------|-------------|---------------|
| BsTool Path Label | QLabel | Identifies path input | BsTool Path: |
| BsTool Path Input | QLineEdit | User-editable path | e.g., C:\Program Files\BsTool\bstool.exe |
| Env Var Label | QLabel | Identifies env var | Env Var: |
| Env Var Display | QLabel | Fixed env var | COMMUNICATION_LINE=AB01 |
| Status Indicator | QLabel | Process status | ● (running) ○ (stopped) ◔ (starting) ✖ (error) |
| Output Display | QTextEdit | Stdout/stderr from bstool.exe | Read-only, monospaced, scrollable |
| Command Input | QLineEdit | User command entry | Enter command... |
| Execute Button | QPushButton | Sends to bstool.exe | Enabled if running |
| Copy to Log Button | QPushButton | Copies output to log | Copy to Log |
| Clear Terminal Button | QPushButton | Clears output display | Clear Terminal |
| Clear Log Button | QPushButton | Clears associated log | Clear Log |

**Visual Mockup (ASCII)**:
```
+---------------------------------------------------------------------+
| BsTool Path: [ C:\Program Files\BsTool\bstool.exe ] COMMUNICATION_LINE=AB01 ● |
+---------------------------------------------------------------------+
|                                                                     |
|  BsTool Output:                                                     |
|  > Initializing bstool...                                           |
|  > BsTool ready.                                                    |
|  >                                                                  |
|  >                                                                  |
|  >                                                                  |
|  >                                                                  |
|                                                                     |
+---------------------------------------------------------------------+
| Command: [                                                ] [Execute] |
+---------------------------------------------------------------------+
| [Copy to Log] [Clear Terminal] [Clear Log]                          |
+---------------------------------------------------------------------+
```

**Rationale**: From BLUEPRINT_bstool_tab_mockup_v1.md/v1 (layout/elements/visual, repeated → table); uniques: ASCII art preserved.

## Integration & Architecture
Bundling/context menu/service (from integration v1/v2 uniques).

### Build Process
- **PyInstaller**: Add ('path/to/bstool.exe', 'bstool.exe') to datas in LOGReporter.spec; access: os.path.join(os.path.dirname(sys.executable), '_internal', 'bstool.exe').

| Component | Modification | Purpose | Access Path |
|-----------|--------------|---------|-------------|
| LOGReporter.spec | Add to datas array | Bundles bstool.exe | _internal/bstool.exe (relative) |

### Context Menu
- **Detection**: ContextMenuService detects .log file selection.
- **Action**: QAction "Run BsTool on this file"; constructs cmd (e.g., bstool -errlog AP01 from filename AP01m_*.log).
- **Trigger**: Calls presenter.process_bstool_command(log_file_path, args).

**Rationale**: From v1 (menu/integration); uniques: Cmd construction (dynamic APxx extract).

### BsToolCommandService (QObject)
Manages subprocess, output to log.

```python
import subprocess
import os
import shlex
import sys
import tempfile
import datetime
from PyQt6.QtCore import QObject, pyqtSignal
from src.commander.services.threading_service import ThreadingService

class BsToolCommandService(QObject):
    status_message_signal = pyqtSignal(str, int)
    bstool_output_signal = pyqtSignal(str, str)
    report_error = pyqtSignal(str)

    def __init__(self, log_writer, parent=None):
        super().__init__(parent)
        self.log_writer = log_writer
        self.threading_service = ThreadingService(parent=self)

    def execute_bstool(self, log_file_path: str, bstool_command_args: str = ""):
        def _run_bstool():
            try:
                bstool_path = os.path.join(os.path.dirname(sys.executable), '_internal', 'bstool.exe')
                command = [bstool_path] + shlex.split(bstool_command_args)

                env = os.environ.copy()
                env['COMMUNICATION_LINE'] = 'AB01'

                # Temp log if empty
                if not log_file_path:
                    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                    log_file_path = os.path.join(tempfile.gettempdir(), f"bstool_output_{timestamp}.log")

                process = subprocess.Popen(
                    command,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    env=env
                )

                for line in iter(process.stdout.readline, ''):
                    self.log_writer.append_to_file(log_file_path, line)
                    self.bstool_output_signal.emit(line, log_file_path)
                process.stdout.close()

                stderr_output = process.stderr.read()
                if stderr_output:
                    self.report_error.emit(f"BsTool Error: {stderr_output}")

                process.wait()
                self.status_message_signal.emit("BsTool execution complete.", 3000)

            except FileNotFoundError:
                self.report_error.emit(f"Error: bstool.exe not found at {bstool_path}. Ensure bundled.")
            except Exception as e:
                self.report_error.emit(f"Error executing BsTool: {e}")

        self.threading_service.run_in_thread(_run_bstool)

    def copy_to_log(self, content: str, log_file_path: str):
        with open(log_file_path, 'a', encoding='utf-8') as f:
            f.write(content + '\n')

    def clear_terminal(self):
        pass  # Emit to UI

    def clear_log(self, log_file_path: str):
        with open(log_file_path, 'w') as f:
            f.truncate(0)
        self.status_message_signal.emit(f"Log {log_file_path} cleared.", 3000)
```

**Signals**: status_message_signal(msg, duration); bstool_output_signal(output, path); report_error(msg).

**Rationale**: From v2 (class/structure/signals, code); uniques: Temp log fix, shlex import (from v3).

## Error Handling
Robust for subprocess (from v2 uniques).

| Condition | Response | Recovery |
|-----------|----------|----------|
| FileNotFoundError (bstool.exe) | Emit error: "not found at {path}. Ensure bundled." | Check bundling |
| Exception (general) | Emit error: "executing BsTool: {e}" | Log traceback |
| Stderr output | Emit report_error with content | User review |

**Rationale**: From v2 (try/except); inline table for density.

## Configuration
Env/path (from v1 uniques).

- **Env Var**: Fixed COMMUNICATION_LINE=AB01 (secure).
- **Path**: User-editable QLineEdit (default: C:\Program Files\BsTool\bstool.exe).
- **Args**: Dynamic from filename (e.g., -errlog AP01).

**Rationale**: From v1 (env/path); condensed.

## Testing
Strategy (from v1 uniques).

- **Unit**: BsToolCommandService (env setting, process mgmt, output capture, signals); mock subprocess/LogWriter.
- **Integration**: End-to-end right-click → exec → output to log.
- **System**: Full build with bundling; verify right-click triggers, output appended.

**Rationale**: From v1 (test strategy); preserved for completeness.

## Version History
- **v1 Baseline**: Core integration/goals (from BLUEPRINT_bstool_integration_v1.md: bundling/menu).
- **v1 Enhancements**: UI layout/mockup (from tab mockup/v1: elements/visual).
- **Merge Notes**: Absorbed clipboard (mechanism v1/v2: flow/validation → #Clipboard subsection if needed, but integrated in output); fixes (v2/v3: temp log, append fix, signals).

**Rationale**: Consolidates versions (v1/v2); lists sources/changes.

## References
- **[BsTool Service Code](src/commander/services/bstool_command_service.py)**: Exec/output.
- **[LogWriter Integration](src/commander/log_writer.py)**: Append to log.
- **[ContextMenuService](src/commander/services/context_menu_service.py)**: Right-click action.
- **[ROADMAP_bstool_integration_v1](roadmaps/ROADMAP_bstool_integration_v1.md#Phases)**: Roadmap.
- **[TECH_ui_command_core_v1 #ServiceLayer](technical/TECH_ui_command_core_v1.md#ServiceLayer)**: UI integration.
- **[Archived: BLUEPRINT_bstool_integration_v1 #Overview](archived/BLUEPRINT_bstool_integration_v1.md#Overview)**: Original goals (redirect).
- **[Archived: BLUEPRINT_bstool_tab_v1 #Overview](archived/BLUEPRINT_bstool_tab_v1.md#Overview)**: Tab details (redirect).

**Rationale**: Bidirectional #links; redirects for archives (e.g., v1/v2 as versions).
