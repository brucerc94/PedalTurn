<p align="center">
  <img src="icono.ico" alt="PDF Page Changer Piano" width="96">
</p>

<h1 align="center">PDF Page Changer Piano</h1>

<p align="center">
  A modern Windows score viewer with MIDI pedal page turning and optional video playback.
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10%2B-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python 3.10+">
  <img src="https://img.shields.io/badge/PySide6-Qt%206-41CD52?style=for-the-badge&logo=qt&logoColor=white" alt="PySide6">
  <img src="https://img.shields.io/badge/Platform-Windows-0078D6?style=for-the-badge&logo=windows&logoColor=white" alt="Windows">
</p>

## Overview

PDF Page Changer Piano is a distraction-free score viewer designed for pianists and keyboard players who need reliable hands-free page turning.

It combines:

- High-quality PDF score rendering
- Two-page spread viewing
- MIDI Control Change pedal navigation
- Optional video playback linked to each score
- Floating controls that automatically hide while playing
- Playlist management for multiple scores
- Versioned `.vdp` project files

The application is built with a modular architecture that separates the UI, application orchestration, navigation rules, and media services.

## Highlights

### Pianist-focused interface

The score occupies the available window with minimal visual distraction. The control panel floats over the viewer and automatically hides after 3.5 seconds.

Press `Esc` to bring the controls back instantly.

### MIDI pedal page turning

Connect a MIDI input device and assign any Control Change message to page turning. The pedal is edge-triggered, so holding it down does not repeatedly advance pages.

### Score playlist

Load multiple PDF scores and switch between them from a compact floating playlist. Each entry can show its current, video-linked, or missing-file state.

### Video playback

Attach one video to each PDF score. Videos play in a separate Qt Multimedia window, loop automatically, preserve aspect ratio, and remember their last window position.

## Features

| Area | Features |
| --- | --- |
| PDF | Two-page spreads, aspect-ratio preservation, page navigation, zoom, LRU page cache |
| MIDI | Device discovery, device selection, automatic pedal detection, channel-independent CC handling, press-edge triggering |
| Video | MP4/AVI/MOV/MKV/WebM support depending on the installed Qt Multimedia backend, looping playback, persistent window position |
| Projects | Version 2 `.vdp` format with legacy project compatibility |
| UI | PySide6 / Qt 6, dark theme, floating controls, auto-hide behavior, no Tkinter |
| Reliability | No global application state, clean PDF/MIDI/video shutdown, duplicate-PDF prevention |

## Requirements

- Windows 10 or Windows 11
- Python 3.10 or newer
- A MIDI input device is optional
- Qt Multimedia-compatible codecs/backend for video formats that require them

## Quick Start

Clone the repository, then run:

```bat
run.bat
```

The launcher creates or repairs the virtual environment, installs missing dependencies, and starts the application.

For a clean Windows executable build:

```bat
build.bat
```

The generated executable is:

```
dist\PDFPageChangerPiano.exe
```

The Windows executable and application window use `icono.ico` as their icon.

## Controls

| Action | Shortcut / Control |
| --- | --- |
| Next spread | `Right Arrow` or MIDI pedal |
| Previous spread | `Left Arrow` |
| Show controls | `Esc` |
| Zoom in/out | `Ctrl + Mouse Wheel` |
| Fit to screen | Floating control: **Fit** |

## MIDI Setup

1. Open **Settings**.
2. Select the MIDI input device.
3. Use **Detect MIDI Pedal** and press the desired pedal once.
4. The detected Control Change number is stored in `config.json`.

The MIDI layer accepts Control Change messages on any MIDI channel.

## VDP Projects

The current project format is versioned:

```json
{
  "version": 2,
  "items": [
    {
      "pdf": "C:\\Scores\\Example.pdf",
      "video": "C:\\Videos\\Example.mp4"
    }
  ]
}
```

Older projects that use `pdf_queue` and `video_map` remain readable.

## Configuration

`config.json` stores:

- Video window width and height
- Selected MIDI device name
- MIDI pedal Control Change number
- Saved video window position

When running from Python, configuration is resolved from the project directory. When running as a packaged executable, it is resolved next to the executable.

## Architecture

```text
PDFPageChangerPiano/
├── pdf_page_changer/
│   ├── core/           # Domain models and navigation rules
│   ├── controllers/    # Application orchestration
│   ├── services/      # PDF, MIDI, media, config, project services
│   ├── ui/            # Qt windows, dialogs, viewer and styling
│   ├── utils/         # Application paths
│   └── main.py        # Application entry point
├── PageChangerPiano.py
├── requirements.txt
├── build.bat
├── run.bat
├── config.json
├── icono.ico
└── README.md
```

## Technology

- **Python**
- **PySide6 / Qt 6**
- **PyMuPDF**
- **Pygame MIDI**
- **Qt Multimedia**
- **PyInstaller**

## Project Status

This branch contains the modular refactor of the original application. The legacy Tkinter UI has been replaced with PySide6, while PDF, MIDI, project, configuration, and media responsibilities are separated into dedicated modules.

## Author

**Bruno Rivas Centty**
