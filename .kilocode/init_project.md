# 🚀 Initialize Project Workflow

This workflow executes a complete project initialization using existing 4-file blueprints. It provides detailed execution order for all project phases from setup through completion, following the established blueprint documentation.

## 🔧 Tool Access

- MCP servers available:
  - `project_memory` (project-local context)
  - `global_memory` (cross-project memory)
  - `sequential_thinking` (structured planning)
  - `firecrawl_mcp` (external knowledge)
  - `context7` (official docs)

## 🔁 Steps

### 1. Load Existing Blueprint Files
- Read all 4 blueprint files from `docs/blueprints/`:
  - `ARCHITECTURE.md` - System design and technical decisions
  - `ROADMAP.md` - Implementation phases and timeline
  - `SETUP.md` - Environment and development workflows
  - `VALIDATION.md` - Testing and quality assurance
- Parse project requirements, technology stack, implementation phases, and key milestones

### 2. Load Memory Context
- Use `global_memory(action="read")` to fetch previous project execution patterns and proven procedures
- Use `project_memory(action="read")` for existing project context and configurations

### 3. Execute Foundation Phase (Phase 1)
- **Environment Setup**: Execute all installation steps from SETUP.md (prerequisites, dependencies, tools)
- **Project Structure**: Create directory structure and initial files per ARCHITECTURE.md specifications
- **Basic Configuration**: Apply environment variables, config files, and development server setup from SETUP.md
- **Foundation Validation**: Run Phase 1 tests from VALIDATION.md (health checks, connectivity, smoke tests)

### 4. Execute Core Development Phase (Phase 2)  
- **Architecture Implementation**: Build core components, business logic, and data models per ARCHITECTURE.md
- **Feature Development**: Implement primary features and workflows specified in ROADMAP.md
- **Initial Testing**: Create and execute unit/integration test suite per VALIDATION.md specifications
- **Core Validation**: Run Phase 2 tests (functionality, integration, performance baselines, code quality)

### 5. Execute Integration & Polish Phase (Phase 3)
- **System Integration**: Complete external service integrations and cross-component communication per ARCHITECTURE.md
- **Comprehensive Testing**: Execute full test suite from VALIDATION.md (end-to-end, performance, security testing)
- **Documentation**: Finalize API docs, user guides, and operational runbooks
- **Deployment**: Execute production setup and deployment procedures from SETUP.md

### 6. Execute Quality Gates & Final Validation
- **Pre-Deployment Checklist**: Complete all quality gate items from VALIDATION.md (test coverage, performance, security)
- **User Acceptance**: Execute acceptance criteria validation and stakeholder review
- **Production Deployment**: Final deployment with monitoring setup and post-deployment validation

### 7. Project Completion & Handoff
- **Documentation Package**: Compile complete architecture, setup, operational, and test documentation
- **Knowledge Transfer**: Execute handoff procedures and team knowledge transfer per VALIDATION.md
- **Project Closure**: Validate final milestones against ROADMAP.md and complete resource cleanup

### 8. Persist Execution Patterns
- Update `global_memory(action="write", data={...})` with successful execution patterns and quality gate approaches
- Update `project_memory(action="write", data={...})` with complete execution timeline and configuration details

### 9. Finalize & Complete
- Validate all blueprint requirements executed successfully across all phases
- Summarize execution results:
  ```ts
  attempt_completion(result="Project initialization complete: all phases executed, quality gates passed, production deployed, documentation delivered.")
  ```

## 🧩 Blueprint Execution Strategy

### Phase-Based Execution
- **Phase 1 (Foundation)**: Environment + Structure + Configuration + Validation
- **Phase 2 (Core Development)**: Architecture + Features + Testing + Validation  
- **Phase 3 (Integration)**: Integration + Testing + Documentation + Deployment
- **Final Validation**: Quality Gates + Acceptance + Production + Handoff

### Blueprint File Integration
- **ARCHITECTURE.md**: Guides structure creation, component implementation, and integration patterns
- **ROADMAP.md**: Defines phase specifications, milestones, and success criteria
- **SETUP.md**: Provides installation, configuration, and deployment procedures
- **VALIDATION.md**: Specifies testing strategies, quality gates, and acceptance criteria

