"""Debug script to check if LOG tokens exist in nodes"""
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Import just the node_manager module directly
import importlib.util
spec = importlib.util.spec_from_file_location("node_manager", "src/commander/node_manager.py")
node_manager_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(node_manager_module)
NodeManager = node_manager_module.NodeManager

# Create node manager
manager = NodeManager()

# Load configuration
config_path = "nodes.json"
if os.path.exists(config_path):
    print(f"Loading configuration from {config_path}...")
    manager.load_configuration(config_path)
    print(f"Loaded {len(manager.nodes)} nodes\n")
    
    # Check first few nodes for LOG tokens
    for node_name, node in list(manager.nodes.items())[:3]:
        print(f"\n=== Node: {node_name} ({node.ip_address}) ===")
        print(f"Total token IDs in node.tokens: {len(node.tokens)}")
        
        # Flatten all tokens to see what types exist
        all_tokens = []
        for token_list in node.tokens.values():
            if isinstance(token_list, list):
                all_tokens.extend(token_list)
            else:
                all_tokens.append(token_list)
        
        # Count by type
        from collections import Counter
        token_types = Counter(t.token_type for t in all_tokens)
        print(f"Token types: {dict(token_types)}")
        
        # Show LOG tokens specifically
        log_tokens = [t for t in all_tokens if t.token_type == "LOG"]
        print(f"LOG tokens found: {len(log_tokens)}")
        for token in log_tokens:
            print(f"  - ID: {token.token_id}, Path: {token.log_path}")
        
        # Show FBC tokens for comparison
        fbc_tokens = [t for t in all_tokens if t.token_type == "FBC"]
        print(f"FBC tokens found: {len(fbc_tokens)}")
        for token in fbc_tokens[:2]:  # Just show first 2
            print(f"  - ID: {token.token_id}, Path: {token.log_path}")
        
        # Show RPC tokens for comparison
        rpc_tokens = [t for t in all_tokens if t.token_type == "RPC"]
        print(f"RPC tokens found: {len(rpc_tokens)}")
        for token in rpc_tokens[:2]:  # Just show first 2
            print(f"  - ID: {token.token_id}, Path: {token.log_path}")

else:
    print(f"Configuration file not found: {config_path}")
