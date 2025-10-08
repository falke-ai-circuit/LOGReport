# 🏗️ Sys File Parsing Feature Architecture

> **Purpose:** *Documents the architecture, design, and implementation of the sys file parsing feature within the LOGReport application, including recent fixes for AP-based and AL-based nodes, and the new requirement for IP address extraction.*

## 📋 Overview
**Problem:** The current parsing approach is rigid due to embedded regex patterns, making it difficult to adapt to new formats or node types. The new requirements for IP extraction and multi-file parsing need to be integrated efficiently. The architectural documentation was outdated and did not reflect the recent changes for AL-based node parsing, leading to a lack of comprehensive understanding of the sys file parsing feature. | **Solution:** A robust design for sys file parsing logic that can identify token IDs, extract IP addresses (specifically 'set XD_IP_ADDR='), differentiate between AP-based (first token only) and AL-based (single token) nodes, and support loading multiple sys files. The design will address the identified tight coupling of regex patterns by proposing externalized configuration. | **Scope:** Documenting the regression in AL-based node parsing and the implemented fix, updating `docs/technical/ARCH_sys_file_parsing_v1.md` to reflect the changes, and incorporating the new requirement for IP address extraction and multi-file loading.

## 🎯 Context
| Aspect | Detail |
|--------|---------|
| **Business Value** | Enables users to quickly load node configurations from existing `.sys` files, reducing manual configuration effort and improving operational efficiency. The recent fixes ensure accurate data for both AP-based and AL-based nodes, and the new IP extraction capability enhances node management. → Faster setup, reduced errors, improved user experience. |
| **System Role** | The sys file parsing feature acts as an input mechanism for node configuration, feeding structured data into the `NodeManager` component and updating the UI. → Interfaces with `NodeManager`, `NodeConfigDialog`, and file system operations. |
| **Success Criteria** | - Sys files are parsed correctly, extracting node names, tokens, and assigning default types. <br> - **IP addresses are extracted from lines matching 'set XD_IP_ADDR='.** <br> - **AP-based nodes (e.g., AP02m, AP02r) and AL-based nodes (e.g., AL01, AL02) are correctly detected and assigned accurate tokens.** <br> - UI allows users to select and load multiple sys files. <br> - Duplicate nodes are handled gracefully (skipped or user-option to overwrite). <br> - `nodes.json` is updated correctly after saving. <br> - All unit and integration tests pass. |

## 🔧 Design

### Core Architecture
```
[Sys File(s)] --(Read)--> [SysFileParser] --(Parsed Data)--> [NodeManager] --(Update)--> [NodeConfigDialog (UI)]
                                 ^                                 |
                                 |                                 v
                                 (Load Sys File(s) Button)       [nodes.json]
```
| Component | Responsibility | Pattern |
|-----------|----------------|---------|
| `SysFileParser` | Extracts node names, tokens, IP addresses (from 'set XD_IP_ADDR='), and assigns default types from `.sys` file content, with specific logic for AP-based and AL-based nodes. It will use externalized regex patterns and node type definitions. | `Global.Approach.DataProcessing.RegexBasedExtraction_Approach`, `Global.DataProcessingPattern.Configuration.NodeConfigurationFromSysFile_Pattern` |
| `NodeManager` | Manages the collection of nodes, including adding new nodes and handling duplicates. | `Global.DataProcessingPattern.Configuration.NodeConfigurationFromSysFile_Pattern` |
| `NodeConfigDialog` | Provides the user interface for loading sys files and displaying node configurations. | `Global.ArchitecturePattern.UI.MVPPresenter_Pattern` |

### Tech Stack
| Layer | Technology | Rationale |
|-------|------------|-----------|
| **Parsing** | Python (re module) | *Native Python regex capabilities for efficient text pattern matching.* |
| **Configuration** | YAML/JSON files | *Externalized configuration for regex patterns and node type definitions, improving flexibility and maintainability.* |
| **UI** | PyQt6 | *Existing framework for the application's GUI, ensuring consistency.* |
| **Data** | JSON files (`nodes.json`) | *Standardized format for node persistence, easy to read and write.* |

