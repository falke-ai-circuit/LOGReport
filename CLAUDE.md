# CLAUDE.md — LOGReport

This is the LOGReport project — a Valmet DNA report generation and Commander tool.

## What It Is

A single Go binary (`logreport`) that connects to Valmet DNA automation nodes via telnet, parses FBC/RPC module configurations and .sys files, stores data in JSON file-based storage (no SQLite, no CGo), and generates commissioning reports (DOCX/JSON/PDF). Includes an embedded React/TypeScript web UI with AXON dark theme and a Commander Window for interactive telnet, BsTool error log extraction, node scanning, and log file management.

## How to Build

```bash
make build          # npm build + go build → single binary
```

## How to Run

```bash
./logreport --port 8080
```

Then open `http://localhost:8080` for the web UI, or use the REST API at `/api/v1/*`.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│              LOGREPORT — SINGLE GO BINARY                    │
│                                                              │
│  ┌────────────────────┐  ┌──────────────────────────────┐  │
│  │  EMBEDDED WEB UI    │  │  REST API + WebSocket         │  │
│  │  React/TypeScript   │  │  /api/v1/* (73 endpoints)     │  │
│  │  Vite + Tailwind    │  │  2 WebSocket endpoints        │  │
│  │  AXON dark theme    │  │  JSON request/response        │  │
│  └────────┬───────────┘  └──────────────┬───────────────┘  │
│           │                             │                   │
│           ▼                             ▼                   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │              HTTP SERVER (net/http, Go 1.22+)         │   │
│  │  /              → embedded static files (GUI)         │   │
│  │  /api/v1/*      → JSON REST handlers                 │   │
│  │  /health        → {"status":"ok","version":"..."}    │   │
│  │  Middleware: logging, CORS, content-type, recovery   │   │
│  └──────────────────────────────────────────────────────┘   │
│                         │                                    │
│                         ▼                                    │
│  ┌──────────────────────────────────────────────────────┐   │
│  │          CORE ENGINE (15 internal packages)           │   │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌─────────┐ │   │
│  │  │ Telnet   │ │ FBC/RPC  │ │ JSON     │ │ Report  │ │   │
│  │  │ Client   │ │ Parser   │ │ Store    │ │ Gen     │ │   │
│  │  └──────────┘ └──────────┘ └──────────┘ └─────────┘ │   │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌─────────┐ │   │
│  │  │ BsTool   │ │ CmdQueue │ │ Nodes    │ │ SysLoad │ │   │
│  │  │ TCP/RE   │ │ Sequencer│ │ Config   │ │ .sys    │ │   │
│  │  └──────────┘ └──────────┘ └──────────┘ └─────────┘ │   │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌─────────┐ │   │
│  │  │ LogFile  │ │ LogWriter│ │ LisDiag  │ │ Browser │ │   │
│  │  │ Scanner  │ │ Per-node │ │ Client   │ │ Launch  │ │   │
│  │  └──────────┘ └──────────┘ └──────────┘ └─────────┘ │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                              │
│  STORE: JSON file-based (no SQLite, no CGo)                  │
│  EMBED: //go:embed all:web/dist-new-flat                     │
│  DEPLOY: ./logreport --port 8080                             │
│  BUILD:  make build  (= npm build && go build)              │
└─────────────────────────────────────────────────────────────┘
```

Single binary, embedded web UI, REST API. No separate server process. `./logreport --port 8080` = everything running.

## Key Facts

- **Store:** JSON file-based (in-memory maps backed by JSON files with atomic writes). No SQLite, no CGo.
- **Embed:** `//go:embed all:web/dist-new-flat` in embed.go. Server reads via `fs.Sub(s.embedFS, "web/dist-new-flat")`.
- **Routes:** 73 `/api/v1/*` endpoints + `/health` + `/` SPA fallback = 75 registered routes.
- **Packages:** 15 internal packages (api, browser, bstool, commandqueue, lisdiag, logfile, logwriter, nodesconfig, parser, report, server, store, sysloader, telnet, types).
- **Go version:** 1.22 (go.mod).
- **Frontend:** 67 .tsx/.ts files, React 18 + Vite 5 + Tailwind 4, 13 test files (Vitest).

## Known Issues

- **Vite outDir mismatch:** `vite.config.ts` outputs to `dist-new` but `embed.go` and `server.go` expect `dist-new-flat`. Fresh `make build` produces a binary with an empty embed — GUI 404s. Fix: change `outDir` in vite.config.ts to `dist-new-flat`.
- **Stale comments:** `server.go` says "11 routes" (actual: 75). `main.go` says "Open the SQLite store" (actual: JSON). Makefile clean target removes `web/dist/` (actual: `web/dist-new-flat/`).
- **Dead code:** `go-backend/` directory is a Go 1.19 module from an earlier iteration (module `github.com/goranjovic55/LOGReport`). Should be removed.
- **Barnacles:** 13 .py scripts in repo root (upload_v*.py, test_*.py, verify_*.py, debug_*.py) from Python era. Should be moved to `scripts/` or deleted.
