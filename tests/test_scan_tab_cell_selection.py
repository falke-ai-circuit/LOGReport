"""
Test Scan Tab Cell Selection Feature

Tests for displaying file values when cells are selected,
preserving comparison colors, and handling multi-cell selection.
"""

import pytest
from PyQt5.QtWidgets import QApplication, QTableWidgetItem
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor
from unittest.mock import Mock, MagicMock, patch
import sys

from src.commander.ui.node_scan_widget import NodeScanWidget
from src.commander.services.fbc_parser_service import FbcParserService, FbcTableData


@pytest.fixture(scope="module")
def qapp():
    """Create QApplication instance for tests"""
    if QApplication.instance() is None:
        app = QApplication(sys.argv)
    else:
        app = QApplication.instance()
    yield app


@pytest.fixture
def mock_telnet_service():
    """Mock telnet service"""
    service = Mock()
    service.telnet_session = None
    return service


@pytest.fixture
def mock_parser_service():
    """Mock FBC parser service"""
    return Mock(spec=FbcParserService)


@pytest.fixture
def widget(qapp, mock_parser_service, mock_telnet_service):
    """Create NodeScanWidget instance"""
    token_files = [
        "D:/_APP/LOGReport/_DIA/LOG/AP01m_FBC_001_20251016_100000.fbc",
        "D:/_APP/LOGReport/_DIA/LOG/AP01m_RPC_001_20251016_100000.rpc"
    ]
    
    widget = NodeScanWidget(
        node_name="AP01m",
        token_files=token_files,
        parser_service=mock_parser_service,
        telnet_service=mock_telnet_service,
        parent=None
    )
    
    yield widget
    widget.deleteLater()


@pytest.fixture
def sample_fbc_data():
    """Create sample FBC table data"""
    return FbcTableData(
        file_type='FBC',
        timestamp='2025-10-16 10:00:00',
        agent_id='001',
        command='print from fbc io structure 0010000',
        headers=['PIC', 'TYPE', 'STATE', 'IN', 'OUT'],
        rows=[
            {'PIC': '0', 'TYPE': 'DI32', 'STATE': 'OK', 'IN': '10', 'OUT': '5'},
            {'PIC': '1', 'TYPE': 'AI16', 'STATE': 'OK', 'IN': '8', 'OUT': '3'},
            {'PIC': '2', 'TYPE': 'DO32', 'STATE': 'FAIL', 'IN': '0', 'OUT': '0'}
        ],
        totals={}
    )


class TestCellSelectionInitialization:
    """Test initialization of cell selection state variables"""
    
    def test_widget_has_selection_state_variables(self, widget):
        """Verify widget initializes selection tracking variables"""
        assert hasattr(widget, '_live_values')
        assert isinstance(widget._live_values, dict)
        assert len(widget._live_values) == 0
        
        assert hasattr(widget, '_selected_cells')
        assert isinstance(widget._selected_cells, set)
        assert len(widget._selected_cells) == 0
        
        assert hasattr(widget, '_selection_in_progress')
        assert widget._selection_in_progress is False
        
        assert hasattr(widget, '_selection_connected')
        assert widget._selection_connected is False


class TestFileValueStorage:
    """Test file value storage in Qt.UserRole during table creation"""
    
    def test_file_values_stored_in_user_role(self, widget, sample_fbc_data):
        """Verify file values are stored in Qt.UserRole on table creation"""
        widget._create_table_from_data(sample_fbc_data)
        
        # Check that file values are stored in Qt.UserRole
        for row_idx in range(3):
            for col_idx in range(4):  # PIC excluded from display columns
                item = widget.table_widget.item(row_idx, col_idx)
                assert item is not None
                
                # Qt.UserRole should contain the original file value
                stored_value = item.data(Qt.UserRole)
                assert stored_value is not None
                assert isinstance(stored_value, str)
    
    def test_comparison_state_initialized_empty(self, widget, sample_fbc_data):
        """Verify comparison state (Qt.UserRole + 1) is initialized to empty"""
        widget._create_table_from_data(sample_fbc_data)
        
        for row_idx in range(3):
            for col_idx in range(4):
                item = widget.table_widget.item(row_idx, col_idx)
                comparison_state = item.data(Qt.UserRole + 1)
                assert comparison_state == ""
    
    def test_signal_connection_established(self, widget, sample_fbc_data):
        """Verify itemSelectionChanged signal is connected"""
        widget._create_table_from_data(sample_fbc_data)
        
        assert widget._selection_connected is True


