import os
import sys
import pytest
from unittest.mock import MagicMock, patch
from PyQt6.QtCore import QPoint, Qt
from PyQt6.QtWidgets import QMenu, QApplication, QTreeWidgetItem

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from commander.presenters.node_tree_presenter import NodeTreePresenter
from commander.services.bstool_command_service import BsToolCommandService
from commander.services.context_menu_service import ContextMenuService
from commander.services.context_menu_filter import ContextMenuFilterService
from commander.node_manager import NodeManager
from commander.models import NodeToken
from commander.command_queue import CommandQueue
from commander.log_writer import LogWriter
from commander.services.fbc_command_service import FbcCommandService
from commander.services.rpc_command_service import RpcCommandService

# Initialize QApplication once for all tests
@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app
    # Don't exit the app to avoid crashes

@pytest.fixture
def mock_node_manager():
    return MagicMock(spec=NodeManager)

@pytest.fixture
def mock_session_manager():
    return MagicMock()

@pytest.fixture
def mock_log_writer():
    return MagicMock(spec=LogWriter)

@pytest.fixture
def mock_command_queue():
    return MagicMock(spec=CommandQueue)

@pytest.fixture
def mock_fbc_service():
    return MagicMock(spec=FbcCommandService)

@pytest.fixture
def mock_rpc_service():
    return MagicMock(spec=RpcCommandService)

@pytest.fixture
def mock_bstool_service():
    return MagicMock(spec=BsToolCommandService)

@pytest.fixture
def mock_context_menu_filter():
    return MagicMock(spec=ContextMenuFilterService)

@pytest.fixture
def mock_context_menu_service(mock_node_manager, mock_context_menu_filter):
    service = ContextMenuService(mock_node_manager, mock_context_menu_filter)
    return service

@pytest.fixture
def mock_view():
    view = MagicMock()
    view.itemAt.return_value = None # Default to no item selected
    return view

@pytest.fixture
def node_tree_presenter(mock_view, mock_node_manager, mock_session_manager,
                        mock_log_writer, mock_command_queue, mock_fbc_service,
                        mock_rpc_service, mock_context_menu_service, mock_bstool_service):
    presenter = NodeTreePresenter(mock_view, mock_node_manager, mock_session_manager,
                                  mock_log_writer, mock_command_queue, mock_fbc_service,
                                  mock_rpc_service, mock_context_menu_service, mock_bstool_service)
    mock_context_menu_service.set_presenter(presenter)
    return presenter

