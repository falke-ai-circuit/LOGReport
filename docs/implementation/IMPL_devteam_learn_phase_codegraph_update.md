# DevTeam Chatmode Update: LEARN Phase Enhancement

**Date**: 2025-10-12  
**Update Type**: Process Improvement  
**Affected Phase**: Phase 8 (LEARN)

---

## Summary

Updated `DevTeam.chatmode.md` Phase 8 (LEARN) to include **standardized codegraph update process** alongside existing project_memory persistence. Previously, LEARN phase only documented appending to `project_memory.json`. Now includes explicit instructions for updating `codegraph.json` when new code files are created or significant modifications are made.

---

## Changes Made

### Before (Original LEARN Phase)
```
**Actions**: Extract learnings → create temp JSONL → append to project_memory.json → verify → cleanup
**Template**: Project memory entity format only
**Completion**: project_memory.json line count
```

### After (Enhanced LEARN Phase)
```
**Actions - Part 1**: Project Memory (learnings: Feature+Method+Pattern)
**Actions - Part 2**: Codegraph (new code: Module+Class+Methods)
**Templates**: Both project memory AND codegraph formats
**Completion**: Both project_memory.json AND codegraph.json line counts
```

---

## New Codegraph Update Process

### When to Update Codegraph
✅ **DO UPDATE**:
- NEW file created (e.g., `bstool_worker.py`) → Add Module + Class + key Methods
- MAJOR method changes (e.g., new signal forwarding method) → Add Method entity  
- NEW class added to existing module → Add Class entity

❌ **SKIP UPDATE**:
- Minor bug fixes (1-2 line changes) → Only project_memory
- Documentation-only changes → Skip codegraph

### Codegraph Format Rules

**Module Entity Format**:
```json
{"type":"entity","name":"Code.Module.{path_with_underscores}","entityType":"Module","observations":["{Brief description} | {N} class, {M} funcs, uses {frameworks}","Methods: {method1}(...), {method2}(...)","Deps: {module1}::{Class1} | {module2}::{Class2}","upd:YYYY-MM-DD,refs:0"]}
```

**Class Entity Format**:
```json
{"type":"entity","name":"Code.Class.{path}.{ClassName}","entityType":"Class","observations":["{Purpose description} | extends {BaseClass}","upd:YYYY-MM-DD,refs:0"]}
```

**Method Entity Format** (for significant methods only):
```json
{"type":"entity","name":"Code.Method.{path}.{ClassName}.{method_name}","entityType":"Method","observations":["{Purpose and signature}","{Implementation details}","{Integration notes}","upd:YYYY-MM-DD,refs:0"]}
```

**Relations** (ALWAYS include):
```json
{"type":"relation","from":"Code.Module.{path}","to":"Code.Domain.{Domain}","relationType":"BELONGS_TO"}
{"type":"relation","from":"Code.Class.{path}.{ClassName}","to":"Code.Module.{path}","relationType":"BELONGS_TO"}
{"type":"relation","from":"Code.Module.{path}","to":"Code.Module.{dependency_path}","relationType":"IMPORTS"}
```

### Key Format Constraints

1. **Concise observations**: 1-3 lines max, structure/dependencies/purpose (NOT detailed implementation)
2. **Naming convention**: `Code.Module.{path_with_underscores}` (e.g., `commander_services_bstool_worker`)
3. **Metadata**: ALWAYS end with `upd:YYYY-MM-DD,refs:0`
4. **Module structure**: 
   - Line 1: `{description} | {N} class, {M} funcs, uses {frameworks}`
   - Line 2: `Methods: {method_signatures}`
   - Line 3: `Deps: {module}::{Class} | {module}::{Class}`
5. **Match existing style**: Read codegraph.json examples first, mimic format exactly

---

## Example: BsTool Signal Forwarding (2025-10-12 Session)

