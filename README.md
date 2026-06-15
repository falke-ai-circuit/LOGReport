# LOGReport

Valmet DNA report generation tool. Single Go binary with embedded React/TypeScript web UI and REST API.

## Quick Start

```bash
# Build
make build

# Run
./cmd/logreport/logreport --port 8080
```

Then open `http://localhost:8080` for the web UI, or use the REST API at `/api/v1/*`.

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/health` | Binary version, uptime, DB status |
| `POST` | `/api/v1/connect` | Connect to DNA node via telnet |
| `GET` | `/api/v1/nodes` | List connected/known DNA nodes |
| `GET` | `/api/v1/nodes/{addr}` | Node detail + IO summary |
| `POST` | `/api/v1/nodes/{addr}/scan` | Run MOD_LIST + IO_LIST on node |
| `GET` | `/api/v1/nodes/{addr}/fbc` | FBC module IO points |
| `GET` | `/api/v1/nodes/{addr}/rpc` | RPC module IO points |
| `POST` | `/api/v1/parse/sysfile` | Upload .sys file, get parsed nodes |
| `POST` | `/api/v1/reports/generate` | Generate report from node data |
| `GET` | `/api/v1/reports/{id}` | Download generated report |
| `GET` | `/api/v1/reports` | List generated reports |

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
│  │  /health        → {"status":"ok","version":"x.y.z"}  │   │
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

## Build

```bash
make build          # Build full binary (npm build + go build)
make test           # Run unit tests
make vet            # Run go vet
make test-integration  # Run integration tests
make clean          # Remove build artifacts
```

## License

MIT
