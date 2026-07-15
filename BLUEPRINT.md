# LOGReport Refactor — Operational Blueprint
## Go Single-Binary + Embedded Web UI + REST API

---

> ## RECONCILIATION BLOCK (2026-07-15 — Coder)
>
> **Reconciled against:** main branch commit d40bdea2 (v3.9.58) + docs commit 411a429a
> **Method:** G-RECON live probes (git log, file counts, LOC, route extraction, package list, handler LOC)
> **Prior reconciliation:** 2026-07-11 at commit fd48f854 (v3.9.12) — all drift items HELD (no regressions)
>
> ### Design Intent → Actual State
>
> | Item | Blueprint Says | Actual on Main (d40bdea2) | Status |
> |------|---------------|--------------------------|--------|
> | Scope | Report pipeline only, Commander excluded | Report pipeline + Commander + BsTool + LisDiag + Project-Specific Settings | RESOLVED — Commander added back, LisDiag added 2026-07-11, project settings added 2026-07-15 |
> | Store | SQLite | JSON file-based (no SQLite, no CGo) | RESOLVED — migration completed 2026-06-30 |
> | Endpoints | 12 | 74 `/api/v1/*` + `/health` + `/` = 76 total | RESOLVED — grew with Commander, Queue, Projects, Settings (incl. project-specific), Logs, Scan, LisDiag |
> | Packages | Not specified | 15 internal packages | RESOLVED — api, browser, bstool, commandqueue, lisdiag, logfile, logwriter, nodesconfig, parser, report, server, store, sysloader, telnet, types |
> | Embed path | `web/dist/` | `//go:embed all:web/dist-new-flat` | RESOLVED — directory renamed |
> | Vite outDir | Not specified | `dist-new-flat` (matches embed) | RESOLVED — fixed in feda78db |
> | Frontend | Not specified | 79 .tsx/.ts files, React 18 + Vite 5 + Tailwind 4 | RESOLVED |
> | Version | 1.1.1 | v3.9.58 (per CHANGELOG) | RESOLVED |
> | Go files | Not specified | 70 non-test + 53 test = 123 (37,011 LOC) | RESOLVED |
> | Scan methods | Not specified | 3: remote_bu (TCP), local_dir (.sys on disk), local_exe (BsTool.exe subprocess) | RESOLVED — local_exe added v3.9.56 |
> | BsTool execution | Not specified | Subprocess-first, TCP-fallback via executeBsToolErrLog() | RESOLVED — added v3.9.56 |
> | Project settings | Not specified | SettingsJSON on Project, GET/POST /api/v1/settings?project_id=X, mergeSettings() overlay | RESOLVED — added v3.9.57 |
>
> ### Open Drift Items
>
> 1. **handlers.go God File (1,350 LOC):** 28 functions spanning nodes, reports, sysfile parsing, BsTool error log. Candidate for domain-based split. (Was 1,374 at fd48f854 — shrank slightly.)
> 2. **Makefile stale comments:** `web-build` and `go-build` target comments say "web/dist/" but actual path is "web/dist-new-flat/". Cosmetic — build commands work correctly.
>
> ### Resolved Drift Items (all HELD at d40bdea2 — no regressions)
>
> 1. ~~BUILD-BREAKING: Vite outDir mismatch~~ — FIXED (feda78db): changed to `dist-new-flat`.
> 2. ~~Stale comments~~ — FIXED (feda78db): server.go, main.go, Makefile clean, embed.go all corrected.
> 3. ~~Dead code go-backend/~~ — FIXED (feda78db): deleted.
> 4. ~~Barnacles~~ — FIXED (feda78db): 13 .py + 2 .exe → scripts/archive/, 10 .md → docs/archive/.
> 5. ~~handlers_commander.go 2684 LOC God File~~ — FIXED (feda78db): split to 95 LOC + 5 domain files.
> 6. ~~NodesPage.tsx 1389 LOC God Component~~ — FIXED (feda78db): split to 489 LOC + 2 extracted components.
>
> **Note:** A prior restructuring (2026-07-03/04) addressed items 2, 5, and 6 locally but was never committed to git. The local repo was subsequently gutted. The restructure was redone and committed as feda78db on 2026-07-09. 11 LisDiag feature commits landed (feda78db → fd48f854). 12 more commits then landed (fd48f854 → d40bdea2) covering: LisDiag crash fixes, test suite expansion (+11 test files), node detection improvements, BsTool subprocess support, project-specific settings, TCP timeout fix, and active exe listing in .lis files. This reconciliation brings docs in sync with d40bdea2 (v3.9.58).
>
> The original blueprint sections below are preserved as historical design intent.
> See CHANGELOG.md for the actual evolution of the project.

