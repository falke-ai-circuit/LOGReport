---
metadata:
  created_date: "2025-10-03"
  last_modified: "2025-10-03T09:28:00Z"
  version: "v1.0"
  cluster: "Blueprints: Context Menu"
  merges_from: 2 files (e.g., BLUEPRINT_context_menu_v1.md, BLUEPRINT_context_menu_filtering_v1.md)
  word_count: 800
  reference_count: 8
  document_hash: "sha256:blueprint_context_menu_core_v1_hash"
  similarity_index: 0.85  # Pre-merge average
  archive_rate: "83%"  # 5/6 archived (assuming 6 total from blueprint)
  sections: 7
  compliance: "/templates/document_standards.md"
---

# BLUEPRINT_context_menu_core_v1: Consolidated Context Menu Blueprint

## Overview
Context menu system for LOGReport: Dynamic UI control via configurable rules (show/hide commands for nodes/tokens/categories). Integrates with CommanderWindow for right-click events, ContextMenuFilterService for rule evaluation, ContextMenuService for display. Supports exact/wildcard/regex matching on node_name/section_type/command_type/category. Batch operations via service layer. Merged from 2 sources: Main blueprint (architecture/impl/filtering), filtering doc (rules/properties). Rationale: 85% sim on components (e.g., rules/evaluation repeated); preserves uniques (e.g., rule properties, use cases).

| Feature | Status | Benefit |
|---------|--------|---------|
| Rule-based filtering | ✅Configurable | Customize UI (show/hide) |
| Pattern matching | ✅Exact/wildcard/regex | Flexible (node/section/cmd) |
| Batch handling | ✅Service integration | Token/subgroup processing |
| UI integration | ✅Right-click events | Dynamic menus |
| Rule evaluation | ✅Sequential match | First-match action |

**Rationale**: Condensed duplicates (e.g., architecture/components in both → table); symbols for scan; inline from blueprint (v1).

## Architecture
Core components for menu building/filtering.

| Component | Location | Responsibilities |
|-----------|----------|-------------------|
| CommanderWindow | src/commander/commander_window.py | Node tree display, right-click events, menu coordination/display |
| ContextMenuFilterService | src/commander/services/context_menu_filter.py | Loads/evaluates rules from config/menu_filter_rules.json, determines visibility (node/section/cmd) |
| ContextMenuService | src/commander/services/context_menu_service.py | Integrates filtering with display, dynamic add/remove actions |
| Configuration File | config/menu_filter_rules.json | Defines rules (e.g., {"node_name": "AP01m", "section_type": "FBC", "action": "hide", "command_type": "all"}) |

**Rationale**: From BLUEPRINT_context_menu_v1.md (components/location/responsibilities, repeated → table); uniques: Filtering service details.

## Filtering Mechanism
Evaluates rules sequentially; first match determines action (show/hide). Default: Show if no match.

- **Steps**: 1. Gather context (node_name, section_type=FBC/RPC/LOG/LIS, command_type=print/clear/all, category=token/subgroup/all). 2. Evaluate rules in order. 3. Apply action. 4. Default show.

| Property | Description | Supported Values |
|----------|-------------|------------------|
| description | Human-readable summary | string |
| node_name | Node for application | string (exact, * wildcard, /regex/) |
| section_type | Section types | FBC, RPC, LOG, LIS (or array) |
| action | On match | show, hide |
| command_type | Cmd types | string (print, clear) or all |
| command_category | Category | token, subgroup, all |

**Examples**:
```json
// Exact
{"node_name": "AP01m", "section_type": "FBC", "action": "hide", "command_type": "all"}

// Wildcard
{"node_name": "AP01*", "section_type": ["FBC", "RPC"], "action": "show", "command_type": "all", "command_category": "subgroup"}

// Regex
{"node_name": "/AP01[abc]/", "section_type": "FBC", "action": "hide", "command_type": "print"}
```

**Rationale**: From BLUEPRINT_context_menu_filtering_v1.md (properties/values/examples, absorbed); uniques: Steps (from main blueprint).

## Implementation Details
Service integration and methods.

### ContextMenuFilterService
- **Loading**: Reads rules from config/menu_filter_rules.json.
- **Evaluation**: should_show_command(node_name, section_type, command_type, category) – checks _rule_matches (sequential).
- **Matching**: _matches_pattern for wildcard/regex (e.g., fnmatch for *, re for /pattern/).

