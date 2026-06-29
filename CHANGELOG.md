# Changelog

## [v3.9.3] — 2026-06-29

### Fixed

- **NodesPage: duplicate file viewer** — Removed floating panel that overlapped with modal (both rendered simultaneously, z-index conflict)
- **NodesPage: missing context menu handlers** — Added bstool_errlog, rpc_clear, fbc_scan, rpc_scan, clear_logs actions (5 dead buttons fixed)
- **NodeTree: parentNode never passed** — Context menu labels for group/token nodes were empty ("Print All FBC Tokens for " with no name). Fixed by adding parentNode to TreeBranchProps and passing it through recursive calls
- **NodeTree: fileColor not applied to tokens** — Token-type nodes used statusColor instead of fileColor. Now token nodes show green/yellow/red based on line count
- **NodeTree: undefined line_count** — Files with unknown line count appeared green (has content). Now show gray (unknown)
- **NodeTree: dead code removed** — Unreachable second token handler block (lines 237-260) that provided fewer menu items
- **CommanderLayout: auto-set log root** — Now auto-sets log root on page load (same as NodesPage)


All notable changes to LOGReport will be documented in this file.

## [v3.9.0] — 2026-06-29

### Added

- **Horizontal top navigation** — Dashboard, Nodes, Reports, Commander as horizontal tabs across the top, replacing the left sidebar (Layout.tsx)
- **Nodes as standalone main area** — New `NodesPage.tsx` component with node tree (left panel) + station cards + sys file ingest + "Open File" button + colorized log viewer. Moved from Commander sub-tab to its own main navigation area.
- **Colorized log file viewer** — Log content rendered with color coding: green (#22c55e) = normal output, red (#ef4444) = errors, yellow (#f59e0b) = prompts/status, teal (#10b981) = success. Available in both NodesPage and CommanderLayout.
- **Double-click on token nodes** — Token-type nodes in the tree now respond to double-click, constructing the file path from log_root + station + type + filename and opening content in the log viewer.
- **"Open File Content" in token context menus** — Right-click on FBC/RPC/LOG token nodes now includes "Open File Content" action.
- **Value persistence across tab changes** — Telnet host/port and BsTool server name/comm line/bstool path are saved to localStorage on connect/execute and restored on component mount. Values survive tab switches.

### Changed

- **CommanderLayout simplified** — Removed Nodes tab, sys scan panel, and NodesTabContent function. Commander now has: Telnet, BsTool, Scan, Log Viewer tabs only. Node tree stays on left for right-click commands.
- **App.tsx routes** — `/nodes` now renders `NodesPage` instead of old `NodeBrowser`. Old NodeBrowser preserved at `/nodes/browser`.
- **embed.go** — Reverted to `web/dist/*` path (was temporarily changed to `web/dist-new/*` during build directory issues).

### Fixed

- **handlers.go listReportsHandler** — Fixed broken variable declarations: `reports` was assigned with `=` without prior declaration in scope; `err` was used from wrong scope. Rewrote with proper `var` declarations.
- **handlers_projects.go** — Added missing `os` import; fixed `nodesConfigPathForProject` call to use `s.` prefix and `strconv.FormatInt` for int64→string conversion.
- **internal/types/sysfile.go** — Added missing `SlotNum int` and `IsFieldbus bool` fields to `SysFileNode` struct (were in deployed binary but not committed to git).

### Commits

| # | Type | Description |
|---|------|-------------|
| 1 | feat | Horizontal top nav, NodesPage, colorized logs, double-click tokens, value persistence |
| 2 | fix | handlers.go listReportsHandler variable scope, handlers_projects.go missing os import, sysfile.go missing struct fields |


## [v1.1.1] — 2026-06-16

### Fixed

- **Template "default" not found** — Report generation failed when no template was specified because the API defaults to `"default"` but no template was seeded in the store. Fixed in `internal/report/generator.go`: when template is `"default"` and not found, fall through with `nil` (use built-in title "LOGReport — {node}"). Custom templates still fail hard if not found. Found via R-LIVE phase.

## [v1.1.0] — 2026-06-16

### Added

- **BsTool Wrapper** — Go wrapper for the proprietary Windows `BsTool.exe` utility. Manages subprocess lifecycle with 10 improvements over the Python original: configurable timeout, structured error types, output encoding detection, line filtering, dry-run mode, graceful shutdown, platform-adaptive executor (Windows real, Linux stub with 501 UNSUPPORTED_PLATFORM), and 96.3% test coverage.
- **POST /api/v1/bstool/errlog** — New API endpoint for BsTool error log extraction (12th endpoint).
- **R-LIVE Review Phase** — Mandatory live binary review in dev-cycle loop: reviewer starts binary, curls every endpoint, tests GUI surfaces with real HTTP requests. Auto-re-loop on FAIL with exact failure evidence. Found and fixed StatusBar bug (wrong URL `/api/v1/health` → `/health`, wrong field names `db`/`nodes` → `db_status`/`node_count`).
- **Creative Integration Testing** — Reviewer doctrine expanded: for any deliverable talking to an external system, reviewer builds a misbehaving mock and tests with real I/O. Mock DNA telnet server built and used to validate Go telnet client (10/12 live tests PASS, 3 edge cases discovered).
- **`.gitkeep` sentinel** — `web/dist/.gitkeep` committed to prevent empty `//go:embed`; `main.go` startup guard warns if embed contains only `.gitkeep`.

### Commits (8 additional, 24 total)

| # | Commit | Description |
|---|--------|-------------|
| 17 | `feat(bstool)` | BsTool wrapper: client, executor, filter, encoding, errors |
| 18 | `fix(bstool)` | Nil-slice fix for splitMessages |
| 19 | `feat(api)` | POST /api/v1/bstool/errlog endpoint + config flags |
| 20 | `test(bstool)` | Integration tests, 96.3% coverage |
| 21 | `fix(web)` | StatusBar: wrong URL + field names (found via R-LIVE) |
| 22 | `fix(embed)` | `.gitkeep` sentinel + startup guard against empty embed |
| 23 | `fix(report)` | Template "default" not found — non-fatal fallthrough |
| 24 | `docs` | CHANGELOG, ROADMAP, project_knowledge.json, BLUEPRINT updated |

---

## [v1.0.0] — 2026-06-16

### Initial Go Refactor Release

Complete Go rewrite of the Python LOGReport tool. Single binary with embedded React/TypeScript web UI, REST API, and full Valmet DNA node interaction pipeline.

### Features

- **Telnet Client** — Native Go telnet client for DNA node communication (connect, auth, MOD_LIST, IO_LIST, SYS_INFO, FBC_PRINT, RPC_PRINT)
- **FBC Parser** — Parse FBC (Fieldbus Configuration) output into typed structs with channel position/type
- **RPC Parser** — Parse RPC (RUPI Counter) output into typed structs with counter name/value
- **SysFile Parser** — Parse Valmet DNA .sys binary files into node tree entries (LID, node type, description)
- **SQLite Store** — Persistent storage for nodes, IO points, reports, and templates with full CRUD
- **DOCX/JSON Reports** — Generate reports from node scan data in DOCX or JSON format
- **REST API** — 11 endpoints: health, connect, nodes CRUD, scan, FBC/RPC views, sysfile upload, report generation/download
- **React Web UI** — Vite + React + TypeScript + Tailwind with AXON dark theme, node browser, IO tables, FBC/RPC grid views, report config/preview/download
- **Single Binary** — `//go:embed web/dist/*` embeds the production React build into the Go binary; `make build` produces a single deployable artifact
- **Graceful Shutdown** — SIGINT/SIGTERM handling with configurable timeout
- **Middleware Stack** — Logging, CORS, content-type enforcement
- **Unit Tests** — >80% coverage across all internal packages (types, telnet, parser, store, report, api)
- **Integration Tests** — Full pipeline: telnet→parse→store→report→api→gui
- **Valmet E2E Harness** — Test framework for real DNA node validation

### Commits (16 total)

| # | Commit | Description |
|---|--------|-------------|
| 1 | `feat: repo init` | Go scaffold, Makefile, CI, docs, agent briefs |
| 2 | `feat(types)` | Core type definitions: Node, IOPoint, FBCModule, RPCModule, Report, SysFile |
| 3 | `feat(telnet)` | Native Go telnet client for DNA node communication |
| 4 | `feat(parser): FBC` | FBC output parser for DNA fieldbus configuration |
| 5 | `feat(parser): RPC` | RPC counter parser for DNA RUPI counters |
| 6 | `feat(parser): sysfile` | Sysfile parser for Valmet DNA .sys files |
| 7 | `feat(store)` | SQLite persistence layer for nodes, IO points, reports |
| 8 | `feat(report)` | DOCX and JSON report generation from node data |
| 9 | `feat(api)` | REST API with 11 endpoints + health + graceful shutdown |
| 10 | `fix(main)` | Wire main.go to start HTTP server with config and graceful shutdown |
| 11 | `feat(web)` | Vite + React + TypeScript + Tailwind scaffold with AXON dark theme |
| 12 | `feat(web)` | Node browser, node detail, IO table, layout, error boundary |
| 13 | `feat(web)` | Report list, report detail, report config, FBC/RPC grid views |
| 14 | `feat(embed)` | Single-binary with embedded web UI + REST API |
| 15 | `test(coverage)` | Unit test coverage >80% across 5/6 packages (82% total) |
| 16 | `test(integration)` | Full pipeline integration tests + Valmet E2E harness |

---

## [v0.1.0] — 2026-06-15

### Added
- Initial repository scaffold
- Go module (`go.mod`) with module path `github.com/falke-ai-circuit/LOGReport`
- Makefile with build, test, release, web-build, clean targets
- AGENTS.md with agent delegation rules and commit conventions
- CLAUDE.md with project overview, build/run instructions, architecture diagram
- project_knowledge.json with hot cache, architecture map, and gotchas tracking
- BLUEPRINT.md with full operational blueprint (16-commit sequence, API spec, package structure)
- ROADMAP.md with phase overview and dependency graph
- CI workflow (`.github/workflows/ci.yml`) — Go test + lint + build on push
- Release workflow (`.github/workflows/release.yml`) — goreleaser on tag
- Agent briefs (`.github/agents/`) — ANALYST, ARCHITECT, CODER, REVIEWER, VALMET
- `.gitignore` — build/, web/dist/, binaries, venv, pycache
- README.md with project overview, quick start, API endpoints, architecture diagram
- LICENSE (MIT)
- CONTRIBUTING.md with conventional commits, PR template, review requirements
