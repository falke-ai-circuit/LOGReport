# LOGReport — Full Test Suite Proposal
**Based on User Entity Modeling & Workflow Discovery**

**Date:** 2026-07-11
**Reviewer:** FalkeRevBot
**Repo:** github.com/falke-ai-circuit/LOGReport (main, commit 7d1835a0)
**Source:** /opt/data/LOGReport/LOGReport-main

---

## User Entity Model

### Who Is the User?

A **Valmet DNA automation engineer** working on ship commissioning. They sit at a laptop connected to a ship's automation network. They have a USB with BsTool.exe and .sys files. They need to:

1. Configure which nodes exist on the ship
2. Create the log file folder structure so commands know where to write
3. Connect to each node over telnet and run diagnostic commands (FBC print, RPC print, BsTool errlog)
4. Watch the command queue execute — pause if something's wrong, resume, retry failures
5. See files fill up with data (tree turns green as files get content)
6. Generate a commissioning report (PDF/DOCX) when all files are collected

### What the User Does Every Day (Critical Path)

```
DAILY WORKFLOW (the one that matters):

1. Open LOGReport in browser → Dashboard shows projects
2. Create or select a project (ship + log_root folder)
3. Go to Nodes page → load .sys files → scan for nodes → configure node list
4. Click "Create Log Structure" → _LOG/ folder tree created with empty files
5. Go to Commander → node tree loads from _LOG/ structure
6. Right-click a file → "fbc_print" → command queued
7. Click "Print All" → all commands queued for all nodes
8. Start queue → commands execute → telnet connects to each node
9. Watch files fill with data → tree colors change (red→green)
10. Pause if a node is unreachable → resume after fixing
11. Retry failed commands after fixing connection
12. Generate report (PDF with TOC, navigable by node)
```

### User Satisfaction Criteria

| Criterion | What "done" looks like from user's seat |
|-----------|----------------------------------------|
| Project created | I see it on Dashboard, I can select it, log_root is set |
| Nodes configured | Node list has real IPs and token types from .sys files |
| Structure created | _LOG/ folder exists on disk with station/type/file hierarchy |
| Tree loads | Commander shows all nodes with correct file colors (red=empty, green=has data) |
| Command executes | Telnet connects, command runs, output written to correct file |
| File fills | File on disk has content, tree item turns green |
| Queue works | I can start/pause/resume/cancel/retry — no circuit breaker blocking |
| Report generated | PDF opens with clickable TOC, each node section has real data |

### User Frustration Triggers

| Trigger | Why it frustrates |
|---------|------------------|
| Circuit breaker blocks all commands | "I fixed the connection but the queue won't retry" |
| retry-failed 404 | "The button is there but nothing happens" |
| File doesn't change color after command | "Did it work? I can't tell" |
| Report has empty sections | "I ran all commands but the report is blank" |
| _LOG/ not created | "Where are my files? Nothing was generated" |
| Queue hangs on wrong content-type | "It just sits there, no error, no response" |

---

## Discovered Workflows (from Source Code Analysis)

### Workflow 1: Project → Nodes → Structure → Commander → Report
**The main pipeline. User does this once per ship.**

```
Step 1: Dashboard → "New Project" → enter project_number, ship_name, log_root
Step 2: Select project → log_root becomes active
Step 3: Nodes page → "Load .sys files" → scan BU for .sys files → parse → node list
Step 4: Configure nodes (IPs, token types: FBC, RPC, LOG, LIS)
Step 5: "Create Log Structure" → POST /nodesconfig/create-structure
         → _LOG/{station}/{type}/{station}_{ip}_{token}.{ext} created
Step 6: Commander page → node tree loads from _LOG/
         → files shown red (empty) or green (has content)
Step 7: Right-click file → context menu → "fbc_print" → command queued
Step 8: "Print All" → POST /commandqueue/batch → all commands queued
Step 9: Start queue → commands execute via telnet/BsTool
Step 10: Output written to files via logwriter
Step 11: Tree colors update (red→yellow→green based on line count)
Step 12: Generate report → POST /reports/generate (pdf/docx)
         → Report has node sections with file content
```

