# 🏗️ Architectural Design Proposal: Telnet Command Population

## Overview
Objective: Evaluate design for Telnet command population, fix signal discrepancy in NodeTreePresenter.on_node_selected. Chosen: H2 - Decouple from NodeTreePresenter, use log_file_selected_signal via intermediary (CommanderPresenter/service).

## Architectural Decision
| Aspect | Rationale | Benefits |
|--------|-----------|----------|
| Separation of Concerns (MVP) | NodeTreePresenter manages UI only; business logic in service | Clean architecture, easier maintenance |
| Flexibility (Service Layer) | Centralize in CommanderPresenter | Reusable rules, easy integration |
| Maintainability | Isolate changes | Reduced impact on UI |
| Consistency | Aligns with existing mediation | Standardized updates |

## Design Blueprint

### Phase 1: Signal Rerouting
| Step | Action | Details |
|------|--------|---------|
| 1. Modify CommanderWindow._connect_signals | Disconnect old, connect to commander_presenter.on_log_file_selected | Use self.node_tree_presenter.log_file_selected_signal |
| 2. Update NodeTreePresenter.on_node_selected | Emit item_data dict (log_path, token, type, node, ip) | Richer context |
| 3. Implement CommanderPresenter.on_log_file_selected | Extract token/type/node; use service to generate cmd; emit set_cmd_input_text_signal | Optional: switch tab, focus input |

### Phase 2: Refinement
| Update | Details |
|--------|---------|
| CommanderPresenter __init__ | Add fbc/rpc services | Already present |
| Review Services | Add generate_cmd(token_id, node_name) methods | Encapsulate logic |
| Tests | Unit: on_log_file_selected; Integration: end-to-end flow; Regression: existing signals | Update test_node_click_telnet_command_input.py |

## Roadmap
| Phase | Focus | Timeline |
|-------|--------|----------|
| 1 Immediate | Core flow | Now |
| 2 Short-term | Refine logic, tests | Next sprint |
| 3 Future | Dedicated service if complex | Later |

## Technology Strategy
| Tech | Usage |
|------|--------|
| PyQt6 Signals | Inter-component comm | Established |
| Type Hinting | Clarity, analysis | Enhance |
| Logging | Debug, insights | Full use |

## Test Strategy
| Type | Focus |
|------|--------|
| Unit | Isolated methods | on_log_file_selected, services |
| Integration | End-to-end | Node select to input |
| Regression | Existing funcs | Log file handling |