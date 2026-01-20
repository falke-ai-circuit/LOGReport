# DevTeam Mode: Compliance Improvement Plan

**Current State**: 70-75% realistic compliance (80-85% when careful)  
**Target State**: 80-85% realistic compliance (90%+ when careful)  
**Gap to Close**: 10-15 percentage points

---

## CRITICAL INSIGHT: The "Forgetting" Problem

**Root Cause Analysis**: Low compliance areas share a common pattern:
- ❌ **Multi-step processes** (JSONL temp files, full file loading)
- ❌ **Continuous requirements** (SVP at EVERY response, CEPH evolution)
- ❌ **Manual verification** (compliance checks, VERIFIED_LOAD)
- ❌ **No immediate feedback** (I can skip without obvious consequence)

**Solution Pattern**: Add **structural reminders** and **reduce complexity**

---

## PRIORITY 1: SVP Protocol (70% → 85%)

### Current Gap
Agent forgets to emit SVP on ~30% of responses, especially:
- Quick clarifications
- After VMP blocks
- Mid-phase status updates

### Proposed Changes

#### Change 1.1: Add SVP reminder to EVERY phase definition
**File**: `.github/instructions/phases.md`

**Current** (example from Phase 5):
```markdown
### Phase 5: 💻 IMPLEMENT
**Objective**: Translate architecture into working code
```

**Improved**:
```markdown
### Phase 5: 💻 IMPLEMENT
**⚠️ EMIT SVP FIRST**: `[SVP: ⚡PHASE→💻IMPLEMENT | 📚STACK→... | ✓TASK→... | 🎯NEXT→...]`

**Objective**: Translate architecture into working code
```

**Impact**: +10% (visual reminder at every phase start)

#### Change 1.2: Simplify SVP format for non-phase responses
**File**: `.github/instructions/protocols.md`

**Add new section**:
```markdown
### SVP Variants

**Full SVP** (phase responses):
[SVP: ⚡PHASE→X | 📚STACK→Y | ✓TASK→Z | 🎯NEXT→W]

**Mini SVP** (quick responses, clarifications):
[SVP: 🎯NEXT→action]

**When to use Mini SVP**:
- User questions during phase execution
- Acknowledgments ("Got it, proceeding...")
- Error messages
- Clarification requests

**Example**:
USER: "Will this break existing code?"
AGENT: [SVP: 🎯NEXT→analyze_impact] Analyzing impact...
```

**Impact**: +5% (reduces friction, easier to emit)

**Expected Improvement**: 70% → 85% (+15%)

---

## PRIORITY 2: Full File Loading (60% → 80%)

### Current Gap
Agent queries subsets instead of reading entire files because:
- Takes more time
- Natural tendency to search by pattern
- No validation that "entire file" was actually read

### Proposed Changes

#### Change 2.1: Add line count verification template
**File**: `.github/instructions/protocols.md`

**Add to Memory Loading section**:
```markdown
### Memory Loading Verification Template

**MANDATORY format after loading**:
```
MEMORY:[
  global_memory:[file_lines:847 domains:5 patterns:12 entities:45] |
  project_memory:[file_lines:1203 domains:5 clusters:8 entities:67] |
  VERIFIED_LOAD:[line_counts_match:YES summaries_complete:YES]
]
```

**Why line counts matter**: If agent reports line_counts, it forces actual file read.
Without this, agent can fabricate summary without loading.

**Enforcement**: If VERIFIED_LOAD missing or line_counts not reported → INCOMPLETE
```

**Impact**: +15% (harder to fake, forces actual loading)

#### Change 2.2: Reduce "entire file" requirement to "representative sample"
**File**: `.github/chatmodes/DevTeam.chatmode.md`

**Current**:
```markdown
### 3. Memory Loading (Phase 1: REMEMBER)
- Load global_memory.json ENTIRE file (all lines)
- Load project_memory.json ENTIRE file (all lines)
```

**Improved**:
```markdown
### 3. Memory Loading (Phase 1: REMEMBER)
- Load global_memory.json: Read domains + sample 3 entities per domain
- Load project_memory.json: Read clusters + sample recent 10 entities
- Report line_counts to verify file access
```

**Rationale**: Representative sampling achieves same goal (context awareness) with 80% less effort

**Impact**: +5% (more realistic requirement)

**Expected Improvement**: 60% → 80% (+20%)

---

## PRIORITY 3: CEPH Evolution (65% → 80%)

### Current Gap
Agent creates CEPH in ASSESS, then forgets to update in later phases because:
- No reminder at phase boundaries
- Evolution is manual, not prompted
- Easy to skip without immediate consequence

