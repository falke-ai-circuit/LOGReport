# LOGReport — Review 2026-06-25-001

**Date:** 2026-06-25
**Reviewer:** FalkeRevBot (Reviewer agent)
**Review type:** refactor (Go+React rewrite of Python PyQt5 desktop app)
**Recipient:** Goran — Valmet DNA engineer who uses log files daily for node diagnostics
**Repo:** /opt/data/LOGReport/
**Original/reference:** /opt/data/workspace-analyst/dev-cycle-logreport-20260615/source/src/

---

## Request Frame

**Literal request:** Review the Go+React rewrite of LOGReport against the original Python PyQt5 desktop app. Identify gaps, test from recipient's POV.

**Actual need:** Does the rewrite match the original's workflows? Can Goran do his daily job (log file → report, scan FBC files, telnet commands, tree navigation) the same way he did in the Python app? What's missing, what drifted?

**Ambiguity:** None — clear comparison request against known original.

---

## Verdict

**VERDICT:** REQUEST NOT FULFILLED

**AUTOMATED TESTS:** Lab generated — see `lab/` folder. 4 Karate feature files (API, frontend, telnet protocol, file processing) + mock DNA node + test fixtures. Tests designed to fail with descriptive gap references when features are missing. Not yet run on Containerlab host — deploy commands in `lab/README.md`.

**Interpretation drift:** Yes — CRITICAL. The Go app generates reports from SQLite scan data. The original processes `.fbc`/`.rpc`/`.log`/`.lis` log files into PDF+DOCX reports. Different data source = different pipeline = interpretation drift on the core function.

---

## Testing Surface Map

| Dimension | Testable? | Method | Status |
|-----------|-----------|--------|--------|
| HTTP API (11 endpoints) | Yes | Karate API tests (`lab/api.feature`) | Tested manually via curl — lab ready to run |
| Web frontend (React SPA) | Yes | Karate browser tests (`lab/frontend.feature`) | Tested manually via browser — lab ready to run |
| Telnet protocol (FBC/RPC/LIS) | Yes, with mock | Mock TCP server (`lab/mocks/dna_telnet_mock.py`) | Mock built — lab ready to run |
| File I/O (.fbc/.rpc/.log/.lis) | Yes, with fixtures | Test fixtures (`lab/fixtures/logs/`) | Fixtures created — lab ready to run |
| Cross-platform (BsTool.exe) | Yes, with Wine | Wine node (not yet added to topology) | Not tested — Windows-only, documented |
| External hardware (real DNA node) | No | Mock + document as untested | Not tested — mock only |

**Lab generated:** Yes — `lab/` folder with Containerlab topology, 4 Karate feature files, mock DNA telnet server, and test fixtures (sample .fbc/.rpc/.lis/.log files).

---

## What Works (Don't Break)

- Report generation (DOCX + JSON) from SQLite scan data — API returns valid DOCX file
- Node tree loads from `nodes.json` (3 nodes: AP01m, AP01r, AL03) with expandable FBC/RPC/LIS groups and tokens
- Telnet tab: IP/port/connect/commands functional — connects and sends commands
- BsTool tab: structure correct (path input, scan button, output area) — path empty, no auto-detection
- SysFile upload: new feature not in original — drag-and-drop .sys file upload, acceptable addition
- Print All Nodes: Pause/Resume/Cancel controls present and functional
- Frontend: Report, Commander, Node tree, Telnet, Scan, BsTool, SysFile pages all render after rebuild
- Health endpoint: `{"status":"ok","version":"1.0.0","db_status":"connected","node_count":0}`
- 11 API endpoints under `/api/v1/*` all respond

---

## Findings

### F1 — CRITICAL — No Log File Processing Pipeline (Interpretation Drift)

**Evidence:** API `POST /api/v1/reports/generate` with `{"format":"pdf"}` returns `{"error":"unsupported format: 'pdf'. Supported formats: docx, json"}`. No log folder selection UI anywhere in the app. No `.fbc`/`.rpc`/`.log`/`.lis` file scanning code in Go source. Report generator (`internal/report/`) reads from SQLite, not from log files.
**Impact on recipient:** Goran's primary workflow is: select log folder → app reads .fbc/.rpc/.log/.lis files → generate PDF report with filtered content. This workflow does not exist in the Go app at all. He cannot do his job.
**Original behavior:** `gui.py` — log folder selection dialog, file filtering by extension, PDF+DOCX generation from log file contents using reportlab.

### F2 — HIGH — Scan Tab is Paste-Based Instead of File-Based

