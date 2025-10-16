---
applyTo: '**'
---

# DevTeam Mode: 11-Phase Workflow

## Phase Transition Checklist

**Before next phase**: ✓STATUS ✓NEXT specified ✓CEPH updated (if exists) ✓LEARNINGS format correct

**CEPH Triggers**: ASSESS→ANALYZE(+HYPOTHESES) | ARCHITECT(+EXPECTED) | IMPLEMENT(+CURRENT) | TEST(+EVIDENCE) | DEBUG(validate HYPOTHESES)

## Phase Definitions

### Phase 0: PLAN
**⚠️ SVP**: `[SVP: ⚡PHASE→📋PLAN | 📚STACK→none | ✓TASK→0/11 | 🎯NEXT→decompose]`  
**Do**: Decompose → identify phases → sequence → manage_todo_list → announce  
**Out**: Standard + `TASKS:[phases]` + `DISCOVERIES:[scope+phases+deps]`

### Phase 1: REMEMBER ⚠️ MANDATORY
**⚠️ SVP**: `[SVP: ⚡PHASE→🧠REMEMBER | 📚STACK→... | ✓TASK→1/11 | 🎯NEXT→load_global]`  
**Do**: Load global (domains+3/domain) + project (clusters+recent 10) + report `file_lines` + verify → docs (README, CHANGELOG, TODO) → logs  
**Out**: Standard + `MEMORY:[global:[file_lines:N domains:X patterns:Y] | project:[file_lines:M clusters:Z] | docs:[files] | VERIFIED_LOAD:[line_counts_reported:YES summaries_complete:YES hierarchies_valid:YES]]`

### Phase 2: ASSESS ⚠️ CODEGRAPH LOAD
**⚠️ SVP**: `[SVP: ⚡PHASE→🔍ASSESS | 📚STACK→... | ✓TASK→2/11 | 🎯NEXT→check_env]`  
**Do**: Check env → review docs (README, CHANGELOG, standards.md, structure.md) → **load codegraph ENTIRE file** → verify (modules/classes/methods/relations) → query modules → create CEPH  
**Out**: Standard + `CEPH:[init]` + `CODEGRAPH:[loaded:YES summary:[modules:N classes:M methods:P relations:[counts]] | VERIFIED_LOAD:[codegraph_complete:YES structure_valid:YES]]` + `CODEGRAPH_REFS:[modules/classes]` + `DOCS_REVIEWED:[files]`

### Phase 3: ANALYZE
**⚠️ SVP**: See protocols.md for format | Example: `[SVP: ⚡PHASE→🔬ANALYZE | 📚STACK→... | ✓TASK→3/11 | 🎯NEXT→map_arch]`  
**Do**: Map architecture → query codegraph (BELONGS_TO, IMPORTS, DOCUMENTED_IN) → analyze dataflow/patterns → identify causes/edges → evolve CEPH  
**Out**: Standard + `CEPH:[updated]` + `LEARNINGS:[pattern:[X]|approach:[Y]]` ⚠️ MANDATORY

### Phase 4: ARCHITECT
**⚠️ SVP**: See protocols.md for format | Example: `[SVP: ⚡PHASE→🏗️ARCHITECT | 📚STACK→... | ✓TASK→4/11 | 🎯NEXT→design]`  
**Do**: Design architecture → query impact (reverse IMPORTS, dependencies) → plan models/interfaces → document decisions → consider scale/maintainability → evolve CEPH  
**Out**: Standard + `CEPH:[updated]` + `LEARNINGS:[pattern:[X]|approach:[Y]]` + `IMPACT_ANALYSIS:[modules:[list] deps:[N] surface:[classes]]`

### Phase 5: IMPLEMENT ⚠️ MANDATORY CODEGRAPH
**⚠️ SVP**: See protocols.md for format | Example: `[SVP: ⚡PHASE→💻IMPLEMENT | 📚STACK→... | ✓TASK→5/11 | 🎯NEXT→query_patterns]`  
**Do**: Implement per architecture → **query codegraph (3 of 5)** → write clean code (<500 lines) → follow conventions → errors/logging → preserve behavior → create tests → evolve CEPH

**Codegraph Queries (min 3 of 5)**:
☐ Similar signatures ☐ Trace IMPORTS ☐ Check BELONGS_TO ☐ Review CALLS ☐ Validate naming

**Out**: Standard + `CEPH:[updated]` + `LEARNINGS:[pattern:[X]|approach:[Y]]` + `ARTIFACTS:[type:path:desc]` + `CODE_PATTERNS:[methods:[list] structures:[N]]`

### Phase 6: DEBUG ⚠️ MANDATORY CODEGRAPH
### Phase 6: DEBUG ⚠️ MANDATORY CODEGRAPH
**⚠️ SVP**: See protocols.md for format | Example: `[SVP: ⚡PHASE→🐛DEBUG | 📚STACK→... | ✓TASK→6/11 | 🎯NEXT→hypotheses]`  
**Do**: Form 3-5 hypotheses (H1:cause→prediction→test) → distill to 1-2 → trace in codegraph (IMPORTS, BELONGS_TO, DOCUMENTED_IN) → add logs → validate → fix → verify → rerun → evolve CEPH  
**Out**: Standard + `CEPH:[updated]` + `LEARNINGS:[pattern:[X]|approach:[Y]]` + `EXECUTION_TRACE:[chain:[methods] classes:[list] issues:[N]]`