---

**Version:** 1.1.1
**Ratified:** 2026-06-15
**Last Updated:** 2026-06-16
**Source:** GR15 directive + dev-cycle loop type + single-binary embedded webserver pattern
**Orchestrator:** FalkeOrchBot
**Lane ID:** dev-cycle-logreport-20260615
**Loop Type:** dev-cycle
**Theme Reference:** AXON (Vite+Tailwind+React/TS, dark industrial, CT102:8200 pattern)
**Repo Structure Reference:** hermes-remote (AGENTS.md, CLAUDE.md, project_knowledge.json, Makefile, BLUEPRINT.md, ROADMAP.md)

---

## 0. SCOPE DECISION (ratified 2026-06-15)

**Verdict:** Partial rewrite — report-generation pipeline + BsTool Go wrapper. Commander GUI excluded.

| In Scope (Go + React) | Out of Scope (Python retained) |
|------------------------|-------------------------------|
| Telnet client | Commander window (PyQt5) |
| FBC/RPC parser | LOG file processing |
| SysFile parser | VNC recording/playback |
| SQLite store | Session recorder/player |
| Report generator (DOCX/JSON) | |
| REST API (12 endpoints) | |
| Web UI (AXON theme) | |
| Health + config | |
| Embed integration | |
| BsTool Go wrapper (v1.1.0) | |
| R-LIVE review phase | |

**Rationale:** BsTool.exe is a proprietary Windows executable with no source code. Cannot be rewritten in Go. A Go wrapper was built (v1.1.0) that manages the subprocess lifecycle with 10 improvements over the Python original. The Commander workflow depends on BsTool.exe and remains in Python. The report-generation pipeline has zero dependency on BsTool.exe and is fully feasible in Go.

---

## 0.1 ARCHITECTURE OVERVIEW

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
│  │  │ Telnet   │ │ FBC/RPC  │ │ JSON     │ │ Report  │ │   │
│  │  │ Client   │ │ Parser   │ │ Store    │ │ Gen     │ │   │
│  │  └──────────┘ └──────────┘ └──────────┘ └─────────┘ │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                              │
│  DEPLOY: ./logreport --port 8080                             │
│  BUILD:  make build  (= npm build && go build)              │
└─────────────────────────────────────────────────────────────┘
```

### Key Architecture Decisions

| Decision | Rationale |
|----------|-----------|
| **Single binary** | No separate server process. `./logreport --port 8080` = everything running. |
| **Go `embed` for frontend** | `//go:embed web/dist/*` — React build output compiled into binary. Zero external files. |
| **AXON theme** | Vite + Tailwind + React/TypeScript, dark industrial. Same component patterns as AXON (CT102:8200). Reference: `/opt/data/skills/axon/SKILL.md`. |
| **REST API for agents** | `/api/v1/nodes`, `/api/v1/io-lists`, `/api/v1/reports` — JSON request/response. No GUI needed for agent use. No OpenAPI spec endpoint — agents know endpoints from docs. |
| **GUI for humans** | `/` serves the React SPA. AXON dark theme. Same binary, same port. |
| **`--port` flag** | Configurable. Default 8080. Works on any machine on the network. |
| **hermes-remote repo structure** | AGENTS.md, CLAUDE.md, project_knowledge.json, Makefile, BLUEPRINT.md, ROADMAP.md, .gitignore. Same conventions as falke-ai-circuit/hermes-remote. |

---

## 1. COMMIT SEQUENCE (16 Commits — Milestone-Based)

**Each commit = one milestone. Each milestone transfers complete functionality from Python original + includes tests + regression probe against Python output.**

