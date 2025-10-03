# Update Modes Workflow

**Purpose**: Mode optimization via analysis→implementation phases | **Modes**: Analysis (1-3): mcp-analyze | Implementation (4-6): mcp-code/mcp-architect | **Batch**: 3-5 modes/cycle | **Target**: Consistent configuration & boundaries

## 6-Phase Architecture

| Phase | Type | Objective | Mode | Output |
|-------|------|-----------|------|--------|
| 1 | Analysis | Current mode assessment | mcp-analyze | Configuration inventory |
| 2 | Analysis | External best practices evaluation | mcp-analyze | Enhancement opportunities |
| 3 | Analysis | Implementation planning | mcp-analyze | Update commands |
| 4 | Implementation | Base template application | mcp-code/architect | Standardized configs |
| 5 | Implementation | Mode boundary enforcement | mcp-code/architect | Validated transitions |
| 6 | Implementation | Validation & integration | mcp-code/architect | Verified modes |

## Parameters

**Scope**: 6 KiloCode modes ↔ configuration standardization | **Batch**: 3-5 modes | **Template**: Base inheritance pattern | **Boundaries**: Strict mode separation | **Integration**: Memory system alignment | **Standards**: Icon + instruction consistency

## Execution Pattern

```bash
# Analysis Phase (mcp-analyze)
1-3: Assess → Research → Plan

# Implementation Phase (mcp-code/mcp-architect)  
4-6: Standardize → Enforce → Validate
```

## Phase Details

### Phase 1: Current Mode Assessment
**Scope**: Configuration inventory, compliance gaps, inheritance patterns, orchestrator log analysis
```
BATCH_PROCESS(modes[3-5]):
→ Load export files (analyze-export.yaml, debug-export.yaml, etc.)
→ Load orchestrator log files: orchestrator_[workflow]_[timestamp].md
→ Assess configuration consistency
→ Compare mode instructions vs logged specialist behavior
→ Identify missing icons and instructions
→ Map inheritance patterns and gaps
→ Analyze delegation rationale vs actual results
→ Calculate rule adherence from logged actions: target ≥85%
```

### Phase 2: External Best Practices Evaluation
**Scope**: Community insights, documentation standards, proven patterns, orchestrator log retrospective
```
RESEARCH_CRITERIA:
→ Official KiloCode documentation (kilocode.ai/docs)
→ Community discussions (Reddit, GitHub)
→ Mode usage patterns and feedback
→ Cross-project successful configurations
→ Orchestrator log retrospective analysis
→ Compare mode instructions vs real-world delegation results
→ Identify instruction gaps causing BLOCKERS or redelegations
→ Map METRICS/LEARNINGS patterns across logged workflows
```

### Phase 3: Implementation Planning
**Scope**: Enhancement prioritization, update commands, batch organization, log-driven improvements
```
PLANNING_OUTPUT:
→ Base template extraction requirements
→ Mode boundary enforcement rules
→ Configuration standardization commands
→ Validation criteria definition
→ Log-driven instruction refinements
→ Prioritize improvements addressing logged BLOCKERS/redelegations
→ Update mode definitions based on METRICS/LEARNINGS analysis
```

### Phase 4: Base Template Application
**Scope**: Template inheritance, instruction standardization, configuration consistency
```
TEMPLATE_COMMANDS:
extract_base_template(common_instructions, base_mode.yaml)
apply_inheritance(mode_config, base_template)
standardize_instructions(mode, memory_integration_pattern)
update_configuration(mode, consistent_format)
```

### Phase 5: Mode Boundary Enforcement
**Scope**: Transition validation, boundary rules, mode separation
```
BOUNDARY_COMMANDS:
enforce_mode_boundaries(mode, strict_separation_rules)
validate_transitions(mode_pairs, allowed_transitions)
implement_middleware(transition_validation)
update_mode_definitions(boundary_specifications)
```

### Phase 6: Validation & Integration
**Scope**: Configuration verification, functionality testing, system integration
```
VALIDATION_COMMANDS:
validate_mode_config(mode, functionality_test)
test_mode_transitions(workflow, boundary_compliance)
verify_memory_integration(mode, system_compatibility)
integration_test(all_modes, comprehensive)
```

## Mode Configuration

| Mode | Primary Function | Key Tools | Memory Integration |
|------|------------------|-----------|-------------------|
| Analyze | Analysis only, no implementation | Read, search, assess | project_memory, global_memory |
| Code | Implementation & modification | Edit, create, replace | project_memory integration |
| Debug | Issue diagnosis & resolution | Test, validate, fix | Error pattern memory |
| Architect | System design & planning | Design, structure, plan | Architecture pattern memory |
| Document | Documentation management | Create, organize, format | Documentation templates |
| Orchestrator | Multi-mode coordination | Coordinate, delegate, manage | Workflow memory |

## Output Formats

