# PHASE8 Sync Blueprint v1

## Overview
Plan for syncing 18 Batch1 docs with codebase (Phase7: 15% sync issues=5 unref'd .bak/changes +20% gaps=7 missing impl +6 inferred partial=18 total). Target: Add explicit refs (e.g., [command_queue.py:15](src/commander/command_queue.py:15)) via insert_content/apply_diff; achieve >80% coverage (pre 65%). Use codebase_search/mcp-code-graph for semantic refs (e.g., 'commander queue patterns'), search_files validate post-sync. Phases: Identify gaps, design inserts, validate coverage/sync %.

## Goals
- Explicit bidirectional refs: Doc→code (add links), code coverage >80% (mentions/impl details).
- Fix unref'd: .bak diffs, recent merges (e.g., command_queue.py.bak → ROADMAP_recent_changes_v1.md).
- Compliance: Markdown links, no >5 lines/insert, regex 'src/commander' count pre/post.

## Identification Strategy
- search_files path=docs regex='command_queue|log_writer|PyQt|bak' file_pattern='*.md' → Target 18 (e.g., 5 sync: logging_system unref'd rotation; 7 gaps: command_services queue impl; 6 partial: bstool_integration PyQt6, session_config NodeManager).
- mcp-code-graph nodes-semantic-search 'batch1 sync gaps commander log writer bstool' → Semantic matches (e.g., log_writer rotation → insert ref line 45).

## Phases & Deliverables

| Phase | Steps | Target Docs (Examples) | Insert Design | Metrics |
|-------|-------|------------------------|---------------|---------|
| **1. Gap ID (6 docs)** | codebase_search 'missing impl refs logging queue bstool'; design insert_content before line 0 (append) or apply_diff for sections. | ARCH_logging_system_v1.md (add rotation), TECH_command_services_v1.md (queue), BLUEPRINT_bstool_integration_v1.md (PyQt6) | ```<br>line:0<br>content:<br>## Codebase Sync<br>- LogWriter rotation: [write_to_log](src/commander/log_writer.py:45-60)<br>- Queue FIFO: [add_command](src/commander/command_queue.py:15)<br>``` | 6 gaps filled; refs count +18 |
| **2. Unref'd Fixes (6 docs)** | search_files '.bak|merge' → Add refs to recent_changes doc; insert diffs summaries. | ARCH_command_queue_v1.md (.bak diff), TECH_bstool_fixes_summary_v1.md (merges), ARCH_session_config_v1.md (NodeManager ties) | ```<br><<<<<<< SEARCH<br>line 20: Future: Async<br>=======<br>line 20: Recent .bak diff: Added throttle [command_queue.py.bak:25 vs main:30] [ROADMAP_recent_changes_v1.md]<br>>>>>>>> REPLACE<br>``` (start_line=20) | 6 unref'd → ref'd; search_files 'bak'=0 post |
| **3. Partial Sync (6 docs)** | mcp-code-graph find-direct-connections 'commander presenter' → Add cross-refs (e.g., session→node_manager). | ARCH_node_manager_architecture.md (config ties), TECH_token_management_guide.md (hybrid), commander_window.md (UI refs) | ```<br>line:0<br>content:<br>### Sync Refs<br>- NodeManager config: [load_nodes](src/commander/node_manager.py:50) [ARCH_session_config_v1.md]<br>``` | 6 partial → full; coverage >80% (line refs/code mentions) |

## Evidence/Rationale
- Phase7: 15% unref'd (5 .bak), 20% gaps (7 missing impl); total 18 actions.
- Codebase: 0 explicit refs (search_files); semantic: log_writer rotation (lines 45-60), queue FIFO (15).
- Hypotheses: H1 inserts + refs →>80% coverage; H2 sync fixes unref'd →0 issues.

## Risks/Mitigation
- Semantic misses: Fallback search_files 'log_writer rotation' for exact lines.
- Over-insert: Limit 1-2 refs/doc; validate char count <200/add.
- Blockers: If graph unavailable, use read_file samples + manual refs.

## Future
- Handoff to code mode for inserts/applies; integrate with report (task-3212).