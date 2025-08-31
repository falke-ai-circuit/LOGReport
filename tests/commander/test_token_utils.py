import os
import sys
import pytest

# Add src directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'src')))

from commander.utils.token_utils import normalize_token, validate_token, is_fbc_token, is_rpc_token

def test_normalize_token_preserves_case():
    """Test that normalize_token preserves original case for non-FBC tokens"""
    # Test non-FBC tokens preserve case
    assert normalize_token("TestToken") == "TestToken"
    assert normalize_token("testtoken") == "testtoken"
    assert normalize_token("TESTTOKEN") == "TESTTOKEN"
    
    # Test FBC tokens with digits are padded but case is preserved
    assert normalize_token("1") == "001"
    assert normalize_token("12") == "012"
    assert normalize_token("123") == "123"
    
    # Test FBC tokens with alphanumeric preserve case
    assert normalize_token("1a") == "1a"
    assert normalize_token("12b") == "12b"
    assert normalize_token("123c") == "123c"

def test_normalize_token_strips_whitespace():
    """Test that normalize_token strips whitespace"""
    assert normalize_token("  test  ") == "test"
    assert normalize_token("\ttest\n") == "test"
    assert normalize_token("  123  ") == "123"

def test_normalize_token_removes_special_chars():
    """Test that normalize_token removes special characters for non-FBC tokens"""
    assert normalize_token("test-token") == "testtoken"
    assert normalize_token("test_token") == "testtoken"
    assert normalize_token("test.token") == "testtoken"
    assert normalize_token("test@token") == "testtoken"

def test_is_fbc_token_case_insensitive():
    """Test that is_fbc_token works with different cases"""
    # Valid FBC tokens
    assert is_fbc_token("123")
    assert is_fbc_token("123a")
    assert is_fbc_token("001")
    assert is_fbc_token("012b")
    
    # Invalid FBC tokens
    assert not is_fbc_token("test")
    assert not is_fbc_token("1234")
    assert not is_fbc_token("12a3")

def test_is_rpc_token_case_insensitive():
    """Test that is_rpc_token works with different cases"""
    # Valid RPC tokens
    assert is_rpc_token("test")
    assert is_rpc_token("test123")
    assert is_rpc_token("TestToken")
    assert is_rpc_token("TESTTOKEN")
    
    # Invalid RPC tokens (FBC tokens)
    assert not is_rpc_token("123")
    assert not is_rpc_token("123a")

def test_validate_token_case_insensitive():
    """Test that validate_token works with different cases"""
    # Valid tokens
    assert validate_token("123")
    assert validate_token("123a")
    assert validate_token("test")
    assert validate_token("TestToken")
    assert validate_token("TESTTOKEN")
    
    # Invalid tokens
    assert not validate_token("")
    assert not validate_token("test@token")
    assert not validate_token("test.token")

def test_case_insensitive_token_matching():
    """Test case-insensitive matching scenarios"""
    # These should all normalize to the same value for comparison purposes
    tokens = ["Test", "test", "TEST", "TeSt"]
    normalized = [normalize_token(token) for token in tokens]
    
    # For non-FBC tokens, the normalized values should preserve case
    assert normalized[0] == "Test"
    assert normalized[1] == "test"
    assert normalized[2] == "TEST"
    assert normalized[3] == "TeSt"
    
    # But for comparison purposes, we should be able to match them case-insensitively
    assert normalized[0].lower() == normalized[1].lower()
    assert normalized[0].lower() == normalized[2].lower()
    assert normalized[0].lower() == normalized[3].lower()