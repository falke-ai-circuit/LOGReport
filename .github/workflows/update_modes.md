# Update Modes Workflow

**Purpose**: Chatmode optimization via workflow log analysis→instruction refinement | **Input**: User specifies target chatmode file | **Focus**: Completion format compliance + field quality analysis → instruction enhancements | **Log Source**: `/logs/workflow_*.md` (batch processing) | **Output**: Optimized chatmode with compliance improvements | **Target**: Compliance ≥90% + Field quality + BLOCKER reduction

## 6-Phase Architecture

| Phase | Objective | Output |
|-------|-----------|--------|
| 0 | Workflow Discovery | Inventory of workflow logs with metadata |
| 1 | Completion Analysis | Field presence rates + compliance scoring |
| 2 | Chatmode Evaluation | Instruction gaps + quality issues mapped |
| 3 | Optimization Planning | Prioritized improvement recommendations |
| 4 | Instruction Updates | Enhanced chatmode with examples + templates |
| 5 | Validation | Compliance improvement measurement |

## Parameters

**User Input**: Target chatmode file path (e.g., `.github/chatmodes/DevTeam.chatmode.md`) | **Logs**: `/logs/workflow_*.md` (all or recent N) | **Analysis**: Field compliance + CEPH/METRICS/LEARNINGS quality + BLOCKER patterns | **Targets**: Compliance ≥90% | Field quality ≥85% | BLOCKER reduction ≥30% | **Style Preservation**: Minimal additions + respect original tone/format + detect unnecessary instructions + simplify without precision loss | **Output**: `/logs/chatmode_optimization_[chatmode_name]_[date].md`

## Execution Pattern

```bash
# Usage: Specify target chatmode file
TARGET_CHATMODE="[path/to/chatmode.md]"  # e.g., .github/chatmodes/DevTeam.chatmode.md

# Phase 0: Discovery
Scan logs/workflow_*.md → Extract metadata → Sort by timestamp

# Phase 1-2: Analysis  
Parse completion formats → Score field compliance → Map to chatmode instructions → Identify gaps

# Phase 3: Planning
Prioritize improvements (Critical→High→Medium→Low) → Generate recommendations

# Phase 4: Implementation
Update chatmode instructions → Add templates/examples → Strengthen requirements

# Phase 5: Validation
Measure predicted improvements → Generate optimization report
```

## Phase Operations

| Phase | Actions | Commands |
|-------|---------|----------|
| 0 | **Workflow Discovery**: Scan `/logs/` → filter `workflow_*.md` → sort by timestamp → extract metadata (feature, date, status) → create inventory | scan_logs\|filter_workflows\|extract_metadata\|create_inventory |
| 1 | **Completion Analysis**: Load workflows → parse phase completion blocks → extract fields (STATUS/PHASE/CEPH/METRICS/LEARNINGS/BLOCKERS/ARTIFACTS/DISCOVERIES) → score presence + quality → aggregate statistics | load_workflows\|parse_completions\|extract_fields\|score_compliance\|aggregate_stats |
| 2 | **Chatmode Evaluation**: Load target chatmode → **analyze style (tone/format/density)** → **detect bloat (redundancy/verbosity)** → map workflow patterns to chatmode instructions → identify instruction gaps (missing examples, unclear requirements, weak enforcement) → **identify simplification opportunities** → evaluate field quality standards | load_chatmode\|**analyze_existing_style**\|**detect_unnecessary_instructions**\|map_workflows_to_instructions\|identify_gaps\|**identify_bloat_patterns**\|evaluate_quality_standards |
| 3 | **Optimization Planning**: Prioritize improvements by impact (Critical: mandatory fields <60%, High: quality fields <70%, Medium: consistency issues, Low: optional enhancements, **Simplification: bloat detected**) → generate specific recommendations → **ensure minimal style additions** → **plan simplification edits** → sequence implementation | prioritize_by_impact\|generate_recommendations\|**ensure_style_compatibility**\|**plan_simplification**\|sequence_improvements |
| 4 | **Instruction Updates**: Update chatmode with templates/examples → clarify ambiguous requirements → strengthen mandatory markers → add quality guidelines → **remove/simplify bloat** → **preserve original tone/format** → integrate successful workflow patterns | update_instructions\|add_templates\|clarify_requirements\|strengthen_enforcement\|**remove_redundancy**\|**simplify_verbose_instructions**\|**preserve_style**\|integrate_patterns |
| 5 | **Validation**: Calculate predicted compliance improvements → validate field presence rate increases → measure quality enhancements → generate optimization report with before/after metrics | calculate_improvements\|validate_increases\|measure_enhancements\|generate_report |