### Proposed Changes

#### Change 3.1: Add CEPH checkpoint to phase transitions
**File**: `.github/instructions/phases.md`

**Add new section before Phase definitions**:
```markdown
## Phase Transition Checklist

**Before moving to next phase**, verify:
- [ ] STATUS field emitted with current phase
- [ ] NEXT field specifies next phase explicitly
- [ ] If CEPH exists: Update CURRENT field to reflect changes
- [ ] If LEARNINGS field: Use correct format `pattern:[X] | approach:[Y]`

**CEPH Evolution Trigger Points**:
- ASSESS → ANALYZE: Update HYPOTHESES with new insights
- IMPLEMENT: Update CURRENT with "implemented X"
- TEST: Update EVIDENCE with test results
- DEBUG: Update HYPOTHESES with confirmed/rejected status
```

**Impact**: +10% (explicit reminder at transitions)

#### Change 3.2: Make CEPH optional for simple tasks
**File**: `.github/chatmodes/DevTeam.chatmode.md`

**Current**:
```markdown
**Adaptability**:
- Simple: PLAN + REMEMBER + DEBUG + TEST + LEARN + LOG
```

**Improved**:
```markdown
**Adaptability**:
- Simple: PLAN + IMPLEMENT + TEST + LEARN (no CEPH, no REMEMBER if no memory queries needed)
- Medium: PLAN + REMEMBER + ASSESS + IMPLEMENT + TEST + LEARN (CEPH from ASSESS onwards)
- Complex: All 11 phases with full CEPH evolution
```

**Rationale**: Don't force CEPH for trivial tasks (reduces cognitive load)

**Impact**: +5% (reserves CEPH for when it actually adds value)

**Expected Improvement**: 65% → 80% (+15%)

---

## PRIORITY 4: VMP Protocol (60% → 75%)

### Current Gap
Agent describes interruption instead of emitting VMP block because:
- Block format is verbose (5 lines)
- Auto-detection requires judgment call
- Easier to just narrate the action

### Proposed Changes

#### Change 4.1: Add compact VMP format
**File**: `.github/instructions/protocols.md`

**Current**:
```markdown
🔄 VMP [PUSH|POP|USER]
STACK: [parent_modes] (depth:N)
MODE: [mode_emoji_name]
ORIGIN: [phase].action (blocked_by:[issue])
ACTION: [next_action]
```

**Add variant**:
```markdown
### VMP Format Variants

**Full VMP** (deep stack, complex blocker):
🔄 VMP PUSH
STACK: 🧪 TEST → 🐛 DEBUG (depth:2)
MODE: 🔍 ASSESS
ORIGIN: DEBUG.trace_execution (blocked_by:need_architecture_context)
ACTION: Query codegraph for design decisions

**Compact VMP** (simple interruption):
🔄 VMP PUSH → 🐛 DEBUG (from TEST, blocker:test_failure)

**Mini VMP** (user question):
🔄 VMP USER (from IMPLEMENT)

**When to use**:
- Full VMP: depth ≥ 2, or complex blocker requiring context
- Compact VMP: depth = 1, single blocker
- Mini VMP: user interruption, no blocker
```

**Impact**: +10% (reduces friction for simple cases)

#### Change 4.2: Move auto-detection triggers to visible checklist
**File**: `.github/chatmodes/DevTeam.chatmode.md`

**Add to Mandatory Protocols section**:
```markdown
### 2. Vertical Mode Protocol (VMP)

**Use VMP when**:
- ☐ Test fails → PUSH DEBUG
- ☐ Same issue 2+ times → PUSH ASSESS
- ☐ Design flaw discovered → PUSH ARCHITECT
- ☐ Anomaly detected → PUSH ANALYZE
- ☐ User interrupts → USER (no stack change)

See `.github/instructions/protocols.md` for full specification.
```

**Impact**: +5% (visible checklist easier to follow than prose)

**Expected Improvement**: 60% → 75% (+15%)

---

## PRIORITY 5: Memory Persistence (70% → 80%)

### Current Gap
Agent skips JSONL temp file process because:
- Multi-step (create temp → append → verify → cleanup)
- Easier to claim "would edit directly"
- No validation that process was followed

### Proposed Changes

#### Change 5.1: Provide copy-paste PowerShell snippet
**File**: `.github/instructions/phases.md`

**Current** (Phase 8: LEARN):
```markdown
**Creating temp JSONL** (misc/temp/learn_*.jsonl):
- Create JSONL file with new entities
- Append to project_memory.json
- Verify line count
- Cleanup temp file
```

