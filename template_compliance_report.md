# Template Compliance Report: Naming and Placement

## Overview
This report details the findings of the template compliance analysis for project documentation, focusing on naming conventions and file placement as defined in `templates/document_standards.md`. The analysis reveals significant non-compliance across the `docs/` directory.

## Document Naming Standards (Pattern: `[DocumentType]_[Subject]_[Version].md`)
### Standard Types and Locations:
| Type | Pattern | Location |
|------|---------|----------|
| **ARCH** | `ARCH_[system]_[v].md` | `/docs/architecture/` |
| **BLUEPRINT** | `BLUEPRINT_[plan]_[v].md` | `/docs/blueprints/` |
| **ROADMAP** | `ROADMAP_[scope]_[v].md` | `/docs/roadmaps/` |
| **TECH** | `TECH_[component]_[v].md` | `/docs/technical/` |
| **GUIDE** | `GUIDE_[feature]_[v].md` | `/docs/user/` |

## Non-Compliant Documents: Naming and Placement

The following documents do not adhere to the specified naming conventions or are located in incorrect directories:

### Naming Convention Violations (Missing `[DocumentType]_` prefix and `_v` suffix)
*   `docs/ARCHITECTURAL/consolidation_blueprint.md` (Expected: `BLUEPRINT_consolidation_v1.md`)
*   `docs/ARCHITECTURAL/roadmaps/documentation_consolidation_roadmap.md` (Expected: `ROADMAP_documentation_consolidation_v1.md`)
*   `docs/architecture/architectural_design_proposal.md` (Expected: `ARCH_telnet_command_population_v1.md`)
*   `docs/architecture/architecture_overview.md` (Expected: `ARCH_logreport_overview_v1.md`)
*   `docs/architecture/batch_operations.md` (Expected: `ARCH_batch_operations_v1.md`)
*   `docs/architecture/bstool_tab_blueprint.md` (Expected: `BLUEPRINT_bstool_tab_v1.md`)
*   `docs/architecture/bstool_tab_mockup.md` (Expected: `BLUEPRINT_bstool_tab_mockup_v1.md`)
*   `docs/architecture/bstool_test_strategy.md` (Expected: `TECH_bstool_test_strategy_v1.md`)
*   `docs/architecture/command_processing_architecture.md` (Expected: `ARCH_command_processing_v1.md`)
*   `docs/architecture/command_queue.md` (Expected: `ARCH_command_queue_v1.md`)
*   `docs/architecture/condensation_analysis_summary.md` (Expected: `ARCH_condensation_analysis_v1.md`)
*   `docs/architecture/log_format_specification.md` (Expected: `TECH_log_format_v1.md`)
*   `docs/architecture/log_writer_architecture.md` (Expected: `ARCH_log_writer_v1.md`)
*   `docs/architecture/log_writer_configuration.md` (Expected: `TECH_log_writer_config_v1.md`)
*   `docs/architecture/logging_configuration.md` (Expected: `TECH_logging_config_v1.md`)
*   `docs/architecture/logging.md` (Expected: `ARCH_logging_v1.md`)
*   `docs/architecture/memory_first_workflow.md` (Expected: `ARCH_mcp_session_process_v1.md`)
*   `docs/architecture/memory_management.md` (Expected: `ARCH_memory_management_v1.md`)
*   `docs/architecture/memory_optimization_report.md` (Expected: `ARCH_memory_optimization_v1.md`)
*   `docs/architecture/memory.md` (Expected: `ARCH_memory_architecture_v1.md`)
*   `docs/architecture/mvp_implementation.md` (Expected: `ARCH_mvp_implementation_v1.md`)
*   `docs/architecture/mvp_pattern_adoption.md` (Expected: `ARCH_mvp_pattern_adoption_v1.md`)
*   `docs/architecture/node_color_determination_logic.md` (Expected: `ARCH_node_color_logic_v1.md`)
*   `docs/architecture/node_manager_architecture.md` (Expected: `ARCH_node_manager_v1.md`)
*   `docs/architecture/node_resolution.md` (Expected: `ARCH_node_resolution_v1.md`)
*   `docs/architecture/optimal_knowledge_organization.md` (Expected: `ARCH_knowledge_organization_v1.md`)
*   `docs/architecture/orchestrator_simulation.md` (Expected: `ARCH_orchestrator_simulation_v1.md`)
*   `docs/architecture/pattern_abstraction_map.md` (Expected: `ARCH_pattern_abstraction_v1.md`)
*   `docs/architecture/refactoring_report.md` (Expected: `TECH_refactoring_report_v1.md`)
*   `docs/architecture/roadmaps/bstool_implementation_roadmap.md` (Expected: `ROADMAP_bstool_implementation_v1.md`)
*   `docs/architecture/service_layer/command_services.md` (Expected: `TECH_command_services_v1.md`)
*   `docs/architecture/service_layer/sequential_command_processor.md` (Expected: `TECH_sequential_command_processor_v1.md`)
*   `docs/architecture/service_layer/service_layer_pattern.md` (Expected: `ARCH_service_layer_pattern_v1.md`)
*   `docs/architecture/token_management/hybrid_token_resolution.md` (Expected: `ARCH_hybrid_token_resolution_v1.md`)
*   `docs/architecture/token_management/token_management_guide.md` (Expected: `GUIDE_token_management_v1.md`)
*   `docs/architecture/token_management/token_processing.md` (Expected: `TECH_token_processing_v1.md`)
*   `docs/blueprints/clipboard_mechanism.md` (Expected: `BLUEPRINT_clipboard_mechanism_v1.md`)
*   `docs/blueprints/context_menu_filtering.md` (Expected: `BLUEPRINT_context_menu_filtering_v1.md`)
*   `docs/blueprints/documentation_review_process.md` (Expected: `BLUEPRINT_documentation_review_v1.md`)
*   `docs/blueprints/integration_points.md` (Expected: `BLUEPRINT_integration_points_v1.md`)
*   `docs/blueprints/memory_consolidation.md` (Expected: `BLUEPRINT_memory_consolidation_v1.md`)
*   `docs/blueprints/memory_template_implementation.md` (Expected: `BLUEPRINT_memory_template_implementation_v1.md`)
*   `docs/blueprints/session_recording_blueprint.md` (Expected: `BLUEPRINT_session_recording_v1.md`)
*   `docs/blueprints/vnc_tab_blueprint.md` (Expected: `BLUEPRINT_vnc_tab_v1.md`)
*   `docs/blueprints/vnc_tab_mockup.md` (Expected: `BLUEPRINT_vnc_tab_mockup_v1.md`)
*   `docs/blueprints/context_menu/context_menu_architecture.md` (Expected: `ARCH_context_menu_v1.md`)
*   `docs/blueprints/context_menu/context_menu_filtering.md` (Expected: `BLUEPRINT_context_menu_filtering_v1.md`)
*   `docs/roadmaps/ROADMAP.md` (Expected: `ROADMAP_commander_module_v1.md`)
*   `docs/roadmaps/task_management.md` (Expected: `ROADMAP_task_management_v1.md`)
*   `docs/roadmaps/vnc_implementation_roadmap.md` (Expected: `ROADMAP_vnc_implementation_v1.md`)
*   `docs/technical/api_token_utilities.md` (Expected: `TECH_api_token_utilities_v1.md`)
*   `docs/technical/bstool_append_output_fix.md` (Expected: `TECH_bstool_append_output_fix_v1.md`)
*   `docs/technical/bstool_command_execution_fixes.md` (Expected: `TECH_bstool_command_execution_fixes_v1.md`)
*   `docs/technical/bstool_fixes_summary.md` (Expected: `TECH_bstool_fixes_summary_v1.md`)
*   `docs/technical/BUILD-INSTRUCTIONS.md` (Expected: `TECH_build_instructions_v1.md`)
*   `docs/technical/CHANGELOG_deduplicated.md` (Expected: `TECH_changelog_deduplicated_v1.md`)
*   `docs/technical/changelog_management.md` (Expected: `TECH_changelog_management_v1.md`)
*   `docs/technical/clear_all_subgroup_files_command.md` (Expected: `TECH_clear_all_subgroup_files_command_v1.md`)
*   `docs/technical/commander_window.md` (Expected: `TECH_commander_window_v1.md`)
*   `docs/technical/implementation_summary.md` (Expected: `TECH_implementation_summary_v1.md`)
*   `docs/technical/log_writer_testing.md` (Expected: `TECH_log_writer_testing_v1.md`)
*   `docs/technical/memory_optimization_tests.md` (Expected: `TECH_memory_optimization_tests_v1.md`)
*   `docs/technical/node_color_update.md` (Expected: `TECH_node_color_update_v1.md`)
*   `docs/technical/node_manager_configuration.md` (Expected: `TECH_node_manager_configuration_v1.md`)
*   `docs/technical/nodes_not_appearing_issue.md` (Expected: `TECH_nodes_not_appearing_issue_v1.md`)
*   `docs/technical/refactor.md` (Expected: `TECH_refactor_v1.md`)
*   `docs/technical/TASKS.md` (Expected: `TECH_tasks_v1.md`)
*   `docs/user/telnet_guide.md` (Expected: `GUIDE_telnet_v1.md`)
*   `docs/user/user_guide.md` (Expected: `GUIDE_user_v1.md`)
*   `docs/user/troubleshooting/troubleshooting_guide.md` (Expected: `GUIDE_troubleshooting_v1.md`)

