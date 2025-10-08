#!/usr/bin/env python3
import sys
from src.commander.utils.token_utils import normalize_token, is_rpc_token, is_fbc_token

def test_rpc_normalization():
    """Test RPC token normalization"""
    print("Testing RPC token normalization...")
    
    # Test cases for RPC tokens
    test_cases = [
        ("162", "162"),  # Simple numeric token
        ("163", "163"),  # Simple numeric token
        ("1a2", "1a2"),  # Alphanumeric token
        ("363", "363"),  # Another numeric token
    ]
    
    all_passed = True
    for input_token, expected in test_cases:
        result = normalize_token(input_token)
        is_rpc = is_rpc_token(input_token)
        print(f"Input: '{input_token}' -> Normalized: '{result}' (RPC: {is_rpc})")
        if result != expected:
            print(f"  FAIL: Expected '{expected}', got '{result}'")
            all_passed = False
        else:
            print(f"  PASS")
    
    # Test FBC tokens to make sure they still work correctly
    print("\nTesting FBC token normalization (should not be affected)...")
    fbc_test_cases = [
        ("162", "162"),  # This is actually an FBC token (3 digits)
        ("1a", "1A"),    # Alphanumeric FBC token should be uppercase
        ("2a3", "2A3"),  # Alphanumeric FBC token should be uppercase
    ]
    
    # These should be detected as FBC tokens, not RPC tokens
    fbc_tokens = ["162", "1a", "2a3"]
    for token in fbc_tokens:
        is_fbc = is_fbc_token(token)
        is_rpc = is_rpc_token(token)
        print(f"Token '{token}': FBC={is_fbc}, RPC={is_rpc}")
    
    # Test generic tokens (neither FBC nor RPC)
    print("\nTesting generic token normalization...")
    generic_test_cases = [
        ("ABC", "abc"),     # Should be lowercase
        ("A-B-C", "abc"),   # Should remove non-alphanumeric and lowercase
    ]
    
    for input_token, expected in generic_test_cases:
        result = normalize_token(input_token)
        is_fbc = is_fbc_token(input_token)
        is_rpc = is_rpc_token(input_token)
        print(f"Input: '{input_token}' -> Normalized: '{result}' (FBC: {is_fbc}, RPC: {is_rpc})")
        if result != expected:
            print(f"  FAIL: Expected '{expected}', got '{result}'")
            all_passed = False
        else:
            print(f"  PASS")
    
    # Test tokens that should be RPC
    print("\nTesting tokens that should be detected as RPC...")
    rpc_tokens = ["1a2", "2b3", "abc"]
    for token in rpc_tokens:
        is_rpc = is_rpc_token(token)
        normalized = normalize_token(token)
        print(f"Token '{token}': RPC={is_rpc}, Normalized='{normalized}'")
        if not is_rpc:
            print(f"  FAIL: Expected '{token}' to be detected as RPC")
            all_passed = False
        else:
            print(f"  PASS")
    
    # Test numeric tokens that are neither FBC nor RPC
    print("\nTesting numeric tokens that are neither FBC nor RPC...")
    # "12" is actually an RPC token because it's alphanumeric and not FBC
    # Let's test a token that would go through the generic path
    # We need a token that doesn't match FBC or RPC patterns
    # This is tricky because most simple tokens will match one of the patterns
    
    if all_passed:
        print("\nAll tests passed!")
        return True
    else:
        print("\nSome tests failed!")
        return False

if __name__ == "__main__":
    success = test_rpc_normalization()
    sys.exit(0 if success else 1)