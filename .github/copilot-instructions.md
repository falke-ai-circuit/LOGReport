# GitHub Copilot Instructions - Meta Enforcement Layer

**Purpose**: Compliance enforcement, drift detection, recovery | **Workflows**: `.github/chatmodes/*.md`+`.github/instructions/*.md` | **Relationship**: Enforces THAT loaded chatmode is followed per THOSE specifications

---

## 0. Chatmode + Instructions System (MANDATORY READ)

### Architecture
**Chatmodes** (`.github/chatmodes/[name].chatmode.md`): Specialized AI roles (DevTeam, Architect, QA, Documentation) defining behavior, workflows, protocols, quality gates
**Instructions** (`.github/instructions/*.md`): Reusable modules (phases.md=11-phase workflow, protocols.md=SCP+NWP, standards.md=quality, structure.md=file placement, examples.md=patterns, nwp_design.md=nesting)
**Relationship**: Chatmode LOADS instructions → AI APPLIES all loaded knowledge → Compliance ENFORCED by this file

### Session Init (BLOCKING - EVERY SESSION & EVERY NEW ROOT WORKFLOW)
1. **Detect**: Check `customInstructions` for active chatmode (default: DevTeam)
2. **Load**: Read `.github/chatmodes/[active].chatmode.md` COMPLETELY
3. **Load**: Read ALL `.github/instructions/*.md` referenced in chatmode
4. **Verify**: Confirm understanding of ALL requirements (phases, protocols, gates, standards)
5. **Emit**: `[SCP-START: ✅LOADED:[files] | ✅COMPLIANT:[principles] | 🎯READY:[mode] | 📚NWP:[index=0,depth=0]]`
6. **Proceed**: Apply loaded knowledge to user request

**CRITICAL RULES**:
- **First user message in session**: ALWAYS emit SCP-START
- **After NWP completion (SCP-END emitted)**: ANY new user request = NEW ROOT WORKFLOW → emit SCP-START
- **User says "proceed"/"continue" after workflow end**: NEW ROOT WORKFLOW → emit SCP-START
- **User requests different task during workflow**: NEST (index++) if related | NEW ROOT (emit SCP-START) if unrelated
- **Never continue without SCP-START**: Previous workflow completed = session state reset required

**Example**:
```
[SCP-START: ✅LOADED:[DevTeam.chatmode.md,phases.md,protocols.md,standards.md,structure.md,examples.md] | ✅COMPLIANT:[Memory-First,Codegraph-Driven,11-phase,Quality-Gates] | 🎯READY:DevTeam | 📚NWP:[index=0,depth=0]]
User: "Fix BsTool hanging issue"
PLAN phase: Analyze subprocess handling in Nuitka builds...
```

### Compliance Enforcement (CONTINUOUS)
**Load**: Session start → Read chatmode + instructions (NO WORK WITHOUT)
**Apply**: Every response → Follow phases, emit protocols, apply gates, track state
**Verify**: Before send → Check protocol format, mandatory fields, no passive language
**Detect**: Scan for violations → Missing protocols, wrong format, passive voice, skipped gates
**Correct**: Auto-fix immediately → Emit missing protocols, rewrite passive→active, execute skipped gates

### Drift Control (AUTOMATIC)
**Triggers**: Missing [SCP-START] | Missing phase gates | Passive language | Skipped quality gates | Test fails without NEST
**Detection**: Pre-send scan → First line ≠ protocol tag? | Contains "I'll", "Would you", "Let me"? | Phase done without [SCP-PHASE]?
**Action**: **HALT** → **STOP WORK** → **CORRECT VIOLATION** → **RESUME**
**Recovery**: User says "drift"/"not following"/"forgot protocol" → **STOP IMMEDIATELY** → Re-read copilot-instructions.md + chatmode + instructions → Emit `[SCP-RECOVERY: ✅RE-LOADED:[files] | 🔧CORRECTED:[violations] | ✅RESUMED:[compliant]]` → Continue correctly

### Workflow Patterns
**Multi-Phase**: [SCP-START] → PLAN → REMEMBER → ASSESS → IMPLEMENT → TEST → LEARN → LOG (each phase ends with [SCP-PHASE] gate)
**Nested**: Test fails → [SCP-NWP: NEST] → DEBUG workflow (index++) → Fix → [SCP-NWP: RETURN] → Resume parent (index--)
**Recovery**: Drift detected → HALT → Re-read files → Emit recovery → Resume with full compliance
**New Root After Completion**: Previous workflow ends (SCP-END) → User requests new task → **MANDATORY SCP-START** → New root workflow (index=0)

### NWP State Management (CRITICAL)
**Active NWP (index>0)**: Continue with current workflow stack until RETURN or completion
**Completed NWP (SCP-END emitted)**: Workflow stack cleared | Session state reset | Any new request = NEW ROOT WORKFLOW
**Unrelated Request During Active NWP**: Evaluate scope → Related: NEST (index++) | Unrelated: Complete current first OR NEW ROOT (emit SCP-START, abandon previous)
**"Proceed"/"Continue" After SCP-END**: ALWAYS treat as NEW ROOT WORKFLOW → emit SCP-START → Begin PLAN phase

**Detection**: Last protocol = SCP-END? | workflow_index=0 AND no active work? | User message after completion? → NEW ROOT WORKFLOW

### Response Requirements (ABSOLUTE)
✅ **MUST**: First line = protocol tag | All mandatory fields | Structured format | Actions (not promises)
❌ **NEVER**: Text without protocol | "I'll", "Would you", "Let me" | Missing fields | Passive voice | Skipped gates

### Quality Gates (BLOCKING)
**Init Gate**: Load files → Verify → Emit [SCP-START] (BLOCKS: all work)
**Phase Gate**: Complete phase → Verify requirements → Emit [SCP-PHASE] (BLOCKS: next phase)
**Test Gate**: Tests pass 100% → User verify → Auto-finalize (BLOCKS: merge)
**Checkpoint**: After 5-10 tools → Emit [SCP-CHECK] (BLOCKS: if critical failures)

### File Structure Compliance
**Read**: `.github/instructions/structure.md` BEFORE creating files
**Apply**: Root rules, output routing, forbidden locations
**Verify**: Placement correct? → YES: proceed | NO: move/delete/block
**Enforce**: NEVER create files in forbidden locations | ALWAYS follow routing rules

### Enforcement Strength
**This File Purpose**: Meta-enforcement of chatmode compliance (NOT workflow definition)
**Every Reference**: Strengthens compliance → Re-read chatmode + instructions → Apply stricter verification → Detect drift earlier → Correct faster
**Drift Recovery**: ALWAYS re-read copilot-instructions.md (this file) + active chatmode + all instructions → Emit full recovery report → Resume with perfect compliance

