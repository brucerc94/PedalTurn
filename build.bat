@echo off
setlocal
cd /d "%~dp0"

echo ========================================
echo PDF Page Changer Piano - Build
echo ========================================
echo.

python -c "import sys; raise SystemExit(0 if sys.version_info >= (3,10) else 1)" >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Se necesita Python 3.10 o superior.
    python --version
    exit /b 1
)

if exist "venv\Scripts\python.exe" (
    "venv\Scripts\python.exe" -c "import sys; raise SystemExit(0 if sys.version_info >= (3,10) else 1)" >nul 2>&1
    if errorlevel 1 (
        echo Eliminando venv antiguo...
        rmdir /s /q "venv"
    )
)

if not exist "venv\Scripts\python.exe" (
    echo Creando entorno virtual...
    python -m venv venv
    if errorlevel 1 goto :error
)

call "venv\Scripts\activate.bat"

echo Actualizando pip...
python -m pip install --upgrade pip
if errorlevel 1 goto :error

echo Instalando dependencias...
python -m pip install -r requirements.txt
if errorlevel 1 goto :error

echo Construyendo ejecutable...
python -m PyInstaller --clean --noconfirm --onefile --windowed --name PDFPageChangerPiano --icon icono.ico --collect-all PySide6.QtMultimedia --hidden-import PySide6.QtMultimedia --hidden-import PySide6.QtMultimediaWidgets PageChangerPiano.py
if errorlevel 1 goto :error

echo.
echo Build completed successfully.
echo Executable: dist\PDFPageChangerPiano.exe
endlocal
exit /b 0

:error
echo.
echo [ERROR] El build fallo.
endlocal
exit /b 1
