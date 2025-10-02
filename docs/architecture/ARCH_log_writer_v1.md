---
metadata:
  created_date: "2025-10-02_000000"
  last_modified: "2025-10-02T17:00:00Z"
  word_count: 250
  reference_count: 0
  document_hash: "md5:log_writer_v1_hash"
  obsolete_check_date: "2025-10-02"
---

# Log Writer Documentation ✅Standardized

## Overview | Feature | Status |
|----------|--------|
| Log creation/writing | ✅Managed |
| Standardized formats | ✅Supported |

## Key Features | Feature | Benefit |
|----------|---------|
| Standardized log files | ✅Consistent |
| Command output append | ✅Traceable |
| File rotation | ✅Size control |
| Multi-type support (FBC/RPC/LOG/LIS) | ✅Versatile |
| Token-based path res | ✅Context-aware |

## Log File Naming | Type | Format | Example |
|------|--------|---------|
| FBC | {node}_{ip}_{token}.fbc | AP01m_192-168-0-11_162.fbc |
| RPC | {node}_{ip}_{token}.rpc | AP01r_192-168-0-27_363.rpc |
| LOG | {node}_{ip}.log or {node}_{ip}_{token}.log | AL01_186_LOG.log |
| LIS | {node}_{ip}_{token}.lis | AL01_186_LIS.lis |

## Directory Structure | Type | Path |
|------|------|
| FBC | {log_root}/FBC/{node}/ |
| RPC | {log_root}/RPC/{node}/ |
| LOG | {log_root}/LOG/ |
| LIS | {log_root}/LIS/{node}/ |

## Important Methods | Method | Desc | Params |
|--------|------|---------|
| write_to_log | Write to log file, token path if avail | content, log_type, node_name=None, token=None |
| write_to_app_log | App log write | message, level=INFO |
| write_clipboard_content | Clipboard to log | content, log_type |
| clear_log | Clear token logs | token_id |

## Log Formatting | Aspect | Detail |
|--------|---------|
| Timestamp | Each entry | ✅Prefixed |
| Original output | Preserved | ✅Intact |
| Line endings | Consistent | ✅Uniform |
| Metadata headers | When appropriate | ✅Added |

## Token Integration | Case | Logic | Symbol |
|------|--------|--------|
| Token w/ log_path | Use direct | ✅Precise |
| Token w/ token_id/ip | Generate filename | ✅Derived |
| No token info | Fallback naming | ⚠️Basic |