### Workflow 2: Commander Queue Lifecycle
**User does this repeatedly during commissioning.**

```
Add commands (single or batch) → Start → watch progress
  → if node unreachable: Pause → fix connection → Resume
  → if commands fail: Retry Failed
  → if need to reorder: drag-and-drop in Queue tab
  → if done: clear queue
  → if need to redo: Restart (reset completed/failed to pending)
```

### Workflow 3: LisDiag Commissioning
**User does this for LIS-type nodes (RSU/DIA channels).**

```
Set lis_mode (rsu/lis/dia) in Settings → Set lis_exe_count (6)
Create structure → LIS files generated as exe1-exeN with mode-aware extensions
Commander → LisDiag tab → enter IP, port, password
Right-click LIS node → "Run LisDiag" → combined exe+io command
  → exe1 sends IO command (0-indexed) and IRB command (1-indexed for RSU)
  → output written to corresponding .rsu/.lis/.dia file
```

### Workflow 4: BsTool Errlog Extraction
**User does this for debugging node errors.**

```
Commander → BsTool tab → enter node info → "Extract Errlog"
  → POST /bstool/errlog with server_name, node_name, ip
  → BsTool.exe runs on Windows VM → reads error log
  → output displayed in panel → can be saved to file
```

### Workflow 5: Report Generation
**User does this when all data is collected.**

```
Reports page → "Generate Report" → select format (pdf/docx)
  → select nodes to include
  → POST /reports/generate {node_addresses, format}
  → Report generated from collected file data
  → Download → open in viewer → navigate by TOC/node sections
```

---

## Test Suite Design

### Tier 1: Fix Existing Broken Tests (MUST DO FIRST)

The existing test suite has regressed. These MUST be fixed before adding new tests.

#### 1.1 Go Backend — Failing Tests

| Test | Package | Failure | Fix |
|------|---------|---------|-----|
| TestDNASystemConfigurator_GeneratedFile | sysloader | Token ID calc: AL02 expects 18f got 181; AP01 expects 22 got 21 | Verify slot_offset logic in sysloader — is it base+slot or base+1? Fix test expectation or code |
| TestDNASystemConfigurator_Refit | sysloader | AL01 should have 1 LIS token, got 2 (LIS+LOG) | Filter logic excludes LOG for AL-type nodes? Verify in parser |
| TestTimeout | telnet | Expected timeout error, got nil (5s) | Increase timeout threshold or make test environment-dependent |
| TestAPIErrorPaths/wrong_content-type | integration | Panics after 10s context deadline | connect handler hangs on wrong content-type — should return 400 immediately |
| E2E suite | test/e2e | 21s timeout | Investigate which sub-test hangs |

#### 1.2 Frontend — Failing Tests

| File | Tests Failing | Root Cause |
|------|---------------|-----------|
| App.test.tsx | 1 — "renders navigation links" | Multiple matches (new routes added since test written) |
| Layout.test.tsx | 3 — SysFile nav link, all 4 links | Nav structure changed (Commander, Settings added) |
| StatusBar.test.tsx | 3 — Offline status | Selector/timing mismatch (API mock returns different shape) |
| ReportConfig.test.tsx | 4 | Form structure changed since test written |
| ReportList.test.tsx | 6 | API response shape changed (now wraps in {reports:[]}) |

**Fix approach:** Update test selectors and expectations to match current component structure. These are stale tests, not broken features.

---

### Tier 2: Backend Unit & API Tests (HIGH PRIORITY)

These cover the 54 untested API routes and 3 packages at 0% coverage.

#### 2.1 Project Management Tests
**File:** `internal/api/handlers_projects_test.go`

