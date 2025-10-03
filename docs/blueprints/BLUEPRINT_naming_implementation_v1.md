# BLUEPRINT_naming_implementation_v1.md

## Overview
**Objective:** Implement Phases 5-6 for 15 core + 233 archived .md docs: Rename to standards (e.g., ARCH_[system]_[v].md), move to /docs/[category]/ (architecture, blueprints, roadmaps, technical, user, archived). Enforce /templates/document_standards.md patterns. Preserve content/links; fix 52 core violations (40% naming inconsistent, 25% wrong placement), 3 archived. Target: 100% compliance, 0 misplacements. Solves: Fragmented naming/placement hindering discoverability.

**Scope:** /docs/ only (248 files post-Phases3-4). Categories: architecture (ARCH_* in /docs/architecture/), blueprints (BLUEPRINT_* in /docs/blueprints/), roadmaps (ROADMAP_* in /docs/roadmaps/), technical (TECH_* in /docs/technical/), user (GUIDE_* in /docs/user/), archived (prefixed in /docs/archived/). Non-goals: Content changes.

**Rationale:** Scans show architecture/ polluted with 25 non-ARCH (e.g., logging.md → TECH_logging_v1.md to technical/); technical/ 20 without TECH_; blueprints/ 5 non-BLUEPRINT; user/ 2 without GUIDE; archived/ 3 without prefix. Evidence: list_files + codebase_search (60% violations). Hypotheses: H1 90% detection → 100% fixes; H2 bulk rename/move → 100% compliance; H3 category mapping → 0 misplacements.

**Risks/Mitigation:** Link breaks (search_and_replace old names); Conflicts (append _v2); Loss (read_file full content before write). Backup: Archive originals with YAML reason.

## Phases & Milestones
| Phase | Actions | Tools | Inputs | Outputs | Timeline |
|-------|---------|-------|--------|---------|----------|
| **Prep** | Validate standards; backup /docs/. | read_file (standards.md); execute_command 'cp -r docs docs_backup'. | templates/document_standards.md; /docs/. | Backup dir; Confirmed patterns (ARCH_[a-z_]+_v\d+\.md etc.). | 2min |
| **Core Renames/Moves (52 files)** | Batch 1-5 (10/file): Read old, write new path with content, delete old. Update links in all docs. | read_file (old); write_to_file (new_path, full content); execute_command 'rm old_path'; search_and_replace (old names → new across /docs/*.md). | Violation list (e.g., docs/architecture/logging.md → docs/technical/TECH_logging_v1.md). | 52 fixed files; Updated links. | 10min |
| **Archived Fixes (3 files)** | Prefix/move non-compliant (e.g., nodes_not_appearing_issue.md → TECH_nodes_not_appearing_issue_v1.md in archived/). | read_file; write_to_file (archived/prefixed.md, content + YAML: reason: 'non-compliant naming fixed'). | Archived list. | 3 prefixed files. | 1min |
| **Validation** | Scan post: 0 violations, 100% match. Metrics: Pre 55 violations → post 0. | search_files (non-pattern regex); list_files (/docs/[category]/). | Fixed files. | Report: 100% naming/placement; O1 pass (100% match), O2 pass (0 misplace), O3 pass (55 fixed). | 3min |
| **Report** | Generate /logs/documents_analysis_5-6_2025-10-03_093000.md: Violations fixed, metrics. | write_to_file (log path, template: violations list, fixes table, metrics). | Validation results. | Phase report. | 2min |

## Violation Mappings (Core: 52; Archived: 3)
**Architecture/ Non-ARCH (25):**
- logging.md → /docs/technical/TECH_logging_v1.md (missing prefix, wrong dir)
- logging_configuration.md → /docs/technical/TECH_logging_configuration_v1.md
- memory_first_workflow.md → /docs/technical/TECH_memory_first_workflow_v1.md
- memory_implementation_phases_5-8_v1.md → /docs/technical/TECH_memory_implementation_phases_5-8_v1.md (add TECH_)
- memory_implementation_summary.md → /docs/technical/TECH_memory_implementation_summary_v1.md
- memory_management.md → /docs/architecture/ARCH_memory_management_v1.md (add ARCH_)
- ... (18 more similar: codebase_implementation_plan_v1.md → /docs/blueprints/BLUEPRINT_codebase_implementation_v1.md; design_document_hierarchical_commands.md → /docs/architecture/ARCH_hierarchical_commands_v1.md; etc.)

**Technical/ Non-TECH (20):**
- bstools_append_output_fix.md → /docs/technical/TECH_bstool_append_output_fix_v1.md (add TECH_)
- changelog_management.md → /docs/technical/TECH_changelog_management_v1.md
- clear_all_subgroup_files_command.md → /docs/technical/TECH_clear_subgroup_files_v1.md
- commander_window.md → /docs/technical/TECH_commander_window_v1.md
- hybrid_token_resolution.md → /docs/technical/TECH_hybrid_token_resolution_v1.md
- implementation_summary.md → /docs/technical/TECH_implementation_summary_v1.md
- log_writer_testing.md → /docs/technical/TECH_log_writer_testing_v1.md
- ... (13 more: memory_optimization_tests.md → TECH_memory_optimization_tests_v1.md; node_color_update.md → TECH_node_color_update_v1.md; etc.)

**Blueprints/ Non-BLUEPRINT (5):**
- memory_template_implementation.md → /docs/blueprints/BLUEPRINT_memory_template_implementation_v1.md (add BLUEPRINT_)
- session_recording_blueprint.md → /docs/blueprints/BLUEPRINT_session_recording_v1.md
- vnc_tab_blueprint.md → /docs/blueprints/BLUEPRINT_vnc_tab_v1.md
- ... (2 more)

**User/ Non-GUIDE (2):**
- telnet_guide.md → /docs/user/GUIDE_telnet_v1.md (add GUIDE_)
- troubleshooting_guide.md → /docs/user/GUIDE_troubleshooting_v1.md

**Archived/ Non-Prefixed (3):**
- nodes_not_appearing_issue.md → /docs/archived/TECH_nodes_not_appearing_issue_v1.md (add TECH_)
- vnc_tab_blueprint.md → /docs/archived/BLUEPRINT_vnc_tab_v1.md (already listed, but if duplicate)
- vnc_tab_mockup.md → /docs/archived/BLUEPRINT_vnc_tab_mockup_v1.md

**Conflicts Handling:** If target exists (e.g., TECH_logging_v1.md), rename to TECH_logging_v2.md; update all refs.

## Link Updates
- Global search_and_replace: Old names → new (e.g., [logging.md] → [TECH_logging_v1.md]); Internal #links unchanged unless path changes.
- Validate: search_files for old names post-implementation = 0.

## Metrics & Oracles
| Metric | Pre | Target Post | Validation |
|--------|-----|-------------|------------|
| Naming Compliance | 60% | 100% | regex ^(ARCH|BLUEPRINT|...)_[a-z_]+_v\d+\.md$ on all .md |
| Placement | 75% | 100% | list_files /docs/[category]/ only compliant files |
| Violations Fixed | 0/55 | 55/55 | Pre/post counts |
| O1: Naming | N/A | Pass: 100% match | Evidence: search_files results |
| O2: Placement | N/A | Pass: 0 misplace | Evidence: dir listings |
| O3: Fixed | N/A | Pass: 55 actions | Evidence: log of renames/moves |

**Success:** All docs compliant; report in /logs/documents_analysis_5-6_2025-10-03_093000.md. Next: Phases 7-8 handoff.