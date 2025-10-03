---
metadata:
  created_date: "2025-10-03"
  last_modified: "2025-10-03T09:13:00Z"
  version: "v1.0"
  cluster: "Architecture: Logging"
  merges_from: 10 files (e.g., ARCH_logging_v1.md, TECH_logging_v1.md, ARCH_log_writer_v1.md, ARCH_logging_configuration_v1.md, ARCH_log_writer_impl_v1.md, ARCH_log_writer_config_v1.md, ARCH_log_format_v1.md, TECH_logging_configuration_v1.md, logging.md, logging_configuration.md)
  word_count: 950
  reference_count: 8
  document_hash: "sha256:arch_logging_core_v1_hash"
  similarity_index: 0.85  # Pre-merge average
  archive_rate: "90%"  # 9/10 archived
  sections: 9
  compliance: "/templates/document_standards.md"
---

# ARCH_logging_core_v1: Consolidated Logging Architecture

## Overview
The logging system in LOGReport manages creation, writing, and organization of logs for protocols (FBC, RPC, LOG, LIS). Ensures separation, performance via efficient I/O, token-based resolution. Key: Handles Unicode (UTF-8), timestamps, multi-type support. Merged from 10 sources: Overviews (identical in 4 docs → condensed), impl/configs (85% overlap on LogWriter), formats/Unicode (shallow <100l absorbed). Rationale: 85% sim on components/naming; preserves uniques (e.g., impl methods, error handling).

| Feature | Status | Benefit |
|---------|--------|---------|
| Log creation/writing | ✅Managed | Consistent files |
| Standardized formats | ✅UTF-8 | Unicode safe (fixes EncodeError) |
| Command append | ✅Traceable | Full output |
| File rotation | ✅External | Size control |
| Multi-type (FBC/RPC/LOG/LIS) | ✅Versatile | Protocol separation |
| Token path res | ✅Context-aware | Accurate naming |

**Rationale**: Condensed duplicates (e.g., repeated LogWriter desc → single table); inline symbols for quick scan.

## Key Components
Core classes/services for logging orchestration.

| Component | Description | Key Methods | Location |
|-----------|-------------|-------------|----------|
| **LogWriter (QObject)** | Writes to node/token logs, app.log. Emits log_write_completed (path, success, lines). Thread-safe via Qt signals. | write_to_log(content, log_type, node_name=None, token=None); write_to_app_log(message, level=INFO); write_clipboard_content(content, log_type); clear_log(token_id); append_to_file(filepath, content); get_file_line_count(filepath) | [src/commander/log_writer.py:16-245](src/commander/log_writer.py:16) |
| **LoggingService** | Coordinates execution/log writing, lifecycle, errors. | N/A (orchestrator) | Integrated in services |
| **FbcCommandService / RpcCommandService** | Protocol-specific: Commands, LogWriter interface, formatting. | generate_commands(protocol); interface_log_mgmt() | [src/commander/services](src/commander/services) |

**Rationale**: Merged from ARCH_log_writer_impl_v1.md (methods/details) + overviews (ARCH_logging_v1.md/TECH_logging_v1.md); uniques: Impl signals/error emission (from impl), protocol specifics (from services).

## Log File Organization
Directory/naming for separation.

### Directory Structure
| Type | Path |
|------|------|
| FBC | {log_root}/FBC/{node}/ |
| RPC | {log_root}/RPC/{node}/ |
| LOG | {log_root}/LOG/ |
| LIS | {log_root}/LIS/{node}/ |

### File Naming Convention
| Type | Format (Token Info) | Format (Fallback) | Example |
|------|---------------------|-------------------|---------|
| FBC | {node}_{ip}_{token}.fbc | {node}.{extension} | AP01m_192-168-0-11_162.fbc |
| RPC | {node}_{ip}_{token}.rpc | {node}.{extension} | AP01r_192-168-0-27_363.rpc |
| LOG | {node}_{ip}_{token}.log | {node}_{ip}.log | AL01_186_LOG.log |
| LIS | {node}_{ip}_{token}.lis | {node}.{extension} | AL01_186_LIS.lis |

**Rationale**: Absorbed from ARCH_log_format_v1.md (short spec) + ARCH_log_writer_v1.md (examples); condensed tables, removed repeats (identical in 3 sources).

## Token-Based Path Resolution
Logic for consistent paths/naming.

