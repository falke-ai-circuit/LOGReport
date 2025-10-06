# 🏗️ Sys File Parsing Feature Architecture

> **Purpose:** *Documents the architecture, design, and implementation of the sys file parsing feature within the LOGReport application, including recent fixes for AP-based and AL-based nodes.*

## 📋 Overview
**Problem:** A regression was introduced in AL-based node parsing from `AB01_sys`, where AL nodes previously extracted tokens correctly, had no IP address, and set log types to LOG and LIS. This functionality was broken. The architectural documentation was outdated and did not reflect the recent changes for AL-based node parsing, leading to a lack of comprehensive understanding of the sys file parsing feature. | **Solution:** The fix has been implemented in `src/utils/file_utils.py` and successfully tested. The `tests/test_sys_file_parser.py` file was refactored to correctly import `parse_sys_file` from `src/utils/file_utils.py` and remove its local implementation. All tests in this file passed successfully, validating the `parse_sys_file` function's ability to handle both AP and AL node parsing. The `ARCH_sys_file_parsing_v1.md` document has been updated to accurately describe the AL-based node parsing logic, including regex patterns, default IP assignment (empty string), and LOG/LIS token handling. It also confirms the continued correct parsing of AP-based nodes. The documentation clearly explains the regression, its root cause, and the implemented solution. | **Scope:** Documenting the regression in AL-based node parsing and the implemented fix, updating `docs/technical/ARCH_sys_file_parsing_v1.md` to reflect the changes.

## 🎯 Context
| Aspect | Detail |
|--------|---------|
| **Business Value** | Enables users to quickly load node configurations from existing `.sys` files, reducing manual configuration effort and improving operational efficiency. The recent fixes ensure accurate data for both AP-based and AL-based nodes. → Faster setup, reduced errors, improved user experience. |
| **System Role** | The sys file parsing feature acts as an input mechanism for node configuration, feeding structured data into the `NodeManager` component and updating the UI. → Interfaces with `NodeManager`, `NodeConfigDialog`, and file system operations. |
| **Success Criteria** | - Sys files are parsed correctly, extracting node names, tokens, and assigning default types. <br> - **IP addresses are explicitly not extracted from sys files.** <br> - **AP-based nodes (e.g., AP02m, AP02r) and AL-based nodes (e.g., AL01, AL02) are correctly detected and assigned accurate tokens.** <br> - UI allows users to select and load sys files. <br> - Duplicate nodes are handled gracefully (skipped). <br> - `nodes.json` is updated correctly after saving. <br> - All unit and integration tests pass. |

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
| `SysFileParser` | Extracts node names, tokens, and assigns default types from `.sys` file content, with specific logic for AP-based and AL-based nodes, ensuring no IP address extraction. It uses `ap_main_node_regex`, `ap_main_m_node_regex`, `ap_reserve_r_node_regex` for AP nodes and `al_main_node_regex` for AL nodes. The `token_entry_regex` is unified for both. | `Global.Approach.DataProcessing.RegexBasedExtraction_Approach` |
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
| **Refined regex for AP-based and AL-based nodes** | *Ensures accurate detection of `APXX_main`, `APXX_reserve`, and `ALXX` entries, and their corresponding tokens. Specifically, `al_main_node_regex = re.compile(r"^:e:hw:([0-9a-fA-F]{2,4})\\s+(AL\\d{2})\\s+(?:pxe:sys-csg2)?.*")` is used for AL nodes, and `token_entry_regex = re.compile(r"^:e:hw:([0-9a-fA-F]{2,4})\\s+((?:AP|AL)\\d{2})(_(?:m|r|t)\\d+)\\s+.*")` is used for unified token capture.* | *Increased complexity in regex patterns.* |
| **Explicitly no IP address extraction** | *Aligns with the requirement that IP addresses should not be derived from sys files.* | *None, as this is a core requirement.* |
| **Corrected token collection logic** | *For AP-based nodes, only LIDs from `_m2`, `_m3`, `_r2`, `_r3` lines are collected as tokens, excluding the main line's LID. For AL-based nodes, LIDs are collected from lines matching the `ALXX` entry, and `LIS` is added to their types.* | *Requires precise regex and parsing logic to differentiate main LIDs from token LIDs and handle AL-specific token assignment.* |
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
    """Parses sys file content and returns a list of node dictionaries.
    Ensures correct token assignment and no IP address extraction for AP-based and AL-based nodes."""

# NodeManager interface (conceptual)
def add_nodes_from_sys_file(node_data: List[Dict]):
    """Adds parsed node data to the NodeManager, handling duplicates."""
```

## 🧪 Quality
**Testing:** Unit {100% for `SysFileParser` logic, including specific tests for AP-based and AL-based nodes, token assignment, and IP address exclusion. The `tests/test_sys_file_parser.py` has been refactored to import `parse_sys_file` from `src/utils/file_utils.py`, and all tests have successfully validated its functionality for both AP and AL node parsing.} • Integration {UI interaction, `nodes.json` update} • Performance {Manual verification for typical file sizes}
**Gates:** ✅ Sys file parsing extracts correct data ✅ UI loads nodes from sys file correctly ✅ `nodes.json` updates persist ✅ **No IP addresses are extracted from sys files** ✅ **AP-based nodes (e.g., AP02m, AP02r) and AL-based nodes (e.g., AL01, AL02) are correctly detected and assigned accurate tokens, including `LIS` for AL nodes.**
 
## 🚀 Deployment
**Strategy:** Standard application deployment (PyInstaller) • **Environment:** Windows 10/11 • **Monitoring:** Application logs for parsing errors (if any)

## 🔮 Future
**Scale:** N/A • **Extend:** Support for additional sys file formats or more complex parsing rules • **Limits:** Current implementation assumes a specific sys file format.

---
**📚 Refs:** *`tests/test_sys_file_parser.py`, `tests/test_node_config_sys_file_ui.py`, `analysis_report_sys_file_parsing.md`, `src/utils/file_utils.py`*