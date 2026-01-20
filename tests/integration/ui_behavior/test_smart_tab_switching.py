"""
Test suite for smart tab switching feature.

Tests scroll-aware tab switching that prevents interrupting users
who are scrolled up reviewing earlier logs.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from PyQt5.QtWidgets import QApplication, QTextEdit
from PyQt5.QtCore import QSettings

# Ensure QApplication exists for Qt widgets
@pytest.fixture(scope="module")
def qapp():
    """Create QApplication for Qt widget tests"""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app


@pytest.fixture
def telnet_tab():
    """Create TelnetTab instance for testing"""
    from src.commander.ui.telnet_tab import TelnetTab
    return TelnetTab()


@pytest.fixture
def bstool_tab():
    """Create BsToolTab instance for testing"""
    from src.commander.ui.bstool_tab import BsToolTab
    return BsToolTab()


@pytest.fixture
def commander_window_minimal(qapp):
    """Create minimal CommanderWindow for testing (mocking heavy dependencies)"""
    with patch('src.commander.ui.commander_window.NodeManager'), \
         patch('src.commander.ui.commander_window.SessionManager'), \
         patch('src.commander.ui.commander_window.CommandQueue'), \
         patch('src.commander.ui.commander_window.LogWriter'), \
         patch('src.commander.ui.commander_window.QSettings'):
        from src.commander.ui.commander_window import CommanderWindow
        window = CommanderWindow()
        yield window


class TestTelnetTabScrollDetection:
    """Test scroll position detection in TelnetTab"""
    
    def test_is_user_at_bottom_when_scrolled_to_bottom(self, qapp, telnet_tab):
        """User is at bottom when scrollbar value equals maximum"""
        # Simulate scrollbar at bottom
        scrollbar = telnet_tab.output.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
        
        assert telnet_tab.is_user_at_bottom() is True
    
    def test_is_user_at_bottom_within_tolerance(self, qapp, telnet_tab):
        """User is considered at bottom within 5px tolerance"""
        scrollbar = telnet_tab.output.verticalScrollBar()
        max_val = scrollbar.maximum()
        
        # Set to 3 pixels from bottom (within 5px tolerance)
        if max_val >= 3:
            scrollbar.setValue(max_val - 3)
            assert telnet_tab.is_user_at_bottom() is True
    
    def test_is_user_not_at_bottom_when_scrolled_up(self, qapp, telnet_tab):
        """User is NOT at bottom when scrolled up beyond tolerance"""
        # Add content to ensure scrollbar has range
        for i in range(100):
            telnet_tab.append_output(f"Line {i}\n")
        
        scrollbar = telnet_tab.output.verticalScrollBar()
        max_val = scrollbar.maximum()
        
        # Scroll up beyond tolerance (more than 5px)
        if max_val > 10:
            scrollbar.setValue(max_val - 10)
            assert telnet_tab.is_user_at_bottom() is False


class TestBsToolTabScrollDetection:
    """Test scroll position detection in BsToolTab"""
    
    def test_is_user_at_bottom_when_scrolled_to_bottom(self, qapp, bstool_tab):
        """User is at bottom when scrollbar value equals maximum"""
        scrollbar = bstool_tab.output.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
        
        assert bstool_tab.is_user_at_bottom() is True
    
    def test_is_user_at_bottom_within_tolerance(self, qapp, bstool_tab):
        """User is considered at bottom within 5px tolerance"""
        scrollbar = bstool_tab.output.verticalScrollBar()
        max_val = scrollbar.maximum()
        
        # Set to 4 pixels from bottom (within 5px tolerance)
        if max_val >= 4:
            scrollbar.setValue(max_val - 4)
            assert bstool_tab.is_user_at_bottom() is True
    
    def test_is_user_not_at_bottom_when_scrolled_up(self, qapp, bstool_tab):
        """User is NOT at bottom when scrolled up beyond tolerance"""
        # Add content to ensure scrollbar has range
        for i in range(100):
            bstool_tab.append_output(f"Line {i}\n")  # BsToolTab.append_output only takes text
        
        scrollbar = bstool_tab.output.verticalScrollBar()
        max_val = scrollbar.maximum()
        
        # Scroll up beyond tolerance (more than 5px)
        if max_val > 15:
            scrollbar.setValue(max_val - 15)
            assert bstool_tab.is_user_at_bottom() is False


class TestSmartTabSwitching:
    """Test CommanderWindow smart tab switching logic"""
    
    def test_smart_switch_unconditional_when_check_scroll_false(self, qapp):
        """Always switch when check_scroll=False regardless of scroll position"""
        with patch('src.commander.ui.commander_window.NodeManager'), \
             patch('src.commander.ui.commander_window.SessionManager'), \
             patch('src.commander.ui.commander_window.CommandQueue'), \
             patch('src.commander.ui.commander_window.LogWriter'), \
             patch.object(QSettings, 'value', return_value=''):  # Mock QSettings.value to return empty
            from src.commander.ui.commander_window import CommanderWindow
            window = CommanderWindow()
            
            # Simulate user scrolled up in telnet tab
            telnet_scrollbar = window.telnet_tab.output.verticalScrollBar()
            telnet_scrollbar.setValue(0)  # Top of scroll
            
            # Set current tab to telnet
            window.session_tabs.setCurrentWidget(window.telnet_tab)
            
            # Switch to bstool with check_scroll=False (user action)
            window._smart_switch_to_tab(window.bstool_tab, check_scroll=False)
            
            # Should switch despite user being scrolled up
            assert window.session_tabs.currentWidget() == window.bstool_tab
    
    def test_smart_switch_blocks_when_user_scrolled_up(self, qapp):
        """Don't switch when check_scroll=True and user scrolled up"""
        with patch('src.commander.ui.commander_window.NodeManager'), \
             patch('src.commander.ui.commander_window.SessionManager'), \
             patch('src.commander.ui.commander_window.CommandQueue'), \
             patch('src.commander.ui.commander_window.LogWriter'), \
             patch.object(QSettings, 'value', return_value=''):
            from src.commander.ui.commander_window import CommanderWindow
            window = CommanderWindow()
            
            # Add content to telnet tab
            for i in range(100):
                window.telnet_tab.append_output(f"Line {i}\n")
            
            # Set current tab to telnet
            window.session_tabs.setCurrentWidget(window.telnet_tab)
            
            # NOW scroll up after content is added (to avoid auto-scroll interference)
            telnet_scrollbar = window.telnet_tab.output.verticalScrollBar()
            max_val = telnet_scrollbar.maximum()
            if max_val > 20:
                telnet_scrollbar.setValue(max_val - 20)  # Scrolled up beyond tolerance
                
                # Verify user is NOT at bottom before testing
                assert not window.telnet_tab.is_user_at_bottom()
            
                # Try to switch with check_scroll=True (sequential execution)
                window._smart_switch_to_tab(window.bstool_tab, check_scroll=True)
            
                # Should NOT switch because user is scrolled up
                assert window.session_tabs.currentWidget() == window.telnet_tab
    
    def test_smart_switch_allows_when_user_at_bottom(self, qapp):
        """Switch when check_scroll=True and user at bottom"""
        with patch('src.commander.ui.commander_window.NodeManager'), \
             patch('src.commander.ui.commander_window.SessionManager'), \
             patch('src.commander.ui.commander_window.CommandQueue'), \
             patch('src.commander.ui.commander_window.LogWriter'), \
             patch.object(QSettings, 'value', return_value=''):
            from src.commander.ui.commander_window import CommanderWindow
            window = CommanderWindow()
            
            # Ensure user is at bottom of telnet tab
            telnet_scrollbar = window.telnet_tab.output.verticalScrollBar()
            telnet_scrollbar.setValue(telnet_scrollbar.maximum())
            
            # Set current tab to telnet
            window.session_tabs.setCurrentWidget(window.telnet_tab)
            
            # Switch with check_scroll=True (sequential execution)
            window._smart_switch_to_tab(window.bstool_tab, check_scroll=True)
            
            # Should switch because user is at bottom
            assert window.session_tabs.currentWidget() == window.bstool_tab
    
    def test_smart_switch_bstool_to_telnet_respects_scroll(self, qapp):
        """Test switching from bstool to telnet respects scroll position"""
        with patch('src.commander.ui.commander_window.NodeManager'), \
             patch('src.commander.ui.commander_window.SessionManager'), \
             patch('src.commander.ui.commander_window.CommandQueue'), \
             patch('src.commander.ui.commander_window.LogWriter'), \
             patch.object(QSettings, 'value', return_value=''):
            from src.commander.ui.commander_window import CommanderWindow
            window = CommanderWindow()
            
            # Add content to bstool tab
            for i in range(100):
                window.bstool_tab.append_output(f"Output {i}\n")
            
            # Set current tab to bstool
            window.session_tabs.setCurrentWidget(window.bstool_tab)
            
            # NOW scroll up after content is added (to avoid auto-scroll from append_output)
            bstool_scrollbar = window.bstool_tab.output.verticalScrollBar()
            max_val = bstool_scrollbar.maximum()
            if max_val > 20:
                bstool_scrollbar.setValue(max_val - 20)  # Scrolled up
                
                # Verify user is NOT at bottom
                assert not window.bstool_tab.is_user_at_bottom()
            
                # Try to switch to telnet with check_scroll=True
                window._smart_switch_to_tab(window.telnet_tab, check_scroll=True)
            
                # Should NOT switch because user is scrolled up in bstool
                assert window.session_tabs.currentWidget() == window.bstool_tab


