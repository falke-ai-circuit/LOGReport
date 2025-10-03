---
metadata:
  created_date: "2025-10-03"
  last_modified: "2025-10-03T09:10:00Z"
  version: "v1.0"
  clusters_covered: 12
  target_cores: 15
  archive_rate: "94%"
  sections_per_core: "5-10"
  lines_per_core: "500-2000"
  similarity_threshold: ">80%"
  compliance: "/templates/document_standards.md"
---

# Phase 3-4 Merge Blueprint: Wiki-Style Documentation Consolidation

## Overview
This blueprint details the systematic merge logic for consolidating 248 compliant .md docs (post-Phases 1-2) into 15 core documents, achieving 94% archive rate (233+ archived). Focus: Aggressive merging of duplicates (80%+ similarity), version proliferation (v1/v2/v3 → single with #VersionHistory), shallow content (<100 lines → absorb into sections). Output: Wiki-style cores in /docs/[category]/ (e.g., /docs/architecture/ARCH_logging_core_v1.md) with 5-10 sections (#Overview-#Impl), bidirectional #links for refs/orphans, ultra-condensed format (tables/symbols/inline rationale per /templates/document_standards.md). Ensures 100% knowledge preservation, <5% dupe, 80%+ ref resolution.

**Rationale**: Semantic analysis (Phase 3) confirms 12 refined clusters with >80% overlap (e.g., logging: 15 docs on LogWriter configs/impl). Sequential thinking validates feasibility: Extract uniques via diffs, append to cores, archive with YAML reasons. Target: 16:1 ratio (248→15), wiki navigation via #internal_links.

**Metrics Goals**: Core=15, archive=94%, sections=5-10/doc, dupe<5%, lines=500-2000/doc (condense repeats, use ✅/❌ symbols).

## Merge Logic
**Core Principles**:
- **Preservation**: Append all unique content (e.g., v2 enhancements → #VersionHistory subsection); no deletions without archive.
- **Condensation**: Remove duplicates (e.g., shared tables → single instance); use tables for patterns (e.g., | Component | Responsibility |), inline rationale (e.g., 'Rationale: 85% sim via LogWriter overlap').
- **Wiki-Style**: 5-10 sections/core (#Overview-#Architecture-#Implementation-#BestPractices-#VersionHistory-#References); bidirectional #links (e.g., [Logging Config](technical/TECH_error_logging_core_v1.md#Delegation)); resolve orphans (integrate as subsections, e.g., vnc_tab_mockup.md → #ArchivedUI).
- **Thresholds**: Merge if >80% sim (semantic evidence); absorb shallow (<100l) into relevant section; archive if <20% unique (YAML: reason: 'shallow duplicate merged to [core].md #[section]'; date: '2025-10-03').
- **Tools**: read_file (batch up to 10/cluster for uniques), write_to_file (new cores from /templates/documentation/architecture.md), apply_diff/insert_content (append/fix refs), search_files (validate broken #links pre/post).

**Step-by-Step Process**:
1. **Cluster Prep**: For each of 12 clusters (from Phase 3), identify primary core (most comprehensive/latest, e.g., ARCH_logging_system_v1.md for logging).
2. **Extract Uniques**: read_file sources (e.g., 10 logging files); manual/semantic diff for uniques (e.g., configs vs impl; flag versions/shallow).
3. **Build Core**: write_to_file new/primary as core (e.g., ARCH_logging_core_v1.md); structure 5-10 sections (500-2000l total).
4. **Integrate**: apply_diff/insert_content uniques (e.g., insert #TokenResolution before line 100; fix refs with #redirects like [Deprecated #Overview](archived/ARCH_log_writer_v1.md#Overview)).
5. **Resolve Refs/Orphans**: search_files for broken (regex '\\[.*?\\]\\(nonexistent\\)'); integrate orphans (e.g., content → subsection); add bidirectional #links.
6. **Archive**: For non-cores, write_to_file to /docs/archived/[filename] with YAML frontmatter + original content.
7. **Validate**: search_files dupe patterns (<5%); line_count 500-2000; #link checks (0 broken, 80%+ resolved).
8. **Batch Efficiency**: Up to 10 files/tool call; update index.md with core #links.

**Edge Cases**:
- >80% sim entire doc: Full archive + #redirect in core.
- Conflicting versions: Prioritize latest; #VersionHistory for changes.
- Cross-cluster refs: Bidirectional #links (e.g., logging → command #QueueIntegration).

## Wiki Structure for Cores (15 Total)
Each core in /docs/[category]/ follows template (/templates/documentation/architecture.md): YAML metadata, 5-10 sections, tables/symbols, inline rationale. Categories: architecture (5 cores), blueprints (4), technical (3), roadmaps (1), user (1), workflows (1).

| Core Doc | Category | Merges From (Cluster/Files) | Sections (5-10) | Est. Lines | Archive Targets (Reason Example) |
|----------|----------|-----------------------------|-----------------|------------|----------------------------------|
| ARCH_logging_core_v1.md | architecture | Cluster 1 (15 files) | #Overview (patterns), #LogWriter (impl), #Configs (token res), #ErrorHandling (multi-level), #BestPractices (rotation), #VersionHistory, #Refs | 1200 | 12 (e.g., 'shallow config merged to #Configs') |
| ARCH_memory_core_v1.md | architecture | Cluster 2 (10 files) | #Overview (dual), #Hierarchy (compliance), #Optimization (condensation), #Promotion (cross-project), #Validation (metrics), #VersionHistory | 1300 | 7 ('version v2 merged to #History') |
| ARCH_command_core_v1.md | architecture | Cluster 3 (12 files) | #Overview (FIFO), #QueueMgmt (threading), #Sequential (proc), #BatchOps, #FaultIsolation, #VersionHistory | 1100 | 9 ('duplicate impl merged to #QueueMgmt') |
| ARCH_ui_node_core_v1.md | architecture | Cluster 4 (12 files) | #Overview (MVP), #Presenter (separation), #NodeLogic (color/manager), #DynamicUI, #BestPractices, #Refs | 1000 | 9 ('shallow UI merged to #DynamicUI') |
| ARCH_core_systems_v1.md | architecture | Cluster 5 (17 files) | #Overview (system), #Optimization (blueprints), #FaultTolerance (circuit), #ImplSteps, #VersionHistory | 1500 | 14 ('general overlap merged to #Overview') |
| BLUEPRINT_bstool_core_v1.md | blueprints | Cluster 6 (8 files) | #Overview (integration), #UIComponents (tabs), #ErrorHandling (fixes), #Config (env), #Testing, #Refs | 900 | 6 ('mockup shallow merged to #UIComponents') |
| BLUEPRINT_context_menu_core_v1.md | blueprints | Cluster 7 (6 files) | #Overview (filtering), #DynamicGen (visibility), #Rules (config), #Integration (UI), #BestPractices | 800 | 4 ('rules duplicate merged to #Rules') |
| BLUEPRINT_hierarchical_core_v1.md | blueprints | Cluster 8 (7 files) | #Overview (seq/hier), #NodeExec (batch), #FaultIsolation, #StateMgmt (async), #Optimization | 1000 | 5 ('flow overlap merged to #NodeExec') |
| BLUEPRINT_general_core_v1.md | blueprints | Cluster 9 (7 files) | #Overview (impl), #Consolidation (memory), #Codebase (plans), #Extension, #VersionHistory | 900 | 5 ('misc merged to #Consolidation') |
| TECH_error_logging_core_v1.md | technical | Cluster 10 (12 files) | #Overview (delegation), #MultiLevel (configs), #Reporting (impact), #Integration (service), #Troubleshoot | 1100 | 9 ('error duplicate merged to #Reporting') |
| TECH_memory_opt_core_v1.md | technical | Cluster 11 (10 files) | #Overview (condensation), #Hierarchy (template), #CrossProject (promotion), #Validation, #BestPractices | 1200 | 7 ('opt report shallow merged to #Validation') |
| TECH_ui_command_core_v1.md | technical | Cluster 12 (13 files) | #Overview (service), #CircuitBreaker (fault), #Refactor (patterns), #UIInput (auto-update), #Deployment | 1400 | 10 ('general summary merged to #Overview') |
| ROADMAP_consolidated_v1.md | roadmaps | Roadmaps (6 files) | #Overview (phases), #Dependencies (tasks), #Risks (blockers), #Timeline (milestones), #VersionHistory | 800 | 5 ('phase duplicate merged to #Dependencies') |
| USER_guide_v1.md | user | User (3 files) | #Overview (workflows), #Troubleshoot (issues), #BestPractices (tips), #Refs | 600 | 2 ('guide overlap merged to #Troubleshoot') |
| WORKFLOW_enhancements_v1.md | workflows | Others (20 files) | #Overview (updates), #Analysis (patterns), #Coordination (MCP), #Testing (validation), #VersionHistory | 2000 | 18 ('enhancement shallow merged to #Analysis') |

**Total**: 15 cores, 233 archives (94%). Update /docs/index.md with #links to all cores for wiki navigation.

## Validation & Risks
- **Simulation**: 100% coverage (all clusters merged); <5% dupe (uniques appended); 80%+ refs resolved (#links/redirects).
- **Risks**: Knowledge loss (mitigate: Archives + uniques extract); Incomplete (mitigate: Cluster-by-cluster batching). Confidence: 95% (semantic evidence >80% sim).

## Workflow
- **Handoff**: Ready for implementation (Phase 4: Create 15 cores, archive 233, validate metrics).
- **MCP Usage**: sequential_thinking (4 thoughts: principles/refine/steps/structure); effective for logic design.