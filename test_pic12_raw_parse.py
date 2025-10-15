"""Debug PIC 12 raw line parsing step by step"""
import re

# Raw line from file (line 21)
raw_line = "  12     BI8 BI8 BI8 BI8 BI8 BI8 BI8 BI8 AI8 AI8 BI8 BI8 TI6 TI6        14"

print("="*80)
print("RAW LINE:")
print(repr(raw_line))
print(f"Visual: {raw_line}")
print()

# Step 1: Extract components using FBC_ROW_PATTERN
FBC_ROW_PATTERN = re.compile(r'^\s*(\d+)\s(.+)\s(\d+)\s*$')
match = FBC_ROW_PATTERN.match(raw_line)

if match:
    pic_number = match.group(1)
    io_units_str = match.group(2)
    sum_value = match.group(3)
    
    print("STEP 1: FBC_ROW_PATTERN match:")
    print(f"  PIC: '{pic_number}'")
    print(f"  IO units string: {repr(io_units_str)}")
    print(f"  Sum: '{sum_value}'")
    print()
    
    # Step 2: Extract I/O units with empty slot detection
    pattern = r'([A-Z]{2}\d+N?)|\s{4,}'
    io_units = []
    
    print("STEP 2: Extracting I/O units:")
    for idx, match_obj in enumerate(re.finditer(pattern, io_units_str)):
        if match_obj.group(1):
            # Valid I/O unit
            unit = match_obj.group(1)
            io_units.append(unit)
            print(f"  Position {idx}: '{unit}' (valid unit)")
        else:
            # Empty slot
            empty_match = match_obj.group(0)
            io_units.append('')
            print(f"  Position {idx}: {repr(empty_match)} (EMPTY SLOT - {len(empty_match)} spaces)")
    
    print()
    print(f"TOTAL UNITS FOUND: {len(io_units)}")
    print(f"Units list: {io_units}")
    print()
    
    # Step 3: Map to column headers (simulating headers 5-20)
    headers = ['PIC', '5', '6', '7', '8', '9', '10', '11', '12', '13', '14', '15', '16', '17', '18', '19', '20', 'sum']
    
    print("STEP 3: Mapping to column headers:")
    row_data = {'PIC': pic_number}
    for i, col_num in enumerate(headers[1:-1]):  # Skip 'PIC' and 'sum'
        if i < len(io_units):
            value = io_units[i]
            row_data[col_num] = value
            marker = "EMPTY" if not value else value
            print(f"  Card {col_num:>2} <- io_units[{i}] = '{value}' ({marker})")
        else:
            row_data[col_num] = ''
            print(f"  Card {col_num:>2} <- (missing) = '' (EMPTY)")
    
    row_data['sum'] = sum_value
    print(f"  Sum: '{sum_value}'")
    print()
    
    print("="*80)
    print("FINAL ROW DATA:")
    for col in headers:
        value = row_data.get(col, 'MISSING')
        marker = "✗ EMPTY" if not value and col not in ['PIC', 'sum'] else f"✓ {value}"
        print(f"  {col:>3}: '{value:6}' {marker}")

else:
    print("ERROR: FBC_ROW_PATTERN did not match!")