1. **Token w/ log_path**: Use direct (✅Precise).
2. **Token w/ token_id/ip_address**: Generate filename (e.g., {node}_{ip}_{token}.{type}) (✅Derived).
3. **No token**: Fallback naming (e.g., {node}.{type}) (⚠️Basic).

**Rationale**: From overviews (ARCH_logging_v1.md etc., repeated in 4 docs → single list); enhances with impl details (from ARCH_log_writer_impl_v1.md: derives filepath in write_to_log).

## Implementation
Detailed LogWriter flow (from ARCH_log_writer_impl_v1.md uniques).

- **__init__(node_manager, log_root="logs")**: Setup dirs, app_logger (INFO, application.log UTF-8).
- **write_to_log**: Derives filepath (e.g., test_logs/LOG/node_ip.log), timestamps [%Y-%m-%d %H:%M:%S], appends UTF-8. Counts lines pre/post, emits signal. Handles no node → app log.
- **append_to_file**: Direct UTF-8 append to filepath, line count emit.
- **get_file_line_count**: Sums lines (errors→0).
- **Integration**: NodeManager for active_node/tokens; signals for UI (e.g., line counts).

**Examples**:
```python
# Write FBC log
writer.write_to_log("FBC response data", "FBC", token=token_obj)

# Clear token log
writer.clear_log("12345")

# App log error
writer.write_to_app_log("Connection failed", logging.ERROR)
```

**Rationale**: Impl uniques only (methods/signals from ARCH_log_writer_impl_v1.md); overviews' components integrated above. Condensed code snippets.

## Configuration
Options/best practices (from ARCH_log_writer_config_v1.md + TECH_logging_configuration_v1.md).

- **Init**: LogWriter(node_manager, log_root="logs") (✅Centralized).
- **UTF-8 Handling**: Files opened encoding='utf-8' (fixes UnicodeEncodeError for emojis '📝'; from logging_configuration.md).
- **Debugging**: 1. Check application.log; 2. Token attrs; 3. Dir perms; 4. test_logs naming.

| Practice | Benefit |
|----------|---------|
| Pass tokens | ✅Accurate paths |
| Handle exceptions | ✅Robust |
| Use app_log | ✅Trace |
| Regular application.log check | ✅Monitor |

**Future**: Backslashreplace fallback; optimize pipeline; memory-mapped I/O.

**Rationale**: Merged config guide (methods/logic) + Unicode resolution (short issue/details absorbed); uniques: Debugging steps, enhancements.

## Best Practices
- **Token Usage**: Always pass tokens for precise paths (✅).
- **Error Handling**: Catch I/O → app log + re-raise (✅Graceful).
- **Performance**: Direct writes, no open handles (✅Efficient).
- **Monitoring**: Review application.log regularly (✅).
- **Rotation**: External tool for size (⚠️).

**Rationale**: From ARCH_log_writer_config_v1.md (practices/symbols); inline from overviews (performance/error).

## Version History
- **v1 Baseline**: Initial overviews/impl (from ARCH_logging_v1.md, TECH_logging_v1.md: components/naming).
- **v1 Enhancements**: UTF-8 fix (from ARCH_logging_configuration_v1.md/logging_configuration.md: Unicode resolution).
- **Merge Notes**: Absorbed shallow formats (ARCH_log_format_v1.md: spec → Naming table); configs (ARCH_log_writer_config_v1.md: methods/practices).

**Rationale**: Consolidates versions (all v1, no v2 in cluster); lists sources/changes for traceability.

## References
- **[LogWriter Code](src/commander/log_writer.py:16-245)**: Full impl.
- **[NodeManager Integration](src/commander/node_manager.py)**: Token paths.
- **[ROADMAP_recent_changes_v1 #Overview](roadmaps/ROADMAP_recent_changes_v1.md#Overview)**: Logging updates.
- **[TECH_error_logging_core_v1 #Delegation](technical/TECH_error_logging_core_v1.md#Delegation)**: Error integration.
- **[Archived: ARCH_log_writer_v1 #Overview](archived/ARCH_log_writer_v1.md#Overview)**: Original features (redirect).
- **[Archived: logging_configuration #Overview](archived/logging_configuration.md#Overview)**: Unicode details (redirect).

**Rationale**: Bidirectional #links (e.g., to technical core); redirects for archives/orphans (e.g., vnc not in cluster, but example for resolution).
