# ROADMAP_vnc_integration_v1.md

## 🎯 VNC Integration Roadmap
This roadmap details VNC viewer integration, covering dynamic IP management, clipboard integration, session recording/replay, and cohesive UI.

## 🚀 Implementation Phases

### Phase 1: UI Foundation (Week 1)
**Objective**: Establish core UI structure & integration points.

| Milestone | Description |
|---|---|
| **M1.1** | `VNCTab` class created (layout hierarchy) |
| **M1.2** | Integration with Commander window theming |
| **M1.3** | Responsive behavior validated (1024x768) |

**Key Tasks**: Create `VNCTab` (QVBoxLayout root); implement top (IP input, log filename), middle (VNC viewer, status), bottom (controls, buttons) sections; integrate CommanderWindow theme; validate responsive behavior.

**Dependencies**: None | **Risks**: Layout inconsistencies | **Mitigation**: Regular UI design reviews.

### Phase 2: Connection Management (Week 2)
**Objective**: Implement reliable VNC connection with dynamic IP handling.

| Milestone | Description |
|---|---|
| **M2.1** | IP extraction from log filenames functional |
| **M2.2** | Connection workflow with error handling |
| **M2.3** | Status indicators synchronized |

**Key Tasks**: Implement log filename parsing (IP); real-time IP validation; connect `SessionManager.ip_changed` signal; develop connection state machine; implement error handling (detailed logs); add auto reconnection (max 3).

**Dependencies**: Phase 1 | **Risks**: IP extraction edge cases | **Mitigation**: Comprehensive filename parser tests.

### Phase 3: Clipboard Integration (Week 3)
**Objective**: Implement automatic & manual clipboard-to-log functionality.

| Milestone | Description |
|---|---|
| **M3.1** | Automatic clipboard monitoring operational |
| **M3.2** | Manual copy button with validation |
| **M3.3** | Ctrl+C implementation with notification |

**Key Tasks**: Implement `ClipboardMonitor`; add auto clipboard-to-logfile (active log file changes); develop manual 'Copy to Log' button; implement Ctrl+C (text selection, `StatusService.show_message`); add format validation (FBC/LIS/LOG/RPC); implement rate limiting (5 ops/min).

**Dependencies**: Phase 2 | **Risks**: Clipboard content sanitization | **Mitigation**: Validation via `TokenUtils`.

### Phase 4: Session Recording (Weeks 4-5)
**Objective**: Deliver complete session recording & replay.

| Milestone | Description |
|---|---|
| **M4.1** | Event capture system operational |
| **M4.2** | `.vncr` storage format implemented |
| **M4.3** | Replay functionality (timeline controls) |

**Key Tasks**: Implement event capture (mouse/keyboard); develop `.vncr` storage (delta encoding); create `SessionRecorder` & `SessionPlayer`; add recording controls to VNC tab toolbar; implement security (redaction, encryption); validate performance (<15% CPU overhead).

**Dependencies**: Phase 3 | **Risks**: Large file size | **Mitigation**: Auto rotation (500MB).

### Phase 5: Validation & Documentation (Week 6)
**Objective**: Ensure quality & provide implementation documentation.

| Milestone | Description |
|---|---|
| **M5.1** | All validation criteria met |
| **M5.2** | User documentation completed |
| **M5.3** | Technical handoff package prepared |

**Key Tasks**: Execute validation checklist (blueprints); create user guide (VNC features); update API documentation; prepare handoff package; conduct architecture review.

## 🗓️ Timeline Overview
| Phase | Duration | Start | End | Deliverables |
|---|---|---|---|---|
| UI Foundation | 1 week | 2025-09-08 | 2025-09-14 | VNCTab UI structure |
| Connection Mgmt | 1 week | 2025-09-15 | 2025-09-21 | IP extraction, connection workflow |
| Clipboard Integration | 1 week | 2025-09-22 | 2025-09-28 | Clipboard monitoring, validation |
| Session Recording | 2 weeks | 2025-09-29 | 2025-10-12 | Event capture, .vncr format, replay |
| Validation & Docs | 1 week | 2025-10-13 | 2025-10-19 | Test reports, user documentation |

## ✅ Validation Criteria
- All integration points documented (`integration_points.md`).
- UI layout matches `vnc_tab_mockup.md` specs.
- Clipboard functionality aligns with `clipboard_mechanism.md`.
- Session recording meets `session_recording_blueprint.md` requirements.
- Implementation follows `structure.md` rules.

## ⚠️ Risk Assessment
| Risk | Probability | Impact | Mitigation |
|---|---|---|---|
| IP parsing edge cases | Medium | High | Comprehensive test coverage |
| Clipboard content sanitization | Low | Critical | Validation via `TokenUtils` |
| Session recording performance | Medium | Medium | Automatic file rotation |
| UI consistency issues | High | Medium | Regular design reviews |

## 🔗 Dependencies Verification
- `src/commander/node_manager.py` (Node context)
- `src/commander/session_manager.py` (VNC session)
- `src/commander/services/log_writer.py` (Log file ops)
- `src/commander/services/clipboard_service.py` (Clipboard access)
- `src/commander/services/status_service.py` (UI feedback)
- `src/commander/utils/token_utils.py` (Format validation)

## 📦 Deliverable Verification
- Roadmap file created (`docs/roadmaps/vnc_implementation_roadmap.md`).
- Blueprint references accurate/up-to-date.
- Timeline aligns with resource availability.
- Risk assessment covers critical path.
- Validation criteria measurable/testable.