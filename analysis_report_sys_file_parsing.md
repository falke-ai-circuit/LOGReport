# Analysis Report: Sys File Parsing Logic for Multi-Token Extraction and Type-Based Default Node Configuration

## Objective
Analyze existing sys file parsing logic to support multi-token extraction and type-based default node configuration.

## Current State (CEPH+ v1.0)
The existing sys file parser (`src/utils/file_utils.py::parse_sys_file`) and mapping logic (`src/node_config_dialog.py::NodeConfigDialog.load_sys_file`) handle single token extraction and basic type assignment (RPC/LOG for 'pxe:', FBC/LIS for '-'). Duplicates are skipped.

## Expected Behavior
The parser should extract multiple tokens (e.g., 1a1, 1a2, 1a3 for AP03_main) and apply default types (FBC RPC and LOG for AP nodes, LOG and LIS for AL nodes) based on node name patterns.

## Problem
The current parser does not correctly extract multiple tokens or apply default types based on node name patterns (AP/AL).

## Evidence
User examples:
*   `:e:hw:1a1 AP03_main pxe:sys-csg2 // AP03 Main PCS` (AP03_main -> AP03m, tokens 1a1,1a2,1a3, FBC RPC, LOG)
*   `:e:hw:21 AL01 pxe:sys-csg2 // AL01 LIS` (AL01 -> AL, token 21, LOG, LIS)

## Analysis Findings

### 1. `src/utils/file_utils.py::parse_sys_file`
*   **Current Regex**: `r'^:e:hw:(\d+)\s+(.+?)\s+(.+?)\s*(// (.+))?$'`
    *   The `(\d+)` group for `lid_str` is restrictive, only matching digits. This prevents the extraction of alphanumeric tokens like `1a1`.
*   **IP Address Generation**: `node_ip = f"192.168.1.{lid}"`
    *   This relies on `lid` being an integer, which conflicts with alphanumeric tokens.
*   **Token Extraction**: Currently extracts a single token from `param` if it starts with `pxe:`.
    *   Does not support generating multiple tokens based on node name patterns.
*   **Type Assignment**: Hardcoded `if/elif` logic based on `param` value (`pxe:` or `-`).
    *   Does not dynamically assign types based on node name patterns (AP/AL).

### 2. `src/node_config_dialog.py::NodeConfigDialog.load_sys_file`
*   This method calls `parse_sys_file` and appends the returned nodes to `self.nodes_data`.
*   It handles duplicate node names but does not contain logic for multi-token generation or type-based default assignment.
*   The core modifications are required within `parse_sys_file` or a new utility function it calls.

## Proposed Changes and Recommendations

To address the requirements, the following changes are recommended, primarily within `src/utils/file_utils.py::parse_sys_file` or a new helper function:

1.  **Update Regex for Alphanumeric Tokens**:
    *   **Current**: `r'^:e:hw:(\d+)\s+(.+?)\s+(.+?)\s*(// (.+))?$'`
    *   **Proposed**: `r'^:e:hw:([\w\d]+)\s+(.+?)\s+(.+?)\s*(// (.+))?$'`
    *   **Rationale**: This change allows `lid_str` to capture alphanumeric values (e.g., `1a1`), which can then be used as a base token ID.

2.  **Conditional IP Address Generation**:
    *   **Logic**: After extracting `lid_str`, check if it's purely numeric.
        *   If `lid_str.isnumeric()`: `lid = int(lid_str)`, then `node_ip = f"192.168.1.{lid}"`.
        *   If `lid_str` is alphanumeric: A default IP (e.g., `192.168.1.0` or a placeholder) or an IP derived from a numeric part of the `hw` or `name` should be assigned. The problem statement implies `1a1` is a token, not necessarily the LID for IP. Further clarification might be needed on how IP should be derived for alphanumeric `lid_str` values. For the purpose of this analysis, we assume `lid_str` is primarily a token identifier.

3.  **Node Name Normalization**:
    *   **Logic**: Introduce a helper function, e.g., `normalize_node_name(name)`, to convert node names like `AP03_main` to `AP03m` or `AL01` to `AL`. This normalized name will be used for type assignment.
    *   **Example**: `AP03_main` -> `AP03m`, `AL01` -> `AL`.

4.  **Multi-token Generation Function**:
    *   **Function**: Create a new helper function, e.g., `generate_tokens_from_pattern(node_name, base_token_id) -> List[str]`.
    *   **Logic**: This function would take the normalized `node_name` and a `base_token_id` (which could be the alphanumeric `lid_str` or a value from `param`).
        *   For "AP" nodes (e.g., `AP03m`): If `base_token_id` is `1a1`, generate `['1a1', '1a2', '1a3']`. The exact pattern for generating `1a2`, `1a3` from `1a1` needs to be defined (e.g., incrementing the numeric part, or a fixed set of suffixes).
        *   For "AL" nodes (e.g., `AL`): If `base_token_id` is `21`, generate `['21']`.
    *   **Integration**: Call this function to populate the `tokens` list in the `node` dictionary.

5.  **Type-Based Default Configuration**:
    *   **Logic**: After normalizing the node name, apply conditional logic to assign default types:
        *   If `normalized_name.startswith('AP')`: `types = ['FBC', 'RPC', 'LOG']`
        *   If `normalized_name.startswith('AL')`: `types = ['LOG', 'LIS']`
    *   **Integration**: This logic replaces the existing `if param.startswith('pxe:')` and `elif param == '-'` blocks for type assignment.

## Conclusion
The existing `sys` file parsing logic requires significant modifications to its regex, IP address handling, token extraction, and type assignment mechanisms to support multi-token extraction and type-based default node configuration. The proposed changes involve updating the regex, introducing conditional logic for IP generation, normalizing node names, implementing a multi-token generation function, and dynamically assigning types based on node name patterns. These changes will ensure accurate and flexible node configuration as per the requirements.