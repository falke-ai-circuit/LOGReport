# Sequential Token Processing Implementation

## Overview

This document describes the implementation of sequential token processing for FBC/RPC services in the LOGReporter application. The implementation ensures that all token types (FBC, RPC, LOG, LIS) are processed uniformly with proper completion-based chaining and safety mechanisms.

The Node class stores tokens as a dictionary of lists (`Dict[str, List[NodeToken]]`) to handle multiple tokens with the same ID but different types. This change was implemented to correctly handle cases where FBC and RPC tokens share the same ID, which is common in the system. This approach allows the system to distinguish between different token types that have the same identifier, ensuring accurate token processing and management.

## Key Features

### 1. Sequential Processing
- Tokens are processed one at a time in the order they appear
- Each token is queued only after the previous one completes
- Completion-based chaining ensures proper sequencing
- Direct callback mechanism for immediate next token processing

### 2. Safety Mechanisms
- **Circuit Breaker**: Stops processing after 3 consecutive failures
- **Timeouts**: Overall processing timeout to prevent indefinite execution
- **Resource Management**: Proper cleanup of resources between tokens

### 3. Error Handling
- Individual token failures don't halt the entire batch
- Detailed error tracking and reporting
- Isolated logging for each token
- Circuit breaker integration with failure tracking

## Implementation Details

### SequentialCommandProcessor Class

The `SequentialCommandProcessor` class manages sequential execution of tokens with isolated logging and error handling. Key methods include:

#### process_tokens_sequentially()
Main entry point for sequential token processing:
- Initializes processing state and creates unique batch ID
- Sets up batch logging with token count
- Prepares each token with isolated logging context
- Normalizes tokens according to protocol-specific rules
- Adds commands to queue for sequential execution
- Uses direct callbacks for immediate next token processing

#### _on_command_completed()
Callback method triggered when a command completes:
- Updates processing statistics (success/failure counts)
- Releases telnet client resources
- Writes token-specific results to log
- Closes token-specific log file
- Checks for batch completion and emits final signals
- Performs batch logging finalization

#### _prepare_token_context()
Creates isolated context for each token:
- Normalizes token ID based on protocol
- Validates node IP address
- Opens token-specific log file
- Writes standardized metadata header to log

#### _release_telnet_client()
Releases telnet client resources:
- Safely closes telnet connections
- Handles exceptions during cleanup
- Resets client reference to prevent reuse

#### process_sequential_batch()
Processes subgroup tokens with circuit breaker:
- Uses consecutive failure tracking (3 failures trigger circuit breaker)
- Per-command timeout handling
- Isolated logging per token
- Periodic resource cleanup

### Safety Mechanisms

#### Circuit Breaker
- **Only activated in `process_sequential_batch` method**
- Triggers after 3 consecutive command failures
- Stops further processing in the current batch
- Requires manual reset before new operations

#### Timeouts
- Per-command timeout tracking
- Overall processing timeout based on token count
- Configurable timeout values
- Graceful termination on timeout

#### Resource Management
- Telnet client cleanup after each token
- Qt event processing to prevent UI freezing
- Garbage collection for memory optimization
- Batch logging resource management

### Batch Logging System
- Unique batch ID generated for each operation
- Centralized batch log with summary statistics
- Token-specific logs with standardized headers
- Metadata includes:
  - Token ID
  - Node name
  - Timestamp
  - Protocol
  - Batch ID

## Token Detection

### Overview

The NodeManager.scan_log_files method is responsible for detecting and mapping log files to tokens. Recent improvements have been made to correctly identify all token types (FBC, RPC, LOG, LIS) in node-specific directories with a unified approach. The implementation ensures that all token types are processed uniformly.

### Key Improvements

#### 1. Uniform Token Classification Logic
- For all file types (.log, .fbc, .rpc, .lis), the method now checks the filename content to determine the token type
- Files are classified based on their filename patterns (e.g., `XXX_FBC.log`, `XXX_RPC.log`, `XXX.fbc`, `XXX.rpc`)
- This ensures consistent handling of all token types regardless of file extension
- All token types (FBC, RPC, LOG, LIS) are processed using the same logic

#### 2. Node Name Extraction
- For node-specific files in node directories, the directory name is used as the node name
- This ensures correct mapping of files to nodes regardless of filename prefixes
- Fallback to filename prefix is used only when directory name doesn't match any known node

#### 3. Token ID Extraction
- Improved extraction of token IDs from filenames with multiple underscores
- For files with pattern `XXX_FBC.log`, the token ID is correctly extracted as `XXX`
- Proper normalization of numeric token IDs to 3-digit format for FBC tokens
- Token ID extraction logic has been updated to properly handle each file type based on their specific filename patterns

#### 4. Token ID Normalization
- For FBC tokens, numeric IDs are padded to 3 digits (e.g., "162" remains "162", "16" becomes "016")
- For FBC tokens, alphanumeric IDs are converted to uppercase (e.g., "163a" becomes "163A")
- For non-FBC tokens, only whitespace is stripped

#### 5. Dynamic IP Discovery
- Scans log directory names and filenames for IP patterns using regex
- Pattern: `(\d{1,3}-\d{1,3}-\d{1,3}-\d{1,3})` (e.g., "192-168-0-11")
- Updates token objects with discovered IP addresses when tokens don't already have a valid IP

#### 6. Enhanced Token Matching Logic
- Token matching logic has been updated to be more specific about token types, ensuring tokens are matched by both token ID AND token type rather than just token ID
- Multiple matching strategies are used in order of precedence to ensure accurate token identification:
  - Case-insensitive exact token ID and type match
  - Case-insensitive token ID and type match (substring)
  - Case-insensitive exact token ID match (only if no token of this type exists)
  - Token ID contains match (only if no token of this type exists)
