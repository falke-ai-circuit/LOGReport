---
applyTo: 'web/src/**,internal/**,cmd/**'
description: 'Coordination patterns for fullstack changes spanning Go backend and React frontend.'
---

# Fullstack Sessions

> LOGReport is Go backend + React frontend in a single binary. Fullstack changes touch both `internal/` and `web/src/`.

## When This Applies
- Editing both Go backend and React frontend in same session
- Adding new API endpoints with UI
- Debugging cross-layer issues

## Pre-Load Skills
When editing both backend + frontend:
```
frontend-react ⭐ + backend-api ⭐
```

## Coordination Checklist
1. **API Changes** → Update Go handler → Update TS types → Update React UI → Test
2. **New Feature** → Plan → Go handler/service → API endpoint → React component → Integration test
3. **Bug Fix** → Debug → Fix → Test (Go test + frontend test)

## Common Patterns

| Change Type | Order | Files |
|-------------|-------|-------|
| New endpoint | `internal/api/handlers*.go` → `web/src/api/*.ts` → `web/src/components/*.tsx` |
| UI update | `web/src/components/*.tsx` → `internal/api/handlers*.go` (if API needed) |
| Bug fix | Debug → Fix source → Run `go test ./internal/...` → Run `cd web && npm test` |
| Report gen | `internal/report/generator.go` → `internal/api/handlers_projects.go` → `web/src/components/ReportList.tsx` |

## Gotchas

| Issue | Solution |
|-------|----------|
| Frontend not updating | Rebuild: `cd web && npm run build` (embedded in Go binary) |
| Version shows "dev" | Inject via ldflags: `-X main.version=v3.9.84` |
| CORS errors | Use `--cors-origin` flag or same-origin (embedded UI) |
| Type mismatch | Check `web/src/types/api.ts` matches Go struct JSON tags |
| Report path doubled | If log_root ends with {project}_{ship}, use directly (Bug #1, v3.9.84) |
| Node count shows 0 | Pass `?project_id=` to `/health` endpoint (Bug #7, v3.9.84) |

## Verification
After fullstack changes:
1. Run Go tests: `go test ./internal/...`
2. Run frontend tests: `cd web && npm test`
3. Build: `cd web && npm run build && cd .. && go build -ldflags "-X main.version=v3.9.84" -o logreport ./cmd/logreport/`
4. Test end-to-end: run binary and test in browser

## Token Optimization
- Use domain_index for O(1) file lookup
- Check hot_cache before reading files
- Batch related edits together
