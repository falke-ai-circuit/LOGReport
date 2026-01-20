@echo off
REM Download UPX compression tool for Nuitka builds
REM UPX reduces executable size by 50-70% with maximum compression

echo ====================================
echo UPX Download Helper
echo ====================================
echo.
echo UPX (Ultimate Packer for eXecutables) reduces executable size
echo by 50-70% using maximum compression settings.
echo.

REM Check if UPX already exists
if exist "upx\upx.exe" (
    echo UPX is already installed in upx\upx.exe
    upx\upx.exe --version
    echo.
    echo To re-download, delete the upx folder and run this script again.
    pause
    exit /b 0
)

REM Check if system UPX exists
where upx >nul 2>&1
if not errorlevel 1 (
    echo System UPX found:
    upx --version
    echo.
    echo You can use system UPX, or download to upx\ folder for bundled use.
    echo.
)

echo Manual download required:
echo.
echo 1. Visit: https://github.com/upx/upx/releases
echo 2. Download the latest Windows 64-bit release (upx-X.XX-win64.zip)
echo 3. Extract the ZIP file
echo 4. Copy upx.exe to: %CD%\upx\upx.exe
echo.
echo Alternative - Quick download (if you have curl or PowerShell):
echo.
echo   Using PowerShell (recommended):
echo   powershell -Command "Invoke-WebRequest -Uri 'https://github.com/upx/upx/releases/download/v4.2.1/upx-4.2.1-win64.zip' -OutFile 'upx.zip'"
echo   powershell -Command "Expand-Archive -Path 'upx.zip' -DestinationPath '.' -Force"
echo   mkdir upx
echo   move upx-4.2.1-win64\upx.exe upx\upx.exe
echo   rmdir /s /q upx-4.2.1-win64
echo   del upx.zip
echo.
echo Would you like to auto-download UPX 4.2.1 now? (Y/N)
set /p DOWNLOAD="Enter choice: "

if /i "%DOWNLOAD%"=="Y" (
    echo.
    echo Downloading UPX 4.2.1...
    powershell -Command "try { Invoke-WebRequest -Uri 'https://github.com/upx/upx/releases/download/v4.2.1/upx-4.2.1-win64.zip' -OutFile 'upx.zip' -ErrorAction Stop; Write-Host 'Download successful!' } catch { Write-Host 'Download failed. Please download manually.'; exit 1 }"
    
    if errorlevel 1 (
        echo Download failed. Please download manually from GitHub.
        pause
        exit /b 1
    )
    
    echo Extracting...
    powershell -Command "Expand-Archive -Path 'upx.zip' -DestinationPath '.' -Force"
    
    if not exist "upx" mkdir upx
    move upx-4.2.1-win64\upx.exe upx\upx.exe
    
    echo Cleaning up...
    rmdir /s /q upx-4.2.1-win64
    del upx.zip
    
    echo.
    echo ====================================
    echo UPX installed successfully!
    echo ====================================
    echo.
    echo Location: %CD%\upx\upx.exe
    upx\upx.exe --version
    echo.
    echo You can now run build_nuitka.bat with UPX compression.
) else (
    echo.
    echo Download cancelled. Build will work without UPX, but executable will be larger.
)

echo.
pause
