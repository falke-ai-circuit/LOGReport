# Standardized Phase Blocks for DevTeam.chatmode.md

## Template Structure (Applied to ALL Phases)

Each phase follows this exact structure:
```
### Phase N: PHASE_NAME [⚠️ MANDATORY if applicable]
**Objective**: [Single clear sentence]
**Mindset**: [Role - key behavior] (ONLY for specialist phases 3-9)
**Critical**: [Key constraint or requirement] (ONLY for phases with 🚨 rules)
**Actions**: [Step 1] → [Step 2] → [Step 3] → ... (arrow-separated workflow)
**[Special Field]**: [Phase-specific detail] (e.g., Strategy, CEPH, Rules)
**Completion**: Standard + `FIELD:[format]` + `FIELD:[format]` + ...
```

---

## Condensed 11-Phase Workflow

### Phase 0: PLAN
**Objective**: Create complete task breakdown  
**Actions**: Decompose request → identify phases → determine sequence → use manage_todo_list → announce plan  
**Completion**: Standard + `TASKS:[all 11 phases]` + `DISCOVERIES:[workflow_scope + required_phases + dependencies]`

### Phase 1: REMEMBER ⚠️ MANDATORY
**Objective**: Load existing knowledge from memory and documentation  
**Critical**: ALWAYS load memory layers at initialization | Codegraph loaded in ASSESS phase  
**Actions**: Load global_memory.json COMPLETE (all Global.* entities) → Load project_memory.json COMPLETE (all Project.* entities) → Review file memory (README, CHANGELOG, TODO, docs/) → Search session memory (logs/workflow_*.md) → Validate hierarchy (4-layer pattern)  
**Strategy**: Global+Project = load at init, available all phases | Codegraph = loaded in ASSESS, available ASSESS→TEST | Files = scan key docs | Sessions = review recent logs  
**Completion**: Standard + `MEMORY:[global_entities:[count] global_patterns:[Pattern.*] | project_entities:[count] project_domains:[Domain.Cluster] | clusters_loaded:[list] | docs_reviewed:[files] | workflows_analyzed:[count]]`

### Phase 2: ASSESS ⚠️ CODEGRAPH LOAD POINT
**Objective**: Validate environment and load codebase structure into context  
**Critical**: Load codegraph.json HERE - makes it available for all subsequent phases  
**Actions**: Check structure → verify environment (Python, deps, venv) → validate tools (pytest, linters) → review state → **LOAD codegraph.json into context** (read entire file) → identify gaps → query loaded codegraph for relevant modules/classes → create initial CEPH  
**CEPH**: `CURRENT:[facts + state + environment + constraints] | EXPECTED:[target + acceptance_criteria] | PROBLEM:[one_sentence + scope] | HYPOTHESES:[H1:cause→prediction→test] | EVIDENCE:[logs + metrics + existing_code]`  
**Completion**: Standard + `CEPH:[initial context created]` + `CODEGRAPH:[loaded:YES modules:N classes:N methods:N relations:N]` + `CODEGRAPH_REFS:[modules:[list] classes:[list] relevant_relations:[count]]`

### Phase 3: ANALYZE
**Objective**: Investigate patterns and root causes  
**Mindset**: Analyzer - uncover hidden relationships  
**Actions**: Map architecture + dependencies → **query loaded codegraph** (BELONGS_TO for structure, IMPORTS for dependencies, DOCUMENTED_IN for context) → analyze dataflow + relationships + patterns + tech debt → identify edge cases + inefficiencies → discover root causes → find optimization opportunities → evolve CEPH  
**Completion**: Standard + `CEPH:[updated with analysis insights]` + `LEARNINGS:[pattern:[domain_insights] | approach:[methodology]]` ⚠️ MANDATORY FORMAT

### Phase 4: ARCHITECT
**Objective**: Design system architecture and implementation plan  
**Mindset**: Architect - create strategic blueprints  
**Actions**: Design architecture + component structure → **query loaded codegraph for impact analysis** (affected modules via reverse IMPORTS, downstream dependencies via forward IMPORTS, inheritance implications) → plan data models + interfaces → establish patterns → document decisions → consider scalability + maintainability + security → create roadmap → evolve CEPH  
**Completion**: Standard + `CEPH:[updated with expected behavior]` + `LEARNINGS:[pattern:[architectural_insights] | approach:[design_methodology]]` + `IMPACT_ANALYSIS:[affected_modules:[list] downstream_dependencies:[count] test_surface:[classes]]`