### Success Criteria
- All roadmap phases completed with milestone validation
- Quality gates passed per validation specifications  
- Production deployment operational and monitored
- Complete documentation package delivered
- Knowledge transfer and project closure completed

MCP servers to be used:
- `project_memory`
- `global_memory`
- `sequential_thinking`
- `firecrawl_mcp`
- `context7`

Memory loading:
- Load project execution patterns using `global_memory` tools
- Load existing project context using `project_memory` tools

Blueprint execution:
- Parse existing blueprint files from `docs/blueprints/` directory
- Execute phases sequentially per ROADMAP.md specifications  

Reasoning & planning:
- Use tools from the `sequential_thinking` MCP server for phase planning and execution coordination

External research:
- Use tools from `firecrawl_mcp` MCP server for implementation best practices when needed
- Use tools from `context7` MCP server for official documentation references

Memory updates before completion:
- Persist execution patterns using:
  - `global_memory` MCP server tools for reusable execution strategies and quality approaches
  - `project_memory` MCP server tools for project-specific timeline and configuration details

Completion:
- Must end with `attempt_completion(result="...")`

## 🧩 Blueprint Framework Integration

### Mandatory AI Process Implementation
Follow the blueprint framework's AI implementation instructions:

1. **ALWAYS create ALL 4 files** - No exceptions, regardless of project type
2. **Identify project type** first using the decision matrix
3. **Apply appropriate adaptations** using the framework's adaptation rules
4. **Replace ALL placeholders** with project-specific content
5. **Ensure cross-file consistency** - References between files must align
6. **Validate completeness** - No empty sections, all placeholders filled

### Project Type Decision Matrix
Apply these adaptations based on identified project type:
- **Web Applications**: UI/UX focus, responsive design, browser compatibility, frontend/backend architecture
- **Mobile Applications**: Platform SDKs, device compatibility, app store requirements, performance optimization
- **APIs/Backend Services**: Endpoints, data models, authentication, scalability, integration patterns
- **Data Projects**: Data pipelines, storage, processing, analytics, data quality, visualization
- **Desktop Applications**: Platform integration, local storage, performance, distribution methods
- **Infrastructure Projects**: Deployment, scaling, monitoring, security, automation, compliance

### Quality Validation Checkpoints
- **Completeness**: All 4 files created with no empty sections
- **Relevance**: Content specifically applies to the identified project type
- **Actionability**: Instructions are specific and immediately usable
- **Consistency**: Information aligns across all files without contradictions

## 📁 File Structure Output

After successful initialization, the project will have:

```
PROJECT_ROOT/
├── docs/
│   └── blueprints/
│       ├── ARCHITECTURE.md    # System design & technical decisions
│       ├── ROADMAP.md        # Implementation phases & timeline
│       ├── SETUP.md          # Environment & development workflows
│       └── VALIDATION.md     # Testing & quality assurance
├── [Initial project structure based on type]
└── [Configuration files based on technology stack]
```

## 🎯 Success Criteria

- Comprehensive project foundation established using standardized 4-file blueprint framework
- All blueprint files contain project-specific, actionable content with no template placeholders
- Project structure and configuration appropriate for identified project type and technology stack
- Setup instructions enable immediate development progress
- Testing strategy and quality gates clearly defined and implementable
- Architectural decisions documented with clear rationale and constraints
- Implementation roadmap provides realistic phases and measurable milestones

MCP servers to be used:
- `project_memory`
- `global_memory`
- `sequential_thinking`
- `firecrawl_mcp`
- `context7`

Memory loading:
- Load cross-project blueprint patterns using `global_memory` tools
- Load any existing project context using `project_memory` tools

Blueprint framework loading:
- Parse the standardized framework from `.kilocode/workflows/blueprint_framework.md`
- Apply AI implementation instructions and adaptation rules

Reasoning & planning:
- Use tools from the `sequential_thinking` MCP server for project analysis and planning

External research:
- Use tools from `firecrawl_mcp` MCP server for domain-specific best practices
- Use tools from `context7` MCP server for official documentation references

Memory updates before completion:
- Persist initialization patterns using:
  - `global_memory` MCP server tools for reusable blueprint adaptations and architectural patterns
  - `project_memory` MCP server tools for project-specific initialization context and decisions

Completion:
- Must end with `attempt_completion(result="...")`
