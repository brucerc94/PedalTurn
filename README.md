# PDF Page Changer Piano

Visor de partituras PDF pensado para tocar con piano/teclado y pedal MIDI.

## Versión 2.0 — refactor modular

Esta rama reemplaza la implementación monolítica anterior por una arquitectura separada por responsabilidades.

pdf_page_changer/
  core/              Modelos y reglas de navegación
  controllers/       Orquestación de la aplicación
  services/          PDF, MIDI, video, configuración y proyectos
  ui/                Ventanas, diálogos, visor y estilos
  main.py            Entrada de la aplicación

## Qué cambia

- PySide6 / Qt 6 en lugar de Tkinter.
- Qt Multimedia para video; se elimina OpenCV de la reproducción.
- Sin estado global para PDF, video, MIDI o configuración.
- Navegación de partituras separada de la interfaz.
- Configuración centralizada y tolerante a JSON inválido.
- Caché LRU para páginas renderizadas.
- Compatibilidad con proyectos .vdp de la versión anterior.
- Detección MIDI no bloqueante mediante el event loop de Qt.
- El pedal responde a una transición de reposo a pulsación para evitar múltiples avances mientras se mantiene presionado.
- Cierre limpio de documentos PDF, MIDI y video.
- Renderizado de páginas manteniendo la proporción.
- Evita duplicar el mismo PDF en la cola.
- Interfaz optimizada para pianistas: la partitura ocupa toda la ventana y los controles flotantes se ocultan automáticamente después de 3,5 segundos.

## Requisitos

- Windows 10/11
- Python 3.10 o superior
- Dispositivo MIDI opcional

## Ejecutar

1. Ejecuta build.bat para crear/actualizar venv e instalar dependencias.
2. Ejecuta run.bat para activar venv y lanzar la aplicación.

También puedes ejecutar PageChangerPiano.py directamente desde el entorno virtual.

## Generar EXE

Usa build.bat o build.ps1.

El ejecutable se genera en dist/PDFPageChangerPiano.exe.

## Funciones

### Partituras
- Agregar múltiples PDFs.
- Seleccionar cualquier PDF de la cola.
- Mostrar dos páginas simultáneamente.
- Siguiente/anterior con botones.
- Navegación con flechas izquierda/derecha.
- Zoom con Ctrl + rueda del mouse.
- Controles de zoom Ajustar, + y −.

### MIDI
- Lista de dispositivos MIDI de entrada.
- Selección de dispositivo desde Configuración.
- Detección del número CC del pedal.
- Soporte para cualquier canal de mensajes Control Change.
- Anti-repetición mientras el pedal permanece presionado.

### Video
- Un video asociado a cada PDF.
- Ventana independiente.
- Reproducción en bucle.
- Conserva la posición de la ventana.
- Mantiene la relación de aspecto.
- Formatos habituales como MP4, AVI, MOV, MKV y WebM según codecs/backend disponibles.

## Proyectos VDP

La versión 2 usa un formato versionado con una lista de items, cada uno con PDF y video opcional.

Los proyectos antiguos que usaban pdf_queue y video_map continúan siendo compatibles.

## Configuración

config.json almacena tamaño inicial de video, CC MIDI, nombre del dispositivo MIDI y posición de la ventana de video.

La ubicación se resuelve junto al ejecutable cuando está empaquetado y junto al proyecto cuando se ejecuta como Python.

## Pruebas

Ejecuta: python -m unittest discover -s tests -v

Las pruebas actuales cubren navegación y compatibilidad del formato VDP.

## Estructura

PDFPageChangerPiano/
  pdf_page_changer/
  tests/
  PageChangerPiano.py
  requirements.txt
  pyproject.toml
  build.bat
  build.ps1
  run.bat
  icono.ico
  config.json
  README.md

## Autor

Bruno Rivas Centty
