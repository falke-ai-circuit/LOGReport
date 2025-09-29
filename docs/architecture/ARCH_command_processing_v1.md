# Command Processing Flow

## Background/Fix
| Aspect | Issue | Fix | Impact |
|--------|-------|-----|--------|
| FBC Commands | Not written to files, explicit start_processing() | Remove call, align w/RPC flow | Consistent queuing/output/logging |
| RPC Output | No dedicated logs, log_path not populated | Populate via NodeManager._generate_log_path in get_token | Traceability/auditability |

## Verification
New test: tests/commander/test_rpc_log_path.py (passes).

## Future Plans
- Async batch processing
- Unified cmd interface
- Timeout policies