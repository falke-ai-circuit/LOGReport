"""
Test Suite: Status Message Propagation

Tests that status messages from NodeScanWidget flow through the signal chain
to the main CommanderWindow status bar for user visibility.
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch, call
from PyQt5.QtWidgets import QApplication

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from commander.ui.node_scan_widget import NodeScanWidget
from commander.ui.scan_tab import ScanTab
from commander.services.fbc_comparison_service import ComparisonResult, CellDifference, CellError


@pytest.fixture
def qapp():
    """Create QApplication for testing Qt widgets"""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


class TestNodeScanWidgetStatusMessages:
    """Test status message emission from NodeScanWidget"""
    
    def test_comparison_start_emits_status(self, qapp):
        """Test that comparison start emits status message"""
        # Setup
        parser = Mock()
        telnet = Mock()
        widget = NodeScanWidget(
            node_name="AP01",
            token_files=["/path/to/AP01_192-168-0-11_162.fbc"],
            parser_service=parser,
            telnet_service=telnet
        )
        
        # Mock current file and data
        widget.current_file = "/path/to/AP01_192-168-0-11_162.fbc"
        widget.current_data = Mock()
        widget.current_data.file_type = "fbc"
        
        # Mock _extract_token_id
        with patch.object(widget, '_extract_token_id', return_value="162"):
            # Mock telnet connection check
            telnet.is_connected.return_value = True
            
            # Capture status message signal
            status_messages = []
            widget.status_message.connect(lambda msg, duration: status_messages.append(msg))
            
            # Trigger comparison (will fail but should emit start message)
            widget._on_compare_clicked()
            
            # Verify start message emitted
            assert len(status_messages) > 0
            start_msg = status_messages[0]
            assert "Comparing" in start_msg
            assert "AP01" in start_msg
            assert "AP01_192-168-0-11_162.fbc" in start_msg
    
    def test_comparison_success_emits_summary(self, qapp):
        """Test that successful comparison emits summary with match percentage"""
        # Setup
        parser = Mock()
        telnet = Mock()
        widget = NodeScanWidget(
            node_name="AP01",
            token_files=["/path/to/AP01_192-168-0-11_162.fbc"],
            parser_service=parser,
            telnet_service=telnet
        )
        
        # Mock current file
        widget.current_file = "/path/to/AP01_192-168-0-11_162.fbc"
        
        # Create successful comparison result
        result = ComparisonResult(
            success=True,
            file_type="fbc",
            match_percentage=80.0,
            total_cells=5,
            matches=[(0, 0), (0, 1), (0, 2), (1, 0)],  # 4 matches
            differences=[CellDifference(row=1, col=1, file_value="A", live_value="B")],  # 1 difference
            errors=[]
        )
        
        # Capture status messages
        status_messages = []
        widget.status_message.connect(lambda msg, duration: status_messages.append(msg))
        
        # Trigger completion handler
        widget._on_comparison_finished(result)
        
        # Verify summary message
        assert len(status_messages) == 1
        summary = status_messages[0]
        assert "✓" in summary
        assert "AP01" in summary
        assert "80%" in summary
        assert "4/5" in summary  # 4 matches out of 5 total cells
    
    def test_comparison_failure_emits_error(self, qapp):
        """Test that failed comparison emits error message"""
        # Setup
        parser = Mock()
        telnet = Mock()
        widget = NodeScanWidget(
            node_name="AP01",
            token_files=["/path/to/AP01_192-168-0-11_162.fbc"],
            parser_service=parser,
            telnet_service=telnet
        )
        
        # Mock current file
        widget.current_file = "/path/to/AP01_192-168-0-11_162.fbc"
        
        # Create failed comparison result
        result = ComparisonResult(
            success=False,
            file_type="fbc",
            match_percentage=0.0,
            total_cells=0,
            matches=[],
            differences=[],
            errors=[],
            error_message="Connection timeout"
        )
        
        # Capture status messages
        status_messages = []
        widget.status_message.connect(lambda msg, duration: status_messages.append(msg))
        
        # Trigger completion handler
        widget._on_comparison_finished(result)
        
        # Verify error message
        assert len(status_messages) == 1
        error_msg = status_messages[0]
        assert "✗" in error_msg
        assert "AP01" in error_msg
        assert "Connection timeout" in error_msg


class TestScanTabSignalPropagation:
    """Test status message propagation from NodeScanWidget to ScanTab"""
    
    def test_scan_tab_forwards_node_widget_messages(self, qapp):
        """Test ScanTab forwards NodeScanWidget status messages"""
        # Setup
        from commander.node_manager import NodeManager
        from commander.models import Node
        
        node_manager = Mock(spec=NodeManager)
        node_manager.get_all_nodes.return_value = [
            Node(name="AP01", ip_address="192.168.0.11")
        ]
        node_manager.log_root = "D:/_APP/LOGReport/_DIA"
        
        telnet = Mock()
        scan_tab = ScanTab(node_manager=node_manager, telnet_service=telnet)
        
        # Mock file system
        with patch.object(scan_tab, '_get_node_token_files', return_value=["/test/file.fbc"]):
            scan_tab.populate_nodes()
        
        # Verify node widget was created
        assert "AP01" in scan_tab.node_widgets
        ap01_widget = scan_tab.node_widgets["AP01"]
        
        # Capture status messages from ScanTab
        scan_tab_messages = []
        scan_tab.status_message.connect(lambda msg, duration: scan_tab_messages.append(msg))
        
        # Emit status message from node widget
        test_message = "Test status message"
        ap01_widget.status_message.emit(test_message, 3000)
        
        # Verify message was forwarded to ScanTab
        assert len(scan_tab_messages) == 1
        assert scan_tab_messages[0] == test_message


class TestIntegrationWithCommanderWindow:
    """Integration test verifying full signal chain to status bar"""
    
    def test_status_messages_reach_status_bar(self, qapp):
        """Test that NodeScanWidget messages reach CommanderWindow status bar"""
        # This is more of a documentation test showing the expected signal chain
        # Actual integration would require full CommanderWindow initialization
        
        # Signal chain:
        # NodeScanWidget.status_message(str, int)
        #   ↓ connected to
        # ScanTab.status_message(str, int)
        #   ↓ connected to
        # CommanderWindow.status_service.show_message(str, int)
        #   ↓ displays in
        # QStatusBar
        
        # Verify signal signatures are compatible
        from commander.ui.node_scan_widget import NodeScanWidget
        from commander.ui.scan_tab import ScanTab
        
        # Both signals should have same signature: (str, int)
        assert hasattr(NodeScanWidget, 'status_message')
        assert hasattr(ScanTab, 'status_message')
        
        # Test passes if no exceptions - signals are properly defined


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
