@echo off
echo ========================================
echo PDF Page Changer Piano - Build Script
echo ========================================

echo.
echo 1. Creating virtual environment...
python -m venv venv

echo.
echo 2. Activating virtual environment...
call venv\Scripts\activate.bat

echo.
echo 3. Upgrading pip...
python -m pip install --upgrade pip

echo.
echo 4. Installing dependencies...
pip install -r requirements.txt

echo.
echo 5. Installing PyInstaller...
pip install pyinstaller

echo.
echo 6. Creating executable...
python setup.py

echo.
echo ========================================
echo Build completed!
echo Executable location: dist\PDFPageChangerPiano.exe
echo ========================================

echo.
echo Press any key to exit...
pause > nul 