```
Commit 01: REPO INIT — go.mod, Makefile, AGENTS.md, CLAUDE.md, project_knowledge.json,
           .github/agents/, CI, README, BLUEPRINT.md, ROADMAP.md, .gitignore
Commit 02: CORE TYPES — internal/types/ (Node, IOPoint, FBCModule, RPCModule, Report, SysFile)
Commit 03: TELNET CLIENT — internal/telnet/ (connect, auth, command, MOD_LIST, IO_LIST, SYS_INFO)
           + tests: mock DNA server, auth failure, timeout, encoding edge cases
           + regression: compare MOD_LIST output vs Python original for same node
Commit 04: FBC PARSER — internal/parser/fbc.go (parse FBC output → typed structs)
           + tests: empty output, malformed headers, missing channels, encoding edge cases
           + regression: byte-level comparison with Python parser for real FBC dumps
Commit 05: RPC PARSER — internal/parser/rpc.go (parse RPC output → typed structs)
           + tests: same edge case suite as FBC
           + regression: byte-level comparison with Python parser for real RPC dumps
Commit 06: SYSFILE PARSER — internal/parser/sysfile.go (parse .sys binary → node tree)
           + tests: real .sys files, corrupt files, empty files, version mismatches
           + regression: node tree matches Python BsTool output
Commit 07: SQLITE STORE — internal/store/ (schema, CRUD, migrations)
           + tests: concurrent writes, schema migration, large dataset (10K+ IO points)
           + regression: query output matches Python in-memory structures
Commit 08: REPORT GENERATOR — internal/report/ (template engine, DOCX/JSON output)
           + tests: empty dataset, max rows, encoding edge cases, template corruption
           + regression: DOCX byte comparison with Python-generated report
Commit 09: REST API + HEALTH — internal/api/ (net/http mux, /api/v1/* handlers, /health)
           + tests: double-submit, auth boundary, content-type poisoning, method confusion
           + regression: curl output comparison with Python CLI output
Commit 10: WEB UI SCAFFOLD — web/ (Vite + React + TypeScript + Tailwind, AXON dark theme)
           + component tree, router, theme.css, useApi hook
           + tests: build succeeds, no console errors, theme renders
Commit 11: WEB UI NODE VIEW — web/ (node browser, IO list table, FBC/RPC views)
           + tests: resize torture (320px→1920px), empty state, rapid interaction
           + regression: screenshot comparison with PyQt5 original
Commit 12: WEB UI REPORT VIEW — web/ (report config, preview, download)
           + tests: all report formats, download works, empty state
Commit 13: EMBED INTEGRATION — //go:embed web/dist/*, Makefile npm build + go build
           + tests: binary runs, GUI loads at /, API responds at /api/v1/*
           + regression: full pipeline produces identical report to Python original
Commit 14: UNIT TESTS (full coverage) — internal/*_test.go across all packages
           + telnet mock, parser edge cases, store CRUD, report generation, API handlers
           + coverage target: >80% per package
Commit 15: INTEGRATION TESTS — test/ (full pipeline: telnet→parse→store→report→api→gui)
           + real DNA node dumps as test fixtures
           + regression: end-to-end output identical to Python original
Commit 16: DOCS + RELEASE — README, CONTRIBUTING, CHANGELOG, git tag v1.0.0
```

### Dependency Graph

```
01 REPO INIT
  │
  ▼
02 CORE TYPES ─────────────────────────────────────┐
  │                                                │
  ├──► 03 TELNET ──► 04 FBC ──► 05 RPC ──► 06 SYSFILE
  │       │            │          │           │
  │       └────────────┴──────────┴───────────┘
  │                    │
  │                    ▼
  ├──► 07 SQLITE ◄─────┘ (needs parsed types)
  │       │
  │       ▼
  ├──► 08 REPORT GEN (needs store + types)
  │       │
  │       ▼
  ├──► 09 REST API (needs all above)
  │       │
  │       ▼
  ├──► 10 WEB SCAFFOLD ──► 11 NODE VIEW ──► 12 REPORT VIEW
  │                                                │
  │       ┌────────────────────────────────────────┘
  │       ▼
  ├──► 13 EMBED (needs web/dist + go build)
  │       │
  │       ▼
  ├──► 14 UNIT TESTS (needs all internal/)
  │       │
  │       ▼
  └──► 15 INTEGRATION (needs full binary)
          │
          ▼
        16 DOCS + RELEASE
```

### Functionality Transfer Rule (NON-NEGOTIABLE)

**Every commit must transfer complete functionality from the Python original.** No stubs. No "will implement later." Each milestone delivers a working, tested, regression-verified component.

