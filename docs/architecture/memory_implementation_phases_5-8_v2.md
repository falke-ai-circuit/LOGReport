# Memory Implementation Blueprint - Phases 5-8 [v2.0]

## Overview
**Objective**: Implement Phases 5-8 (Entity, Cluster, Domain, Type) for project_memory optimization per analysis reports. Ensure 4-layer hierarchy compliance: [MemoryType].[Domain].[SubCluster].[EntityType]_[Name]. Condense to 60-80 chars/observation. Remove obsoletes (generics, promoted, empty, >80% similarity, unused >6mo). Use MCP tools: create_entities/relations, add_observations, delete_entities/observations/relations. Batch ≤10/file.

**Scope**: Project-specific (LOGReport); align with global patterns (e.g., DualMemory_System, CircuitBreaker_Pattern). Risks: Interdependencies (delete before create); validate post-phase.

**Success Metrics**: 100% hierarchy compliance, 25-35% node reduction, no orphans, metadata complete (type, version, updated).

## Phases & Actions

### Phase 5: Entity Layer
**Rationale**: Fix gaps (missing Domain/SubCluster), condense verbose (e.g., SystemComponent), delete obsoletes (generics like CodeAnomaly, promoted UI patterns). Create relations for cohesion.

**Actions** (MCP Commands):
- **Rename** (5 entities): e.g., project_memory.create_entities([{name: "Project.CodeAnalysis.CodeAnomaly.UI.BsToolTabAppendOutput_Deviation", entityType: "CodeAnomaly", observations: ["UI deviation in BsTool tab append output | 45 chars"]}]) – replace old.
- **Condense** (6 entities): e.g., project_memory.add_observations({entityName: "Project.SystemComponent.Command.CommandProcessing_SystemComponent", contents: ["Consolidated command processing: Queue, Services, Execution, State, Batch Tokens. Thread-safe, error-handled. Aligns global Command Pattern | 78 chars"]}).
- **Delete** (10+ obsoletes): project_memory.delete_entities({entityNames: ["Project.CodeAnomaly", "Project.Problem", "Project.TestSuite", "Project.Refactoring", "Project.DesignPattern", "Project.UIPattern.Input.CommandInputAutoUpdate_Pattern", ...]}).
- **Relations** (4): project_memory.create_relations([{from: "Project.CodeAnalysis.CodeAnomaly.UI.BsToolTabAppendOutput_Deviation", to: "Project.ProblemResolution.Problem.UI.BsToolOutputDisplay_Issue", relationType: "CAUSES"}]).

**Deliverables**: Updated entities (~20 new/renamed), condensed observations, no generics. Validate: search_nodes("entity hierarchy compliance").

### Phase 6: Cluster Layer
**Rationale**: Create domain-aligned clusters, move entities from generics, condense overcrowded (e.g., SystemComponent_Cluster), delete placeholders (e.g., WorkflowAnomaly_Cluster).

**Actions** (MCP Commands):
- **Create** (20+ clusters): e.g., project_memory.create_entities([{name: "Project.CodeAnalysis.CodeAnomaly_Cluster", entityType: "Cluster", observations: ["Groups code anomalies in LOGReport | 42 chars"]}]).
- **Move** (15+ entities): e.g., project_memory.create_relations([{from: "Project.CodeAnomaly.UI.BsToolTabAppendOutput_Deviation", to: "Project.CodeAnalysis.CodeAnomaly_Cluster", relationType: "BELONGS_TO"}]).
- **Condense** (5 clusters): e.g., project_memory.add_observations({entityName: "Project.Cluster.SystemComponent.SystemComponent_Cluster", contents: ["Groups project system components for organization | 58 chars"]}).
- **Delete** (5 placeholders): project_memory.delete_entities({entityNames: ["Project.Cluster.WorkflowAnomaly.WorkflowAnomaly_Cluster", "Project.Cluster.Problem.Problem_Cluster", ...]}).

**Deliverables**: Specific clusters (e.g., CodeAnomaly_Cluster), no overcrowding. Validate: read_graph diff pre/post.

### Phase 7: Domain Layer
**Rationale**: Assign unassigned clusters to domains, condense verbose (e.g., ProblemResolution), merge redundants, remove empty.

**Actions** (MCP Commands):
- **Create** (15+ domains): e.g., project_memory.create_entities([{name: "Project.Domain.WorkflowAnomaly", entityType: "Domain", observations: ["Workflow anomaly domain in LOGReport | 46 chars"]}]).
- **Move** (20+ clusters): e.g., project_memory.create_relations([{from: "Project.Cluster.WorkflowAnomaly.WorkflowAnomaly_Cluster", to: "Project.Domain.WorkflowAnomaly", relationType: "BELONGS_TO_DOMAIN"}]).
- **Condense** (8 domains): e.g., project_memory.add_observations({entityName: "Project.Domain.ProblemResolution", contents: ["Bug fixes and debugging solutions domain | 48 chars"]}).
- **Delete/Merge** (3+): project_memory.delete_entities({entityNames: ["empty_domain1", ...]}); merge similar via rename+move.

**Deliverables**: Logical domains (e.g., UI, Architecture), no unassigned. Validate: search_nodes("domain assignments").

### Phase 8: Type Layer
**Rationale**: Type domains (e.g., MemoryType.Test), condense verbose, promote universals (e.g., to global), remove empty/redundants.

**Actions** (MCP Commands):
- **Create** (20+ types): e.g., project_memory.create_entities([{name: "Project.MemoryType.WorkflowAnomaly", entityType: "MemoryType", observations: ["Workflow anomaly memory type | 32 chars"]}]).
- **Move** (15+ domains): e.g., project_memory.create_relations([{from: "Project.Domain.WorkflowAnomaly", to: "Project.MemoryType.WorkflowAnomaly", relationType: "BELONGS_TO_TYPE"}]).
- **Condense** (10 types): e.g., project_memory.add_observations({entityName: "Project.MemoryType.ProblemResolution", contents: ["Problem resolution memory type: bugs/debug | 52 chars"]}).
- **Delete/Promote** (5+): project_memory.delete_entities({entityNames: ["empty_type1", ...]}); flag promotions (e.g., UI patterns to global).

**Deliverables**: Typed hierarchy, metadata (type:MemoryType, version:1.0, updated:2025-09-30). Validate: read_graph full hierarchy.

## Implementation Strategy
- **Sequence**: Phase5→6→7→8 (delete before create to avoid orphans).
- **Batching**: ≤10 entities/clusters/domains/types per MCP call.
- **Validation**: Post-phase: project_memory.read_graph; diff vs baseline (project_memory_before_optimization.json). Metrics: node count Δ(-25%), connections (+15%).
- **Fallbacks**: If delete fails (deps), add_observations("pending_deletion"). Align with global (e.g., is_a Type.ArchitecturalPattern).
- **Artifacts**: Updated project_memory.json; summary in docs/architecture/memory_implementation_summary.md.

## Risks & Mitigations
- **Interdeps**: Sequence deletes; use relations for temp links.
- **Data Loss**: Backup pre-run; condense preserves essence.
- **MCP Limits**: Batch; retry on -32603 (enum errors).

**Next**: Execute in COMPLETE phase.