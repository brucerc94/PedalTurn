@echo off
setlocal
cd /d "%~dp0"

echo ========================================
echo PDF Page Changer Piano - Run
echo ========================================
echo.

rem System Python must be compatible with PySide6 6.x.
python -c "import sys; raise SystemExit(0 if sys.version_info >= (3,10) else 1)" >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Se necesita Python 3.10 o superior.
    python --version
    echo.
    pause
    exit /b 1
)

rem Create the environment when it does not exist.
if not exist "venv\Scripts\python.exe" (
    echo Creando entorno virtual...
    python -m venv venv
    if errorlevel 1 goto :venv_error
)

rem Recreate an old/incompatible environment.
"venv\Scripts\python.exe" -c "import sys; raise SystemExit(0 if sys.version_info >= (3,10) else 1)" >nul 2>&1
if errorlevel 1 (
    echo El entorno virtual existente usa una version incompatible de Python.
    echo Recreando venv...
    rmdir /s /q "venv"
    python -m venv venv
    if errorlevel 1 goto :venv_error
)

call "venv\Scripts\activate.bat"

rem Install dependencies only when the environment is missing them.
python -c "import PySide6, fitz, pygame" >nul 2>&1
if errorlevel 1 (
    echo Dependencias nuevas no encontradas.
    echo Instalando requirements.txt...
    python -m pip install --upgrade pip
    if errorlevel 1 goto :deps_error
    python -m pip install -r requirements.txt
    if errorlevel 1 goto :deps_error
)

rem Verify imports before launching.
python -c "import PySide6, fitz, pygame" >nul 2>&1
if errorlevel 1 goto :deps_error

echo Entorno virtual listo.
echo Iniciando PDF Page Changer Piano...
echo.

python "PageChangerPiano.py"
if errorlevel 1 (
    echo.
    echo [ERROR] La aplicacion termino con un error.
    pause
    exit /b 1
)

endlocal
exit /b 0

:venv_error
echo.
echo [ERROR] No se pudo crear el entorno virtual.
pause
exit /b 1

:deps_error
echo.
echo [ERROR] No se pudieron instalar las dependencias.
echo Ejecuta build.bat para reconstruir el entorno completo.
pause
exit /b 1
