# Token Processing Documentation

## Overview

The token processing system in LOGReport handles the identification, management, and execution of commands for various token types (FBC, RPC, LOG, LIS). This document describes the core mechanisms for token storage, resolution, and processing.

## NodeToken Storage Strategy

Tokens are stored in nodes using a dictionary mapping token IDs to lists of tokens:

```python
class Node:
    tokens: Dict[str, List[NodeToken]] = field(default_factory=dict)
```

This structure allows:
- Multiple tokens with the same ID but different types
- Efficient lookup by token ID
- Proper handling of token type specificity

### Storage Implementation

The `Node.add_token()` method manages token storage:

```python
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

### Benefits of This Strategy

1. **Type Differentiation**: Tokens with identical IDs but different types (e.g., FBC and RPC) are stored separately
2. **Efficient Updates**: Existing tokens of the same type are replaced rather than duplicated
3. **Flexible Retrieval**: Easy to retrieve all tokens with a specific ID or filter by type
4. **Memory Efficiency**: No duplicate tokens of the same type and ID

## Token Resolution Process

### 1. Configuration Loading
Tokens are initially loaded from `nodes.json` configuration:
- Each node contains a list of configured tokens
- Tokens are validated for proper structure and data types
- Tokens are added to nodes using the storage strategy

### 2. File Discovery
The NodeManager scans log directories for additional tokens:
- Recursively walks through log directory structure
- Extracts token information from filenames
- Creates temporary token representations for discovered files

### 3. Dynamic IP Resolution
For tokens with incomplete IP information:
- Scans directory names and filenames for IP patterns
- Extracts IP addresses in format `192-168-0-11`
- Updates token objects with discovered IP addresses
- Converts IP format from hyphens to dots (192.168.0.11)

### 4. Hybrid Resolution
When a specific token type is not available:
- Uses existing token of different type with same ID as fallback
- Creates derived token with appropriate type conversion
- Maintains consistency in token properties (IP, port, etc.)

## Token Types

### FBC (FieldBus Communication) Tokens
- Used for fieldbus communication commands
- Command format: `print from fbc io structure {token_id}0000`
- Support both print operations

### RPC (Remote Procedure Call) Tokens
- Used for remote procedure call commands
- Command format: `print from fbc rupi counters {token_id}0000` (print)
- Command format: `clear fbc rupi counters {token_id}0000` (clear)
- Support both print and clear operations

### LOG Tokens
- Represent log files for general logging
- Used for documentation and tracking purposes
- No direct command execution

### LIS Tokens
- Represent list files for system information
- Used for system status and configuration tracking
- No direct command execution

## Token Processing Workflow

### 1. Command Generation
- Services generate properly formatted command strings
- Token information is retrieved using the storage strategy
- Command parameters are validated before queuing

### 2. Queue Management
- Commands are added to the CommandQueue for execution
- Queue items include command string, token object, and optional telnet client
- Queue processing is sequential to maintain order

### 3. Command Execution
- Commands are executed through Telnet sessions
- Results are logged to appropriate log files
- Errors are handled and reported through error handling services

### 4. Result Logging
- Command output is captured and logged
- Log files are managed with rotation (10MB max, 5 backups)
- Timestamps and protocol annotations are added to logs

## Best Practices

### 1. Token ID Consistency
- Maintain consistent token ID formats across all representations
- Pad numeric IDs with leading zeros (001, 002, etc.)
- Use consistent case for alphanumeric IDs

### 2. IP Address Formatting
- Use hyphens in filenames and convert to dots in memory
- Filename: `AP01m_192-168-0-11_162.fbc`
- Memory: `192.168.0.11`

### 3. Type Safety
- Always verify token type before command execution
- Use appropriate service methods for each token type
- Implement fallback mechanisms for hybrid resolution

### 4. Error Handling
- Log token resolution steps for troubleshooting
- Handle missing tokens gracefully with appropriate error messages
- Validate token properties before command generation

## Testing

Token processing is validated through comprehensive test cases:

### test_same_token_id_different_types_command_execution
This test ensures proper handling of tokens with the same ID but different types:
- Verifies both FBC and RPC tokens with ID "162" can coexist
- Confirms correct command generation for each token type
- Validates that tokens are different objects with different types

### test_fbc_command_execution
Tests FBC command generation and queuing:
- Scans log files to discover tokens
- Executes FBC command for specific token
- Verifies correct command format and token properties

### test_rpc_command_execution
Tests RPC command generation and queuing:
- Scans log files to discover tokens
- Executes RPC print and clear commands for specific token
- Verifies correct command formats and token properties

## Related Components

### Core Classes
- [NodeManager](src/commander/node_manager.py)
- [NodeToken](src/commander/models.py)
- [Node](src/commander/models.py)

### Service Classes
- [FbcCommandService](src/commander/services/fbc_command_service.py)
- [RpcCommandService](src/commander/services/rpc_command_service.py)
- [CommandQueue](src/commander/command_queue.py)

### Test Cases
- [test_command_execution.py](tests/commander/test_command_execution.py)

## References

- [Node Implementation](src/commander/models.py)
- [NodeManager Implementation](src/commander/node_manager.py)
- [FbcCommandService Implementation](src/commander/services/fbc_command_service.py)
- [RpcCommandService Implementation](src/commander/services/rpc_command_service.py)
- [Test Cases](tests/commander/test_command_execution.py)