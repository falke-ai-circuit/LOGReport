# VMP Enforcement Strategy with Self-Verify Protocol (SVP)

**Version**: 2.0.0  
**Date**: 2025-10-13  
**Purpose**: Ensure continuous adherence to DevTeam chatmode workflow with minimal overhead via lightweight state tracking

## Problem Statement

During long sessions, AI agents may drift from structured workflows, forgetting to:
- Execute VMP mode activation actions when PUSH occurs
- Verify mandatory fields in completion status
- Query memory/codegraph at required phases
- Follow proper format requirements (LEARNINGS pattern|approach, METRICS deltas)
- **Track current workflow state (phase, stack depth, next action)**

## Solution: Self-Verify Protocol (SVP) + Multi-Layer Verification

### Core Innovation: SVP State Tracker

**Concept**: Append lightweight state summary to EVERY agent response (single line suffix)

**Format**:
```
[SVP: ⚡PHASE→🔬ANALYZE | 📚STACK→none | ✓TASK→3/11 | 🎯NEXT→query_codegraph_IMPORTS]
```

**Fields**:
- **⚡PHASE**: Current phase/mode (horizontal: ANALYZE, vertical: DEBUG)
- **📚STACK**: VMP depth (`none` horizontal, `depth:N→🐛DEBUG←💻IMPLEMENT` vertical)
- **✓TASK**: Progress indicator (`3/11` phases, `reading_files` action)
- **🎯NEXT**: Immediate next action (`continue_IMPLEMENT`, `VMP_POP`, `query_codegraph`)

**Why This Works**:
1. **Persistent Reminder**: Agent writes SVP suffix → forces state awareness check
2. **Auto-Return Logic**: Stack depth explicitly shows POP targets (depth:2 = 2 POPs needed)
3. **Branch Clarity**: NEXT field prevents ambiguity (continue horizontal OR vertical operation)
4. **Minimal Overhead**: Single line, 4 fields, ~70 characters

### SVP Enforcement Layers
**Location**: DevTeam.chatmode.md → Core Principles  
**Mechanism**: Added to chatmode initialization, loaded every session
```markdown
- **Self-Verification ⚠️ CONTINUOUS**: Before EVERY STATUS emission, check compliance: 
  phase actions executed | VMP activation performed | mandatory fields present | 
  memory/codegraph queried | proper format used
```

**Trigger**: Agent reads this at session start, reminder present throughout conversation context

### Layer 2: Completion Format Checklist
**Location**: DevTeam.chatmode.md → Completion Format  
**Mechanism**: Inline checklist before STATUS emission
```markdown
**Compliance Check** (agent self-verify before STATUS emission):  
Before emitting STATUS completion, verify: 
✓ Phase actions executed per workflow section 
✓ VMP mode activation performed if PUSH occurred 
✓ Mandatory fields present (LEARNINGS format, METRICS deltas, CEPH evolution) 
✓ Memory/codegraph queried where required 
✓ NEXT action specified 
If checklist fails → BLOCKERS:[missing_items] + partial status
```

**Trigger**: Agent must review checklist immediately before writing STATUS block

### Layer 3: Phase Transition Verification
**Location**: DevTeam.chatmode.md → Communication  
**Mechanism**: Explicit verification requirement at phase boundaries
```markdown
**Phase Transitions**: At EVERY phase boundary, re-verify: 
Current phase actions complete | Next phase requirements known | 
VMP stack resolved or documented | Compliance check passed
```

**Trigger**: Fires when agent moves from one phase to another (e.g., ASSESS→ANALYZE)

### Layer 4: VMP Mode Activation Table
**Location**: DevTeam.chatmode.md → VMP Mode Activation Actions  
**Mechanism**: Reference table for contextual actions when mode PUSH occurs
```markdown
| Mode | Activation Actions | Context |
|------|-------------------|---------|
| 🧠 REMEMBER | Query project_memory.json/global_memory.json for current topic... | Retrieve knowledge for current blocker |
| 🔍 ASSESS | Scan README/CHANGELOG/docs for current issue... | Re-evaluate situation with fresh context |
...
```

**Trigger**: Agent consults table when VMP PUSH detected, executes mode-specific actions

## Enforcement Mechanism

### Automatic Triggers
1. **Session Start**: Core Principles loaded → Self-Verification rule active
2. **Phase Completion**: Agent reaches "write STATUS" → Compliance Check triggers
3. **Phase Transition**: Moving to new phase → Phase Transition Verification triggers
4. **VMP PUSH**: Blocker detected → Mode Activation Table consulted → Actions executed

### Failure Handling
If compliance check fails:
```
STATUS: partial
PHASE: [CURRENT_PHASE]
BLOCKERS: [missing_VMP_activation | missing_LEARNINGS_format | missing_codegraph_query]
NEXT: [fix_blockers_then_retry]
```

