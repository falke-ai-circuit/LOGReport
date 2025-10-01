---
metadata:
  created_date: "2025-10-01_062200"
  last_modified: "2025-10-01T06:22:00Z"
  last_accessed: "2025-10-01T06:22:00Z"
  word_count: 280
  reference_count: 3
  document_hash: "sha256:phase6_test_hash"
  similarity_index: 0.03
  obsolete_check_date: "2025-10-01"
---

# ARCH Phase 6: Test Strategy for Naming Standardization

## Overview
Validate Phase6: Rename/move 21 Batch1 peripherals to [Type]_[Subject]_[v1].md in /docs/[category]/; 100% compliance, link preservation, no content loss. Types: TECH_/technical/ (13 logging/memory e.g., logging.md → TECH_logging_v1.md), BLUEPRINT_/blueprints/ (8 plans e.g., codebase_implementation_plan_v1.md → BLUEPRINT_codebase_implementation_v1.md). Pyramid: Unit (patterns) → Integration (end-to-end) → Compliance (metrics). Evidence: Pre/post list_files/search_files; O1: 21 actions (count), O2: 100% standards (regex), O3: Report metrics (pre/post tables).

## Test Cases
| ID | Type | Description | Inputs | Expected | Validation |
|----|------|-------------|--------|----------|------------|
| TC-1 | Unit | Regex naming pattern | Sample names (logging.md, memory.md) | Match ^[TYPE]_[a-z_]+_v\d+\.md$ (e.g., TECH_logging_v1.md) | search_files regex; 100% match |
| TC-2 | Unit | Category mapping | File list (21 peripherals) | TECH_ → /technical/, BLUEPRINT_ → /blueprints/, ARCH_ → /architecture/ | Manual map + templates/document_standards.md; 100% correct |
| TC-3 | Integration | Rename/move end-to-end | 21 files (content from read_file) | New paths with full content (write_to_file); old paths gone | list_files pre/post; file count=21 new, content hash unchanged |
| TC-4 | Integration | Link preservation | Refs to old paths (search_files old names) | Replace old → new (search_and_replace if broken) | search_files "old_path"; 0 broken post |
| TC-5 | Compliance | Pre/post metrics | Baseline (Phase5: 0 core viol, 21 misplace) | Post: Names=21 match, Locations=/category/, Compliance=100% | search_files count (names/locations); Δ+100% compliance |
| TC-6 | Edge | Metadata add | Files without YAML | Add metadata (created/last_mod/word_count/hash etc.) | read_file new; YAML present, hash=content SHA256 |
| TC-7 | Edge | v1 default | No [v] files (e.g., logging.md) | Append _v1.md | Regex match _v1$; 100% |
| TC-8 | Negative | Invalid category | Ambiguous file (e.g., optimal_knowledge_organization.md) | Fallback TECH_/technical/ | Manual review; no misplace |

## Execution
- **Tools:** list_files (pre/post inventory), search_files (metrics/refs), read_file (content baseline), write_to_file (new files full content), search_and_replace (link fixes if needed).
- **Sequence:** Pre-metrics → Rename/move batch (≤10/file) → Post-metrics → Link check/replace → Validate compliance.
- **Automation:** Script-like via MCP (e.g., sequential_thinking for steps); manual for edge.
- **Coverage:** 100% files (21), 80% links (search estimate), metrics full.

## Metrics & Oracles
| Metric | Pre (Phase5) | Target Post | Validation |
|--------|--------------|-------------|------------|
| Violations | 21 misplace | 0 | list_files non-ARCH in /architecture/ =0 |
| Compliance | 0% peripherals | 100% | regex match 21/21 |
| Content Integrity | N/A | 100% unchanged | hash pre/post = same |
| Links | N/A | 0 broken | search_files old paths =0 |

- O1:pass: 21 renames/moves (evidence: file count Δ); O2:pass: Standards enforced (evidence: regex/list_files); O3:pass: Metrics/actions in report (evidence: tables).

## Risks & Mitigation
- Link breaks: search_files + replace (low risk, <5% refs); Content loss: Full copy (none); Conflicts: Backup old (rename first). Conf: 95% (tools reliable).