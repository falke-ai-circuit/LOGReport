---
applyTo: '**'
description: 'Project architecture reference for LOGReport - folder structure, component layers, and code organization patterns.'
---

# Architecture & Structure

Project organization for LOGReport (Log Processing & Reporting Tool).

> **Note:** LOGReport was rewritten from Python/PyQt5 to Go+React in v3.9.x. The Go backend (`internal/`, `cmd/`) is the active codebase. The Python source (`src/`) is legacy and not built.

## When This Applies
- Adding new files or components
- Navigating unfamiliar parts of codebase
- Deciding where to place new code
- Moving or reorganizing code

## Root Structure

| Folder | Purpose |
|--------|---------|
| `cmd/logreport/` | Go main entry point (main.go) |
| `internal/` | Go backend packages (15 packages) |
| `web/src/` | React 18 + TypeScript frontend |
| `web/dist-new-flat/` | Vite build output (embedded by Go) |
| `src/` | Legacy Python/PyQt5 source (not built) |
| `.github/` | AKIS framework + workflows |
| `embed.go` | Go embed directive for frontend |

## Root Files
- .go: embed.go, go.mod, go.sum
- .md: README.md, CHANGELOG.md, DESIGN.md
- .json: go.mod (module: github.com/falke-ai-circuit/LOGReport)
- .exe: logreport-x64.exe (Windows build output)

## Layers

| Layer | Tech | Location |
|-------|------|----------|
| Backend | Go 1.22+ | `cmd/logreport/`, `internal/` |
| Frontend | React 18 + TypeScript + Vite | `web/src/` |
| Embedded UI | Go `embed.FS` | `embed.go` → `web/dist-new-flat/` |
| Legacy | Python/PyQt5 | `src/` (historical, not built) |
| Agent | AKIS framework | `.github/` |

## Go Backend Packages (`internal/`)

| Package | Purpose |
|---------|---------|
| `internal/api` | HTTP handlers — REST API, projects, reports, nodes, telnet, queue, BsTool |
| `internal/report` | Report generation — PDF, DOCX, JSON (`outputPathForConfig`) |
| `internal/parser` | SysFile parser, FBC/RPC/LIS log parsers |
| `internal/logfile` | File scanner — discovers .fbc/.rpc/.log/.lis files |
| `internal/nodesconfig` | Node configuration load/save (`nodes.json`) |
| `internal/store` | SQLite-backed project store |
| `internal/telnet` | Telnet client |
| `internal/bstool` | BsTool.exe integration |
| `internal/lisdiag` | LisDiag integration |
| `internal/commandqueue` | Sequential command queue |
| `internal/server` | HTTP server, health endpoint |
| `internal/types` | Shared types (ReportConfig, etc.) |
| `internal/logwriter` | Log file writing utilities |

## Frontend Components (`web/src/`)

| Component | Purpose |
|-----------|---------|
| `Dashboard.tsx` | Project list, create/edit/delete, health display |
| `CommanderLayout.tsx` | Main layout, node tree, telnet tabs |
| `NodeTree.tsx` | Hierarchical node tree with FBC/RPC/LOG/LIS |
| `ReportList.tsx` | Report list with descriptive filenames, download |
| `ReportConfig.tsx` | Report configuration form |
| `StatusBar.tsx` | Status bar with project info and node count |

## File Placement

| Type | Location |
|------|----------|
| Go source | `internal/`, `cmd/` |
| Frontend | `web/src/` |
| Frontend build | `web/dist-new-flat/` |
| Go tests | `internal/*_test.go`, `internal/**/*_test.go` |
| Frontend tests | `web/src/**/__tests__/*.test.tsx` |
| Legacy Python | `src/` (not built) |
| Config | `.github/` |

## Finding Related Code

| Component | Location |
|-----------|----------|
| HTTP API handlers | `internal/api/handlers*.go` |
| Project CRUD | `internal/api/handlers_projects.go` |
| Report generation | `internal/report/generator.go`, `internal/report/pdf.go` |
| Node config | `internal/api/handlers_nodesconfig.go`, `internal/nodesconfig/` |
| File scanner | `internal/logfile/` |
| SysFile parser | `internal/parser/` |
| Health endpoint | `internal/api/handlers.go` (healthHandler) |
| Command queue | `internal/commandqueue/`, `internal/api/handlers_queue.go` |
| BsTool | `internal/bstool/`, `internal/api/handlers_bstool.go` |
| Main entry | `cmd/logreport/main.go` |

## ⚠️ Critical Gotchas

| Pattern | Issue | Solution |
|---------|-------|----------|
| Go build | Version string | Inject via ldflags: `-X main.version=v3.9.84` |
| Report path | Doubled path (Bug #1, v3.9.84) | If log_root ends with {project}_{ship}, use directly |
| Report filename | UUID vs descriptive (Bug #2, v3.9.84) | Pass ProjectNumber/ShipName to ReportConfig |
| Report save dir | Wrong location (Bug #4, v3.9.84) | OutputDir = {logRoot}/reports/ |
| Health node count | Shows 0 (Bug #7, v3.9.84) | Pass ?project_id= to /health endpoint |
| Go version | Go 1.22+ required | Tested with Go 1.23.12 |
| Frontend embed | Must build before Go | `cd web && npm run build` then `go build` |
