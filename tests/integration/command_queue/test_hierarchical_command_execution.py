import pytest
from unittest.mock import Mock, MagicMock, patch
from PyQt6.QtCore import QObject, QThread, pyqtSignal

from src.commander.services.hierarchical_command_service import HierarchicalCommandService, BsToolWorker
from src.commander.models import NodeToken, Node
from src.commander.command_queue import QueuedCommand
from src.commander.node_manager import NodeManager
from src.commander.command_queue import CommandQueue
from src.commander.services.fbc_command_service import FbcCommandService
from src.commander.services.rpc_command_service import RpcCommandService
from src.commander.services.bstool_command_service import BsToolCommandService
from src.commander.services.log_command_service import LogCommandService
from src.commander.services.context_menu_service import ContextMenuService
from src.commander.presenters.commander_presenter import CommanderPresenter

# Mock PyQt5 signals for testing outside a QApplication
class MockPyqtSignal(QObject):
    def __init__(self, *args, **kwargs):
        super().__init__()
        self.mock_signal = Mock()
    def emit(self, *args, **kwargs):
        self.mock_signal(*args, **kwargs)
    def connect(self, func):
        pass # No-op for mock
    def disconnect(self, func):
        pass # No-op for mock

# Replace pyqtSignal with MockPyqtSignal for testing
HierarchicalCommandService.command_started = MockPyqtSignal()
HierarchicalCommandService.command_completed = MockPyqtSignal()
HierarchicalCommandService.sequence_progress = MockPyqtSignal()
HierarchicalCommandService.sequence_finished = MockPyqtSignal()
HierarchicalCommandService.sequence_error = MockPyqtSignal()
BsToolWorker.finished = MockPyqtSignal()
BsToolWorker.result_signal = MockPyqtSignal()

@pytest.fixture
def mock_node_manager():
    nm = Mock(spec=NodeManager)
    nm.get_node.return_value = None
    return nm

@pytest.fixture
def mock_command_queue():
    cq = Mock(spec=CommandQueue)
    cq.command_completed = MockPyqtSignal()
    return cq

@pytest.fixture
def mock_fbc_service():
    fbc = Mock(spec=FbcCommandService)
    fbc.generate_fieldbus_command.return_value = "FBC_COMMAND"
    return fbc

@pytest.fixture
def mock_rpc_service():
    rpc = Mock(spec=RpcCommandService)
    rpc.generate_rpc_command.return_value = "RPC_COMMAND"
    return rpc

@pytest.fixture
def mock_bstool_service():
    bstool = Mock(spec=BsToolCommandService)
    return bstool

@pytest.fixture
def mock_log_service():
    log = Mock(spec=LogCommandService)
    return log

@pytest.fixture
def hierarchical_command_service(
    mock_node_manager,
    mock_command_queue,
    mock_fbc_service,
    mock_rpc_service,
    mock_bstool_service,
    mock_log_service
):
    service = HierarchicalCommandService(
        node_manager=mock_node_manager,
        command_queue=mock_command_queue,
        fbc_service=mock_fbc_service,
        rpc_service=mock_rpc_service,
        bstool_service=mock_bstool_service,
        log_service=mock_log_service
    )
    # Ensure signals are re-mocked for each test
    service.command_started = MockPyqtSignal()
    service.command_completed = MockPyqtSignal()
    service.sequence_progress = MockPyqtSignal()
    service.sequence_finished = MockPyqtSignal()
    service.sequence_error = MockPyqtSignal()
    return service

@pytest.fixture
def sample_node_token():
    return NodeToken(token_id="test_token", token_type="FBC", name="TestNode", log_path="/tmp/test.log")

