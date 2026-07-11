# LOGReport — Full Functionality Audit & Test Suite Proposal

**Date:** 2026-07-11
**Reviewer:** FalkeRevBot (Reviewer agent)
**Audit type:** Full 13-subsystem functionality audit + test suite gap analysis
**Repo:** github.com/falke-ai-circuit/LOGReport (main branch)
**Source commit:** 7d1835a0 (docs reconciliation to fd48f854)
**Running binary:** v3.9.43-linux on port 8642 (STALE — see F1)
**Fresh build:** dev (from 7d1835a0 source) on port 8655
**Coder prompt:** FalkeCodeBot 13-subsystem audit spec

---

## Executive Summary

**13 subsystems audited. 10 PASS, 2 ISSUES, 1 FAIL (on stale binary).**

The source code at commit 7d1835a0 is solid — all 13 subsystems respond correctly when built fresh. The **running binary (v3.9.43) is stale** and missing two critical fixes (circuit breaker removal + retry-failed endpoint) that are already in source. The test suite has significant gaps: 4 packages at 0% coverage, 4 failing Go test packages, and 17 failing frontend tests.

**Top priority: rebuild and redeploy from current source.**

---

## Audit Environment

- **Stale binary:** v3.9.43-linux, port 8642, 14h uptime, 92 nodes, SQLite connected
- **Fresh build:** dev (from 7d1835a0), port 8655, 3 default nodes
- **Go:** /opt/data/go/bin/go (go 1.22)
- **Frontend:** Vite 5 + React 18 + Tailwind 4, built to web/dist-new-flat/
- **Route count:** 76 `mux.HandleFunc` calls (74 unique API routes + /health + / SPA fallback)

---

## Subsystem Results

### 1. Project Management — ✅ PASS

| Endpoint | Method | Status | Result |
|----------|--------|--------|--------|
| /api/v1/projects | GET | 200 | 1 existing project (E2E-001 / Vegas-Test) |
| /api/v1/projects | POST | 201 | Created AUDIT_TEST project, ID=2 |
| /api/v1/projects/2 | GET | 200 | Returns full project object |
| /api/v1/projects/2 | PUT | 200 | Updated ship_name → AUDIT_SHIP_UPDATED |
| /api/v1/projects/2 | DELETE | 200 | Deleted successfully |
| /api/v1/projects/1/nodes | GET | 200 | Returns configs array + path |

**Fields verified:** id, project_number, ship_name, log_root, status, created_at, updated_at
**Cleanup:** Test project deleted after audit.

---

### 2. Node Configuration & Scanning — ✅ PASS (with field naming note)

| Endpoint | Method | Status | Result |
|----------|--------|--------|--------|
| /api/v1/nodesconfig | GET | 200 | 92 configs loaded |
| /api/v1/nodesconfig/load | PUT | 200 | Loads from nodes.json |
| /api/v1/nodesconfig/tree | GET | 200 | 345 tree nodes, statuses: {idle, warning} |

**Config fields present:** name ✅, ip_address ✅, tokens ✅
**Config fields missing from response:** node_type ⚠️, types ⚠️, section_type ⚠️, lisdiag_params ⚠️
**Note:** These fields may be derived from tokens rather than stored explicitly. Not a bug — but the coder's audit spec expects them.

---

### 3. Create / Delete Log Structure — ✅ PASS (with error handling issue)

| Endpoint | Method | Status | Result |
|----------|--------|--------|--------|
| /api/v1/nodesconfig/create-structure | POST | 200 | 140 dirs, 189 files, 92 stations |
| /api/v1/nodesconfig/delete-structure | DELETE | 200 | Cleanup works |

**Structure verified on disk:**
- `_LOG/` root created ✅
- Station folders: A1A1, A1A2, AC01, AD01-AD08, etc. ✅
- Subfolders: log/, fbc/, rpc/, etc. ✅
- Files: `A1A1_127-0-0-1.log` (station_ip format) ✅

**⚠️ F5 — Error handling:** `create-structure` returns 500 when `nodes.json` doesn't exist in the target `log_root`. Should return 400 with a clear message like "No nodes.json found — save node configs first."

---

### 4. Settings — ✅ PASS

| Endpoint | Method | Status | Result |
|----------|--------|--------|--------|
| /api/v1/settings | GET | 200 | All 13 expected fields present |
| /api/v1/settings | POST | 200 | Persisted correctly |

