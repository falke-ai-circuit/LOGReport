"""Debug table creation issue"""
import sys
sys.path.insert(0, 'd:/_APP/LOGReport/src')

from commander.services.fbc_parser_service import FbcParserService

# Test the parser with actual file
parser = FbcParserService()
result = parser.parse_file(r'd:\_APP\LOGReport\_DIA\FBC\AP01\AP01_192-168-0-11_162.fbc')

print(f"Headers: {result.headers}")
print(f"Total headers: {len(result.headers)}")
print(f"Total rows: {len(result.rows)}")
print()

# Check what display_headers would be (after removing PIC)
display_headers = [h for h in result.headers if h.upper() != 'PIC']
print(f"Display headers (PIC removed): {display_headers}")
print(f"Total display columns: {len(display_headers)}")
print()

# Check first 3 rows structure
for i in range(min(3, len(result.rows))):
    row = result.rows[i]
    print(f"Row {i} - PIC: {row.get('PIC', 'MISSING')}")
    print(f"  Keys: {list(row.keys())}")
    print(f"  Values sample: {dict(list(row.items())[:5])}")
    print()

# Check if row data matches display_headers
print("="*80)
print("Checking if all display_headers exist in row data:")
test_row = result.rows[0]
for header in display_headers:
    exists = header in test_row
    value = test_row.get(header, 'MISSING')
    print(f"  '{header}': exists={exists}, value='{value}'")
