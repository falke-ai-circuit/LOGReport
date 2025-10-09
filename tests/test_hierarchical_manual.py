"""
Manual integration test for node-level hierarchical command execution.
Run this script to manually verify the feature works correctly.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from unittest.mock import MagicMock
from PyQt6.QtWidgets import QApplication, QMenu
from PyQt6.QtCore import Qt

from commander.services.context_menu_service import ContextMenuService
from commander.services.context_menu_filter import ContextMenuFilterService
from commander.node_manager import NodeManager
from commander.models import Node, NodeToken


def test_node_context_menu():
    """Test that node context menu shows hierarchical option."""
    print("\n" + "="*80)
    print("TEST 1: Node Context Menu Shows Hierarchical Option")
    print("="*80)
    
    # Create QApplication
    app = QApplication.instance() or QApplication([])
    
    # Setup mocks
    node_manager = MagicMock(spec=NodeManager)
    test_node = Node(name="AP01m", ip_address="192.168.0.11", status="online")
    test_node.tokens = {
        "FBC": [NodeToken(token_id="162", token_type="FBC", name="AP01m", ip_address="192.168.0.11")],
        "RPC": [NodeToken(token_id="162", token_type="RPC", name="AP01m", ip_address="192.168.0.11")]
    }
    node_manager.get_node.return_value = test_node
    
    # Create filter service
    context_menu_filter = ContextMenuFilterService()
    
    # Create context menu service
    context_menu_service = ContextMenuService(
        node_manager=node_manager,
        context_menu_filter=context_menu_filter
    )
    
    # Create mock presenter
    mock_presenter = MagicMock()
    context_menu_service.set_presenter(mock_presenter)
    
    # Test node data (this is what would come from QTreeWidgetItem)
    node_data = {
        "type": "node",
        "node_name": "AP01m"
    }
    
    # Create menu
    menu = QMenu()
    
    # Try to show context menu
    print(f"\n✓ Testing node data: {node_data}")
    result = context_menu_service.show_context_menu(
        menu=menu,
        item_data=node_data,
        position=None
    )
    
    # Check results
    print(f"✓ Context menu shown: {result}")
    print(f"✓ Number of actions: {len(menu.actions())}")
    
    if len(menu.actions()) > 0:
        print(f"\n✓ Menu actions found:")
        for i, action in enumerate(menu.actions()):
            print(f"  {i+1}. {action.text()}")
        
        # Check for hierarchical option
        action_texts = [action.text() for action in menu.actions()]
        has_hierarchical = any("Execute All Commands Hierarchically" in text for text in action_texts)
        
        if has_hierarchical:
            print(f"\n✅ SUCCESS: Hierarchical command option IS present!")
            return True
        else:
            print(f"\n❌ FAILURE: Hierarchical command option NOT found!")
            print(f"   Expected: 'Execute All Commands Hierarchically for AP01m'")
            return False
    else:
        print(f"\n❌ FAILURE: No menu actions were added!")
        return False


def test_subgroup_context_menu():
    """Test that subgroup context menu still works."""
    print("\n" + "="*80)
    print("TEST 2: Subgroup Context Menu (Regression Test)")
    print("="*80)
    
    # Create QApplication
    app = QApplication.instance() or QApplication([])
    
    # Setup mocks
    node_manager = MagicMock(spec=NodeManager)
    test_node = Node(name="AP01m", ip_address="192.168.0.11", status="online")
    test_node.tokens = {
        "FBC": [
            NodeToken(token_id="162", token_type="FBC", name="AP01m", ip_address="192.168.0.11"),
            NodeToken(token_id="163", token_type="FBC", name="AP01m", ip_address="192.168.0.11")
        ]
    }
    node_manager.get_node.return_value = test_node
    
    # Create filter service
    context_menu_filter = ContextMenuFilterService()
    
    # Create context menu service
    context_menu_service = ContextMenuService(
        node_manager=node_manager,
        context_menu_filter=context_menu_filter
    )
    
    # Create mock presenter
    mock_presenter = MagicMock()
    context_menu_service.set_presenter(mock_presenter)
    
    # Test subgroup data (FBC section)
    subgroup_data = {
        "section_type": "FBC",
        "node": "AP01m",
        "type": "section"
    }
    
    # Create menu
    menu = QMenu()
    
    # Try to show context menu
    print(f"\n✓ Testing subgroup data: {subgroup_data}")
    result = context_menu_service.show_context_menu(
        menu=menu,
        item_data=subgroup_data,
        position=None
    )
    
    # Check results
    print(f"✓ Context menu shown: {result}")
    print(f"✓ Number of actions: {len(menu.actions())}")
    
    if len(menu.actions()) > 0:
        print(f"\n✓ Menu actions found:")
        for i, action in enumerate(menu.actions()):
            print(f"  {i+1}. {action.text()}")
        print(f"\n✅ SUCCESS: Subgroup menu still works!")
        return True
    else:
        print(f"\n❌ FAILURE: Subgroup menu not showing!")
        return False


if __name__ == "__main__":
    print("\n" + "="*80)
    print("MANUAL INTEGRATION TEST: Node Hierarchical Commands")
    print("="*80)
    
    # Run tests
    test1_passed = test_node_context_menu()
    test2_passed = test_subgroup_context_menu()
    
    # Summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    print(f"✓ Test 1 (Node Context Menu):     {'✅ PASSED' if test1_passed else '❌ FAILED'}")
    print(f"✓ Test 2 (Subgroup Menu):         {'✅ PASSED' if test2_passed else '❌ FAILED'}")
    print("="*80)
    
    if test1_passed and test2_passed:
        print("\n🎉 ALL TESTS PASSED! Feature is working correctly.")
        sys.exit(0)
    else:
        print("\n⚠️  SOME TESTS FAILED! Please review the output above.")
        sys.exit(1)