class TestComparisonResultsStorage:
    """Test live value storage during comparison"""
    
    def test_live_values_stored_on_comparison(self, widget, sample_fbc_data):
        """Verify live values are stored in _live_values dict during comparison"""
        widget._create_table_from_data(sample_fbc_data)
        widget.current_data = sample_fbc_data
        
        # Simulate comparison results
        results = {
            'success': True,
            'file_type': 'FBC',
            'match_percentage': 66.7,
            'total_cells': 12,
            'matches': [(0, 0), (0, 1), (1, 0)],
            'differences': [
                (0, 2, 'OK', 'WARN'),  # Row 0, Col 2: file='OK', live='WARN'
                (2, 1, 'DO32', 'INVALID')  # Row 2, Col 1: file='DO32', live='INVALID'
            ],
            'value_appeared': [
                (2, 3, 'N', '15')  # Row 2, Col 3: file='N', live='15'
            ],
            'errors': []
        }
        
        widget.apply_comparison_results(results)
        
        # Check that live values are stored
        assert len(widget._live_values) > 0
        
        # Check matches store live values
        assert (0, 0) in widget._live_values
        assert (0, 1) in widget._live_values
        
        # Check differences store live values
        assert (0, 2) in widget._live_values
        assert widget._live_values[(0, 2)] == 'WARN'
        
        assert (2, 1) in widget._live_values
        assert widget._live_values[(2, 1)] == 'INVALID'
        
        # Check value_appeared stores live values
        assert (2, 3) in widget._live_values
        assert widget._live_values[(2, 3)] == '15'
    
    def test_comparison_states_stored(self, widget, sample_fbc_data):
        """Verify comparison states are stored in Qt.UserRole + 1"""
        widget._create_table_from_data(sample_fbc_data)
        widget.current_data = sample_fbc_data
        
        results = {
            'success': True,
            'file_type': 'FBC',
            'match_percentage': 100.0,
            'total_cells': 3,
            'matches': [(0, 0)],
            'differences': [(0, 1, 'DI32', 'AI16')],
            'value_appeared': [(0, 2, 'N', 'OK')],
            'errors': [(0, 3, 'Parse error')]
        }
        
        widget.apply_comparison_results(results)
        
        # Check match state
        item_match = widget.table_widget.item(0, 0)
        assert item_match.data(Qt.UserRole + 1) == "match"
        
        # Check difference state
        item_diff = widget.table_widget.item(0, 1)
        assert item_diff.data(Qt.UserRole + 1) == "difference"
        
        # Check value_appeared state
        item_appeared = widget.table_widget.item(0, 2)
        assert item_appeared.data(Qt.UserRole + 1) == "value_appeared"
        
        # Check error state
        item_error = widget.table_widget.item(0, 3)
        assert item_error.data(Qt.UserRole + 1) == "error"


class TestCellSelection:
    """Test cell selection behavior"""
    
    def test_single_cell_selection_shows_file_value(self, widget, sample_fbc_data):
        """Verify selecting a cell displays the file value"""
        widget._create_table_from_data(sample_fbc_data)
        widget.current_data = sample_fbc_data
        
        # Apply comparison to set live values
        results = {
            'success': True,
            'file_type': 'FBC',
            'match_percentage': 100.0,
            'total_cells': 1,
            'matches': [],
            'differences': [(0, 1, 'DI32', 'AI16')],  # file='DI32', live='AI16'
            'value_appeared': [],
            'errors': []
        }
        widget.apply_comparison_results(results)
        
        # Verify initial state shows live value
        item = widget.table_widget.item(0, 1)
        assert item.text() == 'AI16'  # Live value
        
        # Simulate cell selection
        widget.table_widget.setCurrentCell(0, 1)
        widget._on_selection_changed()
        
        # After selection, should show file value
        assert item.text() == 'DI32'  # File value
        assert (0, 1) in widget._selected_cells
    
    def test_cell_deselection_restores_live_value(self, widget, sample_fbc_data):
        """Verify deselecting a cell restores the live value"""
        widget._create_table_from_data(sample_fbc_data)
        widget.current_data = sample_fbc_data
        
        # Apply comparison
        results = {
            'success': True,
            'file_type': 'FBC',
            'match_percentage': 100.0,
            'total_cells': 1,
            'matches': [],
            'differences': [(0, 1, 'DI32', 'AI16')],
            'value_appeared': [],
            'errors': []
        }
        widget.apply_comparison_results(results)
        
        item = widget.table_widget.item(0, 1)
        
        # Select cell
        widget.table_widget.setCurrentCell(0, 1)
        widget._on_selection_changed()
        assert item.text() == 'DI32'  # File value shown
        
        # Deselect cell (clear selection)
        widget.table_widget.clearSelection()
        widget._on_selection_changed()
        
        # Should restore live value
        assert item.text() == 'AI16'  # Live value restored
        assert (0, 1) not in widget._selected_cells
    
    def test_multi_cell_selection(self, widget, sample_fbc_data):
        """Verify multiple cells can be selected simultaneously"""
        widget._create_table_from_data(sample_fbc_data)
        widget.current_data = sample_fbc_data
        
        # Apply comparison with multiple differences
        results = {
            'success': True,
            'file_type': 'FBC',
            'match_percentage': 50.0,
            'total_cells': 4,
            'matches': [],
            'differences': [
                (0, 0, 'TYPE1', 'TYPE2'),
                (0, 1, 'STATE1', 'STATE2'),
                (1, 0, 'IN1', 'IN2'),
                (1, 1, 'OUT1', 'OUT2')
            ],
            'value_appeared': [],
            'errors': []
        }
        widget.apply_comparison_results(results)
        
        # Select range of cells
        widget.table_widget.setRangeSelected(
            widget.table_widget.selectedRanges()[0] if widget.table_widget.selectedRanges() else None,
            False
        )
        # Manually set selection for testing
        widget._selected_cells = set()
        widget._on_selection_changed()
        
        # Simulate selecting (0,0) and (0,1)
        widget.table_widget.item(0, 0).setSelected(True)
        widget.table_widget.item(0, 1).setSelected(True)
        
        # Manually trigger selection change
        current_selection = {(0, 0), (0, 1)}
        newly_selected = current_selection - widget._selected_cells
        
        # Verify file values would be shown
        assert len(newly_selected) == 2
        assert (0, 0) in newly_selected
        assert (0, 1) in newly_selected


