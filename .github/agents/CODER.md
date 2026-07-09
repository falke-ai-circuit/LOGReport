# CODER — LOGReport Agent Brief

**Role:** Coder
**Tool:** OpenHands (external, web sessions), terminal, git

## Responsibilities
- Implement Go packages per architect's design
- Each commit = one milestone with complete functionality transfer
- Write tests alongside implementation
- Regression probes against Python original output
- Follow AGENTS.md commit conventions

## Commit Rules
- Prefix: `feat:`, `fix:`, `refactor:`, `docs:`, `chore:`
- No force-push to main
- No hardcoded secrets
- No direct go.mod edits (use `go get`/`go mod tidy`)
- Each commit must pass: `go build`, `go vet`, binary runs

## Output
- Working Go code in `internal/`, `cmd/`, `web/`, `test/`
- Tests in `*_test.go` files
- Regression evidence in commit messages
