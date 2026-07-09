# LOGReport v420 — Review 2026-07-01-006 (Review-005 Fixes Verification)

**Date:** 2026-07-01
**Reviewer:** Coder agent
**Review type:** Verification of 12 findings from review-005 (F1-F12) + v418-v419 feature audit
**Live binary:** LOGReport v420 on vegas-vm-v5 (Windows Server 2019, agent_id=a0-falke)
**Listening port:** 8700
**Testing method:** Source code review + live API testing via HermesRemote exec API (SSH tunnel to VPS → VM)

---

## Verdict Summary

| Finding | Severity | Verdict | Evidence |
|---------|----------|---------|----------|
| F1 | CRITICAL | **PASS** | `_LOG/AP01m/fbc/AP01m_192-168-0-11_22.fbc` structure confirmed on disk |
| F2 | CRITICAL | **PASS** | Project creation auto-creates `_LOG/` — confirmed `_LOG` in project dir immediately after POST |
| F3 | CRITICAL | **PASS** | PDF has `/Link`, `/Dest`, `/Annots` — 8 clickable TOC entries, 10 pages |
| F4 | CRITICAL | **PASS** (code) | Dashboard.tsx calls `selectProject(created.id, ...)` after creation |
| F5 | CRITICAL | **PASS** (partial) | "Create Structure" button (FolderPlus icon) in NodeTree toolbar; not in Nodes sub-header |
| F6 | HIGH | **PASS** | Queue batches 11 commands; CommandQueueBar shows "N remaining" in code |
| F7 | HIGH | **PASS** (code) | NodeTree.tsx has `showPulse` logic + `animation: 'pulse 1s ease-in-out infinite'` + CSS `@keyframes pulse` |
| F8 | HIGH | **FAIL** | Cancel takes 8s to stop — telnet Connect() blocks cancel channel |
| F9 | HIGH | **PASS** (code) | `CMD_STATUS_COLORS.failed = '#f97316'` (orange) in NodeTree.tsx |
| F10 | MEDIUM | **PASS** | Tree API returns station `status` field — all 7 stations show `error` (empty files) |
| F11 | MEDIUM | **PASS** | DOCX has Heading1, TOC field (`TOC \o`), bookmarks (`bookmarkStart`), `fldChar`, `styles.xml` with Heading1 style |
| F12 | MEDIUM | **PASS** | Settings GET returns all 9 fields; POST save echoes `bstool_path` and `communication_line` correctly |

**Score: 11 PASS, 1 FAIL (F8)**

---

## Detailed Evidence

### F1 — _LOG wrapper folder: PASS

**Source:** `handlers_structure.go` L116: `dir := filepath.Join(logRoot, logRootName, stationName, strings.ToLower(tokenType))` — adds `_LOG` segment + lowercase type dirs.

**Live test:** `POST /api/v1/nodesconfig/create-structure` with `log_root: "C:\temp\test_v420_f1b"`:
```
created_dirs: 11, created_files: 11, station_count: 7
First 3 paths:
  C:\temp\test_v420_f1b\_LOG\AP01m\fbc\AP01m_192-168-0-11_22.fbc
  C:\temp\test_v420_f1b\_LOG\AP01m\rpc\AP01m_192-168-0-11_22.rpc
  C:\temp\test_v420_f1b\_LOG\AP01m\log\AP01m_192-168-0-11.log
```
- `_LOG` wrapper: ✅ present
- Lowercase type dirs: ✅ `fbc/`, `rpc/`, `log/`
- `BuildFileTree` reads from `_LOG/` first, falls back to old `{station}/{type}/` path (loader.go L246-251)

### F2 — Auto-create on project creation: PASS

**Source:** `handlers_projects.go` L48-53: after `CreateProject`, calls `s.createLogStructure(created.LogRoot)` if `LogRoot != ""`.

**Live test:** `POST /api/v1/projects` with `log_root: "C:\temp\test_v420_f2b"`:
```
Project created: id=9, T420F2B/TEST_F2B
Contents of C:\temp\test_v420_f2b: _LOG
_LOG auto-created: True
```

### F3 — PDF clickable TOC: PASS

**Source:** `pdf.go` L157-168: `tocLinks[node] = pdf.AddLink()` → `pdf.CellFormat(0, 7, ..., link)` → `pdf.SetLink(tocLinks[node], -1, pdf.PageNo())`.

**Live test:** Generated PDF from `_LOG` structure (7 nodes, 11 files):
```
FileSize: 6615
Link: True
Dest: True
Annots: True
PageCount: 10
```
First 2000 chars of PDF binary show 8 `/Annot /Subtype /Link` entries with `/Dest [5 0 R /XYZ ...]` targets — clickable TOC confirmed.

