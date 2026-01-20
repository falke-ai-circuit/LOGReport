# Script to check DLL dependencies of the built executable
# Run this on Windows Server 2012 to identify missing dependencies

param(
    [string]$ExePath = "dist\LOGReporter.exe"
)

Write-Host "Checking dependencies for: $ExePath" -ForegroundColor Cyan

# Check if the executable exists
if (-not (Test-Path $ExePath)) {
    Write-Host "ERROR: Executable not found at $ExePath" -ForegroundColor Red
    exit 1
}

Write-Host "`nExecutable size: $((Get-Item $ExePath).Length / 1MB) MB" -ForegroundColor Green

# Try to run the executable with error capture
Write-Host "`nAttempting to run executable..." -ForegroundColor Cyan
try {
    $process = Start-Process -FilePath $ExePath -PassThru -Wait -NoNewWindow -ErrorAction Stop
    Write-Host "Process exited with code: $($process.ExitCode)" -ForegroundColor $(if ($process.ExitCode -eq 0) { "Green" } else { "Red" })
} catch {
    Write-Host "ERROR: Failed to start process: $_" -ForegroundColor Red
}

# Check for common missing DLLs
Write-Host "`nChecking for common runtime DLLs on system..." -ForegroundColor Cyan
$requiredDLLs = @(
    "vcruntime140.dll",
    "vcruntime140_1.dll",
    "msvcp140.dll",
    "msvcp140_1.dll",
    "msvcp140_2.dll",
    "concrt140.dll",
    "ucrtbase.dll",
    "api-ms-win-crt-runtime-l1-1-0.dll"
)

foreach ($dll in $requiredDLLs) {
    $found = $false
    $searchPaths = @(
        "C:\Windows\System32",
        "C:\Windows\SysWOW64",
        "$env:ProgramFiles\Microsoft Visual Studio",
        "$env:ProgramFiles(x86)\Microsoft Visual Studio"
    )
    
    foreach ($path in $searchPaths) {
        if (Test-Path "$path\$dll") {
            Write-Host "  [OK] $dll found in $path" -ForegroundColor Green
            $found = $true
            break
        }
    }
    
    if (-not $found) {
        Write-Host "  [MISSING] $dll not found on system" -ForegroundColor Red
    }
}

# Check Windows version
Write-Host "`nWindows Version:" -ForegroundColor Cyan
$osInfo = Get-WmiObject -Class Win32_OperatingSystem
Write-Host "  OS: $($osInfo.Caption)" -ForegroundColor White
Write-Host "  Version: $($osInfo.Version)" -ForegroundColor White
Write-Host "  Build: $($osInfo.BuildNumber)" -ForegroundColor White

# Check if running on Windows Server 2012
if ($osInfo.Caption -like "*Server 2012*") {
    Write-Host "`n*** Running on Windows Server 2012 ***" -ForegroundColor Yellow
    Write-Host "To fix Qt platform plugin issues, install:" -ForegroundColor Yellow
    Write-Host "  1. Visual C++ Redistributable 2015-2022 (x64)" -ForegroundColor Yellow
    Write-Host "  2. Download from: https://aka.ms/vs/17/release/vc_redist.x64.exe" -ForegroundColor Yellow
}

Write-Host "`nDone!" -ForegroundColor Green
