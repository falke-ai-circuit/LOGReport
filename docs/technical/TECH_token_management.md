# 🔑 Token Management System

<!-- METADATA -->
metadata: {
  created_date: "2025-10-08_164500",
  last_modified: "2025-10-08_180000",
  last_accessed: "2025-10-08_180000",
  word_count: 3200,
  reference_count: 4,
  document_hash: "token_mgmt_tech_consolidated_v2",
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

SYS files contain node and token configuration data that can be automatically parsed. The system supports **multi-file selection** and distinguishes between **main configuration files** (e.g., `AB01_sys`) and **token-specific files** (e.g., `181.sys`, `41.sys`) for IP address resolution.

### SYS File Format

The LOGReport system supports two types of SYS files:

#### Main Configuration Files (e.g., `AB01_sys`)

```
# Main SYS file format - defines nodes and token relationships
AP01m FBC 161 0 ap01m_common
AP01 162 163  # AP node with main token 161, subordinate tokens 162, 163
AP02m 181 182 ap02m_common

AL01 RPC 191 al01_common  # AL node with single token 191
AL02 192 al02_common
```

**Node Type Distinction:**
- **AP Nodes** (e.g., `AP01`, `AP02m`): Multiple tokens with main+subordinate structure
  - Main token used for IP lookup (stored in `_main_token` field)
  - Subordinate tokens only appear in `tokens` list
  - Example: `AP01` has `_main_token=161`, `tokens=[162,163]`
  
- **AL Nodes** (e.g., `AL01`, `AL02`): Single token structure
  - Single token serves both purposes
  - Token appears in both `_main_token` field and `tokens` list
  - Example: `AL01` has `_main_token=191`, `tokens=[191]`

#### Token-Specific Files (e.g., `181.sys`, `41.sys`)

```
# Token-specific file format - contains IP address for specific token
# Filename pattern: {token_id}.sys (numeric only)
IP=192.168.0.12
PORT=23
DESCRIPTION=AP02m main token IP address
```

**Purpose:** Provides IP addresses for individual tokens, automatically associated with nodes via the `_main_token` field.

### SYS Parser Implementation

The current implementation in `src/utils/file_utils.py` uses regex-based parsing with support for both AP and AL node types:

```python
def parse_sys_file(sys_path: str) -> List[Dict[str, Any]]:
    """
    Parse .sys file and extract node configurations.
    
    Supports two node types:
    - AP nodes: Main token + subordinate tokens (e.g., "AP01 162 163" with main=161)
    - AL nodes: Single token (e.g., "AL01 RPC 191 al01_common")
    
    Args:
        sys_path: Path to .sys file
    
    Returns:
        List of node dictionaries with structure:
        {
            'name': str,           # Node name (e.g., 'AP01', 'AL01')
            'log_type': str,       # Protocol ('FBC' or 'RPC')
            'tokens': List[str],   # Token list (subordinate only for AP, single for AL)
            '_main_token': str,    # Token for IP lookup (always present)
            'log_path': str        # Log path pattern (optional)
        }
    """
    nodes = []
    
    # Regex patterns for different node formats
    al_pattern = re.compile(
        r'^([A-Z]{2}\d{2}[mr]?)\s+(FBC|RPC)\s+(\d+)\s*(\S+)?',
        re.IGNORECASE
    )
    
    ap_main_node_regex = re.compile(
        r'^([A-Z]{2}\d{2}[mr]?)\s+(?:FBC|RPC)\s+(\d+)\s+\d+\s+\S+',
        re.IGNORECASE
    )
    
    ap_pattern = re.compile(
        r'^([A-Z]{2}\d{2}[mr]?)\s+(\d+(?:\s+\d+)*)',
        re.IGNORECASE
    )
    
    try:
        with open(sys_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        for line in content.splitlines():
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            
            # Try AL pattern first (most specific)
            match = al_pattern.match(line)
            if match:
                node_name, log_type, token, log_path = match.groups()
                nodes.append({
                    'name': node_name,
                    'log_type': log_type.upper(),
                    'tokens': [token],          # AL: Include token in list
                    '_main_token': token,       # AL: Same token for IP lookup
                    'log_path': log_path or ''
                })
                continue
            
            # Try AP main node pattern (AP01m FBC 161 0 ...)
            match = ap_main_node_regex.match(line)
            if match:
                node_name, main_token = match.groups()
                # Main token stored for IP lookup, not in tokens list
                # Actual tokens extracted separately
                continue
            
            # Try AP pattern (AP01 162 163)
            match = ap_pattern.match(line)
            if match:
                node_name, token_str = match.groups()
                tokens = token_str.split()
                
                # Determine main token from AP01m reference
                # Main token = first token of corresponding AP##m node
                main_token = None
                base_name = node_name.rstrip('mr')[:4]  # e.g., "AP01" -> "AP01"
                
                # Look for main node in already parsed nodes
                for existing_node in nodes:
                    if existing_node['name'].startswith(base_name) and existing_node['name'].endswith('m'):
                        main_token = existing_node.get('_main_token')
                        break
                
                nodes.append({
                    'name': node_name,
                    'log_type': 'FBC',  # Default for AP nodes
                    'tokens': tokens,    # AP: Only subordinate tokens
                    '_main_token': main_token or tokens[0],  # Fallback to first token
                    'log_path': ''
                })
    
    except Exception as e:
        logging.error(f"Error parsing SYS file {sys_path}: {e}")
    
    return nodes


def merge_node_data(existing_nodes: Dict, parsed_nodes: List[Dict], token_ips: Dict[str, str]):
    """
    Merge parsed SYS data with existing node configuration.
    
    Handles:
    - IP association via _main_token field
    - Token-specific IP files (e.g., 181.sys -> token 181)
    - Overwrite mode for reloading
    
    Args:
        existing_nodes: Current node dictionary (modified in place)
        parsed_nodes: Nodes from main SYS file
        token_ips: Dict mapping token_id -> IP address from token files
    """
    for node_data in parsed_nodes:
        node_name = node_data['name']
        
        # Associate IP via _main_token lookup
        main_token = node_data.get('_main_token')
        if main_token and main_token in token_ips:
            node_data['ip_address'] = token_ips[main_token]
        
        # Overwrite existing node or create new
        existing_nodes[node_name] = node_data
```

**Key Implementation Details:**

| Aspect | Implementation | Rationale |
|--------|----------------|-----------|
| **Multi-file Selection** | `QFileDialog.getOpenFileNames()` (plural) | User can select main + token files in one operation |
| **File Type Detection** | Numeric filename → token file, else main file | Automatic categorization (e.g., `181.sys` vs `AB01_sys`) |
| **Token Separation** | AP: `tokens` excludes main, AL: `tokens` includes single | Reflects structural difference between node types |
| **IP Lookup** | Via `_main_token` field in `token_ips` dict | Decouples IP storage from token list |
| **Merge Behavior** | Direct assignment (overwrite) | Reload replaces data instead of merging |

### Node Configuration Dialog Integration

The `src/node_config_dialog.py` provides UI integration for SYS file loading:

```python
class NodeConfigDialog(QDialog):
    """Node configuration dialog with SYS file import."""
    
    def load_sys_file(self):
        """
        Load and parse SYS files with multi-file selection support.
        
        Workflow:
        1. Show file dialog (multi-select enabled)
        2. Categorize files: main config vs token-specific
        3. Parse main file for node definitions
        4. Parse token files for IP addresses
        5. Merge data and update UI
        """
        file_paths, _ = QFileDialog.getOpenFileNames(
            self,
            "Select SYS Files",
            "",
            "SYS Files (*.sys);;All Files (*)"
        )
        
        if not file_paths:
            return
        
        # Categorize files
        main_files = []
        token_files = []
        
        for path in file_paths:
            filename = os.path.basename(path)
            name_part = filename.rsplit('.', 1)[0]
            
            if name_part.isdigit():
                token_files.append(path)
            else:
                main_files.append(path)
        
        # Parse token files for IP addresses
        token_ips = {}
        for token_path in token_files:
            filename = os.path.basename(token_path)
            token_id = filename.rsplit('.', 1)[0]
            
            with open(token_path, 'r', encoding='utf-8', errors='ignore') as f:
                for line in f:
                    if line.startswith('IP='):
                        ip = line.split('=', 1)[1].strip()
                        token_ips[token_id] = ip
                        break
        
        # Parse main files and merge with token IPs
        for main_path in main_files:
            nodes = parse_sys_file(main_path)
            
            # Overwrite mode: replace existing node data
            for node_data in nodes:
                node_name = node_data['name']
                
                # Associate IP via _main_token
                main_token = node_data.get('_main_token')
                if main_token in token_ips:
                    node_data['ip_address'] = token_ips[main_token]
                
                # Update or create node in UI
                self.nodes[node_name] = node_data
        
        self.populate_table()
        QMessageBox.information(
            self,
            "SYS Files Loaded",
            f"Loaded {len(main_files)} main file(s) and {len(token_files)} token file(s)"
        )
```

### SYS File Usage

```python
# Example: Load SYS files and populate node configuration

# 1. Multi-file selection in UI
file_paths = QFileDialog.getOpenFileNames(
    parent,
    "Select SYS Files",
    "",
    "SYS Files (*.sys);;All Files (*)"
)[0]

# 2. Categorize files automatically
main_files = [p for p in file_paths if not os.path.basename(p).rsplit('.', 1)[0].isdigit()]
token_files = [p for p in file_paths if os.path.basename(p).rsplit('.', 1)[0].isdigit()]

# 3. Parse token files for IP addresses
token_ips = {}
for token_path in token_files:
    token_id = os.path.basename(token_path).rsplit('.', 1)[0]
    with open(token_path, 'r') as f:
        for line in f:
            if line.startswith('IP='):
                token_ips[token_id] = line.split('=')[1].strip()
                break

# 4. Parse main files and merge
nodes = {}
for main_path in main_files:
    parsed_nodes = parse_sys_file(main_path)
    merge_node_data(nodes, parsed_nodes, token_ips)

# 5. Verify node structure
for node_name, node_data in nodes.items():
    print(f"{node_name}:")
    print(f"  Type: {node_data['log_type']}")
    print(f"  Main Token: {node_data.get('_main_token')}")
    print(f"  Subordinate Tokens: {node_data['tokens']}")
    print(f"  IP: {node_data.get('ip_address', 'N/A')}")
```

**Expected Output:**
```
AP01m:
  Type: FBC
  Main Token: 161
  Subordinate Tokens: []
  IP: 192.168.0.11

AP01:
  Type: FBC
  Main Token: 161
  Subordinate Tokens: ['162', '163']
  IP: 192.168.0.11

AL01:
  Type: RPC
  Main Token: 191
  Subordinate Tokens: ['191']
  IP: 192.168.0.15
```

### Testing

Comprehensive test suite in `tests/test_sys_file_parsing_fixed.py`:

```python
def test_main_sys_file_parsing():
    """Test parsing of main SYS file (AB01_sys)."""
    nodes = parse_sys_file('AB01_sys')
    
    # Verify AP01m node
    ap01m = next(n for n in nodes if n['name'] == 'AP01m')
    assert ap01m['_main_token'] == '161'
    assert ap01m['log_type'] == 'FBC'
    
    # Verify AP01 node
    ap01 = next(n for n in nodes if n['name'] == 'AP01')
    assert ap01['_main_token'] == '161'  # Inherits from AP01m
    assert ap01['tokens'] == ['162', '163']  # Subordinate only
    
    # Verify AL01 node
    al01 = next(n for n in nodes if n['name'] == 'AL01')
    assert al01['_main_token'] == '191'
    assert al01['tokens'] == ['191']  # Single token included


def test_token_ip_association():
    """Test IP address association via _main_token."""
    nodes = parse_sys_file('AB01_sys')
    token_ips = {
        '161': '192.168.0.11',
        '181': '192.168.0.12',
        '191': '192.168.0.15'
    }
    
    node_dict = {}
    merge_node_data(node_dict, nodes, token_ips)
    
    # AP01 should get IP from token 161
    assert node_dict['AP01']['ip_address'] == '192.168.0.11'
    
    # AL01 should get IP from token 191
    assert node_dict['AL01']['ip_address'] == '192.168.0.15'
```

**Test Results:** ✅ All 5 tests passing (as of 2025-10-08)

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

**Document Status**: ✅ **COMPLETE** - Updated with multi-file SYS parsing implementation  
**Last Updated**: 2025-10-08  
**Consolidation**: token_processing.md + hybrid_token_resolution.md + sys_file_parsing.md + 6 others  
**Recent Changes**: Added multi-file selection, AP/AL node distinction, _main_token field documentation  
**Next Review**: 2026-01-08 (90 days)
