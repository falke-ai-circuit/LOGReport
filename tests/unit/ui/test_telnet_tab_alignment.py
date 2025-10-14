"""
Test suite for Telnet tab ASCII table column alignment fix.

Validates QPlainTextEdit provides proper monospace character rendering
for FBC command output with ASCII tables.
"""

import pytest
from PyQt5.QtWidgets import QApplication, QPlainTextEdit
from PyQt5.QtGui import QFont
from PyQt5.QtTest import QTest
from PyQt5.QtCore import Qt

# Import the module under test
import sys
from pathlib import Path
src_path = Path(__file__).parent.parent.parent.parent / "src"
sys.path.insert(0, str(src_path))

from commander.ui.telnet_tab import TelnetTab


@pytest.fixture(scope="module")
def qapp():
    """Create QApplication instance for testing PyQt5 widgets."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app


@pytest.fixture
def telnet_tab(qapp):
    """Create TelnetTab instance for testing."""
    tab = TelnetTab()
    yield tab
    tab.deleteLater()


class TestTelnetTabWidgetType:
    """Test that telnet tab uses QPlainTextEdit instead of QTextEdit."""
    
    def test_output_widget_is_qplaintextedit(self, telnet_tab):
        """Verify output widget is QPlainTextEdit instance."""
        assert isinstance(telnet_tab.output, QPlainTextEdit), \
            f"Expected QPlainTextEdit, got {type(telnet_tab.output).__name__}"
    
    def test_output_widget_is_readonly(self, telnet_tab):
        """Verify output widget is read-only."""
        assert telnet_tab.output.isReadOnly(), \
            "Output widget should be read-only"
    
    def test_monospace_font_configured(self, telnet_tab):
        """Verify monospace font is properly configured."""
        font = telnet_tab.output.font()
        assert font.family() == "Courier New", \
            f"Expected Courier New font, got {font.family()}"
        assert font.fixedPitch(), \
            "Font should have fixed pitch enabled"
        assert font.pointSize() == 10, \
            f"Expected 10pt font size, got {font.pointSize()}"


class TestASCIITableAlignment:
    """Test ASCII table column alignment with QPlainTextEdit."""
    
    @pytest.fixture
    def sample_fbc_table(self):
        """Sample FBC command output with ASCII table."""
        return """Display Field Bus Configuration via agent 1620000