## Analysis Focus

### Style Preservation Principles
**Minimal Additions**: Only add instructions that directly address compliance gaps | Avoid padding or filler content | Match existing instruction density  
**Tone Matching**: Preserve original voice (formal/conversational/technical) | Use similar sentence structures | Maintain consistent terminology  
**Format Respect**: Match existing formatting patterns (tables/bullets/paragraphs) | Preserve spacing and organization | Keep similar section lengths  
**Bloat Detection**: Identify redundant instructions (same concept repeated 3+ times) | Flag verbose explanations (can be condensed 50%+ without detail loss) | Detect unnecessary examples (concepts already clear)  
**Simplification Without Loss**: Condense verbose instructions while preserving all requirements | Merge redundant sections | Remove filler words while keeping precision | Consolidate repetitive examples into single clear template  
**Quality Over Quantity**: Fewer precise instructions > many vague ones | One clear example > three redundant ones | Explicit requirements > lengthy explanations

### Workflow Discovery (Phase 0)
- Scan `/logs/` directory for `workflow_*.md` files
- Extract metadata: feature name, timestamp, status (completed/partial/failed)
- Sort by timestamp (recent first) for quality trends
- Optional: limit to recent N workflows (default: all)

### Field Compliance Analysis (Phase 1)
**Core Fields**: STATUS, PHASE, TASKS, DISCOVERIES, BLOCKERS (all phases)  
**Phase-Specific**: MEMORY (REMEMBER), CEPH (ASSESS+), LEARNINGS (specialist phases), ARTIFACTS (output phases), METRICS (TEST), HANDOFFS (LOG)

**Scoring**:
- Present + complete = 1.0
- Present + partial = 0.5
- Missing = 0.0
- Aggregate per phase, per workflow, overall average

**Quality Checks**:
- CEPH: All 5 fields present (CURRENT|EXPECTED|PROBLEM|HYPOTHESES|EVIDENCE)
- METRICS: Includes Δ values + baselines + scope
- LEARNINGS: Structured as pattern|approach|context
- ARTIFACTS: Format type:path:description
- MEMORY: Entity count + verification

### Chatmode Instruction Evaluation (Phase 2)
- Load target chatmode file
- **Analyze existing style**: Tone (formal/conversational) + format (dense/spacious) + structure (hierarchical/flat) + instruction density
- **Detect bloat**: Unnecessary repetition + overly verbose instructions + redundant examples + excessive enforcement markers
- Map workflow completion patterns to chatmode phase instructions
- Identify gaps:
  - **Missing Field Pattern**: Field X absent in ≥40% of phase Y → instruction unclear
  - **Partial Field Pattern**: Field X incomplete in ≥30% → needs quality examples
  - **Quality Issues**: Field present but low-value → needs specificity guidelines
  - **Bloat Pattern**: Excessive instructions without compliance improvement → simplify/remove
- **Style compatibility**: Ensure additions match original tone + format + density

### Optimization Priorities (Phase 3)
**🔴 Critical** (Mandatory fields <60% compliance): Add ⚠️ markers + explicit formats + validation checkpoints (minimal style)  
**🟠 High** (Quality fields <70%): Add good/bad examples + structure templates (match existing tone)  
**🟡 Medium** (Consistency issues): Standardize formats + add cross-phase guidelines (preserve format density)  
**🟢 Low** (Optional enhancements): Add usage examples + clarify benefits (only if gaps exist)  
**🔵 Simplification** (Bloat detected): Remove redundancy + condense verbose instructions + eliminate unnecessary repetition (without precision loss)

## Optimization Report Template

**File**: `/logs/chatmode_optimization_[chatmode_name]_[date].md`

