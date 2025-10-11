import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch
from src.utils.file_utils import parse_sys_file, merge_node_data
from src.node_config_dialog import NodeConfigDialog
from PyQt5.QtWidgets import QApplication, QFileDialog, QMessageBox

# Mock QApplication for UI tests
@pytest.fixture(scope="session")
def qapp():
    app = QApplication([])
    yield app
    app.quit()

# Sample sys file content for testing
SAMPLE_MAIN_SYS_CONTENT = """
:e:hw:AB01 AP01 pxe:sys-csg2
:e:hw:AB02 AP01_t01 pxe:sys-csg2
:e:hw:AB03 AL03 pxe:sys-csg2
"""

SAMPLE_TOKEN_SYS_CONTENT_AB01 = """
set XD_IP_ADDR=192.168.1.100
"""

SAMPLE_TOKEN_SYS_CONTENT_AB02 = """
set XD_IP_ADDR=192.168.1.101
"""

SAMPLE_TOKEN_SYS_CONTENT_AB03 = """
set XD_IP_ADDR=192.168.1.102
"""

def test_parse_sys_file_ip_extraction():
    token_sys_contents = {
        "AB01": SAMPLE_TOKEN_SYS_CONTENT_AB01,
        "AB02": SAMPLE_TOKEN_SYS_CONTENT_AB02
    }
    parsed_nodes = parse_sys_file(SAMPLE_MAIN_SYS_CONTENT, token_sys_contents)

    ap01_node = next((node for node in parsed_nodes if node["name"] == "AP01"), None)
    assert ap01_node is not None
    assert ap01_node["ip"] == "192.168.1.100"
    assert {"token_id": "AB01", "token_type": "UNKNOWN"} in ap01_node["tokens"]
    assert {"token_id": "AB02", "token_type": "UNKNOWN"} in ap01_node["tokens"]

    al03_node = next((node for node in parsed_nodes if node["name"] == "AL03"), None)
    assert al03_node is not None
    assert al03_node["ip"] == "192.168.1.102" # Should get IP from AB03.sys if it were passed
    assert {"token_id": "AB03", "token_type": "UNKNOWN"} in al03_node["tokens"]

def test_parse_sys_file_token_format():
    parsed_nodes = parse_sys_file(SAMPLE_MAIN_SYS_CONTENT)
    ap01_node = next((node for node in parsed_nodes if node["name"] == "AP01"), None)
    assert ap01_node is not None
    assert all(isinstance(token, dict) and "token_id" in token and "token_type" in token for token in ap01_node["tokens"])
    assert {"token_id": "AB01", "token_type": "UNKNOWN"} in ap01_node["tokens"]
    assert {"token_id": "AB02", "token_type": "UNKNOWN"} in ap01_node["tokens"]

def test_load_sys_file_integration(qapp, tmp_path):
    # Create dummy sys files
    main_sys_file = tmp_path / "main.sys"
    main_sys_file.write_text(SAMPLE_MAIN_SYS_CONTENT)

    ab01_sys_file = tmp_path / "AB01.sys"
    ab01_sys_file.write_text(SAMPLE_TOKEN_SYS_CONTENT_AB01)

    ab02_sys_file = tmp_path / "AB02.sys"
    ab02_sys_file.write_text(SAMPLE_TOKEN_SYS_CONTENT_AB02)

    ab03_sys_file = tmp_path / "AB03.sys"
    ab03_sys_file.write_text(SAMPLE_TOKEN_SYS_CONTENT_AB03)

    dialog = NodeConfigDialog()
    
    with patch.object(QFileDialog, 'getOpenFileName', return_value=(str(main_sys_file), '')):
        with patch.object(QMessageBox, 'information', MagicMock()):
            dialog.load_sys_file()

    ap01_node = next((node for node in dialog.nodes_data if node["name"] == "AP01"), None)
    assert ap01_node is not None
    assert ap01_node["ip"] == "192.168.1.100"
    assert {"token_id": "AB01", "token_type": "UNKNOWN"} in ap01_node["tokens"]
    assert {"token_id": "AB02", "token_type": "UNKNOWN"} in ap01_node["tokens"]

    al03_node = next((node for node in dialog.nodes_data if node["name"] == "AL03"), None)
    assert al03_node is not None
    assert al03_node["ip"] == "192.168.1.102"
    assert {"token_id": "AB03", "token_type": "UNKNOWN"} in al03_node["tokens"]

def test_load_sys_file_merge_with_existing_ip(qapp, tmp_path):
    # Create dummy sys files
    main_sys_file = tmp_path / "main.sys"
    main_sys_file.write_text(SAMPLE_MAIN_SYS_CONTENT)

    ab01_sys_file = tmp_path / "AB01.sys"
    ab01_sys_file.write_text(SAMPLE_TOKEN_SYS_CONTENT_AB01)

    dialog = NodeConfigDialog()
    # Pre-populate with an existing node that has an IP
    dialog.nodes_data = [
        {"name": "AP01", "ip": "10.0.0.1", "tokens": [{"token_id": "AB01", "token_type": "UNKNOWN"}], "types": ["FBC"]}
    ]
    
    with patch.object(QFileDialog, 'getOpenFileName', return_value=(str(main_sys_file), '')):
        with patch.object(QMessageBox, 'information', MagicMock()):
            dialog.load_sys_file()

    ap01_node = next((node for node in dialog.nodes_data if node["name"] == "AP01"), None)
    assert ap01_node is not None
    assert ap01_node["ip"] == "10.0.0.1" # Existing IP should be preserved
    assert {"token_id": "AB01", "token_type": "UNKNOWN"} in ap01_node["tokens"]

def test_load_sys_file_merge_new_ip(qapp, tmp_path):
    # Create dummy sys files
    main_sys_file = tmp_path / "main.sys"
    main_sys_file.write_text(SAMPLE_MAIN_SYS_CONTENT)

    ab01_sys_file = tmp_path / "AB01.sys"
    ab01_sys_file.write_text(SAMPLE_TOKEN_SYS_CONTENT_AB01)

    dialog = NodeConfigDialog()
    # Pre-populate with an existing node that has no IP
    dialog.nodes_data = [
        {"name": "AP01", "ip": "", "tokens": [{"token_id": "AB01", "token_type": "UNKNOWN"}], "types": ["FBC"]}
    ]
    
    with patch.object(QFileDialog, 'getOpenFileName', return_value=(str(main_sys_file), '')):
        with patch.object(QMessageBox, 'information', MagicMock()):
            dialog.load_sys_file()

    ap01_node = next((node for node in dialog.nodes_data if node["name"] == "AP01"), None)
    assert ap01_node is not None
    assert ap01_node["ip"] == "192.168.1.100" # New IP should be applied
    assert {"token_id": "AB01", "token_type": "UNKNOWN"} in ap01_node["tokens"]
