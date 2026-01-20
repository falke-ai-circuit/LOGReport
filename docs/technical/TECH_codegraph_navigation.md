# Codegraph Navigation Guide

## Overview
Our optimized codegraph (32KB) is designed as a **navigational index**, not a detailed reference. Think of it as a **table of contents** that helps you quickly locate code, then you read the actual source files for details.

## Navigation Workflow

### Step 1: Understand High-Level Structure (Domain → Cluster → Module)

**Query codegraph for domains:**
```python
# Domains available:
- Core (GUI, report generation, log processing)
- Commander (command execution, telnet, UI)
- Runtime_hooks (application initialization)
- Utilities (shared utilities)
```

### Step 2: Drill Down to Specific Area

**Example: "I need to understand context menu functionality"**

**Codegraph Query:**
```
Domain: Commander
  ↓
Cluster: Services
  ↓
Module: commander_services_context_menu_service
  ↓
Class: ContextMenuService
  ↓
File Path: src/commander/services/context_menu_service.py
```

**Action:** Read the actual file for implementation details
```python
# Now read the source file:
read_file("src/commander/services/context_menu_service.py")
```

### Step 3: Read Documentation (If Available)

**Codegraph shows implicit connections:**
- `Code.Domain.Commander` → Check `docs/architecture/ARCH_command_system.md`
- `Code.Cluster.Commander.Services` → Check `docs/technical/TECH_commander_window.md`
- `Code.Class.*.ContextMenuService` → Check `docs/blueprints/BLUEPRINT_context_menu.md`

## Practical Use Cases

### Use Case 1: Feature Location
**Question:** "Where is the node tree UI implemented?"

**Navigation:**
1. Load codegraph → Find `Domain: Commander`
2. Find `Cluster: UI` 
3. Find `Module: commander_ui_node_tree_view`
4. Find `Class: NodeTreeView`
5. **Read source:** `src/commander/ui/node_tree_view.py`

### Use Case 2: Impact Detection
**Question:** "What modules will be affected if I change LogProcessor?"

**Navigation:**
1. Find `Code.Class.processor.LogProcessor`
2. Find parent: `Code.Module.processor.File`
3. Query relations: "What IMPORTS this module?"
4. Get list of dependent modules
5. **Review each:** Read source files of affected modules

### Use Case 3: Architecture Understanding
**Question:** "How is the Commander system organized?"

**Navigation:**
1. Find `Code.Domain.Commander`
2. List all clusters: `Services`, `UI`, `Presenters`, `Utils`, `Commands`
3. See module distribution across clusters
4. **Read docs:** `docs/architecture/ARCH_command_system.md` for design rationale

### Use Case 4: Debugging Data Flow
**Question:** "How does telnet command execution flow?"

**Navigation:**
1. Entry point: `Code.Module.commander_telnet_client`
2. Follow BELONGS_TO: `Commander.Telnet_client` cluster
3. Find related: `Code.Class.TelnetService`
4. **Read source files in order:**
   - `src/commander/telnet_client.py`
   - `src/commander/services/telnet_service.py`
   - `src/commander/command_queue.py`

## Key Classes Mapped (Entry Points)

Our codegraph includes only **9 key architectural classes**:

1. **LogReportGUI** - Main GUI application (Root)
2. **CommanderWindow** - Commander window (Commander)
3. **CommanderPresenter** - Commander business logic
4. **NodeTreePresenter** - Node tree management
5. **NodeTreeView** - Node tree UI
6. **ContextMenuService** - Context menu handling
7. **TelnetService** - Telnet communication
8. **LogProcessor** - Log file processing (Core)
9. **NodeManager** - Node configuration management

**These are your entry points** - locate them in codegraph, then read their source files.

## What Codegraph DOES Provide

✅ **Module location** - All 69 modules mapped  
✅ **Domain organization** - 4 domains, ~35 clusters  
✅ **Key class identification** - 9 architectural classes  
✅ **Hierarchy structure** - Type→Domain→Cluster→Module→Class  
✅ **Basic relations** - BELONGS_TO (structure), INHERITS (class hierarchy)  
✅ **File path mapping** - Module name → source file path  

## What Codegraph DOES NOT Provide

❌ **Method-level details** - (Removed for size optimization)  
❌ **Function parameters** - (Read source file)  
❌ **Implementation logic** - (Read source file)  
❌ **Code examples** - (Read source file)  
❌ **Detailed call chains** - (Minimal CALLS relations preserved)  

## Workflow Summary

```
┌─────────────────────────────────────────────────────┐
│  1. LOCATE using codegraph (32KB, instant load)    │
│     - Find domain, cluster, module, class          │
│     - Identify file path                           │
│     - Check impact surface                         │
└─────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────┐
│  2. READ SOURCE for details                        │
│     - Open: src/[module_path].py                   │
│     - Review: methods, parameters, logic           │
│     - Understand: implementation details           │
└─────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────┐
│  3. READ DOCS for architecture (if needed)         │
│     - ARCH_*.md for system design                  │
│     - TECH_*.md for technical details              │
│     - BLUEPRINT_*.md for feature specs             │
└─────────────────────────────────────────────────────┘
```

## Size Optimization Trade-offs

**We traded detail for constant availability:**

- **Before:** 1,064 KB, 750 entities, 5,115 relations (too large to load)
- **After:** 32 KB, 113 entities, 114 relations (loads in every session)

**Result:** Codegraph is now a **fast lookup index**, not a comprehensive database. You can load it instantly in every session without token budget concerns, locate what you need in ≤3 hops, then read the actual source code for implementation details.

## Quick Reference Commands

```python
# Load codegraph
codegraph = load_codegraph()

# Find module by keyword
find_module("context_menu")  # Returns: Code.Module.commander_services_context_menu_service.File

# Get file path
get_file_path(module)  # Returns: src/commander/services/context_menu_service.py

# Find class
find_class("TelnetService")  # Returns: Code.Class.commander_telnet_service.TelnetService

# Get dependencies
get_dependencies(module)  # Returns: List of modules that import this one

# Navigate hierarchy
get_cluster(module)  # Returns: Code.Cluster.Commander.Services
get_domain(cluster)  # Returns: Code.Domain.Commander
```

---

**Bottom Line:** Our codegraph is a **navigational map** (32KB, <30ms load) that helps you quickly find the right source file to read. It's optimized for **constant availability** across all sessions, not exhaustive detail. Load it, locate what you need, then read the source code for full understanding.
