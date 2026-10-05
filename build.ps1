$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

Write-Host "========================================" -ForegroundColor Green
Write-Host "PDF Page Changer Piano - Build" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green

if (-not (Test-Path "venv\Scripts\python.exe")) {
    Write-Host "Creating virtual environment..." -ForegroundColor Yellow
    python -m venv venv
}

$python = Join-Path $PSScriptRoot "venv\Scripts\python.exe"

Write-Host "Installing dependencies..." -ForegroundColor Yellow
& $python -m pip install --upgrade pip
& $python -m pip install -r requirements.txt

Write-Host "Building executable..." -ForegroundColor Yellow
& $python -m PyInstaller --clean --noconfirm --onefile --windowed --name PDFPageChangerPiano --icon icono.ico --collect-all PySide6.QtMultimedia --hidden-import PySide6.QtMultimedia --hidden-import PySide6.QtMultimediaWidgets PageChangerPiano.py

Write-Host "" 
Write-Host "Build completed successfully." -ForegroundColor Green
Write-Host "Executable: dist\PDFPageChangerPiano.exe" -ForegroundColor Green
