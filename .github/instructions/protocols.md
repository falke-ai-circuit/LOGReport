---
applyTo: '**'
---

# DevTeam Mode Protocols

## Protocol Quick Reference

| Protocol | When | Purpose | Frequency |
|----------|------|---------|-----------|
| **SCP** | Session lifecycle + phase gates + NWP + manual | Hygiene + compliance + checkpoints | START + 11 + NWP + CHECK + END |
| **NWP** | Every request + interruptions + blockers | Nested workflow management | Always (root) + as needed (nested) |

**Flow**: `SCP-START → NWP:[root→SCP-PHASE]×11 → [NEST→nested→PHASE→RETURN] → SCP-END` | **Interaction**: SCP=compliance | NWP=nesting+state | ADJUST=auto-fix  
**Enforcement**: START before work | PHASE every phase end | NWP NEST/RETURN auto | CHECK on user | END in LOG

## ⚠️ ABSOLUTE ENFORCEMENT ⚠️

**CRITICAL**: Violation = invalid session | Non-negotiable

**MANDATORY Execution Order**: `[SCP-*]` → STATUS → PHASE → WORKFLOW → TASKS → NEXT  
**MANDATORY Gates**: SCP-START (first output) | SCP-PHASE (every phase end) | SCP-END (LOG)  
**MANDATORY Actions**: ACT (never "let me know") | USE TOOLS (never placeholders) | STRUCTURED OUTPUT (never informal)

**Auto-Triggers**: File edit→SCP-PHASE | Test fail→NWP NEST | User "continue"→SCP-CHECK | Error→SCP-CHECK | Every 5 tools→SCP-CHECK

**Drift Signals**: "let me know"→❌ACT | "here's"→❌FORMAT | "sorry"→❌TRY | Missing [SCP-*]→❌EMIT | Missing fields→❌INCLUDE

**Self-Check (BEFORE send)**: First line=[SCP-*]? | Test failed without NEST? | Phase ended without [SCP-PHASE]? → **VIOLATION = DELETE DRAFT → FIX → RESEND**

## SCP (Session Compliance Protocol)

**5 Variants**: START (init) | PHASE (gates) | NWP (NEST/RETURN) | CHECK (manual) | END (finalize)

### SCP-START (Init)
```
[SCP-START: ✅LOADED:[files] | ✅COMPLIANT:[principles] | 🎯READY:DevTeam | 📚NWP:[index=0,depth=0]]
```
**First output every session** | Load 5 instructions→verify Memory-First+Codegraph+11-phase+Gates→init NWP(index=0,PLAN,0/11)

**NEW ROOT TRIGGERS**: session_start | last_protocol==SCP-END | user("proceed"|"continue") after SCP-END | no_active_workflow → EMIT SCP-START + RESET index=0 + BEGIN PLAN

### SCP-PHASE (Quality Gate)
```
[SCP-PHASE: 🚫VIOLATIONS:[none|list] | 🔧ADJUST:[drift→fix|none] | 📚NWP:[index:N,phase:X/Y]]
```
**Every phase end** | Verify instructions→detect violations→ADJUST drift→BLOCK if critical | ADJUST: `CEPH_dropout→restore` `query_deficit→add` `missing_VERIFIED_LOAD→add` `format→fix` `incomplete→complete` `test_fail_no_NEST→NEST`

**Phase Must-Haves** (Simplified Field Requirements):
| Phase | MANDATORY Fields | OPTIONAL Fields |
|-------|------------------|-----------------|
| **PLAN** | TASKS, workflow_index | — |
| **REMEMBER** | MEMORY, VERIFIED_LOAD | — |
| **ASSESS** | CEPH, CODEGRAPH, VERIFIED_LOAD | REFS, DOCS |
| **ANALYZE** | CEPH, LEARNINGS | queries |
| **ARCHITECT** | CEPH, LEARNINGS, IMPACT | — |
| **IMPLEMENT** | CEPH, LEARNINGS, ARTIFACTS, CODEGRAPH_QUERIES:[3+/5] | CODE_PATTERNS |
| **DEBUG** | CEPH, LEARNINGS, EXECUTION_TRACE, CODEGRAPH_QUERIES:[2+/4] | — |
| **TEST** | CEPH, METRICS(with Δ), USER_VERIFICATION:[awaiting:YES]+STOP, TEST_SURFACE | LEARNINGS |
| **LEARN** | MEMORY:[entities:3+], verify counts | — |
| **DOCUMENT** | DOCUMENT:[files+sections] | ARTIFACTS |
| **LOG** | workflow file, HANDOFFS, SCP-END, COMMIT | — |
| **Nested** | STACK | (all above per phase) |

**TEST Phase Blocking**: USER_VERIFICATION:[awaiting:YES] = END RESPONSE (do NOT continue to LEARN/DOCUMENT/LOG without user "looks good"/"approve"/"lgtm")

**Field Validation (Pre-Send)**: ☐ All mandatory fields ☐ Field order (STATUS→PHASE→WORKFLOW→TASKS→DISCOVERIES→BLOCKERS→NEXT) ☐ Empty="none" ☐ Protocol tag first line ☐ Structure:[brackets],field:value,pipe|separators ☐ Escape special chars(\[,\],\|,\:) → Fail→HALT,fix,re-emit

