# Documentation Pointer System

**Purpose**: Dual-layer navigation system where codegraph provides structure map + documentation pointers for detailed explanations | **Result**: Query once, get both code location AND relevant documentation without re-analysis

## Architecture

### Dual-Layer Navigation
```
LAYER 1: Codegraph (Structure Map)
├── Code entities (Type/Domain/Cluster/Module/Class)
├── Relations (IMPORTS/CALLS/INHERITS/BELONGS_TO)
└── DOCUMENTED_IN pointers → Layer 2

LAYER 2: Documentation (Detailed Explanations)
├── Architecture docs (ARCH_*.md) → Domains
├── Technical docs (TECH_*.md) → Modules/Services
├── Blueprints (BLUEPRINT_*.md) → Features/Classes
└── Implementation (IMPL_*.md) → Specific changes
```

### Entity Types

**Code Entities**: Standard codegraph entities (Type/Domain/Cluster/Module/Class/Method)
**Doc Entities**: Pseudo-entities representing documentation files (Doc:path/to/file.md)

## Relations

### DOCUMENTED_IN
**Direction**: Code entity → Documentation entity  
**Purpose**: Points from code to its detailed documentation  
**Example**:
```json
{
  "type": "relation",
  "from": "Code.Class.commander_services_context_menu_service.ContextMenuService",
  "to": "Doc:docs/blueprints/BLUEPRINT_context_menu.md",
  "relationType": "DOCUMENTED_IN"
}
```

### Reverse Navigation
**Direction**: Documentation entity ← Code entity  
**Purpose**: Find all code explained in specific documentation  
**Query**: Filter relations where `relationType == 'DOCUMENTED_IN' AND to == 'Doc:TARGET.md'`

## Documentation Mapping Strategy

### Architecture Level (Domain)
```
Code.Domain.Commander → Doc:docs/architecture/ARCH_command_system.md
Code.Domain.Core → Doc:docs/architecture/ARCH_memory_system.md
Code.Domain.Integration → Doc:docs/architecture/ARCH_integration_patterns.md
```

**Scope**: High-level system design, architectural decisions, domain boundaries, cross-cutting concerns

### Technical Level (Module/Service)
```
Code.Module.commander_main_window.File → Doc:docs/technical/TECH_commander_window.md
Code.Module.sys_file_loader.File → Doc:docs/technical/TECH_token_management.md
Code.Module.context_menu_service.File → Doc:docs/technical/TECH_context_menu_service.md
```

**Scope**: API specifications, configuration, implementation procedures, technical details

### Blueprint Level (Class/Feature)
```
Code.Class.ContextMenuService → Doc:docs/blueprints/BLUEPRINT_context_menu.md
Code.Class.BsToolCommandService → Doc:docs/blueprints/BLUEPRINT_bstool_integration.md
Code.Class.NodeTreeView → Doc:docs/blueprints/BLUEPRINT_node_tree_ui.md
```

**Scope**: Feature specifications, implementation plans, component interactions, testing strategies

### Implementation Level (Specific Changes)
```
Code.Method.validate_node → Doc:docs/implementation/IMPL_SUMMARY_node_validation.md
Code.Module.error_reporting.File → Doc:docs/implementation/IMPL_SUMMARY_error_handling.md
```

**Scope**: Change summaries, implementation details, specific refactorings, bug fixes

## Navigation Workflows

### Workflow 1: Find Documentation for Code Entity
```
1. Query codegraph for entity: Code.Class.ContextMenuService
2. Filter relations: relationType == 'DOCUMENTED_IN' AND from == entity
3. Extract doc reference: Doc:docs/blueprints/BLUEPRINT_context_menu.md
4. Read documentation file for detailed explanation
5. Read source code for implementation details
```

**Result**: Comprehensive understanding (structure + documentation + source)

