# BsTool Bundling Test Documentation

**Date**: 2025-10-13  
**Purpose**: Validate BsTool.exe bundling and path detection in PyInstaller executable

## Overview

This document outlines the testing procedure for verifying that BsTool.exe is properly bundled with the LOGReporter executable and that the application correctly detects and handles various scenarios.

## Pre-Requisites

1. ✅ BsTool.exe exists in project root (`D:\_APP\LOGReport\BsTool.exe`)
2. ✅ LOGReporter_PyQt5.spec configured with BsTool.exe in `binaries` section
3. ✅ bstool_path_resolver.py implemented with detection logic
4. ✅ bstool_tab.py auto-populates path field on initialization

## Test Scenarios

### Scenario 1: Normal Operation (BsTool.exe Present)

**Objective**: Verify auto-detection works when BsTool.exe is bundled

**Steps**:
1. Build executable: `pyinstaller --clean LOGReporter_PyQt5.spec`
2. Navigate to `dist\LOGReporter\` directory
3. Verify `BsTool.exe` exists in the same directory as `LOGReporter.exe`
4. Launch `LOGReporter.exe`
5. Navigate to **BsTool** tab
6. Observe the "BsTool Execution Path" field

**Expected Results**:
- ✅ Path field auto-populated with correct path to bundled BsTool.exe
- ✅ Path should be: `<exe_directory>\BsTool.exe` or `<_MEIPASS>\BsTool.exe`
- ✅ No error messages in logs
- ✅ BsTool commands execute successfully

**Validation**:
```
Expected path format: C:\path\to\dist\LOGReporter\BsTool.exe
OR (if onefile mode): C:\Users\<user>\AppData\Local\Temp\_MEI<random>\BsTool.exe
```

---

### Scenario 2: Missing BsTool.exe (Error Handling)

**Objective**: Verify graceful degradation when BsTool.exe is not found

**Setup**:
1. In the `dist\LOGReporter\` directory, rename `BsTool.exe` to `BsTool_BACKUP.exe`
2. This simulates the scenario where BsTool.exe is missing

**Steps**:
1. Launch `LOGReporter.exe`
2. Navigate to **BsTool** tab
3. Observe the "BsTool Execution Path" field
4. Check `debug.log` and `system.log` for error messages
5. Attempt to execute a BsTool command (if possible)

**Expected Results**:
- ✅ Path field should be **empty** OR show placeholder text
- ✅ Log files should contain warning: `"Could not find BsTool.exe"`
- ✅ Application continues running (no crash)
- ✅ User can manually enter path if needed
- ✅ Attempting to execute command shows user-friendly error

**Log Validation**:
```
Expected log entry:
WARNING - get_bstool_path: Could not find bstool.exe in any expected location
```

---

### Scenario 3: Manual Path Override

**Objective**: Verify user can manually specify BsTool.exe location

**Setup**:
1. Create alternate directory: `dist\LOGReporter\tools\`
2. Move `BsTool_BACKUP.exe` to this directory and rename back to `BsTool.exe`
3. BsTool.exe now at: `dist\LOGReporter\tools\BsTool.exe`

**Steps**:
1. Launch `LOGReporter.exe`
2. Navigate to **BsTool** tab
3. Path field should be empty (auto-detection fails)
4. Click **Browse** button or manually type path: `tools\BsTool.exe`
5. Execute a BsTool command
6. Close and re-open application

**Expected Results**:
- ✅ Empty path field on first launch
- ✅ User can browse or type custom path
- ✅ Commands execute successfully with custom path
- ✅ Custom path **persists** across sessions (saved in QSettings)

**Persistence Validation**:
- After restart, the manually entered path should still be in the field

---

### Scenario 4: PyInstaller Onefile Mode (If Used)

**Objective**: Verify BsTool.exe extraction in onefile mode

**Setup**:
- Modify `.spec` file for onefile mode (if not already)
- Add `runtime_hooks` if needed

**Steps**:
1. Build with onefile mode
2. Launch single `LOGReporter.exe`
3. Navigate to BsTool tab
4. Check path field
5. Open Task Manager → Details → Find LOGReporter.exe
6. Note the PID and check `%TEMP%` for `_MEI*` directories

**Expected Results**:
- ✅ BsTool.exe extracted to temporary `_MEI*` directory
- ✅ Path shows temp location: `C:\Users\<user>\AppData\Local\Temp\_MEI<random>\BsTool.exe`
- ✅ Commands execute from temp location
- ✅ Temp files cleaned up after application closes

---

## Automated Test Script

A PowerShell test script is available: `scripts\test_bundled_exe.ps1`

**Usage**:
```powershell
cd D:\_APP\LOGReport
.\scripts\test_bundled_exe.ps1
```

The script automates:
- Building the executable
- Setting up test scenarios
- Launching application for each scenario
- Providing step-by-step instructions
- Cleanup

---

## Validation Checklist

After completing all test scenarios, verify:

### ✅ Build Configuration
- [ ] `LOGReporter_PyQt5.spec` includes `('BsTool.exe', '.')` in `binaries`
- [ ] Build completes without errors
- [ ] `BsTool.exe` present in `dist` output directory

### ✅ Auto-Detection
- [ ] Path field auto-populates in normal scenario
- [ ] Detection works in both dev and bundled modes
- [ ] Correct priority: `_MEIPASS` → `executable dir` → `project root`

### ✅ Error Handling
- [ ] Application doesn't crash when BsTool.exe missing
- [ ] User-friendly error messages displayed
- [ ] Warning logs written (not errors that crash)
- [ ] UI remains functional

### ✅ User Override
- [ ] Manual path entry works
- [ ] Browse button functions
- [ ] Custom path persists across sessions
- [ ] Relative and absolute paths both work

### ✅ Command Execution
- [ ] Commands work with auto-detected path
- [ ] Commands work with manual path
- [ ] Temp file reading works (10s timeout)
- [ ] Output displays correctly in BsTool tab

---

## Known Issues / Edge Cases

### Issue 1: Path with Spaces
- **Test**: Try path like `C:\Program Files\BsTool\BsTool.exe`
- **Expected**: Should work with proper quoting in subprocess call

### Issue 2: UNC Paths
- **Test**: Try network path like `\\server\share\BsTool.exe`
- **Expected**: Should work if network accessible

### Issue 3: Unicode Characters
- **Test**: Path with non-ASCII characters
- **Expected**: Should work with proper encoding

### Issue 4: Read-Only Temp Directory
- **Test**: Temp folder permissions restricted
- **Expected**: Graceful error message

---

## Reporting Results

After testing, document findings in:
1. `TODO.md` - Mark task as completed or note issues
2. `CHANGELOG.md` - Add entry for bundling feature
3. `logs/workflow_*.md` - Create workflow log for this task

**Template**:
```markdown
## BsTool Bundling Test Results

