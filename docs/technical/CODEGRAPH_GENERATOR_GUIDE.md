# Code Graph Generator - Universal & Portable

**Version**: 1.0  
**Last Updated**: 2025-10-09

## Overview

The Code Graph Generator is a **universal, portable Python script** that scans any Python codebase and generates a hierarchical structure representation (`codegraph.json`). It automatically detects project structure, creates proper domain/cluster hierarchies, and tracks all code entities and their relationships.

## Key Features

### ✨ Universal & Portable
- **Zero project-specific dependencies**: Works with any Python project
- **Auto-detection**: Discovers folder structure and creates appropriate domains
- **Configurable**: Command-line arguments for customization
- **Smart defaults**: Works out-of-the-box with sensible defaults

### 📊 Comprehensive Analysis
- **Entities**: Modules, classes, methods, functions (with metadata)
- **Relations**: Imports, calls, inheritance, hierarchical structure
- **6-Layer Hierarchy**: Type → Domain → Cluster → Module → Class → Method/Function

### 🛡️ Robust Error Handling
- **Syntax error tolerance**: Logs errors, continues processing
- **Exclude patterns**: Skip unwanted directories automatically
- **Validation**: Ensures proper hierarchy compliance

## Installation

### Prerequisites
- Python 3.7+
- Standard library only (no external dependencies)

### Setup
1. Copy `generate_codegraph.py` to your project's scripts folder
2. Run directly - no installation needed!

```bash
# Option 1: Copy to scripts folder
cp generate_codegraph.py /path/to/your/project/scripts/

# Option 2: Use from anywhere (make executable)
chmod +x generate_codegraph.py
./generate_codegraph.py --src /path/to/project/src
```

## Usage

### Basic Usage

```bash
# Scan ./src (or current directory if no src/)
python generate_codegraph.py

# Specify source directory
python generate_codegraph.py --src ./myapp

# Custom output path
python generate_codegraph.py --output ./my_graph.json

# Verbose mode (see auto-detection)
python generate_codegraph.py --verbose
```

### Advanced Usage

```bash
# Exclude additional patterns
python generate_codegraph.py --exclude test --exclude migrations

# Full custom configuration
python generate_codegraph.py \
  --src ./backend/api \
  --output ./docs/api_graph.json \
  --exclude __pycache__ \
  --exclude .pytest_cache \
  --verbose
```

### Command-Line Options

| Option | Description | Default |
|--------|-------------|---------|
| `--src PATH` | Source directory to scan | `./src` (or `./` if no src/) |
| `--output PATH` | Output file path | `./codegraph.json` |
| `--exclude PATTERN` | Exclude pattern (repeatable) | See default excludes below |
| `--verbose` | Enable verbose logging | Disabled |
| `--version` | Show version | - |
| `--help` | Show help message | - |

### Default Exclude Patterns

The following patterns are excluded by default:
- `__pycache__`
- `.egg-info`
- `venv`
- `.venv`
- `env`
- `.env`
- `build`
- `dist`
- `.git`

Use `--exclude` to add more patterns (defaults are always included).

## Auto-Detection

### Domain Detection

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

**Custom Folders**: Any folder not in the map is automatically added with a capitalized domain name.

### Cluster Detection

Clusters are created from the first two path levels:

```
src/commander/services/menu.py
    ↓
Domain: Commander
Cluster: Commander.Services
Module: commander.services.menu
```

## Output Structure

### Hierarchy (6 Layers)

```
Code.Type.Codebase                          (1 entity)
  └─ Code.Domain.{domain}                   (N entities)
      └─ Code.Cluster.{cluster}             (N entities)
          └─ Code.Module.{module}.File      (N entities)
              ├─ Code.Class.{class}         (N entities)
              │   └─ Code.Method.{method}   (N entities)
              └─ Code.Function.{function}   (N entities)
```

### Entity Types

| Type | Count Example | Description |
|------|---------------|-------------|
| **Type** | 1 | Root codebase type |
| **Domain** | 3-10 | Functional domains |
| **Cluster** | 10-50 | Module groupings |
| **Module** | 50-200 | Python files |
| **Class** | 50-300 | Class definitions |
| **Method** | 200-1000 | Methods in classes |
| **Function** | 10-100 | Top-level functions |

### Relation Types

| Type | Description | Example |
|------|-------------|---------|
| **BELONGS_TO** | Hierarchical containment | Method → Class → Module → Cluster → Domain → Type |
| **IS_A** | Type relationship | Domain → Type |
| **IMPORTS** | Module dependencies | `module_a` imports `module_b` |
| **CALLS** | Function invocations | `func_a` calls `func_b` |
| **INHERITS** | Class inheritance | `ClassA` inherits from `ClassB` |

### Entity Metadata

Each entity includes observations:

#### Module
```json
{
  "type": "entity",
  "name": "Code.Module.myapp_services_auth.File",
  "entityType": "Module",
  "observations": [
    "File: myapp/services/auth.py",
    "Module: myapp.services.auth",
    "Authentication service module",
    "upd:2025-10-09,refs:0"
  ]
}
```

#### Class
```json
{
  "type": "entity",
  "name": "Code.Class.myapp_services_auth.AuthService",
  "entityType": "Class",
  "observations": [
    "Class in myapp.services.auth",
    "Handles user authentication and authorization",
    "Inherits: BaseService",
    "Methods: 12",
    "upd:2025-10-09,refs:0"
  ]
}
```

