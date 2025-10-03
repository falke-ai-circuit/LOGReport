---
metadata:
  created_date: "2025-10-02_000000"
  last_modified: "2025-10-02T17:15:00Z"  # Post-merge
  word_count: 850  # Combined estimate
  reference_count: 6  # Aggregated
  document_hash: "md5:logging_system_merged_hash"
  obsolete_check_date: "2025-10-02"
  merge_sources: ["logging.md", "ARCH_log_format_v1.md", "TECH_logging_v1.md"]  # Preserved refs
---

# Unified Logging System Architecture (Merged Overview + Format + General) ✅Integrated

## Overview | Feature | Status |
|----------|--------|
| Log creation/writing/org | ✅Managed |
| Token path res | ✅Context |
| Standardized naming | ✅Consistent |
| Efficient I/O (no handles) | ✅Perf |
| NodeManager integration | ✅Aware |

Key Features | Feature | Benefit |
|----------|---------|
| Standardized files | ✅Org |
| Command append | ✅Trace |
| Rotation | ✅Size |
| Multi-type (FBC/RPC/LOG/LIS) | ✅Vers |
| Token res | ✅Accurate |
| Direct write | ✅Resource |
| Error handling | ✅Robust |

The logging system in LOGReport handles creation, management, and writing of log files for different protocol types (FBC, RPC, LOG, LIS). It ensures proper separation and organization of logs while maintaining performance through efficient file handle management. (Unique from logging.md: General architecture preserved.)

## Log Key Structure
The LogWriter uses token-based identification where possible, falling back to composite keys in the format `(token_id, protocol)` where:
- `token_id`: Numeric identifier from node configuration
- `protocol`: Lowercase string ("fbc", "rpc", etc.)

## Directory Structure | Type | Path |
|------|------|
| FBC | {log_root}/FBC/{node}/ |
| RPC | {log_root}/RPC/{node}/ |
| LOG | {log_root}/LOG/ |
| LIS | {log_root}/LIS/{node}/ |

## File Naming Conventions | Protocol | w/Token | Fallback | Ex |
|----------|---------|----------|----|
| FBC | {node}_{ip}_{token}.fbc | {node}.{ext} | AP01m_192-168-0-11_162.fbc |
| RPC | {node}_{ip}_{token}.rpc | {node}.{ext} | AP01r_192-168-0-27_363.rpc |
| LOG | {node}_{ip}_{token}.log | {node}_{ip}.log | AL01_186_LOG.log |
| LIS | {node}_{ip}_{token}.lis | {node}.{ext} | AL01_186_LIS.lis |

## Log File Format Specification (Merged from ARCH_log_format_v1.md)
### Structure
| Aspect | Details |
|--------|---------|
| Directory | log_root/LOG/ |
| Naming | {node.name}_*.log |
| Optimizations | Centralized parsing, token extract (no ext), validation |

### Examples
| Format | Example |
|--------|---------|
| FBC | AP01m_192-168-0-11_162.fbc |
| RPC | AP01r_192-168-0-27_363.rpc |
| Standard | AL01_186_LOG.log |

### Processing Rules
1. Tokens from filename pre-ext
2. Node: [A-Z0-9]+
3. IP: dotted/dashed
4. Port: numeric

### Test Coverage
| Type | Details |
|------|---------|
| Unit | Parsing utils |
| Integration | Full pipeline |
| Coverage | 100% filename logic |

## Token-Based Path Resolution | Priority | Logic | Symbol |
|----------|--------|--------|
| 1 | Token.log_path direct | ✅Precise |
| 2 | token_id/ip_address generate | ✅Derived |
| 3 | Fallback naming | ⚠️Basic |

Ensures consistent naming/location by context ✅Reliable

## Key Components (Merged from TECH_logging_v1.md)
### LogWriter
Primary class responsible for:
- Writing content to appropriate log files
- Handling token-based log path resolution
- Managing application logging
- Handling file I/O operations

### LoggingService
Orchestrates the logging process:
- Coordinates between command execution and log writing
- Manages log lifecycle events
- Handles error conditions in logging

### FbcCommandService / RpcCommandService
Protocol-specific services that:
- Generate appropriate commands for their protocol
- Interface with LogWriter for log management
- Handle protocol-specific formatting and processing

## Key Methods (LogWriter) | Method | Init/Params | Desc |
|--------|-------------|------|
| LogWriter | node_manager, log_root="logs" | Setup dirs, app_logger |
| write_to_log | content, log_type, node_name=None, token=None | Write to file, derive path, emit signal |
| write_to_app_log | message, level=INFO | App log |
| write_clipboard_content | content, log_type | Delegate write_to_log |
| clear_log | token_id | Clear token path |

## Processing Rules | Rule | Detail |
|------|---------|
| 1 | Tokens from filename pre-ext | ✅Extract |
| 2 | Node [A-Z0-9]+ | ✅Validate |
| 3 | IP dotted/dashed | ✅Format |
| 4 | Port numeric | ✅Type |

## Performance Considerations
- Direct file writing without keeping handles open
- Efficient path resolution using token attributes
- Memory-efficient handling of multiple concurrent logs

## Error Handling
- Graceful handling of file I/O errors
- Comprehensive logging of error conditions to application log
- Fallback behavior for inaccessible log directories

## LogReportGUI Logging Setup | Step | Detail |
|------|---------|
| Format | %(asctime)s - %(name)s - %(levelname)s - %(message)s | ✅Standard |
| Dir | logs/ if not exist | ✅Auto |
| Root logger | DEBUG+ | ✅Capture |
| Console handler | sys.stdout | ✅Display |
| File handler | application.log | ✅Persist |

Ensures events from LogProcessor/ReportGenerator logged console/file ✅Traceable

## Debugging Strategy | Step | Action | Tool |
|------|--------|------|
| 1 | Check application.log | Errors | Logs |
| 2 | Verify token attrs | Set | Inspect |
| 3 | Confirm dir perms | Access | OS |
| 4 | Review naming test_logs | Patterns | List |

## Best Practices | Practice | Benefit |
|----------|---------|
| Pass tokens | Accurate path | ✅ |
| Handle exceptions | Robust | ✅ |
| Use app_log debug | Trace | ✅ |
| Check application.log | Monitor | ✅ |

## Codebase Sync | Component | Ref | Detail |
|----------|-----|---------|
| LogWriter | [src/commander/log_writer.py:16-245](src/commander/log_writer.py:16) | __init__ [22-50], write_to_log [51-142], signals [20], line_count [223-245] |
| Queue Int | command_completed_with_log_status → log_write_completed [src/commander/command_queue.py:148](src/commander/command_queue.py:148) | ✅Link |
| App Log | application.log [src/commander/log_writer.py:39-49](src/commander/log_writer.py:39) | ✅Handler |

## Codebase Sync (Additional Preserved Refs)
- LogWriter: [src/commander/log_writer.py:51](src/commander/log_writer.py:51)
- CommandQueue: [src/commander/command_queue.py:1](src/commander/command_queue.py:1)
- Recent Changes: [ROADMAP_recent_changes_v1 #Overview](docs/roadmaps/ROADMAP_recent_changes_v1.md#Overview)
- ARCH_logging_system_v1.md (self-ref for overview)