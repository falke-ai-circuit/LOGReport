# CODER PROMPT: LOGReport Commander Window Implementation

**Project:** /opt/data/LOGReport/  
**Branch:** dev-cycle-logreport-20260615  
**Language:** Go backend + React/TypeScript frontend (Vite + Tailwind)  
**Scope:** Add the Commander window — interactive command center that was excluded from the initial refactor

---

## CONTEXT: What Was Missed

The original Python LOGReport had TWO windows:

1. **Report Window** (`gui.py`) — ✅ Already refactored to Go. File selection, format choice, report generation.
2. **Commander Window** (`commander_window.py`, 686 lines) — ❌ NOT refactored. Interactive command center with:
   - Node tree from `nodes.json` (hierarchical: node → FBC/RPC/LOG/LIS groups → token leaves)
   - Live telnet session to Valmet DNA debugger (connect, send commands, see output in terminal)
   - BsTool.exe integration (error log extraction via subprocess)
   - Scan tab with FBC/RPC comparison tables + auto-refresh
   - Command queue with sequential execution, pause/resume/cancel
   - "Print All Nodes" batch execution
   - Log file writing (command output → per-node log files)
   - Context menu (right-click → FBC print, RPC print, BsTool errlog)

The original Python source is at: `/opt/data/workspace-analyst/dev-cycle-logreport-20260615/source/src/commander/`

The full gap analysis is at: `/opt/data/LOGReport/SCOPE_GAP_ANALYSIS.md`

---

## WHAT ALREADY EXISTS (Do NOT recreate)

### Go backend (reusable):
- `internal/telnet/client.go` — `Dial(host, port, timeout)`, `SendCommand(cmd)`, `ReadUntilPrompt()`, `Close()` — one-shot telnet client
- `internal/telnet/commands.go` — `FBCPrint(token)`, `FBCClear(token)`, `RPCPrint(token)`, `RPCClear(token)`, `CommandResolver` map (ps→show all, fis→print_fieldbus, rc→print_fieldbus_rupi_counters)
- `internal/telnet/filter.go` — `FilterOutput()` — ANSI strip, control char removal
- `internal/parser/fbc.go` — `ParseFBC(output)` → `[]FBCModule`
- `internal/parser/rpc.go` — `ParseRPC(output)` → `[]RPCModule`
- `internal/parser/sysfile.go` — `ParseSysFile(content)` → `[]SysFileEntry`
- `internal/store/` — SQLite store with nodes, iopoints, modules, reports, templates CRUD
- `internal/bstool/client.go` — `NewClient()`, `ErrLog(serverName)` with COMMUNICATION_LINE env var, node suffix stripping
- `internal/types/node.go` — `Node` struct with Address, Name, Type, Status, TokenID, Port
- `internal/api/server.go` — HTTP server with 12 routes registered, Go 1.22+ routing
- `internal/api/handlers.go` — All existing handlers (connect, nodes, scan, fbc, rpc, sysfile, reports, bstool/errlog)

### React frontend (reusable):
- `web/src/App.tsx` — React Router with Layout, routes for /, /nodes, /nodes/:addr, /reports, /reports/:id, /sysfile
- `web/src/components/Layout.tsx` — Sidebar nav + content area
- `web/src/components/NodeBrowser.tsx` — Flat node list with connect form
- `web/src/components/NodeDetail.tsx` — Node detail with FBC/RPC tabs, scan button
- `web/src/components/FBCView.tsx`, `RPCView.tsx` — FBC/RPC display
- `web/src/components/StatusBar.tsx` — Health dot, version
- `web/src/components/ReportConfig.tsx`, `ReportList.tsx`, `ReportDetail.tsx` — Report UI
- `web/src/components/SysFileUpload.tsx` — SysFile upload

