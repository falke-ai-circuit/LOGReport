---
metadata:
  created_date: "2025-10-02_000000"
  last_modified: "2025-10-02T17:00:00Z"
  word_count: 120
  reference_count: 0
  document_hash: "md5:log_format_hash"
  obsolete_check_date: "2025-10-02"
---

# Log File Format Specification

## Structure
| Aspect | Details |
|--------|---------|
| Directory | log_root/LOG/ |
| Naming | {node.name}_*.log |
| Optimizations | Centralized parsing, token extract (no ext), validation |

## Examples
| Format | Example |
|--------|---------|
| FBC | AP01m_192-168-0-11_162.fbc |
| RPC | AP01r_192-168-0-27_363.rpc |
| Standard | AL01_186_LOG.log |

## Processing Rules
1. Tokens from filename pre-ext
2. Node: [A-Z0-9]+
3. IP: dotted/dashed
4. Port: numeric

## Test Coverage
| Type | Details |
|------|---------|
| Unit | Parsing utils |
| Integration | Full pipeline |
| Coverage | 100% filename logic |