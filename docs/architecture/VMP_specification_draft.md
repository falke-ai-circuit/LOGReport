# Vertical Mode Protocol (VMP) - Unified Specification

**Version**: 2.0.0 (Unified)  
**Date**: 2025-10-13  
**Purpose**: Unified workflow interruption management - handles user questions AND agent-detected blockers via single protocol

---

## Core Concept

**VMP** = Unified interruption protocol | Handles **user-driven** (questions, feedback) AND **agent-driven** (anomalies, blockers, test failures) interruptions | Stack-based context preservation | Automatic PUSH/POP operations | Breadcrumb navigation

**Key Insight**: All workflow interruptions share same pattern: preserve context → resolve → resume | No need to differentiate between user vs agent - ORIGIN field naturally shows the source

---

## VMP Operations (Unified)

### 1. VMP (User Interruption)

**When**: User asks question, provides feedback, changes requirements

```
🔄 VMP
STACK: [current_stack] (depth:N)
MODE: [current_mode_emoji_name]
ORIGIN: [current_phase].action (interrupted_by:[user_question|feedback|new_info])
STATUS: [current_state]

[Address user's interruption]

ACTION: RESUME [phase].action
```

**Example**:
```
🔄 VMP
STACK: 🏗️ ARCHITECT (depth:0)
MODE: 🏗️ ARCHITECT
ORIGIN: ARCHITECT.api_design (interrupted_by:[user_question_about_auth])
STATUS: designing_rate_limiting

JWT authentication will integrate with existing auth_service.py, supporting refresh tokens

ACTION: RESUME api_design with auth layer integration
```

---

### 2. VMP PUSH (Enter Vertical Mode)

**When**: Agent detects blocker/anomaly requiring vertical exploration

```
🔄 VMP PUSH
STACK: [parent_modes_with_arrows] (depth:N)
MODE: [new_vertical_mode_emoji_name]
ORIGIN: [parent_phase].action (blocked_by:[specific_issue])
TRIGGER: [anomaly|test_failure|design_flaw|investigation_needed|requirement_gap]

[Brief context for vertical transition]

ACTION: [first_action_in_new_mode]
```

**Example**:
```
🔄 VMP PUSH
STACK: 🏗️ ARCHITECT (depth:1)
MODE: 🔬 ANALYZE
ORIGIN: ARCHITECT.validator_design (blocked_by:[circular_import_pattern])
TRIGGER: codegraph_anomaly

Codegraph shows IMPORTS cycle: validators/__init__.py ↔ base.py ↔ field.py

ACTION: Map import graph using codegraph IMPORTS relations
```

---

### 3. VMP POP (Exit Vertical Mode)

**When**: Vertical exploration complete, blocker resolved

```
🔄 VMP POP
STACK: [remaining_stack_after_pop] (depth:N-1)
MODE: [parent_mode_resumed]
RESOLVED: [what_was_accomplished]

[Summary of resolution]

ACTION: [RESUME parent_action | CONTINUE horizontal | PUSH another_mode]
```

**Example**:
```
🔄 VMP POP
STACK: 🏗️ ARCHITECT (depth:1)
MODE: 🏗️ ARCHITECT
RESOLVED: ANALYZE confirmed hub-spoke pattern eliminates circular imports

Analysis identified __init__.py imports all validators at once. Hub pattern with lazy loading resolves cycle.

ACTION: RESUME validator_design with new architecture pattern
```

---

## Unified Approach

**No Distinction**: VMP handles user interruptions AND agent blockers uniformly  
**ORIGIN Field**: Naturally shows source - `interrupted_by:[user_question]` vs `blocked_by:[anomaly]`  
**Stack Behavior**: User interruptions stay at current depth (answer & resume) | Agent blockers PUSH to new depth (explore & POP)  
**Simpler Mental Model**: One protocol for all context switches

---

## Auto-Detection Triggers (PUSH)

Agent **automatically emits VMP PUSH** when detecting these patterns:

