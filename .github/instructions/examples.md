---
applyTo: '**'
---

# DevTeam Protocol Examples & Reference

**Companion to**: protocols.md (core specifications)

## SCP Examples

### Session Initialization

**SCP-START**: Load chatmode+5 → Verify Memory-First+Codegraph+multi-phase+Quality-Gates → Init NWP(index=0)+tracking → Emit `[SCP-START: ✅LOADED:[chatmode,phases,protocols,standards,structure,examples] | ✅COMPLIANT:[Memory-First,Codegraph-Driven,11-phase,Quality-Gates] | 🎯READY:DevTeam | 📚NWP:[index=0,depth=0]]`
### Phase Completion (Quality Gates)

**SCP-PHASE (compliant)**: `[SCP-PHASE: 🚫VIOLATIONS:[none] | 🔧ADJUST:[none] | 📚NWP:[index:0,phase:5/11]]`

**SCP-PHASE (warnings)**: `[SCP-PHASE: 🚫VIOLATIONS:[query_deficit:2/5_only] | 🔧ADJUST:[add_BELONGS_TO+IMPORTS+CALLS_now] | 📚NWP:[index:1,phase:5/8]]`

**SCP-PHASE (critical)**: `[SCP-PHASE: 🚫VIOLATIONS:[missing_memory:CRITICAL] | 🔧ADJUST:[load_global+project_immediately] | 📚NWP:[index:0,phase:1/11]]`

**SCP-PHASE (test failure)**: `[SCP-PHASE: 🚫VIOLATIONS:[test_failed_no_NEST:CRITICAL] | 🔧ADJUST:[emit_SCP-NWP_NEST→test_failure_now] | 📚NWP:[index:0,phase:7/11]]`

**SCP-PHASE (CEPH dropout)**: `[SCP-PHASE: 🚫VIOLATIONS:[CEPH_dropout:missing_EXPECTED] | 🔧ADJUST:[restore_from_previous_response] | 📚NWP:[index:0,phase:4/11]]`

### NWP Transitions

**NEST**: `[SCP-NWP: 🔄NEST→test_failure | 📚INDEX:[0→1] | 🎯REASON:validation_failed | 📍FROM:IMPLEMENT | 🗂️PHASES:[1,2,6,7,8]]`

**RETURN**: `[SCP-NWP: 🔄RETURN←test_failure | 📚INDEX:[1→0] | ✅RESOLVED | 📍RESUME:IMPLEMENT | 🔄MERGE:[CEPH+fix]]`

**NEST (nested)**: `[SCP-NWP: 🔄NEST→user_request | 📚INDEX:[1→2] | 🎯REASON:architecture_question | 📍FROM:DEBUG | 🗂️PHASES:[2,3,7,8]]`

**RETURN (nested)**: `[SCP-NWP: 🔄RETURN←user_request | 📚INDEX:[2→1] | ✅RESOLVED | 📍RESUME:DEBUG | 🔄MERGE:[CEPH+insights]]`
### Manual Status & Session End

**SCP-CHECK**: `[SCP-CHECK: 📊PHASE:IMPLEMENT | ✅STATUS:in_progress | 📚INDEX:0 | 🗂️STACK:0 | 🎯NEXT:complete_validation]` | Nested: `[SCP-CHECK: 📊PHASE:DEBUG | ✅STATUS:investigating | 📚INDEX:1 | 🗂️STACK:1 | 🎯NEXT:test_H2]`

**SCP-END**: `[SCP-END: 📊SCORE:92% | ✅FOLLOWED:[SCP-PHASE:9/9,NWP:1,CEPH:yes] | 🚫VIOLATIONS:[0:critical,1:minor:incomplete_query] | 📈QUALITY:[tests:100%,memory:4_entities,docs:3_files,queries:8] | 🔧TUNE:[phases:clarify_IMPLEMENT_threshold] | 🎓INSIGHTS:[signal_propagation] | 💬COMMIT:"fix(classifier): implement pattern-priority logic" | 📚NWP:[nested_count:1,max_depth:1,total_phases:17]]`

## NWP Stack Example

**Single Nesting**: IMPLEMENT (5/11, 60%) → Test fail → nested DEBUG → fix → return → IMPLEMENT (80%)
```
[SCP-NWP: 🔄NEST→test_failure | 📚INDEX:[0→1] | 🎯REASON:validation_failed | 📍FROM:IMPLEMENT | 🗂️PHASES:[1,2,6,7,8]]
↓ Nested (index=1): REMEMBER→ASSESS→DEBUG→TEST→LEARN
[SCP-NWP: 🔄RETURN←test_failure | 📚INDEX:[1→0] | ✅RESOLVED | 📍RESUME:IMPLEMENT | 🔄MERGE:[CEPH+fix]]
↓ Resume root (index=0): IMPLEMENT → continue
```

