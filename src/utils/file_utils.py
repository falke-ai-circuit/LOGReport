from pathlib import Path
from typing import List, Dict, Optional
import re
import json

def filter_lines(lines: List[str], mode: str = "all", limit: int = 0,
                 start: int = 0, end: int = 0) -> List[str]:
    """Filter a list of lines based on the requested mode."""
    if not lines:
        return []
    mode = mode.lower()
    if mode == 'first' and limit > 0:
        return lines[:limit]
    if mode == 'last' and limit > 0:
        return lines[-limit:]
    if mode == 'range' and start > 0 and end > start:
        return lines[start - 1:end]
    return lines


def read_text_file(filepath: Path, encodings=None) -> List[str]:
    """Read text file using a list of encodings and return lines."""
    encodings = encodings or ['utf-8', 'ascii', 'latin-1']
    for enc in encodings:
        try:
            with open(filepath, 'r', encoding=enc) as f:
                return [line.rstrip('\n') for line in f.readlines()]
        except UnicodeDecodeError:
            continue
    raise ValueError(f"Could not read {filepath} with any supported encoding")


def parse_sys_file(file_content: str, sys_file_path: Optional[Path] = None) -> List[Dict]:
    """
    Parse a sys file and extract node configurations.
    
    Args:
        file_content: The content of the sys file
        sys_file_path: Optional path to the sys file. If provided and the file is a 
                      token-specific file (e.g., 181.sys), IP address will be extracted.
    
    Returns:
        List of node dictionaries with name, ip, tokens, and types
    """
    nodes_data = {}
    extracted_ip = ""

    # Regex patterns
    ap_main_node_regex = re.compile(r"^:e:hw:([0-9a-fA-F]{2,4})\s+(AP\d{2})\s+pxe:sys-csg2.*")
    ap_main_m_node_regex = re.compile(r"^:e:hw:([0-9a-fA-F]{2,4})\s+(AP\d{2})_main\s+pxe:sys-csg2.*")
    ap_reserve_r_node_regex = re.compile(r"^:e:hw:([0-9a-fA-F]{2,4})\s+(AP\d{2})_reserve\s+pxe:sys-csg2.*")
    al_main_node_regex = re.compile(r"^:e:hw:([0-9a-fA-F]{2,4})\s+(AL\d{2})\s+pxe:sys-csg2.*")
    token_entry_regex = re.compile(r"^:e:hw:([0-9a-fA-F]{2,4})\s+((?:AP|AL)\d{2})(_main|_reserve|_t\d+|_m\d+|_r\d+)?\s+.*")
    ip_address_regex = re.compile(r"set XD_IP_ADDR=(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})")
    
    lines = file_content.splitlines()

    # Extract IP address only if sys_file_path is provided and it's a token-specific file
    # Token-specific files can be:
    # 1. Pure decimal (e.g., 181, 41, 21) - max 5 chars
    # 2. Bare hexadecimal (e.g., 1a1, 3a1, 1c1, 1e1) - max 5 chars
    # 3. Prefixed hex (e.g., 0x1a1, x3a1) - max 7 chars (0x + 5)
    if sys_file_path:
        file_stem = sys_file_path.stem
        is_token_file = False
        
        # Check if it's a pure decimal token (with length constraint)
        if file_stem.isdigit() and len(file_stem) <= 5:
            is_token_file = True
        # Check if it's a hexadecimal token (with or without 0x/x prefix)
        elif file_stem.lower().startswith(('0x', 'x')):
            # Remove prefix and check if remaining chars are hex
            hex_part = file_stem[2:] if file_stem.lower().startswith('0x') else file_stem[1:]
            if all(c in '0123456789abcdefABCDEF' for c in hex_part) and len(hex_part) <= 5:
                is_token_file = True
        # Check if it's a bare hexadecimal token (no 0x prefix but contains hex digits)
        elif all(c in '0123456789abcdefABCDEF' for c in file_stem) and len(file_stem) <= 5:
            is_token_file = True
        
        if is_token_file:
            for line in lines:
                if ip_match := ip_address_regex.match(line):
                    extracted_ip = ip_match.group(1)
                    break  # Assume only one IP address per file

    # First pass: Identify main nodes and initialize their data
    # The main LID (e.g., 181 for AP02_main) is stored separately for IP lookup
    # but NOT added to the tokens list - only subordinate tokens are added
    for line in lines:
        match_ap = ap_main_node_regex.match(line)
        match_ap_main = ap_main_m_node_regex.match(line)
        match_ap_reserve = ap_reserve_r_node_regex.match(line)

        if match_ap:
            lid, node_name_prefix = match_ap.groups()
            full_node_name = node_name_prefix
            nodes_data[full_node_name] = {
                "name": full_node_name,
                "ip": "",
                "tokens": [],  # Main LID not included - only for IP lookup
                "types": ["FBC", "RPC", "LOG"],
                "_main_token": lid  # Store for IP lookup but not in tokens list
            }
        elif match_ap_main:
            lid, node_name_prefix = match_ap_main.groups()
            full_node_name = f"{node_name_prefix}m"
            nodes_data[full_node_name] = {
                "name": full_node_name,
                "ip": "",
                "tokens": [],  # Main LID not included - only for IP lookup
                "types": ["FBC", "RPC", "LOG"],
                "_main_token": lid  # Store for IP lookup but not in tokens list
            }
        elif match_ap_reserve:
            lid, node_name_prefix = match_ap_reserve.groups()
            full_node_name = f"{node_name_prefix}r"
            nodes_data[full_node_name] = {
                "name": full_node_name,
                "ip": "",
                "tokens": [],  # Reserve LID not included - only for IP lookup
                "types": ["FBC", "RPC", "LOG"],
                "_main_token": lid  # Store for IP lookup but not in tokens list
            }
        elif al_match := al_main_node_regex.match(line):
            lid, node_name = al_match.groups()
            nodes_data[node_name] = {
                "name": node_name,
                "ip": "",
                "tokens": [lid],  # For AL nodes, main token IS in tokens list (single token)
                "types": ["LOG", "LIS"],
                "_main_token": lid  # Store for IP lookup as well
            }

    # Second pass: Extract tokens and assign to the correct node
    for line in lines:
        # Skip lines that define main nodes
        if (ap_main_node_regex.match(line) or
            ap_main_m_node_regex.match(line) or
            ap_reserve_r_node_regex.match(line) or
            al_main_node_regex.match(line)):
            continue  # Skip this line, it's a main node definition

        token_match = token_entry_regex.match(line)
        if token_match:
            token_lid, node_prefix, suffix = token_match.groups()
            
            parent_node_name = None
            if suffix and suffix.startswith("_m"):
                if f"{node_prefix}m" in nodes_data:
                    parent_node_name = f"{node_prefix}m"
                elif node_prefix in nodes_data:
                    parent_node_name = node_prefix
            elif suffix and suffix.startswith("_r"):
                if f"{node_prefix}r" in nodes_data:
                    parent_node_name = f"{node_prefix}r"
            elif suffix and suffix.startswith("_t"):
                if node_prefix in nodes_data:
                    parent_node_name = node_prefix
            elif not suffix and node_prefix in nodes_data:  # Handle nodes without suffix
                parent_node_name = node_prefix
            
            if parent_node_name and token_lid not in nodes_data[parent_node_name]["tokens"]:
                nodes_data[parent_node_name]["tokens"].append(token_lid)
            
            # Also add token to the base node if it's a suffixed node
            if suffix and node_prefix in nodes_data and token_lid not in nodes_data[node_prefix]["tokens"]:
                nodes_data[node_prefix]["tokens"].append(token_lid)
    
    # Sort tokens for consistent output
    for node_name in nodes_data:
        nodes_data[node_name]["tokens"].sort()

    # If this is a token-specific file and we extracted an IP, return a minimal node for IP mapping
    # This allows the caller to extract just the IP without getting node structure
    if extracted_ip and sys_file_path:
        file_stem = sys_file_path.stem
        is_token_file = False
        
        # Check if it's a pure decimal token (with length constraint)
        if file_stem.isdigit() and len(file_stem) <= 5:
            is_token_file = True
        # Check if it's a hexadecimal token (with or without 0x/x prefix)
        elif file_stem.lower().startswith(('0x', 'x')):
            # Remove prefix and check if remaining chars are hex
            hex_part = file_stem[2:] if file_stem.lower().startswith('0x') else file_stem[1:]
            if all(c in '0123456789abcdefABCDEF' for c in hex_part) and len(hex_part) <= 5:
                is_token_file = True
        # Check if it's a bare hexadecimal token (no 0x prefix but contains hex digits)
        elif all(c in '0123456789abcdefABCDEF' for c in file_stem) and len(file_stem) <= 5:
            is_token_file = True
        
        if is_token_file:
            # Return a single "dummy" node with just the IP for mapping purposes
            return [{
                "name": f"_token_{file_stem}",
                "ip": extracted_ip,
                "tokens": [file_stem],
                "types": []
            }]

    # Convert nodes_data to list and keep _main_token for caller to use
    # Don't remove it yet - let the caller decide
    return list(nodes_data.values())

