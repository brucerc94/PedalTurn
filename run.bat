@echo off
setlocal

cd /d "%~dp0"

echo ========================================
echo PDF Page Changer Piano - Run
echo ========================================
echo.

if not exist "venv\Scripts\python.exe" (
    echo [ERROR] No se encontro el entorno virtual "venv".
    echo Ejecuta primero build.bat o crea el entorno virtual manualmente.
    echo.
    pause
    exit /b 1
)

echo Activando entorno virtual...
call "venv\Scripts\activate.bat"

echo Iniciando PDF Page Changer Piano...
echo.

python "PageChangerPiano.py"

if errorlevel 1 (
    echo.
    echo [ERROR] La aplicacion termino con un error.
    pause
)

endlocal
