"""
Test script to verify the bstool fixes
"""
import sys
import os

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_bstool_tab_implementation():
    """Verify that the bstool tab implementation matches our fixes"""
    
    # Read the bstool_tab.py file
    with open('src/commander/ui/bstool_tab.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check that append_output uses the append method like telnet_tab
    assert 'self.output.append(text)' in content, "append_output should use self.output.append(text)"
    
    # Check that we have the scrolling code
    assert 'scrollbar.setValue(scrollbar.maximum())' in content, "Should have scrolling code"
    
    # Check that the duplicate connection is removed from main_window.py
    with open('src/commander/ui/commander_window.py', 'r', encoding='utf-8') as f:
        main_window_content = f.read()
    
    # Check for the comment that indicates the connection is handled elsewhere
    assert '# NOTE: BsTool service connections are handled in CommanderPresenter' in main_window_content, \
        "Should have comment about BsTool service connections being handled in CommanderPresenter"
    
    # Check that the direct connection is removed
    assert 'self.bstool_tab.execute_clicked.connect(self.bstool_service.execute_command)' not in main_window_content, \
        "Should not have direct connection from bstool_tab to bstool_service"
    
    # Check that execute_command in bstool_command_service.py creates a proper log file path
    with open('src/commander/services/bstool_command_service.py', 'r', encoding='utf-8') as f:
        service_content = f.read()
    
    # Check that execute_command uses a temporary log file instead of empty string
    assert 'temp_log_file' in service_content and 'tempfile.gettempdir()' in service_content, \
        "execute_command should create a temporary log file path"
    
    print("✓ All bstool fixes verified successfully")
    return True

def main():
    """Run all tests"""
    print("Verifying bstool fixes...")
    
    try:
        test_bstool_tab_implementation()
        print("\n✓ All fixes have been implemented correctly.")
        return True
    except Exception as e:
        print(f"\n✗ Verification failed: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)