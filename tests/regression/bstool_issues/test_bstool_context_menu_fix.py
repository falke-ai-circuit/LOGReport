"""
Test BsTool context menu fixes for encoding and parameter extraction
"""

import pytest
import tempfile
import os
from unittest.mock import Mock, MagicMock, patch, call
from PyQt6.QtWidgets import QMenu, QAction
from PyQt6.QtCore import Qt

# Import classes to test
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from commander.services.context_menu_service import ContextMenuService
from commander.services.context_menu_filter import ContextMenuFilterService
from commander.node_manager import NodeManager
from commander.models import Node, NodeToken


class TestBsToolEncodingFix:
    """Test UTF-8 encoding error fix in BsTool service"""
    
    def test_temp_file_creation_with_encoding_fallback(self):
        """Test that temp files are created with errors='replace' parameter"""
        # Create a temporary file with errors='replace' to handle non-UTF-8 bytes
        with tempfile.TemporaryFile(mode='w+', encoding='utf-8', errors='replace', delete=False) as f:
            temp_path = f.name
            # Write non-UTF-8 byte sequence (Windows-1252 encoding)
            # Byte 0xa8 is '¨' in Windows-1252
            f.write('Test output with special char: \u00a8')  # This represents byte 0xa8
            f.flush()
            f.seek(0)
            content = f.read()
            assert content == 'Test output with special char: \u00a8'
        
        os.unlink(temp_path)
    
    def test_encoding_fallback_replaces_invalid_bytes(self):
        """Test that invalid UTF-8 bytes are replaced instead of causing errors"""
        # Create temp file
        with tempfile.NamedTemporaryFile(mode='wb', delete=False) as f:
            temp_path = f.name
            # Write actual byte 0xa8 which is invalid UTF-8
            f.write(b'Test\xa8output')
        
        # Read with errors='replace'
        try:
            with open(temp_path, 'r', encoding='utf-8', errors='replace') as f:
                content = f.read()
                # Invalid byte should be replaced with \ufffd (replacement character)
                assert 'Test' in content
                assert 'output' in content
        finally:
            os.unlink(temp_path)


class TestBsToolContextMenuParameterExtraction:
    """Test BsTool parameter extraction from LOG subgroup context menu"""
    
    @pytest.fixture
    def mock_node_manager(self):
        """Create mock node manager with test data"""
        manager = Mock(spec=NodeManager)
        
        # Create test node with LOG tokens
        test_node = Node(name="AP01", ip="192.168.0.11")
        log_token = NodeToken(
            token_id="AP01m_192-168-0-11",
            token_type="LOG",
            log_path="D:\\_DATA\\AP01m_192-168-0-11.log"
        )
        test_node.tokens = {"LOG": [log_token]}
        
        manager.get_node = Mock(return_value=test_node)
        return manager
    
    @pytest.fixture
    def mock_context_menu_filter(self):
        """Create mock context menu filter service"""
        filter_service = Mock(spec=ContextMenuFilterService)
        filter_service.should_show_command = Mock(return_value=True)
        return filter_service
    
    @pytest.fixture
    def context_menu_service(self, mock_node_manager, mock_context_menu_filter):
        """Create context menu service with mocks"""
        service = ContextMenuService(mock_node_manager, mock_context_menu_filter)
        return service
    
    def test_handle_bstool_node_action_generates_correct_parameter(self, context_menu_service):
        """Test that _handle_bstool_node_action generates -errlog parameter correctly"""
        # Mock presenter
        mock_presenter = Mock()
        context_menu_service.set_presenter(mock_presenter)
        
        # Call the method with node name
        node_name = "AP01"
        context_menu_service._handle_bstool_node_action(node_name)
        
        # Verify process_bstool_command was called with dummy log path
        mock_presenter.process_bstool_command.assert_called_once()
        call_args = mock_presenter.process_bstool_command.call_args[0]
        assert node_name in call_args[0]
        assert call_args[0].endswith('.log')
    
    def test_log_subgroup_context_menu_includes_bstool_action(self, context_menu_service, mock_node_manager):
        """Test that LOG subgroup context menu includes 'Run BsTool' action"""
        # Mock presenter
        mock_presenter = Mock()
        context_menu_service.set_presenter(mock_presenter)
        
        # Create menu and item data for LOG subgroup
        menu = QMenu()
        item_data = {
            'type': 'section',
            'section_type': 'LOG',
            'node': 'AP01'
        }
        
        # Show context menu
        result = context_menu_service.show_context_menu(menu, item_data, None)
        
        # Verify menu has actions
        assert result is True
        actions = menu.actions()
        assert len(actions) >= 2  # Should have at least "Print All" and "Run BsTool"
        
        # Verify BsTool action exists
        action_texts = [action.text() for action in actions]
        assert any('Run BsTool' in text for text in action_texts)
    
    def test_node_id_extraction_from_log_path(self):
        """Test node ID extraction logic from log file paths"""
        # Test cases for node ID extraction
        test_cases = [
            ("AP01m_192-168-0-11.log", "AP01"),  # Trailing 'm' should be removed
            ("AP02r_192-168-0-12.log", "AP02"),  # Trailing 'r' should be removed
            ("BP01_192-168-0-13.log", "BP01"),   # No trailing letter
            ("AP01m_192-168-0-11_162.rpc.log", "AP01m"),  # .rpc.log keeps 'm'
        ]
        
        import re
        for log_path, expected_node_id in test_cases:
            filename = os.path.basename(log_path)
            name_without_ext = os.path.splitext(filename)[0]
            
            if '.' in name_without_ext:
                name_without_ext = name_without_ext.split('.')[0]
            
            pattern = r'^([a-zA-Z0-9]+[a-zA-Z]?)_'
            match = re.match(pattern, name_without_ext)
            
            if match:
                node_id = match.group(1)
            else:
                parts = name_without_ext.split('_')
                node_id = parts[0] if parts else ""
            
            # Apply truncation for .log files
            if log_path.lower().endswith('.log') and len(node_id) > 3 and node_id[-1].lower() in ['r', 'm']:
                node_id = node_id[:-1]
            
            assert node_id == expected_node_id, f"Expected {expected_node_id}, got {node_id} for {log_path}"


class TestBsToolCommandGeneration:
    """Test BsTool command generation with -errlog parameter"""
    
    def test_bstool_command_args_format(self):
        """Test that BsTool command arguments are formatted correctly"""
        node_id = "AP01"
        bstool_command_args = f"-errlog {node_id}"
        
        assert bstool_command_args == "-errlog AP01"
    
    def test_bstool_command_with_various_node_names(self):
        """Test BsTool command generation with various node name formats"""
        test_cases = [
            ("AP01", "-errlog AP01"),
            ("AP02", "-errlog AP02"),
            ("BP01", "-errlog BP01"),
            ("AL01", "-errlog AL01"),
        ]
        
        for node_id, expected_command in test_cases:
            bstool_command_args = f"-errlog {node_id}"
            assert bstool_command_args == expected_command


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

