import pytest
from unittest.mock import MagicMock, patch
from PyQt6.QtWidgets import QApplication, QPlainTextEdit, QPushButton
from src.commander.presenters.commander_presenter import CommanderPresenter
from src.commander.ui.commander_ui_factory import CommanderUIFactory
from src.commander.ui.session_view import SessionView
from src.commander.ui.telnet_tab import TelnetTab
from src.commander.node_manager import NodeManager
from src.commander.log_writer import LogWriter
from src.commander.services.status_service import StatusService

@pytest.fixture(scope="module")
def app():
    """Fixture for a QApplication instance."""
    return QApplication([])

@pytest.fixture
def mock_ui_factory(app):
    """Fixture for a mocked CommanderUIFactory."""
    # Create mocks for the UI components
    ui_factory = MagicMock(spec=CommanderUIFactory)
    session_view = MagicMock(spec=SessionView)
    telnet_tab = MagicMock(spec=TelnetTab)
    vnc_tab = MagicMock()  # Add mock for vnc_tab
    node_tree_view = MagicMock()  # Add missing mock
    
    # Set up the mock hierarchy
    ui_factory.session_view = session_view
    ui_factory.node_tree_view = node_tree_view  # Add to UI factory
    ui_factory.vnc_tab = vnc_tab  # For CommanderPresenter
    session_view.vnc_tab = vnc_tab  # For SessionPresenter
    session_view.telnet_tab = telnet_tab
    
    # Mock the output widget
    telnet_tab.output = MagicMock(spec=QPlainTextEdit)
    
    return ui_factory

@pytest.fixture
def mock_services(app):
    """Fixture for mocked services."""
    node_manager = MagicMock(spec=NodeManager)
    log_writer = MagicMock(spec=LogWriter)
    status_service = MagicMock(spec=StatusService)
    
    return {
        'node_manager': node_manager,
        'log_writer': log_writer,
        'status_service': status_service
    }

@pytest.fixture
def commander_presenter(mock_ui_factory, mock_services):
    """Fixture for CommanderPresenter with mocked dependencies."""
    presenter = CommanderPresenter(
        ui_factory=mock_ui_factory,
        node_manager=mock_services['node_manager'],
        log_writer=mock_services['log_writer'],
        status_service=mock_services['status_service'],
        session_manager=MagicMock(),
        command_queue=MagicMock(),
        fbc_service=MagicMock(),
        rpc_service=MagicMock(),
        context_menu_service=MagicMock()
    )
    return presenter

class TestButtonActions:
    """Tests for button action functionalities."""

    def test_clear_terminal_button(self, commander_presenter, mock_ui_factory):
        """Verify that clear_terminal method calls the output.clear() method on the telnet tab."""
        commander_presenter.clear_terminal()
        mock_ui_factory.session_view.telnet_tab.output.clear.assert_called_once()