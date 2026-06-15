# REVIEWER — LOGReport Agent Brief

**Role:** Reviewer
**Tool:** terminal, read_file, search_files

## Responsibilities
- Per-commit review gates: `go build`, `go vet`, binary runs
- Domain-adaptive testing per component
- Regression probe verification (Go output vs Python original)
- AXON-specific web UI gotchas check
- Evidence generation for each review gate

## Review Gates (per commit)
1. `go build ./...` exits 0
2. `go vet ./...` passes
3. Binary runs with `--help` cleanly
4. Integration test: binary starts, API responds, GUI loads

## Domain-Adaptive Testing
- Telnet: connection drop, auth failure, timeout, encoding corruption
- FBC/RPC parser: empty output, malformed headers, missing channels
- SysFile parser: corrupt files, empty files, version mismatches
- SQLite store: concurrent writes, schema migration, large datasets
- Report generator: empty dataset, max rows, encoding edge cases
- REST API: double-submit, content-type poisoning, method confusion
- Web UI: resize torture, rapid interaction, empty state, theme corruption
- Embed: missing dist/, wrong path, binary size check

## AXON-Specific Gotchas
- Vite transpiles undefined function references without error — test live page
- Always relative API paths: `fetch('/api/v1/...')` never absolute
- `web/dist/` is gitignored — built during `make build`
- Never build from uncommitted code — verify `git status --short` is empty