#### Method
```json
{
  "type": "entity",
  "name": "Code.Method.myapp_services_auth_AuthService.authenticate",
  "entityType": "Method",
  "observations": [
    "Method in myapp.services.auth",
    "Authenticate user with credentials",
    "Params: username, password, remember_me",
    "Decorators: @validate_input",
    "upd:2025-10-09,refs:0"
  ]
}
```

## Integration

### With Existing Projects

#### Step 1: Copy Script
```bash
# Copy to your project
cp generate_codegraph.py /your/project/scripts/
```

#### Step 2: Generate
```bash
cd /your/project
python scripts/generate_codegraph.py --verbose
```

#### Step 3: Verify
```bash
# Check output
ls -lh codegraph.json

# Quick stats
grep -c '"type": "entity"' codegraph.json
grep -c '"type": "relation"' codegraph.json
```

### With CI/CD

Add to your CI pipeline to track code structure changes:

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
```

### With Pre-commit Hooks

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
        always_run: true
```

## Query Examples

### PowerShell
```powershell
# Find all classes
Get-Content codegraph.json | Select-String '"entityType": "Class"'

# Count methods
(Get-Content codegraph.json | Select-String '"entityType": "Method"').Count

# Find imports for a module
Get-Content codegraph.json | Select-String '"from": "Code.Module.auth.*IMPORTS'

# Find what calls a function
Get-Content codegraph.json | Select-String '"to": "Code.Method.*authenticate.*CALLS'
```

### Bash
```bash
# Find all classes
grep '"entityType": "Class"' codegraph.json

# Count methods
grep -c '"entityType": "Method"' codegraph.json

# Find imports
grep '"from": "Code.Module.auth.*IMPORTS' codegraph.json

# Find callers
grep '"to": "Code.Method.*authenticate.*CALLS' codegraph.json
```

### Python
```python
import json

# Load graph
with open('codegraph.json') as f:
    lines = f.readlines()

entities = [json.loads(line) for line in lines if '"type": "entity"' in line]
relations = [json.loads(line) for line in lines if '"type": "relation"' in line]

# Find all classes
classes = [e for e in entities if e.get('entityType') == 'Class']
print(f"Total classes: {len(classes)}")

# Find imports for a module
imports = [r for r in relations if r.get('relationType') == 'IMPORTS']
print(f"Total imports: {len(imports)}")

# Find call chains
calls = [r for r in relations if r.get('relationType') == 'CALLS']
print(f"Total function calls: {len(calls)}")
```

## Customization

### Custom Domain Mapping

Edit `_build_domain_map()` in the script to add project-specific mappings:

```python
def _build_domain_map(self) -> Dict[str, str]:
    domain_map = {
        # Add your custom mappings
        'myfeature': 'MyFeature',
        'specialmodule': 'SpecialModule',
        # ... defaults ...
    }
    return domain_map
```

### Custom Cluster Logic

Edit `_get_cluster_from_path()` to change cluster naming:

```python
def _get_cluster_from_path(self, module_path: str) -> str:
    parts = module_path.split('.')
    # Your custom logic here
    return f"Custom.{parts[0]}"
```

## Troubleshooting

### No Output File
```bash
# Check permissions
ls -la codegraph.json

# Specify full path
python generate_codegraph.py --output /full/path/to/output.json
```

### Syntax Errors in Source
```
WARNING: Error processing file.py: syntax error
```
**Solution**: File is logged and skipped. Fix syntax or add to excludes.

### Missing Domains
```bash
# Run with verbose to see domain map
python generate_codegraph.py --verbose
```
**Solution**: Add custom mappings in `_build_domain_map()`.

### Slow Performance
```bash
# Exclude test files
python generate_codegraph.py --exclude test --exclude tests

# Exclude large directories
python generate_codegraph.py --exclude migrations --exclude vendor
```

## Best Practices

### When to Regenerate
- After adding new modules/classes
- After significant refactoring
- Weekly (for active development)
- Before major releases

### Exclude Patterns
Always exclude:
- Virtual environments (`venv`, `.venv`)
- Build artifacts (`build/`, `dist/`)
- Test fixtures (`fixtures/`, `test_data/`)
- Generated code (`*_pb2.py`, `migrations/`)

### CI Integration
- Run on every PR to track structure changes
- Store as artifact for review
- Compare with main branch to show impact

### Version Control
- **Don't commit** `codegraph.json` (too large, auto-generated)
- Add to `.gitignore`
- Generate on-demand or in CI

## Performance

| Project Size | Files | Time | Output Size |
|--------------|-------|------|-------------|
| Small | 10-50 | <1s | 10-50 KB |
| Medium | 50-200 | 1-5s | 50-500 KB |
| Large | 200-500 | 5-15s | 500KB-2MB |
| Very Large | 500+ | 15-60s | 2-10MB |

## Limitations

- **Python only**: Only analyzes Python files (.py)
- **Syntax required**: Files with syntax errors are skipped
- **No type inference**: Does not resolve dynamic types
- **Simple call detection**: May miss indirect calls (getattr, etc.)

## Future Enhancements

Potential improvements:
1. Multi-language support (JavaScript, TypeScript, Java)
2. Type annotation extraction
3. Complexity metrics (cyclomatic complexity, LOC)
4. Dead code detection
5. Circular dependency warnings
6. Interactive visualization
7. Diff mode (compare two graphs)

## Related Documentation

- [Code Graph Guide](CODEGRAPH_GUIDE.md) - Usage and query examples
- [Code Graph Integration](../../IMPLEMENTATION_SUMMARY_codegraph_integration.md) - Unified.chatmode integration

---

**Script Location**: `scripts/generate_codegraph.py`  
**License**: Portable - Copy freely  
**Version**: 1.0
