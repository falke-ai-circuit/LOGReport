#!/usr/bin/env python3
"""
Test script to verify multiple tokens per node functionality
"""
import sys
import os

# Add src to path so we can import commander modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from commander.node_manager import NodeManager

def test_multiple_tokens():
    """Test that NodeManager can handle multiple tokens with the same ID"""
    print("Testing multiple tokens functionality...")
    
    # Create a node manager
    nm = NodeManager()
    
    # Load the existing configuration
    success = nm.load_configuration("src/nodes.json")
    if not success:
        print("Failed to load configuration")
        return False
    
    # Check if we have nodes
    nodes = nm.get_all_nodes()
    print(f"Loaded {len(nodes)} nodes")
    
    # Check if any node has multiple tokens with the same ID
    for node in nodes:
        print(f"Node: {node.name}")
        for token_id, token_list in node.tokens.items():
            print(f"  Token ID: {token_id}, Count: {len(token_list)}")
            for i, token in enumerate(token_list):
                print(f"    Token {i}: {token.token_type} - {token.log_path}")
    
    # Test adding a new token with an existing ID
    if nodes:
        test_node = nodes[0]
        print(f"\nTesting adding duplicate token to node: {test_node.name}")
        
        # Get an existing token ID
        if test_node.tokens:
            existing_token_id = list(test_node.tokens.keys())[0]
            existing_token = test_node.tokens[existing_token_id][0]
            print(f"Adding duplicate of token ID: {existing_token_id}")
            
            # Create a new token with the same ID but different type
            from commander.models import NodeToken
            new_token = NodeToken(
                token_id=existing_token_id,
                token_type="TEST",
                name=f"{test_node.name} TEST",
                ip_address=test_node.ip_address,
                port=2077
            )
            
            # Add the new token
            test_node.add_token(new_token)
            
            # Verify we now have more tokens with the same ID
            token_count = len(test_node.tokens[existing_token_id])
            print(f"Tokens with ID {existing_token_id}: {token_count}")
            
            if token_count > 1:
                print("SUCCESS: Multiple tokens with same ID are supported")
                return True
            else:
                print("FAILURE: Multiple tokens with same ID are not supported")
                return False
        else:
            print("No existing tokens found to test with")
            return False
    else:
        print("No nodes loaded")
        return False

if __name__ == "__main__":
    success = test_multiple_tokens()
    if success:
        print("\nAll tests passed!")
        sys.exit(0)
    else:
        print("\nSome tests failed!")
        sys.exit(1)