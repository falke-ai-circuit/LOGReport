# BLUEPRINT_documents_condensation_v1.md

## Overview
Systematic plan for Phases 1-2: Analyze & fix 248 .md docs in /docs/ for compliance with /templates/document_standards.md. Target: Ultra-condensed format (60-80 chars avg/line, max density via tables/inline/symbols ✅❌⚠️), structure (5-10 sections, no nesting>2 levels), metadata (YAML block). Preserve knowledge; /docs/ only. From Phase0: 12 clusters (e.g., Architecture:72 files), 15 core targets. Pre-metrics: 60% verbose (>80 chars/line), 70% missing tables/symbols, 100% no metadata. Post-target: Density +50%, compliance 100%.

## Phases
| Phase | Actions | Tools | Inputs | Outputs | Metrics |
|-------|---------|-------|--------|---------|---------|
| Scan | List all .md; regex scan verbose lines (^.{80,}$); check metadata absence (no YAML keys: created_date|last_modified|word_count|reference_count|document_hash|obsolete_check_date|section_count|internal_link_count); % tables (<20% lines match \|---\|); symbols (<50% lines have ✅❌⚠️). Prioritize clusters (Architecture first). | list_files (recursive=true); search_files (regex ^.{80,}$, \|\-\-\-\| for tables, ✅❌⚠️ for symbols, YAML metadata block). | /docs/ (248 files); standards.md. | Gap report: Files|Pre-chars/line|%Tables|%Symbols|Metadata%. | Coverage 100%; verbose files 60%; gaps identified 100%. |
| Transform | For each file: Add YAML metadata (auto-gen: created_date:2025-10-03; last_modified:now; word_count:len(content); etc.); replace verbose paras/lists>5 items with tables (|Field|Value|Status|); flatten H4 under H3 (inline • subpoints); compress sentences (pipes \| for lists, abbreviations); enforce 60-80 chars/line. Batch 10 files. Preserve unique insights. | read_file (batch 10); apply_diff (surgical edits); write_to_file (full if small). | Gap report; standards.md. | Updated files (condensed, compliant). | Density +50% (avg chars/line <80); compliance 100%; no knowledge loss (diff validate). |
| Validate | Re-scan post-fix: char/line count; % tables/symbols/metadata; structure (5-10 sections, no deep nesting). Test: Pre/post metrics; checklist (tables where lists>3, symbols 90%+, metadata 100%). | search_files (post-regex); read_file (sample 20%). | Updated files. | Validation report: Compliance=100%, density=+50%. | O1:100% compliance; O2:density +50%; O3:gaps fixed (no filler, aids 90%+). |

## Rules
- **Detection Regex**: Verbose: ^.{80,}$ (lines>80 chars); Missing metadata: No block with keys created_date|last_modified|word_count|reference_count|document_hash|obsolete_check_date|section_count|internal_link_count; No tables: <20% lines match \|---\| pattern; No symbols: <50% lines contain ✅❌⚠️.
- **Transformation Rules**: Paras→tables (e.g., long desc → |Issue|Cause|Fix|Status✅); lists>5 → |Item|Detail|Note|; Flatten: Merge H4 to H3 with •; Compress: Use \| pipes (e.g., Steps: Load\|Parse\|Validate); Add metadata YAML top (e.g., metadata: {created_date:2025-10-03, last_modified:2025-10-03T08:53, word_count:500, ...}).
- **Sample Transform**: Original: "This is a long verbose paragraph explaining something in detail that exceeds 80 characters and lacks structure." → |Field|Description|Status| |Verbose Para|Long explanation lacks tables/symbols|Replace with table✅| (60 chars). List: - Item1 - Item2 → |Items|Details| |Item1|Desc1|•Sub| |Item2|Desc2|.

## Test Strategy
- **Pre/Post Metrics**: Char/line avg (target <80); table % (>80% lists converted); symbol % (>90% status/needs); metadata presence (100% YAML blocks).
- **Checklist**: Structure (5-10 sections✅); no nesting>2 (flatten✅); visual aids (tables/symbols 90%+✅); density (60-80 chars avg✅).
- **Validation**: Sample 20 files manual review; full scan post-batch; report gaps fixed.

## Constraints
- /docs/ only; batch 10 files (tool limits); preserve knowledge (archives if merged); no external changes.

## Report Output
Generate /logs/documents_analysis_1-2_2025-10-03_090000.md: |File|Pre-chars|Post-chars|Gaps Fixed (verbose|tables|symbols|metadata)|Compliance| (all 248 rows summary).