## ⚡ Implementation
| Decision | Rationale | Trade-offs |
|----------|-----------|------------|
| **Externalized Configuration for Regex and Node Types** | *Decouples parsing logic from code, allowing easy updates and additions of new sys file formats or node types without code changes.* | *Introduces an additional configuration file to manage.* |
| **Modular Parsing Functions** | *Dedicated functions for file loading, token detection, IP extraction, and node type differentiation will enhance code organization and reusability.* | *Slightly increased initial development effort for modularization.* |
| **IP Address Extraction from 'set XD_IP_ADDR='** | *Addresses the new requirement for IP address extraction, providing more complete node configuration data.* | *Requires careful regex pattern definition to accurately capture IP addresses without false positives.* |
| **Refined regex for AP-based and AL-based nodes** | *Ensures accurate detection of `APXX_main`, `APXX_reserve`, and `ALXX` entries, and their corresponding tokens. Specifically, `al_main_node_regex = re.compile(r"^:e:hw:([0-9a-fA-F]{2,4})\\s+(AL\\d{2})\\s+(?:pxe:sys-csg2)?.*")` is used for AL nodes, and `token_entry_regex = re.compile(r"^:e:hw:([0-9a-fA-F]{2,4})\\s+((?:AP|AL)\\d{2})(_(?:m|r|t)\\d+)\\s+.*")` is used for unified token capture.* | *Increased complexity in regex patterns.* |
| **Corrected token collection logic** | *For AP-based nodes, only LIDs from `_m2`, `_m3`, `_r2`, `_r3` lines are collected as tokens, excluding the main line's LID. For AL-based nodes, LIDs are collected from lines matching the `ALXX` entry, and `LIS` is added to their types.* | *Requires precise regex and parsing logic to differentiate main LIDs from token LIDs and handle AL-specific token assignment.* |
| **Support for Multiple Sys Files** | *Allows users to load multiple sys files simultaneously, improving efficiency for bulk node configuration.* | *Requires robust error handling and duplicate management across multiple files.* |
| **UI integration via `NodeConfigDialog`** | *Leverages existing UI components for a seamless user experience.* | *Tight coupling between UI and parsing initiation, though mediated by presenter.* |
| **Duplicate node handling** | *Prevents data redundancy and ensures data integrity in `nodes.json`. Will include options for users to overwrite or skip duplicates.* | *Requires clear UI feedback and user interaction for conflict resolution.* |

**Performance:** Latency {<100ms for typical sys files, potentially higher for multiple large files} • Throughput {N/A - local file processing} • Scale {N/A - local file processing}  
**Security:** Auth {N/A - local file access} • Data {N/A - no sensitive data extracted beyond IP} • Access {Standard OS file permissions}

## 🔗 Integration
**Dependencies:** `SysFileParser` → `NodeManager` → `NodeConfigDialog`  
**APIs:** ```python
# SysFileParser interface (conceptual)
def parse_sys_files(file_paths: List[str]) -> List[Dict]:
    """Parses content from multiple sys files and returns a list of node dictionaries.
    Ensures correct token assignment, extracts IP addresses from 'set XD_IP_ADDR=', and handles AP-based and AL-based nodes."""

# NodeManager interface (conceptual)
def add_nodes_from_sys_file(node_data: List[Dict], overwrite_duplicates: bool = False):
    """Adds parsed node data to the NodeManager, handling duplicates based on user preference."""
```

## 🧪 Quality
**Testing:** Unit {100% for `SysFileParser` logic, including specific tests for AP-based and AL-based nodes, token assignment, IP address extraction, and multi-file parsing. The `tests/test_sys_file_parser.py` will be updated to reflect these changes.} • Integration {UI interaction, `nodes.json` update, multi-file loading scenarios} • Performance {Manual verification for typical file sizes and multiple file loads}
**Gates:** ✅ Sys file parsing extracts correct data ✅ IP addresses are extracted from 'set XD_IP_ADDR=' ✅ UI loads nodes from sys file correctly ✅ `nodes.json` updates persist ✅ AP-based and AL-based nodes are correctly detected and assigned accurate tokens, including `LIS` for AL nodes. ✅ Multiple sys files can be loaded and processed.
 
## 🚀 Deployment
**Strategy:** Standard application deployment (PyInstaller) • **Environment:** Windows 10/11 • **Monitoring:** Application logs for parsing errors (if any)

## 🔮 Future
**Scale:** N/A • **Extend:** Support for additional sys file formats or more complex parsing rules, dynamic regex updates from a central server. • **Limits:** Current implementation assumes a specific sys file format.

---
**📚 Refs:** *`tests/test_sys_file_parser.py`, `tests/test_node_config_sys_file_ui.py`, `logs/analysis_report_sys_file_parsing.md`, `src/utils/file_utils.py`, `config/sys_parsing_rules.json` (new)*