| Test Name | What It Proves |
|-----------|---------------|
| TestCreateProject | POST /projects with valid data → 201, returns project with ID |
| TestCreateProjectMissingFields | POST /projects without project_number → 400 |
| TestListProjects | GET /projects → 200, returns {projects: [], total: N} |
| TestGetProject | GET /projects/{id} → 200, full project object |
| TestGetProjectNotFound | GET /projects/9999 → 404 |
| TestUpdateProject | PUT /projects/{id} → 200, updated_at changes |
| TestDeleteProject | DELETE /projects/{id} → 200, then GET returns 404 |
| TestGetProjectNodes | GET /projects/{id}/nodes → 200, returns configs + path |
| TestSaveProjectNodes | POST /projects/{id}/nodes with configs → 200, then GET returns saved configs |
| TestGenerateProjectReportPDF | POST /projects/{id}/report {format:"pdf"} → 200, file_path returned |
| TestGenerateProjectReportDOCX | POST /projects/{id}/report {format:"docx"} → 200 |
| TestGenerateProjectReportJSON | POST /projects/{id}/report {format:"json"} → **should work** (currently fails — F7) |
| TestGenerateProjectReportInvalidFormat | POST /projects/{id}/report {format:"xml"} → 400 |

#### 2.2 Command Queue Full Lifecycle Tests
**File:** `internal/api/handlers_queue_test.go`

| Test Name | What It Proves |
|-----------|---------------|
| TestQueueAdd | POST /commandqueue/add → 200, command appears in status |
| TestQueueAddMultiple | Add 3 commands → status total=3, all pending |
| TestQueueBatch | POST /commandqueue/batch {project_id} → 200, batch_added=true |
| TestQueueBatchNode | POST /commandqueue/batch-node → 200, commands for single node |
| TestQueueBatchNodeLisDiag | batch-node with command_type=lisdiag → combined exe+io commands |
| TestQueueStart | Start → state=running |
| TestQueuePause | Start → Pause → state=paused |
| TestQueueResume | Pause → Resume → state=running |
| TestQueueCancel | Running → Cancel → state=idle |
| TestQueueStatus | Status returns {current, total, state, commands: [...]} |
| TestQueueReorder | Reorder from=0 to=2 → command order changes |
| TestQueueReorderOutOfBounds | from=99 → moved=false, no crash |
| TestQueueRemove | Remove by ID → removed=true |
| TestQueueRemoveNotFound | Remove nonexistent ID → removed=false |
| TestQueueClear | Clear → total=0, state=idle |
| TestQueueRestart | Add commands, start, cancel, restart → all back to pending |
| TestQueueRetryFailed | Add commands, start, let fail, retry-failed → failed→pending |
| TestQueueRetryFailedNoFailed | retry-failed with no failures → retried=0 |
| TestQueueNoCircuitBreakerBlocking | Add 10 commands to unreachable host, start, verify NONE blocked by circuit breaker |

#### 2.3 Log File Operations Tests
**File:** `internal/api/handlers_logs_test.go`

| Test Name | What It Proves |
|-----------|---------------|
| TestListLogRoot | GET /logs/list → 200, returns entries |
| TestListLogFiles | GET /logs/files?log_root=X → 200, files with metadata |
| TestLogContent | GET /logs/content?path=X → 200, {content, path, size} |
| TestSetLogRoot | POST /logs/setroot {path:X} → 200, {set:true} |
| TestSetLogRootMissingPath | POST /logs/setroot {} → 400 |
| TestCreateLogFile | POST /logs/create {path} → 200, file exists on disk |
| TestCreateLogFileConflict | Create existing file → 409 |
| TestSaveLog | POST /logs/save {path, content} → 200, content written |
| TestReadSavedLog | Save then read → content matches |
| TestEraseLog | Create+save+erase → file exists but empty |
| TestDeleteLogFile | POST /logs/delete {path} → 200, file gone |
| TestMoveLogFile | Create+move → file in new location |
| TestCreateFolder | POST /logs/create-folder {path} → 200, dir exists |
| TestBrowseDir | GET /browse?path=/tmp → 200, entries array |
| TestWriteLogByNode | POST /logs/{nodeName} → writes log for station |
| TestReadLogByNode | GET /logs/{nodeName}/{fileName} → file content |

#### 2.4 Node Config & Structure Tests
**File:** `internal/api/handlers_nodesconfig_test.go`