| Commit | Python Original | Go Replacement | Transfer Check |
|--------|----------------|----------------|----------------|
| 03 | `telnetlib` connection, MOD_LIST, IO_LIST | `internal/telnet/` native Go telnet | Same MOD_LIST output for same node |
| 04 | FBC output parser | `internal/parser/fbc.go` | Same typed structs for same input |
| 05 | RPC output parser | `internal/parser/rpc.go` | Same typed structs for same input |
| 06 | BsTool .sys parser | `internal/parser/sysfile.go` | Same node tree for same .sys file |
| 07 | In-memory node/IOPoint storage | SQLite store | Same query results |
| 08 | Report generator (DOCX/JSON) | `internal/report/` | Byte-identical DOCX for same data |
| 09 | CLI output | REST API JSON | Same data, different format |
| 10-12 | PyQt5 desktop GUI | React web UI | Same information, web-accessible |
| 13 | Nuitka .exe bundle | Go single binary | Same functionality, single file |

---

## 2. REST API SPEC (Functional Endpoints Only — No /openapi)

Agents know endpoints from this blueprint. No runtime discovery endpoint.

| Method | Path | Description | Agent Use |
|--------|------|-------------|-----------|
| `GET` | `/health` | Binary version, uptime, DB status | Health check |
| `POST` | `/api/v1/connect` | Connect to DNA node via telnet | Valmet E2E |
| `GET` | `/api/v1/nodes` | List connected/known DNA nodes | Researcher, Analyst |
| `GET` | `/api/v1/nodes/{addr}` | Node detail + IO summary | Conductor profiling |
| `POST` | `/api/v1/nodes/{addr}/scan` | Run MOD_LIST + IO_LIST on node | Valmet, Operative |
| `GET` | `/api/v1/nodes/{addr}/fbc` | FBC module IO points | Any agent |
| `GET` | `/api/v1/nodes/{addr}/rpc` | RPC module IO points | Any agent |
| `POST` | `/api/v1/parse/sysfile` | Upload .sys file, get parsed nodes | Valmet, Analyst |
| `POST` | `/api/v1/reports/generate` | Generate report from node data | Conductor, Valmet |
| `GET` | `/api/v1/reports/{id}` | Download generated report | Any agent |
| `GET` | `/api/v1/reports` | List generated reports | Conductor |

### Example: Agent Usage

```bash
# Agent connects to DNA node
curl -X POST http://logreport-host:8080/api/v1/connect \
  -H "Content-Type: application/json" \
  -d '{"address":"192.168.1.100","username":"engineer","password":"***"}'
# → {"node":{"address":"192.168.1.100","type":"ACN","status":"connected"}}

# Agent scans IO
curl -X POST http://logreport-host:8080/api/v1/nodes/192.168.1.100/scan
# → {"fbc_modules":[...], "rpc_modules":[...], "io_points":247}

# Agent generates report
curl -X POST http://logreport-host:8080/api/v1/reports/generate \
  -H "Content-Type: application/json" \
  -d '{"node_address":"192.168.1.100","format":"docx","template":"commissioning"}'
# → {"report_id":"rpt-20260615-001","status":"generated","path":"/reports/rpt-20260615-001.docx"}
```

---

## 3. GO PACKAGE STRUCTURE