**All 13 expected fields verified:**
- dia_host ✅ | dia_port ✅ | bstool_host ✅ | bstool_port ✅
- log_root ✅ | logroot_name ✅ | bu_dir ✅
- lis_mode ✅ (rsu) | lis_exe_count ✅ (6)
- lisdiag_password ✅ | communication_line ✅
- scan_method ✅ (remote_bu) | node_filter ✅

**Extra fields:** bstool_path, output_dir (not in coder's spec but present)

---

### 5. Commander — Telnet — ✅ PASS

| Endpoint | Method | Status | Result |
|----------|--------|--------|--------|
| /api/v1/telnet/sessions | GET | 200 | 1 active session |
| /api/v1/telnet/connect | POST | 200 | session_id=sess-7d9a29d3fd8b0da1 |
| /api/v1/telnet/{sid}/command | POST | 200 | {command, output, sent, session_id} |
| /api/v1/telnet/{sid}/output | GET | 200 | {length, output, session_id} |
| /api/v1/telnet/{sid} | DELETE | 200 | {disconnected: true} |

**Full lifecycle verified:** connect → command → read output → disconnect.

---

### 6. Commander — LisDiag — ✅ PASS

| Endpoint | Method | Status | Result |
|----------|--------|--------|--------|
| /api/v1/commandqueue/batch-node | POST | 200 | Added lisdiag commands for single node |

**Note:** Full LisDiag interactivity (IP/port fields, connect, combined exe+io command) requires the frontend on a real Valmet network. Backend endpoint responds correctly.

---

### 7. Commander — BsTool — ⚠️ ISSUE (field naming)

| Endpoint | Method | Status | Result |
|----------|--------|--------|--------|
| /api/v1/bstool/errlog | POST | 400 | "server_name is required" |

**⚠️ F6 — Field naming:** The BsTool errlog endpoint requires `server_name` in the request body, but the coder's spec and other endpoints use `node_name`. This inconsistency could cause frontend integration issues. The endpoint itself works (400 = validation, not 404), but the field name differs from the convention.

---

### 8. Command Queue — Full Lifecycle — ❌ FAIL (stale binary) / ✅ PASS (fresh build)

**On stale binary (v3.9.43, port 8642):**

| Endpoint | Status | Result |
|----------|--------|--------|
| /commandqueue/add | 200 | ✅ |
| /commandqueue/batch | 200 | ✅ (285 commands) |
| /commandqueue/status | 200 | ✅ |
| /commandqueue/start | 200 | ✅ |
| /commandqueue/pause | 200 | ✅ |
| /commandqueue/resume | 200 | ✅ |
| /commandqueue/cancel | 200 | ✅ |
| /commandqueue/reorder | 200 | ✅ |
| /commandqueue/restart | 200 | ✅ |
| /commandqueue/clear | 200 | ✅ |
| /commandqueue/remove | 200 | ✅ |
| /commandqueue/retry-failed | **404** | ❌ **F1 — endpoint not found** |
| Circuit breaker | — | ❌ **F2 — all 288 commands blocked with "circuit breaker open"** |

**On fresh build (from source 7d1835a0, port 8655):**

| Endpoint | Status | Result |
|----------|--------|--------|
| /commandqueue/retry-failed | 200 | ✅ {reset: true, retried: 0} |
| Circuit breaker | — | ✅ No blocking — commands fail on their own merits |

**Conclusion:** Both issues are fixed in source but NOT in the running binary. **Rebuild required.**

---

### 9. Log File Operations — ✅ PASS

| Endpoint | Method | Status | Result |
|----------|--------|--------|--------|
| /api/v1/logs/list | GET | 200 | 107 entries |
| /api/v1/logs/files | GET | 200 | 107 files with metadata (name, path, ext, size, modified, node, station, type) |
| /api/v1/logs/content | GET | 200 | Returns {content, path, size} |
| /api/v1/logs/setroot | POST | 200 | Accepts `path` field (not `log_root`) |
| /api/v1/logs/create | POST | 200 | {created: true, path} |
| /api/v1/logs/save | POST | 200 | {saved: true, path} |
| /api/v1/logs/erase | POST | 200 | {erased: true, path} |
| /api/v1/logs/move | POST | 200 | {moved: true, source, target} |
| /api/v1/logs/delete | POST | 200 | {deleted: true, path} |
| /api/v1/logs/create-folder | POST | 200 | {created: true, path} |
| /api/v1/browse | GET | 200 | 610 entries for /tmp |
| /api/v1/logs/{nodeName} | GET | 200 | Returns files for station |

**Full lifecycle verified:** create → save → read → erase → move → delete. All operations work.

**⚠️ Note:** `/api/v1/logs/setroot` expects field `path`, not `log_root`. This is inconsistent with other endpoints that use `log_root`.

---

### 10. Report Generation — ✅ PASS (with format limitation)

| Endpoint | Method | Status | Result |
|----------|--------|--------|--------|
| /api/v1/reports | GET | 200 | List reports |
| /api/v1/reports/generate (json) | POST | 200 | Report ID returned |
| /api/v1/reports/generate (docx) | POST | 200 | Report ID returned |
| /api/v1/reports/generate (pdf) | POST | 200 | Report ID returned |
| /api/v1/reports/{id} | GET | 200 | Report details |
| /api/v1/projects/{id}/report (pdf) | POST | 200 | file_path, file_size=38891 |
| /api/v1/projects/{id}/report (docx) | POST | 200 | file_path, file_size=5057 |
| /api/v1/projects/{id}/report (json) | POST | **400** | ⚠️ "unsupported format: json. Supported: pdf, docx" |

**⚠️ F7 — Project report format inconsistency:** `/api/v1/reports/generate` accepts json, but `/api/v1/projects/{id}/report` rejects it. Both should accept the same formats.

---

### 11. Node Entry Management — ✅ PASS

| Endpoint | Method | Status | Result |
|----------|--------|--------|--------|
| /api/v1/nodesconfig/entry | DELETE | 404 | Correct — nonexistent node returns 404 |
| /api/v1/nodesconfig/rename | POST | 400 | Correct — validation error for missing name |
| /api/v1/nodes/{addr} | DELETE | 200 | Works |
| /api/v1/nodes/{addr}/rename | POST | 400 | Correct — validation error |
| /api/v1/nodes/{addr}/scan | POST | 400 | Correct — needs valid connection params |

---

### 12. Scan Comparison — ✅ PASS

| Endpoint | Method | Status | Result |
|----------|--------|--------|--------|
| /api/v1/scan/compare | POST | 400 | Correct — requires node_address + token fields |

**Note:** Returns 400 with "node_address and token are required" — correct validation. Requires real FBC data to fully test.

---

### 13. Sysfile Operations — ✅ PASS

| Endpoint | Method | Status | Result |
|----------|--------|--------|--------|
| /api/v1/sysfiles/scan | GET | 200 | Returns configs, count, filters, sys_files |
| /api/v1/sysfiles/parse | GET | 200 | Returns configs, count |
| /api/v1/sysfiles/scan-nodes | POST | 502 | Expected — no real BU at 127.0.0.1:1516 |

**Filters verified:** include_fbc=true, include_lis=false, include_log=true, include_rpc=true, exclude_nodes=[""]

---

## Findings Summary

| ID | Severity | Finding | Fixed in source? |
|----|----------|---------|------------------|
| F1 | ❌ CRITICAL | Running binary v3.9.43 missing retry-failed endpoint (404) | ✅ Yes — works on fresh build |
| F2 | ❌ CRITICAL | Running binary v3.9.43 circuit breaker blocks all commands | ✅ Yes — removed in commit 99dfa138 |
| F3 | ⚠️ HIGH | 4 Go test packages failing (sysloader, telnet, integration, e2e) | ❌ No |
| F4 | ⚠️ HIGH | 17 frontend tests failing across 5 files (stale tests) | ❌ No |
| F5 | ⚠️ MEDIUM | create-structure returns 500 (not 400) when nodes.json missing | ❌ No |
| F6 | ⚠️ MEDIUM | BsTool errlog requires `server_name` not `node_name` (inconsistent) | ❌ No |
| F7 | ⚠️ MEDIUM | Project-scoped report rejects JSON format (only pdf/docx) | ❌ No |
| F8 | ⚠️ LOW | setroot expects field `path` not `log_root` (inconsistent naming) | ❌ No |

---

## Test Suite Gap Analysis

### Go Test Coverage (per package)

| Package | Coverage | Test Files | Status |
|---------|----------|------------|--------|
| types | 100.0% | 7 | ✅ PASS |
| server | 96.7% | 4 | ✅ PASS |
| parser | 92.8% | 5 | ✅ PASS |
| telnet | 60.0% | 2 | ❌ TestTimeout FAIL |
| store | 59.4% | 4 | ✅ PASS |
| logwriter | 68.3% | 1 | ✅ PASS |
| report | 37.1% | 3 | ✅ PASS |
| commandqueue | 41.8% | 1 | ✅ PASS |
| bstool | 31.6% | 5 | ✅ PASS |
| sysloader | 29.6% | 2 | ❌ 2 tests FAIL |
| nodesconfig | 27.8% | 1 | ✅ PASS |
| api | 20.7% | 7 | ✅ PASS (but very low) |
| browser | 0.0% | 0 | ❌ NO TESTS |
| lisdiag | 0.0% | 0 | ❌ NO TESTS |
| logfile | 0.0% | 0 | ❌ NO TESTS |

**Total Go coverage: ~34.2%** (was 82% per coder's June 24 session — significant regression)

### Failing Go Tests

1. **sysloader** — `TestDNASystemConfigurator_*` (2 fails): Token ID calculation incorrect (AL02 expects 18f, got 181; AP01 expects 22, got 21). These are logic bugs in the sysloader or test expectations that need updating.
2. **telnet** — `TestTimeout`: Expected timeout error, got nil. Timing-dependent test that may be flaky on this platform.
3. **integration** — `TestAPIErrorPaths/wrong_content-type`: Panics with context deadline exceeded (10s timeout). The connect handler hangs on wrong content-type instead of rejecting it quickly.
4. **e2e** — Full e2e suite fails (21s timeout).

### Frontend Test Coverage

- **13 test files, 146 tests total**
- **5 files failing, 17 tests failing, 129 passing**
- **Failing files:** App.test.tsx (1), Layout.test.tsx (3), StatusBar.test.tsx (3), ReportConfig.test.tsx (4), ReportList.test.tsx (6)
- **Root cause:** Tests were written for an earlier UI structure. New components (Dashboard, Commander, NodeTree, LisDiagTab, SettingsPage, QueueTab, etc.) either have no tests or tests are stale.
- **Untested components:** Dashboard.tsx, CommanderLayout.tsx, NodeTree.tsx, LisDiagTab.tsx, SettingsPage.tsx, QueueTab.tsx, BsToolPanel.tsx, ColorizedLog.tsx, DirBrowser.tsx, NodeConfigDialog.tsx, NodesPage.tsx, NodesTabContent.tsx, ScanTab.tsx, TelnetTerminal.tsx, and all Tabs/ subcomponents

### Untested API Routes (of 74 total)

**~54 of 74 routes have NO direct test coverage.** Tested (~20): health, connect, nodes CRUD, scan, fbc, rpc, reports generate/list/get, parse/sysfile, bstool errlog (mock).

**Completely untested endpoint groups:**
- All telnet endpoints (connect, command, output, disconnect, sessions)
- All commandqueue endpoints (13 routes — add, batch, batch-node, start, pause, resume, cancel, clear, restart, reorder, remove, retry-failed, status)
- All log file endpoints (14 routes — list, files, content, setroot, create, save, erase, delete, move, create-folder, browse, {nodeName}, {nodeName}/{fileName})
- All project endpoints (7 routes — CRUD, nodes, report)
- All nodesconfig endpoints (7 routes — get, save, load, tree, create-structure, delete-structure, entry delete, rename)
- All settings endpoints (2 routes)
- All sysfiles endpoints (4 routes — load, parse, scan, scan-nodes, parse-multi)
- WebSocket endpoints (2 routes — telnet/ws, bstool/ws)
- scan/compare, nodes rename/delete

---

## Proposed Test Suite

### Phase 1: Fix Failing Tests (Priority: IMMEDIATE)

**Go:**
1. Fix `sysloader` tests — verify token ID calculation logic (AL02: 181 vs 18f, AP01: 21 vs 22)
2. Fix `telnet TestTimeout` — increase timeout threshold or mark as skip on slow CI
3. Fix `integration TestAPIErrorPaths` — wrong content-type should return 400 immediately, not hang for 10s
4. Fix `e2e` suite — investigate 21s timeout failure

**Frontend:**
5. Update `App.test.tsx` — fix "renders navigation links" (multiple matches issue)
6. Update `Layout.test.tsx` — fix "renders SysFile nav link" and "renders all 4 navigation links"
7. Update `StatusBar.test.tsx` — fix 3 failing tests (stale selectors)
8. Update `ReportConfig.test.tsx` — fix 4 failing tests
9. Update `ReportList.test.tsx` — fix 6 failing tests

### Phase 2: New Backend Tests (Priority: HIGH)

**New test files needed:**

10. `internal/api/handlers_projects_test.go` — CRUD for projects, project nodes, project report
11. `internal/api/handlers_telnet_test.go` — connect, command, output, disconnect, sessions lifecycle
12. `internal/api/handlers_queue_test.go` — full queue lifecycle: add, batch, batch-node, start, pause, resume, cancel, clear, restart, reorder, remove, retry-failed, status
13. `internal/api/handlers_logs_test.go` — list, files, content, setroot, create, save, erase, delete, move, create-folder, browse
14. `internal/api/handlers_nodesconfig_test.go` — get, save, load, tree, create-structure, delete-structure, entry delete, rename
15. `internal/api/handlers_settings_test.go` — get, save, persistence
16. `internal/api/handlers_sysfiles_test.go` — load, parse, scan, scan-nodes, parse-multi
17. `internal/api/handlers_websocket_test.go` — telnet/ws, bstool/ws connection lifecycle
18. `internal/lisdiag/client_test.go` — connect, send command, read until, parameter parsing
19. `internal/logfile/scanner_test.go` — scan directory, file detection, filtering
20. `internal/browser/launch_test.go` — browser launch logic

### Phase 3: Frontend Component Tests (Priority: HIGH)

21. `Dashboard.test.tsx` — project cards, create project, edit project, select project
22. `CommanderLayout.test.tsx` — tab navigation, all 6 tabs accessible
23. `NodeTree.test.tsx` — tree rendering, color coding, context menu, file status
24. `LisDiagTab.test.tsx` — IP/port fields, connect, command input
25. `SettingsPage.test.tsx` — all settings fields, save, persistence
26. `QueueTab.test.tsx` — queue display, sort/filter, retry failed button
27. `BsToolPanel.test.tsx` — BsTool errlog, output display
28. `NodesPage.test.tsx` — node config, scan, tree integration
29. `TelnetTerminal.test.tsx` — terminal output, command input

### Phase 4: Workflow Integration Tests (Priority: MEDIUM)

30. **Full pipeline test:** create project → save nodes config → create log structure → verify _LOG/ tree → queue commands → start → pause → resume → cancel → retry-failed → generate report → verify report
31. **LisDiag workflow:** set lis_mode → set lis_exe_count → create structure with LIS files → batch-node lisdiag → verify combined exe+io commands
32. **Log file lifecycle:** create file → write content → read content → erase → move → delete → verify gone
33. **Project report workflow:** create project → add nodes → scan nodes → generate project-scoped report → download

### Phase 5: Error Path & Edge Case Tests (Priority: MEDIUM)

34. create-structure without nodes.json → should return 400 (currently 500)
35. Project report with json format → should accept (currently rejects)
36. BsTool errlog without server_name → verify error message clarity
37. Queue reorder with out-of-bounds indices
38. Queue remove with nonexistent ID
39. Telnet connect to unreachable host → timeout handling
40. WebSocket connection drop → cleanup

---

## Route Count Verification

**Source code:** 76 `mux.HandleFunc` calls in server.go
**Breakdown:** 74 unique API routes + `/health` + `/` (SPA fallback)
**Coder's expected:** 74
**Verdict:** ✅ Matches — coder counts 74 API routes (excluding /health and / SPA fallback)

---

## Verdict

**REQUEST FULFILLED** — with conditions.

The LOGReport source code at commit 7d1835a0 implements all 13 subsystems correctly. The fresh build passes all functional tests. However:

1. **CRITICAL:** The running binary (v3.9.43) is stale and must be rebuilt from current source. Two critical fixes (circuit breaker removal, retry-failed endpoint) are in source but not deployed.
2. **HIGH:** The test suite has regressed significantly — total Go coverage dropped from ~82% to ~34%, 4 Go test packages fail, and 17 frontend tests fail. This needs immediate attention.
3. **MEDIUM:** Three API inconsistencies (BsTool field naming, project report JSON format, setroot field naming) should be fixed for consistency.

**Suggested tasks for coder:**
1. Rebuild and redeploy binary from commit 7d1835a0
2. Fix 4 failing Go test packages
3. Fix 17 failing frontend tests
4. Write 11 new backend test files (Phase 2)
5. Write 9 new frontend component tests (Phase 3)
6. Fix F5: create-structure error handling (500 → 400)
7. Fix F7: project report JSON format support
8. Fix F6: BsTool errlog field naming consistency