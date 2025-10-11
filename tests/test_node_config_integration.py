import pytest
import json
import os
from unittest.mock import patch, MagicMock
from PyQt5.QtWidgets import QApplication, QListWidgetItem
from PyQt5.QtCore import Qt
from src.node_config_dialog import NodeConfigDialog
from src.sys_file_loader import SysFileParser
from src.sys_file_loader import SysFileLoader

# Ensure QApplication is initialized for PyQt5 widgets
@pytest.fixture(scope="session")
def app():
    return QApplication([])

@pytest.fixture
def node_config_dialog(app):
    dialog = NodeConfigDialog()
    yield dialog
    dialog.close()

@pytest.fixture
def mock_sys_file_content_ap():
    return """
:e:hw:161 AP01		pxe:sys-csg2	// AP01 PCS
:e:hw:162 AP01_m2	-               // FBC2
:e:hw:163 AP01_m3       -               // FBC3
"""

@pytest.fixture
def mock_sys_file_content_al():
    return """
:e:hw:501 AL01		pxe:sys-csg2	// AL01 Node
:e:hw:502 AL01_t1	-               // LIS Token 1
:e:hw:503 AL01_t2       -               // LIS Token 2
"""

class TestNodeConfigIntegration:
    @patch('PyQt5.QtWidgets.QMessageBox.information', MagicMock())
    @patch('PyQt5.QtWidgets.QMessageBox.critical', MagicMock())
    @patch('PyQt5.QtWidgets.QMessageBox.warning', MagicMock())
    def test_initialization_with_default_config(self, node_config_dialog):
        # Ensure the dialog initializes with some default data
        assert len(node_config_dialog.nodes_data) > 0
        assert node_config_dialog.node_list.count() > 0

    @patch('PyQt5.QtWidgets.QFileDialog.getOpenFileName')
    @patch('src.sys_file_loader.SysFileLoader.load_sys_file_and_extract_ip')
    @patch('PyQt5.QtWidgets.QMessageBox.information', MagicMock())
    @patch('PyQt5.QtWidgets.QMessageBox.critical', MagicMock())
    @patch('PyQt5.QtWidgets.QMessageBox.warning', MagicMock())
    def test_load_sys_file_extracts_ip_success(self, mock_load_sys_file_and_extract_ip, mock_getOpenFileName, node_config_dialog):
        # Setup initial node data
        node_config_dialog.nodes_data = [
            {"name": "AP01", "tokens": ["162"], "types": ["FBC"], "ip": ""}
        ]
        node_config_dialog.populate_node_list()
        node_config_dialog.node_list.setCurrentRow(0) # Select the node

        mock_getOpenFileName.return_value = ("test_ap.sys", "System Files (*.txt *.sys);;All Files (*)")
        mock_load_sys_file_and_extract_ip.return_value = "192.168.1.100"

        node_config_dialog.load_sys_file()

        # Verify that load_sys_file_and_extract_ip was called with correct arguments
        mock_load_sys_file_and_extract_ip.assert_called_once_with(
            "AP01", ["162"], os.path.dirname("test_ap.sys")
        )
        # Verify the IP address is updated in the UI and internal data
        assert node_config_dialog.ip_input.text() == "192.168.1.100"
        assert node_config_dialog.nodes_data["ip"] == "192.168.1.100"
        # Verify information message is shown
        QMessageBox.information.assert_called_once()
        assert "Successfully extracted IP address: 192.168.1.100" in QMessageBox.information.call_args

    @patch('PyQt5.QtWidgets.QFileDialog.getOpenFileName')
    @patch('src.sys_file_loader.SysFileLoader.load_sys_file_and_extract_ip')
    @patch('PyQt5.QtWidgets.QMessageBox.information', MagicMock())
    @patch('PyQt5.QtWidgets.QMessageBox.critical', MagicMock())
    @patch('PyQt5.QtWidgets.QMessageBox.warning', MagicMock())
    def test_load_sys_file_no_ip_found(self, mock_load_sys_file_and_extract_ip, mock_getOpenFileName, node_config_dialog):
        # Setup initial node data
        node_config_dialog.nodes_data = [
            {"name": "AP01", "tokens": ["162"], "types": ["FBC"], "ip": ""}
        ]
        node_config_dialog.populate_node_list()
        node_config_dialog.node_list.setCurrentRow(0) # Select the node

        mock_getOpenFileName.return_value = ("test_ap.sys", "System Files (*.txt *.sys);;All Files (*)")
        mock_load_sys_file_and_extract_ip.return_value = None # Simulate no IP found

        node_config_dialog.load_sys_file()

        # Verify that load_sys_file_and_extract_ip was called
        mock_load_sys_file_and_extract_ip.assert_called_once()
        # Verify IP address is not updated
        assert node_config_dialog.ip_input.text() == ""
        assert node_config_dialog.nodes_data["ip"] == ""
        # Verify warning message is shown
        QMessageBox.warning.assert_called_once()
        assert "Could not extract IP address" in QMessageBox.warning.call_args

    @patch('PyQt5.QtWidgets.QFileDialog.getOpenFileName')
    @patch('src.sys_file_loader.SysFileLoader.load_sys_file_and_extract_ip')
    @patch('PyQt5.QtWidgets.QMessageBox.warning', MagicMock())
    def test_load_sys_file_no_node_selected(self, mock_load_sys_file_and_extract_ip, mock_getOpenFileName, node_config_dialog):
        mock_getOpenFileName.return_value = ("test.sys", "System Files (*.txt *.sys);;All Files (*)")
        node_config_dialog.node_list.clearSelection() # Ensure no node is selected

        node_config_dialog.load_sys_file()

        mock_load_sys_file_and_extract_ip.assert_not_called()
        QMessageBox.warning.assert_called_once()
        assert "Please select a node first." in QMessageBox.warning.call_args

    @patch('PyQt5.QtWidgets.QFileDialog.getOpenFileName')
    @patch('src.sys_file_loader.SysFileLoader.load_sys_file_and_extract_ip')
    @patch('PyQt5.QtWidgets.QMessageBox.warning', MagicMock())
    def test_load_sys_file_incomplete_node_data(self, mock_load_sys_file_and_extract_ip, mock_getOpenFileName, node_config_dialog):
        node_config_dialog.nodes_data = [
            {"name": "AP01", "tokens": [], "types": ["FBC"], "ip": ""} # Missing tokens
        ]
        node_config_dialog.populate_node_list()
        node_config_dialog.node_list.setCurrentRow(0)

        mock_getOpenFileName.return_value = ("test.sys", "System Files (*.txt *.sys);;All Files (*)")
        node_config_dialog.load_sys_file()

        mock_load_sys_file_and_extract_ip.assert_not_called()
        QMessageBox.warning.assert_called_once()
        assert "Selected node must have a name and tokens" in QMessageBox.warning.call_args

    @patch('PyQt5.QtWidgets.QFileDialog.getExistingDirectory')
    @patch('src.sys_file_loader.SysFileLoader.load_sys_files_from_directory')
    @patch('src.sys_file_loader.SysFileParser._parse_single_sys_file_content')
    @patch('PyQt5.QtWidgets.QMessageBox.information', MagicMock())
    @patch('PyQt5.QtWidgets.QMessageBox.critical', MagicMock())
    def test_load_sys_directory_success(self, mock_parse_single_sys_file_content, mock_load_sys_files_from_directory, mock_getExistingDirectory, node_config_dialog, mock_sys_file_content_ap, mock_sys_file_content_al):
        mock_getExistingDirectory.return_value = "/mock/sys/dir"
        mock_load_sys_files_from_directory.return_value = {
            "ap.sys": mock_sys_file_content_ap,
            "al.sys": mock_sys_file_content_al
        }
        
        mock_parse_single_sys_file_content.side_effect = [
            {"name": "AP01", "ip_address": "", "tokens": [{"token_id": "162", "token_type": "FBC"}, {"token_id": "163", "token_type": "FBC"}], "types": ["FBC", "RPC", "LOG"]},
            {"name": "AL01", "ip_address": "", "tokens": [{"token_id": "502", "token_type": "LIS"}, {"token_id": "503", "token_type": "LIS"}], "types": ["LOG", "LIS"]}
        ]

        node_config_dialog.load_sys_directory()

        # Verify that the node data is updated
        assert any(node['name'] == "AP01" for node in node_config_dialog.nodes_data)
        assert any(node['name'] == "AL01" for node in node_config_dialog.nodes_data)
        assert node_config_dialog.node_list.findItems("AP01", Qt.MatchFlag.MatchExactly)
        assert node_config_dialog.node_list.findItems("AL01", Qt.MatchFlag.MatchExactly)

    @patch('PyQt5.QtWidgets.QFileDialog.getExistingDirectory')
    @patch('src.sys_file_loader.SysFileLoader.load_sys_files_from_directory')
    @patch('PyQt5.QtWidgets.QMessageBox.information', MagicMock())
    @patch('PyQt5.QtWidgets.QMessageBox.critical', MagicMock())
    def test_load_sys_directory_no_sys_files_found(self, mock_load_sys_files_from_directory, mock_getExistingDirectory, node_config_dialog):
        mock_getExistingDirectory.return_value = "/mock/empty/dir"
        mock_load_sys_files_from_directory.return_value = {}

        node_config_dialog.load_sys_directory()

        # Verify that no new nodes were added
        assert not any(node['name'] == "AP01" for node in node_config_dialog.nodes_data)
        assert not node_config_dialog.node_list.findItems("AP01", Qt.MatchFlag.MatchExactly)

    @patch('PyQt5.QtWidgets.QFileDialog.getExistingDirectory')
    @patch('src.sys_file_loader.SysFileLoader.load_sys_files_from_directory')
    @patch('src.sys_file_loader.SysFileParser._parse_single_sys_file_content')
    @patch('PyQt5.QtWidgets.QMessageBox.information', MagicMock())
    @patch('PyQt5.QtWidgets.QMessageBox.critical', MagicMock())
    def test_load_sys_directory_no_valid_nodes_found(self, mock_parse_single_sys_file_content, mock_load_sys_files_from_directory, mock_getExistingDirectory, node_config_dialog):
        mock_getExistingDirectory.return_value = "/mock/invalid/dir"
        mock_load_sys_files_from_directory.return_value = {
            "invalid.sys": "invalid content"
        }
        mock_parse_single_sys_file_content.return_value = [] # Simulate no valid nodes parsed

        node_config_dialog.load_sys_directory()

        # Verify that no new nodes were added
        assert not any(node['name'] == "AP01" for node in node_config_dialog.nodes_data)
        assert not node_config_dialog.node_list.findItems("AP01", Qt.MatchFlag.MatchExactly)