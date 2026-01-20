"""
Debug script to test what environment variables and paths are available in Nuitka builds
"""
import sys
import os

print("="*80)
print("ENVIRONMENT DETECTION")
print("="*80)
print(f"sys.frozen: {getattr(sys, 'frozen', False)}")
print(f"hasattr(sys, '_MEIPASS'): {hasattr(sys, '_MEIPASS')}")
if hasattr(sys, '_MEIPASS'):
    print(f"sys._MEIPASS: {sys._MEIPASS}")
print(f"sys.executable: {sys.executable}")
print(f"os.path.dirname(sys.executable): {os.path.dirname(sys.executable)}")
print(f"__file__: {__file__}")
print(f"os.path.dirname(__file__): {os.path.dirname(__file__)}")

print("\n" + "="*80)
print("NUITKA-SPECIFIC ATTRIBUTES")
print("="*80)
# Nuitka-specific detection
print(f"'__compiled__' in dir(): {('__compiled__' in dir())}")
print(f"hasattr(sys, '__compiled__'): {hasattr(sys, '__compiled__')}")

# Check all sys attributes
print("\nAll sys attributes containing 'compiled' or 'nuitka':")
for attr in dir(sys):
    if 'compiled' in attr.lower() or 'nuitka' in attr.lower():
        print(f"  sys.{attr}: {getattr(sys, attr, 'N/A')}")

print("\n" + "="*80)
print("LOOKING FOR BsTool.exe")
print("="*80)

# Check common locations
locations = [
    os.path.dirname(sys.executable),
    os.path.join(os.path.dirname(sys.executable), "BsTool.exe"),
    os.getcwd(),
    os.path.join(os.getcwd(), "BsTool.exe"),
]

if hasattr(sys, '_MEIPASS'):
    locations.extend([
        sys._MEIPASS,
        os.path.join(sys._MEIPASS, "BsTool.exe"),
    ])

for loc in locations:
    exists = os.path.exists(loc) if loc else False
    print(f"{loc}: {'EXISTS' if exists else 'NOT FOUND'}")

# List files in executable directory
exe_dir = os.path.dirname(sys.executable)
print(f"\nFiles in {exe_dir}:")
try:
    files = os.listdir(exe_dir)
    bstool_files = [f for f in files if 'bstool' in f.lower()]
    if bstool_files:
        print(f"  BsTool-related: {bstool_files}")
    else:
        print(f"  No BsTool files found")
        print(f"  Total files: {len(files)}")
        # Show first 20 files
        for f in files[:20]:
            print(f"    {f}")
except Exception as e:
    print(f"  Error listing directory: {e}")