| Trigger Type | From Phase | To Phase | Detection Keywords/Patterns | Mandatory? |
|-------------|-----------|----------|----------------------------|-----------|
| **Anomaly** | Any | ANALYZE | "unexpected", "mismatch", "inconsistent", "contradictory codegraph", "pattern violation" | No |
| **Investigation** | ANALYZE | DEBUG | "hypothesis unclear", "need trace", "3+ hypotheses", "runtime validation needed", "empirical evidence required" | No |
| **Test Failure** | TEST | DEBUG | Test pass < 100%, pytest FAILED, exit code ≠ 0, "AssertionError" | **YES** |
| **Design Flaw** | DEBUG/IMPLEMENT | ARCHITECT | "architectural limitation", "requires redesign", "interface change needed", "tight coupling blocks", "performance bottleneck" | No |
| **Requirement Gap** | Any | ANALYZE | "ambiguous requirement", "unclear criteria", "conflicting specs", "edge case undefined", "acceptance criteria missing" | No |
| **Context Missing** | IMPLEMENT/DEBUG | ASSESS | "environment unclear", "dependency unknown", "tool unavailable", "configuration undefined" | No |

**Mandatory Rule**: TEST phase with ANY failure (< 100% pass) **MUST** PUSH DEBUG (non-negotiable quality gate)

---

### POP Triggers (Automatic Vertical Exit)

Agent **automatically emits VMP POP** when detecting completion:

| Condition | Recognition Pattern | Action |
|-----------|-------------------|--------|
| **Objective Met** | STATUS: completed + BLOCKERS: none + DISCOVERIES: [resolution] | POP with RESOLVED |
| **Context Ready** | LEARNINGS extracted + ARTIFACTS created + CEPH updated | POP with CONTEXT |
| **Blocker Cleared** | Parent BLOCKER resolved + Solution available | POP with resolution |
| **Phase Complete** | Vertical phase standard completion reached | POP to parent |

---

### CONTINUE Horizontal (No Vertical Transition)

Agent stays in horizontal flow when:

| Condition | Action |
|-----------|--------|
| Stack depth = 0 + STATUS: completed + BLOCKERS: none | CONTINUE to next horizontal phase |
| Stack depth = 0 + STATUS: partial/failed + Trigger detected | PUSH appropriate recovery phase |
| Stack depth ≥ 1 + Work ongoing | Stay in current vertical mode |
| Stack depth ≥ 1 + Vertical complete | POP to parent |

---

## Decision Tree

```
┌─────────────────────────────┐
│   Phase Action/Completion   │
└──────────────┬──────────────┘
               │
        ┌──────▼──────┐
        │ Check Stack │
        └──────┬──────┘
               │
        ┌──────▼──────────────────────┐
        │ Stack Depth?                │
        └──────┬──────────────────────┘
               │
        ┌──────▼──────────┬───────────────────┐
        │                 │                   │
    Depth = 0         Depth ≥ 1          Mid-Phase
  (Horizontal)        (Vertical)        (Any Depth)
        │                 │                   │
        │                 │                   │
  ┌─────▼─────┐     ┌─────▼──────┐     ┌─────▼──────┐
  │ Status?   │     │ Objective? │     │ Trigger?   │
  └─────┬─────┘     └─────┬──────┘     └─────┬──────┘
        │                 │                   │
  ┌─────▼─────────┐ ┌─────▼──────────┐ ┌─────▼──────────┐
  │ completed?    │ │ Achieved?      │ │ Pattern Match? │
  ├─ YES          │ ├─ YES → POP     │ ├─ Anomaly      │
  │  → CONTINUE   │ ├─ NO → Check    │ │  → PUSH ANALYZE│
  │    horizontal │ │   blockers:    │ ├─ Test Fail    │
  ├─ NO           │ │   ├─ Found →   │ │  → PUSH DEBUG  │
  │  → Check      │ │   │   PUSH     │ ├─ Design Flaw  │
  │    trigger    │ │   └─ None →    │ │  → PUSH ARCH   │
  │  → PUSH       │ │      CONTINUE  │ └─ None         │
  └───────────────┘ └────────────────┘   → Stay/Continue│
                                      └─────────────────┘
```

