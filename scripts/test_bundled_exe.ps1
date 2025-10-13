# Test Script for Bundled LOGReporter with BsTool.exe Detection
# This script tests the behavior when BsTool.exe cannot be found

Write-Host "==================================" -ForegroundColor Cyan
Write-Host "BsTool Bundling Test Script" -ForegroundColor Cyan
Write-Host "==================================" -ForegroundColor Cyan
Write-Host ""

# Configuration
$ProjectRoot = "D:\_APP\LOGReport"
$DistDir = Join-Path $ProjectRoot "dist"
$TestDir = Join-Path $ProjectRoot "test_bundle"
$BackupDir = Join-Path $ProjectRoot "test_bundle\backup"

Write-Host "[1] Pre-test Checks" -ForegroundColor Yellow
Write-Host "-----------------------------------"

# Check if BsTool.exe exists
$BsToolSource = Join-Path $ProjectRoot "BsTool.exe"
if (-not (Test-Path $BsToolSource)) {
    Write-Host "[ERROR] BsTool.exe not found in project root: $BsToolSource" -ForegroundColor Red
    Write-Host "Please ensure BsTool.exe exists before running this test." -ForegroundColor Red
    exit 1
}
Write-Host "[OK] BsTool.exe found in project root" -ForegroundColor Green

# Check if spec file exists
$SpecFile = Join-Path $ProjectRoot "LOGReporter_PyQt5.spec"
if (-not (Test-Path $SpecFile)) {
    Write-Host "[ERROR] LOGReporter_PyQt5.spec not found: $SpecFile" -ForegroundColor Red
    exit 1
}
Write-Host "[OK] Spec file found" -ForegroundColor Green

Write-Host ""
Write-Host "[2] Building Executable" -ForegroundColor Yellow
Write-Host "-----------------------------------"

# Build the executable
Write-Host "Running PyInstaller..." -ForegroundColor Cyan
Set-Location $ProjectRoot
pyinstaller --clean LOGReporter_PyQt5.spec

if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERROR] PyInstaller build failed with exit code $LASTEXITCODE" -ForegroundColor Red
    exit 1
}
Write-Host "[OK] Build completed successfully" -ForegroundColor Green

Write-Host ""
Write-Host "[3] Preparing Test Environment" -ForegroundColor Yellow
Write-Host "-----------------------------------"

# Clean and create test directory
if (Test-Path $TestDir) {
    Write-Host "Removing existing test directory..." -ForegroundColor Cyan
    Remove-Item -Path $TestDir -Recurse -Force
}
New-Item -Path $TestDir -ItemType Directory | Out-Null
New-Item -Path $BackupDir -ItemType Directory | Out-Null

# Copy built executable to test directory
$ExePath = Join-Path $DistDir "LOGReporter.exe"
if (-not (Test-Path $ExePath)) {
    Write-Host "[ERROR] Built executable not found: $ExePath" -ForegroundColor Red
    exit 1
}

Write-Host "Copying executable to test directory..." -ForegroundColor Cyan
Copy-Item -Path $ExePath -Destination $TestDir

# Check if BsTool.exe was bundled
$BundledBsTool = Join-Path $TestDir "BsTool.exe"
if (Test-Path $BundledBsTool) {
    Write-Host "[OK] BsTool.exe was bundled with executable" -ForegroundColor Green
} else {
    Write-Host "[WARNING] BsTool.exe not found in dist directory" -ForegroundColor Yellow
    Write-Host "Checking if it's in _internal folder (onedir mode)..." -ForegroundColor Cyan
    
    $InternalBsTool = Join-Path $TestDir "_internal\BsTool.exe"
    if (Test-Path $InternalBsTool) {
        Write-Host "[OK] BsTool.exe found in _internal folder" -ForegroundColor Green
        $BundledBsTool = $InternalBsTool
    } else {
        Write-Host "[ERROR] BsTool.exe not found in bundled output" -ForegroundColor Red
        Write-Host "Check the .spec file 'binaries' section" -ForegroundColor Red
        exit 1
    }
}

Write-Host ""
Write-Host "[4] Test Scenario 1: Normal Operation" -ForegroundColor Yellow
Write-Host "-----------------------------------"
Write-Host "Testing with BsTool.exe present..." -ForegroundColor Cyan
Write-Host ""
Write-Host "INSTRUCTIONS:" -ForegroundColor Magenta
Write-Host "1. The application will start" -ForegroundColor White
Write-Host "2. Go to BsTool tab" -ForegroundColor White
Write-Host "3. Check if 'BsTool Execution Path' field is auto-populated" -ForegroundColor White
Write-Host "4. Expected: Path should show the bundled BsTool.exe location" -ForegroundColor White
Write-Host "5. Close the application to continue to next test" -ForegroundColor White
Write-Host ""
Read-Host "Press Enter to start Test 1"

