"""Test table column creation"""
import sys
sys.path.insert(0, 'd:/_APP/LOGReport/src')

from commander.services.fbc_parser_service import FbcParserService

# Parse the file
parser = FbcParserService()
result = parser.parse_file(r'd:\_APP\LOGReport\_DIA\FBC\AP01\AP01_192-168-0-11_162.fbc')

print(f"Total headers (including PIC): {len(result.headers)}")
print(f"Headers: {result.headers}")
print()

# Display headers (excluding PIC)
display_headers = [h for h in result.headers if h.upper() != 'PIC']
print(f"Display headers (no PIC): {len(display_headers)}")
print(f"Display headers: {display_headers}")
print()

print("Expected: 17 columns (5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, sum)")
print(f"Actual: {len(display_headers)} columns")
print()

# Verify PIC values for vertical headers
print("Vertical header labels (PIC values):")
for row_data in result.rows:
    pic_value = row_data.get('PIC', '') or row_data.get('pic', '')
    print(f"  {pic_value}")
