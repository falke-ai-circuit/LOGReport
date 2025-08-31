import os
import sys
import logging
from src.commander.node_manager import NodeManager

# Setup logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('debug_token_test.log'),
        logging.StreamHandler()
    ]
)

def test_ap01m_token_detection():
    """Test token detection for AP01m node"""
    print("\n=== Starting AP01m Token Detection Test ===")
    
    # Initialize node manager
    manager = NodeManager()
    
    # Set log root to test_logs directory
    log_root = os.path.join(os.getcwd(), "test_logs")
    print(f"Setting log root to: {log_root}")
    manager.set_log_root(log_root)
    
    # Get AP01m node
    node = manager.get_node("AP01m")
    if not node:
        print("Error: AP01m node not found")
        return
        
    # Print all tokens for AP01m
    print("\nAll tokens for AP01m:")
    for token_id, token in node.tokens.items():
        print(f"Token ID: {token_id}, Type: {token.token_type}, Path: {token.log_path}")
    
    # Check for FBC tokens 162, 163, 164
    expected_fbc = {'162', '163', '164'}
    detected_fbc = {t.token_id for t in node.tokens.values() if t.token_type == 'FBC'}
    
    print("\nTest Results:")
    print(f"Expected FBC tokens: {expected_fbc}")
    print(f"Detected FBC tokens: {detected_fbc}")
    
    missing = expected_fbc - detected_fbc
    extra = detected_fbc - expected_fbc
    
    if not missing and not extra:
        print("SUCCESS: All expected FBC tokens detected")
    else:
        if missing:
            print(f"FAIL: Missing FBC tokens: {missing}")
        if extra:
            print(f"FAIL: Unexpected FBC tokens: {extra}")

if __name__ == "__main__":
    test_ap01m_token_detection()
    print("\n=== Test Complete ===")
    print("Check 'debug_token_test.log' for detailed debug output")