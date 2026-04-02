@echo off
setlocal

echo [HierarchicalDatacubes] Installing using Python 3.10+...

REM Check if Python Launcher is installed
where py >nul 2>&1 || (
    echo ❌ Python launcher not found. Please install Python 3.10 or higher.
    exit /b 1
)

REM Check if Python 3.10 or higher is available
py -3.10 --version >nul 2>&1 || (
    echo ❌ Python 3.10 not detected. Please install it from:
    echo https://www.python.org/downloads/
    exit /b 1
)

REM Create virtual environment
echo Creating virtual environment...
py -3.10 -m venv .venv

REM Install dependencies directly inside the venv
echo Installing dependencies...
call .venv\Scripts\activate.bat && (
    python -m ensurepip --upgrade
    python -m pip install --upgrade pip
    python -m pip install -e .
)

echo.
echo ✅ HierarchicalDatacubes is ready to use!
echo To run it:
echo     .venv\Scripts\activate
echo     datacube-gui     for the PyQt6 Interface
echo     datacube-cli     for the CLI Benchmarking Tool
echo.
pause
