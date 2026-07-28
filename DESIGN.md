# LOGReport Design

## System Overview

LOGReport is a single-binary web application: a Go HTTP server with an embedded React frontend. It provides structured log analysis and report generation for Valmet DNA automation system backups.

## Architecture

```
┌─────────────────────────────────────────────────┐
│                   LOGReport Binary               │
│                                                  │
│  ┌─────────────┐    ┌──────────────────────────┐ │
│  │  Go Server   │    │  Embedded React Frontend  │ │
│  │  (net/http)  │    │  (embed.FS → dist-new-flat)│ │
│  │              │    │                           │ │
│  │  REST API    │◄──►│  Dashboard, Commander,    │ │
│  │  handlers    │    │  Reports, NodeTree        │ │
│  └──────┬───────┘    └──────────────────────────┘ │
│         │                                        │
│  ┌──────┴──────────────────────────────────────┐ │
│  │           Internal Packages                │ │
│  │  api · report · parser · logfile · store   │ │
│  │  nodesconfig · telnet · bstool · lisdiag   │ │
│  │  commandqueue · server · types · logwriter │ │
│  └──────┬──────────────────────────────────────┘ │
│         │                                        │
│  ┌──────┴──────┐  ┌────────┐  ┌──────────────┐  │
│  │  SQLite DB  │  │ filesystem │ │ BsTool.exe  │  │
│  │  (store)    │  │ (logs)  │  │  (external)  │  │
│  └─────────────┘  └────────┘  └──────────────┘  │
└─────────────────────────────────────────────────┘
```

## Report Generation Flow (v3.9.84)

```
User selects project
        │
        ▼
┌──────────────────────┐
│  Resolve log path    │  ◄── Bug #1 fix: if log_root ends with
│  (handlers_projects) │      {project}_{ship}, use directly
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│  Scan log files      │  ◄── logfile.ScanFiles(logRoot)
│  (.fbc/.rpc/.log/.lis)│      Finds files in correct path
└──────────┬───────────┘      (Bug #3 fix: ~50KB not ~2KB)
           │
           ▼
┌──────────────────────┐
│  Build ReportConfig   │  ◄── ProjectNumber, ShipName passed
│  (types.ReportConfig) │      for descriptive filename (Bug #2)
│                       │      OutputDir = {logRoot}/reports/
│                       │      (Bug #4 fix)
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│  Generate report     │  ◄── report.Generate(cfg)
│  (PDF/DOCX/JSON)     │      Processes scan entries
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│  outputPathForConfig │  ◄── {ProjectNumber}_{ShipName}_{date}.{ext}
│  (generator.go)      │      e.g., G0001_GORIZIA_TEST_2026-07-28.pdf
│                      │      Falls back to UUID if no project info
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│  Save to             │  ◄── {logRoot}/reports/{filename}
│  {logRoot}/reports/  │      (Bug #4 fix: was parent dir)
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│  ReportList display  │  ◄── Extracts filename from file_path
│  (ReportList.tsx)   │      Shows descriptive name, not UUID
└──────────────────────┘
```

### Path Resolution Logic (Bug #1)

```go
// handlers_projects.go — createProject / updateProject
projectFolderName := fmt.Sprintf("%s_%s", req.ProjectNumber, req.ShipName)
if strings.HasSuffix(req.LogRoot, projectFolderName) {
    // User already specified the project folder as log_root — use it directly
    logRoot = req.LogRoot
} else {
    logRoot = filepath.Join(req.LogRoot, projectFolderName)
}
```

This prevents the doubled path issue where `log_root` already containing `{project}_{ship}` would get the suffix appended again, causing the scanner to find zero files.

### Health Endpoint (Bug #7)

```
GET /health                    → global node count (from default nodes.json)
GET /health?project_id=123      → project-specific node count (from {logRoot}/nodes.json)
```

The frontend passes `project_id` when fetching health to get the correct node count for the active project.

### StatusBar Fallback (Bug #8)

```
If project object loaded → "Project {number} — {ship}"
If project ID only (object not loaded) → "Project #ID"
If no project → "No project selected"
```

## Node Configuration

`nodes.json` lives at `{logRoot}/nodes.json`. The path is resolved by:

- `nodesConfigPath()` — global default (checks DBPath, ./config/, data/)
- `nodesConfigPathForProject(projectID)` — looks up project's `log_root` from store, returns `{logRoot}/nodes.json`
- `nodesConfigPathForLogRoot(logRoot)` — returns `{logRoot}/nodes.json`

All endpoints that accept `?project_id=` use the project-scoped path when the parameter is provided.

## Data Flow

```
Valmet DNA Backup (filesystem)
    │
    ├── .fbc files ──► parser ──► FBC sections (tokens, commands)
    ├── .rpc files ──► parser ──► RPC sections
    ├── .log files ──► parser ──► LOG sections (errlog, events)
    ├── .lis files ──► parser ──► LIS sections
    │
    ▼
logfile.ScanFiles(logRoot)
    │
    ▼
report.Generate(ReportConfig)
    │
    ├── PDF  ──► {logRoot}/reports/{project}_{ship}_{date}.pdf
    ├── DOCX ──► {logRoot}/reports/{project}_{ship}_{date}.docx
    └── JSON ──► {logRoot}/reports/{project}_{ship}_{date}.json
```

## Command Queue

The command queue ensures sequential execution of all structured commands (telnet, FBC print, RPC print, BsTool). No parallel commands are allowed by design. Live interactive telnet typing is the only exception that bypasses the queue.

## External Tool Integration

| Tool | Purpose | Integration |
|------|---------|-------------|
| BsTool.exe | FBC file analysis | `internal/bstool` — local or remote (Hermes agent) |
| LisDiag.exe | LIS file diagnostics | `internal/lisdiag` — TCP connection, single-conn protocol |
| Telnet | Node communication | `internal/telnet` — direct TCP |