# TECH_api_token_utilities_v1.md

## Overview

The Token Utilities module provides comprehensive token normalization, validation, and processing functions for the LOGReport Commander application, ensuring consistent token handling across the system.

## Specs

### TokenValidator Class

**Purpose**: Core token validation and normalization.

| Method | Description | Parameters | Returns |
|---|---|---|---|
| `normalize_token` | Normalizes token string with caching. | `token` (str) | `str` |
| `validate_token` | Validates token against standard pattern. | `token` (str) | `bool` |
| `is_fbc_token` | Checks if token is FBC type (`^\d{3}[a-z]?$`). | `token` (str) | `bool` |
| `is_rpc_token` | Checks if token is RPC type (`^[a-z0-9]+$` & not FBC). | `token` (str) | `bool` |
| `validate_token_node` | Validates token's node information. | `token` (NodeToken), `node_name` (str, optional) | `bool` |

**Normalization Rules**:
- **FBC**: 3-digit numeric padded with zeros; alphanumeric to uppercase.
- **RPC**: Lowercase; non-alphanumeric removed.
- **LOG/LIS**: Basic lowercase with character filtering.
- **Numeric**: Padded to 3 digits with leading zeros.

**Validation Rules**:
- Matches `^[a-zA-Z0-9]+$`.
- Not empty, must be string.

### TokenRateLimiter Class

**Purpose**: Rate limiting for token processing.

| Method | Description | Parameters | Returns |
|---|---|---|---|
| `is_allowed` | Checks if processing is allowed. | None | `bool` |
| `get_wait_time` | Gets time to wait before next token. | None | `float` |

### Singleton Instances

- `token_validator`: `TokenValidator` instance for global use.
- `token_rate_limiter`: `TokenRateLimiter` instance for global use.

## Examples

### Basic Token Operations

```python
from src.commander.utils.token_utils import normalize_token, is_fbc_token, is_rpc_token

# Normalize & check types
fbc_token = normalize_token("162")      # "162"
rpc_token = normalize_token("abc123")   # "abc123"
log_token = normalize_token("LOG001")   # "log001"

print(is_fbc_token("162"))      # True
print(is_rpc_token("abc123"))   # True
print(is_fbc_token("abc123"))   # False
```

### Token Validation

```python
from src.commander.utils.token_utils import validate_token, validate_token_node

# Validate format
is_valid = validate_token("162")  # True
is_invalid = validate_token("16-2")  # False

# Validate node info (MockToken for example)
class MockToken:
    def __init__(self, ip, token_id, name):
        self.ip_address = ip
        self.token_id = token_id
        self.name = name

token = MockToken("192.168.1.1", "162", "TEST_NODE")
is_valid_node = validate_token_node(token, "TEST_NODE")  # True
```

### Rate Limiting

```python
from src.commander.utils.token_utils import is_token_processing_allowed, get_token_processing_wait_time
import time # Added import for time.sleep

if is_token_processing_allowed():
    # Process token
    pass # Placeholder for actual processing
else:
    wait_time = get_token_processing_wait_time()
    time.sleep(wait_time)
```

## Troubleshooting

### Error Handling

- **Type Errors**: Input type validation.
- **Value Errors**: Handles invalid token formats.
- **Attribute Errors**: Checks for required attributes.
- **Logging**: All errors logged with severity.

### Performance Considerations

- **Caching**: `normalize_token` uses LRU caching.
- **Rate Limiting**: Prevents excessive processing.
- **Regex**: Compiled patterns for efficiency.
- **String Ops**: Optimized string processing.

### Integration with NodeManager

Seamless integration with `NodeManager` for token handling.

```python
from src.commander.node_manager import NodeManager
from src.commander.utils.token_utils import normalize_token

nm = NodeManager()
nm.load_configuration("nodes.json")

node = nm.get_node("TEST_NODE")
if node:
    for token in node.tokens.values():
        print(f"Token: {token.token_id} (Type: {token.token_type})")
```

### Testing

Comprehensive test coverage: unit, integration, performance, error handling.

**Run Tests**: `python -m pytest tests/test_token_utils.py -v`

## Version History

- **v1.0.0**: Initial implementation.
- **v1.1.0**: Caching & rate limiting.
- **v1.2.0**: Enhanced validation & error handling.
- **v1.3.0**: Fixed circular import dependencies.
- **v1.4.0**: Comprehensive documentation & testing.

## Future Enhancements

- **Custom Token Types**: Extensible system.
- **Performance Metrics**: Built-in monitoring.
- **Configuration Schema**: JSON schema validation.
- **Migration Tools**: Automated format migration.