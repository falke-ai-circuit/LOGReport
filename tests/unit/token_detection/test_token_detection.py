#!/usr/bin/env python3
"""
Test script to verify token detection for AP01m node using the actual NodeManager
"""
import sys
import os

# Add src to path so we can import commander modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_token_detection():
    """Test token detection for AP01m node"""
    print("Testing token detection for AP01m...")
    
    try:
        # Import the actual NodeManager
        from commander.node_manager import NodeManager
        
        # Create a node manager
        nm = NodeManager()
        
        # Load the existing configuration
        success = nm.load_configuration()
        if not success:
            print("Failed to load configuration")
            return False
        
        # Scan log files
        nm.scan_log_files()
        
        # Get AP01m node
        node = nm.get_node("AP01m")
        if not node:
            print("AP01m node not found")
            return False
        
        print(f"Node: {node.name}")
        print(f"IP Address: {node.ip_address}")
        
        # Count total tokens
        total_tokens = 0
        for token_list in node.tokens.values():
            total_tokens += len(token_list)
        print(f"Number of token IDs: {len(node.tokens)}")
        print(f"Total number of tokens: {total_tokens}")
        
        # Print all tokens
        for token_id, token_list in node.tokens.items():
            for token in token_list:
                print(f"  Token ID: {token_id}, Type: {token.token_type}, Path: {token.log_path}")
        
        # Check specifically for tokens 162, 163, 164
        expected_tokens = {"162", "163", "164"}
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
            print(f"  Token ID: {token.token_id}, Type: {token.token_type}, Path: {token.log_path}")
        
        print(f"\nRPC tokens: {len(rpc_tokens)}")
        for token in rpc_tokens:
            print(f"  Token ID: {token.token_id}, Type: {token.token_type}, Path: {token.log_path}")
        
        # Check if we have both FBC and RPC tokens for each expected ID
        fbc_ids = {t.token_id for t in fbc_tokens}
        rpc_ids = {t.token_id for t in rpc_tokens}
        
        print(f"\nFBC token IDs: {fbc_ids}")
        print(f"RPC token IDs: {rpc_ids}")
        
        all_good = True
        for token_id in expected_tokens:
            has_fbc = token_id in fbc_ids
            has_rpc = token_id in rpc_ids
            print(f"Token {token_id}: FBC={has_fbc}, RPC={has_rpc}")
            if not (has_fbc and has_rpc):
                all_good = False
        
        if all_good:
            print("\nSUCCESS: Both FBC and RPC tokens are detected for all expected token IDs!")
        else:
            print("\nFAILURE: Not all token IDs have both FBC and RPC tokens.")
        
        return all_good
        
    except Exception as e:
        print(f"Error during test: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_token_detection()
    sys.exit(0 if success else 1)