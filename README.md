# LOGReport

Valmet DNA report generation and Commander tool. Single Go binary with embedded React/TypeScript web UI and REST API.

## Quick Start

```bash
# Build (frontend + backend → single binary)
make build

# Run
./logreport --port 8080
```

Then open `http://localhost:8080` for the web UI, or use the REST API at `/api/v1/*`.

## What It Does

- Connects to Valmet DNA automation nodes via telnet
- Parses FBC/RPC module configurations and .sys files
- Generates commissioning reports (DOCX/JSON/PDF)
- Commander Window: interactive telnet terminal, BsTool error log extraction, node scanning, log file management
- Project management: group nodes + log root + reports per ship/work package

## Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                   LOGREPORT — SINGLE GO BINARY                    │
│                                                                    │
│  ┌────────────────────┐  ┌──────────────────────────────────┐   │
│  │  EMBEDDED WEB UI     │  │  REST API + WebSocket             │   │
│  │  React/TypeScript   │  │  /api/v1/* (74 endpoints)         │  │
│  │  Vite + Tailwind    │  │  2 WebSocket endpoints            │   │
│  │  AXON dark theme    │  │  JSON request/response            │   │
│  └────────┬───────────┘  └──────────────┬───────────────────┘   │
│           │                               │                       │
│           ▼                               ▼                       │
│  ┌──────────────────────────────────────────────────────────┐     │
│  │              HTTP SERVER (net/http, Go 1.22+)             │     │
│  │  /              → embedded static files (GUI)             │     │
│  │  /api/v1/*      → JSON REST handlers                     │     │
│  │  /health        → {"status":"ok","version":"..."}       │     │
│  │  Middleware: logging, CORS, content-type, recovery       │     │
│  └──────────────────────────────────────────────────────────┘     │
│                         │                                          │
│                         ▼                                          │
│  ┌──────────────────────────────────────────────────────────┐     │
│  │              CORE ENGINE (15 internal packages)           │     │
│  │  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌──────────────┐   │     │
│  │  │ Telnet   │ │ Parser  │ │ Store   │ │ Report Gen   │   │     │
│  │  │ Client   │ │ FBC/RPC │ │ (JSON)  │ │ DOCX/JSON/PDF│   │     │
│  │  └─────────┘ └─────────┘ └─────────┘ └──────────────┘   │     │
│  │  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌──────────────┐   │     │
│  │  │ BsTool   │ │ CmdQueue│ │ Nodes   │ │ SysLoader    │   │     │
│  │  │ TCP/RE   │ │ Sequencer│ │ Config  │ │ .sys parser  │   │     │
│  │  └─────────┘ └─────────┘ └─────────┘ └──────────────┘   │     │
│  │  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌──────────────┐   │     │
│  │  │ LogFile  │ │ LogWriter│ │ LisDiag │ │ Browser      │   │     │
│  │  │ Scanner  │ │ Per-node │ │ Client  │ │ Auto-launch  │   │     │
│  │  └─────────┘ └─────────┘ └─────────┘ └──────────────┘   │     │
│  └──────────────────────────────────────────────────────────┘     │
│                                                                    │
│  STORE: JSON file-based (no SQLite, no CGo)                        │
│  DEPLOY: ./logreport --port 8080                                   │
│  BUILD:  make build  (= npm build && go build)                    │
│  EMBED:  //go:embed all:web/dist-new-flat                          │
└──────────────────────────────────────────────────────────────────┘
```

### Package Layout (15 internal packages + cmd + root)

```
cmd/logreport/          # Main entry point, banner, flag parsing
cmd/bstool-debug/       # BsTool protocol debug utilities (3 variants)
cmd/bstool-mitm/        # BsTool MITM tool for protocol reverse engineering
internal/
  api/                  # HTTP handlers (74 endpoints), middleware, WebSocket, server
  browser/              # Auto-launch browser for headless hosts
  bstool/               # BsTool wrapper + native TCP transport (RE'd protocol)
  commandqueue/         # Sequential command execution with pause/resume/cancel/clear/reorder
  lisdiag/              # LISDIAG telnet client for remote LIS frame capture
  logfile/              # Log root directory scanner (.fbc/.rpc/.log/.lis)
  logwriter/            # Per-node log file writer
  nodesconfig/          # nodes.json loader, tree builder, station naming
  parser/               # FBC, RPC, and SysFile parsers
  report/               # DOCX, JSON, PDF report generation
  server/               # Config, health, graceful shutdown
  store/                # JSON file-based persistence (nodes, IO points, reports, projects, templates)
  sysloader/            # .sys file loader → NodeConfig + folder structure creation
  telnet/               # Native Go telnet client for DNA nodes
  types/                # Core types: Node, IOPoint, FBCModule, RPCModule, Report, SysFile, Project, NodeConfig, TreeNode
embed.go                # //go:embed all:web/dist-new-flat (package assets)
web/                    # React/TypeScript frontend (Vite + Tailwind)
```

### API Endpoints (74 registered routes)

**Health & Connectivity:**
- `GET /health` — version, uptime, DB status, node count
- `GET /api/v1/health` — same, under API prefix
- `POST /api/v1/connect` — connect to DNA node via telnet

**Nodes:**
- `GET /api/v1/nodes` — list known DNA nodes
- `GET /api/v1/nodes/{addr}` — node detail + IO summary (FBC/RPC counts)
- `POST /api/v1/nodes/{addr}/scan` — run FBC_PRINT + RPC_PRINT, parse, store
- `DELETE /api/v1/nodes/{addr}` — delete node from store
- `POST /api/v1/nodes/{addr}/rename` — rename node in store
- `GET /api/v1/nodes/{addr}/fbc` — FBC module IO points
- `GET /api/v1/nodes/{addr}/rpc` — RPC module IO points

**Reports:**
- `POST /api/v1/reports/generate` — generate DOCX/JSON/PDF report
- `GET /api/v1/reports` — list all generated reports
- `GET /api/v1/reports/{id}` — download report or get metadata
- `DELETE /api/v1/reports/{id}` — delete report

**SysFile Parsing:**
- `POST /api/v1/parse/sysfile` — upload .sys file, get parsed node entries
- `POST /api/v1/sysfiles/load` — load .sys files from disk
- `GET /api/v1/sysfiles/parse` — parse .sys files in a directory
- `GET /api/v1/sysfiles/scan` — scan directory for .sys files
- `POST /api/v1/sysfiles/parse-multi` — parse multiple .sys files
- `POST /api/v1/sysfiles/scan-nodes` — scan nodes via DIA debugger or BsTool TCP

**BsTool:**
- `POST /api/v1/bstool/errlog` — BsTool error log extraction
- `GET /api/v1/bstool/ws` — WebSocket for BsTool interactive session

**Telnet (Commander):**
- `POST /api/v1/telnet/connect` — open telnet session to node
- `POST /api/v1/telnet/execute` — execute single DIA command with node context
- `POST /api/v1/telnet/{sessionID}/command` — send command to open session
- `DELETE /api/v1/telnet/{sessionID}` — close telnet session
- `GET /api/v1/telnet/sessions` — list active telnet sessions
- `GET /api/v1/telnet/{sessionID}/output` — get session output buffer
- `GET /api/v1/telnet/ws` — WebSocket persistent telnet terminal

**Command Queue:**
- `POST /api/v1/commandqueue/add` — add command to queue
- `POST /api/v1/commandqueue/start` — start queue execution
- `POST /api/v1/commandqueue/pause` — pause queue
- `POST /api/v1/commandqueue/resume` — resume queue
- `POST /api/v1/commandqueue/cancel` — cancel queue
- `POST /api/v1/commandqueue/clear` — clear all commands from queue
- `POST /api/v1/commandqueue/remove` — remove specific command from queue
- `POST /api/v1/commandqueue/reorder` — reorder commands in queue
- `POST /api/v1/commandqueue/restart` — restart queue execution
- `GET /api/v1/commandqueue/status` — queue status
- `POST /api/v1/commandqueue/batch` — batch add commands
- `POST /api/v1/commandqueue/batch-node` — batch add commands for a specific node

**Nodes Config:**
- `GET /api/v1/nodesconfig` — get nodes.json configuration
- `POST /api/v1/nodesconfig` — save nodes.json configuration
- `PUT /api/v1/nodesconfig/load` — load nodes.json from file
- `GET /api/v1/nodesconfig/tree` — get hierarchical tree structure for frontend
- `POST /api/v1/nodesconfig/create-structure` — create FBC/RPC/LOG/LIS folder structure on disk
- `DELETE /api/v1/nodesconfig/delete-structure` — delete folder structure
- `DELETE /api/v1/nodesconfig/entry` — delete node entry from nodes.json
- `POST /api/v1/nodesconfig/rename` — rename node entry in nodes.json

**Log Files:**
- `GET /api/v1/logs/{nodeName}` — list log files for a node
- `GET /api/v1/logs/{nodeName}/{fileName}` — read log file content
- `POST /api/v1/logs/{nodeName}` — write log file
- `POST /api/v1/logs/save` — save log file content
- `GET /api/v1/logs/list` — list log root directory
- `GET /api/v1/logs/files` — list all log files
- `GET /api/v1/logs/content` — get log file content by path
- `POST /api/v1/logs/setroot` — set log root directory
- `POST /api/v1/logs/erase` — erase (empty) a log file
- `POST /api/v1/logs/delete` — delete a log file from disk
- `POST /api/v1/logs/create` — create a new empty log file
- `POST /api/v1/logs/move` — move/rename a log file
- `POST /api/v1/logs/create-folder` — create a new folder on disk

**Scan:**
- `POST /api/v1/scan/compare` — scan comparison between nodes

**Projects:**
- `POST /api/v1/projects` — create project
- `GET /api/v1/projects` — list projects
- `GET /api/v1/projects/{id}` — project detail
- `PUT /api/v1/projects/{id}` — update project
- `DELETE /api/v1/projects/{id}` — delete project
- `POST /api/v1/projects/{id}/report` — generate report for project
- `GET /api/v1/projects/{id}/nodes` — get project-scoped nodes config
- `POST /api/v1/projects/{id}/nodes` — save project-scoped nodes config

**Settings:**
- `GET /api/v1/settings` — read settings (DIA host/port, BsTool host/port, log root, output dir, scan method, node filter)
- `POST /api/v1/settings` — save settings

**Directory Browsing:**
- `GET /api/v1/browse` — browse directory for path selection

## Build

```bash
make build              # Build full binary (npm build + go build)
make test               # Run unit tests
make test-integration   # Run integration tests
make vet                # Run go vet
make release            # Release build with version stamp
make clean              # Remove build artifacts
make dev                # Dev mode: separate Vite dev server + Go API
make run                # Build and run on default port (8642)
make run PORT=9000      # Build and run on custom port
```

## Server Flags

```
--port int          HTTP server port (default 8642)
--db-path string    Data directory path for JSON store (default "logreport-data")
--log-level string  Log level: debug, info, warn, error (default "info")
--cors-origin       Allowed CORS origin (default "" = no CORS)
--bstool-path       Path to BsTool.exe (auto-detect if empty)
--bstool-remote     Hermes-remote agent for remote BsTool execution
--bstool-timeout    BsTool timeout in seconds (default 15)
--communication-line  DNA node hostname/IP for TCP transport (default "AB01")
--version           Print version and exit
--help              Print usage and exit
```

## Deployment

- **Target:** Windows VM (Valmet DNA environment) — cross-compiled LOGReport.exe
- **Cross-compile:** `GOOS=windows GOARCH=amd64 CGO_ENABLED=0 go build -o LOGReport.exe ./cmd/logreport/`
- **No CGo required** — store is JSON file-based, pure Go stdlib

## License

MIT — see [LICENSE](LICENSE)