Agent explicitly documents what was missed, preventing silent drift.

## Minimal Overhead Design

**Why This Works**:
1. **No New Phases**: No additional workflow steps, just verification at existing checkpoints
2. **Inline Reminders**: Checklist embedded in completion format (agent reads it anyway)
3. **Self-Documenting**: Failures captured in BLOCKERS field (visible to user + agent)
4. **Natural Triggers**: Verification points align with existing workflow boundaries

**Changes Required**: Only 3 additions to chatmode file:
- Core Principles: +1 line (Self-Verification)
- Completion Format: +3 lines (Compliance Check)
- Communication: +1 line (Phase Transitions)
- VMP Section: +7 lines (Mode Activation Table)

**Total Overhead**: 12 lines added to 251-line chatmode (4.8% increase)

## Examples

### Correct Adherence (ASSESS Phase)
```
STATUS: completed
PHASE: ASSESS
TASKS: [x] PLAN | [x] REMEMBER | [x] ASSESS | [ ] ANALYZE...
DISCOVERIES: [codegraph loaded (120 entities), docs reviewed (README, standards.md), environment validated (Python 3.11, pytest 8.4.1)]
CEPH: [CURRENT:[LOGReport PyQt5 app, telnet+bstool tabs working] | EXPECTED:[fix ASCII column alignment] | PROBLEM:[Monospace font not preserving table alignment] | HYPOTHESES:[H1:font rendering→test Liberation Mono]]
BLOCKERS: none
CODEGRAPH: [loaded:YES summary:[modules:45 classes:78 methods:340] | VERIFIED_LOAD:[codegraph_complete:YES]]
DOCS_REVIEWED: [README.md, standards.md, TODO.md]
NEXT: proceed_to_ANALYZE

✓ Compliance Check Passed: Phase actions executed ✓ | VMP activation N/A ✓ | Mandatory fields present ✓ | Codegraph queried ✓ | NEXT specified ✓
```

### VMP Mode Activation (IMPLEMENT → ANALYZE)
```
🔄 VMP PUSH
STACK: 💻 IMPLEMENT (depth:1)
MODE: 🔬 ANALYZE
ORIGIN: IMPLEMENT.column_alignment (blocked_by:unknown_font_behavior)
TRIGGER: Anomaly detected - monospace font not preserving alignment despite tab-to-space conversion

[VMP Mode Activation: ANALYZE]
✓ Query codegraph IMPORTS/BELONGS_TO → telnet_tab.py imports PyQt5.QtWidgets.QTextEdit
✓ Map dataflow → append_output() → insertPlainText() → font rendering
✓ Identify root causes → QTextEdit uses platform font rendering (variable-width fallback)
✓ Update CEPH.HYPOTHESES → H1:font fallback→test QPlainTextEdit, H2:manual spacing→pre-format content

RESOLVED: QTextEdit limitations identified, alternative widget required

ACTION: VMP POP to IMPLEMENT with solution (use QPlainTextEdit or pre-format content)
```

### Failed Compliance Check
```
STATUS: partial
PHASE: DEBUG
TASKS: [x] PLAN | [x] REMEMBER | [x] ASSESS | [x] ANALYZE | [x] ARCHITECT | [x] IMPLEMENT | [x] DEBUG | [ ] TEST...
DISCOVERIES: [bug fixed in telnet_tab.py line 145, QPlainTextEdit now used]
BLOCKERS: [missing_codegraph_trace | missing_hypotheses_documentation]
NEXT: document_execution_trace_then_retry_DEBUG_completion

❌ Compliance Check Failed: Phase actions partial (no CALLS trace) | VMP activation N/A | Mandatory fields missing (EXECUTION_TRACE) | Codegraph not queried for CALLS chains | NEXT specified
```

Agent explicitly states what's missing, re-executes requirements, then completes properly.

## Effectiveness

**Hypothesis**: Multi-layer self-verification creates persistent reminders throughout session lifecycle without adding workflow complexity.

**Expected Outcome**: Agent maintains adherence via:
1. Initial reminder (Core Principles)
2. Pre-completion verification (Compliance Check)
3. Boundary checks (Phase Transitions)
4. Contextual guidance (VMP Mode Activation Table)

**Fallback**: If agent forgets checklist, emits STATUS without verification → user sees missing fields → user prompts agent → agent re-reads Compliance Check → corrects output.

## Maintenance

**Update Frequency**: Only when adding new mandatory fields or phases  
**Backward Compatibility**: Existing phases unchanged, only verification added  
**Documentation Sync**: Changes to workflow require updating Compliance Check items

---

**Key Insight**: Self-verification at natural checkpoints (STATUS emissions, phase transitions) creates automatic enforcement without explicit "verification phases" that would slow workflow.
