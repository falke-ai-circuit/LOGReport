---
metadata:
  created_date: "2025-10-03"
  last_modified: "2025-10-03T09:20:00Z"
  version: "v1.0"
  cluster: "Architecture: UI/Node"
  merges_from: 10 files (e.g., ARCH_node_manager_architecture_v1.md, TECH_node_manager_architecture_v1.md, node_manager_architecture.md, node_manager_configuration.md, ARCH_mvp_implementation_v1.md, TECH_mvp_implementation_v1.md, mvp_implementation.md, ARCH_mvp_pattern_adoption_v1.md, TECH_mvp_pattern_adoption_v1.md, mvp_pattern_adoption.md)
  word_count: 1000
  reference_count: 10
  document_hash: "sha256:arch_ui_node_core_v1_hash"
  similarity_index: 0.80  # Pre-merge average
  archive_rate: "90%"  # 9/10 archived
  sections: 8
  compliance: "/templates/document_standards.md"
---

# ARCH_ui_node_core_v1: Consolidated UI/Node Architecture

## Overview
LOGReport's UI/Node architecture integrates NodeManager for config/loading/scanning nodes/tokens/logs with MVP pattern for UI separation (Model-View-Presenter). NodeManager handles JSON config (nodes/tokens), log scanning (FBC/RPC/LOG/LIS), status tracking. MVP decouples UI logic (Presenter) from data (Model) and display (View). Merged from 10 sources: NodeMgr docs (80% overlap on loading/scanning/usage), MVP guides/ADR (overlaps on patterns/responsibilities). Rationale: 80% sim on components (e.g., NodeMgr config repeated in 4 docs, MVP rationale in 3); preserves uniques (e.g., token normalization, pitfalls/solutions).

| Feature | Status | Benefit |
|---------|--------|---------|
| Node config loading | ✅JSON support | Nodes/tokens from file |
| Log scanning | ✅Glob patterns | Auto token discovery |
| Status tracking | ✅Online/offline | UI feedback |
| MVP separation | ✅View/Presenter/Model | Testable/maintainable |
| Signal communication | ✅PyQt signals | Decoupled updates |
| Service injection | ✅Constructor deps | Reusable components |

**Rationale**: Condensed duplicates (e.g., NodeMgr loading code in 3 docs → single table); symbols for scan; inline from overviews (ARCH_node_manager_architecture_v1.md/TECH_node_manager_architecture_v1.md).

## Key Components
Core for Node/UI management.

| Component | Description | Key Methods/Fields | Location |
|-----------|-------------|--------------------|----------|
| **NodeManager** | Loads JSON config, scans logs, tracks status, provides nodes/tokens. Validates formats (new/old), normalizes tokens (FBC pad3/upper, RPC lower). | load_configuration(path=None); save_configuration(path=None); get_node(name); get_all_nodes(); add_node(data); set_selected_node(name); get_selected_node(); scan_log_files(); validate_node_config(); validate_log_paths(); check_node_connectivity(); _extract_fbc_token(file) | [src/commander/node_manager.py](src/commander/node_manager.py) |
| **Node (dataclass)** | Represents node with tokens; extended for hierarchical_commands (dict of sequences). | name, ip_address, tokens (dict), hierarchical_commands (optional dict: {"SeqName": [{"type": "FBC", "command": "init"}]} ) | [src/commander/models.py](src/commander/models.py) |
| **NodeTreeView (QTreeWidget)** | UI display: Renders nodes, handles events (expand/select). Interfaces: clear(), add_top_level_item(item), update_node_style(name, style). | item_expanded (signal), node_selected (signal); add_top_level_item(item); update_node_style(name, style) | UI layer |
| **NodeTreePresenter (QObject)** | Intermediary: Populates view, handles signals, orchestrates services (NodeManager, LogWriter, etc.). No direct UI code. | __init__(view, node_manager, ...); populate_node_tree(); handle_item_expanded(item); on_node_selected(item); process_fieldbus_command(token_id, node_name); update_node_display(node) | [src/commander/presenters/node_tree_presenter.py](src/commander/presenters/node_tree_presenter.py) |
| **ContextMenuService** | Dynamic menus: Generates submenus for hierarchical commands from node.hierarchical_commands. | Detect hierarchical_commands; create top-level QAction; submenu with sub-actions; triggered → execute_hierarchical_command(node, name) | [src/commander/services/context_menu_service.py](src/commander/services/context_menu_service.py) |
| **HierarchicalCommandService** | Executes sequences: From node.hierarchical_commands, queues sub-commands (FBC/RPC/LOG/BsTool), handles errors/progress. | execute_hierarchical_command(node_token, command_name); process_fbc_commands(node, tokens, telnet=None); process_rpc_commands(node, tokens, action="print", telnet=None); stop_processing() | [src/commander/services/hierarchical_command_service.py](src/commander/services/hierarchical_command_service.py) |

