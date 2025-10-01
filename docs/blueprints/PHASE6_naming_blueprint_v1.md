---
metadata:
  created_date: "2025-10-01_062100"
  last_modified: "2025-10-01T06:21:00Z"
  last_accessed: "2025-10-01T06:21:00Z"
  word_count: 450
  reference_count: 5
  document_hash: "sha256:phase6_blueprint_hash"
  similarity_index: 0.05
  obsolete_check_date: "2025-10-01"
---

# BLUEPRINT Phase 6: Naming Standardization Implementation

## Objective
Enforce [Type]_[Subject]_[v].md pattern + /docs/[category]/ placement for Batch1 peripherals (21 files misplaced in /docs/architecture/ post-Phase5). Preserve content/links; high prio core ARCH (monitor), med peripherals. Target: 100% compliance, 0 violations. Solves: Dir pollution (60% logging/memory → /technical/, 40% plans → /blueprints/).

## Phases & Milestones
| Phase | Description | Inputs | Outputs | Deliverables | Timeline | Dependencies |
|-------|-------------|--------|---------|--------------|----------|--------------|
| **1. Inventory** | List 21 peripherals via list_files (/docs/architecture/ non-ARCH_*); categorize (60% TECH_logging/memory: logging.md etc.; 40% BLUEPRINT_plans: codebase_implementation_plan_v1.md etc.); validate Phase5 evidence. | Phase5 report, list_files output | Categorized list (21 files, mappings e.g., logging.md → TECH_logging_v1.md /technical/) | /docs/analysis/Batch1_violations_inventory_v1.md | 5min | None |
| **2. Rename** | Apply [Type]_[Subject]_[v1].md: TECH_ for technical/logging/memory (e.g., TECH_logging_configuration_v1.md); BLUEPRINT_ for plans/impl (e.g., BLUEPRINT_codebase_implementation_v1.md); ARCH_ for arch-related (e.g., ARCH_node_manager_v1.md if fits). Use search_and_replace for pattern match/add prefix/v. | Categorized list, templates/document_standards.md | Renamed content (preserve YAML metadata if present; add if absent) | Updated files (temp paths) | 10min | Phase1 |
| **3. Move** | Relocate to /docs/[category]/: /technical/ (TECH_*), /blueprints/ (BLUEPRINT_*), /architecture/ (ARCH_*). Use write_to_file (new path, full content). Auto-create dirs. | Renamed files | Moved files in correct /docs/[category]/ | Final paths (e.g., /docs/technical/TECH_logging_v1.md) | 5min | Phase2 |
| **4. Validate** | Check compliance (list_files + regex ^[TYPE]_[a-z_]+_v\d+\.md$); test links (search_files for refs to old paths, replace if broken); metrics pre/post (names/locations/compliance via search_files count). | Moved files | Validation report (100% match, 0 broken links) | Pre/post metrics table | 5min | Phase3 |

## Resources
- **Tools:** list_files (inventory), search_and_replace (rename), write_to_file (move/content), search_files (validate/links/metrics).
- **Standards:** templates/document_standards.md ([Type] patterns, metadata YAML: created/last_mod/word_count/hash etc.).
- **Priorities:** High: 13 logging/memory (impact: nav/search); Med: 8 plans (consistency); Low: Metadata adds (post-rename).
- **Risks/Mitigation:** Link breaks → search_files + replace old paths; Content loss → Full copy in write_to_file; Conflicts → Backup old via rename first.

## Test Strategy
- **Unit:** Regex validation on sample renames (e.g., logging.md → TECH_logging_v1.md match).
- **Integration:** End-to-end: Inventory → Rename → Move → list_files confirm paths/names; search_files no broken refs.
- **Compliance:** Pre: 0% peripherals compliant; Post: 100% (metrics: names=21 match, locations=/category/, compliance=100%).
- **Edge:** v1 default if no v; Category fallback (technical if ambiguous); Obsolete check (hash unchanged).
- **Success:** O1: 21 renames/moves (evidence: file count); O2: 100% standards (evidence: regex/list_files); O3: Report w/metrics (evidence: pre/post tables).

## Metrics
| Metric | Target | Baseline (Phase5) | Δ |
|--------|--------|-------------------|---|
| Compliance | 100% | 0% peripherals | +100% |
| Redundancy Reduction | N/A | 21 misplaced | -21 violations |
| Effort | <30min | N/A | Track via timestamps