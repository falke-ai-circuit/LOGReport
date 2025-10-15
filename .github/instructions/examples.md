---
applyTo: '**'
---

# DevTeam Mode Examples

## VMP Activation Patterns (with SVP)

**Pattern 1: IMPLEMENT→ANALYZE** (anomaly):
```
[SVP: ⚡PHASE→💻IMPLEMENT | 📚STACK→none | ✓TASK→5/11 | 🎯NEXT→fix]
🔄 VMP PUSH → 🔬 ANALYZE (anomaly:font_rendering)
[SVP: ⚡PHASE→🔬ANALYZE | 📚STACK→depth:1→💻IMPLEMENT | ✓TASK→query | 🎯NEXT→trace_IMPORTS]
Query: QTextEdit vs QPlainTextEdit → RESOLVED:use QPlainTextEdit
🔄 VMP POP
[SVP: ⚡PHASE→💻IMPLEMENT | 📚STACK→none | ✓TASK→5/11 | 🎯NEXT→apply_fix]
```

**Pattern 2: DEBUG→ASSESS** (repeated failures):
```
[SVP: ⚡PHASE→🐛DEBUG | 📚STACK→none | ✓TASK→6/11 | 🎯NEXT→trace]
🔄 VMP PUSH → 🔍 ASSESS (repeated:path_issue_2nd_time)
[SVP: ⚡PHASE→🔍ASSESS | 📚STACK→depth:1→🐛DEBUG | ✓TASK→scan | 🎯NEXT→query]
Scan standards+codegraph → RESOLVED:normalization_missing_3_locations
🔄 VMP POP
```

**Pattern 3: TEST→ARCHITECT** (design flaw):
```
[SVP: ⚡PHASE→🧪TEST | 📚STACK→none | ✓TASK→7/11 | 🎯NEXT→run]
9/9 pass BUT design_flaw → 🔄 VMP PUSH → 🏗️ ARCHITECT (limitation:widget)
[SVP: ⚡PHASE→🏗️ARCHITECT | 📚STACK→depth:1→🧪TEST | ✓TASK→impact | 🎯NEXT→query_reverse_IMPORTS]
Evaluate alternatives → RESOLVED:custom_QTreeWidget_with_delegate
🔄 VMP POP
```

**Pattern 4: USER** (no stack change):
```
[SVP: ⚡PHASE→💻IMPLEMENT | 📚STACK→none | ✓TASK→5/11 | 🎯NEXT→create]
USER: "What does validation do?"
🔄 VMP USER (from IMPLEMENT)
[Answer...] ACTION:RESUME
```

**Pattern 5: Deep Stack** (depth:2):
```
💻 IMPLEMENT → (test fail) → 🐛 DEBUG → (circular import) → 🔬 ANALYZE
[SVP: ⚡PHASE→🔬ANALYZE | 📚STACK→depth:2→🐛DEBUG←💻IMPLEMENT | ✓TASK→map | 🎯NEXT→trace]
```

## Error Recovery / Auto-Detection

| Scenario | Detection | Action |
|----------|-----------|--------|
| **Test Failure** | <100% pass | PUSH DEBUG → hypotheses → fix → POP |
| **Repeated** | 2+ same issue | PUSH ASSESS → systemic → fix → POP |
| **Design Flaw** | Limitation | PUSH ARCHITECT → alternatives → POP |
| **Anomaly** | Unexpected | PUSH ANALYZE → root cause → POP |
| **Memory/Codegraph Missing** | File not found | Verify/proceed without → create in LEARN |
| **User Verify Timeout** | No response | DO NOT auto-proceed → re-present |

**Triggers**: Test fail→DEBUG | Repeated→ASSESS | Design→ARCHITECT | Anomaly→ANALYZE | User→[MODE] | Circular→ANALYZE

## CEPH Evolution Examples

**Simple**: `ASSESS: CURRENT:[Rejects AP01M] EXPECTED:[Accept all] HYPOTHESES:[H1:Pattern update] → TEST: EXPECTED:[MET] EVIDENCE:[9/9 pass]`

**Complex**: `ASSESS: CURRENT:[No UI] EXPECTED:[Tree widget] HYPOTHESES:[H1:New widget|H2:Extend] → ANALYZE: H1:VALIDATED|H2:REJECTED → ARCHITECT: EXPECTED:[Tree+delegate] → IMPLEMENT → TEST: EXPECTED:[MET] EVIDENCE:[12/12,95%(+15%)]`

## Compliance Checklists

**Note**: These checklists are now verified automatically through CVP (Compliance Verification Protocol). See CVP section in protocols.md for full specification.

