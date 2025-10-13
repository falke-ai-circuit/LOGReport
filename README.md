# LOGReport Project Overview

## Memory Consolidation Workflow Implementation

The LOGReport project implements a dual memory consolidation workflow that combines project-specific memory with cross-project global memory. This approach ensures both localized context and reusable knowledge patterns are maintained.

### What is LOGReport?

LOGReport is a comprehensive tool for converting multiple log files from industrial control systems into organized PDF/DOCX reports. It supports various log file formats including:

- **Standard logs**: `.log`, `.txt` files
- **Commander protocol logs**: `.lis` (LIS), `.fbc` (FBC), `.rpc` (RPC) files

The application features:
- **Recursive directory scanning**: Automatically discovers log files in nested folder structures
- **Multi-format report generation**: Creates professional PDF or Word documents with node-based organization
- **Node-based organization**: Groups logs by node name (AP01, AP02m, AL01) with file type ordering (.fbc→.rpc→.log→.lis)
- **Clickable Table of Contents**: PDF reports include clickable navigation with anchor bookmarks for each node chapter
- **Intelligent line wrapping**: Automatically wraps long lines at 80 characters (verified for A4 page width) to prevent text overflow
- **Flexible content filtering**: Configure line limits, ranges, and filtering modes
- **Commander integration**: Full support for telnet/BsTool-based log collection from industrial devices
- **BsTool bundling**: BsTool.exe automatically bundled and detected - no manual configuration needed

### BsTool Integration

LOGReporter includes **automatic BsTool.exe bundling** for seamless deployment:

**✅ No Manual Setup Required**
- BsTool.exe packaged inside LOGReporter.exe
- Path auto-detection on startup (no configuration needed)
- Works in both development and packaged environments

**🔧 How It Works**
- **Development mode**: Detects BsTool.exe in project root
- **Packaged mode**: Extracts BsTool.exe to temporary directory at runtime
- **Manual override**: Users can specify custom BsTool.exe location if needed

**📦 Building with BsTool**
When building the executable, BsTool.exe is automatically included:
```powershell
# BsTool.exe must be in project root
pyinstaller --clean LOGReporter_PyQt5.spec
```

The packaged executable includes BsTool.exe and automatically detects its location. See [BUILD-INSTRUCTIONS.md](BUILD-INSTRUCTIONS.md) for complete build details.

### Dual Memory System
- **Project Memory**: Stores project-specific entities, relationships, and implementation details using the `project_memory` MCP server
- **Global Memory**: Maintains reusable patterns, best practices, and cross-project knowledge using the `global_memory` MCP server

### Memory Consolidation Process
1. Knowledge is first captured and validated in project memory
2. Approved patterns are promoted to global memory for reuse across projects
3. Version chaining ensures consistency during promotion
4. All operations are scoped to the `document_user` identity for traceability

## Promoted Global Patterns

The LOGReport project has successfully contributed to and refined several key universal patterns in global memory, ensuring their reusability across diverse projects. The memory hierarchy compliance workflow has also been successfully implemented, ensuring adherence to the `[MemoryType].[Domain].[SubCluster].[EntityType]_[Name]` template and significantly enhancing knowledge organization and retrievability.

### Universal Architectural Patterns

- **MVP (Model-View-Presenter) Pattern**: Separates presentation logic from UI components for better testability and maintainability.
- **Dual Memory System**: Combines project-specific memory with cross-project global memory for balanced knowledge management.
- **Service Layer Pattern**: Centralizes business logic in dedicated service classes for consistent processing and maintainability.
- **Circuit Breaker Pattern**: Stateful mechanism to prevent cascading failures in service calls, improving system resilience.
- **NodeManager Configuration Loading Pattern**: Robust configuration parsing and validation for application stability.
- **Dynamic Configuration Reload Pattern**: Ensures application components trigger full configuration reloads upon external dependency changes.
- **Circular Dependency Resolution Pattern**: Strategies for decoupling modules and improving reusability.

### Universal Design Patterns

