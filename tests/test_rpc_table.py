"""Test table creation with RPC file"""
import sys
sys.path.insert(0, 'd:/_APP/LOGReport/src')

from commander.services.fbc_parser_service import FbcParserService

# Parse RPC file
parser = FbcParserService()
result = parser.parse_file(r'd:\_APP\LOGReport\_DIA\RPC\AP02m\AP02m_192-168-0-12_183.rpc')

print("="*80)
print("RPC FILE PARSING:")
print(f"Headers: {result.headers}")
print(f"Total headers: {len(result.headers)}")
print(f"Total rows: {len(result.rows)}")
print()

# Simulate UI display (remove PIC from body)
display_headers = [h for h in result.headers if h.upper() != 'PIC']
print("DISPLAY HEADERS (table columns):")
print(f"  Display headers: {display_headers}")
print(f"  Total: {len(display_headers)}")
print()

print("VERTICAL HEADERS (row labels):")
for i, row_data in enumerate(result.rows[:5]):
    # Test both uppercase and lowercase
    pic_value = row_data.get('PIC', '') or row_data.get('pic', '')
    print(f"  Row {i}: PIC = '{pic_value}'")
print()

print("="*80)
print("SAMPLE ROW DATA (PIC 0):")
pic0 = result.rows[0]
pic_value = pic0.get('PIC', '') or pic0.get('pic', '')
print(f"Vertical Header: PIC = '{pic_value}'")
print("Table Columns:")
for col_idx, header in enumerate(display_headers):
    value = pic0.get(header, '')
    print(f"  Col {col_idx}: {header} = '{value}'")
print()

print("Testing if any exception occurs during table creation simulation...")
try:
    # Simulate the exact code from _create_table_from_data
    vertical_labels = []
    for row_data in result.rows:
        pic_value = row_data.get('PIC', '') or row_data.get('pic', '')
        vertical_labels.append(str(pic_value))
    
    print(f"✓ Created {len(vertical_labels)} vertical labels")
    
    # Simulate cell population
    cell_count = 0
    for row_idx, row_data in enumerate(result.rows):
        for col_idx, header in enumerate(display_headers):
            value = row_data.get(header, '')
            item_text = str(value)
            cell_count += 1
    
    print(f"✓ Would create {cell_count} table cells")
    print("✓ No exceptions - table creation should work!")
    
except Exception as e:
    print(f"✗ EXCEPTION: {e}")
    import traceback
    traceback.print_exc()
