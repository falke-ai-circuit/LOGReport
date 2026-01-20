# Codegraph Update Quick Reference

## Purpose
Unified script for updating codegraph.json - consolidates generation, optimization, documentation linking, and validation in a single 6-phase workflow.

## Usage

### Basic Update
```powershell
python scripts/update_codegraph.py
```

**Output**: codegraph.json (optimized, <100KB, with doc pointers)

### What It Does
1. **Assesses** existing codegraph
2. **Scans** src/ and docs/ directories
3. **Plans** optimization strategy
4. **Generates** optimized entity/relation graph
5. **Integrates** documentation pointers
6. **Validates** size and performance

## Output Format

### Success Criteria
- ✅ Size: <100KB (current: 23.40KB)
- ✅ Load: <1s (current: 19ms)
- ✅ Coverage: All modules mapped
- ✅ Documentation: Key entities linked to docs

### Typical Output
```
WORKFLOW COMPLETE
Time elapsed: 0.2s
Output: d:\_APP\LOGReport\codegraph.json
Status: SUCCESS ✅
```

## Codegraph Contents

### Entities (~80)
- 1 Type entity (Code.Type.Codebase)
- 4 Domain entities (Commander, Frontend, Services, Core)
- ~65 Module entities (all .py files)
- ~7 Class entities (key classes only)
- ~7 Doc entities (documentation pointers)

### Relations (~80)
- BELONGS_TO: Module→Domain, Class→Module
- INHERITS: Class→Parent (if applicable)
- DOCUMENTED_IN: Code→Doc (documentation pointers)

## Optimization Strategy

### Included
- ✅ All modules (Type/Domain/Cluster/Module hierarchy)
- ✅ Key classes: LogReportGUI, CommanderMainWindow, ContextMenuService, BsToolCommandService, NodeTreeView, NodeTreePresenter, SystemFileLoader, TokenDetector
- ✅ Documentation pointers for domains, key modules, key classes

### Excluded (for size optimization)
- ❌ Private methods (keep public/critical only)
- ❌ Utility classes (focus on core architecture)
- ❌ Method-level detail (read source for implementation)
- ❌ IMPORTS/CALLS relations (kept only BELONGS_TO/INHERITS/DOCUMENTED_IN)

### Why These Choices?
**Goal**: Navigational map that fits in memory for constant loading
**Trade-off**: Location precision over exhaustive detail
**Pattern**: Use codegraph to LOCATE → read source for DETAILS

## Documentation Integration

### Mapping Strategy
```
Code.Domain.* → ARCH_*.md (architecture)
Code.Module.* → TECH_*.md (technical)
Code.Class.* → BLUEPRINT_*.md (blueprints)
```

### Example
```json
{
  "from": "Code.Class.commander_services_context_menu_service.ContextMenuService",
  "to": "Doc:docs/blueprints/BLUEPRINT_context_menu.md",
  "relationType": "DOCUMENTED_IN"
}
```

### Navigation Pattern
1. Query codegraph for entity
2. Check for DOCUMENTED_IN relations
3. Load referenced documentation
4. Read source code for implementation

## Update Triggers

### When to Regenerate
- ✅ After feature completion (new modules/classes)
- ✅ After major refactoring (changed structure)
- ✅ After documentation updates (new ARCH/TECH/BLUEPRINT docs)
- ✅ Periodic refresh (monthly or quarterly)
- ✅ When adding key classes to codebase

### When NOT to Regenerate
- ❌ Minor code changes (method edits)
- ❌ Documentation typo fixes
- ❌ Test file updates (not in src/)
- ❌ Configuration changes

## Size Management

### Current Status
- **Size**: 23.40 KB
- **Target**: <100KB
- **Headroom**: 76.60 KB (326% under target)
- **Efficiency**: 0.3 KB per entity, 0.3 KB per relation

### If Size Exceeds Target
1. Reduce class count (keep only most critical)
2. Remove more doc pointers (keep only domain-level)
3. Further truncate observations (<18 chars)
4. Prune additional relations

### Growth Projection
- +10 modules → +3KB
- +5 classes → +2KB
- +10 doc pointers → +1KB
- **Safe growth**: Can add ~250 more entities before hitting 100KB limit

## Testing

### Validation Tests
```powershell
# Test navigation
python misc/scripts/test_navigation.py

# Test documentation pointers
python misc/scripts/test_doc_pointers.py
```

### Expected Results
- ✅ All domains navigable
- ✅ All modules mapped
- ✅ Key classes identified
- ✅ Documentation pointers functional
- ✅ Size <100KB
- ✅ Load time <1s

## Troubleshooting

### SyntaxWarning: invalid escape sequence
**Cause**: Raw string escaping issue in source files
**Impact**: File parsing skipped but codegraph still generated
**Fix**: Update source file or add to skip list

### Size Over 100KB
**Cause**: Too many entities/relations
**Fix**: Increase filtering aggressiveness in `_optimize_aggressively()`

### Missing Documentation Links
**Cause**: Doc file not found or mapping not configured
**Fix**: Add mapping to `_add_documentation_pointers()` method

### Module Count Mismatch
**Cause**: New files added or files renamed
**Fix**: Normal - regeneration will sync

## Comparison to update_memory

### Similarities
- 6-phase workflow structure
- Assess→Scan→Plan→Generate→Integrate→Validate
- Single script execution
- Size optimization focus
- Validation metrics

### Differences
| Aspect | update_memory | update_codegraph |
|--------|--------------|------------------|
| **Input** | Session context | Source code |
| **Output** | Memory entities | Code structure |
| **Size** | ~50-200KB | <100KB (target) |
| **Relations** | Semantic | Structural |
| **Update frequency** | Per session | Per feature |
| **Optimization** | Relevance | Navigability |

## Best Practices

### Maintenance Schedule
- **Daily**: Not needed (codegraph changes slowly)
- **Weekly**: Only if active development
- **Per Feature**: Run after significant changes
- **Monthly**: Recommended refresh cycle

### Quality Checks
1. Size <100KB ✅
2. Load time <1s ✅
3. All modules covered ✅
4. Key classes mapped ✅
5. Documentation linked ✅

### Integration with DevTeam Mode
```
Phase 2 (ASSESS): Load codegraph.json into context
Phase 3-7: Query codegraph for navigation
Phase 8 (LEARN): Optionally regenerate if structure changed
```

## Quick Commands

```powershell
# Update codegraph
python scripts/update_codegraph.py

# Validate size
Get-Item codegraph.json | Select-Object Name, @{N='Size(KB)';E={[math]::Round($_.Length/1KB,2)}}

# Count entities/relations
Get-Content codegraph.json | Measure-Object -Line

# Test navigation
python misc/scripts/test_navigation.py

# Test doc pointers
python misc/scripts/test_doc_pointers.py
```

## Performance Metrics

### Benchmarks
- **Generation**: 0.2s (full regeneration)
- **File I/O**: 19ms (load time)
- **Memory**: ~50KB in memory (compressed JSON)
- **Query**: <1ms (in-memory filtering)

### Scalability
- **Current**: 70 Python files → 23.40KB codegraph
- **Projected 200 files**: ~67KB codegraph (within target)
- **Projected 500 files**: ~167KB (would need optimization)

---

**Core Principle**: Single script, full workflow, optimized output. Run when structure changes, load in every session, query for navigation + documentation context.
