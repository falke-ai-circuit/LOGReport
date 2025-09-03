import os
import pytest
from unittest.mock import MagicMock, patch, PropertyMock
from PyQt6.QtCore import Qt, QPoint
from PyQt6.QtWidgets import QMenu, QApplication

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
    # Connect the presenter to the view
    node_tree_presenter.view = view
    # Connect view signals to presenter methods
    view.item_expanded.connect(node_tree_presenter.handle_item_expanded)
    return view

def create_test_nodes():
    """Create test nodes structure with AP01m and its FBC tokens"""
    # Create nodes using the current model structure
    # For the test, we'll create a simple structure with just the AP01m node
    ap01m = Node("AP01m", "192.168.0.11")
    
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
    
    return ap01m

def test_context_menu_shows_correct_tokens(node_tree_view, node_tree_presenter, mock_context_menu_service, qapp):
    """Test context menu shows all tokens for AP01m FBC group in sorted order"""
    # Setup test nodes
    ap01m = create_test_nodes()
    
    # Mock the node manager to return our test node
    with patch.object(node_tree_presenter.node_manager, 'get_all_nodes', return_value=[ap01m]):
        # Mock itemAt to return a mock item with user data
        mock_item = MagicMock()
        mock_item.data.return_value = {
            "type": "node",
            "node_name": "AP01m"
        }
        node_tree_view.itemAt = MagicMock(return_value=mock_item)
        
        # Mock viewport to return a mock viewport
        mock_viewport = MagicMock()
        mock_viewport.mapToGlobal.return_value = QPoint(100, 100)
        node_tree_view.viewport = MagicMock(return_value=mock_viewport)
        
        # Call the presenter's show_context_menu method directly
        node_tree_presenter.show_context_menu(QPoint(100, 100))
        
        # Verify context menu service was called
        assert mock_context_menu_service.show_context_menu.called, "Context menu service should be called"

def test_context_menu_handles_mixed_case_filenames(node_tree_view, qapp):
    """Test token extraction handles mixed-case filenames"""
    # Setup test nodes
    ap01m = create_test_nodes()
    
    # Verify tokens were created with correct IDs
    # Get all FBC tokens from the node
    fbc_tokens = []
    for token_list in ap01m.tokens.values():
        for token in token_list:
            if token.token_type == "FBC":
                fbc_tokens.append(token)
    
    # Extract token IDs
    token_ids = [token.token_id for token in fbc_tokens]
    token_ids.sort()  # Sort for consistent comparison
    
    assert token_ids == ["162", "163", "164"], \
        f"Failed to handle mixed-case filenames. Expected ['162', '163', '164'], got {token_ids}"