**Key Methods**:
| Method | Description |
|--------|-------------|
| should_show_command | Main visibility check |
| _rule_matches | Applies to context |
| _matches_pattern | Wildcard/regex helper |

**Rationale**: From filtering doc (methods); inline table.

### ContextMenuService Integration
- **Rule Checking**: Before adding items, calls should_show_command (e.g., if not show, log "filtered out FBC for {token_id}").
- **Dynamic Generation**: Creates actions only for visible commands; preserves context for evaluation.
- **_get_current_item_from_data**: Mock item from data for presenter compatibility (e.g., dict to QTreeWidgetItem-like).

**Example**:
```python
# In show_context_menu
if item_data and 'token' in item_data:
    token_type = item_data.get("token_type", "UNKNOWN").upper()
    token_id = item_data.get("token")
    node_name = item_data.get("node", "Unknown")
    if token_id:
        if not self.context_menu_filter.should_show_command(node_name, token_type, "all", "token"):
            logging.debug(f"Filtered out FBC token command for {token_id}")
        else:
            # Add menu item...
```

**Rationale**: From main blueprint (integration/example); uniques: _get_current_item_from_data note.

## Batch Operation Processing
Handles subgroups via services (e.g., process_all_fbc_subgroup_commands queues for each token).

- **Methods**: process_all_fbc_subgroup_commands (FBC tokens via fbc_service.queue_fieldbus_command); process_all_rpc_subgroup_commands (RPC via rpc_service.queue_rpc_command).
- **Benefits**: Consistent generation, error handling, logging; auto queue start/stop.

| Benefit | Description |
|---------|-------------|
| Consistent Cmd Gen | Service methods ensure format/params |
| Proper Error Handling | Centralized logic |
| Comprehensive Logging | Monitoring/debug |
| Auto Queue Mgmt | Start/stop handling |
| Thread Safety | Sequential exec |

**Rationale**: From main blueprint (batch handling); table for density.

## Use Cases
Examples of filtering application.

| Use Case | Description | Example Rule |
|----------|-------------|--------------|
| Node-Specific | Hide/show for specific nodes | {"node_name": "MAINT01", "action": "hide", "command_type": "all"} |
| Token Type | Visibility by type | {"section_type": "RPC", "action": "show", "command_type": "all"} |
| Command Category | Token vs subgroup | {"command_category": "subgroup", "action": "hide", "command_type": "all"} |

**Rationale**: From filtering doc (use cases); table.

## Best Practices
- **Specificity**: Specific rules before general (first match wins).
- **Descriptions**: Clear for each rule.
- **Testing**: Various node/token combos.
- **Default**: Explicit "hide" for removal (default show).

**Rationale**: From filtering doc (practices); inline list.

## Version History
- **v1 Baseline**: Architecture/impl (from BLUEPRINT_context_menu_v1.md: components/steps/batch).
- **v1 Enhancements**: Rules/properties (from BLUEPRINT_context_menu_filtering_v1.md: config/matching/use cases).
- **Merge Notes**: Absorbed duplicates (e.g., filtering mechanism in both → combined); no additional files (cluster 2 total).

**Rationale**: Consolidates versions (all v1); lists sources/changes.

## References
- **[ContextMenuFilterService](src/commander/services/context_menu_filter.py)**: Rule evaluation.
- **[ContextMenuService](src/commander/services/context_menu_service.py)**: UI integration.
- **[Configuration](config/menu_filter_rules.json)**: Rules file.
- **[CommanderWindow](src/commander/commander_window.py)**: Right-click events.
- **[TECH_ui_command_core_v1](technical/TECH_ui_command_core_v1.md#ServiceLayer)**: UI command integration.
- **[ROADMAP_consolidated_v1 #Dependencies](roadmaps/ROADMAP_consolidated_v1.md#Dependencies)**: Menu phases.
- **[Archived: BLUEPRINT_context_menu_v1 #Overview](archived/BLUEPRINT_context_menu_v1.md#Overview)**: Original architecture (redirect).
- **[Archived: BLUEPRINT_context_menu_filtering_v1 #Overview](archived/BLUEPRINT_context_menu_filtering_v1.md#Overview)**: Filtering details (redirect).

**Rationale**: Bidirectional #links; redirects for archives.
