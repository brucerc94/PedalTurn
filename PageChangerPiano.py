import fitz  # PyMuPDF
import cv2
import pygame.midi
import numpy as np
import json
import os
import threading
import queue
from tkinter import (
    Tk, Toplevel, Button, Label, Canvas, Listbox, Scrollbar,
    filedialog, simpledialog, messagebox, VERTICAL, END, Frame
)
from PIL import Image, ImageTk

# === CONFIGURACIÓN GENERAL ===
THRESHOLD = 64

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
                    status, cc_number, value, _ = event[0]
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
        self.master = master
        self.master.geometry("1000x800")
        self.pdf_queue   = []
        self.video_map   = {}           # mapa PDF → ruta de vídeo
        self.current_pdf_index = 0
        self.doc         = None
        self.current_page= 0
        self.num_pages   = 0
        self.page_cache  = {}
        self.zoom        = 1

        # estado de la ventana de vídeo
        self.video_win    = None
        self.video_label  = None
        self.video_cap    = None
        self.video_visible= False
        self.frame_queue  = queue.Queue(maxsize=1)
        self.video_thread = None

        # Frame de botones
        self.btn_frame = Frame(master)
        self.btn_frame.pack(pady=5)
        Button(self.btn_frame, text="← Anterior",       command=self.pagina_anterior).grid(row=0, column=0, padx=5)
        Button(self.btn_frame, text="Siguiente →",      command=self.pagina_siguiente).grid(row=0, column=1, padx=5)
        Button(self.btn_frame, text="Agregar PDF a cola", command=self.agregar_pdf).grid(row=0, column=2, padx=5)
        Button(self.btn_frame, text="Guardar lista",    command=self.guardar_lista).grid(row=0, column=3, padx=5)
        Button(self.btn_frame, text="Cargar lista",     command=self.cargar_lista).grid(row=0, column=4, padx=5)
        Button(self.btn_frame, text="Cambiar pedal MIDI", command=self.cambiar_pedal).grid(row=0, column=5, padx=5)
        Button(self.btn_frame, text="Agregar video",    command=self.agregar_video).grid(row=0, column=6, padx=5)
        Button(self.btn_frame, text="Toggle Video",     command=self.toggle_video).grid(row=0, column=7, padx=5)
        Button(self.btn_frame, text="Eliminar PDF",     command=self.eliminar_pdf).grid(row=0, column=8, padx=5)
        Button(self.btn_frame, text="Cerrar",           command=self.cerrar_aplicacion).grid(row=0, column=9, padx=5)

        # Frame para la cola
        self.queue_frame = Frame(master)
        self.queue_frame.pack(fill="x", padx=10, pady=5)
        Label(self.queue_frame, text="Cola de PDFs:").pack(anchor="w")
        self.lst_queue = Listbox(self.queue_frame, height=4)
        self.lst_queue.pack(fill="x", side="left", expand=True)
        scrollbar = Scrollbar(self.queue_frame, orient=VERTICAL, command=self.lst_queue.yview)
        scrollbar.pack(side="right", fill="y")
        self.lst_queue.config(yscrollcommand=scrollbar.set)
        self.lst_queue.bind("<<ListboxSelect>>", self.on_select)

        # Canvas para mostrar el PDF
        self.canvas = Canvas(master, width=800, height=600)
        self.canvas.pack(fill="both", expand=True)

        self.master.after(100, self.verificar_midi)
        self._update_title()

    def _update_title(self):
        if self.doc:
            name = os.path.basename(self.pdf_queue[self.current_pdf_index])
            self.master.title(f"Visor V1.3 - {name} (Página {self.current_page+1}/{self.num_pages})")
        else:
            self.master.title("Visor V1.3")

    def _update_queue_view(self):
        self.lst_queue.delete(0, END)
        for i, path in enumerate(self.pdf_queue):
            name = os.path.basename(path)
            prefix = "→ " if i == self.current_pdf_index else "   "
            self.lst_queue.insert(END, prefix + name)
        if self.pdf_queue:
            self.lst_queue.see(self.current_pdf_index)

    def on_select(self, event):
        sel = event.widget.curselection()
        if not sel: return
        idx = sel[0]
        if idx == self.current_pdf_index:
            return
        self.current_pdf_index = idx
        # programa la recarga para dentro de unos milisegundos
        self.master.after(20, self._refresh_pdf)

    def _refresh_pdf(self):
        """Carga el PDF y muestra su página sin bloquear la UI."""
        self.cargar_pdf_actual()
        self.current_page = 0
        self.mostrar_pagina()

    def agregar_pdf(self):
        path = elegir_pdf()
        if path:
            self.pdf_queue.append(path)
            self._update_queue_view()
            messagebox.showinfo("PDF agregado", f"{os.path.basename(path)} en cola.")
            if not self.doc:
                self.cargar_pdf_actual()
                self.current_page = 0
                self.mostrar_pagina()

    def guardar_lista(self):
        if not self.pdf_queue:
            messagebox.showerror("Error", "La cola está vacía."); return
        path = filedialog.asksaveasfilename(
            title="Guardar lista de PDFs y vídeos",
            filetypes=[("Archivos VDP", "*.vdp")],
            defaultextension=".vdp"
        )
        if not path: return
        data = {"pdf_queue": self.pdf_queue, "video_map": self.video_map}
        try:
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
            messagebox.showinfo("Éxito", "Guardado correctamente.")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo guardar: {e}")

    def cargar_lista(self):
        path = filedialog.askopenfilename(
            title="Cargar lista de PDFs y vídeos",
            filetypes=[("Archivos VDP", "*.vdp")]
        )
        if not path: return
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            self.pdf_queue = data.get("pdf_queue", [])
            self.video_map   = data.get("video_map", {})
            self.current_pdf_index = 0
            self._update_queue_view()
            self.cargar_pdf_actual()
            self.current_page = 0
            self.mostrar_pagina()
            messagebox.showinfo("Éxito", "Cargado correctamente.")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo cargar: {e}")

    def agregar_video(self):
        if not self.pdf_queue:
            messagebox.showwarning("Error", "No hay PDF cargado."); return
        path = filedialog.askopenfilename(
            title="Seleccione el vídeo para este PDF",
            filetypes=[("Vídeos", "*.mp4;*.avi;*.mov"), ("Todos", "*.*")]
        )
        if not path: return
        pdf_path = self.pdf_queue[self.current_pdf_index]
        self.video_map[pdf_path] = path
        messagebox.showinfo("Vídeo agregado", f"Vídeo asignado a {os.path.basename(pdf_path)}")
        if self.video_visible:
            self._open_video_window(path)

    def toggle_video(self):
        """Muestra u oculta la ventana de vídeo fija 1920×1080."""
        if self.video_visible:
            if self.video_win and self.video_win.winfo_exists():
                self.video_win.withdraw()
            self.video_visible = False
        else:
            pdf = self.pdf_queue[self.current_pdf_index] if self.pdf_queue else None
            vid = self.video_map.get(pdf) if pdf else None
            if vid:
                self._open_video_window(vid)
                self.video_win.deiconify()
                self.video_visible = True
            else:
                messagebox.showinfo("Sin vídeo", "No hay vídeo asignado al PDF actual.")

    def _open_video_window(self, video_path):
        # Configura ventana fija y no redimensionable
        if not self.video_win or not self.video_win.winfo_exists():
            self.video_win = Toplevel(self.master)
            self.video_win.title("Vídeo asociado")
            self.video_win.geometry("1920x1080")
            self.video_win.resizable(False, False)
            self.video_label = Label(self.video_win)
            self.video_label.pack(fill="both", expand=True)
        else:
            self.video_win.deiconify()

        # (Re)inicia captura y cola
        if self.video_cap:
            self.video_cap.release()
        with self.frame_queue.mutex:
            self.frame_queue.queue.clear()
        self.video_cap = cv2.VideoCapture(video_path)
        # Inicia lector en hilo separado
        self.video_thread = threading.Thread(target=self._video_reader, daemon=True)
        self.video_thread.start()
        # Empieza la actualización UI
        self._play_video_frame()

    def _video_reader(self):
        """Lee frames y mantiene siempre el más reciente en frame_queue."""
        while self.video_visible and self.video_cap.isOpened():
            ret, frame = self.video_cap.read()
            if not ret:
                self.video_cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                continue
            if not self.frame_queue.full():
                self.frame_queue.put(frame)

    def _play_video_frame(self):
        """Toma el último frame disponible y actualiza el label."""
        if self.video_visible:
            try:
                frame = self.frame_queue.get_nowait()
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                # Ajustar al tamaño de la ventana de vídeo
                vw = self.video_win.winfo_width()
                vh = self.video_win.winfo_height()
                # A veces aún no está bien inicializado, comprueba un tamaño mínimo
                if vw < 10 or vh < 10:
                    vw, vh = 1920, 1080
                frame = cv2.resize(frame, (vw, vh), interpolation=cv2.INTER_AREA)
                img = Image.fromarray(frame)
                imgtk = ImageTk.PhotoImage(img)
                self.video_label.imgtk = imgtk
                self.video_label.config(image=imgtk)
            except queue.Empty:
                pass
            # programa siguiente actualización
            self.video_win.after(30, self._play_video_frame)
        else:
            # si ya no es visible, libera recursos
            if self.video_cap:
                self.video_cap.release()

    def cargar_pdf_actual(self):
        if not self.pdf_queue or self.current_pdf_index >= len(self.pdf_queue):
            return
        path = self.pdf_queue[self.current_pdf_index]
        try:
            self.doc = fitz.open(path)
            self.num_pages = len(self.doc)
            self.page_cache.clear()
            self._update_queue_view()
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo abrir el PDF:\n{e}")

    def pagina_anterior(self):
        if self.current_page >= 2:
            self.current_page -= 2
        elif self.current_page == 1:
            self.current_page = 0
        elif self.current_pdf_index > 0:
            self.current_pdf_index -= 1
            self.cargar_pdf_actual()
            self.current_page = (self.num_pages - 2) if self.num_pages % 2 == 0 else (self.num_pages - 1)
        self.mostrar_pagina()

    def pagina_siguiente(self):
        if self.current_page + 2 <= self.num_pages - 1:
            self.current_page += 2
        elif self.num_pages % 2 == 1 and self.current_page + 1 < self.num_pages:
            self.current_page += 1
        elif self.current_pdf_index < len(self.pdf_queue) - 1:
            self.current_pdf_index += 1
            self.cargar_pdf_actual()
            self.current_page = 0
        self.mostrar_pagina()

    def mostrar_pagina(self):
        if not self.doc: return
        pages = []
        for offset in (0, 1):
            idx = self.current_page + offset
            if 0 <= idx < self.num_pages:
                if idx in self.page_cache:
                    img = self.page_cache[idx]
                else:
                    page = self.doc.load_page(idx)
                    mat = fitz.Matrix(self.zoom, self.zoom)
                    pix = page.get_pixmap(matrix=mat)
                    arr = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, pix.n)
                    if pix.n == 4:
                        arr = arr[..., :3]
                    img = Image.fromarray(cv2.cvtColor(arr, cv2.COLOR_BGR2RGB))
                    self.page_cache[idx] = img
            else:
                img = Image.new("RGB", (800,1000), color=(211,211,211))
            pages.append(img)

        widths, heights = zip(*(i.size for i in pages))
        combined = Image.new("RGB", (sum(widths), max(heights)), "white")
        x = 0
        for i in pages:
            combined.paste(i, (x,0))
            x += i.width

        w, h = self.canvas.winfo_width(), self.canvas.winfo_height()
        img_resized = combined.resize((w,h), Image.LANCZOS)
        self.tk_img = ImageTk.PhotoImage(img_resized)
        self.canvas.delete("all")
        self.canvas.create_image(0,0,anchor="nw",image=self.tk_img)
        self._update_title()

        # si el vídeo está visible, recarga su fuente
        if self.video_visible:
            pdf = self.pdf_queue[self.current_pdf_index]
            vid = self.video_map.get(pdf)
            if vid:
                self._open_video_window(vid)

    def verificar_midi(self):
        if midi_input.poll():
            events = midi_input.read(10)
            for e in events:
                status, cc, val, _ = e[0]
                if status == 176 and cc == MIDI_PEDAL_CC and val >= THRESHOLD:
                    self.pagina_siguiente()
        self.master.after(100, self.verificar_midi)

    def cambiar_pedal(self):
        nuevo = detectar_cc()
        if nuevo is not None:
            global MIDI_PEDAL_CC
            MIDI_PEDAL_CC = nuevo

    def eliminar_pdf(self):
        if not self.pdf_queue:
            messagebox.showwarning("Error", "La cola está vacía."); return
        eliminado = self.pdf_queue.pop(self.current_pdf_index)
        messagebox.showinfo("PDF eliminado", f"{os.path.basename(eliminado)} removido.")
        if not self.pdf_queue:
            self.doc = None
            self.current_page = 0
            self.num_pages = 0
            self.page_cache.clear()
            self.canvas.delete("all")
            self._update_queue_view()
            self._update_title()
            return
        if self.current_pdf_index >= len(self.pdf_queue):
            self.current_pdf_index = len(self.pdf_queue)-1
        self.cargar_pdf_actual()
        self.current_page = 0
        self.mostrar_pagina()

    def cerrar_aplicacion(self):
        try: midi_input.close()
        except: pass
        try: pygame.midi.quit()
        except: pass
        if self.video_cap:
            self.video_cap.release()
        self.master.destroy()

if __name__ == "__main__":
    root = Tk()
    app = PartituraApp(root)
    root.mainloop()