**Multi-Level**: Root→DEBUG→ASSESS→back DEBUG→back Root
```
[SCP-NWP: NEST→test_failure | INDEX:[0→1] | FROM:IMPLEMENT | PHASES:[1,2,6,7,8]]
  [SCP-NWP: NEST→repeated_failures | INDEX:[1→2] | FROM:DEBUG | PHASES:[1,2,3,7,8]]
    ↓ index=2: deeper investigation
  [SCP-NWP: RETURN←repeated_failures | INDEX:[2→1] | RESUME:DEBUG | MERGE:[CEPH+insights]]
[SCP-NWP: RETURN←test_failure | INDEX:[1→0] | RESUME:IMPLEMENT | MERGE:[CEPH+fix]]
```

**State Preservation**: NEST captures {phase, progress:"60%", CEPH, context:"validation_layer"} → RETURN merges {CEPH:updated, learnings:3, artifacts:fix.py} → Resume exactly where paused
## CEPH Evolution Example

`ASSESS:[CURRENT:gap | EXPECTED:complete | PROBLEM:isolated | HYPOTHESES:H1:chain | EVIDENCE:patterns]`  
`IMPLEMENT:[CURRENT:done | EXPECTED:same | PROBLEM:same | HYPOTHESES:same | EVIDENCE:+files]`  
`TEST:[CURRENT:validated | EXPECTED:achieved | PROBLEM:resolved | HYPOTHESES:validated | EVIDENCE:pass]`

## NWP Patterns

**DEBUG (5)**: Test fail → NEST → REMEMBER→ASSESS→DEBUG→TEST→LEARN → RETURN  
**ARCHITECT (8)**: Design flaw → NEST → REMEMBER→ASSESS→ANALYZE→ARCHITECT→IMPLEMENT→TEST→LEARN→DOC → RETURN  
**Query (3)**: Question → NEST → ASSESS→answer→LEARN → RETURN  
**Multi-nested**: Root→DEBUG nested→ASSESS nested→back→back

## SCP-PHASE Patterns

**Query Deficit**: `[SCP-PHASE: ✓CEPH | ✓Codegraph:1/5 | 🚫1:insufficient | 🔧add_BELONGS_TO+IMPORTS+CALLS | 📚NWP:[index:1,phase:5/8]]` → Need 2 more

**Missing Verify**: `[SCP-PHASE: ✓Memory | ✓protocols:no_VERIFIED_LOAD | 🚫1:critical | 🔧add_line_counts+summaries | 📚NWP:[index:0,phase:1/11]]` → VERIFIED_LOAD missing

**Format Error**: `[SCP-PHASE: ✓CEPH | ✓standards:LEARNINGS_wrong | 🚫1:format | 🔧rewrite_pattern_approach | 📚NWP:[index:1,phase:3/8]]` → Current: LEARNINGS:[Used DI] | Required: [pattern:DI|approach:constructor]

**CEPH Dropout**: `[SCP-PHASE: ✓[] | ✓CEPH:missing | 🚫1:dropout | 🔧restore | 📚NWP:[index:0,phase:4/11]]` → Evolution stopped

**Usage**: Emit first at phase end → self-verify vs chatmode+5 → ADJUST corrects drift → Critical BLOCKS next

**Field Validation**: `[SCP-PHASE: 🚫VIOLATIONS:[mandatory_fields_missing:STATUS,NEXT] | 🔧ADJUST:[add_required_fields_now] | 📚NWP:[index:0,phase:5/11]]` → STATUS/NEXT missing

**Structure Error**: `[SCP-PHASE: 🚫VIOLATIONS:[bracket_mismatch:protocol_tag] | 🔧ADJUST:[fix_structure:(SCP-PHASE→[SCP-PHASE]] | 📚NWP:[index:1,phase:3/8]]` → Used (SCP-PHASE) not [SCP-PHASE]

## Completion Examples

**REMEMBER**: `[SCP-PHASE: 🚫VIOLATIONS:[none] | 🔧ADJUST:[none] | 📚NWP:[index:0,phase:1/11]]`  
`STATUS: complete | PHASE: 1/11 REMEMBER | WORKFLOW: index=0, depth=0`  
`MEMORY: [global:47_lines project:479_lines] | VERIFIED_LOAD: [line_counts:YES summaries:YES hierarchies:YES]`  
`DISCOVERIES: Memory established | BLOCKERS: none | NEXT: ASSESS`

