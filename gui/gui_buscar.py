import os
import threading
import urllib.request
import tkinter as tk
from datetime import datetime
from tkinter import ttk, PhotoImage, filedialog, messagebox as mb
from PIL import Image, ImageTk

from utils.order_utils import sort_by
from utils.api_client import ApiManagerAcontarSacClient
from data.exp_excel import exportar_excel
from utils.helpers import resource_path
from db.query import (
    buscar_data,
    buscar_bien_d,
    actualizar_detalles,
    actualizar_registro,
    cambio_detalles,
    insertar_tabla2,
    obtener_fotos_bien,
    agregar_foto_bien,
    eliminar_foto_bien,
)

_RENDER_CHUNK_SIZE = 400


class Window_buscar(tk.Toplevel):
    def __init__(self, root=None, user=None, team=None):
        super().__init__(root)
        self.root = root
        self.user = user
        self.team = team
        self.title("Búsqueda, Gestión y Control Fotográfico de Bienes Patrimoniales - AEC S.A.C.")

        # Dimensiones y límites de ventana
        self.geometry("1260x760")
        self.minsize(1040, 620)
        self.configure(bg="#f8fafc")

        # Directorio local de fotografías y cliente API
        base_dir = os.path.dirname(os.path.abspath(__file__))
        self.photos_dir = os.path.normpath(os.path.join(base_dir, "..", "photos"))
        os.makedirs(self.photos_dir, exist_ok=True)
        self.api_client = getattr(self.root, "api_client", None) or ApiManagerAcontarSacClient()

        # Estado de galería fotográfica del bien seleccionado
        self.fotos_bien_actual = []
        self.foto_idx_actual = 0
        self._tk_preview_img = None
        self._current_preview_path = None
        self._render_token = 0
        self._select_debounce_job = None
        self._raw_rows_cache = []

        # Configurar icono de ventana
        icon_path = resource_path(os.path.join("img", "favicon.ico"))
        if os.path.exists(icon_path):
            try:
                self.iconbitmap(icon_path)
            except Exception:
                pass

        # Cargar iconos de forma segura
        self.iconoBuscar = self._cargar_icono("img/buscar.png")
        self.iconoExcel = self._cargar_icono("img/excel.png")

        # Contenedor raíz
        self.frame_u = tk.Frame(self, bg="#f8fafc")
        self.frame_u.pack(fill='both', expand=True, padx=12, pady=10)

        # Variables y estilos
        self.variables()
        self._configurar_estilos()

        # Componentes de la interfaz
        self.widgets()
        self.widget_field_botton()

        # Cargar búsqueda inicial
        self.buscar()

        # Enlaces de eventos
        self.tree.bind("<<TreeviewSelect>>", self._on_tree_select_debounced)
        self.tree.bind("<Double-Button-1>", self.mostrar_datos_)
        self.etrCod.bind("<Return>", lambda e: self.buscar_cod())
        self.etrBien.bind("<Return>", lambda e: self.buscar())

        # Centrar ventana
        self._centrar_ventana()
        self.focus_set()

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

        # Labels y Cards
        style.configure('Card.TLabelframe', background='#ffffff', relief='solid', borderwidth=1, bordercolor='#e2e8f0')
        style.configure('Card.TLabelframe.Label', background='#ffffff', foreground='#0f172a', font=('Segoe UI', 10, 'bold'))

        style.configure('BuscarField.TLabel', background='#ffffff', foreground='#334155', font=('Segoe UI', 9))
        style.configure('BuscarBold.TLabel', background='#ffffff', foreground='#0f172a', font=('Segoe UI', 9, 'bold'))

        # Botones
        style.configure('Action.TButton', font=('Segoe UI', 9), padding=(6, 3))
        style.configure('Primary.TButton', font=('Segoe UI', 9, 'bold'), padding=(8, 4))
        style.configure('Success.TButton', font=('Segoe UI', 9, 'bold'), padding=(8, 4))

        # Treeview
        style.configure(
            'Buscar.Treeview',
            font=('Segoe UI', 9),
            rowheight=26,
            background='#ffffff',
            fieldbackground='#ffffff',
            bordercolor='#e2e8f0',
            borderwidth=1
        )
        style.configure(
            'Buscar.Treeview.Heading',
            font=('Segoe UI', 9, 'bold'),
            background='#f1f5f9',
            foreground='#1e293b',
            padding=(5, 6)
        )
        style.map('Buscar.Treeview', background=[('selected', '#2563eb')], foreground=[('selected', '#ffffff')])

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

    def variables(self):
        self.codi = tk.StringVar()
        self.deno = tk.StringVar()
        self.inve = tk.StringVar()
        self.codp = tk.StringVar()
        self.acta = tk.StringVar()
        self.marc = tk.StringVar()
        self.seri = tk.StringVar()
        self.fech = tk.StringVar()
        self.dadq = tk.StringVar()
        self.mode = tk.StringVar()
        self.colo = tk.StringVar()
        self.aact = tk.StringVar()
        self.esta = tk.StringVar()
        self.dime = tk.StringVar()
        self.obse = tk.StringVar()

        self.otro = tk.StringVar()
        self.situ = tk.StringVar()
        self.tipo = tk.StringVar()
        self.valo = tk.StringVar()
        self.ctac = tk.StringVar()
        self.cint = tk.StringVar()

        self.bien = tk.StringVar()
        self.crit = tk.StringVar(value="DenBien")
        self.filtro_fotos_var = tk.StringVar(value="Todos los bienes")
        self.total_encontrados_var = tk.StringVar(value="📦 Total: 0")
        self.total_con_foto_var = tk.StringVar(value="📷 Con foto: 0")
        self.total_sin_foto_var = tk.StringVar(value="⚠️ Sin foto: 0")

    def widgets(self):
        # ---- Card Superior: Ficha de Detalle + Panel de Fotografías ----
        self.card_detalle = ttk.LabelFrame(
            self.frame_u,
            text=" 🔍 Ficha de Detalle, Edición y Fotografías del Bien (asset_photos) ",
            style='Card.TLabelframe',
            padding=(12, 8)
        )
        self.card_detalle.pack(fill="x", side='top', pady=(0, 8))

        main_top = tk.Frame(self.card_detalle, bg="#ffffff")
        main_top.pack(fill="both", expand=True)

        # Lado izquierdo: Formulario de datos del bien
        content = tk.Frame(main_top, bg="#ffffff")
        content.pack(side="left", fill="both", expand=True, padx=(0, 12))

        # Lado derecho: Panel de Fotografías del Bien
        self._construir_panel_fotos(main_top)

        # Fila 0: Búsqueda rápida por código y botones de acción
        top_bar = tk.Frame(content, bg="#ffffff")
        top_bar.pack(fill="x", pady=(0, 8))

        ttk.Label(top_bar, text="Cód. Bien:", style='BuscarBold.TLabel').pack(side='left', padx=(0, 6))
        self.etrCod = ttk.Entry(top_bar, textvariable=self.codi, width=14, font=('Segoe UI', 9, 'bold'))
        self.etrCod.pack(side='left', padx=(0, 6))

        btnBus = ttk.Button(
            top_bar,
            text=" Buscar",
            image=self.iconoBuscar if self.iconoBuscar else None,
            compound='left',
            command=self.buscar_cod,
            style='Primary.TButton'
        )
        btnBus.pack(side='left', padx=(0, 12))

        ttk.Label(top_bar, text="Denominación:", style='BuscarField.TLabel').pack(side='left', padx=(0, 6))
        etrDen = ttk.Entry(top_bar, textvariable=self.deno, font=('Segoe UI', 9, 'bold'), state='readonly')
        etrDen.pack(side='left', fill='x', expand=True, padx=(0, 12))

        btnDeta = ttk.Button(
            top_bar,
            text="💾 Guardar Cambios",
            command=self.actualizar_det,
            style='Success.TButton'
        )
        btnDeta.pack(side='right')

        # Cuadrícula de 3 columnas de propiedades
        grid_frame = tk.Frame(content, bg="#ffffff")
        grid_frame.pack(fill="x", pady=(0, 6))
        grid_frame.columnconfigure(1, weight=1)
        grid_frame.columnconfigure(3, weight=1)
        grid_frame.columnconfigure(5, weight=1)

        # ==== Columna 1: Inventario y Ubicación ====
        ttk.Label(grid_frame, text="Nº Inventario:", style='BuscarField.TLabel').grid(column=0, row=0, padx=(0, 4), pady=3, sticky="w")

        inve_box = tk.Frame(grid_frame, bg="#ffffff")
        inve_box.grid(column=1, row=0, padx=(0, 12), pady=3, sticky="ew")
        etrInve = ttk.Entry(inve_box, textvariable=self.inve, width=10, justify="center")
        etrInve.pack(side="left", padx=(0, 4))
        btnInve = ttk.Button(inve_box, text="Asignar Acta", command=self.actualizar_cod, style='Action.TButton')
        btnInve.pack(side="left")

        ttk.Label(grid_frame, text="Inv. Anterior:", style='BuscarField.TLabel').grid(column=0, row=1, padx=(0, 4), pady=3, sticky="w")
        ttk.Entry(grid_frame, textvariable=self.acta, state='readonly').grid(column=1, row=1, padx=(0, 12), pady=3, sticky="ew")

        ttk.Label(grid_frame, text="Cta. Contable:", style='BuscarField.TLabel').grid(column=0, row=2, padx=(0, 4), pady=3, sticky="w")
        ttk.Entry(grid_frame, textvariable=self.ctac, state='readonly').grid(column=1, row=2, padx=(0, 12), pady=3, sticky="ew")

        ttk.Label(grid_frame, text="Cód. Patrimonial:", style='BuscarField.TLabel').grid(column=0, row=3, padx=(0, 4), pady=3, sticky="w")
        ttk.Entry(grid_frame, textvariable=self.codp, state='readonly').grid(column=1, row=3, padx=(0, 12), pady=3, sticky="ew")

        ttk.Label(grid_frame, text="Cód. Interno:", style='BuscarField.TLabel').grid(column=0, row=4, padx=(0, 4), pady=3, sticky="w")
        ttk.Entry(grid_frame, textvariable=self.cint, state='readonly').grid(column=1, row=4, padx=(0, 12), pady=3, sticky="ew")

        ttk.Label(grid_frame, text="Fecha Adqui.:", style='BuscarField.TLabel').grid(column=0, row=5, padx=(0, 4), pady=3, sticky="w")
        ttk.Entry(grid_frame, textvariable=self.fech, state='readonly').grid(column=1, row=5, padx=(0, 12), pady=3, sticky="ew")

        ttk.Label(grid_frame, text="Doc. Adqui.:", style='BuscarField.TLabel').grid(column=0, row=6, padx=(0, 4), pady=3, sticky="w")
        ttk.Entry(grid_frame, textvariable=self.dadq, state='readonly').grid(column=1, row=6, padx=(0, 12), pady=3, sticky="ew")

        # ==== Columna 2: Valores y Situación ====
        ttk.Label(grid_frame, text="Valor Adqui.:", style='BuscarField.TLabel').grid(column=2, row=0, padx=(0, 4), pady=3, sticky="w")
        ttk.Entry(grid_frame, textvariable=self.valo, state='readonly', justify='right').grid(column=3, row=0, padx=(0, 12), pady=3, sticky="ew")

        ttk.Label(grid_frame, text="Situación:", style='BuscarField.TLabel').grid(column=2, row=1, padx=(0, 4), pady=3, sticky="w")
        ttk.Entry(grid_frame, textvariable=self.situ).grid(column=3, row=1, padx=(0, 12), pady=3, sticky="ew")

        ttk.Label(grid_frame, text="Otros:", style='BuscarField.TLabel').grid(column=2, row=2, padx=(0, 4), pady=3, sticky="w")
        ttk.Entry(grid_frame, textvariable=self.otro).grid(column=3, row=2, padx=(0, 12), pady=3, sticky="ew")

        ttk.Label(grid_frame, text="Observación:", style='BuscarField.TLabel').grid(column=2, row=3, padx=(0, 4), pady=3, sticky="w")
        ttk.Entry(grid_frame, textvariable=self.obse).grid(column=3, row=3, padx=(0, 12), pady=3, sticky="ew")

        ttk.Label(grid_frame, text="Tipo:", style='BuscarField.TLabel').grid(column=2, row=4, padx=(0, 4), pady=3, sticky="w")
        ttk.Entry(grid_frame, textvariable=self.tipo).grid(column=3, row=4, padx=(0, 12), pady=3, sticky="ew")

        # ==== Columna 3: Características Físicas ====
        ttk.Label(grid_frame, text="Estado:", style='BuscarField.TLabel').grid(column=4, row=0, padx=(0, 4), pady=3, sticky="w")
        ttk.Entry(grid_frame, textvariable=self.esta).grid(column=5, row=0, padx=(0, 2), pady=3, sticky="ew")

        ttk.Label(grid_frame, text="Marca:", style='BuscarField.TLabel').grid(column=4, row=1, padx=(0, 4), pady=3, sticky="w")
        ttk.Entry(grid_frame, textvariable=self.marc).grid(column=5, row=1, padx=(0, 2), pady=3, sticky="ew")

        ttk.Label(grid_frame, text="Modelo:", style='BuscarField.TLabel').grid(column=4, row=2, padx=(0, 4), pady=3, sticky="w")
        ttk.Entry(grid_frame, textvariable=self.mode).grid(column=5, row=2, padx=(0, 2), pady=3, sticky="ew")

        ttk.Label(grid_frame, text="Serie:", style='BuscarField.TLabel').grid(column=4, row=3, padx=(0, 4), pady=3, sticky="w")
        ttk.Entry(grid_frame, textvariable=self.seri).grid(column=5, row=3, padx=(0, 2), pady=3, sticky="ew")

        ttk.Label(grid_frame, text="Color:", style='BuscarField.TLabel').grid(column=4, row=4, padx=(0, 4), pady=3, sticky="w")
        ttk.Entry(grid_frame, textvariable=self.colo).grid(column=5, row=4, padx=(0, 2), pady=3, sticky="ew")

        ttk.Label(grid_frame, text="Dimensión:", style='BuscarField.TLabel').grid(column=4, row=5, padx=(0, 4), pady=3, sticky="w")
        ttk.Entry(grid_frame, textvariable=self.dime).grid(column=5, row=5, padx=(0, 2), pady=3, sticky="ew")

        # Fila de Nota multilínea
        nota_box = tk.Frame(content, bg="#ffffff")
        nota_box.pack(fill="x", pady=(4, 0))

        ttk.Label(nota_box, text="Nota:", style='BuscarField.TLabel').pack(side="left", padx=(0, 8), anchor="n")
        self.txtNota = tk.Text(nota_box, height=2, font=('Segoe UI', 9), bg='white', relief='solid', bd=1)
        self.txtNota.pack(side="left", fill="x", expand=True)

    # -------------------------------------------------------------------------
    # PANEL DE FOTOGRAFÍAS DEL BIEN (VISTA PREVIA, AGREGAR, ELIMINAR, AMPLIAR)
    # -------------------------------------------------------------------------
    def _construir_panel_fotos(self, parent):
        self.photo_card = tk.Frame(parent, bg="#f8fafc", bd=1, relief="solid", width=275, padx=8, pady=6)
        self.photo_card.pack(side="right", fill="y")
        self.photo_card.pack_propagate(False)

        # Cabecera del panel de fotos con contador
        hdr_foto = tk.Frame(self.photo_card, bg="#f8fafc")
        hdr_foto.pack(fill="x", pady=(0, 4))

        tk.Label(
            hdr_foto,
            text="📷 Fotografías",
            bg="#f8fafc",
            fg="#0f172a",
            font=("Segoe UI", 9, "bold")
        ).pack(side="left")

        self.lbl_foto_badge = tk.Label(
            hdr_foto,
            text="Sin seleccionar",
            bg="#e2e8f0",
            fg="#475569",
            font=("Segoe UI", 8, "bold"),
            padx=7,
            pady=2
        )
        self.lbl_foto_badge.pack(side="right")

        # Lienzo / contenedor de miniatura
        self.preview_container = tk.Frame(
            self.photo_card, bg="#0f172a", bd=1, relief="solid", height=145, cursor="hand2"
        )
        self.preview_container.pack(fill="x", pady=(0, 4))
        self.preview_container.pack_propagate(False)

        self.lbl_photo_preview = tk.Label(
            self.preview_container,
            text="Seleccione un bien\npara ver sus fotos",
            bg="#0f172a",
            fg="#94a3b8",
            font=("Segoe UI", 8),
            justify="center",
            cursor="hand2"
        )
        self.lbl_photo_preview.pack(fill="both", expand=True)
        self.lbl_photo_preview.bind("<Button-1>", lambda _e: self.abrir_visor_foto_grande())

        # Barra de navegación entre fotos del bien (◀ 1/N ▶ + Ver grande)
        nav_bar = tk.Frame(self.photo_card, bg="#f8fafc")
        nav_bar.pack(fill="x", pady=(0, 4))

        self.btn_foto_prev = ttk.Button(
            nav_bar, text="◀", width=3, command=self._foto_anterior, state="disabled"
        )
        self.btn_foto_prev.pack(side="left")

        self.lbl_foto_pag = tk.Label(
            nav_bar,
            text="0 / 0",
            bg="#f8fafc",
            fg="#334155",
            font=("Segoe UI", 8, "bold")
        )
        self.lbl_foto_pag.pack(side="left", expand=True)

        self.btn_foto_next = ttk.Button(
            nav_bar, text="▶", width=3, command=self._foto_siguiente, state="disabled"
        )
        self.btn_foto_next.pack(side="left", padx=(0, 4))

        self.btn_foto_zoom = ttk.Button(
            nav_bar, text="🔍 Ver", width=7, command=self.abrir_visor_foto_grande, state="disabled"
        )
        self.btn_foto_zoom.pack(side="right")

        # Acciones: Agregar y Eliminar Foto
        act_bar = tk.Frame(self.photo_card, bg="#f8fafc")
        act_bar.pack(fill="x")

        self.btn_add_foto = ttk.Button(
            act_bar,
            text="➕ Agregar Foto",
            command=self.accion_agregar_foto,
            style="Action.TButton"
        )
        self.btn_add_foto.pack(side="left", fill="x", expand=True, padx=(0, 3))

        self.btn_del_foto = ttk.Button(
            act_bar,
            text="🗑️ Eliminar",
            command=self.accion_eliminar_foto,
            style="Action.TButton",
            state="disabled"
        )
        self.btn_del_foto.pack(side="right", fill="x", expand=True, padx=(3, 0))

    def _cargar_fotos_del_bien_actual(self):
        """Consulta `asset_photos` para el bien actual y actualiza el panel de fotos."""
        codigo = (self.cint.get() or self.codi.get()).strip()
        if not codigo:
            self.fotos_bien_actual = []
            self.foto_idx_actual = 0
            self._actualizar_ui_panel_fotos()
            return

        self.fotos_bien_actual = obtener_fotos_bien(codigo)
        self.foto_idx_actual = 0
        self._actualizar_ui_panel_fotos()

    def _actualizar_ui_panel_fotos(self):
        total = len(self.fotos_bien_actual)
        self._tk_preview_img = None
        self._current_preview_path = None

        if total == 0:
            self.lbl_foto_badge.config(text="⚠️ 0 fotos (Sin foto)", bg="#fef2f2", fg="#b91c1c")
            self.lbl_foto_pag.config(text="0 / 0")
            self.btn_foto_prev.config(state="disabled")
            self.btn_foto_next.config(state="disabled")
            self.btn_foto_zoom.config(state="disabled")
            self.btn_del_foto.config(state="disabled")
            self.lbl_photo_preview.config(
                image="",
                text="⚠️ Este bien no tiene fotografías\n\nHaz clic en '➕ Agregar Foto'\npara adjuntar una imagen",
                fg="#fca5a5"
            )
            return

        if self.foto_idx_actual >= total:
            self.foto_idx_actual = total - 1
        if self.foto_idx_actual < 0:
            self.foto_idx_actual = 0

        foto = self.fotos_bien_actual[self.foto_idx_actual]
        sinc_icon = "✅" if foto.get("sincronizado") == 1 else "⏳"
        self.lbl_foto_badge.config(
            text=f"📷 {total} {'foto' if total == 1 else 'fotos'} {sinc_icon}",
            bg="#dcfce7",
            fg="#15803d"
        )
        self.lbl_foto_pag.config(text=f"{self.foto_idx_actual + 1} / {total}")
        self.btn_foto_prev.config(state="normal" if self.foto_idx_actual > 0 else "disabled")
        self.btn_foto_next.config(state="normal" if self.foto_idx_actual < total - 1 else "disabled")
        self.btn_foto_zoom.config(state="normal")
        self.btn_del_foto.config(state="normal")

        ruta = foto.get("ruta_foto", "")
        local_path = self._resolver_ruta_local(ruta)
        if local_path and os.path.exists(local_path):
            self._render_miniatura_local(local_path)
        elif ruta:
            self.lbl_photo_preview.config(
                image="",
                text="⬇️ Descargando foto\ndesde el servidor...",
                fg="#38bdf8"
            )
            threading.Thread(
                target=self._hilo_descargar_foto,
                args=(ruta, foto.get("id")),
                daemon=True
            ).start()
        else:
            self.lbl_photo_preview.config(image="", text="📷 Ruta de foto vacía", fg="#94a3b8")

    def _resolver_ruta_local(self, ruta):
        if not ruta:
            return None
        ruta_clean = str(ruta).replace("\\", "/")
        if os.path.isabs(ruta) and os.path.exists(ruta):
            return ruta
        nombre = os.path.basename(ruta_clean)
        candidatos = [
            os.path.join(self.photos_dir, nombre),
            os.path.join(self.photos_dir, ruta_clean),
            os.path.join(self.photos_dir, f"code_{nombre}"),
        ]
        for c in candidatos:
            if os.path.exists(c):
                return c
        return None

    def _render_miniatura_local(self, path_img):
        self._current_preview_path = path_img
        try:
            with Image.open(path_img) as img:
                img_copy = img.copy()
                img_copy.thumbnail((250, 138), Image.Resampling.LANCZOS)
                self._tk_preview_img = ImageTk.PhotoImage(img_copy)
                self.lbl_photo_preview.config(image=self._tk_preview_img, text="")
        except Exception as e:
            self.lbl_photo_preview.config(image="", text=f"❌ Error al leer imagen:\n{e}", fg="#f87171")

    def _hilo_descargar_foto(self, ruta_remota, foto_id):
        try:
            url = self.api_client.get_photo_url(ruta_remota)
            if not url:
                return
            nombre_archivo = os.path.basename(str(ruta_remota).replace("\\", "/"))
            destino = os.path.join(self.photos_dir, nombre_archivo)
            req = urllib.request.Request(
                url,
                headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AcontarSoft/1.0"}
            )
            with urllib.request.urlopen(req, timeout=20) as response, open(destino, "wb") as out_file:
                out_file.write(response.read())

            if os.path.exists(destino) and os.path.getsize(destino) > 0:
                def _apply():
                    if not self.winfo_exists():
                        return
                    if (
                        self.fotos_bien_actual
                        and self.foto_idx_actual < len(self.fotos_bien_actual)
                        and self.fotos_bien_actual[self.foto_idx_actual].get("id") == foto_id
                    ):
                        self._render_miniatura_local(destino)
                self.after(0, _apply)
            else:
                self.after(0, lambda: self.lbl_photo_preview.config(image="", text="📷 Foto no disponible", fg="#94a3b8"))
        except Exception:
            if self.winfo_exists():
                self.after(
                    0,
                    lambda: self.lbl_photo_preview.config(
                        image="", text="📷 Foto en servidor\n(Sin conexión local)", fg="#fbbf24"
                    ),
                )

    def _foto_anterior(self):
        if self.foto_idx_actual > 0:
            self.foto_idx_actual -= 1
            self._actualizar_ui_panel_fotos()

    def _foto_siguiente(self):
        if self.foto_idx_actual < len(self.fotos_bien_actual) - 1:
            self.foto_idx_actual += 1
            self._actualizar_ui_panel_fotos()

    def accion_agregar_foto(self):
        codigo = (self.cint.get() or self.codi.get()).strip()
        if not codigo:
            mb.showinfo(
                "Seleccione un bien",
                "Primero seleccione un bien en la tabla o búsquelo por su código para agregarle fotografías.",
                parent=self
            )
            return

        archivos = filedialog.askopenfilenames(
            title=f"Agregar Fotografía(s) al Bien {codigo}",
            filetypes=[
                ("Imágenes", "*.jpg;*.jpeg;*.png;*.webp;*.bmp"),
                ("Todos los archivos", "*.*")
            ],
            parent=self
        )
        if not archivos:
            return

        agregadas = 0
        errores = []
        for arc in archivos:
            try:
                agregar_foto_bien(codigo, arc, photos_dir=self.photos_dir)
                agregadas += 1
            except Exception as e:
                errores.append(f"{os.path.basename(arc)}: {e}")

        self._cargar_fotos_del_bien_actual()
        if self.fotos_bien_actual:
            self.foto_idx_actual = 0
            self._actualizar_ui_panel_fotos()
        self._actualizar_contador_fila_tree(codigo, len(self.fotos_bien_actual))

        if errores:
            mb.showwarning(
                "Resultado parcial",
                f"Se agregaron {agregadas} foto(s).\nErrores:\n" + "\n".join(errores),
                parent=self
            )

    def accion_eliminar_foto(self):
        if not self.fotos_bien_actual or self.foto_idx_actual >= len(self.fotos_bien_actual):
            return

        foto = self.fotos_bien_actual[self.foto_idx_actual]
        codigo = (self.cint.get() or self.codi.get()).strip()
        nombre_foto = os.path.basename(foto.get("ruta_foto", "")) or f"ID #{foto.get('id')}"

        if not mb.askyesno(
            "Confirmar eliminación",
            f"¿Está seguro de eliminar la fotografía '{nombre_foto}' del bien '{codigo}'?",
            parent=self
        ):
            return

        if eliminar_foto_bien(foto["id"]):
            self._cargar_fotos_del_bien_actual()
            self._actualizar_contador_fila_tree(codigo, len(self.fotos_bien_actual))
        else:
            mb.showerror("Error", "No se pudo eliminar la fotografía seleccionada.", parent=self)

    def _actualizar_contador_fila_tree(self, codigo_int, nuevo_total_fotos):
        """Actualiza en vivo la celda de fotos en el Treeview y recalcula los contadores superiores."""
        cod_str = str(codigo_int).strip()
        # Si el filtro activo es SIN_FOTOS y ahora tiene foto (o viceversa), refrescamos la búsqueda
        modo_filtro = self.filtro_fotos_var.get()
        if ("Sin fotografías" in modo_filtro and nuevo_total_fotos > 0) or (
            "Con fotografías" in modo_filtro and nuevo_total_fotos == 0
        ):
            self.buscar()
            return

        # Actualizar cache en memoria y fila en Treeview sin perder posición de scroll
        for idx, r in enumerate(self._raw_rows_cache):
            if str(r[0]).strip() == cod_str or str(r[3]).strip() == cod_str:
                r_list = list(r)
                r_list[-1] = nuevo_total_fotos
                self._raw_rows_cache[idx] = tuple(r_list)

        foto_label = f"📷 {nuevo_total_fotos}" if nuevo_total_fotos > 0 else "⚠️ 0"
        for item_id in self.tree.get_children():
            vals = list(self.tree.item(item_id, "values"))
            if len(vals) >= 7 and (str(vals[1]).strip() == cod_str or str(vals[4]).strip() == cod_str):
                vals[6] = foto_label
                base_tag = "evenrow" if int(vals[0] or 1) % 2 == 0 else "oddrow"
                foto_tag = "con_foto" if nuevo_total_fotos > 0 else "sin_foto"
                self.tree.item(item_id, values=vals, tags=(base_tag, foto_tag))
                break

        self._recalcular_kpis_fotos()

    def abrir_visor_foto_grande(self):
        """Abre un visor modal de tamaño completo para inspeccionar, agregar o eliminar fotos del bien."""
        if not self.fotos_bien_actual:
            if (self.cint.get() or self.codi.get()).strip():
                self.accion_agregar_foto()
            return

        visor = tk.Toplevel(self)
        codigo = (self.cint.get() or self.codi.get()).strip()
        denom = self.deno.get().strip()
        visor.title(f"Visor Fotográfico — Bien [{codigo}] {denom}")
        visor.geometry("920x680")
        visor.minsize(720, 500)
        visor.configure(bg="#0f172a")
        visor.transient(self)

        # Barra superior informativa
        top_f = tk.Frame(visor, bg="#1e293b", padx=14, pady=10)
        top_f.pack(fill="x")

        lbl_info = tk.Label(
            top_f,
            text="",
            bg="#1e293b",
            fg="#f8fafc",
            font=("Segoe UI", 10, "bold"),
            anchor="w"
        )
        lbl_info.pack(side="left", fill="x", expand=True)

        lbl_meta = tk.Label(
            top_f,
            text="",
            bg="#1e293b",
            fg="#38bdf8",
            font=("Segoe UI", 9, "bold")
        )
        lbl_meta.pack(side="right")

        # Área central de la imagen
        canvas_f = tk.Frame(visor, bg="#0f172a")
        canvas_f.pack(fill="both", expand=True, padx=12, pady=8)

        lbl_big = tk.Label(canvas_f, bg="#0f172a", fg="#cbd5e1", font=("Segoe UI", 10))
        lbl_big.pack(fill="both", expand=True)

        # Barra inferior de controles del visor
        bot_f = tk.Frame(visor, bg="#1e293b", padx=14, pady=10)
        bot_f.pack(fill="x")

        btn_v_prev = ttk.Button(bot_f, text="◀ Anterior")
        btn_v_prev.pack(side="left", padx=(0, 6))

        lbl_v_pag = tk.Label(bot_f, text="1 / 1", bg="#1e293b", fg="#f8fafc", font=("Segoe UI", 9, "bold"))
        lbl_v_pag.pack(side="left", padx=8)

        btn_v_next = ttk.Button(bot_f, text="Siguiente ▶")
        btn_v_next.pack(side="left", padx=(6, 16))

        def _refrescar_visor():
            if not self.fotos_bien_actual:
                visor.destroy()
                return
            total = len(self.fotos_bien_actual)
            if self.foto_idx_actual >= total:
                self.foto_idx_actual = total - 1
            foto = self.fotos_bien_actual[self.foto_idx_actual]
            ruta = foto.get("ruta_foto", "")
            sinc = "✅ Sincronizado" if foto.get("sincronizado") == 1 else "⏳ Local (Pendiente)"
            lbl_info.config(text=f"📦 [{codigo}] {denom}   —   Archivo: {os.path.basename(ruta)}")
            lbl_meta.config(text=f"Fecha: {foto.get('fecha') or '—'}   |   {sinc}")
            lbl_v_pag.config(text=f"Foto {self.foto_idx_actual + 1} de {total}")
            btn_v_prev.config(state="normal" if self.foto_idx_actual > 0 else "disabled")
            btn_v_next.config(state="normal" if self.foto_idx_actual < total - 1 else "disabled")

            local_p = self._resolver_ruta_local(ruta)
            if local_p and os.path.exists(local_p):
                try:
                    visor.update_idletasks()
                    w = max(480, canvas_f.winfo_width() - 24)
                    h = max(360, canvas_f.winfo_height() - 24)
                    with Image.open(local_p) as im:
                        im_c = im.copy()
                        im_c.thumbnail((w, h), Image.Resampling.LANCZOS)
                        visor._big_tk = ImageTk.PhotoImage(im_c)
                        lbl_big.config(image=visor._big_tk, text="")
                except Exception as ex:
                    lbl_big.config(image="", text=f"No se pudo renderizar la imagen:\n{ex}")
            else:
                lbl_big.config(image="", text="⬇️ Descargando imagen del servidor...")

        def _ir_ant():
            self._foto_anterior()
            _refrescar_visor()

        def _ir_sig():
            self._foto_siguiente()
            _refrescar_visor()

        def _agregar_desde_visor():
            self.accion_agregar_foto()
            if visor.winfo_exists():
                _refrescar_visor()

        def _eliminar_desde_visor():
            self.accion_eliminar_foto()
            if visor.winfo_exists():
                _refrescar_visor()

        btn_v_prev.config(command=_ir_ant)
        btn_v_next.config(command=_ir_sig)

        ttk.Button(bot_f, text="🗑️ Eliminar Esta Foto", command=_eliminar_desde_visor).pack(side="right", padx=(6, 0))
        ttk.Button(bot_f, text="➕ Agregar Nueva Foto", command=_agregar_desde_visor).pack(side="right", padx=6)

        visor.bind("<Configure>", lambda _e: visor.after_idle(_refrescar_visor))
        visor.after(50, _refrescar_visor)

    # -------------------------------------------------------------------------
    # TABLA INFERIOR DE RESULTADOS Y FILTROS DE FOTOS
    # -------------------------------------------------------------------------
    def widget_field_botton(self):
        # ---- Card Inferior: Búsqueda Avanzada y Tabla de Resultados ----
        self.card_resultados = ttk.LabelFrame(
            self.frame_u,
            text=" 📋 Búsqueda Avanzada en Base de Datos y Control de Fotografías por Bien ",
            style='Card.TLabelframe',
            padding=(12, 8)
        )
        self.card_resultados.pack(fill="both", side="bottom", expand=True)

        # Barra superior de filtros
        filter_bar = tk.Frame(self.card_resultados, bg="#ffffff")
        filter_bar.pack(fill="x", pady=(0, 8))

        ttk.Label(filter_bar, text="Criterio:", style='BuscarField.TLabel').pack(side="left", padx=(0, 4))

        self.cbxCrit = ttk.Combobox(
            filter_bar,
            textvariable=self.crit,
            state="readonly",
            values=["CodInt", "ActaAnt", "Inv", "CodPat", "DenBien", "Estado", "Dimension", "Marca", "Modelo",
                    "Serie", "Color", "CtaCont", "ValAdq", "Obs"],
            width=11,
            font=('Segoe UI', 9)
        )
        self.cbxCrit.pack(side="left", padx=(0, 8))

        ttk.Label(filter_bar, text="Buscar:", style='BuscarField.TLabel').pack(side="left", padx=(0, 4))
        self.etrBien = ttk.Entry(filter_bar, textvariable=self.bien, font=('Segoe UI', 9), width=20)
        self.etrBien.pack(side="left", padx=(0, 8))

        ttk.Label(filter_bar, text="Fotos:", style='BuscarBold.TLabel').pack(side="left", padx=(0, 4))
        self.cbxFiltroFotos = ttk.Combobox(
            filter_bar,
            textvariable=self.filtro_fotos_var,
            state="readonly",
            values=[
                "Todos los bienes",
                "⚠️ Sin fotografías (0 fotos)",
                "📷 Con fotografías (1+ fotos)",
            ],
            width=23,
            font=('Segoe UI', 9)
        )
        self.cbxFiltroFotos.pack(side="left", padx=(0, 8))
        self.cbxFiltroFotos.bind("<<ComboboxSelected>>", lambda _e: self.buscar())

        btnBuscarFiltro = ttk.Button(
            filter_bar,
            text=" Buscar",
            image=self.iconoBuscar if self.iconoBuscar else None,
            compound='left',
            command=self.buscar,
            style='Primary.TButton'
        )
        btnBuscarFiltro.pack(side="left", padx=(0, 4))

        btnLimpiar = ttk.Button(
            filter_bar,
            text="Limpiar",
            command=self._limpiar_filtro,
            style='Action.TButton'
        )
        btnLimpiar.pack(side="left", padx=(0, 10))

        # Chips interactivos de conteo (Total, Con foto, Sin foto)
        lbl_total = tk.Label(
            filter_bar,
            textvariable=self.total_encontrados_var,
            bg="#f1f5f9",
            fg="#0f172a",
            font=('Segoe UI', 8, 'bold'),
            padx=8,
            pady=3,
            relief='solid',
            bd=1,
            cursor="hand2"
        )
        lbl_total.pack(side="left", padx=(0, 4))
        lbl_total.bind("<Button-1>", lambda _e: self._aplicar_chip_fotos("Todos los bienes"))

        lbl_con_foto = tk.Label(
            filter_bar,
            textvariable=self.total_con_foto_var,
            bg="#dcfce7",
            fg="#15803d",
            font=('Segoe UI', 8, 'bold'),
            padx=8,
            pady=3,
            relief='solid',
            bd=1,
            cursor="hand2"
        )
        lbl_con_foto.pack(side="left", padx=(0, 4))
        lbl_con_foto.bind("<Button-1>", lambda _e: self._aplicar_chip_fotos("📷 Con fotografías (1+ fotos)"))

        lbl_sin_foto = tk.Label(
            filter_bar,
            textvariable=self.total_sin_foto_var,
            bg="#fef2f2",
            fg="#b91c1c",
            font=('Segoe UI', 8, 'bold'),
            padx=8,
            pady=3,
            relief='solid',
            bd=1,
            cursor="hand2"
        )
        lbl_sin_foto.pack(side="left")
        lbl_sin_foto.bind("<Button-1>", lambda _e: self._aplicar_chip_fotos("⚠️ Sin fotografías (0 fotos)"))

        # Botón Exportar a Excel
        btnExpo = ttk.Button(
            filter_bar,
            text=" Exportar Excel",
            image=self.iconoExcel if self.iconoExcel else None,
            compound='left',
            command=self.exportar,
            style='Action.TButton'
        )
        btnExpo.pack(side="right")

        # Contenedor del Treeview
        table_frame = tk.Frame(self.card_resultados, bg="#ffffff")
        table_frame.pack(fill='both', expand=True)
        table_frame.rowconfigure(0, weight=1)
        table_frame.columnconfigure(0, weight=1)

        cab = tuple(range(1, 17))
        self.tree = ttk.Treeview(
            table_frame,
            columns=cab,
            height=13,
            show='headings',
            style='Buscar.Treeview',
            selectmode='browse'
        )

        headers = [
            (1,  'Item',                  45,  "center"),
            (2,  'Cód. Interno',          80,  "center"),
            (3,  'Acta Ant.',             70,  "center"),
            (4,  'Inv.',                  65,  "center"),
            (5,  'Cód. Patrimonial',      105, "center"),
            (6,  'Denominación del Bien', 260, "w"),
            (7,  '📷 Fotos',              75,  "center"),
            (8,  'Estado',                60,  "center"),
            (9,  'Dimensión',             85,  "w"),
            (10, 'Marca',                 85,  "w"),
            (11, 'Modelo',                85,  "w"),
            (12, 'Serie',                 85,  "w"),
            (13, 'Color',                 80,  "w"),
            (14, 'Cuenta Contable',       100, "w"),
            (15, 'Valor Adq.',            85,  "e"),
            (16, 'Observación',           115, "w"),
        ]

        for col_id, titulo, ancho, alineacion in headers:
            self.tree.heading(col_id, text=titulo, command=lambda c=col_id: sort_by(self.tree, c, False))
            self.tree.column(col_id, width=ancho, minwidth=40, stretch=(col_id == 6), anchor=alineacion)

        # Tags de alternancia de color y estado fotográfico
        self.tree.tag_configure('evenrow', background='#ffffff')
        self.tree.tag_configure('oddrow', background='#f8fafc')
        self.tree.tag_configure('sin_foto', foreground='#0f172a')
        self.tree.tag_configure('con_foto', foreground='#0f172a')

        # Scrollbars
        vscrollbar = ttk.Scrollbar(table_frame, orient='vertical', command=self.tree.yview)
        hscrollbar = ttk.Scrollbar(table_frame, orient='horizontal', command=self.tree.xview)
        self.tree.configure(yscrollcommand=vscrollbar.set, xscrollcommand=hscrollbar.set)

        self.tree.grid(column=0, row=0, sticky='nsew')
        vscrollbar.grid(column=1, row=0, sticky='ns')
        hscrollbar.grid(column=0, row=1, sticky='ew')

        # Pie informativo
        footer = tk.Frame(self.card_resultados, bg="#f8fafc")
        footer.pack(fill="x", side="bottom", pady=(4, 0))

        lbl_tip = tk.Label(
            footer,
            text="💡 Tip: Selecciona cualquier fila para ver sus fotografías y datos al instante  |  Haz clic en los indicadores '📷 Con foto' o '⚠️ Sin foto' para filtrar rápidamente.",
            bg="#f8fafc",
            fg="#64748b",
            font=("Segoe UI", 8, "italic"),
            anchor="w"
        )
        lbl_tip.pack(side="left", padx=4)

    def _aplicar_chip_fotos(self, opcion):
        self.filtro_fotos_var.set(opcion)
        self.buscar()

    def _limpiar_filtro(self):
        self.bien.set("")
        self.filtro_fotos_var.set("Todos los bienes")
        self.buscar()

    def _recalcular_kpis_fotos(self):
        total = len(self._raw_rows_cache)
        con_foto = sum(1 for r in self._raw_rows_cache if int(r[-1] or 0) > 0)
        sin_foto = total - con_foto
        self.total_encontrados_var.set(f"📦 Total: {total:,}")
        self.total_con_foto_var.set(f"📷 Con foto: {con_foto:,}")
        self.total_sin_foto_var.set(f"⚠️ Sin foto: {sin_foto:,}")

    def buscar(self):
        self._render_token += 1
        token_actual = self._render_token

        children = self.tree.get_children()
        if children:
            self.tree.delete(*children)

        modo_txt = self.filtro_fotos_var.get()
        if "Sin fotografías" in modo_txt:
            filtro_fotos = "SIN_FOTOS"
        elif "Con fotografías" in modo_txt:
            filtro_fotos = "CON_FOTOS"
        else:
            filtro_fotos = "TODOS"

        try:
            r = buscar_data(self.crit.get(), self.bien.get().strip(), filtro_fotos=filtro_fotos) or []
            self._raw_rows_cache = list(r)
            self._recalcular_kpis_fotos()

            total_filas = len(self._raw_rows_cache)

            def _insertar_lote(inicio=0):
                if token_actual != self._render_token or not self.winfo_exists():
                    return
                fin = min(inicio + _RENDER_CHUNK_SIZE, total_filas)
                for idx in range(inicio, fin):
                    contact = self._raw_rows_cache[idx]
                    cell = idx + 1
                    # contact: [CodInt, ActaAnt, Inv, CodPat, DenBien, Estado, Dimension, Marca, Modelo, Serie, Color, CtaCont, ValAdq, Obs, TotalFotos]
                    num_fotos = int(contact[-1] or 0)
                    foto_str = f"📷 {num_fotos}" if num_fotos > 0 else "⚠️ 0"
                    fila_tree = [
                        str(cell),
                        contact[0],
                        contact[1],
                        contact[2],
                        contact[3],
                        contact[4],
                        foto_str,
                        contact[5],
                        contact[6],
                        contact[7],
                        contact[8],
                        contact[9],
                        contact[10],
                        contact[11],
                        contact[12],
                        contact[13],
                    ]
                    base_tag = 'evenrow' if cell % 2 == 0 else 'oddrow'
                    foto_tag = 'con_foto' if num_fotos > 0 else 'sin_foto'
                    self.tree.insert('', tk.END, values=fila_tree, tags=(base_tag, foto_tag))

                if fin < total_filas:
                    self.after(1, _insertar_lote, fin)

            _insertar_lote(0)
        except Exception as e:
            mb.showerror("Error de Búsqueda", f"Ocurrió un error al consultar los datos: {e}", parent=self)

    def _on_tree_select_debounced(self, _event=None):
        """Carga automáticamente los detalles y fotografías al seleccionar una fila."""
        if self._select_debounce_job is not None:
            try:
                self.after_cancel(self._select_debounce_job)
            except Exception:
                pass
        self._select_debounce_job = self.after(90, self.mostrar_datos_)

    def mostrar_datos_(self, *args):
        curActa = self.tree.focus()
        if not curActa:
            sel = self.tree.selection()
            curActa = sel[0] if sel else ""
        if not curActa:
            return
        vnb = self.tree.item(curActa)['values']
        if vnb and len(vnb) > 1:
            j = vnb[1]
            self.codi.set(j)
            self.buscar_cod(silencioso=True)

    def buscar_cod(self, *args, silencioso=False):
        codigo_buscado = self.codi.get().strip()
        if not codigo_buscado:
            if not silencioso:
                mb.showinfo(message="Ingrese un código para buscar", title="¡Atención!", parent=self)
            return

        r = buscar_bien_d(1, codigo_buscado)
        if not r:
            if not silencioso:
                mb.showinfo(message=f"El código '{codigo_buscado}' no existe en la base de datos.", title="¡Atención!", parent=self)
                self.focus_set()
            return

        try:
            datos = ['deno', 'inve', 'acta', 'marc', 'seri', 'mode', 'fech', 'dadq', 'colo', 'esta',
                     'dime', 'obse', 'otro', 'situ', 'codp', 'txtNota', 'tipo', 'valo', 'ctac', 'cint']
            for i, dato in enumerate(datos):
                valor = str(r[0][i]) if r[0][i] is not None else ""
                if dato == 'valo':
                    try:
                        valor = '{:,.2f}'.format(float(valor))
                    except (ValueError, TypeError):
                        pass
                    getattr(self, dato).set(valor)
                elif dato == 'txtNota':
                    self.txtNota.delete("1.0", "end")
                    self.txtNota.insert("1.0", valor)
                else:
                    getattr(self, dato).set(valor)

            # Cargar galería de fotografías del bien seleccionado desde asset_photos
            self._cargar_fotos_del_bien_actual()
        except Exception as e:
            if not silencioso:
                mb.showerror(message=f"Error procesando los datos del bien: {str(e)}", title="Error", parent=self)
                self.focus_set()

    def actualizar_det(self):
        self.data = [
            self.marc.get(), self.mode.get(), self.colo.get(), self.seri.get(),
            self.esta.get(), self.dime.get(), self.obse.get(), self.otro.get(),
            self.situ.get(), self.fech.get(), self.dadq.get(), self.txtNota.get("1.0", "end-1c"),
            self.tipo.get()
        ]

        self.data_c = [
            self.marc.get(), self.mode.get(), self.colo.get(), self.seri.get(),
            self.esta.get(), self.dime.get(), self.tipo.get()
        ]

        if (self.marc.get() == "" or self.mode.get() == "" or self.colo.get() == "" or
            self.seri.get() == "" or self.esta.get() == "" or self.dime.get() == "" or self.tipo.get() == ""):
            mb.showwarning(
                message="Los campos Marca, Modelo, Color, Tipo, Serie, Estado y Dimensiones son obligatorios.",
                title="Campos Incompletos",
                parent=self
            )
            self.focus_set()
            return

        try:
            self.validar_datos()
            actualizar_detalles(self.codi.get(), self.data)
            self.buscar_cod(silencioso=True)
            mb.showinfo(message="¡Datos del bien actualizados correctamente!", title="Acontar S.A.C.", parent=self)
            self.focus_set()
        except Exception as e:
            mb.showerror(message=f"Error al actualizar el bien: {str(e)}", title="Error", parent=self)
            self.focus_set()

    def actualizar_cod(self):
        codigo = self.codi.get().strip()
        if not codigo:
            mb.showinfo(message="Seleccione o busque un bien primero.", title="¡Atención!", parent=self)
            self.focus_set()
            return

        j = self.inve.get().strip()
        if not j or j == "0":
            confirmar = mb.askyesno(
                title="Des-inventariar Bien",
                message=(
                    f"El campo 'Nº Inventario' está vacío.\n\n"
                    f"¿Desea quitar el bien '{codigo}' del inventario actual (des-inventariar)?"
                ),
                parent=self,
            )
            if not confirmar:
                self.focus_set()
                return
            try:
                actualizar_registro(codigo, ["", "", "", ""])
                self.buscar()
                self.buscar_cod(silencioso=True)
                mb.showinfo(
                    message="¡Bien des-inventariado localmente y encolado para sincronizar con el servidor!",
                    title="Actualización",
                    parent=self,
                )
                self.focus_set()
            except Exception as e:
                mb.showerror(message=f"Ocurrió un error al des-inventariar: {e}", title="Error", parent=self)
            return

        try:
            Acta = j
            now = datetime.now()
            F_inv = now.strftime("%d/%m/%Y %H:%M:%S")
            data = [Acta, F_inv, self.user, self.team]

            actualizar_registro(codigo, data)
            self.buscar()
            self.buscar_cod(silencioso=True)
            mb.showinfo(message="¡Asignación a inventario registrada y encolada con éxito!", title="Actualización", parent=self)
            self.focus_set()
        except Exception as e:
            mb.showerror(message=f"Ocurrió un error al registrar: {e}", title="Error", parent=self)

    def exportar(self):
        self.lista = [
            'Item', 'Código interno', 'Acta Ant', 'Inv', 'Código patrimonial', 'Denominación',
            'Fotos', 'Estado', 'Dimensión', 'Marca', 'Modelo', 'Serie', 'Color', 'Cuenta Contable', 'Valor', 'Obs'
        ]
        datos = []
        for item in self.tree.get_children():
            values = self.tree.item(item, "values")
            datos.append(values)

        if not datos:
            mb.showwarning("Sin datos", "No hay registros disponibles para exportar.", parent=self)
            return

        try:
            exportar_excel("Buscar_Bienes", self.lista, datos)
            mb.showinfo("Exportación Exitosa", "Archivo Excel generado con éxito en la carpeta 'exportar/'.", parent=self)
            self.focus_set()
        except Exception as e:
            mb.showerror("Error al Exportar", f"No se pudo exportar a Excel: {e}", parent=self)
            self.focus_set()

    def validar_datos(self):
        try:
            r = buscar_bien_d(2, self.codi.get())
            if r and len(r) > 0:
                r_lista = list(r[0])
                if self.data_c != r_lista:
                    insertar = cambio_detalles(self.codi.get())
                    try:
                        insertar_tabla2(insertar)
                    except Exception as e:
                        print(f"Registro en tabla de cambios duplicado o ignorado: {e}")
        except Exception as ex:
            print(f"Error en validar_datos: {ex}")