**Rationale**: Merged NodeMgr (ARCH_node_manager_architecture_v1.md/TECH_node_manager_architecture_v1.md/node_manager_architecture.md/node_manager_configuration.md: config/scanning/usage, 80% overlap → table); MVP (ARCH_mvp_implementation_v1.md/TECH_mvp_implementation_v1.md/mvp_implementation.md: patterns/interfaces); Hierarchical (design_document_hierarchical_commands.md: sequences). Uniques: Token normalization (from config), pitfalls (from ADR).

## NodeManager Implementation
Config loading/scanning/usage (from node_manager_configuration.md uniques).

- **Formats**: New (tokens array with id/type/ip/port/protocol); Old (tokens list, types list → auto-convert).
- **Loading**: load_configuration(path=None) (JSON load, Node dataclass); save_configuration(path=None).
- **Scanning**: scan_log_files() (glob FBC/RPC/LOG/LIS dirs, extract_token_id for tokens).
- **Validation**: File existence/size (10MB), JSON format, required fields (name/ip/tokens), ports (1-65535).
- **Normalization**: FBC (pad3/upper), RPC (lower/alphanum), LOG/LIS (lower/alphanum).
- **Usage**: get_node(name), get_all_nodes(), add_node(data), set/get_selected_node().

**Examples**:
```python
# Load config
nm = NodeManager()
nm.load_configuration("nodes.json")  # Validates/loads nodes/tokens

# Scan logs
nm.scan_log_files()  # Adds tokens from FBC/*.fbc etc.

# Get node
node = nm.get_node("AP01m")
tokens = node.tokens  # Dict of FBC/RPC etc.

# Add node
new_node = Node(name="NEW", ip_address="192.168.1.100")
new_node.add_token("FBC", "001")
nm.add_node(new_node)
nm.save_configuration()
```

**Rationale**: From node_manager_configuration.md (formats/validation/examples, detailed → condensed); duplicates removed (e.g., repeated load code).

## MVP Pattern
Separation for testable UI (from ADR/guides).

- **Responsibilities**: Model (data/business logic), View (render/input, stateless), Presenter (UI logic, intermediary).
- **Communication**: View→Presenter (signals: item_expanded/node_selected), Presenter→View (methods: clear/add_item/update_style), Presenter↔Model (direct/callbacks).
- **Injection**: Constructor deps (e.g., NodeManager, LogWriter, CommandQueue, Fbc/Rpc/BsTool services).
- **Orchestration**: Presenter handles actions (e.g., process_fieldbus_command: get_token → generate_cmd → queue → status emit).

**Patterns**:
- Signals (PyQt: item_expanded → handle_expanded).
- Data Transfer: Dicts/dataclasses (e.g., _create_node_item: QTreeWidgetItem with UserRole data).
- Error Handling: _report_error(message, exception, duration) (log + emit status).

