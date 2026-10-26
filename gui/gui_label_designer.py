import io
import os
import tkinter as tk
from tkinter import ttk, messagebox as mb
from PIL import Image, ImageTk
import fitz
from reportlab.pdfgen import canvas as rl_canvas
from reportlab.lib.units import mm

from label.label_layout import (
    get_label_layout,
    save_label_layout,
    reset_label_layout,
)
from label.label_gen import draw_label_page, _cargar_logo_reader
from utils.config_utils import ConfigUtils
from utils.helpers import resource_path


class Window_label_designer(tk.Toplevel):
    """
    Diseñador visual interactivo WYSIWYG sobre la Vista Previa Real (ReportLab + PyMuPDF):
    Permite seleccionar, arrastrar, redimensionar desde las esquinas y editar con doble clic
    directamente sobre la etiqueta renderizada en tiempo real.
    """

    def __init__(self, parent=None, on_save_callback=None):
        super().__init__(parent)
        self.parent = parent
        self.on_save_callback = on_save_callback

        self.title("Diseñador Interactivo de Etiquetas (Edición Directa sobre Vista Previa Real)")
        try:
            icon_p = resource_path("img/favicon.ico")
            if os.path.exists(icon_p):
                self.iconbitmap(icon_p)
        except Exception:
            pass

        self.geometry("1200x740")
        self.minsize(1060, 650)
        self.configure(bg="#f8fafc")
        self.transient(parent)
        self.grab_set()

        # Datos en memoria
        self.layout = get_label_layout()
        self.selected_key = "denominacion"  # Elemento seleccionado por defecto
        self.scale = 9.0                    # Píxeles por mm para el lienzo principal (50mm = 450px)
        self.offset_x = 38                  # Margen regla izquierda
        self.offset_y = 38                  # Margen regla superior

        # Estado de arrastre / redimensionamiento en ambos lienzos (principal y vista previa derecha)
        self.drag_data = {
            "x": 0,
            "y": 0,
            "mode": None,       # "move" | "resize_se" | "resize_e" | "resize_s"
            "elem_key": None,
            "canvas_scale": 9.0,
            "canvas_ox": 38,
            "canvas_oy": 38,
        }

        # Cache de logo e imágenes PhotoImage para evitar recolección de basura
        self._logo_reader_cache = None
        self._logo_loaded = False
        self.canvas_real_photo = None
        self._updating_widgets = False
        self._inline_entry = None

        # Mostrar u ocultar cajas guía sobre la vista previa real
        self.var_mostrar_guias = tk.BooleanVar(value=True)

        self._crear_interfaz()
        self._cargar_datos_etiqueta()
        self._cargar_elemento_en_inspector(self.selected_key)
        self.redibujar_todo()

    # -------------------------------------------------------------------------
    # CONSTRUCCIÓN DE INTERFAZ
    # -------------------------------------------------------------------------
    def _crear_interfaz(self):
        # 1. Barra de Título Superior
        frame_header = tk.Frame(self, bg="#0f172a", height=52)
        frame_header.pack(fill="x", side="top")

        tk.Label(
            frame_header,
            text="📐 DISEÑADOR INTERACTIVO EN VISTA PREVIA REAL",
            font=("Segoe UI", 12, "bold"),
            fg="#ffffff",
            bg="#0f172a"
        ).pack(side="left", padx=16, pady=10)

        tk.Label(
            frame_header,
            text="|  Arrastre para mover • Esquina inferior derecha para redimensionar • Doble clic para editar el texto directamente",
            font=("Segoe UI", 9),
            fg="#94a3b8",
            bg="#0f172a"
        ).pack(side="left", padx=4, pady=10)

        # 2. Contenedor Principal (2 Columnas)
        paned = tk.PanedWindow(self, orient="horizontal", bg="#cbd5e1", bd=0, sashwidth=5)
        paned.pack(fill="both", expand=True, padx=10, pady=8)

        # Columna Izquierda: Lienzo Interactivo con Vista Previa Real integrada
        self.frame_left = ttk.Frame(paned, padding=8)
        paned.add(self.frame_left, minsize=580, width=630)

        # Columna Derecha: Inspector de Propiedades y Vista Previa Real 1:1 también interactiva
        self.frame_right = ttk.Frame(paned, padding=8)
        paned.add(self.frame_right, minsize=460, width=530)

        self._construir_panel_canvas()
        self._construir_panel_inspector()

        # 3. Barra Inferior de Acciones
        frame_bottom = tk.Frame(self, bg="#f8fafc", bd=1, relief="groove")
        frame_bottom.pack(fill="x", side="bottom", padx=10, pady=(0, 8))

        btn_guardar = ttk.Button(frame_bottom, text="💾 Guardar Diseño", command=self.guardar_configuracion)
        btn_guardar.pack(side="right", padx=6, pady=8)

        btn_cerrar = ttk.Button(frame_bottom, text="✕ Cerrar", command=self.destroy)
        btn_cerrar.pack(side="right", padx=6, pady=8)

        btn_prueba = ttk.Button(frame_bottom, text="🖨️ Imprimir Prueba", command=self.imprimir_etiqueta_prueba)
        btn_prueba.pack(side="left", padx=6, pady=8)

        btn_default = ttk.Button(
            frame_bottom,
            text="↺ Restaurar Predeterminado (50x25mm)",
            command=self.restaurar_valores_defecto
        )
        btn_default.pack(side="left", padx=6, pady=8)

    def _construir_panel_canvas(self):
        top_bar = ttk.Frame(self.frame_left)
        top_bar.pack(fill="x", pady=(0, 6))

        ttk.Label(
            top_bar,
            text="Lienzo de Vista Previa Real Interactivo (1mm = 9px)",
            font=("Segoe UI", 9, "bold")
        ).pack(side="left")

        ttk.Checkbutton(
            top_bar,
            text="Mostrar guías de campos",
            variable=self.var_mostrar_guias,
            command=self.redibujar_todo
        ).pack(side="right", padx=4)

        canvas_container = tk.Frame(self.frame_left, bg="#cbd5e1", bd=1, relief="solid")
        canvas_container.pack(fill="both", expand=True)

        self.canvas = tk.Canvas(canvas_container, bg="#e2e8f0", highlightthickness=0, cursor="hand2")
        self.canvas.pack(fill="both", expand=True)

        # Eventos de ratón para seleccionar, arrastrar, redimensionar y editar inline con doble clic
        self.canvas.bind("<Button-1>", lambda e: self._on_interactive_press(e, self.canvas, self.scale, self.offset_x, self.offset_y))
        self.canvas.bind("<B1-Motion>", self._on_interactive_motion)
        self.canvas.bind("<ButtonRelease-1>", self._on_interactive_release)
        self.canvas.bind("<Double-Button-1>", lambda e: self._on_canvas_double_click(e, self.canvas, self.scale, self.offset_x, self.offset_y))

        # Teclas de dirección para ajuste fino de precisión (0.5 mm)
        self.bind("<Left>", lambda _e: self._nudge_selected(-0.5, 0.0))
        self.bind("<Right>", lambda _e: self._nudge_selected(0.5, 0.0))
        self.bind("<Up>", lambda _e: self._nudge_selected(0.0, -0.5))
        self.bind("<Down>", lambda _e: self._nudge_selected(0.0, 0.5))

        # Botones de alineación rápida bajo el lienzo
        frame_align = ttk.Frame(self.frame_left)
        frame_align.pack(fill="x", pady=(6, 0))

        ttk.Label(frame_align, text="Alineación rápida:", font=("Segoe UI", 8, "italic")).pack(side="left", padx=4)
        ttk.Button(frame_align, text="⬅ Izq (2mm)", command=lambda: self._ajustar_posicion_rapida(x=2.0)).pack(side="left", padx=2)
        ttk.Button(frame_align, text="➡ QR Der (31mm)", command=lambda: self._ajustar_posicion_rapida(x=31.0)).pack(side="left", padx=2)
        ttk.Button(frame_align, text="⬆ Arriba (1mm)", command=lambda: self._ajustar_posicion_rapida(y=1.0)).pack(side="left", padx=2)
        ttk.Button(frame_align, text="⬇ Abajo (20mm)", command=lambda: self._ajustar_posicion_rapida(y=20.0)).pack(side="left", padx=2)

    def _construir_panel_inspector(self):
        # 1. Selector de Elemento + Edición directa de su texto en vivo
        f_elem_sel = ttk.LabelFrame(self.frame_right, text=" 1. Elemento Seleccionado y Texto en Vivo ", padding=8)
        f_elem_sel.pack(fill="x", pady=(0, 6))

        ttk.Label(f_elem_sel, text="Elemento:").grid(row=0, column=0, padx=4, pady=3, sticky="w")

        self.opciones_elementos = [
            ("denominacion", "📝 Denominación del Bien"),
            ("cod_patrimonial", "🏷️ Código Patrimonial"),
            ("cod_interno", "🔢 Código Interno"),
            ("ubicacion", "📍 Oficina / Ubicación"),
            ("inventario", "📅 Inventario / Periodo"),
            ("qr", "📱 Código QR"),
            ("logo", "🖼️ Logo de Entidad"),
            ("entidad", "🏢 Nombre de Entidad"),
        ]

        self.var_elem_sel = tk.StringVar(value="📝 Denominación del Bien")
        self.cbx_elem = ttk.Combobox(
            f_elem_sel,
            textvariable=self.var_elem_sel,
            values=[item[1] for item in self.opciones_elementos],
            state="readonly",
            width=30
        )
        self.cbx_elem.grid(row=0, column=1, padx=6, pady=3, sticky="ew")
        self.cbx_elem.bind("<<ComboboxSelected>>", self._on_combobox_elem_select)

        ttk.Label(f_elem_sel, text="Texto / Dato:").grid(row=1, column=0, padx=4, pady=3, sticky="w")
        self.var_sample_text = tk.StringVar(value="")
        self.etr_sample_text = ttk.Entry(f_elem_sel, textvariable=self.var_sample_text)
        self.etr_sample_text.grid(row=1, column=1, padx=6, pady=3, sticky="ew")
        self.etr_sample_text.bind("<KeyRelease>", self._on_sample_text_entry_change)
        f_elem_sel.columnconfigure(1, weight=1)

        # 2. Propiedades del Elemento Seleccionado
        self.f_props = ttk.LabelFrame(self.frame_right, text=" 2. Posición, Tamaño y Tipografía ", padding=8)
        self.f_props.pack(fill="x", pady=(0, 6))

        self.var_visible = tk.BooleanVar(value=True)
        self.var_x = tk.DoubleVar(value=2.0)
        self.var_y = tk.DoubleVar(value=6.8)
        self.var_w = tk.DoubleVar(value=30.0)
        self.var_h = tk.DoubleVar(value=8.0)
        self.var_font_size = tk.DoubleVar(value=5.0)
        self.var_bold = tk.BooleanVar(value=False)
        self.var_align = tk.StringVar(value="Izquierda")

        self.chk_visible = ttk.Checkbutton(
            self.f_props,
            text="Visible en la etiqueta",
            variable=self.var_visible,
            command=self._on_prop_change
        )
        self.chk_visible.grid(row=0, column=0, columnspan=2, padx=4, pady=(2, 4), sticky="w")

        ttk.Label(self.f_props, text="Posición X (mm):").grid(row=1, column=0, padx=4, pady=3, sticky="w")
        self.spn_x = ttk.Spinbox(
            self.f_props, from_=0.0, to=100.0, increment=0.5,
            textvariable=self.var_x, width=9, command=self._on_prop_change
        )
        self.spn_x.grid(row=1, column=1, padx=4, pady=3, sticky="w")
        self.spn_x.bind("<KeyRelease>", lambda _e: self._on_prop_change())

        ttk.Label(self.f_props, text="Posición Y (mm):").grid(row=1, column=2, padx=(10, 4), pady=3, sticky="w")
        self.spn_y = ttk.Spinbox(
            self.f_props, from_=0.0, to=100.0, increment=0.5,
            textvariable=self.var_y, width=9, command=self._on_prop_change
        )
        self.spn_y.grid(row=1, column=3, padx=4, pady=3, sticky="w")
        self.spn_y.bind("<KeyRelease>", lambda _e: self._on_prop_change())

        ttk.Label(self.f_props, text="Ancho Máx / Ancho (mm):").grid(row=2, column=0, padx=4, pady=3, sticky="w")
        self.spn_w = ttk.Spinbox(
            self.f_props, from_=1.0, to=100.0, increment=0.5,
            textvariable=self.var_w, width=9, command=self._on_prop_change
        )
        self.spn_w.grid(row=2, column=1, padx=4, pady=3, sticky="w")
        self.spn_w.bind("<KeyRelease>", lambda _e: self._on_prop_change())

        self.lbl_h = ttk.Label(self.f_props, text="Alto (mm):")
        self.lbl_h.grid(row=2, column=2, padx=(10, 4), pady=3, sticky="w")
        self.spn_h = ttk.Spinbox(
            self.f_props, from_=1.0, to=100.0, increment=0.5,
            textvariable=self.var_h, width=9, command=self._on_prop_change
        )
        self.spn_h.grid(row=2, column=3, padx=4, pady=3, sticky="w")
        self.spn_h.bind("<KeyRelease>", lambda _e: self._on_prop_change())

        self.lbl_fs = ttk.Label(self.f_props, text="Tamaño Fuente (pt):")
        self.lbl_fs.grid(row=3, column=0, padx=4, pady=3, sticky="w")
        self.spn_fs = ttk.Spinbox(
            self.f_props, from_=3.0, to=30.0, increment=0.5,
            textvariable=self.var_font_size, width=9, command=self._on_prop_change
        )
        self.spn_fs.grid(row=3, column=1, padx=4, pady=3, sticky="w")
        self.spn_fs.bind("<KeyRelease>", lambda _e: self._on_prop_change())

        self.chk_bold = ttk.Checkbutton(
            self.f_props,
            text="Negrita (Bold)",
            variable=self.var_bold,
            command=self._on_prop_change
        )
        self.chk_bold.grid(row=3, column=2, columnspan=2, padx=(10, 4), pady=3, sticky="w")

        self.lbl_align = ttk.Label(self.f_props, text="Alineación:")
        self.lbl_align.grid(row=4, column=0, padx=4, pady=3, sticky="w")
        self.cbx_align = ttk.Combobox(
            self.f_props,
            textvariable=self.var_align,
            values=["Izquierda", "Centro", "Derecha"],
            state="readonly",
            width=12
        )
        self.cbx_align.grid(row=4, column=1, padx=4, pady=3, sticky="w")
        self.cbx_align.bind("<<ComboboxSelected>>", lambda _e: self._on_prop_change())

        # 3. Datos Globales de la Etiqueta (Entidad y Período)
        f_datos = ttk.LabelFrame(self.frame_right, text=" 3. Datos Globales de la Etiqueta (BD) ", padding=8)
        f_datos.pack(fill="x", pady=(0, 6))

        self.var_entidad = tk.StringVar()
        self.var_periodo = tk.StringVar()

        ttk.Label(f_datos, text="Entidad:").grid(row=0, column=0, padx=4, pady=2, sticky="w")
        self.etr_entidad = ttk.Entry(f_datos, textvariable=self.var_entidad)
        self.etr_entidad.grid(row=0, column=1, columnspan=2, padx=4, pady=2, sticky="ew")

        ttk.Label(f_datos, text="Período / Año:").grid(row=1, column=0, padx=4, pady=2, sticky="w")
        self.cbx_periodo = ttk.Combobox(
            f_datos, textvariable=self.var_periodo,
            values=[str(y) for y in range(2018, 2032)],
            state="normal", width=10
        )
        self.cbx_periodo.grid(row=1, column=1, padx=4, pady=2, sticky="w")

        btn_guardar_datos = ttk.Button(
            f_datos, text="💾 Guardar Entidad y Período",
            command=self._guardar_datos_etiqueta
        )
        btn_guardar_datos.grid(row=1, column=2, padx=4, pady=2, sticky="e")

        self.etr_entidad.bind("<KeyRelease>", lambda _e: self._on_datos_change())
        self.cbx_periodo.bind("<<ComboboxSelected>>", lambda _e: self._on_datos_change())
        self.cbx_periodo.bind("<KeyRelease>", lambda _e: self._on_datos_change())
        f_datos.columnconfigure(1, weight=1)

        # 4. Dimensiones de la Etiqueta (Globales)
        f_dim = ttk.LabelFrame(self.frame_right, text=" 4. Dimensiones de la Etiqueta Térmica ", padding=8)
        f_dim.pack(fill="x", pady=(0, 6))

        self.var_lbl_w = tk.DoubleVar(value=float(self.layout.get("label", {}).get("width_mm", 50.0)))
        self.var_lbl_h = tk.DoubleVar(value=float(self.layout.get("label", {}).get("height_mm", 25.0)))

        ttk.Label(f_dim, text="Ancho (mm):").grid(row=0, column=0, padx=4, pady=3, sticky="w")
        spn_lw = ttk.Spinbox(f_dim, from_=20.0, to=150.0, increment=1.0, textvariable=self.var_lbl_w, width=8)
        spn_lw.grid(row=0, column=1, padx=4, pady=3, sticky="w")
        spn_lw.bind("<KeyRelease>", lambda _e: self._on_label_size_change())
        spn_lw.config(command=self._on_label_size_change)

        ttk.Label(f_dim, text="Alto (mm):").grid(row=0, column=2, padx=(12, 4), pady=3, sticky="w")
        spn_lh = ttk.Spinbox(f_dim, from_=15.0, to=100.0, increment=1.0, textvariable=self.var_lbl_h, width=8)
        spn_lh.grid(row=0, column=3, padx=4, pady=3, sticky="w")
        spn_lh.bind("<KeyRelease>", lambda _e: self._on_label_size_change())
        spn_lh.config(command=self._on_label_size_change)

    # -------------------------------------------------------------------------
    # RENDERIZADO EN MEMORIA DE LA VISTA PREVIA REAL (REPORTLAB + PYMUPDF)
    # -------------------------------------------------------------------------
    def _obtener_logo_reader(self):
        if not self._logo_loaded:
            self._logo_loaded = True
            try:
                cfg_inst = ConfigUtils()
                direccion = cfg_inst.load_config()
                self._logo_reader_cache = _cargar_logo_reader(direccion)
            except Exception:
                self._logo_reader_cache = None
        return self._logo_reader_cache

    def _construir_sample_data_actual(self) -> dict:
        """Toma los textos actuales de muestra del lienzo y de los campos Entidad/Período."""
        elems = self.layout.get("elements", {})
        ent = self.var_entidad.get().strip() if hasattr(self, "var_entidad") else ""
        per = self.var_periodo.get().strip() if hasattr(self, "var_periodo") else ""

        ent_sample = ent or elems.get("entidad", {}).get("sample", "MUNICIPALIDAD EJEMPLO")
        inv_sample = (f"INVENTARIO {per}" if per else elems.get("inventario", {}).get("sample", "INVENTARIO 2026"))

        return {
            "entidad": ent_sample,
            "den": elems.get("denominacion", {}).get("sample", "COMPUTADORA PORTATIL CORE I7"),
            "codint": elems.get("cod_interno", {}).get("sample", "1052"),
            "codpatr": elems.get("cod_patrimonial", {}).get("sample", "740899990001"),
            "ubi": elems.get("ubicacion", {}).get("sample", "ALMACEN CENTRAL - OFICINA 101"),
            "inv": inv_sample,
        }

    def _renderizar_etiqueta_pil(self, target_w_px: int, target_h_px: int) -> Image.Image | None:
        """
        Genera el PDF real con ReportLab en un buffer de memoria (sin tocar el disco)
        y lo convierte en una imagen PIL de alta definición del tamaño exacto solicitado.
        """
        try:
            lbl_w_mm = float(self.layout.get("label", {}).get("width_mm", 50.0))
            lbl_h_mm = float(self.layout.get("label", {}).get("height_mm", 25.0))
            sample_data = self._construir_sample_data_actual()

            pdf_buffer = io.BytesIO()
            c = rl_canvas.Canvas(pdf_buffer)
            c.setPageSize((lbl_w_mm * mm, lbl_h_mm * mm))

            draw_label_page(
                c,
                sample_data.get("den", ""),
                sample_data.get("codint", ""),
                sample_data.get("codpatr", ""),
                sample_data.get("ubi", ""),
                sample_data.get("inv", ""),
                sample_data.get("entidad", ""),
                logo_reader=self._obtener_logo_reader(),
                layout=self.layout,
            )
            c.showPage()
            c.save()

            pdf_bytes = pdf_buffer.getvalue()
            with fitz.open(stream=pdf_bytes, filetype="pdf") as doc:
                page = doc[0]
                zoom_x = max(target_w_px / max(page.rect.width, 1.0), 1.0)
                zoom_y = max(target_h_px / max(page.rect.height, 1.0), 1.0)
                pix = page.get_pixmap(matrix=fitz.Matrix(zoom_x, zoom_y), alpha=False)
                pil_img = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
                if pil_img.size != (int(target_w_px), int(target_h_px)):
                    pil_img = pil_img.resize((int(target_w_px), int(target_h_px)), Image.Resampling.LANCZOS)
                return pil_img
        except Exception as e:
            print(f"Error al renderizar vista previa en memoria: {e}")
            return None

    # -------------------------------------------------------------------------
    # DIBUJADO DEL LIENZO INTERACTIVO + VISTA PREVIA REAL
    # -------------------------------------------------------------------------
    def _obtener_dimensiones_elemento(self, key: str, cfg: dict) -> tuple[float, float]:
        if key in ("qr", "logo"):
            return float(cfg.get("width_mm", 18.0 if key == "qr" else 5.3)), float(cfg.get("height_mm", 18.0 if key == "qr" else 5.3))
        w_mm = float(cfg.get("max_width_mm", 25.0))
        font_pt = float(cfg.get("font_size", 6.0))
        default_h = max(round(font_pt * 0.55, 1), 3.2)
        h_mm = float(cfg.get("max_height_mm", default_h))
        return w_mm, h_mm

    def redibujar_todo(self):
        """Redibuja el lienzo interactivo con la vista previa real en vivo."""
        self.redibujar_canvas()

    def redibujar_canvas(self):
        """Dibuja las reglas milimétricas, la Vista Previa Real en vivo y las guías interactivas."""
        self.canvas.delete("all")

        lbl_w_mm = float(self.layout.get("label", {}).get("width_mm", 50.0))
        lbl_h_mm = float(self.layout.get("label", {}).get("height_mm", 25.0))

        label_w_px = int(round(lbl_w_mm * self.scale))
        label_h_px = int(round(lbl_h_mm * self.scale))

        ox = self.offset_x
        oy = self.offset_y

        # 1. Regla Superior (X)
        self.canvas.create_rectangle(ox, oy - 22, ox + label_w_px, oy, fill="#f1f5f9", outline="#94a3b8")
        for mm_x in range(0, int(lbl_w_mm) + 1, 5):
            px = ox + mm_x * self.scale
            h_tick = 8 if mm_x % 10 == 0 else 4
            self.canvas.create_line(px, oy, px, oy - h_tick, fill="#475569")
            if mm_x % 10 == 0:
                self.canvas.create_text(px, oy - 14, text=str(mm_x), font=("Segoe UI", 7, "bold"), fill="#1e293b")

        # 2. Regla Izquierda (Y)
        self.canvas.create_rectangle(ox - 24, oy, ox, oy + label_h_px, fill="#f1f5f9", outline="#94a3b8")
        for mm_y in range(0, int(lbl_h_mm) + 1, 5):
            py = oy + mm_y * self.scale
            w_tick = 8 if mm_y % 10 == 0 else 4
            self.canvas.create_line(ox, py, ox - w_tick, py, fill="#475569")
            if mm_y % 10 == 0:
                self.canvas.create_text(ox - 13, py, text=str(mm_y), font=("Segoe UI", 7, "bold"), fill="#1e293b")

        # 3. Sombra y Fondo Real de la Etiqueta (ReportLab renderizado en vivo)
        self.canvas.create_rectangle(ox + 4, oy + 4, ox + label_w_px + 4, oy + label_h_px + 4, fill="#94a3b8", outline="")
        self.canvas.create_rectangle(ox, oy, ox + label_w_px, oy + label_h_px, fill="#ffffff", outline="#1e293b", width=2)

        pil_real = self._renderizar_etiqueta_pil(label_w_px, label_h_px)
        if pil_real is not None:
            self.canvas_real_photo = ImageTk.PhotoImage(pil_real)
            self.canvas.create_image(ox, oy, image=self.canvas_real_photo, anchor="nw")

        # 4. Superponer guías interactivas y manijas de selección/redimensionamiento
        self._dibujar_guias_en_canvas(self.canvas, self.scale, ox, oy, mostrar_no_seleccionados=self.var_mostrar_guias.get())

    def _dibujar_guias_en_canvas(self, target_canvas: tk.Canvas, scale: float, ox: float, oy: float, mostrar_no_seleccionados: bool):
        """Dibuja los contornos interactivos y manijas sobre el canvas indicado."""
        elems = self.layout.get("elements", {})
        for key, cfg in elems.items():
            if not cfg.get("visible", True):
                continue

            is_selected = (key == self.selected_key)
            if not is_selected and not mostrar_no_seleccionados:
                continue

            x_mm = float(cfg.get("x_mm", 0.0))
            y_mm = float(cfg.get("y_mm", 0.0))
            w_mm, h_mm = self._obtener_dimensiones_elemento(key, cfg)

            x1 = ox + x_mm * scale
            y1 = oy + y_mm * scale
            x2 = x1 + w_mm * scale
            y2 = y1 + h_mm * scale

            if is_selected:
                # Contorno activo azul con etiqueta superior y manija de redimensionamiento en esquina SE
                target_canvas.create_rectangle(
                    x1, y1, x2, y2,
                    outline="#2563eb",
                    width=2,
                )
                nombre_corto = cfg.get("nombre", key)
                badge_text = f" {nombre_corto} ({x_mm:.1f}, {y_mm:.1f} mm) "
                badge_y = max(y1 - 13, 2)
                target_canvas.create_rectangle(
                    x1, badge_y, x1 + len(badge_text) * 5.3, badge_y + 13,
                    fill="#2563eb", outline="#2563eb"
                )
                target_canvas.create_text(
                    x1 + 3, badge_y + 6,
                    text=badge_text,
                    anchor="w",
                    font=("Segoe UI", 7, "bold"),
                    fill="#ffffff"
                )

                # Manijas en las 4 esquinas (la inferior derecha redimensiona ancho/alto)
                hs = 4
                for hx, hy, fill_c in [
                    (x1, y1, "#2563eb"),
                    (x2, y1, "#2563eb"),
                    (x1, y2, "#2563eb"),
                    (x2, y2, "#dc2626"),  # Esquina SE destacada para redimensionar
                ]:
                    target_canvas.create_rectangle(
                        hx - hs, hy - hs, hx + hs, hy + hs,
                        fill=fill_c, outline="#ffffff", width=1
                    )
            else:
                # Guía punteada sutil para elementos no seleccionados
                target_canvas.create_rectangle(
                    x1, y1, x2, y2,
                    outline="#94a3b8",
                    dash=(3, 3),
                    width=1,
                )

    # -------------------------------------------------------------------------
    # INTERACCIÓN DIRECTA: SELECCIONAR, MOVER, REDIMENSIONAR Y DOBLE CLIC INLINE
    # -------------------------------------------------------------------------
    def _cerrar_editor_inline(self, guardar=True):
        if self._inline_entry is not None:
            try:
                if guardar:
                    nuevo_txt = self._inline_entry.get().strip()
                    key = getattr(self._inline_entry, "elem_key", None)
                    if key:
                        self._aplicar_texto_a_elemento(key, nuevo_txt)
                self._inline_entry.destroy()
            except Exception:
                pass
            self._inline_entry = None

    def _aplicar_texto_a_elemento(self, key: str, nuevo_txt: str):
        cfg = self.layout.get("elements", {}).get(key)
        if not cfg:
            return
        cfg["sample"] = nuevo_txt
        if key == "entidad":
            self.var_entidad.set(nuevo_txt)
        elif key == "inventario":
            limpio = nuevo_txt.upper().replace("INVENTARIO", "").strip()
            if limpio:
                self.var_periodo.set(limpio)
        if key == self.selected_key:
            self._updating_widgets = True
            self.var_sample_text.set(nuevo_txt)
            self._updating_widgets = False
        self.redibujar_todo()

    def _detectar_elemento_en_punto(self, click_x_mm: float, click_y_mm: float) -> tuple[str | None, str]:
        """
        Devuelve `(elem_key, mode)` donde `mode` es `'resize_se'` si se presionó
        la esquina inferior derecha del elemento seleccionado, o `'move'`.
        """
        elems = self.layout.get("elements", {})

        # 1. Comprobar primero si se presionó la esquina de redimensionamiento del elemento seleccionado
        if self.selected_key in elems and elems[self.selected_key].get("visible", True):
            cfg_sel = elems[self.selected_key]
            sx = float(cfg_sel.get("x_mm", 0.0))
            sy = float(cfg_sel.get("y_mm", 0.0))
            sw, sh = self._obtener_dimensiones_elemento(self.selected_key, cfg_sel)
            if abs(click_x_mm - (sx + sw)) <= 1.8 and abs(click_y_mm - (sy + sh)) <= 1.8:
                return self.selected_key, "resize_se"

        # 2. Buscar qué elemento contiene el punto clicado
        for key in reversed(list(elems.keys())):
            cfg = elems[key]
            if not cfg.get("visible", True):
                continue
            x_mm = float(cfg.get("x_mm", 0.0))
            y_mm = float(cfg.get("y_mm", 0.0))
            w_mm, h_mm = self._obtener_dimensiones_elemento(key, cfg)
            if x_mm <= click_x_mm <= (x_mm + w_mm) and y_mm <= click_y_mm <= (y_mm + h_mm):
                return key, "move"

        return None, "move"

    def _on_interactive_press(self, event, active_canvas: tk.Canvas, scale: float, ox: float, oy: float):
        """Selecciona un elemento o inicia su arrastre/redimensionamiento en cualquiera de las vistas."""
        self._cerrar_editor_inline(guardar=True)

        click_x_mm = (event.x - ox) / scale
        click_y_mm = (event.y - oy) / scale

        clicked_key, mode = self._detectar_elemento_en_punto(click_x_mm, click_y_mm)
        if clicked_key:
            self.selected_key = clicked_key
            self.drag_data["x"] = event.x
            self.drag_data["y"] = event.y
            self.drag_data["elem_key"] = clicked_key
            self.drag_data["mode"] = mode
            self.drag_data["canvas_scale"] = scale
            self.drag_data["canvas_ox"] = ox
            self.drag_data["canvas_oy"] = oy

            for k, label_text in self.opciones_elementos:
                if k == clicked_key:
                    self.var_elem_sel.set(label_text)
                    break
            self._cargar_elemento_en_inspector(clicked_key)
            self.redibujar_todo()

    def _on_interactive_motion(self, event):
        """Arrastra o redimensiona en vivo sobre la Vista Previa Real."""
        key = self.drag_data.get("elem_key")
        if not key or key not in self.layout.get("elements", {}):
            return

        scale = self.drag_data.get("canvas_scale", self.scale)
        dx_mm = (event.x - self.drag_data["x"]) / scale
        dy_mm = (event.y - self.drag_data["y"]) / scale

        if abs(dx_mm) < 0.25 and abs(dy_mm) < 0.25:
            return

        cfg = self.layout["elements"][key]
        lbl_w = float(self.layout.get("label", {}).get("width_mm", 50.0))
        lbl_h = float(self.layout.get("label", {}).get("height_mm", 25.0))
        mode = self.drag_data.get("mode", "move")

        if mode == "resize_se":
            w_actual, h_actual = self._obtener_dimensiones_elemento(key, cfg)
            nuevo_w = max(2.0, min(round((w_actual + dx_mm) * 2.0) / 2.0, lbl_w))
            nuevo_h = max(2.0, min(round((h_actual + dy_mm) * 2.0) / 2.0, lbl_h))

            if key in ("qr", "logo"):
                cfg["width_mm"] = nuevo_w
                cfg["height_mm"] = nuevo_h
            else:
                cfg["max_width_mm"] = nuevo_w
                cfg["max_height_mm"] = nuevo_h

            self.drag_data["x"] = event.x
            self.drag_data["y"] = event.y
            self._updating_widgets = True
            self.var_w.set(nuevo_w)
            self.var_h.set(nuevo_h)
            self._updating_widgets = False
            self.redibujar_todo()
        else:
            nueva_x = round((float(cfg.get("x_mm", 0.0)) + dx_mm) * 2.0) / 2.0
            nueva_y = round((float(cfg.get("y_mm", 0.0)) + dy_mm) * 2.0) / 2.0
            nueva_x = max(0.0, min(nueva_x, lbl_w - 1.5))
            nueva_y = max(0.0, min(nueva_y, lbl_h - 1.5))

            if nueva_x != cfg.get("x_mm") or nueva_y != cfg.get("y_mm"):
                cfg["x_mm"] = nueva_x
                cfg["y_mm"] = nueva_y
                self.drag_data["x"] = event.x
                self.drag_data["y"] = event.y

                self._updating_widgets = True
                self.var_x.set(nueva_x)
                self.var_y.set(nueva_y)
                self._updating_widgets = False
                self.redibujar_todo()

    def _on_interactive_release(self, _event):
        self.drag_data["elem_key"] = None
        self.drag_data["mode"] = None

    def _on_canvas_double_click(self, event, active_canvas: tk.Canvas, scale: float, ox: float, oy: float):
        """Abre un cuadro de edición inline directamente sobre el elemento clicado en la Vista Previa Real."""
        self._cerrar_editor_inline(guardar=True)

        click_x_mm = (event.x - ox) / scale
        click_y_mm = (event.y - oy) / scale
        clicked_key, _ = self._detectar_elemento_en_punto(click_x_mm, click_y_mm)

        if not clicked_key or clicked_key == "logo":
            return

        self.selected_key = clicked_key
        self._cargar_elemento_en_inspector(clicked_key)
        cfg = self.layout["elements"][clicked_key]

        x_mm = float(cfg.get("x_mm", 0.0))
        y_mm = float(cfg.get("y_mm", 0.0))
        w_mm, _h_mm = self._obtener_dimensiones_elemento(clicked_key, cfg)

        px = int(ox + x_mm * scale)
        py = int(oy + y_mm * scale)
        pw = max(int(w_mm * scale), 140)

        sample_data = self._construir_sample_data_actual()
        key_to_sample = {
            "entidad": sample_data["entidad"],
            "denominacion": sample_data["den"],
            "cod_patrimonial": sample_data["codpatr"],
            "cod_interno": sample_data["codint"],
            "ubicacion": sample_data["ubi"],
            "inventario": sample_data["inv"],
            "qr": sample_data["codpatr"],
        }
        valor_inicial = key_to_sample.get(clicked_key, cfg.get("sample", ""))

        entry = tk.Entry(
            active_canvas,
            font=("Segoe UI", 9, "bold"),
            bg="#fef9c3",
            fg="#0f172a",
            relief="solid",
            bd=2
        )
        entry.elem_key = clicked_key
        entry.insert(0, valor_inicial)
        entry.select_range(0, tk.END)
        entry.place(x=px, y=py, width=pw, height=24)
        entry.focus_set()

        entry.bind("<Return>", lambda _e: self._cerrar_editor_inline(guardar=True))
        entry.bind("<Escape>", lambda _e: self._cerrar_editor_inline(guardar=False))
        entry.bind("<FocusOut>", lambda _e: self._cerrar_editor_inline(guardar=True))
        self._inline_entry = entry

    def _nudge_selected(self, dx_mm: float, dy_mm: float):
        """Mueve el elemento seleccionado con las flechas del teclado si el foco no está en un Entry."""
        focused = self.focus_get()
        if isinstance(focused, (tk.Entry, ttk.Entry, ttk.Spinbox, ttk.Combobox)):
            return
        cfg = self.layout.get("elements", {}).get(self.selected_key)
        if not cfg:
            return
        lbl_w = float(self.layout.get("label", {}).get("width_mm", 50.0))
        lbl_h = float(self.layout.get("label", {}).get("height_mm", 25.0))
        nx = max(0.0, min(round(float(cfg.get("x_mm", 0.0)) + dx_mm, 1), lbl_w - 1.0))
        ny = max(0.0, min(round(float(cfg.get("y_mm", 0.0)) + dy_mm, 1), lbl_h - 1.0))
        cfg["x_mm"] = nx
        cfg["y_mm"] = ny
        self._updating_widgets = True
        self.var_x.set(nx)
        self.var_y.set(ny)
        self._updating_widgets = False
        self.redibujar_todo()

    # -------------------------------------------------------------------------
    # MANEJO DEL INSPECTOR DE PROPIEDADES
    # -------------------------------------------------------------------------
    def _on_combobox_elem_select(self, _event=None):
        texto_sel = self.var_elem_sel.get()
        for k, label_text in self.opciones_elementos:
            if label_text == texto_sel:
                self.selected_key = k
                self._cargar_elemento_en_inspector(k)
                self.redibujar_todo()
                break

    def _on_sample_text_entry_change(self, _event=None):
        if self._updating_widgets:
            return
        self._aplicar_texto_a_elemento(self.selected_key, self.var_sample_text.get())

    def _cargar_elemento_en_inspector(self, key):
        """Carga las propiedades del elemento seleccionado en los widgets del inspector."""
        cfg = self.layout.get("elements", {}).get(key)
        if not cfg:
            return

        self._updating_widgets = True

        self.var_visible.set(bool(cfg.get("visible", True)))
        self.var_x.set(float(cfg.get("x_mm", 0.0)))
        self.var_y.set(float(cfg.get("y_mm", 0.0)))

        sample_actual = self._construir_sample_data_actual()
        sample_map = {
            "entidad": sample_actual["entidad"],
            "denominacion": sample_actual["den"],
            "cod_patrimonial": sample_actual["codpatr"],
            "cod_interno": sample_actual["codint"],
            "ubicacion": sample_actual["ubi"],
            "inventario": sample_actual["inv"],
            "qr": sample_actual["codpatr"],
            "logo": "(Imagen de Logo)",
        }
        self.var_sample_text.set(sample_map.get(key, cfg.get("sample", "")))
        self.etr_sample_text.configure(state="disabled" if key == "logo" else "normal")

        is_graphic = (key in ("qr", "logo"))

        if is_graphic:
            self.var_w.set(float(cfg.get("width_mm", 10.0)))
            self.var_h.set(float(cfg.get("height_mm", 10.0)))
            self.lbl_h.grid()
            self.spn_h.grid()

            self.lbl_fs.grid_remove()
            self.spn_fs.grid_remove()
            self.chk_bold.grid_remove()
            self.lbl_align.grid_remove()
            self.cbx_align.grid_remove()
        else:
            self.var_w.set(float(cfg.get("max_width_mm", 30.0)))
            self.var_h.set(float(cfg.get("max_height_mm", 8.0)))
            self.var_font_size.set(float(cfg.get("font_size", 6.0)))
            self.var_bold.set(bool(cfg.get("font_bold", False)))

            align_val = cfg.get("align", "left")
            align_esp = {"left": "Izquierda", "center": "Centro", "right": "Derecha"}.get(align_val, "Izquierda")
            self.var_align.set(align_esp)

            self.lbl_h.grid_remove()
            self.spn_h.grid_remove()

            self.lbl_fs.grid()
            self.spn_fs.grid()
            self.chk_bold.grid()
            self.lbl_align.grid()
            self.cbx_align.grid()

        self._updating_widgets = False

    def _on_prop_change(self):
        """Se ejecuta cuando el usuario modifica cualquier Spinbox, Checkbox o Combo."""
        if self._updating_widgets:
            return

        key = self.selected_key
        cfg = self.layout.get("elements", {}).get(key)
        if not cfg:
            return

        try:
            cfg["visible"] = self.var_visible.get()
            cfg["x_mm"] = round(float(self.var_x.get()), 1)
            cfg["y_mm"] = round(float(self.var_y.get()), 1)

            is_graphic = (key in ("qr", "logo"))
            if is_graphic:
                cfg["width_mm"] = round(float(self.var_w.get()), 1)
                cfg["height_mm"] = round(float(self.var_h.get()), 1)
            else:
                cfg["max_width_mm"] = round(float(self.var_w.get()), 1)
                cfg["font_size"] = round(float(self.var_font_size.get()), 1)
                cfg["font_bold"] = self.var_bold.get()

                align_eng = {"Izquierda": "left", "Centro": "center", "Derecha": "right"}.get(self.var_align.get(), "left")
                cfg["align"] = align_eng
        except ( tk.TclError, ValueError ):
            return

        self.redibujar_todo()

    def _on_label_size_change(self):
        """Actualiza las dimensiones totales de la etiqueta."""
        try:
            self.layout["label"]["width_mm"] = float(self.var_lbl_w.get())
            self.layout["label"]["height_mm"] = float(self.var_lbl_h.get())
            self.redibujar_todo()
        except (tk.TclError, ValueError):
            pass

    def _ajustar_posicion_rapida(self, x=None, y=None):
        """Ajuste rápido de coordenadas con un clic."""
        key = self.selected_key
        cfg = self.layout.get("elements", {}).get(key)
        if not cfg:
            return
        if x is not None:
            cfg["x_mm"] = float(x)
            self.var_x.set(float(x))
        if y is not None:
            cfg["y_mm"] = float(y)
            self.var_y.set(float(y))

        self.redibujar_todo()

    # -------------------------------------------------------------------------
    # DATOS DE ENTIDAD Y PERÍODO Y PERSISTENCIA
    # -------------------------------------------------------------------------
    def _cargar_datos_etiqueta(self):
        """Carga entidad y período desde la BD / config.ini al abrir el diseñador."""
        try:
            from db.query import datos_iniciales
            datos = datos_iniciales()
            if datos:
                ent = str(datos[1] or "")
                per = str(datos[2] or "")
                self.var_entidad.set(ent)
                self.var_periodo.set(per)
                if ent and "entidad" in self.layout.get("elements", {}):
                    self.layout["elements"]["entidad"]["sample"] = ent
                if per and "inventario" in self.layout.get("elements", {}):
                    self.layout["elements"]["inventario"]["sample"] = f"INVENTARIO {per}"
        except Exception as e:
            print(f"Error cargando datos iniciales: {e}")

    def _guardar_datos_etiqueta(self):
        """Guarda entidad y período en la BD y config.ini, luego refresca la vista previa."""
        from db.query import actualizar_datos
        entidad = self.var_entidad.get().strip()
        periodo = self.var_periodo.get().strip()
        try:
            actualizar_datos(1, [entidad, periodo, ""])
            mb.showinfo(
                "Datos Guardados",
                f"Entidad y período guardados con éxito.\n\nEntidad: {entidad}\nPeríodo: {periodo}",
                parent=self
            )
            self.redibujar_todo()
        except Exception as e:
            mb.showerror("Error", f"No se pudo guardar:\n{e}", parent=self)

    def _on_datos_change(self):
        """Sincroniza el cambio de Entidad o Período con la vista previa en vivo."""
        ent = self.var_entidad.get().strip()
        per = self.var_periodo.get().strip()
        if "entidad" in self.layout.get("elements", {}) and ent:
            self.layout["elements"]["entidad"]["sample"] = ent
        if "inventario" in self.layout.get("elements", {}) and per:
            self.layout["elements"]["inventario"]["sample"] = f"INVENTARIO {per}"
        if self.selected_key in ("entidad", "inventario"):
            self._cargar_elemento_en_inspector(self.selected_key)
        self.redibujar_todo()

    def guardar_configuracion(self):
        """Persiste la configuración en el archivo JSON y datos de entidad/período en BD."""
        self._cerrar_editor_inline(guardar=True)
        if hasattr(self, "var_entidad") and hasattr(self, "var_periodo"):
            try:
                from db.query import actualizar_datos
                entidad = self.var_entidad.get().strip()
                periodo = self.var_periodo.get().strip()
                if entidad or periodo:
                    actualizar_datos(1, [entidad, periodo, ""])
            except Exception as e:
                print(f"Error sincronizando datos: {e}")
        ok, msg = save_label_layout(self.layout)
        if ok:
            mb.showinfo(
                "Diseñador de Etiquetas",
                "¡Diseño de etiqueta guardado con éxito!\nSe aplicará a todas las impresiones.",
                parent=self
            )
            if self.on_save_callback:
                try:
                    self.on_save_callback()
                except Exception as e:
                    print(f"Error en callback on_save: {e}")
        else:
            mb.showerror("Error al guardar", msg, parent=self)

    def restaurar_valores_defecto(self):
        """Restaura los valores estándar 50x25 mm."""
        if mb.askyesno("Confirmar", "¿Desea restaurar el diseño de etiqueta a los valores predeterminados (50x25 mm)?", parent=self):
            _ok, default_layout = reset_label_layout()
            self.layout = default_layout
            self.var_lbl_w.set(self.layout["label"]["width_mm"])
            self.var_lbl_h.set(self.layout["label"]["height_mm"])
            self._cargar_datos_etiqueta()
            self._cargar_elemento_en_inspector(self.selected_key)
            self.redibujar_todo()
            if self.on_save_callback:
                self.on_save_callback()
            mb.showinfo("Restaurado", "Diseño restaurado a los valores predeterminados.", parent=self)

    def imprimir_etiqueta_prueba(self):
        """Imprime directamente una etiqueta de prueba en la impresora térmica."""
        try:
            from label.label_gen import build_label
            from db.query import mostrar_datos_bienes
            bienes = mostrar_datos_bienes()
            if bienes and len(bienes) > 0:
                cod_prueba = bienes[0][0]
                acta_prueba = bienes[0][1]
            else:
                cod_prueba = "1001"
                acta_prueba = "1"

            save_label_layout(self.layout)
            build_label(1, cod_prueba, acta_prueba, oficina_personalizada="OFICINA PRUEBA")
            mb.showinfo("Impresión", "Se envió la etiqueta de prueba a la impresora térmica configurada.", parent=self)
        except Exception as e:
            mb.showerror("Error al imprimir prueba", f"No se pudo enviar la prueba de impresión:\n{e}", parent=self)
