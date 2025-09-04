import os
import sys
import pytest
from unittest.mock import MagicMock, patch
from PyQt6.QtCore import QPoint

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

# Mock the problematic imports
sys.modules['telnetlib'] = MagicMock()

from commander.services.context_menu_service import ContextMenuService
from commander.models import NodeToken
from commander.services.context_menu_filter import ContextMenuFilterService
from commander.node_manager import NodeManager

def test_fbc_subsection_context_menu_contains_only_print_all_action():
    """Test that FBC subsection context menu only displays 'Print all FBC tokens' and no individual token commands."""
    # Create mock dependencies
    mock_node_manager = MagicMock(spec=NodeManager)
    mock_context_menu_filter = MagicMock(spec=ContextMenuFilterService)
    
    # Create the service
    context_menu_service = ContextMenuService(mock_node_manager, mock_context_menu_filter)
    
    # Create test data for FBC subsection
    fbc_subsection_data = {
        "section_type": "FBC",
        "node": "AP01m"
    }
    
    # Mock QMenu to avoid Qt dependencies
    class MockMenu:
        def __init__(self):
            self._actions = []
            
        def addAction(self, action):
            self._actions.append(action)
            
        def actions(self):
            return self._actions
            
        def exec(self, position):
            pass  # Do nothing, just for testing
    
    # Create a mock menu
    menu = MockMenu()
    
    # Mock the context menu filter to allow FBC subgroup commands
    with patch.object(context_menu_service.context_menu_filter, 'should_show_command', return_value=True):
        # Mock get_node_tokens to return some test tokens
        mock_tokens = [
            NodeToken("162", "FBC", "AP01m", "192.168.0.11"),
            NodeToken("163", "FBC", "AP01m", "192.168.0.11"),
            NodeToken("164", "FBC", "AP01m", "192.168.0.11")
        ]
        
        # Mock the get_node_tokens method
        context_menu_service.get_node_tokens = MagicMock(return_value=mock_tokens)
        
        # Mock presenter
        mock_presenter = MagicMock()
        context_menu_service.set_presenter(mock_presenter)
        
        # Mock QAction to avoid Qt dependencies
        class MockAction:
            def __init__(self, text, parent=None):
                self._text = text
                # Mock the triggered signal
                self.triggered = MagicMock()
                
            def text(self):
                return self._text
        
        # Patch QAction
        with patch('commander.services.context_menu_service.QAction', MockAction):
            # Call show_context_menu with FBC subsection data
            position = QPoint(100, 100)
            result = context_menu_service.show_context_menu(menu, fbc_subsection_data, position)
            
            # Verify that the menu was shown
            assert result == True, "Context menu should be shown for FBC subsection"
            
            # Get all actions from the menu
            actions = menu.actions()
            
            # Verify that there is exactly one action
            assert len(actions) == 1, f"Expected exactly 1 action, but got {len(actions)}"
            
            # Verify that the action is 'Print All FBC Tokens for AP01m'
            action_text = actions[0].text()
            expected_text = "Print All FBC Tokens for AP01m"
            assert action_text == expected_text, f"Expected action text '{expected_text}', but got '{action_text}'"
            
            # Verify that no individual token actions are present
            individual_token_actions = [action for action in actions if "Token" in action.text() and "Print All" not in action.text()]
            assert len(individual_token_actions) == 0, f"Found {len(individual_token_actions)} individual token actions, expected 0"