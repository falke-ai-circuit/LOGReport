# LOGReport Project Overview

## Memory Consolidation Workflow Implementation

The LOGReport project implements a dual memory consolidation workflow that combines project-specific memory with cross-project global memory. This approach ensures both localized context and reusable knowledge patterns are maintained.

### Dual Memory System
- **Project Memory**: Stores project-specific entities, relationships, and implementation details using the `project_memory` MCP server
- **Global Memory**: Maintains reusable patterns, best practices, and cross-project knowledge using the `global_memory` MCP server

### Memory Consolidation Process
1. Knowledge is first captured and validated in project memory
2. Approved patterns are promoted to global memory for reuse across projects
3. Version chaining ensures consistency during promotion
4. All operations are scoped to the `document_user` identity for traceability

## Promoted Global Patterns

The LOGReport project has successfully promoted several key architectural patterns to global memory for reuse across projects:

### MVP (Model-View-Presenter) Pattern
- **Description**: Separates presentation logic from UI components for better testability and maintainability
- **Implementation**: Used throughout the Commander UI with dedicated presenter classes
- **Benefits**: Enhanced modularity, easier testing, and clearer separation of concerns

### Context Menu Filtering Pattern
- **Description**: Dynamic UI customization through configuration-driven command visibility
- **Implementation**: Configurable rules in `config/menu_filter_rules.json` control menu item visibility
- **Benefits**: Flexible UI customization without code changes, improved user experience

### Service Layer Pattern
- **Description**: Centralizes business logic in dedicated service classes
- **Implementation**: FbcCommandService and RpcCommandService handle all command-related operations
- **Benefits**: Consistent command processing, reduced code duplication, improved maintainability

### Hybrid Token Resolution Pattern
- **Description**: Multi-step token resolution with intelligent fallback mechanisms
- **Implementation**: Handles tokens that may exist in multiple formats or locations
- **Benefits**: Robust token handling, graceful degradation when primary tokens unavailable

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

### Implementation Details
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

### System Blueprints
- [Context Menu Filtering](docs/blueprints/context_menu_filtering.md) - Dynamic UI configuration
- [Session Recording](docs/blueprints/session_recording_blueprint.md) - Command capture/replay
- [VNC Integration](docs/blueprints/vnc_tab_blueprint.md) - Remote control implementation

### API References
- [Token Processing](docs/api_token_utilities.md) - FBC/RPC handling
- [Node Management](docs/node_manager_configuration.md) - Device tree configuration