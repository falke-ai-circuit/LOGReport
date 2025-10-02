# TECH_command_services_v1.md

## Overview

This document details the architecture, usage, and integration of command services within the LOGReport Commander application. It covers `CommandService` (base class), `FbcCommandService`, `RpcCommandService`, and `BsToolCommandService`.

## Specs

### CommandService (Base Class)

- Abstract base class for all command services.
- Defines common interface for queuing and execution.
- Standardizes error handling and response processing.
- Provides dependency injection for command queue and log writer.

### FBC Command Service

**Purpose**: Queues and processes Fieldbus (FBC) commands.

| Method | Description | Parameters |
|---|---|---|
| `queue_fieldbus_command` | Queues FBC command. | `node_name`, `token_id` |
| `handle_response` | Processes FBC command response. | `response` |

### RPC Command Service

**Purpose**: Queues RPC print/clear commands.

| Method | Description | Parameters |
|---|---|---|
| `queue_rpc_command` | Queues RPC print/clear command. | `node_name`, `token_id`, `action` |

### BsTool Command Service

**Purpose**: Executes `bstool.exe` and manages its output.

| Method | Description | Parameters |
|---|---|---|
| `execute_bstool` | Executes `bstool.exe` in a separate thread. | `log_file_path`, `bstool_command_args` |
| `copy_to_log` | Writes content to a specified log file. | `content`, `log_file_path` |
| `clear_log` | Truncates a log file. | `log_file_path` |

## Examples

### Executing FBC Command

```python
# From CommanderWindow context menu
fbc_service.queue_fieldbus_command("AP01m", "12345")

# Manually via queue
command_queue.add_command(
    "print from fbc io structure 123450000",
    node="AP01m",
    token="12345"
)
```

### Executing BsTool Command

```python
# From CommanderWindow context menu or directly
bstool_service.execute_bstool("path/to/selected_log.log", "-errlog AP01")
```

### Handling Command Results

```python
# Example response handler
def on_command_complete(response):
    if "structure" in response:
        parse_fieldbus_structure(response)
    elif "counters" in response:
        parse_rupi_counters(response)
```

## Troubleshooting

### Standardized Error Handling

Base `CommandService` includes robust error handling for connection failures and timeouts.

```python
# Base CommandService error handling snippet
def execute_command(self, command, node_name, token_id):
    try:
        response = self.telnet_session.send_command(command)
        if "ERROR" in response:
            self.handle_error(response, node_name, token_id)
            return None
        return response
    except ConnectionError as e:
        self.logger.error(f"Connection failed for {node_name}: {e}")
        self.reconnect()
        raise
    except TimeoutError as e:
        self.logger.error(f"Command timeout for {node_name}: {e}")
        self.handle_timeout(command, node_name)
        raise
```

## Config

### Integration Points

- **CommanderWindow**: Updates status bar, provides context menu actions, manages command I/O.
- **LogWriter**: Appends command outputs, includes metadata, handles log file rotation.

## Version History

- **v1.0 (2025-09-28)**: Initial condensation and reformatting.

## Future Enhancements

### Adding New Command Type
1. Create new `CommandService` subclass.
2. Implement command formatting.
3. Add response handling.
4. Register with `CommanderWindow`.
## Codebase Sync
- LogWriter: [src/commander/log_writer.py:51](src/commander/log_writer.py:51)
- CommandQueue: [src/commander/command_queue.py:1](src/commander/command_queue.py:1)
## Codebase Sync
- LogWriter: [src/commander/log_writer.py:51](src/commander/log_writer.py:51)
- CommandQueue: [src/commander/command_queue.py:1](src/commander/command_queue.py:1)
 🔗 [ARCH_command_queue_v1](architecture/ARCH_command_queue_v1.md)