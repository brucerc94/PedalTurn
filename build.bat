@echo off
setlocal
cd /d "%~dp0"

echo ========================================
echo PDF Page Changer Piano - Build
echo ========================================
echo.

if not exist "venv\Scripts\python.exe" (
    echo Creating virtual environment...
    python -m venv venv
    if errorlevel 1 goto :error
)

echo Installing dependencies...
"venv\Scripts\python.exe" -m pip install --upgrade pip
if errorlevel 1 goto :error
"venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 goto :error

echo Building executable...
"venv\Scripts\python.exe" -m PyInstaller --clean --noconfirm --onefile --windowed --name PDFPageChangerPiano --icon icono.ico --collect-all PySide6.QtMultimedia --hidden-import PySide6.QtMultimedia --hidden-import PySide6.QtMultimediaWidgets PageChangerPiano.py
if errorlevel 1 goto :error

echo.
echo Build completed successfully.
echo Executable: dist\PDFPageChangerPiano.exe
goto :end

:error
echo.
echo Build failed.
exit /b 1

:end
endlocal
