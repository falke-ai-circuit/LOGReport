# Changelog

## [v3.9.66] — 2026-07-16

### Fixed

- **Commander tree scroll stutter eliminated** — Tree no longer refreshes on every queue-add action. Removed 17 unnecessary `setTreeReloadKey` calls from queue-add, queue-start, queue-stop, queue-clear, queue-restart, retry-failed, and batch-queue actions. Tree now refreshes only when: (1) queue finishes (running→done/idle transition detected by NodeTree polling), (2) file operations (erase, save), (3) BsTool direct execution, (4) logRoot change. Also removed per-command tree reload during execution — tree was being refreshed on every command index advance, causing constant re-renders. Scroll position is now fully preserved during manual scrolling.
- **Settings page nav link restored** — Settings tab was removed from navigation in commit a3414c45 (v3.9.55 era). The /settings route still existed but was unreachable from the UI. Added Settings NavLink back to Layout.tsx.

## [v3.9.58] — 2026-07-15

### Added

- **LisDiag: active exe listing in .lis files** — Before each `exe N` + `io` command sequence, LisDiag now sends a bare `exe` (no number) command first. The response (listing all active exes on the RSU) is captured and included in each .lis file output. Each .lis file now contains two sections: `=== Active Exes ===` (the bare `exe` response) and `=== IO Output (exe N) ===` (the per-exe io frame data). This makes the actual RSU hardware exe count visible in every .lis file for diagnostics.

### Commits

- `d40bdea2` feat: send 'exe' (no number) before 'exe N' to include active exe listing in .lis output

## [v3.9.57] — 2026-07-15

### Added

- **Project-specific settings** — `SettingsJSON` field added to `Project` struct (`internal/types/project.go`). `GET /api/v1/settings?project_id=X` and `POST` endpoints in `internal/api/handlers_settings.go` allow loading/saving per-project settings. `mergeSettings()` overlays project-specific values over global defaults. `getSettingsForProject()` helper provides project-aware settings to all backend handlers. Allows different `lis_mode` (rsu vs lisdiag), `bu_dir`, `bstool_host`, `node_filter`, etc. per project. `Server.activeProjectID` tracks currently selected project. BsTool exec handler uses project-specific settings when available.

### Fixed

- **AP token structure** — `isFieldbusLID()` helper distinguishes CPU slots (`_main`/`_reserve` → LOG only, LID 161) from fieldbus slots (`_m2`/`_m3`/`_r2`/`_r3` → FBC+RPC, LID 162/163). Result: 2 FBC + 2 RPC per AP station (was incorrectly 3+3). CPU slots no longer generate spurious FBC/RPC files.
- **AL token structure** — AL station `nodeType` now maps to `{TokenLIS, TokenLOG}`. AL stations get 501 (LIS) + 501 (LOG) → 6 .lis files + 1 .log file. The .log file is needed for BsTool errlog (PCS startup log) in addition to .lis files.
- **BsTool TCP timeout** — Default 1516ms serial-era timeout was too short for LAN/WAN TCP. `sendBlock`/`recvBlock` now use minimum 5s deadline. Initial dial timeout increased to 5s. This was the root cause of TCP BsTool failures in production.

### Commits

- `5ab172e3` fix: correct token structure + project-specific settings + TCP timeout

## [v3.9.56] — 2026-07-14

### Added

- **BsTool.exe subprocess support** — `local_exe` scan method added as alternative to `remote_bu` (TCP). When `BsTool.exe` is auto-detected in the LOGReport root directory on startup, settings auto-switch to `local_exe`. Subprocess-first, TCP-fallback approach: the shared `executeBsToolErrLog()` helper (in new file `internal/api/handlers_bstool_exec.go`) tries subprocess first, falls back to TCP if subprocess fails or BsTool.exe is not found. Used by REST errlog, WebSocket errlog, and queue executor. `bstool_path` and `communication_line` from settings are wired to all BsTool calls. BsTool.exe v8.26 verified (same protocol as our reverse-engineered TCP implementation).

### Commits

- `ed0ef76a` feat: BsTool.exe subprocess support + auto-detect in logreport root

## [v3.9.55] — 2026-07-14

### Fixed

- **Settings/Config tab removed from navigation** — The standalone Settings tab was removed from the main navigation (`Layout.tsx`). Settings access is now through project-specific settings API. Frontend rebuilt (`dist-new-flat`).
- **LIDMapping test** — Fixed to include BL/BP entries (14 LID types, not 12). Context menu IP fallback from parent node. LisDiag IP fallback from `nodesconfig` when `cmd.IP` is empty.
- **XdSysUsed filter chain verified** — Confirmed with real `nodes.zip` data. Node filter `AP,AL,BP,BL` verified: 70 configs, no A1O1/OPS/ALP.

### Commits

- `a3414c45` fix: remove Settings/Config tab, rebuild frontend, fix LIDMapping test

## [v3.9.54] — 2026-07-14

### Fixed