### Incorrect Placement
*   `docs/ARCHITECTURAL/consolidation_blueprint.md` (Should be in `/docs/blueprints/`)
*   `docs/ARCHITECTURAL/roadmaps/documentation_consolidation_roadmap.md` (Should be in `/docs/roadmaps/`)
*   `docs/architecture/bstool_tab_blueprint.md` (Should be in `/docs/blueprints/`)
*   `docs/architecture/bstool_tab_mockup.md` (Should be in `/docs/blueprints/`)
*   `docs/architecture/bstool_test_strategy.md` (Should be in `/docs/technical/`)
*   `docs/architecture/token_management/token_management_guide.md` (Should be in `/docs/user/`)
*   `docs/blueprints/context_menu/context_menu_architecture.md` (Should be in `/docs/architecture/`)
*   `docs/blueprints/context_menu/context_menu_filtering.md` (Should be in `/docs/blueprints/` or `/docs/architecture/`)

## Summary of Non-Compliance
The majority of the existing documentation files do not adhere to the `[DocumentType]_[Subject]_[Version].md` naming pattern. Many files are also located in incorrect subdirectories, leading to a disorganized and inconsistent documentation structure.

## Recommendations
1.  **Rename all non-compliant files** to follow the `[DocumentType]_[Subject]_[Version].md` pattern.
2.  **Relocate misplaced files** to their correct `docs/` subdirectories based on their document type.
3.  **Implement a versioning strategy** for all documents, starting with `v1` for initial compliance.