def merge_node_data(existing_nodes: List[Dict], new_nodes: List[Dict]) -> List[Dict]:
    """
    Merges new node data into existing node data.
    Preserves existing nodes not present in new_nodes.
    Updates existing nodes with new data if names match.
    Handles both old format (tokens as strings) and new format (tokens as objects).
    """
    merged_nodes = {node["name"]: node for node in existing_nodes}

    for new_node in new_nodes:
        node_name = new_node["name"]
        if node_name in merged_nodes:
            # Update existing node with new data
            existing_node = merged_nodes[node_name]
            new_ip = new_node.get("ip", "")
            
            # Update IP: prefer non-empty new IP, otherwise keep existing
            if new_ip:
                existing_node["ip"] = new_ip
            elif not existing_node.get("ip"):
                existing_node["ip"] = ""
            
            # Merge tokens (handle both formats)
            new_tokens = new_node.get("tokens", [])
            existing_tokens = existing_node.get("tokens", [])
            
            # Check format of tokens
            if new_tokens:
                if isinstance(new_tokens[0], str):
                    # Old format: tokens are strings
                    # Merge string tokens
                    existing_token_ids = set()
                    if existing_tokens and isinstance(existing_tokens[0], str):
                        existing_token_ids = set(existing_tokens)
                    elif existing_tokens and isinstance(existing_tokens[0], dict):
                        # Existing is new format, extract token_ids
                        existing_token_ids = {t.get("token_id") for t in existing_tokens}
                    
                    for token_id in new_tokens:
                        if token_id not in existing_token_ids:
                            if existing_tokens and isinstance(existing_tokens[0], dict):
                                # Can't mix formats, skip
                                pass
                            else:
                                existing_tokens.append(token_id)
                                existing_token_ids.add(token_id)
                    
                    existing_node["tokens"] = existing_tokens
                else:
                    # New format: tokens are objects with token_id and token_type
                    existing_token_keys = set()
                    if existing_tokens and isinstance(existing_tokens[0], dict):
                        existing_token_keys = {(t.get("token_id"), t.get("token_type")) for t in existing_tokens}
                    
                    for new_token in new_tokens:
                        token_key = (new_token.get("token_id"), new_token.get("token_type"))
                        if token_key not in existing_token_keys:
                            existing_tokens.append(new_token)
                            existing_token_keys.add(token_key)
                    
                    existing_node["tokens"] = existing_tokens
            
            # Merge types, ensuring no duplicates
            existing_types = set(existing_node.get("types", []))
            new_types = set(new_node.get("types", []))
            merged_types = list(existing_types.union(new_types))
            merged_types.sort()
            existing_node["types"] = merged_types
        else:
            # Add new node
            merged_nodes[node_name] = new_node
    
    return list(merged_nodes.values())