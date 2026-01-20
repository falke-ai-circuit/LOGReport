"""Debug script to analyze spacing in PIC 12 line"""
import re

# Actual PIC 12 line from log
line = "  12     BI8 BI8 BI8 BI8 BI8 BI8 BI8 BI8 AI8 AI8 BI8 BI8 TI6 TI6        14"

print("=" * 80)
print("LINE ANALYSIS:")
print(f"Full line: '{line}'")
print(f"Line length: {len(line)}")
print()

# Character-by-character breakdown
print("Character breakdown (first 30 chars):")
for i, char in enumerate(line[:30]):
    if char == ' ':
        print(f"  Index {i:2d}: SPACE")
    else:
        print(f"  Index {i:2d}: '{char}'")
print()

# Find PIC number position
pic_match = re.search(r'\d+', line)
if pic_match:
    print(f"PIC number '12' found at index {pic_match.start()}-{pic_match.end()}")
    print(f"After PIC (from index {pic_match.end()}): '{line[pic_match.end():]}'")
    
    # Count spaces after PIC
    spaces_after_pic = ""
    for char in line[pic_match.end():]:
        if char == ' ':
            spaces_after_pic += char
        else:
            break
    print(f"Spaces after PIC: {len(spaces_after_pic)} spaces")
    print()

# Test current regex
FBC_ROW_PATTERN = re.compile(r'^\s*(\d+)\s+(.+?)\s+(\d+)\s*$')
match = FBC_ROW_PATTERN.match(line)
if match:
    print("REGEX MATCH GROUPS:")
    print(f"  Group 1 (PIC): '{match.group(1)}'")
    print(f"  Group 2 (IO units): '{match.group(2)}'")
    print(f"  Group 3 (sum): '{match.group(3)}'")
    print()
    
    # Check what's in group 2
    io_str = match.group(2)
    print(f"IO string length: {len(io_str)}")
    print(f"IO string starts with space? {io_str[0] == ' ' if io_str else 'N/A'}")
    
    # Count leading spaces in captured group
    leading_spaces = 0
    for char in io_str:
        if char == ' ':
            leading_spaces += 1
        else:
            break
    print(f"Leading spaces in captured IO string: {leading_spaces}")
    print()

# Test with different regex patterns
print("=" * 80)
print("TESTING ALTERNATIVE REGEX PATTERNS:")
print()

# Option 1: Greedy middle capture
pattern1 = re.compile(r'^\s*(\d+)\s+(.+)\s+(\d+)\s*$')
match1 = pattern1.match(line)
if match1:
    print("Pattern 1: r'^\s*(\d+)\s+(.+)\s+(\d+)\s*$' (greedy)")
    print(f"  IO string: '{match1.group(2)}'")
    print(f"  Length: {len(match1.group(2))}")
else:
    print("Pattern 1: NO MATCH")
print()

# Option 2: Capture between specific positions
pattern2 = re.compile(r'^\s*(\d+)\s+(.*?)\s+(\d+)\s*$')
match2 = pattern2.match(line)
if match2:
    print("Pattern 2: r'^\s*(\d+)\s+(.*?)\s+(\d+)\s*$' (allow empty)")
    print(f"  IO string: '{match2.group(2)}'")
    print(f"  Length: {len(match2.group(2))}")
else:
    print("Pattern 2: NO MATCH")
print()

# Option 3: Split on PIC and sum
pattern3 = re.compile(r'^\s*(\d+)\s(.+)\s(\d+)\s*$')
match3 = pattern3.match(line)
if match3:
    print("Pattern 3: r'^\s*(\d+)\s(.+)\s(\d+)\s*$' (single space)")
    print(f"  IO string: '{match3.group(2)}'")
    print(f"  Length: {len(match3.group(2))}")
    
    # Check for 4+ consecutive spaces at start
    leading_spaces = 0
    for char in match3.group(2):
        if char == ' ':
            leading_spaces += 1
        else:
            break
    print(f"  Leading spaces: {leading_spaces}")
else:
    print("Pattern 3: NO MATCH")
