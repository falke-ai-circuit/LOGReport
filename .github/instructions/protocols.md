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

### Memory Verification Template

```
MEMORY:[
  global_memory:[file_lines:847 domains:5 patterns:12 entities:45] |
  project_memory:[file_lines:1203 domains:5 clusters:8 entities:67] |
  VERIFIED_LOAD:[line_counts_match:YES summaries_complete:YES]
]
```

**Enforcement**: No `VERIFIED_LOAD` or `line_counts` → INCOMPLETE

## CEPH (Context Evolution Protocol)

**Structure**: `CEPH:[CURRENT:[facts+state] | EXPECTED:[target+criteria] | PROBLEM:[statement] | HYPOTHESES:[H1:cause→prediction→test] | EVIDENCE:[logs+metrics]]`

**Component Updates**:

| Component | When | Example |
|-----------|------|---------|
| CURRENT | ASSESS(init), after phases | `[9 methods, PyQt5 widgets]` |
| EXPECTED | ASSESS(init), ARCHITECT(refined), TEST(validated) | `[Tree widget + selection]` |
| PROBLEM | ASSESS(init), rarely | `[No UI for node selection]` |
| HYPOTHESES | ANALYZE(form), DEBUG(3-5), TEST(validate) | `[H1:QTreeWidget→hierarchy→docs]` |
| EVIDENCE | Throughout, TEST(final) | `[9/9 pass, 95%(+15%)]` |

**Hypothesis Format**: `HN:cause→prediction→test` | Start 3-5 → distill to 1-2 most likely

**Evolution**: Simple=ASSESS→TEST | Complex=ASSESS→ANALYZE→ARCHITECT→IMPLEMENT→TEST (update at each phase)

## Completion Format

**Standard**:
```
STATUS: [completed|partial|failed]
PHASE: [name]
TASKS: [list]
DISCOVERIES: [findings]
BLOCKERS: [none|issues]
NEXT: [action]
```

**Protocol Fields** (when applicable):
- `STACK:[breadcrumb] (depth:N)` (VMP depth≥1)
- `CEPH:[...]` (ASSESS onwards)
- `MEMORY:[...+VERIFIED_LOAD]` (REMEMBER)
- `LEARNINGS:[pattern:[X]|approach:[Y]]` ⚠️ MANDATORY (specialist phases)
- `METRICS:[...]` ⚠️ WITH DELTAS: `95%(+15%)|9/9(+9)` (TEST)

**Compliance Check**: ✓Actions ✓VMP ✓Fields ✓Queries ✓NEXT ✓SVP | Fail→`BLOCKERS:[items]`+`STATUS:partial`

**Phase Transitions**: ✓Complete ✓Requirements ✓Stack ✓CEPH ✓SVP