### What We Did ✅ CORRECT
Created `codegraph_additions_signal_forwarding.jsonl`:
```json
{"type":"entity","name":"Code.Module.commander_services_bstool_worker","entityType":"Module","observations":["QRunnable worker for synchronous BsTool execution | 1 class, 1 func, uses PyQt5","Methods: run()","Deps: command_queue::CommandWorkerSignals","upd:2025-10-12,refs:0"]}
{"type":"entity","name":"Code.Class.commander_services_bstool_worker.BsToolWorker","entityType":"Class","observations":["QRunnable worker for BsTool command execution in thread pool | extends QRunnable","upd:2025-10-12,refs:0"]}
{"type":"relation","from":"Code.Module.commander_services_bstool_worker","to":"Code.Domain.Commander","relationType":"BELONGS_TO"}
```

**Why Correct**:
- ✅ Concise observations (1-2 lines)
- ✅ Metadata included (`upd:2025-10-12,refs:0`)
- ✅ Module format: description | counts | framework
- ✅ Class format: purpose | base class
- ✅ Relations: BELONGS_TO added

### What We Initially Did Wrong ❌
First attempt had:
```json
{"type":"entity","name":"Code.Module.commander_services_bstool_worker","entityType":"Module","observations":["QRunnable worker for synchronous BsTool execution | 1 class, 194 lines, uses subprocess+tempfile","Key methods: __init__(bstool_path, bstool_args, log_file_path, token, env), run() executes BsTool subprocess with 10s timeout","Implementation: stdin=DEVNULL (BsTool interactive), stdout/stderr redirected to tempfile, content-based success (file size check not return_code)","Signal flow: Emits CommandWorkerSignals.command_completed(command, result, success, token) → forwarded to CommandQueue","Timeout behavior: 10s timeout expected for interactive BsTool, logs as INFO not WARNING, terminates process gracefully","Content validation: success=True if tempfile has content (os.path.getsize > 0), success=False if empty/timeout","Deps: subprocess, os, tempfile, logging | PyQt5.QtCore::QRunnable | command_queue::CommandWorkerSignals","created:2025-10-12,modified:2025-10-12,refs:0"]}
```

**Why Wrong**:
- ❌ Too verbose (8 observation lines, should be 3 max)
- ❌ Implementation details in codegraph (belongs in project_memory)
- ❌ Wrong metadata format (`created:...` should be `upd:...`)
- ❌ Didn't match existing codegraph style

---

## Rationale for Update

**Problem**: Previous LEARN phase only documented project_memory.json updates. When code changes occurred, codegraph updates were ad-hoc and inconsistent with existing format.

**Solution**: Standardize codegraph updates in LEARN phase with:
1. Clear templates matching existing format
2. Explicit format rules (concise, metadata, naming)
3. Decision criteria (when to update vs skip)
4. Examples showing correct vs incorrect approaches

**Benefits**:
- Consistent codegraph format across all updates
- Clear guidance for AI agents on when/how to update codegraph
- Reduces manual cleanup of incorrectly formatted entries
- Maintains codegraph quality as codebase evolves

---

## Impact on Future Workflows

**All future LEARN phases will**:
1. Update **both** project_memory.json (learnings) AND codegraph.json (code structure)
2. Follow standardized format templates
3. Apply decision criteria (new files = yes, minor fixes = no)
4. Verify both file line counts increased
5. Match existing codegraph style by reading examples first

**Completion format updated**:
```
MEMORY:[entities:[3+:names] | project_memory:[+N_lines] | codegraph:[+M_lines] | verified:[before→after_counts]]
```

---

## Validation

Updated chatmode validated against:
- ✅ Existing codegraph.json format (lines 1-299)
- ✅ This session's corrected format (BsTool worker example)
- ✅ 4-layer hierarchy rules from memory system
- ✅ DevTeam workflow principles (standardization, quality, maintainability)

---

## Conclusion

Phase 8 (LEARN) now provides complete guidance for persisting both **conceptual learnings** (project_memory.json) and **code structure** (codegraph.json) in standardized formats. This ensures memory systems remain consistent, high-quality, and maintainable as the codebase evolves.