**Evidence:** Scan tab UI shows a textarea with placeholder "Paste FBC file data here". No file dropdown, no file picker.
**Impact on recipient:** In the original, Goran selects FBC files from a dropdown populated by the log root directory. The app parses the file and shows a structured table. In the Go app, he has to manually paste file contents — tedious, error-prone, and breaks the file-comparison workflow.
**Original behavior:** `scan_tab.py` + `node_scan_widget.py` — file dropdown from log_root, parsed table, cell-by-cell comparison with green/red/yellow coding via `fbc_comparison_service.py`.

### F3 — HIGH — No "Set Log Root" in Commander

**Evidence:** Commander toolbar has no "Set Log Root" button or input. No log root concept in the Go app.
**Impact on recipient:** The log root is the foundation for Scan tab file listing, report generation from log files, and log writer output destination. Without it, the entire file-based workflow chain is broken.
**Original behavior:** `commander_window.py` — "Set Log Root" button in toolbar, stores path in session config.

### F4 — MEDIUM — No Color-Coded Status Icons on Tree Tokens

**Evidence:** Tree renders nodes as text labels with expand/collapse arrows. No colored circles or status indicators.
**Impact on recipient:** Goran relies on quick visual scan — green = connected, red = error, yellow = warning, gray = idle. Without icons, he has to click each node to check status.
**Original behavior:** `tree_view.py` — `QTreeView` with custom delegate painting colored circles based on telnet connection status.

### F5 — MEDIUM — No Log Writer with Decorative Headers

**Evidence:** Telnet tab sends commands and shows output, but no log file is written. No `log_writer` package in Go source.
**Impact on recipient:** Goran needs persistent logs of all telnet commands with structured headers for audit and debugging.
**Original behavior:** `log_writer.py` — writes to log files with `═══` header bars, command metadata, output body, `───` separators.

### F6 — MEDIUM — No Hierarchical Commands / Context Menus

**Evidence:** Tree nodes have no right-click context menu. No command hierarchy in Go source.
**Impact on recipient:** In the original, right-clicking a node shows available commands. Some commands are hierarchical — "Scan Node" triggers sub-commands sequentially.
**Original behavior:** `hierarchical_command_service.py` + `sequential_command_processor.py`.

### F7 — MEDIUM — PDF Format Not Supported

**Evidence:** `curl -s -X POST http://localhost:8642/api/v1/reports/generate -d '{"format":"pdf"}'` returns `{"error":"unsupported format: 'pdf'"}`
**Impact on recipient:** Goran needs PDF reports for sharing and archiving. DOCX only is insufficient.
**Original behavior:** `gui.py` — PDF generation via reportlab.

### F8 — LOW — No Per-Node Progress Indicator in Print All Nodes

**Evidence:** Print All Nodes has Pause/Resume/Cancel but no per-node progress display — just an overall bar.
**Impact on recipient:** When printing 20+ nodes, Goran wants to see which node is being processed.
**Original behavior:** `commander_window.py` — per-node progress labels.

---

## Gaps (Priority-Ordered)

| # | Severity | Gap | References |
|---|----------|-----|------------|
| 1 | CRITICAL | Log file → PDF report pipeline (interpretation drift) | `gui.py` → `internal/report/`, `internal/api/` |
| 2 | HIGH | Scan tab: file-based instead of paste-based | `scan_tab.py`, `node_scan_widget.py`, `fbc_comparison_service.py` → `web/src/pages/Scan.tsx` |
| 3 | HIGH | Set Log Root in Commander | `commander_window.py` → `web/src/pages/Commander.tsx` |
| 4 | MEDIUM | Color-coded status icons on tree tokens | `tree_view.py` → `web/src/components/` (tree) |
| 5 | MEDIUM | Log writer with decorative output | `log_writer.py` → `internal/telnet/` (new package) |
| 6 | MEDIUM | Hierarchical commands + context menus | `hierarchical_command_service.py` → `internal/api/`, `web/src/pages/Commander.tsx` |
| 7 | LOW | Per-node progress in Print All Nodes | `commander_window.py` → `web/src/pages/Commander.tsx` |

---

## Suggested Tasks

> Actionable suggestions for the orchestrator/coder, derived from the findings above.
> The orchestrator reads this section directly and decomposes into delegations.

### TASK 1: Log File → PDF Report Pipeline
- **Priority:** CRITICAL
- **Depends on:** none
- **Delegate to:** Analyst first (research Go PDF library + design API), then Coder
- **Reference:** `gui.py`, `log_writer.py` → `internal/report/`, `internal/api/`
- **What to build:**
  1. Log folder selection in the Report page UI — folder picker or path input that sets a "log root" directory
  2. File scanning: read `.fbc`, `.rpc`, `.log`, `.lis` files from the selected folder
  3. Line filtering: filter log lines by date range, node, severity
  4. PDF report generation: produce a PDF from the filtered log data (consider `github.com/jung-kurt/gofpdf`, `github.com/signintech/gopdf`, `github.com/go-pdf/fpdf`)
  5. API endpoint: `POST /api/v1/reports/generate` should accept `format=pdf` (currently returns error)
  6. Keep DOCX and JSON working — don't break existing formats
