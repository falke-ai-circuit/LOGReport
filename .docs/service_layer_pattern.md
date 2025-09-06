# Service Layer Pattern Documentation

## Overview

The Service Layer Pattern is a core architectural pattern in the LOGReport project that centralizes business logic in dedicated service classes. This pattern separates concerns by moving command generation, execution, error handling, and logging logic from UI components and data models into specialized service classes.

## Key Benefits

1. **Centralized Business Logic**: All command-related operations are handled in service classes
2. **Consistent Implementation**: Standardized approaches to command generation and execution
3. **Enhanced Testability**: Services can be unit tested independently of UI components
4. **Improved Maintainability**: Changes to business logic only require updates to service classes
5. **Reduced Code Duplication**: Common operations are implemented once in service methods

## Implementation Details

### Service Classes

The LOGReport project implements two primary service classes:

1. **FbcCommandService**: Handles FBC (FieldBus Communication) command operations
2. **RpcCommandService**: Handles RPC (Remote Procedure Call) command operations

Both services inherit from QObject to support Qt signal/slot mechanisms for UI communication.

### Core Responsibilities

Each service class is responsible for:

1. **Command Generation**: Creating properly formatted command strings
2. **Token Management**: Retrieving and validating NodeToken objects
3. **Queue Operations**: Adding commands to the CommandQueue for execution
4. **Log Management**: Initializing and managing log files for command output
5. **Error Handling**: Providing consistent error handling and reporting
6. **UI Communication**: Emitting signals to update the user interface

### Service Integration

Services are integrated through the CommanderService class which:

1. **Coordinates Operations**: Manages interactions between FbcCommandService and RpcCommandService
2. **Handles Events**: Connects service signals to appropriate handlers
3. **Manages Dependencies**: Provides services with required dependencies (NodeManager, CommandQueue, etc.)

### Signal/Slot Communication

Services use Qt signals to communicate with UI components:

```python
# Define signals for UI updates
set_command_text = pyqtSignal(str)
switch_to_telnet_tab = pyqtSignal()
focus_command_input = pyqtSignal()
status_message = pyqtSignal(str, int)  # message, duration
report_error = pyqtSignal(str)         # error message
```

## Usage Examples

### FBC Command Processing

```python
# In UI component (e.g., NodeTreePresenter)
def process_fieldbus_command(self, token_id, node_name):
    # Validate and queue command through service
    self.fbc_service.queue_fieldbus_command(node_name, token_id, telnet_client)
    # Start command processing
    self.command_queue.start_processing()
```

### RPC Command Processing

```python
# In UI component (e.g., ContextMenuService)
def _handle_rpc_token_action(self, node_name, token_id, action_type):
    # Normalize token ID
    normalized_token_id = normalize_token(token_id)
    # Process command through service
    token_part = normalized_token_id.split('_')[-1] if '_' in normalized_token_id else normalized_token_id
    self.presenter.process_rpc_command(node_name, normalized_token_id, action_type)
```

## Best Practices

### 1. Always Use Service Methods
Never generate command strings directly in UI components. Always use service methods for:
- Command generation
- Token validation
- Queue management
- Error handling

### 2. Centralize Business Logic
Keep all business logic in service classes:
- Command formatting rules
- Validation logic
- Error recovery procedures
- Logging implementations

### 3. Maintain Consistent Interfaces
Service methods should have consistent signatures and behavior:
```python
def queue_command_type(self, node_name: str, token_id: str, additional_params...)
```

### 4. Handle Errors Gracefully
Services should catch and handle exceptions appropriately:
- Log errors with sufficient context
- Emit appropriate UI signals
- Provide meaningful error messages to users

### 5. Use Dependency Injection
Services should receive dependencies through constructor parameters:
```python
def __init__(self, node_manager: NodeManager, command_queue: CommandQueue, parent=None):
    super().__init__(parent)
    self.node_manager = node_manager
    self.command_queue = command_queue
```

## Related Components

### CommanderService
The central coordinator that manages FbcCommandService and RpcCommandService instances and handles cross-service operations.

### CommandQueue
The execution engine that processes queued commands from service classes.

### NodeManager
Provides token and node data to service classes for command generation.

## Testing

Service classes are tested through dedicated unit tests in `tests/commander/test_command_execution.py`:

- `test_fbc_command_execution`: Validates FBC command generation and queuing
- `test_rpc_command_execution`: Validates RPC command generation and queuing
- `test_same_token_id_different_types_command_execution`: Ensures proper handling of tokens with same ID but different types

## References

- [FbcCommandService Implementation](src/commander/services/fbc_command_service.py)
- [RpcCommandService Implementation](src/commander/services/rpc_command_service.py)
- [CommanderService Implementation](src/commander/services/commander_service.py)
- [Batch Operations Architecture](.docs/batch_operations_architecture.md)