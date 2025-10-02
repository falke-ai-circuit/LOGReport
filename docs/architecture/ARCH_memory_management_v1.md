# 🧠 Dual Memory Consolidation Workflow

This document outlines the standardized process for managing and consolidating project and global memory within the system.

## ♻️ Step-by-Step Consolidation Plan

### 1. 🔓 Selective Memory Loading Step

* **Selective Global Memory Loading**: Use **MCP server tools available on the `global_memory` server** with targeted loading:
  * Query specific types|domains|clusters|entities based on current task context rather than loading entire global memory
  * Use search/filter parameters to load only relevant hierarchy components: `load_by_type([type])` | `load_by_domain([domain])` | `load_by_cluster([cluster])`
  * Implement progressive loading: Load Type→Domain→Cluster→Entity in sequence as needed
  * Skip loading unrelated global patterns to reduce memory overhead
* **Project Memory Loading**: Use **MCP server tools available on the `project_memory` server** to load project-local memory (entities, structures, known issues).
* **Context-Aware Loading**: Determine what global memory components are needed based on:
  * Current task requirements (debug→load debug patterns, refactor→load refactor patterns)
  * Project memory references (load global components referenced by project entities)
  * Active workflow phase (load only relevant global memory for current phase)
* **Loading Validation**: Verify successful loading of relevant memory contexts before proceeding; avoid loading unnecessary global data.

### 2. 👤 Identity-Based Scoping

* Determine the user identity from the current mode:
  * For example: `debug-mode` → `debug_user`, `auto-doc-writer` → `docs_user`
  * If the mode is unknown, fall back to a generic identity like `default_user`
* Use this identity to scope all memory operations consistently across both memory types.
* Validate that the identity is properly set and accessible for all subsequent operations.

### 3. 🎯 Analyze Project Structure

* Scan the following areas, and analyze each independently:
* Source code (`src/`)
* Documentation (`docs/`)
* Key project metadata (`README.md`, `TODO.md`, `CHANGELOG.md`)
* Document any inconsistencies or issues found during analysis.
* Handle errors gracefully if any area is inaccessible or malformed.

### 4. 🌐 Leverage External References

* Use `firecrawl_mcp(...)` MCP server tools to:
  * Search GitHub, Reddit, SuperUser for domain models and naming conventions
  * Validate or improve the knowledge graph structure
  * Explore how other systems model similar entities
* Use `context7(...)` MCP server tools to:
  * Retrieve official documentation and API standards
  * Compare against language or framework standards
  * Access accurate syntax examples and best practices
* Validate findings from external sources before applying them.

### 5. 🧠 Plan Consolidation

* Use `sequential_thinking(...)` MCP server tools to:
  * Detect duplicated or fragmented entities
  * Spot weak or missing relationships
  * Identify unlinked bugs, configs, or features
  * Identify differences between memories and documentation and source code.
  * Suggest generalization or promotion of reusable insights
* Document the consolidation plan with clear justifications for each proposed change.
* Validate the plan with consistency checks before execution.

### 6. 📅 Selective Knowledge Tracking During Execution

* While performing tasks, record new facts, structural inferences, behaviors, naming decisions, and task outcomes:
  * Use **tools from the `project_memory` MCP server** for project-specific knowledge
  * Use **tools from the `global_memory` MCP server** for reusable abstractions or cross-project patterns with selective targeting:
    * Only update relevant global hierarchy components (type|domain|cluster|entity) based on current context
    * Avoid updating unrelated global patterns to minimize unnecessary writes
    * Use targeted global memory operations: `update_type()` | `update_domain()` | `update_cluster()` | `update_entity()`
* **Progressive Loading During Execution**: Load additional global memory components on-demand as new patterns emerge
* Track intermediate states and decisions for auditability with selective memory scope.
* Handle any errors in knowledge recording without stopping the overall workflow.

### 7. ✏️ Apply Selective Memory Updates

* In `project_memory(...)` MCP server tools, apply changes:
  * Merge duplicates
  * Rename and re-cluster entities
  * Remove or add entities and observations based on documents and source code
  * Link configs, services, modules, or events logically
* In `global_memory(...)` MCP server tools, promote with selective targeting:
  * Target specific hierarchy levels: type|domain|cluster|entity based on relevance
  * Promote only universally applicable concepts to avoid global memory bloat
  * Use selective promotion: `promote_to_type()` | `promote_to_domain()` | `promote_to_cluster()`
  * Avoid updating irrelevant global patterns or distant hierarchy components
* **Selective Update Strategy**: Update only loaded global memory components; leave unloaded components unchanged
* Validate each update to ensure consistency and correctness within selective scope.

### 8. ✅ Validation Steps

* Perform consistency checks on both memory graphs:
  * Verify no broken relationships or orphaned entities
  * Confirm all promoted patterns are correctly applied
  * Check for any conflicts between project and global memory
* Validate that all changes align with the original consolidation plan.
* Handle validation failures with appropriate error reporting and recovery options.

### 9. 🧹 Selective Global Memory Cleanup

* Once key insights are promoted to global memory:
  * Re-analyze only the loaded/modified global memory components for duplication or overlap
  * Use `sequential_thinking(...)` MCP server tools to clean, deduplicate, and restructure within selective scope
  * Finalize updates only to actively used global memory hierarchy components
  * Avoid unnecessary cleanup of unrelated global memory areas
* **Selective Cleanup Strategy**: Target cleanup operations to specific type|domain|cluster|entity components that were actively loaded/modified
* Ensure loaded global memory remains consistent and optimized without affecting unloaded components.
* Handle any cleanup errors without affecting the overall process.

### 10. 🚪 Session Closure with Selective Scope

* Confirm all memory operations are completed within selective loading scope:
  * Verify all project-specific insights are properly recorded in `project_memory`
  * Ensure relevant reusable patterns are correctly promoted to loaded `global_memory` components
  * Validate that unloaded global memory components remain unchanged and consistent
* **Selective Validation**: Perform consistency checks only on loaded global memory hierarchy components
* **Scope Documentation**: Log which global memory components were loaded/modified for session tracking
* Log session completion with timestamp, selective scope summary, and operations performed on specific hierarchy levels.
* Handle any last-minute errors or inconsistencies within the selective loading scope.

### 11. ⚠️ Error Handling and Recovery

* Implement error handling for each major step:
  * Memory loading failures should attempt fallback mechanisms
  * Analysis errors should skip problematic areas but continue with valid ones
  * Update failures should rollback changes and report detailed error information
  * Validation failures should provide recovery options or alternative approaches
* Log all errors with sufficient context for debugging and recovery.
* Ensure graceful degradation when non-critical steps fail.

### 12. 📋 Final Summary

* Summarize everything in a clear `attempt_completion(result="...")` output, including:
  * What was updated and why
  * How memory graphs improved
  * Patterns or reusable abstractions discovered
  * Any issues encountered and how they were resolved
  * Validation results and consistency checks
  * Session closure confirmation and final state of memory graphs