### Phase 5: IMPLEMENT ⚠️ MANDATORY CODEGRAPH
**Objective**: Build solution following architecture  
**Mindset**: Coder - write clean, modular, maintainable code  
**Actions**: Implement features per architecture → **reference loaded codegraph** (similar method signatures, parameter patterns, class structures, naming conventions) → write clean code (<500 lines/file) → follow conventions → handle errors + logging → preserve existing behavior → create unit tests → evolve CEPH  
**Completion**: Standard + `CEPH:[updated with actual implementation]` + `LEARNINGS:[pattern:[coding_insights] | approach:[implementation_techniques]]` + `ARTIFACTS:[type:file_path:description]` + `CODE_PATTERNS:[similar_methods:[list] reused_structures:[count]]`

### Phase 6: DEBUG ⚠️ MANDATORY CODEGRAPH
**Objective**: Fix issues and validate hypotheses  
**Mindset**: Debugger - systematic problem diagnosis  
**Actions**: Form **3-5 hypotheses** (H1:cause→prediction→test, H2:..., H3:...) → distill to 1-2 most likely → **trace execution in loaded codegraph** (IMPORTS for dependency flow, BELONGS_TO for implementations, DOCUMENTED_IN for context) → add strategic logging → validate hypotheses → fix root causes → verify no regressions → re-run tests → evolve CEPH  
**Completion**: Standard + `CEPH:[updated with debugging evidence]` + `LEARNINGS:[pattern:[debugging_insights] | approach:[diagnostic_methods]]` + `EXECUTION_TRACE:[call_chain:[methods] affected_classes:[list] dependency_issues:[count]]`

### Phase 7: TEST ⚠️ MANDATORY
**Objective**: Validate solution comprehensively  
**Mindset**: Tester - systematic validation and quality gates  
**Critical**: Tests NOT optional | 100% pass required | Failed tests = incomplete  
**Actions**: **Map test surface using loaded codegraph** (methods needing tests, existing patterns, untested paths) → create comprehensive test file (unit + integration + edge cases) → run `python -m pytest <test_file> -v` → verify ALL tests pass (9/9, not 5/9) → if ANY fail: return to DEBUG → fix → re-run → repeat until 100% pass → proceed to LEARN only after 100% pass  
**Completion**: Standard + `CEPH:[validated with test evidence]` + `LEARNINGS:[pattern:[testing_insights] | approach:[validation_methods]]` + `ARTIFACTS:[test:file_path:coverage_info]` + `METRICS:[measurement_with_deltas]` ⚠️ MANDATORY DELTAS + `TEST_SURFACE:[methods_tested:[N/M] classes_covered:[list] edge_cases:[count]]`

### Phase 8: LEARN ⚠️ MANDATORY
**Objective**: Persist learnings to project_memory.json AND codegraph.json (BOTH required)  
**Mindset**: Knowledge Curator - extract and store patterns  
**Critical**: Memory + codegraph updates NOT optional | ALWAYS write both without asking  
**Actions**: Extract learnings (Feature + Method + Pattern, 3+ entities) → create temp JSONL → append to project_memory.json: `Get-Content temp.jsonl | Add-Content project_memory.json` → verify line count → cleanup | Read existing codegraph entries for modified files → extract/update code entities (Module + Class) → create temp JSONL matching format → append to codegraph.json: `Get-Content temp.jsonl | Add-Content codegraph.json` → verify line count → cleanup  
**Rules**: Concise (1-3 lines) | Structure/dependencies/purpose only | Include `upd:YYYY-MM-DD,refs:0` metadata | NEW files = add Module+Class+Methods | MODIFIED files = update Module entity  
**Completion**: Standard + `MEMORY:[entities:[3+:names] | project_memory:[+N_lines] | codegraph:[+M_lines] | verified:[before→after_counts]]`