| Test Name | What It Proves |
|-----------|---------------|
| TestGetNodesConfig | GET /nodesconfig → 200, configs array with real fields |
| TestSaveNodesConfig | POST /nodesconfig with configs → 200, then GET returns saved |
| TestLoadNodesConfig | PUT /nodesconfig/load → 200, loads from file |
| TestGetNodesConfigTree | GET /nodesconfig/tree → 200, tree with children, status values |
| TestCreateLogStructure | POST /nodesconfig/create-structure → 200, dirs+files created |
| TestCreateStructureNoNodesJson | create-structure without nodes.json → **should be 400** (currently 500 — F5) |
| TestDeleteLogStructure | DELETE /nodesconfig/delete-structure → 200 |
| TestDeleteNodeConfigEntry | DELETE /nodesconfig/entry?name=X → 200 or 404 |
| TestRenameNodeConfigEntry | POST /nodesconfig/rename → 200 |

#### 2.5 Settings Tests
**File:** `internal/api/handlers_settings_test.go`

| Test Name | What It Proves |
|-----------|---------------|
| TestGetSettings | GET /settings → 200, all 13 fields present |
| TestSaveSettings | POST /settings → 200, then GET returns saved values |
| TestSettingsPersistence | Save, restart server, GET → values persisted |
| TestSettingsPartialSave | POST with subset of fields → doesn't wipe others |

#### 2.6 Telnet Session Tests
**File:** `internal/api/handlers_telnet_test.go`

| Test Name | What It Proves |
|-----------|---------------|
| TestTelnetConnect | POST /telnet/connect → 200, session_id returned |
| TestTelnetConnectMissingFields | POST without host → 400 |
| TestTelnetCommand | Connect → send command → 200, output returned |
| TestTelnetOutput | Connect → command → GET output → 200 |
| TestTelnetDisconnect | Connect → DELETE → 200, disconnected=true |
| TestListSessions | Multiple connects → GET sessions → count matches |
| TestTelnetDisconnectNonexistent | DELETE invalid session → 404 or error |
| TestTelnetExecute | POST /telnet/execute → 200 (single command mode) |

#### 2.7 BsTool Tests
**File:** `internal/api/handlers_bstool_test.go` (enhance existing)

| Test Name | What It Proves |
|-----------|---------------|
| TestBsToolErrLogMissingServerName | POST /bstool/errlog without server_name → 400 |
| TestBsToolErrLogFields | Verify which field names are required (server_name vs node_name — F6) |
| TestBsToolErrLogMockExecution | Mock executor → returns errlog output |

#### 2.8 Sysfile Tests
**File:** `internal/api/handlers_sysfiles_test.go`

| Test Name | What It Proves |
|-----------|---------------|
| TestSysFileScan | GET /sysfiles/scan?dir=X → 200, configs+filters |
| TestSysFileScanMissingDir | GET /sysfiles/scan without dir → 400 |
| TestSysFileParse | GET /sysfiles/parse?dir=X → 200, configs |
| TestSysFileParseMulti | POST /sysfiles/parse-multi → 200 |
| TestScanNodes | POST /sysfiles/scan-nodes → 200 or 502 (no BU) |
| TestLoadSysFiles | POST /sysfiles/load → 200 |

#### 2.9 LisDiag Client Tests
**File:** `internal/lisdiag/client_test.go` (NEW — 0% coverage)

| Test Name | What It Proves |
|-----------|---------------|
| TestLisDiagConnect | Mock TCP server → connect succeeds |
| TestLisDiagConnectTimeout | Unreachable host → timeout error |
| TestLisDiagSendCommand | Mock server → send command → get response |
| TestLisDiagReadUntil | Mock server with prompt → readUntil finds prompt |
| TestLisDiagClose | Connect → close → no leak |
| TestIOCommand | Channel 0 → correct command string |
| TestIRBCommand | Channel 1 → correct command string |
| TestORBCommand | Channel 1 → correct command string |
| TestExeCommand | ExeNum 1 → correct command string |
| TestParseParameters | "1234:password" → port=1234, password="password" |

#### 2.10 Logfile Scanner Tests
**File:** `internal/logfile/scanner_test.go` (NEW — 0% coverage)

| Test Name | What It Proves |
|-----------|---------------|
| TestScanEmptyDir | Empty directory → 0 files |
| TestScanWithFBCFiles | Directory with .fbc files → FileEntry with correct metadata |
| TestScanWithMixedFiles | .fbc + .rpc + .log + .lis → all found, correct types |
| TestScanStationNesting | Station-nested structure → correct node_name, station_name |
| TestScanFileData | File with content → FileData with parsed lines |
| TestScanNoMatchingFiles | .txt files only → 0 entries (only .fbc/.rpc/.log/.lis) |

