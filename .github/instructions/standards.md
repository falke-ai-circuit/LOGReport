---
applyTo: '**'
---

# Project Standards

## 4-Layer Memory System

**Pattern**: `[Type].[Domain].[Cluster].[EntityType]_[Name]` (MANDATORY 4 levels, no orphans)  
**Files**: `project_memory.json` (Project.*) | `global_memory.json` (Global.*) | `codegraph.json` (Code.*)

### Components
**Type**: Project | Global | Code | Tool | Config  
**Domain**: Frontend | Backend | Architecture | Data | DevOps | Integration | Commander | Core | Services  
**Cluster**: UI | API | Testing | Database | CI | Command | ContextMenu | NodeTree | etc.  
**EntityType**: Component | Service | Pattern | Workflow | Model | Handler | Tool | Config | Module | Class | Method | Function

### Validation
✅ 4-layer path | 80-120 char observations | 8 metadata fields (created, modified, accessed, refs, usage, path, hash, obs_check) | hierarchy connections  
❌ Missing layers | >120 chars | orphaned entities | vague names

## Memory Templates

### Project Memory
`{"type":"entity", "name":"Project.[Domain].[Cluster].[Name]", "entityType":"[Type]", "observations":["Description with architecture/implementation details.", "Integration: signals/handlers/components used.", "created:YYYY-MM-DD,modified:YYYY-MM-DD,refs:0"]}`

### Codegraph Module
`{"type":"entity","name":"Code.Module.{path}","entityType":"Module","observations":["{description} | {N} class, {M} funcs, uses {frameworks}","Methods: {signatures}","Deps: {imports}","upd:YYYY-MM-DD,refs:0"]}`

### Codegraph Class
`{"type":"entity","name":"Code.Class.{path}.{ClassName}","entityType":"Class","observations":["{purpose} | extends {base}","upd:YYYY-MM-DD,refs:0"]}`

### Relations
**Required**: BELONGS_TO (Module→Domain, Class→Module) | IMPORTS (Module→Module)  
**Rules**: Read codegraph.json examples first | Match existing format exactly

## Documentation Standards

### Templates by Type
| Type | Location | Structure | Purpose |
|------|----------|-----------|---------|
| **ARCH** | `docs/architecture/` | Overview→Architecture→Components→Decisions→Implementation | System design, architectural decisions, patterns |
| **BLUEPRINT** | `docs/blueprints/` | Overview→Requirements→Architecture→Plan→Testing→Resources | Implementation plans, project phases |
| **TECH** | `docs/technical/` | Overview→Architecture→API→Config→Security→Performance | API specs, configurations, technical procedures |
| **GUIDE** | `docs/user/` | Overview→Getting Started→Concepts→Procedures→Troubleshooting | User workflows, features, how-to guides |

**Rules**: Sync with code | Document all public APIs | Include usage examples | Update in DOCUMENT phase

## Quality Standards

**Code**: <500 lines/file | Single responsibility | Understandable by future devs | Efficient (not premature) | Validate inputs | Graceful error handling  
**Testing**: 100% pass MANDATORY | Unit + Integration + Edge cases | `python -m pytest <test_file> -v` | ALL tests pass (9/9, not 5/9) | Failed = return to DEBUG  
**Documentation**: Sync with code | All public APIs documented | Include examples | Update in DOCUMENT phase  
**Logging**: Structured format | Capture all phase completions | Session records in `logs/workflow_*.md` | Chronological reconstruction

## Codegraph Standards

**Update Triggers**: NEW files (Module + Class + Methods) | MODIFIED files (update Module entity)  
**Content**: 1-3 lines max | Structure + dependencies + purpose only | Match existing tone  
**Metadata**: `upd:YYYY-MM-DD,refs:0` (MANDATORY)

**Update Process**: Read existing entries → extract/update entities → create temp JSONL → append to codegraph.json → verify line count → cleanup

## Communication Standards

**Phase Indicators**: 📋 PLAN | 🧠 REMEMBER | 🔍 ASSESS | 🔬 ANALYZE | 🏗️ ARCHITECT | 💻 IMPLEMENT | 🐛 DEBUG | 🧪 TEST | 🎓 LEARN | 📚 DOCUMENT | 📝 LOG

**Status Format**:
```
STATUS: [completed|partial|failed]
PHASE: [PHASE_NAME]
TASKS: [phase_list with current phase: completed, others: pending/done]
DISCOVERIES: [key_findings + insights + decisions]
BLOCKERS: [none|specific_issues]
NEXT: [proceed_to_next_phase|alternative_action]
```

**Optional Fields**: `CEPH:[context]` (ASSESS+) | `MEMORY:[entities_loaded]` (REMEMBER) | `LEARNINGS:[pattern:[X] | approach:[Y]]` (specialist phases) | `ARTIFACTS:[type:path:description]` (IMPLEMENT, TEST, LEARN, DOCUMENT) | `METRICS:[measurement_with_deltas]` (TEST, MUST include Δ) | `DOCUMENT:[updates]` (DOCUMENT) | `HANDOFFS:[future_patterns]` (LOG)

## Format Requirements ⚠️ MANDATORY

### Metrics (TEST Phase)
**Rule**: ALWAYS include (Δ±X%) or (+N) showing change from baseline

✅ `METRICS:[coverage=95%(+15%) src:pytest scope:unit | tests=9/9(+9) src:pytest scope:integration]`  
❌ `METRICS:[coverage=95% | tests=9/9]` (missing +Δ deltas)

**First Implementation**: Use (+N) showing new additions

### Learnings (Specialist Phases)
**Rule**: ALWAYS use `pattern:[X] | approach:[Y]` with pipe separator

✅ `LEARNINGS:[pattern:[Centralized validation for DRY] | approach:[Color coding in populate_node_list for real-time feedback]]`  
❌ Free-form text, bullet points, or paragraphs without pattern:|approach: structure