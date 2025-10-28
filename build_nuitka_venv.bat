@echo off
REM Build LOGReporter using Nuitka in virtual environment
REM Ensures clean, isolated build

echo ====================================
echo LOGReport Nuitka Build (venv)
echo ====================================
echo.

REM Check if venv exists
if not exist ".venv-build" (
    echo Virtual environment not found. Creating...
    call setup_build_env.bat
    if errorlevel 1 (
        echo ERROR: Failed to setup environment
        exit /b 1
    )
)

REM Activate venv
echo Activating virtual environment...
call .venv-build\Scripts\activate.bat

REM Verify Nuitka is installed
python -m nuitka --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Nuitka not found in virtual environment
    echo Run: setup_build_env.bat
    exit /b 1
)

REM Check if BsTool.exe exists
if not exist "BsTool.exe" (
    echo ERROR: BsTool.exe not found in project root
    echo Please place BsTool.exe in the project directory
    exit /b 1
)

REM Clean previous build
echo Cleaning previous build artifacts...
if exist "main.build" rmdir /s /q main.build
if exist "main.dist" rmdir /s /q main.dist
if exist "main.onefile-build" rmdir /s /q main.onefile-build
if exist "dist\LOGReporter.exe" del /f /q dist\LOGReporter.exe

REM Create dist directory
if not exist "dist" mkdir dist

echo.
echo Starting Nuitka compilation...
echo This may take 10-20 minutes on first run...
echo.

REM Run Nuitka with optimizations
python -m nuitka ^
    --standalone ^
    --onefile ^
    --windows-console-mode=disable ^
    --enable-plugin=pyqt5 ^
    --include-data-dir=assets=assets ^
    --include-data-file=BsTool.exe=BsTool.exe ^
    --include-data-file=src/nodes.json=src/nodes.json ^
    --include-data-file=version_info.txt=version_info.txt ^
    --include-package=reportlab ^
    --include-package=docx ^
    --include-package=PyQt5 ^
    --include-package=PIL ^
    --follow-imports ^
    --assume-yes-for-downloads ^
    --output-dir=dist ^
    --output-filename=LOGReporter.exe ^
    --company-name="LOGReport Project" ^
    --product-name="LOGReporter" ^
    --file-version=1.0.0.0 ^
    --product-version=1.0.0 ^
    --file-description="Industrial Log Report Generator" ^
    --onefile-tempdir-spec={TEMP}\LOGReporter ^
    --windows-company-name="LOGReport Project" ^
    --lto=yes ^
    src\main.py

if errorlevel 1 (
    echo.
    echo ERROR: Nuitka compilation failed
    echo Check the error messages above
    exit /b 1
)

REM Apply UPX compression if available
echo.
echo Applying UPX compression...
if exist "upx\upx.exe" (
    echo Using bundled UPX from upx\upx.exe
    upx\upx.exe --best --lzma --ultra-brute dist\LOGReporter.exe
    if errorlevel 1 (
        echo WARNING: UPX compression failed, but executable is still usable
    ) else (
        echo UPX compression applied successfully!
    )
) else (
    where upx >nul 2>&1
    if errorlevel 1 (
        echo WARNING: UPX not found - skipping compression
        echo Download UPX from: https://github.com/upx/upx/releases
        echo Place upx.exe in the 'upx' folder or add to PATH
        echo Executable is still fully functional without compression
    ) else (
        echo Using system UPX
        upx --best --lzma --ultra-brute dist\LOGReporter.exe
        if errorlevel 1 (
            echo WARNING: UPX compression failed, but executable is still usable
        ) else (
            echo UPX compression applied successfully!
        )
    )
)

echo.
echo ====================================
echo Build completed successfully!
echo ====================================
echo.
echo Executable location: dist\LOGReporter.exe
echo.
echo File size:
dir dist\LOGReporter.exe | findstr LOGReporter.exe
echo.
echo Next steps:
echo 1. Test the executable: dist\LOGReporter.exe
echo 2. Verify BsTool integration works
echo 3. Test report generation functionality
echo.

pause
