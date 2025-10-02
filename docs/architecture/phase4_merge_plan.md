# Phase 4 Merge Plan: Content Optimization

## Overview
- **Before Count**: 97 docs (from Phase 3).
- **Target After**: ~70 docs (28% reduction via 25 merges/consolidations + 10 archives).
- **Principles**: No info loss (combine unique content, preserve refs/metadata); prioritize latest version; validate post-merge sim<80%.
- **Batches**: Max 10 files per operation; sequential (duplicates first, then redundants, archives last).
- **Tools**: read_file (sources), write_to_file (new/merged), apply_diff (updates), move_file (archives with YAML reason).

## 1. Duplicates Merges (12 pairs/clusters, >80% sim)
Merge into single target (latest version), append unique sections (e.g., tables/methods), remove duplicates.

- **Bstool Tabs (3 pairs → 1 doc)**:
  - Sources: blueprints/BLUEPRINT_bstool_tab_v1.md, blueprints/BLUEPRINT_bstool_integration_v1.md, blueprints/BLUEPRINT_BsTool_Integration_v2.md (sim 82%).
  - Target: blueprints/BLUEPRINT_bstool_tab_v1.md (append unique UI/code refs from v2/integration).
  - Action: read_file all, write_to_file target with combined YAML + unique content.

- **Logging Blueprints (5 pairs → 1 doc)**:
  - Sources: architecture/ARCH_log_writer_v1.md, architecture/ARCH_log_writer_impl_v1.md, architecture/ARCH_log_writer_config_v1.md, architecture/ARCH_log_format_v1.md, architecture/logging_configuration.md (sim 85%).
  - Target: architecture/ARCH_logging_system_v1.md (merge methods/tables, retain config/format uniques).
  - Action: Batch read_file (5 files), write_to_file target.

- **Queue Variants (4 pairs → 1 doc)**:
  - Sources: architecture/ARCH_cmd_queue_impl_v1.md, architecture/ARCH_command_queue_v1.md, architecture/ARCH_command_processing_v1.md, architecture/ARCH_command_system_v1.md (sim 81%).
  - Target: architecture/ARCH_command_queue_v1.md (consolidate FIFO/threading logic).
  - Action: read_file all, apply_diff to target for overlaps + insert_content uniques.

## 2. Redundancy Consolidations (18 docs, >50% overlap)
Consolidate clusters, integrate overlaps via apply_diff, create variants if needed.

- **High: Logging Variants (12 docs → 3 main + 2 variants)**:
  - Cluster: architecture/logging.md, technical/TECH_logging_v1.md, technical/TECH_logging_configuration_v1.md, +9 others (e.g., ARCH_session_config_v1.md overlaps; 65% shared components/resolution).
  - Targets: 
    - Main1: architecture/ARCH_logging_system_v1.md (overview + core).
    - Main2: technical/TECH_logging_configuration_v1.md (config).
    - Main3: technical/TECH_logging_v1.md (impl).
    - Variant1: architecture/ARCH_log_writer_config_v1.md (writer-specific).
    - Variant2: architecture/logging_configuration.md (legacy compat).
  - Action: Batch1 (6 files) apply_diff to Main1/Main2; Batch2 (6 files) to Main3/variants. Preserve refs.

- **Medium: Queue (8 docs → 4)**:
  - Cluster: architecture/ARCH_batch_operations_v1.md, technical/TECH_command_services_v1.md, +6 overlaps (55% shared queue logic).
  - Targets: 4 consolidated (e.g., queue_core.md, batch_ops.md, command_services.md, processing.md).
  - Action: Group into 4, write_to_file new targets with merged uniques.

- **Thematic: PyQt (5 docs → 2)**:
  - Cluster: technical/TECH_pyqt_migration_v1.md, architecture/PyQt remnants (e.g., node_color_logic.md overlaps; 52%).
  - Targets: 2 (migration_guide.md, pyqt_deprecation.md).
  - Action: Merge into targets, archive PyQt5 obsoletes.

## 3. Obsoletes Archives (10 out of 15 candidates)
Move to archived/ with YAML reason (--- reason: 'zero refs deprecated' ---). Delete originals post-validation.

- List (prioritized 10):
  1. blueprints/vnc_tab_mockup.md (reason: 'zero refs, deprecated').
  2. architecture/ARCH_cli_main_v1.md (reason: 'outdated CLI, low refs').
  3. blueprints/BLUEPRINT_context_menu_architecture_v1.md (reason: 'superseded by v2').
  4. roadmaps/ROADMAP_vnc_integration_v1.md (reason: 'orphan, 90d inactive').
  5. technical/nodes_not_appearing_issue.md (reason: 'resolved, no usage').
  6. blueprints/vnc_tab_blueprint.md (reason: 'duplicate of mockup').
  7. technical/TECH_pyqt_migration_v1.md (partial PyQt5; reason: 'deprecated remnants').
  8. architecture/ARCH_condensation_analysis_v1.md (reason: 'obsolete analysis').
  9. technical/bstool_append_output_fix.md (reason: 'integrated into main').
  10. technical/hybrid_token_resolution.md (reason: 'superseded by TECH_token_utilities_v1.md').

- Action: For each, read_file, write_to_file archived/[filename] with YAML prepend, then delete original (or mark for manual).

## Validation Steps
- Post-merge: search_files regex 'logging|bstool|queue' (*.md) → confirm no >80% sim pairs.
- Counts: list_files docs/ recursive → 70 files.
- Links/Orphans: search_files 'links to archived' → stable (no increase).
- Report: Generate /logs/documents_analysis_4_2025-10-02_171500.md with before/after, changes list.

## Risks & Mitigations
- Info Loss: Diff review uniques before write.
- Batch Limits: 2-3 batches for logging (12 files).
- Backup: Pre-phase copy /docs/ to /docs/backup_phase4/.