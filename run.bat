@echo off
setlocal
cd /d "%~dp0"

echo ========================================
echo PedalTurn - Run
echo ========================================
echo.

rem System Python must be compatible with PySide6 6.x.
python -c "import sys; raise SystemExit(0 if sys.version_info >= (3,10) else 1)" >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python 3.10 or newer is required.
    python --version
    echo.
    pause
    exit /b 1
)

rem Create the environment when it does not exist.
if not exist "venv\Scripts\python.exe" (
    echo Creating virtual environment...
    python -m venv venv
    if errorlevel 1 goto :venv_error
)

rem Recreate an old or incompatible environment.
"venv\Scripts\python.exe" -c "import sys; raise SystemExit(0 if sys.version_info >= (3,10) else 1)" >nul 2>&1
if errorlevel 1 (
    echo Existing virtual environment uses an incompatible Python version.
    echo Recreating virtual environment...
    rmdir /s /q "venv"
    python -m venv venv
    if errorlevel 1 goto :venv_error
)

call "venv\Scripts\activate.bat"

rem Install dependencies only when the environment is missing them.
python -c "import PySide6, pymupdf, pygame" >nul 2>&1
if errorlevel 1 (
    echo Required dependencies not found.
    echo Installing requirements.txt...
    python -m pip install --upgrade pip
    if errorlevel 1 goto :deps_error
    python -m pip install -r requirements.txt
    if errorlevel 1 goto :deps_error
)

rem Verify imports before launching.
python -c "import PySide6, pymupdf, pygame" >nul 2>&1
if errorlevel 1 goto :deps_error

echo Virtual environment ready.
echo Starting PedalTurn...
echo.

python "PageChangerPiano.py"
if errorlevel 1 (
    echo.
    echo [ERROR] The application exited with an error.
    pause
    exit /b 1
)

endlocal
exit /b 0

:venv_error
echo.
echo [ERROR] Could not create the virtual environment.
pause
exit /b 1

:deps_error
echo.
echo [ERROR] Dependencies could not be installed.
echo Run build.bat to rebuild the environment.
pause
exit /b 1