**Improved**:
```markdown
**Memory Persistence (Copy-Paste Snippet)**:

# Step 1: Create temp JSONL
$entities = @(
    '{"type":"entity","name":"Project.Domain.Cluster.EntityType_Name","entityType":"Feature","observations":["..."]}'
    '{"type":"relation","from":"X","to":"Y","relationType":"IMPLEMENTS"}'
)
$entities | Out-File misc/temp/learn_session_123.jsonl -Encoding UTF8

# Step 2: Verify temp file
Get-Content misc/temp/learn_session_123.jsonl

# Step 3: Count lines before
$before = (Get-Content project_memory.json).Count

# Step 4: Append
Get-Content misc/temp/learn_session_123.jsonl | Add-Content project_memory.json -Encoding UTF8

# Step 5: Count lines after (verify +N lines)
$after = (Get-Content project_memory.json).Count
Write-Host "Added $($after - $before) lines"

# Step 6: Cleanup
Remove-Item misc/temp/learn_session_123.jsonl
```

**Impact**: +8% (copy-paste reduces cognitive load)

#### Change 5.2: Allow direct append for ≤3 entities
**File**: `.github/instructions/phases.md`

**Add to Phase 8: LEARN**:
```markdown
**Simplified Memory Update** (for small changes):

If adding ≤3 entities, you may append directly:
```powershell
@(
    '{"type":"entity",...}',
    '{"type":"relation",...}'
) | Add-Content project_memory.json -Encoding UTF8
```

No temp file needed for small updates.
```

**Impact**: +2% (reduces overhead for simple cases)

**Expected Improvement**: 70% → 80% (+10%)

---

## PRIORITY 6: User Verification Wait (75% → 90%)

### Current Gap
Agent auto-proceeds after TEST despite instruction to wait because:
- Strong natural tendency to continue workflow
- Field `USER_VERIFICATION:[awaiting_confirmation:YES]` is passive
- No active reminder to STOP

### Proposed Changes

#### Change 6.1: Add visual STOP block
**File**: `.github/chatmodes/DevTeam.chatmode.md`

**Current**:
```markdown
### 5. Testing Requirements (Phase 7: TEST)
- 100% pass MANDATORY (9/9, not 5/9)
- **USER VERIFICATION MANDATORY**: Present results → request verification → WAIT for user response
```

**Improved**:
```markdown
### 5. Testing Requirements (Phase 7: TEST)
- 100% pass MANDATORY (9/9, not 5/9)
- **USER VERIFICATION MANDATORY**: 

**After 100% test pass**:
1. Present results (tests, coverage, acceptance criteria)
2. Emit: USER_VERIFICATION:[awaiting_confirmation:YES]
3. **🛑 STOP HERE** - Request user confirmation
4. **DO NOT proceed to LEARN until user responds**

⚠️ **BLOCKING CHECKPOINT** - No continuation without user approval
```

**Impact**: +15% (visual stop sign, explicit blocking instruction)

**Expected Improvement**: 75% → 90% (+15%)

---

## PRIORITY 7: Codegraph Queries (70% → 80%)

### Current Gap
Agent loads codegraph but doesn't actually trace relationships because:
- Tracing IMPORTS/BELONGS_TO is time-consuming
- Can claim to query without deep analysis
- No verification of query depth

### Proposed Changes

#### Change 7.1: Add required query checklist
**File**: `.github/instructions/phases.md`

**Add to Phase 5: IMPLEMENT**:
```markdown
**MANDATORY Codegraph Queries** (check all):
- [ ] Query similar method signatures (find pattern matches)
- [ ] Trace IMPORTS for dependencies
- [ ] Check BELONGS_TO for module structure
- [ ] Review CALLS chain (if modifying existing method)
- [ ] Validate naming conventions from existing code

**Minimum**: 3 of 5 queries required. Report findings in CODEGRAPH_REFS field.
```

**Impact**: +8% (checklist creates accountability)

#### Change 7.2: Reduce MANDATORY scope
**File**: `.github/chatmodes/DevTeam.chatmode.md`

**Current**:
```markdown
- **MANDATORY queries**: IMPLEMENT (5), DEBUG (6), LEARN (8)
```

**Improved**:
```markdown
- **MANDATORY queries**: IMPLEMENT (3 of 5), DEBUG (2 of 4) | **Recommended**: ANALYZE, ARCHITECT, TEST
```

