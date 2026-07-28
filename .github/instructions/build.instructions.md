---
applyTo: '**/*.go,Makefile,**/*.sh,go.mod,go.sum'
description: 'Build and deployment commands for LOGReport Go+React application.'
---

# Build

Build and validation commands for LOGReport.

## When This Applies
- Building the binary
- Running tests
- Deploying to target machines

## Prerequisites

- Go 1.22+ (tested with Go 1.23.12)
- Node.js 18+ and npm (for frontend build)

## Build Steps

```bash
# 1. Build frontend (Vite → web/dist-new-flat/)
cd web && npm install && npm run build

# 2. Build backend with version injection
go build -ldflags "-X main.version=v3.9.84" -o logreport ./cmd/logreport/

# Cross-compile for Windows:
GOOS=windows GOARCH=amd64 go build -ldflags "-X main.version=v3.9.84" -o logreport-x64.exe ./cmd/logreport/
```

The React frontend is embedded into the Go binary via `embed.go` (`//go:embed all:web/dist-new-flat`).

## Run

```bash
./logreport --port 8642 --db-path logreport-data
```

Open `http://localhost:8642` in a browser.

## Testing

```bash
# Go tests (all 15 internal packages)
go test ./internal/...

# Frontend tests
cd web && npm test
```

## Common Tasks

| Task | Command |
|------|---------|
| Build frontend | `cd web && npm run build` |
| Build backend | `go build -ldflags "-X main.version=v3.9.84" -o logreport ./cmd/logreport/` |
| Run | `./logreport --port 8642` |
| Go tests | `go test ./internal/...` |
| Frontend tests | `cd web && npm test` |
| Cross-compile Windows | `GOOS=windows GOARCH=amd64 go build -ldflags "-X main.version=v3.9.84" -o logreport-x64.exe ./cmd/logreport/` |

## ⚡ Command Batching (Reduce API Calls)

**Batch independent commands with `&&`:**
```bash
# ❌ Bad: 3 separate terminal calls
cd web && npm run build
go build -o logreport ./cmd/logreport/
./logreport

# ✅ Good: 1 terminal call
cd web && npm run build && cd .. && go build -ldflags "-X main.version=v3.9.84" -o logreport ./cmd/logreport/ && ./logreport
```

## ⛔ MANDATORY Before Finishing

1. **Run tests** for all packages: `go test ./internal/...`
2. **Build passes**: `go build ./cmd/logreport/`
3. **Frontend builds** (if UI modified): `cd web && npm run build`

## ⚠️ Critical Gotchas

- **Version string** — Must inject via ldflags: `-X main.version=v3.9.84`. Without it, version shows "dev".
- **Frontend must build before Go** — `web/dist-new-flat/` must exist before `go build` (embedded via `//go:embed`).
- **Go 1.22+ required** — go.mod specifies `go 1.22`. Tested with Go 1.23.12.
- **Windows cross-compile** — Use `GOOS=windows GOARCH=amd64` for target VMs.
