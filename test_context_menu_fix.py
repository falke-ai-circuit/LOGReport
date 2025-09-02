#!/usr/bin/env python3
"""
Test script to verify the context menu fix
"""
import sys
import os
import logging

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Import the modules
try:
    from commander.models import Node, NodeToken
    from commander.node_manager import NodeManager
    from commander.services.context_menu_service import ContextMenuService
    from commander.services.context_menu_filter import ContextMenuFilterService
    print("✓ All modules imported successfully")
except ImportError as e:
    print(f"✗ Import error: {e}")
    sys.exit(1)

def test_get_node_tokens():
    """Test the get_node_tokens method fix"""
    print("Testing get_node_tokens method fix...")
    
    # Set up logging
    logging.basicConfig(level=logging.DEBUG)
    
    # Create a node manager
    node_manager = NodeManager()
    
    # Create a test node
    node = Node(name="AP01m", ip_address="192.168.0.11")
    
    # Add some tokens to the node
    token1 = NodeToken(
        token_id="162",
        token_type="FBC",
        name="AP01m",
        ip_address="192.168.0.11"
    )
    
    token2 = NodeToken(
        token_id="163",
        token_type="FBC",
        name="AP01m",
        ip_address="192.168.0.11"
    )
    
    token3 = NodeToken(
        token_id="test",
        token_type="RPC",
        name="AP01m",
        ip_address="192.168.0.11"
    )
    
    # Add tokens to node
    node.add_token(token1)
    node.add_token(token2)
    node.add_token(token3)
    
    # Add node to node manager
    node_manager.nodes[node.name] = node
    
    # Create context menu service
    context_menu_filter = ContextMenuFilterService()
    context_menu_service = ContextMenuService(node_manager, context_menu_filter)
    
    # Test getting FBC tokens
    try:
        fbc_tokens = context_menu_service.get_node_tokens("AP01m", "FBC")
        print(f"Found {len(fbc_tokens)} FBC tokens: {[t.token_id for t in fbc_tokens]}")
        assert len(fbc_tokens) == 2, f"Expected 2 FBC tokens, got {len(fbc_tokens)}"
        print("✓ FBC token retrieval test passed")
    except Exception as e:
        print(f"✗ FBC token retrieval test failed: {e}")
        return False
    
    # Test getting RPC tokens
    try:
        rpc_tokens = context_menu_service.get_node_tokens("AP01m", "RPC")
        print(f"Found {len(rpc_tokens)} RPC tokens: {[t.token_id for t in rpc_tokens]}")
        assert len(rpc_tokens) == 1, f"Expected 1 RPC token, got {len(rpc_tokens)}"
        print("✓ RPC token retrieval test passed")
    except Exception as e:
        print(f"✗ RPC token retrieval test failed: {e}")
        return False
    
    print("All tests passed!")
    return True

if __name__ == "__main__":
    success = test_get_node_tokens()
    sys.exit(0 if success else 1)