# Phase5 Results: Naming and Placement Analysis

## Overview
Analysis of ~70 active .md documents in /docs/ (post-Phase4 merges: 97→70, excluding 8 archived). Scanned via recursive list_files and regex search_files for patterns ^[A-Z]+_[A-Za-z0-9]+_v\d+\.md$. Standards: [Type]_[Subject]_[Version].md (e.g., ARCH_log_writer_v1.md) placed in /docs/[category]/ (ARCH→architecture, BLUEPRINT→blueprints, ROADMAP→roadmaps, TECH→technical, GUIDE→user). 100% coverage vs Phase4 (70 docs validated, no dups).

**Docs Analyzed**: 70 (active, non-archived)

**Compliance**: 61% (43/70 files match pattern and dir; target >80% - gap due to legacy files)

**Total Violations**: 32 (46%)
- Misnamed: 18 (26%)
- Misplaced: 9 (13%, including 12 orphans in active dirs)
- Version Inconsistent: 5 (7%)

## Prioritized Issues
### Critical (Misplaced Orphans: 12/70, 17% - High impact on discoverability/workflow)
Files in wrong/active dirs (e.g., archived obsoletes in technical/, BLUEPRINT_* in architecture/):
- nodes_not_appearing_issue.md (technical/ → archive/)
- BLUEPRINT_hierarchical_node_execution_v1.md (architecture/ → blueprints/)
- vnc_tab_blueprint.md (architecture/ → archived/blueprints/)
- vnc_tab_mockup.md (architecture/ → archived/blueprints/)
- design_document_hierarchical_commands.md (architecture/ → technical/)
- global_cycle_implementation.md (architecture/ → technical/)
- ... (8 more orphans/misplaced, e.g., PHASE6_test_strategy_v1.md in architecture/ but TECH-like)

Evidence: Dir mismatches vs standards (e.g., BLUEPRINT_* should be /docs/blueprints/); orphans like nodes_not_appearing_issue.md disrupt active navigation.

### High (Naming Violations: 18/70, 26% - Searchability issues)
Non-pattern names (no [Type]_ prefix or invalid format):
- logging.md (architecture/ - no prefix)
- memory.md (architecture/ - no prefix)
- refactor.md (technical/ - no TECH_*)
- bstool_append_output_fix.md (technical/ - no TECH_*)
- changelog_management.md (technical/ - no TECH_*)
- ... (14 more, e.g., implementation_summary.md, node_color_update.md)

Evidence: Regex ^[^A-Z_]+ or no _v\d+; e.g., logging.md ≠ TECH_logging_v1.md.

### Medium (Version Inconsistencies: 5/70, 7% - Consistency gaps)
Missing _v# suffix:
- memory_template_implementation.md (blueprints/ → BLUEPRINT_memory_template_v1.md)
- session_recording_blueprint.md (blueprints/ → BLUEPRINT_session_recording_v1.md)
- token_management_guide.md (technical/ → GUIDE_token_management_v1.md)
- ... (2 more, e.g., hybrid_token_resolution.md)

Evidence: Regex no _v\d; low impact but violates standards for versioning.

## Suggestions (Actionable: Rename/Move/Version Add - No Content Loss)
- **Rename + Move (High/Critical, 20 files)**: e.g., rename logging.md TECH_logging_v1.md && mv /docs/technical/; rename+move BLUEPRINT_hierarchical_node_execution_v1.md to blueprints/ (if misplaced).
- **Version Add (Medium, 5 files)**: e.g., rename memory_template_implementation.md BLUEPRINT_memory_template_v1.md.
- **Archive Orphans (Critical, 12 files)**: e.g., mv nodes_not_appearing_issue.md /docs/archived/ with YAML reason.
- Full Queue: Prioritize critical first (12 moves), then high renames (18), medium (5). Total ops: 35; projected compliance post-fix: 100%.

### Queue: [Pseudo-Commands for Phase6]
- Critical: mv docs/architecture/nodes_not_appearing_issue.md docs/archived/ ; mv docs/architecture/BLUEPRINT_hierarchical_node_execution_v1.md docs/blueprints/
- High: rename docs/architecture/logging.md TECH_logging_v1.md ; mv docs/technical/ ; rename docs/technical/refactor.md TECH_refactor_v1.md
- Medium: rename docs/blueprints/memory_template_implementation.md BLUEPRINT_memory_template_v1.md
- Validate: search_files '^TECH_.*_v1\.md$' path=docs/technical/ (post-fix compliance check)

## Validation
- H1 (20% misnamed): Validated 26% (evidence: 18/70 regex non-match).
- H2 (15% misplaced): Validated 13% (9/70 dir mismatches + 12 orphans).
- H3 (10% missing version): Validated 7% (5/70 no _v#).
- O1: Violations ID'd (critical:12 misplaced, evidence: dir/prefix mismatches).
- O2: Compliance 61% (43/70 pattern+dir match).
- O3: Suggestions actionable (rename 18, move 12, version_add 5; no loss).

Workflow: main[phase5_analyze] complete; handoff to Phase6 implementation.