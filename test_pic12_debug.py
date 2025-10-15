"""Debug PIC 12 empty slot parsing"""
import sys
sys.path.insert(0, 'd:/_APP/LOGReport/src')

from commander.services.fbc_parser_service import FbcParserService

# Test the parser with actual file
parser = FbcParserService()
result = parser.parse_file(r'd:\_APP\LOGReport\_DIA\FBC\AP01\AP01_192-168-0-11_162.fbc')

print("="*80)
print("PIC 12 (should have EMPTY at card 5, then BI8 BI8 BI8... TI6 TI6 at cards 6-20):")
pic12 = result.rows[12]
print(f"PIC: {pic12['PIC']}")
print(f"Row keys: {list(pic12.keys())}")
print()

# Check each column
for col in result.headers[1:-1]:  # Skip PIC and sum
    value = pic12.get(col, 'MISSING')
    marker = "✗ EMPTY" if not value else f"✓ {value}"
    print(f"  Card {col:>2}: '{value:6}' {marker}")
print(f"Sum: {pic12['sum']}")
print()

# Check raw line from file
print("="*80)
print("Raw line from file (line 21):")
with open(r'd:\_APP\LOGReport\_DIA\FBC\AP01\AP01_192-168-0-11_162.fbc', 'r') as f:
    lines = f.readlines()
    print(repr(lines[20]))  # Line 21 (0-indexed)
    print(f"Visual: {lines[20]}")
