import math
import os
import shutil
import sqlite3
import threading
import tkinter as tk
from datetime import datetime
from tkinter import filedialog, messagebox as mb, ttk
from PIL import Image, ImageTk

from utils.api_client import ApiManagerAcontarSacClient
from utils.config_helper import get_config


class Window_asset_photos(tk.Toplevel):
    """Ventana paginada para gestionar y visualizar fotografías de activos (asset_photos)."""

    PAGE_SIZE_OPTIONS = [25, 50, 100, 200]

    def __init__(self, root=None):
        super().__init__(root)
        self.root = root
        self.title("Gestión de Fotografías de Activos (asset_photos) - AcontarSoft")
        self.geometry("1180x690")
        self.minsize(960, 540)

        # Icono
        icon_path = os.path.join(os.path.dirname(__file__), "..", "img", "favicon.ico")
        if os.path.exists(icon_path):
            try:
                self.iconbitmap(icon_path)
            except Exception:
                pass

        # Rutas de base de datos y fotos
        base_dir = os.path.dirname(os.path.abspath(__file__))
        default_db = os.path.join(base_dir, "..", "db", "orap2022.db")
        self.db_path = getattr(self.root, "db_path", os.path.normpath(default_db))
        self.photos_dir = os.path.join(base_dir, "..", "photos")
        os.makedirs(self.photos_dir, exist_ok=True)

        self.api_client = getattr(self.root, "api_client", None) or ApiManagerAcontarSacClient()

        # Variables de Paginación y Filtros
        self.page_current = 1
        self.page_size = 50
        self.total_records = 0
        self.total_pages = 1

        self.search_var = tk.StringVar()
        self.search_field_var = tk.StringVar(value="Cód. Interno")
        self.filter_sync_var = tk.StringVar(value="Todos")
        self.page_size_var = tk.IntVar(value=50)
        self.page_input_var = tk.StringVar(value="1")

        self.current_selected_photo = None
        self._current_tk_img = None
        self._current_image_path = None
        self._resize_job = None
        self._lista_oculta = False

        # Asegurar índices para búsqueda ultrarrápida
        self._asegurar_indices()

        self._build_ui()
        self.cargar_pagina(1)

    def _asegurar_indices(self):
        """Crea índices en SQLite para que la paginación y búsqueda sean instantáneas."""
        try:
            conn = sqlite3.connect(self.db_path)
            cur = conn.cursor()
            cur.execute("CREATE INDEX IF NOT EXISTS idx_asset_photos_asset_id ON asset_photos(asset_id);")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_asset_photos_cod_int ON asset_photos(codigo_interno);")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_asset_photos_sync ON asset_photos(sincronizado);")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_assets_id ON assets(id);")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_assets_cod_int ON assets(codigo_interno);")
            conn.commit()
            conn.close()
        except Exception:
            pass

    def _build_ui(self):
        # 1. Barra de Herramientas y Filtros
        frame_top = ttk.Frame(self, padding=(10, 8))
        frame_top.pack(fill="x")

        ttk.Label(frame_top, text="🔍 Buscar:", font=("Helvetica", 9, "bold")).pack(side="left", padx=(0, 4))
        
        # Criterio de búsqueda (Por defecto Código Interno)
        self.cb_criterio = ttk.Combobox(
            frame_top, textvariable=self.search_field_var,
            values=["Cód. Interno", "Cód. Patrimonial", "Denominación", "ID Asset", "Todo"],
            state="readonly", width=14
        )
        self.cb_criterio.pack(side="left", padx=(0, 6))
        self.cb_criterio.bind("<<ComboboxSelected>>", lambda e: self.aplicar_filtros())

        self.txt_search = ttk.Entry(frame_top, textvariable=self.search_var, width=22)
        self.txt_search.pack(side="left", padx=(0, 4))
        self.txt_search.bind("<Return>", lambda e: self.aplicar_filtros())

        btn_buscar = ttk.Button(frame_top, text="Filtrar", command=self.aplicar_filtros)
        btn_buscar.pack(side="left", padx=(0, 4))

        btn_limpiar = ttk.Button(frame_top, text="✖ Limpiar", command=self.limpiar_busqueda)
        btn_limpiar.pack(side="left", padx=(0, 10))

        ttk.Label(frame_top, text="Estado:").pack(side="left", padx=(0, 5))
        cb_sync = ttk.Combobox(
            frame_top, textvariable=self.filter_sync_var,
            values=["Todos", "Sincronizados (1)", "Pendientes (0)"],
            state="readonly", width=15
        )
        cb_sync.pack(side="left", padx=(0, 10))
        cb_sync.bind("<<ComboboxSelected>>", lambda e: self.aplicar_filtros())

        btn_refresh = ttk.Button(frame_top, text="🔄 Refrescar", command=lambda: self.cargar_pagina(self.page_current))
        btn_refresh.pack(side="left", padx=(0, 5))

        btn_add = ttk.Button(frame_top, text="➕ Asociar Foto", command=self.dialogo_asociar_foto)
        btn_add.pack(side="left", padx=(0, 5))

        btn_scan = ttk.Button(frame_top, text="📂 Escanear Carpeta", command=self.escanear_carpeta_local)
        btn_scan.pack(side="left", padx=(0, 5))

        self.lbl_global_count = ttk.Label(frame_top, text="Total: 0 registros", font=("Helvetica", 9, "bold"))
        self.lbl_global_count.pack(side="right", padx=5)

        # 2. Panel Principal Dividido (Treeview a la izquierda, Visor a la derecha)
        self.paned = ttk.PanedWindow(self, orient="horizontal")
        self.paned.pack(fill="both", expand=True, padx=10, pady=(0, 5))

        # --- Panel Izquierdo: Lista Paginada ---
        self.frame_left = ttk.Frame(self.paned, padding=2)
        self.paned.add(self.frame_left, weight=1)

        columns = ("id", "codigo_interno", "cod_patrimonial", "denominacion", "ruta_foto", "fecha", "sincronizado")
        self.tree = ttk.Treeview(self.frame_left, columns=columns, show="headings", selectmode="browse")

        self.tree.heading("id", text="ID")
        self.tree.heading("codigo_interno", text="Cód. Int")
        self.tree.heading("cod_patrimonial", text="Cód. Patrimonial")
        self.tree.heading("denominacion", text="Denominación del Bien")
        self.tree.heading("ruta_foto", text="Archivo / Ruta")
        self.tree.heading("fecha", text="Fecha")
        self.tree.heading("sincronizado", text="Sync")

        self.tree.column("id", width=50, anchor="center")
        self.tree.column("codigo_interno", width=75, anchor="center")
        self.tree.column("cod_patrimonial", width=105, anchor="center")
        self.tree.column("denominacion", width=190, anchor="w")
        self.tree.column("ruta_foto", width=130, anchor="w")
        self.tree.column("fecha", width=100, anchor="center")
        self.tree.column("sincronizado", width=60, anchor="center")

        scroll_y = ttk.Scrollbar(self.frame_left, orient="vertical", command=self.tree.yview)
        scroll_x = ttk.Scrollbar(self.frame_left, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=scroll_y.set, xscrollcommand=scroll_x.set)

        self.tree.grid(row=0, column=0, sticky="nsew")
        scroll_y.grid(row=0, column=1, sticky="ns")
        scroll_x.grid(row=1, column=0, sticky="ew")

        self.frame_left.rowconfigure(0, weight=1)
        self.frame_left.columnconfigure(0, weight=1)

        self.tree.bind("<<TreeviewSelect>>", self._on_tree_select)
        self.tree.bind("<Double-1>", lambda e: self.abrir_en_visor_sistema())

        # --- Barra Inferior de Paginación ---
        frame_pagination = ttk.Frame(self.frame_left, padding=(2, 6))
        frame_pagination.grid(row=2, column=0, columnspan=2, sticky="ew")

        self.btn_first = ttk.Button(frame_pagination, text="⏮", width=3, command=self.ir_primera_pagina)
        self.btn_first.pack(side="left", padx=2)

        self.btn_prev = ttk.Button(frame_pagination, text="◀", width=4, command=self.pagina_anterior)
        self.btn_prev.pack(side="left", padx=2)

        ttk.Label(frame_pagination, text="Pág.").pack(side="left", padx=(4, 2))
        self.etr_page = ttk.Entry(frame_pagination, textvariable=self.page_input_var, width=5, justify="center")
        self.etr_page.pack(side="left", padx=2)
        self.etr_page.bind("<Return>", lambda e: self._ir_a_pagina_escrita())

        self.lbl_pages_total = ttk.Label(frame_pagination, text="de 1")
        self.lbl_pages_total.pack(side="left", padx=(2, 4))

        btn_go = ttk.Button(frame_pagination, text="Ir", width=3, command=self._ir_a_pagina_escrita)
        btn_go.pack(side="left", padx=2)

        self.btn_next = ttk.Button(frame_pagination, text="▶", width=4, command=self.pagina_siguiente)
        self.btn_next.pack(side="left", padx=2)

        self.btn_last = ttk.Button(frame_pagination, text="⏭", width=3, command=self.ir_ultima_pagina)
        self.btn_last.pack(side="left", padx=2)

        ttk.Separator(frame_pagination, orient="vertical").pack(side="left", fill="y", padx=6)

        ttk.Label(frame_pagination, text="Cant:").pack(side="left", padx=(2, 2))
        cb_size = ttk.Combobox(
            frame_pagination, textvariable=self.page_size_var,
            values=self.PAGE_SIZE_OPTIONS, state="readonly", width=4
        )
        cb_size.pack(side="left", padx=2)
        cb_size.bind("<<ComboboxSelected>>", self._on_change_page_size)

        self.lbl_page_info = ttk.Label(frame_pagination, text="0 - 0 de 0", font=("Helvetica", 8))
        self.lbl_page_info.pack(side="right", padx=5)

        # --- Panel Derecho: Visor y Ficha de Foto (Ocupa la mayor parte del espacio) ---
        self.frame_right = ttk.LabelFrame(self.paned, text=" Vista Previa y Ficha de Foto ", padding=8)
        self.paned.add(self.frame_right, weight=3)

        # Ficha superior compacta
        frame_info = ttk.Frame(self.frame_right)
        frame_info.pack(fill="x", pady=(0, 4))

        self.lbl_den = ttk.Label(frame_info, text="Seleccione una fotografía para previsualizar", font=("Helvetica", 10, "bold"), wraplength=550)
        self.lbl_den.pack(anchor="w", pady=(0, 2))

        self.lbl_codes = ttk.Label(frame_info, text="Cód. Patrimonial: - | Cód. Interno: -", font=("Helvetica", 9))
        self.lbl_codes.pack(anchor="w", pady=(0, 2))

        self.lbl_path = ttk.Label(frame_info, text="Archivo: -", font=("Helvetica", 8), foreground="#555555", wraplength=550)
        self.lbl_path.pack(anchor="w", pady=(0, 2))

        # Contenedor de la Imagen: Ocupa TODO el espacio disponible dinámicamente
        self.frame_img_container = tk.Frame(self.frame_right, bg="#1a1a1a")
        self.frame_img_container.pack(fill="both", expand=True, pady=4)

        self.lbl_canvas = tk.Label(
            self.frame_img_container, 
            bg="#1a1a1a", 
            text="Haga clic en una fila para cargar la foto\n\n(Doble clic en la foto para Pantalla Completa)", 
            fg="#888888",
            font=("Helvetica", 10)
        )
        self.lbl_canvas.pack(fill="both", expand=True)
        self.lbl_canvas.bind("<Double-1>", lambda e: self.ver_pantalla_completa())
        self.frame_img_container.bind("<Configure>", self._on_container_resize)

        # Barra de Acciones del Visor
        frame_actions = ttk.Frame(self.frame_right)
        frame_actions.pack(fill="x", pady=(4, 0))

        self.btn_toggle_list = ttk.Button(frame_actions, text="◀ Ocultar Lista", command=self.toggle_lista)
        self.btn_toggle_list.pack(side="left", padx=(0, 2))

        self.btn_fullscreen = ttk.Button(frame_actions, text="🔍 Pantalla Completa", command=self.ver_pantalla_completa)
        self.btn_fullscreen.pack(side="left", padx=2)

        self.btn_open_external = ttk.Button(frame_actions, text="🖥️ Abrir en Sistema", command=self.abrir_en_visor_sistema)
        self.btn_open_external.pack(side="left", padx=2)

        self.btn_open_folder = ttk.Button(frame_actions, text="📁 Abrir Carpeta", command=self.abrir_carpeta_fotos)
        self.btn_open_folder.pack(side="left", padx=2)

        self.btn_upload = ttk.Button(frame_actions, text="⬆️ Subir", command=self.subir_foto_al_servidor)
        self.btn_upload.pack(side="left", padx=2)

        self.btn_delete = ttk.Button(frame_actions, text="🗑️ Eliminar", command=self.eliminar_foto)
        self.btn_delete.pack(side="right", padx=(2, 0))

    def limpiar_busqueda(self):
        """Limpia el cuadro de búsqueda y restaura los filtros."""
        self.search_var.set("")
        self.filter_sync_var.set("Todos")
        self.aplicar_filtros()

    def toggle_lista(self):
        """Oculta o muestra el panel de la lista para aprovechar el 100% del ancho de la ventana."""
        if self._lista_oculta:
            self.paned.insert(0, self.frame_left, weight=1)
            self._lista_oculta = False
            self.btn_toggle_list.config(text="◀ Ocultar Lista")
        else:
            self.paned.forget(self.frame_left)
            self._lista_oculta = True
            self.btn_toggle_list.config(text="▶ Mostrar Lista")
        self.after(100, self._render_imagen_actual)

    def ver_pantalla_completa(self):
        """Abre la imagen en una ventana maximizada que utiliza el 100% de la pantalla."""
        if not getattr(self, "_current_image_path", None) or not os.path.exists(self._current_image_path):
            mb.showinfo("Información", "Por favor seleccione una fotografía primero.", parent=self)
            return

        top = tk.Toplevel(self)
        titulo = "Fotografía en Pantalla Completa"
        if self.current_selected_photo:
            titulo = f"Foto - {self.current_selected_photo.get('denominacion', '')} (Cód. Int: {self.current_selected_photo.get('codigo_interno', '')})"
        top.title(titulo)
        top.geometry("1024x720")
        try:
            top.state("zoomed")
        except Exception:
            pass
        top.configure(bg="#111111")

        bar_top = tk.Frame(top, bg="#222222", height=36)
        bar_top.pack(fill="x")

        lbl_info = tk.Label(bar_top, text=titulo, bg="#222222", fg="#ffffff", font=("Helvetica", 10, "bold"))
        lbl_info.pack(side="left", padx=12, pady=6)

        btn_close = ttk.Button(bar_top, text="✕ Cerrar (Esc)", command=top.destroy)
        btn_close.pack(side="right", padx=10, pady=6)
        top.bind("<Escape>", lambda e: top.destroy())

        lbl_full = tk.Label(top, bg="#111111")
        lbl_full.pack(fill="both", expand=True)

        def _render_full(event=None):
            try:
                top.update_idletasks()
                w = max(300, top.winfo_width() - 20)
                h = max(200, top.winfo_height() - 55)
                with Image.open(self._current_image_path) as img:
                    img_copy = img.copy()
                    img_copy.thumbnail((w, h), Image.Resampling.LANCZOS)
                    top._tk_img = ImageTk.PhotoImage(img_copy)
                    lbl_full.config(image=top._tk_img)
            except Exception as e:
                lbl_full.config(text=f"Error al abrir imagen: {e}", fg="#ffffff")

        top.bind("<Configure>", lambda e: top.after(80, _render_full))
        top.after(50, _render_full)

    def _construir_where(self):
        """Construye dinámicamente la cláusula WHERE y los parámetros para SQL."""
        conditions = ["ap.deleted_at IS NULL"]
        params = []

        query = self.search_var.get().strip()
        criterio = self.search_field_var.get() if hasattr(self, "search_field_var") else "Cód. Interno"

        if query:
            like_val = f"%{query}%"
            if criterio == "Cód. Interno":
                conditions.append("""(
                    ap.codigo_interno LIKE ? OR 
                    ast.codigo_interno LIKE ? OR 
                    CAST(ap.asset_id AS TEXT) = ?
                )""")
                params.extend([like_val, like_val, query])
            elif criterio == "Cód. Patrimonial":
                conditions.append("ast.codigo_patrimonial LIKE ?")
                params.append(like_val)
            elif criterio == "Denominación":
                conditions.append("ast.denominacion LIKE ?")
                params.append(like_val)
            elif criterio == "ID Asset":
                conditions.append("CAST(ap.asset_id AS TEXT) = ?")
                params.append(query)
            else:  # Todo
                conditions.append("""(
                    ap.codigo_interno LIKE ? OR 
                    ast.codigo_interno LIKE ? OR 
                    ast.codigo_patrimonial LIKE ? OR 
                    ast.denominacion LIKE ? OR 
                    ap.ruta_foto LIKE ? OR
                    CAST(ap.id AS TEXT) LIKE ? OR
                    CAST(ap.asset_id AS TEXT) LIKE ?
                )""")
                params.extend([like_val] * 7)

        sync_filtro = self.filter_sync_var.get()
        if sync_filtro == "Sincronizados (1)":
            conditions.append("ap.sincronizado = 1")
        elif sync_filtro == "Pendientes (0)":
            conditions.append("ap.sincronizado = 0")

        where_sql = " WHERE " + " AND ".join(conditions)
        return where_sql, params

    def cargar_pagina(self, numero_pagina):
        """Carga exclusivamente el bloque de registros (LIMIT / OFFSET) correspondiente a la página."""
        try:
            conn = sqlite3.connect(self.db_path)
            cur = conn.cursor()

            where_sql, params = self._construir_where()

            # 1. Contar el total de registros filtrados
            cur.execute(f"""
                SELECT COUNT(*) 
                FROM asset_photos ap
                LEFT JOIN assets ast ON ast.id = ap.asset_id
                {where_sql}
            """, params)
            self.total_records = cur.fetchone()[0]

            # 2. Calcular límites de paginación
            self.page_size = int(self.page_size_var.get())
            self.total_pages = max(1, math.ceil(self.total_records / self.page_size))

            if numero_pagina < 1:
                numero_pagina = 1
            elif numero_pagina > self.total_pages:
                numero_pagina = self.total_pages

            self.page_current = numero_pagina
            self.page_input_var.set(str(self.page_current))
            offset = (self.page_current - 1) * self.page_size

            # 3. Consultar únicamente el lote solicitado (LIMIT / OFFSET)
            sql_data = f"""
                SELECT 
                    ap.id,
                    COALESCE(ap.codigo_interno, ast.codigo_interno, ''),
                    COALESCE(ast.codigo_patrimonial, b.CodPat, ''),
                    COALESCE(ast.denominacion, b.DenBien, 'Bien sin denominación'),
                    COALESCE(ap.ruta_foto, ''),
                    COALESCE(ap.fecha, ''),
                    COALESCE(ap.sincronizado, 0),
                    COALESCE(ap.asset_id, 0)
                FROM asset_photos ap
                LEFT JOIN assets ast ON ast.id = ap.asset_id
                LEFT JOIN bienes b ON b.CodInt = ast.codigo_interno
                {where_sql}
                ORDER BY ap.id DESC
                LIMIT ? OFFSET ?
            """
            cur.execute(sql_data, params + [self.page_size, offset])
            self._current_page_data = cur.fetchall()
            conn.close()

            # 4. Refrescar Treeview de forma ultraligera
            for item in self.tree.get_children():
                self.tree.delete(item)

            for row in self._current_page_data:
                photo_id, cod_int, cod_pat, den, ruta, fecha, sinc, asset_id = row
                sinc_txt = "Sí (1)" if sinc == 1 else "No (0)"
                self.tree.insert(
                    "", "end",
                    values=(photo_id, cod_int, cod_pat, den, os.path.basename(ruta) if ruta else "", fecha, sinc_txt)
                )

            # 5. Actualizar información de paginación
            desde = offset + 1 if self.total_records > 0 else 0
            hasta = min(offset + len(self._current_page_data), self.total_records)
            self.lbl_pages_total.config(text=f"de {self.total_pages}")
            self.lbl_page_info.config(text=f"Mostrando {desde} - {hasta} de {self.total_records} fotos")
            self.lbl_global_count.config(text=f"Total: {self.total_records} fotos")

            # 6. Estado de los botones de navegación
            self.btn_first.config(state="normal" if self.page_current > 1 else "disabled")
            self.btn_prev.config(state="normal" if self.page_current > 1 else "disabled")
            self.btn_next.config(state="normal" if self.page_current < self.total_pages else "disabled")
            self.btn_last.config(state="normal" if self.page_current < self.total_pages else "disabled")

        except Exception as e:
            mb.showerror("Error al cargar fotos", f"No se pudo consultar asset_photos:\n{e}", parent=self)

    def aplicar_filtros(self):
        """Reinicia a la primera página aplicando los filtros vigentes."""
        self.cargar_pagina(1)

    def ir_primera_pagina(self):
        self.cargar_pagina(1)

    def ir_ultima_pagina(self):
        self.cargar_pagina(self.total_pages)

    def pagina_anterior(self):
        if self.page_current > 1:
            self.cargar_pagina(self.page_current - 1)

    def pagina_siguiente(self):
        if self.page_current < self.total_pages:
            self.cargar_pagina(self.page_current + 1)

    def _ir_a_pagina_escrita(self):
        try:
            pag = int(self.page_input_var.get().strip())
            self.cargar_pagina(pag)
        except ValueError:
            self.page_input_var.set(str(self.page_current))

    def _on_change_page_size(self, event=None):
        self.cargar_pagina(1)

    def _on_tree_select(self, event):
        """Carga bajo demanda la fotografía seleccionada (Lazy loading)."""
        selected = self.tree.selection()
        if not selected:
            return

        item = self.tree.item(selected[0])
        photo_id = item["values"][0]

        for row in getattr(self, "_current_page_data", []):
            if row[0] == photo_id:
                self.current_selected_photo = {
                    "id": row[0],
                    "codigo_interno": row[1],
                    "cod_patrimonial": row[2],
                    "denominacion": row[3],
                    "ruta_foto": row[4],
                    "fecha": row[5],
                    "sincronizado": row[6],
                    "asset_id": row[7]
                }
                self._actualizar_visor(self.current_selected_photo)
                break

    def _actualizar_visor(self, photo_data):
        """Muestra los detalles y carga la imagen seleccionada de forma aislada."""
        self.lbl_den.config(text=f"📦 {photo_data['denominacion']}")
        self.lbl_codes.config(
            text=f"Cód. Patrimonial: {photo_data['cod_patrimonial'] or 'S/C'} | "
                 f"Cód. Interno: {photo_data['codigo_interno'] or 'S/C'}"
        )
        ruta = photo_data["ruta_foto"]
        self.lbl_path.config(text=f"Archivo: {ruta}")

        # Liberar imagen anterior de memoria
        self._current_tk_img = None
        self._current_image_path = None

        archivo_local = self._resolver_ruta_local(ruta)
        if archivo_local and os.path.exists(archivo_local):
            self._mostrar_imagen_en_label(archivo_local)
        else:
            if ruta and str(ruta).strip():
                self.lbl_canvas.config(text="⬇️ Descargando del servidor...", image="")
                threading.Thread(target=self._hilo_descargar_foto, args=(ruta,), daemon=True).start()
            else:
                self.lbl_canvas.config(text="📷 Sin fotografía asignada", image="")

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
            os.path.join(self.photos_dir, "photos", nombre),
            os.path.join(self.photos_dir, "uploads", "photos", nombre),
        ]
        for c in candidatos:
            if os.path.exists(c):
                return c
        return None

    def _mostrar_imagen_en_label(self, path_img):
        """Registra la ruta activa y dispara el renderizado ajustado al espacio total."""
        self._current_image_path = path_img
        self._render_imagen_actual()

    def _render_imagen_actual(self):
        """Renderiza la imagen ocupando TODO el espacio disponible del contenedor sin deformar."""
        if not getattr(self, "_current_image_path", None) or not os.path.exists(self._current_image_path):
            return
        try:
            self.frame_img_container.update_idletasks()
            cont_w = self.frame_img_container.winfo_width()
            cont_h = self.frame_img_container.winfo_height()

            # Espacio disponible con margen estético de seguridad
            avail_w = max(200, cont_w - 12)
            avail_h = max(150, cont_h - 12)

            with Image.open(self._current_image_path) as img:
                img_copy = img.copy()
                img_copy.thumbnail((avail_w, avail_h), Image.Resampling.LANCZOS)
                self._current_tk_img = ImageTk.PhotoImage(img_copy)
                self.lbl_canvas.config(image=self._current_tk_img, text="")
        except Exception as e:
            self.lbl_canvas.config(text=f"❌ Error al abrir imagen:\n{e}", image="")

    def _on_container_resize(self, event=None):
        """Debounce al redimensionar la ventana o splitter para reescalar la foto fluidamente."""
        if not getattr(self, "_current_image_path", None):
            return
        if hasattr(self, "_resize_job") and self._resize_job:
            try:
                self.after_cancel(self._resize_job)
            except Exception:
                pass
        self._resize_job = self.after(100, self._render_imagen_actual)

    def _hilo_descargar_foto(self, ruta_remota):
        try:
            url = self.api_client.get_photo_url(ruta_remota)
            if not url:
                return

            nombre_archivo = os.path.basename(str(ruta_remota).replace("\\", "/"))
            destino = os.path.join(self.photos_dir, nombre_archivo)

            import urllib.request
            req = urllib.request.Request(
                url,
                headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AcontarSoft/1.0"}
            )
            with urllib.request.urlopen(req, timeout=20) as response, open(destino, "wb") as out_file:
                out_file.write(response.read())

            if os.path.exists(destino) and os.path.getsize(destino) > 0:
                self.after(0, lambda: self._mostrar_imagen_en_label(destino))
            else:
                self.after(0, lambda: self.lbl_canvas.config(
                    text="📷 Imagen vacía recibida del servidor", image=""
                ))
        except Exception as e:
            self.after(0, lambda: self.lbl_canvas.config(
                text=f"📷 Foto en servidor no descargada:\n{e}", image=""
            ))

    def abrir_en_visor_sistema(self):
        if not self.current_selected_photo:
            mb.showinfo("Información", "Por favor seleccione una fotografía primero.", parent=self)
            return

        ruta = self._resolver_ruta_local(self.current_selected_photo["ruta_foto"])
        if ruta and os.path.exists(ruta):
            try:
                os.startfile(ruta)
            except Exception as e:
                mb.showerror("Error", f"No se pudo abrir el visor del sistema: {e}", parent=self)
        else:
            mb.showwarning("Atención", "El archivo de imagen no se encuentra en el disco local.", parent=self)

    def abrir_carpeta_fotos(self):
        try:
            os.startfile(self.photos_dir)
        except Exception as e:
            mb.showerror("Error", f"No se pudo abrir la carpeta: {e}", parent=self)

    def dialogo_asociar_foto(self):
        archivo = filedialog.askopenfilename(
            title="Seleccionar Fotografía de Activo",
            filetypes=[("Imágenes", "*.jpg;*.jpeg;*.png"), ("Todos los archivos", "*.*")],
            parent=self
        )
        if not archivo:
            return

        win_input = tk.Toplevel(self)
        win_input.title("Asociar Fotografía a Bien")
        win_input.geometry("380x210")
        win_input.resizable(False, False)
        win_input.transient(self)
        win_input.grab_set()

        cod_default = self.current_selected_photo["codigo_interno"] if self.current_selected_photo else ""
        v_cod = tk.StringVar(value=cod_default)

        ttk.Label(win_input, text="Archivo seleccionado:").pack(anchor="w", padx=15, pady=(15, 2))
        ttk.Label(win_input, text=os.path.basename(archivo), font=("Helvetica", 9, "bold")).pack(anchor="w", padx=15)

        ttk.Label(win_input, text="Código Interno o Patrimonial del Bien:").pack(anchor="w", padx=15, pady=(10, 2))
        etr_cod = ttk.Entry(win_input, textvariable=v_cod, width=25)
        etr_cod.pack(anchor="w", padx=15)
        etr_cod.focus_set()

        def _guardar_asociacion():
            codigo = v_cod.get().strip()
            if not codigo:
                mb.showwarning("Atención", "Ingrese el código del bien.", parent=win_input)
                return

            try:
                nombre_destino = f"code_{codigo}_{os.path.basename(archivo)}"
                ruta_final = os.path.join(self.photos_dir, nombre_destino)
                shutil.copy2(archivo, ruta_final)

                conn = sqlite3.connect(self.db_path)
                cur = conn.cursor()
                cur.execute("""
                    SELECT id, codigo_interno FROM assets 
                    WHERE codigo_interno = ? OR codigo_patrimonial = ? LIMIT 1
                """, (codigo, codigo))
                row_ast = cur.fetchone()
                asset_id = row_ast[0] if row_ast else None
                cod_int = row_ast[1] if row_ast else codigo

                now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                cur.execute("""
                    INSERT INTO asset_photos (
                        asset_id, codigo_interno, ruta_foto, fecha, sincronizado, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, 0, ?, ?)
                """, (asset_id, cod_int, nombre_destino, now_str, now_str, now_str))
                conn.commit()
                conn.close()

                win_input.destroy()
                mb.showinfo("Éxito", "Fotografía asociada correctamente a asset_photos.", parent=self)
                self.cargar_pagina(1)

            except Exception as e:
                mb.showerror("Error", f"No se pudo guardar la fotografía:\n{e}", parent=win_input)

        ttk.Button(win_input, text="💾 Guardar Asociación", command=_guardar_asociacion).pack(fill="x", padx=15, pady=15)

    def subir_foto_al_servidor(self):
        if not self.current_selected_photo:
            mb.showinfo("Información", "Seleccione una foto para subir.", parent=self)
            return

        photo = self.current_selected_photo
        if photo["sincronizado"] == 1:
            mb.showinfo("Información", "Esta fotografía ya figura como sincronizada en el servidor.", parent=self)
            return

        archivo_local = self._resolver_ruta_local(photo["ruta_foto"])
        if not archivo_local or not os.path.exists(archivo_local):
            mb.showerror("Error", "No se encontró el archivo local para subir.", parent=self)
            return

        def _hilo_subida():
            try:
                conn = sqlite3.connect(self.db_path)
                cur = conn.cursor()
                cur.execute("""
                    SELECT id FROM inventory_records 
                    WHERE codigo_interno = ? OR codigo_patrimonial = ? LIMIT 1
                """, (photo["codigo_interno"], photo["cod_patrimonial"]))
                row_inv = cur.fetchone()
                user_id = int(get_config(conn, "logged_user_id", "1"))
                conn.close()

                if not row_inv:
                    self.after(0, lambda: mb.showwarning(
                        "Atención", "No se encontró un registro en inventory_records para vincular la foto.", parent=self
                    ))
                    return

                record_id = row_inv[0]
                res = self.api_client.upload_photo(record_id, user_id, archivo_local)

                if res.get("status_code") in (200, 201):
                    conn = sqlite3.connect(self.db_path)
                    cur = conn.cursor()
                    cur.execute("UPDATE asset_photos SET sincronizado = 1 WHERE id = ?", (photo["id"],))
                    conn.commit()
                    conn.close()

                    self.after(0, lambda: mb.showinfo("Éxito", "Foto subida y sincronizada correctamente.", parent=self))
                    self.after(0, lambda: self.cargar_pagina(self.page_current))
                else:
                    msg = res.get("data", {}).get("message", "Error desconocido del servidor.")
                    self.after(0, lambda: mb.showerror("Error al subir", f"El servidor rechazó la foto:\n{msg}", parent=self))

            except Exception as e:
                self.after(0, lambda: mb.showerror("Error de red", f"No se pudo conectar al servidor:\n{e}", parent=self))

        threading.Thread(target=_hilo_subida, daemon=True).start()

    def eliminar_foto(self):
        if not self.current_selected_photo:
            mb.showinfo("Información", "Seleccione una foto para eliminar.", parent=self)
            return

        photo_id = self.current_selected_photo["id"]
        if not mb.askyesno("Confirmar eliminación", f"¿Desea eliminar el registro de la foto #{photo_id}?", parent=self):
            return

        try:
            conn = sqlite3.connect(self.db_path)
            cur = conn.cursor()
            cur.execute("""
                UPDATE asset_photos 
                SET deleted_at = CURRENT_TIMESTAMP 
                WHERE id = ?
            """, (photo_id,))
            conn.commit()
            conn.close()

            mb.showinfo("Éxito", "Registro de fotografía eliminado.", parent=self)
            self.current_selected_photo = None
            self.lbl_canvas.config(image="", text="Registro eliminado")
            self.cargar_pagina(self.page_current)

        except Exception as e:
            mb.showerror("Error", f"No se pudo eliminar el registro:\n{e}", parent=self)

    def escanear_carpeta_local(self):
        try:
            archivos = [
                f for f in os.listdir(self.photos_dir) 
                if f.lower().endswith((".jpg", ".jpeg", ".png"))
            ]
            if not archivos:
                mb.showinfo("Escanear Carpeta", "No se encontraron imágenes en la carpeta photos/.", parent=self)
                return

            conn = sqlite3.connect(self.db_path)
            cur = conn.cursor()
            cur.execute("SELECT ruta_foto FROM asset_photos WHERE deleted_at IS NULL")
            registrados = {os.path.basename(r[0]) for r in cur.fetchall() if r[0]}

            nuevos = 0
            now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            for f in archivos:
                if f not in registrados:
                    cod = f.replace("code_", "").split(".")[0].split("_")[0]

                    cur.execute("""
                        SELECT id, codigo_interno FROM assets 
                        WHERE codigo_interno = ? OR codigo_patrimonial = ? LIMIT 1
                    """, (cod, cod))
                    row = cur.fetchone()
                    asset_id = row[0] if row else None
                    cod_int = row[1] if row else cod

                    cur.execute("""
                        INSERT INTO asset_photos (
                            asset_id, codigo_interno, ruta_foto, fecha, sincronizado, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, 0, ?, ?)
                    """, (asset_id, cod_int, f, now_str, now_str, now_str))
                    nuevos += 1

            conn.commit()
            conn.close()

            mb.showinfo("Escanear Carpeta", f"Escaneo completado.\nSe registraron {nuevos} nuevas fotografías locales.", parent=self)
            self.cargar_pagina(1)

        except Exception as e:
            mb.showerror("Error al escanear", f"Ocurrió un error al escanear la carpeta:\n{e}", parent=self)
