"""
Tests for the Print All Nodes button functionality.
Tests the bulk operation that executes print commands for all nodes sequentially.
"""

import pytest
import sys
import os
from unittest.mock import MagicMock, patch, call

# Add src directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'src')))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
from PyQt6.QtTest import QTest

from commander.ui.node_tree_view import NodeTreeView
from commander.presenters.node_tree_presenter import NodeTreePresenter
from commander.models import Node, NodeToken
from commander.node_manager import NodeManager


# Mock QApplication for PyQt5 tests
@pytest.fixture(scope='session', autouse=True)
def qapplication_fixture():
    """Create QApplication for PyQt5 tests"""
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    yield app
    # Note: We don't quit the app here as it may be needed for other tests


class TestPrintAllNodesButton:
    """Test suite for the Print All Nodes button feature"""

    @pytest.fixture
    def node_tree_view(self):
        """Create a NodeTreeView instance for testing"""
        return NodeTreeView()

    @pytest.fixture
    def mock_node_manager(self):
        """Create a mock NodeManager with test nodes"""
        manager = MagicMock(spec=NodeManager)
        
        # Create test nodes with various token types
        node1 = Node(
            name="AP01M",
            ip_address="10.0.0.1",
            tokens=[
                NodeToken(token_id="162", token_type="FBC", node_name="AP01M"),
                NodeToken(token_id="163", token_type="RPC", node_name="AP01M"),
            ],
            status="online"
        )
        
        node2 = Node(
            name="AP02M",
            ip_address="10.0.0.2",
            tokens=[
                NodeToken(token_id="164", token_type="FBC", node_name="AP02M"),
            ],
            status="online"
        )
        
        node3 = Node(
            name="AP03M",
            ip_address="10.0.0.3",
            tokens=[
                NodeToken(token_id="165", token_type="RPC", node_name="AP03M"),
            ],
            status="online"
        )
        
        manager.get_all_nodes.return_value = [node1, node2, node3]
        manager.get_node.side_effect = lambda name: {
            "AP01M": node1,
            "AP02M": node2,
            "AP03M": node3
        }.get(name)
        
        return manager

    @pytest.fixture
    def node_tree_presenter(self, node_tree_view, mock_node_manager):
        """Create a NodeTreePresenter with mocked dependencies"""
        mock_session_manager = MagicMock()
        mock_log_writer = MagicMock()
        mock_command_queue = MagicMock()
        mock_fbc_service = MagicMock()
        mock_rpc_service = MagicMock()
        mock_context_menu_service = MagicMock()
        mock_bstool_service = MagicMock()
        
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

    def test_print_all_nodes_button_exists(self, node_tree_view):
        """Test that the Print All Nodes button is present in the UI"""
        assert hasattr(node_tree_view, 'print_all_nodes_btn')
        assert node_tree_view.print_all_nodes_btn is not None
        assert node_tree_view.print_all_nodes_btn.text() == "Print All Nodes"

    def test_print_all_nodes_button_has_tooltip(self, node_tree_view):
        """Test that the button has a helpful tooltip"""
        tooltip = node_tree_view.print_all_nodes_btn.toolTip()
        assert "Execute print commands" in tooltip
        assert "sequentially" in tooltip

    def test_print_all_nodes_signal_emitted(self, node_tree_view, qtbot):
        """Test that clicking the button emits the print_all_nodes_clicked signal"""
        # Track signal emissions
        signal_emitted = []
        node_tree_view.print_all_nodes_clicked.connect(lambda: signal_emitted.append(True))
        
        # Click the button
        qtbot.mouseClick(node_tree_view.print_all_nodes_btn, Qt.MouseButton.LeftButton)
        
        # Verify signal was emitted
        assert len(signal_emitted) == 1

    def test_process_all_nodes_print_commands_calls_per_node_handler(
        self, node_tree_presenter, mock_node_manager
    ):
        """Test that process_all_nodes_print_commands iterates through all nodes"""
        # Mock the per-node print command method to avoid actual execution
        with patch.object(
            node_tree_presenter, 
            'process_node_print_commands',
            return_value=None
        ) as mock_process_node:
            
            # Call the bulk handler
            node_tree_presenter.process_all_nodes_print_commands()
            
            # Verify get_all_nodes was called
            mock_node_manager.get_all_nodes.assert_called_once()
            
            # Verify process_node_print_commands was called for each node
            assert mock_process_node.call_count == 3
            mock_process_node.assert_any_call("AP01M")
            mock_process_node.assert_any_call("AP02M")
            mock_process_node.assert_any_call("AP03M")

    def test_process_all_nodes_with_no_nodes(self, node_tree_presenter, mock_node_manager):
        """Test that the handler gracefully handles empty node list"""
        # Set up empty node list
        mock_node_manager.get_all_nodes.return_value = []
        
        # This should not raise an exception
        node_tree_presenter.process_all_nodes_print_commands()
        
        # Verify get_all_nodes was called
        mock_node_manager.get_all_nodes.assert_called_once()

    def test_process_all_nodes_continues_after_failure(
        self, node_tree_presenter, mock_node_manager
    ):
        """Test that processing continues even if one node fails"""
        call_count = [0]
        
        def mock_process_with_failure(node_name):
            call_count[0] += 1
            if node_name == "AP02M":
                raise Exception("Simulated node processing error")
        
        # Mock the per-node handler to fail for AP02M
        with patch.object(
            node_tree_presenter,
            'process_node_print_commands',
            side_effect=mock_process_with_failure
        ):
            # This should not stop processing other nodes
            node_tree_presenter.process_all_nodes_print_commands()
            
            # Verify all nodes were attempted (3 calls despite 1 failure)
            assert call_count[0] == 3

    def test_process_all_nodes_emits_status_messages(self, node_tree_presenter):
        """Test that status messages are emitted during bulk processing"""
        status_messages = []
        node_tree_presenter.status_message_signal.connect(
            lambda msg, timeout: status_messages.append(msg)
        )
        
        # Mock the per-node handler to prevent actual execution
        with patch.object(
            node_tree_presenter,
            'process_node_print_commands',
            return_value=None
        ):
            node_tree_presenter.process_all_nodes_print_commands()
        
        # Verify status messages were emitted
        assert len(status_messages) > 0
        assert any("Starting print command execution for ALL nodes" in msg for msg in status_messages)
        assert any("Processing" in msg and "nodes" in msg for msg in status_messages)
        assert any("complete" in msg for msg in status_messages)

    def test_process_all_nodes_provides_aggregate_statistics(self, node_tree_presenter):
        """Test that final summary includes success/failure counts"""
        status_messages = []
        node_tree_presenter.status_message_signal.connect(
            lambda msg, timeout: status_messages.append(msg)
        )
        
        # Mock to simulate 2 successes and 1 failure
        call_count = [0]
        
        def mock_process_with_partial_failure(node_name):
            call_count[0] += 1
            if call_count[0] == 2:
                raise Exception("Simulated failure")
        
        with patch.object(
            node_tree_presenter,
            'process_node_print_commands',
            side_effect=mock_process_with_partial_failure
        ):
            node_tree_presenter.process_all_nodes_print_commands()
        
        # Find the summary message
        summary_messages = [msg for msg in status_messages if "complete" in msg and "successful" in msg]
        assert len(summary_messages) > 0
        
        summary = summary_messages[0]
        assert "2 successful" in summary
        assert "1 failed" in summary
        assert "total: 3" in summary

    def test_button_integration_with_presenter(
        self, node_tree_view, node_tree_presenter, qtbot
    ):
        """Test end-to-end integration: button click -> signal -> presenter method"""
        # Track whether the presenter method was called
        method_called = []
        
        # Connect the signal to the presenter method
        node_tree_view.print_all_nodes_clicked.connect(
            lambda: method_called.append(True)
        )
        
        # Click the button
        qtbot.mouseClick(node_tree_view.print_all_nodes_btn, Qt.MouseButton.LeftButton)
        
        # Verify the handler was invoked
        assert len(method_called) == 1


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

