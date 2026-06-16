# Contributing to LOGReport

## Commit Conventions

Use conventional commits with the following prefixes:

- `feat:` — New feature or component
- `fix:` — Bug fix
- `refactor:` — Code restructuring without behavior change
- `test:` — Test additions or improvements
- `docs:` — Documentation changes
- `chore:` — Maintenance, CI, build tooling

Each commit must represent one complete milestone with full functionality transfer from the Python original.

## Pull Request Process

1. Create a feature branch from `main`
2. Implement changes following AGENTS.md conventions
3. Ensure `go build ./...` and `go vet ./...` pass
4. Ensure `npm run build --prefix web` passes (for frontend changes)
5. Write tests for new functionality
6. Submit PR with description of changes and evidence of testing
7. Reviewer verifies: build, vet, binary runs, integration test

## Review Requirements

- `go build ./...` exits 0
- `go vet ./...` passes
- `npm run build --prefix web` passes
- Binary runs with `--help` cleanly
- Integration test: binary starts, API responds, GUI loads
- No hardcoded secrets
- No direct edits to `go.mod`/`go.sum` (use `go get`/`go mod tidy`)

## Branch Strategy

- `main` — stable, tagged releases
- `dev-cycle-*` — development cycle branches (one per release cycle)
- Feature branches from `main` for isolated changes

## Forbidden

- Force-push to main without explicit approval
- Breaking proto changes without version bump
- Hardcoded secrets in source (use env vars)
- Direct edits to `go.mod`/`go.sum`