#### 2.11 Browser Tests
**File:** `internal/browser/launch_test.go` (NEW — 0% coverage)

| Test Name | What It Proves |
|-----------|---------------|
| TestLaunchURL | URL passed correctly to browser open function |
| TestLaunchFallback | Primary browser fails → fallback browser tried |

---

### Tier 3: Frontend Component Tests (HIGH PRIORITY)

15+ components have zero test coverage. These model what the user SEES and CLICKS.

#### 3.1 Dashboard Tests
**File:** `web/src/components/__tests__/Dashboard.test.tsx`

| Test Name | What It Proves |
|-----------|---------------|
| TestRendersProjects | Projects from API → cards rendered with project_number, ship_name |
| TestRendersHealth | Health endpoint → version, uptime shown |
| TestCreateProject | Click "New Project" → fill form → submit → POST /projects called → project appears |
| TestSelectProject | Click project card → selectProject called → navigates to /nodes |
| TestEditProject | Click Edit → change log_root → save → PUT /projects/{id} called |
| TestDeleteProject | Click delete → confirm → DELETE /projects/{id} called → card disappears |
| TestEmptyProjectsState | No projects → "Create your first project" message |
| TestCreateProjectValidation | Submit without project_number → error message shown |

#### 3.2 CommanderLayout Tests
**File:** `web/src/components/__tests__/CommanderLayout.test.tsx`

| Test Name | What It Proves |
|-----------|---------------|
| TestRendersAllTabs | 6 tabs visible: Debugger, LisDiag, BsTool, Scan, Log Viewer, Queue |
| TestTabSwitching | Click each tab → correct panel shows |
| TestNodeTreeLoads | Tree loads from /nodesconfig/tree |
| TestLogRootSync | Log root changes → POST /logs/setroot called |
| TestQueueBarRenders | Queue has commands → CommandQueueBar visible with Start/Pause/Cancel |
| TestQueueBarPolling | QueueBar polls /commandqueue/status at 1s interval |

#### 3.3 NodeTree Tests
**File:** `web/src/components/__tests__/NodeTree.test.tsx`

| Test Name | What It Proves |
|-----------|---------------|
| TestRendersTreeFromAPI | Mock /nodesconfig/tree → tree nodes rendered with correct names |
| TestFileColorRed | file.line_count=0 → red color |
| TestFileColorYellow | file.line_count<10 → yellow color |
| TestFileColorGreen | file.line_count>=10 → green color |
| TestFileColorMissing | Token with no file on disk → red |
| TestContextMenuFBC | Right-click FBC file → context menu shows "fbc_print" |
| TestContextMenuRPC | Right-click RPC file → context menu shows "rpc_print" |
| TestContextMenuBsTool | Right-click node → context menu shows "bstool errlog" |
| TestContextMenuLisDiag | Right-click LIS file → context menu shows "Run LisDiag" |
| TestContextMenuFileMgmt | Right-click in nodes mode → Create/Move/Delete file options |
| TestTreeExpansion | Click station → children (type subfolders) expand |
| TestActiveCommandOverlay | Running command → accent color overlay on file |
| TestCompletedCommandOverlay | Completed command → green overlay |

#### 3.4 QueueTab Tests
**File:** `web/src/components/__tests__/QueueTab.test.tsx`

| Test Name | What It Proves |
|-----------|---------------|
| TestRendersCommands | Commands from /commandqueue/status → rendered in list |
| TestSortByOrder | Default sort = order (queue position) |
| TestSortByStatus | Click sort → filter by status (pending/running/completed/failed) |
| TestSortByType | Click sort → filter by type (bstool/fbc/rpc/lisdiag) |
| TestClearButton | Click Clear → POST /commandqueue/clear |
| TestRestartButton | Click Restart → POST /commandqueue/restart |
| TestRetryFailedButton | Failed commands exist → "Retry Failed (N)" button visible → click → POST /retry-failed |
| TestRetryFailedHidden | No failed commands → button hidden |
| TestNoConfigButton | "Config" button NOT present in UI |

