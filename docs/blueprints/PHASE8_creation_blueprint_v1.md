# PHASE8 Creation Blueprint v1

## Overview
Design for creating 3 missing docs in Batch1 alignment: ARCH_log_writer_impl_v1.md (full LogWriter impl), ROADMAP_recent_changes_v1.md (.bak diffs/merges), TECH_pyqt_migration_v1.md (PyQt5→6). Constraints: <1000 chars/doc, explicit codebase refs (e.g., src/commander/log_writer.py lines), use templates/documentation/technical.md. Target: Fill 20% gaps (Phase7: missing impl refs in logging/queue). Phases: Template adapt, content gen, ref insert, validate coverage.

## Goals
- Create structured docs with explicit code refs (>80% coverage post-create).
- Preserve existing Batch1 (no overwrites).
- Metrics: Pre 65% coverage → +10% from creates (3/36 docs).
- Compliance: Markdown, YAML metadata, <1000 chars.

## Phases & Deliverables

| Phase | Steps | Artifacts | Metrics |
|-------|-------|-----------|---------|
| **1. Template Prep** | Copy templates/documentation/technical.md; add YAML metadata (created_date:2025-10-01_070500, word_count est<200). | Temp files in /logs/phase8_temp/ | 3 templates ready |
| **2. Content Gen** | ARCH_log_writer_impl: Detail rotation/error (from src/commander/log_writer.py: write_to_log lines 45-60). ROADMAP_recent_changes: Diff .bak (command_queue.py.bak vs main, session_manager.py.bak). TECH_pyqt_migration: PyQt5→6 changes (BLUEPRINT_bstool_integration_v1.md refs). | docs/architecture/ARCH_log_writer_impl_v1.md (450 chars)<br>docs/roadmaps/ROADMAP_recent_changes_v1.md (600 chars)<br>docs/technical/TECH_pyqt_migration_v1.md (500 chars) | Content <1000 chars/doc; explicit refs (e.g., [LogWriter.write_to_log](src/commander/log_writer.py:45)) |
| **3. Ref Insert** | Add cross-refs: log_writer_impl → ARCH_logging_system_v1.md; recent_changes → ARCH_command_queue_v1.md; pyqt_migration → BLUEPRINT_bstool_integration_v1.md. Use insert_content at line 0 for append. | Updated 3 docs with refs | 100% explicit refs; validate search_files regex 'src/commander' |
| **4. Validate** | Compute coverage (read_file + line count refs/code mentions); ensure >80% sync. | /logs/phase8_creation_validation.md | Coverage +10%; 0 outdated |

## Evidence/Rationale
- Phase7 gaps: 20% missing impl (e.g., LogWriter rotation); creates target logging/queue/migration.
- Codebase: Recent .bak (command_queue.py.bak lines 1-50 diffs); PyQt6 in src/commander/qt_init.py.
- Hypotheses: H1 creates fill gaps (+15% coverage); H2 explicit refs →0 unref'd.

## Risks/Mitigation
- Char limit: Condense tables (e.g., |Method|Desc|Ref|).
- Ref accuracy: Use codebase_search 'log writer rotation' pre-insert.
- Blockers: None; fallback manual diffs if .bak read fails.

## Future
- Integrate into Phase8 sync (task-3211); handoff to code mode for impl if needed.