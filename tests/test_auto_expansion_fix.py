"""
Test auto-expansion and highlighting during Print All Nodes workflow.

This test validates that when log_write_completed is triggered, it properly
calls _highlight_current_file to expand and highlight the processed file.
"""
import os
import sys
from unittest.mock import Mock, MagicMock, patch

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

def test_log_write_triggers_highlighting():
    """Test that handle_log_write_completed triggers _highlight_current_file"""
    from commander.presenters.node_tree_presenter import NodeTreePresenter
    from PyQt6.QtWidgets import QTreeWidgetItem
    from PyQt6.QtCore import Qt
    
    # Create mock dependencies
    view = Mock()
    node_manager = Mock()
    session_manager = Mock()
    log_writer = Mock()
    command_queue = Mock()
    fbc_service = Mock()
    rpc_service = Mock()
    context_menu_service = Mock()
    bstool_service = Mock()
    
    # Create presenter
    presenter = NodeTreePresenter(
        view, node_manager, session_manager, log_writer,
        command_queue, fbc_service, rpc_service,
        context_menu_service, bstool_service
    )
    
    # Setup test data
    log_path = "C:\\Users\\test\\_DIA\\FBC\\AP01\\AP01_192-168-0-11_162.fbc"
    normalized_path = os.path.normpath(log_path)
    
    # Create mock file item with proper data
    file_item = Mock(spec=QTreeWidgetItem)
    item_data = {
        "node": "AP01",
        "token": "162",
        "token_type": "FBC",
        "ip_address": "192.168.0.11",
        "log_path": normalized_path
    }
    file_item.data.return_value = item_data
    
    # Add to file_item_map
    presenter.file_item_map[normalized_path] = file_item
    
    # Mock _highlight_current_file to track if it's called
    presenter._highlight_current_file = Mock()
    
    # Trigger log write completion
    presenter.handle_log_write_completed(
        log_path=log_path,
        success=True,
        total_line_count=50,
        lines_written_by_command=50,
        content_written=""
    )
    
    # Verify _highlight_current_file was called
    assert presenter._highlight_current_file.called, "_highlight_current_file should be called"
    
    # Verify it was called with correct parameters
    call_args = presenter._highlight_current_file.call_args
    assert call_args is not None, "Should have call arguments"
    
    # Extract arguments
    node_name, token_info, file_path = call_args[0]
    
    assert node_name == "AP01", f"Expected node_name 'AP01', got '{node_name}'"
    assert token_info.token_id == "162", f"Expected token_id '162', got '{token_info.token_id}'"
    assert token_info.token_type == "FBC", f"Expected token_type 'FBC', got '{token_info.token_type}'"
    assert file_path == log_path, f"Expected path '{log_path}', got '{file_path}'"
    
    print("✅ Test passed: Log write completion triggers auto-expansion")

def test_highlighting_not_triggered_when_file_not_in_map():
    """Test that highlighting is skipped gracefully when file not in map"""
    from commander.presenters.node_tree_presenter import NodeTreePresenter
    
    # Create mock dependencies
    view = Mock()
    node_manager = Mock()
    session_manager = Mock()
    log_writer = Mock()
    command_queue = Mock()
    fbc_service = Mock()
    rpc_service = Mock()
    context_menu_service = Mock()
    bstool_service = Mock()
    
    # Create presenter
    presenter = NodeTreePresenter(
        view, node_manager, session_manager, log_writer,
        command_queue, fbc_service, rpc_service,
        context_menu_service, bstool_service
    )
    
    # Mock _highlight_current_file
    presenter._highlight_current_file = Mock()
    
    # Trigger log write for file not in map
    log_path = "C:\\Users\\test\\_DIA\\FBC\\AP01\\nonexistent.fbc"
    
    presenter.handle_log_write_completed(
        log_path=log_path,
        success=True,
        total_line_count=50,
        lines_written_by_command=50,
        content_written=""
    )
    
    # Verify _highlight_current_file was NOT called
    assert not presenter._highlight_current_file.called, "_highlight_current_file should not be called for unmapped files"
    
    print("✅ Test passed: Highlighting skipped gracefully for unmapped files")

def test_color_update_still_happens():
    """Test that color update still occurs even with highlighting addition"""
    from commander.presenters.node_tree_presenter import NodeTreePresenter
    from PyQt6.QtWidgets import QTreeWidgetItem
    
    # Create mock dependencies
    view = Mock()
    node_manager = Mock()
    session_manager = Mock()
    log_writer = Mock()
    command_queue = Mock()
    fbc_service = Mock()
    rpc_service = Mock()
    context_menu_service = Mock()
    bstool_service = Mock()
    
    # Create presenter
    presenter = NodeTreePresenter(
        view, node_manager, session_manager, log_writer,
        command_queue, fbc_service, rpc_service,
        context_menu_service, bstool_service
    )
    
    # Setup test data
    log_path = "C:\\Users\\test\\_DIA\\FBC\\AP01\\AP01_192-168-0-11_162.fbc"
    normalized_path = os.path.normpath(log_path)
    
    # Create mock file item
    file_item = Mock(spec=QTreeWidgetItem)
    item_data = {
        "node": "AP01",
        "token": "162",
        "token_type": "FBC",
        "ip_address": "192.168.0.11",
        "log_path": normalized_path
    }
    file_item.data.return_value = item_data
    presenter.file_item_map[normalized_path] = file_item
    
    # Mock methods
    presenter._highlight_current_file = Mock()
    presenter._check_and_update_node_color = Mock()
    
    # Set command success first
    presenter.node_status[log_path] = {"command_success": True, "log_success": None, "total_line_count": None, "lines_written_by_command": None}
    
    # Trigger log write completion
    presenter.handle_log_write_completed(
        log_path=log_path,
        success=True,
        total_line_count=50,
        lines_written_by_command=50,
        content_written=""
    )
    
    # Verify color update was called
    assert presenter._check_and_update_node_color.called, "_check_and_update_node_color should be called"
    assert presenter._check_and_update_node_color.call_args[0][0] == log_path, "Color update should use correct log_path"
    
    print("✅ Test passed: Color update still happens with highlighting")

if __name__ == "__main__":
    print("Testing auto-expansion fix for Print All Nodes workflow...\n")
    
    test_log_write_triggers_highlighting()
    test_highlighting_not_triggered_when_file_not_in_map()
    test_color_update_still_happens()
    
    print("\n✅ All tests passed!")
