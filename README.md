# LOGReport

**Structured log analysis & reporting tool for Valmet DNA automation systems.**

Version: **v3.9.84**

LOGReport scans fieldbus (FBC), RPC, log, and LIS files from Valmet DNA control system backups, generates structured PDF/DOCX/JSON reports, and provides a web-based commander UI for node management, telnet sessions, and BsTool integration.

## Architecture

LOGReport is a Go backend + React frontend single-binary application. The React frontend is embedded into the Go binary at build time.

| Layer | Tech | Location |
|-------|------|----------|
| Backend | Go 1.22+ | `cmd/logreport/`, `internal/` |
| Frontend | React 18 + TypeScript + Vite | `web/src/` |
| Embedded UI | Go `embed.FS` | `embed.go` → `web/dist-new-flat/` |
| Legacy Python | PyQt5 (historical) | `src/` (not built, kept for reference) |

### Backend Packages (`internal/`)

| Package | Purpose |
|---------|---------|
| `internal/api` | HTTP handlers — REST API, project CRUD, report generation, node config, telnet, command queue, BsTool |
| `internal/report` | Report generation — PDF, DOCX, JSON. `outputPathForConfig` builds descriptive filenames |
| `internal/parser` | SysFile parser, FBC/RPC/LIS log parsers |
| `internal/logfile` | Log file scanner — discovers .fbc/.rpc/.log/.lis files in a log root |
| `internal/nodesconfig` | Node configuration load/save (`nodes.json`) |
| `internal/store` | SQLite-backed project store |
| `internal/telnet` | Telnet client for node communication |
| `internal/bstool` | BsTool.exe integration (FBC analysis tool) |
| `internal/lisdiag` | LisDiag integration (LIS file diagnostics) |
| `internal/commandqueue` | Sequential command queue for batch operations |
| `internal/server` | HTTP server, health endpoint, middleware |
| `internal/types` | Shared type definitions (ReportConfig, etc.) |
| `internal/logwriter` | Log file writing utilities |

### Frontend (`web/src/`)

| Component | Purpose |
|-----------|---------|
| `Dashboard.tsx` | Project list, create/edit/delete, health display |
| `CommanderLayout.tsx` | Main layout, node tree, telnet tabs |
| `NodeTree.tsx` | Hierarchical node tree with FBC/RPC/LOG/LIS sections |
| `ReportList.tsx` | Report list with descriptive filenames, download |
| `ReportConfig.tsx` | Report configuration form |
| `StatusBar.tsx` | Bottom status bar with project info and node count |
| `CommandQueueBar.tsx` | Sequential command queue UI |

## Build

### Prerequisites

- Go 1.22+ (tested with Go 1.23.12)
- Node.js 18+ and npm (for frontend build)

### Build steps

```bash
# 1. Build frontend
cd web && npm install && npm run build

# 2. Copy build to embed directory
# (Vite outputs to web/dist-new-flat/ which is embedded by Go)

# 3. Build backend with version injection
go build -ldflags "-X main.version=v3.9.84" -o logreport ./cmd/logreport/

# Or build for Windows:
GOOS=windows GOARCH=amd64 go build -ldflags "-X main.version=v3.9.84" -o logreport-x64.exe ./cmd/logreport/
```

### Run

```bash
./logreport --port 8642 --db-path logreport-data
```

The binary serves the React UI and REST API on the same port. Open `http://localhost:8642` in a browser.

### Flags

| Flag | Default | Description |
|------|---------|-------------|
| `--port` | 8642 | HTTP server port |
| `--db-path` | logreport-data | Data directory |
| `--log-level` | info | debug, info, warn, error |
| `--bstool-path` | auto | Path to BsTool.exe |
| `--bstool-remote` | | Hermes-remote agent URL for BsTool |
| `--bstool-timeout` | 15 | BsTool timeout in seconds |
| `--browser` | auto | Browser exe path (Supermium auto-detect) |
| `--no-browser` | false | Disable auto-launching browser |
| `--version` | | Print version and exit |

## REST API

