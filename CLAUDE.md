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
│  │  React/TypeScript   │  │  /api/v1/* (74 endpoints)     │  │
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
- **Vite outDir:** `dist-new-flat` (matches embed — build pipeline correct).
- **Routes:** 74 `/api/v1/*` endpoints + `/health` + `/` SPA fallback = 76 registered routes.
- **Packages:** 15 internal packages (api, browser, bstool, commandqueue, lisdiag, logfile, logwriter, nodesconfig, parser, report, server, store, sysloader, telnet, types).
- **Go version:** 1.22 (go.mod).
- **Go files:** 70 non-test + 53 test = 123 total (37,011 LOC).
- **Frontend:** 79 .tsx/.ts files, React 18 + Vite 5 + Tailwind 4, 14 test files (Vitest).
- **Scan methods:** `remote_bu` (BsTool TCP protocol, default), `local_dir` (.sys files on disk), `local_exe` (BsTool.exe subprocess — auto-detected in LOGReport root, added v3.9.56).
- **BsTool execution:** Subprocess-first, TCP-fallback. Shared `executeBsToolErrLog()` in `handlers_bstool_exec.go`. BsTool.exe auto-detected in LOGReport root on startup.
- **BsTool TCP timeout:** Minimum 5s (raised from 1516ms serial-era default in v3.9.57).
- **Project-specific settings:** `SettingsJSON` on `Project` struct. `GET/POST /api/v1/settings?project_id=X`. `mergeSettings()` overlays project over global. `getSettingsForProject()` helper.
- **Node detection:** XdSysUsed filter is case-insensitive. Node filter (AP,AL,BP,BL) applied after XdSysUsed. `isFieldbusLID()` distinguishes CPU (_main/_reserve → LOG) from fieldbus (_m2/_m3/_r2/_r3 → FBC+RPC) slots.
- **Token structure:** AP = 1 LOG (CPU) + 2 FBC + 2 RPC (fieldbus). AL = LIS + LOG (6 .lis + 1 .log). A1O/A1A/B1O/B1A = LOG only.
- **LisDiag .lis format:** Each file contains `=== Active Exes ===` (bare `exe` response) + `=== IO Output (exe N) ===` (per-exe io frames). `io` sent without number (shows all frames).

## Known Issues

- **handlers.go God File:** `handlers.go` is 1,350 LOC with 28 functions spanning nodes, reports, sysfile parsing, and BsTool error log. Candidate for domain-based split.
- **Makefile stale comments:** `web-build` and `go-build` target comments say "web/dist/" but actual embed path is "web/dist-new-flat/". Cosmetic — build commands work correctly.

## Resolved Issues (2026-07-09, commit feda78db)

- ~~Vite outDir mismatch~~ — FIXED: changed to `dist-new-flat`.
- ~~Stale comments~~ — FIXED: server.go, main.go, Makefile clean target, embed.go all corrected.
- ~~Dead code go-backend/~~ — FIXED: deleted (35 files).
- ~~Barnacles~~ — FIXED: 13 .py + 2 .exe moved to scripts/archive/, 10 .md moved to docs/archive/.
- ~~handlers_commander.go 2684 LOC~~ — FIXED: split into 5 domain files (95 LOC stub + 5 files).
- ~~NodesPage.tsx 1389 LOC~~ — FIXED: split into 3 files (489 LOC root + 2 components).
