import os
import sys
import pytest

# Add src directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'src')))

# Direct import to avoid circular dependencies
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'src', 'commander', 'utils')))
from log_filename_parser import extract_ip_from_filename, is_valid_ip


def test_extract_ip_from_filename_dashed_format():
    """Test extracting IP from filenames with dashed format (e.g., 192-168-0-11)"""
    # Standard cases
    assert extract_ip_from_filename("AP01m_192-168-0-11_162.fbc") == "192.168.0.11"
    assert extract_ip_from_filename("AP01r_192-168-0-27_362.fbc") == "192.168.0.27"
    assert extract_ip_from_filename("AP02m_192-168-0-12_182.fbc") == "192.168.0.12"
    assert extract_ip_from_filename("AP02r_192-168-0-28_382.fbc") == "192.168.0.28"
    assert extract_ip_from_filename("AP03m_192-168-0-13_2a2.fbc") == "192.168.0.13"
    assert extract_ip_from_filename("AP03r_192-168-0-29_1a2.fbc") == "192.168.0.29"
    
    # Edge case: zero IP
    assert extract_ip_from_filename("AP01r_0-0-0-0_363.fbc") == "0.0.0.0"


def test_extract_ip_from_filename_underscore_format():
    """Test extracting IP from filenames with underscore format (e.g., 192_168_0_52)"""
    assert extract_ip_from_filename("AL01_192-168-0-52_exe1_5irb_5orb.lis") == "192.168.0.52"
    assert extract_ip_from_filename("AL02_192-168-0-55_exe1_5irb_5orb.lis") == "192.168.0.55"


def test_extract_ip_from_filename_dot_format():
    """Test extracting IP from filenames with dot format (e.g., 192.168.1.2)"""
    assert extract_ip_from_filename("NODE2_192.168.1.2_456.rpc") == "192.168.1.2"


def test_extract_ip_from_filename_edge_cases():
    """Test extracting IP from filenames with edge cases"""
    # Empty filename
    assert extract_ip_from_filename("") == ""
    
    # No IP in filename
    assert extract_ip_from_filename("test_file.txt") == ""
    
    # Invalid IP format
    assert extract_ip_from_filename("test_999-999-999-999_file.txt") == ""
    
    # Out of range IP parts
    assert extract_ip_from_filename("test_256-1-1-1_file.txt") == ""
    assert extract_ip_from_filename("test_1-256-1-1_file.txt") == ""
    assert extract_ip_from_filename("test_1-1-256-1_file.txt") == ""
    assert extract_ip_from_filename("test_1-1-1-256_file.txt") == ""
    
    # Non-numeric parts
    assert extract_ip_from_filename("test_a-b-c-d_file.txt") == ""


def test_is_valid_ip_valid_addresses():
    """Test validating valid IP addresses"""
    # Standard valid IPs
    assert is_valid_ip("192.168.0.11") is True
    assert is_valid_ip("192.168.0.27") is True
    assert is_valid_ip("192.168.0.52") is True
    assert is_valid_ip("192.168.1.2") is True
    
    # Edge cases
    assert is_valid_ip("0.0.0.0") is True
    assert is_valid_ip("255.255.255.255") is True
    assert is_valid_ip("127.0.0.1") is True


def test_is_valid_ip_invalid_addresses():
    """Test validating invalid IP addresses"""
    # Invalid formats
    assert is_valid_ip("") is False
    assert is_valid_ip("192.168.0") is False  # Missing octet
    assert is_valid_ip("192.168.0.11.5") is False  # Extra octet
    assert is_valid_ip("192.168.0.11.5.6") is False  # Extra octets
    
    # Out of range values
    assert is_valid_ip("256.1.1.1") is False
    assert is_valid_ip("1.256.1.1") is False
    assert is_valid_ip("1.1.256.1") is False
    assert is_valid_ip("1.1.1.256") is False
    assert is_valid_ip("-1.1.1.1") is False
    
    # Non-numeric values
    assert is_valid_ip("a.b.c.d") is False
    assert is_valid_ip("192.168.0.a") is False
    assert is_valid_ip("192.168.0.1a") is False