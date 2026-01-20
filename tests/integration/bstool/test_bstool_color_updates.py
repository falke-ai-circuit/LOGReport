"""
Test BsTool LOG file color updates with node suffix handling
"""
import pytest
import os
from unittest.mock import Mock, MagicMock, patch
from PyQt6.QtWidgets import QTreeWidgetItem
from PyQt6.QtCore import Qt


def test_bstool_completed_updates_colors():
    """
    Test that _handle_bstool_completed sets command_success in node_status.
    Color updates happen through handle_log_write_completed (same flow as FBC/RPC).
    
    This test verifies:
    1. command_success is set in node_status
    2. _check_and_update_node_color is called
    3. Color updates use the same logic as FBC/RPC files
    """
    # Create mock presenter with necessary attributes
    from src.commander.presenters.node_tree_presenter import NodeTreePresenter
    
    # Mock dependencies
    mock_view = Mock()
    mock_node_manager = Mock()
    mock_session_manager = Mock()
    mock_log_writer = Mock()
    mock_command_queue = Mock()
    mock_fbc_service = Mock()
    mock_rpc_service = Mock()
    mock_context_menu_service = Mock()
    mock_bstool_service = Mock()
    
    # Create presenter
    presenter = NodeTreePresenter(
        view=mock_view,
        node_manager=mock_node_manager,
        session_manager=mock_session_manager,
        log_writer=mock_log_writer,
        command_queue=mock_command_queue,
        fbc_service=mock_fbc_service,
        rpc_service=mock_rpc_service,
        context_menu_service=mock_context_menu_service,
        bstool_service=mock_bstool_service
    )
    
    # Mock file item
    file_item = QTreeWidgetItem(["AP01m_192-168-0-11.log"])
    file_item.setData(0, Qt.ItemDataRole.UserRole, {
        "log_path": "D:/LOGReport/_DIA/LOG/AP01m_192-168-0-11.log",
        "token": "AP01m_192-168-0-11",
        "token_type": "LOG",
        "node": "AP01m"
    })
    
    # Add to file_item_map
    log_path = "D:/LOGReport/_DIA/LOG/AP01m_192-168-0-11.log"
    normalized_path = os.path.normpath(log_path)
    presenter.file_item_map[normalized_path] = file_item
    
    # Mock _check_and_update_node_color
    presenter._check_and_update_node_color = Mock()
    
    # Test Case 1: Successful execution
    presenter._handle_bstool_completed(log_path, success=True, return_code=0)
    
    # Verify command_success was set in node_status
    assert log_path in presenter.node_status
    assert presenter.node_status[log_path]["command_success"] is True
    
    # Verify _check_and_update_node_color was called
    presenter._check_and_update_node_color.assert_called_once_with(log_path)
    
    # Reset
    presenter._check_and_update_node_color.reset_mock()
    
    # Test Case 2: Failed execution
    presenter._handle_bstool_completed(log_path, success=False, return_code=1)
    
    # Verify command_success was set to False
    assert presenter.node_status[log_path]["command_success"] is False
    
    # Verify _check_and_update_node_color was called again
    presenter._check_and_update_node_color.assert_called_once_with(log_path)


def test_bstool_color_update_with_node_suffix():
    """
    Test that command_success is set correctly for nodes with 'm' or 'r' suffix.
    
    Scenario:
    - Node name: AP01m
    - LOG file: AP01m_192-168-0-11.log
    - BsTool command: -errlog AP01 (suffix stripped)
    - Color update: Sets command_success in node_status (colors updated by handle_log_write_completed)
    """
    from src.commander.presenters.node_tree_presenter import NodeTreePresenter
    
    # Mock dependencies
    mock_view = Mock()
    mock_node_manager = Mock()
    mock_session_manager = Mock()
    mock_log_writer = Mock()
    mock_command_queue = Mock()
    mock_fbc_service = Mock()
    mock_rpc_service = Mock()
    mock_context_menu_service = Mock()
    mock_bstool_service = Mock()
    
    # Create presenter
    presenter = NodeTreePresenter(
        view=mock_view,
        node_manager=mock_node_manager,
        session_manager=mock_session_manager,
        log_writer=mock_log_writer,
        command_queue=mock_command_queue,
        fbc_service=mock_fbc_service,
        rpc_service=mock_rpc_service,
        context_menu_service=mock_context_menu_service,
        bstool_service=mock_bstool_service
    )
    
    # Test with various node suffix scenarios
    test_cases = [
        ("AP01m_192-168-0-11.log", "D:/LOGReport/_DIA/LOG/AP01m_192-168-0-11.log"),
        ("AP02r_192-168-0-12.log", "D:/LOGReport/_DIA/LOG/AP02r_192-168-0-12.log"),
        ("BP01_192-168-0-13.log", "D:/LOGReport/_DIA/LOG/BP01_192-168-0-13.log"),  # No suffix
    ]
    
    for filename, log_path in test_cases:
        # Create file item
        file_item = QTreeWidgetItem([filename])
        file_item.setData(0, Qt.ItemDataRole.UserRole, {
            "log_path": log_path,
            "token": filename.replace('.log', ''),
            "token_type": "LOG",
            "node": filename.split('_')[0]
        })
        
        # Add to file_item_map with normalized path
        normalized_path = os.path.normpath(log_path)
        presenter.file_item_map[normalized_path] = file_item
        
        # Mock _check_and_update_node_color
        presenter._check_and_update_node_color = Mock()
        
        # Handle BsTool completion
        presenter._handle_bstool_completed(log_path, success=True, return_code=0)
        
        # Verify command_success was set (should work regardless of suffix)
        assert log_path in presenter.node_status, f"node_status not created for {filename}"
        assert presenter.node_status[log_path]["command_success"] is True, f"command_success not set for {filename}"
        
        # Verify _check_and_update_node_color was called
        assert presenter._check_and_update_node_color.called, f"Color check not triggered for {filename}"
        
        # Reset for next iteration
        presenter.node_status.clear()
        presenter.file_item_map.clear()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

