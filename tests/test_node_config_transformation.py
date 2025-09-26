import json

# Sample data in the old format (similar to what's in nodes.json)
old_format_data = [
    {
        "name": "AP01m",
        "ip": "192.168.0.11",
        "tokens": ["162", "163", "164"],
        "types": ["FBC", "RPC", "LOG"]
    },
    {
        "name": "AL01",
        "ip": "192.168.0.52",
        "tokens": ["186"],
        "types": ["LOG", "LIS"]
    }
]

def transform_to_new_format(nodes_data):
    """Transform nodes data to the new format"""
    transformed_data = []
    for node in nodes_data:
        # Create a new node with ip_address instead of ip
        new_node = {
            "name": node.get("name", ""),
            "ip_address": node.get("ip", ""),
            "tokens": []
        }
        
        # Transform tokens to detailed objects
        tokens = node.get("tokens", [])
        types = node.get("types", [])
        
        # For FBC and RPC types, create entries for each token
        # Based on the nodes_test.json format, it seems like all tokens get entries for selected types
        for token_type in types:
            # Skip LIS for now, handle it separately
            if token_type == "LIS":
                continue
            
            # For each token, create a detailed object
            for token in tokens:
                # Create token object with appropriate port and protocol
                token_obj = {
                    "token_id": token,
                    "token_type": token_type,
                    "port": 23,  # Default port for telnet
                    "protocol": "telnet"  # Default protocol
                }
                new_node["tokens"].append(token_obj)
        
        # Add LIS token if LIS type is selected
        if "LIS" in types:
            lis_token_obj = {
                "token_id": "default_lis_token",  # Default LIS token ID
                "token_type": "LIS",
                "port": 23,
                "protocol": "telnet"
            }
            new_node["tokens"].append(lis_token_obj)
        
        transformed_data.append(new_node)
    
    return transformed_data

def transform_to_old_format(nodes_data):
    """Transform nodes data from new format to old format"""
    old_format_data = []
    for node in nodes_data:
        # Create a new node with ip instead of ip_address
        new_node = {
            "name": node.get("name", ""),
            "ip": node.get("ip_address", ""),
            "tokens": [],
            "types": []
        }
        
        # Extract tokens and types from detailed token objects
        token_ids = []
        types = set()
        for token_obj in node.get("tokens", []):
            token_id = token_obj.get("token_id")
            token_type = token_obj.get("token_type")
            
            # Add token_id to list if not already present
            if token_id and token_id not in token_ids and token_id != "default_lis_token":
                token_ids.append(token_id)
            
            # Add token_type to set
            if token_type:
                types.add(token_type)
        
        new_node["tokens"] = token_ids
        new_node["types"] = list(types)
        
        old_format_data.append(new_node)
    
    return old_format_data

# Test the transformation
print("Original data (old format):")
print(json.dumps(old_format_data, indent=2))

# Transform to new format
new_format_data = transform_to_new_format(old_format_data)
print("\nTransformed data (new format):")
print(json.dumps(new_format_data, indent=2))

# Transform back to old format
restored_data = transform_to_old_format(new_format_data)
print("\nRestored data (old format):")
print(json.dumps(restored_data, indent=2))

# Compare with nodes_test.json format
# Load nodes_test.json to compare
try:
    with open("nodes_test.json", "r") as f:
        nodes_test_data = json.load(f)
    print("\nSample from nodes_test.json:")
    print(json.dumps(nodes_test_data[:2], indent=2))  # Show first 2 nodes
except FileNotFoundError:
    print("\nCould not find nodes_test.json for comparison")