```
LOGReport/
├── cmd/
│   └── logreport/
│       └── main.go              # Entry point, --port flag, server start
├── internal/
│   ├── types/
│   │   ├── node.go              # Node, IOPoint, ModuleType
│   │   ├── fbc.go               # FBCModule, FBCChannel
│   │   ├── rpc.go               # RPCModule, RPCSignal
│   │   ├── sysfile.go           # SysFileHeader, SysFileNode
│   │   └── report.go            # ReportConfig, ReportFormat
│   ├── telnet/
│   │   ├── client.go            # Dial, auth, command execution
│   │   ├── commands.go          # MOD_LIST, IO_LIST, SYS_INFO
│   │   └── client_test.go
│   ├── parser/
│   │   ├── fbc.go               # FBC output → typed structs
│   │   ├── rpc.go               # RPC output → typed structs
│   │   ├── sysfile.go           # .sys file binary parser
│   │   ├── fbc_test.go
│   │   ├── rpc_test.go
│   │   ├── sysfile_test.go
│   │   └── testdata/            # Real FBC/RPC/sysfile samples from Python test suite
│   ├── store/
│   │   ├── db.go                # SQLite connection, migrations
│   │   ├── nodes.go             # Node CRUD
│   │   ├── iopoints.go          # IO point CRUD
│   │   ├── reports.go           # Report metadata CRUD
│   │   └── store_test.go
│   ├── report/
│   │   ├── generator.go         # Template engine
│   │   ├── templates/           # DOCX/JSON templates
│   │   ├── docx.go              # DOCX generation
│   │   └── generator_test.go
│   ├── api/
│   │   ├── server.go            # net/http mux, route registration
│   │   ├── handlers.go          # All /api/v1/* handlers
│   │   ├── middleware.go        # Logging, CORS
│   │   └── handlers_test.go
│   └── server/
│       ├── config.go            # --port, --db-path, --log-level
│       ├── health.go            # /health handler
│       └── shutdown.go          # Graceful shutdown
├── web/
│   ├── src/
│   │   ├── App.tsx              # Root component, router
│   │   ├── components/
│   │   │   ├── NodeBrowser.tsx  # Node list + detail
│   │   │   ├── IOTable.tsx      # IO point table with filters
│   │   │   ├── FBCView.tsx      # FBC module visualization
│   │   │   ├── RPCView.tsx      # RPC module visualization
│   │   │   ├── ReportConfig.tsx # Report generation form
│   │   │   ├── ReportPreview.tsx# Report preview + download
│   │   │   └── StatusBar.tsx    # Connection status, health
│   │   ├── hooks/
│   │   │   └── useApi.ts        # API client hook (relative paths — NEVER absolute IPs)
│   │   ├── styles/
│   │   │   └── theme.css        # AXON dark industrial theme (Tailwind)
│   │   └── main.tsx             # Entry point
│   ├── index.html               # Title + favicon (AXON pattern)
│   ├── public/
│   │   └── favicon.svg          # LOGReport favicon
│   ├── package.json
│   ├── tsconfig.json
│   ├── tailwind.config.ts       # AXON dark theme config
│   ├── vite.config.ts
│   └── dist/                    # Build output → Go embed target (gitignored — AXON pattern)
├── test/
│   ├── integration/
│   │   ├── pipeline_test.go     # Full pipeline test
│   │   └── testdata/            # Real DNA node dumps from Python test suite
│   └── e2e/
│       └── valmet_test.go       # Valmet E2E test harness
├── go.mod
├── go.sum
├── Makefile                     # make build, make test, make release
├── AGENTS.md                    # Agent delegation rules (hermes-remote pattern)
├── CLAUDE.md                    # Project overview + build/run instructions
├── project_knowledge.json       # Hot cache + architecture map + gotchas
├── BLUEPRINT.md                 # This document
├── ROADMAP.md                   # Phase overview + timeline
├── .gitignore                   # build/, dist/, binaries, .venv/
├── .github/
│   ├── workflows/
│   │   ├── ci.yml               # Go test + lint + build
│   │   └── release.yml          # goreleaser
│   └── agents/
│       ├── ANALYST.md
│       ├── ARCHITECT.md
│       ├── CODER.md
│       ├── REVIEWER.md
│       └── VALMET.md
├── README.md
├── CONTRIBUTING.md
├── CHANGELOG.md
└── LICENSE
```

---

## 4. MAKEFILE

```makefile
.PHONY: build test release clean web-build

# Default port
PORT ?= 8080

# Single command: build everything into one binary
build: web-build go-build

# Build React frontend → web/dist/ (gitignored — AXON pattern)
web-build:
	cd web && npm ci && npm run build

# Build Go binary with embedded web/dist/
go-build:
	go build -o logreport ./cmd/logreport/

# Run with embedded web UI
run: build
	./logreport --port $(PORT)

# Development mode: separate frontend dev server + Go API
dev:
	cd web && npm run dev & \
	go run ./cmd/logreport/ --port $(PORT) --cors-origin=http://localhost:5173

# Tests
test:
	go test ./internal/... -v -count=1

test-integration:
	go test ./test/integration/... -v -count=1

# Release build (goreleaser or manual)
release: build
	goreleaser release --clean

# Clean
clean:
	rm -f logreport
	rm -rf web/dist/
```

---

## 5. AGENT BRIEFS

### Phase 0 — REPO INIT (Coder/OpenHands)