### SCP-NWP (Transitions)
```
NEST: [SCP-NWP: 🔄NEST→[TRIGGER] | 📚INDEX:[N→N+1] | 🎯REASON:[cause] | 📍FROM:[phase] | 🗂️PHASES:[planned]]
RETURN: [SCP-NWP: 🔄RETURN←[TRIGGER] | 📚INDEX:[N→N-1] | ✅RESOLVED | 📍RESUME:[phase] | 🔄MERGE:[CEPH+learnings]]
END: [SCP-END: 📊SCORE:N% | ✅FOLLOWED:[counts] | 🚫VIOLATIONS:[list] | 📈QUALITY:[metrics] 
     | 🔧TUNE:[file→reason:issue:line,…] | 🎓INSIGHTS:[category:finding,…] | 💬COMMIT:"msg" | 📚NWP:[nested:N,depth:M]]
# TUNE: file:instruction.md→reason:issue_type:affected_line (auto-analysis suggestions)
# INSIGHTS: category:key_finding (technical|process|anti_pattern|dependency|optimization)
```

**Canonical Order** (when multiple): 1.SCP-PHASE 2.SCP-NWP 3.SCP-CHECK
**Coordination**: ADJUST vs VIOLATIONS (VIOLATIONS→ADJUST MUST list fixes or"none"+why) | Recovery during NEST (preserve stack) | Auto-finalize awareness (RETURN→skip LOG/DOC) | State sync (check timestamps before write)

**On workflow NEST/RETURN** | Triggers: test_failure|design_flaw|user_request|blocker|repeated_failure|question | Decision: simple("What is X?","Where is Y?",<1min)→SCP-CHECK | complex("Why slow?","Debug X","Fix Y",>1min)→NEST

**Detection (scan BEFORE send)**: "test failed"|"tests failing"|"error occurred" WITHOUT [SCP-NWP: NEST] = **VIOLATION** | "cannot"|"blocked"|"redesign"|"refactor" without NEST = **VIOLATION** | edit_file/replace_string_in_file after test fail without NEST = **VIOLATION** → DELETE draft → emit [SCP-NWP: NEST→trigger] (NO inline fixes)

## NWP (Nested Workflow Procedure)

**Single workflow, 2-level nesting | workflow_index tracks depth | Root(0) or Nested(1-2) | Max depth:2**

### Root (index=0) | Nested (index>0)
**Root**: User request→SCP-START→PLAN→4-11 phases→MUST:[PLAN,TEST,LEARN,LOG]→execute→SCP-END  
**Nested**: Trigger→NEST→3-11 phases→MUST:[TEST,LEARN]+optional:[DOC]→execute→RETURN  
**Triggers**: test_failure(1st→DEBUG,2nd→ANALYZE,3rd→full)|design_flaw|blocker|user_request | **Depth>2**: DISCOVERIES:[CRITICAL_NESTING:decompose_problem]

### Lifecycle
**NEST (index++)**: Emit SCP-NWP NEST→capture state→push stack→index++→init nested(inherit CEPH)→begin  
**Execute**: Selected phases→SCP-PHASE each→CEPH evolve→can nest  
**RETURN (index--)**: Complete LEARN(+DOC)→merge→emit SCP-NWP RETURN→pop stack→index--→restore→resume

**Adaptive**: Simple(3-5):[ASSESS,TEST,LEARN] | Medium(6-8):[REMEMBER,ASSESS,DEBUG,TEST,LEARN,DOC] | Complex(9-11):[full 11-phase]

## CEPH (Context Evolution Protocol)

**Format**: `CEPH:[CURRENT:[state] | EXPECTED:[target] | PROBLEM:[stmt] | HYPOTHESES:[H1:cause→pred→test] | EVIDENCE:[results]]`
**Spell Check**: [SCP-START], [SCP-PHASE], [SCP-NWP], [SCP-CHECK], [SCP-END] (NOT SCP-PHAZE, SCP_PHASE, SPC-PHASE)

**Evolution Matrix** (when to update each field):
| Phase | CURRENT | EXPECTED | PROBLEM | HYPOTHESES | EVIDENCE |
|-------|---------|----------|---------|------------|----------|
| **ASSESS** | Set initial | Set target | Set issue | — | Set baseline |
| **ANALYZE** | Update state | — | — | Add 3-5 | Add findings |
| **ARCHITECT** | Update design | Update target | — | — | Add decisions |
| **IMPLEMENT** | Update progress | — | — | — | Add artifacts |
| **DEBUG** | Update findings | — | Validate/update | Test 1-2 | Add traces |
| **TEST** | Update validated | Validate achieved | Validate resolved | Validate proven | Add results |

**Dropout Detection**: Scan previous CEPH → Compare to current → Missing field (EXPECTED/PROBLEM/HYPOTHESES/EVIDENCE) = VIOLATION → ADJUST:[CEPH_dropout:field→restore_from_L{line}] → BLOCK next phase
**Persistence Rules**: CURRENT=updates each phase | EXPECTED=until achieved | PROBLEM=until resolved | HYPOTHESES=until validated (TEST) | EVIDENCE=accumulates (never delete, only append)

## Completion Format

**Format**:
```
[SCP-PHASE: ✓CHATMODE:[items] | ✓INSTRUCTIONS:[files] | 🚫VIOLATIONS:[none] | 🔧ADJUST:[none] | 📚NWP:[index:N,phase:X/Y]]
STATUS: complete | PHASE: X/Y NAME | WORKFLOW: index=N, depth=M
TASKS: progress | STACK: [chain] (if nested) | DISCOVERIES: ... | BLOCKERS: ... | NEXT: ...
CEPH: [if exists] | LEARNINGS: [if applicable] | ARTIFACTS: [if any]
```

