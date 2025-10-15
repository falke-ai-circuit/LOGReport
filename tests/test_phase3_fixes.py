"""
Phase 3 Final Fixes - Verification Test
Tests FIX 1, FIX 2, FIX 3
"""
import sys
sys.path.insert(0, 'D:\\_APP\\LOGReport\\src')

def test_fix1_autoload():
    """FIX 1: Verify auto-load is enabled"""
    print("\n=== FIX 1: Auto-load Selected File ===")
    
    with open('d:\\_APP\\LOGReport\\src\\commander\\ui\\node_scan_widget.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check that auto-load is enabled (not commented out)
    if 'QTimer.singleShot(100, self._load_most_recent_file)' in content:
        print("✅ Auto-load enabled with 100ms delay")
    else:
        print("❌ Auto-load NOT found or still commented")
    
    # Check that old disabled code is removed
    if '# DISABLED: Auto-load causes crash' in content:
        print("❌ Old disabled comment still present")
    else:
        print("✅ Old disabled comment removed")


def test_fix2_tab_switch():
    """FIX 2: Verify tab switch prevention logic exists"""
    print("\n=== FIX 2: Prevent Tab Switch ===")
    
    with open('d:\\_APP\\LOGReport\\src\\commander\\ui\\commander_window.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check for Scan tab check
    if 'if current_tab == scan_tab:' in content:
        print("✅ Scan tab check found in _handle_command_generated()")
    else:
        print("❌ Scan tab check NOT found")
    
    # Check for select_file_only call
    if 'scan_tab.select_file_only(file_path)' in content:
        print("✅ select_file_only() call found")
    else:
        print("❌ select_file_only() call NOT found")
    
    # Check Qt import
    if 'from PyQt5.QtCore import QSettings, pyqtSignal, Qt' in content:
        print("✅ Qt import added for ItemDataRole")
    else:
        print("❌ Qt import missing")


def test_fix2_select_file_only_method():
    """FIX 2: Verify select_file_only method exists"""
    print("\n=== FIX 2: select_file_only Method ===")
    
    with open('d:\\_APP\\LOGReport\\src\\commander\\ui\\node_scan_widget.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    if 'def select_file_only(self, file_path: str) -> bool:' in content:
        print("✅ select_file_only() method defined")
    else:
        print("❌ select_file_only() method NOT found")
    
    # Check method doesn't call comparison
    if 'Select file from dropdown WITHOUT triggering comparison' in content:
        print("✅ Method documented as 'without comparison'")
    else:
        print("❌ Method documentation missing")


def test_fix3_pic0_skip():
    """FIX 3: Verify PIC 0 skip logic exists"""
    print("\n=== FIX 3: PIC 0 Comparison Skip ===")
    
    with open('d:\\_APP\\LOGReport\\src\\commander\\services\\fbc_comparison_service.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check for PIC 0 check
    if "if file_pic_normalized == '0':" in content:
        print("✅ PIC 0 check found")
    else:
        print("❌ PIC 0 check NOT found")
    
    # Check for skip log message
    if 'Skipping PIC 0 comparison (not reported by telnet)' in content:
        print("✅ Skip log message found")
    else:
        print("❌ Skip log message NOT found")
    
    # Check for continue statement (skip comparison)
    lines = content.split('\n')
    found_pic0_continue = False
    for i, line in enumerate(lines):
        if "if file_pic_normalized == '0':" in line:
            # Check next 3 lines for continue
            for j in range(i, min(i+5, len(lines))):
                if 'continue' in lines[j] and '#' not in lines[j].split('continue')[0]:
                    found_pic0_continue = True
                    break
    
    if found_pic0_continue:
        print("✅ Continue statement found (skips PIC 0 comparison)")
    else:
        print("❌ Continue statement NOT found")


def test_all_fixes():
    """Run all fix verification tests"""
    print("="*60)
    print("PHASE 3 FINAL FIXES - VERIFICATION")
    print("="*60)
    
    test_fix1_autoload()
    test_fix2_tab_switch()
    test_fix2_select_file_only_method()
    test_fix3_pic0_skip()
    
    print("\n" + "="*60)
    print("VERIFICATION COMPLETE")
    print("="*60)


if __name__ == '__main__':
    test_all_fixes()