---

## Safety Mechanisms

### Maximum Depth Limit

**Rule**: Stack depth ≤ 5 (prevents infinite nesting)

**Enforcement**:
```
🔄 VMP DEPTH_LIMIT
STACK: [5_level_deep_stack] (depth:5 MAX_REACHED)
MODE: [current_mode]
WARNING: Maximum vertical depth reached, forcing resolution path

BLOCKER: Cannot PUSH deeper, must POP or resolve current stack
ACTION: [Complete current mode | Emergency POP_ALL | Request user guidance]
```

---

### Emergency POP_ALL

**Trigger**: Stack depth = 5 + blocked + no resolution path  
**Action**: Collapse entire stack to depth 0, document in LOG as partial workflow

```
🔄 VMP POP_ALL
STACK: [empty] (depth:0 EMERGENCY_COLLAPSE)
MODE: [returning_to_horizontal]
REASON: [max_depth_reached | circular_vertical_dependency | user_abort]
STATUS: partial_workflow_vertical_stack_collapsed

Stack collapsed from depth 5. Vertical explorations logged but incomplete.
Artifacts: [list_of_discoveries_from_each_level]

ACTION: CONTINUE horizontal from [last_stable_phase] OR LOG partial workflow
```

---

### PEEK Before POP

**Use Case**: Verify parent context ready before popping

```
🔄 VMP PEEK
STACK: 🏗️ ARCHITECT ← 🔬 ANALYZE (depth:2)
MODE: 🔬 ANALYZE
QUERY: ARCHITECT blocker cleared?
RESULT: yes (validator pattern resolved, design can continue)

ACTION: POP to ARCHITECT
```

---

## Integration with Existing Phases

### Phase Completion Format Extension

**Standard completion** (unchanged):
```
STATUS: [completed|partial|failed]
PHASE: [PHASE_NAME]
TASKS: [phase_list]
DISCOVERIES: [findings]
BLOCKERS: [issues]
NEXT: [action]
```

**With VMP** (optional STACK field):
```
STATUS: [completed|partial|failed]
PHASE: [PHASE_NAME]
STACK: [breadcrumb_trail] (depth:N)  ← NEW OPTIONAL FIELD
TASKS: [phase_list]
DISCOVERIES: [findings]
BLOCKERS: [issues]
NEXT: [action]
```

**Rule**: STACK field appears **only when depth ≥ 1** (vertical mode active)

---

### CEPH Evolution Across Stack

**Principle**: CEPH context flows through vertical stack, accumulating evidence

**Example**:
```
ARCHITECT (depth:1):
  CEPH: CURRENT:[validator module design]
        EXPECTED:[circular import resolved]
        PROBLEM:[__init__.py import cycle]
        HYPOTHESES:[H1:flat structure | H2:__init__ imports all | H3:import order]
  
  PUSH ANALYZE (depth:2):
    CEPH: CURRENT:[mapping import graph] (inherited from ARCHITECT)
          EXPECTED:[identify cycle source]
          PROBLEM:[__init__.py import cycle] (same)
          HYPOTHESES:[H2:__init__ imports all | H3:import order] (narrowed)
    
    PUSH DEBUG (depth:3):
      CEPH: CURRENT:[tracing runtime imports] (inherited)
            EXPECTED:[confirm hypothesis H2]
            PROBLEM:[__init__.py import cycle] (same)
            HYPOTHESES:[H2:__init__ imports all] (focused)
            EVIDENCE:[trace shows all validators loaded at once] (NEW)
      
      POP to ANALYZE (depth:2):
        CEPH: CURRENT:[analysis complete]
              EXPECTED:[hub-spoke pattern]
              PROBLEM:[RESOLVED]
              HYPOTHESES:[H2 CONFIRMED]
              EVIDENCE:[trace + hub pattern from codegraph] (accumulated)
    
    POP to ARCHITECT (depth:1):
      CEPH: CURRENT:[validator design with hub pattern]
            EXPECTED:[lazy loading implementation]
            PROBLEM:[RESOLVED]
            HYPOTHESES:[validated]
            EVIDENCE:[full vertical exploration] (complete picture)

CONTINUE horizontal → IMPLEMENT (depth:0)
```

