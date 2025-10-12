# PyQt6 → PyQt5 Test Migration Addendum
**Date**: 2025-10-12  
**Context**: Application migrated from PyQt6 to PyQt5 a few days ago (2025-01-11)  
**Issue**: 33 tests (40.2%) still use PyQt6 imports  
**Phase**: Will be addressed in Phase 6 (Alignment Implementation)

## Migration Context

### Application Migration (Completed 2025-01-11)
- **Reason**: Windows Server 2012 compatibility (Qt 6.4+ requires Win 10 1809+, Qt 5.15.2 supports Server 2012)
- **Scope**: 169+ files updated (80+ in src/, 89+ in tests/)
- **Pattern**: 5-step migration (imports, enums, methods, QAction, runtime paths)
- **Result**: 23/34 PyQt-specific tests passing, 11 pre-existing business logic failures

### Test Migration Status (Current)
- **PyQt5**: 32 tests (39.0%) - Correctly migrated
- **PyQt6**: 33 tests (40.2%) - **LAGGING BEHIND**
- **None**: 17 tests (20.7%) - No Qt dependency

## Root Cause Analysis

### Why 33 Tests Remained in PyQt6

1. **LLM-Generated Tests (Primary)**: 27/33 are root-level tests likely generated before migration
   - These tests were created ad-hoc and never properly integrated
   - No systematic review process caught them during migration

2. **Overlooked During Migration**: Some tests may have been skipped
   - Bulk migration used PowerShell regex patterns
   - May have missed files due to path patterns or timing

3. **Post-Migration Creation**: Some tests created after migration using old templates/patterns
   - Developers may have copied from old test files
   - LLM may have used pre-migration codebase examples

## Affected Test Distribution

### By Location
| Location | PyQt6 Tests | Total Tests | % PyQt6 |
|----------|-------------|-------------|---------|
| Root (unconsolidated) | 27 | 35 | 77.1% |
| Commander | 6 | 40 | 15.0% |
| Other | 0 | 7 | 0% |

### By Theme
| Theme | PyQt6 Tests | Notes |
|-------|-------------|-------|
| Token Detection | 5 | All root-level versions |
| Node Management | 4 | Root-level tests |
| BsTool | 2 | Root-level tests |
| Command Execution | 2 | Root hierarchical tests |
| Node Config | 3 | All UI-related |
| Telnet | 2 | Root-level tests |
| Tree Expansion | 2 | Auto-expansion tests |
| Qt Behavior | 1 | Root-level test |
| Other | 12 | Various scattered tests |

## 5-Step Migration Pattern

### Step 1: Import Statements
```python
# BEFORE (PyQt6)
from PyQt6.QtWidgets import QMainWindow, QWidget
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QPalette

# AFTER (PyQt5)
from PyQt5.QtWidgets import QMainWindow, QWidget
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QPalette
```

### Step 2: Enum Attributes
```python
# BEFORE (PyQt6)
palette.setColor(QPalette.ColorRole.Window, Qt.GlobalColor.black)
item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

# AFTER (PyQt5)
palette.setColor(QPalette.Window, Qt.black)
item.setTextAlignment(Qt.AlignCenter)
```

### Step 3: Method Calls
```python
# BEFORE (PyQt6)
app.exec()
dialog.exec()

# AFTER (PyQt5)
app.exec_()
dialog.exec_()
```

### Step 4: QAction Import Path
```python
# BEFORE (PyQt6)
from PyQt6.QtGui import QAction

# AFTER (PyQt5)
from PyQt5.QtWidgets import QAction
```

### Step 5: Runtime Paths (if any)
```python
# BEFORE (PyQt6)
'PyQt6/Qt6/plugins'

# AFTER (PyQt5)
'PyQt5/Qt5/plugins'
```

## Test-Specific Migration Considerations

