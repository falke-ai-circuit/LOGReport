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

#### Token-Specific Files (e.g., `181.sys`, `41.sys`, `1a1.sys`, `3a1.sys`)

```
# Token-specific file format - contains IP address for specific token
# Filename patterns (max 5 chars for bare format):
#   - Pure decimal: 181.sys, 41.sys, 21.sys
#   - Bare hexadecimal: 1a1.sys, 3a1.sys, 1c1.sys, 1e1.sys, 4a1.sys
#   - Prefixed hexadecimal: 0x1a1.sys, x3a1.sys
IP=192.168.0.12
PORT=23
DESCRIPTION=AP02m main token IP address
```

**Purpose:** Provides IP addresses for individual tokens, automatically associated with nodes via the `_main_token` field.

**Token ID Format:** 
- **Decimal tokens**: Pure numeric (e.g., `181`, `41`, `21`, `201`, `221`)
- **Hexadecimal tokens (bare)**: No prefix, contains hex digits a-f (e.g., `1a1`, `3a1`, `1c1`, `1e1`, `4a1`, `4c1`)
- **Hexadecimal tokens (prefixed)**: With `0x` or `x` prefix (e.g., `0x1a1`, `x3a1`)
- **Length constraint**: Maximum 5 characters for bare format (decimal or hex), up to 7 for prefixed (`0x` + 5 chars)

**Examples:**
- `181.sys` → token ID `181` (decimal)
- `1a1.sys` → token ID `1a1` (hexadecimal, for AP03m main token)
- `3a1.sys` → token ID `3a1` (hexadecimal, for AP03r reserve token)
- `0x1c1.sys` → token ID `0x1c1` (prefixed hexadecimal)

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

## � SYS File Parsing Fixes

### Recent Improvements (October 8, 2025)

Fixed critical issues in SYS file parsing implementation to correctly handle main sys files (like `AB01_sys`) and token-specific sys files (like `181.sys`, `41.sys`) with proper token management and IP address association.

### Problems Identified & Fixed

#### 1. Token Extraction Bug
**Location:** `src/node_config_dialog.py` line ~594  
**Issue:** Code was assigning the entire tokens list instead of extracting the first element:
```python
token_id = node["tokens"]  # WRONG - assigns list ['181', '182', '183']
```
**Fix:** 
```python
token_id = node["tokens"][0]  # CORRECT - extracts first element '181'
```

#### 2. Single File Selection Limitation
**Issue:** Dialog only allowed selecting one sys file at a time  
**Fix:** Changed from `QFileDialog.getOpenFileName` to `getOpenFileNames` (plural) to support multiple file selection simultaneously

#### 3. Incorrect Token Management
**Issue:** Main/generic tokens (like 181 for AP02m) were being added to the tokens list, but they should only be used for IP address lookup. However, AL nodes need their single token in the list.

**Fix:** 
- **AP nodes**: Main tokens stored in `_main_token` field internally, NOT in tokens list
- **AL nodes**: Main token IS in tokens list (AL has only one token for both purposes)
- Only subordinate tokens (182, 183 for AP02m) are added to AP tokens list
- `_main_token` is removed before saving node data (cleanup phase)

**Example**:
```python
# AP02m node structure (before cleanup)
{
    "name": "AP02m",
    "tokens": ["182", "183"],        # Subordinate tokens only
    "_main_token": "181",             # For IP lookup
    "log_type": "FBC",
    "ip_address": ""
}

# AL02 node structure (before cleanup)
{
    "name": "AL02",
    "tokens": [],                     # Empty (main token not operational)
    "_main_token": "41",              # For IP lookup only
    "log_type": "LOG",
    "ip_address": ""
}
```

#### 4. Merge vs Overwrite Behavior
**Issue:** Sys file loading was merging with existing nodes instead of replacing them, causing confusion and inconsistent state.

**Fix:** Changed to **overwrite mode** - loading sys files now replaces all existing nodes with a clean slate from the sys files.