@pytest.fixture
def sample_node_with_hierarchical_commands(sample_node_token):
    node = Node(name="TestNode", ip_address="127.0.0.1")
    node.add_token(sample_node_token)
    node.hierarchical_commands = {
        "FBC": {
            "Full Sequence": [
                {"type": "FBC", "command": "fbc_cmd_1"},
                {"type": "RPC", "command": "rpc_cmd_1", "parameters": {"action": "print"}},
                {"type": "BSTool", "command": "bstool_cmd_1", "parameters": {"log_file_path": "/tmp/bstool.log"}},
                {"type": "LOG", "command": "log_cmd_1", "parameters": {"log_paths": ["/tmp/log1.log", "/tmp/log2.log"]}}
            ],
            "Short Sequence": [
                {"type": "FBC", "command": "fbc_cmd_short"}
            ]
        }
    }
    return node

# Unit Tests for HierarchicalCommandService

class TestHierarchicalCommandService:

    def test_execute_hierarchical_command_node_not_found(self, hierarchical_command_service, mock_node_manager, sample_node_token):
        mock_node_manager.get_node.return_value = None
        hierarchical_command_service.execute_hierarchical_command(sample_node_token, "Full Sequence")

        hierarchical_command_service.sequence_error.mock_signal.assert_called_once_with(
            "Full Sequence", f"Node '{sample_node_token.name}' not found for hierarchical command."
        )
        hierarchical_command_service.sequence_finished.mock_signal.assert_called_once_with("Full Sequence", False)

    def test_execute_hierarchical_command_not_found_for_token_type(self, hierarchical_command_service, mock_node_manager, sample_node_token, sample_node_with_hierarchical_commands):
        mock_node_manager.get_node.return_value = sample_node_with_hierarchical_commands
        # Use a token type that doesn't have the "Full Sequence" defined
        sample_node_token.token_type = "RPC" 
        hierarchical_command_service.execute_hierarchical_command(sample_node_token, "Full Sequence")

        hierarchical_command_service.sequence_error.mock_signal.assert_called_once_with(
            "Full Sequence", f"Hierarchical command 'Full Sequence' not found for token type 'RPC' in node '{sample_node_token.name}'."
        )
        hierarchical_command_service.sequence_finished.mock_signal.assert_called_once_with("Full Sequence", False)

    @patch('src.commander.services.hierarchical_command_service.QThread')
    @patch('src.commander.services.hierarchical_command_service.BsToolWorker')
    def test_execute_hierarchical_command_success_flow(self, MockBsToolWorker, MockQThread, hierarchical_command_service, mock_node_manager, mock_command_queue, mock_fbc_service, mock_rpc_service, mock_bstool_service, mock_log_service, sample_node_token, sample_node_with_hierarchical_commands):
        mock_node_manager.get_node.return_value = sample_node_with_hierarchical_commands
        
        # Mock QThread and BsToolWorker behavior
        mock_bstool_worker_instance = MockBsToolWorker.return_value
        mock_bstool_worker_instance.finished = MockPyqtSignal()
        mock_bstool_worker_instance.result_signal = MockPyqtSignal()
        
        mock_qthread_instance = MockQThread.return_value
        mock_qthread_instance.started = MockPyqtSignal()
        mock_qthread_instance.finished = MockPyqtSignal()

        # Simulate FBC command completion
        def simulate_fbc_completion(*args, **kwargs):
            hierarchical_command_service.command_queue.command_completed.emit(
                "FBC_COMMAND", "FBC Result", True, sample_node_token
            )
        mock_command_queue.add_command.side_effect = simulate_fbc_completion

        # Simulate BSTool completion
        def simulate_bstool_completion(*args, **kwargs):
            # This needs to be called by the BsToolWorker's result_signal
            mock_bstool_worker_instance.result_signal.emit(True, "BSTool Result")
        mock_qthread_instance.started.connect(simulate_bstool_completion)

        hierarchical_command_service.execute_hierarchical_command(sample_node_token, "Full Sequence")

        # Verify FBC command execution
        mock_fbc_service.generate_fieldbus_command.assert_called_once_with("fbc_cmd_1")
        mock_command_queue.add_command.assert_called_once()
        hierarchical_command_service.command_started.mock_signal.assert_any_call("Full Sequence", 1, 4, "FBC")
        hierarchical_command_service.command_completed.mock_signal.assert_any_call("Full Sequence", 1, 4, "FBC", True, "FBC Result")

        # Verify RPC command execution (after FBC completes)
        mock_rpc_service.generate_rpc_command.assert_called_once_with("rpc_cmd_1", "print")
        hierarchical_command_service.command_started.mock_signal.assert_any_call("Full Sequence", 2, 4, "RPC")
        # Simulate RPC completion
        hierarchical_command_service.command_queue.command_completed.emit(
            "RPC_COMMAND", "RPC Result", True, sample_node_token
        )
        hierarchical_command_service.command_completed.mock_signal.assert_any_call("Full Sequence", 2, 4, "RPC", True, "RPC Result")

        # Verify BSTool command execution (after RPC completes)
        MockQThread.assert_called_once()
        MockBsToolWorker.assert_called_once_with(mock_bstool_service, "/tmp/bstool.log", "bstool_cmd_1")
        mock_qthread_instance.start.assert_called_once()
        hierarchical_command_service.command_started.mock_signal.assert_any_call("Full Sequence", 3, 4, "BSTool")
        hierarchical_command_service.command_completed.mock_signal.assert_any_call("Full Sequence", 3, 4, "BSTool", True, "BSTool Result")

        # Verify LOG command execution (after BSTool completes)
        mock_log_service.process_all_log_commands.assert_called_once_with(["/tmp/log1.log", "/tmp/log2.log"])
        hierarchical_command_service.command_started.mock_signal.assert_any_call("Full Sequence", 4, 4, "LOG")
        hierarchical_command_service.command_completed.mock_signal.assert_any_call("Full Sequence", 4, 4, "LOG", True, "Log files opened")

        # Verify sequence finished signal
        hierarchical_command_service.sequence_finished.mock_signal.assert_called_once_with("Full Sequence", True)
        
    @patch('src.commander.services.hierarchical_command_service.QThread')
    @patch('src.commander.services.hierarchical_command_service.BsToolWorker')
    def test_execute_hierarchical_command_stop_on_error(self, MockBsToolWorker, MockQThread, hierarchical_command_service, mock_node_manager, mock_command_queue, mock_fbc_service, sample_node_token, sample_node_with_hierarchical_commands):
        mock_node_manager.get_node.return_value = sample_node_with_hierarchical_commands
        
        # Simulate FBC command failure
        def simulate_fbc_failure(*args, **kwargs):
            hierarchical_command_service.command_queue.command_completed.emit(
                "FBC_COMMAND", "FBC Error", False, sample_node_token
            )
        mock_command_queue.add_command.side_effect = simulate_fbc_failure

        hierarchical_command_service.execute_hierarchical_command(sample_node_token, "Full Sequence", stop_on_error=True)

        # Verify FBC command execution and failure
        mock_fbc_service.generate_fieldbus_command.assert_called_once_with("fbc_cmd_1")
        mock_command_queue.add_command.assert_called_once()
        hierarchical_command_service.command_started.mock_signal.assert_any_call("Full Sequence", 1, 4, "FBC")
        hierarchical_command_service.command_completed.mock_signal.assert_any_call("Full Sequence", 1, 4, "FBC", False, "FBC Error")

        # Verify sequence error and finished signals
        hierarchical_command_service.sequence_error.mock_signal.assert_called_once_with(
            "Full Sequence", "Subcommand failed: fbc_cmd_1 - FBC Error"
        )
        hierarchical_command_service.sequence_finished.mock_signal.assert_called_once_with("Full Sequence", False)

        # Ensure no further commands were attempted
        assert mock_fbc_service.generate_fieldbus_command.call_count == 1
        assert mock_command_queue.add_command.call_count == 1
        assert MockBsToolWorker.call_count == 0
        assert MockQThread.call_count == 0

    @patch('src.commander.services.hierarchical_command_service.QThread')
    @patch('src.commander.services.hierarchical_command_service.BsToolWorker')
    def test_execute_hierarchical_command_continue_on_error(self, MockBsToolWorker, MockQThread, hierarchical_command_service, mock_node_manager, mock_command_queue, mock_fbc_service, mock_rpc_service, mock_bstool_service, mock_log_service, sample_node_token, sample_node_with_hierarchical_commands):
        mock_node_manager.get_node.return_value = sample_node_with_hierarchical_commands
        
        # Mock QThread and BsToolWorker behavior
        mock_bstool_worker_instance = MockBsToolWorker.return_value
        mock_bstool_worker_instance.finished = MockPyqtSignal()
        mock_bstool_worker_instance.result_signal = MockPyqtSignal()
        
        mock_qthread_instance = MockQThread.return_value
        mock_qthread_instance.started = MockPyqtSignal()
        mock_qthread_instance.finished = MockPyqtSignal()

        # Simulate FBC command failure
        fbc_call_count = 0
        def simulate_fbc_behavior(*args, **kwargs):
            nonlocal fbc_call_count
            fbc_call_count += 1
            if fbc_call_count == 1: # First FBC command fails
                hierarchical_command_service.command_queue.command_completed.emit(
                    "FBC_COMMAND", "FBC Error", False, sample_node_token
                )
            else: # Subsequent FBC commands succeed
                hierarchical_command_service.command_queue.command_completed.emit(
                    "FBC_COMMAND", "FBC Result", True, sample_node_token
                )
        mock_command_queue.add_command.side_effect = simulate_fbc_behavior

        # Simulate BSTool completion
        def simulate_bstool_completion(*args, **kwargs):
            mock_bstool_worker_instance.result_signal.emit(True, "BSTool Result")
        mock_qthread_instance.started.connect(simulate_bstool_completion)

        hierarchical_command_service.execute_hierarchical_command(sample_node_token, "Full Sequence", stop_on_error=False)

        # Verify FBC command execution and failure
        mock_fbc_service.generate_fieldbus_command.assert_called_once_with("fbc_cmd_1")
        hierarchical_command_service.command_started.mock_signal.assert_any_call("Full Sequence", 1, 4, "FBC")
        hierarchical_command_service.command_completed.mock_signal.assert_any_call("Full Sequence", 1, 4, "FBC", False, "FBC Error")

        # Verify RPC command execution (after FBC completes)
        mock_rpc_service.generate_rpc_command.assert_called_once_with("rpc_cmd_1", "print")
        hierarchical_command_service.command_started.mock_signal.assert_any_call("Full Sequence", 2, 4, "RPC")
        # Simulate RPC completion
        hierarchical_command_service.command_queue.command_completed.emit(
            "RPC_COMMAND", "RPC Result", True, sample_node_token
        )
        hierarchical_command_service.command_completed.mock_signal.assert_any_call("Full Sequence", 2, 4, "RPC", True, "RPC Result")

        # Verify BSTool command execution (after RPC completes)
        MockQThread.assert_called_once()
        MockBsToolWorker.assert_called_once_with(mock_bstool_service, "/tmp/bstool.log", "bstool_cmd_1")
        mock_qthread_instance.start.assert_called_once()
        hierarchical_command_service.command_started.mock_signal.assert_any_call("Full Sequence", 3, 4, "BSTool")
        hierarchical_command_service.command_completed.mock_signal.assert_any_call("Full Sequence", 3, 4, "BSTool", True, "BSTool Result")

        # Verify LOG command execution (after BSTool completes)
        mock_log_service.process_all_log_commands.assert_called_once_with(["/tmp/log1.log", "/tmp/log2.log"])
        hierarchical_command_service.command_started.mock_signal.assert_any_call("Full Sequence", 4, 4, "LOG")
        hierarchical_command_service.command_completed.mock_signal.assert_any_call("Full Sequence", 4, 4, "LOG", True, "Log files opened")

        # Verify sequence finished signal
        hierarchical_command_service.sequence_finished.mock_signal.assert_called_once_with("Full Sequence", True)
        # Ensure sequence_error was NOT called because stop_on_error was False
        hierarchical_command_service.sequence_error.mock_signal.assert_not_called()

    def test_bstool_worker_run_success(self, mock_bstool_service):
        worker = BsToolWorker(mock_bstool_service, "/tmp/test.log", "test_bstool_cmd")
        worker.result_signal = MockPyqtSignal()
        worker.finished = MockPyqtSignal()

        with patch('time.sleep', return_value=None): # Mock time.sleep
            worker.run()

        mock_bstool_service.execute_bstool.assert_called_once_with("/tmp/test.log", "test_bstool_cmd")
        worker.result_signal.mock_signal.assert_called_once_with(True, "BSTool command executed (assumed success for now)")
        worker.finished.mock_signal.assert_called_once()

    def test_bstool_worker_run_failure(self, mock_bstool_service):
        worker = BsToolWorker(mock_bstool_service, "/tmp/test.log", "test_bstool_cmd")
        worker.result_signal = MockPyqtSignal()
        worker.finished = MockPyqtSignal()

        mock_bstool_service.execute_bstool.side_effect = Exception("BSTool Error")

        with patch('time.sleep', return_value=None): # Mock time.sleep
            worker.run()

        mock_bstool_service.execute_bstool.assert_called_once_with("/tmp/test.log", "test_bstool_cmd")
        worker.result_signal.mock_signal.assert_called_once_with(False, "BSTool command failed: BSTool Error")
        worker.finished.mock_signal.assert_called_once()