**Analysis Phase (Phases 1-3)**:
```
PHASE_ID: [1-3/6] Analysis
BATCH_ID: [batch_number/total_batches]
MODE: [mode_name → standardized_configuration]
ANALYSIS: [config_gap|boundary_violation|instruction_inconsistency|missing_integration]
LOG_ANALYSIS: [rule_adherence_%|redelegation_count|blocker_patterns|metrics_summary]
RECOMMENDATION: [apply_template|enforce_boundary|standardize_config|add_integration|refine_instructions_per_log]
RATIONALE: [consistency_improvement|boundary_clarity|memory_alignment|log_driven_refinement]
PRIORITY: [critical|high|medium|low]
IMPLEMENTATION_READINESS: [ready_for_execution|needs_refinement|requires_validation]
```

**Implementation Phase (Phases 4-6)**:
```
PHASE_ID: [4-6/6] Implementation  
BATCH_ID: [batch_number/total_batches]
MODE: [mode_name → updated_configuration]
ACTION: [apply_template|enforce_boundary|standardize|validate|refine_instructions]
CONFIG_COMMAND: [specific configuration update command executed]
EXECUTION_STATUS: [planned|in_progress|completed|validated]
IMPACT: [consistency_improved|boundaries_enforced|integration_enhanced|log_insights_applied]
VALIDATION: [config_verified|transitions_working|memory_integrated|log_compliance_improved]
```

## MCP Integration

**Mode Separation**: Analysis phases (1-3) in mcp-analyze | Implementation phases (4-6) in mcp-code/architect | **Base Template**: Inheritance pattern for consistent configuration | **Memory Integration**: project_memory and global_memory access patterns | **Boundary Enforcement**: Strict mode separation and transition validation | **Tool Access**: Mode-specific tool eligibility and restrictions | **Batch Processing**: Context preservation via structured execution
- Simplify Orchestrator mode configuration
- Use `edit_file(...)` to write improved mode spec back to `.kilocode/`

### 6. Persist Final Memory-Driven Overrides
- If enhancements are deemed reusable:
  - Promote shared patterns to `global_memory` using `global_memory(action="write", data={…})`
- Always update `project_memory` with final local mode adjustments

### 7. Finalize & Backup
- Summarize all mode refinements and reasoning:
  ```ts
  attempt_completion(result="Completed mode optimization: mode updates applied, memory synced, best practices integrated.")
  ```

## 🧩 Enhancement Details

### Base Mode Template
Create a base mode template that extracts the recurrent instruction pattern found in multiple modes:
```yaml
baseModeTemplate:
  customInstructions: >-
    • Remember using global_memory and project_memory if we have solved similar problem, and load whole knowledge from it
```

### Inheritance Pattern
Apply the base template to Code, Debug, and Optimize modes through inheritance:
```yaml
customModes:
  - slug: code
    name: Code
    inherits: baseModeTemplate
    # Additional mode-specific instructions
```

### Strict Boundary Enforcement
Implement explicit role restrictions to prevent mode boundary violations:
```yaml
customModes:
  - slug: architect
    roleRestrictions:
      - Cannot generate implementation code
      - Must only produce architectural designs
```

### Standardized Configuration
Apply consistent YAML structure across all mode files:
```yaml
customModes:
  - slug: [mode-slug]
    name: [Mode Name]
    iconName: [icon-codicon]
    roleDefinition: [Concise role description]
    whenToUse: [Clear usage guidance]
    description: [Brief description]
    groups: [read, edit, browser, command, mcp]
    customInstructions: [Mode-specific instructions]
    source: project
```

### Transition Validation Middleware
Implement validation steps to ensure mode transitions follow the MultiModeWorkflow pattern:
```yaml
transitionValidation:
  - Plan with Architect mode first
  - Implement with Code mode
  - Debug and troubleshoot with Debug mode
  - Use Orchestrator mode for complex multi-step projects
```

### Memory Integration
Update both project_memory and global_memory with mode configuration changes:
- Use `project_memory` for local insights specific to this project
- Use `global_memory` for generalized patterns applicable across projects

MCP servers to be used:
- `project_memory`
- `global_memory`
- `sequential_thinking`
- `firecrawl_mcp`
- `context7`

Memory loading:
- Instruct to load project-specific context using `project_memory` tools
- Load cross-project knowledge using `global_memory` tools

Reasoning & planning:
- Use tools from the `sequential_thinking` MCP server

Community research:
- Use tools from `firecrawl_mcp` MCP server for any additional research needed for documentation.
- Use tools from `context7` MCP server for any official documentation references.

Memory updates before completion:
- Persist task results using:
  - `project_memory` MCP server tools for local insights (e.g., the content of the `update_modes.md` file)
  - `global_memory` MCP server tools for generalized patterns (e.g., best practices for workflow documentation)

Completion:
- Must end with `attempt_completion(result="...")`