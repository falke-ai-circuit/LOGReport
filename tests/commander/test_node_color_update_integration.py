import pytest
from unittest.mock import MagicMock, patch
from PyQt6.QtCore import QObject, pyqtSignal, Qt
from PyQt6.QtWidgets import QApplication, QTreeWidget, QTreeWidgetItem
from PyQt6.QtGui import QColor

import sys
import os

# Add src directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'src')))

from commander.presenters.node_tree_presenter import NodeTreePresenter
from commander.ui.node_tree_view import NodeTreeView
from commander.node_manager import NodeManager
from commander.session_manager import SessionManager
from commander.log_writer import LogWriter
from commander.command_queue import CommandQueue
from commander.services.fbc_command_service import FbcCommandService
from commander.services.rpc_command_service import RpcCommandService
from commander.models import NodeToken

@pytest.fixture(scope="session")
def qapp():
    """Fixture for QApplication"""
    return QApplication([])

@pytest.fixture
def mock_node_manager():
    nm = MagicMock(spec=NodeManager)
    nm.get_all_nodes.return_value = []
    nm.log_root = "/tmp/logs" # Add a mock log_root
    nm.scan_log_files = MagicMock() # Mock scan_log_files
    return nm

@pytest.fixture
def mock_session_manager():
    return MagicMock(spec=SessionManager)

@pytest.fixture
def mock_log_writer():
    lw = MagicMock(spec=LogWriter)
    return lw

@pytest.fixture
def mock_command_queue():
    cq = MagicMock(spec=CommandQueue)
    return cq

@pytest.fixture
def mock_fbc_service():
    return MagicMock(spec=FbcCommandService)

@pytest.fixture
def mock_rpc_service():
    return MagicMock(spec=RpcCommandService)

@pytest.fixture
def mock_context_menu_service():
    return MagicMock()

@pytest.fixture
def mock_bstool_service():
    return MagicMock()

@pytest.fixture
def node_tree_view(qapp):
    view = NodeTreeView()
    view.node_tree = QTreeWidget() # Mock the QTreeWidget for testing
    view.node_tree.setHeaderLabels(["Nodes"])
    view.node_tree.setColumnWidth(0, 300)
    return view

@pytest.fixture
def node_tree_presenter(node_tree_view, mock_node_manager, mock_session_manager,
                        mock_log_writer, mock_command_queue, mock_fbc_service,
                        mock_rpc_service, mock_context_menu_service, mock_bstool_service):
    presenter = NodeTreePresenter(
        view=node_tree_view,
        node_manager=mock_node_manager,
        session_manager=mock_session_manager,
        log_writer=mock_log_writer,
        command_queue=mock_command_queue,
        fbc_service=mock_fbc_service,
        rpc_service=mock_rpc_service,
        context_menu_service=mock_context_menu_service,
        bstool_service=mock_bstool_service
    )
    return presenter

class TestNodeColorUpdateIntegration:
    def test_node_color_changes_on_successful_command_and_log_write(self, qapp, node_tree_view, node_tree_presenter,
                                                                     mock_command_queue, mock_log_writer, mock_node_manager):
        """
        Test that node color changes to green when both command and log write are successful.
        """
        node_name = "TestNode"
        token_id = "123"
        
        # Mock a node in NodeManager
        mock_node = MagicMock()
        mock_node.name = node_name
        mock_node.ip_address = "127.0.0.1"
        mock_node.status = "online"
        mock_node_manager.get_all_nodes.return_value = [mock_node]
        mock_node_manager.get_node.return_value = mock_node
        
        # Create a node item directly for testing
        node_item = QTreeWidgetItem([f"{node_name} (127.0.0.1)"])
        node_item.setData(0, Qt.ItemDataRole.UserRole, {"type": "node", "node_name": node_name})
        node_tree_view.node_tree.addTopLevelItem(node_item)

        # Ensure the presenter's internal node_status is initialized
        node_tree_presenter.node_status[node_name] = {"command_success": None, "log_success": None}
        
        with patch.object(NodeTreeView, 'update_node_color', MagicMock()) as mock_update_node_color:
            # Simulate command completion and log write completion by directly calling handlers
            mock_token = NodeToken(token_id=token_id, token_type="FBC", name=node_name, ip_address="127.0.0.1")
            
            node_tree_presenter.handle_command_completed("test_command", "success", True, mock_token)
            node_tree_presenter.handle_log_write_completed(node_name, token_id, True)
            
            # Verify that update_node_color was called with the correct arguments
            mock_update_node_color.assert_called_once_with(node_name, "green")

    def test_node_color_changes_to_red_on_command_failure(self, qapp, node_tree_view, node_tree_presenter,
                                                          mock_command_queue, mock_log_writer, mock_node_manager):
        """
        Test that node color changes to red when command fails.
        """
        node_name = "AnotherNode"
        token_id = "456"
        
        # Mock a node in NodeManager
        mock_node = MagicMock()
        mock_node.name = node_name
        mock_node.ip_address = "127.0.0.2"
        mock_node.status = "online"
        mock_node_manager.get_all_nodes.return_value = [mock_node]
        mock_node_manager.get_node.return_value = mock_node
        
        # Create a node item directly for testing
        node_item = QTreeWidgetItem([f"{node_name} (127.0.0.2)"])
        node_item.setData(0, Qt.ItemDataRole.UserRole, {"type": "node", "node_name": node_name})
        node_tree_view.node_tree.addTopLevelItem(node_item)

        # Ensure the presenter's internal node_status is initialized
        node_tree_presenter.node_status[node_name] = {"command_success": None, "log_success": None}
        
        with patch.object(NodeTreeView, 'update_node_color', MagicMock()) as mock_update_node_color:
            mock_token = NodeToken(token_id=token_id, token_type="RPC", name=node_name, ip_address="127.0.0.2")
            
            node_tree_presenter.handle_command_completed("failed_command", "error", False, mock_token)
            node_tree_presenter.handle_log_write_completed(node_name, token_id, True)
            
            # Verify that update_node_color was called with the correct arguments
            mock_update_node_color.assert_called_once_with(node_name, "red")

    def test_node_color_changes_to_red_on_log_write_failure(self, qapp, node_tree_view, node_tree_presenter,
                                                            mock_command_queue, mock_log_writer, mock_node_manager):
        """
        Test that node color changes to red when log write fails.
        """
        node_name = "ThirdNode"
        token_id = "789"
        
        # Mock a node in NodeManager
        mock_node = MagicMock()
        mock_node.name = node_name
        mock_node.ip_address = "127.0.0.3"
        mock_node.status = "online"
        mock_node_manager.get_all_nodes.return_value = [mock_node]
        mock_node_manager.get_node.return_value = mock_node
        
        # Create a node item directly for testing
        node_item = QTreeWidgetItem([f"{node_name} (127.0.0.3)"])
        node_item.setData(0, Qt.ItemDataRole.UserRole, {"type": "node", "node_name": node_name})
        node_tree_view.node_tree.addTopLevelItem(node_item)

        # Ensure the presenter's internal node_status is initialized
        node_tree_presenter.node_status[node_name] = {"command_success": None, "log_success": None}
        
        with patch.object(NodeTreeView, 'update_node_color', MagicMock()) as mock_update_node_color:
            mock_token = NodeToken(token_id=token_id, token_type="LOG", name=node_name, ip_address="127.0.0.3")
            
            node_tree_presenter.handle_command_completed("successful_command", "output", True, mock_token)
            node_tree_presenter.handle_log_write_completed(node_name, token_id, False)
            
            # Verify that update_node_color was called with the correct arguments
            mock_update_node_color.assert_called_once_with(node_name, "red")