**Benefits**:
- Predictable behavior (what you see in sys files is what you get)
- No merge conflicts or unexpected state
- Clean configuration reloads
- Easier debugging and testing

#### 5. IP Address Association Logic
**Issue:** IP addresses weren't being correctly associated with nodes from token-specific sys files.

**Fix:** 
- Token-specific files (`181.sys`, `41.sys`) are detected by numeric filename pattern
- IP is extracted only from token-specific files (not from main sys files)
- IP is mapped to nodes via their `_main_token` field (not first token in list)
- Auto-discovery of token sys files in the same directory as main sys file

**IP Association Flow**:
```
1. Load main file (AB01_sys) → nodes have _main_token set
2. Load token files (181.sys, 41.sys) → extract IPs into mapping {token: IP}
3. Associate IPs → match node._main_token to token in mapping
4. Result: node.ip_address = token_mapping[node._main_token]
```

### Files Modified

#### 1. `src/utils/file_utils.py`

**`parse_sys_file()` Enhancements**:
- Added `_main_token` field to store main/generic token for IP lookup
- **AP nodes**: Main tokens (181) are NOT added to tokens list, only subordinate tokens (182, 183)
- **AL nodes**: Main token (41) is NOT added to tokens list (empty list for operational tokens)
- Better detection of token-specific files vs main sys files (numeric filename pattern)
- Improved docstring extraction and metadata handling

**`merge_node_data()` Improvements**:
- Handles both old format (tokens as strings) and new format (tokens as objects)
- Better merging logic for tokens and types
- Preserves `_main_token` during merge for IP association
- Cleans up internal fields before final save

#### 2. `src/node_config_dialog.py`

**`load_sys_file()` Refactoring**:
- Changed to `getOpenFileNames` for multiple file selection
- Categorizes files into main sys files and token-specific sys files
- Parses main files without IP extraction
- Parses token files with IP extraction
- Auto-discovers token sys files in same directory as selected main file
- Uses `_main_token` for IP lookup instead of first token in list
- **OVERWRITE MODE**: Replaces existing nodes instead of merging
- Cleans up `_main_token` field before saving (internal field only)
- Provides informative user feedback about files loaded and nodes created

#### 3. `tests/test_sys_file_parsing_fixed.py`

**Updated Test Suite**:
- Verifies AP02m has tokens `["182", "183"]` NOT `["181", "182", "183"]`
- Verifies AL02 has empty tokens list `[]` (41 is main token only)
- Verifies IP addresses correctly assigned via `_main_token`
- Tests merge functionality with both old and new formats
- Tests overwrite behavior
- **Result**: All 5 tests now pass ✅

### Complete Loading Flow Example

**Scenario:** Loading `AB01_sys` with `181.sys` and `41.sys`

**Step 1: Select Files**
```
User selects: AB01_sys, 181.sys, 41.sys
(or just AB01_sys - auto-discovers 181.sys and 41.sys)
```

**Step 2: Categorization**
```
Main files: ['AB01_sys']           # Has node definitions
Token files: ['181.sys', '41.sys']  # Has IP addresses
```

**Step 3: Parse Main File (`AB01_sys`)**
```python
# Result for AP02m:
{
    "name": "AP02m",
    "tokens": ["182", "183"],      # Subordinate tokens only
    "_main_token": "181",           # Main token for IP lookup
    "log_type": "FBC",
    "ip_address": ""
}

# Result for AL02:
{
    "name": "AL02",
    "tokens": [],                   # Empty (no subordinate tokens)
    "_main_token": "41",            # Main token for IP lookup
    "log_type": "LOG",
    "ip_address": ""
}
```

**Step 4: Parse Token Files**
```python
# From 181.sys:
token_ips["181"] = "192.168.0.12"

# From 41.sys:
token_ips["41"] = "192.168.0.2"

# Result mapping:
token_ips = {
    "181": "192.168.0.12",
    "41": "192.168.0.2"
}
```

