import pytest
import os
from unittest.mock import Mock, patch
from PyQt5.QtCore import QObject, pyqtSignal

from src.commander.log_writer import LogWriter
from src.commander.presenters.node_tree_presenter import NodeTreePresenter
from src.commander.models import Node, NodeToken

# --- Fixtures ---

@pytest.fixture
def mock_node_manager():
    nm = Mock()
    nm.log_root = "test_logs"
    return nm

@pytest.fixture
def log_writer(mock_node_manager):
    # Ensure the test_logs directory exists for LogWriter
    os.makedirs("test_logs", exist_ok=True)
    writer = LogWriter(mock_node_manager, log_root="test_logs")
    yield writer
    # Close handlers to release file lock
    for handler in writer.app_logger.handlers[:]:
        writer.app_logger.removeHandler(handler)
        handler.close()
    # Clean up test_logs after tests
    for root, dirs, files in os.walk("test_logs", topdown=False):
        for name in files:
            try:
                os.remove(os.path.join(root, name))
            except OSError as e:
                print(f"Error removing file {os.path.join(root, name)}: {e}")
        for name in dirs:
            try:
                os.rmdir(os.path.join(root, name))
            except OSError as e:
                print(f"Error removing directory {os.path.join(root, name)}: {e}")
    try:
        os.rmdir("test_logs")
    except OSError as e:
        print(f"Error removing directory test_logs: {e}")


@pytest.fixture
def node_tree_presenter():
    mock_view = Mock()
    mock_node_manager = Mock()
    mock_session_manager = Mock()
    
    # Mock LogWriter and CommandQueue instances, then their signals
    mock_log_writer_instance = Mock(spec=LogWriter)
    mock_log_writer_instance.log_write_completed = Mock()
    mock_log_writer_instance.log_write_completed.connect = Mock() # Ensure connect method exists
    
    mock_command_queue_instance = Mock()
    mock_command_queue_instance.command_completed = Mock()
    mock_command_queue_instance.command_completed.connect = Mock() # Ensure connect method exists

    mock_fbc_service = Mock()
    mock_rpc_service = Mock()
    mock_context_menu_service = Mock()
    mock_bstool_service = Mock()

    presenter = NodeTreePresenter(
        mock_view, mock_node_manager, mock_session_manager,
        mock_log_writer_instance, mock_command_queue_instance, mock_fbc_service,
        mock_rpc_service, mock_context_menu_service, mock_bstool_service
    )
    return presenter, mock_view, mock_log_writer_instance, mock_command_queue_instance

# --- LogWriter Tests ---

def test_get_file_line_count_empty_file(log_writer):
    filepath = os.path.join("test_logs", "empty.log")
    with open(filepath, 'w') as f:
        pass
    assert log_writer.get_file_line_count(filepath) == 0

def test_get_file_line_count_small_file(log_writer):
    filepath = os.path.join("test_logs", "small.log")
    with open(filepath, 'w') as f:
        f.write("line1\nline2\nline3")
    assert log_writer.get_file_line_count(filepath) == 3

def test_get_file_line_count_large_file(log_writer):
    filepath = os.path.join("test_logs", "large.log")
    with open(filepath, 'w') as f:
        for i in range(1000):
            f.write(f"line{i}\n")
    assert log_writer.get_file_line_count(filepath) == 1000

def test_log_write_completed_signal_write_to_log(log_writer):
    mock_slot = Mock()
    log_writer.log_write_completed.connect(mock_slot)
    
    token = NodeToken(name="TestNode", token_id="123", token_type="LOG", ip_address="127.0.0.1")
    # Mock active_node for LogWriter.write_to_log
    mock_active_node = Mock()
    mock_active_node.name = "ActiveNode"
    log_writer.node_manager.active_node = mock_active_node

    log_writer.write_to_log("Test content", "LOG", token=token)
    
    mock_slot.assert_called_once()
    args, kwargs = mock_slot.call_args
    assert args == "TestNode"
    assert args == "123"
    assert args is True # success
    assert "test_logs" in args # filepath
    assert args > 0 # line_count should be > 0

def test_log_write_completed_signal_append_to_file(log_writer):
    mock_slot = Mock()
    log_writer.log_write_completed.connect(mock_slot)
    
    filepath = os.path.join("test_logs", "append.log")
    with open(filepath, 'w') as f:
        f.write("initial line\n")
    
    token = NodeToken(name="TestNode", token_id="456", token_type="LOG", ip_address="127.0.0.1")
    log_writer.append_to_file(filepath, "Appended content", token=token)
    
    mock_slot.assert_called_once()
    args, kwargs = mock_slot.call_args
    assert args == "TestNode"
    assert args == "456"
    assert args is True # success
    assert args == filepath # filepath
    assert args == 2 # line_count should be 2

# --- NodeTreePresenter Tests ---

def test_handle_command_completed_updates_status(node_tree_presenter):
    presenter, _, _, _ = node_tree_presenter
    node_name = "NodeA"
    token = NodeToken(name=node_name, token_id="T1", token_type="FBC", ip_address="1.1.1.1")
    
    presenter.node_status[node_name] = {"command_success": None, "log_success": None, "line_count": None}
    presenter.handle_command_completed("cmd", "res", True, token)
    
    assert presenter.node_status[node_name]["command_success"] is True

def test_handle_log_write_completed_updates_status(node_tree_presenter):
    presenter, _, _, _ = node_tree_presenter
    node_name = "NodeB"
    
    presenter.node_status[node_name] = {"command_success": None, "log_success": None, "line_count": None}
    presenter.handle_log_write_completed(node_name, "T2", True, "/path/to/log.log", 10)
    
    assert presenter.node_status[node_name]["log_success"] is True
    assert presenter.node_status[node_name]["line_count"] == 10

@pytest.mark.parametrize("command_success, log_success, line_count, expected_color", [
    (True, True, 10, "green"),
    (True, True, 3, "yellow"),
    (False, True, 10, "red"),
    (True, False, 10, "red"),
    (False, False, 3, "red"),
    (True, True, None, "red"), # Fallback for missing line_count
])
def test_check_and_update_node_color_logic(node_tree_presenter, command_success, log_success, line_count, expected_color):
    presenter, mock_view, _, _ = node_tree_presenter
    node_name = "NodeC"
    
    presenter.node_status[node_name] = {
        "command_success": command_success,
        "log_success": log_success,
        "line_count": line_count
    }
    
    presenter._check_and_update_node_color(node_name)
    
    if command_success is not None and log_success is not None:
        mock_view.update_node_color.assert_called_once_with(node_name, expected_color)
        # Verify status is reset
        assert presenter.node_status[node_name] == {"command_success": None, "log_success": None, "line_count": None}
    else:
        mock_view.update_node_color.assert_not_called()
        # Status should not be reset if not fully determined
        assert presenter.node_status[node_name] == {
            "command_success": command_success,
            "log_success": log_success,
            "line_count": line_count
        }

def test_node_status_initialization_in_handle_log_write_completed(node_tree_presenter):
    presenter, _, _, _ = node_tree_presenter
    node_name = "NewNode"
    
    # Simulate log write completed for a node not yet in node_status
    presenter.handle_log_write_completed(node_name, "T3", True, "/path/to/new_log.log", 7)
    
    assert node_name in presenter.node_status
    assert presenter.node_status[node_name]["log_success"] is True
    assert presenter.node_status[node_name]["line_count"] == 7
    assert presenter.node_status[node_name]["command_success"] is None # Should be None initially