#### 3.5 LisDiagTab Tests
**File:** `web/src/components/__tests__/LisDiagTab.test.tsx`

| Test Name | What It Proves |
|-----------|---------------|
| TestRendersAlwaysInteractive | Tab always shows IP/port fields (not gated by state) |
| TestIPField | IP input field present and editable |
| TestPortField | Port input field present and editable |
| TestConnectButton | Click connect → connects to LisDiag host |
| TestCommandInput | Command input field present → type → send |
| TestPasswordField | Password field present (from settings lisdiag_password) |

#### 3.6 SettingsPage Tests
**File:** `web/src/components/__tests__/SettingsPage.test.tsx`

| Test Name | What It Proves |
|-----------|---------------|
| TestRendersAllFields | All 13 settings fields rendered with current values |
| TestDiaHostField | dia_host input → change → updateField called |
| TestLisModeSelect | lis_mode dropdown → rsu/lis/dia options |
| TestLisExeCount | lis_exe_count number input → change value |
| TestSaveButton | Click Save → POST /settings with all fields |
| TestSavePersistence | Save → reload → values match |

#### 3.7 BsToolPanel Tests
**File:** `web/src/components/__tests__/BsToolPanel.test.tsx`

| Test Name | What It Proves |
|-----------|---------------|
| TestRendersServerInput | Server name input present |
| TestRendersNodeInput | Node name input present |
| TestErrlogButton | Click "Extract Errlog" → POST /bstool/errlog |
| TestOutputDisplay | BsTool output → displayed in panel |
| TestConnectionStatus | Connection status indicator present |

#### 3.8 TelnetTerminal Tests
**File:** `web/src/components/__tests__/TelnetTerminal.test.tsx`

| Test Name | What It Proves |
|-----------|---------------|
| TestRendersTerminal | Terminal output area present |
| TestCommandInput | Command input field present |
| TestSendCommand | Type command → Enter → command sent to session |
| TestOutputDisplay | Telnet output → displayed in terminal area |

#### 3.9 NodesPage Tests
**File:** `web/src/components/__tests__/NodesPage.test.tsx`

| Test Name | What It Proves |
|-----------|---------------|
| TestRendersNodeList | Nodes from API → rendered in list/table |
| TestScanButton | Click scan → POST /nodes/{addr}/scan |
| TestSysFileUpload | Upload .sys file → POST /parse/sysfile |
| TestCreateStructure | Click "Create Structure" → POST /nodesconfig/create-structure |
| TestFileMgmtContext | Right-click → Create/Move/Delete file options |

---

### Tier 4: Workflow Integration Tests (MEDIUM PRIORITY)

These test CONNECTED SEQUENCES, not isolated features. This is where the user's real work happens.

#### 4.1 Go Backend: Full Pipeline Integration
**File:** `test/integration/full_pipeline_test.go`

```go
func TestFullWorkflowPipeline(t *testing.T) {
    // 1. Create project
    // 2. Save node configs to project
    // 3. Create log structure → verify _LOG/ on disk
    // 4. GET tree → verify tree has stations and files
    // 5. Queue batch → verify commands match nodes
    // 6. Start queue (mock executor) → verify commands execute
    // 7. Verify files written → logwriter output correct
    // 8. Generate report (pdf) → verify report has content
    // 9. Delete project → cleanup
}
```

#### 4.2 Go Backend: Queue Lifecycle Integration
**File:** `test/integration/queue_lifecycle_test.go`

```go
func TestQueueLifecycleWorkflow(t *testing.T) {
    // 1. Clear queue
    // 2. Batch add from project → total > 0
    // 3. Start → state=running
    // 4. Pause → state=paused
    // 5. Resume → state=running
    // 6. Cancel → state=idle
    // 7. Restart → all back to pending
    // 8. Start with failing executor → all fail
    // 9. Retry-failed → failed→pending
    // 10. Start again → verify NO circuit breaker blocking
    // 11. Reorder → verify order changed
    // 12. Remove by ID → verify removed
    // 13. Clear → total=0
}
```

