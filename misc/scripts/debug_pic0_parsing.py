"""Debug script to test PIC 0 parsing"""
import re

# Simulated telnet response lines
telnet_lines = [
    "PIC  5   6   7   8   9  10  11  12  13  14  15  16  17  18  19  20    sum",
    "----------------------------------------------------------------------------",
    "  0 AI8 BI8 BO8 BI8 BI8 BI8 BO8 BI8 BO8 BI8 BO8 BI8 BO8 BI8 AO4         15",
    "  1 AI8 BI8 BI8 BI8 BO8 BI8 BO8 BI8 BI8 BI8 BI8NBI8 BO8 TI6 TI6         15",
    "  2 AI8 BI8 BI8N BI8 BO8 BI8 BO8 BI8 BI8 BI8 BI8 AO4 BI8 BI8 BI8        15"
]

# FBC_ROW_PATTERN from parser
FBC_ROW_PATTERN = re.compile(r'^\s*(\d+)\s(.+)\s(\d+)\s*$')

print("=" * 80)
print("Testing PIC 0 Parsing")
print("=" * 80)

for i, line in enumerate(telnet_lines):
    if i == 0:
        print(f"\n[HEADER] Line {i}: {repr(line)}")
        continue
    if line.startswith('---'):
        print(f"[SEPARATOR] Line {i}: {repr(line)}")
        continue
    
    print(f"\n[DATA] Line {i}: {repr(line)}")
    print(f"  Length: {len(line)} chars")
    
    # Test original line (with leading spaces)
    match_original = FBC_ROW_PATTERN.match(line)
    print(f"  Match (original): {match_original is not None}")
    if match_original:
        print(f"    PIC: {repr(match_original.group(1))}")
        print(f"    IO: {repr(match_original.group(2))}")
        print(f"    Sum: {repr(match_original.group(3))}")
    
    # Test stripped line (current behavior)
    line_stripped = line.strip()
    match_stripped = FBC_ROW_PATTERN.match(line_stripped)
    print(f"  Match (stripped): {match_stripped is not None}")
    if match_stripped:
        print(f"    PIC: {repr(match_stripped.group(1))}")
        print(f"    IO: {repr(match_stripped.group(2))}")
        print(f"    Sum: {repr(match_stripped.group(3))}")

print("\n" + "=" * 80)
print("Analysis Complete")
print("=" * 80)
