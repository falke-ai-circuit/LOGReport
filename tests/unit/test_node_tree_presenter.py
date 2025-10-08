"""
Unit tests for NodeTreePresenter
"""
import pytest
from unittest.mock import MagicMock, patch
from PyQt6.QtGui import QColor
from src.commander.presenters.node_tree_presenter import NodeTreePresenter
from src.commander.node_manager import NodeManager
from src.commander.session_manager import SessionManager
from src.commander.log_writer import LogWriter
from src.commander.command_queue import CommandQueue
from src.commander.services.fbc_command_service import FbcCommandService
from src.commander.services.rpc_command_service import RpcCommandService
from src.commander.services.context_menu_service import ContextMenuService
from src.commander.services.bstool_command_service import BsToolCommandService

class TestNodeTreePresenter:
    """Test suite for NodeTreePresenter class"""
    
    @pytest.fixture
    def mock_view(self):
        """Create a mock view"""
        mock_view = MagicMock()
        mock_view.node_tree = MagicMock()
        mock_view.node_tree.invisibleRootItem.return_value = MagicMock()
        return mock_view
    
    @pytest.fixture
    def mock_node_manager(self):
        """Create a mock NodeManager"""
        mock_nm = MagicMock()
        mock_nm.get_node.return_value = MagicMock()
        return mock_nm
    
    @pytest.fixture
    def mock_session_manager(self):
        """Create a mock SessionManager"""
        mock_sm = MagicMock()
        mock_sm.validate_token.return_value = True
        return mock_sm
    
    @pytest.fixture
    def mock_log_writer(self):
        """Create a mock LogWriter"""
        mock_lw = MagicMock()
        return mock_lw
    
    @pytest.fixture
    def mock_command_queue(self):
        """Create a mock CommandQueue"""
        mock_cq = MagicMock()
        return mock_cq
    
    @pytest.fixture
    def mock_fbc_service(self):
        """Create a mock FbcCommandService"""
        mock_fbc = MagicMock()
        return mock_fbc
    
    @pytest.fixture
    def mock_rpc_service(self):
        """Create a mock RpcCommandService"""
        mock_rpc = MagicMock()
        return mock_rpc
    
    @pytest.fixture
    def mock_context_menu_service(self):
        """Create a mock ContextMenuService"""
        mock_cm = MagicMock()
        return mock_cm
    
    @pytest.fixture
    def mock_bstool_service(self):
        """Create a mock BsToolService"""
        mock_bs = MagicMock()
        return mock_bs
    
    @pytest.fixture
    def presenter(self, mock_view, mock_node_manager, mock_session_manager, mock_log_writer, 
                  mock_command_queue, mock_fbc_service, mock_rpc_service, mock_context_menu_service, mock_bstool_service):
        """Create a NodeTreePresenter instance with mocked dependencies"""
        return NodeTreePresenter(
            view=mock_view,
            node_manager=mock_node_manager,
            session_manager=mock_session_manager,
            log_writer=mock_log_writer,
            command_queue=mock_command_queue,
            fbc_service=mock_fbc_service,
            rpc_service=mock_rpc_service,
            context_menu_service=mock_context_menu_service,
            bstool_service=mock_bstool_service
        )
    
    def test_set_node_color_success(self, presenter):
        """Test set_node_color method sets the correct color for a node"""
        # Setup
        mock_item = MagicMock()
        mock_root_item = MagicMock()
        mock_root_item.childCount.return_value = 1
        mock_root_item.child.return_value = mock_item
        mock_item.data.return_value = {"type": "node", "node_name": "AP01m"}
        mock_node_tree = presenter.view.node_tree
        mock_node_tree.invisibleRootItem.return_value = mock_root_item
        mock_root_item.childCount.return_value = 1
        mock_root_item.child.return_value = mock_item
        mock_item.data.return_value = {"type": "node", "node_name": "AP01m"}
        
        # Execute
        presenter.set_node_color("AP01m", QColor("green"))
        
        # Verify
        mock_item.setForeground.assert_called_with(0, QColor("green"))
    
    def test_set_node_color_no_match(self, presenter):
        """Test set_node_color method when no node is found"""
        # Setup
        mock_root_item = MagicMock()
        mock_root_item.childCount.return_value = 0
        mock_node_tree = presenter.view.node_tree
        mock_node_tree.invisibleRootItem.return_value = mock_root_item
        
        # Execute
        presenter.set_node_color("NonExistentNode", QColor("red"))
        
        # Verify no setForeground is called
        mock_item = MagicMock()
        mock_item.setForeground.assert_not_called()
    
    def test_handle_command_and_log_completion_success(self, presenter):
        """Test handle_command_and_log_completion for successful case"""
        # Setup
        mock_token = MagicMock()
        mock_token.name = "AP01m"
        
        # Execute
        with patch.object(presenter, 'set_node_color') as mock_set_color:
            presenter.handle_command_and_log_completion("test_command", "result", True, mock_token, True)
            
        # Verify
        mock_set_color.assert_called_with("AP01m", QColor("green"))
    
    def test_handle_command_and_log_completion_failure(self, presenter):
        """Test handle_command_and_log_completion for failure case"""
        # Setup
        mock_token = MagicMock()
        mock_token.name = "AP01m"
        
        # Execute
        with patch.object(presenter, 'set_node_color') as mock_set_color:
            presenter.handle_command_and_log_completion("test_command", "result", False, mock_token, True)
            
        # Verify
        mock_set_color.assert_called_with("AP01m", QColor("red"))
    
    def test_handle_command_and_log_completion_log_failure(self, presenter):
        """Test handle_command_and_log_completion when log fails but command succeeds"""
        # Setup
        mock_token = MagicMock()
        mock_token.name = "AP01m"
        
        # Execute
        with patch.object(presenter, 'set_node_color') as mock_set_color:
            presenter.handle_command_and_log_completion("test_command", "result", True, mock_token, False)
            
        # Verify
        mock_set_color.assert_called_with("AP01m", QColor("red"))
    
    def test_handle_log_write_completion_success(self, presenter):
        """Test handle_log_write_completion for successful log write"""
        # Setup
        with patch.object(presenter, 'set_node_color') as mock_set_color:
            presenter.handle_log_write_completion("AP01m", "token_id", True)
            
        # Verify
        mock_set_color.assert_called_with("AP01m", QColor("green"))
    
    def test_handle_log_write_completion_failure(self, presenter):
        """Test handle_log_write_completion for failed log write"""
        # Setup
        with patch.object(presenter, 'set_node_color') as mock_set_color:
            presenter.handle_log_write_completion("AP01m", "token_id", False)
            
        # Verify
        mock_set_color.assert_called_with("AP01m", QColor("red"))