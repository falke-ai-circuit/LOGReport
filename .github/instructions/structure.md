---
applyTo: '**'
---

# Project Structure

## Directory Organization ⚠️ MANDATORY

**Root**: Config files ONLY (package.json, requirements.txt, pytest.ini, .gitignore, README.md, CHANGELOG.md, TODO.md, TASKS.md, ROADMAP.md, codegraph.json, project_memory.json)

```
src/{module}/          # Source (<500 lines/file): services/, presenters/, models/
tests/{module}/        # Mirror src/: test_{feature}.py
docs/                  # architecture/, blueprints/, technical/, user/, analysis/, implementation/, examples/
config/                # Configurations (*.yaml, *.json)
templates/             # Doc templates (memory_standards.md, documentation/*.md)
logs/                  # Workflow logs (git-excluded): workflow_*.md, *.log
misc/                  # scripts/ (*.ps1, *.bat, *.sh), temp/ (*_additions*.jsonl, *Copy.*), tools/
assets/                # Static resources (images, icons)
build/, dist/          # Build artifacts (auto-generated, git-excluded)
.github/               # chatmodes/, instructions/, global_memory.json (abstract patterns)
```

**Forbidden in Root**: test_*.py, *IMPLEMENTATION*.md, *SUMMARY*.md, *_additions*.jsonl, *.ps1, *.bat, sample data (*.sys, *.txt, *.json), temp files (*_temp*, *Copy*), backups (*.bak, *_backup*)

**HALT Behavior**: Validation fails → VIOLATIONS:[path:rule_violated→correct_path] → BLOCK creation (NOT create then move) → Wait for user/auto-correct → Resume after corrected

## File Placement by Phase ⚠️ ENFORCE STRICTLY

**Pre-Creation Validation (BLOCKING)**: ☐ Not in forbidden locations ☐ Routing correct ☐ Path matches type → Fail→VIOLATIONS:[path:wrong→correct],BLOCK,suggest

| Phase | Output Type | Location | Pattern |
|-------|-------------|----------|---------|
| **ANALYZE** | Analysis reports | `docs/analysis/` | `[topic]_analysis.md`, `[topic]_report.md` |
| **IMPLEMENT** | Source code | `src/{module}/` | `{module}/{feature}.py` |
| | Tests | `tests/` | `test_{feature}.py` |
| | Summaries | `docs/implementation/` | `IMPLEMENTATION_SUMMARY_[feature].md` |
| **TEST** | Test files | `tests/` | `test_{feature}.py` |
| | Reports | `misc/temp/` | `test_report_*.txt` |
| **DOCUMENT** | Core docs | `docs/{type}/` | `ARCH_*.md`, `TECH_*.md`, `BLUEPRINT_*.md`, `GUIDE_*.md` |
| **LEARN** | Memory temp | `misc/temp/` | `*_additions*.jsonl` |
| **LOG** | Workflow logs | `logs/` | `workflow_[feature]_[YYYYMMDD_HHMMSS].md` |
| **Scripts** | Utilities | `misc/scripts/` | `*.ps1`, `*.bat`, `*.sh` |
| **Examples** | Sample data | `docs/examples/` | `*.sys`, `*.pdf`, `*.json`, `*.txt` |

## Document Structure by Type

### Core Documentation
| Type | Location | Structure | Files |
|------|----------|-----------|-------|
| **ARCH** | `docs/architecture/` | Overview→Architecture→Components→Decisions→Implementation | System design, decisions, patterns |
| **BLUEPRINT** | `docs/blueprints/` | Overview→Requirements→Architecture→Plan→Testing→Resources | Implementation plans, phases |
| **TECH** | `docs/technical/` | Overview→Architecture→API→Config→Security→Performance | API specs, configs, procedures |
| **GUIDE** | `docs/user/` | Overview→Getting Started→Concepts→Procedures→Troubleshooting | User workflows, features |

### Workflow Documentation
| Type | Location | Lifecycle | Purpose |
|------|----------|-----------|---------|
| **Analysis** | `docs/analysis/` | 30 days → archive to `docs/archive/analysis/[YYYY-MM]/` | Pattern detection, root cause analysis |
| **Implementation** | `docs/implementation/` | 30 days → archive to `docs/archive/implementation/[YYYY-MM]/` | Feature summaries, integration notes |
| **Workflow Logs** | `logs/` | Git-excluded, local only | Session reconstruction, phase tracking |