---

## Workflow Examples

### Example 1: Simple Vertical (Single PUSH/POP)

**Scenario**: IMPLEMENT → DEBUG → IMPLEMENT

```
💻 IMPLEMENT building validator.py
  STATUS: in-progress
  DISCOVERIES: [validate_email method implemented]
  TRIGGER: "test_email_validation FAILED (unexpected regex behavior)"
  
  🔄 VMP PUSH
  STACK: 💻 IMPLEMENT (depth:1)
  MODE: 🐛 DEBUG
  ORIGIN: IMPLEMENT.validate_email (blocked_by:[test_failure])
  TRIGGER: test_failure_mandatory
  
  🐛 DEBUG investigating regex
    DISCOVERIES: [regex missing ^ anchor, matches substring not full string]
    STATUS: completed
    BLOCKERS: none
    
    🔄 VMP POP
    STACK: 💻 IMPLEMENT (depth:1)
    MODE: 💻 IMPLEMENT
    RESOLVED: DEBUG found missing regex anchor (^email_pattern$)
    CONTEXT: Fix applied to validate_email, test now passes
    
💻 IMPLEMENT (resumed)
  STATUS: completed
  DISCOVERIES: [validate_email fixed and tested]
  BLOCKERS: none
  
  CONTINUE horizontal → TEST
```

---

### Example 2: Deep Vertical (Triple Nesting)

**Scenario**: ARCHITECT → ANALYZE → DEBUG → ARCHITECT

```
🏗️ ARCHITECT designing API gateway
  DISCOVERIES: [rate limiting needed, token validation unclear]
  TRIGGER: "authentication scope undefined (requirement gap)"
  
  🔄 VMP PUSH
  STACK: 🏗️ ARCHITECT (depth:1)
  MODE: 🔬 ANALYZE
  ORIGIN: ARCHITECT.api_gateway (blocked_by:[auth_scope_undefined])
  TRIGGER: requirement_gap
  
  🔬 ANALYZE requirement clarification
    DISCOVERIES: [3 hypotheses: JWT vs session vs API key]
    TRIGGER: "3+ hypotheses, need runtime validation"
    
    🔄 VMP PUSH
    STACK: 🏗️ ARCHITECT ← 🔬 ANALYZE (depth:2)
    MODE: 🐛 DEBUG
    ORIGIN: ANALYZE.auth_investigation (blocked_by:[unclear_hypothesis])
    TRIGGER: investigation_needed
    
    🐛 DEBUG testing auth methods
      DISCOVERIES: [existing codebase uses JWT with refresh tokens]
      STATUS: completed
      
      🔄 VMP POP
      STACK: 🏗️ ARCHITECT ← 🔬 ANALYZE (depth:2)
      MODE: 🔬 ANALYZE
      RESOLVED: DEBUG confirmed JWT pattern in auth_service.py
      CONTEXT: Codegraph shows 15 modules IMPORT auth.jwt_handler
      
  🔬 ANALYZE (resumed)
    LEARNINGS: [pattern:[JWT with refresh tokens standard] | approach:[query codegraph for usage patterns]]
    STATUS: completed
    
    🔄 VMP POP
    STACK: 🏗️ ARCHITECT (depth:1)
    MODE: 🏗️ ARCHITECT
    RESOLVED: ANALYZE confirmed JWT authentication standard across codebase
    CONTEXT: CEPH.EXPECTED updated with JWT integration requirements
    
🏗️ ARCHITECT (resumed)
  DISCOVERIES: [API gateway will use existing JWT handler, rate limiting per token]
  STATUS: completed
  
  CONTINUE horizontal → IMPLEMENT
```

---

### Example 3: Lateral Vertical (PUSH Different Phase from Stack)

**Scenario**: ARCHITECT → ANALYZE → POP → ARCHITECT (finds new issue) → DEBUG