- **How to verify (recipient perspective):**
  - User selects a log folder → sees list of `.fbc`/`.rpc`/`.log`/`.lis` files
  - User picks PDF format → report generates from actual log file contents
  - `curl -s -X POST http://localhost:8642/api/v1/reports/generate -d '{"format":"pdf","log_root":"/path/to/logs"}'` returns a PDF file, not an error
  - Run `lab/file-processing.feature` — all scenarios pass
  - Run `lab/api.feature` — PDF scenario passes

### TASK 2: Scan Tab — File-Based Instead of Paste-Based
- **Priority:** HIGH
- **Depends on:** TASK 1 (needs log root concept)
- **Delegate to:** Coder
- **Reference:** `scan_tab.py`, `node_scan_widget.py`, `fbc_comparison_service.py` → `web/src/pages/Scan.tsx`
- **What to build:**
  1. File dropdown: populate from the log root directory, showing `.fbc` files
  2. Parsed table: when a file is selected, parse its contents and display as a structured table
  3. Cell-by-cell comparison: compare two loaded FBC files, highlighting differences:
     - Green: matching cells, Red: mismatched, Yellow: present in one file only
  4. Remove the "Paste FBC file data here" textarea
- **How to verify:**
  - User opens Scan tab → sees dropdown of `.fbc` files from log root
  - User selects a file → sees parsed table, not paste box
  - User selects two files → sees side-by-side comparison with color-coded differences
  - Run `lab/frontend.feature` — "should NOT have paste textarea" scenario passes
  - Run `lab/file-processing.feature` — "Compare two FBC files" scenario passes

### TASK 3: Tree Status Icons + Log Writer + Set Log Root
- **Priority:** MEDIUM
- **Depends on:** none (independent, can run in parallel with TASK 1)
- **Delegate to:** Coder
- **Reference:** `tree_view.py`, `log_writer.py`, `commander_window.py` → `web/src/components/` (tree), `internal/telnet/`, `web/src/pages/Commander.tsx`
- **What to build:**
  1. Status icons on tree tokens: green (connected), red (error), yellow (warning), gray (idle)
  2. "Set Log Root" button in Commander toolbar
  3. Log writer: when telnet commands execute, write structured output to log file with decorative headers (`═══`, `───`, boxed titles with command/node/timestamp)
- **How to verify:**
  - User opens Commander → tree nodes have colored status icons
  - User clicks "Set Log Root" → can set a folder path
  - User runs a telnet command → log file appears with decorative headers
  - Run `lab/telnet.feature` — "telnet command produces log file" scenario passes
  - Run `lab/frontend.feature` — "Set Log Root button" scenario passes

### TASK 4: Hierarchical Commands + Context Menus
- **Priority:** MEDIUM
- **Depends on:** TASK 2 + TASK 3
- **Delegate to:** Coder
- **Reference:** `hierarchical_command_service.py`, `sequential_command_processor.py` → `internal/api/`, `web/src/pages/Commander.tsx`
- **What to build:**
  1. Right-click context menu on tree nodes — shows available commands for that node type
  2. Command hierarchy: some commands have sub-commands that execute sequentially (e.g., "Scan Node" → "Get FBC" → "Get RPC" → "Compare")
  3. Sequential execution with existing Pause/Resume/Cancel controls
  4. Per-node progress indicator: show which step is running
- **How to verify:**
  - User right-clicks a node → sees context menu with available commands
  - User selects a hierarchical command → sub-steps execute sequentially with progress
  - User can Pause/Resume/Cancel mid-sequence
  - Log writer records each step's output

