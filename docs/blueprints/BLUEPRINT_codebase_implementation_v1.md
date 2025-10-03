# 📐 Blueprint: Codebase Implementation Plan - Batch 3 Roadmaps (v1.0)

## I. Overview
| Field | Value |
|-------|-------|
| **Objective** | Align roadmap documentation with the current codebase and future plans, addressing identified gaps, inconsistencies, and outdated information. |
| **Scope** | Updating existing roadmap documents, creating new roadmap documents for recently implemented features, and outlining development tasks for missing features. |
| **Deliverables** | Updated roadmap documents, new roadmap documents, detailed `mcp-code` subtasks, comprehensive test strategy. |
| **Context** | Based on the "Codebase Analysis Report - Batch 3 Roadmaps" (logs/documents_analysis_codebase_2025-09-29T194257.md). |
| **Risks** | Complexity of updating multiple documents, potential for new inconsistencies, resource allocation for `mcp-code` tasks. |
| **Mitigation** | Phased implementation, clear task delegation, thorough review process, adherence to documentation standards. |

## II. Phases & Milestones

### Phase 1: Existing Roadmap Updates
| Milestone | Deliverables | Tasks | Status |
|-----------|--------------|-------|--------|
| All existing roadmap documents updated to reflect current codebase. | Updated `ROADMAP_documentation_consolidation_v1.md`, `ROADMAP_task_management_v1.md`, `ROADMAP_commander_module_v1.md`, `ROADMAP_vnc_integration_v1.md`. | 1.1. Update `ROADMAP_documentation_consolidation_v1.md`: Mark unimplemented scripts (file relocation, link checking, taxonomy compliance, content checksum validation, documentation index update, contribution guidelines) as 'planned/deferred'. • 1.2. Update `ROADMAP_task_management_v1.md`: Mark unimplemented features ('Task Lifecycle', 'Complexity Scoring', 'Priority Management', 'MCP Server Integration', 'Reporting') as 'planned/deferred'. • 1.3. Update `ROADMAP_commander_module_v1.md`: Mark 'OCR Service', FTP features, log handling ('LSR Formatter', 'Auto-Header'), and security features ('Credential Vault', 'Input Sanitization') as 'planned/deferred'. • 1.4. Update `ROADMAP_vnc_integration_v1.md`: Mark 'Redaction' for session recording as 'planned/deferred'. • 1.5. Harmonize log writing methods in `ROADMAP_bstool_integration_v1.md` (from Batch 2, ensure consistency with `LogWriter.append_to_file` and direct file writing). • 1.6. Update PyQt version reference in `ROADMAP_bstool_integration_v1.md` (from Batch 2, PyQt5 to PyQt6). • 1.7. Clarify `_get_current_item_from_data` in `BLUEPRINT_context_menu_v1.md` (from Batch 2, clarify 'mock' nature). | [ ] Pending |

### Phase 2: New Roadmap Documentation for Implemented Features
| Milestone | Deliverables | Tasks | Status |
|-----------|--------------|-------|--------|
| New roadmap documents created for all recently implemented features. | New `ROADMAP_context_menu_filtering_v1.md`, `ROADMAP_dual_memory_consolidation_v1.md`, `ROADMAP_dynamic_ip_extraction_v1.md`, `ROADMAP_enhanced_token_handling_v1.md`, `ROADMAP_sequential_reasoning_v1.md`, `ROADMAP_external_validation_v1.md`, `ROADMAP_memory_management_updates_v1.md`, `ROADMAP_command_queue_fix_v1.md`, `ROADMAP_node_resolution_fix_v1.md`. | 2.1. Create `ROADMAP_context_menu_filtering_v1.md`. • 2.2. Create `ROADMAP_dual_memory_consolidation_v1.md`. • 2.3. Create `ROADMAP_dynamic_ip_extraction_v1.md`. • 2.4. Create `ROADMAP_enhanced_token_handling_v1.md`. • 2.5. Create `ROADMAP_sequential_reasoning_v1.md`. • 2.6. Create `ROADMAP_external_validation_v1.md`. • 2.7. Create `ROADMAP_memory_management_updates_v1.md`. • 2.8. Create `ROADMAP_command_queue_fix_v1.md`. • 2.9. Create `ROADMAP_node_resolution_fix_v1.md`. | [ ] Pending |

### Phase 3: Development of Missing Features (Delegation to `mcp-code`)
| Milestone | Deliverables | Tasks | Status |
|-----------|--------------|-------|--------|
| Detailed `mcp-code` subtasks defined for each missing feature. | `mcp-code` tasks for documentation consolidation scripts, task management features, security features, VNC redaction, log handling features, and IP extraction integration. | 3.1. `mcp-code` task: Develop documentation consolidation scripts (file relocation, link checking, taxonomy compliance, content checksum validation, documentation index update, contribution guidelines). • 3.2. `mcp-code` task: Implement task management features ('Task Lifecycle', 'Complexity Scoring', 'Priority Management', 'MCP Server Integration', 'Reporting'). • 3.3. `mcp-code` task: Implement security features ('Credential Vault', 'Input Sanitization'). • 3.4. `mcp-code` task: Implement VNC redaction. • 3.5. `mcp-code` task: Implement/clarify 'LSR Formatter' and 'Auto-Header' in `LogWriter`. • 3.6. `mcp-code` task: Ensure direct integration of 'IP extraction from log filenames' with `SessionManager` for VNC. | [ ] Pending |

## III. Test Strategy
| Aspect | Approach | Metrics |
|--------|----------|---------|
| **Documentation Accuracy** | Manual review and cross-referencing with codebase. | % of discrepancies identified and resolved. |
| **Completeness** | Checklist against identified gaps in analysis report. | % of gaps addressed. |
| **Code-Doc Synchronization** | Verification of feature descriptions against actual code implementation. | % of synchronization issues resolved. |
| **Link Validation** | Automated link checking for internal and external references. | % of broken links identified and fixed. |
| **Standard Compliance** | Review against `document_standards.md` template. | % of compliance with naming, structure, metadata. |

## IV. Resource Requirements
| Role | Responsibilities |
|------|------------------|
| **`mcp-architect`** | Overall planning, design, oversight, and final review. |
| **`mcp-code`** | Implementation of missing features, creation of new documentation, updates to existing documentation. |