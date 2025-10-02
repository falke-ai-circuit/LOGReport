---
reason: 'superseded by v2'
archived_date: '2025-10-02'
original_path: 'docs/blueprints/BLUEPRINT_context_menu_architecture_v1.md'
---

# Context Menu Architecture

This document details the architecture and implementation of the context menu system in the LOGReport application, with a focus on the filtering mechanism that controls command visibility and the service layer integration for batch operations.

## Overview

The context menu system provides users with a right-click interface to execute commands on nodes and log files. The system has been enhanced with a filtering mechanism that dynamically controls which commands are visible based on node type, section type, and other contextual factors. Additionally, the system now properly handles batch operations through service layer integration, ensuring all tokens in a batch are processed correctly.

## 🧩 Core Components

| Component | Location | Responsibilities |
|-----------|----------|------------------|
| **CommanderWindow** | `src/commander/commander_window.py` | Manages node tree display, handles right-click events, coordinates menu building, displays context menu |
| **ContextMenuFilterService** | `src/commander/services/context_menu_filter.py` | Loads/evaluates filtering rules (`config/menu_filter_rules.json`), determines command visibility based on context (node, section, command type) |
| **Configuration File** | `config/menu_filter_rules.json` | Defines filtering rules (e.g., `{"node_name": "AP01m", "section_type": "FBC", "action": "hide", "command_type": "all"}`) |

## Filtering Mechanism

The filtering system works by evaluating a set of rules in sequence, with the first matching rule determining the outcome. Rules can match on:

- **Node Name**: Exact match, wildcard patterns (*, ?), or regular expressions
- **Section Type**: FBC, RPC, or other section types
- **Command Type**: Specific command types or "all" for any command

The evaluation follows these steps:
1. When a context menu is requested, the system gathers the current context (node name, section type, etc.)
2. Each rule is evaluated in order until a match is found
3. The action ("show" or "hide") from the first matching rule is applied
4. If no rules match, the command is shown by default

## Implementation Details

The `ContextMenuFilterService` class implements the filtering logic with the following key methods:

- `should_show_command(node_name, section_type, command_type)`: Main entry point that determines visibility
- `_rule_matches(rule, node_name, section_type, command_type)`: Checks if a rule applies to the current context
- `_matches_pattern(value, pattern)`: Handles pattern matching with support for exact, wildcard, and regex patterns

## Batch Operation Processing

The context menu system handles batch operations through dedicated methods in the `CommanderWindow` class:

- `process_all_fbc_subgroup_commands()`: Processes all FBC tokens in a subgroup by calling `fbc_service.queue_fieldbus_command()` for each token
- `process_all_rpc_subgroup_commands()`: Processes all RPC tokens in a subgroup by calling `rpc_service.queue_rpc_command()` for each token

These methods ensure proper command generation, error handling, and logging by leveraging the service layer rather than direct command queue manipulation. The service methods handle command processing internally, including starting the command queue when needed, which eliminates the need for explicit `command_queue.start_processing()` calls.

## 🔗 Service Layer Integration Benefits

| Benefit | Description |
|---------|-------------|
| **Consistent Command Generation** | Service methods ensure correct format & parameters |
| **Proper Error Handling** | Centralized error handling logic |
| **Comprehensive Logging** | Appropriate logging for monitoring & debugging |
| **Automatic Queue Management** | Handles starting/stopping command queue |
| **Thread Safety** | Ensures thread-safe command execution |
| **Extensibility** | New functionality added without UI code modification |

## Usage Example

To hide a specific command type for a node pattern:

```json
{
  "description": "Hide print commands for maintenance nodes",
  "node_name": "MNT*",
  "section_type": "FBC",
  "action": "hide",
  "command_type": "print"
}
```

## Benefits

This architecture provides several advantages:

1. **Flexibility**: Rules can be modified without code changes
2. **Maintainability**: Centralized control of menu visibility
3. **Scalability**: Easy to add new rules for different node types
4. **Consistency**: Uniform approach to command filtering across the application
5. **Configurability**: Environment-specific rules can be deployed through configuration

## Future Enhancements

Potential improvements to the system include:
- GUI for managing filter rules
- Rule validation and testing tools
- Performance optimization for large rule sets
- Integration with user roles/permissions
- Logging of rule evaluations for debugging