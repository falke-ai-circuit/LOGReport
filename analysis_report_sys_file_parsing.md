# Sys File Parsing Analysis Report

## Objective
Investigate and identify the root causes of incorrect sys file parsing for AP-based nodes (AP02m, AP02r) using AB01_sys and nodes.json, and propose solutions.

## CEPH+ - Canonical Problem Pack
**CURRENT:** AB01_sys contains AP02_main and AP02_reserve entries. nodes.json has existing AP02m/AP02r configs. Current parsing logic (ARCH_sys_file_parsing_v1.md, project memory) incorrectly parses AP-based nodes. AP02m has an invented IP, incorrect tokens (181, 182, 183 instead of 182, 183). AP02r is not detected. IP addresses should not be extracted from sys file.
**EXPECTED:** AP02m: no IP, tokens 182, 183. AP02r: detected, no IP, tokens 382, 383.
**PROBLEM:** Existing sys file parsing logic incorrectly extracts IP addresses, misidentifies tokens, and fails to detect certain AP-based nodes from AB01_sys, leading to incorrect node configurations.
**HYPOTHESES:**
H1: Regex patterns for AP0XX_main/AP0XX_reserve are incorrect/incomplete.
H2: Token assignment logic for AP-based nodes is flawed.
H3: Parsing logic for AP0XX_reserve is missing/flawed.
H4: IP address assignment logic is not correctly preventing IP insertion or defaults to incorrect IP.

## Investigation Findings

### Discrepancies Identified
1.  **AP02m (AP02_main):**
    *   **IP Address:** The current parsing logic assigns an invented IP address (e.g., "192.168.1.181") to AP02m, which contradicts the requirement that IP addresses should not be extracted from the sys file.
    *   **Tokens:** The `AB01_sys` file shows `AP02_main` with LID `181`, followed by `AP02_m2` (LID `182`) and `AP02_m3` (LID `183`). The current parsing logic incorrectly includes `181` as a token for AP02m, resulting in tokens `[181, 182, 183]` instead of the expected `[182, 183]`.
2.  **AP02r (AP02_reserve):**
    *   **Detection:** The `AP02_reserve` entry in `AB01_sys` (LID `381`, followed by `AP02_r2` with `382` and `AP02_r3` with `383`) is not detected by the current parsing logic. Consequently, AP02r is not added to the node configurations.

### Root Causes (Confirmed from Code Analysis)
The primary root causes were identified by analyzing the `parse_sys_file` function in `src/utils/file_utils.py`:

1.  **Hardcoded IP Address Assignment (H4 Confirmed):**
    *   The code explicitly assigns an IP address using `node_ip = f"192.168.1.{token_raw}"` for both `AP0XX_main` and `ALXX` entries. This directly violates the requirement to not extract IP addresses from the sys file.
2.  **Incorrect Token Collection for Main Nodes (H2 Confirmed):**
    *   For `AP0XX_main` entries, the LID from the main line itself (e.g., `181` for `AP02_main`) is added to the `tokens` list. The requirement is that only LIDs from the `_m2` and `_m3` (or `_r2`, `_r3`) lines should be considered tokens for the node.
3.  **Missing Parsing Logic for Reserve Nodes (H3 Confirmed):**
    *   There is no dedicated `elif` block or regex pattern within `parse_sys_file` to specifically handle `AP0XX_reserve` entries. The current logic only accounts for `AP0XX_main` and `ALXX` entries, causing `AP02_reserve` and its associated tokens (`382`, `383`) to be entirely missed during parsing.

## Proposed Solutions

Based on the identified root causes, the following solutions are proposed:

1.  **Remove IP Address Assignment:**
    *   Modify the `parse_sys_file` function to ensure that the `ip` field for all parsed nodes is always an empty string, as per the requirement. This involves removing or commenting out lines that assign an IP address.
2.  **Refine Token Collection Logic:**
    *   Adjust the logic for `AP0XX_main` entries to prevent the LID from the main line (e.g., `181`) from being added to the `tokens` list. Only LIDs from subsequent `_m2` and `_m3` lines should be collected.
3.  **Add Parsing Logic for Reserve Nodes:**
    *   Implement a new `elif` block within `parse_sys_file` to specifically detect and process `AP0XX_reserve` entries. This logic should:
        *   Derive the node name (e.g., `AP02r`).
        *   Initialize its `ip` as an empty string.
        *   Collect tokens only from subsequent `_r2` and `_r3` lines.

## Conclusion
The investigation successfully identified the root causes of the incorrect sys file parsing for AP-based nodes. The proposed solutions directly address these issues, ensuring that AP02m and AP02r are correctly parsed without IP addresses and with the accurate set of tokens, aligning with the specified requirements.