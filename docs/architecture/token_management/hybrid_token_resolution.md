# Hybrid Token Resolution Documentation

## Overview

The Hybrid Token Resolution system is a sophisticated approach to handling token identification and command execution in the LOGReport project. This system addresses the challenge of managing tokens that may exist in multiple formats or locations by implementing a multi-step resolution process with intelligent fallback mechanisms.

## Problem Statement

In complex network environments, tokens may be represented in various ways:
- As explicit configurations in `nodes.json`
- As discovered files in log directories
- As dynamically extracted information from filenames
- As fallback representations when primary tokens are unavailable

The hybrid token resolution system ensures that commands can be executed successfully even when the primary token representation is not available.

## Resolution Process

The hybrid token resolution follows a specific sequence:

### 1. Primary Token Lookup
First, the system attempts to find an exact match for the requested token:
- Search for a token with the exact ID and type in the node configuration
- Validate that the token has all required properties (IP address, port, etc.)

### 2. File-Based Discovery
If no exact match is found, the system scans log files:
- Recursively scan the log root directory for relevant files
- Extract token information from filenames using pattern matching
- Create temporary token representations for discovered files

### 3. Dynamic IP Resolution
For tokens with incomplete IP information:
- Scan directory names and filenames for IP address patterns
- Extract IP addresses in the format `192-168-0-11`
- Update token objects with discovered IP addresses
- Convert IP format from hyphens to dots (192.168.0.11)

### 4. Fallback Mechanism
When a specific token type is not available:
- Use an existing token of a different type with the same ID
- Create a derived token with appropriate type conversion
- Maintain consistency in token properties (IP, port, etc.)

## Implementation Details

### RpcCommandService Fallback Logic

The RPC command service implements the primary fallback mechanism:

```python
def get_token(self, node_name: str, token_id: str) -> NodeToken:
    """Get token with fallback to FBC token if RPC token not found"""
    node = self.node_manager.get_node(node_name)
    if not node:
        raise ValueError(f"Node {node_name} not found")
    
    # First try to find exact RPC token match
    token_list = node.tokens.get(token_id)
    if token_list:
        for token in token_list:
            if token.token_type == "RPC":
                return token
    
    # Fallback to FBC token if available
    if token_list:
        for token in token_list:
            if token.token_type == "FBC":
                # Create derived RPC token from FBC token
                return NodeToken(
                    token_id=token.token_id,
                    token_type="RPC",
                    name=token.name,
                    ip_address=token.ip_address,
                    port=token.port,
                    protocol=token.protocol
                )
    
    raise ValueError(f"Token {token_id} not found for node {node_name}")
```

### NodeManager Token Management

The NodeManager handles token storage and retrieval:

```python
class Node:
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
```

### Dynamic IP Resolution

The system dynamically extracts IP addresses from filenames:

```python
def _scan_for_dynamic_ips(self, log_root: str):
    """Scans log directory for IPs using regex pattern"""
    ip_pattern = r"(\d{1,3}-\d{1,3}-\d{1,3}-\d{1,3})"
    
    for dirpath, _, filenames in os.walk(log_root):
        # Process directory names for IP patterns
        dir_name = os.path.basename(dirpath)
        ip_matches = re.findall(ip_pattern, dir_name)
        if ip_matches:
            for ip_match in ip_matches:
                formatted_ip = ip_match.replace('-', '.')
                self._update_tokens_with_ip(formatted_ip)
        
        # Process filenames for IP patterns
        for filename in filenames:
            ip_matches = re.findall(ip_pattern, filename)
            if ip_matches:
                for ip_match in ip_matches:
                    formatted_ip = ip_match.replace('-', '.')
                    self._update_tokens_with_ip(formatted_ip)
```

## Token Storage Strategy

Tokens are stored in nodes as a dictionary mapping token IDs to lists of tokens:

```python
class Node:
    tokens: Dict[str, List[NodeToken]] = field(default_factory=dict)
```

This structure allows:
- Multiple tokens with the same ID but different types
- Efficient lookup by token ID
- Proper handling of token type specificity

## Use Cases

### 1. Missing RPC Token
When an RPC command is requested but no RPC token exists:
1. System finds FBC token with same ID
2. Creates derived RPC token with FBC properties
3. Executes command successfully

### 2. Incomplete IP Information
When a token has IP address "0.0.0.0":
1. System scans log directories for IP patterns
2. Finds matching IP in filename or directory name
3. Updates token with discovered IP address
4. Proceeds with command execution

### 3. New Log Files
When new log files appear without configuration:
1. System discovers files during directory scan
2. Extracts token information from filenames
3. Creates temporary token representations
4. Allows commands to be executed on new files

## Best Practices

### 1. Consistent Token IDs
Maintain consistent token ID formats across all representations:
- Pad numeric IDs with leading zeros (001, 002, etc.)
- Use consistent case for alphanumeric IDs

### 2. IP Address Formatting
Use hyphens in filenames and convert to dots in memory:
- Filename: `AP01m_192-168-0-11_162.fbc`
- Memory: `192.168.0.11`

### 3. Fallback Validation
When creating derived tokens, validate all properties:
- Ensure IP address is valid
- Verify port number is appropriate
- Confirm protocol compatibility

### 4. Logging and Debugging
Log token resolution steps for troubleshooting:
- Log when fallback mechanisms are used
- Record IP address discovery events
- Track temporary token creation

## Testing

The hybrid token resolution system is tested through:
- `test_same_token_id_different_types_command_execution`: Validates FBC/RPC token differentiation
- `test_fbc_command_execution`: Tests primary token lookup
- `test_rpc_command_execution`: Tests fallback mechanism

## Related Components

### Core Classes
- [NodeManager](src/commander/node_manager.py)
- [RpcCommandService](src/commander/services/rpc_command_service.py)
- [FbcCommandService](src/commander/services/fbc_command_service.py)

### Data Models
- [NodeToken](src/commander/models.py)
- [Node](src/commander/models.py)

### Test Cases
- [test_command_execution.py](tests/commander/test_command_execution.py)

## References

- [NodeManager Implementation](src/commander/node_manager.py)
- [RpcCommandService Implementation](src/commander/services/rpc_command_service.py)
- [FbcCommandService Implementation](src/commander/services/fbc_command_service.py)
- [NodeToken Model](src/commander/models.py)
- [Test Cases](tests/commander/test_command_execution.py)