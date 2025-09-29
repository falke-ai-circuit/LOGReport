# Context Menu Filtering Documentation

## Overview

The Context Menu Filtering system provides dynamic control over which context menu options are displayed to users based on configurable rules. This system enables administrators to customize the UI experience by showing or hiding specific commands for different nodes, token types, or command categories.

## Architecture

The context menu filtering system consists of two main components:

1. **ContextMenuFilterService**: Core service that evaluates filtering rules
2. **ContextMenuService**: UI service that integrates filtering with context menu display

## Configuration

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
    }
  ]
}
```

### ⚙️ Rule Properties

| Property | Description | Supported Values |
|---|---|---|
| **`description`** | Human-readable rule summary | `string` |
| **`node_name`** | Node name for rule application | `string` (exact, wildcard `*`, regex `/pattern/`) |
| **`section_type`** | Section type(s) | `FBC`, `RPC`, `LOG`, `LIS` (or `array` of types) |
| **`action`** | Action to perform on match | `show`, `hide` |
| **`command_type`** | Command type(s) | `string` (e.g., `print`, `clear`) or `all` |
| **`command_category`** | Command category | `token`, `subgroup`, `all` |

## Implementation Details

### ContextMenuFilterService

The `ContextMenuFilterService` class is responsible for:

1. **Loading Rules**: Reading filtering rules from the configuration file
2. **Rule Evaluation**: Determining if commands should be shown based on context
3. **Pattern Matching**: Supporting wildcard and regex patterns in rule definitions

#### 🔑 Key Methods

| Method | Description |
|---|---|
| `should_show_command()` | Main entry for command visibility evaluation |
| `_rule_matches()` | Internal check if rule applies to current context |
| `_matches_pattern()` | Helper for wildcard/regex pattern matching |

### ContextMenuService Integration

The `ContextMenuService` integrates filtering through:

1. **Rule Checking**: Before adding menu items, checking if they should be visible
2. **Dynamic Menu Generation**: Only creating menu actions for visible commands
3. **Context Preservation**: Maintaining proper context information for rule evaluation

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

## Pattern Matching

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

## 🎯 Use Cases

| Use Case | Description | Example Rule |
|---|---|---|
| **Node-Specific Filtering** | Hide/show commands for specific nodes | `{"node_name": "MAINT01", "action": "hide", "command_type": "all"}` |
| **Token Type Filtering** | Control visibility by token type | `{"section_type": "RPC", "action": "show", "command_type": "all"}` |
| **Command Category Filtering** | Control visibility of token vs. subgroup commands | `{"command_category": "subgroup", "action": "hide", "command_type": "all"}` |

## Best Practices

### 1. Rule Specificity
Place more specific rules before general ones since the first matching rule takes precedence.

### 2. Descriptive Rules
Use clear descriptions to document the purpose of each rule.

### 3. Testing
Test filtering rules with various node and token combinations to ensure expected behavior.

### 4. Default Behavior
Remember that the default behavior is to show commands, so explicit "hide" rules are needed to remove options.

## Related Components

### Configuration File
- [menu_filter_rules.json](config/menu_filter_rules.json)

### Service Classes
- [ContextMenuFilterService](src/commander/services/context_menu_filter.py)
- [ContextMenuService](src/commander/services/context_menu_service.py)

### UI Integration
- [NodeTreePresenter](src/commander/presenters/node_tree_presenter.py)

## Testing

Context menu filtering is tested through:
- Manual verification of menu options with different rule configurations
- Unit tests for pattern matching functions
- Integration tests with sample configuration files

## References

- [ContextMenuFilterService Implementation](src/commander/services/context_menu_filter.py)
- [ContextMenuService Implementation](src/commander/services/context_menu_service.py)
- [Configuration File](config/menu_filter_rules.json)