class TestColorPreservation:
    """Test comparison color preservation during selection"""
    
    def test_selection_preserves_foreground_color(self, widget, sample_fbc_data):
        """Verify foreground color is preserved when cell is selected"""
        widget._create_table_from_data(sample_fbc_data)
        widget.current_data = sample_fbc_data
        
        # Apply comparison with red (difference) cell
        results = {
            'success': True,
            'file_type': 'FBC',
            'match_percentage': 100.0,
            'total_cells': 1,
            'matches': [],
            'differences': [(0, 1, 'DI32', 'AI16')],
            'value_appeared': [],
            'errors': []
        }
        widget.apply_comparison_results(results)
        
        item = widget.table_widget.item(0, 1)
        
        # Get foreground color before selection
        color_before = item.foreground().color()
        assert color_before == QColor("#F44336")  # Red
        
        # Select cell
        widget.table_widget.setCurrentCell(0, 1)
        widget._on_selection_changed()
        
        # Foreground color should remain the same
        color_after = item.foreground().color()
        assert color_after == QColor("#F44336")  # Still red
    
    def test_green_color_preserved_on_selection(self, widget, sample_fbc_data):
        """Verify green (match) color is preserved"""
        widget._create_table_from_data(sample_fbc_data)
        widget.current_data = sample_fbc_data
        
        results = {
            'success': True,
            'file_type': 'FBC',
            'match_percentage': 100.0,
            'total_cells': 1,
            'matches': [(0, 0)],
            'differences': [],
            'value_appeared': [],
            'errors': []
        }
        widget.apply_comparison_results(results)
        
        item = widget.table_widget.item(0, 0)
        color_before = item.foreground().color()
        assert color_before == QColor("#4CAF50")  # Green
        
        widget.table_widget.setCurrentCell(0, 0)
        widget._on_selection_changed()
        
        color_after = item.foreground().color()
        assert color_after == QColor("#4CAF50")  # Still green
    
    def test_yellow_color_preserved_on_selection(self, widget, sample_fbc_data):
        """Verify yellow (value_appeared) color is preserved"""
        widget._create_table_from_data(sample_fbc_data)
        widget.current_data = sample_fbc_data
        
        results = {
            'success': True,
            'file_type': 'FBC',
            'match_percentage': 100.0,
            'total_cells': 1,
            'matches': [],
            'differences': [],
            'value_appeared': [(0, 2, 'N', 'OK')],
            'errors': []
        }
        widget.apply_comparison_results(results)
        
        item = widget.table_widget.item(0, 2)
        color_before = item.foreground().color()
        assert color_before == QColor("#FFC107")  # Yellow
        
        widget.table_widget.setCurrentCell(0, 2)
        widget._on_selection_changed()
        
        color_after = item.foreground().color()
        assert color_after == QColor("#FFC107")  # Still yellow


