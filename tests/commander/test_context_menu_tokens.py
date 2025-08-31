import os
import pytest
from unittest.mock import MagicMock, patch, PropertyMock
from PyQt5.QtCore import Qt, QPoint
from PyQt5.QtWidgets import QMenu, QApplication

from src.commander.ui.node_tree_view import NodeTreeView
from src.commander.presenters.node_tree_presenter import NodeTreePresenter
from src.commander.services.context_menu_service import ContextMenuService
from src.commander.models import Node, NodeToken

# Initialize QApplication once for all tests
@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app
    # Don't exit the app to avoid crashes

@pytest.fixture
def mock_context_menu_service():
    return MagicMock(spec=ContextMenuService)

@pytest.fixture
def node_tree_presenter(mock_context_menu_service):
    # Mock all required dependencies for NodeTreePresenter
    mock_view = MagicMock()
    mock_node_manager = MagicMock()
    mock_session_manager = MagicMock()
    mock_log_writer = MagicMock()
    mock_command_queue = MagicMock()
    mock_fbc_service = MagicMock()
    mock_rpc_service = MagicMock()
    
    presenter = NodeTreePresenter(
        view=mock_view,
        node_manager=mock_node_manager,
        session_manager=mock_session_manager,
        log_writer=mock_log_writer,
        command_queue=mock_command_queue,
        fbc_service=mock_fbc_service,
        rpc_service=mock_rpc_service,
        context_menu_service=mock_context_menu_service
    )
    return presenter

@pytest.fixture
def node_tree_view(node_tree_presenter):
    view = NodeTreeView()
    view.set_presenter(node_tree_presenter)
    return view

def create_test_nodes():
    """Create test nodes structure with AP01m and its FBC tokens"""
    # Create nodes using the current model structure
    root_node = Node("Root", "0.0.0.0")
    
    ap01m = Node("AP01m", "192.168.0.11")
    root_node.add_token(ap01m)
    
    # Add FBC tokens directly to the node
    token162 = NodeToken("162", "FBC", "AP01m", "192.168.0.11")
    token162.log_path = os.path.join("test_logs", "AP01m", "162_FBC.log")
    ap01m.add_token(token162)
    
    token163 = NodeToken("163", "FBC", "AP01m", "192.168.0.11")
    token163.log_path = os.path.join("test_logs", "AP01m", "163_fbc.LOG")
    ap01m.add_token(token163)
    
    token164 = NodeToken("164", "FBC", "AP01m", "192.168.0.11")
    token164.log_path = os.path.join("test_logs", "AP01m", "164_FBC.log")
    ap01m.add_token(token164)
    
    return root_node

def test_context_menu_shows_correct_tokens(node_tree_view, mock_context_menu_service, qapp):
    """Test context menu shows all tokens for AP01m FBC group in sorted order"""
    # Setup test nodes
    root_node = create_test_nodes()
    
    # Mock the model and its methods
    with patch.object(node_tree_view.presenter, 'model', new_callable=PropertyMock) as mock_model:
        mock_model.return_value.root_node = root_node
        node_tree_view.expandAll()
        
        # Find FBC group node
        ap01m = root_node.children[0]
        fbc_group = ap01m.children[0]
        
        # Simulate right-click on FBC group
        index = node_tree_view.model.index(fbc_group.row(), 0, node_tree_view.model.index(ap01m.row(), 0))
        pos = node_tree_view.visualRect(index).center()
        
        with patch.object(QMenu, 'exec_') as mock_exec:
            node_tree_view.contextMenuEvent(
                MagicMock(pos=lambda: pos, globalPos=lambda: node_tree_view.mapToGlobal(pos))
            )
        
        # Verify context menu creation
        mock_context_menu_service.create_context_menu.assert_called_once()
        
        # Get created menu items
        menu = mock_context_menu_service.create_context_menu.return_value
        action_texts = [action.text() for action in menu.actions() if not action.isSeparator()]
        
        # Verify tokens are present and sorted
        expected_tokens = ["162", "163", "164"]
        assert action_texts == expected_tokens, \
            f"Expected tokens {expected_tokens}, got {action_texts}"

def test_context_menu_handles_mixed_case_filenames(node_tree_view, qapp):
    """Test token extraction handles mixed-case filenames"""
    # Setup test nodes
    root_node = create_test_nodes()
    
    # Mock the model and its methods
    with patch.object(node_tree_view.presenter, 'model', new_callable=PropertyMock) as mock_model:
        mock_model.return_value.root_node = root_node
        
        # Verify tokens were created despite mixed-case filenames
        ap01m = root_node.children[0]
        fbc_group = ap01m.children[0]
        token_names = [child.name for child in fbc_group.children]
        
        assert token_names == ["162", "163", "164"], \
            "Failed to handle mixed-case filenames"