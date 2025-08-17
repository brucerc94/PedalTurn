# PDF Page Changer Piano

Aplicación para cambiar páginas de partituras PDF usando controles MIDI (pedales de piano).

## Características

- Visualización de partituras PDF
- Control de páginas mediante pedales MIDI
- Reproducción de videos sincronizados
- Interfaz gráfica intuitiva
- Soporte para múltiples PDFs en cola

## Requisitos del Sistema

- Windows 10/11
- Python 3.8 o superior
- Dispositivo MIDI (pedal de piano, teclado, etc.)

## Instalación y Configuración

### Opción 1: Script Automático (Recomendado)

1. **Ejecutar el script de construcción:**
   ```cmd
   # Usando Command Prompt
   build.bat
   
   # O usando PowerShell
   .\build.ps1
   ```

2. **El script automáticamente:**
   - Crea un entorno virtual
   - Instala todas las dependencias
   - Genera el ejecutable
   - El archivo .exe se creará en la carpeta `dist/`

### Opción 2: Instalación Manual

1. **Crear entorno virtual:**
   ```cmd
   python -m venv venv
   venv\Scripts\activate
   ```

2. **Instalar dependencias:**
   ```cmd
   pip install -r requirements.txt
   ```

3. **Ejecutar la aplicación:**
   ```cmd
   python PageChangerPiano.py
   ```

## Dependencias

- **PyMuPDF (fitz)**: Renderizado de PDFs
- **OpenCV (cv2)**: Procesamiento de video
- **NumPy**: Manejo de arrays de imagen
- **Pygame**: Interfaz de video y MIDI
- **PIL/Pillow**: Manipulación de imágenes
- **Tkinter**: Interfaz gráfica (incluido con Python)

## Uso

1. **Ejecutar la aplicación:**
   - Doble clic en `PDFPageChangerPiano.exe` (si usaste el script)
   - O ejecutar `python PageChangerPiano.py` (si instalaste manualmente)

2. **Configurar dispositivo MIDI:**
   - La aplicación detectará automáticamente dispositivos MIDI
   - Selecciona tu dispositivo de entrada
   - Presiona el pedal o tecla que usarás para cambiar página

3. **Cargar partituras:**
   - Usa "Agregar PDF" para cargar archivos de partitura
   - Puedes cargar múltiples PDFs
   - Usa "Guardar lista" para guardar tu configuración

4. **Reproducir videos (opcional):**
   - Usa "Agregar video" para asignar videos a partituras
   - Usa "Toggle Video" para mostrar/ocultar el video

## Controles

- **Pedal MIDI**: Cambiar a la siguiente página
- **Botón "Siguiente →"**: Página siguiente
- **Botón "← Anterior"**: Página anterior
- **Botón "Cambiar pedal"**: Reconfigurar control MIDI

## Estructura del Proyecto

```
PDFPageChangerPiano/
├── PageChangerPiano.py      # Código principal
├── requirements.txt         # Dependencias
├── setup.py                # Script de construcción
├── build.bat               # Script automático (CMD)
├── build.ps1               # Script automático (PowerShell)
├── icono.ico               # Icono de la aplicación
└── README.md               # Este archivo
```

## Solución de Problemas

### Error de MIDI
- Asegúrate de que tu dispositivo MIDI esté conectado y funcionando
- Verifica que el driver del dispositivo esté instalado

### Error de Video
- Asegúrate de que los archivos de video sean compatibles (MP4, AVI, MOV)
- Verifica que el codec de video esté instalado en el sistema

### Error de PDF
- Verifica que los archivos PDF no estén corruptos
- Asegúrate de que los PDFs no estén protegidos con contraseña

## Notas Técnicas

- La aplicación usa PyInstaller para crear el ejecutable
- El entorno virtual aísla las dependencias del sistema
- Los archivos .vdp guardan la configuración de PDFs y videos

## Autor

Bruno - Versión 1.3

