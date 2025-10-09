# Code Graph Guide

**Version**: 1.0  
**Last Updated**: 2025-10-09

## Overview

`codegraph.json` is an automatically-generated hierarchical representation of the entire `src/` codebase. It mirrors the structure of `project_memory.json` but focuses on actual code entities (modules, classes, functions, methods) and their dependencies.

## Purpose

- **Code Navigation**: Understand code structure and relationships
- **Dependency Tracking**: See what imports what, what calls what
- **Architecture Visualization**: Get a bird's-eye view of the codebase
- **Refactoring Support**: Identify impacts of changes
- **Documentation**: Auto-generated code structure reference

## Structure

### Hierarchy (6 Layers)

```
Code.Type.Codebase                          (Root Type)
  └─ Code.Domain.{domain}                   (Domain: Core, Commander, Services, etc.)
      └─ Code.Cluster.{cluster}             (Cluster: grouping of related modules)
          └─ Code.Module.{module}.File      (Module: Python file)
              ├─ Code.Class.{module}.{class}         (Class definition)
              │   └─ Code.Method.{module}_{class}.{method}  (Method in class)
              └─ Code.Function.{module}.{function}   (Top-level function)
```

### Entity Types

| Entity Type | Description | Example |
|-------------|-------------|---------|
| **Type** | Root codebase type | `Code.Type.Codebase` |
| **Domain** | Functional domain | `Code.Domain.Commander` |
| **Cluster** | Module grouping | `Code.Cluster.Commander.Services` |
| **Module** | Python file | `Code.Module.commander_services_context_menu_service.File` |
| **Class** | Class definition | `Code.Class.commander_services_context_menu_service.ContextMenuService` |
| **Method** | Class method | `Code.Method.commander_services_context_menu_service_ContextMenuService.show_context_menu` |
| **Function** | Top-level function | `Code.Function.utils_file_utils.filter_lines` |

### Relation Types

| Relation | Description | Example |
|----------|-------------|---------|
| **BELONGS_TO** | Hierarchical containment | Method → Class → Module → Cluster → Domain |
| **IS_A** | Type relationship | Domain → Type |
| **IMPORTS** | Import dependency | Module A imports Module B |
| **CALLS** | Function call | Function A calls Function B |
| **INHERITS** | Class inheritance | Class A inherits from Class B |

## Generated Statistics

Based on current codebase (`src/` folder):

- **Total Entities**: 749
- **Total Relations**: 5,114
- **Modules**: 70
- **Classes**: 83
- **Methods**: 524
- **Functions**: 38
- **Domains**: 12
- **Clusters**: 33

### Relation Breakdown

- **CALLS**: 3,635 (function/method invocations)
- **BELONGS_TO**: 745 (hierarchical structure)
- **IMPORTS**: 682 (module dependencies)
- **INHERITS**: 49 (class inheritance)
- **IS_A**: 3 (domain-to-type)

## Usage

### Generate Code Graph

```powershell
# Run the generator script
python scripts\generate_codegraph.py

# Output: codegraph.json (root directory)
```

### Regenerate After Code Changes

The codegraph should be regenerated after:
- Adding new modules, classes, or functions
- Significant refactoring
- Changing import structure
- Major architectural changes

**Recommendation**: Run weekly or after major feature additions.

### Query Examples

#### Find all methods in a class
```powershell
Get-Content codegraph.json | Select-String 'Code.Method.*ContextMenuService'
```

#### Find what a module imports
```powershell
Get-Content codegraph.json | Select-String '"from": "Code.Module.context_menu_service.*IMPORTS"'
```

#### Find all classes that inherit from a base
```powershell
Get-Content codegraph.json | Select-String '"relationType": "INHERITS".*QMainWindow'
```

#### Count methods per domain
```powershell
Get-Content codegraph.json | Select-String 'Code.Method' | Measure-Object
```

## Entity Observations

Each entity includes metadata observations:

### Module
- File path (relative to `src/`)
- Module import path
- Module docstring (first line, max 120 chars)
- Update date and reference count

### Class
- Containing module
- Class docstring (first line, max 120 chars)
- Base classes (inheritance)
- Method count
- Update date and reference count

### Method/Function
- Containing module/class
- Docstring (first line, max 120 chars)
- Parameters (first 5 shown)
- Decorators (if any)
- Update date and reference count

## Integration with Project Memory

While `project_memory.json` tracks **conceptual** entities (features, bugs, decisions), `codegraph.json` tracks **code** entities (modules, classes, functions).

| Aspect | project_memory.json | codegraph.json |
|--------|---------------------|----------------|
| **Focus** | Conceptual (features, patterns, decisions) | Physical (code structure) |
| **Updates** | Manual (during LEARN phase) | Automated (script) |
| **Entities** | Project.Feature.*, Project.Method.* | Code.Module.*, Code.Class.* |
| **Purpose** | Knowledge capture, patterns | Dependency tracking, navigation |
| **Lifetime** | Persistent (never regenerated) | Regenerated on demand |

## Maintenance

### Script Location
`scripts/generate_codegraph.py`

### Excluded Paths
- `__pycache__/`
- `.egg-info/`
- Files with syntax errors (logged as warnings)

### Error Handling
- Syntax errors in files: logged as WARNING, file skipped
- Missing docstrings: defaults to "{name} class/function"
- Unparseable AST nodes: gracefully skipped

## Visualization Potential

The codegraph can be used to generate:
- **Dependency graphs** (using Graphviz, D3.js)
- **Module relationship diagrams**
- **Class hierarchy trees**
- **Call graphs** (function invocation chains)
- **Import dependency maps**

## Future Enhancements

Potential improvements:
1. **Type annotations**: Extract parameter and return types
2. **Complexity metrics**: Add cyclomatic complexity, lines of code
3. **Test coverage**: Link to test files
4. **Change history**: Track entity evolution over commits
5. **Interactive explorer**: Web-based graph visualization
6. **Dead code detection**: Identify unreferenced entities
7. **Circular dependency detection**: Flag architectural issues

## Related Documentation

- [Memory Standards](../templates/memory_standards.md) - Project memory structure
- [Architectural Design Proposal](../arch/architectural_design_proposal.md) - System architecture
- [README.md](../../README.md) - Project overview

---

**Note**: This is an automated code analysis artifact. Do not edit `codegraph.json` manually - regenerate using the script.
