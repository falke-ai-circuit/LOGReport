# Quick BsTool Bundling Test
# Run this for a fast manual test

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "  Quick BsTool Bundling Test" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

$ProjectRoot = "D:\_APP\LOGReport"
cd $ProjectRoot

# Step 1: Build
Write-Host "[1/5] Building executable..." -ForegroundColor Yellow
pyinstaller --clean LOGReporter_PyQt5.spec
if ($LASTEXITCODE -ne 0) { 
    Write-Host "Build failed!" -ForegroundColor Red
    exit 1 
}

# Step 2: Check bundling
Write-Host "`n[2/5] Checking if BsTool.exe was bundled..." -ForegroundColor Yellow
$DistDir = "dist\LOGReporter"
if (Test-Path "$DistDir\BsTool.exe") {
    Write-Host "✅ BsTool.exe found in: $DistDir\BsTool.exe" -ForegroundColor Green
} elseif (Test-Path "$DistDir\_internal\BsTool.exe") {
    Write-Host "✅ BsTool.exe found in: $DistDir\_internal\BsTool.exe" -ForegroundColor Green
    $DistDir = "$DistDir\_internal"
} else {
    Write-Host "❌ BsTool.exe NOT found in dist directory!" -ForegroundColor Red
    Write-Host "Check LOGReporter_PyQt5.spec binaries section" -ForegroundColor Yellow
    exit 1
}

# Step 3: Test normal operation
Write-Host "`n[3/5] TEST 1: Normal Operation" -ForegroundColor Yellow
Write-Host "------------------------------------" -ForegroundColor Yellow
Write-Host "Action: Launch LOGReporter.exe with BsTool.exe present" -ForegroundColor Cyan
Write-Host "`nInstructions:" -ForegroundColor Magenta
Write-Host "  1. Go to BsTool tab" -ForegroundColor White
Write-Host "  2. Check if path field is auto-filled" -ForegroundColor White
Write-Host "  3. Note the path shown" -ForegroundColor White
Write-Host "  4. Close the app`n" -ForegroundColor White

Read-Host "Press Enter to start Test 1"
Start-Process -FilePath "$DistDir\..\LOGReporter.exe" -WorkingDirectory "$DistDir\.."

Write-Host "`nWaiting for you to close the application..." -ForegroundColor Yellow
Read-Host "Press Enter when done with Test 1"

# Step 4: Rename BsTool and test
Write-Host "`n[4/5] TEST 2: Missing BsTool.exe" -ForegroundColor Yellow
Write-Host "------------------------------------" -ForegroundColor Yellow
Write-Host "Action: Rename BsTool.exe to simulate missing file" -ForegroundColor Cyan

$BsToolPath = "$DistDir\BsTool.exe"
$BackupPath = "$DistDir\BsTool_HIDDEN.exe"

if (Test-Path $BsToolPath) {
    Move-Item $BsToolPath $BackupPath -Force
    Write-Host "✅ Renamed BsTool.exe → BsTool_HIDDEN.exe" -ForegroundColor Green
}

Write-Host "`nInstructions:" -ForegroundColor Magenta
Write-Host "  1. Go to BsTool tab" -ForegroundColor White
Write-Host "  2. Path field should be EMPTY" -ForegroundColor White
Write-Host "  3. Check logs for warnings" -ForegroundColor White
Write-Host "  4. Try manually entering path: $BackupPath" -ForegroundColor White
Write-Host "  5. Close the app`n" -ForegroundColor White

Read-Host "Press Enter to start Test 2"
Start-Process -FilePath "$DistDir\..\LOGReporter.exe" -WorkingDirectory "$DistDir\.."

Write-Host "`nWaiting for you to close the application..." -ForegroundColor Yellow
Read-Host "Press Enter when done with Test 2"

# Step 5: Restore and cleanup
Write-Host "`n[5/5] Cleanup" -ForegroundColor Yellow
Write-Host "------------------------------------" -ForegroundColor Yellow

if (Test-Path $BackupPath) {
    Move-Item $BackupPath $BsToolPath -Force
    Write-Host "✅ Restored BsTool.exe" -ForegroundColor Green
}

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "  Test Complete!" -ForegroundColor Green
Write-Host "========================================`n" -ForegroundColor Cyan

Write-Host "Summary Questions:" -ForegroundColor Yellow
Write-Host "  1. Did path auto-populate in Test 1?" -ForegroundColor White
Write-Host "  2. Was path empty in Test 2?" -ForegroundColor White
Write-Host "  3. Did manual path entry work?" -ForegroundColor White
Write-Host "  4. Check debug.log for any errors`n" -ForegroundColor White

# Open logs
$OpenLogs = Read-Host "Open debug.log? (y/n)"
if ($OpenLogs -eq 'y') {
    if (Test-Path "debug.log") {
        notepad debug.log
    } else {
        Write-Host "debug.log not found in current directory" -ForegroundColor Yellow
    }
}

Write-Host "`nDone!`n" -ForegroundColor Green
