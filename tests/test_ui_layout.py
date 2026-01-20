"""Test UI table layout - PIC as vertical headers"""
import sys
sys.path.insert(0, 'd:/_APP/LOGReport/src')

from commander.services.fbc_parser_service import FbcParserService

# Test the parser
parser = FbcParserService()
result = parser.parse_file(r'd:\_APP\LOGReport\_DIA\FBC\AP01\AP01_192-168-0-11_162.fbc')

print("="*80)
print("FILE HEADERS:")
print(f"  All headers: {result.headers}")
print(f"  Total: {len(result.headers)}")
print()

# Simulate UI display (remove PIC from body)
display_headers = [h for h in result.headers if h.upper() != 'PIC']
print("DISPLAY HEADERS (table columns):")
print(f"  Display headers: {display_headers}")
print(f"  Total: {len(display_headers)}")
print()

print("VERTICAL HEADERS (row labels):")
for i, row_data in enumerate(result.rows[:5]):  # Show first 5
    pic_value = row_data.get('PIC', '')
    print(f"  Row {i}: PIC = {pic_value}")
print()

print("="*80)
print("SAMPLE ROW DATA (PIC 0):")
pic0 = result.rows[0]
print(f"Vertical Header: PIC = {pic0['PIC']}")
print("Table Columns:")
for col_idx, header in enumerate(display_headers):
    value = pic0.get(header, '')
    marker = "✓" if value else "EMPTY"
    print(f"  Col {col_idx}: {header} = '{value}' {marker}")
print()

print("="*80)
print("SAMPLE ROW DATA (PIC 11):")
pic11 = result.rows[11]
print(f"Vertical Header: PIC = {pic11['PIC']}")
print("Table Columns:")
for col_idx, header in enumerate(display_headers):
    value = pic11.get(header, '')
    if header == '7':
        marker = "✓ EMPTY (FIXED)" if not value else "✗ SHOULD BE EMPTY"
    elif header == '14':
        marker = "✓ BI8N (FIXED)" if value == 'BI8N' else f"✗ WRONG: {value}"
    else:
        marker = "✓" if value else "EMPTY"
    print(f"  Col {col_idx}: {header} = '{value}' {marker}")
