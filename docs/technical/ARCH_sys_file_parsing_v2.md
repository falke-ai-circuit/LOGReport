# 🏗️ Architectural Design: Sys File Parsing v2

> **Purpose:** *To define the architecture for a multi-stage sys file parsing process to support dependent file lookups for IP address extraction.*

## 📋 Overview
**Problem:** The current parsing logic only handles a single sys file. A new requirement mandates parsing a secondary `[tokenid].sys` file for AP nodes to extract an IP address. | **Solution:** Introduce a multi-stage parsing process. The main `parse_sys_file` function will be modified to orchestrate this. A new private helper function, `_parse_ip_from_sys`, will handle the secondary file parsing. The UI layer in `NodeConfigDialog` will provide the necessary base path for file resolution. | **Scope:** This design covers changes to `src/utils/file_utils.py` and `src/node_config_dialog.py`. It includes data flow, function contracts, and error handling for the new parsing logic.

## 🎯 Context
| Aspect | Detail |
|--------|---------|
| **Business Value** | Enables the system to automatically configure IP addresses for AP nodes, reducing manual configuration and potential for errors. |
| **System Role** | The parsing logic is a core utility function consumed by the UI layer (`NodeConfigDialog`) to populate node configuration data. |
| **Success Criteria** | O1: Data flow from UI to parsing functions is clearly documented. O2: Roles and responsibilities of `parse_sys_file`, `_parse_ip_from_sys`, and the calling method in `NodeConfigDialog` are explicitly defined. O3: Error handling for missing secondary files or parsing failures is specified. |

## 🔧 Design

### Core Architecture
```
[NodeConfigDialog] -- (file_path) --> [parse_sys_file(content, base_path)]
       |
       +-- (For AP Nodes) --> [_parse_ip_from_sys(token, base_path)] -- reads --> [tokenid].sys
       |
       <-- (nodes_data with IP) --
```
| Component | Responsibility | Pattern |
|-----------|----------------|---------|
| `NodeConfigDialog.load_sys_file` | Orchestrates file loading. Prompts user for the main sys file, extracts the base path, and calls `parse_sys_file` with file content and the base path. | UI-driven Orchestrator |
| `file_utils.parse_sys_file` | Main parsing orchestrator. Performs initial parsing for nodes and tokens. For AP nodes, iterates through tokens and calls `_parse_ip_from_sys` to find an IP. Updates the node data with the found IP. | Facade, Multi-stage Pipeline |
| `file_utils._parse_ip_from_sys` | New private helper. Constructs the secondary file path `[base_path]/[tokenid].sys`. Reads and parses this file to find the IP address. Returns the IP or an empty string if not found or if an error occurs. | Helper/Utility Function |

### Tech Stack
| Layer | Technology | Rationale |
|-------|------------|-----------|
| {Backend} | Python 3.x | *Existing technology for the application.* |
| {UI} | PyQt | *Existing technology for the application's GUI.* |

## ⚡ Implementation
| Decision | Rationale | Trade-offs |
|----------|-----------|------------|
| Extend `file_utils.py` with a private helper function `_parse_ip_from_sys`. | Keeps related logic cohesive and encapsulates the new IP parsing responsibility, adhering to the Single Responsibility Principle. | Slightly increases the complexity of `parse_sys_file`, which now orchestrates a sub-process. The alternative (handling this in the UI layer) would violate the separation of concerns. |
| The `parse_sys_file` function signature is changed to accept a `base_path`. | This is required to allow the utility function to resolve the path to dependent sys files without having direct file system awareness of the user's selection. | The calling code in `NodeConfigDialog` must be updated to provide this new argument. |

**Performance:** Negligible impact. The secondary file parsing is a fast I/O operation.  
**Security:** No change in security posture. File access is limited to user-selected paths.

## 🔗 Integration
**Dependencies:** `src/node_config_dialog.py` → `src/utils/file_utils.py`  
**APIs:** 
```python
# src/utils/file_utils.py
def parse_sys_file(file_content: str, base_path: str) -> list[dict]:
    # ... existing parsing logic ...
    # ... new logic to call _parse_ip_from_sys for AP nodes ...

def _parse_ip_from_sys(token: str, base_path: str) -> str:
    # ... logic to find, read, and parse [tokenid].sys ...
```

## 🧪 Quality
**Testing:** Existing unit tests in `tests/test_node_config_parser.py` will be extended to cover the new IP extraction logic. Test cases will include: successful IP extraction, handling of missing secondary files (should not raise an error), and handling of secondary files that do not contain an IP.  
**Gates:** ✅ All existing tests must pass. ✅ New tests for IP extraction must pass.

## 🚀 Deployment
**Strategy:** Standard update. • **Environment:** No new requirements. • **Monitoring:** N/A.

## 🔮 Future
**Scale:** N/A. • **Extend:** The `base_path` parameter could be used for resolving other types of dependent configuration files in the future. • **Limits:** Assumes a flat directory structure for `[tokenid].sys` files relative to the main sys file.

---
**📚 Refs:** `docs/architecture/ARCH_sys_file_parsing_v1.md`