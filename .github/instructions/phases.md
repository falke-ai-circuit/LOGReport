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
**Global Memory**: Abstract patterns/concepts distilled from project memory (cross-project reusable knowledge) | **Location**: `.github/global_memory.json` | **Content**: Universal patterns, architectural concepts, reusable approaches  
**Project Memory**: Project-specific entities/implementations | **Location**: `project_memory.json` (root) | **Content**: Concrete classes, methods, features, tests  
**Out**: MEMORY:[global:[lines:N domains:X patterns:Y] | project:[lines:M clusters:Z] | docs:[files] | VERIFIED_LOAD:[line_counts:YES summaries:YES hierarchies:YES]]  
**VERIFIED_LOAD**: Must include read_file() calls (not claims without tools) | Components: line_counts(global:N,project:M) + summaries(domains:X) + hierarchies(clusters:Y) | False positive→HALT
**Failures**: missing→create empty+VIOLATIONS:[memory_missing→created_empty] | corrupted→repair script+VIOLATIONS:[corrupted_LX-Y→repaired] | oversized(>5000)→auto-optimizer+VIOLATIONS:[oversized_N→condensed_M] | timeout→retry+chunk(500)+VIOLATIONS:[timeout→chunked] | parse→skip+VIOLATIONS:[parse_failed]

### 2: ASSESS ⚠️ CODEGRAPH
**Do**: Check env → review docs → **load codegraph ENTIRE** → verify(modules/classes/methods/relations) → query → create CEPH | **Subagent**: If scope uncertain or multi-iteration research needed → invoke Plan/DevTeam/custom agent(detailed prompt→output format→research intent) → integrate findings | **Custom agents**: Create `.agent.md` in `.github/agents/` for specialized personas (e.g., code reviewer, planner) → LM auto-selects based on description  
**Out**: CEPH:[init] + CODEGRAPH:[loaded:YES summary:[modules:N classes:M methods:P relations:[counts]] | VERIFIED_LOAD:[complete:YES structure:YES]] + REFS:[modules/classes] + DOCS:[files]  
**Failures**: missing→create empty+VIOLATIONS:[codegraph_missing→created_empty] | corrupted→repair+VIOLATIONS:[corrupted→repaired] | empty(entities:0)→valid+DISCOVERIES:[codegraph_empty:rebuild_needed] | query=0→valid+DISCOVERIES:[query_X_returned_0],continue | timeout(>10s)→retry+VIOLATIONS:[timeout→retry],HALT if persists | count mismatch→HALT,investigate

### 3: ANALYZE
**Do**: Map arch → query codegraph(BELONGS_TO,IMPORTS,DOCUMENTED_IN) → analyze dataflow/patterns → identify causes/edges → evolve CEPH | **Subagent**: For exploration/unknown patterns → invoke Plan/custom agent(search across files→return findings) → feed to CEPH | LM may auto-select custom agent if matching description  
**Out**: CEPH:[updated] + LEARNINGS:[pattern:[X]|approach:[Y]] ⚠️

### 4: ARCHITECT
**Do**: Design → query impact(reverse IMPORTS, deps) → plan models/interfaces → document decisions → scale/maintainability → evolve CEPH  
**Out**: CEPH:[updated] + LEARNINGS:[pattern:[X]|approach:[Y]] + IMPACT:[modules:[list] deps:[N] surface:[classes]]

### 5: IMPLEMENT ⚠️ CODEGRAPH
**Do**: Per architecture → **query codegraph (3/5)** → clean code(<500) → conventions → errors/logging → preserve behavior → tests → evolve CEPH

**Queries (min 3/5)**: ☐ Signatures ☐ IMPORTS ☐ BELONGS_TO ☐ CALLS ☐ Naming  
**Track**: Emit `CODEGRAPH_QUERIES:[N/5]` during work | ⚠️ 3/5 minimum or SCP-PHASE blocks
**Pre-Implementation (BLOCKING)**: ☐ REMEMBER ☐ ASSESS ☐ PLAN ☐ Queries(3/5) → Unchecked → BLOCK edit_file

**Out**: CEPH:[updated] + LEARNINGS:[pattern:[X]|approach:[Y]] + ARTIFACTS:[type:path:desc] + CODE_PATTERNS:[methods:[list] structures:[N]] + CODEGRAPH_QUERIES:[N/5]

### 6: DEBUG ⚠️ CODEGRAPH
**Do**: Form 3-5 hypotheses(H1:cause→pred→test) → distill 1-2 → **trace codegraph (2/4 min)** → logs → validate → fix → verify → rerun → evolve CEPH | **Subagent**: For complex traces/uncertain root cause → invoke DevTeam agent(autonomous investigation→return chain) → test hypotheses  
**Track**: Emit `CODEGRAPH_QUERIES:[N/4]` during trace | ⚠️ 2/4 minimum or SCP-PHASE blocks  
**Queries (min 2/4)**: ☐ CALLS chains ☐ IMPORTS dependencies ☐ Class implementations ☐ Method signatures  
**Out**: CEPH:[updated] + LEARNINGS:[pattern:[X]|approach:[Y]] + EXECUTION_TRACE:[chain:[methods] classes:[list] issues:[N]] + CODEGRAPH_QUERIES:[N/4]

