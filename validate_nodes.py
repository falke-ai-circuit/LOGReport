import json
import sys
import os

# Add the src directory to the path so we can import the NodeManager
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from commander.node_manager import NodeManager

def validate_nodes_config(nodes_data):
    """Validate the nodes.json structure using NodeManager's _validate_config_structure method"""
    try:
        # Create a NodeManager instance
        nm = NodeManager()
        
        # Use the _validate_config_structure method to validate the data
        is_valid = nm._validate_config_structure(nodes_data)
        
        return is_valid
    except Exception as e:
        print(f"Error during validation: {str(e)}")
        return False

if __name__ == "__main__":
    # The nodes.json content provided in the task
    nodes_data = [
        {
            "name": "AP01m",
            "ip_address": "192.168.1.101",
            "tokens": [
                {
                    "token_id": "162",
                    "token_type": "FBC",
                    "port": 2077,
                    "protocol": "telnet"
                },
                {
                    "token_id": "163",
                    "token_type": "FBC",
                    "port": 5901,
                    "protocol": "telnet"
                },
                {
                    "token_id": "164",
                    "token_type": "FBC",
                    "port": 2077,
                    "protocol": "telnet"
                },
            ]
        },
        {
            "name": "AP01r",
            "ip_address": "192.168.1.102",
            "tokens": [
                {
                    "token_id": "362",
                    "token_type": "FBC",
                    "port": 2077,
                    "protocol": "telnet"
                },
                {
                    "token_id": "363",
                    "token_type": "RPC",
                    "port": 2077,
                    "protocol": "telnet"
                }
            ]
        },
        {
            "name": "AP01r",
            "ip_address": "192.168.1.102",
            "tokens": [
                {
                    "token_id": "360",
                    "token_type": "FTP",
                    "port": 2121,
                    "protocol": "ftp"
                },
                {
                    "token_id": "361",
                    "token_type": "LOG",
                    "port": 2077,
                    "protocol": "telnet"
                }
            ]
        },
        {
            "name": "AL03",
            "ip_address": "192.168.1.103",
            "tokens": [
                {
                    "token_id": "451",
                    "token_type": "LIS",
                    "port": 2121,
                    "protocol": "ftp"
                }
            ]
        }
    ]
    
    # Validate the structure
    is_valid = validate_nodes_config(nodes_data)
    
    print(f"Is nodes.json structure valid? {is_valid}")
    print(json.dumps(nodes_data, indent=2))