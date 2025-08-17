import os
import json
import threading

import fitz                    # PyMuPDF: renderizado de PDF
import cv2                     # conversión a/desde arrays NumPy
import numpy as np             # manejo de arrays de imagen
import pygame                  # interfaz de vídeo
import pygame.midi             # entrada MIDI
from pygame._sdl2 import Window  # para recuperar posición de la ventana de vídeo

from tkinter import (          # UI principal
    Tk, Button, Label, Canvas, Listbox, Scrollbar, Frame, PanedWindow,
    filedialog, simpledialog, messagebox, VERTICAL, END, HORIZONTAL,
    ttk, PhotoImage, StringVar, IntVar, BooleanVar
)
from PIL import Image, ImageTk  # manipulación y despliegue de imágenes

# === CONFIGURACIÓN GENERAL ===
THRESHOLD = 64
VIDEO_WIDTH, VIDEO_HEIGHT = 1920, 1080  # Tamaño fijo para el video

# === FUNCIÓN PARA ELEGIR PDF ===
def elegir_pdf():
    return filedialog.askopenfilename(
        title="Seleccione el PDF de la partitura",
        filetypes=[("Archivos PDF", "*.pdf")]
    )

# === FUNCIÓN PARA SELECCIONAR MIDI ===
def seleccionar_midi_input():
    dispositivos = []
    for i in range(pygame.midi.get_count()):
        interf, name, is_input, is_output, opened = pygame.midi.get_device_info(i)
        if is_input:
            dispositivos.append((i, name.decode()))
    if not dispositivos:
        messagebox.showerror("Sin dispositivos", "No se encontraron dispositivos MIDI de entrada.")
        return None
    opciones = "\n".join([f"{i}: {nombre}" for i, nombre in dispositivos])
    return simpledialog.askinteger(
        "Seleccionar MIDI",
        f"Seleccione el ID del dispositivo MIDI:\n\n{opciones}",
        minvalue=0, maxvalue=999
    )

# === INICIALIZACIÓN MIDI ===
pygame.midi.init()
input_id = seleccionar_midi_input()
if input_id is None:
    pygame.midi.quit()
    exit()
midi_input = pygame.midi.Input(input_id)

# === DETECCIÓN DE PEDAL DINÁMICA ===
def detectar_cc():
    info = Tk()
    info.title("Presione pedal o tecla MIDI...")
    info.geometry("350x100")
    info.attributes("-topmost", True)
    Label(info, text="Presione el pedal o tecla MIDI que usará para pasar página.").pack(pady=20)
    info.update()
    try:
        while True:
            info.update()
            if midi_input.poll():
                events = midi_input.read(10)
                for event in events:
                    try:
                        if isinstance(event, (list, tuple)) and len(event) > 0:
                            event_data = event[0]
                            if isinstance(event_data, (list, tuple)) and len(event_data) >= 4:
                                status, cc_number, value, _ = event_data
                                if status == 176 and value >= THRESHOLD:
                                    info.destroy()
                                    messagebox.showinfo("Control MIDI detectado", f"Se detectó CC #{cc_number}")
                                    return cc_number
                    except (IndexError, TypeError):
                        continue
    except Exception as e:
        info.destroy()
        messagebox.showerror("Error", f"Error al detectar CC: {e}")
        midi_input.close()
        pygame.midi.quit()
        exit()

MIDI_PEDAL_CC = None

class ModernButton(Button):
    """Botón moderno con estilo personalizado"""
    def __init__(self, parent, text, command, custom_color=None, **kwargs):
        super().__init__(parent, text=text, command=command, **kwargs)
        
        # Usar el color personalizado si se proporciona, sino el azul por defecto
        self.custom_color = custom_color or "#4a90e2"
        
        self.configure(
            relief="flat",
            bd=0,
            padx=15,
            pady=8,
            font=("Segoe UI", 9, "bold"),
            bg=self.custom_color,
            fg="white",
            activebackground=self.custom_color,
            activeforeground="white",
            cursor="hand2"
        )
        
        self.bind("<Enter>", self.on_enter)
        self.bind("<Leave>", self.on_leave)
    
    def on_enter(self, e):
        # Oscurecer ligeramente el color personalizado para el efecto hover
        self.configure(bg=self._darken_color(self.custom_color))
    
    def on_leave(self, e):
        # Restaurar el color personalizado original
        self.configure(bg=self.custom_color)
    
    def _darken_color(self, color):
        """Oscurece ligeramente un color hexadecimal"""
        try:
            # Convertir color hex a RGB
            color = color.lstrip('#')
            r, g, b = int(color[:2], 16), int(color[2:4], 16), int(color[4:], 16)
            # Oscurecer un 20%
            r = max(0, int(r * 0.8))
            g = max(0, int(g * 0.8))
            b = max(0, int(b * 0.8))
            return f"#{r:02x}{g:02x}{b:02x}"
        except:
            return self.custom_color  # Color de respaldo

