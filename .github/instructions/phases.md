---
applyTo: '**'
---

# DevTeam Mode: Multi-Phase Workflow

## Phase Transitions

**Before next**: ✓STATUS ✓NEXT ✓CEPH(if exists) ✓LEARNINGS(format)  
**CEPH Triggers**: ASSESS→ANALYZE(+HYPOTHESES) | ARCHITECT(+EXPECTED) | IMPLEMENT(+CURRENT) | TEST(+EVIDENCE) | DEBUG(validate)

## Phases

### 0: PLAN
**Do**: Decompose → identify phases → sequence → manage_todo_list → announce  
**Out**: TASKS:[phases] + DISCOVERIES:[scope+phases+deps]

### 1: REMEMBER ⚠️ MANDATORY
**Do**: Load global(domains+3/domain)+project(clusters+recent10)+report lines → verify → docs → logs  
**Out**: MEMORY:[global:[lines:N domains:X patterns:Y] | project:[lines:M clusters:Z] | docs:[files] | VERIFIED_LOAD:[line_counts:YES summaries:YES hierarchies:YES]]

### 2: ASSESS ⚠️ CODEGRAPH
**Do**: Check env → review docs → **load codegraph ENTIRE** → verify(modules/classes/methods/relations) → query → create CEPH  
**Out**: CEPH:[init] + CODEGRAPH:[loaded:YES summary:[modules:N classes:M methods:P relations:[counts]] | VERIFIED_LOAD:[complete:YES structure:YES]] + REFS:[modules/classes] + DOCS:[files]

### 3: ANALYZE
**Do**: Map arch → query codegraph(BELONGS_TO,IMPORTS,DOCUMENTED_IN) → analyze dataflow/patterns → identify causes/edges → evolve CEPH  
**Out**: CEPH:[updated] + LEARNINGS:[pattern:[X]|approach:[Y]] ⚠️

### 4: ARCHITECT
**Do**: Design → query impact(reverse IMPORTS, deps) → plan models/interfaces → document decisions → scale/maintainability → evolve CEPH  
**Out**: CEPH:[updated] + LEARNINGS:[pattern:[X]|approach:[Y]] + IMPACT:[modules:[list] deps:[N] surface:[classes]]

### 5: IMPLEMENT ⚠️ CODEGRAPH
**Do**: Per architecture → **query codegraph (3/5)** → clean code(<500) → conventions → errors/logging → preserve behavior → tests → evolve CEPH

**Queries (min 3/5)**: ☐ Signatures ☐ IMPORTS ☐ BELONGS_TO ☐ CALLS ☐ Naming  
**Track**: Emit `CODEGRAPH_QUERIES:[N/5]` during work | ⚠️ 3/5 minimum or SCP-PHASE blocks

**Out**: CEPH:[updated] + LEARNINGS:[pattern:[X]|approach:[Y]] + ARTIFACTS:[type:path:desc] + CODE_PATTERNS:[methods:[list] structures:[N]] + CODEGRAPH_QUERIES:[N/5]

### 6: DEBUG ⚠️ CODEGRAPH
**Do**: Form 3-5 hypotheses(H1:cause→pred→test) → distill 1-2 → **trace codegraph (2/4 min)** → logs → validate → fix → verify → rerun → evolve CEPH  
**Track**: Emit `CODEGRAPH_QUERIES:[N/4]` during trace | ⚠️ 2/4 minimum or SCP-PHASE blocks  
**Out**: CEPH:[updated] + LEARNINGS:[pattern:[X]|approach:[Y]] + EXECUTION_TRACE:[chain:[methods] classes:[list] issues:[N]] + CODEGRAPH_QUERIES:[N/4]

### 7: TEST ⚠️ MANDATORY
**Do**: Extract criteria → map surface(codegraph) → coverage → pytest -v → **100% MANDATORY** → IF fail: route(logic→DEBUG | design→ARCHITECT | requirements→ANALYZE) → **CHECKPOINT: Present, verify, 🛑WAIT** → confirm("looks good")→**auto-finalize** LEARN→DOC→LOG | reject→nest  
**Out**: CEPH:[validated] + LEARNINGS:[pattern:[X]|approach:[Y]] + ARTIFACTS:[test:path:coverage] + METRICS:[WITH_Δ] ⚠️ + TEST_SURFACE:[methods:[N/M] classes:[list] edges:[N]] + USER_VERIFICATION:[awaiting:YES] ⚠️

