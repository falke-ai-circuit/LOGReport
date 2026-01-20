import pytest
from pathlib import Path
from src.utils.file_utils import parse_sys_file

@pytest.fixture
def main_sys_content():
    return """
:e:hw:181 AP02_main pxe:sys-csg2 // AP02 Main PCS
:e:hw:182 AP02_m2 - // FBC2
"""

@pytest.fixture
def dependent_sys_content():
    return """
# This is a dependent sys file
:e:ip:192.168.1.123 // The IP address
"""

def test_ip_extraction_from_dependent_file(tmp_path, main_sys_content, dependent_sys_content):
    """
    Tests that the IP address is correctly extracted from a dependent sys file.
    """
    # Create the main and dependent sys files
    main_sys_file = tmp_path / "main.sys"
    main_sys_file.write_text(main_sys_content)

    # The token '182' from AP02_m2 will be used to find the dependent file
    dependent_sys_file = tmp_path / "182.sys"
    dependent_sys_file.write_text(dependent_sys_content)

    # Parse the main sys file
    parsed_data = parse_sys_file(main_sys_content, base_path=str(tmp_path))

    # Find the AP02m node
    ap02m_node = next((node for node in parsed_data if node["name"] == "AP02m"), None)

    # Assert that the node was found and the IP address is correct
    assert ap02m_node is not None
    assert ap02m_node["ip"] == "192.168.1.123"

def test_ip_extraction_missing_dependent_file(tmp_path, main_sys_content):
    """
    Tests that no error is raised and the IP remains empty if the dependent file is missing.
    """
    # Create only the main sys file
    main_sys_file = tmp_path / "main.sys"
    main_sys_file.write_text(main_sys_content)

    # Parse the main sys file
    parsed_data = parse_sys_file(main_sys_content, base_path=str(tmp_path))

    # Find the AP02m node
    ap02m_node = next((node for node in parsed_data if node["name"] == "AP02m"), None)

    # Assert that the node was found and the IP address is empty
    assert ap02m_node is not None
    assert ap02m_node["ip"] == ""

def test_ip_extraction_dependent_file_no_ip(tmp_path, main_sys_content):
    """
    Tests that the IP remains empty if the dependent file exists but does not contain an IP address.
    """
    # Create the main and dependent sys files
    main_sys_file = tmp_path / "main.sys"
    main_sys_file.write_text(main_sys_content)

    dependent_sys_content_no_ip = """
# This dependent file has no IP
:e:some_other_data:value
"""
    dependent_sys_file = tmp_path / "182.sys"
    dependent_sys_file.write_text(dependent_sys_content_no_ip)

    # Parse the main sys file
    parsed_data = parse_sys_file(main_sys_content, base_path=str(tmp_path))

    # Find the AP02m node
    ap02m_node = next((node for node in parsed_data if node["name"] == "AP02m"), None)

    # Assert that the node was found and the IP address is empty
    assert ap02m_node is not None
    assert ap02m_node["ip"] == ""