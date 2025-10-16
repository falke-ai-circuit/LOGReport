---
applyTo: '**'
---

# DevTeam Protocol Examples & Reference

**Companion to**: protocols.md (core specifications)

## SCP Examples

**Session Start**: `[SCP-START: ✅LOADED:[chatmode,phases,protocols,standards,structure,examples,document_update_system] | ✅COMPLIANT:[Memory-First,Codegraph-Driven,11-phase,Quality-Gates] | 🎯READY:DevTeam]`

**Session End (LOG phase)**: `[SCP-END: 📊SCORE:92% | ✅FOLLOWED:[SVP:18/18,CVP:9/9,VMP:1,CEPH:yes] | 🚫VIOLATIONS:[0:critical,1:minor:incomplete_codegraph_query] | 📈QUALITY:[tests:100%,memory:4_entities,docs:3_files,queries:8] | 🔧TUNE:[phases:clarify_IMPLEMENT_query_threshold,protocols:add_VMP_timeout_guidance] | 🎓INSIGHTS:[signal_propagation_pattern,hierarchical_color_persistence]]`

## SVP Examples

**Phase Start**: `[SVP: ⚡PHASE→🔍ASSESS | 📚STACK→none | ✓TASK→2/11 | 🎯NEXT→load_codegraph]`
**Within Phase**: `[SVP: 🎯NEXT→query_class_relations]`
**VMP Push**: `[SVP: ⚡PHASE→🐛DEBUG | 📚STACK→1 (IMPLEMENT→DEBUG) | ✓TASK→blocker | 🎯NEXT→analyze_test_failure]`
**User Question**: `[SVP: 🎯NEXT→answer_user_question]`

## CEPH Evolution Example (Real Workflow)

**ASSESS**: `CEPH:[CURRENT:gap_identified | EXPECTED:feature_complete | PROBLEM:status_messages_isolated | HYPOTHESES:H1:signal_chain | EVIDENCE:existing_patterns]`

**IMPLEMENT**: `CEPH:[CURRENT:implementation_complete | EXPECTED:same | PROBLEM:same | HYPOTHESES:same | EVIDENCE:files_modified]`

**TEST**: `CEPH:[CURRENT:validated | EXPECTED:achieved | PROBLEM:resolved | HYPOTHESES:validated | EVIDENCE:tests_pass]`

## CVP Response Examples

**✅ Full Compliance**: `[CVP: ✓CHATMODE:[SVP,Memory,Codegraph,CEPH] | ✓INSTRUCTIONS:[protocols,phases,standards,structure] | 🚫VIOLATIONS:[none]]`

**⚠️ Partial**: `[CVP: ✓CHATMODE:[SVP,Memory] | ⚠️CHATMODE:[Codegraph:2/5] | 🚫VIOLATIONS:[1:insufficient_queries]]`

**❌ Failed**: `[CVP: ❌CHATMODE:[Memory:not_loaded] | ❌INSTRUCTIONS:[protocols:no_SVP] | 🚫VIOLATIONS:[2:critical]]`

## CVP Usage in Real Workflows

**Pattern**: Emit CVP as FIRST LINE before STATUS in every phase completion. Self-verify against chatmode + all 5 instruction files. Critical violations (❌) BLOCK next phase until fixed.

**Example Phase Completion with CVP**:
```
[CVP: ✓CHATMODE:[SVP,Codegraph:5/5,CEPH,LEARNINGS] | ✓INSTRUCTIONS:[protocols,phases,standards,structure] | 🚫VIOLATIONS:[none]]
STATUS: completed
PHASE: IMPLEMENT
TASKS: [x][x][x][x][x][x][ ][ ][ ][ ][ ]
...rest of completion format...
```

## Completion Format Examples

**REMEMBER Phase**:
```
[CVP: ✓CHATMODE:[SVP,Memory,VERIFIED_LOAD] | ✓INSTRUCTIONS:[protocols,phases] | 🚫VIOLATIONS:[none]]
STATUS: completed
PHASE: REMEMBER
TASKS: [x][x][ ][ ][ ][ ][ ][ ][ ][ ][ ]
MEMORY: [global_domains:47 project_entities:479]
VERIFIED_LOAD: [line_counts_reported:YES summaries_complete:YES hierarchies_valid:YES]
DISCOVERIES: Memory system well-established
BLOCKERS: none
NEXT: proceed_to_ASSESS
```

**IMPLEMENT Phase**:
```
[CVP: ✓CHATMODE:[SVP,Codegraph:5/5,CEPH,LEARNINGS] | ✓INSTRUCTIONS:[all] | 🚫VIOLATIONS:[none]]
STATUS: completed
PHASE: IMPLEMENT
TASKS: [x][x][x][x][x][x][ ][ ][ ][ ][ ]
CEPH: [CURRENT:complete | EXPECTED:ready | EVIDENCE:5_files]
LEARNINGS: [pattern:signal_propagation | approach:hierarchical_forwarding]
ARTIFACTS: [node_scan_widget.py:+20 | commander_window.py:+3]
CODEGRAPH_QUERIES: 5 (BELONGS_TO, CALLS, IMPORTS, DOCUMENTED_IN)
DISCOVERIES: Pattern reusable
BLOCKERS: none
NEXT: proceed_to_TEST
```

**TEST Phase**:
```
[CVP: ✓CHATMODE:[SVP,Tests:15/15,METRICS,USER_VERIFICATION,CEPH] | ✓INSTRUCTIONS:[protocols,phases] | 🚫VIOLATIONS:[none]]
STATUS: awaiting_user_confirmation
PHASE: TEST
TASKS: [x][x][x][x][x][x][x][ ][ ][ ][ ]
CEPH: [CURRENT:validated | EXPECTED:achieved | EVIDENCE:15/15_pass]
METRICS: tests=15/15(+15) | coverage=92%(+12%) | files=2(+2)
USER_VERIFICATION: [awaiting_confirmation:YES]
**STOPPING HERE** - Awaiting user approval before LEARN.
DISCOVERIES: Pattern works reliably
BLOCKERS: none (pending user)
NEXT: await_user_approval → proceed_to_LEARN
```
