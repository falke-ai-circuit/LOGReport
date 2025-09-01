#!/usr/bin/env python3
"""
Debug script to verify token detection for AP01m node
"""
import sys
import os
import json
import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional

# Define models directly to avoid import issues
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

def debug_token_detection():
    """Debug token detection for AP01m node"""
    print("Debugging token detection for AP01m...")
    
    # Create a simple node manager-like structure
    nodes = {}
    
    # Create AP01m node
    ap01m_node = Node("AP01m", "192.168.0.11")
    nodes["AP01m"] = ap01m_node
    
    # Simulate the scanning process by adding tokens directly
    # Add FBC tokens
    fbc_tokens_data = [
        ("162", "D:\\_APP\\LOGReport\\test_logs\\FBC\\AP01m\\AP01m_192-168-0-11_162.fbc"),
        ("163", "D:\\_APP\\LOGReport\\test_logs\\FBC\\AP01m\\AP01m_192-168-0-11_163.fbc"),
        ("164", "D:\\_APP\\LOGReport\\test_logs\\FBC\\AP01m\\AP01m_192-168-0-11_164.fbc")
    ]
    
    for token_id, path in fbc_tokens_data:
        token = NodeToken(token_id, "FBC", f"AP01m FBC", "192.168.0.11", 23)
        token.log_path = path
        ap01m_node.add_token(token)
        print(f"[DEBUG] ADDED FBC token to node: {token_id} | Path: {path}")
    
    # Add RPC tokens
    rpc_tokens_data = [
        ("162", "D:\\_APP\\LOGReport\\test_logs\\RPC\\AP01m\\AP01m_192-168-0-11_162.rpc"),
        ("163", "D:\\_APP\\LOGReport\\test_logs\\RPC\\AP01m\\AP01m_192-168-0-11_163.rpc"),
        ("164", "D:\\_APP\\LOGReport\\test_logs\\RPC\\AP01m\\AP01m_192-168-0-11_164.rpc")
    ]
    
    for token_id, path in rpc_tokens_data:
        token = NodeToken(token_id, "RPC", f"AP01m RPC", "192.168.0.11", 23)
        token.log_path = path
        ap01m_node.add_token(token)
        print(f"[DEBUG] ADDED RPC token to node: {token_id} | Path: {path}")
    
    # Add LOG token
    log_token = NodeToken("192-168-0-11", "LOG", f"AP01m LOG", "192.168.0.11", 23)
    log_token.log_path = "D:\\_APP\\LOGReport\\test_logs\\LOG\\AP01m_192-168-0-11.log"
    ap01m_node.add_token(log_token)
    print(f"[DEBUG] ADDED LOG token to node: 192-168-0-11 | Path: {log_token.log_path}")
    
    # Print results
    node = nodes["AP01m"]
    print(f"Node: {node.name}")
    print(f"IP Address: {node.ip_address}")
    
    # Count total tokens
    total_tokens = 0
    for token_list in node.tokens.values():
        total_tokens += len(token_list)
    print(f"Number of tokens: {total_tokens}")
    
    # Print all tokens
    for token_id, token_list in node.tokens.items():
        for token in token_list:
            print(f"  Token ID: {token.token_id}, Type: {token.token_type}, Path: {token.log_path}")
    
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
    
    return all_good

if __name__ == "__main__":
    debug_token_detection()