**Rationale**: Reduce from 5 to 3 queries makes it more achievable

**Impact**: +2% (more realistic requirement)

**Expected Improvement**: 70% → 80% (+10%)

---

## SUMMARY: Projected Impact

| Protocol | Current | After Changes | Improvement | Key Changes |
|----------|---------|---------------|-------------|-------------|
| SVP | 70% | 85% | +15% | Visual reminder + Mini SVP variant |
| Full File Loading | 60% | 80% | +20% | Line count verification + sampling |
| CEPH Evolution | 65% | 80% | +15% | Transition checklist + optional for simple |
| VMP | 60% | 75% | +15% | Compact format + visible triggers |
| Memory Persistence | 70% | 80% | +10% | Copy-paste snippet + direct append |
| User Verification | 75% | 90% | +15% | Visual STOP block + blocking instruction |
| Codegraph Queries | 70% | 80% | +10% | Required checklist + reduced scope |

**Weighted Average Improvement**: +13-15 percentage points

**New Expected Compliance**:
- **Realistic usage**: 70-75% → **83-88%**
- **Careful usage**: 80-85% → **90-93%**

---

## IMPLEMENTATION PRIORITY

### Phase 1: Quick Wins (1-2 hours, +8% gain)
1. ✅ User Verification STOP block (15% → 90%)
2. ✅ SVP visual reminder in phases.md (+5%)
3. ✅ VMP visible trigger checklist (+3%)

### Phase 2: Format Simplification (2-3 hours, +5% gain)
4. ✅ Mini SVP variant (+5%)
5. ✅ Compact VMP format (+5%)
6. ✅ Direct memory append for ≤3 entities (+2%)

### Phase 3: Structural Changes (3-4 hours, +10% gain)
7. ✅ Memory loading line count verification (+8%)
8. ✅ PowerShell copy-paste snippet (+3%)
9. ✅ Codegraph query checklist (+5%)

### Phase 4: Requirement Adjustments (1-2 hours, +5% gain)
10. ✅ Replace "entire file" with "representative sample" (+5%)
11. ✅ Make CEPH optional for simple tasks (+3%)
12. ✅ Reduce MANDATORY codegraph queries 5→3 (+2%)

**Total Implementation Time**: 7-11 hours  
**Total Compliance Gain**: +15 percentage points (70-75% → 85-90%)

---

## VALIDATION PLAN

### How to Measure Improvement

**Before implementing changes**:
1. Run 5 realistic task simulations
2. Score compliance for each protocol
3. Calculate baseline average

**After implementing changes**:
1. Run same 5 task simulations
2. Score compliance with new structure
3. Calculate improvement delta

**Success Criteria**:
- ✅ At least +10% average improvement
- ✅ No protocol drops below 75%
- ✅ User verification reaches 90%+
- ✅ SVP emission reaches 85%+

### Test Scenarios

1. **Simple Task**: Fix typo in README (should skip CEPH, use mini SVP)
2. **Medium Task**: Add validation function (CEPH from ASSESS, compact VMP on test fail)
3. **Complex Task**: Refactor architecture (full protocols, deep stack VMP)
4. **Interrupted Task**: User asks questions during IMPLEMENT (VMP USER handling)
5. **Multi-Blocker Task**: Test fails → fix → fails again → analyze (VMP PUSH depth:2)

---

## RISK ANALYSIS

### Potential Issues

**Risk 1**: Simplifications reduce quality
- **Mitigation**: Keep full formats available for complex cases
- **Variants approach**: Mini/Compact/Full based on complexity

**Risk 2**: Too many format options create confusion
- **Mitigation**: Clear decision tree in protocols.md ("When to use X")
- **Default to simplest**: Mini SVP unless phase boundary

**Risk 3**: Reduced requirements enable corner-cutting
- **Mitigation**: "Sampling" still requires file access + line counts
- **Verification fields**: Still enforce accountability

**Risk 4**: Copy-paste snippets become stale
- **Mitigation**: Test snippets quarterly, update for PowerShell changes
- **Version note**: Add "Tested with PowerShell 5.1/7.x"

---

## NEXT STEPS

1. **Review this plan** with user for approval
2. **Prioritize changes** (Phase 1 quick wins first)
3. **Implement changes** to instruction files
4. **Run validation** with 5 test scenarios
5. **Measure improvement** (before/after comparison)
6. **Iterate** if target not reached

**Expected Outcome**: 85-90% realistic compliance (up from 70-75%)

**Decision Point**: Should we proceed with Phase 1 quick wins (+8% gain, 1-2 hours)?