- **LisDiag: `io` command without number** — Now sends `io` without a channel number (was `io N`). Shows all frames (at least 5) instead of limiting to 1-2. The `exe N` command already selects the channel, so the number on `io` was redundant and restrictive.
- **Case-insensitive XdSysUsed matching** — `.sys` files like `101.SYS` (uppercase) were being dropped because the `activeSysPaths` map had `101.sys` (lowercase). Now matches regardless of case.
- **Node filter applied after XdSysUsed filtering** — The `node_filter` setting (e.g. `AP,AL,BP,BL`) is now applied in the scan-nodes endpoint after XdSysUsed filtering, not before. This ensures only active nodes matching the filter are included. Verified on Vegas VM: 70 configs with `AL,BL,AP,BP` filter. All AL01-AL16 present with correct IPs and tokens.

### Commits

- `beda681a` fix: io without number + case-insensitive XdSysUsed matching + node filter

## [v3.9.12] — 2026-07-07

### Added

- **Remote BU scan: BsTool.exe subprocess fallback** — When the native Go TCP protocol fails (returns 0 files or error), the scan-nodes handler now falls back to running `BsTool.exe -ls` and `BsTool.exe -cat` as subprocesses. This guarantees compatibility with any BU that BsTool.exe supports. The subprocess inherits the parent environment (critical: `COMMUNICATION_TYPES` system env var must be present) and adds `COMMUNICATION_LINE`. Working directory is set to BsTool.exe's location.
- **Remote BU scan: reconnect before each file operation** — Updated `FileTransport.ListDir` and `ReadFile` to reconnect (close + fresh handshake) before each operation, matching BsTool.exe's `zzInitTcpLineIO` behavior.
- **New file: `internal/bstool/subprocess.go`** — `SubprocessRetrieveSysFiles`, `subprocessListDir`, `subprocessCatFile`, `parseListOutput` functions.

### Fixed

- **Remote BU scan now works on Vegas VM** — The native Go TCP protocol returns `param=0` for READ_DIR on this BU (buc_16.20.exe), but BsTool.exe subprocess successfully lists and retrieves 35 .sys files → 99 NodeConfigs. The subprocess fallback bridges the gap.
- **Environment variable inheritance** — `exec.Command.Env` was replacing the entire environment instead of appending. Fixed: `cmd.Env = append(os.Environ(), "COMMUNICATION_LINE=...")` to inherit system env vars like `COMMUNICATION_TYPES`.

## [v3.9.11] — 2026-07-07

### Added

- **Settings: Node Filter** — New `node_filter` field in Settings page. Comma-separated station prefixes to include/exclude. Examples: `AP,AL` = only AP+AL stations, `AP,AL,-AL08` = AP+AL except AL08, `-A1O,-B1O` = all except A1O+B1O. Leave empty for all nodes. Applied during scan-nodes for both local_dir and remote_bu methods.

### Fixed

- **Scan nodes: remote_bu is default** — `scan_method` defaults to `remote_bu` (BsTool TCP). No automatic fallback to local directory. User selects method in Settings.
- **Scan nodes: hostname support** — BU host field accepts hostnames (e.g. `localhost`, `bu.internal.example.com`), not just IP addresses. TCP transport uses `net.Dial` which resolves hostnames.
- **Scan nodes: commLine default** — Communication line defaults to `AB01` if not set in settings.

## [v3.9.10] — 2026-07-07

### Fixed

- **Version display** — Health endpoint now returns the build-injected version (via `main.version` ldflag) instead of hardcoded "1.0.0". CLI `--version` prints `LOGReport v3.9.10 (windows/amd64)`. Frontend StatusBar and Dashboard show the real version from health API.
- **Commander: command input visibility** — Changed `overflow: hidden` to `overflow: auto` on the tab content container so the TelnetTerminal command input bar is always visible at the bottom and not clipped.
- **Commander: Log Viewer hint text** — Updated from "Double-click a file" to "Click a file" to match the new single-click behavior.

## [v3.9.9] — 2026-07-07

### Added

- **Settings: Scan Method toggle** — New `scan_method` setting in Settings page with dropdown: "Remote BU (BsTool TCP Protocol)" (default) or "Local Directory (.sys files on disk)". No automatic fallback between methods — the selected method is used exclusively.
- **Nodes page: Clear Nodes button** — Two-word button "Clear Nodes" in the Nodes page toolbar that removes all detected node configs from the project with a confirmation dialog.

### Fixed

- **Double .log files** — LOG-type tokens were creating duplicate tree entries and duplicate files on disk because `buildFileName` for LOG type doesn't include token ID (`{station}_{ip}.log`), so multiple LOG tokens produced identical filenames. Now deduplicated: one LOG file per station+IP combination. Fixed in `BuildTree`, `BuildFileTree` (3 locations), and `createLogStructure`.
- **Commander: single-click opens files** — Clicking on .li/.fbc/.rpc/.log files in the Commander node tree now opens file content on the right side (Log Viewer tab) immediately, instead of requiring a double-click.

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
