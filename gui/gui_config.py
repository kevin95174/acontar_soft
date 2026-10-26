import os
import tkinter as tk
import configparser
from tkinter import ttk, PhotoImage, filedialog
from tkinter import messagebox as mb
from PIL import Image, ImageTk

from db.query import (
    mostrar_personal,
    mostrar_datos_bienes,
    delete_table,
    exportar_data,
    datos_iniciales,
    actualizar_datos,
)
from data.config_db import exportar_inv, crear, importar
from data.exp_excel import exportar_excel
from utils.helpers import resource_path


class Window_config(tk.Toplevel):
    def __init__(self, root=None):
        super().__init__(root)
        self.root = root
        self.title("Configuración del Sistema e Intercambio de Datos - AEC S.A.C.")
        self.geometry("980x680")
        self.minsize(880, 580)
        self.configure(bg="#f8fafc")

        # Configurar icono de ventana
        icon_path = resource_path(os.path.join("img", "favicon.ico"))
        if os.path.exists(icon_path):
            try:
                self.iconbitmap(icon_path)
            except Exception:
                pass

        self.config_path = "config.ini"
        self.config = configparser.ConfigParser()
        self.img_label_path = None
        self.img_ficha_path = None

        # Cargar iconos de forma segura
        self.iconoSubir = self._cargar_icono("img/subir.png")
        self.iconoBajar = self._cargar_icono("img/bajar.png")
        self.iconoBorrar = self._cargar_icono("img/borrar.png")
        self.iconoCSV = self._cargar_icono("img/csv.png")
        self.iconoSelec = self._cargar_icono("img/seleccion.png")
        self.iconoExcel = self._cargar_icono("img/excel.png")
        self.iconoLupa = self._cargar_icono("img/lupa.png")

        # Variables de estado
        self.ent = tk.StringVar()
        self.per = tk.StringVar()
        self.fec = tk.StringVar()
        self.nbase = tk.StringVar()
        self.narch = tk.StringVar()
        self.selecIm = tk.StringVar(value="bienes")
        self.selec = tk.StringVar(value="bienes")
        self.lbl_tree_info_var = tk.StringVar(value="Listo")

        # Estilos TTK
        self._configurar_estilos()

        # Contenedor principal con Notebook
        self._crear_interfaz()

        # Cargar datos iniciales
        self.load_config()
        self.mostrar_datos()
        self.cargar_imagen_guardada()
        self.recargar_arbol()

        # Centrar ventana respecto al padre o la pantalla
        self._centrar_ventana()

    def _cargar_icono(self, rel_path):
        """Carga un PhotoImage usando resource_path de forma segura."""
        full_path = resource_path(rel_path)
        if os.path.exists(full_path):
            try:
                return PhotoImage(file=full_path)
            except Exception:
                return None
        return None

    def _configurar_estilos(self):
        style = ttk.Style(self)

        # Notebook
        style.configure("Config.TNotebook", background="#f8fafc", borderwidth=0)
        style.configure(
            "Config.TNotebook.Tab",
            font=("Segoe UI", 10, "bold"),
            padding=(18, 9),
            background="#e2e8f0",
            foreground="#334155"
        )
        style.map(
            "Config.TNotebook.Tab",
            background=[("selected", "#ffffff")],
            foreground=[("selected", "#0f172a")]
        )

        # Labels generales
        style.configure(
            "Header.TLabel",
            background="#ffffff",
            foreground="#0f172a",
            font=("Segoe UI", 12, "bold")
        )
        style.configure(
            "SubHeader.TLabel",
            background="#ffffff",
            foreground="#64748b",
            font=("Segoe UI", 9)
        )
        style.configure(
            "Field.TLabel",
            background="#ffffff",
            foreground="#334155",
            font=("Segoe UI", 9, "bold")
        )
        style.configure(
            "Card.TLabelframe",
            background="#ffffff",
            foreground="#1e293b",
            bordercolor="#e2e8f0",
            borderwidth=1,
            relief="solid"
        )
        style.configure(
            "Card.TLabelframe.Label",
            background="#ffffff",
            foreground="#0f172a",
            font=("Segoe UI", 10, "bold")
        )

        # Botones de Acción
        style.configure(
            "Primary.TButton",
            font=("Segoe UI", 9, "bold"),
            padding=(10, 6)
        )
        style.configure(
            "Success.TButton",
            font=("Segoe UI", 9, "bold"),
            padding=(10, 6)
        )
        style.configure(
            "Danger.TButton",
            font=("Segoe UI", 9, "bold"),
            padding=(10, 6)
        )
        style.configure(
            "Action.TButton",
            font=("Segoe UI", 9),
            padding=(8, 5)
        )

        # Treeview
        style.configure(
            "Custom.Treeview",
            font=("Segoe UI", 9),
            rowheight=26,
            background="#ffffff",
            fieldbackground="#ffffff",
            bordercolor="#e2e8f0",
            borderwidth=1
        )
        style.configure(
            "Custom.Treeview.Heading",
            font=("Segoe UI", 9, "bold"),
            background="#f1f5f9",
            foreground="#1e293b",
            padding=(6, 6)
        )
        style.map("Custom.Treeview", background=[("selected", "#2563eb")], foreground=[("selected", "#ffffff")])

    def _centrar_ventana(self):
        self.update_idletasks()
        ancho = self.winfo_width()
        alto = self.winfo_height()
        if self.root:
            rx = self.root.winfo_x()
            ry = self.root.winfo_y()
            rw = self.root.winfo_width()
            rh = self.root.winfo_height()
            x = rx + (rw // 2) - (ancho // 2)
            y = ry + (rh // 2) - (alto // 2)
        else:
            x = (self.winfo_screenwidth() // 2) - (ancho // 2)
            y = (self.winfo_screenheight() // 2) - (alto // 2)
        self.geometry(f"+{max(0, x)}+{max(0, y)}")

    def _crear_interfaz(self):
        # Notebook principal
        self.nbk = ttk.Notebook(self, style="Config.TNotebook")
        self.tab1 = tk.Frame(self.nbk, bg="#f8fafc")
        self.tab2 = tk.Frame(self.nbk, bg="#f8fafc")
        self.tab3 = tk.Frame(self.nbk, bg="#f8fafc")

        self.nbk.add(self.tab1, text="  ⚙️ Datos Generales  ")
        self.nbk.add(self.tab2, text="  📥 Importar CSV  ")
        self.nbk.add(self.tab3, text="  📤 Exportar Datos  ")
        self.nbk.pack(fill="both", expand=True, padx=12, pady=10)

        self.tab1_()
        self.tab2_()
        self.tab3_()

    # -------------------------------------------------------------
    # TAB 1: DATOS GENERALES Y LOGOS
    # -------------------------------------------------------------
    def tab1_(self):
        container = tk.Frame(self.tab1, bg="#f8fafc")
        container.pack(fill="both", expand=True, padx=15, pady=15)
        container.columnconfigure(0, weight=1)
        container.columnconfigure(1, weight=1)
        container.rowconfigure(0, weight=1)

        # ---- Tarjeta Izquierda: Información de la Entidad ----
        card_datos = ttk.LabelFrame(container, text=" Información de la Entidad ", style="Card.TLabelframe", padding=(20, 16))
        card_datos.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        card_datos.columnconfigure(1, weight=1)

        desc_lbl = ttk.Label(
            card_datos,
            text="Configura los datos base de la institución que se reflejarán\nen las actas, fichas y reportes impresos.",
            style="SubHeader.TLabel",
            justify="left"
        )
        desc_lbl.grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 18))

        # Campo: Entidad
        ttk.Label(card_datos, text="Nombre de Entidad:", style="Field.TLabel").grid(row=1, column=0, sticky="w", pady=8)
        etrEnt = ttk.Entry(card_datos, textvariable=self.ent, font=("Segoe UI", 10))
        etrEnt.grid(row=1, column=1, sticky="ew", pady=8, padx=(10, 0))

        # Campo: Periodo
        ttk.Label(card_datos, text="Periodo / Ejercicio:", style="Field.TLabel").grid(row=2, column=0, sticky="w", pady=8)
        cbxPer = ttk.Combobox(
            card_datos,
            values=[str(year) for year in range(2020, 2031)],
            textvariable=self.per,
            state="readonly",
            font=("Segoe UI", 10)
        )
        cbxPer.grid(row=2, column=1, sticky="ew", pady=8, padx=(10, 0))

        # Campo: Fecha
        ttk.Label(card_datos, text="Fecha de Inventario:", style="Field.TLabel").grid(row=3, column=0, sticky="w", pady=8)
        etrFec = ttk.Entry(card_datos, textvariable=self.fec, font=("Segoe UI", 10))
        etrFec.grid(row=3, column=1, sticky="ew", pady=8, padx=(10, 0))

        # Espaciador vertical
        card_datos.rowconfigure(4, weight=1)

        # Botón Guardar Datos
        btn_box = tk.Frame(card_datos, bg="#ffffff")
        btn_box.grid(row=5, column=0, columnspan=2, sticky="ew", pady=(15, 5))
        btn_box.columnconfigure(0, weight=1)

        btnCon = ttk.Button(
            btn_box,
            text="💾 Guardar Cambios de Entidad",
            style="Primary.TButton",
            command=self.actualizar
        )
        btnCon.pack(fill="x", ipady=3)

        # ---- Tarjeta Derecha: Logotipos Institucionales ----
        card_logos = ttk.LabelFrame(container, text=" Logotipos Institucionales ", style="Card.TLabelframe", padding=(20, 16))
        card_logos.grid(row=0, column=1, sticky="nsew", padx=(10, 0))
        card_logos.columnconfigure(0, weight=1)
        card_logos.columnconfigure(1, weight=1)

        desc_logos = ttk.Label(
            card_logos,
            text="Selecciona las imágenes de logo que se utilizarán\nen las etiquetas de código de barras y fichas de inventario.",
            style="SubHeader.TLabel",
            justify="left"
        )
        desc_logos.grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 14))

        # Sub-tarjeta: Logo Etiquetas
        box_etiqueta = tk.LabelFrame(
            card_logos,
            text=" Logo para Etiquetas de Código de Barras ",
            bg="#ffffff",
            fg="#334155",
            font=("Segoe UI", 9, "bold"),
            relief="groove",
            padx=10,
            pady=10
        )
        box_etiqueta.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(0, 12))
        box_etiqueta.columnconfigure(0, weight=1)

        # Contenedor de preview con borde
        preview_frame1 = tk.Frame(box_etiqueta, bg="#f1f5f9", width=200, height=80, relief="solid", bd=1)
        preview_frame1.pack(pady=5)
        preview_frame1.pack_propagate(False)

        self.img_label = tk.Label(preview_frame1, text="[ Sin logo cargado ]", bg="#f1f5f9", fg="#94a3b8", font=("Segoe UI", 8))
        self.img_label.pack(expand=True, fill="both")

        btnLEt = ttk.Button(
            box_etiqueta,
            text="📂 Seleccionar Logo Etiquetas...",
            style="Action.TButton",
            command=lambda: self.abrir_logo(1)
        )
        btnLEt.pack(pady=(4, 0))

        # Sub-tarjeta: Logo Ficha
        box_ficha = tk.LabelFrame(
            card_logos,
            text=" Logo para Ficha Técnica de Inventario ",
            bg="#ffffff",
            fg="#334155",
            font=("Segoe UI", 9, "bold"),
            relief="groove",
            padx=10,
            pady=10
        )
        box_ficha.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(6, 0))
        box_ficha.columnconfigure(0, weight=1)

        preview_frame2 = tk.Frame(box_ficha, bg="#f1f5f9", width=200, height=80, relief="solid", bd=1)
        preview_frame2.pack(pady=5)
        preview_frame2.pack_propagate(False)

        self.img_ficha = tk.Label(preview_frame2, text="[ Sin logo cargado ]", bg="#f1f5f9", fg="#94a3b8", font=("Segoe UI", 8))
        self.img_ficha.pack(expand=True, fill="both")

        btnLFi = ttk.Button(
            box_ficha,
            text="📂 Seleccionar Logo Ficha...",
            style="Action.TButton",
            command=lambda: self.abrir_logo(2)
        )
        btnLFi.pack(pady=(4, 0))

    def abrir_logo(self, valor):
        filepath = filedialog.askopenfilename(
            title="Seleccionar imagen de logotipo",
            filetypes=[("Archivos de imagen", "*.png *.jpg *.jpeg *.gif *.bmp"), ("Todos los archivos", "*.*")]
        )
        if filepath:
            if valor == 1:
                self.img_label_path = filepath
                image_widget = self.img_label
            elif valor == 2:
                self.img_ficha_path = filepath
                image_widget = self.img_ficha

            self.save_config()
            try:
                image = Image.open(filepath)
                image.thumbnail((190, 75))
                photo = ImageTk.PhotoImage(image)
                image_widget.config(image=photo, text="", bg="#ffffff")
                image_widget.photo = photo
                mb.showinfo("Logotipo Actualizado", "El logotipo se ha guardado correctamente.", parent=self)
            except Exception as e:
                mb.showerror("Error de Imagen", f"No se pudo cargar la imagen: {e}", parent=self)
            self.focus_set()

    def load_config(self):
        if os.path.exists(self.config_path):
            try:
                self.config.read(self.config_path)
                if 'Settings' in self.config:
                    self.img_label_path = self.config['Settings'].get('img_label_path', '')
                    self.img_ficha_path = self.config['Settings'].get('img_ficha_path', '')
            except Exception:
                pass

    def save_config(self):
        if not self.config.has_section('Settings'):
            self.config.add_section('Settings')
        self.config.set('Settings', 'img_label_path', self.img_label_path or '')
        self.config.set('Settings', 'img_ficha_path', self.img_ficha_path or '')
        self.config.set('Settings', 'entidad', self.ent.get())
        self.config.set('Settings', 'periodo', self.per.get())
        try:
            with open(self.config_path, 'w', encoding='utf-8') as config_file:
                self.config.write(config_file)
        except Exception:
            pass

    def cargar_imagen_guardada(self):
        if self.img_label_path and os.path.exists(self.img_label_path):
            try:
                image = Image.open(self.img_label_path)
                image.thumbnail((190, 75))
                self.photo = ImageTk.PhotoImage(image)
                self.img_label.config(image=self.photo, text="", bg="#ffffff")
            except Exception:
                pass

        if self.img_ficha_path and os.path.exists(self.img_ficha_path):
            try:
                image = Image.open(self.img_ficha_path)
                image.thumbnail((190, 75))
                self.photo2 = ImageTk.PhotoImage(image)
                self.img_ficha.config(image=self.photo2, text="", bg="#ffffff")
            except Exception:
                pass

    def mostrar_datos(self):
        try:
            r = datos_iniciales()
            if r and len(r) > 1:
                self.ent.set(r[1] or "")
                if len(r) > 2 and r[2]:
                    self.per.set(r[2])
                if len(r) > 3 and r[3]:
                    self.fec.set(r[3])
        except Exception:
            pass

    def actualizar(self):
        lista = [self.ent.get(), self.per.get(), self.fec.get()]
        try:
            actualizar_datos(1, lista)
            self.save_config()
            mb.showinfo(title="Acontar S.A.C.", message="¡Datos actualizados con éxito!", parent=self)
        except Exception as e:
            mb.showerror(title="Error", message=f"Ocurrió un error al actualizar: {str(e)}", parent=self)
        finally:
            self.focus_set()

    # -------------------------------------------------------------
    # TAB 2: IMPORTACIÓN DE DATOS CSV
    # -------------------------------------------------------------
    def tab2_(self):
        container = tk.Frame(self.tab2, bg="#f8fafc")
        container.pack(fill="both", expand=True, padx=15, pady=12)

        # ---- Panel Superior: Opciones de Importación ----
        card_ctrl = ttk.LabelFrame(container, text=" Opciones de Importación de Datos ", style="Card.TLabelframe", padding=(15, 12))
        card_ctrl.pack(fill="x", pady=(0, 10))

        # Fila 1: Selección de Tabla y Archivo
        f1 = tk.Frame(card_ctrl, bg="#ffffff")
        f1.pack(fill="x", pady=(0, 8))

        ttk.Label(f1, text="Tabla destino:", style="Field.TLabel").pack(side="left", padx=(0, 6))
        self.cbx_import_table = ttk.Combobox(
            f1,
            textvariable=self.selecIm,
            state="readonly",
            values=["bienes", "personal", "bienes afectados"],
            width=18,
            font=("Segoe UI", 9)
        )
        self.cbx_import_table.pack(side="left", padx=(0, 15))
        self.cbx_import_table.bind("<<ComboboxSelected>>", lambda e: self.recargar_arbol())

        ttk.Label(f1, text="Archivo CSV:", style="Field.TLabel").pack(side="left", padx=(0, 6))
        self.etr_archivo = ttk.Entry(f1, textvariable=self.narch, font=("Segoe UI", 9))
        self.etr_archivo.pack(side="left", fill="x", expand=True, padx=(0, 8))

        btnSeinv = ttk.Button(
            f1,
            text="Examinar...",
            image=self.iconoSelec if self.iconoSelec else None,
            compound="left",
            style="Action.TButton",
            command=self.select_file
        )
        btnSeinv.pack(side="left")

        # Fila 2: Botones de Acción
        f2 = tk.Frame(card_ctrl, bg="#ffffff")
        f2.pack(fill="x")

        # Botón Importar (Destacado)
        btnExinv = ttk.Button(
            f2,
            text="  Importar Datos a la Base de Datos",
            image=self.iconoSubir if self.iconoSubir else None,
            compound="left",
            style="Success.TButton",
            command=self.importar_bd
        )
        btnExinv.pack(side="left", padx=(0, 10))

        # Botón Recargar / Vista previa
        btnRecargar = ttk.Button(
            f2,
            text="  Refrescar Registros",
            image=self.iconoLupa if self.iconoLupa else None,
            compound="left",
            style="Action.TButton",
            command=self.recargar_arbol
        )
        btnRecargar.pack(side="left", padx=(0, 10))

        # Botón Borrar (Peligro)
        btnBorra = ttk.Button(
            f2,
            text="  Vaciar Tabla Seleccionada",
            image=self.iconoBorrar if self.iconoBorrar else None,
            compound="left",
            style="Danger.TButton",
            command=self.borrar_datos
        )
        btnBorra.pack(side="right")

        # ---- Panel Inferior: Treeview con Registros ----
        card_table = ttk.LabelFrame(container, text=" Registros en Base de Datos ", style="Card.TLabelframe", padding=(10, 8))
        card_table.pack(fill="both", expand=True)

        # Barra de estado superior del árbol
        top_bar = tk.Frame(card_table, bg="#ffffff")
        top_bar.pack(fill="x", pady=(0, 5))
        self.lbl_info = ttk.Label(top_bar, textvariable=self.lbl_tree_info_var, font=("Segoe UI", 9, "italic"), foreground="#475569")
        self.lbl_info.pack(side="left")

        self.tree_container = tk.Frame(card_table, bg="#ffffff")
        self.tree_container.pack(fill="both", expand=True)
        self.tree_container.rowconfigure(0, weight=1)
        self.tree_container.columnconfigure(0, weight=1)

        self.tree = None
        self.scrollbarV = None
        self.scrollbarH = None

    def recargar_arbol(self):
        """Reconstruye el Treeview y carga los registros según la tabla seleccionada."""
        tabla = self.selecIm.get()

        # Limpiar contenedor anterior
        for widget in self.tree_container.winfo_children():
            widget.destroy()

        if tabla == "bienes":
            columnas = [
                "CodInt", "ActaAnt", "Inv", "CodPat", "DenBien", "NroDocAdq", "FechAdq",
                "ValAdq", "DepAcum", "ValNeto", "CtaCont", "DenCta", "Estado", "Marca", "Modelo",
                "Tipo", "Color", "Serie", "Dimension", "Placa", "NroMotor", "NroChasis", "Matricula",
                "AñoFab", "Nota", "Obs", "FechInv", "Otros", "Situacion"
            ]
        else:
            columnas = [
                "Acta", "dep", "prov", "dist", "local", "area", "oficina",
                "dni", "nombre", "apellidoPat", "apellidoMat"
            ]

        self.tree = ttk.Treeview(
            self.tree_container,
            columns=columnas,
            show="headings",
            style="Custom.Treeview",
            selectmode="extended"
        )

        for col in columnas:
            self.tree.heading(col, text=col)
            ancho = 140 if col in ["DenBien", "DenCta", "nombre", "apellidoPat"] else 95
            self.tree.column(col, width=ancho, minwidth=60, stretch=False)

        # Configurar colores alternados en filas
        self.tree.tag_configure("evenrow", background="#ffffff")
        self.tree.tag_configure("oddrow", background="#f8fafc")

        self.scrollbarV = ttk.Scrollbar(self.tree_container, orient=tk.VERTICAL, command=self.tree.yview)
        self.scrollbarH = ttk.Scrollbar(self.tree_container, orient=tk.HORIZONTAL, command=self.tree.xview)
        self.tree.configure(yscroll=self.scrollbarV.set, xscroll=self.scrollbarH.set)

        self.tree.grid(column=0, row=0, sticky="nsew")
        self.scrollbarV.grid(column=1, row=0, sticky="ns")
        self.scrollbarH.grid(column=0, row=1, sticky="ew")

        # Cargar datos desde la base de datos
        try:
            if tabla == "bienes":
                datos = mostrar_datos_bienes()
            else:
                datos = mostrar_personal()

            self.show_data(datos)
            total = len(datos) if datos else 0
            self.lbl_tree_info_var.set(f"📊 Tabla: '{tabla}' | Total de registros cargados: {total}")
        except Exception as e:
            self.lbl_tree_info_var.set(f"⚠️ Error al consultar datos: {e}")

    def show_data(self, j):
        if not self.tree:
            return
        for item in self.tree.get_children():
            self.tree.delete(item)
        if j:
            for idx, b in enumerate(j):
                tag = "evenrow" if idx % 2 == 0 else "oddrow"
                self.tree.insert('', tk.END, values=b, tags=(tag,))

    def select_file(self):
        filetypes = (
            ('Archivos CSV (*.csv)', '*.csv'),
            ('Todos los archivos (*.*)', '*.*')
        )
        initialdir = getattr(self, 'last_folder', '/')
        filename = filedialog.askopenfilename(
            title='Seleccionar archivo CSV para importar',
            initialdir=initialdir,
            filetypes=filetypes
        )
        if filename:
            self.last_folder = os.path.dirname(filename)
            self.narch.set(filename)
            self.focus_set()
        return filename

    def importar_bd(self):
        tabla = self.selecIm.get()
        archivo = self.narch.get()

        if not archivo or not os.path.exists(archivo):
            mb.showwarning("Archivo no seleccionado", "Por favor selecciona un archivo CSV válido antes de importar.", parent=self)
            return

        try:
            if tabla == "personal":
                importar(archivo, 1)
            else:
                importar(archivo, 2)

            self.recargar_arbol()
            mb.showinfo("Importación Exitosa", f"Los datos de '{tabla}' se importaron correctamente a la base de datos.", parent=self)
        except Exception as e:
            mb.showerror("Error de Importación", f"Ocurrió un error al importar los datos:\n{str(e)}", parent=self)
        finally:
            self.focus_set()

    def borrar_datos(self):
        tabla = self.selecIm.get()
        confirmacion = mb.askyesno(
            "¡Atención - Eliminar Datos!",
            f"¿Estás completamente seguro de que deseas eliminar TODOS los registros de la tabla '{tabla}'?\n\nEsta acción no se puede deshacer.",
            icon='warning',
            parent=self
        )
        if confirmacion:
            try:
                delete_table(tabla)
                self.recargar_arbol()
                mb.showinfo("Datos Eliminados", f"Se han eliminado todos los registros de la tabla '{tabla}'.", parent=self)
            except Exception as e:
                mb.showerror("Error", f"Ocurrió un error al borrar los registros: {e}", parent=self)
            finally:
                self.focus_set()

    # Compatibilidad con llamadas heredadas
    def tree_view(self):
        self.recargar_arbol()

    def test(self):
        self.recargar_arbol()

    def crear_bd(self):
        r = self.nbase.get()
        crear(r)

    # -------------------------------------------------------------
    # TAB 3: EXPORTACIÓN DE DATOS
    # -------------------------------------------------------------
    def tab3_(self):
        container = tk.Frame(self.tab3, bg="#f8fafc")
        container.pack(fill="both", expand=True, padx=20, pady=20)

        # Tarjeta de selección de módulo
        card_sel = ttk.LabelFrame(container, text=" Selección de Datos a Exportar ", style="Card.TLabelframe", padding=(20, 16))
        card_sel.pack(fill="x", pady=(0, 20))

        row_sel = tk.Frame(card_sel, bg="#ffffff")
        row_sel.pack(fill="x")

        ttk.Label(row_sel, text="Selecciona el módulo o tabla a exportar:", style="Field.TLabel").pack(side="left", padx=(0, 12))
        cbx_export = ttk.Combobox(
            row_sel,
            textvariable=self.selec,
            state="readonly",
            values=["bienes", "personal", "sobrantes", "users"],
            width=20,
            font=("Segoe UI", 10)
        )
        cbx_export.pack(side="left")

        # Contenedor de las dos tarjetas de exportación (CSV y Excel)
        cards_grid = tk.Frame(container, bg="#f8fafc")
        cards_grid.pack(fill="both", expand=True)
        cards_grid.columnconfigure(0, weight=1)
        cards_grid.columnconfigure(1, weight=1)

        # ---- Card 1: Exportar a CSV ----
        card_csv = ttk.LabelFrame(cards_grid, text=" Exportación en Formato CSV ", style="Card.TLabelframe", padding=(20, 20))
        card_csv.grid(row=0, column=0, sticky="nsew", padx=(0, 10))

        ttk.Label(
            card_csv,
            text="📄 Formato Texto Plano (.csv)",
            style="Header.TLabel"
        ).pack(anchor="w", pady=(0, 8))

        ttk.Label(
            card_csv,
            text="Ideal para copias de seguridad rápidas y para importar\ndatos en otros sistemas o bases de datos sin pérdida de formato.",
            style="SubHeader.TLabel",
            justify="left"
        ).pack(anchor="w", pady=(0, 20))

        btn_csv = ttk.Button(
            card_csv,
            text="  Exportar Archivo CSV",
            image=self.iconoCSV if self.iconoCSV else None,
            compound="left",
            style="Primary.TButton",
            command=self.exportar_csv
        )
        btn_csv.pack(fill="x", ipady=4)

        # ---- Card 2: Exportar a Excel ----
        card_excel = ttk.LabelFrame(cards_grid, text=" Exportación en Formato Excel ", style="Card.TLabelframe", padding=(20, 20))
        card_excel.grid(row=0, column=1, sticky="nsew", padx=(10, 0))

        ttk.Label(
            card_excel,
            text="📊 Hoja de Cálculo Excel (.xlsx)",
            style="Header.TLabel"
        ).pack(anchor="w", pady=(0, 8))

        ttk.Label(
            card_excel,
            text="Genera un archivo con encabezados listos para análisis,\nreportes contables e inventario físico con formato de celda.",
            style="SubHeader.TLabel",
            justify="left"
        ).pack(anchor="w", pady=(0, 20))

        btn_excel = ttk.Button(
            card_excel,
            text="  Exportar a Microsoft Excel",
            image=self.iconoExcel if self.iconoExcel else None,
            compound="left",
            style="Success.TButton",
            command=self.exportar_bd
        )
        btn_excel.pack(fill="x", ipady=4)

        # Nota informativa al pie
        info_frame = tk.Frame(container, bg="#f8fafc")
        info_frame.pack(fill="x", pady=(15, 0))

        lbl_pie = ttk.Label(
            info_frame,
            text="ℹ️ Los archivos exportados se guardarán automáticamente en la carpeta local 'exportar/' del sistema.",
            font=("Segoe UI", 9, "italic"),
            background="#f8fafc",
            foreground="#64748b"
        )
        lbl_pie.pack(anchor="center")

    def exportar_csv(self):
        tabla = self.selec.get()
        try:
            exportar_inv(tabla)
            mb.showinfo(
                title='Acontar S.A.C.',
                message=f"¡Los datos de '{tabla}' se exportaron con éxito a la carpeta 'exportar/' en formato CSV!",
                parent=self
            )
            self.focus_set()
        except Exception as e:
            mb.showerror(title='Error al Exportar CSV', message=f"Ocurrió un error: {str(e)}", parent=self)
            self.focus_set()

    def exportar_bd(self):
        tabla = self.selec.get()
        try:
            data_expo = exportar_data(tabla)
            if not data_expo or len(data_expo) < 2:
                mb.showwarning("Sin datos", f"No se encontraron registros para exportar en '{tabla}'.", parent=self)
                return
            exportar_excel(tabla, data_expo[0], data_expo[1])
            mb.showinfo(
                title='Acontar S.A.C.',
                message=f"¡Los datos de '{tabla}' se exportaron con éxito a Excel (.xlsx)!",
                parent=self
            )
            self.focus_set()
        except Exception as e:
            mb.showerror(title="Error al Exportar Excel", message=f"Ocurrió un error: {str(e)}", parent=self)
            self.focus_set()
