"""
Test Scan Tab Card Status Handling

Tests card removal (RED text) and card reinsertion (GREEN text) scenarios.
Verifies that text doesn't disappear and colors persist correctly.
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch
from PyQt5.QtWidgets import QApplication, QTableWidgetItem
from PyQt5.QtGui import QColor
from PyQt5.QtCore import Qt

# Add src directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from commander.ui.node_scan_widget import NodeScanWidget
from commander.services.fbc_parser_service import FbcTableData


@pytest.fixture(scope="module")
def qapp():
    """Create QApplication instance for tests"""
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    yield app


@pytest.fixture
def mock_parser_service():
    """Mock FbcParserService"""
    parser = Mock()
    
    # Create sample file data with 3 PICs
    file_data = FbcTableData(
        file_type='FBC',
        timestamp='2025-11-27 10:00:00',
        agent_id='AP01m',
        command='print from fbc io structure 0010000',
        headers=['PIC', 'I0', 'I1', 'O0', 'O1', 'sum'],
        rows=[
            {'PIC': '0', 'I0': 'AA', 'I1': 'BB', 'O0': 'CC', 'O1': 'DD', 'sum': '10'},
            {'PIC': '1', 'I0': 'EE', 'I1': 'FF', 'O0': 'GG', 'O1': 'HH', 'sum': '20'},
            {'PIC': '2', 'I0': 'II', 'I1': 'JJ', 'O0': 'KK', 'O1': 'LL', 'sum': '30'},
        ],
        totals={}
    )
    
    parser.parse_file.return_value = file_data
    return parser


@pytest.fixture
def mock_telnet_service():
    """Mock TelnetService"""
    telnet = Mock()
    telnet.telnet_session = Mock()
    telnet.telnet_session.is_connected = True
    return telnet


@pytest.fixture
def widget(qapp, mock_parser_service, mock_telnet_service):
    """Create NodeScanWidget instance"""
    token_files = ['/fake/path/AP01m_FBC_001.fbc']
    widget = NodeScanWidget(
        node_name='AP01m',
        token_files=token_files,
        parser_service=mock_parser_service,
        telnet_service=mock_telnet_service,
        load_delay_ms=0
    )
    return widget


def test_card_removal_shows_red_text(widget, mock_parser_service):
    """
    Test that when a card is removed (missing from live data),
    the text shows the file value in RED, not disappearing.
    """
    # Load initial file
    widget.load_token_file('/fake/path/AP01m_FBC_001.fbc')
    
    # Verify table is populated
    assert widget.table_widget.rowCount() == 3
    assert widget.table_widget.columnCount() == 5  # PIC removed from display
    
    # Simulate comparison result where PIC 1 is MISSING (card removed)
    comparison_results = {
        'success': True,
        'file_type': 'FBC',
        'match_percentage': 66.7,
        'total_cells': 15,  # 3 PICs x 5 columns
        'matches': [(0, 0), (0, 1), (0, 2), (0, 3), (0, 4)],  # PIC 0 all match
        'differences': [],
        'value_appeared': [],
        'errors': [  # PIC 1 missing - all cells marked as errors
            (1, 0, 'PIC 1 missing in live data'),
            (1, 1, 'PIC 1 missing in live data'),
            (1, 2, 'PIC 1 missing in live data'),
            (1, 3, 'PIC 1 missing in live data'),
            (1, 4, 'PIC 1 missing in live data'),
        ]
    }
    
    # Apply comparison results
    widget.apply_comparison_results(comparison_results)
    
    # Verify PIC 0 cells are GREEN (match)
    for col in range(5):
        item = widget.table_widget.item(0, col)
        assert item is not None
        # Check green color (match)
        assert item.foreground().color() == QColor("#4CAF50")
    
    # Verify PIC 1 cells show RED text with file values (NOT disappeared)
    expected_values = ['EE', 'FF', 'GG', 'HH', '20']
    for col in range(5):
        item = widget.table_widget.item(1, col)
        assert item is not None
        # Check text is present (file value)
        assert item.text() == expected_values[col], f"Col {col} text should be {expected_values[col]}, got {item.text()}"
        # Check RED color (error)
        assert item.foreground().color() == QColor("#F44336"), f"Col {col} should be RED"
        # Check tooltip mentions error
        assert 'Card Missing/Error' in item.toolTip()


def test_card_reinsertion_shows_green_text(widget, mock_parser_service):
    """
    Test that when a card is reinserted (present in live data after removal),
    the text shows GREEN if values match.
    """
    # Load initial file
    widget.load_token_file('/fake/path/AP01m_FBC_001.fbc')
    
    # First comparison: Card removed (PIC 1 missing)
    comparison_results_removed = {
        'success': True,
        'file_type': 'FBC',
        'match_percentage': 66.7,
        'total_cells': 15,
        'matches': [(0, 0), (0, 1), (0, 2), (0, 3), (0, 4)],
        'differences': [],
        'value_appeared': [],
        'errors': [
            (1, 0, 'PIC 1 missing in live data'),
            (1, 1, 'PIC 1 missing in live data'),
            (1, 2, 'PIC 1 missing in live data'),
            (1, 3, 'PIC 1 missing in live data'),
            (1, 4, 'PIC 1 missing in live data'),
        ]
    }
    widget.apply_comparison_results(comparison_results_removed)
    
    # Verify PIC 1 is RED
    for col in range(5):
        item = widget.table_widget.item(1, col)
        assert item.foreground().color() == QColor("#F44336")
    
    # Second comparison: Card reinserted (PIC 1 present, values match)
    comparison_results_reinserted = {
        'success': True,
        'file_type': 'FBC',
        'match_percentage': 100.0,
        'total_cells': 15,
        'matches': [
            (0, 0), (0, 1), (0, 2), (0, 3), (0, 4),  # PIC 0 match
            (1, 0), (1, 1), (1, 2), (1, 3), (1, 4),  # PIC 1 match (reinserted)
            (2, 0), (2, 1), (2, 2), (2, 3), (2, 4),  # PIC 2 match
        ],
        'differences': [],
        'value_appeared': [],
        'errors': []
    }
    widget.apply_comparison_results(comparison_results_reinserted)
    
    # Verify PIC 1 cells are now GREEN (match)
    for col in range(5):
        item = widget.table_widget.item(1, col)
        assert item is not None
        # Check green color (match)
        assert item.foreground().color() == QColor("#4CAF50"), f"Col {col} should be GREEN after reinsertion"
        # Check tooltip mentions match
        assert 'Match' in item.toolTip()


def test_card_with_different_values_shows_red(widget, mock_parser_service):
    """
    Test that when a card is present but has different values,
    it shows RED (difference), not disappearing.
    """
    # Load initial file
    widget.load_token_file('/fake/path/AP01m_FBC_001.fbc')
    
    # Comparison: PIC 1 present but values changed
    comparison_results = {
        'success': True,
        'file_type': 'FBC',
        'match_percentage': 73.3,
        'total_cells': 15,
        'matches': [
            (0, 0), (0, 1), (0, 2), (0, 3), (0, 4),  # PIC 0 match
            (2, 0), (2, 1), (2, 2), (2, 3), (2, 4),  # PIC 2 match
        ],
        'differences': [  # PIC 1 has different values
            (1, 0, 'EE', 'XX'),  # File: EE, Live: XX
            (1, 1, 'FF', 'YY'),
            (1, 2, 'GG', 'ZZ'),
            (1, 3, 'HH', 'WW'),
            (1, 4, '20', '99'),
        ],
        'value_appeared': [],
        'errors': []
    }
    widget.apply_comparison_results(comparison_results)
    
    # Verify PIC 1 cells show RED with live values
    expected_live_values = ['XX', 'YY', 'ZZ', 'WW', '99']
    for col in range(5):
        item = widget.table_widget.item(1, col)
        assert item is not None
        # Check text is live value
        assert item.text() == expected_live_values[col]
        # Check RED color (difference)
        assert item.foreground().color() == QColor("#F44336")
        # Check tooltip mentions value change
        assert 'Value Changed' in item.toolTip()


def test_state_tracking_cleared_on_new_file(widget, mock_parser_service):
    """
    Test that state tracking dictionaries are cleared when loading a new file.
    """
    # Load initial file
    widget.load_token_file('/fake/path/AP01m_FBC_001.fbc')
    
    # Apply comparison (populate _live_values)
    comparison_results = {
        'success': True,
        'file_type': 'FBC',
        'match_percentage': 100.0,
        'total_cells': 15,
        'matches': [(i, j) for i in range(3) for j in range(5)],
        'differences': [],
        'value_appeared': [],
        'errors': []
    }
    widget.apply_comparison_results(comparison_results)
    
    # Verify state is populated
    assert len(widget._live_values) > 0
    
    # Load same file again (simulates refresh)
    widget.load_token_file('/fake/path/AP01m_FBC_001.fbc')
    
    # Verify state is cleared
    assert len(widget._live_values) == 0
    assert len(widget._selected_cells) == 0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
