# ROADMAP_bstool_integration_v1.md

## 🎯 BsTool Integration Roadmap
This roadmap details `bstool.exe` integration into LOGReport. It covers bundling, context menu triggering, and output redirection to log files, building on `docs/architecture/bstool_tab_blueprint.md`.

## 🚀 Phases & Milestones

### Phase 1: Core Service Development (BsToolCommandService)
**Objective:** Implement `bstool.exe` process management, fixed `COMMUNICATION_LINE=AB01` env var, and output capture.

| Milestone | Description | Deliverables |
|---|---|---|
| **M1.1** | `BsToolCommandService` class definition | `src/commander/services/bstool_command_service.py` |
| **M1.2** | Process launch & termination (`execute_bstool`) | `src/commander/services/bstool_command_service.py` |
| **M1.3** | Output capture & redirection (to `LogWriter`) | `src/commander/services/bstool_command_service.py` |
| **M1.4** | UI action implementations (`copy_to_log`, `clear_terminal`, `clear_log`) | `src/commander/services/bstool_command_service.py` |
| **M1.5** | Asynchronous execution (via `ThreadingService`) | `src/commander/services/bstool_command_service.py` |
| **M1.6** | Unit tests for `BsToolCommandService` | `tests/commander/unit/test_bstool_command_service.py` |

### Phase 2: Context Menu Integration & Build
**Objective:** Integrate `bstool.exe` into build, enable execution via right-click context menu on `.log` files.

| Milestone | Description | Deliverables |
|---|---|---|
| **M2.1** | PyInstaller spec file modification (bundle `bstool.exe`) | `LOGReporter.spec` |
| **M2.2** | `ContextMenuService` extension (add "Run BsTool" action) | `src/commander/services/context_menu_service.py` |
| **M2.3** | Presenter integration (`process_bstool_command`) | `src/commander/presenters/commander_presenter.py` |
| **M2.4** | Integration tests (end-to-end flow) | `tests/commander/integration/test_bstool_context_menu_integration.py` |

### Phase 3: Documentation & Refinement
**Objective:** Finalize documentation, refine, and prepare for deployment.

| Milestone | Description | Deliverables |
|---|---|---|
| **M3.1** | User Guide update (BsTool context menu) | `docs/user/user_guide.md` |
| **M3.2** | Technical documentation update (bundling, context menu, service) | `docs/technical/` |
| **M3.3** | System tests (full build, right-click verification) | Finalized code, updated build scripts |
| **M3.4** | Performance optimization (execution, output handling) | Finalized code, updated build scripts |

## 🔗 Dependencies
- `BsTool Integration Blueprint` (`docs/architecture/bstool_tab_blueprint.md`)
- `bstool.exe` availability
- `ThreadingService`, `LogWriter` components

## ⚠️ Risks & Mitigations
| Risk | Mitigation |
|---|---|
| `bstool.exe` bundling issues (PyInstaller) | Thorough spec file testing; PyInstaller hooks |
| `COMMUNICATION_LINE` env var propagation | Verify subprocess env setup in tests |
| `bstool.exe` compatibility (output, I/O) | Flexible output parsing; clear error messages |
| Performance degradation (frequent execution, large output) | Optimize `subprocess` calls; buffer output |
| Security vulnerabilities (external commands) | Trust `bstool.exe`; restrict to internal paths |

## ✨ Future Enhancements
- Configurable `COMMUNICATION_LINE` (secure settings)
- Progress indication for long-running `bstool.exe`
- Advanced output parsing/syntax highlighting in log file