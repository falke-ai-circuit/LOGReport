# Memory & Codegraph Load Verification

**Purpose**: Ensure complete file loading in REMEMBER and ASSESS phases of DevTeam Mode  
**Created**: 2025-10-13  
**Status**: Active

## Overview

DevTeam Mode requires full loading of memory and codegraph files to prevent context loss and ensure all knowledge is available throughout the workflow. This document provides the verification format and expected outputs.

## File Inventory

| File | Lines | Entities | Purpose |
|------|-------|----------|---------|
| `global_memory.json` | ~120 | ~60 entities + ~60 relations | Cross-project reusable patterns |
| `project_memory.json` | ~450 | ~450 entities | Project-specific knowledge |
| `codegraph.json` | ~308 | ~150 modules/classes + ~150 relations | Codebase structure & dependencies |

## Verification Format

### REMEMBER Phase (Phase 1)

**Load Requirements**:
- Read `global_memory.json` completely (all 120 lines)
- Read `project_memory.json` completely (all 450 lines)
- Extract last 2 entries from each file
- Report hierarchies to prove complete load

**Example Completion**:
```
STATUS: completed
PHASE: REMEMBER
MEMORY:[
  global_entities:60 global_patterns:Pattern.* | 
  project_entities:450 project_domains:Testing.Coverage.Feature | 
  clusters_loaded:[Testing,Implementation,Architecture] | 
  docs_reviewed:[README.md,CHANGELOG.md,TODO.md] | 
  workflows_analyzed:5 | 
  VERIFIED_LOAD:[
    global_last:"Global.Domain.Workflows" 
    project_last:"Project.Testing.Coverage.Feature_Phase2TestSuiteQuality" 
    confirms_complete:YES
  ]
]
```

**Last Entries Expected**:
- **global_memory.json** (line 120): `Global.Domain.Workflows` relation
- **project_memory.json** (line 448): `Project.Testing.Coverage.Feature_Phase2TestSuiteQuality`

### ASSESS Phase (Phase 2)

**Load Requirements**:
- Read `codegraph.json` completely (all 308 lines)
- Extract last 2 Module entries
- Report hierarchy to prove complete load
- Test query to confirm context accessibility

**Example Completion**:
```
STATUS: completed
PHASE: ASSESS
CEPH:[
  CURRENT:[LOGReport PyQt5 app, 448 project entities, 308 codegraph entities] | 
  EXPECTED:[Enhanced memory verification] | 
  PROBLEM:[Inconsistent memory loading] | 
  HYPOTHESES:[H1:Partial file reads→missing context→incomplete analysis]
]
CODEGRAPH:[
  loaded:YES modules:80 classes:70 methods:150 relations:150 | 
  VERIFIED_LOAD:[
    codegraph_last:"Code.Tests.Unit.Module_test_token_detection" 
    confirms_complete:YES
  ]
]
CODEGRAPH_REFS:[
  modules:[node_tree_presenter,telnet_service,bstool_worker] | 
  classes:[NodeTreePresenter,TelnetService,BsToolWorker] | 
  relevant_relations:25
]
```

**Last Module Entries Expected**:
- **codegraph.json** (line 306): `Code.Tests.Unit.Module_test_log_creator`
- **codegraph.json** (line 307): `Code.Tests.Unit.Module_test_sys_file_parser`
- **codegraph.json** (line 308): `Code.Tests.Unit.Module_test_token_detection`

## Verification in Later Phases

### Phase 3 (ANALYZE) - Query Usage
```
LEARNINGS:[
  pattern:[Sequential execution requires Telnet connection check] | 
  approach:[Query codegraph for IMPORTS relations to trace dependencies]
]
# Evidence: Referenced Project.Commander.Sequential.Feature_AutoConnect from memory
# Evidence: Queried Code.Presenter.Module_node_tree_presenter for method signatures
```

### Phase 4 (ARCHITECT) - Impact Analysis
```
IMPACT_ANALYSIS:[
  affected_modules:[node_tree_presenter,telnet_service] | 
  downstream_dependencies:3 | 
  test_surface:[NodeTreePresenter,TelnetService]
]
# Evidence: Used codegraph IMPORTS relations to identify downstream impacts
```

### Phase 5 (IMPLEMENT) - Code Patterns
```
CODE_PATTERNS:[
  similar_methods:[_ensure_debugger_connection,_validate_connection] | 
  reused_structures:5
]
# Evidence: Referenced codegraph for existing method signatures and parameter patterns
```