**REMEMBER (corrupted)**: `[SCP-PHASE: 🚫VIOLATIONS:[project_memory_corrupted_L37-86] | 🔧ADJUST:[ran_repair_script→kept_36+added_19=55_total] | 📚NWP:[index:0,phase:1/11]]`  
`STATUS: complete | PHASE: 1/11 REMEMBER | WORKFLOW: index=0, depth=0`  
`MEMORY: [global:47 project:55(repaired)] | VERIFIED_LOAD: [line_counts:YES summaries:YES hierarchies:YES]`  
`DISCOVERIES: Corrupted JSON repaired via Python script | BLOCKERS: none | NEXT: ASSESS`

**IMPLEMENT**: `[SCP-PHASE: 🚫VIOLATIONS:[none] | 🔧ADJUST:[none] | 📚NWP:[index:0,phase:5/11]]`  
`STATUS: complete | PHASE: 5/11 IMPLEMENT | WORKFLOW: index=0, depth=0`  
`CEPH: [CURRENT:complete | EXPECTED:ready | EVIDENCE:5_files]`  
`LEARNINGS: [pattern:signal_propagation | approach:hierarchical_forwarding]`  
`ARTIFACTS: [node_scan_widget.py:+20 | commander_window.py:+3] | CODEGRAPH_QUERIES:[5/5:Signatures,IMPORTS,BELONGS_TO,CALLS,Naming]`  
`DISCOVERIES: Pattern reusable | BLOCKERS: none | NEXT: TEST`

**TEST (pass)**: `[SCP-PHASE: 🚫VIOLATIONS:[none] | 🔧ADJUST:[none] | 📚NWP:[index:0,phase:7/11]]`  
`STATUS: awaiting | PHASE: 7/11 TEST | WORKFLOW: index=0, depth=0`  
`CEPH: [CURRENT:validated | EXPECTED:achieved | EVIDENCE:15/15_pass] | METRICS: tests=15/15(+15)|coverage=92%(+12%)|files=2(+2)`  
`**CHECKPOINT: Tests passing. Verify...** | **STOPPING** | USER_VERIFICATION: [awaiting:YES]`  
`BLOCKERS: none(pending user) | NEXT: approve→LEARN | reject→NEST`

**TEST (fail→NEST)**: `[SCP-PHASE: 🚫VIOLATIONS:[test_failed:3/15] | 🔧ADJUST:[NEST→DEBUG_required] | 📚NWP:[index:0,phase:7/11]]`  
`STATUS: failed | PHASE: 7/11 TEST | WORKFLOW: index=0, depth=0`  
`METRICS: tests=12/15(+15:3_fail)|coverage=85%(+8%)|files=2(+2)`  
`BLOCKERS: validation_failed:test_comparison_processor.py | NEXT: NEST→DEBUG`  
`[SCP-NWP: 🔄NEST→test_failure | 📚INDEX:[0→1] | 🎯REASON:validation_failed | 📍FROM:TEST | 🗂️PHASES:[1,2,6,7,8]]`

**DEBUG (Nested)**: `[SCP-NWP: 🔄NEST→test_failure | 📚INDEX:[0→1] | 🎯REASON:validation_failed | 📍FROM:TEST | 🗂️PHASES:[1,2,6,7,8]]`  
`[SCP-PHASE: 🚫VIOLATIONS:[none] | 🔧ADJUST:[none] | 📚NWP:[index:1,phase:6/8]]`  
`STATUS: in_progress | PHASE: 6/8 DEBUG | WORKFLOW: index=1, depth=1`  
`STACK: [root:TEST]→[nested:DEBUG]`  
`CEPH: [HYPOTHESES:H1:null_input→AttributeError→add_check H2:timing→race→sync] | CODEGRAPH_QUERIES:[3/4:CALLS,IMPORTS,implementations]`  
`LEARNINGS: [pattern:null_handling | approach:defensive_checks]`  
`EXECUTION_TRACE: [chain:compare_entities→get_dxf_attribute→AttributeError] | DISCOVERIES: Missing null check line 113 | NEXT: fix→TEST→RETURN`  
`[SCP-NWP: 🔄RETURN←test_failure | 📚INDEX:[1→0] | ✅RESOLVED | 📍RESUME:TEST | 🔄MERGE:[CEPH+fix]]`

**Auto-finalize**: User "looks good" → LEARN→DOCUMENT→LOG