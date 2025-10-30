@echo off
REM Test script for Nuitka bundled executable
REM Run this AFTER building with build_nuitka.bat

echo ================================================================================
echo Testing Nuitka Bundled Executable - BsTool Path Resolution
echo ================================================================================
echo.

if not exist "dist\LOGReporter.exe" (
    echo ERROR: dist\LOGReporter.exe not found!
    echo Please run build_nuitka.bat first.
    pause
    exit /b 1
)

echo Found: dist\LOGReporter.exe
echo.

echo Starting LOGReporter.exe...
echo Check debug.log for detailed path resolution diagnostics.
echo.

REM Start the application and wait a few seconds
start "" "dist\LOGReporter.exe"
timeout /t 5 /nobreak >nul

echo.
echo Application started. 
echo.
echo IMPORTANT: Check the following for diagnostics:
echo   1. debug.log - Look for "BsTool" or "bstool_path_resolver" entries
echo   2. Watch for any error dialogs in the application
echo   3. Try using BsTool functionality and check if it hangs
echo.
echo If you see errors, check these paths manually:
echo   - %%TEMP%%\LOGReporter\BsTool.exe
echo   - Where %%TEMP%% is typically: C:\Users\[YourUsername]\AppData\Local\Temp
echo.

REM Wait for user input before checking log
pause

echo.
echo ================================================================================
echo Checking debug.log for BsTool path resolution...
echo ================================================================================
echo.

if exist "debug.log" (
    echo Last 50 lines containing "bstool" or "BsTool":
    findstr /i "bstool" debug.log | more
) else (
    echo debug.log not found yet. Application may not have initialized logging.
)

echo.
echo ================================================================================
pause
