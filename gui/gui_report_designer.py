import io
import os
import tkinter as tk
from tkinter import ttk, filedialog
from tkinter import messagebox as mb
from PIL import Image, ImageTk
import fitz

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.platypus import SimpleDocTemplate, Table, Paragraph
from reportlab.lib.styles import ParagraphStyle
from utils.pdf_utils import PageNumCanvas
from utils.report_template_manager import ReportTemplateManager
from db.query import reporte_01
from utils.helpers import resource_path


class Window_report_designer(tk.Toplevel):
    """
    Diseñador visual interactivo WYSIWYG de Reportes con calibración geométrica milimétrica:
    - Las cajas y líneas del diseñador coinciden pixel a pixel con las líneas de la tabla PDF.
    - Drag & Drop para reordenar columnas arrastrando con el ratón.
    - Redimensionamiento arrastrando el borde derecho de cada columna.
    - Opciones completas de tipografía: tamaño de letra, fuente, alineación y color de cabecera.
    - Edición inline con doble clic sobre encabezados y títulos.
    - Ajuste fino con teclado (flechas).
    """

    OPCIONES_FUENTES = [
        "Helvetica",
        "Helvetica-Bold",
        "Helvetica-Oblique",
        "Times-Roman",
        "Times-Bold",
        "Courier",
        "Courier-Bold"
    ]

    PALETA_COLORES = [
        ("#DBDBDB", "Gris clásico"),
        ("#BFDBFE", "Azul corporativo"),
        ("#E2E8F0", "Slate moderno"),
        ("#DCFCE7", "Verde menta"),
        ("#FEF08A", "Amarillo suave"),
        ("#FED7AA", "Naranja suave"),
        ("#FFFFFF", "Blanco puro")
    ]

    # Geometría exacta de la página y tabla ReportLab
    PAGE_W_PT = 841.89     # A4 Landscape width
    PAGE_H_PT = 595.27     # A4 Landscape height
    LEFT_MARGIN = 40.0     # Margen izquierdo ReportLab
    TOP_MARGIN = 20.0      # Margen superior ReportLab
    ROW_H_TIT1 = 26.0      # Altura fila 0 (Título)
    ROW_H_TIT2 = 12.0      # Altura fila 1 (Subtítulo)
    ROW_H_TIT3 = 24.0      # Altura fila 2 (Entidad)
    ROW_H_HEADER = 22.0    # Altura fila 3 (Encabezados de columna)
    ROW_H_DATA = 18.0      # Altura filas de datos de muestra

    def __init__(self, parent=None, valor=1, on_save_callback=None):
        super().__init__(parent)
        self.parent = parent
        self.valor = valor
        self.on_save_callback = on_save_callback

        self.title("Diseñador Visual de Reportes — Calibración Geométrica y Drag & Drop (AcontarSoft)")
        try:
            icon_p = resource_path("img/favicon.ico")
            if os.path.exists(icon_p):
                self.iconbitmap(icon_p)
        except Exception:
            pass

        self.geometry("1260x800")
        self.minsize(1100, 700)
        self.configure(bg="#f8fafc")
        self.transient(parent)
        self.grab_set()

        # Plantilla y columnas en memoria
        self.template = ReportTemplateManager.get_template(self.valor)
        self.columnas = [dict(c) for c in self.template.get("columnas", [])]

        for col in self.columnas:
            col.setdefault("font_size", 7)
            col.setdefault("font_name", "Helvetica")
            col.setdefault("align", "CENTER" if col.get("campo_bd") in ["item", "CodInt", "CodPat", "Estado", "estado", "situacion"] else "LEFT")
            col.setdefault("header_bg", "#DBDBDB")

        self.selected_key = "col_0"
        self.selected_col_idx = 0

        # Datos de muestra de la BD
        self.raw_sample_data = self._obtener_datos_muestra()

        # Variables de control
        self.var_titulo = tk.StringVar(value=self.template.get("titulo", ""))
        self.var_subtitulo = tk.StringVar(value=self.template.get("subtitulo", ""))
        self.var_entidad = tk.StringVar(value=self.template.get("entidad", ""))
        self.var_logo = tk.StringVar(value=self.template.get("logo_path", ""))
        self.var_mostrar_logo = tk.BooleanVar(value=self.template.get("mostrar_logo", True))
        self.var_mostrar_guias = tk.BooleanVar(value=True)

        self.var_col_label = tk.StringVar()
        self.var_col_ancho = tk.IntVar(value=50)
        self.var_col_visible = tk.BooleanVar(value=True)
        self.var_col_font_size = tk.IntVar(value=7)
        self.var_col_font_name = tk.StringVar(value="Helvetica")
        self.var_col_align = tk.StringVar(value="LEFT")
        self.var_col_header_bg = tk.StringVar(value="#DBDBDB")

        # Escala real del renderizado
        self.offset_x = 20
        self.offset_y = 20
        self.actual_scale_x = 1.0
        self.actual_scale_y = 1.0

        # Estado de Arrastrar y Soltar (Drag & Drop) y Redimensionamiento
        self.drag_data = {
            "x": 0,
            "y": 0,
            "mode": None,              # "resize_col" | "drag_col" | "select"
            "col_idx": None,
            "start_ancho": 50,
            "current_mouse_x": 0,
            "current_mouse_y": 0,
            "target_insert_idx": None,
        }

        self.canvas_photo = None
        self._updating = False
        self._inline_entry = None

        self._centrar_ventana(1260, 800)
        self._construir_interfaz()
        self._cargar_seleccion_en_inspector()
        self.renderizar_y_dibujar()

    def _centrar_ventana(self, w, h):
        self.update_idletasks()
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        x = (sw - w) // 2
        y = (sh - h) // 2
        self.geometry(f"{w}x{h}+{x}+{y}")

    def _obtener_datos_muestra(self):
        try:
            r = reporte_01(self.valor) or []
            if r:
                muestras = []
                for idx, row in enumerate(r[:6], 1):
                    row_list = list(row)
                    if self.valor != 10:
                        # Asegurar que el correlativo numérico esté siempre en el índice 0 para calibrar con la BD
                        row_list.insert(0, str(idx))
                    muestras.append(row_list)
                return muestras
        except Exception:
            pass

        # Fallbacks de muestra personalizados según el tipo de reporte
        if self.valor == 2:
            return [
                ["1", "740800000001", "CAMIONETA 4X4 PICK UP DOBLE CABINA", "SUB DIRECCION - PATRIMONIO", "B", "GOBIERNO REGIONAL"],
                ["2", "740800000002", "COMPUTADORA DE ESCRITORIO CORE I7", "ALMACEN CENTRAL", "B", "MUNICIPALIDAD PROVINCIAL"],
                ["3", "740800000003", "IMPRESORA MULTIFUNCIONAL LASERJET", "OFICINA DE CONTABILIDAD", "R", "SEDE CENTRAL"],
            ]
        elif self.valor == 4:
            return [
                ["1", "001", "740800000001", "COMPUTADORA PORTATIL CORE I5", "1503.0201", "EQUIPOS COMPUTACIONALES", "FAC-00123", "15/03/2021", "3,500.00", "1,200.00", "2,300.00"],
                ["2", "002", "740800000002", "ESCRITORIO DE MADERA 3 GAVETAS", "1503.0101", "MUEBLES Y ENSERES", "FAC-00456", "20/05/2020", "850.00", "450.00", "400.00"],
            ]
        elif self.valor == 5:
            return [
                ["1", "001", "740800000001", "ESCRITORIO DE MADERA ANTIGUO", "ALMACEN CENTRAL - DEPOSITO 1", "M", "NACIONAL", "ESTANDAR", "S/S", "CAOBA", "D"],
                ["2", "002", "740800000002", "SILLA GIRATORIA TAPIZADA", "DEPOSITO GENERAL", "M", "GENERICO", "OFICINA", "S/S", "NEGRO", "D"],
            ]
        elif self.valor == 8:
            return [
                ["1", "ALMACEN CENTRAL - PISO 2", "SILLA DE ESPERA METALICA 3 CUERPOS", "B", "ISO", "STANDARD", "S/S", "OFICINA", "AZUL", "0.80X0.50"],
                ["2", "GERENCIA REGIONAL", "VENTILADOR DE PIE INDUSTRIAL", "R", "OSTER", "MAX-COOL", "OST-998", "ELECTRICO", "NEGRO", "1.40X0.40"],
            ]
        elif self.valor == 9:
            return [
                ["1", "001", "740800000001", "FOTOCOPIADORA DIGITAL MULTIFUNCION", "DEPOSITO GENERAL", "M", "CANON", "IR-2000", "CN123", "GRIS", "OFICINA", "RES-045-2024"],
                ["2", "002", "740800000002", "SERVIDOR DE RED TORRE", "ALMACEN CENTRAL", "M", "DELL", "POWEREDGE", "DL998", "NEGRO", "OFICINA", "RES-045-2024"],
            ]
        elif self.valor == 10:
            return [
                ["1501", "1501.02", "MAQUINARIA Y EQUIPO", "150,000.00", "25", "145,000.00", "24", "5,000.00", "1"],
                ["1503", "1503.01", "VEHICULOS DE TRANSPORTE", "320,000.00", "8", "320,000.00", "8", "0.00", "0"],
                ["1503", "1503.02", "EQUIPOS COMPUTACIONALES", "85,400.00", "42", "80,200.00", "39", "5,200.00", "3"],
            ]
        elif self.valor == 11:
            return [
                ["1", "001", "740800000001", "MONITOR LED 24 PULGADAS FULL HD", "CORREGIDO", "B", "SAMSUNG", "S24F350", "OFICINA", "SAM9876", "NEGRO", "24 PULG", "VERIFICADO EN CAMPO"],
                ["2", "001", "740800000001", "MONITOR GENERICO", "ORIGINAL", "R", "S/M", "S/M", "S/T", "S/S", "S/C", "S/D", "DATO INICIAL INCOMPLETO"],
            ]

        # Predeterminado para reportes 1, 7 y generales
        return [
            ["1", "001", "740800000001", "COMPUTADORA PERSONAL PORTATIL", "HP", "PROBOOK 450", "5CD12345", "NEGRO", "OFICINA", "35X25", "B", "ALMACEN CENTRAL"],
            ["2", "002", "740800000002", "ESCRITORIO DE MADERA 3 GAVETAS", "NACIONAL", "ESTANDAR", "S/S", "CAOBA", "OFICINA", "1.20X0.70", "R", "GERENCIA REGIONAL"],
            ["3", "003", "740800000003", "SILLON GIRATORIO ERGONOMICO", "GENERICO", "EJECUTIVO", "S/S", "NEGRO", "OFICINA", "ESTANDAR", "B", "CONTABILIDAD"],
            ["4", "004", "740800000004", "IMPRESORA MULTIFUNCIONAL LASER", "EPSON", "ECOTANK", "EPS78912", "NEGRO", "OFICINA", "40X35", "B", "RECURSOS HUMANOS"],
        ]

    # -------------------------------------------------------------------------
    # CONSTRUCCIÓN DE LA INTERFAZ
    # -------------------------------------------------------------------------
    def _construir_interfaz(self):
        # 1. Barra de Título Superior
        f_header = tk.Frame(self, bg="#0f172a", height=54)
        f_header.pack(fill="x", side="top")

        tk.Label(
            f_header,
            text="🎨  DISEÑADOR VISUAL WYSIWYG — CALIBRACIÓN EXACTA DE TABLA",
            font=("Segoe UI", 11, "bold"),
            fg="#ffffff",
            bg="#0f172a"
        ).pack(side="left", padx=16, pady=10)

        tk.Label(
            f_header,
            text="|  Las guías coinciden exactamente con la cuadrícula • Arrastra para reordenar • Arrastra el borde rojo para redimensionar",
            font=("Segoe UI", 9),
            fg="#94a3b8",
            bg="#0f172a"
        ).pack(side="left", padx=4, pady=10)

        # 2. Contenedor Principal PanedWindow
        paned = tk.PanedWindow(self, orient="horizontal", bg="#cbd5e1", bd=0, sashwidth=6)
        paned.pack(fill="both", expand=True, padx=10, pady=8)

        # Columna Izquierda: Lienzo con Hoja A4 y Cajas
        self.frame_left = ttk.Frame(paned, padding=8)
        paned.add(self.frame_left, minsize=680, width=780)

        # Columna Derecha: Inspector Completo
        self.frame_right = ttk.Frame(paned, padding=8)
        paned.add(self.frame_right, minsize=440, width=460)

        self._construir_panel_canvas()
        self._construir_panel_inspector()

        # 3. Barra Inferior de Acciones
        f_bottom = tk.Frame(self, bg="#f8fafc", bd=1, relief="groove")
        f_bottom.pack(fill="x", side="bottom", padx=10, pady=(0, 8))

        ttk.Button(f_bottom, text="↺ Restaurar Predeterminado", command=self._restablecer).pack(side="left", padx=6, pady=8)
        ttk.Button(f_bottom, text="✕ Cerrar", command=self.destroy).pack(side="right", padx=6, pady=8)
        ttk.Button(f_bottom, text="💾 Guardar Diseño", command=self._guardar).pack(side="right", padx=6, pady=8)

    def _construir_panel_canvas(self):
        top_bar = ttk.Frame(self.frame_left)
        top_bar.pack(fill="x", pady=(0, 6))

        ttk.Label(
            top_bar,
            text="📄 Vista Previa Real en Vivo (Calibrada con ReportLab)",
            font=("Segoe UI", 9, "bold")
        ).pack(side="left")

        ttk.Checkbutton(
            top_bar,
            text="Mostrar guías de columnas",
            variable=self.var_mostrar_guias,
            command=self._redibujar_guias_canvas
        ).pack(side="right", padx=4)

        canvas_container = tk.Frame(self.frame_left, bg="#94a3b8", bd=1, relief="solid")
        canvas_container.pack(fill="both", expand=True)

        self.canvas = tk.Canvas(canvas_container, bg="#475569", highlightthickness=0, cursor="arrow")
        self.canvas.pack(fill="both", expand=True)

        self.canvas.bind("<Button-1>", self._on_canvas_press)
        self.canvas.bind("<B1-Motion>", self._on_canvas_motion)
        self.canvas.bind("<ButtonRelease-1>", self._on_canvas_release)
        self.canvas.bind("<Motion>", self._on_canvas_hover)
        self.canvas.bind("<Double-Button-1>", self._on_canvas_double_click)
        self.canvas.bind("<Configure>", lambda _e: self.renderizar_y_dibujar())

        self.bind("<Left>", lambda _e: self._nudge_column(-5))
        self.bind("<Right>", lambda _e: self._nudge_column(5))
        self.bind("<Up>", lambda _e: self._mover_columna_izq())
        self.bind("<Down>", lambda _e: self._mover_columna_der())

        frame_quick = ttk.Frame(self.frame_left)
        frame_quick.pack(fill="x", pady=(6, 0))

        ttk.Label(frame_quick, text="Ajuste rápido:", font=("Segoe UI", 8, "italic")).pack(side="left", padx=4)
        ttk.Button(frame_quick, text="➖ -5 pt", command=lambda: self._nudge_column(-5)).pack(side="left", padx=2)
        ttk.Button(frame_quick, text="➕ +5 pt", command=lambda: self._nudge_column(5)).pack(side="left", padx=2)
        ttk.Button(frame_quick, text="◀ Izquierda", command=self._mover_columna_izq).pack(side="left", padx=2)
        ttk.Button(frame_quick, text="▶ Derecha", command=self._mover_columna_der).pack(side="left", padx=2)

    def _construir_panel_inspector(self):
        # 1. Card: Encabezado Institucional
        card_encabezado = ttk.LabelFrame(
            self.frame_right,
            text=" 🏛️ 1. Encabezado Institucional y Logotipo ",
            padding=8
        )
        card_encabezado.pack(fill="x", pady=(0, 6))
        card_encabezado.columnconfigure(1, weight=1)

        ttk.Label(card_encabezado, text="Título:").grid(row=0, column=0, sticky="w", pady=2)
        etr_tit = ttk.Entry(card_encabezado, textvariable=self.var_titulo, font=("Segoe UI", 9))
        etr_tit.grid(row=0, column=1, columnspan=2, sticky="ew", padx=(6, 0), pady=2)
        etr_tit.bind("<KeyRelease>", lambda _e: self._on_text_change())

        ttk.Label(card_encabezado, text="Subtítulo:").grid(row=1, column=0, sticky="w", pady=2)
        etr_sub = ttk.Entry(card_encabezado, textvariable=self.var_subtitulo, font=("Segoe UI", 9))
        etr_sub.grid(row=1, column=1, columnspan=2, sticky="ew", padx=(6, 0), pady=2)
        etr_sub.bind("<KeyRelease>", lambda _e: self._on_text_change())

        ttk.Label(card_encabezado, text="Entidad:").grid(row=2, column=0, sticky="w", pady=2)
        etr_ent = ttk.Entry(card_encabezado, textvariable=self.var_entidad, font=("Segoe UI", 9))
        etr_ent.grid(row=2, column=1, columnspan=2, sticky="ew", padx=(6, 0), pady=2)
        etr_ent.bind("<KeyRelease>", lambda _e: self._on_text_change())

        ttk.Label(card_encabezado, text="Logo:").grid(row=3, column=0, sticky="w", pady=2)
        etr_logo = ttk.Entry(card_encabezado, textvariable=self.var_logo, font=("Segoe UI", 8))
        etr_logo.grid(row=3, column=1, sticky="ew", padx=(6, 4), pady=2)
        etr_logo.bind("<KeyRelease>", lambda _e: self._on_text_change())

        ttk.Button(card_encabezado, text="📁", width=3, command=self._examinar_logo).grid(row=3, column=2, sticky="e", pady=2)

        ttk.Checkbutton(
            card_encabezado,
            text="Mostrar logotipo en el encabezado",
            variable=self.var_mostrar_logo,
            command=self.renderizar_y_dibujar
        ).grid(row=4, column=1, columnspan=2, sticky="w", padx=(6, 0), pady=(2, 2))

        # 2. Card: Formato y Tipografía de la Columna
        card_cols = ttk.LabelFrame(
            self.frame_right,
            text=" 📊 2. Formato, Tipografía y Alineación de Columna ",
            padding=8
        )
        card_cols.pack(fill="both", expand=True, pady=(0, 6))
        card_cols.columnconfigure(1, weight=1)

        ttk.Label(card_cols, text="Columna Activa:", font=("Segoe UI", 9, "bold")).grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 2))
        self.cbx_cols = ttk.Combobox(card_cols, state="readonly", font=("Segoe UI", 9))
        self.cbx_cols.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(0, 4))
        self.cbx_cols.bind("<<ComboboxSelected>>", self._on_col_combobox_select)

        # Botones de gestión rápida de columnas (Agregar / Eliminar)
        f_col_tools = tk.Frame(card_cols)
        f_col_tools.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(0, 4))
        f_col_tools.columnconfigure(0, weight=1)
        f_col_tools.columnconfigure(1, weight=1)

        ttk.Button(f_col_tools, text="➕ Agregar Columna", command=self._agregar_columna).grid(row=0, column=0, sticky="ew", padx=(0, 2))
        ttk.Button(f_col_tools, text="🗑️ Eliminar Columna", command=self._eliminar_columna).grid(row=0, column=1, sticky="ew", padx=(2, 0))

        self.chk_col_vis = ttk.Checkbutton(
            card_cols,
            text="Visible en la tabla del reporte",
            variable=self.var_col_visible,
            command=self._on_col_visible_toggle
        )
        self.chk_col_vis.grid(row=3, column=0, columnspan=2, sticky="w", pady=2)

        ttk.Label(card_cols, text="Encabezado:").grid(row=4, column=0, sticky="w", pady=2)
        self.etr_label = ttk.Entry(card_cols, textvariable=self.var_col_label, font=("Segoe UI", 9))
        self.etr_label.grid(row=4, column=1, sticky="ew", padx=(6, 0), pady=2)
        self.etr_label.bind("<KeyRelease>", lambda _e: self._on_col_label_change())

        ttk.Label(card_cols, text="Dato BD Asignado:").grid(row=5, column=0, sticky="w", pady=2)
        self.cbx_campo_bd = ttk.Combobox(card_cols, state="readonly", font=("Segoe UI", 9))
        self.cbx_campo_bd.grid(row=5, column=1, sticky="ew", padx=(6, 0), pady=2)
        self.cbx_campo_bd.bind("<<ComboboxSelected>>", self._on_campo_bd_selected)

        ttk.Label(card_cols, text="Ancho PDF (pt):").grid(row=6, column=0, sticky="w", pady=2)
        self.spn_ancho = ttk.Spinbox(
            card_cols, from_=15, to=450, increment=5,
            textvariable=self.var_col_ancho, width=8,
            command=self._on_col_ancho_change
        )
        self.spn_ancho.grid(row=6, column=1, sticky="w", padx=(6, 0), pady=2)
        self.spn_ancho.bind("<KeyRelease>", lambda _e: self._on_col_ancho_change())

        ttk.Separator(card_cols, orient="horizontal").grid(row=7, column=0, columnspan=2, sticky="ew", pady=(6, 6))

        # Alineación
        ttk.Label(card_cols, text="Alineación:").grid(row=8, column=0, sticky="w", pady=2)
        f_align = tk.Frame(card_cols)
        f_align.grid(row=8, column=1, sticky="w", padx=(6, 0), pady=2)

        self.btn_align_left = ttk.Button(f_align, text="⬅ Izq", width=6, command=lambda: self._set_alignment("LEFT"))
        self.btn_align_left.pack(side="left", padx=1)
        self.btn_align_center = ttk.Button(f_align, text="⏺ Centro", width=7, command=lambda: self._set_alignment("CENTER"))
        self.btn_align_center.pack(side="left", padx=1)
        self.btn_align_right = ttk.Button(f_align, text="➡ Der", width=6, command=lambda: self._set_alignment("RIGHT"))
        self.btn_align_right.pack(side="left", padx=1)

        # Tamaño de Fuente
        ttk.Label(card_cols, text="Tamaño Letra:").grid(row=9, column=0, sticky="w", pady=2)
        f_font_size = tk.Frame(card_cols)
        f_font_size.grid(row=9, column=1, sticky="w", padx=(6, 0), pady=2)

        self.spn_font_size = ttk.Spinbox(
            f_font_size, from_=5, to=14, increment=1,
            textvariable=self.var_col_font_size, width=6,
            command=self._on_font_prop_change
        )
        self.spn_font_size.pack(side="left")
        self.spn_font_size.bind("<KeyRelease>", lambda _e: self._on_font_prop_change())
        ttk.Label(f_font_size, text="pt (predet: 7)").pack(side="left", padx=(4, 0))

        # Familia de Fuente
        ttk.Label(card_cols, text="Fuente / Estilo:").grid(row=10, column=0, sticky="w", pady=2)
        self.cbx_font_name = ttk.Combobox(
            card_cols,
            values=self.OPCIONES_FUENTES,
            textvariable=self.var_col_font_name,
            state="readonly",
            font=("Segoe UI", 9)
        )
        self.cbx_font_name.grid(row=10, column=1, sticky="ew", padx=(6, 0), pady=2)
        self.cbx_font_name.bind("<<ComboboxSelected>>", lambda _e: self._on_font_prop_change())

        # Color de Fondo de Cabecera
        ttk.Label(card_cols, text="Color Cabecera:").grid(row=11, column=0, sticky="w", pady=2)
        self.cbx_header_bg = ttk.Combobox(
            card_cols,
            values=[f"{name} ({hex_c})" for hex_c, name in self.PALETA_COLORES],
            state="readonly",
            font=("Segoe UI", 9)
        )
        self.cbx_header_bg.grid(row=11, column=1, sticky="ew", padx=(6, 0), pady=2)
        self.cbx_header_bg.bind("<<ComboboxSelected>>", self._on_color_combobox_change)

        ttk.Separator(card_cols, orient="horizontal").grid(row=12, column=0, columnspan=2, sticky="ew", pady=(6, 6))

        f_orden = tk.Frame(card_cols)
        f_orden.grid(row=13, column=0, columnspan=2, sticky="ew", pady=2)
        f_orden.columnconfigure(0, weight=1)
        f_orden.columnconfigure(1, weight=1)

        ttk.Button(f_orden, text="◀ Mover a Izquierda", command=self._mover_columna_izq).grid(row=0, column=0, sticky="ew", padx=(0, 2))
        ttk.Button(f_orden, text="▶ Mover a Derecha", command=self._mover_columna_der).grid(row=0, column=1, sticky="ew", padx=(2, 0))

        ttk.Button(
            card_cols,
            text="📐 Auto-ajustar Anchos al Ancho A4 (760 pt)",
            command=self._auto_ajustar_anchos
        ).grid(row=14, column=0, columnspan=2, sticky="ew", pady=(6, 2))

        self.lbl_resumen_anchos = tk.Label(
            card_cols,
            text="Ancho total: 0 pt / 760 pt",
            font=("Segoe UI", 9, "italic"),
            fg="#475569"
        )
        self.lbl_resumen_anchos.grid(row=15, column=0, columnspan=2, sticky="w", pady=(2, 0))

        self._actualizar_combobox_columnas()

    # -------------------------------------------------------------------------
    # GESTIÓN Y FORMATO DE COLUMNAS
    # -------------------------------------------------------------------------
    def _actualizar_combobox_columnas(self):
        nombres = []
        for i, c in enumerate(self.columnas):
            estado = "🟢" if c.get("visible", True) else "⚪"
            lbl = c.get("label", "").replace("\n", " ")
            al = c.get("align", "LEFT")[0]
            fs = c.get("font_size", 7)
            campo = c.get("campo_bd", "")
            nombres.append(f"{estado} {i+1}. {lbl} [{campo}|{al}|{fs}pt]")

        self.cbx_cols["values"] = nombres
        if 0 <= self.selected_col_idx < len(nombres):
            self.cbx_cols.current(self.selected_col_idx)

        suma = sum(c.get("ancho", 50) for c in self.columnas if c.get("visible", True))
        diferencia = 760 - suma
        dif_txt = f"+{diferencia} pt libres" if diferencia >= 0 else f"{diferencia} pt (exceso)"
        color = "#16a34a" if abs(diferencia) <= 10 else ("#ea580c" if diferencia < 0 else "#2563eb")
        self.lbl_resumen_anchos.config(
            text=f"Ancho total: {suma} pt / 760 pt  ({dif_txt})",
            fg=color
        )

    def _cargar_seleccion_en_inspector(self):
        if not (0 <= self.selected_col_idx < len(self.columnas)):
            return
        col = self.columnas[self.selected_col_idx]

        self._updating = True
        self.var_col_label.set(col.get("label", ""))
        self.var_col_ancho.set(col.get("ancho", 50))
        self.var_col_visible.set(col.get("visible", True))
        self.var_col_font_size.set(col.get("font_size", 7))
        self.var_col_font_name.set(col.get("font_name", "Helvetica"))
        self.var_col_align.set(col.get("align", "LEFT"))
        self.var_col_header_bg.set(col.get("header_bg", "#DBDBDB"))

        curr_bg = col.get("header_bg", "#DBDBDB").upper()
        for i, (hex_c, _name) in enumerate(self.PALETA_COLORES):
            if hex_c.upper() == curr_bg:
                self.cbx_header_bg.current(i)
                break

        # Sincronizar Combobox de Campo BD
        campos = ReportTemplateManager.obtener_campos_disponibles(self.valor)
        campo_actual = col.get("campo_bd", "")
        nombres_campos = [f"{desc} ({cid})" for cid, desc in campos]
        self.cbx_campo_bd["values"] = nombres_campos

        idx_campo = 0
        for i, (cid, _desc) in enumerate(campos):
            if cid == campo_actual:
                idx_campo = i
                break
        if nombres_campos:
            self.cbx_campo_bd.current(idx_campo)

        self._updating = False

    def _on_campo_bd_selected(self, _event=None):
        if self._updating:
            return
        idx = self.cbx_campo_bd.current()
        campos = ReportTemplateManager.obtener_campos_disponibles(self.valor)
        if 0 <= idx < len(campos):
            cid, cdesc = campos[idx]
            col = self.columnas[self.selected_col_idx]
            col["campo_bd"] = cid

            # Si el label actual estaba vacío, sugerir el nombre amigable
            if not col.get("label"):
                sug_label = cdesc.split(" (")[0]
                col["label"] = sug_label
                self.var_col_label.set(sug_label)

            # Centrar automáticamente campos de códigos y estado si aún está en default
            if cid in ["item", "CodInt", "CodPat", "Estado", "estado", "situacion"]:
                col["align"] = "CENTER"
                self.var_col_align.set("CENTER")

            self._actualizar_combobox_columnas()
            self.renderizar_y_dibujar()

    def _agregar_columna(self):
        campos = ReportTemplateManager.obtener_campos_disponibles(self.valor)
        campos_en_uso = {c.get("campo_bd") for c in self.columnas}
        cid_elegido, desc_elegida = campos[0] if campos else ("item", "Columna")
        for cid, desc in campos:
            if cid not in campos_en_uso:
                cid_elegido, desc_elegida = cid, desc
                break

        nueva_col = {
            "id": f"col_{len(self.columnas) + 1}",
            "label": desc_elegida.split(" (")[0],
            "campo_bd": cid_elegido,
            "ancho": 60,
            "visible": True,
            "font_size": 7,
            "font_name": "Helvetica",
            "align": "CENTER" if cid_elegido in ["item", "CodInt", "CodPat", "Estado", "estado", "situacion"] else "LEFT",
            "header_bg": "#DBDBDB"
        }
        self.columnas.append(nueva_col)
        self.selected_col_idx = len(self.columnas) - 1
        self.selected_key = f"col_{self.selected_col_idx}"
        self._actualizar_combobox_columnas()
        self._cargar_seleccion_en_inspector()
        self.renderizar_y_dibujar()

    def _eliminar_columna(self):
        if len(self.columnas) <= 1:
            mb.showwarning("Atención", "El reporte debe tener al menos una columna.", parent=self)
            return
        col = self.columnas[self.selected_col_idx]
        nombre = col.get("label", "").replace("\n", " ")
        if mb.askyesno("Confirmar eliminación", f"¿Está seguro de eliminar la columna '{nombre}' del reporte?", parent=self):
            del self.columnas[self.selected_col_idx]
            if self.selected_col_idx >= len(self.columnas):
                self.selected_col_idx = len(self.columnas) - 1
            self.selected_key = f"col_{self.selected_col_idx}"
            self._actualizar_combobox_columnas()
            self._cargar_seleccion_en_inspector()
            self.renderizar_y_dibujar()

    def _set_alignment(self, align_val):
        if self._updating:
            return
        self.var_col_align.set(align_val)
        self.columnas[self.selected_col_idx]["align"] = align_val
        self._actualizar_combobox_columnas()
        self.renderizar_y_dibujar()

    def _on_font_prop_change(self):
        if self._updating:
            return
        col = self.columnas[self.selected_col_idx]
        try:
            col["font_size"] = max(5, min(14, int(self.var_col_font_size.get())))
        except Exception:
            pass
        col["font_name"] = self.var_col_font_name.get()
        self._actualizar_combobox_columnas()
        self.renderizar_y_dibujar()

    def _on_color_combobox_change(self, _event=None):
        if self._updating:
            return
        idx = self.cbx_header_bg.current()
        if idx >= 0:
            hex_c, _name = self.PALETA_COLORES[idx]
            self.var_col_header_bg.set(hex_c)
            self.columnas[self.selected_col_idx]["header_bg"] = hex_c
            self.renderizar_y_dibujar()

    def _on_col_combobox_select(self, _event=None):
        idx = self.cbx_cols.current()
        if idx >= 0:
            self.selected_col_idx = idx
            self.selected_key = f"col_{idx}"
            self._cargar_seleccion_en_inspector()
            self._redibujar_guias_canvas()

    def _on_col_visible_toggle(self):
        if self._updating:
            return
        col = self.columnas[self.selected_col_idx]
        col["visible"] = self.var_col_visible.get()
        self._actualizar_combobox_columnas()
        self.renderizar_y_dibujar()

    def _on_col_label_change(self):
        if self._updating:
            return
        col = self.columnas[self.selected_col_idx]
        col["label"] = self.var_col_label.get()
        self._actualizar_combobox_columnas()
        self.renderizar_y_dibujar()

    def _on_col_ancho_change(self):
        if self._updating:
            return
        try:
            val = int(self.var_col_ancho.get())
            if val < 15:
                val = 15
            self.columnas[self.selected_col_idx]["ancho"] = val
            self._actualizar_combobox_columnas()
            self.renderizar_y_dibujar()
        except ValueError:
            pass

    def _on_text_change(self):
        self.renderizar_y_dibujar()

    def _mover_columna_izq(self):
        if self.selected_col_idx <= 0:
            return
        idx = self.selected_col_idx
        self.columnas[idx - 1], self.columnas[idx] = self.columnas[idx], self.columnas[idx - 1]
        self.selected_col_idx = idx - 1
        self.selected_key = f"col_{self.selected_col_idx}"
        self._actualizar_combobox_columnas()
        self._cargar_seleccion_en_inspector()
        self.renderizar_y_dibujar()

    def _mover_columna_der(self):
        if self.selected_col_idx >= len(self.columnas) - 1:
            return
        idx = self.selected_col_idx
        self.columnas[idx + 1], self.columnas[idx] = self.columnas[idx], self.columnas[idx + 1]
        self.selected_col_idx = idx + 1
        self.selected_key = f"col_{self.selected_col_idx}"
        self._actualizar_combobox_columnas()
        self._cargar_seleccion_en_inspector()
        self.renderizar_y_dibujar()

    def _nudge_column(self, delta_pt: int):
        focused = self.focus_get()
        if isinstance(focused, (tk.Entry, ttk.Entry, ttk.Spinbox, ttk.Combobox)):
            return
        col = self.columnas[self.selected_col_idx]
        nuevo_ancho = max(15, min(450, col.get("ancho", 50) + delta_pt))
        col["ancho"] = nuevo_ancho
        self._updating = True
        self.var_col_ancho.set(nuevo_ancho)
        self._updating = False
        self._actualizar_combobox_columnas()
        self.renderizar_y_dibujar()

    def _auto_ajustar_anchos(self):
        visibles = [c for c in self.columnas if c.get("visible", True)]
        if not visibles:
            mb.showwarning("Atención", "No hay columnas visibles para auto-ajustar.", parent=self)
            return
        ReportTemplateManager.auto_ajustar_anchos(visibles, ancho_total_objetivo=760)
        self._cargar_seleccion_en_inspector()
        self._actualizar_combobox_columnas()
        self.renderizar_y_dibujar()

    def _examinar_logo(self):
        ruta = filedialog.askopenfilename(
            title="Seleccionar Logotipo Institucional",
            filetypes=[("Imágenes", "*.png *.jpg *.jpeg *.bmp"), ("Todos los archivos", "*.*")],
            parent=self
        )
        if ruta:
            self.var_logo.set(ruta)
            self.renderizar_y_dibujar()

    # -------------------------------------------------------------------------
    # GEOMETRÍA CALIBRADA AL MILÍMETRO
    # -------------------------------------------------------------------------
    def _obtener_cajas_geometria(self):
        """
        Calcula las coordenadas exactas de las cajas para que coincidan
        al 100% con la cuadrícula dibujada por ReportLab Table.
        """
        cajas = {}

        # 1. Logo (posicionado en el canvas de ReportLab en x=40, y_top=10.27, h=50)
        cajas["logo"] = {
            "nombre": "Logotipo",
            "x_pt": self.LEFT_MARGIN,
            "y_pt": 10.27,
            "w_pt": 90.0,
            "h_pt": 50.0,
            "tipo": "logo"
        }

        # 2. Títulos institucionales (filas 0, 1 y 2 de la tabla)
        cajas["titulo"] = {
            "nombre": "Título",
            "x_pt": self.LEFT_MARGIN,
            "y_pt": self.TOP_MARGIN,
            "w_pt": 760.0,
            "h_pt": self.ROW_H_TIT1,
            "tipo": "titulo"
        }
        cajas["subtitulo"] = {
            "nombre": "Subtítulo",
            "x_pt": self.LEFT_MARGIN,
            "y_pt": self.TOP_MARGIN + self.ROW_H_TIT1,
            "w_pt": 760.0,
            "h_pt": self.ROW_H_TIT2,
            "tipo": "subtitulo"
        }
        cajas["entidad"] = {
            "nombre": "Entidad",
            "x_pt": self.LEFT_MARGIN,
            "y_pt": self.TOP_MARGIN + self.ROW_H_TIT1 + self.ROW_H_TIT2,
            "w_pt": 760.0,
            "h_pt": self.ROW_H_TIT3,
            "tipo": "entidad"
        }

        # 3. Columnas de la Tabla (Fila 3 de la tabla ReportLab)
        # y_start exacto = 20 + 26 + 12 + 24 = 82.0 pt
        y_header = self.TOP_MARGIN + self.ROW_H_TIT1 + self.ROW_H_TIT2 + self.ROW_H_TIT3
        h_header = self.ROW_H_HEADER
        h_tabla = len(self.raw_sample_data) * self.ROW_H_DATA

        x_col = self.LEFT_MARGIN

        for i, col in enumerate(self.columnas):
            if not col.get("visible", True):
                continue
            w_col = float(col.get("ancho", 50))
            cajas[f"col_{i}"] = {
                "nombre": col.get("label", "").replace("\n", " "),
                "col_idx": i,
                "x_pt": x_col,
                "y_pt": y_header,
                "w_pt": w_col,
                "h_pt": h_header,
                "h_total_pt": h_header + h_tabla,
                "tipo": "columna"
            }
            x_col += w_col

        return cajas

    # -------------------------------------------------------------------------
    # RENDERIZADO EN VIVO Y CALIBRACIÓN DE LÍNEAS
    # -------------------------------------------------------------------------
    def renderizar_y_dibujar(self):
        self._cerrar_editor_inline(guardar=False)

        try:
            temp_template = {
                "titulo": self.var_titulo.get().strip() or "REPORTE DE INVENTARIO",
                "subtitulo": self.var_subtitulo.get().strip() or "Inventario Patrimonial",
                "entidad": self.var_entidad.get().strip() or "ENTIDAD",
                "logo_path": self.var_logo.get().strip(),
                "mostrar_logo": self.var_mostrar_logo.get(),
                "columnas": self.columnas
            }

            encabezados, datos_proc, colwidths, cols_meta = ReportTemplateManager.preparar_datos_para_pdf(
                self.valor, self.raw_sample_data, template=temp_template, incluir_metadata=True
            )

            # Generar PDF en memoria con hAlign='LEFT' y alturas de fila exactas
            pdf_buffer = io.BytesIO()
            doc = SimpleDocTemplate(
                pdf_buffer,
                pagesize=landscape(A4),
                rightMargin=40, leftMargin=40,
                topMargin=20, bottomMargin=50
            )

            elements = []
            h1 = ParagraphStyle(name='Heading2', fontSize=12, alignment=1, fontName='HELVETICA-BOLD')

            titulo1 = [[Paragraph(str(temp_template["titulo"]), h1)]]
            titulo2 = [[Paragraph(str(temp_template["subtitulo"]), h1)]]
            titulo3 = [[Paragraph(str(temp_template["entidad"]), h1)]]

            table_data = []
            for row in datos_proc:
                row_data = []
                for index, cell in enumerate(row):
                    meta = cols_meta[index] if index < len(cols_meta) else {}
                    fn = meta.get("font_name", "Helvetica")
                    fs = meta.get("font_size", 7)
                    align_str = meta.get("align", "LEFT")
                    align_val = 1 if align_str == "CENTER" else (2 if align_str == "RIGHT" else 0)

                    c_style = ParagraphStyle(
                        name=f"Cell_{index}_{fn}_{fs}_{align_val}",
                        fontName=fn,
                        fontSize=fs,
                        leading=fs + 1.5,
                        alignment=align_val
                    )
                    row_data.append(Paragraph(str(cell if cell is not None else ""), c_style))
                table_data.append(row_data)

            tabla = titulo1 + titulo2 + titulo3 + [encabezados] + list(table_data)

            # Alturas fijadas milimétricamente
            rowHeights = [self.ROW_H_TIT1, self.ROW_H_TIT2, self.ROW_H_TIT3, self.ROW_H_HEADER] + [self.ROW_H_DATA] * len(datos_proc)

            estilos = [
                ('SPAN', (0, 0), (-1, 0)),
                ('SPAN', (0, 1), (-1, 1)),
                ('SPAN', (0, 2), (-1, 2)),
                ('BACKGROUND', (0, 3), (-1, 3), '#DBDBDB'),
                ('GRID', (0, 3), (-1, -1), 0.5, colors.black),
                ('ALIGN', (0, 3), (-1, 3), 'CENTER'),
                ('VALIGN', (0, 0), (-1, 0), 'BOTTOM'),
                ('VALIGN', (0, 1), (-1, 1), 'MIDDLE'),
                ('VALIGN', (0, 2), (-1, 2), 'TOP'),
                ('VALIGN', (0, 3), (-1, -1), 'MIDDLE'),
                # Padding controlado
                ('TOPPADDING', (0, 3), (-1, -1), 2),
                ('BOTTOMPADDING', (0, 3), (-1, -1), 2),
                ('LEFTPADDING', (0, 3), (-1, -1), 3),
                ('RIGHTPADDING', (0, 3), (-1, -1), 3),
            ]

            for idx_col, meta in enumerate(cols_meta):
                bg = meta.get("header_bg")
                if bg:
                    try:
                        estilos.append(('BACKGROUND', (idx_col, 3), (idx_col, 3), colors.HexColor(bg)))
                    except Exception:
                        pass

            # CRÍTICO: hAlign='LEFT' para que la tabla empiece exactamente en leftMargin=40.0 pt
            t = Table(tabla, colWidths=colwidths, rowHeights=rowHeights, repeatRows=4, style=estilos, hAlign='LEFT')
            elements.append(t)

            def make_canvas(*args, **kwargs):
                return PageNumCanvas(
                    *args,
                    orientacion=0,
                    logo_path=temp_template["logo_path"],
                    mostrar_logo=temp_template["mostrar_logo"],
                    **kwargs
                )

            doc.build(elements, canvasmaker=make_canvas)

            # Rasterizar página con PyMuPDF fitz
            pdf_bytes = pdf_buffer.getvalue()
            with fitz.open(stream=pdf_bytes, filetype="pdf") as f_doc:
                if len(f_doc) > 0:
                    page = f_doc[0]
                    cw = max(self.canvas.winfo_width(), 680)
                    ch = max(self.canvas.winfo_height(), 480)

                    aspect = self.PAGE_W_PT / self.PAGE_H_PT
                    target_w = cw - 30
                    target_h = int(target_w / aspect)
                    if target_h > ch - 30:
                        target_h = ch - 30
                        target_w = int(target_h * aspect)

                    zoom = target_w / page.rect.width
                    mat = fitz.Matrix(zoom, zoom)
                    pix = page.get_pixmap(matrix=mat, alpha=False)
                    pil_img = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)

                    self.canvas_photo = ImageTk.PhotoImage(pil_img)
                    self.offset_x = (cw - pix.width) // 2
                    self.offset_y = (ch - pix.height) // 2
                    # Factores de escala exactos basados en el tamaño del pixmap rasterizado
                    self.actual_scale_x = pix.width / self.PAGE_W_PT
                    self.actual_scale_y = pix.height / self.PAGE_H_PT

        except Exception as e:
            print(f"Error renderizando PDF interactivo: {e}")

        self._redibujar_guias_canvas()

    def _redibujar_guias_canvas(self):
        self.canvas.delete("all")

        ox = self.offset_x
        oy = self.offset_y
        sx = self.actual_scale_x
        sy = self.actual_scale_y

        # Imagen PDF renderizado en vivo
        if self.canvas_photo:
            pw = self.canvas_photo.width()
            ph = self.canvas_photo.height()
            self.canvas.create_rectangle(ox + 5, oy + 5, ox + pw + 5, oy + ph + 5, fill="#334155", outline="")
            self.canvas.create_rectangle(ox, oy, ox + pw, oy + ph, fill="#ffffff", outline="#0f172a", width=1)
            self.canvas.create_image(ox, oy, anchor="nw", image=self.canvas_photo)

        if not self.var_mostrar_guias.get():
            return

        cajas = self._obtener_cajas_geometria()

        for key, c in cajas.items():
            is_selected = (key == self.selected_key)

            x1 = ox + round(c["x_pt"] * sx)
            y1 = oy + round(c["y_pt"] * sy)
            x2 = ox + round((c["x_pt"] + c["w_pt"]) * sx)
            y2 = oy + round((c["y_pt"] + c["h_pt"]) * sy)

            if is_selected:
                if c["tipo"] == "columna":
                    y_total2 = oy + round((c["y_pt"] + c.get("h_total_pt", c["h_pt"])) * sy)
                    self.canvas.create_rectangle(
                        x1, y1, x2, y_total2,
                        outline="#2563eb", width=2
                    )

                self.canvas.create_rectangle(
                    x1, y1, x2, y2,
                    outline="#2563eb", width=2
                )

                badge_txt = f" {c['nombre']} ({int(c['w_pt'])} pt) "
                badge_y = max(y1 - 15, oy)
                badge_w = min(len(badge_txt) * 6.5, x2 - x1)
                self.canvas.create_rectangle(
                    x1, badge_y, x1 + badge_w, badge_y + 14,
                    fill="#2563eb", outline="#2563eb"
                )
                self.canvas.create_text(
                    x1 + 3, badge_y + 7,
                    text=badge_txt, anchor="w",
                    font=("Segoe UI", 7, "bold"), fill="#ffffff"
                )

                # Manija roja en el borde derecho
                hs = 4
                ym = (y1 + y2) / 2
                self.canvas.create_rectangle(
                    x2 - hs, ym - hs, x2 + hs, ym + hs,
                    fill="#dc2626", outline="#ffffff", width=1
                )
            else:
                self.canvas.create_rectangle(
                    x1, y1, x2, y2,
                    outline="#94a3b8", dash=(2, 2), width=1
                )

        if self.drag_data.get("mode") == "drag_col":
            self._dibujar_indicador_drag_drop()

    def _dibujar_indicador_drag_drop(self):
        ox = self.offset_x
        sx = self.actual_scale_x
        sy = self.actual_scale_y
        mx = self.drag_data["current_mouse_x"]
        my = self.drag_data["current_mouse_y"]
        cajas = self._obtener_cajas_geometria()

        key = self.drag_data.get("elem_key")
        c = cajas.get(key)
        if not c:
            return

        w = c["w_pt"] * sx
        h = c["h_pt"] * sy
        gx1 = mx - w / 2
        gy1 = my - h / 2
        gx2 = gx1 + w
        gy2 = gy1 + h

        self.canvas.create_rectangle(
            gx1, gy1, gx2, gy2,
            fill="#dbeafe", outline="#2563eb", width=2, stipple="gray25"
        )
        self.canvas.create_text(
            (gx1 + gx2) / 2, (gy1 + gy2) / 2,
            text=f"Moviendo: {c['nombre']}",
            font=("Segoe UI", 8, "bold"), fill="#1e40af"
        )

        cajas_cols = [(k, info) for k, info in cajas.items() if info["tipo"] == "columna"]
        target_idx = None
        target_x_canvas = None

        pt_mx = (mx - ox) / sx

        for _k, info in cajas_cols:
            x_mid = info["x_pt"] + info["w_pt"] / 2
            if pt_mx < x_mid:
                target_idx = info["col_idx"]
                target_x_canvas = ox + round(info["x_pt"] * sx)
                break
        else:
            if cajas_cols:
                last_info = cajas_cols[-1][1]
                target_idx = len(self.columnas)
                target_x_canvas = ox + round((last_info["x_pt"] + last_info["w_pt"]) * sx)

        self.drag_data["target_insert_idx"] = target_idx

        if target_x_canvas is not None:
            y1 = self.offset_y + round(cajas_cols[0][1]["y_pt"] * sy)
            y2 = self.offset_y + round((cajas_cols[0][1]["y_pt"] + cajas_cols[0][1].get("h_total_pt", 100)) * sy)
            self.canvas.create_line(
                target_x_canvas, y1, target_x_canvas, y2,
                fill="#2563eb", width=3
            )
            self.canvas.create_polygon(
                target_x_canvas - 5, y1 - 6,
                target_x_canvas + 5, y1 - 6,
                target_x_canvas, y1,
                fill="#2563eb"
            )
            self.canvas.create_polygon(
                target_x_canvas - 5, y2 + 6,
                target_x_canvas + 5, y2 + 6,
                target_x_canvas, y2,
                fill="#2563eb"
            )

    # -------------------------------------------------------------------------
    # INTERACCIÓN DEL RATÓN: DRAG & DROP Y RESIZE
    # -------------------------------------------------------------------------
    def _detectar_caja_en_pixel(self, px, py):
        ox = self.offset_x
        oy = self.offset_y
        sx = self.actual_scale_x
        sy = self.actual_scale_y
        pt_x = (px - ox) / sx
        pt_y = (py - oy) / sy

        cajas = self._obtener_cajas_geometria()

        for key, c in cajas.items():
            x1 = c["x_pt"]
            y1 = c["y_pt"]
            x2 = x1 + c["w_pt"]
            y2 = y1 + c["h_pt"]

            if c["tipo"] == "columna":
                # Borde derecho para redimensionar (±5 pt)
                if abs(pt_x - x2) <= 5.0 and (y1 - 2 <= pt_y <= y1 + c.get("h_total_pt", c["h_pt"]) + 2):
                    return key, "resize_col", c
                # Clic en cabecera para arrastrar y soltar
                if x1 <= pt_x <= x2 and y1 <= pt_y <= y2:
                    return key, "drag_col", c

            if x1 <= pt_x <= x2 and y1 <= pt_y <= y2:
                return key, "select", c

        return None, None, None

    def _on_canvas_press(self, event):
        self._cerrar_editor_inline(guardar=True)
        key, mode, c = self._detectar_caja_en_pixel(event.x, event.y)

        if key:
            self.selected_key = key
            if c and "col_idx" in c:
                self.selected_col_idx = c["col_idx"]
                self._cargar_seleccion_en_inspector()
                self._actualizar_combobox_columnas()

            self.drag_data["x"] = event.x
            self.drag_data["y"] = event.y
            self.drag_data["current_mouse_x"] = event.x
            self.drag_data["current_mouse_y"] = event.y
            self.drag_data["elem_key"] = key
            self.drag_data["col_idx"] = c.get("col_idx") if c else None
            self.drag_data["mode"] = mode
            if c:
                self.drag_data["start_ancho"] = c.get("w_pt", 50)

            self._redibujar_guias_canvas()

    def _on_canvas_motion(self, event):
        mode = self.drag_data.get("mode")
        col_idx = self.drag_data.get("col_idx")

        self.drag_data["current_mouse_x"] = event.x
        self.drag_data["current_mouse_y"] = event.y

        if mode == "resize_col" and col_idx is not None and col_idx < len(self.columnas):
            dx_pt = (event.x - self.drag_data["x"]) / self.actual_scale_x
            nuevo_ancho = max(15, min(450, round((self.drag_data["start_ancho"] + dx_pt) / 5.0) * 5))
            if nuevo_ancho != self.columnas[col_idx]["ancho"]:
                self.columnas[col_idx]["ancho"] = nuevo_ancho
                self.var_col_ancho.set(nuevo_ancho)
                self._actualizar_combobox_columnas()
                self._redibujar_guias_canvas()

        elif mode == "drag_col":
            self._redibujar_guias_canvas()

    def _on_canvas_release(self, event):
        mode = self.drag_data.get("mode")
        col_idx = self.drag_data.get("col_idx")
        target_idx = self.drag_data.get("target_insert_idx")

        if mode == "resize_col":
            self.renderizar_y_dibujar()

        elif mode == "drag_col" and col_idx is not None and target_idx is not None:
            if target_idx != col_idx and target_idx != col_idx + 1:
                col_obj = self.columnas.pop(col_idx)
                if target_idx > col_idx:
                    nuevo_slot = target_idx - 1
                else:
                    nuevo_slot = target_idx
                self.columnas.insert(nuevo_slot, col_obj)
                self.selected_col_idx = nuevo_slot
                self.selected_key = f"col_{nuevo_slot}"
                self._actualizar_combobox_columnas()
                self._cargar_seleccion_en_inspector()
                self.renderizar_y_dibujar()
            else:
                self._redibujar_guias_canvas()

        self.drag_data["mode"] = None

    def _on_canvas_hover(self, event):
        key, mode, _c = self._detectar_caja_en_pixel(event.x, event.y)
        if mode == "resize_col":
            self.canvas.config(cursor="sb_h_double_arrow")
        elif mode == "drag_col":
            self.canvas.config(cursor="fleur")
        elif key:
            self.canvas.config(cursor="hand2")
        else:
            self.canvas.config(cursor="arrow")

    def _on_canvas_double_click(self, event):
        key, _mode, c = self._detectar_caja_en_pixel(event.x, event.y)
        if not key or not c:
            return

        x1 = self.offset_x + round(c["x_pt"] * self.actual_scale_x)
        y1 = self.offset_y + round(c["y_pt"] * self.actual_scale_y)
        w = max(int(c["w_pt"] * self.actual_scale_x), 120)
        h = max(int(c["h_pt"] * self.actual_scale_y), 24)

        if c["tipo"] == "columna":
            col = self.columnas[c["col_idx"]]
            texto_actual = col.get("label", "").replace("\n", " ")
        elif c["tipo"] == "titulo":
            texto_actual = self.var_titulo.get()
        elif c["tipo"] == "subtitulo":
            texto_actual = self.var_subtitulo.get()
        elif c["tipo"] == "entidad":
            texto_actual = self.var_entidad.get()
        else:
            return

        self._inline_entry = ttk.Entry(self.canvas, font=("Segoe UI", 9, "bold"))
        self._inline_entry.insert(0, texto_actual)
        self._inline_entry.elem_key = key
        self._inline_entry.col_idx = c.get("col_idx")
        self._inline_entry.tipo = c["tipo"]
        self._inline_entry.place(x=x1, y=y1, width=w, height=h)
        self._inline_entry.focus_set()
        self._inline_entry.select_range(0, tk.END)

        self._inline_entry.bind("<Return>", lambda _e: self._cerrar_editor_inline(guardar=True))
        self._inline_entry.bind("<FocusOut>", lambda _e: self._cerrar_editor_inline(guardar=True))
        self._inline_entry.bind("<Escape>", lambda _e: self._cerrar_editor_inline(guardar=False))

    def _cerrar_editor_inline(self, guardar=True):
        if self._inline_entry is not None:
            try:
                if guardar:
                    txt = self._inline_entry.get().strip()
                    tipo = getattr(self._inline_entry, "tipo", "")
                    col_idx = getattr(self._inline_entry, "col_idx", None)

                    if tipo == "columna" and col_idx is not None:
                        self.columnas[col_idx]["label"] = txt
                        self.var_col_label.set(txt)
                        self._actualizar_combobox_columnas()
                    elif tipo == "titulo":
                        self.var_titulo.set(txt)
                    elif tipo == "subtitulo":
                        self.var_subtitulo.set(txt)
                    elif tipo == "entidad":
                        self.var_entidad.set(txt)

                    self.renderizar_y_dibujar()
                self._inline_entry.destroy()
            except Exception:
                pass
            finally:
                self._inline_entry = None

    # -------------------------------------------------------------------------
    # RESTABLECER Y GUARDAR
    # -------------------------------------------------------------------------
    def _restablecer(self):
        if mb.askyesno("Confirmar", "¿Deseas restaurar la plantilla a los valores predeterminados?", parent=self):
            orig = ReportTemplateManager.reset_template(self.valor)
            self.template = orig
            self.columnas = [dict(c) for c in orig.get("columnas", [])]
            for col in self.columnas:
                col.setdefault("font_size", 7)
                col.setdefault("font_name", "Helvetica")
                col.setdefault("align", "CENTER" if col.get("campo_bd") in ["item", "CodInt", "CodPat", "Estado"] else "LEFT")
                col.setdefault("header_bg", "#DBDBDB")

            self.var_titulo.set(orig.get("titulo", ""))
            self.var_subtitulo.set(orig.get("subtitulo", ""))
            self.var_entidad.set(orig.get("entidad", ""))
            self.var_logo.set(orig.get("logo_path", ""))
            self.var_mostrar_logo.set(orig.get("mostrar_logo", True))
            self.selected_col_idx = 0
            self.selected_key = "col_0"
            self._actualizar_combobox_columnas()
            self._cargar_seleccion_en_inspector()
            self.renderizar_y_dibujar()
            mb.showinfo("Restablecido", "Diseño restablecido a valores predeterminados.", parent=self)

    def _guardar(self):
        visibles = [c for c in self.columnas if c.get("visible", True)]
        if not visibles:
            mb.showwarning("Atención", "Debe haber al menos una columna visible en el reporte.", parent=self)
            return

        nueva_plantilla = {
            "titulo": self.var_titulo.get().strip(),
            "subtitulo": self.var_subtitulo.get().strip(),
            "entidad": self.var_entidad.get().strip(),
            "logo_path": self.var_logo.get().strip(),
            "mostrar_logo": self.var_mostrar_logo.get(),
            "columnas": self.columnas
        }

        ok = ReportTemplateManager.save_template(self.valor, nueva_plantilla)
        if ok:
            mb.showinfo("Éxito", "¡Diseño de reporte guardado correctamente!", parent=self)
            if self.on_save_callback:
                self.on_save_callback(nueva_plantilla)
            self.destroy()
        else:
            mb.showerror("Error", "No se pudo guardar el diseño.", parent=self)
