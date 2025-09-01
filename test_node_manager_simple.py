#!/usr/bin/env python3
"""
Simple test script to verify node_manager functionality
"""
import sys
import os
import json

# Add src to path so we can import commander modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Let's try to directly import the node_manager module
import importlib.util

# Specify the path to the node_manager.py file
node_manager_path = os.path.join(os.path.dirname(__file__), 'src', 'commander', 'node_manager.py')

# Load the module
spec = importlib.util.spec_from_file_location("node_manager", node_manager_path)
node_manager_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(node_manager_module)

# Import the models module the same way
models_path = os.path.join(os.path.dirname(__file__), 'src', 'commander', 'models.py')
spec2 = importlib.util.spec_from_file_location("models", models_path)
models_module = importlib.util.module_from_spec(spec2)
spec2.loader.exec_module(models_module)

def test_node_manager():
    """Test node manager functionality"""
    print("Testing NodeManager functionality...")
    
    # Create a simple NodeManager instance
    NodeManager = node_manager_module.NodeManager
    Node = models_module.Node
    NodeToken = models_module.NodeToken
    
    # Create a node manager
    nm = NodeManager.__new__(NodeManager)  # Create instance without calling __init__
    
    # Initialize the attributes manually
    nm.nodes = {}
    nm.log_root = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
        "test_logs"
    )
    nm.selected_node = None
    nm.config_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "src", "nodes_test.json"
    )
    
    # Load configuration
    success = nm.load_configuration()
    if not success:
        print("Failed to load configuration")
        return False
    
    print(f"Loaded {len(nm.nodes)} nodes")
    
    # Add some test tokens to a node
    node = nm.get_node("AP01m")
    if not node:
        print("AP01m node not found")
        return False
    
    print(f"Node: {node.name}")
    print(f"IP Address: {node.ip_address}")
    
    # Add some test tokens
    fbc_token = NodeToken("162", "FBC", "AP01m FBC", "192.168.0.11", 23)
    rpc_token = NodeToken("162", "RPC", "AP01m RPC", "192.168.0.11", 23)
    
    node.add_token(fbc_token)
    node.add_token(rpc_token)
    
    # Check if both tokens are there
    token_lists = list(node.tokens.values())
    total_tokens = sum(len(token_list) for token_list in token_lists)
    print(f"Number of token IDs: {len(node.tokens)}")
    print(f"Total number of tokens: {total_tokens}")
    
    # Print all tokens
    for token_id, token_list in node.tokens.items():
        for token in token_list:
            print(f"  Token ID: {token_id}, Type: {token.token_type}")
    
    # Check specifically for our test tokens
    fbc_tokens = []
    rpc_tokens = []
    
    for token_list in node.tokens.values():
        for token in token_list:
            if token.token_type == "FBC":
                fbc_tokens.append(token)
            elif token.token_type == "RPC":
                rpc_tokens.append(token)
    
    print(f"\nFBC tokens: {len(fbc_tokens)}")
    for token in fbc_tokens:
        print(f"  Token ID: {token.token_id}, Type: {token.token_type}")
    
    print(f"\nRPC tokens: {len(rpc_tokens)}")
    for token in rpc_tokens:
        print(f"  Token ID: {token.token_id}, Type: {token.token_type}")
    
    # Check if we have both FBC and RPC tokens for token ID 162
    has_fbc = any(t.token_id == "162" and t.token_type == "FBC" for t in fbc_tokens)
    has_rpc = any(t.token_id == "162" and t.token_type == "RPC" for t in rpc_tokens)
    
    print(f"\nToken 162: FBC={has_fbc}, RPC={has_rpc}")
    
    if has_fbc and has_rpc:
        print("\nSUCCESS: Both FBC and RPC tokens are detected for token ID 162!")
        return True
    else:
        print("\nFAILURE: Not both FBC and RPC tokens are detected for token ID 162.")
        return False

if __name__ == "__main__":
    success = test_node_manager()
    sys.exit(0 if success else 1)