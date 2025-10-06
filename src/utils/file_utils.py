from pathlib import Path
from typing import List, Dict
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


def parse_sys_file(file_content: str) -> List[Dict]:
    nodes_data = {}

    # Regex patterns
    ap_main_node_regex = re.compile(r"^:e:hw:([0-9a-fA-F]{2,4})\s+(AP\d{2})\s+pxe:sys-csg2.*")
    ap_main_m_node_regex = re.compile(r"^:e:hw:([0-9a-fA-F]{2,4})\s+(AP\d{2})_main\s+pxe:sys-csg2.*")
    ap_reserve_r_node_regex = re.compile(r"^:e:hw:([0-9a-fA-F]{2,4})\s+(AP\d{2})_reserve\s+pxe:sys-csg2.*")
    al_main_node_regex = re.compile(r"^:e:hw:([0-9a-fA-F]{2,4})\s+(AL\d{2})\s+pxe:sys-csg2.*")
    token_entry_regex = re.compile(r"^:e:hw:([0-9a-fA-F]{2,4})\s+((?:AP|AL)\d{2})(_main|_reserve|_t\d+|_m\d+|_r\d+)?\s+.*")
    
    lines = file_content.splitlines()

    # First pass: Identify main nodes and initialize their data
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
                "tokens": [],
                "types": ["FBC", "RPC", "LOG"]
            }
        elif match_ap_main:
            lid, node_name_prefix = match_ap_main.groups()
            full_node_name = f"{node_name_prefix}m"
            nodes_data[full_node_name] = {
                "name": full_node_name,
                "ip": "",
                "tokens": [],
                "types": ["FBC", "RPC", "LOG"]
            }
        elif match_ap_reserve:
            lid, node_name_prefix = match_ap_reserve.groups()
            full_node_name = f"{node_name_prefix}r"
            nodes_data[full_node_name] = {
                "name": full_node_name,
                "ip": "",
                "tokens": [],
                "types": ["FBC", "RPC", "LOG"]
            }
        elif al_match := al_main_node_regex.match(line):
            lid, node_name = al_match.groups()
            nodes_data[node_name] = {
                "name": node_name,
                "ip": "",
                "tokens": [lid], # Extract LID as a token for AL nodes
                "types": ["LOG", "LIS"]
            }

    # Second pass: Extract tokens and assign to the correct node
    for line in lines:
        # Skip lines that define main nodes
        if (ap_main_node_regex.match(line) or
            ap_main_m_node_regex.match(line) or
            ap_reserve_r_node_regex.match(line) or
            al_main_node_regex.match(line)):
            continue # Skip this line, it's a main node definition

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
            elif not suffix and node_prefix in nodes_data: # Handle nodes without suffix (e.g., AP01, AL03)
                parent_node_name = node_prefix
            
            if parent_node_name and token_lid not in nodes_data[parent_node_name]["tokens"]:
                nodes_data[parent_node_name]["tokens"].append(token_lid)
            
            # Also add token to the base node if it's a suffixed node
            if suffix and node_prefix in nodes_data and token_lid not in nodes_data[node_prefix]["tokens"]:
                nodes_data[node_prefix]["tokens"].append(token_lid)
    
    # Sort tokens for consistent output
    for node_name in nodes_data:
        nodes_data[node_name]["tokens"].sort()

    return list(nodes_data.values())

def merge_node_data(existing_nodes: List[Dict], new_nodes: List[Dict]) -> List[Dict]:
    """
    Merges new node data into existing node data.
    Preserves existing nodes not present in new_nodes.
    Updates existing nodes with new data if names match.
    """
    merged_nodes = {node["name"]: node for node in existing_nodes}

    for new_node in new_nodes:
        node_name = new_node["name"]
        if node_name in merged_nodes:
            # Update existing node with new data, preserving IP if not empty in existing
            existing_node = merged_nodes[node_name]
            new_ip = new_node.get("ip", "")
            
            # Preserve existing IP if new IP is empty or not provided
            if existing_node.get("ip") and not new_ip:
                new_node["ip"] = existing_node["ip"]
            elif existing_node.get("ip_address") and not new_ip: # Handle 'ip_address' key
                new_node["ip_address"] = existing_node["ip_address"]
            
            # Merge tokens, ensuring no duplicates and preserving existing token structure
            existing_tokens = { (t.get("token_id"), t.get("token_type")) : t for t in existing_node.get("tokens", []) }
            for new_token in new_node.get("tokens", []):
                token_key = (new_token.get("token_id"), new_token.get("token_type"))
                if token_key not in existing_tokens:
                    existing_tokens[token_key] = new_token
            new_node["tokens"] = list(existing_tokens.values())

            # Merge types, ensuring no duplicates
            existing_types = set(existing_node.get("types", []))
            new_types = set(new_node.get("types", []))
            new_node["types"] = list(existing_types.union(new_types))
            new_node["types"].sort() # Sort for consistent output

            # Update the merged node
            merged_nodes[node_name].update(new_node)
        else:
            # Add new node
            merged_nodes[node_name] = new_node
    
    return list(merged_nodes.values())