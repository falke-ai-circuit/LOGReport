"""
Test suite for node-level print command execution.

This test suite validates:
1. Node context menu shows "Execute All Print Commands for [nodename]"
2. Only Print commands execute (FBC, RPC print, LOG display - NO BsTool)
3. LOG subgroup context menu shows "Print All LOG Tokens for [nodename]"
4. Error handling works correctly
5. Status messages are emitted properly
"""

import pytest
from unittest.mock import MagicMock, patch, call
from PyQt5.QtWidgets import QApplication, QMenu, QTreeWidgetItem
from PyQt5.QtCore import Qt

from commander.services.context_menu_service import ContextMenuService
from commander.services.context_menu_filter import ContextMenuFilterService
from commander.presenters.node_tree_presenter import NodeTreePresenter
from commander.node_manager import NodeManager
from commander.models import Node, NodeToken


@pytest.fixture
def qapp(qapp):
    """Fixture to ensure QApplication is initialized."""
    return qapp


@pytest.fixture
def node_manager():
    """Create a mock node manager with test data."""
    manager = MagicMock(spec=NodeManager)
    
    # Create test node with FBC, RPC, and LOG tokens
    test_node = Node(
        name="AP01m",
        ip_address="192.168.0.11",
        tokens={
            "FBC": [
                NodeToken(token_id="162", token_type="FBC", name="AP01m", log_path="/logs/AP01m_162.fbc.log"),
                NodeToken(token_id="163", token_type="FBC", name="AP01m", log_path="/logs/AP01m_163.fbc.log"),
            ],
            "RPC": [
                NodeToken(token_id="162", token_type="RPC", name="AP01m", log_path="/logs/AP01m_162.rpc.log"),
                NodeToken(token_id="163", token_type="RPC", name="AP01m", log_path="/logs/AP01m_163.rpc.log"),
            ],
            "LOG": [
                NodeToken(token_id="AP01m.log", token_type="LOG", name="AP01m", log_path="/logs/AP01m.log"),
            ]
        }
    )
    
    manager.get_node.return_value = test_node
    return manager


@pytest.fixture
def context_menu_filter():
    """Create a mock context menu filter service."""
    filter_service = MagicMock(spec=ContextMenuFilterService)
    filter_service.should_show_command.return_value = True
    return filter_service


@pytest.fixture
def context_menu_service(node_manager, context_menu_filter):
    """Create context menu service with mocked dependencies."""
    return ContextMenuService(node_manager, context_menu_filter)


