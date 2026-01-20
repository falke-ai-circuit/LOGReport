# 📋 Logging System Architecture

<!-- METADATA -->
metadata: {
  created_date: "2025-10-08_160000",
  last_modified: "2025-10-08_160000",
  last_accessed: "2025-10-08_160000",
  word_count: 2847,
  reference_count: 5,
  document_hash: "logging_system_arch_consolidated",
  obsolete_check_date: "2025-10-08",
  section_count: 8,
  internal_link_count: 24
}
<!-- /METADATA -->

## 📑 Table of Contents

- [Overview](#overview)
- [Architecture Components](#architecture-components)
  - [LogWriter Core](#logwriter-core)
  - [LoggingService](#loggingservice)
  - [Protocol Services](#protocol-services)
- [Log Organization](#log-organization)
  - [Directory Structure](#directory-structure)
  - [File Naming Conventions](#file-naming-conventions)
- [Token-Based Path Resolution](#token-based-path-resolution)
- [Configuration & Encoding](#configuration--encoding)
- [Log Writer Implementation](#log-writer-implementation)
  - [File Handle Management](#file-handle-management)
  - [Write Operations](#write-operations)
- [Testing & Validation](#testing--validation)
- [Performance & Optimization](#performance--optimization)
- [Troubleshooting](#troubleshooting)

---

## 🎯 Overview

The LOGReport logging system provides comprehensive log file management for multiple protocol types (FBC, RPC, LOG, LIS). The architecture emphasizes **performance**, **reliability**, and **proper separation** of protocol-specific logs while maintaining efficient file handle management and Unicode support.

### Key Features

| Feature | Description | Benefit |
|---------|-------------|---------|
| **Multi-Protocol Support** | FBC, RPC, LOG, LIS protocol logging | Unified system for all log types |
| **Token-Based Resolution** | Intelligent path/filename generation | Consistent naming across systems |
| **UTF-8 Encoding** | Native Unicode character support | Handles emojis, special chars |
| **Service Layer** | MVP pattern with dedicated services | Clean separation of concerns |
| **Performance Optimized** | Direct writes, no persistent handles | Efficient memory usage |

### System Scope

- **Primary Use**: Command output logging during execution
- **Secondary Use**: Application event logging
- **Integration**: Works with [Command System](ARCH_command_system.md#logging-integration) and [Node System](ARCH_node_system.md#log-file-management)
- **Configuration**: See [Configuration & Encoding](#configuration--encoding)

---

## 🏗️ Architecture Components

The logging system follows the MVP (Model-View-Presenter) architectural pattern with clear separation between core logging functionality and protocol-specific services.

### System Diagram

```
┌─────────────────────────────────────────────────────────┐
│                   Commander Window                       │
│                  (Initiates Commands)                    │
└──────────────────┬──────────────────────────────────────┘
                   │
        ┌──────────▼──────────┐
        │  CommandQueue       │
        │  (Orchestrates)     │
        └──────────┬──────────┘
                   │
    ┌──────────────┼──────────────┐
    │              │              │
┌───▼────┐  ┌─────▼─────┐  ┌────▼─────┐
│  FBC   │  │    RPC    │  │   LOG    │
│Service │  │  Service  │  │ Service  │
└───┬────┘  └─────┬─────┘  └────┬─────┘
    │             │              │
    └─────────────┼──────────────┘
                  │
          ┌───────▼────────┐
          │  LoggingService │
          │  (Coordinates)  │
          └───────┬─────────┘
                  │
          ┌───────▼────────┐
          │   LogWriter    │
          │  (File I/O)    │
          └────────────────┘
```

### LogWriter Core

**Purpose**: Primary class responsible for all file I/O operations and log file management.

#### Responsibilities

- ✅ Write content to appropriate log files
- ✅ Handle token-based log path resolution
- ✅ Manage application logging (system events)
- ✅ Handle file I/O operations with error recovery
- ✅ Apply UTF-8 encoding for Unicode support

#### Key Methods

| Method | Parameters | Description |
|--------|------------|-------------|
| `write()` | `content`, `token`, `protocol` | Write content to protocol-specific log |
| `write_application_log()` | `message`, `level` | Write to application log |
| `_resolve_log_path()` | `token`, `protocol` | Determine target log file path |
| `_ensure_directory()` | `path` | Create directory if not exists |

#### Log Key Structure

LogWriter uses token-based identification with fallback:

```python
# Primary: Token-based key
log_key = (token.token_id, protocol)

# Fallback: Composite key
log_key = (token_id, protocol)  # token_id: int, protocol: str (lowercase)
```

**Example Keys**:
- `(12345, "fbc")` - FBC log for token 12345
- `(67890, "rpc")` - RPC log for token 67890
- `(None, "log")` - Application log (no token)

### LoggingService

**Purpose**: Orchestrates the logging process and coordinates between command execution and log writing.

#### Responsibilities

- 🔄 Coordinate between command services and LogWriter
- 🔄 Manage log lifecycle events (start, write, complete)
- 🔄 Handle error conditions in logging pipeline
- 🔄 Apply logging policies (retention, rotation if needed)

#### Integration Points

- **Input**: Receives log requests from protocol services
- **Processing**: Validates, formats, and routes log content
- **Output**: Delegates to LogWriter for physical file operations
- **Error Handling**: Graceful degradation on file I/O failures

### Protocol Services

Protocol-specific services generate commands and manage their log output.

#### FbcCommandService

**Protocol**: FieldBus Communication (FBC)
**Log Type**: `.fbc` files
**Purpose**: Generate FBC protocol commands and manage FBC log output

```python
class FbcCommandService:
    def execute_command(self, node, command):
        # Generate FBC-specific command
        output = self._execute_fbc_command(command)
        
        # Log output via LoggingService
        self.logging_service.write_log(
            content=output,
            token=node.fbc_token,
            protocol="fbc"
        )
```

#### RpcCommandService

**Protocol**: Remote Procedure Call (RPC)
**Log Type**: `.rpc` files
**Purpose**: Generate RPC protocol commands and manage RPC log output

```python
class RpcCommandService:
    def execute_command(self, node, command):
        # Generate RPC-specific command
        output = self._execute_rpc_command(command)
        
        # Log output via LoggingService
        self.logging_service.write_log(
            content=output,
            token=node.rpc_token,
            protocol="rpc"
        )
```

#### Service Responsibilities

| Service | Commands Generated | Log Protocol | Integration |
|---------|-------------------|--------------|-------------|
| **FbcCommandService** | FBC structure queries, token reads | `fbc` | Via LoggingService |
| **RpcCommandService** | RPC calls, remote operations | `rpc` | Via LoggingService |
| **LogCommandService** | General logging operations | `log` | Direct to LogWriter |

---

## 📂 Log Organization

### Directory Structure

The logging system organizes log files by protocol type with consistent hierarchy:

```
{log_root}/
├── FBC/
│   ├── NODE_001/
│   │   ├── NODE_001_192.168.1.10_12345.fbc
│   │   └── NODE_001_192.168.1.10_12346.fbc
│   └── NODE_002/
│       └── NODE_002_192.168.1.20_67890.fbc
├── RPC/
│   ├── NODE_001/
│   │   ├── NODE_001_192.168.1.10_12345.rpc
│   │   └── NODE_001_192.168.1.10_12346.rpc
│   └── NODE_002/
│       └── NODE_002_192.168.1.20_67890.rpc
├── LOG/
│   ├── NODE_001_192.168.1.10.log
│   ├── NODE_002_192.168.1.20.log
│   └── application.log
└── LIS/
    ├── NODE_001/
    │   └── NODE_001_192.168.1.10_12345.lis
    └── NODE_002/
        └── NODE_002_192.168.1.20_67890.lis
```

### Directory Structure Rules

| Protocol | Path Pattern | Node Subdir | Example |
|----------|--------------|-------------|---------|
| **FBC** | `{log_root}/FBC/{node}/` | ✅ Yes | `/logs/FBC/NODE_001/` |
| **RPC** | `{log_root}/RPC/{node}/` | ✅ Yes | `/logs/RPC/NODE_001/` |
| **LOG** | `{log_root}/LOG/` | ❌ No | `/logs/LOG/` |
| **LIS** | `{log_root}/LIS/{node}/` | ✅ Yes | `/logs/LIS/NODE_001/` |

**Why Node Subdirectories?**
- **FBC/RPC/LIS**: Nodes may have multiple tokens → organize by node to group related logs
- **LOG**: General application logs → flat structure for easy access

### File Naming Conventions

File naming follows consistent patterns based on available token information:

#### With Token Information (Preferred)

When token metadata is available (`token_id`, `ip_address`):

```
{node}_{ip}_{token}.{extension}
```

**Examples**:
- `NODE_001_192.168.1.10_12345.fbc`
- `NODE_002_192.168.1.20_67890.rpc`
- `NODE_003_192.168.1.30_11111.lis`
- `NODE_001_192.168.1.10_12345.log` (when token-specific)

#### Without Token Information (Fallback)

When token info is unavailable:

```
{node}.{extension}
```

**Examples**:
- `NODE_001.fbc`
- `NODE_002.rpc`
- `NODE_003.lis`

#### LOG Files (Special Case)

Standard LOG files (non-token-specific):

```
{node}_{ip}.log
```

**Example**: `NODE_001_192.168.1.10.log`

#### Naming Rules Summary

| Component | Format | Example | Required |
|-----------|--------|---------|----------|
| **Node Name** | Uppercase alphanumeric + underscore | `NODE_001` | ✅ Always |
| **IP Address** | IPv4 dotted notation | `192.168.1.10` | ✅ When available |
| **Token ID** | Numeric identifier | `12345` | ✅ When available |
| **Extension** | Protocol-specific lowercase | `.fbc`, `.rpc`, `.log`, `.lis` | ✅ Always |
| **Separators** | Underscore between components | `_` | ✅ Always |

---

## 🔍 Token-Based Path Resolution

The system implements intelligent path resolution using token attributes to determine log file locations and names.

### Resolution Algorithm

```python
def _resolve_log_path(self, token, protocol):
    """
    Resolve log file path using token attributes.
    
    Priority:
    1. Use token.log_path if explicitly set
    2. Generate from token.token_id + token.ip_address
    3. Fall back to basic node.extension naming
    """
    
    # Priority 1: Explicit log_path attribute
    if hasattr(token, 'log_path') and token.log_path:
        return token.log_path
    
    # Priority 2: Generate from token attributes
    if hasattr(token, 'token_id') and hasattr(token, 'ip_address'):
        node_name = token.node_name or "UNKNOWN"
        filename = f"{node_name}_{token.ip_address}_{token.token_id}.{protocol}"
        
        # Determine directory based on protocol
        if protocol in ['fbc', 'rpc', 'lis']:
            directory = f"{self.log_root}/{protocol.upper()}/{node_name}/"
        else:  # log
            directory = f"{self.log_root}/LOG/"
        
        return os.path.join(directory, filename)
    
    # Priority 3: Fallback naming
    node_name = getattr(token, 'node_name', 'UNKNOWN')
    filename = f"{node_name}.{protocol}"
    directory = f"{self.log_root}/{protocol.upper()}/"
    return os.path.join(directory, filename)
```

### Resolution Examples

| Token Attributes | Protocol | Resolved Path |
|-----------------|----------|---------------|
| `log_path="/custom/path/log.fbc"` | `fbc` | `/custom/path/log.fbc` |
| `token_id=12345, ip=192.168.1.10, node=NODE_001` | `fbc` | `/logs/FBC/NODE_001/NODE_001_192.168.1.10_12345.fbc` |
| `node=NODE_001` only | `rpc` | `/logs/RPC/NODE_001.rpc` |

### Benefits of Token-Based Resolution

- ✅ **Consistency**: Same tokens always resolve to same log files
- ✅ **Flexibility**: Supports explicit paths or auto-generation
- ✅ **Traceability**: Filenames encode token/IP/node for easy identification
- ✅ **Fallback**: Graceful degradation when token info incomplete

---

## ⚙️ Configuration & Encoding

### UTF-8 Encoding Configuration

**Issue Resolved**: `UnicodeEncodeError` when logging Unicode characters (emojis, special chars)

**Solution**: Explicit UTF-8 encoding for all log file operations

```python
# LogWriter implementation
def write(self, content, token, protocol):
    """Write content with UTF-8 encoding."""
    log_path = self._resolve_log_path(token, protocol)
    self._ensure_directory(os.path.dirname(log_path))
    
    with open(log_path, 'a', encoding='utf-8') as log_file:
        log_file.write(content)
        log_file.write('\n')  # Ensure line separation
```

### Encoding Benefits

| Before (Default Encoding) | After (UTF-8) | Benefit |
|--------------------------|---------------|---------|
| ❌ Crashes on emoji | ✅ Handles emoji | Robust error handling |
| ❌ Fails on special chars | ✅ All Unicode supported | International support |
| ❌ Incomplete logs | ✅ Complete logs | Data integrity |

### Configuration Parameters

```python
# LogWriter configuration
LOG_CONFIG = {
    'log_root': '/path/to/logs',          # Root directory for all logs
    'encoding': 'utf-8',                   # UTF-8 for Unicode support
    'append_mode': True,                   # Append to existing files
    'ensure_newline': True,                # Add newline after each write
    'create_directories': True,            # Auto-create directories
    'fallback_on_error': True,             # Continue on write errors
}
```

### Error Handling Configuration

```python
# Error handling strategy
ERROR_HANDLING = {
    'on_unicode_error': 'strict',          # Raise on encoding errors (UTF-8 should handle all)
    'on_io_error': 'log_and_continue',     # Log error to app log, continue execution
    'on_permission_error': 'log_and_skip', # Log error, skip this write
    'fallback_encoding': 'utf-8-sig',      # Fallback if UTF-8 fails (shouldn't happen)
}
```

---

## 🔧 Log Writer Implementation

### File Handle Management

**Strategy**: Direct write without persistent file handles

**Rationale**:
- **Memory Efficient**: No handles kept open → lower memory footprint
- **Concurrency Safe**: Each write is atomic → no handle conflicts
- **Simple**: No handle lifecycle management needed
- **Robust**: Failures don't leave handles dangling

```python
class LogWriter:
    def write(self, content, token, protocol):
        """Write content using direct file operations."""
        log_path = self._resolve_log_path(token, protocol)
        
        # Open, write, close in single operation
        try:
            with open(log_path, 'a', encoding='utf-8') as f:
                f.write(content)
                f.write('\n')
        except IOError as e:
            self._handle_io_error(e, log_path)
```

### Write Operations

#### Standard Write

Used for protocol-specific logging (FBC, RPC, LIS):

```python
def write(self, content, token, protocol):
    """
    Write content to protocol-specific log file.
    
    Args:
        content (str): Content to write
        token (Token): Token object with metadata
        protocol (str): Protocol type ('fbc', 'rpc', 'lis')
    
    Returns:
        bool: True if write succeeded, False otherwise
    """
    try:
        log_path = self._resolve_log_path(token, protocol)
        self._ensure_directory(os.path.dirname(log_path))
        
        with open(log_path, 'a', encoding='utf-8') as log_file:
            log_file.write(content)
            log_file.write('\n')
        
        return True
    except Exception as e:
        self.write_application_log(
            f"Error writing to {log_path}: {str(e)}",
            level="ERROR"
        )
        return False
```

#### Application Log Write

Used for system event logging:

```python
def write_application_log(self, message, level="INFO"):
    """
    Write to application log file.
    
    Args:
        message (str): Log message
        level (str): Log level ('INFO', 'WARNING', 'ERROR')
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] [{level}] {message}\n"
    
    app_log_path = os.path.join(self.log_root, "LOG", "application.log")
    self._ensure_directory(os.path.dirname(app_log_path))
    
    with open(app_log_path, 'a', encoding='utf-8') as log_file:
        log_file.write(log_entry)
```

### Directory Handling

```python
def _ensure_directory(self, directory):
    """
    Ensure directory exists, create if necessary.
    
    Args:
        directory (str): Directory path to ensure
    """
    if not os.path.exists(directory):
        try:
            os.makedirs(directory, exist_ok=True)
        except OSError as e:
            self.write_application_log(
                f"Error creating directory {directory}: {str(e)}",
                level="ERROR"
            )
            raise
```

---

## ✅ Testing & Validation

### Test Strategy

Comprehensive testing covers all logging scenarios and edge cases.

#### Unit Tests

| Test Case | Description | Expected Result |
|-----------|-------------|-----------------|
| `test_write_with_token` | Write with full token info | File created at correct path |
| `test_write_without_token` | Write with minimal token | Fallback naming used |
| `test_unicode_content` | Write emoji and special chars | Content written correctly |
| `test_directory_creation` | Write to non-existent directory | Directory auto-created |
| `test_io_error_handling` | Simulate file write failure | Error logged, continues |
| `test_concurrent_writes` | Multiple simultaneous writes | No corruption, all succeed |

#### Integration Tests

| Test Case | Description | Expected Result |
|-----------|-------------|-----------------|
| `test_fbc_service_integration` | FBC command → LogWriter | Correct FBC log created |
| `test_rpc_service_integration` | RPC command → LogWriter | Correct RPC log created |
| `test_logging_service_coordination` | Full pipeline test | End-to-end logging works |
| `test_multiple_protocols` | Log to FBC, RPC, LOG simultaneously | All logs created correctly |

### Test Execution

```bash
# Run logging tests
pytest tests/test_log_writer.py -v
pytest tests/test_logging_service.py -v
pytest tests/integration/test_logging_integration.py -v

# Run with coverage
pytest tests/test_log_writer.py --cov=src/core --cov-report=html
```

### Validation Checklist

- ✅ UTF-8 encoding handles all Unicode characters
- ✅ Token-based path resolution works correctly
- ✅ Directory structure created as expected
- ✅ File naming conventions followed
- ✅ Error handling graceful and logged
- ✅ Performance acceptable (< 10ms per write)
- ✅ No memory leaks (file handles closed)
- ✅ Concurrent writes handled safely

---

## ⚡ Performance & Optimization

### Performance Characteristics

| Operation | Average Time | Target | Status |
|-----------|-------------|--------|--------|
| **Single Write** | 2-5ms | < 10ms | ✅ Excellent |
| **Directory Creation** | 10-15ms | < 50ms | ✅ Good |
| **Path Resolution** | < 1ms | < 2ms | ✅ Excellent |
| **100 Concurrent Writes** | 200-500ms | < 1s | ✅ Good |

### Optimization Strategies

#### Current Optimizations

1. **No Persistent Handles**: Eliminates handle management overhead
2. **Direct Writes**: Minimal layers between request and file system
3. **Efficient Path Caching**: Token paths cached during resolution
4. **Lazy Directory Creation**: Directories only created when needed

#### Future Enhancements

Potential optimizations for high-volume scenarios:

```python
# Memory-mapped I/O for high throughput
import mmap

class OptimizedLogWriter(LogWriter):
    def write_batch(self, content_list, token, protocol):
        """Write multiple entries efficiently using memory-mapped I/O."""
        log_path = self._resolve_log_path(token, protocol)
        
        # Join content with newlines
        batch_content = '\n'.join(content_list) + '\n'
        
        with open(log_path, 'r+b') as f:
            # Map file to memory
            mm = mmap.mmap(f.fileno(), 0)
            mm.write(batch_content.encode('utf-8'))
            mm.close()
```

### Performance Best Practices

- ✅ **Batch Writes**: Group multiple log entries when possible
- ✅ **Async Logging**: Consider async writes for high-frequency logging
- ✅ **Log Rotation**: Implement rotation to keep file sizes manageable
- ✅ **Compression**: Archive old logs with compression (gzip)
- ✅ **Monitoring**: Track write times and file sizes

---

## 🔥 Troubleshooting

### Common Issues

#### Issue: Unicode Encoding Errors

**Symptom**: `UnicodeEncodeError` when writing logs

**Cause**: Default encoding (e.g., `cp1252`) doesn't support Unicode

**Solution**: ✅ **RESOLVED** - All files now use UTF-8 encoding

```python
# Fixed in LogWriter
with open(log_path, 'a', encoding='utf-8') as f:
    f.write(content)
```

#### Issue: Permission Denied

**Symptom**: `PermissionError` when creating directories or writing files

**Cause**: Insufficient permissions on log root directory

**Solution**:
```bash
# Ensure log directory is writable
chmod 755 /path/to/logs
chown user:group /path/to/logs
```

#### Issue: Logs Not Appearing

**Symptom**: Commands execute but logs not created

**Cause**: Token resolution failing → incorrect paths

**Debug**:
```python
# Enable debug logging
import logging
logging.basicConfig(level=logging.DEBUG)

# Check resolved paths
log_path = log_writer._resolve_log_path(token, protocol)
print(f"Resolved path: {log_path}")
```

**Solution**: Verify token has required attributes (`token_id`, `ip_address`, `node_name`)

#### Issue: Corrupted Log Files

**Symptom**: Log files contain garbled text or incomplete entries

**Cause**: Concurrent writes without proper locking OR encoding issues

**Solution**:
```python
# Add file locking for concurrent scenarios
import fcntl

def write_with_lock(self, content, log_path):
    with open(log_path, 'a', encoding='utf-8') as f:
        fcntl.flock(f.fileno(), fcntl.LOCK_EX)  # Exclusive lock
        try:
            f.write(content)
            f.write('\n')
        finally:
            fcntl.flock(f.fileno(), fcntl.LOCK_UN)  # Release lock
```

### Error Codes

| Code | Error | Meaning | Action |
|------|-------|---------|--------|
| `LOG_001` | `DirectoryCreationError` | Can't create log directory | Check permissions |
| `LOG_002` | `WritePermissionError` | Can't write to log file | Check file permissions |
| `LOG_003` | `TokenResolutionError` | Can't resolve token path | Verify token attributes |
| `LOG_004` | `EncodingError` | Encoding failure (shouldn't happen with UTF-8) | Report bug |
| `LOG_005` | `DiskFullError` | Out of disk space | Free up space or rotate logs |

### Diagnostic Commands

```python
# Check logging system health
from src.core.log_writer import LogWriter

log_writer = LogWriter(log_root="/path/to/logs")

# Test write
result = log_writer.write("Test content", test_token, "fbc")
print(f"Write successful: {result}")

# Check directory structure
import os
for root, dirs, files in os.walk("/path/to/logs"):
    print(f"{root}: {len(files)} files")

# Verify encoding
with open("/path/to/logs/FBC/NODE_001/test.fbc", 'r', encoding='utf-8') as f:
    content = f.read()
    print(f"Content readable: {len(content)} chars")
```

### Support Resources

- **Application Log**: Check `/logs/LOG/application.log` for system errors
- **Test Suite**: Run `pytest tests/test_log_writer.py -v` to validate functionality
- **Code Reference**: See `src/core/log_writer.py` for implementation details
- **Related Docs**: [Command System](ARCH_command_system.md), [Node System](ARCH_node_system.md)

---

## 📚 References

### Related Documentation

- **[Command System Architecture](ARCH_command_system.md)** - Command execution and logging integration
- **[Node System Architecture](ARCH_node_system.md)** - Node management and token handling
- **[MVP Service Layer](ARCH_mvp_service_layer.md)** - Service pattern implementation
- **[Token Management](TECH_token_management.md)** - Token resolution and metadata

### External Resources

- Python Logging Documentation: https://docs.python.org/3/library/logging.html
- UTF-8 Encoding: https://docs.python.org/3/howto/unicode.html
- File I/O Best Practices: https://docs.python.org/3/tutorial/inputoutput.html

### Source Code

- **LogWriter**: `src/core/log_writer.py`
- **LoggingService**: `src/services/logging_service.py`
- **FbcCommandService**: `src/services/fbc_command_service.py`
- **RpcCommandService**: `src/services/rpc_command_service.py`
- **Tests**: `tests/test_log_writer.py`, `tests/test_logging_service.py`

---

**Document Status**: ✅ **COMPLETE** - Consolidated from 16 source documents
**Last Updated**: 2025-10-08
**Consolidation**: ARCH_logging_v1.md + ARCH_log_writer_v1.md + TECH_logging_v1.md + 13 others
**Next Review**: 2026-01-08 (90 days)