**Rule**: NEVER delete → always archive | Integrate key insights to core docs during DOCUMENT phase

## Memory File Structure

### Memory Hierarchy
**Files**: `project_memory.json` (Project.* - root) | `.github/global_memory.json` (Global.* - abstract patterns) | `codegraph.json` (Code.* - root)  
**Pattern**: `[Type].[Domain].[Cluster].[EntityType]_[Name]` (MANDATORY 4 levels)  
**Relationship**: Project memory contains concrete implementations → Global memory distills abstract patterns for cross-project reuse

### Memory Organization
```
project_memory.json          # Project-specific entities (root)
├── Project.Frontend.*       # UI components, presenters, views
├── Project.Backend.*        # Services, models, data
├── Project.Integration.*    # Commands, handlers, interfaces
└── Project.Architecture.*   # Patterns, workflows, decisions

.github/global_memory.json   # Cross-project abstract patterns (config)
├── Global.Patterns.*        # Reusable approaches (distilled from projects)
├── Global.Tools.*           # Development utilities (universal)
└── Global.Workflows.*       # Process templates (cross-project)

codegraph.json              # Code structure entities (root)
├── Code.Module.*           # File-level modules
├── Code.Class.*            # Class definitions
└── Code.Method.*           # Function/method signatures
```

**Update Rules**: 
- **LEARN phase**: Extract 3+ entities → temp JSONL → append project_memory → verify line count → cleanup
- **update_memory workflow**: Distill project patterns → abstract → append global_memory → verify ratios → cleanup
- **Distillation**: Project-specific→Universal | Implementation→Pattern | Concrete→Abstract | Context-dependent→Context-agnostic

### Codegraph Structure
**NEW files**: Module + Class + Methods | **MODIFIED files**: Update Module entity | **Metadata**: `upd:YYYY-MM-DD,refs:0`  
**Relations**: BELONGS_TO (Class→Module, Module→Domain) | IMPORTS (Module→Module) | INHERITS (Class→Class) | DOCUMENTED_IN (Code→Doc)

## Naming Conventions

**Files**: `{TYPE}_{subject}.md` (lowercase, NO versions) | `test_{feature}.py` | `workflow_{feature}_{YYYYMMDD_HHMMSS}.md`  
**Code**: PascalCase (classes) | snake_case (functions/methods) | UPPER_SNAKE_CASE (constants)  
**Memory**: `[Type].[Domain].[Cluster].[EntityType]_[Name]` (e.g., `Project.Frontend.NodeTree.Feature_ColorCoding`)

## Size Limits

**Source**: <500 lines/file | **Observations**: 80-120 chars | **Codegraph descriptions**: 1-3 lines
**Memory Limits**: <3000 lines (recommended) | <5000 lines (hard limit, triggers auto-optimizer)  
**Codegraph Limits**: <100KB file size | <150 entities (recommended: <100)  
**JSON Limits**: <10MB serialized size (pre-write size check required)

## Instruction File Limits ⚠️ MAINTAIN

**Optimal Line Counts** (updated 2025-10-19):

| File | Current | Optimal Range | Hard Max | Purpose |
|------|---------|---------------|----------|---------|
| **chatmode.md** | 117 | 60-120 | 130 | High-level overview, must stay lean |
| **phases.md** | 97 | 70-100 | 120 | Phase workflow specifications |
| **standards.md** | 107 | 70-110 | 130 | Quality standards, format templates |
| **protocols.md** | 107 | 75-120 | 150 | Core protocol definitions (densest) |
| **structure.md** | 120 | 70-100 | 110 | File organization reference |
| **examples.md** | 155 | 100-150 | 180 | Pattern demonstrations (teaching) |
| **TOTAL** | **703** | **445-700** | **820** | Full instruction set |

**Token Budget**: Current ~9.8K tokens | Optimal 8K-12K | Hard Max 15K tokens

**Growth Management**: Archive old examples → Compress prose to tables → Split if >hard max → One source of truth per concept

**Review Triggers**: Single file >optimal → Total >12K tokens → Compliance degradation detected