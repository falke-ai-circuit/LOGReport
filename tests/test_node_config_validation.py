#!/usr/bin/env python3
"""
Test suite for NodeConfigDialog validation and color coding features.

Tests:
1. Node validation logic (complete vs incomplete nodes)
2. Color coding in node list (green for complete, red for incomplete)
3. Standalone tokenid.sys matching to existing nodes
"""
import pytest
import sys
import os
from pathlib import Path
from unittest.mock import MagicMock, patch
from PyQt5.QtWidgets import QApplication, QListWidgetItem
from PyQt5.QtGui import QColor

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from node_config_dialog import NodeConfigDialog


@pytest.fixture(scope="module")
def qapp():
    """Create QApplication instance for tests"""
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    yield app


@pytest.fixture
def dialog(qapp):
    """Create NodeConfigDialog instance for testing"""
    with patch('node_config_dialog.NodeConfigDialog.save_config_as_default'):
        dialog = NodeConfigDialog()
        dialog.nodes_data = []  # Start with empty data
        return dialog


class TestNodeValidation:
    """Test node validation logic"""
    
    def test_complete_node_with_all_fields(self, dialog):
        """Test that a node with all required fields is valid"""
        node = {
            "name": "AP01m",
            "ip": "192.168.1.101",
            "tokens": ["162", "163"],
            "types": ["FBC", "RPC"]
        }
        assert dialog.validate_node(node) is True
    
    def test_incomplete_node_missing_name(self, dialog):
        """Test that a node without a name is invalid"""
        node = {
            "name": "",
            "ip": "192.168.1.101",
            "tokens": ["162", "163"],
            "types": ["FBC", "RPC"]
        }
        assert dialog.validate_node(node) is False
    
    def test_incomplete_node_missing_ip(self, dialog):
        """Test that a node without an IP is invalid"""
        node = {
            "name": "AP01m",
            "ip": "",
            "tokens": ["162", "163"],
            "types": ["FBC", "RPC"]
        }
        assert dialog.validate_node(node) is False
    
    def test_incomplete_node_missing_types(self, dialog):
        """Test that a node without types is invalid"""
        node = {
            "name": "AP01m",
            "ip": "192.168.1.101",
            "tokens": ["162", "163"],
            "types": []
        }
        assert dialog.validate_node(node) is False
    
    def test_incomplete_node_fbc_missing_tokens(self, dialog):
        """Test that a FBC node without tokens is invalid"""
        node = {
            "name": "AP01m",
            "ip": "192.168.1.101",
            "tokens": [],
            "types": ["FBC"]
        }
        assert dialog.validate_node(node) is False
    
    def test_complete_node_log_type_no_tokens(self, dialog):
        """Test that a LOG-only node without tokens is valid"""
        node = {
            "name": "AP01m",
            "ip": "192.168.1.101",
            "tokens": [],
            "types": ["LOG"]
        }
        assert dialog.validate_node(node) is True
    
    def test_complete_node_lis_type_no_tokens(self, dialog):
        """Test that a LIS-only node without tokens is valid"""
        node = {
            "name": "AL01",
            "ip": "192.168.1.102",
            "tokens": [],
            "types": ["LIS"]
        }
        assert dialog.validate_node(node) is True


class TestNodeColorCoding:
    """Test node list color coding"""
    
    def test_populate_node_list_colors_complete_nodes_green(self, dialog):
        """Test that complete nodes are colored green"""
        dialog.nodes_data = [
            {
                "name": "AP01m",
                "ip": "192.168.1.101",
                "tokens": ["162", "163"],
                "types": ["FBC"]
            }
        ]
        dialog.populate_node_list()
        
        item = dialog.node_list.item(0)
        assert item is not None
        assert item.foreground().color() == QColor("green")
    
    def test_populate_node_list_colors_incomplete_nodes_red(self, dialog):
        """Test that incomplete nodes are colored red"""
        dialog.nodes_data = [
            {
                "name": "AP01m",
                "ip": "",  # Missing IP
                "tokens": ["162", "163"],
                "types": ["FBC"]
            }
        ]
        dialog.populate_node_list()
        
        item = dialog.node_list.item(0)
        assert item is not None
        assert item.foreground().color() == QColor("red")
    
    def test_populate_node_list_mixed_colors(self, dialog):
        """Test that node list correctly shows mixed colors"""
        dialog.nodes_data = [
            {
                "name": "AP01m",
                "ip": "192.168.1.101",
                "tokens": ["162"],
                "types": ["FBC"]
            },
            {
                "name": "AP02m",
                "ip": "",  # Incomplete
                "tokens": ["182"],
                "types": ["FBC"]
            },
            {
                "name": "AL01",
                "ip": "192.168.1.103",
                "tokens": [],
                "types": ["LOG"]
            }
        ]
        dialog.populate_node_list()
        
        # First node should be green (complete)
        assert dialog.node_list.item(0).foreground().color() == QColor("green")
        # Second node should be red (missing IP)
        assert dialog.node_list.item(1).foreground().color() == QColor("red")
        # Third node should be green (complete)
        assert dialog.node_list.item(2).foreground().color() == QColor("green")


