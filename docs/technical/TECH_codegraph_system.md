# Code Graph System - Technical Guide

---
**Metadata**:
- **title**: Code Graph System - Technical Guide
- **type**: TECH
- **category**: technical
- **version**: 1.0
- **last_updated**: 2025-10-09
- **status**: active
- **owner**: development-team
- **related_docs**: [ARCH_memory_system.md](../architecture/ARCH_memory_system.md), [ARCH_chatmode_orchestrator.md](../architecture/ARCH_chatmode_orchestrator.md)
- **tags**: [codegraph, code-analysis, dependencies, ast, memory-system, automation]

---

## Table of Contents
- [📋 Overview](#-overview)
- [🏗️ Architecture](#️-architecture)
- [🔧 Generator](#-generator)
- [📖 Usage Guide](#-usage-guide)
- [🔗 Integration](#-integration)
- [🌐 Universal Capabilities](#-universal-capabilities)
- [💡 Best Practices](#-best-practices)

---

## 📋 Overview

The **Code Graph System** provides automated hierarchical representation of the entire Python codebase, generating `codegraph.json` that mirrors the structure of `project_memory.json` but focuses on actual code entities (modules, classes, methods, functions) and their relationships.

### Purpose

**Primary Functions**:
- **Code Navigation** - Understand code structure and relationships at a glance
- **Dependency Tracking** - Visualize what imports what, what calls what
- **Architecture Visualization** - Bird's-eye view of entire codebase structure
- **Refactoring Support** - Identify impacts of changes before making them
- **Documentation** - Auto-generated code structure reference that stays current
- **Onboarding** - Help new developers understand codebase architecture quickly

**Key Benefits**:
- Zero maintenance overhead (fully automated)
- Always synchronized with code (regenerate on demand)
- Portable generator (works with any Python project)
- Rich metadata extraction (docstrings, params, decorators)
- Comprehensive relationship tracking (imports, calls, inheritance)

### Integration Points

**Memory System Connection**:
- Complements `project_memory.json` (conceptual knowledge)
- Used by orchestrator REMEMBER phase (Phase 1) - indexed at init, queried throughout workflow
- Enables code-aware development (ANALYZE, ARCHITECT, IMPLEMENT phases leverage structure)
- Cross-references with project entities (feature implementations link to code entities)

**Workflow Usage**:
| Phase | Usage | Query Pattern |
|-------|-------|---------------|
| **REMEMBER (1)** | Index structure | Load complete module/class/method hierarchy |
| **ASSESS (2)** | Find references | Search for existing implementations, test files |
| **ANALYZE (3)** | Trace flows | Follow CALLS chains, IMPORTS dependencies, INHERITS hierarchies |
| **ARCHITECT (4)** | Impact analysis | Identify affected modules, downstream dependencies |
| **IMPLEMENT (5)** | Pattern matching | Reference similar method signatures, class structures |
| **DEBUG (6)** | Execution trace | Follow CALLS from error point, check IMPORTS |
| **TEST (7)** | Coverage gaps | Map all methods needing tests, find untested paths |

### Statistics (LOGReport Project)

**Current Codebase** (`src/` folder):
- **Total Entities**: 749 (modules, classes, methods, functions)
- **Total Relations**: 5,114 (calls, imports, inheritance, hierarchy)
- **Modules**: 70 Python files
- **Classes**: 83 class definitions
- **Methods**: 524 methods in classes
- **Functions**: 38 top-level functions
- **Domains**: 12 functional domains
- **Clusters**: 33 module groupings

**Relation Breakdown**:
- **CALLS**: 3,635 (function/method invocations)
- **BELONGS_TO**: 745 (hierarchical structure)
- **IMPORTS**: 682 (module dependencies)
- **INHERITS**: 49 (class inheritance)
- **IS_A**: 3 (domain-to-type relationships)

---

## 🏗️ Architecture

### 6-Layer Hierarchy

The code graph follows a strict 6-layer hierarchy mirroring the 4-layer memory system but with additional granularity for code entities:

```
Code.Type.Codebase                                    (Layer 1: Root Type)
  └─ Code.Domain.{domain}                             (Layer 2: Functional Domain)
      └─ Code.Cluster.{cluster}                       (Layer 3: Module Grouping)
          └─ Code.Module.{module}.File                (Layer 4: Python File)
              ├─ Code.Class.{module}.{class}          (Layer 5: Class Definition)
              │   └─ Code.Method.{module}_{class}.{method}   (Layer 6: Method)
              └─ Code.Function.{module}.{function}    (Layer 6: Function)
```

**Hierarchy Rules**:
- All entities connect through BELONGS_TO relations
- Methods MUST connect to Classes (not directly to Clusters)
- Classes connect to Modules (file level)
- Modules connect to Clusters (grouping level)
- Clusters connect to Domains (functional area)
- Domains connect to Type (codebase root)

### Entity Types

| Entity Type | Layer | Description | Naming Pattern | Example |
|-------------|-------|-------------|----------------|---------|
| **Type** | 1 | Root codebase type | `Code.Type.Codebase` | `Code.Type.Codebase` |
| **Domain** | 2 | Functional domain | `Code.Domain.{domain}` | `Code.Domain.Commander` |
| **Cluster** | 3 | Module grouping | `Code.Cluster.{domain}.{cluster}` | `Code.Cluster.Commander.Services` |
| **Module** | 4 | Python file | `Code.Module.{path}.File` | `Code.Module.commander_services_menu.File` |
| **Class** | 5 | Class definition | `Code.Class.{path}.{class}` | `Code.Class.commander_services_menu.MenuService` |
| **Method** | 6 | Class method | `Code.Method.{path}_{class}.{method}` | `Code.Method.commander_services_menu_MenuService.show_menu` |
| **Function** | 6 | Top-level function | `Code.Function.{path}.{function}` | `Code.Function.utils_helpers.format_text` |

**Naming Conventions**:
- Paths use underscores: `commander_services_menu` (not dots or slashes)
- Class names preserve PascalCase: `MenuService`
- Method/function names preserve snake_case: `show_menu`
- `.File` suffix indicates module entity (not a literal file)

### Relation Types

| Relation | Description | Direction | Example |
|----------|-------------|-----------|---------|
| **BELONGS_TO** | Hierarchical containment | Child → Parent | Method → Class → Module → Cluster → Domain → Type |
| **IS_A** | Type relationship | Instance → Type | Domain → Type |
| **IMPORTS** | Module dependency | Importer → Imported | `module_a` imports `module_b` |
| **CALLS** | Function invocation | Caller → Callee | `func_a` calls `func_b` (within same module or cross-module) |
| **INHERITS** | Class inheritance | Child → Parent | `ClassA` inherits from `ClassB` |

**Relation Characteristics**:
- **BELONGS_TO**: Always upward in hierarchy (defines structure)
- **IMPORTS**: Horizontal across modules (defines dependencies)
- **CALLS**: Horizontal across methods/functions (defines behavior flow)
- **INHERITS**: Horizontal across classes (defines type hierarchy)

### Entity Metadata (Observations)

Each entity includes detailed metadata in the `observations` array:

#### Module Entity
```json
{
  "type": "entity",
  "name": "Code.Module.commander_services_context_menu_service.File",
  "entityType": "Module",
  "observations": [
    "File: src/commander/services/context_menu_service.py",
    "Module: commander.services.context_menu_service",
    "Context menu service for node operations",
    "upd:2025-10-09,refs:0"
  ]
}
```

**Module Metadata**:
- File path (relative to `src/`)
- Module import path (dot notation)
- Module docstring (first line, max 120 chars)
- Update date and reference count

#### Class Entity
```json
{
  "type": "entity",
  "name": "Code.Class.commander_services_context_menu_service.ContextMenuService",
  "entityType": "Class",
  "observations": [
    "Class in commander.services.context_menu_service",
    "Manages context menu creation and display",
    "Inherits: QObject",
    "Methods: 8",
    "upd:2025-10-09,refs:0"
  ]
}
```

**Class Metadata**:
- Containing module
- Class docstring (first line, max 120 chars)
- Base classes (inheritance chain)
- Method count
- Update date and reference count

#### Method/Function Entity
```json
{
  "type": "entity",
  "name": "Code.Method.commander_services_context_menu_service_ContextMenuService.show_context_menu",
  "entityType": "Method",
  "observations": [
    "Method in commander.services.context_menu_service",
    "Display context menu at cursor position",
    "Params: position, node, parent",
    "Decorators: @pyqtSlot",
    "upd:2025-10-09,refs:0"
  ]
}
```

**Method/Function Metadata**:
- Containing module/class
- Docstring (first line, max 120 chars)
- Parameters (first 5 shown)
- Decorators (if any)
- Update date and reference count

### Domain Auto-Detection

The generator automatically maps folder names to domains:

| Folder Name | Domain | Folder Name | Domain |
|-------------|--------|-------------|--------|
| `api` | API | `services` | Services |
| `backend` | Backend | `tests` | Testing |
| `commander` | Commander | `ui` | UI |
| `config` | Configuration | `utils` | Utilities |
| `controllers` | Controllers | `views` | Views |
| `models` | Models | `widgets` | Widgets |
| `presenters` | Presenters | *custom* | Capitalized |

**Custom Folders**: Any folder not in the mapping is automatically added with a capitalized domain name.

**Cluster Detection**: Clusters are created from the first two path levels:
```
src/commander/services/menu_service.py
    ↓
Domain: Commander
Cluster: Commander.Services
Module: commander.services.menu_service
```

---

## 🔧 Generator

### Script: `generate_codegraph.py`

**Location**: `scripts/generate_codegraph.py`  
**Language**: Python 3.7+  
**Dependencies**: Standard library only (no external packages)

**Key Features**:
- ✨ **Universal & Portable** - Works with any Python project, zero configuration
- 📊 **Comprehensive Analysis** - Extracts modules, classes, methods, functions, imports, calls, inheritance
- 🛡️ **Robust Error Handling** - Syntax error tolerance, graceful degradation
- ⚙️ **Configurable** - Command-line arguments for customization
- 🚀 **Smart Defaults** - Works out-of-the-box with sensible defaults

### Installation

**Prerequisites**:
- Python 3.7+ (standard library only)

**Setup**:
```bash
# Option 1: Use from scripts folder (already in project)
python scripts/generate_codegraph.py

# Option 2: Copy to another project
cp scripts/generate_codegraph.py /path/to/other/project/scripts/

# Option 3: Make executable (Unix)
chmod +x scripts/generate_codegraph.py
./scripts/generate_codegraph.py
```

### Command-Line Interface

**Basic Usage**:
```bash
# Scan ./src (or current directory if no src/)
python scripts/generate_codegraph.py

# Specify source directory
python scripts/generate_codegraph.py --src ./myapp

# Custom output path
python scripts/generate_codegraph.py --output ./docs/code_structure.json

# Verbose mode (see auto-detection in action)
python scripts/generate_codegraph.py --verbose
```

**Advanced Usage**:
```bash
# Exclude additional patterns
python scripts/generate_codegraph.py --exclude test --exclude migrations

# Full custom configuration
python scripts/generate_codegraph.py \
  --src ./backend/api \
  --output ./docs/api_graph.json \
  --exclude __pycache__ \
  --exclude .pytest_cache \
  --verbose
```

### Command-Line Options

| Option | Description | Default | Example |
|--------|-------------|---------|---------|
| `--src PATH` | Source directory to scan | `./src` (or `./` if no src/) | `--src ./backend` |
| `--output PATH` | Output file path | `./codegraph.json` | `--output ./docs/graph.json` |
| `--exclude PATTERN` | Exclude pattern (repeatable) | See defaults below | `--exclude test` |
| `--verbose` | Enable verbose logging | Disabled | `--verbose` |
| `--version` | Show version | - | `--version` |
| `--help` | Show help message | - | `--help` |

**Default Exclude Patterns** (always applied):
- `__pycache__` - Python bytecode cache
- `.egg-info` - Package metadata
- `venv`, `.venv`, `env`, `.env` - Virtual environments
- `build`, `dist` - Build artifacts
- `.git` - Version control

Use `--exclude` to add more patterns (defaults always included).

### Error Handling

**Syntax Errors**:
```
WARNING: Error processing file.py: invalid syntax (file.py, line 10)
```
- File is logged and skipped
- Processing continues with remaining files
- Check warning logs for details

**Missing Docstrings**:
- Defaults to `"{name} class"` or `"{name} function"`
- No error, graceful degradation

**Unparseable AST Nodes**:
- Logged as INFO
- Node skipped, file processing continues

### Performance

| Project Size | Files | Time | Output Size |
|--------------|-------|------|-------------|
| **Small** | 10-50 | <1s | 10-50 KB |
| **Medium** | 50-200 | 1-5s | 50-500 KB |
| **Large** | 200-500 | 5-15s | 500KB-2MB |
| **Very Large** | 500+ | 15-60s | 2-10MB |

**LOGReport Project**: 70 files → ~2s → 450 KB

---

## 📖 Usage Guide

### Generate Code Graph

**PowerShell** (Windows):
```powershell
# Basic generation
python scripts\generate_codegraph.py

# Verify output
ls -l codegraph.json

# Quick stats
(Get-Content codegraph.json | Select-String '"type": "entity"').Count
(Get-Content codegraph.json | Select-String '"type": "relation"').Count
```

**Bash** (Linux/Mac):
```bash
# Basic generation
python scripts/generate_codegraph.py

# Verify output
ls -lh codegraph.json

# Quick stats
grep -c '"type": "entity"' codegraph.json
grep -c '"type": "relation"' codegraph.json
```

---

## 🔗 Cluster Layer Enhancement

**Version**: 5-Layer Hierarchy  
**Added**: 2025-01-19  
**Impact**: Richer organizational context while maintaining <100KB size target

### Evolution from 4-Layer to 5-Layer

The codegraph structure was enhanced from 4-layer to **5-layer** hierarchy, adding a Cluster layer between Domain and Module for more specific organizational context.

**Before** (4 layers):
```
Code.Type.Python
└── Code.Domain.Commander
    ├── Code.Module.context_menu_service
    └── Code.Module.bstool_command_service
```

**After** (5 layers):
```
Code.Type.Python
└── Code.Domain.Commander
    └── Code.Cluster.Commander.Services
        ├── Code.Module.context_menu_service
        └── Code.Module.bstool_command_service
```

### Cluster Definitions by Domain

**Commander Domain** (4 clusters):
- **Services**: Command services (context menu, bstool, error reporting)
- **Views**: UI views (node tree, dialogs, widgets)
- **Presenters**: Presenters (mediates between models and views)
- **Models**: Data models (node configuration, state management)

**Core Domain** (3 clusters):
- **FileIO**: File I/O (log loading, token detection, file processing)
- **Processing**: Data processing (log parsing, report generation)
- **Configuration**: Configuration (settings, constants, contracts)

**Frontend Domain** (3 clusters):
- **MainUI**: Main GUI (windows, tabs, primary interface)
- **Dialogs**: Dialog windows (configuration, settings)
- **Workers**: Background workers (async processing, threading)

### Benefits

**Organizational Clarity**:
- Clear separation between service types (BsTool service vs Telnet service vs Context menu service)
- Easier navigation: "Find all services" vs "Find all modules in Commander"
- Better grouping for related functionality

**Query Efficiency**:
```python
# Before: Search all Commander modules
query = "Code.Domain.Commander.Code.Module.*"

# After: Search only service modules
query = "Code.Domain.Commander.Code.Cluster.Services.*"
```

**Size Impact**:
- Added ~200 cluster entities
- Increased file size by ~2KB (within 100KB target)
- Improved semantic value outweighs minimal size increase

### Implementation Details

**Script**: `scripts/update_codegraph.py` - Phase 3 (Cluster Assignment)  
**Logic**: Pattern-based cluster detection from module names:
- `*_service.py` → Services cluster
- `*_view.py`, `*_window.py` → Views cluster
- `*_presenter.py` → Presenters cluster
- `*_model.py`, `*_models.py` → Models cluster
- `*_loader.py`, `*_parser.py` → FileIO cluster
- `*_processor.py`, `*_generator.py` → Processing cluster

---

## 🤖 DevTeam Integration Patterns

**Integration Date**: 2025-10-11  
**Purpose**: Mandate codegraph usage in DevTeam orchestrator workflow for code-aware development

### Phase-Specific Codegraph Usage

Codegraph integrated into DevTeam.chatmode with phase-specific requirements:

| Phase | Usage Level | Codegraph Operations |
|-------|-------------|----------------------|
| **REMEMBER (1)** | Optional | Load global/project memory, codegraph typically loaded in ASSESS |
| **ASSESS (2)** | **LOAD POINT** | **Read entire codegraph.json into context** - makes all entities available |
| **ANALYZE (3)** | Recommended | Query BELONGS_TO for structure, IMPORTS for dependencies, DOCUMENTED_IN for context |
| **ARCHITECT (4)** | Recommended | Query for impact analysis (affected modules, downstream dependencies, inheritance) |
| **IMPLEMENT (5)** | **⚠️ MANDATORY** | Reference similar method signatures, parameter patterns, class structures, naming conventions |
| **DEBUG (6)** | **⚠️ MANDATORY** | Trace CALLS chains, locate implementations via BELONGS_TO, follow IMPORTS for dependency issues |
| **TEST (7)** | Recommended | Map all methods needing tests, identify untested paths, dependency-based test surface |

### Codegraph Query Patterns

**ANALYZE Phase** - Pattern Detection:
```python
# Detect emergent patterns across codebase
query = "Code.Module.*context_menu*"  # Find all context menu related modules
# Follow BELONGS_TO to understand structure
# Follow IMPORTS to map dependencies
# Check DOCUMENTED_IN for existing documentation
```

**ARCHITECT Phase** - Impact Analysis:
```python
# Identify affected modules when changing component X
affected = []
for module in codegraph.query("Code.Module.*"):
    if module.imports("component_x"):
        affected.append(module)
        # Follow forward IMPORTS to find downstream dependencies
        downstream = module.get_dependents()
        affected.extend(downstream)
```

**IMPLEMENT Phase** - Pattern Matching:
```python
# Reference similar method signatures before implementing
similar_methods = codegraph.query("Code.Method.*validate_token*")
for method in similar_methods:
    # Check parameter patterns
    # Review naming conventions
    # Understand return types
    # Copy consistent patterns
```

**DEBUG Phase** - Execution Trace:
```python
# Trace execution from error point
error_method = codegraph.get_method("NodeTreePresenter.handle_command_completed")
# Follow CALLS relations backward (who calls this?)
callers = error_method.get_incoming_calls()
# Follow CALLS forward (what does this call?)
callees = error_method.get_outgoing_calls()
# Check IMPORTS for dependency issues
dependencies = error_method.module.get_imports()
```

**TEST Phase** - Coverage Mapping:
```python
# Map all methods needing tests
untested_methods = []
for method in codegraph.query("Code.Method.*"):
    # Query for corresponding test file
    test_file = f"test_{method.module_name}.py"
    if not codegraph.has_entity(test_file):
        untested_methods.append(method)
```

### Integration Benefits

**Code-Aware Development**:
- Implementations follow existing patterns automatically
- Impact analysis prevents breaking changes
- Debug sessions faster with execution trace
- Test coverage gaps immediately visible

**Consistency Enforcement**:
- New code matches existing naming conventions
- Method signatures consistent across similar methods
- Import patterns follow established architecture
- Documentation pointers guide doc creation

**Workflow Efficiency**:
- No manual codebase searching required
- Patterns discovered automatically via queries
- Dependencies mapped instantly
- Related code found with single query

### DevTeam Chatmode Changes

**Core Principles Addition**:
```markdown
- **Codegraph-Driven ⚠️ MANDATORY**: ALWAYS query codegraph.json for navigation, 
  impact analysis, patterns | OBLIGATORY in IMPLEMENT + DEBUG phases | 
  PREFERABLY in ANALYZE + ARCHITECT + TEST phases
```

**Phase Actions Enhanced**:
- ANALYZE: Added "**query loaded codegraph** (BELONGS_TO, IMPORTS, DOCUMENTED_IN, detect patterns)"
- ARCHITECT: Added "**query loaded codegraph for impact analysis** (affected modules, downstream dependencies)"
- IMPLEMENT: Added "**reference loaded codegraph** (similar signatures, class structures, conventions)"
- DEBUG: Added "**trace execution in loaded codegraph** (CALLS chains, BELONGS_TO, IMPORTS)"

**Completion Format Enhanced**:
- ANALYZE: Added `CODEGRAPH_REFS:[modules:[list] classes:[list] relevant_relations:[count]]`
- ARCHITECT: Added `IMPACT_ANALYSIS:[affected_modules:[list] downstream_dependencies:[count]]`
- IMPLEMENT: Added `CODE_PATTERNS:[similar_methods:[list] reused_structures:[count]]`
- DEBUG: Added `EXECUTION_TRACE:[call_chain:[methods] affected_classes:[list] dependency_issues:[count]]`
- TEST: Added `TEST_SURFACE:[methods_tested:[N/M] classes_covered:[list] edge_cases:[count]]`

---

## 📝 Documentation Pointer System

**Feature**: Bidirectional Code↔Documentation Linking  
**Implementation Date**: 2025-10-11  
**Purpose**: Rich context in single query without re-analysis

### Concept

**Problem**: Querying code structure gives entities but no documentation context. Developers must separately search for relevant docs.

**Solution**: DOCUMENTED_IN relations linking code entities to documentation files, creating bidirectional navigation.

**Benefits**:
- No re-analysis required (query once, get code + docs)
- Rich context in single query (structure + documentation + source pointers)
- Persistent knowledge (links survive sessions)
- Minimal size impact (+1.35KB for 7 doc pointers)

### Implementation

**Doc Entities** in codegraph.json:
```json
{
  "type": "entity",
  "name": "Doc:docs/technical/TECH_codegraph.md",
  "entityType": "Documentation",
  "observations": ["Documentation for Codebase", "upd:2025-10-11,refs:0"]
}
```

**DOCUMENTED_IN Relations**:
```json
{
  "type": "relation",
  "from": "Code.Type.Codebase",
  "to": "Doc:docs/technical/TECH_codegraph.md",
  "relationType": "DOCUMENTED_IN"
}
```

### Usage Patterns

**Query with Documentation Context**:
```python
# Query Commander domain
commander = codegraph.get_entity("Code.Domain.Commander")

# Get documentation automatically
doc_links = commander.get_relations("DOCUMENTED_IN")
for doc in doc_links:
    print(f"Documented in: {doc.target}")
    # Output: "Documented in: docs/architecture/ARCH_command_system.md"
```

**Reverse Query** (Find code for documentation):
```python
# Query documentation entity
doc = codegraph.get_entity("Doc:docs/architecture/ARCH_memory_system.md")

# Find what it documents
documented_entities = doc.get_incoming_relations("DOCUMENTED_IN")
for entity in documented_entities:
    print(f"Documents: {entity.name}")
    # Output: "Documents: Code.Domain.Core"
```

### Size Impact Analysis

**Baseline** (without doc pointers):
- Entities: 749
- Relations: 5,114
- Size: 22.05KB

**Enhanced** (with doc pointers):
- Entities: 752 (+3 Doc entities)
- Relations: 5,121 (+7 DOCUMENTED_IN)
- Size: 23.40KB (+1.35KB, 6.1% increase)

**Headroom**: Target is <100KB, current 23.40KB leaves 76.60KB headroom (326% under target)

### Strategic Pointer Placement

**High-Value Entities Only**:
- Type entities (Codebase → TECH_codegraph.md)
- Domain entities (Commander → ARCH_command_system.md, Core → ARCH_memory_system.md)
- Key classes (NodeTreePresenter → ARCH_node_system.md)

**Not Linked**:
- Individual methods (too granular, would add 500+ relations)
- Utility modules (documented in parent domain)
- Generated files (no documentation needed)

### Integration with DevTeam

**ANALYZE Phase** - Automatic Context:
```python
# Query module for analysis
module = codegraph.get_entity("Code.Module.commander_node_manager")
# Documentation link included automatically
docs = module.get_documentation_links()
# Read relevant docs for analysis context
```

**IMPLEMENT Phase** - Pattern Guidance:
```python
# Find similar implementations
similar = codegraph.query("Code.Class.*Presenter*")
for cls in similar:
    # Get documentation for best practices
    docs = cls.get_documentation_links()
    # Follow documented patterns
```

**DOCUMENT Phase** - Update Tracking:
```python
# Find entities without documentation
undocumented = []
for entity in codegraph.query("Code.Class.*"):
    if not entity.has_relation("DOCUMENTED_IN"):
        undocumented.append(entity)
# Create documentation for undocumented entities
```

---

## 💡 Best Practices

### When to Regenerate

**Always Regenerate After**:
- ✅ Adding new modules, classes, or functions
- ✅ Significant refactoring (moving/renaming files)
- ✅ Changing import structure
- ✅ Major architectural changes

**Recommended Schedule**:
- **Active Development**: Weekly or after major feature additions
- **Stable Maintenance**: Monthly or before releases
- **CI/CD**: On every PR to track structure changes

**Not Necessary After**:
- Small bug fixes (single-line changes)
- Comment updates
- Documentation changes

### Query Patterns

#### PowerShell Examples

**Find All Methods in a Class**:
```powershell
Get-Content codegraph.json | Select-String 'Code.Method.*ContextMenuService'
```

**Find What a Module Imports**:
```powershell
Get-Content codegraph.json | Select-String '"from": "Code.Module.context_menu_service.*IMPORTS"'
```

**Find All Classes Inheriting from Base**:
```powershell
Get-Content codegraph.json | Select-String '"relationType": "INHERITS".*QMainWindow'
```

**Count Methods Per Domain**:
```powershell
(Get-Content codegraph.json | Select-String 'Code.Method.*Commander').Count
```

**Find Function Call Chains**:
```powershell
Get-Content codegraph.json | Select-String '"relationType": "CALLS"' | Select-String 'show_menu'
```

#### Python Query Script

```python
import json

# Load code graph
with open('codegraph.json') as f:
    lines = f.readlines()

entities = [json.loads(line) for line in lines if '"type": "entity"' in line]
relations = [json.loads(line) for line in lines if '"type": "relation"' in line]

# Find all classes
classes = [e for e in entities if e.get('entityType') == 'Class']
print(f"Total classes: {len(classes)}")

# Find imports for a specific module
target_module = "Code.Module.commander_services_menu.File"
imports = [r for r in relations 
           if r.get('relationType') == 'IMPORTS' 
           and r.get('from') == target_module]
print(f"Module imports: {len(imports)}")

# Find all methods calling a specific function
target_func = "show_context_menu"
callers = [r for r in relations 
           if r.get('relationType') == 'CALLS' 
           and target_func in r.get('to', '')]
print(f"Callers: {len(callers)}")

# Build call graph for a method
def get_call_chain(method_name, depth=2):
    chain = []
    queue = [(method_name, 0)]
    visited = set()
    
    while queue:
        current, level = queue.pop(0)
        if level >= depth or current in visited:
            continue
        visited.add(current)
        
        # Find what current calls
        calls = [r['to'] for r in relations 
                if r.get('relationType') == 'CALLS' 
                and current in r.get('from', '')]
        
        chain.extend([(current, c, level) for c in calls])
        queue.extend([(c, level + 1) for c in calls])
    
    return chain

# Example: Get what show_context_menu calls
chain = get_call_chain('Code.Method.*show_context_menu')
for caller, callee, level in chain:
    print(f"{'  ' * level}{caller} → {callee}")
```

### Integration with Memory System

| Aspect | project_memory.json | codegraph.json |
|--------|---------------------|----------------|
| **Focus** | Conceptual (features, patterns, decisions) | Physical (code structure, dependencies) |
| **Updates** | Manual (during LEARN phase) | Automated (regenerate script) |
| **Entity Types** | Project.Feature.*, Project.Method.* | Code.Module.*, Code.Class.* |
| **Purpose** | Knowledge capture, patterns | Dependency tracking, navigation |
| **Lifetime** | Persistent (never regenerated) | Regenerated on demand |
| **Size** | ~1-2 MB (curated entities) | ~0.5-10 MB (all code entities) |
| **Query Pattern** | Search for concepts/features | Search for code structure |

**Cross-Referencing**:
- Project memory entities reference code entities: `"Related code: Code.Class.commander_services_menu.MenuService"`
- Code graph provides implementation details for project features
- Use both together: project memory (what/why) + code graph (how)

---

## 🔗 Integration

### CI/CD Integration

**GitHub Actions Example**:
```yaml
# .github/workflows/codegraph.yml
name: Update Code Graph

on:
  push:
    branches: [main, develop]
  pull_request:

jobs:
  generate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Generate Code Graph
        run: python scripts/generate_codegraph.py --verbose
      
      - name: Upload Artifact
        uses: actions/upload-artifact@v3
        with:
          name: codegraph
          path: codegraph.json
      
      - name: Compare with Main
        if: github.event_name == 'pull_request'
        run: |
          # Download main branch graph
          git fetch origin main
          git show origin/main:codegraph.json > codegraph_main.json
          
          # Compare entity counts
          echo "Main branch entities:"
          grep -c '"type": "entity"' codegraph_main.json || echo "0"
          echo "PR branch entities:"
          grep -c '"type": "entity"' codegraph.json || echo "0"
```

**Pre-commit Hook**:
```yaml
# .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: generate-codegraph
        name: Generate Code Graph
        entry: python scripts/generate_codegraph.py
        language: system
        pass_filenames: false
        always_run: false  # Only on code changes
        files: ^src/.*\.py$
```

### Orchestrator Workflow Integration

**Phase 1: REMEMBER** (Initialization):
```python
# Load code graph structure at initialization
codegraph_index = load_codegraph_index('codegraph.json')
# → 749 entities, 5,114 relations loaded

# Index by type for fast queries
modules_index = index_by_type(codegraph_index, 'Module')     # 70 modules
classes_index = index_by_type(codegraph_index, 'Class')      # 83 classes
methods_index = index_by_type(codegraph_index, 'Method')     # 524 methods
```

**Phase 2: ASSESS** (Find Implementations):
```python
# Find existing implementations
existing_menu_classes = query_codegraph(
    codegraph_index, 
    "Code.Class.*menu*",
    case_insensitive=True
)
# → Returns: ContextMenuService, MenuService, etc.
```

**Phase 3: ANALYZE** (Trace Dependencies):
```python
# Trace import dependencies
imports = get_relations_by_type(
    codegraph_index,
    relation_type='IMPORTS',
    from_entity='Code.Module.commander_services_menu.File'
)
# → Returns all modules imported by menu service

# Follow call chains
call_chain = follow_calls(
    codegraph_index,
    start='Code.Method.*show_context_menu',
    depth=3
)
# → Returns complete invocation chain
```

**Phase 4: ARCHITECT** (Impact Analysis):
```python
# Find all downstream dependencies
affected = find_downstream_dependencies(
    codegraph_index,
    changed_module='Code.Module.commander_services_menu.File'
)
# → Returns all modules that import this module
# → Returns all classes/methods that call methods in this module
```

**Phase 5: IMPLEMENT** (Pattern Matching):
```python
# Find similar method signatures
similar_methods = find_methods_with_params(
    codegraph_index,
    params=['position', 'node', 'parent']
)
# → Returns methods with similar parameter patterns

# Check naming conventions
menu_methods = query_codegraph(
    codegraph_index,
    "Code.Method.*menu*"
)
# → Analyze naming patterns for consistency
```

### MCP Server Integration

The code graph can be exposed through Model Context Protocol for AI-assisted development:

**MCP Resource**:
```json
{
  "uri": "codegraph://logreport",
  "name": "LOGReport Code Structure",
  "description": "Complete code graph with 749 entities and 5,114 relations",
  "mimeType": "application/x-ndjson"
}
```

**MCP Tools**:
- `codegraph.query_entities` - Search for entities by pattern
- `codegraph.get_dependencies` - Get import dependencies for module
- `codegraph.trace_calls` - Follow function call chains
- `codegraph.find_implementations` - Find classes implementing interface
- `codegraph.analyze_impact` - Assess change impact

---

## 🌐 Universal Capabilities

### Cross-Project Usage

The generator is **portable** and works with any Python project:

**Step 1: Copy Generator**:
```bash
# Copy to target project
cp scripts/generate_codegraph.py /path/to/other/project/scripts/
```

**Step 2: Generate**:
```bash
cd /path/to/other/project
python scripts/generate_codegraph.py --src ./src --verbose
```

**Step 3: Customize Domain Mapping** (Optional):
```python
# Edit generate_codegraph.py: _build_domain_map()
def _build_domain_map(self) -> Dict[str, str]:
    return {
        # Add project-specific mappings
        'myfeature': 'MyFeature',
        'specialmodule': 'SpecialModule',
        # ... defaults ...
    }
```

### Multi-Project Code Graphs

Generate separate code graphs for different projects and compare:

```python
# Generate graphs
python generate_codegraph.py --src ./project_a/src --output graph_a.json
python generate_codegraph.py --src ./project_b/src --output graph_b.json

# Compare architectures
def compare_architectures(graph_a, graph_b):
    # Load both graphs
    entities_a = load_entities(graph_a)
    entities_b = load_entities(graph_b)
    
    # Compare metrics
    print(f"Project A: {len(entities_a)} entities")
    print(f"Project B: {len(entities_b)} entities")
    
    # Find common patterns
    patterns_a = extract_patterns(entities_a)
    patterns_b = extract_patterns(entities_b)
    common = set(patterns_a) & set(patterns_b)
    
    print(f"Common patterns: {common}")
```

### Customization Options

**Custom Domain Logic**:
```python
def _get_domain_from_path(self, path: str) -> str:
    # Custom domain detection logic
    if 'admin' in path:
        return 'Administration'
    if 'customer' in path:
        return 'CustomerManagement'
    # ... fall back to default
    return self._default_domain(path)
```

**Custom Cluster Naming**:
```python
def _get_cluster_from_path(self, module_path: str) -> str:
    parts = module_path.split('.')
    # Your custom logic
    if len(parts) >= 3:
        return f"{parts[0].capitalize()}.{parts[1]}.{parts[2]}"
    return f"Custom.{parts[0]}"
```

**Custom Observation Format**:
```python
def _create_class_entity(self, class_node, module_path):
    # Custom observation format
    observations = [
        f"Class: {class_node.name}",
        f"Module: {module_path}",
        f"LOC: {self._count_lines(class_node)}",  # Custom metric
        f"Complexity: {self._calculate_complexity(class_node)}",  # Custom metric
        f"upd:{datetime.now().strftime('%Y-%m-%d')},refs:0"
    ]
    # ...
```

---

## 💡 Best Practices

### Regeneration Strategy

**When to Regenerate**:
- ✅ **After feature implementation** - Capture new modules/classes
- ✅ **After refactoring** - Update structure changes
- ✅ **Weekly during active development** - Keep current
- ✅ **Before PR merge** - Ensure accurate for review
- ✅ **Before releases** - Snapshot final structure

**When NOT to Regenerate**:
- ❌ After comment-only changes
- ❌ After documentation updates
- ❌ After configuration changes (no code structure impact)
- ❌ After single-line bug fixes

### Exclude Patterns

**Always Exclude**:
```bash
python generate_codegraph.py \
  --exclude venv \
  --exclude .venv \
  --exclude build \
  --exclude dist \
  --exclude __pycache__ \
  --exclude .pytest_cache \
  --exclude migrations  # Django migrations
```

**Project-Specific Excludes**:
- Test fixtures: `--exclude fixtures`
- Generated code: `--exclude *_pb2.py` (protobuf)
- Vendor code: `--exclude vendor` or `--exclude third_party`
- Legacy code: `--exclude legacy` (if not actively maintained)

### Version Control

**Do NOT Commit** `codegraph.json`:
```gitignore
# .gitignore
codegraph.json
```

**Rationale**:
- Large file size (0.5-10 MB)
- Auto-generated (no manual edits)
- Changes on every code commit (noise)
- Regenerate on-demand or in CI

**Alternative**: Commit to separate branch for reference:
```bash
# Store in gh-pages or docs branch
git checkout gh-pages
python scripts/generate_codegraph.py
git add codegraph.json
git commit -m "Update code graph snapshot"
git push origin gh-pages
```

### Query Optimization

**Efficient Queries**:
```python
# ✅ GOOD: Specific pattern
entities = [e for e in entities if 'Code.Method.*MenuService' in e['name']]

# ❌ BAD: Load all, then filter
all_entities = load_all_entities()
menu_methods = [e for e in all_entities if 'MenuService' in e['name']]

# ✅ BETTER: Index by type first
methods = index_by_type(entities, 'Method')
menu_methods = [m for m in methods if 'MenuService' in m['name']]
```

**Precompute Indices**:
```python
# At initialization
indices = {
    'modules': index_by_type(entities, 'Module'),
    'classes': index_by_type(entities, 'Class'),
    'methods': index_by_type(entities, 'Method'),
    'by_domain': index_by_domain(entities),
    'imports': index_relations(relations, 'IMPORTS'),
    'calls': index_relations(relations, 'CALLS')
}

# Fast queries throughout workflow
menu_classes = [c for c in indices['classes'] if 'menu' in c['name'].lower()]
```

### Maintenance Schedule

**Daily** (if using pre-commit hook):
- Regenerate on code changes automatically

**Weekly** (active development):
- Manual regeneration
- Review new entities/relations
- Update project documentation if structure changed significantly

**Monthly** (stable projects):
- Regenerate and verify
- Archive snapshot for comparison
- Check for architectural drift

**Quarterly**:
- Deep analysis (complexity trends, dependency growth)
- Refactoring opportunities identification
- Architecture review with code graph as reference

### Troubleshooting

**No Output File**:
```bash
# Check permissions
ls -la codegraph.json

# Specify full path
python generate_codegraph.py --output /full/path/to/output.json

# Check for errors
python generate_codegraph.py --verbose
```

**Syntax Errors in Source Files**:
```
WARNING: Error processing file.py: invalid syntax (file.py, line 10)
```
- Fix syntax error in source file, or
- Add file to exclude patterns: `--exclude problematic_file.py`

**Missing Domains**:
```bash
# Run with verbose to see domain detection
python generate_codegraph.py --verbose

# Customize domain mapping in script if needed
```

**Slow Performance**:
```bash
# Exclude test files
python generate_codegraph.py --exclude test --exclude tests

# Exclude large generated directories
python generate_codegraph.py --exclude migrations --exclude vendor
```

**Empty Relations**:
- Check for relative imports (may not be detected)
- Verify AST parsing succeeded (check verbose logs)
- Some dynamic calls (getattr, exec) won't be captured

### Future Enhancements

**Planned**:
1. **Type annotations** - Extract parameter and return types
2. **Complexity metrics** - Cyclomatic complexity, LOC per entity
3. **Test coverage integration** - Link to test files, show coverage %
4. **Change tracking** - Track entity evolution over commits
5. **Interactive visualization** - Web-based graph explorer
6. **Dead code detection** - Identify unreferenced entities
7. **Circular dependency detection** - Flag architectural issues
8. **Multi-language support** - JavaScript, TypeScript, Java, C#

**Contribution Opportunities**:
- Add domain mappings for common frameworks (Django, Flask, FastAPI)
- Build visualization tools (D3.js, Graphviz, Cytoscape)
- Create MCP server integration
- Develop VS Code extension for inline navigation

---

## 📚 Related Documentation

**Architecture**:
- [ARCH_memory_system.md](../architecture/ARCH_memory_system.md) - 4-layer memory hierarchy and code memory layer
- [ARCH_chatmode_orchestrator.md](../architecture/ARCH_chatmode_orchestrator.md) - 11-phase workflow and code graph usage

**Implementation**:
- [IMPLEMENTATION_SUMMARY_codegraph.md](../implementation/IMPLEMENTATION_SUMMARY_codegraph.md) - Original implementation details
- [IMPLEMENTATION_SUMMARY_codegraph_integration.md](../implementation/IMPLEMENTATION_SUMMARY_codegraph_integration.md) - MCP integration
- [IMPLEMENTATION_SUMMARY_universal_codegraph.md](../implementation/IMPLEMENTATION_SUMMARY_universal_codegraph.md) - Universal capabilities

**Templates**:
- [memory_standards.md](../templates/memory_standards.md) - Memory system standards
- [document_standards.md](../templates/document_standards.md) - Documentation standards

**Project**:
- [README.md](../../README.md) - Project overview with code graph section
- [DOCUMENTATION_STRUCTURE.md](../DOCUMENTATION_STRUCTURE.md) - Documentation organization

---

**Script Location**: `scripts/generate_codegraph.py`  
**Output Location**: `codegraph.json` (project root, git-ignored)  
**Regeneration Frequency**: Weekly during active development, monthly for stable projects  
**License**: Portable - Copy freely to any project
