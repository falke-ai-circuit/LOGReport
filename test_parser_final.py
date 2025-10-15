"""Test FBC parser with fixed regex"""
import sys
sys.path.insert(0, 'd:/_APP/LOGReport/src')

from commander.services.fbc_parser_service import FbcParserService

# Test the parser with actual file
parser = FbcParserService()
result = parser.parse_file(r'd:\_APP\LOGReport\_DIA\FBC\AP01\AP01_192-168-0-11_162.fbc')

print(f"Headers: {result.headers}")
print(f"Total headers: {len(result.headers)}")
print()

# Check specific problematic rows
print("="*80)
print("PIC 0 (should have all values including empty column 20):")
pic0 = result.rows[0]
print(f"PIC: {pic0['PIC']}")
for col in result.headers[1:-1]:  # Skip PIC and sum
    value = pic0.get(col, 'MISSING')
    marker = "✓" if value else "✗ EMPTY"
    print(f"  Col {col}: '{value}' {marker}")
print(f"Sum: {pic0['sum']}")
print()

print("="*80)
print("PIC 1 (should have BI8N at column 15):")
pic1 = result.rows[1]
print(f"PIC: {pic1['PIC']}")
for col in result.headers[1:-1]:
    value = pic1.get(col, 'MISSING')
    marker = "✓ BI8N" if value == 'BI8N' else ("✓" if value else "✗ EMPTY")
    print(f"  Col {col}: '{value}' {marker}")
print(f"Sum: {pic1['sum']}")
print()

print("="*80)
print("PIC 11 (should have empty column 7, BI8N at column 14):")
pic11 = result.rows[11]
print(f"PIC: {pic11['PIC']}")
for col in result.headers[1:-1]:
    value = pic11.get(col, 'MISSING')
    marker = "✗ EMPTY" if not value else ("✓ BI8N" if value == 'BI8N' else "✓")
    print(f"  Col {col}: '{value}' {marker}")
print(f"Sum: {pic11['sum']}")
