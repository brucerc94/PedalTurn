@echo off
setlocal
cd /d "%~dp0"

echo ========================================
echo PedalTurn - Build
echo ========================================
echo.

python -c "import sys; raise SystemExit(0 if sys.version_info >= (3,10) else 1)" >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python 3.10 or newer is required.
    python --version
    exit /b 1
)

if exist "venv\Scripts\python.exe" (
    "venv\Scripts\python.exe" -c "import sys; raise SystemExit(0 if sys.version_info >= (3,10) else 1)" >nul 2>&1
    if errorlevel 1 (
        echo Removing incompatible virtual environment...
        rmdir /s /q "venv"
    )
)

if not exist "venv\Scripts\python.exe" (
    echo Creating virtual environment...
    python -m venv venv
    if errorlevel 1 goto :error
)

call "venv\Scripts\activate.bat"

echo Upgrading pip...
python -m pip install --upgrade pip
if errorlevel 1 goto :error

echo Installing dependencies...
python -m pip install -r requirements.txt
if errorlevel 1 goto :error

echo Building executable...
python -m PyInstaller --clean --noconfirm --onefile --windowed --name PedalTurn --icon icono.ico --collect-all PySide6.QtMultimedia --hidden-import PySide6.QtMultimedia --hidden-import PySide6.QtMultimediaWidgets PageChangerPiano.py
if errorlevel 1 goto :error

echo.
echo Build completed successfully.
echo Executable: dist\PedalTurn.exe
endlocal
exit /b 0

:error
echo.
echo [ERROR] Build failed.
endlocal
exit /b 1