```
LANE: dev-cycle-logreport-20260615
LOOP TYPE: dev-cycle
PHASE: 0 (REPO INIT)
ROLE: coder
TOOL: OpenHands

TASK: Create standardized Falke repo on GitHub following hermes-remote conventions.

REPO: github.com/falke-ai-circuit/LOGReport
LANGUAGE: Go 1.22+
FRONTEND: React/TypeScript (Vite + Tailwind, AXON dark theme)
STRUCTURE REFERENCE: github.com/falke-ai-circuit/hermes-remote

DELIVERABLES:
1. go.mod (module github.com/falke-ai-circuit/LOGReport)
2. Makefile (build, test, release, web-build targets)
3. AGENTS.md (agent delegation rules — commit style, forbidden, review gates)
4. CLAUDE.md (project overview, build/run instructions, architecture)
5. project_knowledge.json (hot cache, architecture map, gotchas — empty initially)
6. BLUEPRINT.md (this document, committed as project reference)
7. ROADMAP.md (phase overview + timeline)
8. .github/workflows/ci.yml (go test, go lint, go build)
9. .github/workflows/release.yml (goreleaser)
10. .github/agents/ (ANALYST.md, ARCHITECT.md, CODER.md, REVIEWER.md, VALMET.md)
11. .gitignore (build/, dist/, binaries, .venv/, __pycache__/)
12. README.md (project overview, quick start, build instructions)
13. LICENSE (MIT)
14. CONTRIBUTING.md (conventional commits, PR template)
15. Initial commit pushed to GitHub

EVIDENCE: Repo URL + commit SHA
```

### Phase 1 — ANALYZE (Analyst) — DEEP FEASIBILITY AUDIT

```
LANE: dev-cycle-logreport-20260615
LOOP TYPE: dev-cycle
PHASE: 1 (ANALYZE)
ROLE: analyst
TOOLS: read_file, search_files, terminal, web_search

TASK: Deep feasibility audit of existing LOGReport Python codebase.
Determine if a complete Go rewrite is feasible, what functionality must transfer,
what can be dropped, and what the real domain constraints are.

SOURCE REPO: github.com/goranjovic55/LOGReport (Python PyQt5, 1.37MB, 300+ files)

CRITICAL QUESTIONS (answer with evidence — file paths + line numbers):
1. TELNET: How does the Python code connect to DNA nodes? What telnet library?
   What commands does it send? What response format does it parse?
2. FBC/RPC: What is the exact output format of MOD_LIST and IO_LIST?
   How does the parser handle channel types, signal types, encoding?
3. SYSFILE: What is the .sys file binary format? How does BsTool parse it?
   Can we replace BsTool with a native Go parser?
4. REPORT: What report formats does it generate? DOCX? JSON? PDF?
   What template engine does it use? What data goes into reports?
5. GUI: What PyQt5 widgets does it use? What views/pages exist?
   Can all functionality be replicated in React?
6. DEPENDENCIES: What external tools does it require? (BsTool.exe, falke-remote, etc.)
   Which are replaceable in Go? Which are not?
7. TEST DATA: What real DNA output samples exist? .sys files? Report templates?
   Can we extract them for Go test fixtures?
8. DEAD CODE: What features are unused or can be dropped?
9. WINDOWS-ONLY: What parts are Windows-only? Can they be made cross-platform?
10. FEASIBILITY VERDICT: Can this be fully rewritten in Go? What are the hard blockers?

OUTPUT:
- /opt/data/.hermes/workspace-analyst/dev-cycle-logreport-20260615/feasibility-audit.md
- Sections: Telnet Analysis, FBC/RPC Protocol, SysFile Format, Report Engine,
  GUI Feature Map, Dependency Audit, Test Data Inventory, Dead Code,
  Windows Dependencies, Feasibility Verdict

EVIDENCE CONTRACT:
- Every claim about existing code references a specific file + line number
- Every protocol claim has raw output sample
- Feasibility verdict is binary: FEASIBLE or NOT FEASIBLE with specific blockers
- Append evolution.jsonl
```

### Phase 2 — DESIGN (Architect)

