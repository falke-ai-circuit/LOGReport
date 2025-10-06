import json
from src.utils.file_utils import parse_sys_file, merge_node_data
from pathlib import Path

try:
    # Read AB01_sys and parse new nodes
    ab01_sys_path = Path('AB01_sys')
    new_nodes = parse_sys_file(str(ab01_sys_path))

    # Read existing nodes.json
    nodes_json_path = Path('nodes.json')
    with open(nodes_json_path, 'r', encoding='utf-8') as f:
        existing_nodes = json.load(f)

    # Merge node data
    merged_nodes = merge_node_data(existing_nodes, new_nodes)

    # Write the merged data back to nodes.json
    with open(nodes_json_path, 'w', encoding='utf-8') as f:
        json.dump(merged_nodes, f, indent=4)

    print("nodes.json updated successfully.")

except Exception as e:
    print(f"An error occurred: {e}")