class PartituraApp:
    def __init__(self, master):
        pygame.init()
        self.master = master
        self.master.geometry("1200x800")
        self.master.configure(bg="#f0f0f0")
        self.master.title("PDF Page Changer Piano - Visor de Partituras")
        
        # Variables de estado
        self.pdf_queue = []
        self.video_map = {}
        self.current_pdf_index = 0
        self.doc = None
        self.current_page = 0
        self.num_pages = 0
        self.page_cache = {}
        self.zoom = 1
        self.video_visible = False
        self.video_thread = None
        self.cap = None
        self.stop_event = threading.Event()
        
        # Variables de interfaz
        self.status_var = StringVar(value="Listo para cargar partituras")
        self.pdf_info_var = StringVar(value="Sin PDF cargado")
        self.page_info_var = StringVar(value="")
        
        # Cargar configuraciones al iniciar
        self.cargar_configuraciones()
        
        self._setup_ui()
        self.master.after(100, self.verificar_midi)
        self._update_title()

    def _setup_ui(self):
        # Frame principal con paneles
        main_paned = PanedWindow(self.master, orient=HORIZONTAL, bg="#f0f0f0")
        main_paned.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Panel izquierdo para controles y lista
        left_panel = Frame(main_paned, bg="#ffffff", relief="raised", bd=1)
        main_paned.add(left_panel, width=280)
        
        # Panel derecho para visualización
        right_panel = Frame(main_paned, bg="#ffffff", relief="raised", bd=1)
        main_paned.add(right_panel)
        
        self._setup_left_panel(left_panel)
        self._setup_right_panel(right_panel)
        self._setup_status_bar()

    def _setup_left_panel(self, parent):
        # Título del panel
        title_frame = Frame(parent, bg="#2c3e50", height=50)
        title_frame.pack(fill="x", pady=(0, 10))
        title_frame.pack_propagate(False)
        
        Label(title_frame, text="CONTROLES", font=("Segoe UI", 14, "bold"), 
              bg="#2c3e50", fg="white").pack(expand=True)
        
        # Sección de archivos
        self._create_section(parent, "GESTIÓN DE ARCHIVOS", [
            ("📁 Agregar PDF", self.agregar_pdf, "#27ae60"),
            ("💾 Guardar Lista", self.guardar_lista, "#8e44ad"),
            ("📂 Cargar Lista", self.cargar_lista, "#3498db"),
            ("🗑️ Eliminar PDF", self.eliminar_pdf, "#e74c3c")
        ])
        
        # Sección de navegación
        self._create_section(parent, "NAVEGACIÓN", [
            ("⏮️ Anterior", self.pagina_anterior, "#f39c12"),
            ("⏭️ Siguiente", self.pagina_siguiente, "#f39c12")
        ])
        
        # Sección de video
        self._create_section(parent, "MULTIMEDIA", [
            ("🎬 Agregar Video", self.agregar_video, "#e67e22"),
            ("📺 Toggle Video", self.toggle_video, "#9b59b6")
        ])
        
        # Sección de configuración
        self._create_section(parent, "CONFIGURACIÓN", [
            ("⚙️ Configuración", self.mostrar_configuracion, "#95a5a6")
        ])
        
        # Lista de PDFs
        list_frame = Frame(parent, bg="#ffffff")
        list_frame.pack(fill="both", expand=True, pady=(10, 0))
        
        Label(list_frame, text="COLA DE PDFs:", font=("Segoe UI", 10, "bold"), 
              bg="#ffffff", fg="#2c3e50").pack(anchor="w", pady=(0, 5))
        
        # Frame para lista y scrollbar
        list_container = Frame(list_frame)
        list_container.pack(fill="both", expand=True)
        
        self.lst = Listbox(list_container, 
                          font=("Consolas", 9),
                          selectmode="single",
                          bg="#f8f9fa",
                          fg="#2c3e50",
                          selectbackground="#3498db",
                          selectforeground="white",
                          relief="flat",
                          bd=1)
        
        scrollbar = ttk.Scrollbar(list_container, orient=VERTICAL, command=self.lst.yview)
        self.lst.configure(yscrollcommand=scrollbar.set)
        
        self.lst.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        self.lst.bind("<<ListboxSelect>>", self.on_select)

    def _create_section(self, parent, title, buttons):
        """Crea una sección con título y botones"""
        section_frame = Frame(parent, bg="#ffffff")
        section_frame.pack(fill="x", pady=(0, 15))
        
        # Título de la sección
        Label(section_frame, text=title, font=("Segoe UI", 10, "bold"), 
              bg="#ffffff", fg="#7f8c8d").pack(anchor="w", pady=(0, 8))
        
        # Botones de la sección
        for text, command, color in buttons:
            btn = ModernButton(section_frame, text=text, command=command, custom_color=color)
            btn.pack(fill="x", pady=2)

    def _setup_right_panel(self, parent):
        # Header del panel derecho
        header_frame = Frame(parent, bg="#ecf0f1", height=60)
        header_frame.pack(fill="x", pady=(0, 10))
        header_frame.pack_propagate(False)
        
        # Información del PDF actual
        info_frame = Frame(header_frame, bg="#ecf0f1")
        info_frame.pack(expand=True, padx=15)
        
        Label(info_frame, textvariable=self.pdf_info_var, 
              font=("Segoe UI", 12, "bold"), bg="#ecf0f1", fg="#2c3e50").pack(anchor="w")
        Label(info_frame, textvariable=self.page_info_var, 
              font=("Segoe UI", 10), bg="#ecf0f1", fg="#7f8c8d").pack(anchor="w")
        
        # Canvas para visualización
        canvas_frame = Frame(parent, bg="#000000")
        canvas_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        
        self.canvas = Canvas(canvas_frame, bg="black", highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)

    def _setup_status_bar(self):
        """Configura la barra de estado inferior"""
        status_frame = Frame(self.master, bg="#34495e", height=30)
        status_frame.pack(fill="x", side="bottom")
        status_frame.pack_propagate(False)
        
        # Información de estado
        Label(status_frame, textvariable=self.status_var, 
              font=("Segoe UI", 9), bg="#34495e", fg="white").pack(side="left", padx=10)
        
        # Información del pedal MIDI
        midi_text = f"Pedal MIDI: CC #{MIDI_PEDAL_CC if MIDI_PEDAL_CC else 'No configurado'}"
        Label(status_frame, text=midi_text, 
              font=("Segoe UI", 9), bg="#34495e", fg="#bdc3c7").pack(side="right", padx=10)

    def mostrar_configuracion(self):
        """Muestra ventana de configuración"""
        config_window = Tk()
        config_window.title("Configuración")
        config_window.geometry("500x400")
        config_window.configure(bg="#f0f0f0")
        config_window.attributes("-topmost", True)
        
        # Centrar ventana
        config_window.grab_set()
        
        Label(config_window, text="Configuración de la Aplicación", 
              font=("Segoe UI", 14, "bold"), bg="#f0f0f0", fg="#2c3e50").pack(pady=20)
        
        # Opciones de configuración
        options_frame = Frame(config_window, bg="#f0f0f0")
        options_frame.pack(fill="both", expand=True, padx=20)
        
        # Configuración de resolución de video
        Label(options_frame, text="Resolución del Video:", 
              font=("Segoe UI", 12, "bold"), bg="#f0f0f0", fg="#2c3e50").pack(anchor="w", pady=(0, 10))
        
        # Frame para botones de resolución
        res_frame = Frame(options_frame, bg="#f0f0f0")
        res_frame.pack(fill="x", pady=(0, 20))
        
        # Botones de resolución predefinidas
        resolutions = [
            ("HD (1280x720)", 1280, 720),
            ("Full HD (1920x1080)", 1920, 1080),
            ("2K (2560x1440)", 2560, 1440),
            ("4K (3840x2160)", 3840, 2160)
        ]
        
        for i, (text, width, height) in enumerate(resolutions):
            btn = Button(res_frame, text=text, 
                        command=lambda w=width, h=height: self.cambiar_resolucion_video(w, h),
                        bg="#3498db", fg="white", relief="flat", padx=15, pady=5)
            btn.pack(fill="x", pady=2)
        
        # Resolución actual
        current_res = f"Resolución actual: {VIDEO_WIDTH}x{VIDEO_HEIGHT}"
        Label(options_frame, text=current_res, 
              font=("Segoe UI", 10), bg="#f0f0f0", fg="#7f8c8d").pack(pady=10)
        
        # Separador
        separator = Frame(options_frame, height=2, bg="#bdc3c7")
        separator.pack(fill="x", pady=20)
        
        # Configuración del pedal MIDI
        Label(options_frame, text="Configuración del Pedal MIDI:", 
              font=("Segoe UI", 12, "bold"), bg="#f0f0f0", fg="#2c3e50").pack(anchor="w", pady=(0, 10))
        
        # Información del pedal actual
        pedal_info = f"Pedal actual: CC #{MIDI_PEDAL_CC if MIDI_PEDAL_CC else 'No configurado'}"
        Label(options_frame, text=pedal_info, 
              font=("Segoe UI", 10), bg="#f0f0f0", fg="#7f8c8d").pack(pady=(0, 10))
        
        # Botón para cambiar pedal
        Button(options_frame, text="🎹 Cambiar Pedal MIDI", 
               command=self.cambiar_pedal,
               bg="#34495e", fg="white", relief="flat", padx=15, pady=8).pack(fill="x", pady=5)
        
        Button(config_window, text="Cerrar", command=config_window.destroy,
               bg="#e74c3c", fg="white", relief="flat", padx=20, pady=5).pack(pady=20)
    
    def cargar_configuraciones(self):
        """Carga las configuraciones guardadas"""
        global VIDEO_WIDTH, VIDEO_HEIGHT, MIDI_PEDAL_CC
        try:
            if os.path.exists("config.json"):
                with open("config.json", "r") as f:
                    config = json.load(f)
                    VIDEO_WIDTH = config.get("video_width", 1920)
                    VIDEO_HEIGHT = config.get("video_height", 1080)
                    MIDI_PEDAL_CC = config.get("midi_pedal_cc", None)
        except Exception as e:
            print(f"Error al cargar configuraciones: {e}")
    
    def guardar_configuraciones(self):
        """Guarda las configuraciones actuales"""
        global VIDEO_WIDTH, VIDEO_HEIGHT, MIDI_PEDAL_CC
        try:
            config = {
                "video_width": VIDEO_WIDTH,
                "video_height": VIDEO_HEIGHT,
                "midi_pedal_cc": MIDI_PEDAL_CC
            }
            with open("config.json", "w") as f:
                json.dump(config, f, indent=2)
        except Exception as e:
            print(f"Error al guardar configuraciones: {e}")
    
    def cambiar_resolucion_video(self, width, height):
        """Cambia la resolución del video"""
        global VIDEO_WIDTH, VIDEO_HEIGHT
        VIDEO_WIDTH, VIDEO_HEIGHT = width, height
        self.status_var.set(f"Resolución del video cambiada a {width}x{height}")
        # Guardar configuración automáticamente
        self.guardar_configuraciones()
        messagebox.showinfo("Resolución Cambiada", 
                          f"La resolución del video se ha cambiado a {width}x{height}.\n"
                          "Los cambios se han guardado automáticamente.")

    def _update_title(self):
        t = "PDF Page Changer Piano - Visor de Partituras"
        if self.doc:
            name = os.path.basename(self.pdf_queue[self.current_pdf_index])
            t += f" - {name} ({self.current_page+1}/{self.num_pages})"
        self.master.title(t)

    def _update_list(self):
        self.lst.delete(0, END)
        for i, p in enumerate(self.pdf_queue):
            pref = "▶ " if i == self.current_pdf_index else "  "
            self.lst.insert(END, pref + os.path.basename(p))
        if self.pdf_queue:
            self.lst.see(self.current_pdf_index)

    def on_select(self, e):
        sel = self.lst.curselection()
        if sel:
            idx = sel[0]
            if idx != self.current_pdf_index:
                was_visible = self.video_visible
                self._stop_video()
                self.current_pdf_index = idx
                self._refresh_pdf()
                if was_visible:
                    self._start_video()

    def agregar_pdf(self):
        p = elegir_pdf()
        if p:
            self.pdf_queue.append(p)
            self._update_list()
            self.status_var.set(f"PDF agregado: {os.path.basename(p)}")
            if not self.doc:
                self._refresh_pdf()

    def guardar_lista(self):
        if not self.pdf_queue:
            messagebox.showerror("Error", "No hay PDFs en la cola para guardar")
            return
        f = filedialog.asksaveasfilename(defaultextension=".vdp", filetypes=[("VDP", "*.vdp")])
        if f:
            json.dump({"pdf_queue": self.pdf_queue, "video_map": self.video_map}, open(f, 'w'), indent=2)
            self.status_var.set("Lista guardada exitosamente")

    def cargar_lista(self):
        was_visible = self.video_visible
        self._stop_video()
        f = filedialog.askopenfilename(filetypes=[("VDP", "*.vdp")])
        if f:
            data = json.load(open(f))
            self.pdf_queue = data.get("pdf_queue", [])
            self.video_map = data.get("video_map", {})
            self.current_pdf_index = 0
            self._refresh_pdf()
            if was_visible:
                self._start_video()
            self.status_var.set(f"Lista cargada: {len(self.pdf_queue)} PDFs")

    def agregar_video(self):
        if not self.pdf_queue:
            messagebox.showwarning("Error", "Primero debes cargar un PDF")
            return
        v = filedialog.askopenfilename(filetypes=[("Videos", "*.mp4;*.avi;*.mov")])
        if v:
            self.video_map[self.pdf_queue[self.current_pdf_index]] = v
            self.status_var.set(f"Video asignado a {os.path.basename(self.pdf_queue[self.current_pdf_index])}")

    def toggle_video(self):
        if self.video_visible:
            self._stop_video()
            self.status_var.set("Video detenido")
        else:
            self._start_video()

    def _start_video(self):
        path = self.video_map.get(self.pdf_queue[self.current_pdf_index])
        if not path:
            messagebox.showinfo("Sin video", "No hay video asignado a este PDF")
            return

        # Si ya tenemos una posición guardada, la aplicamos
        if hasattr(self, 'video_pos') and self.video_pos:
            x, y = self.video_pos
            os.environ['SDL_VIDEO_WINDOW_POS'] = f"{x},{y}"
        else:
            # opcional: centra la ventana la primera vez
            os.environ['SDL_VIDEO_CENTERED'] = '1'

        
        self.video_visible = True
        self.stop_event.clear()
        self.cap = cv2.VideoCapture(path)
        pygame.display.init()
        screen = pygame.display.set_mode((VIDEO_WIDTH, VIDEO_HEIGHT))
        pygame.display.set_caption("Vídeo")
        self.video_thread = threading.Thread(target=self._video_loop, args=(screen,), daemon=True)
        self.video_thread.start()

        # 👉 fuerza a que la ventana de partituras quede por encima
        self.master.lift()
        self.master.attributes('-topmost', True)
        # opcional: desactivar "topmost" si no quieres que siempre esté por encima
        self.master.after(100, lambda: self.master.attributes('-topmost', False))
        
        self.status_var.set("Video iniciado")

    def _video_loop(self, screen):
        clock = pygame.time.Clock()
        try:
            while self.video_visible and not self.stop_event.is_set():
                if self.cap is None:
                    break
                ret, frame = self.cap.read()
                if not ret:
                    if self.cap is not None:
                        self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                    continue
                frame = cv2.resize(frame, (VIDEO_WIDTH, VIDEO_HEIGHT))
                img = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                surf = pygame.surfarray.make_surface(np.rot90(img))
                screen.blit(surf, (0, 0))
                pygame.display.flip()
                for ev in pygame.event.get():
                    if ev.type == pygame.QUIT:
                        self.video_visible = False
                        break
                clock.tick(30)
        finally:
            # Solo liberamos el video, la pantalla se cierra en _stop_video
            if self.cap is not None:
                self.cap.release()

    def _stop_video(self):
        # Señalizar al hilo que debe detenerse
        if self.video_visible:
            try:
                win = Window.from_display_module()
                self.video_pos = win.position
            except:
                self.video_pos = None
            self.video_visible = False
            self.stop_event.set()
        # Esperar a que el hilo termine completamente
        if self.video_thread:
            self.video_thread.join()
            self.video_thread = None
        # Liberar captura si aún existe
        if self.cap:
            self.cap.release()
            self.cap = None
        # Cerrar la ventana de vídeo
        try:
            pygame.display.quit()
        except Exception:
            pass

    def _refresh_pdf(self):
        path = self.pdf_queue[self.current_pdf_index]
        self.doc = fitz.open(path)
        self.num_pages = len(self.doc)
        self.current_page = 0
        self.page_cache.clear()
        self._update_list()
        self.mostrar_pagina()
        
        # Actualizar información en la interfaz
        self.pdf_info_var.set(f"PDF: {os.path.basename(path)}")
        self.page_info_var.set(f"Páginas: {self.num_pages} | Página actual: {self.current_page + 1}")

    def pagina_anterior(self):
        if self.current_page >= 2:
            self.current_page -= 2
        elif self.current_pdf_index > 0:
            was_visible = self.video_visible
            self._stop_video()
            self.current_pdf_index -= 1
            self._refresh_pdf()
            if was_visible:
                self._start_video()
        self.mostrar_pagina()

    def pagina_siguiente(self):
        if self.current_page + 2 < self.num_pages:
            self.current_page += 2
        elif self.current_pdf_index < len(self.pdf_queue) - 1:
            was_visible = self.video_visible
            self._stop_video()
            self.current_pdf_index += 1
            self._refresh_pdf()
            if was_visible:
                self._start_video()
        self.mostrar_pagina()

    def mostrar_pagina(self):
        if not self.doc:
            return
        imgs = []
        for off in (0, 1):
            idx = self.current_page + off
            if 0 <= idx < self.num_pages:
                if idx not in self.page_cache:
                    pix = self.doc.load_page(idx).get_pixmap(matrix=fitz.Matrix(self.zoom, self.zoom))
                    arr = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, pix.n)
                    self.page_cache[idx] = Image.fromarray(cv2.cvtColor(arr[..., :3], cv2.COLOR_BGR2RGB))
                imgs.append(self.page_cache[idx])
            else:
                imgs.append(Image.new("RGB", (800, 1000), (211, 211, 211)))
        total_w = sum(im.width for im in imgs)
        max_h = max(im.height for im in imgs)
        combo = Image.new("RGB", (total_w, max_h), (0, 0, 0))
        x = 0
        for im in imgs:
            combo.paste(im, (x, 0))
            x += im.width
        w, h = self.canvas.winfo_width(), self.canvas.winfo_height()
        if w > 1 and h > 1:  # Evitar error si el canvas no tiene dimensiones
            self.tk_img = ImageTk.PhotoImage(combo.resize((w, h), Image.LANCZOS))
            self.canvas.delete("all")
            self.canvas.create_image(0, 0, anchor="nw", image=self.tk_img)
        self._update_title()
        
        # Actualizar información de página
        if self.doc:
            self.page_info_var.set(f"Páginas: {self.num_pages} | Página actual: {self.current_page + 1}")

    def verificar_midi(self):
        if midi_input.poll():
            events = midi_input.read(10)
            for event in events:
                status, cc_number, value, _ = event[0]
                if status == 176 and cc_number == MIDI_PEDAL_CC and value >= THRESHOLD:
                    self.pagina_siguiente()
        self.master.after(100, self.verificar_midi)

    def cambiar_pedal(self):
        cc = detectar_cc()
        if cc is not None:
            globals()['MIDI_PEDAL_CC'] = cc
            self.status_var.set(f"Pedal MIDI configurado: CC #{cc}")
            # Guardar configuración automáticamente
            self.guardar_configuraciones()

    def eliminar_pdf(self):
        if not self.pdf_queue:
            messagebox.showwarning("Error", "No hay PDFs para eliminar")
            return
            
        was_visible = self.video_visible
        self._stop_video()
        if self.pdf_queue:
            self.pdf_queue.pop(self.current_pdf_index)
            if self.pdf_queue:
                self.current_pdf_index %= len(self.pdf_queue)
                self._refresh_pdf()
                if was_visible:
                    self._start_video()
            else:
                self.canvas.delete("all")
                self.doc = None
                self.pdf_info_var.set("Sin PDF cargado")
                self.page_info_var.set("")
                self._update_list()
            self.status_var.set("PDF eliminado")

    def cerrar_aplicacion(self):
        self._stop_video()
        midi_input.close()
        pygame.midi.quit()
        pygame.quit()
        self.master.destroy()

if __name__ == "__main__":
    root = Tk()
    root.configure(bg="#f0f0f0")
    PartituraApp(root)
    root.mainloop()




    
