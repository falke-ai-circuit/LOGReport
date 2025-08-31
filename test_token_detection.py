#!/usr/bin/env python3
"""
Test script to verify token detection for all file types
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from commander.node_manager import NodeManager

def test_token_detection():
    """Test that all token types are detected correctly"""
    print("Testing token detection for all file types...")
    
    # Create node manager instance
    nm = NodeManager()
    
    # Check initial nodes
    nodes = nm.get_all_nodes()
    print(f"Initial nodes: {len(nodes)}")
    for node in nodes:
        print(f"  Node: {node.name}, IP: {node.ip_address}, Tokens: {len(node.tokens)}")
    
    # Scan log files
    print("\nScanning log files...")
    nm.scan_log_files()
    
    # Check nodes after scanning
    nodes = nm.get_all_nodes()
    print(f"\nNodes after scanning: {len(nodes)}")
    
    # Check tokens for a specific node
    test_node = nm.get_node("AP01m")
    if test_node:
        print(f"\nNode: {test_node.name}")
        print(f"IP: {test_node.ip_address}")
        print(f"Tokens: {len(test_node.tokens)}")
        
        # Print all tokens for this node
        fbc_count = 0
        rpc_count = 0
        other_count = 0
        
        for token_id, token in test_node.tokens.items():
            print(f"  Token ID: {token_id}, Type: {token.token_type}, Path: {token.log_path}")
            if token.token_type == "FBC":
                fbc_count += 1
            elif token.token_type == "RPC":
                rpc_count += 1
            else:
                other_count += 1
                
        print(f"  FBC tokens: {fbc_count}")
        print(f"  RPC tokens: {rpc_count}")
        print(f"  Other tokens: {other_count}")
    else:
        print("AP01m node not found")
        
    # Check all RPC tokens specifically
    rpc_tokens = []
    for node in nodes:
        for token in node.tokens.values():
            if token.token_type == "RPC":
                rpc_tokens.append(token)
                
    print(f"\nFound {len(rpc_tokens)} RPC tokens in total:")
    for token in rpc_tokens:
        print(f"  Node: {token.name}, Token ID: {token.token_id}, Path: {token.log_path}")
        
    # Check all LIS tokens
    lis_tokens = []
    for node in nodes:
        for token in node.tokens.values():
            if token.token_type == "LIS":
                lis_tokens.append(token)
                
    print(f"\nFound {len(lis_tokens)} LIS tokens in total:")
    for token in lis_tokens:
        print(f"  Node: {token.name}, Token ID: {token.token_id}, Path: {token.log_path}")

if __name__ == "__main__":
    test_token_detection()