# MCP Session Process Workflow

This document outlines the standardized session process for managing and consolidating knowledge within both project-specific and global memory systems. This workflow ensures that insights are properly captured, validated, and shared across contexts following the SESSION PROCESS structure.

## Overview

The MCP Session Process Workflow is a structured approach to knowledge management that leverages both local project memory and global cross-project memory. This system enables teams to maintain project-specific details while promoting reusable patterns and best practices across the organization.

## Session Process Steps

### 0. SESSION_START
Begin every session by loading memory systems:
- Use `project_memory` tools to load project-local knowledge and previous patterns
- Use `global_memory` tools to load cross-project insights and solutions
- Initialize task tracking and workflow state using `meta-mind`
- Scope all operations under the current mode's user identity

### 1. CONTEXT_PHASE
Understand current environment and read documentation:
- Assess work environment internally using `sequential_thinking` | `meta-mind`
- Read project documentation for comprehensive context using `deepwiki`
- Load project context and understand current state
- Create initial CEPH structure for analysis delegation

### 2. RESEARCH_PHASE (when needed)
Investigate external sources for additional information:
- Use `firecrawl_mcp` to explore community-backed solutions and external sources
- Search GitHub, Reddit, and technical forums for similar implementations
- Use `deepwiki` for pattern comparison and knowledge validation
- Access authoritative documentation using external research tools
- Validate proposed solutions against industry norms

### 3. PLANNING_PHASE
Create systematic strategy informed by context and research:
- Use `sequential_thinking` MCP server to break down steps systematically
- Design coordination strategy using `meta-mind`
- Plan complex tasks using structured thinking approaches
- Forecast risks and identify potential failure points
- Validate assumptions before implementation

### 4. EXECUTION_PHASE
Apply step-by-step reasoning and execute the plan:
- Use `sequential_thinking` for complex problem solving and reasoning
- Delegate to specialists with CEPH+ understanding using `new_task(mode="specialist")`
- Handle specialist BLOCKERS and coordination using `meta-mind`
- Use `mcp-code-graph` for code structure analysis and dependency mapping
- Perform runtime observation and iterative testing
- Execute targeted implementation and change management
- Ensure all updates reflect final outcomes and are scoped under the mode's user identity

## Best Practices

- **Load memory before planning**: Always begin with context recall
- **Plan before executing**: Use sequential reasoning for complex tasks
- **Validate before updating**: Ensure accuracy before persisting knowledge
- **Distinguish contexts**: Keep project-specific and reusable knowledge separate
- **Persist for continuity**: Ensure knowledge is available for future tasks

## MCP Server Directory

| MCP Server Name | Purpose |
|----------------|---------|
| `project_memory` | Project-local memory graph (task-specific updates) |
| `global_memory` | Persistent cross-project memory (reusable insights) |
| `sequential_thinking` | Stepwise planning server |
| `firecrawl_mcp` | Community reference and error resolution server |
| `context7` | Official documentation, language, and API standard references |
| `code-graph-mcp` | Code graph analysis: indexes codebase, lists entities and relationships, outputs full JSON dependency/call graph |

## Example Implementation

```python
# Example of memory-first workflow in code
def execute_task():
    # 1. Load contexts
    project_context = load_project_memory()
    global_context = load_global_memory()
    
    # 2. Plan with sequential reasoning
    plan = create_sequential_plan(project_context, global_context)
    
    # 3. Execute with validation
    for step in plan:
        validate_step(step)
        execute_step(step)
        track_outcome(step)
    
    # 4. Consolidate knowledge
    update_project_memory(final_outcomes)
    update_global_memory(generalized_patterns)