# Update Modes Workflow

**Purpose**: Chatmode optimization via workflow log analysis→instruction refinement | **Input**: User specifies target chatmode file | **Focus**: Compliance format + field quality + instruction consistency → minimal enhancements | **Log Source**: `/logs/workflow_*.md` (batch processing) | **Output**: Optimized chatmode with compliance improvements | **Target**: Compliance ≥90% + Field quality + BLOCKER reduction | **⚠️ CRITICAL CONSTRAINT**: ALL edited files (target chatmode + instruction files) MUST remain ≤100 lines

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

**User Input**: Target chatmode file path | **Instruction Files**: All `*.md` files in `.github/instructions/` directory (loaded dynamically) | **Logs**: `/logs/workflow_*.md` (all or recent N) | **Analysis**: Field compliance + quality patterns + instruction consistency | **Targets**: Compliance ≥90% | Field quality ≥85% | BLOCKER reduction ≥30% | **⚠️ PRIMARY CONSTRAINT**: All edited files ≤100 lines (MANDATORY) | **Style Preservation**: Minimal additions + respect original tone/format + detect unnecessary instructions + simplify without precision loss | **Output**: `/logs/chatmode_optimization_[chatmode_name]_[date].md`

## Execution Pattern

```bash
# Usage: Specify target chatmode file
TARGET_CHATMODE="[path/to/chatmode.md]"  # User provides chatmode path
INSTRUCTION_DIR=".github/instructions/"  # Auto-discover all *.md files

# Phase 0: Discovery
Scan logs/workflow_*.md → Extract metadata → Sort by timestamp
Load all instruction files from INSTRUCTION_DIR

# Phase 1-2: Analysis  
Parse completion formats → Score field compliance → Map to chatmode + instruction files → Identify gaps → **Check line counts**

# Phase 3: Planning
Prioritize improvements (Critical→High→Medium→Low) → Generate recommendations → **Calculate line budget (100 - current_lines)**

# Phase 4: Implementation
**MANDATORY FIRST**: Remove bloat to free space → Update chatmode instructions → Add templates/examples → Strengthen requirements → **Verify ≤100 lines**

# Phase 5: Validation
Measure predicted improvements → **Confirm all files ≤100 lines** → Generate optimization report
```

## Phase Operations

| Phase | Actions | Commands |
|-------|---------|----------|
| 0 | **Workflow Discovery**: Scan `/logs/` → filter `workflow_*.md` → sort by timestamp → extract metadata (feature, date, status) → create inventory → **scan instruction directory** → **record line counts** | scan_logs\|filter_workflows\|extract_metadata\|scan_instructions\|**record_line_counts**\|create_inventory |
| 1 | **Completion Analysis**: Load workflows → parse phase completion blocks → extract fields (STATUS/PHASE/CEPH/METRICS/LEARNINGS/BLOCKERS/ARTIFACTS/DISCOVERIES) → score presence + quality → aggregate statistics | load_workflows\|parse_completions\|extract_fields\|score_compliance\|aggregate_stats |
| 2 | **Chatmode Evaluation**: Load target chatmode + **scan .github/instructions/ for all *.md files** → **analyze style (tone/format/density)** → **check compliance/consistency** → **detect bloat (redundancy/verbosity)** → map workflow patterns to instructions → identify gaps → **identify simplification opportunities** → evaluate field quality standards → **calculate line budgets** | load_chatmode\|scan_instruction_directory\|load_all_instructions\|**analyze_existing_style**\|**check_instruction_compliance**\|**detect_bloat**\|map_workflows_to_instructions\|identify_gaps\|**calculate_line_budgets**\|evaluate_quality_standards |
| 3 | **Optimization Planning**: **MANDATORY: Check if files >100 lines → prioritize bloat removal FIRST** → Prioritize improvements by impact (Critical: mandatory fields <60%, High: quality fields <70%, Medium: consistency issues, Low: optional enhancements, **Simplification: bloat detected**, **Compliance: instruction misalignment**, **Line Limit: files >100 lines**) → generate specific recommendations → **ensure minimal style additions (only fix gaps, preserve working patterns)** → **plan removal before addition** → **enforce 100-line limit** → sequence implementation | **check_line_limits**\|**prioritize_bloat_removal**\|prioritize_by_impact\|generate_recommendations\|**ensure_minimal_changes**\|**plan_removal_first**\|**enforce_line_limits**\|sequence_improvements |
| 4 | **Instruction Updates**: **STEP 1: Remove bloat to free space** → **STEP 2: Add minimal improvements** → Update chatmode with templates/examples → clarify ambiguous requirements → strengthen mandatory markers → add quality guidelines → **preserve original tone/format** → **ensure alignment with all instruction files** → **FINAL VALIDATION: verify all files ≤100 lines** | **remove_bloat_first**\|update_instructions\|add_templates\|clarify_requirements\|strengthen_enforcement\|**preserve_style**\|**align_with_instructions**\|**final_line_count_validation** |
| 5 | **Validation**: Calculate predicted compliance improvements → validate field presence rate increases → measure quality enhancements → **verify all edited files ≤100 lines** → generate optimization report with before/after metrics + line counts | calculate_improvements\|validate_increases\|measure_enhancements\|**verify_line_limits**\|generate_report |