### F4 — Auto-select project after creation: PASS (code review)

**Source:** `Dashboard.tsx` L85-87: after `fetchProjects()`, calls `selectProject(created.id, created.log_root || newProject.log_root || '')`.

The `useActiveProject` hook (`useActiveProject.ts`) sets `localStorage` and fires `activeProjectChange` event for cross-component sync.

### F5 — Create Structure button: PASS (partial)

**Source:** `NodeTree.tsx` L320-330: `FolderPlus` icon button labeled "Create Structure" in NodeTree toolbar, visible when `onCreateStructure` prop is provided.

**Note:** Button is in the NodeTree component toolbar, not in the NodesPage sub-header. This is a known partial fix — the button exists but in a different location than the review-005 suggestion.

### F6 — Remaining count in sequence bar: PASS

**Source:** `CommandQueueBar.tsx` L117: `Command ${status.current + 1}/${status.total}: ${cmdLabel} — ${status.total - status.current - 1} remaining`

**Live test:** `POST /api/v1/commandqueue/batch` → `total: 11` commands queued. Status endpoint returns `commands`, `current`, `total` — frontend computes remaining.

### F7 — Pulsing marker on executing file: PASS (code review)

**Source:** `NodeTree.tsx`:
- L539: `const showPulse = isActive;`
- L594-607: pulsing `<span>` with `animation: 'pulse 1s ease-in-out infinite'`, `boxShadow: '0 0 4px var(--accent)'`
- L618-632: duplicate pulsing marker for file type nodes
- `isActive` set at L526-528 when `activeCommand.status === 'running'` and node matches

**CSS:** `theme.css` L140-143: `@keyframes pulse { 0%, 100% { opacity: 1; transform: scale(1); } 50% { opacity: 0.4; transform: scale(1.3); } }`

### F8 — Immediate pause/cancel: FAIL

**Source:** `queue.go` L198-209 (Pause) and L224-236 (Cancel): both close `cancelCh`. `waitForOutput` (handlers_commander.go L1295-1298, L1318-1321) checks `cancelCh` and returns immediately.

**Live test:** Queued 11 commands, started, waited 2s, cancelled:
```
t+1s: state=running, running=1, cancelled=0
t+2s: state=running, running=1, cancelled=0
...
t+7s: state=running, running=1, cancelled=0
t+8s: state=idle, running=0, cancelled=10
```
**Root cause:** The executor function (`handlers_commander.go` L577-651) first calls `s.telnetSM.Connect()` (L615) which blocks for up to 10 seconds when the DIA host (192.168.0.11) is unreachable. The `cancelCh` is only checked inside `waitForOutput` (L637), NOT during the `Connect` call. When the first command is in the connection phase, closing `cancelCh` has no effect until the connect timeout expires.

**Fix needed:** Pass `cancelCh` to the telnet `Connect` call, or use a context-based dial with cancellation. Alternatively, check `cancelCh` after `Connect` returns and before `SendCommand`.

### F9 — Distinct failed color: PASS (code review)

**Source:** `NodeTree.tsx` L39: `failed: '#f97316'` (orange) — distinct from `error: 'var(--error)'` (red) at L47.
Also L40: `error: '#f97316'` — command errors also use orange.

### F10 — Node aggregate color: PASS

**Source:** `loader.go` L388-404: `aggregateStationStatus()` — any error→"error", some warning→"warning", all idle→"idle". Called at L333: `stationNode.Status = aggregateStationStatus(stationNode.Children)`.

**Live test:** Tree API returns station status:
```
Station statuses: ['AP01m=error', 'AP05m=error', 'AB01=error', 'AD01=error', 'A1A1=error', 'A1O1=error', 'B1O1=error']
```
All stations show `error` because all files are empty (0 bytes → `fileStatus(0) = "error"`). This is correct behavior — empty files = error status.

### F11 — DOCX TOC + heading styles: PASS

**Source:** `generator.go`:
- L264-270: TOC field with `w:fldChar` (begin/separate/end) + `TOC \o "1-1" \h \z` instruction
- L282-284: `w:bookmarkStart`/`w:bookmarkEnd` for each node
- L283: `w:pStyle w:val="Heading1"` on node headings
- L347-373: `word/styles.xml` with Heading1 style definition (Arial bold 16pt, outlineLvl 0)
- L223-224: Content types include `styles.xml` override

