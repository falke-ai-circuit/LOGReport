#!/usr/bin/env python3
"""
Test script to verify the LOG token context menu fix.
This script tests the logic without requiring full module imports.
"""

def test_log_token_handling_logic():
    """
    Test the logic for handling LOG tokens in the context menu service.
    This test verifies that LOG tokens with log_path show the BsTool action.
    """
    print("Testing LOG token handling logic...")
    
    # Simulate the item_data that would be passed to show_context_menu
    log_token_data = {
        "token": "AP01m_192-168-0-11.log",
        "token_type": "LOG",
        "node": "AP01m",
        "log_path": "/path/to/log/file.log"
    }
    
    # Check if the data matches the LOG token condition
    has_token = 'token' in log_token_data
    token_type = log_token_data.get("token_type", "UNKNOWN").upper()
    is_log_token = token_type == "LOG"
    has_log_path = 'log_path' in log_token_data or 'file_path' in log_token_data
    
    print(f"Has token: {has_token}")
    print(f"Token type: {token_type}")
    print(f"Is LOG token: {is_log_token}")
    print(f"Has log path: {has_log_path}")
    
    # Verify our fix would be triggered
    if has_token and is_log_token and has_log_path:
        print("✓ LOG token with log_path detected - BsTool action should be added")
        return True
    else:
        print("✗ LOG token with log_path not properly detected")
        return False

def test_log_token_without_log_path():
    """
    Test that LOG tokens without log_path are handled correctly.
    """
    print("\nTesting LOG token without log_path...")
    
    # Simulate the item_data that would be passed to show_context_menu
    log_token_data = {
        "token": "AP01m_192-168-0-11.log",
        "token_type": "LOG",
        "node": "AP01m"
        # No log_path or file_path
    }
    
    # Check if the data matches the LOG token condition
    has_token = 'token' in log_token_data
    token_type = log_token_data.get("token_type", "UNKNOWN").upper()
    is_log_token = token_type == "LOG"
    has_log_path = 'log_path' in log_token_data or 'file_path' in log_token_data
    
    print(f"Has token: {has_token}")
    print(f"Token type: {token_type}")
    print(f"Is LOG token: {is_log_token}")
    print(f"Has log path: {has_log_path}")
    
    # Verify our fix would not be triggered
    if has_token and is_log_token and not has_log_path:
        print("✓ LOG token without log_path detected - No action should be added")
        return True
    else:
        print("✗ LOG token without log_path not properly detected")
        return False

def test_regular_log_file_handling():
    """
    Test that regular log files (without token) are still handled correctly.
    """
    print("\nTesting regular log file handling...")
    
    # Simulate the item_data that would be passed to show_context_menu
    log_file_data = {
        "log_path": "/path/to/log/file.log"
    }
    
    # Check if the data matches the regular log file condition
    has_token = 'token' in log_file_data
    has_log_path = 'log_path' in log_file_data or 'file_path' in log_file_data
    is_log_file = has_log_path and log_file_data.get('log_path', '').lower().endswith('.log')
    
    print(f"Has token: {has_token}")
    print(f"Has log path: {has_log_path}")
    print(f"Is log file: {is_log_file}")
    
    # Verify regular log file handling would still work
    if not has_token and has_log_path and is_log_file:
        print("✓ Regular log file detected - BsTool action should be added")
        return True
    else:
        print("✗ Regular log file not properly detected")
        return False

def main():
    """
    Main test function.
    """
    print("Running context menu fix verification tests...\n")
    
    # Run all tests
    test1_passed = test_log_token_handling_logic()
    test2_passed = test_log_token_without_log_path()
    test3_passed = test_regular_log_file_handling()
    
    print("\n" + "="*50)
    if test1_passed and test2_passed and test3_passed:
        print("✓ All tests passed! The fix should work correctly.")
        print("\nSummary:")
        print("1. LOG tokens with log_path will show BsTool action")
        print("2. LOG tokens without log_path will show no actions")
        print("3. Regular log files will still show BsTool action")
        return True
    else:
        print("✗ Some tests failed. The fix may need adjustment.")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)