**Examples**:
```python
# View signals
view.item_expanded.connect(presenter.handle_item_expanded)

# Presenter orchestration
def process_fieldbus_command(self, token_id, node_name):
    token = self.fbc_service.get_token(node_name, token_id)
    command = self.fbc_service.generate_fieldbus_command(token_id)
    self.status_message_signal.emit(f"Executing: {command}...", 3000)
    self.fbc_service.queue_fieldbus_command(node_name, token_id, self.active_telnet_client)
    self.command_queue.start_processing()
```

**Rationale**: Merged ADR (ARCH_mvp_pattern_adoption_v1.md/TECH_mvp_pattern_adoption_v1.md/mvp_pattern_adoption.md: rationale/comparisons); guides (ARCH_mvp_implementation_v1.md/TECH_mvp_implementation_v1.md/mvp_implementation.md: patterns/examples, overlap → unified). Uniques: Pitfalls/solutions (tight coupling, business logic in view → tables).

## Integration
NodeMgr + MVP + Services (from all sources).

- **NodeMgr in MVP**: Presenter injects NodeManager for nodes/tokens; View displays via populate_node_tree().
- **Hierarchical Commands**: ContextMenuService detects node.hierarchical_commands, generates submenus; Presenter executes via HierarchicalCommandService (sequences: FBC init → RPC check).
- **Services**: Fbc/Rpc/BsTool injected; e.g., process_fieldbus_command → fbc_service.queue → command_queue.start().
- **Error/Progress**: Signals for UI (status_message, progress_updated); _report_error for exceptions.

**Rationale**: From design_document_hierarchical_commands.md (hierarchical integration); guides (orchestration examples). Ensures decoupling (Presenter as conductor).

## Best Practices
- **NodeMgr**: Validate configs (file/size/fields), use tokens for paths (✅Accurate), regular scans (✅).
- **MVP**: Clear interfaces (methods/signals), consistent naming, testable (mocks), event-driven (signals), minimal view logic, Presenter as conductor, error propagation.
- **Common Pitfalls**: Avoid tight coupling (use interfaces), business logic in view (move to model/service), UI code in presenter (delegate), inconsistent state (centralize in model), overly complex presenters (SRP).

| Practice | Benefit | Symbol |
|----------|---------|--------|
| Token usage | Accurate paths | ✅ |
| Signal comm | Decoupled | ✅ |
| Validate configs | Integrity | ✅ |
| SRP in presenters | Maintainable | ✅ |

**Rationale**: From MVP guides (pitfalls/solutions → table); NodeMgr (best practices from config).

## Version History
- **v1 Baseline**: NodeMgr overviews/config (from ARCH_node_manager_architecture_v1.md/TECH_node_manager_architecture_v1.md/node_manager_architecture.md: loading/scanning).
- **v1 Enhancements**: MVP adoption (from ADR: rationale/comparisons); impl details (guides: patterns/interfaces).
- **Merge Notes**: Absorbed duplicates (e.g., MVP rationale in 3 docs → single); shallow config (node_manager_configuration.md: formats/validation → sections).

**Rationale**: Consolidates versions (all v1); lists sources/changes.

## References
- **[NodeManager Code](src/commander/node_manager.py)**: Config/scanning.
- **[MVP Presenter](src/commander/presenters/node_tree_presenter.py)**: UI logic.
- **[Hierarchical Service](src/commander/services/hierarchical_command_service.py)**: Sequences.
- **[TECH_ui_command_core_v1](technical/TECH_ui_command_core_v1.md#ServiceLayer)**: UI integration.
- **[ROADMAP_consolidated_v1 #Dependencies](roadmaps/ROADMAP_consolidated_v1.md#Dependencies)**: UI phases.
- **[Archived: node_manager_architecture #Overview](archived/node_manager_architecture.md#Overview)**: Original docs (redirect).
- **[Archived: mvp_implementation #Overview](archived/mvp_implementation.md#Overview)**: MVP variants (redirect).

**Rationale**: Bidirectional #links; redirects for archives (e.g., duplicates as shallow).