**Step 5: IP Association**
```python
# For each node, lookup IP using _main_token:
AP02m._main_token = "181" → IP = token_ips["181"] = "192.168.0.12"
AL02._main_token = "41"   → IP = token_ips["41"] = "192.168.0.2"

# Update nodes:
AP02m.ip_address = "192.168.0.12"
AL02.ip_address = "192.168.0.2"
```

**Step 6: Cleanup & Save**
```python
# Remove internal _main_token field:
for node in nodes:
    node.pop('_main_token', None)

# OVERWRITE existing nodes_data (doesn't merge):
self.nodes_data = {}
for node in nodes:
    self.nodes_data[node['name']] = node

# Final saved nodes (no _main_token):
{
    "AP02m": {
        "name": "AP02m",
        "tokens": ["182", "183"],
        "log_type": "FBC",
        "ip_address": "192.168.0.12"
    },
    "AL02": {
        "name": "AL02",
        "tokens": [],
        "log_type": "LOG",
        "ip_address": "192.168.0.2"
    }
}
```

### Node Type Comparison

#### AP-Based Nodes (e.g., AP02m, AP01m)
- **Main Token**: 181, 161 (used for IP lookup only, not in tokens list)
- **Subordinate Tokens**: 182, 183 / 162, 163 (in tokens list for operations)
- **Log Types**: FBC, RPC, LOG
- **IP Association**: Via main token from token-specific sys file

#### AL-Based Nodes (e.g., AL02, AL01)
- **Main Token**: 41, 191 (used for IP lookup only, not in tokens list)
- **Subordinate Tokens**: None (empty tokens list)
- **Log Types**: LOG, LIS
- **IP Association**: Via main token from token-specific sys file

### Usage in Node Configuration Dialog

**Loading SYS Files**:
1. Click "Load Sys File" button in Node Configuration dialog
2. Select one or more sys files:
   - **Option A**: Just main file (`AB01_sys`) - will auto-discover token files in same directory
   - **Option B**: Main + token files (`AB01_sys`, `181.sys`, `41.sys`) - explicit selection
   - **Option C**: Just token files if nodes already exist - updates IPs only
3. System processes files and **OVERWRITES** existing configuration
4. Nodes displayed with correct tokens (subordinate only) and IP addresses
5. User sees informative message: "Loaded X files, created/updated Y nodes"

### Benefits of Fixes

1. **Correct Token Management** - Main tokens properly separated from operational (subordinate) tokens
2. **Multiple File Support** - Load all related sys files in single operation
3. **Auto-Discovery** - Automatically finds token sys files in same directory as main file
4. **Clean Overwrites** - Loading sys files gives fresh start, no merge confusion or stale state
5. **Proper IP Association** - IPs correctly mapped via main tokens, not first token in list
6. **Error Prevention** - No more "str object has no attribute 'get'" errors from list/dict confusion
7. **Clear User Feedback** - Informative messages about files loaded and nodes created/updated
8. **Consistent Behavior** - Predictable results match sys file contents exactly
9. **Easier Testing** - Clear expectations, all tests passing
10. **Better Debugging** - Overwrite mode eliminates merge-related bugs

### Known Limitations

- Auto-discovery only works for token files in same directory as main sys file
- Token-specific files must have numeric filenames (e.g., `181.sys`, not `token_181.sys`)
- Overwrite mode means existing manual edits are lost when loading sys files
- No validation of token consistency across files

### Related Documentation

- [IMPLEMENTATION_SUMMARY_codegraph.md](../implementation/IMPLEMENTATION_SUMMARY_codegraph.md) - Related implementation patterns
- [Node Configuration Dialog](../architecture/ARCH_node_system.md#node-configuration) - Dialog architecture
- Test suite: `tests/test_sys_file_parsing_fixed.py` - Comprehensive test coverage

---

## �🔍 Token ID Extraction

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
