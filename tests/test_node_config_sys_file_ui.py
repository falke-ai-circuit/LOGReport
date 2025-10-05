import pytest
import json
import os
from unittest.mock import patch, MagicMock
from PyQt6.QtWidgets import QApplication, QFileDialog, QMessageBox, QListWidget
from PyQt6.QtCore import Qt
from src.node_config_dialog import NodeConfigDialog
from src.utils import file_utils

# Fixture for QApplication
@pytest.fixture(scope="session")
def qapp():
    app = QApplication([])
    yield app
    app.quit()

# Fixture for NodeConfigDialog
@pytest.fixture
def dialog(qapp, tmp_path):
    # Create a temporary nodes.json for testing
    temp_nodes_json = tmp_path / "nodes.json"
    initial_nodes_data = [
        {"name": "AP00", "tokens": ["001", "002"], "types": ["FBC"], "ip": "192.168.0.1"}
    ]
    with open(temp_nodes_json, 'w') as f:
        json.dump(initial_nodes_data, f, indent=4)

    # Patch the config_file path to use the temporary file
    with patch('src.node_config_dialog.NodeConfigDialog.config_file', new=str(temp_nodes_json)):
        dialog = NodeConfigDialog()
        yield dialog
        dialog.close()

# Fixture for a mock sys file
@pytest.fixture
def mock_sys_file(tmp_path):
    sys_file_content = """
:e:hw:100	AP100	pxe:1001	// AP100_node
:e:hw:101	AP101	-		// AP101_node
:e:hw:102	AP102	pxe:1002	// AP102_node
"""
    sys_file_path = tmp_path / "mock.sys"
    with open(sys_file_path, 'w') as f:
        f.write(sys_file_content)
    return str(sys_file_path)

# Fixture for a mock sys file with duplicates
@pytest.fixture
def mock_sys_file_duplicates(tmp_path):
    sys_file_content = """
:e:hw:100	AP00	pxe:1001	// AP00_duplicate
:e:hw:101	AP101	-		// AP101_node
"""
    sys_file_path = tmp_path / "mock_dup.sys"
    with open(sys_file_path, 'w') as f:
        f.write(sys_file_content)
    return str(sys_file_path)

