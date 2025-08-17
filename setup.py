import PyInstaller.__main__
import os
import sys

def create_exe():
    """Create executable using PyInstaller"""
    
    # PyInstaller arguments
    args = [
        'PageChangerPiano.py',
        '--onefile',
        '--windowed',
        '--name=PDFPageChangerPiano',
        '--icon=icono.ico',
        '--add-data=icono.ico;.',
        '--hidden-import=pygame.midi',
        '--hidden-import=pygame._sdl2',
        '--hidden-import=cv2',
        '--hidden-import=fitz',
        '--hidden-import=PIL',
        '--hidden-import=numpy',
        '--collect-all=pygame',
        '--collect-all=cv2',
        '--collect-all=fitz',
        '--collect-all=PIL',
    ]
    
    # Run PyInstaller
    PyInstaller.__main__.run(args)

if __name__ == "__main__":
    create_exe() 