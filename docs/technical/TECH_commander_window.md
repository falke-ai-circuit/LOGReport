# 🖥️ Commander Window System

<!-- METADATA -->
metadata: {
  created_date: "2025-10-08_171500",
  last_modified: "2025-10-08_171500",
  last_accessed: "2025-10-08_171500",
  word_count: 1847,
  reference_count: 4,
  document_hash: "commander_window_tech",
  obsolete_check_date: "2025-10-08",
  section_count: 6,
  internal_link_count: 14
}
<!-- /METADATA -->

## 📑 Table of Contents

- [Overview](#overview)
- [Window Architecture](#window-architecture)
- [Node Tree Widget](#node-tree-widget)
- [Command Execution](#command-execution)
- [UI Components](#ui-components)
- [Integration Points](#integration-points)

---

## 🎯 Overview

The Commander Window provides the main UI for node management, command execution, and log viewing in the LOGReport application.

### Key Features

| Feature | Description | Benefit |
|---------|-------------|---------|
| **Node Tree View** | Hierarchical node display with color coding | Visual status overview |
| **Context Menu** | Right-click commands for nodes/tokens | Quick access |
| **Batch Operations** | Multi-select command execution | Efficiency |
| **Real-time Updates** | Live status updates via signals | Current information |
| **Log Integration** | Direct log file access | Convenient analysis |

---

## 🏗️ Window Architecture

The Commander Window uses PyQt6 with Model-View-Presenter (MVP) pattern.

**Architecture Components**:
```
CommanderWindow (View)
    ├── NodeTreeWidget (Model/View)
    │   ├── Node Items (QTreeWidgetItem)
    │   ├── Token Items (QTreeWidgetItem)
    │   └── Color Coding (Green/Yellow/Red)
    ├── ContextMenuService (Controller)
    │   ├── Menu Generation
    │   ├── Command Handling
    │   └── Filtering Logic
    └── Signal Handlers
        ├── Command Completion
        ├── Progress Updates
        └── Status Changes
```

See: [Node System](../architecture/ARCH_node_system.md#ui-integration)

---

## 🌲 Node Tree Widget

The Node Tree Widget displays nodes and tokens in a hierarchical structure.

**Tree Structure**:
```
📦 Nodes (Root)
├── 🟢 AP01m (Node - Online, Success)
│   ├── 🔵 162 (FBC Token)
│   ├── 🔵 163 (FBC Token)
│   └── 🔵 67890 (RPC Token)
├── 🟡 AP02m (Node - Online, Minimal Data)
│   ├── 🔵 164 (FBC Token)
│   └── 🔵 165 (FBC Token)
└── 🔴 AP03m (Node - Offline or Error)
    └── 🔵 166 (FBC Token)
```

**Color Coding**:
- 🟢 **Green**: Command success + log success + line_count > 5
- 🟡 **Yellow**: Command success + log success + line_count ≤ 5
- 🔴 **Red**: Command failure or log failure

See: [Node System - Color Determination](../architecture/ARCH_node_system.md#color-determination-logic)

---

## ⚙️ Command Execution

Commands are executed through context menu or batch operations.

**Execution Flow**:
1. User right-clicks node/token
2. Context menu displays available commands
3. User selects command
4. Command queued for execution
5. Sequential processor executes command
6. Results logged and UI updated

**Supported Commands**:
- **FBC Commands**: Print from FBC IO structure
- **RPC Commands**: Print/Clear from FBC RUPI counters
- **BsTool**: Process log files with BsTool.exe
- **LOG Commands**: Open log directory, view logs

See: [Command System](../architecture/ARCH_command_system.md#integration-points)

---

## 🎨 UI Components

Key UI components in the Commander Window.

**Main Components**:

| Component | Type | Purpose |
|-----------|------|---------|
| **Node Tree** | QTreeWidget | Display nodes and tokens |
| **Status Bar** | QStatusBar | Show status messages |
| **Progress Bar** | QProgressBar | Display command progress |
| **Toolbar** | QToolBar | Quick action buttons |
| **Menu Bar** | QMenuBar | Application menu |

**Widget Hierarchy**:
```python
class CommanderWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # Central widget
        self.node_tree = NodeTreeWidget()
        self.setCentralWidget(self.node_tree)
        
        # Status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.status_bar.addPermanentWidget(self.progress_bar)
        
        # Toolbar
        self.toolbar = self.addToolBar("Main")
        self._setup_toolbar()
        
        # Menu bar
        self._setup_menu_bar()
        
        # Connect signals
        self._connect_signals()
```

---

## 🔗 Integration Points

The Commander Window integrates with multiple system components.

**Integration Map**:
- **Node Manager**: Loads nodes and tokens → [Node System](../architecture/ARCH_node_system.md)
- **Command Queue**: Executes commands → [Command System](../architecture/ARCH_command_system.md)
- **Logging Service**: Writes command logs → [Logging System](../architecture/ARCH_logging_system.md)
- **Context Menu Service**: Generates dynamic menus
- **Session Manager**: Manages telnet sessions

**Signal Connections**:
```python
# Command completion
command_queue.command_completed.connect(self.update_node_status)

# Progress updates
processor.progress_updated.connect(self.update_progress_bar)

# Status messages
processor.status_message.connect(self.show_status_message)

# Tree selection
self.node_tree.itemSelectionChanged.connect(self.handle_selection_change)
```

---

## 📚 References

### Related Documentation

- **[Node System](../architecture/ARCH_node_system.md)** - Node management and UI integration
- **[Command System](../architecture/ARCH_command_system.md)** - Command execution
- **[Context Menu System](../blueprints/BLUEPRINT_context_menu.md)** - Context menu details

### Source Code

- **Commander Window**: `src/ui/commander_window.py`
- **Node Tree Widget**: `src/ui/widgets/node_tree_widget.py`
- **Context Menu Service**: `src/commander/services/context_menu_service.py`

---

**Document Status**: ✅ **COMPLETE** - Consolidated from 7 source documents
**Last Updated**: 2025-10-08
**Next Review**: 2026-01-08 (90 days)
