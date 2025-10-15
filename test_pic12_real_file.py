"""Test PIC 12 parsing with real file"""
from pathlib import Path
from src.commander.services.fbc_parser_service import FBCParserService

# Initialize parser
parser = FBCParserService()

# Parse the AP01_162.fbc file
file_path = Path("_DIA/FBC/AP01_162.fbc")
if not file_path.exists():
    print(f"ERROR: File not found: {file_path}")
    exit(1)

print("="*80)
print(f"Parsing: {file_path}")
print()

# Parse file
result = parser.parse_file(str(file_path))

print(f"Headers: {result.headers}")
print(f"Number of rows: {len(result.rows)}")
print()

# Find PIC 12 row
pic12_row = None
for row in result.rows:
    if row.get('PIC') == '12':
        pic12_row = row
        break

if pic12_row:
    print("="*80)
    print("PIC 12 DATA (should have EMPTY at card 5, then BI8 BI8...TI6 TI6):")
    print("="*80)
    
    # Print card values
    for card_num in ['5', '6', '7', '8', '9', '10', '11', '12', '13', '14', '15', '16', '17', '18', '19', '20']:
        value = pic12_row.get(card_num, '?')
        status = "✓" if value else "✗ EMPTY"
        if not value:
            print(f"  Card {card_num:>2}: {'':<8} {status}")
        else:
            print(f"  Card {card_num:>2}: {value:<8} {status}")
    
    print(f"  Sum: {pic12_row.get('sum', '?')}")
    print()
    
    # Verify expectations
    print("VERIFICATION:")
    errors = []
    
    if pic12_row.get('5'):
        errors.append("  ❌ Card 5 should be EMPTY but has value")
    else:
        print("  ✅ Card 5 is EMPTY (correct)")
    
    if pic12_row.get('6') == 'BI8':
        print("  ✅ Card 6 is BI8 (correct)")
    else:
        errors.append(f"  ❌ Card 6 should be BI8 but is '{pic12_row.get('6')}'")
    
    if pic12_row.get('19') == 'TI6':
        print("  ✅ Card 19 is TI6 (correct)")
    else:
        errors.append(f"  ❌ Card 19 should be TI6 but is '{pic12_row.get('19')}'")
    
    if not pic12_row.get('20'):
        print("  ✅ Card 20 is EMPTY (correct)")
    else:
        errors.append(f"  ❌ Card 20 should be EMPTY but is '{pic12_row.get('20')}'")
    
    if errors:
        print()
        print("ERRORS FOUND:")
        for error in errors:
            print(error)
    else:
        print()
        print("🎉 ALL CHECKS PASSED! PIC 12 parsing is CORRECT!")
else:
    print("ERROR: PIC 12 not found in parsed data")
