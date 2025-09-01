#!/usr/bin/env python3
"""
Standalone test script to verify the Node class can handle multiple tokens with the same ID but different types
"""
from dataclasses import dataclass, field
from typing import Dict, List

@dataclass
class NodeToken:
    token_id: str
    token_type: str  # FBC/RPC/LOG/LIS - matches file extension exactly
    name: str = "default"
    ip_address: str = "0.0.0.0"
    port: int = 23
    log_path: str = ""
    protocol: str = "telnet"
    
    def __init__(self, token_id: str, token_type: str, name: str = "default",
                 ip_address: str = "0.0.0.0", port: int = 23, **kwargs):
        self.token_id = token_id
        self.token_type = token_type
        self.name = name
        self.ip_address = ip_address
        self.port = port
        self.log_path = kwargs.get('log_path', "")
        self.protocol = kwargs.get('protocol', "telnet")


@dataclass
class Node:
    name: str
    ip_address: str
    status: str = "offline"
    tokens: Dict[str, List[NodeToken]] = field(default_factory=dict)

    def add_token(self, token: NodeToken):
        if token.token_id not in self.tokens:
            self.tokens[token.token_id] = []
        # Check if a token of the same type already exists
        for i, existing_token in enumerate(self.tokens[token.token_id]):
            if existing_token.token_type == token.token_type:
                # Replace the existing token of the same type
                self.tokens[token.token_id][i] = token
                return
        # Add the new token
        self.tokens[token.token_id].append(token)

def test_node_token_handling():
    """Test that Node can handle multiple tokens with the same ID but different types"""
    print("Testing Node token handling...")
    
    # Create a node
    node = Node("AP01m", "192.168.0.11")
    
    # Add FBC tokens
    fbc_token_162 = NodeToken("162", "FBC", "AP01m FBC", "192.168.0.11", 23)
    fbc_token_163 = NodeToken("163", "FBC", "AP01m FBC", "192.168.0.11", 23)
    fbc_token_164 = NodeToken("164", "FBC", "AP01m FBC", "192.168.0.11", 23)
    
    node.add_token(fbc_token_162)
    node.add_token(fbc_token_163)
    node.add_token(fbc_token_164)
    
    # Add RPC tokens with the same IDs
    rpc_token_162 = NodeToken("162", "RPC", "AP01m RPC", "192.168.0.11", 23)
    rpc_token_163 = NodeToken("163", "RPC", "AP01m RPC", "192.168.0.11", 23)
    rpc_token_164 = NodeToken("164", "RPC", "AP01m RPC", "192.168.0.11", 23)
    
    node.add_token(rpc_token_162)
    node.add_token(rpc_token_163)
    node.add_token(rpc_token_164)
    
    # Verify the results
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
        return True
    else:
        print("\nFAILURE: Not all token IDs have both FBC and RPC tokens.")
        return False

if __name__ == "__main__":
    import sys
    success = test_node_token_handling()
    sys.exit(0 if success else 1)