### API endpoints already registered (server.go:117-153):
1. `GET /health`
2. `POST /api/v1/connect`
3. `GET /api/v1/nodes`
4. `GET /api/v1/nodes/{addr}`
5. `POST /api/v1/nodes/{addr}/scan`
6. `GET /api/v1/nodes/{addr}/fbc`
7. `GET /api/v1/nodes/{addr}/rpc`
8. `POST /api/v1/parse/sysfile`
9. `POST /api/v1/reports/generate`
10. `GET /api/v1/reports`
11. `GET /api/v1/reports/{id}`
12. `POST /api/v1/bstool/errlog`

---

## IMPLEMENTATION SPEC

### Phase 1: Backend — Commander APIs

#### 1A. Node Types Expansion (`internal/types/node.go`)

**Add Token type** to model nodes.json structure:

```go
// TokenType identifies the kind of token (FBC, RPC, LOG, LIS, FTP).
type TokenType string

const (
    TokenFBC TokenType = "FBC"
    TokenRPC TokenType = "RPC"
    TokenLOG TokenType = "LOG"
    TokenLIS TokenType = "LIS"
    TokenFTP TokenType = "FTP"
)

// Token represents a single token entry from nodes.json.
type Token struct {
    TokenID  string    `json:"token_id"`
    TokenType TokenType `json:"token_type"`
    Port     int       `json:"port"`
    Protocol string    `json:"protocol"` // "telnet" or "ftp"
}

// NodeConfig represents the full nodes.json entry (node + all tokens).
type NodeConfig struct {
    Name      string  `json:"name"`
    IPAddress string  `json:"ip_address"`
    Tokens    []Token `json:"tokens"`
}
```

**Add to Node struct:** `Tokens []Token` field.

#### 1B. Nodes.json Loader (`internal/nodesconfig/loader.go`)

New package to load/save the original nodes.json format:

```go
package nodesconfig

// LoadFromFile parses nodes.json (array of NodeConfig).
func LoadFromFile(path string) ([]NodeConfig, error)

// LoadFromBytes parses nodes.json from byte slice.
func LoadFromBytes(data []byte) ([]NodeConfig, error)

// SaveToFile writes NodeConfig array back to nodes.json.
func SaveToFile(path string, configs []NodeConfig) error

// BuildTree converts flat NodeConfig list to hierarchical tree structure
// for the frontend: root nodes → token groups (FBC/RPC/LOG/LIS) → token leaves.
func BuildTree(configs []NodeConfig) *TreeNode

// TreeNode is the hierarchical structure for the frontend node tree.
type TreeNode struct {
    Name     string     `json:"name"`
    Type     string     `json:"type"`     // "node", "group", "token"
    IP       string     `json:"ip,omitempty"`
    TokenID  string     `json:"token_id,omitempty"`
    Port     int        `json:"port,omitempty"`
    Protocol string     `json:"protocol,omitempty"`
    Status   string     `json:"status,omitempty"` // "idle", "connected", "error"
    Children []TreeNode `json:"children,omitempty"`
}
```

**Source format** (`/opt/data/workspace-analyst/dev-cycle-logreport-20260615/source/src/nodes.json`):
```json
[
    {"name": "AP01m", "ip_address": "192.168.1.101", "tokens": [
        {"token_id": "162", "token_type": "FBC", "port": 2077, "protocol": "telnet"},
        {"token_id": "163", "token_type": "FBC", "port": 5901, "protocol": "telnet"}
    ]}
]
```

**BuildTree output:** Group tokens by type under each node:
```
AP01m (node, 192.168.1.101)
├── FBC (group)
│   ├── 162 (token, port 2077, telnet)
│   └── 163 (token, port 5901, telnet)
├── RPC (group)
│   └── 363 (token, port 2077, telnet)
└── LOG (group)
    └── 361 (token, port 2077, telnet)
```

#### 1C. WebSocket Telnet Session Manager (`internal/telnet/session.go`)

New file for persistent interactive telnet sessions:

```go
package telnet

// SessionManager manages persistent telnet connections keyed by session ID.
// Each session maintains a live telnet connection that can be interacted
// with via WebSocket — send commands, receive streamed output.
type SessionManager struct {
    sessions map[string]*Session
    mu       sync.RWMutex
}

// Session wraps a persistent telnet connection with streaming output.
type Session struct {
    ID        string
    Client    *Client
    Address   string
    Port      int
    Connected bool
    Output    chan string  // streamed output to WebSocket
    Done      chan struct{}
}

// NewSessionManager creates a new session manager.
func NewSessionManager() *SessionManager

// Connect creates a new persistent telnet session.
func (sm *SessionManager) Connect(sessionID, host string, port int, timeout time.Duration) (*Session, error)

// SendCommand sends a command through an existing session.
func (sm *SessionManager) SendCommand(sessionID, cmd string) error

// Disconnect closes a session.
func (sm *SessionManager) Disconnect(sessionID string) error

// GetSession returns an active session by ID.
func (sm *SessionManager) GetSession(sessionID string) (*Session, bool)

// ListSessions returns all active session IDs.
func (sm *SessionManager) ListSessions() []string
```

**Key behaviors:**
- After `Connect()`, a background goroutine reads from the telnet connection and pushes output to `Session.Output` channel
- The WebSocket handler reads from `Output` channel and writes to the WebSocket
- `SendCommand()` writes to the telnet connection (command + `\r\n`)
- Buffer clearing: before sending a command, clear the input buffer (matching Python `read_very_eager()` + Ctrl+X + Ctrl+Z behavior from `telnet_client.py:82-89`)
- Prompt detection: use the existing `promptPatterns` regexes to determine when command output is complete
- The output is filtered through `FilterOutput()` before being sent to the channel

#### 1D. WebSocket Handler (`internal/api/handlers_websocket.go`)

New file for WebSocket endpoints:

```go
package api

// telnetWSHandler handles WebSocket connections for interactive telnet sessions.
// 
// URL: ws://host/api/v1/telnet/ws?session={sessionID}
// 
// Messages from client (JSON):
//   {"action": "connect", "host": "192.168.1.101", "port": 2077}
//   {"action": "command", "command": "show all"}
//   {"action": "disconnect"}
//
// Messages from server (JSON):
//   {"type": "output", "data": "FBC agent 162\nPIC  5  6  7..."}
//   {"type": "status", "connected": true, "session_id": "sess-xxx"}
//   {"type": "error", "message": "Connection failed"}
//   {"type": "prompt", "data": "1a% "}  — command complete, prompt detected
func (s *Server) telnetWSHandler(w http.ResponseWriter, r *http.Request)

// bstoolWSHandler handles WebSocket for BsTool output streaming.
// URL: ws://host/api/v1/bstool/ws
// Messages from client: {"action": "execute", "server_name": "AP01", "command": "..."}
// Messages from server: {"type": "output", "data": "..."}, {"type": "done", "exit_code": 0}
func (s *Server) bstoolWSHandler(w http.ResponseWriter, r *http.Request)
```

**WebSocket library:** Use `github.com/gorilla/websocket` — add to go.mod.

**Route registration** (add to `server.go` `registerRoutes`):
```go
mux.HandleFunc("/api/v1/telnet/ws", s.telnetWSHandler)
mux.HandleFunc("/api/v1/bstool/ws", s.bstoolWSHandler)
```

**SessionManager** should be added to the `Server` struct:
```go
type Server struct {
    store        *store.Store
    startTime    time.Time
    config       *server.Config
    embedFS      embed.FS
    bstoolClient *bstool.Client
    telnetSM     *telnet.SessionManager  // NEW
}
```

#### 1E. Command Queue (`internal/commandqueue/queue.go`)

New package for sequential command execution:

```go
package commandqueue

// CommandType identifies the type of command to execute.
type CommandType string

const (
    CmdFBC    CommandType = "fbc"
    CmdRPC    CommandType = "rpc"
    CmdLOG    CommandType = "log"
    CmdBsTool CommandType = "bstool"
    CmdRaw    CommandType = "raw"
)

// QueuedCommand represents a single command in the queue.
type QueuedCommand struct {
    ID         string
    Type       CommandType
    NodeName   string
    TokenID    string
    Command    string    // resolved command string
    Status     string    // "pending", "running", "completed", "failed", "cancelled"
    Output     string
    Error      string
    StartedAt  *time.Time
    FinishedAt *time.Time
}

// Queue manages sequential command execution with pause/resume/cancel.
type Queue struct {
    commands  []QueuedCommand
    current   int
    paused    bool
    cancelled bool
    mu        sync.Mutex
    onOutput  func(cmd QueuedCommand)  // callback for output streaming
    onStatus  func(cmd QueuedCommand)  // callback for status changes
}

// NewQueue creates a new command queue.
func NewQueue(onOutput, onStatus func(QueuedCommand)) *Queue

// Add adds a command to the queue.
func (q *Queue) Add(cmd QueuedCommand)

// Start begins sequential execution. Blocks until queue is empty or cancelled.
func (q *Queue) Start() error

// Pause pauses execution after the current command completes.
func (q *Queue) Pause()

// Resume resumes execution from the paused position.
func (q *Queue) Resume()

// Cancel cancels all pending commands.
func (q *Queue) Cancel()

// Status returns the current queue state.
func (q *Queue) Status() (current int, total int, paused bool)

// AddBatchFromNodes generates FBC+RPC+LOG commands for all nodes in a NodeConfig list.
// Matches Python "Print All Nodes" behavior: for each node, for each token, generate
// the appropriate print command.
func (q *Queue) AddBatchFromNodes(configs []nodesconfig.NodeConfig, sessionID string, sm *telnet.SessionManager)
```

**AddBatchFromNodes logic** (matching Python `node_tree_presenter.py` `process_all_nodes_print_commands`):
```
for each node in configs:
    for each token in node.tokens:
        if token.type == FBC:
            add QueuedCommand{Type: CmdFBC, Command: FBCPrint(token.id)}
        if token.type == RPC:
            add QueuedCommand{Type: CmdRPC, Command: RPCPrint(token.id)}
        if token.type == LOG:
            add QueuedCommand{Type: CmdLOG, Command: ...}
```

#### 1F. Log Writer (`internal/logwriter/writer.go`)

New package for writing command output to per-node log files:

```go
package logwriter

// LogWriter writes command output to per-node log files.
type LogWriter struct {
    logRoot string  // root directory for log files
}

// New creates a LogWriter with the given root directory.
func New(logRoot string) *LogWriter

// WriteOutput appends command output to a node's log file.
// File path: {logRoot}/{nodeName}/{tokenType}_{tokenID}.log
func (lw *LogWriter) WriteOutput(nodeName, tokenType, tokenID, output string) error

// ReadLog reads the content of a node's log file.
func (lw *LogWriter) ReadLog(nodeName, tokenType, tokenID string) (string, error)

// ListLogs lists all log files for a node.
func (lw *LogWriter) ListLogs(nodeName string) ([]LogEntry, error)

// LogEntry represents a log file entry.
type LogEntry struct {
    FileName  string
    FilePath  string
    Size      int64
    ModifiedAt time.Time
}
```

#### 1G. New REST Endpoints

Add to `internal/api/handlers.go` (or new `handlers_commander.go`):

| Method | Path | Purpose |
|--------|------|---------|
| `GET` | `/api/v1/nodesconfig` | Load nodes.json, return as NodeConfig[] |
| `POST` | `/api/v1/nodesconfig` | Save nodes.json |
| `PUT` | `/api/v1/nodesconfig/load` | Load from file path (query param: path) |
| `GET` | `/api/v1/nodesconfig/tree` | Get hierarchical tree (BuildTree output) |
| `POST` | `/api/v1/telnet/connect` | Create persistent session (returns session_id) |
| `POST` | `/api/v1/telnet/{sessionID}/command` | Send command to session |
| `DELETE` | `/api/v1/telnet/{sessionID}` | Disconnect session |
| `GET` | `/api/v1/telnet/sessions` | List active sessions |
| `POST` | `/api/v1/commandqueue/add` | Add command to queue |
| `POST` | `/api/v1/commandqueue/start` | Start queue execution |
| `POST` | `/api/v1/commandqueue/pause` | Pause queue |
| `POST` | `/api/v1/commandqueue/resume` | Resume queue |
| `POST` | `/api/v1/commandqueue/cancel` | Cancel queue |
| `GET` | `/api/v1/commandqueue/status` | Get queue status |
| `POST` | `/api/v1/commandqueue/batch` | "Print All Nodes" — generate batch from nodes.json |
| `GET` | `/api/v1/logs/{nodeName}` | List log files for node |
| `GET` | `/api/v1/logs/{nodeName}/{fileName}` | Read specific log file |
| `POST` | `/api/v1/logs/{nodeName}` | Write/append log file (body: {token_type, token_id, output}) |
| `POST` | `/api/v1/scan/compare` | Compare file FBC data with live telnet scan |