### Mock Decorators
```python
# BEFORE (PyQt6)
@patch('src.commander.ui.commander_window.QMessageBox', spec=QMessageBox)
# Comment: Uses PyQt6 QMessageBox

# AFTER (PyQt5)
@patch('src.commander.ui.commander_window.QMessageBox', spec=QMessageBox)
# Comment: Uses PyQt5 QMessageBox (import updated at top)
```

### Import Validation Tests
Some tests explicitly check imports - these need special attention:
```python
# Example: test_bstool_import.py
def test_bstool_imports():
    # Validate that PyQt5 is used (not PyQt6)
    assert 'PyQt5' in sys.modules
```

## Migration Execution Plan (Phase 6)

### Automated Approach (PowerShell)
```powershell
# Step 1: Backup
Copy-Item "d:\_APP\LOGReport\tests" "d:\_APP\LOGReport\backups\tests_pre_pyqt5_migration" -Recurse

# Step 2: Bulk Replace Imports
Get-ChildItem -Path "d:\_APP\LOGReport\tests" -Recurse -Filter "*.py" | ForEach-Object {
    $content = Get-Content $_.FullName -Raw
    $content = $content -replace 'from PyQt6', 'from PyQt5'
    $content = $content -replace 'import PyQt6', 'import PyQt5'
    Set-Content $_.FullName -Value $content
}

# Step 3: Enum Updates (manual validation recommended)
Get-ChildItem -Path "d:\_APP\LOGReport\tests" -Recurse -Filter "*.py" | ForEach-Object {
    $content = Get-Content $_.FullName -Raw
    # Common enum patterns
    $content = $content -replace 'QPalette\.ColorRole\.', 'QPalette.'
    $content = $content -replace 'Qt\.GlobalColor\.', 'Qt.'
    $content = $content -replace 'Qt\.AlignmentFlag\.', 'Qt.'
    Set-Content $_.FullName -Value $content
}

# Step 4: Method calls (exec → exec_) - manual review recommended
```

### Manual Verification (Required)
1. **QAction imports**: Check 6-8 tests with context menus
2. **exec() calls**: Search for `.exec()` and update to `.exec_()`
3. **Complex enums**: Validate alignment flags, key modifiers
4. **Comments**: Update any PyQt6 references in docstrings

### Validation
```bash
# After migration, run all tests
pytest tests/ -v --tb=short

# Expected: Pass rate should match or improve pre-migration 23/34 PyQt tests
# Any failures should be business logic, not import errors
```

## Priority Order for Migration

### HIGH PRIORITY (Break functionality)
1. **Integration tests** (19 tests) - May fail with import errors
2. **System tests** (3 tests) - E2E workflows affected

### MEDIUM PRIORITY (Quality issues)
3. **Unit tests** (6 tests) - Isolated but need consistency
4. **Exploratory tests** (5 tests) - Low impact but should be consistent

## Expected Outcomes

### Before Migration
- **PyQt6 tests**: 33 (40.2%)
- **Import errors**: Potential when running these tests
- **Inconsistency**: Mixed PyQt5/PyQt6 imports across test suite

### After Migration
- **PyQt6 tests**: 0 (0%)
- **PyQt5 tests**: 65 (79.3%)
- **No Qt tests**: 17 (20.7%)
- **Consistency**: 100% PyQt5 where Qt is used
- **Pass rate**: Maintain or improve 23/34 PyQt test pass rate

## Risks & Mitigation

### Risk 1: Enum Breaking Changes
- **Issue**: PyQt6 → PyQt5 enum syntax differences
- **Mitigation**: Manual review of complex enum usage (alignment, colors, keys)
- **Test**: Run tests incrementally, validate enum-heavy tests first

### Risk 2: exec() Method Ambiguity
- **Issue**: Python's `exec()` vs Qt's `exec_()`
- **Mitigation**: Search for `\.exec\(` and validate each instance
- **Test**: Pay attention to dialog and app execution

### Risk 3: QAction Import Path
- **Issue**: QAction moved from QtGui to QtWidgets in PyQt5
- **Mitigation**: Explicit check of all QAction imports
- **Test**: Context menu tests should validate this