**Date**: 2025-10-13
**Tester**: [Your Name]
**Build**: LOGReporter v[X.Y.Z]

### Scenario 1: Normal Operation
- Status: ✅ PASS / ❌ FAIL
- Notes: [observations]

### Scenario 2: Missing BsTool
- Status: ✅ PASS / ❌ FAIL
- Notes: [observations]

### Scenario 3: Manual Override
- Status: ✅ PASS / ❌ FAIL
- Notes: [observations]

### Overall Assessment
- Bundling: ✅ Working / ❌ Issues
- Auto-detection: ✅ Working / ❌ Issues
- Error handling: ✅ Working / ❌ Issues
- Ready for production: ✅ YES / ❌ NO
```

---

## Troubleshooting

### BsTool.exe Not Found in Dist
**Symptom**: `BsTool.exe` missing after build

**Solutions**:
1. Check `.spec` file `binaries` section
2. Verify `BsTool.exe` exists in project root before build
3. Run `pyinstaller --clean` to rebuild from scratch
4. Check build output for warnings

### Path Field Empty Despite BsTool Present
**Symptom**: Path field not auto-populating

**Solutions**:
1. Check `debug.log` for path detection attempts
2. Verify `bstool_tab.py` calls `_auto_populate_bstool_path()`
3. Check if `bstool_path_resolver.get_bstool_path()` returns correct path
4. Test in Python console:
   ```python
   from commander.utils.bstool_path_resolver import get_bstool_path
   print(get_bstool_path())
   ```

### Commands Fail Despite Correct Path
**Symptom**: Path shows correctly but commands don't execute

**Solutions**:
1. Check file permissions on `BsTool.exe`
2. Verify temp directory is writable
3. Check subprocess call in `bstool_command_service.py`
4. Increase timeout if commands are slow

---

## Next Steps

After successful testing:
1. ✅ Update `TODO.md` - Mark task complete
2. ✅ Update `CHANGELOG.md` - Document bundling feature
3. ✅ Update `README.md` - Add bundling info to installation section
4. ✅ Create workflow log in `logs/`
5. ✅ Update `project_memory.json` with learnings
6. ✅ Commit changes to git
7. ✅ Create release build

---

**End of Test Documentation**
