import fitz  # PyMuPDF
import cv2
import pygame.midi
import numpy as np
import json
import os
from tkinter import Tk, Button, Label, Canvas, Listbox, Scrollbar, filedialog, simpledialog, messagebox, VERTICAL, END
from PIL import Image, ImageTk
from tkinter import Frame

# === CONFIGURACIÓN GENERAL ===
THRESHOLD = 64

# === FUNCIONES PARA MANEJO DE ARCHIVOS ===
def elegir_pdf():
    return filedialog.askopenfilename(
        title="Seleccione el PDF de la partitura",
        filetypes=[("Archivos PDF", "*.pdf")]
    )

def guardar_lista(lista):
    path = filedialog.asksaveasfilename(
        title="Guardar lista de PDFs",
        filetypes=[("Archivos JSON", "*.json")],
        defaultextension=".json"
    )
    if path:
        with open(path, 'w') as f:
            json.dump(lista, f)

def cargar_lista():
    path = filedialog.askopenfilename(
        title="Cargar lista de PDFs",
        filetypes=[("Archivos JSON", "*.json")]
    )
    if path:
        with open(path, 'r') as f:
            return json.load(f)
    return []

# === FUNCIÓN PARA SELECCIONAR MIDI DESDE UNA LISTA ===
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

# === INTERFAZ PRINCIPAL ===
class PartituraApp:
    def __init__(self, master):
        self.master = master
        self.master.geometry("1000x800")
        self.pdf_queue = []
        self.current_pdf_index = 0
        self.doc = None
        self.current_page = 0
        self.num_pages = 0
        self.page_cache = {}
        self.zoom = 1

        # Frame de botones arriba
        self.btn_frame = Frame(master)
        self.btn_frame.pack(pady=5)
        Button(self.btn_frame, text="← Anterior", command=self.pagina_anterior).grid(row=0, column=0, padx=5)
        Button(self.btn_frame, text="Siguiente →", command=self.pagina_siguiente).grid(row=0, column=1, padx=5)
        Button(self.btn_frame, text="Agregar PDF a cola", command=self.agregar_pdf).grid(row=0, column=2, padx=5)
        Button(self.btn_frame, text="Guardar lista", command=self.guardar_lista).grid(row=0, column=3, padx=5)
        Button(self.btn_frame, text="Cargar lista", command=self.cargar_lista).grid(row=0, column=4, padx=5)
        Button(self.btn_frame, text="Cambiar pedal MIDI", command=self.cambiar_pedal).grid(row=0, column=5, padx=5)
        Button(self.btn_frame, text="Cerrar", command=self.cerrar_aplicacion).grid(row=0, column=6, padx=5)

        # Frame para mostrar la cola
        self.queue_frame = Frame(master)
        self.queue_frame.pack(fill="x", padx=10, pady=5)
        Label(self.queue_frame, text="Cola de PDFs:").pack(anchor="w")
        self.lst_queue = Listbox(self.queue_frame, height=4)
        self.lst_queue.pack(fill="x", side="left", expand=True)
        scrollbar = Scrollbar(self.queue_frame, orient=VERTICAL, command=self.lst_queue.yview)
        scrollbar.pack(side="right", fill="y")
        self.lst_queue.config(yscrollcommand=scrollbar.set)

        # Canvas de visualización
        self.canvas = Canvas(master, width=800, height=600)
        self.canvas.pack(fill="both", expand=True)

        self.master.after(100, self.verificar_midi)
        self._update_title()

    def _update_title(self):
        if self.doc:
            name = os.path.basename(self.pdf_queue[self.current_pdf_index])
            self.master.title(f"Visor de Partitura V.1.1 - {name} (Página {self.current_page+1}/{self.num_pages})")
        else:
            self.master.title("Visor de Partitura V.1.1")

    def _update_queue_view(self):
        self.lst_queue.delete(0, END)
        for i, path in enumerate(self.pdf_queue):
            name = os.path.basename(path)
            prefix = "→ " if i == self.current_pdf_index else "   "
            self.lst_queue.insert(END, prefix + name)

    def agregar_pdf(self):
        path = elegir_pdf()
        if path:
            self.pdf_queue.append(path)
            self._update_queue_view()
            messagebox.showinfo("PDF agregado", f"{path} se agregó a la cola.")
            if not self.doc:
                self.cargar_pdf_actual()

    def guardar_lista(self):
        if self.pdf_queue:
            guardar_lista(self.pdf_queue)
        else:
            messagebox.showerror("Error", "La cola de PDFs está vacía.")

    def cargar_lista(self):
        lista = cargar_lista()
        if lista:
            self.pdf_queue = lista
            self.current_pdf_index = 0
            self._update_queue_view()
            self.cargar_pdf_actual()

    def cargar_pdf_actual(self):
        if not self.pdf_queue or self.current_pdf_index >= len(self.pdf_queue):
            return
        path = self.pdf_queue[self.current_pdf_index]
        try:
            self.doc = fitz.open(path)
            self.num_pages = len(self.doc)
            self.current_page = 0
            self.page_cache.clear()
            self._update_queue_view()
            self.mostrar_pagina()
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo abrir el PDF:\n{e}")

    def mostrar_pagina(self):
        if not self.doc:
            return
        if self.current_page in self.page_cache:
            img_pil = self.page_cache[self.current_page]
        else:
            page = self.doc.load_page(self.current_page)
            mat = fitz.Matrix(self.zoom, self.zoom)
            pix = page.get_pixmap(matrix=mat)
            arr = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, pix.n)
            if pix.n == 4:
                arr = arr[:, :, :3]
            img_rgb = cv2.cvtColor(arr, cv2.COLOR_BGR2RGB)
            img_pil = Image.fromarray(img_rgb)
            self.page_cache[self.current_page] = img_pil
        w, h = self.canvas.winfo_width(), self.canvas.winfo_height()
        img_resized = img_pil.resize((w, h), Image.LANCZOS)
        self.tk_img = ImageTk.PhotoImage(img_resized)
        self.canvas.delete("all")
        self.canvas.create_image(0, 0, anchor="nw", image=self.tk_img)
        self._update_title()

    def pagina_anterior(self):
        if self.current_page > 0:
            self.current_page -= 1
        elif self.current_pdf_index > 0:
            self.current_pdf_index -= 1
            self.cargar_pdf_actual()
        self.mostrar_pagina()

    def pagina_siguiente(self):
        if self.current_page < self.num_pages - 1:
            self.current_page += 1
        elif self.current_pdf_index < len(self.pdf_queue) - 1:
            self.current_pdf_index += 1
            self.cargar_pdf_actual()
        self.mostrar_pagina()

    def verificar_midi(self):
        if midi_input.poll():
            events = midi_input.read(10)
            for event in events:
                status, cc_number, value, _ = event[0]
                if status == 176 and cc_number == MIDI_PEDAL_CC and value >= THRESHOLD:
                    self.pagina_siguiente()
        self.master.after(100, self.verificar_midi)

    def cambiar_pedal(self):
        nuevo_cc = detectar_cc()
        if nuevo_cc is not None:
            global MIDI_PEDAL_CC
            MIDI_PEDAL_CC = nuevo_cc

    def cerrar_aplicacion(self):
        try:
            midi_input.close()
        except:
            pass
        pygame.midi.quit()
        self.master.destroy()

# === INICIAR APP ===
root = Tk()
app = PartituraApp(root)
root.mainloop()
# === FINALIZACIÓN ===
midi_input.close()
pygame.midi.quit()
