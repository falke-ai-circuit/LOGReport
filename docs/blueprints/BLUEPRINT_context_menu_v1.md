# Context Menu System Blueprint

## Overview

This document details the architecture, implementation, and filtering mechanism of the context menu system in the LOGReport application. The system provides dynamic control over which context menu options are displayed to users based on configurable rules, enabling administrators to customize the UI experience by showing or hiding specific commands for different nodes, token types, or command categories. Additionally, the system properly handles batch operations through service layer integration, ensuring all tokens in a batch are processed correctly.

## 1. Architecture

The context menu system consists of several core components working in conjunction:

### 🧩 Core Components

| Component | Location | Responsibilities |
|---|---|---|
| **CommanderWindow** | `src/commander/commander_window.py` | Manages node tree display, handles right-click events, coordinates menu building, displays context menu |
| **ContextMenuFilterService** | `src/commander/services/context_menu_filter.py` | Loads/evaluates filtering rules (`config/menu_filter_rules.json`), determines command visibility based on context (node, section, command type) |
| **ContextMenuService** | `src/commander/services/context_menu_service.py` | UI service that integrates filtering with context menu display, dynamically adds/removes menu actions |
| **Configuration File** | `config/menu_filter_rules.json` | Defines filtering rules (e.g., `{"node_name": "AP01m", "section_type": "FBC", "action": "hide", "command_type": "all"}`) |

## 2. Filtering Mechanism

The filtering system works by evaluating a set of rules in sequence, with the first matching rule determining the outcome. Rules can match on:

- **Node Name**: Exact match, wildcard patterns (*, ?), or regular expressions
- **Section Type**: FBC, RPC, LOG, LIS, or other section types
- **Command Type**: Specific command types (e.g., `print`, `clear`) or "all" for any command
- **Command Category**: `token`, `subgroup`, `all`

The evaluation follows these steps:
1. When a context menu is requested, the system gathers the current context (node name, section type, command type, command category).
2. Each rule is evaluated in order until a match is found.
3. The action ("show" or "hide") from the first matching rule is applied.
4. If no rules match, the command is shown by default.

### ⚙️ Rule Properties

| Property | Description | Supported Values |
|---|---|---|
| **`description`** | Human-readable rule summary | `string` |
| **`node_name`** | Node name for rule application | `string` (exact, wildcard `*`, regex `/pattern/`) |
| **`section_type`** | Section type(s) | `FBC`, `RPC`, `LOG`, `LIS` (or `array` of types) |
| **`action`** | Action to perform on match | `show`, `hide` |
| **`command_type`** | Command type(s) | `string` (e.g., `print`, `clear`) or `all` |
| **`command_category`** | Command category | `token`, `subgroup`, `all` |

## 3. Implementation Details

### 3.1. ContextMenuFilterService

The `ContextMenuFilterService` class is responsible for:

1. **Loading Rules**: Reading filtering rules from the configuration file.
2. **Rule Evaluation**: Determining if commands should be shown based on context.
3. **Pattern Matching**: Supporting wildcard and regex patterns in rule definitions.

#### 🔑 Key Methods

| Method | Description |
|---|---|
| `should_show_command()` | Main entry for command visibility evaluation |
| `_rule_matches()` | Internal check if rule applies to current context |
| `_matches_pattern()` | Helper for wildcard/regex pattern matching |

### 3.2. ContextMenuService Integration

**Note on `_get_current_item_from_data`**: This method is used to create a mock item from item data for compatibility with existing presenter methods that expect a `QTreeWidget` item structure. This ensures seamless integration without altering core UI component expectations.

The `ContextMenuService` integrates filtering through:

1. **Rule Checking**: Before adding menu items, checking if they should be visible.
2. **Dynamic Menu Generation**: Only creating menu actions for visible commands.
3. **Context Preservation**: Maintaining proper context information for rule evaluation.

#### Example Integration

```python
# In ContextMenuService.show_context_menu()
if item_data and isinstance(item_data, dict) and 'token' in item_data:
    token_type = item_data.get("token_type", "UNKNOWN").upper()
    token_id = item_data.get("token")
    node_name = item_data.get("node", "Unknown")

    if token_id:
        # Check if FBC token commands should be shown
        if not self.context_menu_filter.should_show_command(
            node_name=node_name,
            section_type=token_type,
            command_type="all",
            command_category="token"
        ):
            logging.debug(f"Context menu filtered out FBC token command for {token_id}")
        else:
            # Add menu item...
```

## 4. Batch Operation Processing

The context menu system handles batch operations through dedicated methods in the `CommanderWindow` class:

- `process_all_fbc_subgroup_commands()`: Processes all FBC tokens in a subgroup by calling `fbc_service.queue_fieldbus_command()` for each token.
- `process_all_rpc_subgroup_commands()`: Processes all RPC tokens in a subgroup by calling `rpc_service.queue_rpc_command()` for each token.

These methods ensure proper command generation, error handling, and logging by leveraging the service layer rather than direct command queue manipulation. The service methods handle command processing internally, including starting the command queue when needed, which eliminates the need for explicit `command_queue.start_processing()` calls.

### 🔗 Service Layer Integration Benefits

| Benefit | Description |
|---|---|
| **Consistent Command Generation** | Service methods ensure correct format & parameters |
| **Proper Error Handling** | Centralized error handling logic |
| **Comprehensive Logging** | Appropriate logging for monitoring & debugging |
| **Automatic Queue Management** | Handles starting/stopping command queue |
| **Thread Safety** | Ensures thread-safe command execution |
| **Extensibility** | New functionality added without UI code modification |

## 5. Configuration Example

Filtering rules are defined in `config/menu_filter_rules.json`:

```json
{
  "rules": [
    {
      "description": "Hide AP01m FBC token commands",
      "node_name": "AP01m",
      "section_type": "FBC",
      "action": "show",
      "command_type": "all",
      "command_category": "token"
    },
    {
      "description": "Show FBC/RPC subgroup menus",
      "section_type": ["FBC", "RPC"],
      "action": "show",
      "command_type": "all",
      "command_category": "subgroup"
    },
    {
      "description": "Hide print commands for maintenance nodes",
      "node_name": "MNT*",
      "section_type": "FBC",
      "action": "hide",
      "command_type": "print"
    }
  ]
}
```

## 6. Pattern Matching

The filtering system supports several pattern matching options:

### Exact Matching
```json
{
  "node_name": "AP01m",
  "section_type": "FBC"
}
```

### Wildcard Matching
```json
{
  "node_name": "AP01*",
  "section_type": ["FBC", "RPC"]
}
```

### Regex Matching
```json
{
  "node_name": "/AP01[abc]/",
  "section_type": "FBC"
}
```

## 7. Use Cases

| Use Case | Description | Example Rule |
|---|---|---|
| **Node-Specific Filtering** | Hide/show commands for specific nodes | `{"node_name": "MAINT01", "action": "hide", "command_type": "all"}` |
| **Token Type Filtering** | Control visibility by token type | `{"section_type": "RPC", "action": "show", "command_type": "all"}` |
| **Command Category Filtering** | Control visibility of token vs. subgroup commands | `{"command_category": "subgroup", "action": "hide", "command_type": "all"}` |

## 8. Benefits

This architecture provides several advantages:

1. **Flexibility**: Rules can be modified without code changes.
2. **Maintainability**: Centralized control of menu visibility.
3. **Scalability**: Easy to add new rules for different node types.
4. **Consistency**: Uniform approach to command filtering across the application.
5. **Configurability**: Environment-specific rules can be deployed through configuration.
6. **User Experience**: Dynamic UI customization based on context.

## 9. Best Practices

### 9.1. Rule Specificity
Place more specific rules before general ones since the first matching rule takes precedence.

### 9.2. Descriptive Rules
Use clear descriptions to document the purpose of each rule.

### 9.3. Testing
Test filtering rules with various node and token combinations to ensure expected behavior.

### 9.4. Default Behavior
Remember that the default behavior is to show commands, so explicit "hide" rules are needed to remove options.

## 10. Related Components

### Configuration File
- [menu_filter_rules.json](config/menu_filter_rules.json)

### Service Classes
- [ContextMenuFilterService](src/commander/services/context_menu_filter.py)
- [ContextMenuService](src/commander/services/context_menu_service.py)

### UI Integration
- [NodeTreePresenter](src/commander/presenters/node_tree_presenter.py)

## 11. Testing

Context menu filtering is tested through:
- Manual verification of menu options with different rule configurations.
- Unit tests for pattern matching functions.
- Integration tests with sample configuration files.

## 12. Future Enhancements

Potential improvements to the system include:
- GUI for managing filter rules.
- Rule validation and testing tools.
- Performance optimization for large rule sets.
- Integration with user roles/permissions.
- Logging of rule evaluations for debugging.

## 13. References

- [ContextMenuFilterService Implementation](src/commander/services/context_menu_filter.py)
- [ContextMenuService Implementation](src/commander/services/context_menu_service.py)
- [Configuration File](config/menu_filter_rules.json)