class TestNodePrintCommands:
    """Test suite for node-level print command execution."""
    
    def test_node_context_menu_shows_print_commands_option(
        self, 
        context_menu_service, 
        context_menu_filter,
        qapp
    ):
        """
        Test that the context menu displays 'Execute All Print Commands' action for node items.
        """
        # Create test data for node item
        node_data = {
            "type": "node",
            "node_name": "AP01m"
        }
        
        # Create a mock menu
        menu = QMenu()
        
        # Mock the presenter
        mock_presenter = MagicMock()
        context_menu_service.set_presenter(mock_presenter)
        
        # Mock the context menu filter to allow print commands
        context_menu_filter.should_show_command.return_value = True
        
        # Show context menu
        result = context_menu_service.show_context_menu(
            menu=menu,
            item_data=node_data,
            position=None
        )
        
        # Verify menu was populated
        assert result is True
        assert len(menu.actions()) > 0
        
        # Verify the print command action was added
        action_texts = [action.text() for action in menu.actions()]
        assert any("Execute All Print Commands" in text for text in action_texts)
        assert "Execute All Print Commands for AP01m" in action_texts
        
        # Verify filter was called with correct parameters
        context_menu_filter.should_show_command.assert_called_once_with(
            node_name="AP01m",
            section_type=None,
            command_type="execute_all_hierarchical",
            command_category="node"
        )
    
    def test_log_subgroup_context_menu_shows_print_all_option(
        self,
        context_menu_service,
        context_menu_filter,
        node_manager,
        qapp
    ):
        """
        Test that LOG subgroup context menu displays 'Print All LOG Tokens' action.
        """
        # Create test data for LOG subgroup item
        log_data = {
            "type": "section",
            "section_type": "LOG",
            "node": "AP01m",
            "tokens": []
        }
        
        # Create a mock menu
        menu = QMenu()
        
        # Mock the presenter
        mock_presenter = MagicMock()
        context_menu_service.set_presenter(mock_presenter)
        
        # Mock the context menu filter
        context_menu_filter.should_show_command.return_value = True
        
        # Mock get_node_tokens to return LOG tokens
        context_menu_service.get_node_tokens = MagicMock(return_value=[
            NodeToken(token_id="AP01m.log", token_type="LOG", name="AP01m", log_path="/logs/AP01m.log"),
        ])
        
        # Show context menu
        result = context_menu_service.show_context_menu(
            menu=menu,
            item_data=log_data,
            position=None
        )
        
        # Verify menu was populated
        assert result is True
        assert len(menu.actions()) > 0
        
        # Verify the print action was added for LOG
        action_texts = [action.text() for action in menu.actions()]
        assert any("Print All LOG Tokens" in text for text in action_texts)
    
    def test_process_node_print_commands_executes_only_print_operations(
        self,
        node_manager,
        qapp
    ):
        """
        Test that process_node_print_commands only executes Print commands (no BsTool).
        """
        # Create mock dependencies
        mock_view = MagicMock()
        mock_session_manager = MagicMock()
        mock_log_writer = MagicMock()
        mock_command_queue = MagicMock()
        mock_fbc_service = MagicMock()
        mock_rpc_service = MagicMock()
        mock_context_menu_service = MagicMock()
        mock_bstool_service = MagicMock()
        
        # Create presenter
        presenter = NodeTreePresenter(
            view=mock_view,
            node_manager=node_manager,
            session_manager=mock_session_manager,
            log_writer=mock_log_writer,
            command_queue=mock_command_queue,
            fbc_service=mock_fbc_service,
            rpc_service=mock_rpc_service,
            context_menu_service=mock_context_menu_service,
            bstool_service=mock_bstool_service
        )
        
        # Execute print commands
        presenter.process_node_print_commands("AP01m")
        
        # Verify FBC commands were queued
        assert mock_fbc_service.queue_fieldbus_command.call_count == 2
        mock_fbc_service.queue_fieldbus_command.assert_any_call("AP01m", "162", None)
        mock_fbc_service.queue_fieldbus_command.assert_any_call("AP01m", "163", None)
        
        # Verify RPC print commands were queued
        assert mock_rpc_service.queue_rpc_command.call_count == 2
        mock_rpc_service.queue_rpc_command.assert_any_call("AP01m", "162", "print", None)
        mock_rpc_service.queue_rpc_command.assert_any_call("AP01m", "163", "print", None)
        
        # Verify BsTool was NOT called (print-only mode)
        mock_bstool_service.execute_bstool.assert_not_called()
        
        # Verify command queue was started
        mock_command_queue.start_processing.assert_called()
    
    def test_process_all_log_subgroup_commands_prints_log_files(
        self,
        node_manager,
        qapp
    ):
        """
        Test that process_all_log_subgroup_commands prints LOG files without BsTool.
        """
        # Create mock dependencies
        mock_view = MagicMock()
        mock_session_manager = MagicMock()
        mock_log_writer = MagicMock()
        mock_command_queue = MagicMock()
        mock_fbc_service = MagicMock()
        mock_rpc_service = MagicMock()
        mock_context_menu_service = MagicMock()
        mock_bstool_service = MagicMock()
        
        # Create presenter
        presenter = NodeTreePresenter(
            view=mock_view,
            node_manager=node_manager,
            session_manager=mock_session_manager,
            log_writer=mock_log_writer,
            command_queue=mock_command_queue,
            fbc_service=mock_fbc_service,
            rpc_service=mock_rpc_service,
            context_menu_service=mock_context_menu_service,
            bstool_service=mock_bstool_service
        )
        
        # Create mock item with LOG tokens
        mock_item = MagicMock()
        mock_item.data = {
            "type": "section",
            "section_type": "LOG",
            "node": "AP01m",
            "tokens": [
                NodeToken(token_id="AP01m.log", token_type="LOG", name="AP01m", log_path="/logs/AP01m.log"),
            ]
        }
        
        # Execute LOG subgroup commands
        with patch.object(presenter, 'log_file_selected_signal') as mock_signal:
            presenter.process_all_log_subgroup_commands(mock_item)
            
            # Verify log file was "printed" (signal emitted)
            mock_signal.emit.assert_called_once_with("AP01m.log")
        
        # Verify BsTool was NOT called
        mock_bstool_service.execute_bstool.assert_not_called()
    
    def test_print_commands_emit_correct_status_messages(
        self,
        node_manager,
        qapp
    ):
        """
        Test that status messages correctly indicate print command execution.
        """
        # Create mock dependencies
        mock_view = MagicMock()
        mock_session_manager = MagicMock()
        mock_log_writer = MagicMock()
        mock_command_queue = MagicMock()
        mock_fbc_service = MagicMock()
        mock_rpc_service = MagicMock()
        mock_context_menu_service = MagicMock()
        mock_bstool_service = MagicMock()
        
        # Create presenter
        presenter = NodeTreePresenter(
            view=mock_view,
            node_manager=node_manager,
            session_manager=mock_session_manager,
            log_writer=mock_log_writer,
            command_queue=mock_command_queue,
            fbc_service=mock_fbc_service,
            rpc_service=mock_rpc_service,
            context_menu_service=mock_context_menu_service,
            bstool_service=mock_bstool_service
        )
        
        # Capture status messages
        status_messages = []
        presenter.status_message_signal.connect(lambda msg, dur: status_messages.append(msg))
        
        # Execute print commands
        presenter.process_node_print_commands("AP01m")
        
        # Verify status messages mention "print" not "hierarchical"
        assert any("print" in msg.lower() for msg in status_messages)
        assert any("Phase 1/3: Printing 2 FBC tokens" in msg for msg in status_messages)
        assert any("Phase 2/3: Printing 2 RPC tokens" in msg for msg in status_messages)
        assert any("Phase 3/3: Printing 1 LOG files" in msg for msg in status_messages)
        assert any("Print command execution complete" in msg for msg in status_messages)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