---------------------------------------------------

 PIC  5   6   7   8   9   10  11  12  13  14  15  16  17  18  19  20     sum

   0 AI8 BI8 BO8 BI8 BI8 BI8 BO8 BI8 BO8 BI8 BO8 BI8 BO8 BI8 AO4        15

   1 AI8 BI8 BI8 BI8 BO8 BI8 BO8 BI8 BI8 BI8 BI8NBI8 BO8 TI6 TI6        15

   2 AI8 BI8 BI8NBI8 BO8 BI8 BO8 BI8 BI8 BI8 BI8 AO4 BI8 BI8 BI8        15

 Total sum: 238 I/O-units, 1843 Channels(1323 input, 520 output)"""
    
    def test_append_preserves_table_structure(self, telnet_tab, sample_fbc_table):
        """Verify append_output preserves ASCII table structure."""
        telnet_tab.append_output(sample_fbc_table)
        
        # Get the plain text content
        content = telnet_tab.output.toPlainText()
        
        # Verify table is present
        assert "PIC  5   6   7" in content, "Table header should be present"
        assert "sum" in content, "Sum column should be present"
        assert "Total sum: 238" in content, "Total sum line should be present"
        
        # Verify multiple rows present
        lines = content.split('\n')
        table_rows = [line for line in lines if line.strip().startswith(('0', '1', '2'))]
        assert len(table_rows) >= 3, f"Expected at least 3 table rows, got {len(table_rows)}"
    
    def test_tab_to_space_conversion(self, telnet_tab):
        """Verify tabs are converted to spaces for consistent alignment."""
        test_input = "Column1\tColumn2\tColumn3"
        telnet_tab.append_output(test_input)
        
        content = telnet_tab.output.toPlainText()
        # Tabs should be converted to 8 spaces
        assert '\t' not in content, "Tabs should be converted to spaces"
        assert "Column1" in content and "Column2" in content, \
            "Content should be preserved after tab conversion"
    
    def test_whitespace_preservation(self, telnet_tab):
        """Verify leading/trailing whitespace is preserved."""
        test_input = "   Leading spaces"
        telnet_tab.append_output(test_input)
        
        content = telnet_tab.output.toPlainText()
        lines = content.strip().split('\n')
        assert lines[0].startswith('   '), \
            "Leading whitespace should be preserved"
    
    def test_monospace_character_width_consistency(self, telnet_tab):
        """Test that character widths are consistent (monospace behavior)."""
        # Create test string with repeated characters
        test_line = "0123456789" * 5  # 50 characters
        telnet_tab.append_output(test_line)
        
        # Get font metrics
        font_metrics = telnet_tab.output.fontMetrics()
        
        # Check character widths are consistent
        char_widths = [font_metrics.horizontalAdvance(c) for c in "0123456789"]
        assert len(set(char_widths)) == 1, \
            f"Character widths should be identical in monospace font: {set(char_widths)}"


class TestScrollBehavior:
    """Test scroll preservation during content appending."""
    
    def test_scroll_to_bottom_when_at_bottom(self, telnet_tab):
        """Verify scroll follows content when user is at bottom."""
        # Add initial content
        for i in range(20):
            telnet_tab.append_output(f"Line {i}")
        
        # Scroll to bottom
        scrollbar = telnet_tab.output.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
        
        # Verify we're at bottom
        assert telnet_tab.is_user_at_bottom(), \
            "Should be at bottom before adding content"
        
        # Add more content
        telnet_tab.append_output("New line")
        
        # Should still be at bottom (auto-scroll)
        QTest.qWait(10)  # Allow UI to update
        assert telnet_tab.is_user_at_bottom(), \
            "Should auto-scroll to bottom when previously at bottom"
    
    def test_scroll_preserved_when_scrolled_up(self, telnet_tab):
        """Verify scroll position preserved when user scrolled up."""
        # Add initial content
        for i in range(30):
            telnet_tab.append_output(f"Line {i}")
        
        # Scroll to middle
        scrollbar = telnet_tab.output.verticalScrollBar()
        mid_position = scrollbar.maximum() // 2
        scrollbar.setValue(mid_position)
        
        # Verify not at bottom
        assert not telnet_tab.is_user_at_bottom(), \
            "Should not be at bottom after scrolling up"
        
        # Store position
        saved_position = scrollbar.value()
        
        # Add more content
        telnet_tab.append_output("New line")
        
        # Position should be preserved
        QTest.qWait(10)  # Allow UI to update
        assert scrollbar.value() == saved_position, \
            f"Scroll position should be preserved: {scrollbar.value()} != {saved_position}"


class TestEdgeCases:
    """Test edge cases and special characters."""
    
    def test_empty_string_append(self, telnet_tab):
        """Verify empty string doesn't break widget."""
        telnet_tab.append_output("")
        content = telnet_tab.output.toPlainText()
        # Should just add a newline
        assert content.count('\n') >= 1
    
    def test_very_long_line(self, telnet_tab):
        """Verify very long lines are handled correctly."""
        long_line = "A" * 500  # 500 character line
        telnet_tab.append_output(long_line)
        
        content = telnet_tab.output.toPlainText()
        assert long_line in content, "Long line should be preserved"
    
    def test_special_characters(self, telnet_tab):
        """Verify special characters are handled correctly."""
        special_chars = "!@#$%^&*()_+-=[]{}|;':\"<>,.?/`~"
        telnet_tab.append_output(special_chars)
        
        content = telnet_tab.output.toPlainText()
        for char in special_chars:
            assert char in content, f"Special character '{char}' should be preserved"
    
    def test_unicode_characters(self, telnet_tab):
        """Verify Unicode characters are handled correctly."""
        unicode_text = "● ○ ◑ ⨯ ✓"  # Connection status icons
        telnet_tab.append_output(unicode_text)
        
        content = telnet_tab.output.toPlainText()
        # Should preserve Unicode (may render as boxes depending on font)
        assert len(content.strip()) > 0, "Unicode content should be preserved"


class TestIntegration:
    """Integration tests for telnet tab functionality."""
    
    def test_multiple_table_appends(self, telnet_tab):
        """Test appending multiple ASCII tables maintains alignment."""
        table1 = " PIC  5   6   7   8\n   0 AI8 BI8 BO8 BI8"
        table2 = " PIC  9  10  11  12\n   1 BI8 BO8 BI8 BI8"
        
        telnet_tab.append_output(table1)
        telnet_tab.append_output(table2)
        
        content = telnet_tab.output.toPlainText()
        lines = content.split('\n')
        
        # Verify both tables present
        pic_lines = [line for line in lines if 'PIC' in line]
        assert len(pic_lines) >= 2, f"Expected 2+ PIC headers, got {len(pic_lines)}"
    
    def test_clear_and_append(self, telnet_tab):
        """Test clearing output and appending new content."""
        telnet_tab.append_output("Old content")
        telnet_tab.output.clear()
        telnet_tab.append_output("New content")
        
        content = telnet_tab.output.toPlainText()
        assert "Old content" not in content, "Old content should be cleared"
        assert "New content" in content, "New content should be present"
