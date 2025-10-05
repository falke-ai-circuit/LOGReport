# 🏗️ Sys File Parsing Feature Architecture

> **Purpose:** *Documents the architecture, design, and implementation of the sys file parsing feature within the LOGReport application.*

## 📋 Overview
**Problem:** The LOGReport application needs to parse `.sys` files to extract node configuration data (names, tokens, types) and integrate it into the existing node management system. | **Solution:** Implement a dedicated sys file parsing logic, integrate it into the UI for user-initiated loading, and ensure comprehensive testing for reliability. | **Scope:** Parsing logic, UI integration, and testing of sys file parsing.

## 🎯 Context
| Aspect | Detail |
|--------|---------|
| **Business Value** | Enables users to quickly load node configurations from existing `.sys` files, reducing manual configuration effort and improving operational efficiency. → Faster setup, reduced errors, improved user experience. |
| **System Role** | The sys file parsing feature acts as an input mechanism for node configuration, feeding structured data into the `NodeManager` component and updating the UI. → Interfaces with `NodeManager`, `NodeConfigDialog`, and file system operations. |
| **Success Criteria** | - Sys files are parsed correctly, extracting node names, tokens, and assigning default types. <br> - IP addresses are explicitly not extracted. <br> - UI allows users to select and load sys files. <br> - Duplicate nodes are handled gracefully (skipped). <br> - `nodes.json` is updated correctly after saving. <br> - All unit and integration tests pass. |

## 🔧 Design

### Core Architecture
```
[Sys File] --(Read)--> [SysFileParser] --(Parsed Data)--> [NodeManager] --(Update)--> [NodeConfigDialog (UI)]
                               ^                                 |
                               |                                 v
                               (Load Sys File Button)          [nodes.json]
```
| Component | Responsibility | Pattern |
|-----------|----------------|---------|
| `SysFileParser` | Extracts node names, tokens, and assigns default types from `.sys` file content. | `Global.Approach.DataProcessing.RegexBasedExtraction_Approach` |
| `NodeManager` | Manages the collection of nodes, including adding new nodes and handling duplicates. | `Global.DataProcessingPattern.Configuration.NodeConfigurationFromSysFile_Pattern` |
| `NodeConfigDialog` | Provides the user interface for loading sys files and displaying node configurations. | `Global.ArchitecturePattern.UI.MVPPresenter_Pattern` |

### Tech Stack
| Layer | Technology | Rationale |
|-------|------------|-----------|
| **Parsing** | Python (re module) | *Native Python regex capabilities for efficient text pattern matching.* |
| **UI** | PyQt6 | *Existing framework for the application's GUI, ensuring consistency.* |
| **Data** | JSON files (`nodes.json`) | *Standardized format for node persistence, easy to read and write.* |

## ⚡ Implementation
| Decision | Rationale | Trade-offs |
|----------|-----------|------------|
| **Regex-based parsing** | *Provides flexibility and precision for extracting specific patterns from unstructured text.* | *Requires careful maintenance of regex patterns if sys file format changes significantly.* |
| **UI integration via `NodeConfigDialog`** | *Leverages existing UI components for a seamless user experience.* | *Tight coupling between UI and parsing initiation, though mediated by presenter.* |
| **Duplicate node skipping** | *Prevents data redundancy and ensures data integrity in `nodes.json`.* | *Users might expect an explicit warning or option to overwrite duplicates (future enhancement).* |

**Performance:** Latency {<100ms for typical sys files} • Throughput {N/A - single file operation} • Scale {N/A - local file processing}  
**Security:** Auth {N/A - local file access} • Data {N/A - no sensitive data extracted} • Access {Standard OS file permissions}

## 🔗 Integration
**Dependencies:** `SysFileParser` → `NodeManager` → `NodeConfigDialog`  
**APIs:** 
```python
# SysFileParser interface (conceptual)
def parse_sys_file(file_content: str) -> List[Dict]:
    """Parses sys file content and returns a list of node dictionaries."""

# NodeManager interface (conceptual)
def add_nodes_from_sys_file(node_data: List[Dict]):
    """Adds parsed node data to the NodeManager, handling duplicates."""
```

## 🧪 Quality
**Testing:** Unit {100% for `SysFileParser` logic} • Integration {UI interaction, `nodes.json` update} • Performance {Manual verification for typical file sizes}  
**Gates:** ✅ Sys file parsing extracts correct data ✅ UI loads nodes from sys file correctly ✅ `nodes.json` updates persist

## 🚀 Deployment
**Strategy:** Standard application deployment (PyInstaller) • **Environment:** Windows 10/11 • **Monitoring:** Application logs for parsing errors (if any)

## 🔮 Future
**Scale:** N/A • **Extend:** Support for additional sys file formats or more complex parsing rules • **Limits:** Current implementation assumes a specific sys file format.

---
**📚 Refs:** *`tests/test_sys_file_parser.py`, `tests/test_node_config_sys_file_ui.py`*