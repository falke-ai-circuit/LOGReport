# SessionConfig Class Architecture

## Overview
The `SessionConfig` class (`src/commander/session_manager.py`) is a dataclass designed to encapsulate and manage the configuration parameters for various session types within the LOGReport application. It provides a structured and type-hinted way to define session-specific settings, ensuring consistency and ease of use across different session management operations.

## Class Definition
```python
@dataclass
class SessionConfig:
    host: str
    port: int
    session_type: SessionType
    username: str = ""
    password: str = ""
    timeout: int = 15
```

## Attributes
- `host` (str): The hostname or IP address of the remote server for the session.
- `port` (int): The port number for connecting to the remote server.
- `session_type` (SessionType): An enumeration (`SessionType` from `src/commander/session_manager.py`) indicating the type of session (e.g., Telnet, VNC).
- `username` (str, optional): The username for authentication, defaults to an empty string.
- `password` (str, optional): The password for authentication, defaults to an empty string.
- `timeout` (int, optional): The connection timeout in seconds, defaults to 15 seconds.

## Usage
`SessionConfig` objects are typically created and passed to session management services (e.g., `SessionManager`, `TelnetService`, `VNCSession`) to establish and configure new sessions. This centralizes session parameter definition, making it easier to manage and modify session behaviors.

## Dependencies
- `SessionType` (from `src/commander/session_manager.py`): An Enum used to define the type of session.
- `@dataclass` (from `dataclasses` module): Python decorator for automatically generating boilerplate methods for data classes.

## Cross-references
- `SessionManager` (from `src/commander/session_manager.py`): Uses `SessionConfig` to create and manage sessions.
- `TelnetSession` (from `src/commander/session_manager.py`): Uses `SessionConfig` for Telnet session parameters.
- `VNCSession` (from `src/commander/session_manager.py`): Uses `SessionConfig` for VNC session parameters.
- `TelnetService.connect` (from `src/commander/services/telnet_service.py`): Consumes `SessionConfig` for connection details.