- **Context Menu Filtering Pattern**: Dynamic UI customization through configuration-driven command visibility.
- **Hybrid Token Resolution Pattern**: Multi-step token resolution with intelligent fallback mechanisms for robust token handling.
- **Composite Key Pattern**: Uses multiple attributes as a composite key for resource management, ensuring unique identification.
- **Sequential Token Processing Pattern**: Processes batch operations through existing single-operation pipelines with isolated context.
- **Stateful Fault Tolerance Pattern**: Stateful mechanism to prevent cascading failures in service calls.
- **Heterogeneous Data Pipeline Pattern**: Processes diverse data types through a unified pipeline with isolated error handling.
- **Multi-Level Error Handling Pattern**: Manages errors at multiple scopes (individual units and system-wide operations).
- **UAL Identifier System**: Standardized asset referencing across contexts.
- **External Tool Integration Pattern**: Integrates external command-line tools with a GUI application.
- **Dynamic UI Presentation Pattern**: Dynamic UI feedback based on asynchronous operations.

### Universal Best Practices

- **API Contract Enforcement**: Standardized API development methodology requiring explicit interface definitions and comprehensive testing.

### Universal Workflow Patterns

- **Problem Solution Workflow**: Generic workflow for identifying, analyzing, solving, and validating issues.
- **Memory Hierarchy Compliance Workflow**: Systematic workflow for ensuring memory hierarchy compliance within a knowledge graph system.

## UAL Identifier System

The Universal Asset Locator (UAL) identifier system provides a standardized way to reference project assets across both project and global memory contexts.

### UAL Format
Identifiers follow the pattern: `ual://[context]/[entity-type]/[entity-name]`

Examples:
- `ual://project/component/CommandQueue` - Project-specific component
- `ual://global/pattern/CommandDesignPattern` - Global design pattern

### UAL Resolution
- Project UALs resolved through `project_memory` MCP server
- Global UALs resolved through `global_memory` MCP server

## Cryptographic Verification Process

The project implements cryptographic verification to ensure memory integrity and documentation authenticity.

### Hash-Based Verification
- All memory entities hashed using SHA-256 for integrity verification
- Relationship changes verified through Merkle tree structures
- Documentation updates include cryptographic signatures for authenticity

### Verification Workflow
1. Entity hashes computed before and after modifications
2. Changes validated against expected hash values
3. Failed verifications trigger rollback procedures
4. Successful verifications update memory graph with new hash references

## Group Node Interactions

Right-clicking on FBC or RPC group nodes in the Commander window triggers batch commands on all child log files within that group.

### Subgroup-Level Execution

Implemented in [`CommanderWindow.process_all_fbc_subgroup_commands()`](src/commander/command_queue.py:71) and [`process_all_rpc_subgroup_commands()`](src/commander/command_queue.py:95) methods:
1. Retrieve child log files via `NodeManager`
2. Dispatch commands through dedicated services:
   ```python
   def process_all_rpc_subgroup_commands(self):
       child_logs = self.node_manager.get_child_log_files()
       for log in child_logs:
           self.rpc_service.queue_rpc_command(log)
   ```
3. Includes error handling and sequential processing

### Node-Level Hierarchical Execution

**NEW in v1.1**: Right-clicking on a node itself provides the option to **Execute All Commands Hierarchically**, which orchestrates a complete three-phase workflow:

1. **Phase 1**: Execute all FBC commands for the node
2. **Phase 2**: Execute all RPC commands for the node  
3. **Phase 3**: Process all LOG files with BsTool

**Example Usage**:
```
AP01m (192.168.0.11) → Right-click → "Execute All Commands Hierarchically for AP01m"
  ├─ Phase 1/3: Executing 5 FBC commands...
  ├─ Phase 2/3: Executing 5 RPC commands...
  └─ Phase 3/3: Processing 3 LOG files...
  ✓ Hierarchical execution complete for AP01m: 13 commands processed
```

**Benefits**:
- **Efficiency**: Execute all node commands with a single action
- **Consistency**: Ensures commands execute in proper order
- **Automation**: Reduces manual effort for multi-protocol testing
- **Configuration**: Can be controlled via `config/menu_filter_rules.json`

