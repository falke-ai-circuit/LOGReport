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
    nodes_data_internal = []
    current_node_group = None

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line or not line.startswith(':e:hw:'):
                    continue

                # Revised regex extraction
                match = re.match(r'^:e:hw:([a-zA-Z0-9]+)\s+([a-zA-Z0-9_]+)\s+([a-zA-Z0-9_:-]+)\s*(//\s*(.+))?$', line)
                if not match:
                    # Fallback for tab-separated lines if primary regex fails
                    parts = line.split('\t')
                    if len(parts) >= 3 and parts.startswith(':e:hw:'):
                        try:
                            token_raw = parts.split(':')[-1].strip()
                            hw_raw = parts.strip()
                            param_raw = parts.strip()
                            comment_raw = parts.strip() if len(parts) > 3 and parts.startswith('//') else ''
                        except (ValueError, IndexError):
                            continue
                    else:
                        continue
                else:
                    token_raw, hw_raw, param_raw, _, comment_raw = match.groups()
                    token_raw = token_raw.strip()
                    hw_raw = hw_raw.strip()
                    param_raw = param_raw.strip()
                    if comment_raw:
                        comment_raw = comment_raw.strip()

                # Determine node type and name
                node_name = None
                node_ip = None
                default_types = []

                # Handle AP0XX_main entries
                ap_main_match = re.match(r'AP(\d{2})_main', hw_raw)
                if ap_main_match:
                    node_id_num = ap_main_match.group(1)
                    node_name = f"AP{node_id_num}m"
                    node_ip = f"192.168.1.{token_raw}" # Assuming token_raw is the LID for IP
                    default_types = ['FBC', 'RPC', 'LOG']

                    if current_node_group and current_node_group['name'] != node_name:
                        nodes_data_internal.append(current_node_group)
                        current_node_group = None # Reset for new node

                    if not current_node_group:
                        current_node_group = {
                            'name': node_name,
                            'ip': node_ip,
                            'tokens': [],
                            'types': default_types
                        }
                    
                    if token_raw not in current_node_group['tokens']:
                        current_node_group['tokens'].append(token_raw)

                # Handle AP0XX_mX entries (sub-nodes)
                elif re.match(r'AP(\d{2})_m\d', hw_raw):
                    ap_sub_match = re.match(r'AP(\d{2})_m\d', hw_raw)
                    if ap_sub_match and current_node_group:
                        expected_main_node_name = f"AP{ap_sub_match.group(1)}m"
                        if current_node_group['name'] == expected_main_node_name:
                            if token_raw not in current_node_group['tokens']:
                                current_node_group['tokens'].append(token_raw)
                        else:
                            # Sub-node without matching main node, or main node already closed
                            # Log a warning or skip
                            pass
                    else:
                        # Sub-node without an active main node group
                        # Log a warning or skip
                        pass

                # Handle ALXX entries
                elif re.match(r'AL\d{2}', hw_raw):
                    node_name = hw_raw
                    node_ip = f"192.168.1.{token_raw}" # Assuming token_raw is the LID for IP
                    default_types = ['LOG', 'LIS']

                    if current_node_group:
                        nodes_data_internal.append(current_node_group)
                        current_node_group = None # Reset for new node

                    current_node_group = {
                        'name': node_name,
                        'ip': node_ip,
                        'tokens': [],
                        'types': default_types
                    }
                    if token_raw not in current_node_group['tokens']:
                        current_node_group['tokens'].append(token_raw)
                
                # If a line is parsed but doesn't fit into a group (e.g., a standalone line not matching AP/AL patterns)
                # and there's no active group, it might be a new standalone node.
                # For now, we'll only process AP/AL groups as per requirements.
                # Any other lines will be implicitly skipped if they don't match the above conditions.

        # After loop, append the last current_node_group if it exists
        if current_node_group:
            nodes_data_internal.append(current_node_group)

        return nodes_data_internal
    except Exception as e:
        raise Exception(f"Parse error: {str(e)}")