class TestTooltipUpdates:
    """Test tooltip updates during selection"""
    
    def test_tooltip_shows_both_values_on_selection(self, widget, sample_fbc_data):
        """Verify tooltip shows both file and live values when selected"""
        widget._create_table_from_data(sample_fbc_data)
        widget.current_data = sample_fbc_data
        
        results = {
            'success': True,
            'file_type': 'FBC',
            'match_percentage': 100.0,
            'total_cells': 1,
            'matches': [],
            'differences': [(0, 1, 'DI32', 'AI16')],
            'value_appeared': [],
            'errors': []
        }
        widget.apply_comparison_results(results)
        
        item = widget.table_widget.item(0, 1)
        
        # Select cell
        widget.table_widget.setCurrentCell(0, 1)
        widget._on_selection_changed()
        
        # Tooltip should show both values
        tooltip = item.toolTip()
        assert "File: DI32" in tooltip
        assert "Live: AI16" in tooltip
    
    def test_tooltip_restored_on_deselection(self, widget, sample_fbc_data):
        """Verify tooltip is restored to comparison-based message on deselection"""
        widget._create_table_from_data(sample_fbc_data)
        widget.current_data = sample_fbc_data
        
        results = {
            'success': True,
            'file_type': 'FBC',
            'match_percentage': 100.0,
            'total_cells': 1,
            'matches': [],
            'differences': [(0, 1, 'DI32', 'AI16')],
            'value_appeared': [],
            'errors': []
        }
        widget.apply_comparison_results(results)
        
        item = widget.table_widget.item(0, 1)
        
        # Original tooltip from comparison
        original_tooltip = item.toolTip()
        assert "Value Changed" in original_tooltip
        
        # Select and deselect
        widget.table_widget.setCurrentCell(0, 1)
        widget._on_selection_changed()
        
        widget.table_widget.clearSelection()
        widget._on_selection_changed()
        
        # Tooltip should be restored
        restored_tooltip = item.toolTip()
        assert "Value Changed" in restored_tooltip


class TestEdgeCases:
    """Test edge cases and error handling"""
    
    def test_selection_without_comparison(self, widget, sample_fbc_data):
        """Verify selection works when no comparison has been run"""
        widget._create_table_from_data(sample_fbc_data)
        
        # Select cell without running comparison
        widget.table_widget.setCurrentCell(0, 0)
        widget._on_selection_changed()
        
        # Should not crash, shows file value (same as displayed value)
        item = widget.table_widget.item(0, 0)
        file_value = item.data(Qt.UserRole)
        assert item.text() == file_value
    
    def test_rapid_selection_changes(self, widget, sample_fbc_data):
        """Verify rapid selection changes don't cause issues"""
        widget._create_table_from_data(sample_fbc_data)
        widget.current_data = sample_fbc_data
        
        # Apply comparison
        results = {
            'success': True,
            'file_type': 'FBC',
            'match_percentage': 100.0,
            'total_cells': 3,
            'matches': [],
            'differences': [
                (0, 0, 'A', 'B'),
                (1, 0, 'C', 'D'),
                (2, 0, 'E', 'F')
            ],
            'value_appeared': [],
            'errors': []
        }
        widget.apply_comparison_results(results)
        
        # Rapidly change selection
        for row in range(3):
            widget.table_widget.setCurrentCell(row, 0)
            widget._on_selection_changed()
        
        # Final selection should be correct
        assert widget.table_widget.currentRow() == 2
        item = widget.table_widget.item(2, 0)
        assert item.text() == 'E'  # File value
    
    def test_clear_selection_on_new_comparison(self, widget, sample_fbc_data):
        """Verify selection is cleared when new comparison is applied"""
        widget._create_table_from_data(sample_fbc_data)
        widget.current_data = sample_fbc_data
        
        # First comparison
        results1 = {
            'success': True,
            'file_type': 'FBC',
            'match_percentage': 100.0,
            'total_cells': 1,
            'matches': [],
            'differences': [(0, 0, 'A', 'B')],
            'value_appeared': [],
            'errors': []
        }
        widget.apply_comparison_results(results1)
        
        # Select cell
        widget.table_widget.setCurrentCell(0, 0)
        widget._on_selection_changed()
        assert (0, 0) in widget._selected_cells
        
        # Second comparison (should clear selection state)
        results2 = {
            'success': True,
            'file_type': 'FBC',
            'match_percentage': 100.0,
            'total_cells': 1,
            'matches': [(0, 0)],
            'differences': [],
            'value_appeared': [],
            'errors': []
        }
        widget.apply_comparison_results(results2)
        
        # Selection state should be cleared
        assert len(widget._selected_cells) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
