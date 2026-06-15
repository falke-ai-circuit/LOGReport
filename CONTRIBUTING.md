# Contributing to LOGReport

## Commit Conventions

Use conventional commits with the following prefixes:

- `feat:` — New feature or component
- `fix:` — Bug fix
- `refactor:` — Code restructuring without behavior change
- `docs:` — Documentation changes
- `chore:` — Maintenance, CI, build tooling

Each commit must represent one complete milestone with full functionality transfer from the Python original.

## Pull Request Process

1. Create a feature branch from `main`
2. Implement changes following AGENTS.md conventions
3. Ensure `go build ./...` and `go vet ./...` pass
4. Write tests for new functionality
5. Submit PR with description of changes and evidence of testing
6. Reviewer verifies: build, vet, binary runs, integration test

## Review Requirements

- `go build ./...` exits 0
- `go vet ./...` passes
- Binary runs with `--help` cleanly
- Integration test: binary starts, API responds, GUI loads
- No hardcoded secrets
- No direct edits to `go.mod`/`go.sum` (use `go get`/`go mod tidy`)

## Forbidden

- Force-push to main without explicit approval
- Breaking proto changes without version bump
- Hardcoded secrets in source (use env vars)
- Direct edits to `go.mod`/`go.sum`
