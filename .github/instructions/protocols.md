---
applyTo: '**'
---

# DevTeam Mode Protocols

## SVP (Self-Verify Protocol)

**Emit at START of EVERY response**:
```
[SVP: ⚡PHASE→[current] | 📚STACK→[depth or none] | ✓TASK→[progress] | 🎯NEXT→[action]]
```

**Variants**:
- **Full** (phase boundaries): `[SVP: ⚡PHASE→💻IMPLEMENT | 📚STACK→none | ✓TASK→5/11 | 🎯NEXT→create_method]`
- **Mini** (quick responses): `[SVP: 🎯NEXT→analyze_impact]`

**Use Mini for**: User questions | Acknowledgments | Errors | Clarifications | Within-phase updates

⚠️ **ENFORCEMENT**: Always emit one variant | Full at phase boundaries | Mini for non-phase responses

## VMP (Vertical Mode Protocol)

**Stack-based interruption management**: Horizontal=11-phase sequential | Vertical=specialist mindset (on-demand) | Max depth: 5

**Variants**:
- **Full** (depth≥2): 5-line block with STACK/MODE/ORIGIN/ACTION
- **Compact** (depth=1): `🔄 VMP PUSH → 🐛 DEBUG (from TEST, blocker:test_failure)`
- **Mini** (user): `🔄 VMP USER (from IMPLEMENT)`

**Auto-Triggers**: Test fail→DEBUG | 2+ failures→ASSESS | Design flaw→ARCHITECT | Anomaly→ANALYZE | User request→[MODE]

**Mode Actions Table**:

| Mode | Actions | Purpose |
|------|---------|---------|
| 🧠 REMEMBER | Query memory→Extract patterns | Retrieve |
| 🔍 ASSESS | Scan docs→Query modules→Update CEPH.CURRENT | Re-evaluate |
| 🔬 ANALYZE | Query IMPORTS/BELONGS_TO→Map flow→Update HYPOTHESES | Deep dive |
| 🏗️ ARCHITECT | Query reverse IMPORTS→Alternatives→Update EXPECTED | Design |
| 💻 IMPLEMENT | Query signatures→Apply style→Create fix | Code |
| 🐛 DEBUG | Query CALLS→3-5 hypotheses→Add logs→Update EVIDENCE | Diagnose |
| 🧪 TEST | Run tests→Verify→Update EVIDENCE | Confirm |

**Operations**: PUSH=preserve+depth+1 | POP=merge+depth-1 | USER=no stack change | CEPH accumulates

**Memory Verification**: `MEMORY:[global_memory:[file_lines:N domains:X] | project_memory:[file_lines:M clusters:Y] | VERIFIED_LOAD:[line_counts_match:YES summaries_complete:YES]]` | No VERIFIED_LOAD → INCOMPLETE

## CEPH (Context Evolution Protocol)

**Structure**: `CEPH:[CURRENT:[state] | EXPECTED:[target] | PROBLEM:[statement] | HYPOTHESES:[H1:cause→prediction→test] | EVIDENCE:[results]]`

**Updates**: CURRENT (ASSESS init, after phases) | EXPECTED (ASSESS init, ARCHITECT refined, TEST validated) | PROBLEM (ASSESS init, rarely) | HYPOTHESES (ANALYZE form, DEBUG 3-5, TEST validate) | EVIDENCE (throughout, TEST final)

**Evolution**: Simple=ASSESS→TEST | Complex=ASSESS→ANALYZE→ARCHITECT→IMPLEMENT→TEST

## CVP (Compliance Verification Protocol)

**Emit at END of EVERY phase** (before STATUS): `[CVP: ✓CHATMODE:[items] | ✓INSTRUCTIONS:[files] | 🚫VIOLATIONS:[none|items]]`

**Purpose**: Self-verify compliance with chatmode + instruction files | Critical violations BLOCK next phase

