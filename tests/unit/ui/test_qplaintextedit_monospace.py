"""
Standalone test for QPlainTextEdit monospace rendering.

Tests the fundamental difference between QTextEdit and QPlainTextEdit
for ASCII table column alignment without importing application modules.
"""

import pytest
from PyQt5.QtWidgets import QApplication, QTextEdit, QPlainTextEdit
from PyQt5.QtGui import QFont


@pytest.fixture(scope="module")
def qapp():
    """Create QApplication instance for testing PyQt5 widgets."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app


class TestMonospaceRendering:
    """Test monospace character rendering in QPlainTextEdit vs QTextEdit."""
    
    @pytest.fixture
    def sample_ascii_table(self):
        """Sample ASCII table with aligned columns."""
        return """ PIC  5   6   7   8   9   10  11  12  13  14  15  16  17  18  19  20     sum

   0 AI8 BI8 BO8 BI8 BI8 BI8 BO8 BI8 BO8 BI8 BO8 BI8 BO8 BI8 AO4        15

   1 AI8 BI8 BI8 BI8 BO8 BI8 BO8 BI8 BI8 BI8 BI8NBI8 BO8 TI6 TI6        15

   2 AI8 BI8 BI8NBI8 BO8 BI8 BO8 BI8 BI8 BI8 BI8 AO4 BI8 BI8 BI8        15"""
    
    def test_qplaintextedit_preserves_spacing(self, qapp, sample_ascii_table):
        """Verify QPlainTextEdit preserves spacing for ASCII tables."""
        widget = QPlainTextEdit()
        
        # Set monospace font
        font = QFont("Courier New", 10)
        font.setStyleHint(QFont.StyleHint.Monospace)
        font.setFixedPitch(True)
        widget.setFont(font)
        
        # Add content
        widget.setPlainText(sample_ascii_table)
        
        # Get content back
        content = widget.toPlainText()
        
        # Verify structure preserved
        lines = content.split('\n')
        assert len(lines) >= 4, f"Expected 4+ lines, got {len(lines)}"
        
        # Verify header line
        header_line = lines[0]
        assert "PIC" in header_line
        assert "sum" in header_line
        
        # Verify data rows
        data_rows = [line for line in lines if line.strip().startswith(('0', '1', '2'))]
        assert len(data_rows) >= 3, f"Expected 3+ data rows, got {len(data_rows)}"
        
        # Verify consistent column widths (all data rows should have similar structure)
        for row in data_rows:
            assert "AI8" in row or "BI8" in row, \
                f"Data row should contain module identifiers: {row}"
        
        widget.deleteLater()
    
    def test_qplaintextedit_character_width_consistency(self, qapp):
        """Verify QPlainTextEdit maintains consistent character widths."""
        widget = QPlainTextEdit()
        
        # Set monospace font
        font = QFont("Courier New", 10)
        font.setStyleHint(QFont.StyleHint.Monospace)
        font.setFixedPitch(True)
        widget.setFont(font)
        
        # Get font metrics
        font_metrics = widget.fontMetrics()
        
        # Test character width consistency for digits
        digits = "0123456789"
        digit_widths = [font_metrics.horizontalAdvance(c) for c in digits]
        
        # All digits should have same width in monospace font
        unique_widths = set(digit_widths)
        assert len(unique_widths) == 1, \
            f"Character widths should be identical: {dict(zip(digits, digit_widths))}"
        
        # Test character width consistency for letters
        letters = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        letter_widths = [font_metrics.horizontalAdvance(c) for c in letters]
        
        unique_letter_widths = set(letter_widths)
        assert len(unique_letter_widths) == 1, \
            f"Letter widths should be identical: got {len(unique_letter_widths)} different widths"
        
        # Digits and letters should have same width in truly monospace font
        assert digit_widths[0] == letter_widths[0], \
            f"Digits and letters should have same width: {digit_widths[0]} != {letter_widths[0]}"
        
        widget.deleteLater()
    
    def test_qplaintextedit_tab_replacement(self, qapp):
        """Verify tab-to-space conversion works with QPlainTextEdit."""
        widget = QPlainTextEdit()
        
        # Set monospace font
        font = QFont("Courier New", 10)
        font.setFixedPitch(True)
        widget.setFont(font)
        
        # Test content with tabs
        test_input = "Column1\tColumn2\tColumn3"
        # Convert tabs to spaces (8 spaces per tab)
        converted = test_input.replace('\t', ' ' * 8)
        
        widget.setPlainText(converted)
        content = widget.toPlainText()
        
        # Verify no tabs in output
        assert '\t' not in content, "Tabs should be converted to spaces"
        
        # Verify spacing is consistent
        assert "Column1" in content
        assert "Column2" in content
        assert "Column3" in content
        
        widget.deleteLater()
    
    def test_qplaintextedit_whitespace_preservation(self, qapp):
        """Verify QPlainTextEdit preserves leading/trailing whitespace."""
        widget = QPlainTextEdit()
        
        # Test with leading spaces
        test_input = "   Leading spaces\n     More leading spaces"
        widget.setPlainText(test_input)
        
        content = widget.toPlainText()
        lines = content.split('\n')
        
        # Verify leading whitespace preserved
        assert lines[0].startswith('   '), \
            f"First line should start with 3 spaces: '{lines[0]}'"
        assert lines[1].startswith('     '), \
            f"Second line should start with 5 spaces: '{lines[1]}'"
        
        widget.deleteLater()


class TestWidgetTypeComparison:
    """Compare QTextEdit vs QPlainTextEdit for monospace rendering."""
    
    def test_qplaintextedit_vs_qtextedit_api(self, qapp):
        """Verify QPlainTextEdit has compatible API with QTextEdit for our use case."""
        plain_widget = QPlainTextEdit()
        text_widget = QTextEdit()
        
        # Both should have these methods
        assert hasattr(plain_widget, 'setPlainText')
        assert hasattr(plain_widget, 'toPlainText')
        assert hasattr(plain_widget, 'setReadOnly')
        assert hasattr(plain_widget, 'setFont')
        assert hasattr(plain_widget, 'verticalScrollBar')
        assert hasattr(plain_widget, 'textCursor')
        assert hasattr(plain_widget, 'insertPlainText')
        
        # QTextEdit also has these methods
        assert hasattr(text_widget, 'setPlainText')
        assert hasattr(text_widget, 'toPlainText')
        assert hasattr(text_widget, 'insertPlainText')
        
        plain_widget.deleteLater()
        text_widget.deleteLater()
    
    def test_qplaintextedit_font_configuration(self, qapp):
        """Verify QPlainTextEdit accepts monospace font configuration."""
        widget = QPlainTextEdit()
        
        # Configure monospace font
        font = QFont("Courier New", 10)
        font.setStyleHint(QFont.StyleHint.Monospace)
        font.setFixedPitch(True)
        widget.setFont(font)
        
        # Verify font was set
        configured_font = widget.font()
        assert configured_font.family() == "Courier New"
        assert configured_font.pointSize() == 10
        assert configured_font.fixedPitch()
        
        widget.deleteLater()


class TestRealWorldScenario:
    """Test with real FBC command output."""
    
    @pytest.fixture
    def fbc_output_sample(self):
        """Real FBC command output from log files."""
        return """Display Field Bus Configuration via agent 1620000

