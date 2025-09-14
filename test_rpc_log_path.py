import sys
import os
import logging

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from commander.node_manager import NodeManager
from commander.services.rpc_command_service import RpcCommandService
from commander.command_queue import CommandQueue

def test_rpc_log_path():
    """Test that RpcCommandService.get_token correctly populates log_path"""
    # Set up logging
    logging.basicConfig(level=logging.DEBUG)
    
    # Create a NodeManager instance
    node_manager = NodeManager()
    
    # Create a CommandQueue instance
    command_queue = CommandQueue()
    
    # Create an RpcCommandService instance
    rpc_service = RpcCommandService(node_manager, command_queue)
    
    # Use a known node from the configuration
    node_name = "AP01m"  # This should be a node that exists in nodes.json
    token_id = "123"
    
    try:
        # Get a token from the RPC service
        token = rpc_service.get_token(node_name, token_id)
        
        # Print the token details
        print(f"Token ID: {token.token_id}")
        print(f"Token Type: {token.token_type}")
        print(f"Token Name: {token.name}")
        print(f"Token IP Address: {token.ip_address}")
        print(f"Token Log Path: {token.log_path}")
        
        # Check if log_path is populated
        if token.log_path:
            print("SUCCESS: log_path is correctly populated!")
            return True
        else:
            print("FAILURE: log_path is empty!")
            return False
    except Exception as e:
        print(f"ERROR: {str(e)}")
        return False

if __name__ == "__main__":
    test_rpc_log_path()