class TestNodeConfigSysFileUI:
    def test_load_sys_file_button_click_and_node_addition(self, qtbot, dialog, mock_sys_file, tmp_path):
        # Simulate clicking the "Load Sys File" button
        with patch.object(QFileDialog, 'getOpenFileName', return_value=(mock_sys_file, '')) as mock_get_file_name:
            with patch.object(QMessageBox, 'information', return_value=QMessageBox.StandardButton.Ok) as mock_message_box:
                initial_node_count = dialog.node_list.count()
                qtbot.mouseClick(dialog.load_sys_btn, Qt.MouseButton.LeftButton)

                # Verify QFileDialog was called
                mock_get_file_name.assert_called_once()

                # Verify new nodes are added to the UI
                assert dialog.node_list.count() == initial_node_count + 3
                assert dialog.node_list.item(initial_node_count).text() == "AP100"
                assert dialog.node_list.item(initial_node_count + 1).text() == "AP101"
                assert dialog.node_list.item(initial_node_count + 2).text() == "AP102"

                # Verify QMessageBox was called with success message
                mock_message_box.assert_called_once()
                assert "Loaded 3 nodes from sys file." in mock_message_box.call_args

                # Verify nodes_data is updated internally
                assert len(dialog.nodes_data) == initial_node_count + 3
                assert dialog.nodes_data[initial_node_count]['name'] == "AP100"
                assert dialog.nodes_data[initial_node_count]['ip'] == "192.168.1.100"
                assert dialog.nodes_data[initial_node_count]['tokens'] == ["1001"]
                assert dialog.nodes_data[initial_node_count]['types'] == ["RPC", "LOG"]

                assert dialog.nodes_data[initial_node_count + 1]['name'] == "AP101"
                assert dialog.nodes_data[initial_node_count + 1]['ip'] == "192.168.1.101"
                assert dialog.nodes_data[initial_node_count + 1]['tokens'] == []
                assert dialog.nodes_data[initial_node_count + 1]['types'] == ["FBC", "LIS"]

                assert dialog.nodes_data[initial_node_count + 2]['name'] == "AP102"
                assert dialog.nodes_data[initial_node_count + 2]['ip'] == "192.168.1.102"
                assert dialog.nodes_data[initial_node_count + 2]['tokens'] == ["1002"]
                assert dialog.nodes_data[initial_node_count + 2]['types'] == ["RPC", "LOG"]

    def test_load_sys_file_duplicate_skipping(self, qtbot, dialog, mock_sys_file_duplicates, tmp_path):
        # Ensure initial nodes_data contains "AP00"
        assert any(node['name'] == "AP00" for node in dialog.nodes_data)
        initial_node_count = dialog.node_list.count()

        # Simulate clicking the "Load Sys File" button with a file containing duplicates
        with patch.object(QFileDialog, 'getOpenFileName', return_value=(mock_sys_file_duplicates, '')) as mock_get_file_name:
            with patch.object(QMessageBox, 'information', return_value=QMessageBox.StandardButton.Ok) as mock_message_box:
                qtbot.mouseClick(dialog.load_sys_btn, Qt.MouseButton.LeftButton)

                # Verify QFileDialog was called
                mock_get_file_name.assert_called_once()

                # Verify only unique nodes are added to the UI
                assert dialog.node_list.count() == initial_node_count + 1 # AP101 is added, AP00 is skipped
                assert dialog.node_list.item(initial_node_count).text() == "AP101"

                # Verify QMessageBox was called with success and skipped message
                mock_message_box.assert_called_once()
                assert "Loaded 1 nodes from sys file. Skipped 1 duplicates." in mock_message_box.call_args

                # Verify nodes_data is updated internally, AP00 should not be duplicated
                assert len(dialog.nodes_data) == initial_node_count + 1
                assert any(node['name'] == "AP00" for node in dialog.nodes_data) # Original AP00 still exists
                assert any(node['name'] == "AP101" for node in dialog.nodes_data) # New AP101 exists
                assert not any(node['name'] == "AP00" and node['ip'] == "192.168.1.100" for node in dialog.nodes_data) # Duplicate AP00 not added

    def test_nodes_json_update_after_load_sys_file_and_save(self, qtbot, dialog, mock_sys_file, tmp_path):
        # Simulate loading sys file
        with patch.object(QFileDialog, 'getOpenFileName', return_value=(mock_sys_file, '')) as mock_get_file_name:
            with patch.object(QMessageBox, 'information', return_value=QMessageBox.StandardButton.Ok):
                qtbot.mouseClick(dialog.load_sys_btn, Qt.MouseButton.LeftButton)

        # Simulate saving the configuration to a new nodes.json
        temp_output_json = tmp_path / "updated_nodes.json"
        with patch.object(QFileDialog, 'getSaveFileName', return_value=(str(temp_output_json), '')) as mock_save_file_name:
            with patch.object(QMessageBox, 'information', return_value=QMessageBox.StandardButton.Ok):
                qtbot.mouseClick(dialog.save_btn, Qt.MouseButton.LeftButton)

                mock_save_file_name.assert_called_once()

        # Verify the content of the saved nodes.json
        with open(temp_output_json, 'r') as f:
            saved_nodes = json.load(f)

        assert len(saved_nodes) == 4 # Initial AP00 + 3 new nodes
        
        # Verify AP00
        ap00_node = next(node for node in saved_nodes if node['name'] == "AP00")
        assert ap00_node['ip_address'] == "192.168.0.1"
        assert {"token_id": "001", "token_type": "FBC", "port": 23, "protocol": "telnet"} in ap00_node['tokens']
        assert {"token_id": "002", "token_type": "FBC", "port": 23, "protocol": "telnet"} in ap00_node['tokens']

        # Verify AP100
        ap100_node = next(node for node in saved_nodes if node['name'] == "AP100")
        assert ap100_node['ip_address'] == "192.168.1.100"
        assert {"token_id": "1001", "token_type": "RPC", "port": 23, "protocol": "telnet"} in ap100_node['tokens']
        assert {"token_id": "1001", "token_type": "LOG", "port": 23, "protocol": "telnet"} in ap100_node['tokens']

        # Verify AP101
        ap101_node = next(node for node in saved_nodes if node['name'] == "AP101")
        assert ap101_node['ip_address'] == "192.168.1.101"
        assert {"token_id": "default_lis_token", "token_type": "LIS", "port": 23, "protocol": "telnet"} in ap101_node['tokens']
        assert {"token_id": "", "token_type": "FBC", "port": 23, "protocol": "telnet"} not in ap101_node['tokens'] # FBC has no tokens in sys file

        # Verify AP102
        ap102_node = next(node for node in saved_nodes if node['name'] == "AP102")
        assert ap102_node['ip_address'] == "192.168.1.102"
        assert {"token_id": "1002", "token_type": "RPC", "port": 23, "protocol": "telnet"} in ap102_node['tokens']
        assert {"token_id": "1002", "token_type": "LOG", "port": 23, "protocol": "telnet"} in ap102_node['tokens']