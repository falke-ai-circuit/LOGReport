"""
Test auto-connect initialization bug fix.

Verifies that auto-connect works on first Print All Nodes press
without requiring a prior manual connection by reading IP/port from telnet_tab UI.
"""

import pytest
from unittest.mock import MagicMock, patch
from src.commander.presenters.node_tree_presenter import NodeTreePresenter


class TestAutoConnectInitialization:
    """Test suite for auto-connect initialization from telnet_tab UI."""
    
    @pytest.fixture
    def mock_dependencies(self):
        """Create mock dependencies for NodeTreePresenter."""
        view = MagicMock()
        node_manager = MagicMock()
        session_manager = MagicMock()
        log_writer = MagicMock()
        command_queue = MagicMock()
        fbc_service = MagicMock()
        rpc_service = MagicMock()
        context_menu_service = MagicMock()
        bstool_service = MagicMock()
        
        return {
            'view': view,
            'node_manager': node_manager,
            'session_manager': session_manager,
            'log_writer': log_writer,
            'command_queue': command_queue,
            'fbc_service': fbc_service,
            'rpc_service': rpc_service,
            'context_menu_service': context_menu_service,
            'bstool_service': bstool_service
        }
    
    @pytest.fixture
    def mock_telnet_service(self):
        """Create mock TelnetService."""
        telnet_service = MagicMock()
        telnet_service.debugger_ip_address = None  # Simulate fresh app startup
        telnet_service.debugger_port = None
        telnet_service._ensure_debugger_connection.return_value = True
        return telnet_service
    
    def test_auto_connect_initializes_ip_port_from_callback(self, mock_dependencies, mock_telnet_service):
        """
        Test that auto-connect initializes debugger IP/port from callback before connection attempt.
        
        Scenario: Fresh app startup, no manual connection yet, IP/port available in telnet_tab UI
        Expected: Auto-connect reads IP/port from callback, initializes telnet_service, connects successfully
        """
        # ARRANGE: Create callback that returns IP/port from UI
        get_connection_info_callback = MagicMock(return_value=("192.168.18.1", 1234))
        
        # Create presenter with telnet_service and callback
        presenter = NodeTreePresenter(
            **mock_dependencies,
            telnet_service=mock_telnet_service,
            get_connection_info_callback=get_connection_info_callback
        )
        
        # Setup node manager to return nodes for processing
        mock_dependencies['node_manager'].log_root = "/fake/logs"
        mock_dependencies['node_manager'].scan_log_files = MagicMock()
        mock_dependencies['node_manager'].get_all_nodes.return_value = [
            MagicMock(node_id="AP01M", logs={'FBC': {'path': 'test.log'}})
        ]
        
        # ACT: Trigger Print All Nodes
        presenter.process_all_nodes_print_commands()
        
        # ASSERT: Callback was called to get IP/port
        get_connection_info_callback.assert_called_once()
        
        # ASSERT: Telnet service was initialized with IP/port from callback
        assert mock_telnet_service.debugger_ip_address == "192.168.18.1"
        assert mock_telnet_service.debugger_port == 1234
        
        # ASSERT: Connection was attempted with initialized IP/port
        mock_telnet_service._ensure_debugger_connection.assert_called_once()
    
    def test_auto_connect_skips_initialization_if_already_set(self, mock_dependencies, mock_telnet_service):
        """
        Test that auto-connect skips initialization if debugger IP/port already set.
        
        Scenario: After first manual connection, debugger_ip_address already populated
        Expected: Auto-connect does not call callback, uses existing IP/port
        """
        # ARRANGE: Set debugger IP/port (simulating prior manual connection)
        mock_telnet_service.debugger_ip_address = "192.168.18.1"
        mock_telnet_service.debugger_port = 1234
        
        get_connection_info_callback = MagicMock(return_value=("192.168.18.1", 1234))
        
        presenter = NodeTreePresenter(
            **mock_dependencies,
            telnet_service=mock_telnet_service,
            get_connection_info_callback=get_connection_info_callback
        )
        
        mock_dependencies['node_manager'].log_root = "/fake/logs"
        mock_dependencies['node_manager'].scan_log_files = MagicMock()
        mock_dependencies['node_manager'].get_all_nodes.return_value = [
            MagicMock(node_id="AP01M", logs={'FBC': {'path': 'test.log'}})
        ]
        
        # ACT: Trigger Print All Nodes
        presenter.process_all_nodes_print_commands()
        
        # ASSERT: Callback was NOT called (IP/port already set)
        get_connection_info_callback.assert_not_called()
        
        # ASSERT: Connection was attempted with existing IP/port
        mock_telnet_service._ensure_debugger_connection.assert_called_once()
    
    def test_auto_connect_handles_missing_callback(self, mock_dependencies, mock_telnet_service):
        """
        Test that auto-connect handles missing callback gracefully.
        
        Scenario: No callback provided (legacy initialization)
        Expected: Auto-connect attempts connection with existing IP/port (may fail if None)
        """
        # ARRANGE: No callback provided
        presenter = NodeTreePresenter(
            **mock_dependencies,
            telnet_service=mock_telnet_service,
            get_connection_info_callback=None
        )
        
        mock_dependencies['node_manager'].log_root = "/fake/logs"
        mock_dependencies['node_manager'].scan_log_files = MagicMock()
        mock_dependencies['node_manager'].get_all_nodes.return_value = [
            MagicMock(node_id="AP01M", logs={'FBC': {'path': 'test.log'}})
        ]
        
        # Mock connection to return False (will fail due to None IP/port)
        mock_telnet_service._ensure_debugger_connection.return_value = False
        
        # ACT: Trigger Print All Nodes
        presenter.process_all_nodes_print_commands()
        
        # ASSERT: Connection was attempted (will fail due to None IP/port)
        mock_telnet_service._ensure_debugger_connection.assert_called_once()
    
    def test_auto_connect_handles_empty_ip_from_callback(self, mock_dependencies, mock_telnet_service):
        """
        Test that auto-connect handles empty IP/port from callback.
        
        Scenario: Callback returns empty/None IP/port (user hasn't configured yet)
        Expected: Auto-connect skips initialization, attempts connection with None IP (will fail)
        """
        # ARRANGE: Callback returns empty IP/port
        get_connection_info_callback = MagicMock(return_value=("", 0))
        
        presenter = NodeTreePresenter(
            **mock_dependencies,
            telnet_service=mock_telnet_service,
            get_connection_info_callback=get_connection_info_callback
        )
        
        mock_dependencies['node_manager'].log_root = "/fake/logs"
        mock_dependencies['node_manager'].scan_log_files = MagicMock()
        mock_dependencies['node_manager'].get_all_nodes.return_value = [
            MagicMock(node_id="AP01M", logs={'FBC': {'path': 'test.log'}})
        ]
        
        # Mock connection to return False (will fail due to None IP/port)
        mock_telnet_service._ensure_debugger_connection.return_value = False
        
        # ACT: Trigger Print All Nodes
        presenter.process_all_nodes_print_commands()
        
        # ASSERT: Callback was called
        get_connection_info_callback.assert_called_once()
        
        # ASSERT: Telnet service was NOT initialized (empty values)
        assert mock_telnet_service.debugger_ip_address is None
        assert mock_telnet_service.debugger_port is None
        
        # ASSERT: Connection was still attempted (will fail)
        mock_telnet_service._ensure_debugger_connection.assert_called_once()