Base URL: `http://localhost:8642/api/v1`

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check (accepts `?project_id=` for project-specific node count) |
| `/projects` | GET, POST | List/create projects |
| `/projects/{id}` | GET, PUT, DELETE | Project CRUD |
| `/projects/{id}/report` | POST | Generate report for project |
| `/projects/{id}/export` | GET | Export project as zip |
| `/reports` | GET | List all reports |
| `/reports/{id}` | GET | Download report file |
| `/nodesconfig` | GET, POST | Load/save node config (accepts `?project_id=`) |
| `/nodesconfig/entry` | DELETE | Delete node entry (accepts `?project_id=`) |
| `/nodesconfig/rename` | POST | Rename node entry |
| `/connect` | POST | Telnet connect |
| `/bstool/*` | various | BsTool operations |
| `/queue/*` | various | Command queue operations |

## Report Generation Flow (v3.9.84)

1. **Project selection** — user selects a project (ProjectNumber + ShipName + log_root)
2. **Path resolution** — if `log_root` already ends with `{project}_{ship}`, use it directly (Bug #1 fix prevents doubled paths)
3. **File scan** — `logfile.ScanFiles(logRoot)` discovers all .fbc/.rpc/.log/.lis files
4. **Config** — `ReportConfig` is built with `ProjectNumber`, `ShipName`, `LogRoot`, and `OutputDir = {logRoot}/reports/`
5. **Generation** — `report.Generate(cfg)` processes scan entries and builds the report
6. **Output filename** — `outputPathForConfig()` creates `{ProjectNumber}_{ShipName}_{date}.{ext}` (e.g., `G0001_GORIZIA_TEST_2026-07-28.pdf`) — not UUID (Bug #2 fix)
7. **Save location** — report saved to `{logRoot}/reports/` folder (Bug #4 fix, was saving to parent directory)
8. **ReportList** — frontend extracts filename from `file_path` for display (not raw UUID report_id)

## Key Fixes in v3.9.84

Eight workflow bugs fixed in this release:

1. **Doubled project path** — if `log_root` already ends with `{project}_{ship}`, the path is used directly instead of appending the project folder name again
2. **UUID report filename** — reports now use descriptive names (`G0001_GORIZIA_TEST_2026-07-28.pdf`) instead of random UUIDs
3. **2KB PDF reports** — scanner was finding files in the wrong (doubled) path; fixed by Bug #1 path resolution fix. Reports are now ~50KB with actual content
4. **Wrong save location** — reports saved to `{logRoot}/reports/` instead of the parent directory
5. **All Nodes selection** — was a metadata display issue; content was correct. Fixed by the path resolution fix
6. **nodes.json location** — inconsistent location was caused by the doubled path bug. Fixed by Bug #1
7. **Node count shows 0** — health endpoint now accepts `?project_id=` param to count nodes from the project-specific `nodes.json`
8. **"No project selected" persists** — StatusBar shows `Project #ID` fallback when the project object is not yet loaded in the frontend

All 15 internal Go packages pass tests.

## Development

### Run tests

```bash
# Go tests
go test ./internal/...

# Frontend tests
cd web && npm test
```

### Project structure

```
LOGReport/
├── cmd/
│   └── logreport/          # Main entry point (main.go)
├── internal/               # Go backend packages (15 packages)
│   ├── api/                # HTTP handlers, REST API
│   ├── report/             # Report generation (PDF, DOCX, JSON)
│   ├── parser/             # SysFile and log parsers
│   ├── logfile/            # File scanner
│   ├── nodesconfig/        # Node configuration
│   ├── store/              # SQLite store
│   ├── telnet/             # Telnet client
│   ├── bstool/             # BsTool integration
│   ├── lisdiag/            # LisDiag integration
│   ├── commandqueue/       # Command queue
│   ├── server/             # HTTP server, health
│   ├── types/              # Shared types
│   └── logwriter/          # Log writer
├── web/                    # React frontend
│   └── src/
│       ├── components/     # React components
│       ├── api/            # API client functions
│       ├── hooks/          # Custom hooks
│       └── types/          # TypeScript types
├── embed.go                # Go embed directive for web/dist-new-flat/
├── go.mod                  # Go module: github.com/falke-ai-circuit/LOGReport
└── src/                    # Legacy Python/PyQt5 source (not built)
```

## Deployment

Deploy to target machines (Vegas VM, Gorizia production) via PROBE chunked upload. See the operational deployment documentation for details.

## License

Proprietary — Falke AI Circuit.