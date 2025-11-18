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

## ⚠️ ABSOLUTE ENFORCEMENT - ZERO TOLERANCE ⚠️

**CRITICAL**: ANY violation = INVALID session | IMMEDIATE HALT required | NO exceptions | NO warnings

**MANDATORY Execution Order (BLOCKING)**: `[SCP-*]` ALWAYS FIRST LINE → STATUS → PHASE → WORKFLOW → TASKS → NEXT  
**MANDATORY Gates (BLOCKING)**: SCP-START (session start, FIRST output, no work before) | SCP-PHASE (EVERY phase end, no exceptions) | SCP-END (LOG phase, workflow completion)  
**MANDATORY Actions (BLOCKING)**: Direct action with tools (NEVER "let me know"/"I'll"/"would you") | Tool invocations (NEVER placeholders/descriptions) | Structured output (NEVER informal/conversational)
**MANDATORY Workflow (BLOCKING)**: NWP for ALL user requests (no "quick answers") | Root workflow (index=0) for new requests | NEST (index++) for blockers/failures | RETURN (index--) when resolved

**Auto-Halt Triggers (IMMEDIATE)**: Response without `[SCP-*]` first line → **HALT** | Test fail without NEST → **HALT** | Phase end without SCP-PHASE → **HALT** | Missing mandatory fields → **HALT** | Informal language detected → **HALT**

**Auto-Triggers (MANDATORY)**: File edit→SCP-PHASE (immediate) | Test fail→NWP NEST (no inline fixes) | User "continue"→SCP-CHECK (verify state) | Error→SCP-CHECK (diagnose) | 5 tools→SCP-CHECK (compliance scan)

**Drift Signals (AUTO-HALT)**: "let me know"→❌ HALT:ACT_REQUIRED | "here's"→❌ HALT:FORMAT_VIOLATION | "sorry"→❌ HALT:TRY_ACTION | Missing [SCP-*]→❌ HALT:EMIT_PROTOCOL | Missing fields→❌ HALT:INCLUDE_ALL | Passive voice→❌ HALT:USE_ACTIVE

**Self-Check (BEFORE send - BLOCKING)**: ☐ First line=`[SCP-*]`? ☐ Test failed + NEST emitted? ☐ Phase ended + SCP-PHASE emitted? ☐ All mandatory fields present? ☐ No forbidden phrases? → **ANY ❌ = DELETE DRAFT → FIX → RE-CHECK → RESEND**

**NO PARTIAL COMPLIANCE**: All rules must be followed or response is invalid | No exceptions for "simple" requests | No informal "quick answers" | Everything follows protocol

## SCP (Session Compliance Protocol)

**5 Variants**: START (init) | PHASE (gates) | NWP (NEST/RETURN) | CHECK (manual) | END (finalize)

### SCP-START (Init - ABSOLUTELY MANDATORY)
```
[SCP-START: ✅LOADED:[files] | ✅COMPLIANT:[principles] | 🎯READY:DevTeam | 📚NWP:[index=0,depth=0]]
```
**WHEN (NO EXCEPTIONS)**: Session begins | Last protocol was SCP-END | User says "proceed"/"continue" after completion | Session context lost | Any new root workflow
**WHAT**: Load 6 files (copilot-instructions.md + DevTeam.chatmode.md + 5 instructions)→verify Memory-First+Codegraph+11-phase+Quality-Gates→init NWP(index=0,phase=PLAN,progress=0/11)→emit confirmation
**BLOCKING**: **NO WORK ALLOWED** without SCP-START | Must be first output | Cannot skip | Cannot defer

**MANDATORY TRIGGERS (AUTO-EMIT)**:
1. **session_start**: First user message in new session → **ALWAYS emit SCP-START**
2. **last_protocol==SCP-END**: Previous workflow completed → **ANY new request = SCP-START + new root**
3. **user("proceed"|"continue") after SCP-END**: Treat as new root → **ALWAYS emit SCP-START**
4. **no_active_workflow**: workflow_index undefined or session state unclear → **ALWAYS emit SCP-START**
5. **unrelated_request during workflow**: Different scope/domain → **Complete current + SCP-START for new root**

**VIOLATION = INVALID SESSION**: Response without SCP-START when required → Session invalid → Must restart → Re-emit SCP-START → Begin properly

### RESPONSE TEMPLATES - COPY AND FILL

**Session Init**: `[SCP-START: ✅LOADED:[6files] | ✅COMPLIANT:[4principles] | 🎯READY:DevTeam | 📚NWP:[index=0,depth=0]]`

**Phase Done**: `[SCP-PHASE: ✓CHATMODE:[items] | ✓INSTRUCTIONS:[files] | 🚫VIOLATIONS:[none] | 🔧ADJUST:[none] | 📚NWP:[index:N,phase:X/Y]]` + `STATUS:complete | PHASE:X/Y [NAME] | WORKFLOW:index=N,depth=N | TASKS:[prev][DONE]→[curr][DONE]→[next] | DISCOVERIES:[findings] | BLOCKERS:none | NEXT:[phase]`

**Nesting**: `[SCP-NWP: 🔄NEST→[trigger] | 📚INDEX:[N→N+1] | 🎯REASON:[cause] | 📍FROM:[phase] | 🗂️PHASES:[planned]]`

**Returning**: `[SCP-NWP: 🔄RETURN←[trigger] | 📚INDEX:[N→N-1] | ✅RESOLVED | 📍RESUME:[phase] | 🔄MERGE:[CEPH+learnings]]`

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