### Risk 4: Test Breakage
- **Issue**: Migration may break currently passing tests
- **Mitigation**: Backup before migration, incremental validation
- **Test**: Run tests after each major change, rollback if needed

## Post-Migration Checklist

- [ ] All 33 PyQt6 tests updated to PyQt5
- [ ] No import errors when running test suite
- [ ] PyQt-specific test pass rate ≥ 23/34 (pre-migration baseline)
- [ ] Manual validation of enum usage
- [ ] Manual validation of exec_() calls
- [ ] Manual validation of QAction imports
- [ ] Comments/docstrings updated
- [ ] Migration documented in CHANGELOG
- [ ] Test consistency verified (no mixed PyQt5/PyQt6)

## Integration with Test Consolidation

### Timing Consideration
**Option A**: Migrate before consolidation (Phase 6 early)
- **Pro**: All tests consistent before reorganization
- **Con**: May update tests that will be removed

**Option B**: Consolidate first, then migrate (Phase 6 late)
- **Pro**: Fewer files to migrate (75 vs 82)
- **Con**: Working with inconsistent imports during consolidation

**Recommendation**: **Option A** - Migrate before consolidation
- Rationale: Import errors can mask other issues during consolidation
- Approach: Quick bulk migration (automated) before manual consolidation work
- Benefit: Cleaner consolidation process with consistent codebase

## Automation Script

```powershell
# Complete PyQt6 → PyQt5 Test Migration Script
# Location: misc/scripts/migrate_tests_pyqt6_to_pyqt5.ps1

param(
    [switch]$DryRun = $false
)

$testDir = "d:\_APP\LOGReport\tests"
$backupDir = "d:\_APP\LOGReport\backups\tests_pre_pyqt5_migration_$(Get-Date -Format 'yyyyMMdd_HHmmss')"

# Step 1: Backup
if (-not $DryRun) {
    Write-Host "Creating backup: $backupDir"
    Copy-Item $testDir $backupDir -Recurse
}

# Step 2: Get all test files
$testFiles = Get-ChildItem -Path $testDir -Recurse -Filter "*.py" | Where-Object {
    (Get-Content $_.FullName -Raw) -match 'PyQt6'
}

Write-Host "Found $($testFiles.Count) files with PyQt6 references"

foreach ($file in $testFiles) {
    Write-Host "Processing: $($file.Name)"
    $content = Get-Content $file.FullName -Raw
    
    # Track changes
    $originalContent = $content
    
    # Apply transformations
    $content = $content -replace 'from PyQt6', 'from PyQt5'
    $content = $content -replace 'import PyQt6', 'import PyQt5'
    $content = $content -replace 'QPalette\.ColorRole\.', 'QPalette.'
    $content = $content -replace 'Qt\.GlobalColor\.', 'Qt.'
    $content = $content -replace 'Qt\.AlignmentFlag\.', 'Qt.'
    $content = $content -replace '# Comment: Uses PyQt6', '# Comment: Uses PyQt5'
    $content = $content -replace 'PyQt6/Qt6', 'PyQt5/Qt5'
    
    # Report changes
    if ($content -ne $originalContent) {
        Write-Host "  - Updated imports and enums"
        if (-not $DryRun) {
            Set-Content $file.FullName -Value $content
        }
    } else {
        Write-Host "  - No changes needed"
    }
}

Write-Host ""
Write-Host "Migration complete!"
Write-Host "Next steps:"
Write-Host "1. Review changes: git diff tests/"
Write-Host "2. Run tests: pytest tests/ -v"
Write-Host "3. Manual validation: Check QAction imports and exec_() calls"
```

---
**Generated**: 2025-10-12  
**Next Action**: Phase 6 - Execute PyQt6 → PyQt5 migration for 33 test files  
**Integration**: Migrate early in Phase 6 before consolidation work