```
LANE: dev-cycle-logreport-20260615
LOOP TYPE: dev-cycle
PHASE: 2 (DESIGN)
ROLE: architect
TOOLS: read_file, search_files, terminal

TASK: Design system architecture for LOGReport Go refactor based on analyst's feasibility audit.

INPUT:
- Analyst's audit: /opt/data/.hermes/workspace-analyst/dev-cycle-logreport-20260615/feasibility-audit.md
- GR15 requirements: Single Go binary, embedded web UI (AXON theme), REST API for agents,
  Valmet E2E tested, commit-per-milestone with full functionality transfer
- Theme reference: AXON (Vite+Tailwind+React/TS, dark industrial, CT102:8200)
- Structure reference: hermes-remote (AGENTS.md, CLAUDE.md, project_knowledge.json)

ARCHITECTURE PATTERN: Single-Binary Embedded Webserver (Go embed)

DELIVERABLES:
1. Component blueprint:
   - Go package structure (cmd/, internal/{types,telnet,parser,store,report,api,server})
   - API spec: all /api/v1/* endpoints with request/response shapes
   - DB schema: SQLite tables (nodes, io_points, reports, templates)
   - Frontend component tree: React components matching AXON patterns
   - Embed strategy: //go:embed web/dist/*, route table for static vs API
2. Commit sequence (16 commits, dependency-ordered, each a complete milestone)
3. Functionality transfer map: Python original → Go replacement per commit
4. Roadmap with time estimates per commit

OUTPUT:
- /opt/data/.hermes/workspace-architect/dev-cycle-logreport-20260615/architecture-blueprint.md
- /opt/data/.hermes/workspace-architect/dev-cycle-logreport-20260615/commit-sequence.md
- /opt/data/.hermes/workspace-architect/dev-cycle-logreport-20260615/api-spec.md

EVIDENCE CONTRACT:
- Every component references a specific requirement from analyst's audit
- Commit sequence respects dependency order
- Functionality transfer map is complete (no gaps)
- Append evolution.jsonl
```

---

## 6. VALMET E2E GATE (Phase V)

Valmet tests with real industrial hardware. This is the **domain gate** — no release without Valmet PASS.

### E2E Checklist

| # | Test | Method | Evidence |
|---|------|--------|----------|
| V1 | **DNA Connection** | `curl -X POST /api/v1/connect` to real DNA node | Telnet output log |
| V2 | **MOD_LIST** | `curl -X POST /api/v1/nodes/{addr}/scan` | Parsed module list vs LightRAG expected |
| V3 | **FBC Extraction** | `curl GET /api/v1/nodes/{addr}/fbc` | IO points match DNA configuration |
| V4 | **RPC Extraction** | `curl GET /api/v1/nodes/{addr}/rpc` | IO points match DNA configuration |
| V5 | **SysFile Parsing** | `curl -X POST /api/v1/parse/sysfile -F file=@real.sys` | Node tree matches DNA |
| V6 | **Report Generation** | `curl -X POST /api/v1/reports/generate` | Report file + format validation |
| V7 | **GWVXG74 Delivery** | falke-remote send report, verify receipt | File receipt confirmation |
| V8 | **LightRAG Cross-Ref** | Query valmet-kb for expected IO structure | KB result vs parsed output |
| V9 | **Fieldbus Debugger** | Validate IO points against physical equipment | Debugger output + 3-source rule |
| V10 | **Regression** | Compare Go output vs Python original for same input | Byte-level or structural match |

### Valmet Verdict Format

```
VALMET E2E VERDICT: PASS | FAIL
DNA NODE TESTED: [address]
IO POINTS VERIFIED: [count]
LIGHTRAG CROSS-REFERENCES: [count matched/unmatched]
FIELD BUS VALIDATION: [PASS/FAIL/NOT AVAILABLE]
GWVXG74 DELIVERY: [PASS/FAIL]
REGRESSION vs PYTHON: [PASS/FAIL — byte-level comparison]
ORIGINAL PROMPT SATISFIED: [YES/NO — with evidence]
```

---

## 7. REVIEWER DOMAIN-ADAPTIVE TESTING (Per Commit)

| Domain | Edge Cases | Realistic Datasets | Regression Probe |
|--------|-----------|-------------------|-----------------|
| **Telnet client** | Connection drop, auth failure, timeout, encoding corruption, partial response | Real MOD_LIST/IO_LIST output from DNA nodes | Compare parsed output vs Python original |
| **FBC/RPC parser** | Empty output, malformed headers, missing channels, encoding edge cases | Real FBC/RPC dumps from ACN/ACN-S nodes | Byte-level comparison with Python parser |
| **SysFile parser** | Corrupt files, empty files, version mismatches, truncated data | Real .sys files from Valmet projects | Node tree matches Python BsTool output |
| **SQLite store** | Concurrent writes, schema migration, large dataset (10K+ IO points), corrupt DB | Production node configs from real projects | Query output comparison |
| **Report generator** | Empty dataset, max rows, encoding edge cases, template corruption | Real Valmet commissioning report data | DOCX/JSON byte comparison |
| **REST API** | Double-submit, auth boundary, content-type poisoning, payload size extremes, method confusion | Real telnet command sequences | curl output comparison |
| **Web UI** | Resize torture (320px→1920px), rapid interaction, empty state, theme corruption, console pollution | Production node configs, real FBC tables | Screenshot comparison with PyQt5 original |
| **Embed integration** | Missing dist/, wrong path, binary size check, static vs API route collision | Full build pipeline | Binary runs + GUI loads + API responds |

