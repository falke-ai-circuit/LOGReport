from pathlib import Path
from typing import List


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


import re
from typing import List, Dict

def parse_sys_file(file_path: str) -> List[Dict]:
    nodes_data = {}

    # Regex patterns
    ap_main_node_regex = re.compile(r"^:e:hw:([0-9a-fA-F]{2,4})\s+(AP\d{2})\s+pxe:sys-csg2.*")
    ap_main_m_node_regex = re.compile(r"^:e:hw:([0-9a-fA-F]{2,4})\s+(AP\d{2})_main\s+pxe:sys-csg2.*")
    ap_reserve_r_node_regex = re.compile(r"^:e:hw:([0-9a-fA-F]{2,4})\s+(AP\d{2})_reserve\s+pxe:sys-csg2.*")
    al_main_node_regex = re.compile(r"^:e:hw:([0-9a-fA-F]{2,4})\s+(AL\d{2})\s+.*")
    token_entry_regex = re.compile(r"^:e:hw:([0-9a-fA-F]{2,4})\s+((?:AP|AL)\d{2})((?:_m\d|_r\d|_t\d)+)\s+.*")
    
    lines = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    except Exception as e:
        raise Exception(f"Error reading file {file_path}: {str(e)}")

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
                "tokens": [],
                "types": ["FBC", "RPC", "LOG", "LIS"]
            }

    # Second pass: Extract tokens and assign to the correct node
    for line in lines:
        token_match = token_entry_regex.match(line)
        if token_match:
            token_lid, node_prefix, suffix = token_match.groups()
            
            parent_node_name = None
            if suffix.startswith("_m"):
                if f"{node_prefix}m" in nodes_data:
                    parent_node_name = f"{node_prefix}m"
                elif node_prefix in nodes_data:
                    parent_node_name = node_prefix
            elif suffix.startswith("_r"):
                if f"{node_prefix}r" in nodes_data:
                    parent_node_name = f"{node_prefix}r"
            else: # For main nodes (APXX or ALXX)
                if node_prefix in nodes_data:
                    parent_node_name = node_prefix
            
            if parent_node_name and token_lid not in nodes_data[parent_node_name]["tokens"]:
                nodes_data[parent_node_name]["tokens"].append(token_lid)
    
    # Sort tokens for consistent output
    for node_name in nodes_data:
        nodes_data[node_name]["tokens"].sort()

    return list(nodes_data.values())