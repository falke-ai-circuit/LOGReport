# Technical Documentation: Node Configuration Parser Token Logic

## 1. Overview
This document details the implementation of conditional logic within `src/node_config_parser.py` to correctly select token IDs for parsing `[tokenid].sys` files based on node type (AL-based vs. AP-based). This enhancement is part of the broader objective to improve the Node configuration window's ability to handle multiple initial sys files and differentiate token handling.

## 2. Implemented Functionality
The `select_token_for_sys_file` function has been modified to incorporate the following logic:
- **AL-based Nodes:** If a node's name starts with "AL", it is considered an AL-based node. For these nodes, the function expects a single token. If `tokens` is a list, the single token from the list is returned. If `tokens` is a string, the string itself is returned.
- **AP-based Nodes:** If a node's name starts with "AP", it is considered an AP-based node. For these nodes, the function can handle multiple tokens but will only use the first token available. If `tokens` is a list, the first element of the list is returned. If `tokens` is a string, the string itself is returned.

## 3. Code Modifications
The primary changes were made to the `select_token_for_sys_file` function in `src/node_config_parser.py`.

**File:** `src/node_config_parser.py`

```python
from typing import List, Dict, Optional

def select_token_for_sys_file(node: Dict) -> Optional[str]:
    """
    Selects the appropriate token ID for parsing a [tokenid].sys file based on node type.
    - For AL-based nodes (single token), use that single token.
    - For AP-based nodes (multiple tokens), use the first token only.
    Returns the selected token ID or None if no suitable token is found.
    """
    node_name = node.get("name", "")
    tokens = node.get("tokens", [])

    if node_name.startswith("AL"):
        # AL-based nodes have a single token (LID)
        if tokens:
            if isinstance(tokens, list) and tokens:
                return tokens[0]  # Return the single token from the list
            elif isinstance(tokens, str):
                return tokens  # Return the token directly if it's a string
    elif node_name.startswith("AP"):
        # AP-based nodes can have multiple tokens, use the first one
        if tokens:
            if isinstance(tokens, list) and tokens:
                return tokens[0]  # Return the first token from the list
            elif isinstance(tokens, str):
                return tokens  # Return the token directly if it's a string
    return None

def get_sys_file_path_from_token(token_id: str) -> str:
    """
    Generates a [tokenid].sys file path from a given token ID.
    """
    return f"{token_id}.sys"
```

## 4. Integration Testing
Basic unit tests were performed to validate the `select_token_for_sys_file` function with various inputs:
- AL node with a single token string.
- AL node with a list containing a single token.
- AP node with a single token string.
- AP node with a list containing multiple tokens (verifying only the first is selected).
- Nodes with no tokens or empty token lists.
- Nodes with names not starting with "AL" or "AP".

All tests confirmed that the function correctly identifies the node type and selects the appropriate token ID as per the requirements.

## 5. Usage Examples
```python
# Example AL-based node
al_node_single_token_str = {"name": "AL_Node1", "tokens": "LID123"}
al_node_single_token_list = {"name": "AL_Node2", "tokens": ["LID456"]}

# Example AP-based node
ap_node_single_token_str = {"name": "AP_Node1", "tokens": "AP_TOKEN_A"}
ap_node_multiple_tokens_list = {"name": "AP_Node2", "tokens": ["AP_TOKEN_B", "AP_TOKEN_C"]}

# Example node with no tokens
no_token_node = {"name": "GenericNode"}

# Test cases
print(f"AL Node (string token): {select_token_for_sys_file(al_node_single_token_str)}")
print(f"AL Node (list token): {select_token_for_sys_file(al_node_single_token_list)}")
print(f"AP Node (string token): {select_token_for_sys_file(ap_node_single_token_str)}")
print(f"AP Node (list token): {select_token_for_sys_file(ap_node_multiple_tokens_list)}")
print(f"No Token Node: {select_token_for_sys_file(no_token_node)}")
```

## 6. Maintenance Notes
- Future changes to node naming conventions or token structures may require updates to this logic.
- Ensure comprehensive unit tests are maintained for this function to prevent regressions.