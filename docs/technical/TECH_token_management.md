# 🔑 Token Management System

<!-- METADATA -->
metadata: {
  created_date: "2025-10-08_164500",
  last_modified: "2025-10-08_164500",
  last_accessed: "2025-10-08_164500",
  word_count: 2456,
  reference_count: 4,
  document_hash: "token_mgmt_tech_consolidated",
  obsolete_check_date: "2025-10-08",
  section_count: 7,
  internal_link_count: 18
}
<!-- /METADATA -->

## 📑 Table of Contents

- [Overview](#overview)
- [Token Processing Architecture](#token-processing-architecture)
- [Hybrid Token Resolution](#hybrid-token-resolution)
- [SYS File Parsing](#sys-file-parsing)
- [Token ID Extraction](#token-id-extraction)
- [API Token Utilities](#api-token-utilities)
- [Integration & Usage](#integration--usage)

---

## 🎯 Overview

The Token Management System provides comprehensive token handling for the LOGReport application, including token resolution, SYS file parsing, token ID extraction, and API utilities. The system supports multiple token types (FBC, RPC, LIS) with intelligent fallback mechanisms and hybrid resolution.

### Key Features

| Feature | Description | Benefit |
|---------|-------------|---------|
| **Hybrid Resolution** | FBC tokens can execute RPC commands | Increased flexibility |
| **SYS File Parsing** | Extract tokens from .sys configuration files | Automatic token discovery |
| **Token ID Extraction** | Parse token IDs from various formats | Robust data handling |
| **Config Parser Logic** | Intelligent token attribute parsing | Accurate metadata extraction |
| **API Utilities** | Helper functions for token operations | Simplified integration |

### System Scope

- **Primary Use**: Token resolution and metadata management
- **Secondary Use**: SYS file parsing and token discovery
- **Integration**: Works with [Node System](ARCH_node_system.md#token-management-integration), [Command System](ARCH_command_system.md#token-based-execution), and [Logging System](ARCH_logging_system.md#token-based-path-resolution)

---

## 🏗️ Token Processing Architecture

Token processing follows a layered architecture with clear separation of concerns:

```
┌─────────────────────────────────────────────┐
│            Token Sources                     │
│  SYS Files | nodes.json | Log Files         │
└──────────────────┬──────────────────────────┘
                   │
         ┌─────────▼────────┐
         │  Token Parser    │
         │  - SYS Parser    │
         │  - ID Extractor  │
         │  - Config Parser │
         └─────────┬────────┘
                   │
         ┌─────────▼────────┐
         │  Token Registry  │
         │  (NodeManager)   │
         └─────────┬────────┘
                   │
         ┌─────────▼────────┐
         │ Token Resolver   │
         │ - Exact Match    │
         │ - Hybrid FBC→RPC │
         │ - Fallback       │
         └─────────┬────────┘
                   │
         ┌─────────▼────────┐
         │  Token Consumer  │
         │  (Command Svcs)  │
         └──────────────────┘
```

### Token Object Model

```python
@dataclass
class NodeToken:
    """
    Complete token representation with metadata.
    
    Attributes:
        token_id: Unique token identifier (string)
        protocol: Token protocol type ('FBC' | 'RPC' | 'LIS')
        node_name: Associated node name
        ip_address: Target IP address for communication
        port: Communication port (default: 23 for telnet)
        log_path: Path to associated log file
        sys_path: Path to source .sys file (if parsed from SYS)
        metadata: Additional token-specific data
    """
    token_id: str
    protocol: str
    node_name: str
    ip_address: Optional[str] = None
    port: Optional[int] = None
    log_path: Optional[str] = None
    sys_path: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate and normalize token data."""
        # Normalize protocol
        self.protocol = self.protocol.upper()
        
        # Set default port if not specified
        if self.port is None:
            self.port = 23  # Default telnet port
        
        # Validate IP address format
        if self.ip_address and not self._is_valid_ip(self.ip_address):
            logging.warning(f"Invalid IP address format for token {self.token_id}: {self.ip_address}")
    
    def _is_valid_ip(self, ip: str) -> bool:
        """Validate IP address format."""
        try:
            parts = ip.split('.')
            return len(parts) == 4 and all(0 <= int(p) <= 255 for p in parts)
        except (ValueError, AttributeError):
            return False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert token to dictionary representation."""
        return {
            'token_id': self.token_id,
            'protocol': self.protocol,
            'node_name': self.node_name,
            'ip_address': self.ip_address,
            'port': self.port,
            'log_path': self.log_path,
            'sys_path': self.sys_path,
            'metadata': self.metadata
        }
```

---

## 🔄 Hybrid Token Resolution

The hybrid resolution system allows FBC tokens to be used for RPC commands when dedicated RPC tokens are unavailable.

### Resolution Algorithm

```python
def resolve_token(node_name: str, token_id: str, target_protocol: str) -> NodeToken:
    """
    Multi-stage token resolution with hybrid support.
    
    Resolution Stages:
    1. Exact Match: Look for token with matching ID and protocol
    2. Normalized Match: Try integer-normalized ID (strip leading zeros)
    3. Hybrid Resolution: If target is RPC, try FBC token
    4. Fallback: Create temporary token from node metadata
    
    Args:
        node_name: Node name to search
        token_id: Token ID to resolve
        target_protocol: Desired protocol ('FBC' or 'RPC')
    
    Returns:
        Resolved NodeToken object
    
    Raises:
        TokenResolutionError: If token cannot be resolved
    """
    node = node_manager.get_node(node_name)
    if not node:
        raise TokenResolutionError(f"Node not found: {node_name}")
    
    # Stage 1: Exact match
    token = node.get_token(target_protocol, token_id)
    if token:
        logging.debug(f"Token resolved (exact match): {node_name}:{token_id}")
        return token
    
    # Stage 2: Normalized match (handle leading zeros)
    if token_id.isdigit():
        normalized_id = str(int(token_id))
        if normalized_id != token_id:
            token = node.get_token(target_protocol, normalized_id)
            if token:
                logging.debug(f"Token resolved (normalized): {node_name}:{normalized_id}")
                return token
    
    # Stage 3: Hybrid resolution (FBC → RPC)
    if target_protocol == 'RPC':
        fbc_token = node.get_token('FBC', token_id)
        if fbc_token:
            # Create RPC token from FBC metadata
            rpc_token = NodeToken(
                token_id=fbc_token.token_id,
                protocol='RPC',
                node_name=node_name,
                ip_address=fbc_token.ip_address or node.ip_address,
                port=fbc_token.port or 23,
                metadata={
                    **fbc_token.metadata,
                    'source': 'hybrid_fbc_to_rpc',
                    'original_protocol': 'FBC'
                }
            )
            logging.info(f"Token resolved (hybrid FBC→RPC): {node_name}:{token_id}")
            return rpc_token
    
    # Stage 4: Fallback - create temporary token
    if node.ip_address:
        temp_token = NodeToken(
            token_id=token_id,
            protocol=target_protocol,
            node_name=node_name,
            ip_address=node.ip_address,
            port=23,
            metadata={'source': 'fallback_temporary'}
        )
        logging.warning(f"Token resolved (fallback): {node_name}:{token_id}")
        return temp_token
    
    # No resolution possible
    raise TokenResolutionError(
        f"Cannot resolve token {token_id} for node {node_name}: "
        f"No {target_protocol} token, no hybrid option, and no node IP"
    )
```

### Resolution Benefits

- ✅ **Flexibility**: Reduces need for duplicate token definitions
- ✅ **Reliability**: Multiple fallback options prevent failures
- ✅ **Compatibility**: Supports legacy configurations with limited token definitions
- ✅ **Transparency**: Logging tracks resolution method used

---

## 📄 SYS File Parsing

SYS files contain node and token configuration data that can be automatically parsed.

### SYS File Format

```
# Example .sys file format
NODE_NAME=AP01m
IP_ADDRESS=192.168.0.11
FBC_TOKENS=12345,12346,12347
RPC_TOKENS=67890,67891
PORT=23
PROTOCOL=FBC

# Token-specific sections
[TOKEN_12345]
TYPE=FBC
IP=192.168.0.11
PORT=23
DESCRIPTION=Main fieldbus token

[TOKEN_67890]
TYPE=RPC
IP=192.168.0.11
PORT=23
DESCRIPTION=RPC interface token
```

### SYS Parser Implementation

```python
class SysFileParser:
    """Parse .sys configuration files to extract tokens."""
    
    def __init__(self):
        self.tokens: List[NodeToken] = []
        self.node_info: Dict[str, Any] = {}
    
    def parse_file(self, filepath: str) -> Tuple[Dict[str, Any], List[NodeToken]]:
        """
        Parse .sys file and extract node info and tokens.
        
        Args:
            filepath: Path to .sys file
        
        Returns:
            Tuple of (node_info dict, list of NodeToken objects)
        """
        self.tokens = []
        self.node_info = {}
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Parse global node info
            self._parse_node_info(content)
            
            # Parse token sections
            self._parse_token_sections(content, filepath)
            
            # Parse comma-separated token lists
            self._parse_token_lists(content, filepath)
            
            return self.node_info, self.tokens
        
        except FileNotFoundError:
            logging.error(f"SYS file not found: {filepath}")
            return {}, []
        except Exception as e:
            logging.error(f"Error parsing SYS file {filepath}: {str(e)}")
            return {}, []
    
    def _parse_node_info(self, content: str):
        """Extract global node information."""
        patterns = {
            'node_name': r'NODE_NAME\s*=\s*(\S+)',
            'ip_address': r'IP_ADDRESS\s*=\s*(\S+)',
            'port': r'PORT\s*=\s*(\d+)',
            'protocol': r'PROTOCOL\s*=\s*(\S+)'
        }
        
        for key, pattern in patterns.items():
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                value = match.group(1)
                if key == 'port':
                    value = int(value)
                self.node_info[key] = value
    
    def _parse_token_sections(self, content: str, sys_path: str):
        """Parse [TOKEN_xxxxx] sections."""
        token_pattern = r'\[TOKEN_(\w+)\](.*?)(?=\[TOKEN_|\Z)'
        matches = re.findall(token_pattern, content, re.DOTALL | re.IGNORECASE)
        
        for token_id, section_content in matches:
            token_data = self._parse_token_section_content(section_content)
            
            token = NodeToken(
                token_id=token_id,
                protocol=token_data.get('type', 'FBC').upper(),
                node_name=self.node_info.get('node_name', 'UNKNOWN'),
                ip_address=token_data.get('ip') or self.node_info.get('ip_address'),
                port=int(token_data.get('port', 23)),
                sys_path=sys_path,
                metadata={'description': token_data.get('description', '')}
            )
            self.tokens.append(token)
    
    def _parse_token_section_content(self, section: str) -> Dict[str, str]:
        """Parse key=value pairs in token section."""
        data = {}
        for line in section.split('\n'):
            line = line.strip()
            if '=' in line and not line.startswith('#'):
                key, value = line.split('=', 1)
                data[key.strip().lower()] = value.strip()
        return data
    
    def _parse_token_lists(self, content: str, sys_path: str):
        """Parse comma-separated token lists (FBC_TOKENS, RPC_TOKENS)."""
        list_patterns = {
            'FBC': r'FBC_TOKENS\s*=\s*([\d,\s]+)',
            'RPC': r'RPC_TOKENS\s*=\s*([\d,\s]+)'
        }
        
        for protocol, pattern in list_patterns.items():
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                token_ids = [t.strip() for t in match.group(1).split(',') if t.strip()]
                for token_id in token_ids:
                    # Only add if not already added from [TOKEN_xxx] section
                    if not any(t.token_id == token_id for t in self.tokens):
                        token = NodeToken(
                            token_id=token_id,
                            protocol=protocol,
                            node_name=self.node_info.get('node_name', 'UNKNOWN'),
                            ip_address=self.node_info.get('ip_address'),
                            port=int(self.node_info.get('port', 23)),
                            sys_path=sys_path
                        )
                        self.tokens.append(token)
```

### SYS File Usage

```python
# Parse SYS file and populate node manager
parser = SysFileParser()
node_info, tokens = parser.parse_file('/path/to/node.sys')

# Create or update node
node_name = node_info.get('node_name')
node = node_manager.get_node(node_name)
if not node:
    node = Node(
        name=node_name,
        ip_address=node_info.get('ip_address'),
        status='offline'
    )
    node_manager.add_node(node)

# Add tokens to node
for token in tokens:
    node.add_token(token.protocol, token.token_id)
    # Update token with parsed metadata
    node_token = node.get_token(token.protocol, token.token_id)
    node_token.ip_address = token.ip_address
    node_token.port = token.port
    node_token.sys_path = token.sys_path
    node_token.metadata = token.metadata
```

---

## 🔍 Token ID Extraction

Token ID extraction handles various input formats and normalizes them.

### Extraction Patterns

```python
class TokenIdExtractor:
    """Extract and normalize token IDs from various formats."""
    
    @staticmethod
    def extract_from_filename(filename: str) -> Optional[str]:
        """
        Extract token ID from log filename.
        
        Supported patterns:
        - NODE_IP_TOKEN.ext → TOKEN
        - NODE_TOKEN.ext → TOKEN
        - TOKEN.ext → TOKEN (if numeric)
        
        Examples:
            "AP01m_192.168.0.11_12345.fbc" → "12345"
            "AP01m_12345.rpc" → "12345"
            "12345.fbc" → "12345"
        """
        # Pattern 1: Full format with IP and token
        match = re.search(r'_(\d+)\.\w+$', filename)
        if match:
            return match.group(1)
        
        # Pattern 2: Numeric filename
        base = os.path.splitext(filename)[0]
        if base.isdigit():
            return base
        
        # Pattern 3: Last numeric segment before extension
        parts = base.split('_')
        if parts and parts[-1].isdigit():
            return parts[-1]
        
        return None
    
    @staticmethod
    def extract_from_config_line(line: str) -> List[str]:
        """
        Extract token IDs from configuration line.
        
        Handles:
        - Comma-separated lists: "12345,12346,12347"
        - Space-separated lists: "12345 12346 12347"
        - Single tokens: "12345"
        - Mixed: "12345, 12346 12347"
        """
        # Remove key=value prefix if present
        if '=' in line:
            line = line.split('=', 1)[1]
        
        # Split by comma or space
        tokens = re.split(r'[,\s]+', line.strip())
        
        # Filter numeric tokens only
        return [t.strip() for t in tokens if t.strip().isdigit()]
    
    @staticmethod
    def normalize_token_id(token_id: str) -> str:
        """
        Normalize token ID format.
        
        Rules:
        - Strip leading zeros: "00123" → "123"
        - Strip whitespace
        - Convert to string if needed
        
        Args:
            token_id: Raw token ID
        
        Returns:
            Normalized token ID string
        """
        if not token_id:
            return ""
        
        # Convert to string
        token_str = str(token_id).strip()
        
        # Strip leading zeros but keep "0" if it's just "0"
        if token_str.isdigit():
            return str(int(token_str))
        
        return token_str
```

---

## 🔧 API Token Utilities

Utility functions for common token operations.

### Token Utilities

```python
class TokenUtils:
    """Utility functions for token operations."""
    
    @staticmethod
    def format_token_key(token_id: str, protocol: str) -> str:
        """
        Create composite key for token lookup.
        
        Format: "PROTOCOL:TOKEN_ID"
        Example: "FBC:12345"
        """
        return f"{protocol.upper()}:{token_id}"
    
    @staticmethod
    def parse_token_key(key: str) -> Tuple[str, str]:
        """
        Parse composite token key.
        
        Args:
            key: Composite key (e.g., "FBC:12345")
        
        Returns:
            Tuple of (protocol, token_id)
        """
        if ':' in key:
            protocol, token_id = key.split(':', 1)
            return protocol.upper(), token_id
        return 'FBC', key  # Default to FBC if no protocol
    
    @staticmethod
    def validate_token_metadata(token: NodeToken) -> List[str]:
        """
        Validate token has required metadata.
        
        Returns:
            List of validation error messages (empty if valid)
        """
        errors = []
        
        if not token.token_id:
            errors.append("Missing token_id")
        
        if not token.protocol:
            errors.append("Missing protocol")
        elif token.protocol not in ['FBC', 'RPC', 'LIS']:
            errors.append(f"Invalid protocol: {token.protocol}")
        
        if not token.node_name:
            errors.append("Missing node_name")
        
        if token.ip_address and not token._is_valid_ip(token.ip_address):
            errors.append(f"Invalid IP address: {token.ip_address}")
        
        if token.port and (token.port < 1 or token.port > 65535):
            errors.append(f"Invalid port: {token.port}")
        
        return errors
    
    @staticmethod
    def tokens_equal(token1: NodeToken, token2: NodeToken) -> bool:
        """
        Compare two tokens for equality.
        
        Tokens are equal if they have same token_id, protocol, and node_name.
        """
        return (
            token1.token_id == token2.token_id and
            token1.protocol == token2.protocol and
            token1.node_name == token2.node_name
        )
    
    @staticmethod
    def merge_token_metadata(
        target: NodeToken, 
        source: NodeToken
    ) -> NodeToken:
        """
        Merge metadata from source token into target token.
        
        Rules:
        - Keep target's existing non-None values
        - Fill in missing values from source
        - Merge metadata dictionaries
        """
        if not target.ip_address and source.ip_address:
            target.ip_address = source.ip_address
        
        if not target.port and source.port:
            target.port = source.port
        
        if not target.log_path and source.log_path:
            target.log_path = source.log_path
        
        if not target.sys_path and source.sys_path:
            target.sys_path = source.sys_path
        
        # Merge metadata dicts
        target.metadata = {**source.metadata, **target.metadata}
        
        return target
```

---

## 🔗 Integration & Usage

### Command Service Integration

```python
class FbcCommandService:
    """FBC command service with token management."""
    
    def execute_command(self, node_name: str, token_id: str):
        """Execute FBC command using token resolution."""
        # Resolve token
        token = resolve_token(node_name, token_id, 'FBC')
        
        # Validate token
        errors = TokenUtils.validate_token_metadata(token)
        if errors:
            raise ValueError(f"Invalid token: {', '.join(errors)}")
        
        # Execute command
        result = self._execute_fbc(token)
        
        # Log to token-specific log file
        log_writer.write(result, token, 'fbc')
```

### Token Discovery Workflow

```python
# 1. Load from configuration
node_manager.load_configuration()

# 2. Parse SYS files
for sys_file in glob.glob('*.sys'):
    parser = SysFileParser()
    node_info, tokens = parser.parse_file(sys_file)
    # Add to node manager...

# 3. Scan log files
node_manager.scan_log_files(log_root)

# 4. Resolve IPs dynamically
node_manager._scan_for_dynamic_ips(log_root)
```

---

## 📚 References

### Related Documentation

- **[Node System](ARCH_node_system.md)** - Node and token registry
- **[Command System](ARCH_command_system.md)** - Token-based command execution
- **[Logging System](ARCH_logging_system.md)** - Token-based log paths

### Source Code

- **Token Model**: `src/models/node_token.py`
- **SYS Parser**: `src/parsers/sys_file_parser.py`
- **Token Utilities**: `src/utils/token_utils.py`
- **Hybrid Resolution**: `src/services/rpc_command_service.py`

---

**Document Status**: ✅ **COMPLETE** - Consolidated from 9 source documents
**Last Updated**: 2025-10-08
**Consolidation**: token_processing.md + hybrid_token_resolution.md + sys_file_parsing.md + 6 others
**Next Review**: 2026-01-08 (90 days)