class TestClearSubgroupLogFiles:
    """Test suite for the 'Clear All Subgroup Files' command functionality."""

    def test_clear_subgroup_log_files_calls_bstool_clear_log(self, node_tree_presenter, mock_bstool_service):
        """
        Test that clear_subgroup_log_files correctly iterates through log files
        and calls bstool_service.clear_log for each.
        """
        # Create a mock subgroup item (e.g., FBC section)
        subgroup_item = QTreeWidgetItem(["FBC"])
        subgroup_item.setData(0, Qt.ItemDataRole.UserRole, {
            "type": "section",
            "section_type": "FBC",
            "node": "AP01m"
        })

        # Create mock file items (children of the subgroup)
        log_path_1 = "/path/to/logs/FBC/AP01m/AP01m_162.fbc"
        log_path_2 = "/path/to/logs/FBC/AP01m/AP01m_163.fbc"

        file_item_1 = QTreeWidgetItem(["AP01m_162.fbc"])
        file_item_1.setData(0, Qt.ItemDataRole.UserRole, {"log_path": log_path_1})
        subgroup_item.addChild(file_item_1)

        file_item_2 = QTreeWidgetItem(["AP01m_163.fbc"])
        file_item_2.setData(0, Qt.ItemDataRole.UserRole, {"log_path": log_path_2})
        subgroup_item.addChild(file_item_2)

        # Track status messages
        status_messages = []
        node_tree_presenter.status_message_signal.connect(lambda msg, dur: status_messages.append(msg))

        # Call the method under test
        node_tree_presenter.clear_subgroup_log_files(subgroup_item)

        # Assert that clear_log was called for each log file
        mock_bstool_service.clear_log.assert_any_call(log_path_1)
        mock_bstool_service.clear_log.assert_any_call(log_path_2)
        assert mock_bstool_service.clear_log.call_count == 2

        # Assert status messages were emitted
        assert any("Clearing all FBC log files for node AP01m..." in msg for msg in status_messages)
        assert any("Cleared 2 FBC log files for node AP01m" in msg for msg in status_messages)

    def test_clear_subgroup_log_files_no_files(self, node_tree_presenter, mock_bstool_service):
        """Test clearing a subgroup with no log files."""
        subgroup_item = QTreeWidgetItem(["RPC"])
        subgroup_item.setData(0, Qt.ItemDataRole.UserRole, {
            "type": "section",
            "section_type": "RPC",
            "node": "AP02m"
        })

        status_messages = []
        node_tree_presenter.status_message_signal.connect(lambda msg, dur: status_messages.append(msg))

        node_tree_presenter.clear_subgroup_log_files(subgroup_item)

        mock_bstool_service.clear_log.assert_not_called()
        assert any("Clearing all RPC log files for node AP02m..." in msg for msg in status_messages)
        assert any("Cleared 0 RPC log files for node AP02m" in msg for msg in status_messages)

    def test_context_menu_shows_clear_all_action_for_subgroup(self, mock_context_menu_service, node_tree_presenter, mock_context_menu_filter, qapp):
        """
        Test that the context menu correctly displays the 'Clear All Subgroup Files'
        action for FBC/RPC subgroup items.
        """
        # Create test data for FBC subsection
        fbc_subsection_data = {
            "section_type": "FBC",
            "node": "AP01m"
        }

        # Create a mock menu
        menu = QMenu()

        # Mock the context menu filter to allow the new command
        mock_context_menu_filter.should_show_command.side_effect = lambda node_name, section_type, command_type, command_category: \
            (command_type == "all" and command_category == "subgroup") or \
            (command_type == "clear_all_subgroup_files" and command_category == "subgroup")

        # Mock get_node_tokens to return some test tokens (not directly used by clear action, but for print action)
        mock_tokens = [
            NodeToken("162", "FBC", "AP01m", "192.168.0.11")
        ]
        mock_context_menu_service.get_node_tokens = MagicMock(return_value=mock_tokens)

        # Mock presenter's clear_subgroup_log_files method
        node_tree_presenter.clear_subgroup_log_files = MagicMock()

        # Call show_context_menu with FBC subsection data
        position = QPoint(100, 100)
        with patch.object(menu, 'exec') as mock_menu_exec:
            result = mock_context_menu_service.show_context_menu(menu, fbc_subsection_data, position)

            assert result == True, "Context menu should be shown for FBC subsection"
            mock_menu_exec.assert_called_once_with(position)

            actions = menu.actions()
            print(f"DEBUG: Type of actions: {type(actions)}")
            print(f"DEBUG: Content of actions: {actions}")
            assert len(actions) == 2, f"Expected 2 actions, but got {len(actions)}"

            print_action = actions
            clear_action = actions

            assert print_action.text() == "Print All FBC Tokens for AP01m"
            assert clear_action.text() == "Clear All FBC Log Files for AP01m"

            # Trigger the clear action and verify presenter method is called
            clear_action.trigger()
            node_tree_presenter.clear_subgroup_log_files.assert_called_once()

    def test_context_menu_hides_clear_all_action_based_on_filter(self, mock_context_menu_service, node_tree_presenter, mock_context_menu_filter, qapp):
        """
        Test that the 'Clear All Subgroup Files' action is hidden when the filter rule
        disallows it.
        """
        fbc_subsection_data = {
            "section_type": "FBC",
            "node": "AP01m"
        }

        menu = QMenu()

        # Mock the context menu filter to hide the new command
        mock_context_menu_filter.should_show_command.side_effect = lambda node_name, section_type, command_type, command_category: \
            (command_type == "all" and command_category == "subgroup") and \
            not (command_type == "clear_all_subgroup_files" and section_type == "FBC")

        mock_tokens = [
            NodeToken("162", "FBC", "AP01m", "192.168.0.11")
        ]
        mock_context_menu_service.get_node_tokens = MagicMock(return_value=mock_tokens)

        node_tree_presenter.clear_subgroup_log_files = MagicMock()

        position = QPoint(100, 100)
        with patch.object(menu, 'exec') as mock_menu_exec:
            result = mock_context_menu_service.show_context_menu(menu, fbc_subsection_data, position)

            assert result == True, "Context menu should be shown for FBC subsection"
            mock_menu_exec.assert_called_once_with(position)

            actions = menu.actions()
            print(f"DEBUG: Type of actions: {type(actions)}")
            print(f"DEBUG: Content of actions: {actions}")
            assert len(actions) == 1, f"Expected 1 action, but got {len(actions)}"
            assert actions.text() == "Print All FBC Tokens for AP01m"

            # Ensure clear action was NOT added
            assert not any("Clear All FBC Log Files" in action.text() for action in actions)