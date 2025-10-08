# Analysis Report: Token Detection Mechanism

## Objective
Investigate how tokens (e.g., 'AP01m 181') are currently detected or can be detected from the initial sys file content. Examine `src/commander/utils/token_utils.py` and related files.

## CEPH+ - Canonical Problem Pack
*   **CURRENT:** Initial sys files are parsed, and tokens need to be detected from their content.
*   **EXPECTED:** A clear understanding of the token detection mechanism, including relevant functions, regex patterns, and data structures in `src/commander/utils/token_utils.py` and related files.
*   **PROBLEM:** Need to identify how tokens are detected to correctly link them to `[tokenid].sys` files for IP address extraction.
*   **HYPOTHESES:** H1: Token detection involves regex matching within the sys file content. H2: `src/commander/utils/token_utils.py` contains the primary logic for token extraction.
*   **EVIDENCE:** File path: `src/commander/utils/token_utils.py`.

## Execution Context
*   **CAPABILITIES:** Access to code graph, semantic search, file reading. Confidence: High.
*   **RISKS:** Incorrect token detection could lead to parsing the wrong `[tokenid].sys` files. Mitigation: Thorough analysis and validation of detection logic. Timeline pressure: Moderate.
*   **CONTEXT:** User wants to enhance Node configuration window to parse `[tokenid].sys` files for IP addresses, supporting multiple initial sys files and differentiating between AL and AP node token handling. Current work focus is on identifying the token detection mechanism.
*   **FOCUS:** Identify Token Detection Mechanism (Task 2 of 9). Branch type: Main. Return target: Orchestrator.
*   **CONSTRAINTS:** Scope limited to understanding token detection.
*   **DELIVERABLES:** Analysis report (token_detection_analysis.md) detailing token detection logic, relevant functions, and patterns.

## Analysis Findings

### 1. Token Extraction from Sys Files (`parse_sys_file` in `src/utils/file_utils.py`)

*   **Function:** `parse_sys_file(file_content: str) -> List[Dict]`
*   **Purpose:** This function is responsible for parsing the raw content of a `.sys` file and extracting structured node data, including node names, IP addresses (currently empty), and a list of associated tokens and types.
*   **Key Regex Patterns:**
    *   `ap_main_node_regex`: `^:e:hw:([0-9a-fA-F]{2,4})\s+(AP\d{2})\s+pxe:sys-csg2.*` - Detects main AP nodes (e.g., `AP01`).
    *   `ap_main_m_node_regex`: `^:e:hw:([0-9a-fA-F]{2,4})\s+(AP\d{2})_main\s+pxe:sys-csg2.*` - Detects AP main nodes with `_main` suffix (e.g., `AP01_main`).
    *   `ap_reserve_r_node_regex`: `^:e:hw:([0-9a-fA-F]{2,4})\s+(AP\d{2})_reserve\s+pxe:sys-csg2.*` - Detects AP reserve nodes with `_reserve` suffix (e.g., `AP01_reserve`).
    *   `al_main_node_regex`: `^:e:hw:([0-9a-fA-F]{2,4})\s+(AL\d{2})\s+pxe:sys-csg2.*` - Detects main AL nodes (e.g., `AL01`).
    *   `token_entry_regex`: `^:e:hw:([0-9a-fA-F]{2,4})\s+((?:AP|AL)\d{2})(_main|_reserve|_t\d+|_m\d+|_r\d+)?\s+.*` - This is the primary regex for extracting tokens. It captures the LID (which is treated as the token ID), the node prefix (e.g., `AP01`, `AL02`), and an optional suffix (`_main`, `_reserve`, `_t\d+`, `_m\d+`, `_r\d+`).
