# ROADMAP — LOGReport v1.0.0

## Phase Overview

| Phase | Scope | Agents | Deliverable |
|-------|-------|--------|-------------|
| **0** | Repo Init | Coder (OpenHands) | go.mod, Makefile, AGENTS.md, CLAUDE.md, CI, README, LICENSE |
| **1** | Analyst Audit | Analyst | feasibility-audit.md — deep audit of Python codebase |
| **2** | Architect Design | Architect | architecture-blueprint.md, commit-sequence.md, api-spec.md |
| **3** | Core Types | Coder | internal/types/ — Node, IOPoint, FBCModule, RPCModule, Report, SysFile |
| **4** | Telnet Client | Coder | internal/telnet/ — connect, auth, MOD_LIST, IO_LIST, SYS_INFO |
| **5** | FBC Parser | Coder | internal/parser/fbc.go — parse FBC output → typed structs |
| **6** | RPC Parser | Coder | internal/parser/rpc.go — parse RPC output → typed structs |
| **7** | SysFile Parser | Coder | internal/parser/sysfile.go — parse .sys binary → node tree |
| **8** | SQLite Store | Coder | internal/store/ — schema, CRUD, migrations |
| **9** | Report Generator | Coder | internal/report/ — template engine, DOCX/JSON output |
| **10** | REST API + Health | Coder | internal/api/ — net/http mux, /api/v1/* handlers, /health |
| **11** | Web UI Scaffold | Coder | web/ — Vite + React + TypeScript + Tailwind, AXON dark theme |
| **12** | Web UI Node View | Coder | web/ — node browser, IO list table, FBC/RPC views |
| **13** | Web UI Report View | Coder | web/ — report config, preview, download |
| **14** | Embed Integration | Coder | //go:embed web/dist/*, Makefile npm build + go build |
| **V** | Valmet E2E | Valmet | Real DNA node testing, LightRAG cross-ref, fieldbus validation |
| **F** | Final Review | Reviewer | Full test suite, regression probes, all gates |
| **15** | Unit Tests | Coder | internal/*_test.go across all packages, >80% coverage |
| **16** | Integration Tests | Coder | test/ — full pipeline: telnet→parse→store→report→api→gui |
| **17** | Docs + Release | Coder | README, CONTRIBUTING, CHANGELOG, git tag v1.0.0 |

---

## Dependency Graph

```
00 REPO INIT
  │
  ▼
01 ANALYST AUDIT ──► 02 ARCHITECT DESIGN
                          │
                          ▼
                    03 CORE TYPES ─────────────────────────────────────┐
                      │                                                │
                      ├──► 04 TELNET ──► 05 FBC ──► 06 RPC ──► 07 SYSFILE
                      │       │            │          │           │
                      │       └────────────┴──────────┴───────────┘
                      │                    │
                      │                    ▼
                      ├──► 08 SQLITE ◄─────┘ (needs parsed types)
                      │       │
                      │       ▼
                      ├──► 09 REPORT GEN (needs store + types)
                      │       │
                      │       ▼
                      ├──► 10 REST API (needs all above)
                      │       │
                      │       ▼
                      ├──► 11 WEB SCAFFOLD ──► 12 NODE VIEW ──► 13 REPORT VIEW
                      │                                                │
                      │       ┌────────────────────────────────────────┘
                      │       ▼
                      ├──► 14 EMBED (needs web/dist + go build)
                      │       │
                      │       ▼
                      ├──► V VALMET E2E ──► F FINAL REVIEW
                      │       │
                      │       ▼
                      ├──► 15 UNIT TESTS (needs all internal/)
                      │       │
                      │       ▼
                      └──► 16 INTEGRATION (needs full binary)
                              │
                              ▼
                            17 DOCS + RELEASE
```

---

## Timeline

| Phase | Est. Time | Status |
|-------|-----------|--------|
| 0 | Done | ✅ Complete |
| 1 | 1 turn | → Next |
| 2 | 1 turn | Pending |
| 3-13 | 11 turns (parallel where possible) | Pending |
| V | 1 turn | Pending |
| F | 1 turn | Pending |
| 14-17 | 4 turns | Pending |

**Total: ~19 turns to production-ready LOGReport with Valmet E2E validation.**
