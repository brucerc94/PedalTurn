Write-Host "========================================" -ForegroundColor Green
Write-Host "PDF Page Changer Piano - Build Script" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green

Write-Host ""
Write-Host "1. Creating virtual environment..." -ForegroundColor Yellow
python -m venv venv

Write-Host ""
Write-Host "2. Activating virtual environment..." -ForegroundColor Yellow
& "venv\Scripts\Activate.ps1"

Write-Host ""
Write-Host "3. Upgrading pip..." -ForegroundColor Yellow
python -m pip install --upgrade pip

Write-Host ""
Write-Host "4. Installing dependencies..." -ForegroundColor Yellow
pip install -r requirements.txt

Write-Host ""
Write-Host "5. Installing PyInstaller..." -ForegroundColor Yellow
pip install pyinstaller

Write-Host ""
Write-Host "6. Creating executable..." -ForegroundColor Yellow
python setup.py

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "Build completed!" -ForegroundColor Green
Write-Host "Executable location: dist\PDFPageChangerPiano.exe" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green

Write-Host ""
Write-Host "Press any key to exit..." -ForegroundColor Cyan
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown") 