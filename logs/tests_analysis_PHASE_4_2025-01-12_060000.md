# PHASE 4: Code-Test Alignment Analysis Report
================================================================================

## Summary Statistics

**Source Modules**: 71
**Test Files**: 88
**Aligned Mappings**: 13
**Integration Tests**: 45
**Orphaned Tests**: 30
**Untested Modules**: 57

**Alignment Ratio**: 18.3% (13/71)

---

## Detailed Test-to-Code Mappings

### ✅ ALIGNED TESTS (13 files)

| Source Module | Test File | Status |
|---------------|-----------|--------|
| `commander.log_writer` | `commander/test_log_writer.py` | ✅ ALIGNED |
| `commander.presenters.node_tree_presenter` | `unit/node_management/test_node_tree_presenter.py` | ✅ ALIGNED |
| `commander.services.bstool_command_service` | `commander/test_bstool_command_service.py` | ✅ ALIGNED |
| `commander.services.clipboard_monitor` | `commander/test_clipboard_monitor.py` | ✅ ALIGNED |
| `commander.services.session_player` | `commander/test_session_player.py` | ✅ ALIGNED |
| `commander.services.session_recorder` | `commander/test_session_recorder.py` | ✅ ALIGNED |
| `commander.ui.commander_window` | `commander/test_commander_window.py` | ✅ ALIGNED |
| `commander.utils.log_filename_parser` | `commander/test_log_filename_parser.py` | ✅ ALIGNED |
| `commander.utils.token_utils` | `unit/token_detection/test_token_utils.py` | ✅ ALIGNED |
| `generator` | `unit/test_generator.py` | ✅ ALIGNED |
| `log_creator` | `unit/test_log_creator.py` | ✅ ALIGNED |
| `node_config_parser` | `integration/node_management/test_node_config_parser.py` | ✅ ALIGNED |
| `sys_file_loader` | `unit/sys_file/test_sys_file_loader.py` | ✅ ALIGNED |

### 🔗 INTEGRATION TESTS (45 files)

*These tests cover multiple modules or end-to-end workflows*

- `commander/integration/test_bstool_context_menu_integration.py`
- `commander/system/test_bstool_path_persistence_e2e.py`
- `commander/system/test_bstool_system_integration.py`
- `commander/system/test_bstool_ui_output_e2e.py`
- `commander/test_bstool_copy_to_log_integration.py`
- `commander/test_token_detection_end_to_end.py`
- `integration/bstool/test_bstool_append.py`
- `integration/bstool/test_bstool_bundling.py`
- `integration/bstool/test_bstool_color_updates.py`
- `integration/command_queue/test_command_execution.py`
- `integration/command_queue/test_command_queue_sequential.py`
- `integration/command_queue/test_hierarchical_command_execution.py`
- `integration/command_queue/test_hierarchical_manual.py`
- `integration/command_queue/test_sequential_integration.py`
- `integration/node_management/test_node_click_telnet_command_input.py`
- `integration/node_management/test_node_color_logic.py`
- `integration/node_management/test_node_color_update_integration.py`
- `integration/node_management/test_node_config_integration.py`
- `integration/node_management/test_node_config_sys_file_ui.py`
- `integration/node_management/test_node_config_transformation.py`
- `integration/node_management/test_node_config_validation.py`
- `integration/node_management/test_node_hierarchical_commands.py`
- `integration/node_management/test_node_print_commands.py`
- `integration/node_management/test_node_tree_presenter_signals.py`
- `integration/telnet/test_telnet_command_output.py`
- `integration/telnet/test_telnet_connect.py`
- `integration/telnet/test_telnet_connect_integration.py`
- `integration/telnet/test_telnet_connection.py`
- `integration/telnet/test_telnet_copy_to_log_integration.py`
- `integration/test_multi_file_report_generation.py`
- `integration/test_processor_integration.py`
- `integration/token_detection/test_context_menu_tokens.py`
- `integration/token_detection/test_fbc_token_detection.py`
- `integration/token_detection/test_token_detection_end_to_end.py`
- `integration/ui_behavior/test_auto_connect_initialization.py`
- `integration/ui_behavior/test_debugger_connection_management.py`
- `integration/ui_behavior/test_pause_resume_cancel.py`
- `integration/ui_behavior/test_pause_resume_cancel_buttons.py`
- `integration/ui_behavior/test_print_all_nodes_auto_connect.py`
- `integration/ui_behavior/test_qt_append_behavior.py`
- `integration/ui_behavior/test_qt_behavior.py`
- `integration/ui_behavior/test_smart_tab_switching.py`
- `integration/ui_behavior/test_startup_color_logic.py`
- `integration/ui_behavior/test_tree_expansion.py`
- `memory_optimization/test_memory_workflow.py`

### ⚠️ ORPHANED TESTS (30 files)

*Tests with no clear corresponding source module*