class TestApplyCurrentChanges:
    """Test that applying changes updates colors"""
    
    def test_apply_changes_updates_color_to_green(self, dialog):
        """Test that completing a node updates its color to green"""
        # Start with an incomplete node
        dialog.nodes_data = [
            {
                "name": "AP01m",
                "ip": "",
                "tokens": ["162"],
                "types": ["FBC"]
            }
        ]
        dialog.populate_node_list()
        dialog.node_list.setCurrentRow(0)
        
        # Simulate user completing the node
        dialog.name_input.setText("AP01m")
        dialog.ip_input.setText("192.168.1.101")
        dialog.token_input.setText("162")
        dialog.type_buttons["FBC"].setChecked(True)
        
        # Apply changes
        dialog.apply_current_changes()
        
        # Check that the item is now green
        item = dialog.node_list.item(0)
        assert item.foreground().color() == QColor("green")
    
    def test_apply_changes_updates_color_to_red(self, dialog):
        """Test that making a node incomplete updates its color to red"""
        # Start with a complete node
        dialog.nodes_data = [
            {
                "name": "AP01m",
                "ip": "192.168.1.101",
                "tokens": ["162"],
                "types": ["FBC"]
            }
        ]
        dialog.populate_node_list()
        dialog.node_list.setCurrentRow(0)
        
        # Simulate user removing IP
        dialog.name_input.setText("AP01m")
        dialog.ip_input.setText("")  # Remove IP
        dialog.token_input.setText("162")
        dialog.type_buttons["FBC"].setChecked(True)
        
        # Apply changes
        dialog.apply_current_changes()
        
        # Check that the item is now red
        item = dialog.node_list.item(0)
        assert item.foreground().color() == QColor("red")


class TestStandaloneTokenSysFile:
    """Test standalone tokenid.sys file loading"""
    
    def test_standalone_token_file_matches_existing_node(self, dialog, tmp_path):
        """Test that loading standalone tokenid.sys updates matching node IP"""
        # Setup: Create existing nodes with tokens
        dialog.nodes_data = [
            {
                "name": "AP01m",
                "ip": "",  # No IP yet
                "tokens": ["162", "163"],
                "types": ["FBC"]
            },
            {
                "name": "AP02m",
                "ip": "",
                "tokens": ["182", "183"],
                "types": ["FBC"]
            }
        ]
        dialog.populate_node_list()
        
        # Create a mock tokenid.sys file with IP
        token_sys_file = tmp_path / "162.sys"
        token_sys_file.write_text("set XD_IP_ADDR=192.168.1.101\n")
        
        # Mock the file dialog to return our test file
        with patch('node_config_dialog.QFileDialog.getOpenFileNames') as mock_dialog:
            mock_dialog.return_value = ([str(token_sys_file)], '')
            
            # Mock the message box
            with patch('node_config_dialog.QMessageBox.information') as mock_msg:
                dialog.load_sys_file()
                
                # Verify IP was updated for the matching node
                assert dialog.nodes_data[0]['ip'] == "192.168.1.101"
                assert dialog.nodes_data[1]['ip'] == ""  # Should remain empty
                
                # Verify message shown
                mock_msg.assert_called_once()
                call_args = mock_msg.call_args[0]
                assert "Token IPs Updated" in call_args[1]
                assert "1 node(s)" in call_args[2]
    
    def test_standalone_token_file_no_matching_node(self, dialog, tmp_path):
        """Test that loading tokenid.sys without matching node shows message"""
        # Setup: Create nodes without matching token
        dialog.nodes_data = [
            {
                "name": "AP01m",
                "ip": "",
                "tokens": ["162", "163"],  # Different tokens
                "types": ["FBC"]
            }
        ]
        
        # Create a token sys file that doesn't match any node
        token_sys_file = tmp_path / "999.sys"
        token_sys_file.write_text("set XD_IP_ADDR=192.168.1.101\n")
        
        # Mock the file dialog
        with patch('node_config_dialog.QFileDialog.getOpenFileNames') as mock_dialog:
            mock_dialog.return_value = ([str(token_sys_file)], '')
            
            # Mock the message box
            with patch('node_config_dialog.QMessageBox.information') as mock_msg:
                dialog.load_sys_file()
                
                # Verify no IPs were updated
                assert dialog.nodes_data[0]['ip'] == ""
                
                # Verify "No Matches Found" message
                mock_msg.assert_called_once()
                call_args = mock_msg.call_args[0]
                assert "No Matches Found" in call_args[1]
    
    def test_standalone_token_file_multiple_matches(self, dialog, tmp_path):
        """Test loading multiple tokenid.sys files updates multiple nodes"""
        # Setup: Create nodes
        dialog.nodes_data = [
            {
                "name": "AP01m",
                "ip": "",
                "tokens": ["162", "163"],
                "types": ["FBC"]
            },
            {
                "name": "AP02m",
                "ip": "",
                "tokens": ["182", "183"],
                "types": ["FBC"]
            }
        ]
        
        # Create multiple token sys files
        token_file_1 = tmp_path / "162.sys"
        token_file_1.write_text("set XD_IP_ADDR=192.168.1.101\n")
        
        token_file_2 = tmp_path / "182.sys"
        token_file_2.write_text("set XD_IP_ADDR=192.168.1.102\n")
        
        # Mock the file dialog
        with patch('node_config_dialog.QFileDialog.getOpenFileNames') as mock_dialog:
            mock_dialog.return_value = ([str(token_file_1), str(token_file_2)], '')
            
            # Mock the message box
            with patch('node_config_dialog.QMessageBox.information') as mock_msg:
                dialog.load_sys_file()
                
                # Verify both IPs were updated
                assert dialog.nodes_data[0]['ip'] == "192.168.1.101"
                assert dialog.nodes_data[1]['ip'] == "192.168.1.102"
                
                # Verify message shows 2 nodes updated
                call_args = mock_msg.call_args[0]
                assert "2 node(s)" in call_args[2]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
