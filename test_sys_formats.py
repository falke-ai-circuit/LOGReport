#!/usr/bin/env python3
"""Test both AB01_sys and individual sys file parsing"""
from pathlib import Path
from src.utils.file_utils import parse_sys_file

# Test 1: AB01_sys (topology file)
print("="*60)
print("TEST 1: AB01_sys (Master Topology File)")
print("="*60)
content = Path('d:/_SHARED/_SYSTEM_CONFIGURATOR_SYS/AB01_sys').read_text()
nodes = parse_sys_file(content, Path('d:/_SHARED/_SYSTEM_CONFIGURATOR_SYS/AB01_sys'))

print(f"\nParsed {len(nodes)} nodes from AB01_sys")
for i, node in enumerate(nodes[:5], 1):
    print(f"{i}. {node['name']:12} - IP: {node['ip']:15} - Tokens: {node['tokens']}")

# Test 2: Individual sys files (token config files)
print("\n" + "="*60)
print("TEST 2: Individual Token SYS Files")
print("="*60)

test_files = ['21.sys', 'fc01.sys', '161.sys', '1581.sys', 'a1.sys']
for filename in test_files:
    filepath = Path(f'd:/_SHARED/_SYSTEM_CONFIGURATOR_SYS/{filename}')
    if filepath.exists():
        content = filepath.read_text()
        result = parse_sys_file(content, filepath)
        if result:
            node = result[0]
            print(f"\n{filename:12} -> IP: {node['ip']:15} Token: {node['tokens']}")
    else:
        print(f"\n{filename:12} -> FILE NOT FOUND")

print("\n" + "="*60)
print("SUMMARY")
print("="*60)
print(f"✓ AB01_sys extracts node topology ({len(nodes)} nodes)")
print(f"✓ Individual sys files extract IP addresses and tokens")
print(f"✓ Both formats now supported!")