**Live test:** DOCX unzipped and checked:
```
Heading1: True
TOC_field: True
Bookmarks: True
FldChar: True
styles_xml: True
Heading1_in_styles: True
```

### F12 — Settings persistence: PASS

**Source:** `handlers_settings.go`:
- L28-38: `defaultSettings()` includes `LogRootName: "_LOG"`, all fields with defaults
- L81-103: `initSettings()` fills zero-value fields with defaults (including `BsToolPath`, `CommunicationLine`)
- L160-182: `handleSaveSettings` fills defaults for empty fields before saving
- L21-24: `Settings` struct has all 9 fields: `dia_host`, `dia_port`, `bstool_host`, `bstool_port`, `log_root`, `logroot_name`, `bstool_path`, `communication_line`, `output_dir`

**Live test:**
- GET settings: all 9 fields present, `logroot_name: "_LOG"`
- POST settings with `bstool_path: "C:\dna\CA\bstool\BsTool.exe"`, `communication_line: "EAS-C2023"`:
  - Save response echoes both values correctly ✅

---

## v418-v419 Features Verification

| Feature | Verdict | Evidence |
|---------|---------|----------|
| Global project selection (`useActiveProject`) | PASS | `web/src/hooks/useActiveProject.ts` — localStorage + custom event sync across Dashboard, Nodes, Commander, Reports, StatusBar |
| Commander LogRoot selector | PASS | `CommanderLayout.tsx` L284-352 — dropdown with project log_roots + custom path input, replaces project dropdown |
| Commander "Print All Logs" button | PASS | `CommanderLayout.tsx` L372 — "Print All Logs" button, handler at L244-265 batches all nodes + starts execution |
| Reports right-click context menu (Delete + Regenerate) | PASS | `ReportList.tsx` L317 `onContextMenu` → L435-468 context menu with "Regenerate Report" + "Delete Report" |
| `DELETE /api/v1/reports/{id}` endpoint | PASS | Live test: `DELETE /api/v1/reports/{id}` returns `{"deleted":true,"id":"..."}` |
| Settings `logroot_name` field (default `_LOG`) | PASS | `handlers_settings.go` L22 + L35: `LogRootName` field with default `_LOG` |
| StatusBar shows active project | PASS | `StatusBar.tsx` L91-95: shows `activeProject.project_number — activeProject.ship_name` with FolderOpen icon |

---

## Logwriter _LOG Path Consistency: PASS

**Source:** `writer.go` L97-111: `logPath()` returns `filepath.Join(lw.logRoot, "_LOG", stationName, typeDir, fileName)` — writes to `_LOG/{station}/{TYPE}/` structure. Consistent with `createLogStructure` which creates `_LOG/{station}/{lowercase-type}/`.

**Note:** Logwriter uses uppercase type dir (`strings.ToUpper(tokenType)`) while `createLogStructure` uses lowercase (`strings.ToLower(tokenType)`). On Windows, the filesystem is case-insensitive, so `FBC` and `fbc` resolve to the same directory. This is not a bug on Windows but would be on Linux.

---

## What Was Not Tested

1. **F4 (auto-select) live UI test** — Edge headless can't set localStorage, so can't verify Commander shows tree after project creation. Code review confirms `selectProject()` is called.
2. **F7 (pulsing marker) visual** — Can't screenshot with project selected (localStorage limitation). Code review confirms all logic + CSS.
3. **F9 (failed color) visual** — No failed commands with real data to observe. Code review confirms orange `#f97316`.
4. **F8 root cause fix** — The cancel channel IS passed to `waitForOutput` (working), but NOT to `telnet.Connect()` (blocking). This is the remaining gap.
5. **Real command execution** — DIA node (192.168.0.11) unreachable from VM. All queue commands fail with telnet timeout.

---

## F8 Failure Analysis

The F8 fix is **partially implemented**. The cancel channel (`cancelCh`) is:
- ✅ Closed by `Pause()` and `Cancel()` (queue.go L202-209, L228-235)
- ✅ Checked by `waitForOutput()` (handlers_commander.go L1295-1298, L1318-1321)
- ✅ Passed to `waitForOutput` from the executor (L637)
- ❌ NOT checked during `telnetSM.Connect()` (L615) — this call blocks for up to 10s on unreachable hosts

When the DIA host is unreachable (as in this test), the first command's executor spends ~8s in `Connect()` before reaching `waitForOutput()`. Cancel during this window has no effect.

**Recommended fix:** Use `net.Dialer` with context in `telnet.Connect()`, passing a context that is cancelled when `cancelCh` is closed. Or add a select on `cancelCh` after `Connect()` returns and before `SendCommand()`.