**Scan compare request:**
```json
{
  "node_address": "192.168.1.101",
  "port": 2077,
  "token": "162",
  "file_data": "FBC agent 162\nPIC  5  6  7  8  sum\n0    AI8  BI8..."
}
```
**Response:**
```json
{
  "comparison": {
    "total_cells": 15,
    "matching": 12,
    "mismatched": 2,
    "file_only": 1,
    "live_only": 0,
    "cells": [
      {"row": 0, "col": 5, "file_value": "AI8", "live_value": "AI8", "status": "match"},
      {"row": 1, "col": 6, "file_value": "BI8", "live_value": "BO8", "status": "mismatch"}
    ]
  }
}
```

---

### Phase 2: Frontend — Commander UI

#### 2A. Commander Layout (`web/src/components/CommanderLayout.tsx`)

New route `/commander` with split-panel layout:
- Left panel (40% width): NodeTree
- Right panel (60% width): Tabbed interface (Telnet | BsTool | Scan)
- Bottom: Command queue status bar (if commands queued)

Add to `App.tsx` routes:
```tsx
<Route path="/commander" element={<CommanderLayout />} />
```

Add to `Layout.tsx` sidebar:
```tsx
<NavLink to="/commander" style={...}>
  <Terminal size={16} />
  Commander
</NavLink>
```

#### 2B. NodeTree Component (`web/src/components/NodeTree.tsx`)

Hierarchical tree component matching the original `node_tree_view.py`:

**Features:**
- Fetch tree from `GET /api/v1/nodesconfig/tree`
- Display as collapsible tree (use nested `<ul>` or a tree library like `react-arborescence` or simple recursive component)
- Node icons: green dot (connected), yellow (warning), red (error), gray (idle)
- Group nodes by token type (FBC, RPC, LOG, LIS) as expandable children
- Token leaves with port + protocol info
- Top buttons: "Load Nodes" (fetch from nodes.json), "Set Log Root" (folder prompt), "Print All Nodes" (POST /api/v1/commandqueue/batch)
- Control buttons: Pause, Resume, Cancel (enabled when queue active)
- Context menu (right-click on token leaf):
  - "FBC Print" → sends `print from fbc io structure {token}0000` to active telnet session
  - "RPC Print" → sends `print from fbc rupi counters {token}0000`
  - "BsTool ErrLog" → calls `POST /api/v1/bstool/errlog` with server name
  - "Copy to Log" → saves current terminal output to node's log file
- Double-click token → select node + switch to telnet tab with command pre-filled
- Status color updates after command execution (green=success, red=failure)

**Tree node rendering:**
```tsx
interface TreeNodeData {
  name: string;
  type: 'node' | 'group' | 'token';
  ip?: string;
  token_id?: string;
  port?: number;
  protocol?: string;
  status?: string;
  children?: TreeNodeData[];
}
```

#### 2C. TelnetTerminal Component (`web/src/components/TelnetTerminal.tsx`)

Interactive terminal matching the original `telnet_tab.py`:

**Features:**
- Connection bar: IP input, Port input, Connect/Disconnect buttons, status indicator (○/●)
- Terminal output: monospace `<pre>` element, auto-scroll to bottom, read-only
- Command input: `<input>` + Execute button, Enter to execute
- "Copy to Log" button → POST output to log writer
- "Clear Terminal" button → clear output display
- "Clear Log" button → clear node's log file
- Command history: up/down arrow navigation (store in component state)
- **WebSocket connection** to `/api/v1/telnet/ws` for real-time output streaming
- Output is filtered and displayed in monospace with ANSI color support (use `ansi-to-html` or display raw filtered text)

**WebSocket protocol:**
```typescript
// Connect
ws.send(JSON.stringify({action: 'connect', host: ip, port: port}));
// Send command
ws.send(JSON.stringify({action: 'command', command: cmd}));
// Disconnect
ws.send(JSON.stringify({action: 'disconnect'}));

// Receive
ws.onmessage = (event) => {
  const msg = JSON.parse(event.data);
  if (msg.type === 'output') appendToTerminal(msg.data);
  if (msg.type === 'status') updateConnectionIndicator(msg.connected);
  if (msg.type === 'error') showError(msg.message);
  if (msg.type === 'prompt') markCommandComplete();
};
```

**Command resolver** (client-side, matching `telnet_commands.py`):
```typescript
function resolveCommand(cmd: string, currentToken?: string): string {
  const resolver: Record<string, (token: string) => string> = {
    'ps': () => 'show all',
    'fis': (t) => `print_fieldbus ${t}0000`,
    'rc': (t) => `print_fieldbus_rupi_counters ${t}0000`,
  };
  // Check if command starts with a token followed by a keyword
  const parts = cmd.trim().toLowerCase().split(/\s+/);
  if (resolver[parts[0]]) return resolver[parts[0]](currentToken || parts[1] || '');
  return cmd; // pass through
}
```

#### 2D. BsToolPanel Component (`web/src/components/BsToolPanel.tsx`)

BsTool interface matching the original `bstool_tab.py`:

**Features:**
- BsTool path input (text field, auto-detect on mount)
- COMMUNICATION_LINE display (default "AB01")
- Status indicator
- Command input + Execute button
- Output display (monospace, read-only)
- "Copy to Log" / "Clear Terminal" buttons
- Uses `POST /api/v1/bstool/errlog` for execution (already exists in backend)
- For streaming output: WebSocket to `/api/v1/bstool/ws` (new endpoint)

#### 2E. ScanTab Component (`web/src/components/ScanTab.tsx`)

FBC/RPC comparison tables matching the original `node_scan_widget.py`:

**Features:**
- Per-node subtabs (one tab per node from tree)
- FBC table: rows = PIC positions, columns = channel positions
  - Color coding: match=green, mismatch=red, file-only=blue, live-only=amber, empty=gray, N/E=red
- RPC table: rows = PIC positions, columns = error counters
- "Compare with Live" button → POST /api/v1/scan/compare
- Auto-refresh dropdown: 5s, 10s, 30s, 60s, 300s (off by default)
- Countdown timer display when auto-refresh active
- Cell selection: click cell to see detailed comparison

#### 2F. CommandQueueBar Component (`web/src/components/CommandQueueBar.tsx`)

Bottom bar showing queue status:

**Features:**
- Progress: "Command 3/15: FBC Print AP01m token 162..."
- Pause/Resume/Cancel buttons
- Status indicator: running (green), paused (yellow), idle (gray)
- Polls `GET /api/v1/commandqueue/status` every 1s when active

#### 2G. NodeConfigDialog Component (`web/src/components/NodeConfigDialog.tsx`)

Node configuration editor matching `node_config_dialog.py`:

**Features:**
- Modal dialog
- Node list (add/remove/edit)
- Per-node: name, IP address, tokens (add/remove with type, port, protocol)
- Save → POST /api/v1/nodesconfig
- Load → GET /api/v1/nodesconfig
- "Load SysFile" button → uses existing /api/v1/parse/sysfile endpoint

---

### Phase 3: Integration

#### 3A. CommanderLayout Integration

The CommanderLayout ties together NodeTree + TelnetTerminal + BsToolPanel + ScanTab + CommandQueueBar:

```tsx
export default function CommanderLayout() {
  const [activeTab, setActiveTab] = useState<'telnet' | 'bstool' | 'scan'>('telnet');
  const [selectedNode, setSelectedNode] = useState<TreeNodeData | null>(null);
  const [currentToken, setCurrentToken] = useState<string>('');

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      <div style={{ display: 'flex', flex: 1 }}>
        <div style={{ width: '40%', borderRight: '1px solid var(--border)' }}>
          <NodeTree 
            onSelectNode={setSelectedNode}
            onSelectToken={(t) => { setCurrentToken(t.token_id || ''); }}
            onContextAction={handleContextAction}
          />
        </div>
        <div style={{ flex: 1 }}>
          <TabBar activeTab={activeTab} onTabChange={setActiveTab} />
          {activeTab === 'telnet' && <TelnetTerminal currentToken={currentToken} />}
          {activeTab === 'bstool' && <BsToolPanel />}
          {activeTab === 'scan' && <ScanTab selectedNode={selectedNode} />}
        </div>
      </div>
      <CommandQueueBar />
    </div>
  );
}
```

#### 3B. Context Menu Actions

When right-clicking a token in the tree:
- "FBC Print": switch to telnet tab, send `FBCPrint(token)` command
- "RPC Print": switch to telnet tab, send `RPCPrint(token)` command
- "BsTool ErrLog": switch to bstool tab, call ErrLog with node name (suffix stripped)
- "Copy to Log": save current terminal output to log file via LogWriter

#### 3C. "Print All Nodes" Batch

1. Fetch nodesconfig tree
2. POST /api/v1/commandqueue/batch with all nodes
3. Start queue execution
4. Stream output to telnet tab
5. Update tree node colors as commands complete (green=success, red=failure)

---

## CRITICAL GOTCHAS

1. **WebSocket library**: Add `github.com/gorilla/websocket` to go.mod. Use `websocket.Upgrader` with CheckOrigin that allows all (for dev).

2. **Go nil slice → JSON null**: Always initialize slices with `make([]T, 0)` before returning in API responses. The existing code already does this — follow the same pattern.

3. **Always relative API paths in frontend**: `fetch('/api/v1/...')` and `ws://window.location.host/api/v1/...` — never absolute IPs.

4. **Commit BEFORE build**: `git add -A && git commit -m "..."` before `npm run build` and `go build`. Vite transpiles undefined functions without error — only test live.

5. **Telnet buffer clearing**: Before sending a command, clear the input buffer. Python sends Ctrl+X (`\x18`) then Ctrl+Z (`\x1A`) with 100ms delay. Implement the same in the SessionManager.

6. **Node suffix stripping for BsTool**: "AP01m" → "AP01", "AP01r" → "AP01". The Go `bstool.stripNodeSuffix()` already handles this — use it.

7. **Command resolver**: The `ps` shorthand maps to `show all`, `fis` maps to `print_fieldbus {token}0000` (NOT `print from fbc io structure`). The `telnet_commands.py` resolver uses `print_fieldbus` while `command_generator.py` uses `print from fbc io structure`. The Go `commands.go` has both — use `FBCPrint()` for generated commands, `CommandResolver` for user input.

8. **Prompt detection**: The DNA debugger prompt is `<number><letter>% ` (e.g., `1a% `, `162b% `). The Go `promptPatterns` regexes match this. Use `ReadUntilPrompt()` for one-shot, prompt pattern matching in the SessionManager for streaming.

9. **Session ID generation**: Use `uuid` or `crypto/rand` to generate session IDs. Don't use predictable IDs.

10. **WebSocket ping/pong**: Implement ping/pong to detect dead connections. 30-second interval.

---

## TESTING REQUIREMENTS

1. **Unit tests** for each new Go package:
   - `internal/nodesconfig/loader_test.go` — parse nodes.json, build tree
   - `internal/telnet/session_test.go` — connect, send command, disconnect with mock server
   - `internal/commandqueue/queue_test.go` — add, start, pause, resume, cancel
   - `internal/logwriter/writer_test.go` — write, read, list log files

