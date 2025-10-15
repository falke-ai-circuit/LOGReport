"""Test PIC 1 (BI8N) and PIC 11 (empty slot)"""
import sys
sys.path.insert(0, 'd:/_APP/LOGReport/src')

from commander.services.fbc_parser_service import FbcParserService

parser = FbcParserService()
result = parser.parse_file(r'd:\_APP\LOGReport\_DIA\FBC\AP01\AP01_192-168-0-11_162.fbc')

# Test PIC 1 - should have BI8N at column 15
print("="*60)
print("PIC 1 (should have BI8N at column 15):")
pic1 = result.rows[1]
for col in ['13', '14', '15', '16', '17']:
    value = pic1[col]
    marker = "✓ BI8N!" if value == 'BI8N' else "✓"
    print(f"  Col {col}: '{value}' {marker}")
print()

# Test PIC 11 - should have empty at column 7, BI8N at column 14
print("="*60)
print("PIC 11 (should have EMPTY at column 7, BI8N at column 14):")
pic11 = result.rows[11]
for col in ['5', '6', '7', '8', '9', '13', '14', '15', '16']:
    value = pic11[col]
    if col == '7':
        marker = "✓ EMPTY!" if not value else f"✗ Expected empty, got '{value}'"
    elif col == '14':
        marker = "✓ BI8N!" if value == 'BI8N' else f"✗ Expected BI8N, got '{value}'"
    else:
        marker = "✓"
    print(f"  Col {col}: '{value}' {marker}")