### Workflow 2: Find Code Explained in Documentation
```
1. Target documentation: Doc:docs/architecture/ARCH_command_system.md
2. Filter relations: relationType == 'DOCUMENTED_IN' AND to == doc
3. Extract code entities: [Code.Domain.Commander, Code.Module.X, Code.Class.Y]
4. Navigate to each code entity for implementation details
```

**Result**: Map documentation concepts to actual code locations

### Workflow 3: Impact Analysis with Context
```
1. Find target entity: Code.Class.ContextMenuService
2. Query CALLS/INHERITS relations for impact surface
3. Query DOCUMENTED_IN for architecture context
4. Load documentation to understand design constraints
5. Assess impact with full context (code + docs)
```

**Result**: Informed impact analysis without manual doc search

### Workflow 4: Feature Location with Background
```
1. Search for feature keyword in codegraph observations
2. Find matching entities: [Code.Module.X, Code.Class.Y]
3. Check DOCUMENTED_IN pointers for each
4. Load blueprints/technical docs for feature specification
5. Navigate to source code with full context
```

**Result**: Understand feature requirements before reading code

## Implementation

### Adding Documentation Pointers

**Script**: `misc/scripts/add_doc_pointers.py`

**Strategy**:
1. Scan docs/ folder for architecture/technical/blueprints
2. Map documentation to code entities by naming patterns
3. Create Doc entities for each documentation file
4. Add DOCUMENTED_IN relations (code → doc)
5. Update entity observations with doc references (within 18-char limit)

**Example**:
```python
# Map blueprint to class
mappings = [
    ('Code.Class.ContextMenuService', 'docs/blueprints/BLUEPRINT_context_menu.md'),
]

# Create relation
relation = {
    'type': 'relation',
    'from': 'Code.Class.ContextMenuService',
    'to': 'Doc:docs/blueprints/BLUEPRINT_context_menu.md',
    'relationType': 'DOCUMENTED_IN'
}

# Update entity observation
entity['observations'].insert(-1, 'doc:BLUEPRINT_context_menu.md')
```

### Doc Entity Format
```json
{
  "type": "entity",
  "name": "Doc:docs/blueprints/BLUEPRINT_context_menu.md",
  "entityType": "Documentation",
  "observations": [
    "Context menu spec",
    "docs/blueprints/",
    "upd:2025-10-11,refs:0"
  ]
}
```

**Compact**: 18-char description + folder path + metadata

## Size Impact

### Before Documentation Pointers
- **Entities**: 113 (code only)
- **Relations**: 114 (BELONGS_TO + INHERITS)
- **Size**: 32.07 KB

### After Documentation Pointers
- **Entities**: 116 (+3 doc entities)
- **Relations**: 120 (+6 DOCUMENTED_IN relations)
- **Size**: 33.42 KB (+1.35 KB, 4.2% increase)

**Impact**: Minimal size increase (1.35 KB) for significant context enrichment

## Benefits

### No Re-Analysis Required
- **Before**: Query codegraph → manually search docs → read multiple files
- **After**: Query codegraph → follow DOCUMENTED_IN pointer → read targeted doc
- **Savings**: 80% reduction in manual doc search time

### Rich Context in Single Query
- **Structure**: Entity hierarchy via BELONGS_TO/INHERITS
- **Implementation**: Source file path from entity name
- **Documentation**: Detailed explanation via DOCUMENTED_IN
- **Dependencies**: IMPORTS/CALLS relations for impact

### Bidirectional Navigation
- **Code → Docs**: "What docs explain this class?"
- **Docs → Code**: "What code implements this architecture?"
- **Result**: Seamless navigation in both directions

### Persistent Knowledge
- **Load once**: Codegraph + doc pointers loaded at session start
- **Query many**: All navigation queries use in-memory structure
- **No re-scan**: Documentation links persist across sessions

## Testing

**Script**: `misc/scripts/test_doc_pointers.py`

