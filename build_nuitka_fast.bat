@echo off
REM LOGReport Nuitka Fast Build Script (Development Mode)
REM Creates a faster build without full optimizations for testing

echo ====================================
echo LOGReport Nuitka Fast Build
echo (Development/Testing Mode)
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

REM Create dist directory if it doesn't exist
if not exist "dist" mkdir dist

echo.
echo Starting Nuitka fast compilation...
echo This will take 3-5 minutes...
echo.

REM Run Nuitka with minimal optimizations for faster builds
python -m nuitka ^
    --standalone ^
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
    src\main.py

if errorlevel 1 (
    echo.
    echo ERROR: Nuitka compilation failed
    echo Check the error messages above
    exit /b 1
)

echo.
echo ====================================
echo Fast build completed!
echo ====================================
echo.
echo Executable location: dist\main.dist\main.exe
echo Note: This is a directory-based build for faster compilation
echo.
echo To run: dist\main.dist\main.exe
echo.

pause