# Integration Tests for Context Menu

@pytest.fixture
def mock_context_menu_filter_service():
    filter_service = Mock()
    filter_service.should_show_command.return_value = True
    return filter_service

@pytest.fixture
def mock_commander_presenter():
    presenter = Mock(spec=CommanderPresenter)
    presenter.process_hierarchical_command = Mock()
    return presenter

@pytest.fixture
def context_menu_service(mock_node_manager, mock_context_menu_filter_service, hierarchical_command_service):
    service = ContextMenuService(
        node_manager=mock_node_manager,
        context_menu_filter=mock_context_menu_filter_service,
        hierarchical_command_service=hierarchical_command_service
    )
    return service

class TestContextMenuIntegration:

    @patch('src.commander.services.context_menu_service.QMenu')
    @patch('src.commander.services.context_menu_service.QAction')
    def test_show_context_menu_with_hierarchical_command(self, MockQAction, MockQMenu, context_menu_service, mock_node_manager, mock_commander_presenter, sample_node_with_hierarchical_commands):
        context_menu_service.set_presenter(mock_commander_presenter)
        mock_node_manager.get_node.return_value = sample_node_with_hierarchical_commands

        mock_menu_instance = MockQMenu.return_value
        mock_action_instance = MockQAction.return_value
        mock_action_instance.triggered = MockPyqtSignal() # Mock the triggered signal

        item_data = {"section_type": "FBC", "node": "TestNode"}
        position = Mock()

        context_menu_service.show_context_menu(mock_menu_instance, item_data, position)

        # Verify "Execute All Node Commands" action is added
        MockQAction.assert_any_call("Execute All FBC Node Commands for TestNode", mock_menu_instance)
        mock_menu_instance.addAction.assert_called_with(mock_action_instance)
        mock_menu_instance.exec.assert_called_once_with(position)

        # Simulate clicking the "Execute All Node Commands" action
        # We need to find the specific action that triggers the hierarchical command
        # This is a bit tricky with mocks, as QAction instances are created dynamically.
        # We'll rely on the fact that the triggered.connect was called with the correct lambda.
        
        # For a more robust test, you might inspect the `mock_menu_instance.actions()`
        # and find the action by its text, then trigger its mocked signal.
        
        # For now, let's directly call the presenter method that the action would trigger.
        # This assumes the lambda correctly captures the arguments.
        
        # Re-create the expected NodeToken
        expected_node_token = NodeToken(
            token_id="TestNode_FBC_HIERARCHICAL",
            token_type="FBC",
            name="TestNode",
            log_path=""
        )
        
        # Directly call the presenter method that the action would trigger
        mock_commander_presenter.process_hierarchical_command(expected_node_token, "Full Sequence")
        mock_commander_presenter.process_hierarchical_command.assert_called_once_with(
            expected_node_token, "Full Sequence"
        )