### AXON-Specific Web UI Gotchas (from AXON skill)

| Gotcha | Rule |
|--------|------|
| **Vite transpiles undefined function references without error** | Reviewer MUST test live page, not just build success. Build success ≠ working app. |
| **Always relative API paths** | `fetch('/api/v1/...')` never `fetch('http://host:8080/...')` |
| **dist/ is gitignored** | Same as AXON — `web/dist/` in .gitignore, built during `make build` |
| **Never build from uncommitted code** | Coder commits BEFORE `npm run build`. Reviewer verifies `git status --short` is empty. |

---

## 8. INFRASTRUCTURE REQUIREMENTS

| Component | Status | Location | Action Needed |
|-----------|--------|----------|---------------|
| OpenHands | ✅ Deployed | Hostinger, web sessions | Ready for coder |
| LightRAG (Valmet) | ⚠️ CT103:9623 — 198 docs | valmet-kb | Health check before Phase V |
| Fieldbus Debugger | ❓ Unconfirmed | Valmet DNA network | Confirm operational |
| Falke Remote | ✅ Deployed | GWVXG74 | Ready for report delivery |
| GitHub org | ✅ falke-ai-circuit | github.com/falke-ai-circuit | Ready for repo |
| Go toolchain | ✅ Installed | go1.22+ at /opt/data/go/bin/go | Ready |
| Node/npm | ✅ Installed | node20+ | Ready for web build |
| Python LOGReport source | ❓ Not cloned locally | github.com/goranjovic55/LOGReport | Clone for analyst audit |
| AXON theme reference | ✅ Available | /opt/data/skills/axon/SKILL.md | Reference for architect |
| hermes-remote structure ref | ✅ Available | /opt/data/workspace-operative/hermes-remote/ | Reference for repo init |
| Reviewer profile | ✅ Active | Test-suite doctrine updated | Ready |
| Valmet profile | ✅ Active | DNA telnet, LightRAG, 3-source | Ready |
| Analyst profile | ✅ Active | Codebase audit | Ready |
| Architect profile | ✅ Active | System design | Ready |
| Coder profile | ✅ Active | OpenHands integration | Ready |

---

## 9. ESCALATION TRIGGERS

| Trigger | Action |
|---------|--------|
| 3× FAIL on same commit | Double-loop: question architect's spec. Analyst re-audits component. |
| OpenHands unavailable | Fallback: coder uses terminal + git directly |
| DNA node unreachable | Valmet escalates to operative: restore DNA connectivity |
| Fieldbus debugger unavailable | Valmet marks fieldbus tests NOT AVAILABLE, proceeds with telnet + LightRAG |
| LightRAG down | Valmet falls back to direct file read of valmet skills |
| Go embed fails (missing dist/) | Coder fixes Makefile web-build target |
| Python source unreachable | Analyst works from local clone or cached knowledge |
| Functionality gap found (Python does X, Go can't) | Analyst flags in feasibility audit → architect designs workaround or drops feature |
| Reviewer cannot generate evidence | INCONCLUSIVE — explain what blocked verification |

---

## 10. CLOSURE CRITERIA

```
ALL 24 commits pushed to github.com/falke-ai-circuit/LOGReport ✅
ALL per-commit reviewer test suites PASS ✅
ALL functionality transferred from Python original (no gaps) ✅
ALL regression probes PASS (Go output matches Python output) ✅
R-LIVE review phase PASS (2 bugs found + fixed) ✅
BsTool Go wrapper (v1.1.0, 96.3% coverage) ✅
VALMET E2E verdict PASS (or PASS with NOT AVAILABLE for fieldbus) ⏳
INTEGRATION test suite PASS ✅
Git tag v1.0.0 ✅
Git tag v1.1.0-c01 ✅
GitHub release with binary artifacts ⏳
Evolution entry in orchestrator evolution.jsonl ⏳
CLOSURE_REQUEST sent to FalkeCondBot ⏳
```