**METRICS** ⚠️: `tests=N/M(+added)|coverage=X%(±Δ)|assertions=Y(+new)|files=Z(+created)` | ✅ `tests=14/14(+14)` | ❌ `tests=14/14` (missing Δ)  
**User Verify**: SCP-PHASE → Present → **BLOCK** → Approve→auto-finalize | Reject→nest

### 8: LEARN ⚠️ MANDATORY
**Do**: Extract 3+ entities(Feature+Method+Pattern) → temp JSONL → append project_memory → verify → cleanup | Update codegraph(Module+Class) → append → verify → cleanup

### 9: DOCUMENT
**Do**: **INCREMENTAL** → Check `logs/.last_document_update.json` → Determine updates → Update affected(README/CHANGELOG/TODO/docs/) → Update tracker → extract TODOs → document API/breaking → guides  
**Logic**: Load tracker → Compare scope → Update TODO if complete | CHANGELOG if user-facing | README if API/arch | docs/ if technical → Record  
**Out**: LEARNINGS:[pattern:[X]|approach:[Y]] + ARTIFACTS:[doc:path:desc] + DOCUMENT:[impact+changes+integration+examples+tracker:YES]

### 10: LOG
**Do**: Review 0-9 → reconstruct chronologically → capture tasks+completions+CEPH+learnings+artifacts → create `logs/workflow_[feature]_[timestamp].md` → **SCP-END** → atomic write  
**Out**: LEARNINGS:[pattern:[X]|approach:[Y]] + ARTIFACTS:[log:logs/workflow_*.md] + HANDOFFS:[patterns+strategies+approaches] + **SCP-END** ⚠️ + COMMIT:"type(scope): desc"

## Memory Ops by Phase

| Phase | Action | Detail | Verification |
|-------|--------|--------|--------------|
| **REMEMBER** | Load | global(domains+3)+project(clusters+10)+docs+logs | file_lines |
| **ASSESS** 🔑 | Load | codegraph ENTIRE+docs | modules/classes/methods/relations |
| **ANALYZE** | Query | IMPORTS/BELONGS_TO/DOCUMENTED_IN | Results |
| **ARCHITECT** | Impact | Reverse IMPORTS, deps | Entities |
| **IMPLEMENT** ⚠️ | Ref | Signatures/patterns/structures(3/5) | CODE_PATTERNS |
| **DEBUG** ⚠️ | Trace | CALLS chains, implementations | EXECUTION_TRACE |
| **TEST** ⚠️ | Map+Verify | Methods/gaps, **user verify** | SURFACE+USER_VERIFICATION |
| **LEARN** ⚠️ | Persist | 3+ entities → temp/direct → append → verify | Line counts Δ |
| **LOG** | Reconstruct | workflow_*.md | N/A |

**Codegraph**: Load ASSESS(2) → available through LEARN(8) | **Mandatory**: IMPLEMENT(3/5), DEBUG(2/4), LEARN(update) | **Recommended**: ANALYZE, ARCHITECT, TEST

## Workflow Adaptability

**Universal NWP**: Same 11 phases, adaptively selected per workflow_index and trigger

**Root (index=0)**: 4-11 phases | **ALWAYS**: PLAN→TEST→LEARN→LOG  
**Nested (index>0)**: 3-11 phases | **ALWAYS**: TEST+LEARN | **Optional**: DOCUMENT

**By Trigger**: test_failure=[1,2,6,7,8] | design_flaw=[1,2,3,4,5,7,8,9] | user_question=[2,answer,8] | blocker=[2,3,7,8] | repeated_failure=[1,2,3,6,7,8]

**MANDATORY**: Root(PLAN,TEST,LEARN,LOG) | Nested(TEST,LEARN) | All(workflow_index tracking)  
**SKIP**: Nested(PLAN,LOG) | Any(unneeded phases)

## Phase Completion Format

```
[SCP-PHASE: ✓CHATMODE:[items] | ✓INSTRUCTIONS:[files] | 🚫VIOLATIONS:[none] | 🔧ADJUST:[none] | 📚NWP:[index:N,phase:X/Y]]
STATUS: complete | PHASE: X/Y NAME | WORKFLOW: index=N, depth=M
TASKS: progress | STACK: [chain] (if nested) | DISCOVERIES: ... | BLOCKERS: ... | NEXT: ...
```


