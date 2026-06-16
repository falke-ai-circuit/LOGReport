# LOGReport v1.0.0

Valmet DNA report generation tool. Single Go binary with embedded React/TypeScript web UI and REST API.

## Quick Start

```bash
# Build
make build

# Run
./logreport --port 8080
```

Then open `http://localhost:8080` for the web UI, or use the REST API at `/api/v1/*`.

## API Endpoints (11 total)

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/health` | Binary version, uptime, DB status, node count |
| `POST` | `/api/v1/connect` | Connect to DNA node via telnet |
| `GET` | `/api/v1/nodes` | List connected/known DNA nodes |
| `GET` | `/api/v1/nodes/{addr}` | Node detail + IO summary (FBC/RPC counts) |
| `POST` | `/api/v1/nodes/{addr}/scan` | Run FBC_PRINT + RPC_PRINT on node, parse and store IO points |
| `GET` | `/api/v1/nodes/{addr}/fbc` | FBC module IO points from store |
| `GET` | `/api/v1/nodes/{addr}/rpc` | RPC module IO points from store |
| `POST` | `/api/v1/parse/sysfile` | Upload .sys file, get parsed node entries |
| `POST` | `/api/v1/reports/generate` | Generate DOCX or JSON report from node scan data |
| `GET` | `/api/v1/reports` | List all generated reports |
| `GET` | `/api/v1/reports/{id}` | Download report file or get metadata |

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│              LOGREPORT — SINGLE GO BINARY                    │
│                                                              │
│  ┌────────────────────┐  ┌──────────────────────────────┐  │
│  │  EMBEDDED WEB UI    │  │  REST API (functional only)  │  │
│  │  React/TypeScript   │  │  /api/v1/*                    │  │
│  │  Vite + Tailwind    │  │  JSON request/response        │  │
│  │  AXON dark theme    │  │  Agent-consumable             │  │
│  └────────┬───────────┘  └──────────────┬───────────────┘  │
│           │                             │                   │
│           ▼                             ▼                   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │              HTTP SERVER (net/http)                   │   │
│  │  /              → embedded static files (GUI)         │   │
│  │  /api/v1/*      → JSON REST handlers                 │   │
│  │  /health        → {"status":"ok","version":"1.0.0"}  │   │
│  └──────────────────────────────────────────────────────┘   │
│                         │                                    │
│                         ▼                                    │
│  ┌──────────────────────────────────────────────────────┐   │
│  │              CORE ENGINE                              │   │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌─────────┐ │   │
│  │  │ Telnet   │ │ FBC/RPC  │ │ SQLite   │ │ Report  │ │   │
│  │  │ Client   │ │ Parser   │ │ Store    │ │ Gen     │ │   │
│  │  └──────────┘ └──────────┘ └──────────┘ └─────────┘ │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                              │
│  DEPLOY: ./logreport --port 8080                             │
│  BUILD:  make build  (= npm build && go build)              │
└─────────────────────────────────────────────────────────────┘
```

### Package Layout

```
cmd/logreport/          # Main entry point
internal/
  api/                  # HTTP handlers (11 endpoints), middleware, server
  parser/               # FBC, RPC, and SysFile parsers
  report/               # DOCX and JSON report generator
  server/               # Config, health, graceful shutdown
  store/                # SQLite persistence (nodes, IO points, reports, templates)
  telnet/               # Native Go telnet client for DNA nodes
  types/                # Core types: Node, IOPoint, FBCModule, RPCModule, Report, SysFile
web/                    # React/TypeScript frontend (Vite + Tailwind)
embed.go                # //go:embed web/dist/* for single-binary deployment
```

## Build

```bash
make build              # Build full binary (npm build + go build)
make test               # Run unit tests (>80% coverage)
make test-integration   # Run integration tests
make vet                # Run go vet
make release            # Goreleaser release build
make clean              # Remove build artifacts
make dev                # Dev mode: separate Vite dev server + Go API
```

## License

MIT — see [LICENSE](LICENSE)
