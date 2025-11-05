---
applyTo: '**'
---

# Project Standards

## 4-Layer Memory System

**Pattern**: `[Type].[Domain].[Cluster].[EntityType]_[Name]` (MANDATORY 4 levels, no orphans)  
**Files**: `project_memory.json` (Project.*) | `global_memory.json` (Global.*) | `codegraph.json` (Code.*)

**Components**: Type (Project|Global|Code|Tool|Config) | Domain (Frontend|Backend|Architecture|Data|DevOps|Integration|Commander|Core|Services) | Cluster (UI|API|Testing|Database|CI|Command|ContextMenu|NodeTree) | EntityType (Component|Service|Pattern|Workflow|Model|Handler|Tool|Config|Module|Class|Method|Function)

**Validation**: ✅ 4-layer path, 80-120 char observations, 8 metadata fields (created/modified/accessed/refs/usage/path/hash/obs_check), hierarchy connections | ❌ Missing layers, >120 chars, orphaned entities, vague names

## Memory Templates

**Project**: `{"type":"entity", "name":"Project.[Domain].[Cluster].[Name]", "entityType":"[Type]", "observations":["Description with architecture/implementation.", "Integration: signals/handlers/components.", "created:YYYY-MM-DD,modified:YYYY-MM-DD,refs:0"]}`

**Codegraph**: `{"type":"entity","name":"Code.Module.{path}","entityType":"Module","observations":["{description} | {N} class, {M} funcs","upd:YYYY-MM-DD,refs:0"]}`

**Relations**: Required (BELONGS_TO:Module→Domain,Class→Module | IMPORTS:Module→Module) | Rules: Read codegraph.json examples first, match existing format exactly

## Standards

**Code**: <500 lines/file | Single responsibility | Understandable | Efficient | Validate inputs | Graceful errors  
**Testing**: 100% pass MANDATORY | Unit+Integration+Edge | `pytest <file> -v` | ALL pass (9/9 not 5/9) | Fail→DEBUG  
**Documentation**: Sync with code | All public APIs | Include examples | Update in DOCUMENT phase  
**Logging**: Structured | Capture all phase completions | Session records `logs/workflow_*.md` | Chronological

**Doc Templates**: ARCH (`docs/architecture/`: Overview→Architecture→Components→Decisions→Implementation) | BLUEPRINT (`docs/blueprints/`: Overview→Requirements→Architecture→Plan→Testing→Resources) | TECH (`docs/technical/`: Overview→Architecture→API→Config→Security→Performance) | GUIDE (`docs/user/`: Overview→Start→Concepts→Procedures→Troubleshooting)

**Codegraph**: Triggers (NEW→Module+Class+Methods | MODIFIED→update Module) | Content (1-3 lines max, structure+deps+purpose, match tone) | Metadata (`upd:YYYY-MM-DD,refs:0` MANDATORY) | Process (read existing→extract/update→temp JSONL→append→verify→cleanup)

## Communication Standards

**Phases**: 📋PLAN | 🧠REMEMBER | 🔍ASSESS | 🔬ANALYZE | 🏗️ARCHITECT | 💻IMPLEMENT | 🐛DEBUG | 🧪TEST | 🎓LEARN | 📚DOCUMENT | 📝LOG

**Status**:
```
STATUS: [complete|partial|failed]
PHASE: [NAME]
TASKS: [phase_list with current→completed/pending/done]
DISCOVERIES: [key_findings+insights+decisions]
BLOCKERS: [none|specific_issues]
NEXT: [next_phase|alternative]
```

**Optional**: STACK:[breadcrumb](depth:N) (index≥1) | CEPH:[context] (ASSESS+) | MEMORY:[entities] (REMEMBER) | LEARNINGS:[pattern:[X]|approach:[Y]] (specialist) | ARTIFACTS:[type:path:desc] (IMPLEMENT/TEST/LEARN/DOCUMENT) | METRICS:[measurement_with_Δ] (TEST, MANDATORY Δ) | DOCUMENT:[updates] (DOCUMENT) | COMMIT:[type(scope):message] (LOG/FINALIZE) | HANDOFFS:[future_patterns] (LOG) | ADJUST:[drift→correction] (SCP-PHASE self-regulation)

## Format Requirements ⚠️ MANDATORY

**NWP**: Use NWP (Nested Workflow Procedure) for workflow nesting | NEST/RETURN operations | Stack notation with → arrows  
✅ `[SCP-NWP: 🔄NEST→test_failure | 📚INDEX:[0→1] | 🎯REASON:validation_failed | 📍FROM:IMPLEMENT | 🗂️PHASES:[1,2,6,7,8]]`  
✅ `[SCP-NWP: 🔄RETURN←test_failure | 📚INDEX:[1→0] | ✅RESOLVED | 📍RESUME:IMPLEMENT | 🔄MERGE:[CEPH+learnings]]`  
❌ Freeform context switching without NWP protocol

**Structure Validation**: Protocol tag:[SCP-*] (NOT SCP-*,(SCP-*),{SCP-*}) | Field separator:colon field:value (NOT =,-) | Multi-value:pipe val1|val2 (NOT comma,semicolon) | Emoji: ✅🚫🎯🔧
**Escaping**: Brackets:\[,\] | Pipes:\| | Colons:\: | Example:`DISCOVERIES:[test_data:\{key\:value\}|count\:5]`
**Position (MANDATORY)**: Protocol tag MUST be first line | ❌ "Analyzing... [SCP-PHASE:...]" | ✅ "[SCP-PHASE:...]\nAnalyzing..."

**Metrics (TEST)**: ALWAYS include (Δ±X%) or (+N) showing change from baseline  
✅ `METRICS:[coverage=95%(+15%)|tests=9/9(+9)]`  
❌ `METRICS:[coverage=95%|tests=9/9]` (missing Δ)

**Learnings (Specialist)**: ALWAYS use `pattern:[X]|approach:[Y]` with pipe separator  
✅ `LEARNINGS:[pattern:[Centralized validation]|approach:[Color coding feedback]]`  
❌ Freeform text without pattern:|approach: structure

**Commit (LOG/FINALIZE)**: `type(scope): brief summary` imperative | Types: feat|fix|refactor|docs|test|chore|perf|style | Length: 50-72 chars  
✅ `COMMIT:[feat(classifier): add pattern discovery]` | `COMMIT:[fix(gui): remove duplicate method]`  
❌ Long-winded | Past tense | Vague

**ADJUST (SCP-PHASE)**: `drift_type→correction_action` or `none` | Scope: SCP-PHASE=compliance drift at phase gates | Usage: Auto-correction, prevents protocol abandonment  
✅ `🔧ADJUST:[none]` | `🔧ADJUST:[query_deficit→add_BELONGS_TO+IMPORTS]` | `🔧ADJUST:[skipped_IMPLEMENT→return_to_phase_5]` | `🔧ADJUST:[test_fail_no_NEST→emit_NEST_now]`  
❌ Generic "fix it" without drift→action mapping | Vague corrections

## Language Standards

**Active Voice**: Use for all actions, implementations, completions | ✅ "Updated classifier" ❌ "I've updated the classifier"  
**Questions**: Allowed for genuine ambiguity requiring user decision | ✅ "Continue with approach A or pivot to B?" ❌ "Would you like me to continue?"  
**Hedging**: Eliminate in action statements | ✅ "Analyzing patterns" ❌ "Let me analyze patterns"