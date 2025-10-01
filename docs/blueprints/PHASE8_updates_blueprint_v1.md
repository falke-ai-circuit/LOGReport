# PHASE8 Updates Blueprint v1

## Overview
Plan for updating 15 refs in Batch1 (Phase7: 10% outdated=3 explicit +12 inferred from gaps/stubs/paths). Target: Fix stubs (e.g., ARCH_command_system_v1.md redirect), paths (pre-Phase6 renames in node_manager), versions (PyQt5→6 in bstool_integration). Use apply_diff for surgical edits (SEARCH exact lines/whitespace, REPLACE with updated refs). Pre-metrics: 10% outdated (3/36). Target: 0% post-update, +5% coverage. Phases: Identify via search_files, design diffs, validate.

## Goals
- Surgical fixes: Update paths/stubs/versions without full rewrites.
- Explicit refs: Add [src/commander/...](path:line) where missing.
- Compliance: Preserve metadata, <10 lines/diff, regex validate post-apply.

## Identification Strategy
- Use search_files path=docs regex='PyQt5|stub redirect|old_path_pattern' file_pattern='*.md' → Target 15 docs (e.g., 3 explicit: command_system, bstool_integration, node_manager; +12: logging_system paths, command_services stubs, session_config renames).
- Inferred from Phase7 gaps: 7 gaps →5 updates (e.g., ARCH_logging_system_v1.md line 76 LogReportGUI→commander/log_writer.py); 5 sync →4 updates (unref'd .bak → add diffs refs); 3 outdated →3 direct.

## Phases & Deliverables

| Phase | Steps | Target Docs (Examples) | Diff Design | Metrics |
|-------|-------|------------------------|-------------|---------|
| **1. Stub Fixes (5 docs)** | SEARCH stub redirects/old stubs; REPLACE with merged content + ref to new (e.g., ARCH_command_system_v1.md: merge queue details). | ARCH_command_system_v1.md, TECH_command_services_v1.md (stubs) | ```<br><<<<<<< SEARCH<br>line 10: Stub: See ARCH_command_queue_v1.md<br>=======<br>line 10: Integrated: Command queue uses FIFO [src/commander/command_queue.py:15]<br>>>>>>>> REPLACE<br>``` (start_line=10) | 5 stubs fixed; 0 redirects |
| **2. Path Updates (5 docs)** | SEARCH pre-Phase6 paths (e.g., gui_workers.py); REPLACE with src/commander/... . | ARCH_node_manager_architecture.md, ARCH_session_config_v1.md (renames) | ```<br><<<<<<< SEARCH<br>line 25: import from gui_workers<br>=======<br>line 25: import from src/commander/node_manager.py [src/commander/node_manager.py:1]<br>>>>>>>> REPLACE<br>``` (start_line=25) | 5 paths valid; search_files 'old_path' =0 |
| **3. Version Fixes (5 docs)** | SEARCH PyQt5/outdated (e.g., bstool); REPLACE PyQt6 + migration note. | BLUEPRINT_bstool_integration_v1.md, TECH_bstool_fixes_summary_v1.md | ```<br><<<<<<< SEARCH<br>line 92: PyQt5.QtCore<br>=======<br>line 92: PyQt6.QtCore (migrated Phase7) [src/commander/qt_init.py:10]<br>>>>>>>> REPLACE<br>``` (start_line=92) | 5 versions current; regex 'PyQt5'=0 |

## Evidence/Rationale
- Phase7: 10% outdated (stubs/old paths); examples: command_system stub, bstool PyQt5, node_manager pre-Phase6.
- Codebase: Recent changes src/commander/command_queue.py (no .bak ref in docs); PyQt6 in qt_init.py.
- Hypotheses: H1 updates fix 10% outdated (15 actions); H2 apply_diff →0 breaks (validate lines).

## Risks/Mitigation
- Line shifts: Use read_file pre-diff, exact SEARCH whitespace.
- Over-updates: Limit to Batch1 (15/36); test apply_diff on temp.
- Blockers: If search_files misses, fallback manual from samples (e.g., ARCH_logging line 76).

## Future
- Handoff to code mode for apply_diff execution; integrate with sync (task-3211).