## Analysis Focus

### Style Preservation Principles
**⚠️ PRIMARY CONSTRAINT**: ALL edited files MUST remain ≤100 lines after modifications | Bloat removal takes priority over additions  
**Minimal Additions**: Only add instructions that directly address compliance gaps | Avoid padding or filler content | Match existing instruction density | **Preserve working patterns**  
**Removal Before Addition**: ALWAYS remove bloat FIRST to create space before adding new content | Calculate available line budget (100 - current_lines - bloat_lines)  
**Tone Matching**: Preserve original voice (formal/conversational/technical) | Use similar sentence structures | Maintain consistent terminology  
**Format Respect**: Match existing formatting patterns (tables/bullets/paragraphs) | Preserve spacing and organization | Keep similar section lengths  
**Bloat Detection**: Identify redundant instructions (same concept repeated 3+ times) | Flag verbose explanations (can be condensed 50%+ without detail loss) | Detect unnecessary examples (concepts already clear)  
**Simplification Without Loss**: Condense verbose instructions while preserving all requirements | Merge redundant sections | Remove filler words while keeping precision | Consolidate repetitive examples into single clear template  
**Quality Over Quantity**: Fewer precise instructions > many vague ones | One clear example > three redundant ones | Explicit requirements > lengthy explanations  
**Line Budget Management**: If file at 95 lines: remove 10 lines of bloat before adding 5 lines | If file at 105 lines: remove 10+ lines, add none | Validate final count ≤100  
**Minimal Changes Only**: Only fix identified compliance gaps and remove proven bloat | Preserve all effective existing patterns | Do not restructure working sections

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
- **Load all instruction sources**: Target chatmode + scan `.github/instructions/` directory for all `*.md` files (dynamic discovery)
- **Analyze existing style**: Tone (formal/conversational) + format (dense/spacious) + structure (hierarchical/flat) + instruction density
- **Compliance analysis**: Check chatmode against all discovered instruction files for consistency, completeness, and effectiveness
- **Detect bloat**: Unnecessary repetition + overly verbose instructions + redundant examples + excessive enforcement markers
- **Effectiveness assessment**: Evaluate if chatmode properly references and enforces instruction file requirements
- Map workflow completion patterns to chatmode phase instructions
- Identify gaps:
  - **Missing Field Pattern**: Field X absent in ≥40% of phase Y → instruction unclear
  - **Partial Field Pattern**: Field X incomplete in ≥30% → needs quality examples
  - **Quality Issues**: Field present but low-value → needs specificity guidelines
  - **Bloat Pattern**: Excessive instructions without compliance improvement → simplify/remove
  - **Instruction Misalignment**: Chatmode contradicts or omits instruction file requirements
- **Style compatibility**: Ensure additions match original tone + format + density

### Optimization Priorities (Phase 3)
**⚫ Line Limit** (Files >100 lines): **HIGHEST PRIORITY** - Remove bloat FIRST before any additions | Target: bring all files to ≤95 lines to allow minimal additions  
**🔴 Critical** (Mandatory fields <60% compliance): Add ⚠️ markers + explicit formats + validation checkpoints (minimal style)  
**🟠 High** (Quality fields <70%): Add good/bad examples + structure templates (match existing tone)  
**🟡 Medium** (Consistency issues): Standardize formats + add cross-phase guidelines (preserve format density)  
** Simplification** (Bloat detected in files <100 lines): Remove redundancy + condense verbose instructions + eliminate unnecessary repetition (without precision loss)  
**🟣 Compliance** (Instruction misalignment): Align chatmode with instruction files + fix contradictions + ensure proper references  
**🟢 Low** (Optional enhancements): Add usage examples + clarify benefits (only if gaps exist AND line budget available)

