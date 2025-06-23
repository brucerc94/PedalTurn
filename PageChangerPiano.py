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
    Tk, Button, Label, Canvas, Listbox, Scrollbar,
    filedialog, simpledialog, messagebox, VERTICAL, END, Frame
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
                for (status, cc_number, value, _) in [e[0] for e in events]:
                    if status == 176 and value >= THRESHOLD:
                        info.destroy()
                        messagebox.showinfo("Control MIDI detectado", f"Se detectó CC #{cc_number}")
                        return cc_number
    except Exception as e:
        info.destroy()
        messagebox.showerror("Error", f"Error al detectar CC: {e}")
        midi_input.close()
        pygame.midi.quit()
        exit()

MIDI_PEDAL_CC = None

class PartituraApp:
    def __init__(self, master):
        pygame.init()
        self.master = master
        self.master.geometry("1000x800")
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

        self._setup_ui()
        self.master.after(100, self.verificar_midi)
        self._update_title()

    def _setup_ui(self):
        frame = Frame(self.master)
        frame.pack(pady=5)
        acciones = [
            ("← Anterior", self.pagina_anterior),
            ("Siguiente →", self.pagina_siguiente),
            ("Agregar PDF", self.agregar_pdf),
            ("Guardar lista", self.guardar_lista),
            ("Cargar lista", self.cargar_lista),
            ("Cambiar pedal", self.cambiar_pedal),
            ("Agregar video", self.agregar_video),
            ("Toggle Video", self.toggle_video),
            ("Eliminar PDF", self.eliminar_pdf),
            ("Cerrar", self.cerrar_aplicacion)
        ]
        for i, (txt, cmd) in enumerate(acciones):
            Button(frame, text=txt, command=cmd).grid(row=0, column=i, padx=3)

        lf = Frame(self.master)
        lf.pack(fill="x", padx=10, pady=5)
        Label(lf, text="Cola de PDFs:").pack(anchor="w")
        self.lst = Listbox(lf, height=4)
        self.lst.pack(fill="x", side="left", expand=True)
        sb = Scrollbar(lf, orient=VERTICAL, command=self.lst.yview)
        sb.pack(side="right", fill="y")
        self.lst.config(yscrollcommand=sb.set)
        self.lst.bind("<<ListboxSelect>>", self.on_select)

        self.canvas = Canvas(self.master, width=800, height=600, bg="black")
        self.canvas.pack(fill="both", expand=True)

    def _update_title(self):
        t = "Viso de Partituras V1.3 by Bruno"
        if self.doc:
            name = os.path.basename(self.pdf_queue[self.current_pdf_index])
            t += f" - {name} ({self.current_page+1}/{self.num_pages})"
        self.master.title(t)

    def _update_list(self):
        self.lst.delete(0, END)
        for i, p in enumerate(self.pdf_queue):
            pref = "→ " if i == self.current_pdf_index else "   "
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
            messagebox.showinfo("PDF agregado", os.path.basename(p))
            if not self.doc:
                self._refresh_pdf()

    def guardar_lista(self):
        if not self.pdf_queue:
            return messagebox.showerror("Error", "Cola vacía")
        f = filedialog.asksaveasfilename(defaultextension=".vdp", filetypes=[("VDP", "*.vdp")])
        if f:
            json.dump({"pdf_queue": self.pdf_queue, "video_map": self.video_map}, open(f, 'w'), indent=2)

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

    def agregar_video(self):
        if not self.pdf_queue:
            return messagebox.showwarning("Error", "Sin PDF")
        v = filedialog.askopenfilename(filetypes=[("Videos", "*.mp4;*.avi;*.mov")])
        if v:
            self.video_map[self.pdf_queue[self.current_pdf_index]] = v

    def toggle_video(self):
        if self.video_visible:
            self._stop_video()
        else:
            self._start_video()

    def _start_video(self):
        path = self.video_map.get(self.pdf_queue[self.current_pdf_index])
        if not path:
            return messagebox.showinfo("Sin video", "No asignado")

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
        # opcional: desactivar “topmost” si no quieres que siempre esté por encima
        self.master.after(100, lambda: self.master.attributes('-topmost', False))

    def _video_loop(self, screen):
        clock = pygame.time.Clock()
        try:
            while self.video_visible and not self.stop_event.is_set():
                ret, frame = self.cap.read()
                if not ret:
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
            self.cap.release()

    def _stop_video(self):
        # Señalizar al hilo que debe detenerse
        if self.video_visible:
            win = Window.from_display_module()
            self.video_pos = win.position  
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
        combo = Image.new("RGB", (total_w, max_h), "black")
        x = 0
        for im in imgs:
            combo.paste(im, (x, 0))
            x += im.width
        w, h = self.canvas.winfo_width(), self.canvas.winfo_height()
        self.tk_img = ImageTk.PhotoImage(combo.resize((w, h), Image.LANCZOS))
        self.canvas.delete("all")
        self.canvas.create_image(0, 0, anchor="nw", image=self.tk_img)
        self._update_title()

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

    def eliminar_pdf(self):
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
                self._update_list()

    def cerrar_aplicacion(self):
        self._stop_video()
        midi_input.close()
        pygame.midi.quit()
        pygame.quit()
        self.master.destroy()

if __name__ == "__main__":
    root = Tk()
    root.configure(bg="black")
    PartituraApp(root)
    root.mainloop()




    
