# 📋 Context Menu System Blueprint

<!-- RECONCILIATION NOTE (2026-07-15 — Coder)
     This blueprint describes the ORIGINAL Python-era context menu system (PyQt5).
     In the Go implementation, context menus are handled in NodeTree.tsx (React/TypeScript).
     Queue actions (clear, restart, retry-failed) are available in context menus.
     Context menu sends commands through the command queue API, not direct execution.
     This document is preserved as historical design reference only.
-->

<!-- METADATA -->
metadata: {
  created_date: "2025-10-08_172500",
  last_modified: "2025-10-08_172500",
  last_accessed: "2025-10-08_172500",
  word_count: 1678,
  reference_count: 3,
  document_hash: "context_menu_blueprint",
  obsolete_check_date: "2025-10-08",
  section_count: 6,
  internal_link_count: 13
}
<!-- /METADATA -->

## 📑 Table of Contents

- [Overview](#overview)
- [Menu Architecture](#menu-architecture)
- [Filtering System](#filtering-system)
- [Command Routing](#command-routing)
- [Configuration](#configuration)
- [Implementation](#implementation)

---

## 🎯 Overview

Blueprint for the dynamic context menu system that provides node and token-specific commands based on filtering rules.

### Key Features

| Feature | Description | Benefit |
|---------|-------------|---------|
| **Dynamic Generation** | Menus generated based on context | Relevant commands only |
| **Filtering Rules** | Configure command visibility | Flexible control |
| **Multi-Protocol** | Support FBC, RPC, BsTool, LOG | Comprehensive |
| **Batch Operations** | Multi-select support | Efficiency |

---

## 🏗️ Menu Architecture

**Context Menu Service**:
```python
class ContextMenuService:
    """Generate dynamic context menus for nodes and tokens."""
    
    def generate_menu(self, items: List[QTreeWidgetItem]) -> QMenu:
        """
        Generate context menu based on selected items.
        
        Args:
            items: Selected tree widget items
        
        Returns:
            QMenu with available commands
        """
        menu = QMenu()
        
        # Determine context
        if all(self._is_node(item) for item in items):
            self._add_node_commands(menu, items)
        elif all(self._is_token(item) for item in items):
            self._add_token_commands(menu, items)
        else:
            # Mixed selection - limited commands
            self._add_common_commands(menu, items)
        
        return menu
```

**Menu Structure**:
```
Context Menu
├── FBC Commands
│   ├── Execute FBC Token
│   └── Execute All FBC Tokens
├── RPC Commands
│   ├── Print RPC Counters
│   └── Clear RPC Counters
├── BsTool Commands
│   └── Process with BsTool
├── LOG Commands
│   ├── Open Log Directory
│   └── View Recent Logs
└── Node Commands
    ├── Refresh Node Status
    └── Configure Node
```

See: [Commander Window](../technical/TECH_commander_window.md#command-execution)

---

## 🔍 Filtering System

The filtering system controls command visibility based on rules.

**Filter Configuration**:
```json
{
  "filters": {
    "fbc_commands": {
      "visible_for": ["fbc_token", "node_with_fbc"],
      "hidden_for": ["rpc_only_node"],
      "conditions": {
        "node_online": true
      }
    },
    "rpc_commands": {
      "visible_for": ["rpc_token", "node_with_rpc"],
      "conditions": {
        "node_online": true
      }
    },
    "bstool_commands": {
      "visible_for": ["any_token"],
      "conditions": {
        "log_exists": true
      }
    }
  }
}
```

**Filter Application**:
```python
def should_show_command(command: str, context: dict) -> bool:
    """
    Determine if command should be shown.
    
    Args:
        command: Command identifier
        context: Current selection context
    
    Returns:
        True if command should be visible
    """
    filter_config = load_filter_config()
    filter_rules = filter_config['filters'].get(command, {})
    
    # Check visible_for rules
    visible_for = filter_rules.get('visible_for', [])
    if visible_for and context['type'] not in visible_for:
        return False
    
    # Check hidden_for rules
    hidden_for = filter_rules.get('hidden_for', [])
    if context['type'] in hidden_for:
        return False
    
    # Check conditions
    conditions = filter_rules.get('conditions', {})
    for condition, required_value in conditions.items():
        if context.get(condition) != required_value:
            return False
    
    return True
```

---

## 🔀 Command Routing

Commands are routed to appropriate services based on type.

**Routing Table**:
| Command | Service | Method |
|---------|---------|--------|
| **Execute FBC** | FbcCommandService | `queue_fieldbus_command()` |
| **Print RPC** | RpcCommandService | `queue_rpc_command('print')` |
| **Clear RPC** | RpcCommandService | `queue_rpc_command('clear')` |
| **Process BsTool** | BsToolCommandService | `execute_bstool()` |
| **Open Log Dir** | LoggingService | `open_log_directory()` |

**Router Implementation**:
```python
def route_command(command: str, context: dict):
    """Route command to appropriate service."""
    
    routing_table = {
        'execute_fbc': lambda: fbc_service.queue_fieldbus_command(
            context['node_name'], 
            context['token_id']
        ),
        'print_rpc': lambda: rpc_service.queue_rpc_command(
            context['node_name'], 
            context['token_id'],
            'print'
        ),
        'clear_rpc': lambda: rpc_service.queue_rpc_command(
            context['node_name'], 
            context['token_id'],
            'clear'
        ),
        'process_bstool': lambda: bstool_service.execute_bstool(
            context['log_path']
        ),
        'open_log_dir': lambda: logging_service.open_log_directory(
            context['node_name']
        )
    }
    
    handler = routing_table.get(command)
    if handler:
        handler()
    else:
        logging.warning(f"Unknown command: {command}")
```

See: [Command System](../architecture/ARCH_command_system.md#command-services)

---

## ⚙️ Configuration

Context menu configuration is stored in JSON format.

**Configuration File**: `config/context_menu.json`

**Example Configuration**:
```json
{
  "version": "1.0",
  "filters": {
    "fbc_commands": {
      "visible_for": ["fbc_token", "node_with_fbc"],
      "conditions": {
        "node_online": true
      }
    },
    "rpc_commands": {
      "visible_for": ["rpc_token", "node_with_rpc"],
      "conditions": {
        "node_online": true
      }
    }
  },
  "commands": {
    "execute_fbc": {
      "label": "Execute FBC Token",
      "icon": "fbc_icon.png",
      "shortcut": "Ctrl+F",
      "filter": "fbc_commands"
    },
    "print_rpc": {
      "label": "Print RPC Counters",
      "icon": "rpc_icon.png",
      "shortcut": "Ctrl+R",
      "filter": "rpc_commands"
    }
  }
}
```

---

## 🔨 Implementation

**Implementation Steps**:

1. **Create ContextMenuService** - Core service for menu generation
2. **Implement Filter System** - Load and apply filtering rules
3. **Build Command Router** - Route commands to services
4. **Add UI Integration** - Connect to NodeTreeWidget
5. **Configure Filters** - Define filtering rules in JSON
6. **Test Scenarios** - Validate all menu combinations

**Key Classes**:
- `ContextMenuService` - Menu generation and filtering
- `CommandRouter` - Command routing logic
- `FilterConfigLoader` - Load filtering configuration

---

## 📚 References

### Related Documentation

- **[Commander Window](../technical/TECH_commander_window.md)** - UI integration
- **[Command System](../architecture/ARCH_command_system.md)** - Command execution
- **[Implementation Plan](BLUEPRINT_implementation_phases.md)** - Implementation roadmap

### Source Code

- **Context Menu Service**: `src/commander/services/context_menu_service.py`
- **Filter Config**: `config/context_menu.json`

---

**Document Status**: ✅ **COMPLETE** - Consolidated from 5 source documents
**Last Updated**: 2025-10-08
**Next Review**: 2026-01-08 (90 days)