### 7: TEST ⚠️ MANDATORY
**Do**: Extract criteria → map surface(codegraph) → coverage → pytest -v → **100% MANDATORY** → IF fail: **NEST→classify→phase** (NO inline fixes) → **🛑 CHECKPOINT: Present, emit USER_VERIFICATION:[awaiting:YES], BLOCKING:[LEARN,DOCUMENT,LOG], END RESPONSE** → **Wait** → confirm("looks good")→**auto-finalize** LEARN→DOC→LOG | reject("issue")→NEST→DEBUG
**Out**: CEPH:[validated] + LEARNINGS:[pattern:[X]|approach:[Y]] + ARTIFACTS:[test:path:coverage] + METRICS:[WITH_Δ] ⚠️ + TEST_SURFACE:[methods:[N/M] classes:[list] edges:[N]] + USER_VERIFICATION:[awaiting:YES] ⚠️

**METRICS** ⚠️: `tests=N/M(+added)|coverage=X%(±Δ)|assertions=Y(+new)|files=Z(+created)` | ✅ `tests=14/14(+14)` | ❌ `tests=14/14` (missing Δ)  
**User Verify**: SCP-PHASE → Present → **BLOCK** → Approve→auto-finalize | Reject→NEST | No response(10 exchanges)→prompt
**Failure Classification**: exception/crash/wrong_behavior→DEBUG | architecture_limit→ARCHITECT | spec_misunderstanding→ANALYZE | tool/env_issue→skip+TODO+continue

### 8: LEARN ⚠️ MANDATORY
**Do**: Extract 3+ entities(Feature+Method+Pattern) → temp JSONL → append project_memory → verify count Δ → cleanup | Update codegraph(Module+Class) → append → verify → cleanup | **Global Memory**: Distill universal patterns from project learnings for cross-project reuse (updated in update_memory workflow)
**Minimum (BLOCKING)**: <3 entities → BLOCK finalization → VIOLATIONS:[learn_minimum_not_met:N<3]

### 9: DOCUMENT
**Do**: **INCREMENTAL** → Check `logs/.last_document_update.json` → Determine updates → Update affected(README/CHANGELOG/TODO/docs/) → Update tracker → extract TODOs → document API/breaking → guides  
**Logic**: Load tracker → Compare scope → Update TODO if complete | CHANGELOG if user-facing | README if API/arch | docs/ if technical → Record  
**Out**: LEARNINGS:[pattern:[X]|approach:[Y]] + ARTIFACTS:[doc:path:desc] + DOCUMENT:[impact+changes+integration+examples+tracker:YES]

### 10: LOG
**Do**: Review 0-9 → **AUTO-ANALYZE**(scan [SCP-*]→count violations/nests→calculate scores→extract learnings→generate TUNE+INSIGHTS) → reconstruct chronologically → capture tasks+completions+CEPH+learnings+artifacts+analysis → create `logs/workflow_[feature]_[timestamp].md` → **SCP-END** → atomic write  
**Mandatory (Root)**: Root workflow (index=0) MUST include LOG after LEARN | Nested workflows skip LOG → Missing LOG in root→HALT+VIOLATIONS:[log_phase_missing:mandatory_in_root]
**Analysis**: Compliance(protocols followed?)+Quality(tests/docs/memory/queries)+Process(efficiency/nesting/blockers)+Tune(instruction improvements)+Insights(technical+process learnings)
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

**By Trigger**: test_failure=[1,2,6,7,8] | design_flaw=[1,2,3,4,5,7,8,9] | user_question=[2,answer,8]|subagent(research) | blocker=[2,3,7,8] | repeated_failure=[1,2,3,6,7,8]

**MANDATORY**: Root(PLAN,TEST,LEARN,LOG) | Nested(TEST,LEARN) | All(workflow_index tracking)  
**SKIP**: Nested(PLAN,LOG) | Any(unneeded phases)

## Phase Completion Format

```
[SCP-PHASE: ✓CHATMODE:[items] | ✓INSTRUCTIONS:[files] | 🚫VIOLATIONS:[none] | 🔧ADJUST:[none] | 📚NWP:[index:N,phase:X/Y]]
STATUS: complete | PHASE: X/Y NAME | WORKFLOW: index=N, depth=M
TASKS: progress | STACK: [chain] (if nested) | DISCOVERIES: ... | BLOCKERS: ... | NEXT: ...
```