### Phase Ordering
- **Phase 1 (parallel):** TASK 1 (critical path, analyst→coder) + TASK 3 (independent, coder)
- **Phase 2:** TASK 2 (depends on TASK 1's log root concept)
- **Phase 3:** TASK 4 (depends on TASK 2 + TASK 3)

---

## Automated Test Lab

**Lab location:** `lab/` folder in this review directory

**Topology:** `lab/topology.yml` — 3 nodes:
- `logreport` (Go app on golang:1.25-alpine, port 8080)
- `mock-dna-node` (Python mock telnet server, port 23, implements FBC/RPC/LIS protocol)
- `karate` (karatelabs/karate-chrome for API + browser tests)

```
┌──────────────┐       ┌──────────────────┐
│  logreport   │───────│  mock-dna-node   │
│  (Go app)    │ eth1  │  (Python mock)   │
│  :8080       │       │  :23 (telnet)    │
└──────────────┘       └──────────────────┘
       │ eth1
┌──────┴───────┐
│   karate     │
│  (test run)  │
└──────────────┘
```

**Karate features:**
- `lab/api.feature` — 11 API endpoint tests (health, nodes, reports, telnet, sysfile, bstool). PDF format test fails with gap reference F1.
- `lab/frontend.feature` — 8 browser tests (report page, commander, tree, scan tab, log root, telnet, bstool, PDF option). Scan paste box test fails with gap reference F2.
- `lab/telnet.feature` — 7 protocol tests (connect, get fbc, get rpc, scan node, status, disconnect, log file check). Log file test fails with gap reference F5.
- `lab/file-processing.feature` — 5 file I/O tests (list log files, process FBC, process all, compare, fixture verification).

**Mocks:**
- `lab/mocks/dna_telnet_mock.py` — Python TCP server implementing Valmet DNA telnet protocol. Responds to: get fbc, get rpc, get lis, scan node, status, help, quit. Returns sample FBC/RPC/LIS data with TOKEN, AI, DI fields.

**Fixtures:**
- `lab/fixtures/logs/AP01m.fbc` — sample FBC data (12 tokens, AI/DI fields)
- `lab/fixtures/logs/AP01m.rpc` — sample RPC data
- `lab/fixtures/logs/AP01m.lis` — sample LIS data
- `lab/fixtures/logs/AP01m.log` — sample log file with timestamps and severity levels

**Results:** Not yet run — lab is ready to deploy. See `lab/README.md` for deployment commands. After coder fixes, re-run the lab — all tests should pass (the `karate.fail()` calls with gap references should stop triggering).

**Test design:** Tests are designed to PASS when features work and FAIL with descriptive gap references when they don't. Example: `karate.fail('PDF format not supported — CRITICAL gap F1')`. This means:
- Before coder fixes: tests fail with gap references = evidence gaps exist
- After coder fixes: tests pass = evidence gaps are closed
- This is built-in regression detection — no need to modify tests after fixes

---

## What Was Not Tested

- No real DNA node available — telnet tested against mock only, not real Valmet DNA hardware
- BsTool.exe is Windows-only — Wine node not yet added to topology (instructions in `lab/README.md`)
- PDF generation — cannot test because the feature doesn't exist
- Hierarchical commands — cannot test because context menus don't exist
- Log writer — cannot test because the feature doesn't exist
- Load testing / concurrent users — not in scope (single-user desktop app replacement)
- Lab not yet deployed on Containerlab host — topology and tests are ready, deployment pending

---

## Build/Run Commands

```bash
# Frontend build (MUST succeed before Go build)
cd /opt/data/LOGReport/web && npm run build

# Go build
cd /opt/data/LOGReport && /opt/data/go/bin/go build -o logreport-bin ./cmd/logreport/

# Go tests
cd /opt/data/LOGReport && /opt/data/go/bin/go test ./... -v

# Frontend tests
cd /opt/data/LOGReport/web && npx vitest run

# Run app
cd /opt/data/LOGReport && ./logreport-bin --port 8642 --db-path logreport.db

# Health check
curl -s http://localhost:8642/api/v1/health

# Run review lab
ssh -i /opt/data/.ssh/hermes_desktop root@100.78.148.26
cd /opt/data/LOGReport/reviews/2026-06-25-review-001/lab
containerlab deploy -t topology.yml
sleep 10
docker exec clab-logreport-test-lab-karate java -jar /karate.jar -o /target/karate-reports /tests/
containerlab destroy -t topology.yml
```

---

## Reviewer Notes

- **Interpretation drift is the critical finding.** The coder built a report generator from SQLite scan data. The original processes log files. Different data pipelines. The coder understood the tech stack but not the workflow.
- **Frontend build had a stale bundle issue** — `tsc -b` failed on unused imports in 3 test files (TS6133), `vite build` never ran, old JS bundle embedded. Commander route 404'd. Fixed during review. Coder must run `npm run build` manually and check exit code before every `go build`.
- **Port 8642** is the correct port for this container environment — forwarded from host Tailscale IP (100.78.148.26) to container.
- **Lab tests are designed to fail with gap references** — this is intentional. Each `karate.fail()` message names the gap (F1, F2, F3, F5) so the coder knows exactly what to fix. After fixes, tests pass = evidence gaps are closed.
- **Re-review after coder fixes:** Deploy lab, run all features, check that gap-reference failures are gone. Then do manual recipient-experience review: select log folder, generate PDF, scan FBC files, check tree icons, right-click context menu. Test from Goran's seat.