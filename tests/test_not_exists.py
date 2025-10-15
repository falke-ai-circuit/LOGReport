"""Test parser with Not Exists rows and IBC format"""
import sys
sys.path.insert(0, 'd:/_APP/LOGReport/src')

from commander.services.fbc_parser_service import FbcParserService

parser = FbcParserService()

print("="*80)
print("TEST 1: AP02m_182.fbc (has 'Not Exists' rows 0-8)")
print("="*80)
result = parser.parse_file('_DIA/FBC/AP02m/AP02m_192-168-0-12_182.fbc')
print(f"Headers: {len(result.headers)} - {result.headers[:5]}...")
print(f"Rows: {len(result.rows)}")
print()

if len(result.rows) > 0:
    # Check PIC 0 (should be Not Exists)
    pic0 = result.rows[0]
    print(f"PIC 0: {pic0.get('PIC')}")
    print(f"  Card 5: '{pic0.get('5', 'MISSING')}' {'✓ N/E' if pic0.get('5') == 'N/E' else '❌'}")
    print(f"  Card 10: '{pic0.get('10', 'MISSING')}' {'✓ N/E' if pic0.get('10') == 'N/E' else '❌'}")
    print(f"  Sum: '{pic0.get('sum', 'MISSING')}' {'✓' if pic0.get('sum') == '0' else '❌'}")
    print()

if len(result.rows) > 9:
    # Check PIC 9 (first with data)
    pic9 = result.rows[9]
    print(f"PIC 9: {pic9.get('PIC')}")
    print(f"  Card 5: '{pic9.get('5', 'MISSING')}' {'✓ Empty' if pic9.get('5') == '' else ('✓ Has data' if pic9.get('5') else '❌')}")
    print(f"  Card 6: '{pic9.get('6', 'MISSING')}' {'✓' if pic9.get('6') else '❌'}")
    print(f"  Sum: '{pic9.get('sum', 'MISSING')}'")
    print()

print("="*80)
print("TEST 2: AP07m_222.fbc (IBC format with columns 0-15)")
print("="*80)
result2 = parser.parse_file('_DIA/FBC/AP07m/AP07m_192-168-0-17_222.fbc')
print(f"Headers: {len(result2.headers)} - {result2.headers}")
print(f"Rows: {len(result2.rows)}")
print()

if len(result2.rows) > 0:
    # Check IBC 0
    ibc0 = result2.rows[0]
    print(f"IBC 0: {ibc0.get('PIC', 'MISSING')}")
    print(f"  First 5 columns: {[ibc0.get(str(i), 'MISSING') for i in range(5)]}")
    print(f"  Sum: '{ibc0.get('sum', 'MISSING')}'")
    print()

if len(result2.rows) > 6:
    # Check IBC 6 (Not Exists)
    ibc6 = result2.rows[6]
    print(f"IBC 6: {ibc6.get('PIC', 'MISSING')}")
    print(f"  Column 0: '{ibc6.get('0', 'MISSING')}' {'✓ N/E' if ibc6.get('0') == 'N/E' else '❌'}")
    print(f"  Sum: '{ibc6.get('sum', 'MISSING')}'")
    print()

print("="*80)
print("SUMMARY")
print("="*80)
print(f"AP02m: {len(result.rows)}/16 rows {'✓ CORRECT' if len(result.rows) == 16 else '❌ WRONG'}")
print(f"AP07m: {len(result2.rows)}/16 rows {'✓ CORRECT' if len(result2.rows) == 16 else '❌ WRONG'}")