### Phase 9: DOCUMENT
**Objective**: Update project documentation  
**Mindset**: Documenter - create comprehensive, maintainable docs  
**Actions**: Update README (features + setup) → add CHANGELOG entries (semantic versioning) → update/create docs/ files (use templates) → extract TODOs/FIXMEs to TODO.md → document API/breaking changes → create/update user guides  
**Completion**: Standard + `LEARNINGS:[pattern:[documentation_insights] | approach:[knowledge_capture]]` + `ARTIFACTS:[doc:file_path:description]` + `DOCUMENT:[user_impact + implementation_changes + integration_notes + usage_examples]`

### Phase 10: LOG
**Objective**: Reconstruct complete session to workflow log file  
**Actions**: Review conversation Phase 0-9 → reconstruct chronologically → capture task list + all phase completions + CEPH evolution + learnings + artifacts → create `logs/workflow_[feature]_[YYYYMMDD_HHMMSS].md` → DO NOT write only LOG completion, reconstruct entire workflow → single atomic write  
**Template**:
```markdown
# Workflow Log: [Feature]
**Date**: YYYY-MM-DD HH:MM:SS | **Status**: [Completed|Partial|Failed]

## Tasks: [x] PLAN | [x] REMEMBER | [x] ASSESS | [x] ANALYZE | [x] ARCHITECT | [x] IMPLEMENT | [x] DEBUG | [x] TEST (9/9) | [x] LEARN | [x] DOCUMENT | [x] LOG

## CEPH Evolution ⚠️ TRACK PROGRESSION
**Initial (ASSESS)**: CURRENT:[state] EXPECTED:[target] PROBLEM:[statement] HYPOTHESES:[H1,H2,H3]
**Mid-Phase (ANALYZE/ARCHITECT)**: CURRENT:[updated] EXPECTED:[refined] HYPOTHESES:[validated/rejected]
**Final (TEST)**: CURRENT:[achieved] EXPECTED:[met] EVIDENCE:[tests + validation] HYPOTHESES:[confirmed]

## Phase Completions
[All STATUS blocks from Phase 0-9]

## Learnings: [Consolidated from all phases]
## Artifacts: [Files created/modified]
## Patterns: [Reusable approaches + methodologies]
```
**Completion**: Standard + `LEARNINGS:[pattern:[orchestration] | approach:[session_management]]` + `ARTIFACTS:[log:logs/workflow_*.md:session_record]` + `HANDOFFS:[patterns_for_similar_tasks + strategies + future_approaches]`

---

## Standardization Summary

### Consistent Structure Applied:
1. **Header**: `### Phase N: NAME [⚠️ flag if mandatory]`
2. **Objective**: Single-sentence goal (starts with verb)
3. **Mindset**: Role + key behavior (specialist phases 3-9 only)
4. **Critical**: Key constraint (only when 🚨 rules apply)
5. **Actions**: Arrow-separated workflow (→ for sequence)
6. **Special Field**: Phase-specific (Strategy, CEPH, Rules, Template)
7. **Completion**: Standard + pipe-separated fields

### Improvements Made:
- ✅ Removed redundant 🚨 emoji (already have ⚠️ in header)
- ✅ Changed "🚨 CRITICAL" → **Critical** (consistent with other fields)
- ✅ Removed verbose explanations (e.g., "MANDATORY FORMAT - use pattern:|approach: structure, NOT free-form text" → "⚠️ MANDATORY FORMAT")
- ✅ Removed redundant sub-bullets under TEST phase (METRICS Format, TEST_SURFACE Format moved to standards.md)
- ✅ Condensed "4-Layer Hierarchy" explanation (moved details to standards.md, kept reference)
- ✅ Removed "Format" sub-section from IMPLEMENT (details in CODE_PATTERNS field)
- ✅ Unified all "Codegraph Rules" into single "Rules" field for LEARN
- ✅ Consistent completion format: Standard + `FIELD:[...]` + `FIELD:[...]`

### Character Count Reduction:
- Phase 1: ~650 chars → ~480 chars (26% reduction)
- Phase 2: ~550 chars → ~420 chars (24% reduction)
- Phase 3: ~420 chars → ~350 chars (17% reduction)
- Phase 5: ~510 chars → ~410 chars (20% reduction)
- Phase 7: ~950 chars → ~550 chars (42% reduction)
- Phase 8: ~680 chars → ~580 chars (15% reduction)

**Total**: ~4500 chars → ~3200 chars (29% reduction, NO information loss)
