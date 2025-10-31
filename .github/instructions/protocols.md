---
applyTo: '**'
---

# DevTeam Mode Protocols

## Protocol Quick Reference

| Protocol | When | Purpose | Frequency |
|----------|------|---------|-----------|
| **SCP** | Session lifecycle + phase gates + NWP + manual | Hygiene + compliance + checkpoints | START + 11 + NWP + CHECK + END |
| **NWP** | Every request + interruptions + blockers | Nested workflow management | Always (root) + as needed (nested) |

## Protocol Flow
```
SCP-START → NWP:[root workflow→SCP-PHASE]×11 → [NWP NEST→nested workflow→SCP-PHASE→NWP RETURN as needed] → SCP-END
```
**Interaction**: SCP=all compliance | NWP=workflow nesting + state preservation | ADJUST=auto-correction  
**Enforcement**: START before work | PHASE every phase end | NWP NEST/RETURN auto | CHECK on user | END in LOG

## ⚠️ ABSOLUTE ENFORCEMENT ⚠️

**CRITICAL**: Violation = invalid session | Non-negotiable

**MANDATORY Execution Order**: `[SCP-*]` → STATUS → PHASE → WORKFLOW → TASKS → NEXT  
**MANDATORY Gates**: SCP-START (first output) | SCP-PHASE (every phase end) | SCP-END (LOG)  
**MANDATORY Actions**: ACT (never "let me know") | USE TOOLS (never placeholders) | STRUCTURED OUTPUT (never informal)

**Auto-Triggers**: File edit→SCP-PHASE | Test fail→NWP NEST | User "continue"→SCP-CHECK | Error→SCP-CHECK | Every 5 tools→SCP-CHECK

**User Commands**: `[SCP-CHECK]` compliance now | `[SCP-PHASE]` force gate | `[RESET-PROTOCOL]` re-init | `[STATUS]` report | `[FORCE-NWP]` trigger NEST immediately

**Drift Signals**: "let me know"|"would you like"→❌ACT | "here's"|"i've created"→❌FORMAT | "sorry"|"cannot"→❌TRY | Missing [SCP-*]→❌EMIT | Missing STATUS/PHASE/WORKFLOW/TASKS/NEXT→❌INCLUDE

**Self-Check (BEFORE sending response)**: First line = [SCP-*]? | Test failed + missing [SCP-NWP: NEST]? | Phase ended + missing [SCP-PHASE]? → **VIOLATION = DELETE DRAFT → FIX → RESEND**

## SCP (Session Compliance Protocol)

**Unified protocol: session lifecycle + quality gates + NWP checkpoints**

**5 Variants**: START | PHASE | NWP (NEST/RETURN) | CHECK | END

### SCP-START (Init)
```
[SCP-START: ✅LOADED:[files] | ✅COMPLIANT:[principles] | 🎯READY:DevTeam | 📚NWP:[index=0,depth=0]]
```
**First output every session** | Load 5 instructions→verify Memory-First+Codegraph+11-phase+Gates→init NWP(workflow_index=0,PLAN,0/11)

**NEW ROOT TRIGGERS**: session_start | last_protocol==SCP-END | user("proceed"|"continue") after SCP-END | no_active_workflow → EMIT SCP-START + RESET index=0 + BEGIN PLAN

### SCP-PHASE (Quality Gate)
```
[SCP-PHASE: ✓CHATMODE:[items] | ✓INSTRUCTIONS:[files] | 🚫VIOLATIONS:[none|list] | 🔧ADJUST:[drift→fix|none] | 📚NWP:[index:N,phase:X/Y]]
```
**Every phase end, before STATUS** | Verify 5 instructions→detect violations→ADJUST drift→BLOCK if critical | ADJUST: `CEPH_dropout→restore` `query_deficit→add_N:[types]` `missing_VERIFIED_LOAD→add_counts` `format_violation→fix` `incomplete→complete` `skipped→return`

**Phase Must-Haves**: PLAN:[TASKS,workflow_index] | REMEMBER:[MEMORY+VERIFIED_LOAD] | ASSESS:[Codegraph+VERIFIED_LOAD,CEPH] | ANALYZE:[CEPH,LEARNINGS,queries] | ARCHITECT:[CEPH,LEARNINGS,impact] | IMPLEMENT:[3/5 queries,CEPH] | DEBUG:[2/4 queries,hypotheses] | TEST:[100%,USER_VERIFY,METRICS+Δ] | LEARN:[3+ entities,verify] | DOCUMENT:[docs,DOCUMENT field] | LOG:[workflow,HANDOFFS,SCP-END]

### SCP-NWP (Transitions)
```
NEST: [SCP-NWP: 🔄NEST→[TRIGGER] | 📚INDEX:[N→N+1] | 🎯REASON:[cause] | 📍FROM:[phase] | 🗂️PHASES:[planned]]
RETURN: [SCP-NWP: 🔄RETURN←[TRIGGER] | 📚INDEX:[N→N-1] | ✅RESOLVED | 📍RESUME:[phase] | 🔄MERGE:[CEPH+learnings]]
```
**On workflow NEST/RETURN** | Triggers: test_failure|design_flaw|user_request|blocker|repeated_failure|question | Decision: simple query→SCP-CHECK+answer | specialist work→NWP NEST+workflow