See: [Hierarchical Command System](docs/architecture/ARCH_command_system.md#node-level-hierarchical-execution)

### Sequential Processing with Execution Controls

**NEW in v1.2**: The Commander window now supports bulk sequential execution of print commands across **all nodes** with full pause/resume/cancel controls:

**Print All Nodes Button**:
- Executes print commands for **all nodes** sequentially (one node at a time)
- Reuses the proven right-click "Execute All Print Commands" mechanism for each node
- Properly queues FBC and RPC commands through service layer
- Updates log files and visual feedback (colors) for each node

**Execution Controls**:
- **Pause**: Temporarily stops execution after current command completes
- **Resume**: Continues from paused state
- **Cancel**: Stops execution and resets to idle state

**Visual Tracking**:
- Tree automatically expands to show currently executing node
- Current log file highlighted during command execution
- Status bar shows progress: "Processing node 3/15: AP03m..."

**Example Usage**:
```
Commander Window Toolbar:
  [Print All Nodes] [Pause] [Resume] [Cancel]
  
Status: "Processing node 3/15: AP03m..."
  ✓ AP01m [5/5 commands] - Logs written, colors updated
  ✓ AP02m [5/5 commands] - Logs written, colors updated
  ► AP03m [2/5 commands] - Currently executing...
  ○ AP04m [pending]
  ... (12 more nodes)
```

**Technical Details**:
- **Sequential Chaining**: Uses `command_queue.is_processing` property to detect when each node's commands complete
- **QTimer Pattern**: 100ms delay after each command ensures reliable state detection
- **Service Integration**: Leverages `FbcCommandService` and `RpcCommandService` for proper command queuing
- **State Machine**: ExecutionState enum (IDLE/RUNNING/PAUSED/CANCELLED) manages control flow

**Benefits**:
- **Efficiency**: Process all nodes with one click instead of individual right-clicks
- **Control**: Pause/resume execution without losing progress
- **Safety**: Cancel anytime to abort remaining operations
- **Visibility**: Real-time visual feedback on execution status

**Implementation**:
- See: [Pause Resume Cancel Controls](docs/implementation/pause_resume_cancel_controls.md) - Full implementation guide
- See: [Print All Nodes Execution Fix](docs/implementation/print_all_nodes_execution_fix.md) - Technical architecture and chaining mechanism

See: [Hierarchical Command System](docs/architecture/ARCH_command_system.md#node-level-hierarchical-execution)

## Documentation

Additional documentation for key components and features:

- [Service Layer Pattern](docs/architecture/service_layer/service_layer_pattern.md) - Centralizes business logic in dedicated service classes
- [Context Menu Filtering](docs/blueprints/context_menu_filtering.md) - Dynamic control over context menu options based on configurable rules
- [Hybrid Token Resolution](docs/architecture/token_management/hybrid_token_resolution.md) - Multi-step token resolution with intelligent fallback mechanisms
- [Token Processing](docs/architecture/token_management/token_processing.md) - Identification, management, and execution of commands for various token types
- [Troubleshooting Guide](docs/user/troubleshooting/troubleshooting_guide.md) - Solutions to common issues related to node resolution and token management
## Documentation Structure

### Core Documentation
- [Changelog Management](docs/changelog/management.md) - Versioning and change tracking
- [Task Management System](docs/roadmaps/task_management.md) - Workflow and prioritization
- [Memory Consolidation](docs/blueprints/memory_consolidation.md) - Dual memory architecture
- **[Code Graph Guide](docs/technical/CODEGRAPH_GUIDE.md)** - Automated codebase structure mapping

### System Blueprints
- [Context Menu Filtering](docs/blueprints/context_menu_filtering.md) - Dynamic UI configuration
- [Session Recording](docs/blueprints/session_recording_blueprint.md) - Command capture/replay
- [VNC Integration](docs/blueprints/vnc_tab_blueprint.md) - Remote control implementation
- [Memory Standards Template](templates/memory_standards.md) - Standardized entity naming + clustering

### API References
- [Token Processing](docs/api_token_utilities.md) - FBC/RPC handling
- [Node Management](docs/node_manager_configuration.md) - Device tree configuration

## Development Workflow

### DevTeam Chatmode with VMP

The project uses **DevTeam chatmode** for structured AI-assisted development with **Vertical Mode Protocol (VMP)** for workflow interruption management.

**11-Phase Workflow**: PLAN → REMEMBER → ASSESS → ANALYZE → ARCHITECT → IMPLEMENT → DEBUG → TEST → LEARN → DOCUMENT → LOG

**VMP Features**:
- **Stack-Based Context**: Preserves workflow context during interruptions (user questions, agent-detected blockers)
- **Auto-Detection**: Automatically routes to appropriate phases when detecting anomalies, test failures, design flaws, requirement gaps
- **PUSH/POP Operations**: Enter vertical exploration (PUSH), resolve blocker, return to horizontal workflow (POP)
- **Breadcrumb Navigation**: Visual stack trail with ← arrows (e.g., 🏗️ ARCHITECT ← 🔬 ANALYZE ← 🐛 DEBUG)
- **Max Depth 5**: Safety limit with emergency POP_ALL for circular dependencies

See [DevTeam.chatmode.md](.github/chatmodes/DevTeam.chatmode.md) for complete workflow specification and [VMP_specification_draft.md](docs/architecture/VMP_specification_draft.md) for detailed protocol documentation.

## Testing

### Test Suite Organization

The project uses a **hierarchical test structure** for scalable organization:

```
tests/
├── unit/               # Isolated component tests
│   ├── sys_file/       # SYS file parsing & loading
│   ├── token_detection/  # Token identification
│   └── test_log_creator.py  # PDF log file creation
├── integration/        # Multi-component workflows
├── system/            # End-to-end scenarios
│   ├── telnet/        # Telnet connection management
│   └── ui/            # PyQt UI testing
└── regression/        # Bug prevention tests
```

### Test Metrics (Phase 6 Baseline - 2025-01-13)
- **Total Tests**: 226 collected (89 files)
- **Pass Rate**: 87.1% (27/31 executable tests)
- **Performance**: 0.34s total runtime, 0.02s slowest test
- **Coverage**: LogCreator (100% passing), Token Detection (100% passing), SYS File Parser (75% passing)

### Environment Blockers
- **Python 3.13**: telnetlib removed (22 tests blocked)
- **PyQt6**: DLL load errors (31 tests blocked)
- **Executable Subset**: 35/89 tests (39%)

### Running Tests

**Full Suite**:
```powershell
python -m pytest tests/ -v
```

**Specific Category**:
```powershell
python -m pytest tests/unit/ -v           # Unit tests only
python -m pytest tests/integration/ -v    # Integration tests
```

**Coverage Report**:
```powershell
python -m pytest tests/ --cov=src --cov-report=html
```

**With Performance Timing**:
```powershell
python -m pytest tests/ --durations=10
```

### Known Issues
- **AL Node Parsing**: 4/4 AL (AL-Link) tests fail with off-by-one token extraction (systematic issue)
- **Import Paths**: 74 tests blocked by missing `src.` prefix in utils/commander imports
- **Fixture Schema**: 13 tests blocked by 'token_id' key mismatch in test fixtures

See [Phase 6 Validation Report](logs/tests_analysis_PHASE_6_VALIDATION_20250113.md) for detailed analysis.

---

## Code Structure Analysis

The project maintains an automatically-generated **code graph** (`codegraph.json`) that provides a complete hierarchical representation of the `src/` codebase:

- **749 entities**: Modules (70), Classes (83), Methods (524), Functions (38)
- **5,114 relations**: IMPORTS, CALLS, INHERITS, BELONGS_TO hierarchies
- **6-layer structure**: Type → Domain → Cluster → Module → Class → Method

Generate the code graph:
```powershell
python scripts\generate_codegraph.py
```

See [Code Graph Guide](docs/technical/CODEGRAPH_GUIDE.md) for detailed usage and query examples.