- `commander/system/test_bstool_ui_output.py`
- `commander/test_bstool_import.py`
- `commander/test_bstool_tab_ui.py`
- `commander/test_button_actions.py`
- `commander/test_button_styling.py`
- `commander/test_clear_log.py`
- `commander/test_clear_subgroup_log_files.py`
- `commander/test_clear_subgroup_log_files_v2.py`
- `commander/test_copy_to_log_functionality.py`
- `commander/test_fbc_subsection_context_menu.py`
- `commander/test_log_write_notification_display.py`
- `commander/test_log_writer_additional.py`
- `commander/test_print_all_nodes_button.py`
- `commander/test_rpc_command_generation.py`
- `commander/test_rpc_log_path.py`
- `commander/test_rpc_token_detection.py`
- `regression/bstool_issues/test_bstool_context_menu_fix.py`
- `regression/ui_issues/test_auto_expansion_fix.py`
- `system/command_queue/test_sequential_output_display.py`
- `system/sys_file/test_sys_file_parsing.py`
- `system/sys_file/test_sys_file_parsing_v2.py`
- `system/telnet/test_telnet_connection_management.py`
- `unit/node_management/test_node_manager_simple.py`
- `unit/node_management/test_node_suffix_stripping.py`
- `unit/rpc_commands/test_rpc_normalization.py`
- `unit/sys_file/test_sys_file_parser.py`
- `unit/token_detection/test_multiple_tokens.py`
- `unit/token_detection/test_token_detection.py`
- `unit/token_detection/test_token_detection_simple.py`
- `unit/token_detection/test_token_detection_standalone.py`

---

## ❌ UNTESTED MODULES (57 modules)

*Source modules with no corresponding test files*

### Commander (51 modules)

- `commander` (19 lines)
- `commander.command_queue` (420 lines)
- `commander.commands.telnet_commands` (114 lines)
- `commander.constants` (43 lines)
- `commander.contracts` (161 lines)
- `commander.icons` (109 lines)
- `commander.main_window` (86 lines)
- `commander.models` (44 lines)
- `commander.node_manager` (789 lines)
- `commander.observable_model` (8 lines)
- `commander.presenters` (6 lines)
- `commander.presenters.commander_presenter` (193 lines)
- `commander.presenters.commander_presenter_utils` (174 lines)
- `commander.presenters.node_tree_presenter_logic` (62 lines)
- `commander.presenters.session_presenter` (115 lines)
- `commander.qt_init` (36 lines)
- `commander.services` (11 lines)
- `commander.services.bstool_worker` (203 lines)
- `commander.services.commander_service` (120 lines)
- `commander.services.context_menu_filter` (211 lines)
- `commander.services.context_menu_service` (439 lines)
- `commander.services.error_handler` (168 lines)
- `commander.services.error_reporter` (84 lines)
- `commander.services.error_reporting` (3 lines)
- `commander.services.error_reporting.interface` (47 lines)
- `commander.services.error_reporting.reporter` (77 lines)
- `commander.services.fbc_command_service` (101 lines)
- `commander.services.hierarchical_command_service` (352 lines)
- `commander.services.log_command_service` (25 lines)
- `commander.services.logging_service` (163 lines)
- `commander.services.queue_management_service` (36 lines)
- `commander.services.rpc_command_service` (113 lines)
- `commander.services.sequential_command_processor` (956 lines)
- `commander.services.status_service` (63 lines)
- `commander.services.telnet_service` (417 lines)
- `commander.services.threading_service` (63 lines)
- `commander.session_manager` (508 lines)
- `commander.telnet_client` (201 lines)
- `commander.ui.bstool_tab` (196 lines)
- `commander.ui.commander_ui_factory` (85 lines)
- `commander.ui.node_tree_view` (255 lines)
- `commander.ui.session_view` (54 lines)
- `commander.ui.telnet_tab` (186 lines)
- `commander.ui.theme` (159 lines)
- `commander.utils` (1 lines)
- `commander.utils.circuit_breaker` (115 lines)
- `commander.utils.constants` (27 lines)
- `commander.utils.error_detection` (82 lines)
- `commander.utils.retry_utils` (132 lines)
- `commander.utils.telnet_filters` (46 lines)
- `commander.widgets` (80 lines)

### Core (5 modules)

- `gui` (381 lines)
- `gui_workers` (20 lines)
- `main` (42 lines)
- `node_config_dialog` (778 lines)
- `processor` (105 lines)

### Utils (1 modules)

- `utils.file_utils` (248 lines)

---

## Recommendations

⚠️ **LOW ALIGNMENT**: Less than 70% of modules have corresponding tests.

1. **Review 30 orphaned tests**:
   - Verify if they test deprecated code (consider deletion)
   - Check if they're integration tests (reclassify)
   - Update naming to match source modules

2. **Create tests for 57 untested modules**:
   - Prioritize high-complexity or critical modules
   - Focus on commander services (business logic)
   - Cover error handling and edge cases

3. **Validate imports**:
   - Run `pytest --collect-only` to check test discovery
   - Verify no broken imports after Phase 3 reorganization