```markdown
# Chatmode Optimization Report: [Chatmode Name]
**Date**: [YYYY-MM-DD] | **Target**: [chatmode_file_path] | **Workflows Analyzed**: [N]

## Style Analysis
**Original Tone**: [formal/conversational/technical] | **Density**: [dense/moderate/spacious] | **Format**: [hierarchical/flat/mixed]  
**Bloat Detected**: [N] redundant sections | [N] verbose instructions | [N] unnecessary examples  
**Preservation Strategy**: [minimal_additions/tone_matching/format_respect]

## Compliance Summary
**Aggregate Score**: [X%] | **Target**: ≥90%  
**Date Range**: [earliest] → [latest]  
**High Compliance (≥90%)**: [N] workflows | **Low Compliance (<70%)**: [N] workflows

## Field Analysis

### Critical Fields (<60% compliance)
- **[Field Name]** ([phase]): [X%] compliance
  - **Issue**: [description]
  - **Recommendation**: [specific action]
  - **Impact**: [predicted improvement]

### Quality Fields (<70% compliance)  
- **[Field Name]** ([phase]): [X%] compliance
  - **Issue**: [description]
  - **Recommendation**: [specific action]

### Consistency Issues
- **[Pattern]**: [description across workflows]
  - **Recommendation**: [standardization approach]

## Simplification Opportunities

### Redundancy Removed
- **[Section]**: [X] instructions → [Y] instructions (condensed [Z%])
  - **Before**: [verbose example]
  - **After**: [condensed example with same precision]

### Bloat Eliminated
- **[Area]**: [description of unnecessary content removed]
  - **Impact**: Clearer instructions without compliance loss

## Instruction Updates

### Changes Made
1. [Phase/Section]: [specific update]
2. [Phase/Section]: [specific update]

### Examples Added
- [Field]: Good example vs Bad example
- [Field]: Template with structure

### Validation Checkpoints Added
- [Phase]: [checkpoint description]

## Predicted Improvements
- [Field] compliance: [X%] → [Y%] (Δ [+Z%])
- Overall compliance: [X%] → [Y%] (Δ [+Z%])

## High-Quality Workflow Patterns
- `[workflow_file]`: [notable pattern to replicate]
```

## Usage Example

**Scenario**: User wants to optimize their DevTeam.chatmode based on all workflow logs

```bash
# User invokes: "Run update_modes workflow on DevTeam.chatmode"
TARGET_CHATMODE=".github/chatmodes/DevTeam.chatmode.md"
```

**Phase 0: Discovery** → Scans logs/, finds 12 workflow files (2025-10-06 to 2025-10-10)

**Phase 1: Analysis** → Extracts completion formats, scores compliance:
- CEPH: 85% present, 70% complete (HYPOTHESES often missing)
- METRICS: 80% present, 45% with Δ values
- LEARNINGS: 90% present, 60% properly structured

**Phase 2: Evaluation** → Maps to chatmode instructions, identifies gaps:
- ASSESS phase: CEPH HYPOTHESES template missing
- TEST phase: METRICS Δ format not emphasized
- LEARN phase: Memory verification requirement unclear

**Phase 3: Planning** → Prioritizes improvements:
- 🔴 Critical: TEST METRICS (45% Δ compliance) → Add explicit format
- 🟠 High: ASSESS HYPOTHESES (55% complete) → Add template
- 🟡 Medium: LEARNINGS consistency (60%) → Standardize structure

**Phase 4: Implementation** → Updates chatmode:
- Adds METRICS format: `coverage=95%(+15%) src:pytest scope:unit`
- Adds HYPOTHESES template: `H1:cause→prediction→test`
- Strengthens LEARN verification: "⚠️ MANDATORY: Verify line count"

**Phase 5: Validation** → Generates report:
```markdown
# Chatmode Optimization Report: DevTeam
**Workflows Analyzed**: 12 | **Compliance**: 78% → 88% (predicted)

## Critical Improvements
1. TEST METRICS Δ format: 45% → 85% (+40%)
2. ASSESS HYPOTHESES: 55% → 85% (+30%)
3. LEARN verification: 40% → 80% (+40%)
```

---

**Output**: `/logs/chatmode_optimization_DevTeam_20251010.md`
