"""Verify all FBC/RPC files parse correctly"""
import sys
sys.path.insert(0, 'd:/_APP/LOGReport/src')

from pathlib import Path
from commander.services.fbc_parser_service import FbcParserService

# Initialize parser
parser = FbcParserService()

# Find all FBC and RPC files
fbc_dir = Path('_DIA/FBC')
rpc_dir = Path('_DIA/RPC')

all_files = []
if fbc_dir.exists():
    all_files.extend(sorted(fbc_dir.rglob('*.fbc')))
if rpc_dir.exists():
    all_files.extend(sorted(rpc_dir.rglob('*.rpc')))

print(f"Found {len(all_files)} files to check")
print("="*80)

issues = []

for file_path in all_files:
    node_name = file_path.parts[-2] if len(file_path.parts) > 1 else 'Unknown'
    file_type = 'FBC' if file_path.suffix == '.fbc' else 'RPC'
    
    try:
        result = parser.parse_file(str(file_path))
        
        # Check if parsing succeeded
        if not result.headers or not result.rows:
            issue = f"❌ {node_name}/{file_path.name}: NO DATA (headers={len(result.headers)}, rows={len(result.rows)})"
            issues.append(issue)
            print(issue)
            continue
        
        # Check expected structure
        if file_type == 'FBC':
            # FBC should have 18 headers: PIC + cards 5-20 + sum
            expected_headers = 18
            if len(result.headers) != expected_headers:
                issue = f"❌ {node_name}/{file_path.name}: WRONG HEADER COUNT (got {len(result.headers)}, expected {expected_headers})"
                issues.append(issue)
                print(issue)
                continue
            
            # Check for 16 PICs (0-15)
            if len(result.rows) != 16:
                issue = f"⚠️  {node_name}/{file_path.name}: UNEXPECTED ROW COUNT (got {len(result.rows)} rows, expected 16)"
                issues.append(issue)
                print(issue)
                continue
        
        elif file_type == 'RPC':
            # RPC should have 6 headers: pic + 5 error columns
            expected_headers = 6
            if len(result.headers) != expected_headers:
                issue = f"❌ {node_name}/{file_path.name}: WRONG HEADER COUNT (got {len(result.headers)}, expected {expected_headers})"
                issues.append(issue)
                print(issue)
                continue
        
        print(f"✅ {node_name}/{file_path.name}: OK (headers={len(result.headers)}, rows={len(result.rows)})")
        
    except Exception as e:
        issue = f"❌ {node_name}/{file_path.name}: EXCEPTION - {e}"
        issues.append(issue)
        print(issue)

print()
print("="*80)
if issues:
    print(f"⚠️  FOUND {len(issues)} ISSUES:")
    for issue in issues:
        print(f"  {issue}")
else:
    print("✅ ALL FILES PARSED SUCCESSFULLY!")
