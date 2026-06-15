# Changelog

All notable changes to LOGReport will be documented in this file.

## [v0.1.0] — 2026-06-15

### Added
- Initial repository scaffold
- Go module (`go.mod`) with module path `github.com/falke-ai-circuit/LOGReport`
- Makefile with build, test, release, web-build, clean targets
- AGENTS.md with agent delegation rules and commit conventions
- CLAUDE.md with project overview, build/run instructions, architecture diagram
- project_knowledge.json with hot cache, architecture map, and gotchas tracking
- BLUEPRINT.md with full operational blueprint (16-commit sequence, API spec, package structure)
- ROADMAP.md with phase overview and dependency graph
- CI workflow (`.github/workflows/ci.yml`) — Go test + lint + build on push
- Release workflow (`.github/workflows/release.yml`) — goreleaser on tag
- Agent briefs (`.github/agents/`) — ANALYST, ARCHITECT, CODER, REVIEWER, VALMET
- `.gitignore` — build/, web/dist/, binaries, venv, pycache
- README.md with project overview, quick start, API endpoints, architecture diagram
- LICENSE (MIT)
- CONTRIBUTING.md with conventional commits, PR template, review requirements
