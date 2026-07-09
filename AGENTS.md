# AGENTS.md — LOGReport (Agent Delegation Rules)

> This file is referenced by agent profiles when working with this repo.

## Repo Conventions

### Build
```bash
make build          # Build full binary (npm build + go build)
make test           # Run unit tests
make vet            # Run go vet
make test-integration  # Run integration tests
make clean          # Remove build artifacts
```

### Commit Style
- Prefix: `feat:`, `fix:`, `refactor:`, `docs:`, `chore:`
- Each commit = one milestone with complete functionality transfer
- Tag: `v1.0.0` annotated with release notes
- Push: `git push origin main --tags`

### Forbidden
- Force-push to main without explicit approval
- Breaking proto changes without version bump
- Hardcoded secrets in source (use env vars)
- Direct edits to `go.mod`/`go.sum` (use `go get`/`go mod tidy`)

### Review Gates
1. `go build ./...` exits 0
2. `go vet ./...` passes
3. Binary runs with `--help` cleanly
4. Integration test: binary starts, API responds, GUI loads
