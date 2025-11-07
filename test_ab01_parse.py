#!/usr/bin/env python3
"""Test AB01_sys parsing"""
from pathlib import Path
from src.utils.file_utils import parse_sys_file

# Read AB01_sys
content = Path('d:/_SHARED/_SYSTEM_CONFIGURATOR_SYS/AB01_sys').read_text()
nodes = parse_sys_file(content)

print(f"Parsed {len(nodes)} nodes from AB01_sys\n")

# Show first 10 nodes
for i, node in enumerate(nodes[:10], 1):
    print(f"{i}. {node['name']:12} - IP: {node['ip']:15} - Tokens: {node['tokens']}")

# Count node types
al_nodes = [n for n in nodes if n['name'].startswith('AL')]
ap_nodes = [n for n in nodes if n['name'].startswith('AP')]
other_nodes = [n for n in nodes if not n['name'].startswith(('AL', 'AP'))]

print(f"\n--- Summary ---")
print(f"Total nodes: {len(nodes)}")
print(f"AL nodes: {len(al_nodes)}")
print(f"AP nodes: {len(ap_nodes)}")
print(f"Other nodes: {len(other_nodes)}")

# Show other nodes
if other_nodes:
    print(f"\nOther nodes found:")
    for node in other_nodes:
        print(f"  {node['name']:12} - {len(node['tokens'])} tokens")
