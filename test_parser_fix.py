"""Test fixed-width FBC parser"""
import re

def parse_fbc_row_fixed_width(line: str):
    """Parse FBC row with regex that handles empty slots and 'N' suffix"""
    # Match pattern: "  PIC IO_UNITS sum"
    match = re.match(r'^\s*(\d+)\s+([\w\sN]+?)\s+(\d+)\s*$', line)
    if not match:
        return None
    
    pic_number = match.group(1)
    io_units_str = match.group(2)
    sum_value = match.group(3)
    
    print(f"PIC: {pic_number}, Sum: {sum_value}")
    print(f"IO string: {repr(io_units_str)}")
    print(f"IO string length: {len(io_units_str)}")
    
    # Extract I/O units: ([A-Z]{2}\d+N?) captures units, (\s{4,}) captures empty slots
    io_units = []
    pattern = r'([A-Z]{2}\d+N?)|\s{4,}'
    
    for match_obj in re.finditer(pattern, io_units_str):
        if match_obj.group(1):
            # Valid I/O unit
            io_units.append(match_obj.group(1))
        else:
            # Empty slot (4+ spaces)
            io_units.append('')
    
    return pic_number, io_units, sum_value


# Test cases
test_lines = [
    "   1 AI8 BI8 BI8 BI8 BO8 BI8 BO8 BI8 BI8 BI8 BI8NBI8 BO8 TI6 TI6        15",  # PIC 1 - BI8N at position 11
    "  11 AI8 BI8     BI8 BO8 BI8 BO8 BI8 BO8 BI8NBI8 BI8 BI8 TI6 TI6        14",  # PIC 11 - empty at position 7
    "   0 AI8 BI8 BO8 BI8 BI8 BI8 BO8 BI8 BO8 BI8 BO8 BI8 BO8 BI8 AO4        15",  # PIC 0 - normal
]

for line in test_lines:
    print("="*80)
    print(f"Input: {line}")
    result = parse_fbc_row_fixed_width(line)
    if result:
        pic, units, sum_val = result
        print(f"Parsed {len(units)} units:")
        for idx, unit in enumerate(units, start=5):
            print(f"  Col {idx}: '{unit}'")
    print()