#### 4.3 Go Backend: Log File Lifecycle Integration
**File:** `test/integration/log_lifecycle_test.go`

```go
func TestLogFileLifecycleWorkflow(t *testing.T) {
    // 1. Create log structure → files on disk
    // 2. List files → verify count matches structure
    // 3. Read file → empty (just created)
    // 4. Save content to file
    // 5. Read file → content matches
    // 6. Erase file → read → empty
    // 7. Move file → verify in new location, gone from old
    // 8. Create folder → verify dir exists
    // 9. Delete file → verify gone
    // 10. Browse directory → verify entries
}
```

#### 4.4 Frontend: Dashboard → Commander → Report Flow
**File:** `web/src/__tests__/workflow.integration.test.tsx`

```tsx
describe('Full User Workflow', () => {
    // 1. Render Dashboard → mock projects API → project card visible
    // 2. Click project → navigates to /nodes
    // 3. Mock node config → tree loads
    // 4. Click "Create Structure" → mock API → success message
    // 5. Navigate to /commander → tree loads with mock data
    // 6. Verify tree shows files with correct colors
    // 7. Navigate to /reports → mock report list
    // 8. Click generate → mock generation → report appears
})
```

---

### Tier 5: Error Path & Edge Case Tests (MEDIUM PRIORITY)

| Test | What It Proves |
|------|---------------|
| TestCreateStructureNoNodesJson | Returns 400 with clear message (currently 500 — F5) |
| TestProjectReportJSONFormat | Should accept json (currently rejects — F7) |
| TestBsToolErrLogFieldNameConsistency | Should use node_name not server_name (F6) |
| TestSetLogRootFieldConsistency | Should accept log_root not just path (F8) |
| TestQueueReorderEmptyQueue | Reorder on empty → no crash |
| TestQueueReorderSameIndex | from=1 to=1 → no-op, no crash |
| TestTelnetConnectUnreachableHost | Non-routable IP → timeout, not hang |
| TestTelnetConnectWrongContentType | Wrong content-type → 400 immediately, not 10s hang |
| TestGenerateReportNoNodes | Empty node_addresses → 400 or empty report |
| TestGenerateReportNonexistentNode | Node not in DB → 404 or empty section |
| TestWebSocketConnectionDrop | WS disconnects → session cleaned up |
| TestConcurrentQueueOperations | Two clients start queue simultaneously → only one succeeds |
| TestProjectDeleteWithNodes | Delete project → nodes config file also removed |
| TestSettingsConcurrentSave | Two concurrent POST /settings → last write wins, no corruption |

---

## Test Infrastructure

### Go Backend
- **Framework:** `testing` + `testify/assert`
- **Mocking:** MockStore with function fields, mock TCP server for telnet/BsTool, in-memory store
- **Coverage target:** >80% per package (currently: api 20%, browser 0%, lisdiag 0%, logfile 0%)
- **Run:** `go test ./internal/... ./test/... -v -cover`

### Frontend
- **Framework:** vitest + @testing-library/react + jsdom
- **Mocking:** Global fetch mock, per-test override
- **Coverage target:** All components tested (currently: 13 files, 15+ untested components)
- **Run:** `npx vitest run`

### Integration
- **Pattern:** Mock TCP server (telnet/BsTool), in-memory store, httptest server
- **Run:** `go test ./test/integration/... ./test/e2e/... -v`

---

## Priority Order

| Priority | What | Why |
|----------|------|-----|
| P0 | Rebuild & redeploy from commit 7d1835a0 | Running binary missing critical fixes |
| P1 | Fix 21 failing tests (4 Go + 17 frontend) | Can't build on broken foundation |
| P2 | Write 11 backend test files (Tier 2) | 54 untested routes, 3 packages at 0% |
| P3 | Write 9 frontend component tests (Tier 3) | 15+ untested components |
| P4 | Write 4 workflow integration tests (Tier 4) | Test connected pipelines, not isolated features |
| P5 | Write 14 error path tests (Tier 5) | Edge cases and known issues |
| P6 | Fix F5/F6/F7/F8 inconsistencies | API contract issues |

**Total new tests proposed: ~120 Go + ~80 frontend = ~200 tests**