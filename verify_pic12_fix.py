"""Simple test to verify PIC 12 parsing is correct"""
import sys
sys.path.insert(0, 'src')

from commander.services.fbc_parser_service import FBCParserService

# Initialize parser  
parser = FBCParserService()

# Parse the file
result = parser.parse_file('_DIA/FBC/AP01/AP01_192-168-0-11_162.fbc')

# Find PIC 12
pic12 = None
for row in result.rows:
    if row.get('PIC') == '12':
        pic12 = row
        break

if pic12:
    print("✅ PIC 12 PARSING RESULTS:")
    print()
    print(f"Card  5: '{pic12.get('5', '')}' {'' if pic12.get('5') else '← EMPTY ✓'}")
    print(f"Card  6: '{pic12.get('6', '')}' {' ← BI8 ✓' if pic12.get('6') == 'BI8' else ''}")
    print(f"Card 19: '{pic12.get('19', '')}' {' ← TI6 ✓' if pic12.get('19') == 'TI6' else ''}")
    print(f"Card 20: '{pic12.get('20', '')}' {'' if pic12.get('20') else '← EMPTY ✓'}")
    print()
    
    # Verify
    all_correct = (
        not pic12.get('5') and  # Card 5 empty
        pic12.get('6') == 'BI8' and  # Card 6 is BI8
        pic12.get('19') == 'TI6' and  # Card 19 is TI6
        not pic12.get('20')  # Card 20 empty
    )
    
    if all_correct:
        print("🎉🎉🎉 ALL CHECKS PASSED! PIC 12 IS CORRECT! 🎉🎉🎉")
    else:
        print("❌ SOME CHECKS FAILED")
else:
    print("❌ PIC 12 NOT FOUND")