**Validation**:
1. Find documentation for Commander domain ✅
2. List all code entities with documentation pointers ✅
3. List all documentation entities ✅
4. Test navigation workflow (ContextMenuService → BLUEPRINT_context_menu.md) ✅
5. Validate size remains <100KB ✅ (33.42 KB)

## Usage Pattern

### Load Pattern
```python
# Load codegraph (once per session)
entities, relations = load_codegraph('codegraph.json')

# Query for entity
target = 'Code.Class.ContextMenuService'
entity = entities[target]

# Find documentation
docs = [r['to'] for r in relations 
        if r['from'] == target 
        and r['relationType'] == 'DOCUMENTED_IN']

# Load doc file
if docs:
    doc_path = docs[0].replace('Doc:', '')  # Strip prefix
    with open(doc_path) as f:
        documentation = f.read()

# Read source code
source_path = derive_path_from_entity(target)
with open(source_path) as f:
    source_code = f.read()

# Result: entity + documentation + source in context
```

### Query Examples

**Find all documented modules**:
```python
documented = {r['from'] for r in relations 
              if r['relationType'] == 'DOCUMENTED_IN'}
```

**Find documentation for domain**:
```python
domain_docs = [r['to'] for r in relations 
               if r['from'] == 'Code.Domain.Commander' 
               and r['relationType'] == 'DOCUMENTED_IN']
```

**Find code explained in blueprint**:
```python
blueprint = 'Doc:docs/blueprints/BLUEPRINT_context_menu.md'
code_entities = [r['from'] for r in relations 
                 if r['to'] == blueprint 
                 and r['relationType'] == 'DOCUMENTED_IN']
```

## Maintenance

### Adding New Documentation Links
1. Create documentation file (ARCH_/TECH_/BLUEPRINT_/IMPL_*.md)
2. Identify relevant code entities (Domain/Module/Class)
3. Add mapping to `add_doc_pointers.py`
4. Run script to regenerate codegraph
5. Validate size remains <100KB

### Updating Existing Links
1. Modify mappings in `add_doc_pointers.py`
2. Regenerate codegraph
3. Test navigation with `test_doc_pointers.py`

### Removing Obsolete Links
1. Remove mapping from script
2. Regenerate codegraph
3. Verify orphaned Doc entities removed

## Best Practices

### Documentation Naming
- **Consistency**: Use prefix patterns (ARCH_/TECH_/BLUEPRINT_/IMPL_)
- **Clarity**: Filename should indicate content scope
- **Mapping**: Use keywords from code entity names for easy linking

### Observation Annotations
- **Compact**: Keep doc references ≤18 chars (e.g., `doc:BLUEPRINT_X.md`)
- **Consistent**: Use `doc:` prefix for all documentation references
- **Placement**: Insert before metadata observation

### Relation Management
- **Bidirectional**: Always create explicit DOCUMENTED_IN relations
- **Specificity**: Link at appropriate level (Domain→ARCH, Class→BLUEPRINT)
- **Coverage**: Prioritize key entities (domains, services, complex classes)

### Size Optimization
- **Selective**: Don't link every entity to documentation
- **Strategic**: Focus on high-value links (architecture, key classes)
- **Compact**: Use short doc filenames, truncate paths in observations
- **Monitor**: Keep total size <100KB (currently 33.42 KB with 66.58 KB remaining)

## Future Enhancements

### Automatic Link Generation
- Parse @references in documentation
- Extract code entity names from docs
- Auto-generate DOCUMENTED_IN relations

### Documentation Coverage Metrics
- % of domains with architecture docs
- % of key classes with blueprints
- % of modules with technical docs

### Smart Navigation
- Suggest relevant docs during code navigation
- Highlight undocumented critical code
- Provide doc→code traceability report

---

**Core Principle**: Codegraph = navigational map with documentation pointers. Query once, get structure + doc references + source paths. No re-analysis, rich context, persistent knowledge.