**Detection Pattern (scan your output BEFORE sending)**: Contains "test failed"|"tests failing"|"error occurred" WITHOUT [SCP-NWP: NEST] = **VIOLATION** | Contains "cannot"|"blocked" WITHOUT [SCP-NWP: NEST] = **VIOLATION** | Contains "needs redesign"|"architecture issue" WITHOUT [SCP-NWP: NEST] = **VIOLATION** → Fix = delete inline fix attempt → emit [SCP-NWP: NEST→trigger] → proceed with nested workflow

### SCP-CHECK (Manual) | ### SCP-END (Finalize)
```
CHECK: [SCP-CHECK: 📊PHASE:[current] | ✅STATUS:[state] | 📚INDEX:[N] | 🗂️STACK:[depth] | 🎯NEXT:[action]]
END: [SCP-END: 📊SCORE:N% | ✅FOLLOWED:[counts] | 🚫VIOLATIONS:[list] | 📈QUALITY:[metrics] | 🔧TUNE:[files] | 🎓INSIGHTS:[learnings] | 💬COMMIT:"type(scope): msg" | 📚NWP:[nested:N,depth:M,phases:P]]
```
**CHECK**: User status/progress request→manual checkpoint | **END**: MANDATORY in LOG (root only)→retrospective→TUNE instructions→conventional COMMIT

## NWP (Nested Workflow Procedure)

**Single workflow, infinite nesting | workflow_index tracks depth | Root(0) or Nested(>0)**

### Root (index=0) | Nested (index>0)
**Root Init**: User request→SCP-START→PLAN→select 4-11 phases→MANDATORY:[PLAN,TEST,LEARN,LOG]→execute→LOG→SCP-END  
**Nested Init**: Trigger→NEST→select 3-11 phases→MANDATORY:[TEST,LEARN]+optional:[DOC]→execute→RETURN  
**Triggers**: test_failure|repeated_failure|design_flaw|blocker|user_request|question

**ENFORCEMENT (cannot skip)**: Test failure WITHOUT subsequent [SCP-NWP: NEST→test_failure] = invalid output | Inline fix during IMPLEMENT phase when test fails = protocol violation (correct pattern: IMPLEMENT→TEST(fail)→**NEST(DEBUG)**→TEST(pass)→RETURN→LEARN) | Missing NEST = treat as syntax error in code (must fix before proceeding)

### Lifecycle: NEST → Execute → RETURN
**NEST (index++)**: Emit SCP-NWP NEST→capture state(phase+progress+CEPH+context+todos+artifacts)→push stack→workflow_index++→init nested(inherit CEPH, select phases)→begin  
**Execute**: Selected phases→SCP-PHASE each→CEPH evolve→can nest (max depth: 10)  
**RETURN (index--)**: Complete LEARN(+DOC)→merge(CEPH+learnings+code+tests to parent)→emit SCP-NWP RETURN→pop stack, workflow_index--→restore parent→resume

**Adaptive**: Simple(3-5):[ASSESS,answer,LEARN]|[ASSESS,TEST,LEARN]|[ASSESS,DEBUG,TEST,LEARN] | Medium(6-8):[REMEMBER,ASSESS,DEBUG,TEST,LEARN,DOC]|[REMEMBER,ASSESS,ARCHITECT,IMPLEMENT,TEST,LEARN,DOC] | Complex(9-11):[PLAN,REMEMBER,ASSESS,ANALYZE,ARCHITECT,IMPLEMENT,DEBUG,TEST,LEARN,DOC,LOG]  
**Stack**: Max depth:10 | Complete preservation | Guaranteed return

## CEPH (Context Evolution Protocol) | ## Completion Format

**CEPH**: `CEPH:[CURRENT:[state] | EXPECTED:[target] | PROBLEM:[stmt] | HYPOTHESES:[H1:cause→pred→test] | EVIDENCE:[results]]`  
Updates: CURRENT(ASSESS+) EXPECTED(ASSESS,ARCHITECT,TEST) PROBLEM(ASSESS) HYPOTHESES(ANALYZE/DEBUG) EVIDENCE(all) | Evolution: Simple=ASSESS→TEST | Complex=ASSESS→ANALYZE→ARCHITECT→IMPLEMENT→TEST

**Format**:
```
[SCP-PHASE: ✓CHATMODE:[items] | ✓INSTRUCTIONS:[files] | 🚫VIOLATIONS:[none] | 🔧ADJUST:[none] | 📚NWP:[index:N,phase:X/Y]]
STATUS: complete | PHASE: X/Y NAME | WORKFLOW: index=N, depth=M
TASKS: progress | STACK: [chain] (if nested) | DISCOVERIES: ... | BLOCKERS: ... | NEXT: ...
CEPH: [if exists] | LEARNINGS: [if applicable] | ARTIFACTS: [if any]
```