### Phase 6 (DEBUG) - Execution Trace
```
EXECUTION_TRACE:[
  call_chain:[process_all_nodes→_ensure_connection→telnet_service.connect] | 
  affected_classes:[NodeTreePresenter,TelnetService] | 
  dependency_issues:1
]
# Evidence: Traced CALLS relations in codegraph to understand execution flow
```

### Phase 7 (TEST) - Test Surface
```
TEST_SURFACE:[
  methods_tested:[6/6] | 
  classes_covered:[NodeTreePresenter,TelnetService] | 
  edge_cases:4
]
# Evidence: Mapped methods from codegraph to identify test coverage gaps
```

## Failure Detection & Recovery

### Symptoms of Incomplete Load

| Symptom | Cause | Recovery |
|---------|-------|----------|
| Missing last entries | Partial file read | Re-read entire file with line count verification |
| Hierarchy mismatch | Wrong file section | Verify file path and reload |
| Zero entities reported | File not found | Check workspace structure |
| Query returns no results | Context not retained | Reload file in current phase |
| Pattern not found in memory | Incomplete project_memory load | Re-read project_memory.json completely |
| Module not in codegraph | Incomplete codegraph load | Re-read codegraph.json completely |

### Recovery Steps

1. **Detect**: Check completion status for VERIFIED_LOAD field
2. **Confirm**: Verify last entry hierarchies match expected patterns
3. **Re-read**: If mismatch, read entire file again (all lines)
4. **Verify**: Extract and report last entries again
5. **Proceed**: Only continue to next phase after confirmation

## Expected Hierarchy Patterns

### Global Memory
- Entities: `Global.[Domain].[Cluster].[EntityType]_[Name]`
- Relations: `Global.[Domain].[Cluster]` → `Global.[Domain]`
- Example: `Global.Domain.Workflows`, `Global.Cluster.Patterns.UI`

### Project Memory
- Entities: `Project.[Domain].[Cluster].[EntityType]_[Name]`
- Example: `Project.Testing.Coverage.Feature_Phase2TestSuiteQuality`
- Example: `Project.Commander.Sequential.Feature_AutoConnect`

### Codegraph
- Modules: `Code.[Domain].[Type].Module_[name]`
- Classes: `Code.[Domain].[Type].Class_[name]`
- Example: `Code.Tests.Unit.Module_test_token_detection`
- Example: `Code.Presenter.Module_node_tree_presenter`

## Integration with DevTeam Mode

This verification protocol is integrated into:
- **Phase 1 (REMEMBER)**: VERIFIED_LOAD field mandatory in completion
- **Phase 2 (ASSESS)**: VERIFIED_LOAD field mandatory in completion
- **Phases 3-7**: Evidence of memory/codegraph usage in learnings
- **Error Recovery**: Automatic re-load on verification failure

## Benefits

1. **Prevents Context Loss**: Ensures all knowledge available throughout workflow
2. **Detects Partial Loads**: Last entry check catches incomplete file reads
3. **Proves Completeness**: Hierarchy patterns confirm correct loading
4. **Enables Tracing**: Can verify knowledge usage in later phases
5. **Debugging Aid**: Clear evidence when memory/codegraph not loaded properly

## Example Workflow

```
Phase 1 REMEMBER:
  → Read global_memory.json (120 lines)
  → Read project_memory.json (450 lines)
  → Extract: Global.Domain.Workflows, Project.Testing.Coverage.Feature_*
  → Report: VERIFIED_LOAD confirms_complete:YES
  ✓ Continue to Phase 2

Phase 2 ASSESS:
  → Read codegraph.json (308 lines)
  → Extract: Code.Tests.Unit.Module_test_token_detection
  → Report: VERIFIED_LOAD confirms_complete:YES
  ✓ Continue to Phase 3

Phase 3 ANALYZE:
  → Query: Find Project.Commander.* patterns
  → Query: Trace Code.Presenter.* IMPORTS
  ✓ Evidence of memory/codegraph usage

Phase 5 IMPLEMENT:
  → Reference: CODE_PATTERNS from codegraph
  → Match: Method signatures from Code.Module.*
  ✓ Evidence of codegraph usage

Phase 8 LEARN:
  → Persist: 3+ entities to project_memory.json
  → Update: Module entries in codegraph.json
  → Verify: Line counts before→after
  ✓ Memory updated successfully
```

## Conclusion

The verification protocol ensures DevTeam Mode has complete context throughout all phases. By reporting last entries and hierarchy patterns in REMEMBER and ASSESS phases, we prove files were loaded completely and enable effective knowledge usage in later phases.
