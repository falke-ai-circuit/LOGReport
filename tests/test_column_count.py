"""Test that parser creates all 16 columns even when some are empty"""
import sys
sys.path.insert(0, 'd:/_APP/LOGReport/src')

from commander.services.fbc_parser_service import FbcParserService

parser = FbcParserService()
result = parser.parse_file(r'd:\_APP\LOGReport\_DIA\FBC\AP01\AP01_192-168-0-11_162.fbc')

print(f'Headers ({len(result.headers)}): {result.headers}')
print()

# Check PIC 0
pic0 = result.rows[0]
data_columns = [k for k in pic0.keys() if k not in ['PIC', 'sum']]
print(f'PIC 0 data columns ({len(data_columns)}): {data_columns}')
print()

# Check each column 5-20
print("PIC 0 column values:")
for col in ['5', '6', '7', '8', '9', '10', '11', '12', '13', '14', '15', '16', '17', '18', '19', '20']:
    value = pic0.get(col, 'MISSING')
    marker = "✓" if value else ("✗ EMPTY" if col in pic0 else "✗✗ MISSING KEY")
    print(f"  Col {col}: '{value}' {marker}")
print(f"  Sum: {pic0['sum']}")
