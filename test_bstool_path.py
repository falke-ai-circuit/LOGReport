"""
Test script to verify BsTool path resolution in different environments.
Run this script to diagnose BsTool.exe path detection issues.
"""

import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from commander.utils.bstool_path_resolver import get_bstool_path, validate_bstool_path

def main():
    print("="*80)
    print("BsTool Path Resolution Diagnostic")
    print("="*80)
    print()
    
    # Check execution environment
    print("Environment Information:")
    print(f"  sys.frozen: {getattr(sys, 'frozen', False)}")
    print(f"  sys._MEIPASS exists: {hasattr(sys, '_MEIPASS')}")
    if hasattr(sys, '_MEIPASS'):
        print(f"  sys._MEIPASS value: {sys._MEIPASS}")
        
        # Check for BsTool.exe in various locations relative to _MEIPASS
        print(f"\n  Checking BsTool.exe locations relative to _MEIPASS:")
        
        # Direct in _MEIPASS
        path1 = os.path.join(sys._MEIPASS, "BsTool.exe")
        print(f"    {path1}: {os.path.exists(path1)}")
        
        # In _MEIPASS\LOGReporter subfolder
        path2 = os.path.join(sys._MEIPASS, "LOGReporter", "BsTool.exe")
        print(f"    {path2}: {os.path.exists(path2)}")
        
        # In parent of _MEIPASS
        parent = os.path.dirname(sys._MEIPASS)
        path3 = os.path.join(parent, "BsTool.exe")
        print(f"    {path3}: {os.path.exists(path3)}")
        
        # In parent\LOGReporter
        path4 = os.path.join(parent, "LOGReporter", "BsTool.exe")
        print(f"    {path4}: {os.path.exists(path4)}")
        
    print(f"  sys.executable: {sys.executable}")
    print(f"  __file__: {__file__}")
    print(f"  Current working directory: {os.getcwd()}")
    print()
    
    # Test path resolution
    print("Path Resolution:")
    bstool_path = get_bstool_path()
    print(f"  get_bstool_path() returned: {bstool_path}")
    print()
    
    # Validate path
    print("Path Validation:")
    if bstool_path:
        is_valid = validate_bstool_path(bstool_path)
        print(f"  validate_bstool_path(): {is_valid}")
        print(f"  os.path.exists(): {os.path.exists(bstool_path)}")
        print(f"  os.path.isfile(): {os.path.isfile(bstool_path)}")
        
        # Check parent directory contents
        parent_dir = os.path.dirname(bstool_path)
        print(f"\n  Parent directory: {parent_dir}")
        if os.path.exists(parent_dir):
            print(f"  Contents of parent directory:")
            try:
                contents = os.listdir(parent_dir)
                # Filter to show only .exe files and first 20 entries
                exe_files = [f for f in contents if f.lower().endswith('.exe')]
                other_files = [f for f in contents if not f.lower().endswith('.exe')][:10]
                
                print(f"    Executable files ({len(exe_files)}):")
                for f in exe_files:
                    print(f"      - {f}")
                
                if other_files:
                    print(f"    Other files (showing first 10 of {len([f for f in contents if not f.lower().endswith('.exe')])}):")
                    for f in other_files:
                        print(f"      - {f}")
            except Exception as e:
                print(f"    Error listing directory: {e}")
    else:
        print("  Path is empty - BsTool.exe not found!")
        
        # Try to help diagnose
        print("\n  Diagnostic suggestions:")
        
        if getattr(sys, 'frozen', False):
            print("    Running in frozen/bundled mode")
            if hasattr(sys, '_MEIPASS'):
                print(f"    Check if BsTool.exe exists in: {sys._MEIPASS}")
                print(f"    Contents of _MEIPASS:")
                try:
                    contents = os.listdir(sys._MEIPASS)
                    exe_files = [f for f in contents if f.lower().endswith('.exe')]
                    print(f"      Executable files found: {exe_files}")
                except Exception as e:
                    print(f"      Error listing _MEIPASS: {e}")
            
            exe_dir = os.path.dirname(sys.executable)
            print(f"    Check if BsTool.exe exists in: {exe_dir}")
            print(f"    Contents of executable directory:")
            try:
                contents = os.listdir(exe_dir)
                exe_files = [f for f in contents if f.lower().endswith('.exe')]
                print(f"      Executable files found: {exe_files}")
            except Exception as e:
                print(f"      Error listing executable directory: {e}")
        else:
            print("    Running in development mode")
            # Calculate project root (script is in root, src is one level down)
            project_root = os.path.dirname(os.path.abspath(__file__))
            expected_path = os.path.join(project_root, "BsTool.exe")
            print(f"    Expected location: {expected_path}")
            print(f"    Exists: {os.path.exists(expected_path)}")
    
    print()
    print("="*80)

if __name__ == "__main__":
    main()