- This approach correctly handles cases where FBC and RPC tokens share the same ID, which is common in the system

### Implementation Details

The scan_log_files method processes files in the following way:

1. For all file types:
   - Extract token type from filename pattern or parent directory
   - Use directory name as node name when available
   - Extract token ID using appropriate pattern matching for each token type

2. Token matching strategies (in order of precedence):
   - Case-insensitive exact token ID and type match
   - Case-insensitive token ID and type match (substring)
   - Case-insensitive exact token ID match (only if no token of this type exists)
   - Token ID contains match (only if no token of this type exists)

3. Enhanced token matching logic:
   - Token matching logic has been updated to be more specific about token types, ensuring tokens are matched by both token ID AND token type rather than just token ID
   - This approach correctly handles cases where FBC and RPC tokens share the same ID, which is common in the system
   - The system can distinguish between different token types that have the same identifier, ensuring accurate token processing and management

4. Token creation for unmatched files:
   - When a file is found but no matching token exists, a new token representation is created
   - The token is added to the node automatically
   - Original token ID case is preserved for FBC files

5. Unified handling of all token types:
   - All token types (FBC, RPC, LOG, LIS) are processed using the same logic
   - Token type is always determined from the filename or directory structure
   - Distance-based matching logic has been removed for improved accuracy

### Token Storage Implementation

The Node class now stores tokens as a dictionary of lists (`Dict[str, List[NodeToken]]`) to handle multiple tokens with the same ID but different types. The `add_token` method in the Node class has been updated to:

1. Store tokens in lists grouped by token ID
2. Check if a token of the same type already exists for a given ID
3. Replace existing tokens of the same type rather than adding duplicates
4. Allow multiple tokens with the same ID but different types to coexist

This implementation ensures that both FBC and RPC tokens with the same ID can be stored and retrieved correctly.

### Configuration Requirements

#### Node Configuration (nodes_test.json)

For proper token detection, the node configuration file must include all expected tokens with their correct types. For example, the AP01m node configuration should include:

```json
[
  {
    "name": "AP01m",
    "ip_address": "192.168.0.11",
    "tokens": [
      {
        "token_id": "162",
        "token_type": "FBC",
        "port": 23,
        "protocol": "telnet"
      },
      {
        "token_id": "163",
        "token_type": "FBC",
        "port": 23,
        "protocol": "telnet"
      },
      {
        "token_id": "164",
        "token_type": "FBC",
        "port": 23,
        "protocol": "telnet"
      },
      {
        "token_id": "162",
        "token_type": "RPC",
        "port": 23,
        "protocol": "telnet"
      },
      {
        "token_id": "163",
        "token_type": "RPC",
        "port": 23,
        "protocol": "telnet"
      },
      {
        "token_id": "164",
        "token_type": "RPC",
        "port": 23,
        "protocol": "telnet"
      }
    ]
  }
]
```

Important notes:
- All tokens (162, 163, 164) must be explicitly listed with their correct `token_type` (FBC, RPC, LOG, LIS)
- The IP address must match the actual node IP address
- Port and protocol should be set according to the node's configuration
- Missing or incorrectly typed tokens may not be detected properly during scanning
- The node configuration file must include all expected tokens with their correct types
- The token type is always determined from the filename or directory structure
- Both FBC and RPC tokens with the same ID can be configured and will be handled correctly

### Example

For the directory structure:
```
test_logs/
└── AP01m/
    ├── 162_FBC.log
    ├── 163_FBC.log
    └── 164_FBC.log
```

All three tokens (162, 163, 164) are correctly detected and mapped to the AP01m node.

## Usage Examples

### Processing FBC Tokens with Error Handling
```python
processor = SequentialCommandProcessor(command_queue, fbc_service, rpc_service, session_manager, logging_service)
tokens = [NodeToken(token_id="162", token_type="FBC"), NodeToken(token_id="163", token_type="FBC")]
try:
    processor.process_fbc_commands("AP01m", tokens)
except Exception as e:
    logger.error(f"Processing failed: {str(e)}")
```

### Processing Mixed Tokens with Normalization
```python
processor = SequentialCommandProcessor(command_queue, fbc_service, rpc_service, session_manager, logging_service)
tokens = [
    NodeToken(token_id="162", token_type="FBC", node_ip="192.168.0.11"),
    NodeToken(token_id="163a", token_type="RPC", node_ip="192.168.0.11")
]
processor.process_tokens_sequentially("AP01m", tokens, action="print")
```

### Subgroup Processing with Circuit Breaker
```python
processor = SequentialCommandProcessor(command_queue, fbc_service, rpc_service, session_manager, logging_service)
tokens = [NodeToken(token_id="163", token_type="RPC"), NodeToken(token_id="164", token_type="RPC")]
results = processor.process_sequential_batch(
    tokens, 
    "FBC", 
    {"node_name": "AP01m", "command": "print"}
)
for result in results:
    if not result.success:
        logger.warning(f"Token {result.token} failed: {result.error}")
```

## Backward Compatibility

The implementation maintains backward compatibility with existing interfaces:
- All existing method signatures are preserved
- Command queue interface remains unchanged
- Signal emissions follow existing patterns
- No breaking changes to public API

## Testing

Unit tests verify:
- Single token processing
- Multiple token processing with partial failures
- Circuit breaker activation
- Timeout handling
- Resource cleanup
- Progress tracking
- Completion-based chaining

End-to-end tests verify:
- Correct detection of FBC and RPC tokens with the same ID
- Proper handling of multiple token types with identical identifiers
- Accurate mapping of log files to tokens based on both ID and type

## Performance Considerations

- Minimal memory footprint through proper resource management
- Efficient event processing to prevent UI freezing
- Optimized logging with batch operations
- Direct callback mechanism for reduced latency