**Verification Scope**: Chatmode (principles, workflow, protocols, format) | protocols.md (SVP, VMP, CEPH, Memory) | phases.md (requirements, outputs, transitions) | standards.md (templates, quality, format) | structure.md (organization, placement, naming) | examples.md (patterns, anti-patterns, checklists)

**Check by Phase**:

| Phase | Must Have | Common Violations |
|-------|-----------|-------------------|
| PLAN | SVP, TASKS, decomposition | Missing task list |
| REMEMBER | SVP, Memory loaded, VERIFIED_LOAD, file_lines | Fake load, no verification |
| ASSESS | SVP, Codegraph loaded, VERIFIED_LOAD, CEPH init, docs | Partial load, no summary |
| ANALYZE | SVP, CEPH updated, LEARNINGS format, queries | Wrong LEARNINGS format |
| ARCHITECT | SVP, CEPH updated, LEARNINGS, impact analysis | No impact analysis |
| IMPLEMENT | SVP, 3/5 codegraph queries, CEPH, LEARNINGS, structure.md | <3 queries, wrong location |
| DEBUG | SVP, 2/4 codegraph queries, hypotheses, CEPH, LEARNINGS | No hypotheses, no queries |
| TEST | SVP, 100% pass, USER_VERIFICATION, METRICS+deltas, CEPH | Auto-proceed, no deltas, <100% |
| LEARN | SVP, 3+ entities, both files updated, line verification | <3 entities, no verification |
| DOCUMENT | SVP, docs updated, DOCUMENT field, structure.md | Skipped, wrong location |
| LOG | SVP, workflow file created, HANDOFFS, reconstruction | Missing file, incomplete |

**Response Variants**:

✅ **Full**: `[CVP: ✓CHATMODE:[SVP,VMP,Memory,Codegraph,CEPH,Completion] | ✓INSTRUCTIONS:[protocols,phases,standards,structure] | 🚫VIOLATIONS:[none]]`

⚠️ **Partial**: `[CVP: ✓CHATMODE:[SVP,Memory] | ⚠️CHATMODE:[Codegraph:2/5] | ✓INSTRUCTIONS:[protocols,phases] | ⚠️INSTRUCTIONS:[standards:LEARNINGS_format] | 🚫VIOLATIONS:[2:Codegraph_queries,LEARNINGS_format]]`

❌ **Failed**: `[CVP: ❌CHATMODE:[Memory:not_loaded,VMP:missing] | ❌INSTRUCTIONS:[protocols:no_SVP,standards:no_VERIFIED_LOAD] | 🚫VIOLATIONS:[4:Memory_not_loaded,VMP_missing,SVP_not_emitted,VERIFIED_LOAD_missing]]`

**Critical Violations** (MUST fix): No SVP | Memory not loaded (REMEMBER) | Codegraph not loaded (ASSESS) | <100% test pass (TEST) | No USER_VERIFICATION (TEST) | <3 entities (LEARN) | Wrong file placement | Missing VERIFIED_LOAD | Missing METRICS deltas | Wrong LEARNINGS format | <3 queries (IMPLEMENT) | <2 queries (DEBUG)

**Integration**: Complete work → Self-check all 6 files → Emit CVP → If violations: add BLOCKERS, STATUS: partial, fix → Emit completion format

## Completion Format

**Standard** (in order): `[CVP: ...]` → STATUS → PHASE → TASKS → DISCOVERIES → BLOCKERS → NEXT

**Protocol Fields** (when applicable): CVP (MANDATORY every phase) | STACK (VMP depth≥1) | CEPH (ASSESS+) | MEMORY+VERIFIED_LOAD (REMEMBER) | LEARNINGS (specialist) | METRICS+deltas (TEST)

**Compliance**: ✓Actions ✓VMP ✓Fields ✓Queries ✓NEXT ✓SVP ✓CVP | Fail→BLOCKERS+STATUS:partial

**Phase Transitions**: ✓Complete ✓Requirements ✓Stack ✓CEPH ✓SVP ✓CVP