class TestBackwardCompatibility:
    """Test that existing functionality is preserved"""
    
    def test_handle_command_generated_forces_switch_for_user_actions(self, qapp):
        """User-initiated actions should always switch tabs"""
        with patch('src.commander.ui.commander_window.NodeManager'), \
             patch('src.commander.ui.commander_window.SessionManager'), \
             patch('src.commander.ui.commander_window.CommandQueue'), \
             patch('src.commander.ui.commander_window.LogWriter'), \
             patch.object(QSettings, 'value', return_value=''):
            from src.commander.ui.commander_window import CommanderWindow
            window = CommanderWindow()
            
            # Scroll up in current tab
            for i in range(100):
                window.telnet_tab.append_output(f"Line {i}\n")
            
            telnet_scrollbar = window.telnet_tab.output.verticalScrollBar()
            max_val = telnet_scrollbar.maximum()
            if max_val > 20:
                telnet_scrollbar.setValue(0)  # Top of scroll
            
            # Set to telnet tab
            window.session_tabs.setCurrentWidget(window.telnet_tab)
            
            # User generates BSTOOL command (user action)
            window._handle_command_generated("bstool -errlog AP01", "BSTOOL")
            
            # Should force switch despite user being scrolled up
            assert window.session_tabs.currentWidget() == window.bstool_tab
