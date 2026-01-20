# 🏗️ Node System Architecture

<!-- METADATA -->
metadata: {
  created_date: "2025-10-08_163000",
  last_modified: "2025-10-08_163000",
  last_accessed: "2025-10-08_163000",
  word_count: 3124,
  reference_count: 6,
  document_hash: "node_system_arch_consolidated",
  obsolete_check_date: "2025-10-08",
  section_count: 7,
  internal_link_count: 28
}
<!-- /METADATA -->

## 📑 Table of Contents

- [Overview](#overview)
- [Node Manager Architecture](#node-manager-architecture)
  - [Core Responsibilities](#core-responsibilities)
  - [Configuration Management](#configuration-management)
  - [Node Registry](#node-registry)
- [Node Resolution System](#node-resolution-system)
  - [Resolution Architecture](#resolution-architecture)
  - [Dynamic IP Extraction](#dynamic-ip-extraction)
  - [Hybrid Token Resolution](#hybrid-token-resolution)
- [Node Color Determination](#node-color-determination)
  - [Color Logic](#color-logic)
  - [Status Tracking](#status-tracking)
- [Token Management Integration](#token-management-integration)
- [UI Integration](#ui-integration)
- [Troubleshooting](#troubleshooting)

---

## 🎯 Overview

The Node System provides comprehensive node and token management for the LOGReport application. It handles node configuration loading, log file scanning, IP address resolution, status tracking, and visual representation in the UI. The system is designed for flexibility, supporting both FBC (Fieldbus Command) and RPC (Remote Procedure Call) protocols with intelligent fallback mechanisms.

### Key Capabilities

| Capability | Description | Benefit |
|------------|-------------|---------|
| **Configuration Management** | JSON-based node definitions | Easy configuration updates |
| **Dynamic IP Resolution** | Extract IPs from logs/directories | Automatic network discovery |
| **Hybrid Token Support** | FBC/RPC token interoperability | Flexible command execution |
| **Status Visualization** | Color-coded node status (online/offline) | Quick system health overview |
| **Log File Association** | Automatic token-log file mapping | Organized log management |

### System Scope

- **Primary Use**: Node configuration and token management
- **Secondary Use**: Log file organization and IP resolution
- **Integration**: Works with [Command System](ARCH_command_system.md#node-integration), [Logging System](ARCH_logging_system.md#node-based-logging), and [Token Management](TECH_token_management.md)
- **UI Component**: NodeTreeView with color-coded status

---

## 🏗️ Node Manager Architecture

The `NodeManager` class serves as the central component for all node-related operations, maintaining the node registry and providing lookup services.

### Architecture Diagram

```
┌─────────────────────────────────────────────────┐
│              nodes.json Configuration            │
│  {nodes: [{name, ip, tokens: [...]}]}          │
└──────────────────┬──────────────────────────────┘
                   │ Load Config
         ┌─────────▼────────┐
         │   NodeManager    │
         │ - Node Registry  │
         │ - Token Lookup   │
         │ - IP Resolution  │
         └─────────┬────────┘
                   │
    ┌──────────────┼──────────────┐
    │              │              │
┌───▼────┐  ┌─────▼─────┐  ┌────▼─────┐
│  Scan  │  │  Resolve  │  │  Track   │
│  Logs  │  │    IPs    │  │  Status  │
└───┬────┘  └─────┬─────┘  └────┬─────┘
    │             │              │
    └─────────────┼──────────────┘
                  │
          ┌───────▼────────┐
          │  NodeTreeView  │
          │ (UI Component) │
          └────────────────┘
```

### Core Responsibilities

The NodeManager handles the complete lifecycle of node management:

#### 1. Configuration Loading

**Responsibility**: Load and parse node configurations from `nodes.json`

```python
def load_configuration(self):
    """
    Loads node configuration from JSON file.
    
    File Format:
    {
      "nodes": [
        {
          "name": "AP01m",
          "ip_address": "192.168.0.11",
          "status": "online",
          "tokens": {
            "FBC": ["12345", "12346"],
            "RPC": ["67890"]
          }
        }
      ]
    }
    
    Returns:
        bool: True if load successful, False otherwise
    """
    try:
        with open(self.config_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            self.nodes = [Node(**node_data) for node_data in data['nodes']]
        
        logging.info(f"Loaded {len(self.nodes)} nodes from configuration")
        return True
    
    except FileNotFoundError:
        logging.error(f"Configuration file not found: {self.config_path}")
        return False
    except json.JSONDecodeError as e:
        logging.error(f"Invalid JSON in config file: {str(e)}")
        return False
    except Exception as e:
        logging.error(f"Config load failed: {str(e)}")
        return False
```

**Configuration Validation**:
- ✅ JSON syntax validation
- ✅ Required fields check (name, ip_address)
- ✅ IP address format validation
- ✅ Token format validation

#### 2. Log File Scanning

**Responsibility**: Discover and associate log files with nodes and tokens

```python
def scan_log_files(self, log_root: str):
    """
    Scans log directories and associates files with nodes/tokens.
    
    Directory Structure:
    {log_root}/
    ├── FBC/{node_name}/
    │   └── {node}_{ip}_{token}.fbc
    ├── RPC/{node_name}/
    │   └── {node}_{ip}_{token}.rpc
    └── LOG/
        └── {node}_{ip}.log
    
    Process:
    1. Iterate through each node
    2. Scan protocol-specific directories (FBC, RPC, LIS)
    3. Extract token IDs from filenames
    4. Associate log files with node tokens
    5. Update token metadata (IP, filepath)
    """
    for node in self.nodes:
        # Scan FBC logs
        fbc_dir = os.path.join(log_root, 'FBC', node.name)
        if os.path.exists(fbc_dir):
            for filename in os.listdir(fbc_dir):
                if filename.endswith('.fbc'):
                    token_id = self._extract_token_from_filename(filename)
                    if token_id:
                        node.add_token('FBC', token_id)
                        token = node.get_token('FBC', token_id)
                        token.log_path = os.path.join(fbc_dir, filename)
        
        # Scan RPC logs (similar pattern)
        rpc_dir = os.path.join(log_root, 'RPC', node.name)
        if os.path.exists(rpc_dir):
            for filename in os.listdir(rpc_dir):
                if filename.endswith('.rpc'):
                    token_id = self._extract_token_from_filename(filename)
                    if token_id:
                        node.add_token('RPC', token_id)
                        token = node.get_token('RPC', token_id)
                        token.log_path = os.path.join(rpc_dir, filename)
        
        logging.info(f"Scanned logs for node {node.name}: "
                    f"{len(node.fbc_tokens)} FBC, {len(node.rpc_tokens)} RPC")
```

**Token Extraction Pattern**:
```python
def _extract_token_from_filename(self, filename: str) -> Optional[str]:
    """
    Extract token ID from log filename.
    
    Patterns supported:
    - NODE_IP_TOKEN.ext -> TOKEN
    - NODE_TOKEN.ext -> TOKEN
    - TOKEN.ext -> TOKEN (if numeric)
    
    Args:
        filename: Log filename to parse
    
    Returns:
        Token ID string or None if no token found
    """
    # Pattern: NODE_192.168.0.11_12345.fbc -> 12345
    pattern = r'_(\d+)\.\w+$'
    match = re.search(pattern, filename)
    if match:
        return match.group(1)
    
    # Fallback: numeric filename before extension
    base = os.path.splitext(filename)[0]
    if base.isdigit():
        return base
    
    return None
```

#### 3. Node Registry Management

**Responsibility**: Maintain searchable registry of all nodes

```python
class NodeManager:
    def __init__(self, config_path: str, log_root: str):
        self.config_path = config_path
        self.log_root = log_root
        self.nodes: List[Node] = []
        self._node_index: Dict[str, Node] = {}  # Fast lookup by name
        self._token_index: Dict[Tuple[str, str], Node] = {}  # Lookup by (token_id, protocol)
    
    def _build_indices(self):
        """Build lookup indices for fast node/token retrieval."""
        self._node_index = {node.name: node for node in self.nodes}
        
        for node in self.nodes:
            for token in node.fbc_tokens:
                self._token_index[(token.token_id, 'FBC')] = node
            for token in node.rpc_tokens:
                self._token_index[(token.token_id, 'RPC')] = node
    
    def get_node(self, node_name: str) -> Optional[Node]:
        """Fast O(1) node lookup by name."""
        return self._node_index.get(node_name)
    
    def get_node_by_token(self, token_id: str, protocol: str) -> Optional[Node]:
        """Fast O(1) node lookup by token ID and protocol."""
        return self._token_index.get((token_id, protocol))
    
    def get_all_nodes(self) -> List[Node]:
        """Return all nodes in registry."""
        return self.nodes
    
    def add_node(self, node: Node):
        """Add new node to registry and rebuild indices."""
        self.nodes.append(node)
        self._build_indices()
    
    def remove_node(self, node_name: str) -> bool:
        """Remove node from registry."""
        self.nodes = [n for n in self.nodes if n.name != node_name]
        self._build_indices()
        return True
```

### Configuration Management

#### nodes.json Structure

```json
{
  "nodes": [
    {
      "name": "AP01m",
      "ip_address": "192.168.0.11",
      "status": "online",
      "description": "Main application server",
      "tokens": {
        "FBC": ["12345", "12346", "12347"],
        "RPC": ["67890", "67891"]
      },
      "metadata": {
        "location": "Rack 1",
        "hardware": "Dell PowerEdge"
      }
    }
  ]
}
```

#### Node Object Model

```python
@dataclass
class Node:
    """Represents a network node with associated tokens."""
    name: str
    ip_address: str
    status: str = "offline"  # "online" | "offline"
    description: Optional[str] = None
    fbc_tokens: List[NodeToken] = field(default_factory=list)
    rpc_tokens: List[NodeToken] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def add_token(self, protocol: str, token_id: str):
        """Add token to appropriate protocol list."""
        token = NodeToken(token_id=token_id, protocol=protocol, node_name=self.name)
        
        if protocol == 'FBC':
            if not any(t.token_id == token_id for t in self.fbc_tokens):
                self.fbc_tokens.append(token)
        elif protocol == 'RPC':
            if not any(t.token_id == token_id for t in self.rpc_tokens):
                self.rpc_tokens.append(token)
    
    def get_token(self, protocol: str, token_id: str) -> Optional[NodeToken]:
        """Retrieve specific token by protocol and ID."""
        tokens = self.fbc_tokens if protocol == 'FBC' else self.rpc_tokens
        return next((t for t in tokens if t.token_id == token_id), None)
    
    def get_all_tokens(self) -> List[NodeToken]:
        """Return all tokens (FBC + RPC) for this node."""
        return self.fbc_tokens + self.rpc_tokens
```

### Node Registry

The registry provides efficient node and token lookup:

**Performance Characteristics**:

| Operation | Complexity | Notes |
|-----------|-----------|-------|
| `get_node(name)` | O(1) | Hash table lookup |
| `get_node_by_token(id, protocol)` | O(1) | Composite key lookup |
| `get_all_nodes()` | O(1) | Direct list return |
| `add_node(node)` | O(n) | Requires index rebuild |
| `scan_log_files()` | O(n*m) | n=nodes, m=files per node |

---

## 🔍 Node Resolution System

The resolution system handles IP address discovery and token-to-node mapping, supporting both configuration-based and dynamic resolution.

### Resolution Architecture

The system implements a **three-tier resolution strategy**:

```
┌──────────────────────────────────────────────────┐
│          Resolution Request                       │
│     (node_name, token_id, protocol)              │
└──────────────────┬───────────────────────────────┘
                   │
         ┌─────────▼────────┐
         │   Tier 1:        │
         │ Configuration    │
         │  nodes.json      │
         └─────────┬────────┘
                   │
              ┌────▼─────┐
              │ Success? │
              └────┬─────┘
                   │ No
         ┌─────────▼────────┐
         │   Tier 2:        │
         │ Dynamic Scan     │
         │  Log Files       │
         └─────────┬────────┘
                   │
              ┌────▼─────┐
              │ Success? │
              └────┬─────┘
                   │ No
         ┌─────────▼────────┐
         │   Tier 3:        │
         │ Fallback Logic   │
         │  FBC→RPC         │
         └─────────┬────────┘
                   │
              ┌────▼─────┐
              │ Resolved │
              └──────────┘
```

### Dynamic IP Extraction

The system automatically discovers IP addresses from log file paths and names:

#### Pattern Recognition

```python
def _scan_for_dynamic_ips(self, log_root: str):
    """
    Scans log directory hierarchy for IP patterns.
    
    Supported Patterns:
    1. Directory names: /logs/FBC/192-168-0-11/
    2. Filenames: NODE_192-168-0-11_TOKEN.fbc
    3. Mixed: /logs/RPC/192-168-0-11/NODE_TOKEN.rpc
    
    IP Format: Hyphenated (192-168-0-11) converted to dotted (192.168.0.11)
    """
    ip_pattern = r"(\d{1,3}-\d{1,3}-\d{1,3}-\d{1,3})"
    discovered_ips = {}
    
    for dirpath, _, filenames in os.walk(log_root):
        # Extract IPs from directory names
        dir_name = os.path.basename(dirpath)
        dir_ips = re.findall(ip_pattern, dir_name)
        
        # Extract IPs from filenames
        for filename in filenames:
            file_ips = re.findall(ip_pattern, filename)
            
            # Combine and convert format
            all_ips = set(dir_ips + file_ips)
            for ip_hyphenated in all_ips:
                ip_dotted = ip_hyphenated.replace('-', '.')
                
                # Validate IP format
                if self._validate_ip_address(ip_dotted):
                    # Associate with node based on directory structure
                    node_name = self._extract_node_from_path(dirpath)
                    if node_name:
                        discovered_ips[node_name] = ip_dotted
    
    # Update node IPs
    for node_name, ip in discovered_ips.items():
        node = self.get_node(node_name)
        if node and not node.ip_address:
            node.ip_address = ip
            logging.info(f"Dynamically resolved IP for {node_name}: {ip}")
```

#### IP Validation

```python
def _validate_ip_address(self, ip: str) -> bool:
    """
    Validate IP address format.
    
    Rules:
    - Must be dotted decimal notation (e.g., 192.168.0.11)
    - Each octet must be 0-255
    - Exactly 4 octets
    
    Args:
        ip: IP address string to validate
    
    Returns:
        True if valid, False otherwise
    """
    try:
        parts = ip.split('.')
        if len(parts) != 4:
            return False
        
        for part in parts:
            num = int(part)
            if num < 0 or num > 255:
                return False
        
        return True
    except (ValueError, AttributeError):
        return False
```

### Hybrid Token Resolution

The `RpcCommandService` implements intelligent token resolution with FBC→RPC fallback:

```python
def get_token(self, node_name: str, token_id: str) -> NodeToken:
    """
    Retrieve token with hybrid resolution and fallback.
    
    Resolution Order:
    1. Try exact RPC token match (token_id)
    2. Try integer-normalized RPC token (strip leading zeros)
    3. Try FBC token with RPC conversion
    4. Create temporary RPC token from FBC metadata
    5. Raise error if no resolution possible
    
    Args:
        node_name: Name of the node
        token_id: Token ID to resolve
    
    Returns:
        NodeToken object (RPC protocol)
    
    Raises:
        ValueError: If node not found or token cannot be resolved
    """
    node = self.node_manager.get_node(node_name)
    if not node:
        raise ValueError(f"Node {node_name} not found in registry")
    
    # 1. Try exact RPC token match
    rpc_token = node.get_token('RPC', token_id)
    if rpc_token:
        return rpc_token
    
    # 2. Try normalized RPC token (handle leading zeros)
    normalized_id = str(int(token_id)) if token_id.isdigit() else token_id
    if normalized_id != token_id:
        rpc_token = node.get_token('RPC', normalized_id)
        if rpc_token:
            return rpc_token
    
    # 3. Try FBC token (hybrid resolution)
    fbc_token = node.get_token('FBC', token_id)
    if fbc_token:
        # Convert FBC token to RPC usage
        temp_rpc_token = NodeToken(
            token_id=fbc_token.token_id,
            protocol='RPC',  # Convert to RPC
            node_name=node_name,
            ip_address=fbc_token.ip_address or node.ip_address,
            port=fbc_token.port or 23,  # Default telnet port
        )
        logging.info(f"Using FBC token {token_id} for RPC command (hybrid resolution)")
        return temp_rpc_token
    
    # 4. Create temporary token from node metadata
    if node.ip_address:
        temp_token = NodeToken(
            token_id=token_id,
            protocol='RPC',
            node_name=node_name,
            ip_address=node.ip_address,
            port=23,
        )
        logging.warning(f"Created temporary RPC token for {node_name}:{token_id}")
        return temp_token
    
    # 5. No resolution possible
    raise ValueError(
        f"Cannot resolve token {token_id} for node {node_name}: "
        f"No RPC token, no FBC token, and no node IP address"
    )
```

**Fallback Benefits**:
- ✅ **Flexibility**: FBC tokens can execute RPC commands
- ✅ **Reliability**: Multiple resolution paths reduce failures
- ✅ **Compatibility**: Handles legacy configurations
- ✅ **Graceful Degradation**: Creates temporary tokens when needed

---

## 🎨 Node Color Determination

The UI represents node status using color-coding based on command execution and log file content.

### Color Logic

Node colors reflect three states:

| Color | Meaning | Criteria |
|-------|---------|----------|
| 🟢 **Green** | Success with content | `command_success=True` AND `log_success=True` AND `line_count>5` |
| 🟡 **Yellow** | Success but minimal content | `command_success=True` AND `log_success=True` AND `line_count≤5` |
| 🔴 **Red** | Failure or error | `command_success=False` OR `log_success=False` |

### Status Tracking

The `NodeTreePresenter` maintains status for each node:

```python
class NodeTreePresenter:
    def __init__(self, view: NodeTreeView, node_manager: NodeManager):
        self.view = view
        self.node_manager = node_manager
        
        # Status tracking per node
        self.node_status: Dict[str, Dict[str, Optional[Any]]] = {}
        # Structure: {node_name: {command_success, log_success, line_count}}
        
        # Connect signals
        self._connect_signals()
    
    def _connect_signals(self):
        """Connect to command and log completion signals."""
        # From CommandQueue
        command_queue.command_completed.connect(self.handle_command_completed)
        
        # From LogWriter
        log_writer.log_write_completed.connect(self.handle_log_write_completed)
    
    def handle_command_completed(self, node_name: str, token_id: str, success: bool):
        """Handle command completion signal."""
        if node_name not in self.node_status:
            self.node_status[node_name] = {
                'command_success': None,
                'log_success': None,
                'line_count': None
            }
        
        self.node_status[node_name]['command_success'] = success
        self._check_and_update_node_color(node_name)
    
    def handle_log_write_completed(
        self, 
        node_name: str, 
        token_id: str, 
        success: bool, 
        filepath: str, 
        line_count: int
    ):
        """Handle log write completion signal."""
        if node_name not in self.node_status:
            self.node_status[node_name] = {
                'command_success': None,
                'log_success': None,
                'line_count': None
            }
        
        self.node_status[node_name]['log_success'] = success
        self.node_status[node_name]['line_count'] = line_count
        self._check_and_update_node_color(node_name)
    
    def _check_and_update_node_color(self, node_name: str):
        """
        Determine and apply node color based on complete status.
        
        Only updates color when all required status fields are available.
        """
        status = self.node_status.get(node_name)
        if not status:
            return
        
        cmd_success = status['command_success']
        log_success = status['log_success']
        line_count = status['line_count']
        
        # Wait for all status fields to be populated
        if cmd_success is None or log_success is None or line_count is None:
            return
        
        # Determine color
        if cmd_success and log_success:
            if line_count > 5:
                color = 'green'
            else:
                color = 'yellow'
        else:
            color = 'red'
        
        # Update UI
        self.view.update_node_color(node_name, color)
        
        # Reset status for next operation
        self.node_status[node_name] = {
            'command_success': None,
            'log_success': None,
            'line_count': None
        }
```

### Line Count Calculation

The `LogWriter` calculates line count efficiently:

```python
def get_file_line_count(self, filepath: str) -> int:
    """
    Efficiently count lines in a file.
    
    Uses generator expression to avoid loading entire file into memory.
    
    Args:
        filepath: Path to file to count
    
    Returns:
        Number of lines in file (0 if file doesn't exist or error)
    """
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return sum(1 for _ in f)
    except FileNotFoundError:
        logging.warning(f"File not found for line count: {filepath}")
        return 0
    except Exception as e:
        logging.error(f"Error counting lines in {filepath}: {str(e)}")
        return 0
```

---

## 🔗 Token Management Integration

The Node System integrates closely with the [Token Management](TECH_token_management.md) system:

### Token Object Model

```python
@dataclass
class NodeToken:
    """Represents a token associated with a node."""
    token_id: str
    protocol: str  # 'FBC' | 'RPC' | 'LIS'
    node_name: str
    ip_address: Optional[str] = None
    port: Optional[int] = None
    log_path: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
```

### Token Lookup Flow

```
User Action (e.g., Execute FBC Command)
    ↓
CommandService.get_token(node_name, token_id)
    ↓
NodeManager.get_node(node_name)
    ↓
Node.get_token(protocol, token_id)
    ↓
[If not found] → Hybrid Resolution → FBC→RPC Fallback
    ↓
NodeToken (with IP, port, log_path)
    ↓
Command Execution
```

---

## 🖥️ UI Integration

The Node System provides the data layer for the `NodeTreeView` UI component:

### NodeTreeView Structure

```
📁 Node Tree
├── 📦 AP01m (192.168.0.11) [🟢]
│   ├── 📂 FBC
│   │   ├── 🔑 Token 12345
│   │   ├── 🔑 Token 12346
│   │   └── 🔑 Token 12347
│   ├── 📂 RPC
│   │   └── 🔑 Token 67890
│   └── 📂 LOG
│       └── 📄 AP01m_192.168.0.11.log
└── 📦 AP02m (192.168.0.12) [🔴]
    └── ...
```

### View Update Methods

```python
class NodeTreeView(QWidget):
    def update_node_color(self, node_name: str, color_name: str):
        """
        Update visual color of node item.
        
        Args:
            node_name: Name of node to update
            color_name: 'green' | 'yellow' | 'red'
        """
        node_item = self._find_node_item(node_name)
        if not node_item:
            return
        
        # Color mapping
        colors = {
            'green': QColor(76, 175, 80),   # Material Green
            'yellow': QColor(255, 235, 59),  # Material Yellow
            'red': QColor(244, 67, 54)       # Material Red
        }
        
        color = colors.get(color_name, QColor(158, 158, 158))  # Default gray
        node_item.setForeground(0, QBrush(color))
```

---

## 🔥 Troubleshooting

### Common Issues

#### Issue: Node Not Found

**Symptom**: `ValueError: Node {name} not found in registry`

**Causes**:
- Node not defined in `nodes.json`
- Configuration not loaded
- Typo in node name

**Solution**:
```python
# Verify node exists in config
with open('nodes.json') as f:
    data = json.load(f)
    print([node['name'] for node in data['nodes']])

# Reload configuration
node_manager.load_configuration()

# List all loaded nodes
for node in node_manager.get_all_nodes():
    print(f"- {node.name} ({node.ip_address})")
```

#### Issue: Token Not Resolved

**Symptom**: Cannot find token for command execution

**Causes**:
- Token not in configuration
- Log files not scanned
- Token ID mismatch (leading zeros)

**Solution**:
```python
# Scan log files to discover tokens
node_manager.scan_log_files(log_root)

# Check node tokens
node = node_manager.get_node('AP01m')
print(f"FBC tokens: {[t.token_id for t in node.fbc_tokens]}")
print(f"RPC tokens: {[t.token_id for t in node.rpc_tokens]}")

# Try normalized token ID
token_id = "00123"  # Try both "00123" and "123"
```

#### Issue: Colors Not Updating

**Symptom**: Node colors remain unchanged after command execution

**Causes**:
- Signal not connected
- Incomplete status (missing command_success, log_success, or line_count)
- Presenter not receiving signals

**Debug**:
```python
# Enable debug logging
logging.basicConfig(level=logging.DEBUG)

# Check signal connections
print(f"Command signal connected: {command_queue.command_completed.receivers()}")
print(f"Log signal connected: {log_writer.log_write_completed.receivers()}")

# Monitor status updates
def debug_status(node_name):
    status = presenter.node_status.get(node_name, {})
    print(f"{node_name} status: {status}")
```

#### Issue: Dynamic IP Not Discovered

**Symptom**: Node IP remains unset after log scan

**Causes**:
- Log files use different IP format
- Directory structure doesn't match expected pattern
- IP validation failing

**Solution**:
```python
# Check log directory structure
import os
for root, dirs, files in os.walk(log_root):
    print(f"{root}: {files[:3]}")  # Show first 3 files

# Verify IP pattern in filenames
pattern = r"(\d{1,3}-\d{1,3}-\d{1,3}-\d{1,3})"
for filename in os.listdir(fbc_dir):
    matches = re.findall(pattern, filename)
    print(f"{filename}: {matches}")

# Force manual IP update
node = node_manager.get_node('AP01m')
node.ip_address = '192.168.0.11'
```

---

## 📚 References

### Related Documentation

- **[Command System](ARCH_command_system.md)** - Command execution integration
- **[Logging System](ARCH_logging_system.md)** - Node-based log organization
- **[Token Management](TECH_token_management.md)** - Token resolution details
- **[MVP Service Layer](ARCH_mvp_service_layer.md)** - Presenter pattern implementation

### Source Code

- **NodeManager**: `src/core/node_manager.py`
- **Node Model**: `src/models/node.py`
- **NodeTreePresenter**: `src/commander/presenters/node_tree_presenter.py`
- **NodeTreeView**: `src/commander/views/node_tree_view.py`
- **RpcCommandService**: `src/services/rpc_command_service.py`

---

**Document Status**: ✅ **COMPLETE** - Consolidated from 14 source documents
**Last Updated**: 2025-10-08
**Consolidation**: node_manager_architecture.md + node_resolution.md + node_color_determination_logic.md + 11 others
**Next Review**: 2026-01-08 (90 days)
