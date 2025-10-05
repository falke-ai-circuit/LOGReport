# Sys File Parsing Analysis Report: AL-based Node Detection Issue

## Objective
Analyze the current sys file parsing logic to identify why AL-based nodes are not being detected or written, focusing on regex patterns and node creation logic.

## Current State
- **`AB01_sys`**: Contains AL nodes (e.g., AL01, AL02, AL03, AL08) with LIDs but no IP addresses.
- **`nodes.json`**: Has an AL01 entry with a default IP ("192.168.0.52") and specific tokens including "default_lis_token" (LIS type).
- **`src/utils/file_utils.py`**:
    - All regex patterns (`ap_main_node_regex`, `ap_main_m_node_regex`, `ap_reserve_r_node_regex`, `token_entry_regex`) are explicitly designed to match "AP" nodes.
    - Node initialization logic hardcodes token types to `["FBC", "RPC", "LOG"]`, which is suitable for AP nodes but incomplete for AL nodes (missing "LIS").
    - IP address handling correctly avoids extracting IPs from the sys file.
- **`docs/technical/ARCH_sys_file_parsing_v1.md`**: Details AP-specific regex refinements and confirms the explicit exclusion of IP address extraction from sys files.
- **`tests/test_sys_file_parser.py`**: The existing test suite is entirely focused on AP-based nodes, with no test cases for AL nodes, indicating a clear gap in test coverage.

## Problem Identification (Hidden Patterns & Root Causes)
The core issue is that the current parsing logic is **AP-node-centric**.
1.  **Regex Patterns**: The regex patterns in `src/utils/file_utils.py` are not designed to capture the specific format of AL-based node entries in `AB01_sys`. They explicitly look for the "AP" prefix, causing AL nodes to be entirely missed during the first pass of node identification.
2.  **Node Creation Logic**: The node creation logic in `src/utils/file_utils.py` does not correctly assign default IP addresses or generate appropriate token types (e.g., LIS) for AL nodes. While IP addresses are correctly not extracted, the default token types are hardcoded for AP nodes, and there's no specific handling for AL nodes to include "LIS" tokens. Additionally, the token assignment logic in the second pass is also AP-centric and does not correctly associate LIDs with AL nodes, especially those without `_m` or `_r` suffixes.

## Optimization Opportunities & Proposed Changes

### 1. Regex Pattern Modifications (`src/utils/file_utils.py`)
-   **New Regex for AL Main Nodes**:
    -   Introduce `al_main_node_regex = re.compile(r"^:e:hw:([0-9a-fA-F]{2,4})\s+(AL\d{2})\s+.*")`
    -   This pattern will capture AL nodes like `AL01`, `AL02`, `AL03`, `AL04`, `AL05`, `AL06`, `AL07`, `AL08` and their corresponding LIDs, regardless of whether they have `pxe:sys-csg2` or just `-` in the parameter field.
-   **Unified Token Entry Regex**:
    -   Modify `token_entry_regex` to `token_entry_regex = re.compile(r"^:e:hw:([0-9a-fA-F]{2,4})\s+((?:AP|AL)\d{2})((?:_m\d|_r\d)?)\s+.*")`
    -   This unified regex will correctly capture tokens for both AP and AL nodes. The `(?:AP|AL)` non-capturing group allows matching either prefix, and `((?:_m\d|_r\d)?)` makes the suffix optional, accommodating AL nodes that have tokens directly associated with their main entry (e.g., `AL01`).

### 2. Node Creation Logic Modifications (`src/utils/file_utils.py`)
-   **Node Initialization (First Pass)**:
    -   Add an `elif` block to handle `al_main_node_regex` matches.
    -   For AL nodes, initialize `ip` as an empty string (as per requirement) and `types` as `["FBC", "RPC", "LOG", "LIS"]`.
    -   *Refer to the previous thought for the exact code snippet for this modification.*
-   **Token Assignment (Second Pass)**:
    -   Update the token assignment logic to correctly identify the parent node for AL tokens. Since AL nodes often don't have `_m` or `_r` suffixes for their tokens, the logic needs to check for the base AL node name.
    -   *Refer to the previous thought for the exact code snippet for this modification.*

## Expected Outcomes
-   AL-based nodes from `AB01_sys` (e.g., AL01, AL02, AL03, AL08) will be correctly detected and added to the `nodes_data`.
-   These AL nodes will be assigned an empty string for `ip_address` (not extracted from sys file).
-   The `tokens` list for AL nodes will correctly include LIDs found in the sys file.
-   The `types` list for AL nodes will correctly include `["FBC", "RPC", "LOG", "LIS"]`.
-   The `nodes.json` file, after parsing and saving, will accurately reflect the detected AL nodes with their assigned default IP and appropriate tokens.
-   Existing AP node parsing functionality should remain unaffected.

## Evidence Chains
-   **AB01_sys**: Provides concrete examples of AL node patterns (e.g., `:e:hw:21 AL01 pxe:sys-csg2 // AL01 LIS`).
-   **nodes.json**: Shows the desired structure for AL01, including `ip_address: "192.168.0.52"` (default) and `tokens` with `default_lis_token` (LIS type).
-   **docs/technical/ARCH_sys_file_parsing_v1.md**: Confirms the design principle of not extracting IP addresses from sys files and the AP-centric nature of previous fixes.
-   **src/utils/file_utils.py**: Direct code analysis reveals the current regex and node creation logic's limitations regarding AL nodes.
-   **tests/test_sys_file_parser.py**: Confirms the absence of test coverage for AL nodes, highlighting the need for new tests to validate the proposed changes.