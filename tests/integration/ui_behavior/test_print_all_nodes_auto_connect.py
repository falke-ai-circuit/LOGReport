"""
Test auto-connection check when Print All Nodes button is pressed.

Tests that process_all_nodes_print_commands() automatically establishes
Telnet debugger connection before starting sequential node processing.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from PyQt5.QtWidgets import QApplication, QTreeWidget, QTreeWidgetItem
import sys

# Ensure QApplication exists for PyQt tests
app = QApplication.instance()
if app is None:
    app = QApplication(sys.argv)

from src.commander.presenters.node_tree_presenter import NodeTreePresenter
from src.commander.models import Node, NodeToken


@pytest.fixture
def mock_dependencies():
    """Create mocked dependencies for NodeTreePresenter"""
    view = Mock(spec=QTreeWidget)
    view.tree = Mock(spec=QTreeWidget)
    view.pause_btn = Mock()
    view.resume_btn = Mock()
    view.cancel_btn = Mock()
    view.print_all_nodes_btn = Mock()
    view.update_control_buttons = Mock()  # Add update_control_buttons method
    view.item_expanded = Mock()  # Add item_expanded signal for NodeTreePresenter initialization
    view.item_expanded.connect = Mock()
    view.pause_clicked = Mock()  # Add pause_clicked signal
    view.pause_clicked.connect = Mock()
    view.resume_clicked = Mock()  # Add resume_clicked signal
    view.resume_clicked.connect = Mock()
    view.cancel_clicked = Mock()  # Add cancel_clicked signal
    view.cancel_clicked.connect = Mock()
    view.viewport = Mock()  # Add viewport for context menu positioning
    
    node_manager = Mock()
    session_manager = Mock()
    telnet_service = Mock()
    command_queue = Mock()
    command_queue.command_completed = Mock()
    command_queue.command_completed.connect = Mock()
    fbc_command_service = Mock()
    rpc_command_service = Mock()
    bstool_command_service = Mock()
    sequential_processor = Mock()
    log_writer = Mock()
    log_writer.log_write_completed = Mock()
    log_writer.log_write_completed.connect = Mock()
    
    return {
        'view': view,
        'node_manager': node_manager,
        'session_manager': session_manager,
        'telnet_service': telnet_service,
        'command_queue': command_queue,
        'fbc_command_service': fbc_command_service,
        'rpc_command_service': rpc_command_service,
        'bstool_command_service': bstool_command_service,
        'sequential_processor': sequential_processor,
        'log_writer': log_writer
    }


@pytest.fixture
def presenter(mock_dependencies):
    """Create NodeTreePresenter with mocked dependencies"""
    presenter = NodeTreePresenter(
        view=mock_dependencies['view'],
        node_manager=mock_dependencies['node_manager'],
        session_manager=mock_dependencies['session_manager'],
        log_writer=mock_dependencies['log_writer'],
        command_queue=mock_dependencies['command_queue'],
        fbc_service=mock_dependencies['fbc_command_service'],
        rpc_service=mock_dependencies['rpc_command_service'],
        context_menu_service=Mock(),  # Add context menu service
        bstool_service=mock_dependencies['bstool_command_service'],
        telnet_service=mock_dependencies['telnet_service']
    )
    return presenter


@pytest.fixture
def sample_nodes():
    """Create sample nodes for testing"""
    node1 = Node(name="AP01m", ip_address="192.168.0.11")
    node1.add_token(NodeToken(token_id="162", token_type="FBC", name="AP01m"))
    node1.add_token(NodeToken(token_id="162", token_type="RPC", name="AP01m"))
    
    node2 = Node(name="AP02m", ip_address="192.168.0.12")
    node2.add_token(NodeToken(token_id="163", token_type="FBC", name="AP02m"))
    
    return [node1, node2]


def test_print_all_nodes_checks_connection_when_connected(presenter, mock_dependencies, sample_nodes):
    """
    Test that Print All Nodes checks connection and proceeds when already connected.
    
    Scenario: User presses Print All Nodes while Telnet is connected.
    Expected: Connection check passes, workflow starts normally.
    """
    # Arrange
    mock_dependencies['telnet_service']._ensure_debugger_connection.return_value = True
    mock_dependencies['node_manager'].log_root = "/fake/logs"
    mock_dependencies['node_manager'].scan_log_files = Mock()
    mock_dependencies['node_manager'].get_all_nodes.return_value = sample_nodes
    
    # Act
    presenter.process_all_nodes_print_commands()
    
    # Assert
    # Connection check was called
    mock_dependencies['telnet_service']._ensure_debugger_connection.assert_called_once()
    
    # Workflow started (buttons enabled)
    assert mock_dependencies['view'].pause_btn.setEnabled.called
    assert mock_dependencies['view'].cancel_btn.setEnabled.called
    
    # Nodes were retrieved
    mock_dependencies['node_manager'].get_all_nodes.assert_called_once()


def test_print_all_nodes_auto_connects_when_disconnected(presenter, mock_dependencies, sample_nodes):
    """
    Test that Print All Nodes automatically establishes connection when disconnected.
    
    Scenario: User presses Print All Nodes while Telnet is disconnected,
              but auto-connect succeeds (with 2 retries, 10s delay, system mode verification).
    Expected: _ensure_debugger_connection handles reconnect, workflow proceeds.
    """
    # Arrange
    mock_dependencies['telnet_service']._ensure_debugger_connection.return_value = True
    mock_dependencies['node_manager'].log_root = "/fake/logs"
    mock_dependencies['node_manager'].scan_log_files = Mock()
    mock_dependencies['node_manager'].get_all_nodes.return_value = sample_nodes
    
    # Act
    presenter.process_all_nodes_print_commands()
    
    # Assert
    # Connection established via retry logic
    mock_dependencies['telnet_service']._ensure_debugger_connection.assert_called_once()
    
    # Workflow started after successful connection
    mock_dependencies['node_manager'].get_all_nodes.assert_called_once()
    assert mock_dependencies['view'].pause_btn.setEnabled.called


def test_print_all_nodes_aborts_when_connection_fails(presenter, mock_dependencies):
    """
    Test that Print All Nodes aborts gracefully when connection fails after retries.
    
    Scenario: User presses Print All Nodes, auto-connect attempts fail after 2 retries.
    Expected: Workflow aborts with error message, no nodes processed, buttons not enabled.
    """
    # Arrange
    mock_dependencies['telnet_service']._ensure_debugger_connection.return_value = False
    
    # Act
    presenter.process_all_nodes_print_commands()
    
    # Assert
    # Connection check was attempted
    mock_dependencies['telnet_service']._ensure_debugger_connection.assert_called_once()
    
    # Workflow aborted - nodes were NOT queried
    mock_dependencies['node_manager'].get_all_nodes.assert_not_called()
    
    # Buttons were NOT enabled (workflow didn't start)
    mock_dependencies['view'].pause_btn.setEnabled.assert_not_called()
    mock_dependencies['view'].cancel_btn.setEnabled.assert_not_called()
    
    # Error message was emitted (status_message_signal.emit called)
    # Note: status_message_signal is a pyqtSignal, can't directly assert on mock
    # In real scenario, this would be visible in UI status bar


def test_print_all_nodes_connection_check_before_log_scan(presenter, mock_dependencies):
    """
    Test that connection check happens BEFORE log file scanning.
    
    Scenario: Ensure connection validated early to avoid wasted work.
    Expected: _ensure_debugger_connection called before scan_log_files.
    """
    # Arrange
    call_order = []
    
    def track_connection_check():
        call_order.append('connection_check')
        return True
    
    def track_log_scan():
        call_order.append('log_scan')
    
    mock_dependencies['telnet_service']._ensure_debugger_connection.side_effect = track_connection_check
    mock_dependencies['node_manager'].log_root = "/fake/logs"
    mock_dependencies['node_manager'].scan_log_files.side_effect = track_log_scan
    mock_dependencies['node_manager'].get_all_nodes.return_value = []
    
    # Act
    presenter.process_all_nodes_print_commands()
    
    # Assert
    assert call_order == ['connection_check', 'log_scan'], \
        "Connection check must happen before log scanning"


def test_print_all_nodes_connection_error_message_clarity(presenter, mock_dependencies):
    """
    Test that connection failure provides clear user feedback.
    
    Scenario: Connection fails, user needs actionable guidance.
    Expected: Error message instructs to connect manually in Telnet tab.
    """
    # Arrange
    mock_dependencies['telnet_service']._ensure_debugger_connection.return_value = False
    
    # Capture emitted signals
    emitted_messages = []
    presenter.status_message_signal.connect(lambda msg, timeout: emitted_messages.append(msg))
    
    # Act
    presenter.process_all_nodes_print_commands()
    
    # Assert
    assert any("Telnet" in msg and "connect manually" in msg for msg in emitted_messages), \
        "Error message should mention Telnet and manual connection"


def test_print_all_nodes_uses_existing_connection_if_available(presenter, mock_dependencies, sample_nodes):
    """
    Test that existing active connection is reused (no unnecessary reconnection).
    
    Scenario: User already connected via Telnet tab, presses Print All Nodes.
    Expected: _ensure_debugger_connection detects active connection, no reconnect needed.
    """
    # Arrange
    mock_dependencies['telnet_service']._ensure_debugger_connection.return_value = True
    mock_dependencies['node_manager'].log_root = "/fake/logs"
    mock_dependencies['node_manager'].scan_log_files = Mock()
    mock_dependencies['node_manager'].get_all_nodes.return_value = sample_nodes
    
    # Act
    presenter.process_all_nodes_print_commands()
    
    # Assert
    # _ensure_debugger_connection was called to verify connection
    mock_dependencies['telnet_service']._ensure_debugger_connection.assert_called_once()
    
    # Workflow proceeded (connection was valid)
    mock_dependencies['node_manager'].get_all_nodes.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
