# TECH_hierarchical_commands_architecture_v1.md

## Overview
This document details the architecture of the hierarchical command execution system, which enables the sequential execution of multiple sub-commands (FBC, RPC, LOG, BSTool) from a single context menu action. This system enhances automation and streamlines complex operational workflows.

## Specs

### HierarchicalCommandService
- **Purpose**: Orchestrates the sequential execution of sub-commands.
- **Location**: `src/commander/services/hierarchical_command_service.py`
- **Key Responsibilities**:
    - Manages the execution flow of a list of sub-commands.
    - Handles error reporting: stops execution on the first error or continues based on configuration.
    - Reports progress and status updates via PyQt signals.
    - Interacts with `CommandQueue` for actual command dispatch.
- **Dependencies**:
    - `NodeManager`: To retrieve node-specific information.
    - `CommandQueue`: For queuing and executing individual commands.
    - `FbcCommandService`, `RpcCommandService`, `BsToolCommandService`, `LogCommandService`: For specific command type execution.

### Node and NodeManager Modifications
- **Node Dataclass**:
    - **Location**: `src/commander/models.py`
    - **Modification**: Added a new field `hierarchical_commands: Dict[str, Dict[str, List[Dict]]]` to store hierarchical command definitions.
    - **Structure**: This field maps a command name (e.g., "Full_Diagnostic") to a dictionary containing command sequences for different token types (e.g., "FBC", "RPC"). Each sequence is a list of dictionaries, where each dictionary defines a sub-command (type, command string, parameters).
- **NodeManager**:
    - **Location**: `src/commander/node_manager.py`
    - **Modification**: Updated `_parse_config` to load the `hierarchical_commands` field from `nodes.json` into `Node` objects.
    - **Modification**: Updated `save_configuration` to correctly serialize and save the `hierarchical_commands` back to `nodes.json`.

### Context Menu Integration
- **ContextMenuService**:
    - **Location**: `src/commander/services/context_menu_service.py`
    - **Modification**: Dynamically generates submenus for hierarchical commands.
    - **Behavior**: When a node with `hierarchical_commands` is right-clicked, a new "Execute All Node Commands" option appears, with a submenu listing the defined hierarchical commands.
- **CommanderPresenter**:
    - **Location**: `src/commander/presenters/commander_presenter.py`
    - **Modification**: Implemented `process_hierarchical_command` method to handle the selection of a hierarchical command from the context menu.
    - **Responsibility**: Initiates the execution of the selected hierarchical command by calling `HierarchicalCommandService.execute_hierarchical_command` and subscribes to its progress signals to provide UI feedback.

## Configuration

### `nodes.json` Structure for Hierarchical Commands
Hierarchical commands are defined within the `nodes.json` file under the `hierarchical_commands` key for each node.

```json
{
  "nodes": [
    {
      "name": "AP01m",
      "ip_address": "192.168.1.10",
      "tokens": {
        "FBC": ["123", "456"],
        "RPC": ["789"]
      },
      "hierarchical_commands": {
        "Full_Diagnostic": {
          "FBC": [
            {"command": "READ_STATUS", "params": {"token": "123"}},
            {"command": "READ_DIAG", "params": {"token": "456"}}
          ],
          "RPC": [
            {"command": "GET_VERSION", "params": {"token": "789"}}
          ],
          "LOG": [
            {"command": "VIEW_LOG", "params": {"path": "/var/log/ap01.log"}}
          ],
          "BSTool": [
            {"command": "-errlog", "params": {"file": "AP01m_error.log"}}
          ]
        },
        "Quick_Check": {
          "FBC": [
            {"command": "PING", "params": {"token": "123"}}
          ]
        }
      }
    }
  ]
}
```

- **`hierarchical_commands`**: A dictionary where keys are the names of the hierarchical commands (e.g., "Full_Diagnostic", "Quick_Check").
- **Sub-command Types**: Each hierarchical command contains keys for command types (`FBC`, `RPC`, `LOG`, `BSTool`).
- **Command Definition**: Each command type lists dictionaries, where each dictionary specifies a `command` string and its `params`.

## References
- **Design Document**: `ceph_hierarchical_execution.json` (for initial problem statement and high-level design)
- **Service Implementation**: `src/commander/services/hierarchical_command_service.py`
- **Node Data Model**: `src/commander/models.py`
- **Node Configuration Management**: `src/commander/node_manager.py`
- **Context Menu Logic**: `src/commander/services/context_menu_service.py`
- **Presenter Logic**: `src/commander/presenters/commander_presenter.py`