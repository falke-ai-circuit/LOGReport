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

## Error Recovery Patterns

| Scenario | Detection | Action | Example |
|----------|-----------|--------|---------|
| **Test Failure** | <100% pass | 🔄 VMP PUSH DEBUG → 3-5 hypotheses → fix → POP | TEST(1/9 fail) → DEBUG(H1:logic_order) → fixed → POP TEST(9/9) |
| **Repeated Failures** | 2+ same issue | 🔄 VMP PUSH ASSESS → identify systemic → fix → POP | DEBUG(path fail 2x) → ASSESS(standards) → normalize → POP |
| **Design Flaw** | Limitation found | 🔄 VMP PUSH ARCHITECT → alternatives → POP | TEST(widget limit) → ARCHITECT(custom delegate) → POP |
| **Anomaly** | Unexpected behavior | 🔄 VMP PUSH ANALYZE → root cause → POP | IMPLEMENT(font broken) → ANALYZE(QTextEdit issue) → POP |
| **Memory Fail** | File missing | Verify exists → check format → validate pattern → re-read | Load error → check JSONL → validate 4-layer → reload |
| **Codegraph Missing** | File not found | Proceed without → create in LEARN | ASSESS(no file) → skip queries → LEARN(create new) |
| **User Verify Timeout** | No response | DO NOT auto-proceed → re-present → escalate | TEST(await) → no answer → re-present results |

## Auto-Detection Triggers

| Pattern | Condition | Target | Example |
|---------|-----------|--------|---------|
| **Test Failure** | <100% pass | DEBUG | `9/9 REQUIRED but 8/9 passed` → DEBUG |
| **Repeated** | Same issue 2+ | ASSESS | `Path error 2nd occurrence` → ASSESS |
| **Design Flaw** | Architecture block | ARCHITECT | `Widget cannot support feature` → ARCHITECT |
| **Anomaly** | Unexpected | ANALYZE | `Font rendering breaks alignment` → ANALYZE |
| **Requirement Gap** | Ambiguous criteria | ANALYZE | `Unclear what "valid" means` → ANALYZE |
| **User Request** | Direct command | [MODE] | `"Can you explain the architecture?"` → ARCHITECT |
| **Circular Dep** | Import loop | ANALYZE | `ModuleA imports ModuleB imports ModuleA` → ANALYZE |

## CEPH Evolution Examples

**Simple Task** (validation fix):
```
ASSESS: CURRENT:[Rejects AP01M] EXPECTED:[Accept all types] HYPOTHESES:[H1:Pattern update needed]
TEST: CURRENT:[Updated pattern] EXPECTED:[MET] HYPOTHESES:[H1:CONFIRMED] EVIDENCE:[9/9 pass]
```

**Complex Task** (UI component):
```
ASSESS: CURRENT:[No UI] EXPECTED:[Tree widget] PROBLEM:[No selection] HYPOTHESES:[H1:New widget | H2:Extend existing]
ANALYZE: CURRENT:[QTreeWidget identified] HYPOTHESES:[H1:VALIDATED | H2:REJECTED] EVIDENCE:[Docs confirm hierarchy support]
ARCHITECT: CURRENT:[Design finalized] EXPECTED:[Tree+delegate] HYPOTHESES:[H1:CONFIRMED] EVIDENCE:[Impact:2 modules]
IMPLEMENT: CURRENT:[Implemented tree+delegate] HYPOTHESES:[H1:COMPLETE]
TEST: CURRENT:[Tested] EXPECTED:[MET] HYPOTHESES:[H1:CONFIRMED] EVIDENCE:[12/12 pass, 95%(+15%)]
```

## Compliance Checklists

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
