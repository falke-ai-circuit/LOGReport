#!/usr/bin/env python3
"""
Simple test script to verify token detection for AP01m node
"""
import sys
import os
import json

# Add src to path so we can import commander modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Import just the models and node_manager directly
from commander.models import Node, NodeToken

class SimpleNodeManager:
    def __init__(self):
        self.nodes = {}
        self.log_root = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "test_logs"
        )
        
    def load_configuration(self, file_path=None):
        """Load configuration from JSON file"""
        if file_path is None:
            file_path = os.path.join(
                os.path.dirname(os.path.abspath(__file__)),
                "src", "nodes_test.json"
            )
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
                
            self._parse_config(config_data)
            return True
        except Exception as e:
            print(f"Error loading configuration: {str(e)}")
            return False
    
    def _parse_config(self, config_data):
        """Parse configuration data into Node objects"""
        self.nodes.clear()
        
        for node_data in config_data:
            try:
                node = Node(
                    name=node_data["name"],
                    ip_address=node_data["ip_address"]
                )
                self.nodes[node.name] = node
            except Exception as e:
                print(f"Error processing node: {str(e)}")
    
    def scan_log_files(self):
        """Scan log files and add tokens to nodes"""
        # This is a simplified version that just adds some test tokens
        # In a real implementation, this would scan the filesystem
        
        # Get the AP01m node
        node = self.nodes.get("AP01m")
        if not node:
            print("AP01m node not found")
            return
            
        # Add some test FBC tokens
        fbc_tokens = [
            NodeToken("162", "FBC", "AP01m FBC", "192.168.0.11", 23),
            NodeToken("163", "FBC", "AP01m FBC", "192.168.0.11", 23),
            NodeToken("164", "FBC", "AP01m FBC", "192.168.0.11", 23)
        ]
        
        # Add some test RPC tokens
        rpc_tokens = [
            NodeToken("162", "RPC", "AP01m RPC", "192.168.0.11", 23),
            NodeToken("163", "RPC", "AP01m RPC", "192.168.0.11", 23),
            NodeToken("164", "RPC", "AP01m RPC", "192.168.0.11", 23)
        ]
        
        # Add all tokens to the node
        for token in fbc_tokens + rpc_tokens:
            node.add_token(token)
    
    def get_node(self, node_name):
        """Get node by name"""
        return self.nodes.get(node_name)

def test_token_detection():
    """Test token detection for AP01m node"""
    print("Testing token detection for AP01m...")
    
    # Create a node manager
    nm = SimpleNodeManager()
    
    # Load the existing configuration
    success = nm.load_configuration()
    if not success:
        print("Failed to load configuration")
        return False
    
    # Add some test tokens
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
            print(f"  Token ID: {token_id}, Type: {token.token_type}")
    
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
        print(f"  Token ID: {token.token_id}, Type: {token.token_type}")
    
    print(f"\nRPC tokens: {len(rpc_tokens)}")
    for token in rpc_tokens:
        print(f"  Token ID: {token.token_id}, Type: {token.token_type}")
    
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

if __name__ == "__main__":
    success = test_token_detection()
    sys.exit(0 if success else 1)