2. **Integration tests**:
   - WebSocket telnet session with mock DNA server
   - Command queue execution with mock telnet
   - "Print All Nodes" batch with mock nodes.json

3. **Frontend tests** (Vitest):
   - `CommanderLayout.test.tsx` — renders tree + tabs
   - `NodeTree.test.tsx` — tree rendering, context menu, selection
   - `TelnetTerminal.test.tsx` — WebSocket mock, command send, output display

4. **E2E test** (`test/e2e/commander_test.go`):
   - Load nodes.json → build tree → connect telnet → send FBC print → parse output → write log → generate report from logs

---

## FILE CREATION ORDER

1. `internal/types/node.go` — expand with Token, NodeConfig, TreeNode types
2. `internal/nodesconfig/loader.go` + `loader_test.go`
3. `internal/telnet/session.go` + `session_test.go`
4. `internal/commandqueue/queue.go` + `queue_test.go`
5. `internal/logwriter/writer.go` + `writer_test.go`
6. `internal/api/handlers_commander.go` — new REST endpoints
7. `internal/api/handlers_websocket.go` — WebSocket handlers
8. `internal/api/server.go` — register new routes, add SessionManager to Server
9. `go.mod` — add gorilla/websocket
10. `web/src/components/CommanderLayout.tsx`
11. `web/src/components/NodeTree.tsx`
12. `web/src/components/TelnetTerminal.tsx`
13. `web/src/components/BsToolPanel.tsx`
14. `web/src/components/ScanTab.tsx`
15. `web/src/components/CommandQueueBar.tsx`
16. `web/src/components/NodeConfigDialog.tsx`
17. `web/src/App.tsx` — add /commander route
18. `web/src/components/Layout.tsx` — add Commander nav link
19. `web/src/types/api.ts` — add new TypeScript types for Commander APIs

---

## EXISTING CODE PATTERNS TO FOLLOW

- **Go style**: Follow existing patterns in `internal/api/handlers.go` — `writeJSON()`, `writeError()`, `writeErrorDetails()`, request struct + JSON decode + validation + handler logic.
- **Go routing**: Use Go 1.22+ method patterns: `mux.HandleFunc("POST /api/v1/foo", handler)`
- **React style**: Follow existing `NodeBrowser.tsx` patterns — `useState`, `useEffect` for data fetching, `fetch('/api/v1/...')`, error handling with try/catch.
- **CSS**: Use existing CSS variables (`var(--bg-primary)`, `var(--text-secondary)`, `var(--accent)`, `var(--border)`, etc.)
- **Testing**: Follow existing test patterns in `internal/api/handlers_test.go` and `web/src/components/__tests__/`

---

## ORIGINAL PYTHON SOURCE REFERENCE

All original Python source is at:
`/opt/data/workspace-analyst/dev-cycle-logreport-20260615/source/src/commander/`

Key files to reference:
- `ui/commander_window.py` (686 lines) — main window structure
- `ui/node_tree_view.py` (254 lines) — tree widget
- `ui/telnet_tab.py` (186 lines) — telnet tab UI
- `ui/bstool_tab.py` (231 lines) — bstool tab UI
- `ui/node_scan_widget.py` (1006 lines) — scan tab with comparison
- `ui/commander_ui_factory.py` — UI factory
- `services/telnet_service.py` (416 lines) — telnet connection management
- `services/bstool_command_service.py` (690 lines) — bstool execution
- `services/fbc_command_service.py` (101 lines) — FBC command generation
- `services/fbc_comparison_service.py` (441 lines) — live vs file comparison
- `presenters/node_tree_presenter.py` (1904 lines) — tree logic + "Print All Nodes"
- `commands/telnet_commands.py` (114 lines) — command resolver + history
- `node_manager.py` (789 lines) — node config loading
- `log_writer.py` (247 lines) — log file writing
- `command_queue.py` — command queue
- `session_manager.py` — session state

Also reference:
- `src/nodes.json` — node configuration format
- `src/node_config_dialog.py` (793 lines) — node config editor