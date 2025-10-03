# Clear All Subgroup Files Command

## Overview
This document describes the implementation and usage of the 'Clear All Subgroup Files' command within the LOGReport application. This feature allows users to clear all log files associated with a selected subgroup (e.g., FBC, RPC sections) directly from the node tree context menu.

## Implementation Details

### 1. NodeTreePresenter.clear_subgroup_log_files
- **File**: `src/commander/presenters/node_tree_presenter.py`
- **Description**: This method is responsible for the core logic of clearing subgroup log files.
    - It takes a `QTreeWidgetItem` representing a subgroup section as input.
    - It extracts the `section_type` and `node` information from the item's user data.
    - It iterates through all child items of the subgroup. For each child identified as a log file (by checking for a `log_path` in its user data), it calls `BsToolCommandService.clear_log()` with the extracted log file path.
    - Status messages are emitted to the UI to inform the user about the clearing process and its completion.
    - Error handling is included to report issues during file clearing.

### 2. ContextMenuService Integration
- **File**: `src/commander/services/context_menu_service.py`
- **Description**: The `show_context_menu` method has been extended to dynamically add the 'Clear All Subgroup Files' action to the context menu.
    - When a subgroup item (specifically "FBC" or "RPC" section types) is right-clicked, a new `QAction` is created with the text "Clear All {section_type} Log Files for {node_name}".
    - This action is connected to the `node_tree_presenter.clear_subgroup_log_files` method, ensuring that when the action is triggered, the presenter's method is called with the relevant subgroup item.
    - The visibility of this action is controlled by the `ContextMenuFilterService`.

### 3. ContextMenuFilterService Rule
- **File**: `config/menu_filter_rules.json`
- **Description**: A new rule has been added to this configuration file to manage the visibility of the 'Clear All Subgroup Files' command.
    - The rule specifies that the `clear_all_subgroup_files` command should be shown (`"action": "show"`) for `section_type` "FBC" and "RPC" under the `command_category` "subgroup". This ensures the command only appears in appropriate contexts.

### 4. Core File Clearing Utility
- **Service**: `BsToolCommandService.clear_log`
- **Description**: This service method is the underlying utility responsible for physically clearing the content of a specified log file. It is called by `NodeTreePresenter.clear_subgroup_log_files`.

## Usage
1. Right-click on an FBC or RPC subgroup node in the node tree.
2. A context menu will appear.
3. Select the "Clear All {section_type} Log Files for {node_name}" option.
4. All log files under that specific subgroup will be cleared, and status messages will be displayed in the application's status bar.

## Testing
Basic unit tests have been initiated to verify:
- `NodeTreePresenter.clear_subgroup_log_files` correctly calls `BsToolCommandService.clear_log` for all child log files.
- The 'Clear All Subgroup Files' action is correctly displayed in the context menu for relevant subgroup types.
- The action is hidden when filter rules disallow it.

## Future Enhancements
- Add confirmation dialog before clearing files.
- Implement undo functionality for cleared files.
- Extend to other subgroup types if required.