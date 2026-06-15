# CLAUDE.md — LOGReport

This is the LOGReport project — a Valmet DNA report generation tool.

## What It Is

A single Go binary (`logreport`) that connects to Valmet DNA automation nodes via telnet, parses FBC/RPC module configurations, stores IO point data in SQLite, and generates commissioning reports (DOCX/JSON). Includes an embedded React/TypeScript web UI with AXON dark theme.

## How to Build

```bash
make build          # npm build + go build → single binary
```

## How to Run

```bash
./cmd/logreport/logreport --port 8080
```

Then open `http://localhost:8080` for the web UI, or use the REST API at `/api/v1/*`.

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

Single binary, embedded web UI, REST API. No separate server process. `./logreport --port 8080` = everything running.