### Phase 7: TEST ⚠️ MANDATORY
**⚠️ SVP**: See protocols.md for format | Example: `[SVP: ⚡PHASE→🧪TEST | 📚STACK→... | ✓TASK→7/11 | 🎯NEXT→run_tests]`  
**Do**: Extract acceptance criteria → map surface via codegraph → create coverage → run pytest -v → **100% pass MANDATORY** → IF fail: route (logic→DEBUG | design→ARCHITECT | requirements→ANALYZE) → **CHECKPOINT: Present results, request verify, 🛑 WAIT** → IF confirm: LEARN | IF reject: fix  
**Out**: Standard + `CEPH:[validated]` + `LEARNINGS:[pattern:[X]|approach:[Y]]` + `ARTIFACTS:[test:path:coverage]` + `METRICS:[WITH_DELTAS]` ⚠️ + `TEST_SURFACE:[methods:[N/M] classes:[list] edges:[N]]` + `USER_VERIFICATION:[presented+awaiting_confirmation:YES]` ⚠️

### Phase 8: LEARN ⚠️ MANDATORY
**⚠️ SVP**: See protocols.md for format | Example: `[SVP: ⚡PHASE→🎓LEARN | 📚STACK→... | ✓TASK→8/11 | 🎯NEXT→extract]`  
**Do**: Extract 3+ entities (Feature+Method+Pattern) → create temp JSONL → append project_memory.json → verify count → cleanup | Update codegraph (Module+Class) → append → verify → cleanup

### Phase 9: DOCUMENT
**⚠️ SVP**: See protocols.md for format | Example: `[SVP: ⚡PHASE→📚DOCUMENT | 📚STACK→... | ✓TASK→9/11 | 🎯NEXT→update]`  
**Do**: **INCREMENTAL UPDATE WORKFLOW** → Check `logs/.last_document_update.json` → Determine which docs need updates based on changes → Update only affected docs (README/CHANGELOG/TODO/docs/) → Update tracker with new timestamps → extract TODOs → document API/breaking changes → user guides  
**Incremental Logic**: Load tracker → Compare current feature scope vs last update → Update TODO if new completion → Update CHANGELOG if user-facing → Update README if API/architecture change → Update docs/ if technical specs changed → Record updates in tracker  
**Out**: Standard + `LEARNINGS:[pattern:[X]|approach:[Y]]` + `ARTIFACTS:[doc:path:desc]` + `DOCUMENT:[impact+changes+integration+examples+tracker_updated:YES]`

### Phase 10: LOG
**⚠️ SVP**: See protocols.md for format | Example: `[SVP: ⚡PHASE→📝LOG | 📚STACK→... | ✓TASK→10/11 | 🎯NEXT→reconstruct]`  
**Do**: Review Phase 0-9 → reconstruct chronologically → capture tasks+completions+CEPH+learnings+artifacts → create `logs/workflow_[feature]_[YYYYMMDD_HHMMSS].md` → **emit SCP-END** → single atomic write  
**Out**: Standard + `LEARNINGS:[pattern:[X]|approach:[Y]]` + `ARTIFACTS:[log:logs/workflow_*.md]` + `HANDOFFS:[patterns+strategies+approaches]` + **SCP-END** (MANDATORY)

## Memory Operations by Phase

| Phase | Action | Detail | Verification |
|-------|--------|--------|--------------|
| **REMEMBER (1)** | Load | global(domains+3/domain)+project(clusters+recent10)+docs+logs | file_lines reported |
| **ASSESS (2)** 🔑 | Load | codegraph ENTIRE+docs | modules/classes/methods/relations |
| **ANALYZE (3)** | Query | IMPORTS/BELONGS_TO/DOCUMENTED_IN | Results confirmed |
| **ARCHITECT (4)** | Impact | Reverse IMPORTS, deps | Entities referenced |
| **IMPLEMENT (5)** ⚠️ | Reference | Signatures/patterns/structures (3 of 5) | CODE_PATTERNS listed |
| **DEBUG (6)** ⚠️ | Trace | CALLS chains, implementations | EXECUTION_TRACE shown |
| **TEST (7)** ⚠️ | Map+Verify | Methods/gaps, **user verify** | TEST_SURFACE+USER_VERIFICATION |
| **LEARN (8)** ⚠️ | Persist | 3+ entities → temp/direct → append → verify | Line counts before→after |
| **LOG (10)** | Reconstruct | Create logs/workflow_*.md | N/A |

**Codegraph**: Load ASSESS(2) → available through LEARN(8) | **Mandatory**: IMPLEMENT(3 of 5), DEBUG(2 of 4), LEARN(update) | **Recommended**: ANALYZE, ARCHITECT, TEST

## Workflow Adaptability

- **Simple** (no CEPH, optional REMEMBER): PLAN + IMPLEMENT + TEST + LEARN
- **Medium** (CEPH from ASSESS): PLAN + REMEMBER + ASSESS + IMPLEMENT + TEST + LEARN
- **Complex** (full workflow): All 11 phases with CEPH evolution

**Skip Rules**: ANALYZE/ARCHITECT=optional for simple | REMEMBER=optional if no memory | DOCUMENT=optional if no user changes | CEPH=optional for trivial
