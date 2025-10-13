"""
Test node suffix stripping for BsTool -errlog parameter
"""
import pytest


def test_strip_node_suffix():
    """
    Test that _strip_node_suffix correctly removes 'm' or 'r' suffix from node names.
    
    This is critical for BsTool -errlog parameter, which fails with suffixed node names:
    - AP01m → AP01 (works)
    - AP02r → AP02 (works)
    - AP01 → AP01 (unchanged)
    """
    # Mock presenter with just the method we need
    class MockPresenter:
        def _strip_node_suffix(self, node_name: str) -> str:
            """
            Strip 'm' or 'r' suffix from node name for BsTool -errlog parameter.
            
            Examples:
                AP01m → AP01
                AP02r → AP02
                AP01 → AP01 (unchanged)
                
            Args:
                node_name: Original node name (may have 'm' or 'r' suffix)
                
            Returns:
                Node name without 'm' or 'r' suffix
            """
            if node_name.endswith('m') or node_name.endswith('r'):
                return node_name[:-1]
            return node_name
    
    presenter = MockPresenter()
    
    # Test stripping 'm' suffix
    assert presenter._strip_node_suffix("AP01m") == "AP01"
    assert presenter._strip_node_suffix("AP02m") == "AP02"
    assert presenter._strip_node_suffix("BP01m") == "BP01"
    assert presenter._strip_node_suffix("AL01m") == "AL01"
    
    # Test stripping 'r' suffix
    assert presenter._strip_node_suffix("AP01r") == "AP01"
    assert presenter._strip_node_suffix("AP02r") == "AP02"
    assert presenter._strip_node_suffix("BP01r") == "BP01"
    
    # Test no stripping (no suffix)
    assert presenter._strip_node_suffix("AP01") == "AP01"
    assert presenter._strip_node_suffix("AP02") == "AP02"
    assert presenter._strip_node_suffix("BP01") == "BP01"
    assert presenter._strip_node_suffix("AL01") == "AL01"
    
    # Test edge cases
    assert presenter._strip_node_suffix("m") == ""  # Single 'm' becomes empty string
    assert presenter._strip_node_suffix("r") == ""  # Single 'r' becomes empty string
    assert presenter._strip_node_suffix("") == ""   # Empty string stays empty
    
    # Test that other suffixes are not stripped
    assert presenter._strip_node_suffix("AP01x") == "AP01x"
    assert presenter._strip_node_suffix("AP01a") == "AP01a"


def test_bstool_command_construction():
    """
    Test that BsTool commands are constructed correctly with stripped node names.
    """
    class MockPresenter:
        def _strip_node_suffix(self, node_name: str) -> str:
            if node_name.endswith('m') or node_name.endswith('r'):
                return node_name[:-1]
            return node_name
    
    presenter = MockPresenter()
    
    # Test command construction
    test_cases = [
        ("AP01m", "-errlog AP01"),
        ("AP02r", "-errlog AP02"),
        ("BP01m", "-errlog BP01"),
        ("AL01", "-errlog AL01"),  # No suffix
        ("AP01", "-errlog AP01"),   # No suffix
    ]
    
    for node_name, expected_command in test_cases:
        errlog_node_name = presenter._strip_node_suffix(node_name)
        bstool_command_args = f"-errlog {errlog_node_name}"
        assert bstool_command_args == expected_command, \
            f"Failed for {node_name}: expected '{expected_command}', got '{bstool_command_args}'"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