```
🏗️ ARCHITECT designing cache layer
  DISCOVERIES: [Redis vs in-memory decision needed]
  
  🔄 VMP PUSH
  STACK: 🏗️ ARCHITECT (depth:1)
  MODE: 🔬 ANALYZE
  
  🔬 ANALYZE performance comparison
    DISCOVERIES: [Redis better for distributed, in-memory faster single node]
    STATUS: completed
    
    🔄 VMP POP
    STACK: 🏗️ ARCHITECT (depth:1)
    MODE: 🏗️ ARCHITECT
    RESOLVED: Use Redis for scalability
    
🏗️ ARCHITECT (resumed)
  DISCOVERIES: [Redis integration design complete]
  TRIGGER: "tight coupling detected in cache_manager.py (design flaw during review)"
  
  🔄 VMP PUSH
  STACK: 🏗️ ARCHITECT (depth:1)
  MODE: 🐛 DEBUG
  ORIGIN: ARCHITECT.cache_design_review (blocked_by:[tight_coupling_singleton])
  TRIGGER: design_flaw
  
  🐛 DEBUG investigating singleton pattern
    DISCOVERIES: [singleton prevents testing, creates global state]
    STATUS: completed
    
    🔄 VMP POP
    STACK: 🏗️ ARCHITECT (depth:1)
    MODE: 🏗️ ARCHITECT
    RESOLVED: Replace singleton with dependency injection
    
🏗️ ARCHITECT (resumed)
  DISCOVERIES: [Cache layer redesigned with DI, testable architecture]
  STATUS: completed
  
  CONTINUE horizontal → IMPLEMENT
```

---

### Example 4: Emergency POP_ALL

**Scenario**: Deep nesting hits limit

```
🏗️ ARCHITECT → 🔬 ANALYZE → 🐛 DEBUG → 🏗️ ARCHITECT → 🔬 ANALYZE → (depth 5 MAX)

🔄 VMP PUSH (BLOCKED)
STACK: 🏗️ ARCHITECT ← 🔬 ANALYZE ← 🐛 DEBUG ← 🏗️ ARCHITECT ← 🔬 ANALYZE (depth:5 MAX_REACHED)
MODE: 🔬 ANALYZE
ATTEMPT: PUSH DEBUG
WARNING: Maximum vertical depth reached, cannot nest deeper

BLOCKER: Circular vertical dependency detected (ANALYZE ↔ DEBUG ↔ ARCHITECT loop)
ACTION: Emergency POP_ALL required

🔄 VMP POP_ALL
STACK: [empty] (depth:0 EMERGENCY_COLLAPSE)
MODE: LOG
REASON: max_depth_circular_dependency
STATUS: partial_workflow_vertical_collapsed

Vertical exploration incomplete due to circular dependencies between phases.
Artifacts collected:
- Level 1 ARCHITECT: [API design with rate limiting]
- Level 2 ANALYZE: [JWT authentication pattern]
- Level 3 DEBUG: [singleton coupling issue]
- Level 4 ARCHITECT: [DI refactor needed]
- Level 5 ANALYZE: [blocked attempting to re-analyze original issue]

Recommendation: Break into separate workflows, address architectural issues first

ACTION: LOG partial workflow, create TODO for architectural cleanup
```

---

## LOG Template Extension

**Standard LOG** (unchanged for horizontal workflows)

**VMP-Enhanced LOG** (when stack used):

```markdown
# Workflow Log: [Feature]
**Date**: YYYY-MM-DD HH:MM:SS | **Status**: [Completed|Partial|Failed]

## Tasks: [standard_phase_list]

## Vertical Stack Trace (VMP)
**Max Depth Reached**: 3
**Total Vertical Transitions**: 7 (4 PUSH, 3 POP)

### Stack Evolution:
1. **ARCHITECT (depth:0)** → PUSH ANALYZE (depth:1) [trigger: requirement_gap]
2. **ANALYZE (depth:1)** → PUSH DEBUG (depth:2) [trigger: investigation_needed]
3. **DEBUG (depth:2)** → POP ANALYZE (depth:1) [resolved: JWT pattern confirmed]
4. **ANALYZE (depth:1)** → POP ARCHITECT (depth:0) [resolved: auth scope clarified]
5. **ARCHITECT (depth:0)** → CONTINUE horizontal → IMPLEMENT

### Vertical Discoveries by Stack Level:
- **Depth 1 (ANALYZE)**: [JWT standard across codebase, 15 modules use auth.jwt_handler]
- **Depth 2 (DEBUG)**: [Runtime trace confirms JWT with refresh token pattern]

## CEPH Evolution [standard]
## Phase Completions [standard]
## Learnings [standard + vertical pattern learnings]
## Artifacts [standard]
## Patterns [standard + stack management patterns]
```

