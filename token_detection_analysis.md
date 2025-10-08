# Token Detection Mechanism Analysis

## Objective
To investigate how tokens (e.g., 'AP01m 181') are currently detected or can be detected from the initial sys file content, focusing on `src/commander/utils/token_utils.py` and related files.

## Overview
The token detection mechanism is a multi-stage process involving initial extraction from sys files using regex patterns defined in a configuration file, followed by validation and normalization of these extracted tokens.

## Key Components and Their Roles

### 1. `config/sys_parsing_rules.json`
This JSON file serves as the central repository for regular expression patterns used in token and node identification.
- **`ip_address`**: `set XD_IP_ADDR=([0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3})` - Extracts IP addresses.
- **`ap_node`**: `^:e:hw:(?P<lid>[0-9a-fA-F]{2,4})\s+(?P<node_name>AP\d{2})(?:m|r|t)?\d*\s+.*` - Identifies AP-based nodes and their LIDs.
- **`al_node`**: `^:e:hw:(?P<lid>[0-9a-fA-F]{2,4})\s+(?P<node_name>AL\d{2})\s+(?:pxe:sys-csg2)?.*` - Identifies AL-based nodes and their LIDs.
- **`token_entry`**: `^:e:hw:(?P<lid>[0-9a-fA-F]{2,4})\s+(?P<node_prefix>(?:AP|AL)\d{2})((?:_m|_r|_t)?\d*)?\s+.*` - Extracts LIDs and node prefixes from token entries.
- **`token_detection_line`**: `(?P<node_id>(?:AP|AL)\d{2}(?:m|r)?)\s+(?P<tokens>[\d,\s]+)` - A broader pattern used by `SysFileLoader` to detect node IDs and associated tokens (comma-separated numeric strings).

### 2. `src/node_config_parser.py` (`SysFileParser` class)
This module is responsible for parsing the content of individual sys files.
- It loads regex patterns from `config/sys_parsing_rules.json`.
- The `_parse_single_sys_file_content` method iterates through lines to:
    - Extract IP addresses using `ip_address_regex`.
    - Determine node type (AP or AL) and extract the node name using `ap_node_regex` or `al_node_regex`.
    - Extract tokens using `token_entry_regex`. It applies specific logic for AL nodes (single LID as token) and AP nodes (collecting LIDs from specific suffixes like `_m2`, `_r2`).

### 3. `src/sys_file_loader.py` (`SysFileLoader` class)
This module handles loading sys files and provides a method for general token detection.
- It initializes `SysFileParser` for parsing individual token sys files.
- The `detect_tokens_from_content` method uses the `token_detection_line_regex` from `config/sys_parsing_rules.json` to find node IDs and their associated comma-separated tokens within a given file content. This is a more general detection mechanism compared to the structured parsing in `SysFileParser`.

### 4. `src/commander/constants.py`
This file defines a general token pattern.
- **`TOKEN_PATTERN`**: `re.compile(r'^[a-zA-Z0-9]+$')` - A broad regex that matches any alphanumeric string. This pattern is used for general validation of tokens.

### 5. `src/commander/utils/token_utils.py` (`TokenValidator` class)
This module provides utilities for normalizing and validating tokens.
- It imports `TOKEN_PATTERN` from `../constants.py`.
- **`normalize_token(self, token: str) -> str`**:
    - Strips whitespace.
    - Special handling for FBC tokens: pads numeric IDs with zeros (e.g., '1' -> '001'), converts alphanumeric to uppercase.
    - Special handling for RPC tokens with IP prefixes (e.g., '192-168-0-11_162'): extracts the numeric ID and pads it with zeros.
    - For other tokens: converts to lowercase, removes non-alphanumeric characters, and pads numeric tokens with leading zeros to 3 digits.
- **`validate_token(self, token: str) -> bool`**: Validates a token against the general `TOKEN_PATTERN`.
- **`is_fbc_token(self, token: str) -> bool`**: Checks if a token matches the FBC pattern (`^\d{3}[a-z]?$`).
- **`is_rpc_token(self, token: str) -> bool`**: Checks if a token is alphanumeric and not an FBC token.
- The `TokenValidator` is instantiated as a singleton `token_validator`, making its methods globally accessible via helper functions (e.g., `normalize_token`, `validate_token`).

## Interconnections and Workflow
1. **Configuration**: `config/sys_parsing_rules.json` defines the core regex patterns for token and node extraction.
2. **Initial Extraction**: `SysFileParser` (`src/node_config_parser.py`) and `SysFileLoader` (`src/sys_file_loader.py`) use these regex patterns to extract raw node information and tokens from sys files. `SysFileParser` focuses on structured extraction based on node types (AL/AP), while `SysFileLoader.detect_tokens_from_content` provides a more general line-by-line token detection.
3. **General Validation**: `TOKEN_PATTERN` in `src/commander/constants.py` provides a basic alphanumeric validation.
4. **Refined Validation and Normalization**: `TokenValidator` in `src/commander/utils/token_utils.py` takes the extracted tokens and performs more specific validation (e.g., `is_fbc_token`, `is_rpc_token`) and normalization (e.g., padding, case conversion) to ensure consistency and compatibility with the system's internal representation.

## Conclusion
Tokens are detected through a combination of regex-based extraction in `src/node_config_parser.py` and `src/sys_file_loader.py` using patterns from `config/sys_parsing_rules.json`, followed by validation and normalization in `src/commander/utils/token_utils.py`. The process differentiates between AL and AP node token handling during extraction and applies specific formatting rules during normalization.