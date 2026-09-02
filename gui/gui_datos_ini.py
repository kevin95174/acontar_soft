import tkinter as tk
import os
import configparser
from PIL import Image, ImageTk
from tkinter import filedialog
from tkinter import messagebox as mb
from tkinter import ttk, PhotoImage
from db.query import datos_iniciales, actualizar_datos

class Window_datos_ini(tk.Toplevel):
    def __init__(self, root=None):
        super().__init__(root)
        self.title("Configuración Inicial")
        self.geometry("600x680")
        self.resizable(False, False)
        
        # Icono con manejo de excepción para evitar fallos si no existe la ruta
        if os.path.exists('./img/favicon.ico'):
            self.iconbitmap('./img/favicon.ico')
            
        self.config_path = 'config.ini'
        self.config = configparser.ConfigParser()
        self.img_label_path = None
        self.img_ficha_path = None

        # Configurar estilos visuales globales
        self.setup_styles()
        
        self.widgets()
        self.load_config()
        self.cargar_imagen_guardada()
        self.mostrar_datos()

    def setup_styles(self):
        """Aplica un tema moderno y personaliza la apariencia de los componentes TTK."""
        self.style = ttk.Style(self)
        
        # Utilizar un tema nativo/limpio si está disponible
        available_themes = self.style.theme_names()
        if "clam" in available_themes:
            self.style.theme_use("clam")

        # Paleta de colores
        COLOR_BG = "#F5F6F8"
        COLOR_PRIMARY = "#2563EB"      # Azul principal
        COLOR_PRIMARY_HOVER = "#1D4ED8"
        COLOR_TEXT = "#1F2937"

        self.configure(bg=COLOR_BG)

        # Configuración de estilos para TTK
        self.style.configure(".", background=COLOR_BG, foreground=COLOR_TEXT, font=("Segoe UI", 9))
        self.style.configure("TLabelframe", background=COLOR_BG, padding=12)
        self.style.configure("TLabelframe.Label", font=("Segoe UI", 10, "bold"), foreground=COLOR_PRIMARY, background=COLOR_BG)
        
        self.style.configure("TLabel", background=COLOR_BG, font=("Segoe UI", 9))
        self.style.configure("TEntry", padding=4)
        self.style.configure("TCombobox", padding=4)

        # Botón Principal
        self.style.configure("Primary.TButton", font=("Segoe UI", 10, "bold"), background=COLOR_PRIMARY, foreground="white", padding=6)
        self.style.map("Primary.TButton", background=[("active", COLOR_PRIMARY_HOVER)])

        # Botón Secundario
        self.style.configure("Secondary.TButton", font=("Segoe UI", 9), padding=4)

    def widgets(self):
        # Contenedor Principal con Margen
        main_container = ttk.Frame(self, padding="20")
        main_container.pack(fill='both', expand=True)

        # Variables de control
        self.ent = tk.StringVar()
        self.per = tk.StringVar()
        self.fec = tk.StringVar()

        # ==========================================
        # SECCIÓN 1: DATOS GENERALES
        # ==========================================
        sec_datos = ttk.LabelFrame(main_container, text="Datos del Sistema")
        sec_datos.pack(fill="x", pady=(0, 15))
        sec_datos.columnconfigure(1, weight=1)  # Hace que las entradas de texto se expandan

        ttk.Label(sec_datos, text="Entidad:").grid(row=0, column=0, sticky="w", pady=5, padx=5)
        ttk.Entry(sec_datos, textvariable=self.ent).grid(row=0, column=1, sticky="ew", pady=5, padx=5)

        ttk.Label(sec_datos, text="Periodo:").grid(row=1, column=0, sticky="w", pady=5, padx=5)
        cbxPer = ttk.Combobox(sec_datos, values=[2020, 2021, 2022, 2023, 2024, 2025, 2026], textvariable=self.per, state="readonly")
        cbxPer.grid(row=1, column=1, sticky="ew", pady=5, padx=5)

        ttk.Label(sec_datos, text="Fecha de Inventario:").grid(row=2, column=0, sticky="w", pady=5, padx=5)
        ttk.Entry(sec_datos, textvariable=self.fec).grid(row=2, column=1, sticky="ew", pady=5, padx=5)

        # ==========================================
        # SECCIÓN 2: LOGOTIPOS E IMÁGENES
        # ==========================================
        sec_logos = ttk.LabelFrame(main_container, text="Logotipos")
        sec_logos.pack(fill="both", expand=True, pady=(0, 15))
        sec_logos.columnconfigure((0, 1), weight=1)

        # Sub-contenedor para Logo Etiquetas
        frame_logo_label = ttk.Frame(sec_logos)
        frame_logo_label.grid(row=0, column=0, padx=10, pady=5, sticky="nsew")
        
        ttk.Label(frame_logo_label, text="Logo para Etiquetas", font=("Segoe UI", 9, "italic")).pack(anchor="center", pady=(0, 5))
        
        # Marco contenedor de previsualización (fijamos tamaño fijo para que no 'salte' el layout)
        preview_box1 = tk.Frame(frame_logo_label, width=160, height=120, bg="#E5E7EB", highlightbackground="#D1D5DB", highlightthickness=1)
        preview_box1.pack_propagate(False)
        preview_box1.pack(pady=5)
        
        self.img_label = tk.Label(preview_box1, bg="#E5E7EB")
        self.img_label.pack(fill="both", expand=True)

        ttk.Button(frame_logo_label, text="Seleccionar Imagen", style="Secondary.TButton", command=lambda: self.abrir_logo(1)).pack(fill="x", pady=5)

        # Sub-contenedor para Logo Ficha
        frame_logo_ficha = ttk.Frame(sec_logos)
        frame_logo_ficha.grid(row=0, column=1, padx=10, pady=5, sticky="nsew")

        ttk.Label(frame_logo_ficha, text="Logo para Ficha", font=("Segoe UI", 9, "italic")).pack(anchor="center", pady=(0, 5))

        preview_box2 = tk.Frame(frame_logo_ficha, width=160, height=120, bg="#E5E7EB", highlightbackground="#D1D5DB", highlightthickness=1)
        preview_box2.pack_propagate(False)
        preview_box2.pack(pady=5)

        self.img_ficha = tk.Label(preview_box2, bg="#E5E7EB")
        self.img_ficha.pack(fill="both", expand=True)

        ttk.Button(frame_logo_ficha, text="Seleccionar Imagen", style="Secondary.TButton", command=lambda: self.abrir_logo(2)).pack(fill="x", pady=5)

        # ==========================================
        # SECCIÓN 3: BOTÓN DE ACCIÓN PRINCIPAL
        # ==========================================
        btnCon = ttk.Button(main_container, text="Guardar Configuración", style="Primary.TButton", command=self.actualizar)
        btnCon.pack(fill="x", ipady=3)

    def abrir_logo(self, valor):
        filepath = filedialog.askopenfilename(filetypes=[("Archivos de imagen", "*.png *.jpg *.jpeg *.gif")])
        if filepath:
            if valor == 1:
                self.img_label_path = filepath
                image_widget = self.img_label
            elif valor == 2:
                self.img_ficha_path = filepath
                image_widget = self.img_ficha

            self.save_config()
            self.renderizar_imagen(filepath, image_widget)
            self.focus_set()

    def renderizar_imagen(self, ruta_imagen, widget_label):
        """Redimensiona y asigna una imagen a un widget Label manteniendo la relación de aspecto."""
        if os.path.exists(ruta_imagen):
            image = Image.open(ruta_imagen)
            image.thumbnail((150, 110))  # Ajuste al área fijada en la UI
            photo = ImageTk.PhotoImage(image)
            widget_label.config(image=photo)
            widget_label.photo = photo  # Evita que el Garbage Collector borre la referencia

    def load_config(self):
        if os.path.exists(self.config_path):
            self.config.read(self.config_path)
            if 'Settings' in self.config:
                self.img_label_path = self.config['Settings'].get('img_label_path', '')
                self.img_ficha_path = self.config['Settings'].get('img_ficha_path', '')

    def save_config(self):
        if not self.config.has_section('Settings'):
            self.config.add_section('Settings')
        self.config.set('Settings', 'img_label_path', self.img_label_path or '')
        self.config.set('Settings', 'img_ficha_path', self.img_ficha_path or '')
        self.config.set('Settings', 'entidad', self.ent.get())
        self.config.set('Settings', 'periodo', self.per.get())
        with open(self.config_path, 'w') as config_file:
            self.config.write(config_file)

    def cargar_imagen_guardada(self):
        if self.img_label_path:
            self.renderizar_imagen(self.img_label_path, self.img_label)

        if self.img_ficha_path:
            self.renderizar_imagen(self.img_ficha_path, self.img_ficha)

    def mostrar_datos(self):
        try:
            r = datos_iniciales()
            if r and len(r) >= 4:
                self.ent.set(r[1])
                self.per.set(r[2])
                self.fec.set(r[3])
        except Exception as e:
            mb.showwarning("Advertencia", f"No se pudieron cargar los datos iniciales: {e}")

    def actualizar(self):
        lista = [self.ent.get(), self.per.get(), self.fec.get()]
        try:
            actualizar_datos(1, lista)
            self.save_config()
            mb.showinfo(title="Éxito", message="¡Configuración actualizada con éxito!")
        except Exception as e:
            mb.showerror(title="Error", message=f"Ocurrió un error al actualizar: {str(e)}")
        finally:
            self.focus_set()