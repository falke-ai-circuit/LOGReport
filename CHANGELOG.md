# Changelog

All notable changes to LOGReport are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/), and this project adheres to [Semantic Versioning](https://semver.org/).

## [v3.9.84] — 2026-07-28

### Fixed

Eight workflow bugs affecting report generation, project paths, and node management:

- **Bug #1: Doubled project path** — When a project's `log_root` already ends with `{project_number}_{ship_name}`, the path is now used directly instead of appending the project folder name again. This was the root cause of Bugs #3, #5, and #6.
  - Files: `internal/api/handlers_projects.go`

- **Bug #2: UUID report filename** — Report filenames now use a descriptive format (`{ProjectNumber}_{ShipName}_{date}.pdf`, e.g., `G0001_GORIZIA_TEST_2026-07-28.pdf`) instead of a random UUID. `ProjectNumber` and `ShipName` are passed to `ReportConfig` so `outputPathForConfig` generates the descriptive name.
  - Files: `internal/api/handlers_projects.go`, `internal/report/generator.go`

- **Bug #3: 2KB PDF reports** — PDF reports were only ~2KB because the file scanner was finding files in the wrong (doubled) directory path. Fixed by the Bug #1 path resolution fix. Reports are now ~50KB with actual log content.
  - Root cause: Bug #1 (doubled path)

- **Bug #4: Report saved to wrong location** — Reports are now saved to `{logRoot}/reports/` folder. Previously, `OutputDir` was set to the parent directory of `logRoot`. The `generateProjectReportHandler` now sets `OutputDir = filepath.Join(p.LogRoot, "reports")`.
  - Files: `internal/api/handlers_projects.go`

- **Bug #5: All Nodes selection not respected** — This was a metadata display issue; the report content was actually correct. Fixed as a downstream effect of the Bug #1 path resolution fix.
  - Root cause: Bug #1 (doubled path)

- **Bug #6: nodes.json location mismatch** — The `nodes.json` file location was inconsistent because the doubled path bug caused it to be read/written from the wrong directory. Fixed by the Bug #1 path resolution fix.
  - Root cause: Bug #1 (doubled path)
  - Files: `internal/api/handlers_nodesconfig.go`

- **Bug #7: Node count shows 0 in health endpoint** — The health endpoint (`GET /health`) now accepts an optional `?project_id=` query parameter. When provided, it counts nodes from the project-specific `nodes.json` (via `nodesConfigPathForProject`) instead of the global default. This returns the correct node count for the active project.
  - Files: `internal/api/handlers.go`

- **Bug #8: "No project selected" persists in StatusBar** — The StatusBar component now shows `Project #ID` as a fallback when the full project object is not yet loaded in the frontend state. Previously, it showed "No project selected" even when a project ID was active.
  - Files: `web/src/components/StatusBar.tsx`, `web/src/components/Dashboard.tsx`

### Changed

- **ReportList shows descriptive filename** — The report list in the frontend now extracts the filename from `file_path` (e.g., `G0001_GORIZIA_TEST_2026-07-28.pdf`) instead of displaying the raw UUID `report_id`. Falls back to `report_id` if `file_path` is not available.
  - Files: `web/src/components/ReportList.tsx`

### Tests

- Fixed project report test to match the new fallback behavior. Projects without an explicit `log_root` now get a default path, so report generation succeeds (empty report) instead of returning HTTP 400.
  - Files: `internal/api/handlers_projects_test.go`
- All 15 internal Go packages pass tests.

## [v3.9.83] — 2026-07-28

### Added

- Real Valmet logo embedded in PDF reports
- Web favicon (Valmet logo)
- App header logo

## [v3.9.82] — 2026-07-28

### Changed

- Internal refactoring and API improvements (details in commit history).

## [v3.9.43] — Earlier

- Version reference used in frontend test mocks (`Dashboard.test.tsx`).