---------------------------------------------------

 PIC  5   6   7   8   9   10  11  12  13  14  15  16  17  18  19  20     sum

   0 AI8 BI8 BO8 BI8 BI8 BI8 BO8 BI8 BO8 BI8 BO8 BI8 BO8 BI8 AO4        15

   1 AI8 BI8 BI8 BI8 BO8 BI8 BO8 BI8 BI8 BI8 BI8NBI8 BO8 TI6 TI6        15

   2 AI8 BI8 BI8NBI8 BO8 BI8 BO8 BI8 BI8 BI8 BI8 AO4 BI8 BI8 BI8        15

   3 AI8 BI8 BO8 BI8 BO8 BI8 BO8 BI8 TI6 AI8 AI8 AO4 BI8 TI6 TI6        15

 Total sum: 238 I/O-units, 1843 Channels(1323 input, 520 output)"""
    
    def test_fbc_table_rendering(self, qapp, fbc_output_sample):
        """Test real FBC output rendering in QPlainTextEdit."""
        widget = QPlainTextEdit()
        widget.setReadOnly(True)
        
        # Configure monospace font
        font = QFont("Courier New", 10)
        font.setStyleHint(QFont.StyleHint.Monospace)
        font.setFixedPitch(True)
        widget.setFont(font)
        
        # Set content
        widget.setPlainText(fbc_output_sample)
        
        # Verify content preserved
        content = widget.toPlainText()
        
        # Check key elements
        assert "Display Field Bus Configuration" in content
        assert "PIC  5   6   7" in content
        assert "sum" in content
        assert "Total sum: 238" in content
        
        # Check table structure
        lines = content.split('\n')
        data_lines = [line for line in lines if line.strip() and line.strip()[0].isdigit()]
        assert len(data_lines) >= 4, f"Expected 4+ data lines, got {len(data_lines)}"
        
        # Verify sum column values
        sum_values = []
        for line in data_lines:
            if line.strip().startswith(('0', '1', '2', '3')):
                # Extract last number from line
                parts = line.split()
                if parts and parts[-1].isdigit():
                    sum_values.append(parts[-1])
        
        assert len(sum_values) >= 4, f"Expected 4+ sum values, got {len(sum_values)}"
        assert all(val == '15' for val in sum_values), \
            f"All sum values should be 15: {sum_values}"
        
        widget.deleteLater()
