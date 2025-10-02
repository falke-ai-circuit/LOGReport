# 🏗️ PHASE8 Codebase Alignment Blueprint

> **Purpose:** *Implementation blueprint for syncing 70 docs with codebase (Phase7 gaps: 15 outdated refs, 10 obsolete, 5 missing, 14 mismatches → >90% alignment via 44 ops)*

## 📋 Overview
**What:** Documentation-codebase synchronization | **Why:** Prevent drift (Phase7: 75% alignment, gaps in refs/impl) | **Goal:** >90% sync, 0 critical gaps, validated via codebase_search

## 🎯 Requirements
| Type | Requirement | Priority | Target |
|------|-------------|----------|--------|
| Functional | Update 15 outdated (PyQt5→6, .bak removal) | H | Exact refs match codebase (search_files verify) |
| Functional | Archive 10 obsolete to /docs/archived/ w/YAML reason | H | No loss, preserve history (move_file) |
| Functional | Create 5 missing (e.g., TECH_session_manager_v1.md from template+get-code) | M | Full coverage (list_code_definition_names vs doc mentions=0 gaps) |
| Functional | Align 14 mismatches (e.g., queue flow doc=impl via write_to_file) | H | Semantic sync (codebase_search 'queue impl' matches doc) |
| Performance | Batch ops ≤10/file (apply_diff/write_to_file limits) | M | <15s/batch, no timeouts |
| Security | No delete, archive only; validate diffs preserve meaning | H | Diff review, post-validate no loss |

## 🔧 Architecture
```
[Phased ops flow: Updates → Creates → Aligns → Archives → Validate → Report]
Docs (/docs/) ←→ Codebase (src/) via MCP tools (apply_diff, write_to_file, mcp-code-graph get-code)
Memory (project_memory add_observations 'Phase8 outcomes') for patterns
```
| Component | Role | Technology | Integration |
|-----------|------|------------|-------------|
| apply_diff | Surgical updates (15 outdated/mismatches) | MCP tool | Target exact lines (read_file first for precision) |
| write_to_file | New/align docs (5 creates, 14 syncs) | MCP tool | Template (/templates/technical.md) + code extract (get-code) |
| move_file | Archive obsolete (10) | MCP tool (or execute_command mv) | To /docs/archived/ w/YAML reason |
| codebase_search | Post-validate sync (>90%) | MCP tool | Query 'doc-codebase gaps' <10% |
| meta-mind | Task coord (mark_done per phase) | MCP server | Req-479 tasks progression |

## ⚡ Implementation Plan
| Phase | Duration | Goals | Deliverables | Dependencies |
|-------|----------|-------|--------------|--------------|
| **🎯 Foundation** | 1 step | Batch outdated updates (15 via apply_diff, e.g., PyQt5→6 in BLUEPRINT_bstool_integration_v1.md) | 15 diff files applied, verify search_files 'PyQt6' =15/15 | Phase7 report (gaps list) |
| **🚀 Features** | 2 steps | Create 5 missing (write_to_file TECH_session_manager_v1.md: template + get-code session_manager.py); Align 14 mismatches (write_to_file sync queue flow in TECH_command_services_v1.md) | 5 new .md, 14 synced docs, coverage 100% (list_code_definition_names gaps=0) | mcp-code-graph get-code extracts |
| **✨ Polish** | 1 step | Archive 10 obsolete (move_file to /docs/archived/ w/reason YAML); Re-validate links (search_files 'broken src/'=0) | 10 archived, links valid | No blockers |
| **📊 Report** | 1 step | Generate /logs/documents_analysis_8_2025-10-02_191500.md (before 75%→95%, changes list, validation) | Report file via write_to_file | All phases complete |

## 🧪 Testing
**Strategy:** Unit (diff accuracy 100%) • Integration (post-tool codebase_search gaps<10%) • E2E (full sync validation)  
**Gates:** P1→Basic updates • P2→Creates/aligns • P3→Archives/report

## 📊 Resources & Timeline
| Resource | P1 | P2 | P3 | Total |
|----------|----|----|----|-------|
| **Team Size** | 1 (AI architect) | 1 | 1 | 1 |
| **Budget** | 0 | 0 | 0 | 0 |
| **Skills** | MCP tools (apply_diff/write_to_file) | mcp-code-graph extracts | Validation (search_files) | Sequential execution |

## ⚠️ Risks
| Risk | Impact | Prob | Mitigation |
|------|--------|------|------------|
| Inaccurate extract | H | M | get-code precise + manual review diffs |
| Batch limits (>10) | M | L | Group by type (outdated batch1=10, batch2=5) |
| Archive wrong | H | L | YAML reasons, no delete |

## 🔗 Dependencies
**External:** MCP servers (meta-mind coord, mcp-code-graph extracts) • firecrawl (if external best practices needed)  
**Internal:** Phase7 report (/logs/documents_analysis_7_2025-10-01_070000.md) • Templates (/templates/technical.md)

## 📈 Success Metrics
**Technical:** Alignment >90% (codebase_search gaps<10%) • Coverage complete (missing=0) • No loss (diffs preserve meaning)  
**Business:** 44 ops executed, report generated, ready for Phase9

---
**📚 Refs:** *Phase7 report, /templates/documentation/blueprint.md, deepwiki LOGReport sync practices*