---

## Communication Standards

### Phase Indicators (Extended)

**Horizontal** (unchanged):
```
📋 PLAN → 🧠 REMEMBER → 🔍 ASSESS → 🔬 ANALYZE → 🏗️ ARCHITECT → 
💻 IMPLEMENT → 🐛 DEBUG → 🧪 TEST → 🎓 LEARN → 📚 DOCUMENT → 📝 LOG
```

**Vertical Stack Notation**:
```
🔄 VMP PUSH → 🏗️ ARCHITECT ← 🔬 ANALYZE ← 🐛 DEBUG (depth:3)
           ↑
      Use ← for breadcrumb trail
```

---

## Error Recovery (Extended)

**Test Failures** (updated with VMP):
```
TEST (encounters failure) 
  → VMP PUSH DEBUG (re-hypothesis, mandatory)
    → DEBUG (fix root cause)
      → POP TEST (verify)
        → IF pass → CONTINUE horizontal → LEARN
        → IF fail → Check failure type:
            ├─ Logic error → Stay in DEBUG, iterate
            ├─ Design flaw → VMP PUSH ARCHITECT
            └─ Requirement mismatch → VMP PUSH ANALYZE
```

**Blocked Phase** (updated with VMP):
```
Any phase (blocker detected)
  → Check trigger pattern
    → IF anomaly → VMP PUSH ANALYZE
    → IF investigation → VMP PUSH DEBUG
    → IF design flaw → VMP PUSH ARCHITECT
    → IF requirement gap → VMP PUSH ANALYZE
    → IF no pattern → Document in BLOCKERS, skip to LOG
```

**Vertical Stack Blocked**:
```
Current vertical mode (blocked + no resolution)
  → VMP PEEK parent stack
    → IF parent can help → POP with blocker status
    → IF parent also blocked → POP_ALL to depth 0
    → IF depth = 5 → Emergency POP_ALL
```

---

## Backward Compatibility

**Unchanged Behavior**:
- All 11 phases execute identically when no vertical transitions occur
- Horizontal workflow (depth 0) unchanged
- Phase completion format same (STACK field optional)
- Memory/Codegraph loading unaffected
- CEPH evolution continues normally
- Task tracking same manage_todo_list

**New Behavior** (Only When Triggered):
- VMP blocks emit only when PUSH/POP/PEEK detected
- STACK field appears only when depth ≥ 1
- LOG template includes vertical trace only if stack used
- Error recovery routes through vertical phases when appropriate

---

## Summary

**VMP Adds**:
- 📍 Stack-based vertical phase transitions (PUSH/POP/PEEK)
- 📍 Auto-detection triggers (6 patterns)
- 📍 Breadcrumb navigation (visual stack trail)
- 📍 Safety limits (max depth 5, emergency POP_ALL)
- 📍 CEPH accumulation across stack
- 📍 LOG template extension for vertical traces

**VMP Preserves**:
- ✅ All 11 horizontal phases unchanged
- ✅ Phase completion format (STACK optional)
- ✅ Memory system (4-layer hierarchy)
- ✅ Quality gates (100% test pass)
- ✅ IRP for simple interruptions
- ✅ Workflow adaptability

**Lines Added**: ~120 lines to DevTeam.chatmode.md  
**Breaking Changes**: None  
**Complexity**: Minimal (extends existing patterns)

---

**END OF VMP SPECIFICATION DRAFT**
