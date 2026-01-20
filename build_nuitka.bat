@echo off
REM LOGReport Nuitka Build Script
REM Creates a portable standalone executable using Nuitka compiler

echo ====================================
echo LOGReport Nuitka Build Script
echo ====================================
echo.

REM Check if Nuitka is installed
python -m nuitka --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Nuitka is not installed
    echo Install with: pip install nuitka
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

REM Create dist directory if it doesn't exist
if not exist "dist" mkdir dist

echo.
echo Starting Nuitka compilation...
echo This may take 10-20 minutes on first run...
echo.

REM Run Nuitka with optimizations and UPX compression
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
    --include-package=telnetlib ^
    --include-module=reportlab.pdfgen ^
    --include-module=reportlab.lib.pagesizes ^
    --include-module=reportlab.lib.styles ^
    --include-module=reportlab.platypus ^
    --include-module=docx.shared ^
    --include-module=docx.enum.text ^
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

REM Move the executable to dist folder if not already there
if exist "main.exe" (
    move /y main.exe dist\LOGReporter.exe
)

REM Apply UPX maximum compression if UPX is available
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
echo Next steps:
echo 1. Test the executable: dist\LOGReporter.exe
echo 2. Verify BsTool integration works
echo 3. Test report generation functionality
echo.

pause