**REMEMBER Phase**:
☐ Load global_memory (domains+3/domain)  
☐ Load project_memory (clusters+recent 10)  
☐ Report file_lines for both  
☐ Summarize: domains/patterns/entities with counts  
☐ Include `VERIFIED_LOAD:[line_counts_reported:YES summaries_complete:YES hierarchies_valid:YES]`

**ASSESS Phase**:
☐ Load codegraph.json ENTIRE file  
☐ Review docs (README, CHANGELOG, standards.md, structure.md)  
☐ Summarize: modules/classes/methods/relations  
☐ Create CEPH (CURRENT, EXPECTED, PROBLEM, HYPOTHESES)  
☐ Include `VERIFIED_LOAD:[codegraph_complete:YES structure_valid:YES]`

**TEST Phase**:
☐ Extract acceptance criteria from user prompt  
☐ Map test surface via codegraph  
☐ Run pytest -v  
☐ Verify 100% pass (ALL tests, not partial)  
☐ IF fail: route appropriately (logic→DEBUG | design→ARCHITECT | requirements→ANALYZE)  
☐ Present results to user  
☐ Request verification explicitly  
☐ **🛑 WAIT for response**  
☐ Include `USER_VERIFICATION:[awaiting_confirmation:YES]`  
☐ Include `METRICS` with deltas: `95%(+15%) | 9/9(+9)`

## Anti-Patterns

❌ **Skip SVP**: Proceeding without `[SVP: ...]` → ✅ ALWAYS emit (Full at phases, Mini at responses)  
❌ **Auto-Proceed**: TEST pass → immediate LEARN → ✅ TEST pass → present → WAIT → confirm → LEARN  
❌ **Fake Load**: Claim "loaded 847 lines" without reading → ✅ Actually load + report `file_lines:847`  
❌ **Shallow Query**: "Queried codegraph" without results → ✅ Show specific findings: `IMPORTS:[json,pathlib]`  
❌ **Skip VMP Block**: Describe "going to debug" → ✅ Emit `🔄 VMP PUSH` block  
❌ **Wrong LEARNINGS**: `LEARNINGS:[We fixed the bug]` → ✅ `LEARNINGS:[pattern:[X]|approach:[Y]]`  
❌ **No Deltas**: `METRICS:[coverage=95%]` → ✅ `METRICS:[coverage=95%(+15%) | tests=9/9(+9)]`  
❌ **Forget CEPH**: Create in ASSESS, never update → ✅ Update at each phase (CURRENT/EXPECTED/EVIDENCE)  
❌ **Skip CVP**: Complete phase without compliance check → ✅ ALWAYS emit `[CVP: ...]` before STATUS

## CVP Examples

**Full Compliance** (IMPLEMENT):
```
[CVP: ✓CHATMODE:[SVP,Codegraph:5/5,CEPH,LEARNINGS,Completion] | ✓INSTRUCTIONS:[protocols,phases,standards,structure] | 🚫VIOLATIONS:[none]]
STATUS: completed | PHASE: IMPLEMENT | BLOCKERS: none
LEARNINGS: pattern:[Validation pattern for normalization] | approach:[Query signatures first]
NEXT: proceed_to_debug
```

**Partial Compliance** (IMPLEMENT, insufficient queries):
```
[CVP: ✓CHATMODE:[SVP,CEPH] | ⚠️CHATMODE:[Codegraph:2/5] | ✓INSTRUCTIONS:[protocols,standards] | ⚠️INSTRUCTIONS:[phases:insufficient_queries] | 🚫VIOLATIONS:[1:Insufficient_queries]]
STATUS: partial | PHASE: IMPLEMENT | BLOCKERS: Need 3/5 codegraph queries (have 2)
NEXT: add_1_query_complete_implement
```

**Critical Violation** (TEST, auto-proceeded):
```
[CVP: ✓CHATMODE:[SVP,Tests:100%] | ❌CHATMODE:[USER_VERIFICATION:missing] | ❌INSTRUCTIONS:[phases:checkpoint_violated,standards:METRICS_no_deltas] | 🚫VIOLATIONS:[2:USER_VERIFICATION,METRICS_deltas]]
STATUS: failed | PHASE: TEST | BLOCKERS: CRITICAL - No USER_VERIFICATION requested, METRICS missing deltas
NEXT: revert_present_results_request_verify
```

**CVP Integration**: Complete work → Self-check 6 files (chatmode, protocols, phases, standards, structure, examples) → Emit CVP → If violations: BLOCKERS + fix → Emit completion