*   **Data Structures:** `nodes_data` (a dictionary where keys are node names and values are dictionaries containing `name`, `ip`, `tokens` (list of strings), and `types` (list of strings)).
*   **Logic Flow:**
    1.  **First Pass:** Iterates through each line of the `file_content`. It uses the `ap_main_node_regex`, `ap_main_m_node_regex`, `ap_reserve_r_node_regex`, and `al_main_node_regex` to identify main node definitions. For each identified node, it initializes an entry in `nodes_data` with its `name`, an empty `ip`, an empty `tokens` list, and predefined `types` (e.g., `["FBC", "RPC", "LOG"]` for AP nodes, `["LOG", "LIS"]` for AL nodes, with the LID as an initial token for AL nodes).
    2.  **Second Pass:** Iterates through the `file_content` again. It skips lines already identified as main node definitions. For other lines, it applies `token_entry_regex` to extract a `token_lid` (the hexadecimal ID from the `:e:hw:` prefix) and the `node_prefix` (e.g., `AP01`, `AL02`). It then attempts to associate this `token_lid` with the correct parent node in `nodes_data` based on the `node_prefix` and any suffix (`_main`, `_reserve`, `_t\d+`, `_m\d+`, `_r\d+`). Tokens are added to the respective node's `tokens` list, ensuring uniqueness and sorting.

### 2. Token Validation and Normalization (`TokenValidator` in `src/commander/utils/token_utils.py`)

*   **Class:** `TokenValidator`
*   **Purpose:** Provides methods to validate and normalize token strings, ensuring consistency and proper categorization.
*   **Key Methods:**
    *   `normalize_token(self, token: str) -> str`:
        *   Strips whitespace.
        *   **FBC Specific:** If `is_fbc_token` is true, numeric FBC tokens are zero-padded to 3 digits (e.g., "1" -> "001"), and alphanumeric FBC tokens are converted to uppercase.
        *   **RPC Specific:** Detects tokens with an IP prefix (e.g., `192-168-0-11_162`) using `re.match(r'^(\d{1,3}-\d{1,3}-\d{1,3}-\d{1,3})_(\d+)$', token)`. It extracts the numeric part (e.g., "162") and zero-pads it to 3 digits if necessary.
        *   **General:** Converts to lowercase and removes non-alphanumeric characters. Numeric tokens are zero-padded to 3 digits.
    *   `validate_token(self, token: str) -> bool`: Uses the global `TOKEN_PATTERN` (defined below) to perform a general validation check.
    *   `is_fbc_token(self, token: str) -> bool`: Checks if a token matches `r'^\d{3}[a-z]?$'` (3 digits followed by an optional lowercase letter) after passing `validate_token`.
    *   `is_rpc_token(self, token: str) -> bool`: Checks if a token is alphanumeric (`r'^[a-z0-9]+$'`) and is *not* an FBC token, after passing `validate_token`.

### 3. `TOKEN_PATTERN` (from `src/commander/constants.py`)

*   **Regex:** `re.compile(r'^[a-zA-Z0-9]+$')`
*   **Purpose:** This is the foundational regex for general token validation. It ensures that any token being processed consists solely of one or more alphanumeric characters.

### How Tokens like 'AP01m 181' are Detected/Handled:

The example token `'AP01m 181'` would first be processed by `parse_sys_file`. The `token_entry_regex` would likely extract `181` as the `token_lid` and `AP01` as the `node_prefix`. The `_m` suffix would indicate it belongs to `AP01m`. When `normalize_token('181')` is called, it would be stripped to `'181'`. Since it's numeric and already 3 digits, it would remain `'181'`. The `is_fbc_token` and `is_rpc_token` methods would then classify it based on their specific patterns.

## Optimization Opportunities

*   **IP Address Extraction:** The `parse_sys_file` currently initializes `ip` as an empty string. An immediate optimization would be to enhance the regex patterns in `parse_sys_file` to extract IP addresses directly from the sys file content if they are present, or from a related configuration.
*   **Unified Token Regex:** While `TOKEN_PATTERN` provides a general validation, the specific FBC/RPC regexes are separate. A more unified or configurable regex approach in `TokenValidator` could simplify future token type additions and maintenance.
*   **Error Handling in `parse_sys_file`:** The current `parse_sys_file` does not explicitly handle malformed lines or unexpected formats. Adding robust error logging or skipping malformed lines could improve resilience and provide better diagnostics during parsing.
*   **Performance:** The `lru_cache` on `normalize_token` is a good start. Further performance analysis could be done on the regex compilation and matching in `parse_sys_file` for very large sys files, potentially pre-compiling all regexes at module load time if not already done.