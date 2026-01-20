import pytest
from unittest.mock import MagicMock, patch
from PyQt6.QtCore import QModelIndex, Qt
from PyQt6.QtWidgets import QApplication

# Mock QApplication for PyQt5 tests
@pytest.fixture(scope='session', autouse=True)
def qapplication_fixture():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app
    if app is not None:
        app.quit()

# Import necessary modules from src
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'src')))

from commander.presenters.node_tree_presenter import NodeTreePresenter
from commander.models import Node, NodeToken
from commander.ui.commander_window import CommanderWindow
from commander.ui.telnet_tab import TelnetTab
from commander.node_manager import NodeManager
from commander.services.commander_service import CommanderService
from commander.services.telnet_service import TelnetService
from commander.session_manager import SessionManager, SessionConfig, SessionType

class TestNodeClickPopulatesTelnetTab:
    @pytest.fixture
    def mock_node_manager(self):
        nm = MagicMock(spec=NodeManager)
        nm.get_node.return_value = Node(name='AP01m', ip_address='192.168.0.11', tokens={
            'FBC': [NodeToken(token_id='162', token_type='FBC', name='AP01m', ip_address='192.168.0.11', log_path='test_logs/FBC/AP01m/AP01m_192-168-0-11_162.fbc')],
            'RPC': [NodeToken(token_id='162', token_type='RPC', name='AP01m', ip_address='192.168.0.11', log_path='test_logs/RPC/AP01m/AP01m_192-168-0-11_162.rpc')]
        })
        return nm

    @pytest.fixture
    def mock_commander_service(self):
        cs = MagicMock(spec=CommanderService)
        return cs

    @pytest.fixture
    def mock_telnet_service(self):
        ts = MagicMock(spec=TelnetService)
        ts.active_telnet_client = MagicMock()
        ts.active_telnet_client.is_connected = True
        return ts

    @pytest.fixture
    def mock_session_manager(self):
        sm = MagicMock(spec=SessionManager)
        return sm

    @pytest.fixture
    def mock_log_writer(self):
        lw = MagicMock()
        return lw

    @pytest.fixture
    def mock_command_queue(self):
        cq = MagicMock()
        return cq

    @pytest.fixture
    def mock_fbc_service(self):
        fbc = MagicMock()
        return fbc

    @pytest.fixture
    def mock_rpc_service(self):
        rpc = MagicMock()
        return rpc

    @pytest.fixture
    def mock_context_menu_service(self):
        cms = MagicMock()
        return cms

    @pytest.fixture
    def mock_bstool_service(self):
        bts = MagicMock()
        return bts

    @pytest.fixture
    def telnet_tab(self):
        tab = TelnetTab()
        tab.command_input = MagicMock() # Mock the QLineEdit for command input
        return tab

    @pytest.fixture
    def commander_window(self, telnet_tab, mock_node_manager, mock_session_manager, mock_log_writer, mock_command_queue, mock_fbc_service, mock_rpc_service, mock_context_menu_service, mock_bstool_service):
        from PyQt6.QtWidgets import QWidget # Import QWidget for mocking
        mock_ui_factory = MagicMock()
        mock_ui_factory.get_main_widget.return_value = QWidget() # Return an actual QWidget instance
        mock_ui_factory.session_view.telnet_tab = telnet_tab
        mock_ui_factory.session_view.bstool_tab = MagicMock()
        mock_ui_factory.session_view.vnc_tab = MagicMock()
        mock_ui_factory.node_tree_view = MagicMock()

        mock_commander_presenter = MagicMock()
        mock_commander_presenter.set_cmd_input_text_signal = MagicMock()

        with patch('commander.ui.commander_ui_factory.CommanderUIFactory', return_value=mock_ui_factory), \
             patch('commander.ui.commander_window.NodeManager', return_value=mock_node_manager), \
             patch('commander.ui.commander_window.SessionManager', return_value=mock_session_manager), \
             patch('commander.ui.commander_window.CommandQueue', return_value=mock_command_queue), \
             patch('commander.ui.commander_window.LogWriter', return_value=mock_log_writer), \
             patch('commander.ui.commander_window.StatusService', return_value=MagicMock()), \
             patch('commander.ui.commander_window.ContextMenuFilterService', return_value=MagicMock()), \
             patch('commander.ui.commander_window.FbcCommandService', return_value=mock_fbc_service), \
             patch('commander.ui.commander_window.RpcCommandService', return_value=mock_rpc_service), \
             patch('commander.ui.commander_window.BsToolCommandService', return_value=mock_bstool_service), \
             patch('commander.ui.commander_window.CommanderService', return_value=MagicMock()), \
             patch('commander.ui.commander_window.TelnetService', return_value=MagicMock()), \
             patch('commander.ui.commander_window.ContextMenuService', return_value=mock_context_menu_service), \
             patch('commander.ui.commander_window.CommanderPresenter', return_value=mock_commander_presenter), \
             patch('commander.ui.commander_window.NodeTreePresenter', return_value=MagicMock()):
            
            window = CommanderWindow()
            window.telnet_tab = telnet_tab # Ensure the mocked telnet_tab is used
            window.tab_widget = MagicMock()
            window.tab_widget.currentWidget.return_value = telnet_tab # Simulate Telnet tab being active
            window.tab_widget.indexOf.return_value = 0 # Simulate Telnet tab index
            window.tab_widget.setCurrentIndex.return_value = None # Mock setCurrentIndex
            window.session_tabs = MagicMock() # Mock session_tabs
            window.session_tabs.setCurrentWidget.return_value = None # Mock setCurrentWidget
            window.node_tree_view = mock_ui_factory.node_tree_view # Assign mocked node_tree_view
            window.status_service = MagicMock() # Mock status_service
            window.commander_presenter = mock_commander_presenter # Assign mocked commander_presenter
            return window

    @pytest.fixture
    def node_tree_presenter(self, mock_node_manager, mock_session_manager, mock_log_writer,
                            mock_command_queue, mock_fbc_service, mock_rpc_service,
                            mock_context_menu_service, mock_bstool_service):
        view = MagicMock() # Mock the view
        presenter = NodeTreePresenter(view, mock_node_manager, mock_session_manager,
                                      mock_log_writer, mock_command_queue,
                                      mock_fbc_service, mock_rpc_service,
                                      mock_context_menu_service, mock_bstool_service)
        return presenter

    def test_fbc_node_click_populates_telnet_command_input(self, node_tree_presenter, commander_window, telnet_tab, mock_node_manager):
        # Connect the signal from presenter to commander window's commander_presenter
        # The actual connection in CommanderWindow is:
        # self.node_tree_presenter.command_generated_signal.connect(self.commander_presenter.handle_command_generated)
        # And then self.commander_presenter.set_cmd_input_text_signal.connect(self.telnet_tab.command_input.setText)
        
        # Mock the handle_command_generated method of commander_presenter
        commander_window.commander_presenter.handle_command_generated = MagicMock()
        
        # Connect the node_tree_presenter's signal to the mocked handler
        node_tree_presenter.command_generated_signal.connect(commander_window.commander_presenter.handle_command_generated)

        # Simulate a node click for an FBC token
        node_name = 'AP01m'
        token_id = '162'
        token_type = 'FBC'
        command = f'print from fbc io structure {token_id}0000'

        # Mock the QModelIndex to return the necessary data
        mock_index = MagicMock(spec=QModelIndex)
        mock_index.data.side_effect = lambda row, role: {
            Qt.ItemDataRole.DisplayRole: f'{node_name} - {token_id}',
            Qt.ItemDataRole.UserRole + 1: {'node_name': node_name, 'token_id': token_id, 'token_type': token_type}
        }.get(role)
        mock_index.isValid.return_value = True

        # Simulate on_node_selected being called
        node_tree_presenter.on_node_selected(mock_index)

        # Assert that handle_command_generated was called with the correct command
        commander_window.commander_presenter.handle_command_generated.assert_called_once_with(command, token_type)
        
        # Simulate the commander_presenter emitting its signal
        commander_window.commander_presenter.set_cmd_input_text_signal.emit(command)

        # Assert that the command input in the Telnet tab is updated
        telnet_tab.command_input.setText.assert_called_once_with(command)
        commander_window.session_tabs.setCurrentWidget.assert_called_once_with(telnet_tab)


    def test_rpc_node_click_populates_telnet_command_input(self, node_tree_presenter, commander_window, telnet_tab, mock_node_manager):
        # Connect the signal from presenter to commander window's commander_presenter
        commander_window.commander_presenter.handle_command_generated = MagicMock()
        node_tree_presenter.command_generated_signal.connect(commander_window.commander_presenter.handle_command_generated)

        # Simulate a node click for an RPC token
        node_name = 'AP01m'
        token_id = '162'
        token_type = 'RPC'
        command = f'print from fbc rupi counters {token_id}0000'

        # Mock the QModelIndex to return the necessary data
        mock_index = MagicMock(spec=QModelIndex)
        mock_index.data.side_effect = lambda row, role: {
            Qt.ItemDataRole.DisplayRole: f'{node_name} - {token_id}',
            Qt.ItemDataRole.UserRole + 1: {'node_name': node_name, 'token_id': token_id, 'token_type': token_type}
        }.get(role)
        mock_index.isValid.return_value = True

        # Simulate on_node_selected being called
        node_tree_presenter.on_node_selected(mock_index)

        # Assert that handle_command_generated was called with the correct command
        commander_window.commander_presenter.handle_command_generated.assert_called_once_with(command, token_type)
        
        # Simulate the commander_presenter emitting its signal
        commander_window.commander_presenter.set_cmd_input_text_signal.emit(command)

        # Assert that the command input in the Telnet tab is updated
        telnet_tab.command_input.setText.assert_called_once_with(command)
        commander_window.session_tabs.setCurrentWidget.assert_called_once_with(telnet_tab)

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