## Optimization Report Template

**File**: `/logs/chatmode_optimization_[chatmode_name]_[date].md`

```markdown
# Chatmode Optimization Report: [Chatmode Name]
**Date**: [YYYY-MM-DD] | **Target**: [chatmode_file_path] | **Workflows Analyzed**: [N] | **Instruction Files**: [N files from .github/instructions/]

## Instruction File Analysis
**Files Loaded**: [list of *.md files from instructions directory] | **Line Counts**: [file:lines, ...] | **⚠️ Over Limit**: [files >100 lines with counts]  
**Compliance Check**: [chatmode alignment with instruction files] | **Gaps**: [missing references or contradictions]  
**Bloat Detected**: [redundant sections across files with line counts] | **Line Budget**: [available lines per file for additions after bloat removal]

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

### Line Budget Enforcement
**Before Changes**: [file: current_lines] | **Bloat Identified**: [file: -N lines to remove] | **Budget**: [file: lines available for additions]

### Changes Made
1. **[File]** (Before: [X] lines → After: [Y] lines): [specific update]
   - Removed: [bloat description, -N lines]
   - Added: [improvement description, +M lines]
   - ✓ Verified: ≤100 lines
2. **[File]** (Before: [X] lines → After: [Y] lines): [specific update]

### Examples Added
- [Field]: Good example vs Bad example
- [Field]: Template with structure

### Validation Checkpoints Added
- [Phase]: [checkpoint description]

## Predicted Improvements
- [Field] compliance: [X%] → [Y%] (Δ [+Z%])
- Overall compliance: [X%] → [Y%] (Δ [+Z%])

## ⚠️ Line Count Validation
**All Edited Files**: ✓ Verified ≤100 lines | **Before/After**: [file: X→Y lines, ...]

## High-Quality Workflow Patterns
- `[workflow_file]`: [notable pattern to replicate]
```

## Usage Example

**Scenario**: User wants to optimize their chatmode based on all workflow logs

```bash
# User invokes workflow with chatmode path
TARGET_CHATMODE=".github/chatmodes/[ChatmodeName].chatmode.md"
INSTRUCTION_DIR=".github/instructions/"  # Auto-scanned for all *.md files
```

**Phase 0: Discovery** → Scans logs/, finds 12 workflow files (2025-10-06 to 2025-10-10) + scans instruction directory (5 files discovered)

**Phase 1: Analysis** → Extracts completion formats, scores compliance:
- CEPH: 85% present, 70% complete (HYPOTHESES often missing)
- METRICS: 80% present, 45% with Δ values
- LEARNINGS: 90% present, 60% properly structured

**Phase 2: Evaluation** → Maps to chatmode + instruction files, identifies gaps:
- ASSESS phase: CEPH HYPOTHESES template missing
- TEST phase: METRICS Δ format not emphasized
- LEARN phase: Memory verification requirement unclear
- Instruction alignment: Chatmode missing reference to structure.md file placement rules

**Phase 3: Planning** → Prioritizes improvements:
- 🔴 Critical: TEST METRICS (45% Δ compliance) → Add explicit format
- 🟠 High: ASSESS HYPOTHESES (55% complete) → Add template
- 🟡 Medium: LEARNINGS consistency (60%) → Standardize structure
- 🟣 Compliance: Add structure.md reference for file placement

**Phase 4: Implementation** → Updates chatmode:
- Adds METRICS format: `coverage=95%(+15%) src:pytest scope:unit`
- Adds HYPOTHESES template: `H1:cause→prediction→test`
- Strengthens LEARN verification: "⚠️ MANDATORY: Verify line count"
- Adds instruction file reference

**Phase 5: Validation** → Generates report:
```markdown
# Chatmode Optimization Report: [ChatmodeName]
**Workflows Analyzed**: 12 | **Compliance**: 78% → 88% (predicted)

## Critical Improvements
1. TEST METRICS Δ format: 45% → 85% (+40%)
2. ASSESS HYPOTHESES: 55% → 85% (+30%)
3. LEARN verification: 40% → 80% (+40%)
```

---

**Output**: `/logs/chatmode_optimization_[chatmode_name]_[date].md`
