import pytest
from unittest.mock import Mock, MagicMock
from PyQt5.QtCore import QObject, pyqtSignal, Qt
from PyQt5.QtWidgets import QTreeWidgetItem
from src.commander.presenters.node_tree_presenter import NodeTreePresenter
from src.commander.models import NodeToken
import os

class TestNodeTreePresenterSignals:

    @pytest.fixture
    def setup_presenter(self):
        # Mock dependencies
        mock_view = MagicMock() # Use MagicMock for view
        # Ensure item_expanded is a mock that has a connect method
        mock_view.item_expanded = Mock()
        mock_view.item_expanded.connect = Mock() # Explicitly mock the connect method
        mock_node_manager = Mock()
        mock_session_manager = Mock()
        mock_log_writer = Mock()
        mock_command_queue = Mock()
        mock_fbc_service = Mock()
        mock_rpc_service = Mock()
        mock_context_menu_service = Mock()
        mock_bstool_service = Mock()

        # Mock command generation methods
        mock_fbc_service.generate_fieldbus_command.return_value = "FBC_COMMAND_GENERATED"
        mock_rpc_service.generate_rpc_command.return_value = "RPC_COMMAND_GENERATED"
        # BSTOOL command is generated within the presenter, so mock its dependencies
        mock_bstool_service._get_bstool_path.return_value = "/fake/path/to/BsTool.exe"

        presenter = NodeTreePresenter(
            mock_view,
            mock_node_manager,
            mock_session_manager,
            mock_log_writer,
            mock_command_queue,
            mock_fbc_service,
            mock_rpc_service,
            mock_context_menu_service,
            mock_bstool_service
        )
        return presenter, mock_fbc_service, mock_rpc_service, mock_bstool_service

    @pytest.mark.parametrize("token_type, expected_command", [
        ("FBC", "FBC_COMMAND_GENERATED"),
        ("RPC", "RPC_COMMAND_GENERATED"),
        ("BSTOOL", "/fake/path/to/BsTool.exe -errlog NODE_A"), # Updated expected command for BSTOOL
    ])
    def test_command_generated_signal_emitted_on_node_selection(self, setup_presenter, token_type, expected_command):
        presenter, mock_fbc_service, mock_rpc_service, mock_bstool_service = setup_presenter
        
        # Mock internal methods of presenter for BSTOOL command generation
        if token_type == "BSTOOL":
            presenter._extract_node_id_from_log_path = Mock(return_value="NODE_A")

        # Mock a QTreeWidgetItem
        mock_item = MagicMock(spec=QTreeWidgetItem)
        mock_item.data.return_value = {
            "log_path": "/fake/path/to/log.fbc",
            "token": "123",
            "token_type": token_type,
            "node": "NODE_A",
            "ip_address": "192.168.0.1"
        }

        # Create a mock slot to connect to the signal
        mock_slot = Mock()
        presenter.command_generated_signal.connect(mock_slot)

        # Simulate node selection
        presenter.on_node_selected(mock_item)

        # Assert that the signal was emitted with the correct command and token type
        mock_slot.assert_called_once_with(expected_command, token_type)

        # Verify the correct service method was called
        if token_type == "FBC":
            mock_fbc_service.generate_fieldbus_command.assert_called_once_with("123")
        elif token_type == "RPC":
            mock_rpc_service.generate_rpc_command.assert_called_once_with("123", "print") # RPC generate_rpc_command takes an action argument
        elif token_type == "BSTOOL":
            mock_bstool_service._get_bstool_path.assert_called_once()
            presenter._extract_node_id_from_log_path.assert_called_once_with("/fake/path/to/log.fbc")

    def test_log_file_selected_signal_emitted_on_node_selection(self, setup_presenter):
        presenter, _, _, _ = setup_presenter

        # Mock a QTreeWidgetItem
        mock_item = MagicMock(spec=QTreeWidgetItem)
        mock_item.data.return_value = {
            "log_path": "/fake/path/to/log.log",
            "token": "LOG_TOKEN",
            "token_type": "LOG",
            "node": "NODE_B",
            "ip_address": "192.168.0.2"
        }

        # Create a mock slot to connect to the signal
        mock_slot = Mock()
        presenter.log_file_selected_signal.connect(mock_slot)

        # Simulate node selection
        presenter.on_node_selected(mock_item)

        # Assert that the signal was emitted with the correct filename
        mock_slot.assert_called_once_with("log.log")

    def test_no_signal_emitted_for_non_log_file_item(self, setup_presenter):
        presenter, mock_fbc_service, mock_rpc_service, mock_bstool_service = setup_presenter

        # Mock a QTreeWidgetItem that is not a log file
        mock_item = MagicMock(spec=QTreeWidgetItem)
        mock_item.data.return_value = {
            "type": "node",
            "node_name": "NODE_C"
        }

        mock_command_slot = Mock()
        presenter.command_generated_signal.connect(mock_command_slot)
        mock_log_slot = Mock()
        presenter.log_file_selected_signal.connect(mock_log_slot)

        # Simulate node selection
        presenter.on_node_selected(mock_item)

        # Assert that no signals were emitted
        mock_command_slot.assert_not_called()
        mock_log_slot.assert_not_called()
        mock_fbc_service.generate_fieldbus_command.assert_not_called()
        mock_rpc_service.generate_rpc_command.assert_not_called()
        mock_bstool_service._get_bstool_path.assert_not_called()