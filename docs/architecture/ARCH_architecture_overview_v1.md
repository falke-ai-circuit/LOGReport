# LOGReport Architecture Overview

## Core Components
| Component | Responsibilities | Key Features |
|-----------|----------------|--------------|
| NetworkSession (Base) | Common interface, error handling | Health monitoring, retries |
| NodeToken | Token validation | id, name, type (FBC/RPC) |
| Node | Config management | Metadata, status, comm |
| CommanderWindow | UI orchestration | Cmd flow, interaction, logs |
| Command Services | Processing layer | Unified FBC/RPC, errors, queue |
| FbcCommandService | FBC logic | Inherits base, session state |
| RpcCommandService | RPC execution | Inherits base, session state |
| Command Queue | Thread-safe exec | Prioritization, state mgmt |
| TelnetOperations | Connection handling | Retry, parsing, timeouts |
| Log Writer | File ops | Rotation (10MB,5 backups), thread-safe |

## Architectural Principles
| Principle | Description | Benefits |
|-----------|-------------|----------|
| Hierarchical Services | Base→Protocol-specific | Reduced duplication |
| Modular Design | UI|Logic|Data separation | Minimal deps |
| Interface Contracts | Defined interfaces | Explicit, standardized errors |
| Thread Safety | Queue sync, atomic ops | No races |

## Data Flow
1. UI initiates cmd
2. Validate/format in CommanderWindow
3. Queue cmd
4. Service processes
5. Log results
6. Update UI

## Error Handling
Centralized in CommanderWindow; service recovery; full logging.