Set-Location $TestDir
Start-Process -FilePath ".\LOGReporter.exe" -Wait

Write-Host "[OK] Test 1 completed" -ForegroundColor Green

Write-Host ""
Write-Host "[5] Test Scenario 2: BsTool.exe Renamed (Simulating Missing File)" -ForegroundColor Yellow
Write-Host "-----------------------------------"

# Rename BsTool.exe to simulate it being missing
if (Test-Path $BundledBsTool) {
    $RenamedPath = $BundledBsTool -replace "BsTool\.exe", "BsTool_RENAMED.exe"
    Write-Host "Renaming BsTool.exe to BsTool_RENAMED.exe..." -ForegroundColor Cyan
    Move-Item -Path $BundledBsTool -Destination $BackupDir -Force
    Write-Host "[OK] BsTool.exe moved to backup directory" -ForegroundColor Green
} else {
    Write-Host "[ERROR] BsTool.exe not found for renaming" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "INSTRUCTIONS:" -ForegroundColor Magenta
Write-Host "1. The application will start WITHOUT BsTool.exe present" -ForegroundColor White
Write-Host "2. Go to BsTool tab" -ForegroundColor White
Write-Host "3. Check if 'BsTool Execution Path' field shows error or is empty" -ForegroundColor White
Write-Host "4. Expected: Field should be empty OR show warning message" -ForegroundColor White
Write-Host "5. Try to execute a BsTool command (should fail gracefully)" -ForegroundColor White
Write-Host "6. Check application logs for error messages" -ForegroundColor White
Write-Host "7. Close the application when done testing" -ForegroundColor White
Write-Host ""
Read-Host "Press Enter to start Test 2 (BsTool.exe missing)"

Set-Location $TestDir
Start-Process -FilePath ".\LOGReporter.exe" -Wait

Write-Host "[OK] Test 2 completed" -ForegroundColor Green

Write-Host ""
Write-Host "[6] Test Scenario 3: Manual Path Override" -ForegroundColor Yellow
Write-Host "-----------------------------------"

# Restore BsTool.exe to a different location
$AlternateLocation = Join-Path $TestDir "alternate_tools"
New-Item -Path $AlternateLocation -ItemType Directory -Force | Out-Null
Copy-Item -Path (Join-Path $BackupDir "BsTool.exe") -Destination $AlternateLocation -Force

Write-Host "[OK] BsTool.exe placed in alternate location: $AlternateLocation" -ForegroundColor Green
Write-Host ""
Write-Host "INSTRUCTIONS:" -ForegroundColor Magenta
Write-Host "1. The application will start (still no BsTool.exe in default location)" -ForegroundColor White
Write-Host "2. Go to BsTool tab" -ForegroundColor White
Write-Host "3. Manually set the path to: $AlternateLocation\BsTool.exe" -ForegroundColor White
Write-Host "4. Try to execute a BsTool command" -ForegroundColor White
Write-Host "5. Expected: Command should work with manually specified path" -ForegroundColor White
Write-Host "6. Close the application when done testing" -ForegroundColor White
Write-Host ""
Read-Host "Press Enter to start Test 3 (Manual path override)"

Set-Location $TestDir
Start-Process -FilePath ".\LOGReporter.exe" -Wait

Write-Host "[OK] Test 3 completed" -ForegroundColor Green

Write-Host ""
Write-Host "[7] Cleanup and Summary" -ForegroundColor Yellow
Write-Host "-----------------------------------"

Write-Host ""
Write-Host "Test Summary:" -ForegroundColor Cyan
Write-Host "  Test 1: Normal operation with bundled BsTool.exe" -ForegroundColor White
Write-Host "  Test 2: Operation without BsTool.exe (error handling)" -ForegroundColor White
Write-Host "  Test 3: Manual path override functionality" -ForegroundColor White
Write-Host ""

$Cleanup = Read-Host "Delete test directory? (y/n)"
if ($Cleanup -eq 'y' -or $Cleanup -eq 'Y') {
    Write-Host "Cleaning up test directory..." -ForegroundColor Cyan
    Set-Location $ProjectRoot
    Remove-Item -Path $TestDir -Recurse -Force
    Write-Host "[OK] Test directory removed" -ForegroundColor Green
} else {
    Write-Host "[INFO] Test directory preserved at: $TestDir" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "==================================" -ForegroundColor Cyan
Write-Host "Testing Complete!" -ForegroundColor Green
Write-Host "==================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Please review the following:" -ForegroundColor Yellow
Write-Host "1. Did the BsTool path auto-populate in Test 1?" -ForegroundColor White
Write-Host "2. Did the application handle missing BsTool.exe gracefully in Test 2?" -ForegroundColor White
Write-Host "3. Did manual path override work in Test 3?" -ForegroundColor White
Write-Host "4. Check debug.log and system.log for any errors" -ForegroundColor White
Write-Host ""
