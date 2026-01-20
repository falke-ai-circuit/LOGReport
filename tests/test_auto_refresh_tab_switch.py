"""
Test Suite: Auto-Refresh Tab Switching

Tests that auto-refresh pauses when user switches away from Scan tab
and resumes when returning, preventing unnecessary background operations.
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QTimer

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from commander.ui.node_scan_widget import NodeScanWidget
from commander.ui.scan_tab import ScanTab
from commander.ui.session_view import SessionView
from commander.node_manager import NodeManager
from commander.models import Node


@pytest.fixture
def qapp():
    """Create QApplication for testing Qt widgets"""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


class TestNodeScanWidgetPauseResume:
    """Test pause/resume functionality in NodeScanWidget"""
    
    def test_pause_auto_refresh_when_enabled(self, qapp):
        """Test pausing auto-refresh stops timers and sets pause flag"""
        # Setup
        parser = Mock()
        telnet = Mock()
        widget = NodeScanWidget(
            node_name="AP01",
            token_files=["/path/to/file.fbc"],
            parser_service=parser,
            telnet_service=telnet
        )
        
        # Enable auto-refresh
        widget.auto_refresh_checkbox.setChecked(True)
        assert widget.auto_refresh_timer.isActive()
        assert widget._auto_refresh_paused is False
        
        # Pause
        widget.pause_auto_refresh()
        
        # Verify timers stopped and flag set
        assert not widget.auto_refresh_timer.isActive()
        assert not widget.countdown_timer.isActive()
        assert widget._auto_refresh_paused is True
        assert widget.auto_refresh_checkbox.isChecked()  # Checkbox state preserved
    
    def test_pause_when_already_paused_does_nothing(self, qapp):
        """Test pausing already-paused widget is safe"""
        # Setup
        parser = Mock()
        telnet = Mock()
        widget = NodeScanWidget(
            node_name="AP01",
            token_files=["/path/to/file.fbc"],
            parser_service=parser,
            telnet_service=telnet
        )
        
        # Enable and pause
        widget.auto_refresh_checkbox.setChecked(True)
        widget.pause_auto_refresh()
        assert widget._auto_refresh_paused is True
        
        # Pause again (should be safe)
        widget.pause_auto_refresh()
        assert widget._auto_refresh_paused is True
    
    def test_pause_when_disabled_does_nothing(self, qapp):
        """Test pausing when auto-refresh is disabled does nothing"""
        # Setup
        parser = Mock()
        telnet = Mock()
        widget = NodeScanWidget(
            node_name="AP01",
            token_files=["/path/to/file.fbc"],
            parser_service=parser,
            telnet_service=telnet
        )
        
        # Auto-refresh disabled by default
        assert not widget.auto_refresh_checkbox.isChecked()
        assert widget._auto_refresh_paused is False
        
        # Pause (should do nothing)
        widget.pause_auto_refresh()
        
        # Verify no change
        assert widget._auto_refresh_paused is False
    
    def test_resume_auto_refresh_restarts_timers(self, qapp):
        """Test resuming auto-refresh restarts timers and clears pause flag"""
        # Setup
        parser = Mock()
        telnet = Mock()
        widget = NodeScanWidget(
            node_name="AP01",
            token_files=["/path/to/file.fbc"],
            parser_service=parser,
            telnet_service=telnet
        )
        
        # Enable, pause, then resume
        widget.auto_refresh_checkbox.setChecked(True)
        widget.pause_auto_refresh()
        assert widget._auto_refresh_paused is True
        
        widget.resume_auto_refresh()
        
        # Verify timers restarted and flag cleared
        assert widget.auto_refresh_timer.isActive()
        assert widget.countdown_timer.isActive()
        assert widget._auto_refresh_paused is False
        assert widget.auto_refresh_checkbox.isChecked()
    
    def test_resume_when_checkbox_unchecked_does_nothing(self, qapp):
        """Test resuming when checkbox unchecked does nothing"""
        # Setup
        parser = Mock()
        telnet = Mock()
        widget = NodeScanWidget(
            node_name="AP01",
            token_files=["/path/to/file.fbc"],
            parser_service=parser,
            telnet_service=telnet
        )
        
        # Enable, pause, then disable checkbox
        widget.auto_refresh_checkbox.setChecked(True)
        widget.pause_auto_refresh()
        widget.auto_refresh_checkbox.setChecked(False)
        
        # Try to resume (should do nothing)
        widget.resume_auto_refresh()
        
        # Verify timers still stopped
        assert not widget.auto_refresh_timer.isActive()
        assert not widget.countdown_timer.isActive()
    
    def test_is_auto_refresh_active_reflects_state(self, qapp):
        """Test is_auto_refresh_active returns correct state"""
        # Setup
        parser = Mock()
        telnet = Mock()
        widget = NodeScanWidget(
            node_name="AP01",
            token_files=["/path/to/file.fbc"],
            parser_service=parser,
            telnet_service=telnet
        )
        
        # Initially disabled and not paused
        assert not widget.is_auto_refresh_active()
        
        # Enable
        widget.auto_refresh_checkbox.setChecked(True)
        assert widget.is_auto_refresh_active()
        
        # Pause
        widget.pause_auto_refresh()
        assert not widget.is_auto_refresh_active()
        
        # Resume
        widget.resume_auto_refresh()
        assert widget.is_auto_refresh_active()


class TestScanTabNodeSwitch:
    """Test node subtab switching pauses/resumes correct widgets"""
    
    def test_node_tab_switch_pauses_inactive_resumes_active(self, qapp):
        """Test switching node subtabs pauses old, resumes new"""
        # Setup
        node_manager = Mock(spec=NodeManager)
        node_manager.get_all_nodes.return_value = [
            Node(name="AP01", ip_address="192.168.0.11"),
            Node(name="AP02", ip_address="192.168.0.12")
        ]
        node_manager.log_root = "D:/_APP/LOGReport/_DIA"
        
        telnet = Mock()
        scan_tab = ScanTab(node_manager=node_manager, telnet_service=telnet)
        
        # Mock file system to return empty lists
        with patch.object(scan_tab, '_get_node_token_files', return_value=["/test/file.fbc"]):
            scan_tab.populate_nodes()
        
        # Verify we have 2 node widgets
        assert len(scan_tab.node_widgets) == 2
        
        # Enable auto-refresh on AP01
        ap01_widget = scan_tab.node_widgets["AP01"]
        ap01_widget.auto_refresh_checkbox.setChecked(True)
        assert ap01_widget.is_auto_refresh_active()
        
        # Switch to AP02 (index 1)
        scan_tab.node_tabs.setCurrentIndex(1)
        
        # Verify AP01 paused, AP02 not started (checkbox still off)
        assert not ap01_widget.is_auto_refresh_active()
        
        # Enable auto-refresh on AP02
        ap02_widget = scan_tab.node_widgets["AP02"]
        ap02_widget.auto_refresh_checkbox.setChecked(True)
        
        # Switch back to AP01
        scan_tab.node_tabs.setCurrentIndex(0)
        
        # Verify AP01 resumed, AP02 paused
        assert ap01_widget.is_auto_refresh_active()
        assert not ap02_widget.is_auto_refresh_active()


class TestSessionViewMainTabSwitch:
    """Test main tab switching pauses/resumes Scan tab"""
    
    def test_switching_away_from_scan_pauses_all(self, qapp):
        """Test switching from Scan to Telnet pauses all auto-refresh"""
        # Setup
        node_manager = Mock(spec=NodeManager)
        node_manager.get_all_nodes.return_value = [
            Node(name="AP01", ip_address="192.168.0.11")
        ]
        node_manager.log_root = "D:/_APP/LOGReport/_DIA"
        
        telnet = Mock()
        session_view = SessionView(node_manager=node_manager, telnet_service=telnet)
        
        # Mock file system
        with patch.object(session_view.scan_tab, '_get_node_token_files', return_value=["/test/file.fbc"]):
            session_view.scan_tab.populate_nodes()
        
        # Switch to Scan tab and enable auto-refresh
        scan_index = session_view.tab_widget.indexOf(session_view.scan_tab)
        session_view.tab_widget.setCurrentIndex(scan_index)
        
        ap01_widget = session_view.scan_tab.node_widgets["AP01"]
        ap01_widget.auto_refresh_checkbox.setChecked(True)
        assert ap01_widget.is_auto_refresh_active()
        
        # Switch to Telnet tab (index 0)
        session_view.tab_widget.setCurrentIndex(0)
        
        # Verify auto-refresh paused
        assert not ap01_widget.is_auto_refresh_active()
    
    def test_switching_to_scan_resumes_active_node(self, qapp):
        """Test switching to Scan tab resumes active node auto-refresh"""
        # Setup
        node_manager = Mock(spec=NodeManager)
        node_manager.get_all_nodes.return_value = [
            Node(name="AP01", ip_address="192.168.0.11")
        ]
        node_manager.log_root = "D:/_APP/LOGReport/_DIA"
        
        telnet = Mock()
        session_view = SessionView(node_manager=node_manager, telnet_service=telnet)
        
        # Mock file system
        with patch.object(session_view.scan_tab, '_get_node_token_files', return_value=["/test/file.fbc"]):
            session_view.scan_tab.populate_nodes()
        
        # Switch to Scan, enable auto-refresh, then switch away
        scan_index = session_view.tab_widget.indexOf(session_view.scan_tab)
        session_view.tab_widget.setCurrentIndex(scan_index)
        
        ap01_widget = session_view.scan_tab.node_widgets["AP01"]
        ap01_widget.auto_refresh_checkbox.setChecked(True)
        
        session_view.tab_widget.setCurrentIndex(0)  # Switch to Telnet
        assert not ap01_widget.is_auto_refresh_active()
        
        # Switch back to Scan
        session_view.tab_widget.setCurrentIndex(scan_index)
        
        # Verify auto-refresh resumed
        assert ap01_widget.is_auto_refresh_active()


class TestIntegration:
    """Integration tests for complete pause/resume workflow"""
    
    def test_multi_level_tab_switching(self, qapp):
        """Test switching both main tab and node subtab works correctly"""
        # Setup
        node_manager = Mock(spec=NodeManager)
        node_manager.get_all_nodes.return_value = [
            Node(name="AP01", ip_address="192.168.0.11"),
            Node(name="AP02", ip_address="192.168.0.12")
        ]
        node_manager.log_root = "D:/_APP/LOGReport/_DIA"
        
        telnet = Mock()
        session_view = SessionView(node_manager=node_manager, telnet_service=telnet)
        
        # Mock file system
        with patch.object(session_view.scan_tab, '_get_node_token_files', return_value=["/test/file.fbc"]):
            session_view.scan_tab.populate_nodes()
        
        # Switch to Scan tab
        scan_index = session_view.tab_widget.indexOf(session_view.scan_tab)
        session_view.tab_widget.setCurrentIndex(scan_index)
        
        # Enable auto-refresh on both nodes
        ap01_widget = session_view.scan_tab.node_widgets["AP01"]
        ap02_widget = session_view.scan_tab.node_widgets["AP02"]
        
        # Initially on AP01 subtab (index 0)
        assert session_view.scan_tab.node_tabs.currentIndex() == 0
        
        # Enable auto-refresh on AP01 (active tab)
        ap01_widget.auto_refresh_checkbox.setChecked(True)
        
        # Manually pause AP02 to simulate initial state
        ap02_widget.auto_refresh_checkbox.setChecked(True)
        ap02_widget.pause_auto_refresh()
        
        # Verify initial state: AP01 active, AP02 paused
        assert ap01_widget.is_auto_refresh_active()
        assert not ap02_widget.is_auto_refresh_active()
        
        # Switch to AP02 subtab
        session_view.scan_tab.node_tabs.setCurrentIndex(1)
        assert not ap01_widget.is_auto_refresh_active()
        assert ap02_widget.is_auto_refresh_active()
        
        # Switch main tab to Telnet (should pause both)
        session_view.tab_widget.setCurrentIndex(0)
        assert not ap01_widget.is_auto_refresh_active()
        assert not ap02_widget.is_auto_refresh_active()
        
        # Switch back to Scan (should resume only AP02, the active subtab)
        session_view.tab_widget.setCurrentIndex(scan_index)
        assert not ap01_widget.is_auto_refresh_active()  # Not active subtab
        assert ap02_widget.is_auto_refresh_active()  # Active subtab


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
