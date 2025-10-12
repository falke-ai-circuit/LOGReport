# Update Codegraph Workflow

**Purpose**: Codebase mapping for impact detection, debugging, and navigation | **Output**: codegraph.json (<100KB, minimal, precise) | **Structure**: 4-layer hierarchy with relations | **Critical**: Size-optimized for constant memory loading across all sessions

## 6-Phase Architecture

| Phase | Type | Objective | Output |
|-------|------|-----------|--------|
| 1 | Analysis | Assess existing codegraph | Structure inventory + delta |
| 2 | Analysis | Scan codebase + docs | Pattern connections |
| 3 | Analysis | Plan update strategy | Generation plan |
| 4 | Implementation | Generate + enrich graph | Enhanced codegraph |
| 5 | Implementation | Integrate documentation | Connected graph |
| 6 | Implementation | Validate + optimize | Minimal precision graph |

## Parameters

**Input**: src/ + docs/ + codegraph.json (existing) | **Output**: codegraph.json (minimal, loadable) | **Hierarchy**: Type→Domain→Module→Class | **Relations**: INHERITS, BELONGS_TO, DOCUMENTED_IN, IMPORTS | **Target**: <100KB for constant loading, ≥90% precision, ≤2 hops navigation | **Critical**: Must remain small enough to load in every session without token budget impact

## Phase Details

### Phase 1: Assessment
```
→ Load existing codegraph.json
→ Analyze entity/relation coverage
→ Identify outdated modules (deleted/renamed files)
→ Detect missing connections + bloat
→ Calculate precision metrics
```

### Phase 2: Analysis
```
→ Scan src/ (modules, classes)
→ Extract inheritance relationships
→ Parse docs/ (architecture, technical, blueprints)
→ Map features→code, architecture→implementation
→ Identify critical paths + impact surface
```

### Phase 3: Planning
```
→ Full regeneration vs incremental update
→ Documentation→code connection mapping
→ Optimal detail level (navigability vs size)
→ Size optimization targets (<100KB for constant loading)
→ Balance: precision vs token budget efficiency
```

### Phase 4: Generation
```
→ Run generator: extract entities + create relations
→ Build hierarchy: Type→Domain→Module→Class
→ Filter observations: only keep functional descriptions
→ Remove generic noise: "Module: X", "File", "Class: X"
```

### Phase 5: Integration
```
→ Link docs/architecture/*.md → Code.Domain.* (DOCUMENTED_IN relations)
→ Link docs/technical/*.md → Code.Module.* (DOCUMENTED_IN relations)
→ Link docs/blueprints/*.md → Code.Class.* (DOCUMENTED_IN relations)
→ Create Doc entities for referenced documentation files
→ Annotate entity observations with doc references (doc:FILENAME.md)
→ Establish bidirectional navigation: code→docs and docs→code
```

### Phase 6: Validation
```
→ Validate: all modules covered, critical relations present
→ Test: impact detection, navigation, data flow tracing
→ Optimize: remove redundant, compress observations, aggressive size reduction
→ Verify: <100KB size (constant loading requirement), ≥90% precision, ≤1s load time
→ Token efficiency: ensure codegraph fits within 5-10% of typical session budget
```

## Codegraph Structure

**4-Layer Hierarchy**: Type → Domain → Module → Class

**Relations**: 
- INHERITS (class hierarchy)
- BELONGS_TO (structural hierarchy)
- DOCUMENTED_IN (documentation pointers)
- IMPORTS (module dependencies)

**Entity Types**: Code entities (Type/Domain/Module/Class) + Documentation entities (Doc:path/to/file.md)

**Entity Format**:
```json
{
  "type": "entity",
  "name": "Code.Module.sys_file_loader",
  "entityType": "Module",
  "observations": [
    "Loads system log files, detects tokens, validates format",
    "doc:TECH_token_management.md",
    "upd:2025-10-11,refs:0"
  ]
}
```

**Class Format**:
```json
{
  "type": "entity",
  "name": "Code.Class.context_menu_service.ContextMenuService",
  "entityType": "Class",
  "observations": [
    "Manages right-click menu actions for node tree: edit/delete/validate",
    "doc:BLUEPRINT_context_menu.md",
    "upd:2025-10-11,refs:0"
  ]
}
```

**Documentation Pointer**:
```json
{
  "type": "relation",
  "from": "Code.Class.context_menu_service.ContextMenuService",
  "to": "Doc:docs/blueprints/BLUEPRINT_context_menu.md",
  "relationType": "DOCUMENTED_IN"
}
```

**Module Dependency**:
```json
{
  "type": "relation",
  "from": "Code.Module.commander_main_window",
  "to": "Code.Module.commander_services_status_service",
  "relationType": "IMPORTS"
}
```

**Query Examples**:
```python
# Forward dependencies: What does X import?
Query: from="Code.Module.X" AND relationType="IMPORTS"
Result: List of modules that X depends on

# Reverse dependencies: What imports X? (Impact analysis!)
Query: to="Code.Module.X" AND relationType="IMPORTS"  
Result: List of modules that depend on X (refactoring impact surface)

# Circular dependencies: Detect import cycles
Query: Follow IMPORTS chain, detect if path returns to origin
Result: Circular dependency warning
```

## Use Cases

