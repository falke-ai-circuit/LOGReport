@echo off
REM Create and setup virtual environment for Nuitka build
REM This ensures clean, isolated build environment

echo ====================================
echo Nuitka Build Environment Setup
echo ====================================
echo.

REM Check if venv already exists
if exist ".venv-build" (
    echo Virtual environment .venv-build already exists.
    echo To recreate, delete .venv-build folder first.
    echo.
    choice /C YN /M "Use existing environment? (Y=Yes, N=Delete and recreate)"
    if errorlevel 2 (
        echo Deleting existing environment...
        rmdir /s /q .venv-build
    ) else (
        echo Using existing environment.
        goto :activate
    )
)

echo Creating virtual environment...
python -m venv .venv-build
if errorlevel 1 (
    echo ERROR: Failed to create virtual environment
    echo Make sure Python is installed correctly
    exit /b 1
)

:activate
echo.
echo Activating virtual environment...
call .venv-build\Scripts\activate.bat

echo.
echo Installing dependencies...
python -m pip install --upgrade pip
pip install -r requirements.txt
pip install nuitka

echo.
echo ====================================
echo Environment ready!
echo ====================================
echo.
echo To build:
echo   1. Activate: .venv-build\Scripts\activate.bat
echo   2. Build: .\build_nuitka.bat
echo.
echo Or run: build_nuitka_venv.bat (does both automatically)
echo.

pause