| Use Case | Query Pattern | Result |
|----------|---------------|--------|
| **Feature Location** | Pattern: `*service*` or `*presenter*` | Navigate user feature to implementation |
| **Architecture** | Code.Domain.X → BELONGS_TO | System structure by domain |
| **Dependencies** | Code.Module.X → IMPORTS | What does module X depend on? |
| **Impact Analysis** | Code.Module.X ← IMPORTS | What modules depend on X? (refactoring safety) |
| **Refactoring** | Code.Class.X → reverse relations | Complete impact surface for safe changes |
| **Documentation** | Code.Entity.X → DOCUMENTED_IN | Pointer to detailed explanations |
| **Context Enrichment** | Doc:*.md → reverse DOCUMENTED_IN | Find code entities explained in doc |

## Output Formats

**Analysis (1-3)**:
```
PHASE: [1-3/6] Analysis
ASSESSMENT: entities:[N] relations:[N] gaps:[list] outdated:[list]
SCAN: modules:[N] classes:[N]
DOCS: arch:[N] tech:[N] blueprints:[N]
DELTA: new:[N] removed:[N] changed:[N] size:[KB]
READINESS: [ready|refine|validate]
```

**Implementation (4-6)**:
```
PHASE: [4-6/6] Implementation
ACTION: [generate|enrich|integrate|validate|optimize]
OUTPUT: entities:[N] relations:[N] size:[KB]
VALIDATION: coverage:[%] precision:[%] nav_depth:[avg] load:[ms]
```

## Quality Metrics

| Metric | Target | Validation |
|--------|--------|------------|
| Entity Coverage | 100% modules | Module count verification |
| Relation Completeness | ≥90% critical | Sample query testing |
| Navigation Efficiency | ≤2 hops | Feature location testing |
| Impact Accuracy | ≥95% | Refactoring validation |
| File Size | ≤100KB | Compression check |
| Load Performance | ≤1s | Memory timing |
| Precision | ≥90% | Query relevance |

## Optimization Strategies

**Size (Critical for Constant Loading)**: Truncate observations (50-80 chars), remove generic observations ("Module: X", "File"), keep only functional descriptions, prune redundant relations, eliminate noise, prioritize navigational value  
**Precision**: Link architectural patterns, tag high-impact entities  
**Performance**: Optimize hierarchy traversal, cache common queries  
**Token Budget**: Target 15-25KB range (3,000-6,000 tokens) to ensure codegraph loadable in every session without budget concerns

## Workflow Integration

**Load Pattern**: Load codegraph.json at EVERY session initialization → keep in memory for full session → query for analysis/debugging/impact detection | **Size requirement ensures constant availability without token budget penalties**

**Usage**: Query for dependencies → analyze impact → reference patterns → trace execution → map test surface → follow DOCUMENTED_IN pointers for detailed explanations

**Update Triggers**: Feature completion, major refactoring, periodic refresh, documentation sync, architecture changes | **Always verify size remains <100KB after updates**

**Update Script**: `scripts/update_codegraph.py` - Unified 6-phase workflow (assess→scan→plan→generate→integrate→validate) | Similar pattern to update_memory.py

**Execution**: `python scripts/update_codegraph.py` → runs all phases → validates size <100KB → outputs codegraph.json

**Core Principle**: Minimal navigable map for impact detection + debugging + feature location + documentation pointers. Size-optimized for constant loading across all sessions. Query to find locations, follow pointers to docs, read source for implementation details.

---

## Implementation Reference

**Unified Script**: `scripts/update_codegraph.py`
- **Phase 1**: Assess existing codegraph (entities, relations, size)
- **Phase 2**: Scan codebase (src/*.py) + documentation (docs/)
- **Phase 3**: Plan strategy (full regeneration with aggressive optimization)
- **Phase 4**: Generate optimized graph (Type→Domain→Module→Class, no clusters)
- **Phase 5**: Integrate documentation pointers (DOCUMENTED_IN relations + Doc entities)
- **Phase 6**: Validate (size <100KB, load <1s) + save codegraph.json

**Optimization Techniques**:
- Entity filtering: Type + Domains + All Modules + Key Classes only
- Observation filtering: Remove generic noise ("Module: X", "File", "Class: X")
- Observation enrichment: Keep only functional descriptions (50-80 chars explaining what it does)
- Name simplification: Code.Module.X instead of Code.Module.X.File
- Relation extraction: BELONGS_TO + INHERITS + DOCUMENTED_IN + IMPORTS (module-level only)
- Compact JSON: No whitespace (separators=(',',':'))
- Strategic doc pointers: Link high-value entities (domains, key classes)

**Size Management**:
- Target: <100KB (current: ~63KB with IMPORTS relations)
- Entity limit: ~80 entities (1 Type + 2-3 Domains + 65 Modules + ~10 Classes + 7 Docs)
- Relation limit: ~220 relations (76 BELONGS_TO + 140 IMPORTS + 3 DOCUMENTED_IN + INHERITS)
- Observation format: [functional_description (50-80 chars), doc_reference (optional), metadata]
- Naming: Shorter paths without .File suffix

**Testing Scripts**:
- `misc/scripts/test_navigation.py` - Test codegraph navigation (domains→modules→classes)
- `misc/scripts/test_doc_pointers.py` - Test documentation pointer navigation

---

**Update Cycle**: Assess existing → Analyze codebase+docs → Plan strategy → Generate graph → Integrate docs → Validate+optimize (size critical)
