"""
Módulo de Estadísticas y Dashboard del Inventario (gui_estadisticas.py)
Visualización gráfica, métricas gerenciales, tablas por Sede, Cuenta,
Inventariador, Estado de Conservación, Bienes Faltantes Detallado
y Bienes de Baja (Informativo).
"""

import os
import queue
import threading
import tkinter as tk
from tkinter import ttk, PhotoImage, messagebox as mb

from db.conex import iniciar_conexion_sqlite
from db.query import datos_iniciales
from data.exp_excel import exportar_excel
from gui.gui_detalles import Window_detalles
from utils.order_utils import sort_by
from utils.helpers import resource_path


class Window_estadisticas(tk.Toplevel):
    """Ventana interactiva de estadísticas, métricas y dashboard del inventario."""

    def __init__(self, root=None):
        super().__init__(root)
        self.root = root
        self.title("📊 Panel de Estadísticas y Dashboard del Inventario")
        self.configure(bg="#f8fafc")
        self.geometry("1320x800")
        self.minsize(1100, 680)

        self._cargar_favicon()
        self._centrar_ventana(1320, 800)
        try:
            self.state("zoomed")
        except Exception:
            pass

        # Cargar datos institucionales (Entidad y Periodo)
        self.entidad_nombre = "ENTIDAD"
        self.periodo_nombre = ""
        try:
            d_ini = datos_iniciales()
            if d_ini and len(d_ini) > 2:
                self.entidad_nombre = str(d_ini[1] or "ENTIDAD").strip()
                self.periodo_nombre = str(d_ini[2] or "").strip()
        except Exception as e:
            print(f"[ESTADISTICAS][WARN] Error cargando datos iniciales: {e}")

        # Iconos opcionales
        self.iconoxls = self._cargar_icono("img/excel.png")
        self.iconoref = self._cargar_icono("img/sincronizar.png")

        # Variables de control y filtros generales
        self.var_sede_filtro = tk.StringVar(value="[ TODAS LAS SEDES / LOCALES ]")
        self.var_condicion_modo = tk.StringVar(value="ALTA")  # ALTA | TODOS | BAJA

        # Variables de KPIs
        self.var_kpi_total = tk.StringVar(value="...")
        self.var_kpi_inv = tk.StringVar(value="...")
        self.var_kpi_fal = tk.StringVar(value="...")
        self.var_kpi_pct = tk.StringVar(value="0.0%")
        self.var_kpi_sob = tk.StringVar(value="...")
        self.var_kpi_baja = tk.StringVar(value="...")
        self.var_kpi_val_adq = tk.StringVar(value="S/ 0.00")
        self.var_kpi_val_baja = tk.StringVar(value="S/ 0.00")

        # Variables de búsqueda en pestañas
        self.var_search_locales = tk.StringVar()
        self.var_search_cuentas = tk.StringVar()
        self.var_search_personal = tk.StringVar()
        self.var_search_denos = tk.StringVar()
        self.var_search_bajas = tk.StringVar()

        # Variables de filtros para la pestaña de Faltantes Detallado
        self.var_search_faltantes = tk.StringVar()
        self.var_fal_filtro_local = tk.StringVar(value="[ TODOS ]")
        self.var_fal_filtro_area = tk.StringVar(value="[ TODAS ]")
        self.var_fal_filtro_oficina = tk.StringVar(value="")
        self.busqueda_oficina_var = self.var_fal_filtro_oficina
        self.var_fal_filtro_cta = tk.StringVar(value="[ TODAS ]")
        self.var_fal_filtro_responsable = tk.StringVar(value="[ TODOS ]")

        # Control del popup predictivo de oficinas
        self._popup_oficinas = None
        self._listbox_oficinas = None
        self._lbl_popup_info = None
        self._resultados_oficinas_actuales = []
        self._entry_activo_oficina = None

        # Listas de opciones de combos para Faltantes
        self.lista_fal_locales = ["[ TODOS ]"]
        self.lista_fal_areas = ["[ TODAS ]"]
        self.lista_fal_oficinas = ["[ TODAS ]"]
        self.lista_fal_cuentas = ["[ TODAS ]"]
        self.lista_fal_responsables = ["[ TODOS ]"]

        # Almacenamiento de datos crudos
        self.raw_locales = []
        self.raw_cuentas = []
        self.raw_personal = []
        self.raw_denos = []
        self.raw_estados = []
        self.raw_bajas = []
        self.raw_faltantes = []
        self.lista_sedes_combo = ["[ TODAS LAS SEDES / LOCALES ]"]

        # Control asíncrono thread-safe
        self.is_loading = False
        self._data_queue = queue.Queue()

        self._configurar_estilos()
        self._crear_interfaz()

        # Cerrar popup al destruir la ventana
        self.bind("<Destroy>", lambda e: self._cerrar_popup_oficinas() if e.widget == self else None)

        # Iniciar carga de datos en segundo plano
        self.cargar_datos_asincrono()

    def _cargar_favicon(self):
        try:
            ruta_ico = resource_path("img/inventario.ico")
            if os.path.exists(ruta_ico):
                self.iconbitmap(ruta_ico)
        except Exception:
            pass

    def _cargar_icono(self, rel_path):
        try:
            ruta = resource_path(rel_path)
            if os.path.exists(ruta):
                return PhotoImage(file=ruta)
        except Exception:
            pass
        return None

    def _centrar_ventana(self, w, h):
        self.update_idletasks()
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        x = max(0, (sw - w) // 2)
        y = max(0, (sh - h) // 2)
        self.geometry(f"{w}x{h}+{x}+{y}")

    def _configurar_estilos(self):
        s = ttk.Style()
        try:
            s.theme_use("clam")
        except Exception:
            pass

        # Notebook
        s.configure("Stats.TNotebook", background="#f8fafc", borderwidth=0)
        s.configure("Stats.TNotebook.Tab", font=("Segoe UI", 9, "bold"), padding=(12, 6), background="#e2e8f0", foreground="#334155")
        s.map("Stats.TNotebook.Tab",
              background=[("selected", "#ffffff")],
              foreground=[("selected", "#0284c7")])

        # Treeviews
        s.configure("Stats.Treeview", font=("Segoe UI", 9), rowheight=25, background="#ffffff", fieldbackground="#ffffff", foreground="#0f172a")
        s.configure("Stats.Treeview.Heading", font=("Segoe UI", 9, "bold"), background="#f1f5f9", foreground="#334155", relief="flat")
        s.map("Stats.Treeview.Heading", background=[("active", "#e2e8f0")])
        s.map("Stats.Treeview", background=[("selected", "#e0f2fe")], foreground=[("selected", "#0369a1")])

    # ─────────────────────────────────────────────────────────────────────────
    # CONSTRUCCIÓN DE LA INTERFAZ
    # ─────────────────────────────────────────────────────────────────────────
    def _crear_interfaz(self):
        # 1. HEADER BANNER
        header = tk.Frame(self, bg="#0f172a", height=66)
        header.pack(fill="x", side="top")

        f_tit = tk.Frame(header, bg="#0f172a")
        f_tit.pack(side="left", padx=16, pady=10)

        lbl_tit = tk.Label(
            f_tit,
            text="📊 DASHBOARD Y ESTADÍSTICAS DEL INVENTARIO",
            font=("Segoe UI", 13, "bold"),
            fg="#f8fafc", bg="#0f172a"
        )
        lbl_tit.pack(anchor="w")

        sub_text = f"Entidad: {self.entidad_nombre}"
        if self.periodo_nombre:
            sub_text += f"  |  Período: {self.periodo_nombre}"
        self.lbl_sub = tk.Label(
            f_tit,
            text=sub_text,
            font=("Segoe UI", 9),
            fg="#94a3b8", bg="#0f172a"
        )
        self.lbl_sub.pack(anchor="w")

        # Acciones y Filtros en Header
        f_actions = tk.Frame(header, bg="#0f172a")
        f_actions.pack(side="right", padx=16, pady=10)

        # Filtro de Condición (Alta vs Todos vs Baja)
        lbl_f_cond = tk.Label(f_actions, text="Condición:", font=("Segoe UI", 9, "bold"), fg="#cbd5e1", bg="#0f172a")
        lbl_f_cond.pack(side="left", padx=(0, 4))

        self.cbx_condicion = ttk.Combobox(
            f_actions,
            values=[
                "Bienes en ALTA (Activos / Inventariables)",
                "Todos los Bienes (Alta + Baja)",
                "Solo Bienes de BAJA (Informativo)"
            ],
            state="readonly",
            width=34
        )
        self.cbx_condicion.current(0)
        self.cbx_condicion.pack(side="left", padx=(0, 10))
        self.cbx_condicion.bind("<<ComboboxSelected>>", self._on_cambio_condicion)

        # Filtro de Sede en Header
        lbl_f_sede = tk.Label(f_actions, text="Sede:", font=("Segoe UI", 9, "bold"), fg="#cbd5e1", bg="#0f172a")
        lbl_f_sede.pack(side="left", padx=(0, 4))

        self.cbx_sede = ttk.Combobox(
            f_actions,
            textvariable=self.var_sede_filtro,
            values=self.lista_sedes_combo,
            state="readonly",
            width=26
        )
        self.cbx_sede.pack(side="left", padx=(0, 10))
        self.cbx_sede.bind("<<ComboboxSelected>>", lambda _e: self.cargar_datos_asincrono())

        btn_ref = ttk.Button(f_actions, text="🔄 Actualizar", command=self.cargar_datos_asincrono)
        btn_ref.pack(side="left", padx=4)

        btn_exp = ttk.Button(f_actions, text="📥 Exportar Excel", command=self.exportar_pestana_activa)
        btn_exp.pack(side="left", padx=4)

        btn_close = ttk.Button(f_actions, text="✕ Cerrar", command=self.destroy)
        btn_close.pack(side="left", padx=(8, 0))

        # 2. CONTENEDOR PRINCIPAL
        self.main_container = tk.Frame(self, bg="#f8fafc")
        self.main_container.pack(fill="both", expand=True, padx=12, pady=(6, 4))

        # Banner de Distinción Institucional (Alta vs Baja)
        self.f_aviso_baja = tk.Frame(self.main_container, bg="#eff6ff", bd=1, relief="solid")
        self.f_aviso_baja.pack(fill="x", pady=(0, 4))

        tk.Label(
            self.f_aviso_baja,
            text="ℹ️ Criterio Institucional: Las estadísticas y porcentajes de avance computan sobre bienes en CONDICIÓN ALTA (Activos). Los bienes de BAJA son informativos. Para auditar los faltantes al detalle, use la pestaña '⚠️ Bienes Faltantes Detallado'.",
            font=("Segoe UI", 8, "italic"),
            fg="#1e40af", bg="#eff6ff",
            padx=10, pady=3
        ).pack(side="left")

        # 3. FILA DE TARJETAS KPI
        self._crear_kpis(self.main_container)

        # 4. NOTEBOOK DE PESTAÑAS
        self.notebook = ttk.Notebook(self.main_container, style="Stats.TNotebook")
        self.notebook.pack(fill="both", expand=True, pady=(4, 0))

        # Pestaña 0: Resumen y Gráficos
        self.tab_resumen = tk.Frame(self.notebook, bg="#f8fafc")
        self.notebook.add(self.tab_resumen, text=" 📈 Resumen y Gráficos ")
        self._construir_tab_resumen(self.tab_resumen)

        # Pestaña 1: Bienes Faltantes Detallado (¡NUEVA!)
        self.tab_faltantes = tk.Frame(self.notebook, bg="#f8fafc")
        self.notebook.add(self.tab_faltantes, text=" ⚠️ Bienes Faltantes Detallado ")
        self._construir_tab_faltantes(self.tab_faltantes)

        # Pestaña 2: Por Sede / Local
        self.tab_locales = tk.Frame(self.notebook, bg="#f8fafc")
        self.notebook.add(self.tab_locales, text=" 🏢 Avance por Sede / Local ")
        self._construir_tab_locales(self.tab_locales)

        # Pestaña 3: Por Cuenta Contable
        self.tab_cuentas = tk.Frame(self.notebook, bg="#f8fafc")
        self.notebook.add(self.tab_cuentas, text=" 💰 Por Cuenta Contable ")
        self._construir_tab_cuentas(self.tab_cuentas)

        # Pestaña 4: Por Inventariador
        self.tab_personal = tk.Frame(self.notebook, bg="#f8fafc")
        self.notebook.add(self.tab_personal, text=" 👷 Rendimiento por Inventariador ")
        self._construir_tab_personal(self.tab_personal)

        # Pestaña 5: Top Bienes
        self.tab_denos = tk.Frame(self.notebook, bg="#f8fafc")
        self.notebook.add(self.tab_denos, text=" 📋 Top 30 Tipos de Bien ")
        self._construir_tab_denos(self.tab_denos)

        # Pestaña 6: Bienes de Baja (Informativo)
        self.tab_bajas = tk.Frame(self.notebook, bg="#f8fafc")
        self.notebook.add(self.tab_bajas, text=" 📉 Bienes de Baja (Informativo) ")
        self._construir_tab_bajas(self.tab_bajas)

        # 5. BARRA DE ESTADO INFERIOR
        self.status_bar = tk.Frame(self, bg="#e2e8f0", height=24)
        self.status_bar.pack(fill="x", side="bottom")

        self.lbl_status = tk.Label(
            self.status_bar,
            text="Listo",
            font=("Segoe UI", 8),
            fg="#475569", bg="#e2e8f0"
        )
        self.lbl_status.pack(side="left", padx=10)

    def _on_cambio_condicion(self, _event=None):
        idx = self.cbx_condicion.current()
        if idx == 0:
            self.var_condicion_modo.set("ALTA")
        elif idx == 1:
            self.var_condicion_modo.set("TODOS")
        elif idx == 2:
            self.var_condicion_modo.set("BAJA")
        self.cargar_datos_asincrono()

    # ─────────────────────────────────────────────────────────────────────────
    # SECCIÓN DE TARJETAS KPI (Distinción Alta / Baja / Avance)
    # ─────────────────────────────────────────────────────────────────────────
    def _crear_kpis(self, parent):
        f_kpi = tk.Frame(parent, bg="#f8fafc")
        f_kpi.pack(fill="x", pady=(0, 4))

        for i in range(7):
            f_kpi.columnconfigure(i, weight=1)

        # 1. Total Padrón Activo (Alta)
        self._crear_kpi_card(f_kpi, 0, "📦 Padrón Activo (Alta)", self.var_kpi_total, "#0284c7", "Inventariables")
        # 2. Inventariados
        self._crear_kpi_card(f_kpi, 1, "✅ Inventariados", self.var_kpi_inv, "#16a34a", "Ubicados / Registrados")
        # 3. Faltantes Reales (con clic directo a la pestaña de faltantes)
        card_fal = self._crear_kpi_card(f_kpi, 2, "⏳ Faltantes Reales", self.var_kpi_fal, "#dc2626", "👉 Clic para ver detalle")
        card_fal.bind("<Button-1>", lambda _e: self._ir_a_tab_faltantes())
        # 4. % Avance Real
        self._crear_kpi_card(f_kpi, 3, "🎯 % Avance Real", self.var_kpi_pct, "#059669", "Progreso Padrón Activo")
        # 5. Sobrantes
        self._crear_kpi_card(f_kpi, 4, "➕ Sobrantes", self.var_kpi_sob, "#7c3aed", "Fuera de Padrón")
        # 6. Bienes de Baja (Informativo)
        card_baj = self._crear_kpi_card(f_kpi, 5, "📉 Bajas (Informativo)", self.var_kpi_baja, "#64748b", "No inciden en avance")
        card_baj.bind("<Button-1>", lambda _e: self.notebook.select(self.tab_bajas))
        # 7. Valorización
        self._crear_kpi_card_doble(f_kpi, 6, "💵 Valorización Activa", self.var_kpi_val_adq, self.var_kpi_val_baja, "#4338ca")

    def _ir_a_tab_faltantes(self):
        self.notebook.select(self.tab_faltantes)

    def _crear_kpi_card(self, parent, col, titulo, var, color_fg, subtitulo):
        card = tk.Frame(parent, bg="#ffffff", bd=1, relief="solid", highlightthickness=0, cursor="hand2")
        card.grid(row=0, column=col, padx=2, sticky="ew")

        tk.Frame(card, bg=color_fg, height=3).pack(fill="x", side="top")
        content = tk.Frame(card, bg="#ffffff", padx=6, pady=4)
        content.pack(fill="both", expand=True)

        tk.Label(content, text=titulo, font=("Segoe UI", 8, "bold"), fg="#64748b", bg="#ffffff").pack(anchor="w")
        tk.Label(content, textvariable=var, font=("Segoe UI", 14, "bold"), fg=color_fg, bg="#ffffff").pack(anchor="w", pady=(1, 0))
        tk.Label(content, text=subtitulo, font=("Segoe UI", 7), fg="#94a3b8", bg="#ffffff").pack(anchor="w")
        return card

    def _crear_kpi_card_doble(self, parent, col, titulo, var1, var2, color_fg):
        card = tk.Frame(parent, bg="#ffffff", bd=1, relief="solid", highlightthickness=0)
        card.grid(row=0, column=col, padx=2, sticky="ew")

        tk.Frame(card, bg=color_fg, height=3).pack(fill="x", side="top")
        content = tk.Frame(card, bg="#ffffff", padx=6, pady=3)
        content.pack(fill="both", expand=True)

        tk.Label(content, text=titulo, font=("Segoe UI", 8, "bold"), fg="#64748b", bg="#ffffff").pack(anchor="w")

        f_val = tk.Frame(content, bg="#ffffff")
        f_val.pack(fill="x", pady=1)
        tk.Label(f_val, text="Activo: ", font=("Segoe UI", 7, "bold"), fg="#475569", bg="#ffffff").pack(side="left")
        tk.Label(f_val, textvariable=var1, font=("Segoe UI", 8, "bold"), fg=color_fg, bg="#ffffff").pack(side="left")

        f_val2 = tk.Frame(content, bg="#ffffff")
        f_val2.pack(fill="x")
        tk.Label(f_val2, text="Bajas: ", font=("Segoe UI", 7, "bold"), fg="#64748b", bg="#ffffff").pack(side="left")
        tk.Label(f_val2, textvariable=var2, font=("Segoe UI", 8, "bold"), fg="#64748b", bg="#ffffff").pack(side="left")

    # ─────────────────────────────────────────────────────────────────────────
    # PESTAÑA 0: RESUMEN Y GRÁFICOS VISUALES
    # ─────────────────────────────────────────────────────────────────────────
    def _construir_tab_resumen(self, parent):
        paned = tk.PanedWindow(parent, orient="horizontal", bg="#cbd5e1", bd=0, sashwidth=4)
        paned.pack(fill="both", expand=True, padx=6, pady=6)

        f_left = tk.Frame(paned, bg="#ffffff", bd=1, relief="solid")
        paned.add(f_left, minsize=480, width=580)

        lbl_chart_tit = tk.Label(
            f_left,
            text="Distribución Visual del Inventario Activo (Condición Alta)",
            font=("Segoe UI", 10, "bold"),
            fg="#1e293b", bg="#f1f5f9",
            padx=10, pady=6
        )
        lbl_chart_tit.pack(fill="x")

        self.canvas_graficos = tk.Canvas(f_left, bg="#ffffff", highlightthickness=0)
        self.canvas_graficos.pack(fill="both", expand=True, padx=8, pady=8)

        f_right = tk.Frame(paned, bg="#ffffff", bd=1, relief="solid")
        paned.add(f_right, minsize=420, width=540)

        lbl_t_tit = tk.Label(
            f_right,
            text="Resumen por Estado de Conservación (Condición Alta)",
            font=("Segoe UI", 10, "bold"),
            fg="#1e293b", bg="#f1f5f9",
            padx=10, pady=6
        )
        lbl_t_tit.pack(fill="x")

        f_tree_est = tk.Frame(f_right, bg="#ffffff")
        f_tree_est.pack(fill="both", expand=True, padx=6, pady=6)

        cols = ("estado", "total", "inv", "fal", "pct_av", "pct_padron")
        self.tree_estados = ttk.Treeview(
            f_tree_est,
            columns=cols,
            show="headings",
            style="Stats.Treeview",
            selectmode="browse"
        )
        self.tree_estados.heading("estado", text="Estado de Conservación")
        self.tree_estados.heading("total", text="Total")
        self.tree_estados.heading("inv", text="Inventariados")
        self.tree_estados.heading("fal", text="Faltantes")
        self.tree_estados.heading("pct_av", text="% Avance")
        self.tree_estados.heading("pct_padron", text="% del Total")

        self.tree_estados.column("estado", width=140, anchor="w")
        self.tree_estados.column("total", width=65, anchor="e")
        self.tree_estados.column("inv", width=85, anchor="e")
        self.tree_estados.column("fal", width=75, anchor="e")
        self.tree_estados.column("pct_av", width=70, anchor="center")
        self.tree_estados.column("pct_padron", width=70, anchor="center")

        scr = ttk.Scrollbar(f_tree_est, orient="vertical", command=self.tree_estados.yview)
        self.tree_estados.configure(yscrollcommand=scr.set)

        self.tree_estados.pack(side="left", fill="both", expand=True)
        scr.pack(side="right", fill="y")

        self.tree_estados.tag_configure("totales", font=("Segoe UI", 9, "bold"), background="#e2e8f0")
        self.tree_estados.tag_configure("par", background="#f8fafc")
        self.tree_estados.tag_configure("impar", background="#ffffff")

    def _redibujar_graficos_canvas(self, estados, total_alta, inv_alta, fal_alta, sob_global, total_baja):
        c = self.canvas_graficos
        c.delete("all")

        w = c.winfo_width()
        h = c.winfo_height()
        if w < 100 or h < 100:
            c.after(100, lambda: self._redibujar_graficos_canvas(estados, total_alta, inv_alta, fal_alta, sob_global, total_baja))
            return

        c.create_text(20, 16, text="AVANCE REAL DEL INVENTARIO ACTIVO (ALTA)", anchor="w", font=("Segoe UI", 9, "bold"), fill="#1e293b")

        pct_inv = (inv_alta / total_alta * 100) if total_alta > 0 else 0
        pct_fal = (fal_alta / total_alta * 100) if total_alta > 0 else 0

        bar_x = 20
        bar_y = 32
        bar_w = max(w - 40, 200)
        bar_h = 24

        c.create_rectangle(bar_x, bar_y, bar_x + bar_w, bar_y + bar_h, fill="#fee2e2", outline="#fca5a5")

        inv_w = int(bar_w * (pct_inv / 100.0))
        if inv_w > 0:
            c.create_rectangle(bar_x, bar_y, bar_x + inv_w, bar_y + bar_h, fill="#10b981", outline="")
            if inv_w > 45:
                c.create_text(bar_x + inv_w // 2, bar_y + bar_h // 2, text=f"{pct_inv:.1f}%", font=("Segoe UI", 8, "bold"), fill="#ffffff")

        c.create_rectangle(bar_x, bar_y + 30, bar_x + 10, bar_y + 40, fill="#10b981", outline="")
        c.create_text(bar_x + 14, bar_y + 35, text=f"Inventariados: {inv_alta:,} ({pct_inv:.1f}%)", anchor="w", font=("Segoe UI", 8), fill="#166534")

        c.create_rectangle(bar_x + 190, bar_y + 30, bar_x + 200, bar_y + 40, fill="#fee2e2", outline="#fca5a5")
        c.create_text(bar_x + 204, bar_y + 35, text=f"Faltantes Reales: {fal_alta:,} ({pct_fal:.1f}%)", anchor="w", font=("Segoe UI", 8), fill="#991b1b")

        c.create_rectangle(bar_x + 380, bar_y + 30, bar_x + 390, bar_y + 40, fill="#64748b", outline="")
        c.create_text(bar_x + 394, bar_y + 35, text=f"Bajas (Info): {total_baja:,}", anchor="w", font=("Segoe UI", 8, "italic"), fill="#475569")

        c.create_line(20, 80, w - 20, 80, fill="#e2e8f0")

        c.create_text(20, 95, text="BIENES ACTIVOS POR ESTADO DE CONSERVACIÓN", anchor="w", font=("Segoe UI", 9, "bold"), fill="#1e293b")

        color_map = {
            "BUENO": "#10b981",
            "REGULAR": "#f59e0b",
            "MALO": "#ef4444",
            "RAEE": "#f97316",
            "NUEVO": "#3b82f6",
            "CHATARRA": "#64748b",
            "SIN ESTADO": "#94a3b8"
        }

        start_y = 120
        row_height = 36
        max_bar_w = max(w - 210, 150)
        max_est_val = max([e[1] for e in estados], default=1) if estados else 1

        for idx, (est_nom, est_tot, est_inv, est_fal) in enumerate(estados):
            y = start_y + idx * row_height
            if y + row_height > h - 10:
                break

            color = color_map.get(est_nom.upper(), "#6366f1")
            c.create_text(20, y + 10, text=est_nom[:14], anchor="w", font=("Segoe UI", 8, "bold"), fill="#334155")

            b_len = int((est_tot / max_est_val) * max_bar_w) if max_est_val > 0 else 0
            b_len = max(b_len, 4)

            c.create_rectangle(130, y, 130 + b_len, y + 18, fill="#fee2e2", outline="#fca5a5")

            inv_ratio = (est_inv / est_tot) if est_tot > 0 else 0
            b_inv_len = int(b_len * inv_ratio)
            if b_inv_len > 0:
                c.create_rectangle(130, y, 130 + b_inv_len, y + 18, fill=color, outline="")

            c.create_text(
                135 + b_len, y + 9,
                text=f"{est_tot:,}  ({inv_ratio * 100:.0f}% inv)",
                anchor="w", font=("Segoe UI", 8), fill="#475569"
            )

    # ─────────────────────────────────────────────────────────────────────────
    # PESTAÑA 1: BIENES FALTANTES DETALLADO (¡NUEVA!)
    # Filtros por Usuario, Oficina, Área, Denominación, Cuenta Contable, etc.
    # ─────────────────────────────────────────────────────────────────────────
    def _construir_tab_faltantes(self, parent):
        # Panel Superior de Filtros Multicriterio (2 Filas compactas)
        f_filtros_padre = tk.Frame(parent, bg="#ffffff", bd=1, relief="solid")
        f_filtros_padre.pack(fill="x", padx=6, pady=(6, 2))

        # Fila 1 de Filtros
        f_row1 = tk.Frame(f_filtros_padre, bg="#ffffff")
        f_row1.pack(fill="x", padx=6, pady=(4, 2))

        tk.Label(f_row1, text="🔍 Buscar:", font=("Segoe UI", 8, "bold"), fg="#1e293b", bg="#ffffff").pack(side="left", padx=(4, 2))
        etr_s = ttk.Entry(f_row1, textvariable=self.var_search_faltantes, width=28)
        etr_s.pack(side="left", padx=(0, 8))
        etr_s.bind("<KeyRelease>", lambda _e: self._filtrar_tabla_faltantes())

        tk.Label(f_row1, text="Sede/Local:", font=("Segoe UI", 8, "bold"), fg="#475569", bg="#ffffff").pack(side="left", padx=(0, 2))
        self.cbx_fal_local = ttk.Combobox(f_row1, textvariable=self.var_fal_filtro_local, values=self.lista_fal_locales, state="readonly", width=22)
        self.cbx_fal_local.pack(side="left", padx=(0, 8))
        self.cbx_fal_local.bind("<<ComboboxSelected>>", self._on_fal_local_changed)

        tk.Label(f_row1, text="Área:", font=("Segoe UI", 8, "bold"), fg="#475569", bg="#ffffff").pack(side="left", padx=(0, 2))
        self.cbx_fal_area = ttk.Combobox(f_row1, textvariable=self.var_fal_filtro_area, values=self.lista_fal_areas, state="readonly", width=22)
        self.cbx_fal_area.pack(side="left", padx=(0, 8))
        self.cbx_fal_area.bind("<<ComboboxSelected>>", self._on_fal_area_changed)

        tk.Label(f_row1, text="Buscar Oficina:", font=("Segoe UI", 8, "bold"), fg="#475569", bg="#ffffff").pack(side="left", padx=(0, 2))
        box_buscar_ofi = tk.Frame(f_row1, bg="#ffffff")
        box_buscar_ofi.pack(side="left", padx=(0, 4))

        self.etrBuscarOficina = ttk.Entry(
            box_buscar_ofi,
            textvariable=self.var_fal_filtro_oficina,
            font=('Segoe UI', 9),
            width=26
        )
        self.etrBuscarOficina.pack(side="left", fill="x", expand=True, padx=(0, 2))
        self.etrBuscarOficina.bind(
            "<FocusIn>",
            lambda _e: self.etrBuscarOficina.after_idle(
                lambda: self.etrBuscarOficina.select_range(0, tk.END)
            )
        )

        self.btnDesplegarOfi = ttk.Button(
            box_buscar_ofi,
            text="▼",
            width=3,
            command=self._desplegar_todas_oficinas
        )
        self.btnDesplegarOfi.pack(side="left")

        # Compatibilidad de referencia
        self.cbx_fal_oficina = self.etrBuscarOficina

        # Vincular buscador predictivo
        self._vincular_busqueda_predictiva_oficina(self.etrBuscarOficina)

        # Fila 2 de Filtros
        f_row2 = tk.Frame(f_filtros_padre, bg="#ffffff")
        f_row2.pack(fill="x", padx=6, pady=(2, 4))

        tk.Label(f_row2, text="Cuenta Contable:", font=("Segoe UI", 8, "bold"), fg="#475569", bg="#ffffff").pack(side="left", padx=(4, 2))
        self.cbx_fal_cta = ttk.Combobox(f_row2, textvariable=self.var_fal_filtro_cta, values=self.lista_fal_cuentas, state="readonly", width=20)
        self.cbx_fal_cta.pack(side="left", padx=(0, 8))
        self.cbx_fal_cta.bind("<<ComboboxSelected>>", lambda _e: self._filtrar_tabla_faltantes())

        tk.Label(f_row2, text="Responsable / Usuario:", font=("Segoe UI", 8, "bold"), fg="#475569", bg="#ffffff").pack(side="left", padx=(0, 2))
        self.cbx_fal_resp = ttk.Combobox(f_row2, textvariable=self.var_fal_filtro_responsable, values=self.lista_fal_responsables, state="readonly", width=28)
        self.cbx_fal_resp.pack(side="left", padx=(0, 8))
        self.cbx_fal_resp.bind("<<ComboboxSelected>>", lambda _e: self._filtrar_tabla_faltantes())

        btn_limpiar = ttk.Button(f_row2, text="✕ Limpiar Filtros", command=self._limpiar_filtros_faltantes)
        btn_limpiar.pack(side="left", padx=4)

        btn_exp_fal = ttk.Button(f_row2, text="📥 Exportar Faltantes", command=self.exportar_pestana_activa)
        btn_exp_fal.pack(side="left", padx=4)

        self.lbl_resumen_faltantes = tk.Label(
            f_row2,
            text="",
            font=("Segoe UI", 8, "bold"),
            fg="#dc2626", bg="#ffffff"
        )
        self.lbl_resumen_faltantes.pack(side="right", padx=6)

        # Barra sutil con sugerencia de doble clic
        f_hint = tk.Frame(parent, bg="#f8fafc")
        f_hint.pack(fill="x", padx=8, pady=(0, 2))
        tk.Label(
            f_hint,
            text="💡 Tip: Haga doble clic sobre cualquier bien faltante para ver su ficha técnica / especificaciones completas.",
            font=("Segoe UI", 8, "italic"),
            fg="#64748b", bg="#f8fafc"
        ).pack(side="left")

        # Treeview de Faltantes Detallado
        f_tree = tk.Frame(parent, bg="#ffffff")
        f_tree.pack(fill="both", expand=True, padx=6, pady=(0, 6))

        cols = (
            "num", "codint", "codpat", "denominacion", "responsable",
            "local", "area", "oficina", "cta_cont", "estado_cons",
            "marca", "modelo", "serie", "val_adq"
        )
        self.tree_faltantes = ttk.Treeview(f_tree, columns=cols, show="headings", style="Stats.Treeview")

        self.tree_faltantes.heading("num", text="#")
        self.tree_faltantes.heading("codint", text="Cód. Int", command=lambda: sort_by(self.tree_faltantes, "codint", True))
        self.tree_faltantes.heading("codpat", text="Cód. Patrimonial", command=lambda: sort_by(self.tree_faltantes, "codpat", False))
        self.tree_faltantes.heading("denominacion", text="Denominación del Bien", command=lambda: sort_by(self.tree_faltantes, "denominacion", False))
        self.tree_faltantes.heading("responsable", text="Responsable / Usuario", command=lambda: sort_by(self.tree_faltantes, "responsable", False))
        self.tree_faltantes.heading("local", text="Sede / Local", command=lambda: sort_by(self.tree_faltantes, "local", False))
        self.tree_faltantes.heading("area", text="Área", command=lambda: sort_by(self.tree_faltantes, "area", False))
        self.tree_faltantes.heading("oficina", text="Oficina", command=lambda: sort_by(self.tree_faltantes, "oficina", False))
        self.tree_faltantes.heading("cta_cont", text="Cuenta", command=lambda: sort_by(self.tree_faltantes, "cta_cont", False))
        self.tree_faltantes.heading("estado_cons", text="Estado", command=lambda: sort_by(self.tree_faltantes, "estado_cons", False))
        self.tree_faltantes.heading("marca", text="Marca", command=lambda: sort_by(self.tree_faltantes, "marca", False))
        self.tree_faltantes.heading("modelo", text="Modelo", command=lambda: sort_by(self.tree_faltantes, "modelo", False))
        self.tree_faltantes.heading("serie", text="Serie", command=lambda: sort_by(self.tree_faltantes, "serie", False))
        self.tree_faltantes.heading("val_adq", text="Val. Adq. (S/)", command=lambda: sort_by(self.tree_faltantes, "val_adq", True))

        self.tree_faltantes.column("num", width=38, anchor="center")
        self.tree_faltantes.column("codint", width=75, anchor="center")
        self.tree_faltantes.column("codpat", width=115, anchor="center")
        self.tree_faltantes.column("denominacion", width=250, anchor="w")
        self.tree_faltantes.column("responsable", width=180, anchor="w")
        self.tree_faltantes.column("local", width=150, anchor="w")
        self.tree_faltantes.column("area", width=150, anchor="w")
        self.tree_faltantes.column("oficina", width=170, anchor="w")
        self.tree_faltantes.column("cta_cont", width=85, anchor="center")
        self.tree_faltantes.column("estado_cons", width=75, anchor="center")
        self.tree_faltantes.column("marca", width=85, anchor="w")
        self.tree_faltantes.column("modelo", width=85, anchor="w")
        self.tree_faltantes.column("serie", width=95, anchor="w")
        self.tree_faltantes.column("val_adq", width=105, anchor="e")

        scr_y = ttk.Scrollbar(f_tree, orient="vertical", command=self.tree_faltantes.yview)
        scr_x = ttk.Scrollbar(f_tree, orient="horizontal", command=self.tree_faltantes.xview)
        self.tree_faltantes.configure(yscrollcommand=scr_y.set, xscrollcommand=scr_x.set)

        self.tree_faltantes.grid(row=0, column=0, sticky="nsew")
        scr_y.grid(row=0, column=1, sticky="ns")
        scr_x.grid(row=1, column=0, sticky="ew")

        f_tree.columnconfigure(0, weight=1)
        f_tree.rowconfigure(0, weight=1)

        self.tree_faltantes.tag_configure("totales", font=("Segoe UI", 9, "bold"), background="#e2e8f0", foreground="#0f172a")
        self.tree_faltantes.tag_configure("par", background="#f8fafc")
        self.tree_faltantes.tag_configure("impar", background="#ffffff")

        # Doble clic para abrir ventana de detalles técnicos del bien
        self.tree_faltantes.bind("<Double-Button-1>", self._on_faltante_double_click)

    def _on_faltante_double_click(self, _event=None):
        item_id = self.tree_faltantes.focus()
        if not item_id:
            return
        vals = self.tree_faltantes.item(item_id, "values")
        if vals and len(vals) > 1:
            codint = str(vals[1]).strip()
            if codint and codint not in ("TOTAL", "#"):
                try:
                    Window_detalles(self, codigo=codint)
                except Exception as e:
                    print(f"[ESTADISTICAS][WARN] Error abriendo detalles para '{codint}': {e}")


    # ─────────────────────────────────────────────────────────────────────────
    # BÚSQUEDA PREDICTIVA DINÁMICA DE OFICINAS (FALTANTES)
    # ─────────────────────────────────────────────────────────────────────────
    def _vincular_busqueda_predictiva_oficina(self, entry_widget):
        entry_widget.bind("<KeyRelease>", lambda e, w=entry_widget: self._on_keyrelease_oficina(e, w))
        entry_widget.bind("<Down>", lambda e, w=entry_widget: self._navegar_popup_oficina(1, w))
        entry_widget.bind("<Up>", lambda e, w=entry_widget: self._navegar_popup_oficina(-1, w))
        entry_widget.bind("<Next>", lambda e, w=entry_widget: self._navegar_popup_oficina(5, w))
        entry_widget.bind("<Prior>", lambda e, w=entry_widget: self._navegar_popup_oficina(-5, w))
        entry_widget.bind("<Return>", lambda e, w=entry_widget: self._confirmar_oficina_predictiva(w))
        entry_widget.bind("<Escape>", lambda _e: self._cerrar_popup_oficinas())
        entry_widget.bind("<FocusOut>", lambda _e: self.after(180, self._verificar_foco_popup_oficinas))

    def _formatear_item_oficina_predictiva(self, fila):
        acta, local, area, oficina, _dni, full_name, n_fal = fila
        ofi_txt = oficina or "(Sin nombre de oficina)"
        detalles = []
        if area and area != "SIN AREA":
            detalles.append(area)
        if local and local != "SIN LOCAL" and local != area:
            detalles.append(local)
        ubic_txt = f" — {' / '.join(detalles)}" if detalles else ""
        resp_txt = f"  |  👤 {full_name}" if full_name and full_name != "SIN ASIGNAR" else ""
        if n_fal > 0:
            badge = f" [⚠️ {n_fal} faltantes]"
        else:
            badge = " [✓ 0 faltantes]" if not acta else f" [Ficha {acta}]"
        return f"🏢 {ofi_txt}{badge}{ubic_txt}{resp_txt}"

    def _buscar_oficinas_predictivo_faltantes(self, termino="", limite=40):
        """Busca oficinas dinámicamente con coincidencia insensible y ordenando por relevancia."""
        import unicodedata

        def _norm(texto):
            if not texto:
                return ""
            s = str(texto).strip().lower()
            return "".join(
                c for c in unicodedata.normalize("NFD", s)
                if unicodedata.category(c) != "Mn"
            )

        loc_sel = self.var_fal_filtro_local.get()
        area_sel = self.var_fal_filtro_area.get()

        conteo_faltantes = {}
        ofi_info = {}
        for r in self.raw_faltantes:
            resp = str(r[3] or "")
            loc = str(r[4] or "")
            area = str(r[5] or "")
            ofi = str(r[6] or "").strip()
            if not ofi or ofi == "SIN OFICINA":
                continue

            if loc_sel != "[ TODOS ]" and loc != loc_sel:
                continue
            if area_sel != "[ TODAS ]" and area != area_sel:
                continue

            conteo_faltantes[ofi] = conteo_faltantes.get(ofi, 0) + 1
            if ofi not in ofi_info:
                ofi_info[ofi] = (loc, area, resp)

        q = _norm(termino)
        tokens = [t for t in q.split() if t]

        try:
            from db.query import buscar_oficinas_predictivo
            ofis_db = buscar_oficinas_predictivo(termino, limite=limite * 2)
        except Exception:
            ofis_db = []

        resultados_dict = {}

        # 1. Oficinas con bienes faltantes en el contexto actual
        for ofi, count in conteo_faltantes.items():
            loc, area, resp = ofi_info[ofi]
            ofi_norm = _norm(ofi)
            loc_norm = _norm(loc)
            area_norm = _norm(area)
            resp_norm = _norm(resp)
            txt_completo = f"{ofi_norm} {loc_norm} {area_norm} {resp_norm}"

            if tokens:
                en_ofi = all(t in ofi_norm for t in tokens)
                en_comp = all(t in txt_completo for t in tokens)
                if not en_ofi and not en_comp:
                    continue

                if ofi_norm == q:
                    rango = 0
                elif ofi_norm.startswith(q):
                    rango = 1
                elif any(p.startswith(tokens[0]) for p in ofi_norm.split()) and en_ofi:
                    rango = 2
                elif en_ofi:
                    rango = 3
                else:
                    rango = 4
            else:
                rango = 0

            prio = (0, rango, -count, ofi_norm)
            fila = ("", loc, area, ofi, "", resp, count)
            resultados_dict[ofi] = (prio, fila)

        # 2. Oficinas generales de la base de datos (conteo 0)
        for fila in ofis_db:
            acta, loc, area, ofi, dni, full_name = fila[:6]
            ofi = (ofi or "").strip()
            if not ofi or ofi in resultados_dict:
                continue
            if loc_sel != "[ TODOS ]" and loc != loc_sel:
                continue
            if area_sel != "[ TODAS ]" and area != area_sel:
                continue

            ofi_norm = _norm(ofi)
            fila_con_conteo = (acta, loc, area, ofi, dni, full_name, 0)
            prio = (1, 5, 0, ofi_norm)
            resultados_dict[ofi] = (prio, fila_con_conteo)

        lista = sorted(resultados_dict.values(), key=lambda x: x[0])
        if limite and limite > 0:
            lista = lista[:limite]
        return [item[1] for item in lista]

    def _on_keyrelease_oficina(self, event, entry_widget):
        teclas_ignorar = {
            "Up", "Down", "Left", "Right", "Return", "Escape", "Tab",
            "Shift_L", "Shift_R", "Control_L", "Control_R", "Alt_L", "Alt_R",
            "Caps_Lock", "Prior", "Next", "Home", "End"
        }
        if event.keysym in teclas_ignorar:
            return

        # Filtra la tabla dinámicamente en tiempo real mientras el usuario tipea
        self._filtrar_tabla_faltantes()

        termino = entry_widget.get().strip()
        if not termino or termino in ("[ TODAS ]", "[ TODOS ]"):
            self._cerrar_popup_oficinas()
            return

        resultados = self._buscar_oficinas_predictivo_faltantes(termino, limite=35)
        self._mostrar_popup_oficinas(entry_widget, resultados, termino)

    def _desplegar_todas_oficinas(self, entry_widget=None):
        target = entry_widget or self.etrBuscarOficina
        if self._popup_oficinas is not None and self._popup_oficinas.winfo_exists():
            self._cerrar_popup_oficinas()
            return

        termino = target.get().strip()
        if termino in ("[ TODAS ]", "[ TODOS ]"):
            termino = ""

        resultados = self._buscar_oficinas_predictivo_faltantes(termino, limite=50)
        target.focus_set()
        self._mostrar_popup_oficinas(target, resultados, termino)

    def _mostrar_popup_oficinas(self, entry_widget, resultados, termino=""):
        self._resultados_oficinas_actuales = list(resultados)
        self._entry_activo_oficina = entry_widget

        if self._popup_oficinas is None or not self._popup_oficinas.winfo_exists():
            popup = tk.Toplevel(self)
            popup.wm_overrideredirect(True)
            popup.transient(self)
            popup.configure(bg="#2563eb")

            contenedor = tk.Frame(popup, bg="#ffffff", bd=0)
            contenedor.pack(fill="both", expand=True, padx=1, pady=1)

            header = tk.Frame(contenedor, bg="#eff6ff", padx=8, pady=4)
            header.pack(fill="x")

            self._lbl_popup_info = tk.Label(
                header,
                text="",
                bg="#eff6ff",
                fg="#1e40af",
                font=("Segoe UI", 8, "bold"),
                anchor="w"
            )
            self._lbl_popup_info.pack(side="left", fill="x", expand=True)

            lbl_cerrar = tk.Label(
                header,
                text="✕",
                bg="#eff6ff",
                fg="#64748b",
                font=("Segoe UI", 8, "bold"),
                cursor="hand2",
                padx=4
            )
            lbl_cerrar.pack(side="right")
            lbl_cerrar.bind("<Button-1>", lambda _e: self._cerrar_popup_oficinas())

            body = tk.Frame(contenedor, bg="#ffffff")
            body.pack(fill="both", expand=True)

            scrollbar = ttk.Scrollbar(body, orient=tk.VERTICAL)
            listbox = tk.Listbox(
                body,
                font=("Segoe UI", 9),
                bg="#ffffff",
                fg="#0f172a",
                selectbackground="#2563eb",
                selectforeground="#ffffff",
                activestyle="none",
                highlightthickness=0,
                bd=0,
                yscrollcommand=scrollbar.set,
                cursor="hand2"
            )
            scrollbar.config(command=listbox.yview)
            listbox.pack(side="left", fill="both", expand=True, padx=(4, 0), pady=2)
            scrollbar.pack(side="right", fill="y", pady=2)

            listbox.bind("<ButtonRelease-1>", self._seleccionar_item_popup_oficina)
            listbox.bind("<Return>", self._seleccionar_item_popup_oficina)
            listbox.bind("<Escape>", lambda _e: self._cerrar_popup_oficinas())
            listbox.bind("<Motion>", self._on_hover_popup_oficina)

            self._popup_oficinas = popup
            self._listbox_oficinas = listbox

        listbox = self._listbox_oficinas
        listbox.delete(0, tk.END)

        if not resultados:
            self._lbl_popup_info.config(
                text=f"⚠️ Sin coincidencias para '{termino}'",
                fg="#b91c1c"
            )
            listbox.insert(tk.END, "  No se encontraron oficinas que coincidan con la búsqueda.")
            listbox.config(height=2, fg="#64748b")
        else:
            n = len(resultados)
            primera = resultados[0]
            cnt_fal = primera[6] if len(primera) > 6 else 0
            txt_extra = f" [{cnt_fal} faltantes]" if cnt_fal > 0 else ""
            self._lbl_popup_info.config(
                text=f"✨ {n} {'oficina' if n == 1 else 'oficinas'} — ↑↓ navegar | Enter o clic: seleccionar{txt_extra}",
                fg="#1e40af"
            )
            listbox.config(fg="#0f172a")
            for fila in resultados:
                listbox.insert(tk.END, self._formatear_item_oficina_predictiva(fila))
            listbox.config(height=min(max(n, 2), 9))
            listbox.selection_clear(0, tk.END)
            listbox.selection_set(0)
            listbox.activate(0)

        self._posicionar_popup_oficinas(entry_widget)

    def _posicionar_popup_oficinas(self, entry_widget):
        if self._popup_oficinas is None or not self._popup_oficinas.winfo_exists():
            return
        try:
            self.update_idletasks()
            x = entry_widget.winfo_rootx()
            y = entry_widget.winfo_rooty() + entry_widget.winfo_height() + 2
            ancho = max(entry_widget.winfo_width() + 180, 520)
            sw = self.winfo_screenwidth()
            if x + ancho > sw - 12:
                x = max(8, sw - ancho - 12)
            self._popup_oficinas.geometry(f"{ancho}x{self._popup_oficinas.winfo_reqheight()}+{x}+{y}")
            self._popup_oficinas.lift()
        except Exception:
            pass

    def _on_hover_popup_oficina(self, event):
        if not self._resultados_oficinas_actuales or self._listbox_oficinas is None:
            return
        idx = self._listbox_oficinas.nearest(event.y)
        if 0 <= idx < len(self._resultados_oficinas_actuales):
            self._listbox_oficinas.selection_clear(0, tk.END)
            self._listbox_oficinas.selection_set(idx)
            self._listbox_oficinas.activate(idx)
            fila = self._resultados_oficinas_actuales[idx]
            ofi = fila[3] or fila[2]
            cnt = fila[6] if len(fila) > 6 else 0
            cnt_txt = f" ({cnt} faltantes)" if cnt > 0 else ""
            if self._lbl_popup_info is not None:
                self._lbl_popup_info.config(
                    text=f"✨ Seleccionar: {ofi}{cnt_txt} — Enter o clic para aplicar"
                )

    def _navegar_popup_oficina(self, delta, entry_widget):
        if self._popup_oficinas is None or not self._popup_oficinas.winfo_exists():
            self._desplegar_todas_oficinas(entry_widget)
            return "break"

        if not self._resultados_oficinas_actuales or self._listbox_oficinas is None:
            return "break"

        sel = self._listbox_oficinas.curselection()
        actual = int(sel[0]) if sel else 0
        nuevo = max(0, min(len(self._resultados_oficinas_actuales) - 1, actual + delta))
        self._listbox_oficinas.selection_clear(0, tk.END)
        self._listbox_oficinas.selection_set(nuevo)
        self._listbox_oficinas.activate(nuevo)
        self._listbox_oficinas.see(nuevo)

        fila = self._resultados_oficinas_actuales[nuevo]
        ofi = fila[3] or fila[2]
        cnt = fila[6] if len(fila) > 6 else 0
        cnt_txt = f" ({cnt} faltantes)" if cnt > 0 else ""
        if self._lbl_popup_info is not None:
            self._lbl_popup_info.config(
                text=f"✨ Seleccionar: {ofi}{cnt_txt} — Presione Enter para aplicar"
            )
        return "break"

    def _seleccionar_item_popup_oficina(self, _event=None):
        if not self._resultados_oficinas_actuales or self._listbox_oficinas is None:
            self._cerrar_popup_oficinas()
            return "break"

        sel = self._listbox_oficinas.curselection()
        idx = int(sel[0]) if sel else 0
        if 0 <= idx < len(self._resultados_oficinas_actuales):
            fila = self._resultados_oficinas_actuales[idx]
            self._aplicar_oficina_seleccionada(fila)
        return "break"

    def _confirmar_oficina_predictiva(self, entry_widget=None):
        target = entry_widget or self.etrBuscarOficina
        if (
            self._popup_oficinas is not None
            and self._popup_oficinas.winfo_exists()
            and self._resultados_oficinas_actuales
        ):
            return self._seleccionar_item_popup_oficina()

        termino = target.get().strip()
        if not termino or termino in ("[ TODAS ]", "[ TODOS ]"):
            return "break"

        resultados = self._buscar_oficinas_predictivo_faltantes(termino, limite=35)
        if not resultados:
            mb.showinfo(
                title="Búsqueda de Oficina",
                message=f"No se encontró ninguna oficina que coincida con '{termino}'."
            )
            return "break"

        if len(resultados) == 1:
            self._aplicar_oficina_seleccionada(resultados[0])
        else:
            self._mostrar_popup_oficinas(target, resultados, termino)
        return "break"

    def _aplicar_oficina_seleccionada(self, fila_oficina):
        acta, local, area, oficina, _dni, full_name, _count = fila_oficina
        self._cerrar_popup_oficinas()
        self.var_fal_filtro_oficina.set(oficina or "")

        # Sincronización inteligente de Local y Área si están en [ TODOS ]
        if local and local != "SIN LOCAL" and self.var_fal_filtro_local.get() == "[ TODOS ]":
            if local in self.lista_fal_locales:
                self.var_fal_filtro_local.set(local)
                areas = ["[ TODAS ]"] + sorted(list(set(r[5] for r in self.raw_faltantes if r[4] == local and r[5] and r[5] != "SIN AREA")))
                self.lista_fal_areas = areas
                self.cbx_fal_area.config(values=self.lista_fal_areas)

        if area and area != "SIN AREA" and self.var_fal_filtro_area.get() == "[ TODAS ]":
            if area in self.lista_fal_areas:
                self.var_fal_filtro_area.set(area)

        self._filtrar_tabla_faltantes()
        self.etrBuscarOficina.focus_set()

    def _verificar_foco_popup_oficinas(self):
        if self._popup_oficinas is None or not self._popup_oficinas.winfo_exists():
            return
        try:
            foco = self.focus_get()
            if foco in (self.etrBuscarOficina, self._listbox_oficinas, self.btnDesplegarOfi):
                return
        except Exception:
            pass
        self._cerrar_popup_oficinas()

    def _cerrar_popup_oficinas(self, _event=None):
        if self._popup_oficinas is not None:
            try:
                if self._popup_oficinas.winfo_exists():
                    self._popup_oficinas.destroy()
            except Exception:
                pass
        self._popup_oficinas = None
        self._listbox_oficinas = None
        self._lbl_popup_info = None
        self._resultados_oficinas_actuales = []

    def _on_fal_local_changed(self, _event=None, actualizar_oficina=True):
        self._cerrar_popup_oficinas()
        loc_sel = self.var_fal_filtro_local.get()
        if loc_sel == "[ TODOS ]":
            areas = ["[ TODAS ]"] + sorted(list(set(r[5] for r in self.raw_faltantes if r[5] and r[5] != "SIN AREA")))
        else:
            areas = ["[ TODAS ]"] + sorted(list(set(r[5] for r in self.raw_faltantes if r[4] == loc_sel and r[5] and r[5] != "SIN AREA")))
        self.lista_fal_areas = areas
        self.cbx_fal_area.config(values=self.lista_fal_areas)
        self.var_fal_filtro_area.set("[ TODAS ]")
        if actualizar_oficina:
            self.var_fal_filtro_oficina.set("")
        self._filtrar_tabla_faltantes()

    def _on_fal_area_changed(self, _event=None, actualizar_oficina=True):
        self._cerrar_popup_oficinas()
        if actualizar_oficina:
            self.var_fal_filtro_oficina.set("")
        self._filtrar_tabla_faltantes()

    def _limpiar_filtros_faltantes(self):
        self._cerrar_popup_oficinas()
        self.var_search_faltantes.set("")
        self.var_fal_filtro_local.set("[ TODOS ]")
        self.var_fal_filtro_area.set("[ TODAS ]")
        self.var_fal_filtro_oficina.set("")
        self.var_fal_filtro_cta.set("[ TODAS ]")
        self.var_fal_filtro_responsable.set("[ TODOS ]")
        # Restablecer áreas
        self.lista_fal_areas = ["[ TODAS ]"] + sorted(list(set(r[5] for r in self.raw_faltantes if r[5] and r[5] != "SIN AREA")))
        self.cbx_fal_area.config(values=self.lista_fal_areas)
        self._filtrar_tabla_faltantes()

    def _filtrar_tabla_faltantes(self):
        """Filtra en memoria los bienes faltantes por texto, local, área, oficina, cuenta y responsable."""
        for item in self.tree_faltantes.get_children():
            self.tree_faltantes.delete(item)

        search = self.var_search_faltantes.get().strip().upper()
        f_loc = self.var_fal_filtro_local.get()
        f_area = self.var_fal_filtro_area.get()
        f_ofi = self.var_fal_filtro_oficina.get()
        f_cta = self.var_fal_filtro_cta.get()
        f_resp = self.var_fal_filtro_responsable.get()

        count = 0
        sum_val = 0.0

        for r in self.raw_faltantes:
            codint = str(r[0] or "")
            codpat = str(r[1] or "")
            deno = str(r[2] or "")
            resp = str(r[3] or "")
            loc = str(r[4] or "")
            area = str(r[5] or "")
            ofi = str(r[6] or "")
            cta = str(r[7] or "")
            est = str(r[8] or "")
            marca = str(r[9] or "")
            modelo = str(r[10] or "")
            serie = str(r[11] or "")
            val = float(r[12] or 0.0)

            # Filtros por desplegables
            if f_loc != "[ TODOS ]" and loc != f_loc:
                continue
            if f_area != "[ TODAS ]" and area != f_area:
                continue
            # Filtro por oficina (búsqueda predictiva dinámica o coincidencia)
            if f_ofi and f_ofi not in ("[ TODAS ]", "[ TODOS ]"):
                ofi_up = ofi.upper()
                f_ofi_up = f_ofi.upper()
                if ofi_up != f_ofi_up and f_ofi_up not in ofi_up:
                    continue
            if f_cta != "[ TODAS ]" and cta != f_cta:
                continue
            if f_resp != "[ TODOS ]" and resp != f_resp:
                continue

            # Búsqueda por texto (multicampo)
            if search:
                coincide = (
                    search in codint.upper() or
                    search in codpat.upper() or
                    search in deno.upper() or
                    search in resp.upper() or
                    search in loc.upper() or
                    search in area.upper() or
                    search in ofi.upper() or
                    search in cta.upper() or
                    search in marca.upper() or
                    search in modelo.upper() or
                    search in serie.upper()
                )
                if not coincide:
                    continue

            count += 1
            sum_val += val
            tag = "par" if count % 2 == 0 else "impar"
            self.tree_faltantes.insert(
                "", "end",
                values=(
                    count, codint, codpat, deno, resp,
                    loc, area, ofi, cta, est,
                    marca, modelo, serie, f"{val:,.2f}"
                ),
                tags=(tag,)
            )

        # Fila fija de TOTALES
        tot_general_faltantes = len(self.raw_faltantes)
        self.tree_faltantes.insert(
            "", "end",
            values=("TOTAL", f"{count} FALTANTES", "", "TOTAL BIENES FALTANTES LISTADOS", "", "", "", "", "", "", "", "", "", f"{sum_val:,.2f}"),
            tags=("totales",)
        )

        self.lbl_resumen_faltantes.config(
            text=f"Mostrando {count:,} de {tot_general_faltantes:,} faltantes | Valor: S/ {sum_val:,.2f}"
        )

    # ─────────────────────────────────────────────────────────────────────────
    # PESTAÑA 2: AVANCE POR SEDE / LOCAL
    # ─────────────────────────────────────────────────────────────────────────
    def _construir_tab_locales(self, parent):
        f_bar = tk.Frame(parent, bg="#ffffff", bd=1, relief="solid")
        f_bar.pack(fill="x", padx=6, pady=(6, 2))

        tk.Label(f_bar, text="🔍 Buscar Local / Sede:", font=("Segoe UI", 9, "bold"), fg="#475569", bg="#ffffff").pack(side="left", padx=(8, 4), pady=6)
        etr_s = ttk.Entry(f_bar, textvariable=self.var_search_locales, width=32)
        etr_s.pack(side="left", padx=4, pady=6)
        etr_s.bind("<KeyRelease>", lambda _e: self._filtrar_tabla_locales())

        btn_clr = ttk.Button(f_bar, text="✕ Limpiar", command=lambda: (self.var_search_locales.set(""), self._filtrar_tabla_locales()))
        btn_clr.pack(side="left", padx=4)

        self.lbl_count_loc = tk.Label(f_bar, text="", font=("Segoe UI", 9, "italic"), fg="#64748b", bg="#ffffff")
        self.lbl_count_loc.pack(side="right", padx=10)

        f_tree = tk.Frame(parent, bg="#ffffff")
        f_tree.pack(fill="both", expand=True, padx=6, pady=(2, 6))

        cols = ("num", "sede", "total", "inv", "fal", "avance", "estado")
        self.tree_locales = ttk.Treeview(f_tree, columns=cols, show="headings", style="Stats.Treeview")

        self.tree_locales.heading("num", text="#")
        self.tree_locales.heading("sede", text="Sede / Local", command=lambda: sort_by(self.tree_locales, "sede", False))
        self.tree_locales.heading("total", text="Total Activos (Alta)", command=lambda: sort_by(self.tree_locales, "total", True))
        self.tree_locales.heading("inv", text="Inventariados", command=lambda: sort_by(self.tree_locales, "inv", True))
        self.tree_locales.heading("fal", text="Faltantes", command=lambda: sort_by(self.tree_locales, "fal", True))
        self.tree_locales.heading("avance", text="% Avance", command=lambda: sort_by(self.tree_locales, "avance", True))
        self.tree_locales.heading("estado", text="Estado")

        self.tree_locales.column("num", width=40, anchor="center")
        self.tree_locales.column("sede", width=360, anchor="w")
        self.tree_locales.column("total", width=110, anchor="e")
        self.tree_locales.column("inv", width=105, anchor="e")
        self.tree_locales.column("fal", width=95, anchor="e")
        self.tree_locales.column("avance", width=85, anchor="center")
        self.tree_locales.column("estado", width=120, anchor="center")

        scr_y = ttk.Scrollbar(f_tree, orient="vertical", command=self.tree_locales.yview)
        scr_x = ttk.Scrollbar(f_tree, orient="horizontal", command=self.tree_locales.xview)
        self.tree_locales.configure(yscrollcommand=scr_y.set, xscrollcommand=scr_x.set)

        self.tree_locales.grid(row=0, column=0, sticky="nsew")
        scr_y.grid(row=0, column=1, sticky="ns")
        scr_x.grid(row=1, column=0, sticky="ew")

        f_tree.columnconfigure(0, weight=1)
        f_tree.rowconfigure(0, weight=1)

        self.tree_locales.tag_configure("completa", background="#dcfce7", foreground="#166534")
        self.tree_locales.tag_configure("alta", background="#ecfdf5", foreground="#065f46")
        self.tree_locales.tag_configure("media", background="#fef9c3", foreground="#854d0e")
        self.tree_locales.tag_configure("baja", background="#fee2e2", foreground="#991b1b")
        self.tree_locales.tag_configure("totales", font=("Segoe UI", 9, "bold"), background="#e2e8f0", foreground="#0f172a")

    # ─────────────────────────────────────────────────────────────────────────
    # PESTAÑA 3: POR CUENTA CONTABLE
    # ─────────────────────────────────────────────────────────────────────────
    def _construir_tab_cuentas(self, parent):
        f_bar = tk.Frame(parent, bg="#ffffff", bd=1, relief="solid")
        f_bar.pack(fill="x", padx=6, pady=(6, 2))

        tk.Label(f_bar, text="🔍 Buscar Cuenta:", font=("Segoe UI", 9, "bold"), fg="#475569", bg="#ffffff").pack(side="left", padx=(8, 4), pady=6)
        etr_s = ttk.Entry(f_bar, textvariable=self.var_search_cuentas, width=32)
        etr_s.pack(side="left", padx=4, pady=6)
        etr_s.bind("<KeyRelease>", lambda _e: self._filtrar_tabla_cuentas())

        btn_clr = ttk.Button(f_bar, text="✕ Limpiar", command=lambda: (self.var_search_cuentas.set(""), self._filtrar_tabla_cuentas()))
        btn_clr.pack(side="left", padx=4)

        self.lbl_count_cta = tk.Label(f_bar, text="", font=("Segoe UI", 9, "italic"), fg="#64748b", bg="#ffffff")
        self.lbl_count_cta.pack(side="right", padx=10)

        f_tree = tk.Frame(parent, bg="#ffffff")
        f_tree.pack(fill="both", expand=True, padx=6, pady=(2, 6))

        cols = ("cuenta", "denominacion", "total", "inv", "fal", "avance", "val_adq", "val_neto")
        self.tree_cuentas = ttk.Treeview(f_tree, columns=cols, show="headings", style="Stats.Treeview")

        self.tree_cuentas.heading("cuenta", text="Cuenta", command=lambda: sort_by(self.tree_cuentas, "cuenta", False))
        self.tree_cuentas.heading("denominacion", text="Denominación de la Cuenta", command=lambda: sort_by(self.tree_cuentas, "denominacion", False))
        self.tree_cuentas.heading("total", text="Total Activos (Alta)", command=lambda: sort_by(self.tree_cuentas, "total", True))
        self.tree_cuentas.heading("inv", text="Inventariados", command=lambda: sort_by(self.tree_cuentas, "inv", True))
        self.tree_cuentas.heading("fal", text="Faltantes", command=lambda: sort_by(self.tree_cuentas, "fal", True))
        self.tree_cuentas.heading("avance", text="% Avance", command=lambda: sort_by(self.tree_cuentas, "avance", True))
        self.tree_cuentas.heading("val_adq", text="Val. Adquisición (S/)", command=lambda: sort_by(self.tree_cuentas, "val_adq", True))
        self.tree_cuentas.heading("val_neto", text="Val. Neto (S/)", command=lambda: sort_by(self.tree_cuentas, "val_neto", True))

        self.tree_cuentas.column("cuenta", width=95, anchor="center")
        self.tree_cuentas.column("denominacion", width=340, anchor="w")
        self.tree_cuentas.column("total", width=110, anchor="e")
        self.tree_cuentas.column("inv", width=95, anchor="e")
        self.tree_cuentas.column("fal", width=85, anchor="e")
        self.tree_cuentas.column("avance", width=80, anchor="center")
        self.tree_cuentas.column("val_adq", width=125, anchor="e")
        self.tree_cuentas.column("val_neto", width=120, anchor="e")

        scr_y = ttk.Scrollbar(f_tree, orient="vertical", command=self.tree_cuentas.yview)
        scr_x = ttk.Scrollbar(f_tree, orient="horizontal", command=self.tree_cuentas.xview)
        self.tree_cuentas.configure(yscrollcommand=scr_y.set, xscrollcommand=scr_x.set)

        self.tree_cuentas.grid(row=0, column=0, sticky="nsew")
        scr_y.grid(row=0, column=1, sticky="ns")
        scr_x.grid(row=1, column=0, sticky="ew")

        f_tree.columnconfigure(0, weight=1)
        f_tree.rowconfigure(0, weight=1)

        self.tree_cuentas.tag_configure("totales", font=("Segoe UI", 9, "bold"), background="#e2e8f0", foreground="#0f172a")
        self.tree_cuentas.tag_configure("par", background="#f8fafc")
        self.tree_cuentas.tag_configure("impar", background="#ffffff")

    # ─────────────────────────────────────────────────────────────────────────
    # PESTAÑA 4: RENDIMIENTO POR INVENTARIADOR / EQUIPO
    # ─────────────────────────────────────────────────────────────────────────
    def _construir_tab_personal(self, parent):
        f_bar = tk.Frame(parent, bg="#ffffff", bd=1, relief="solid")
        f_bar.pack(fill="x", padx=6, pady=(6, 2))

        tk.Label(f_bar, text="🔍 Buscar Inventariador / Equipo:", font=("Segoe UI", 9, "bold"), fg="#475569", bg="#ffffff").pack(side="left", padx=(8, 4), pady=6)
        etr_s = ttk.Entry(f_bar, textvariable=self.var_search_personal, width=32)
        etr_s.pack(side="left", padx=4, pady=6)
        etr_s.bind("<KeyRelease>", lambda _e: self._filtrar_tabla_personal())

        btn_clr = ttk.Button(f_bar, text="✕ Limpiar", command=lambda: (self.var_search_personal.set(""), self._filtrar_tabla_personal()))
        btn_clr.pack(side="left", padx=4)

        self.lbl_count_per = tk.Label(f_bar, text="", font=("Segoe UI", 9, "italic"), fg="#64748b", bg="#ffffff")
        self.lbl_count_per.pack(side="right", padx=10)

        f_tree = tk.Frame(parent, bg="#ffffff")
        f_tree.pack(fill="both", expand=True, padx=6, pady=(2, 6))

        cols = ("num", "inventariador", "equipo", "bienes_inv", "pct_aporte", "primer_reg", "ultimo_reg")
        self.tree_personal = ttk.Treeview(f_tree, columns=cols, show="headings", style="Stats.Treeview")

        self.tree_personal.heading("num", text="#")
        self.tree_personal.heading("inventariador", text="Inventariador / Usuario", command=lambda: sort_by(self.tree_personal, "inventariador", False))
        self.tree_personal.heading("equipo", text="Equipo de Inventario", command=lambda: sort_by(self.tree_personal, "equipo", False))
        self.tree_personal.heading("bienes_inv", text="Bienes Inventariados", command=lambda: sort_by(self.tree_personal, "bienes_inv", True))
        self.tree_personal.heading("pct_aporte", text="% de Aporte", command=lambda: sort_by(self.tree_personal, "pct_aporte", True))
        self.tree_personal.heading("primer_reg", text="Primer Registro")
        self.tree_personal.heading("ultimo_reg", text="Último Registro")

        self.tree_personal.column("num", width=40, anchor="center")
        self.tree_personal.column("inventariador", width=300, anchor="w")
        self.tree_personal.column("equipo", width=160, anchor="center")
        self.tree_personal.column("bienes_inv", width=140, anchor="e")
        self.tree_personal.column("pct_aporte", width=100, anchor="center")
        self.tree_personal.column("primer_reg", width=140, anchor="center")
        self.tree_personal.column("ultimo_reg", width=140, anchor="center")

        scr_y = ttk.Scrollbar(f_tree, orient="vertical", command=self.tree_personal.yview)
        scr_x = ttk.Scrollbar(f_tree, orient="horizontal", command=self.tree_personal.xview)
        self.tree_personal.configure(yscrollcommand=scr_y.set, xscrollcommand=scr_x.set)

        self.tree_personal.grid(row=0, column=0, sticky="nsew")
        scr_y.grid(row=0, column=1, sticky="ns")
        scr_x.grid(row=1, column=0, sticky="ew")

        f_tree.columnconfigure(0, weight=1)
        f_tree.rowconfigure(0, weight=1)

        self.tree_personal.tag_configure("totales", font=("Segoe UI", 9, "bold"), background="#e2e8f0", foreground="#0f172a")
        self.tree_personal.tag_configure("par", background="#f8fafc")
        self.tree_personal.tag_configure("impar", background="#ffffff")

    # ─────────────────────────────────────────────────────────────────────────
    # PESTAÑA 5: TOP TIPOS DE BIEN (DENOMINACIONES)
    # ─────────────────────────────────────────────────────────────────────────
    def _construir_tab_denos(self, parent):
        f_bar = tk.Frame(parent, bg="#ffffff", bd=1, relief="solid")
        f_bar.pack(fill="x", padx=6, pady=(6, 2))

        tk.Label(f_bar, text="🔍 Buscar Denominación:", font=("Segoe UI", 9, "bold"), fg="#475569", bg="#ffffff").pack(side="left", padx=(8, 4), pady=6)
        etr_s = ttk.Entry(f_bar, textvariable=self.var_search_denos, width=32)
        etr_s.pack(side="left", padx=4, pady=6)
        etr_s.bind("<KeyRelease>", lambda _e: self._filtrar_tabla_denos())

        btn_clr = ttk.Button(f_bar, text="✕ Limpiar", command=lambda: (self.var_search_denos.set(""), self._filtrar_tabla_denos()))
        btn_clr.pack(side="left", padx=4)

        self.lbl_count_deno = tk.Label(f_bar, text="", font=("Segoe UI", 9, "italic"), fg="#64748b", bg="#ffffff")
        self.lbl_count_deno.pack(side="right", padx=10)

        f_tree = tk.Frame(parent, bg="#ffffff")
        f_tree.pack(fill="both", expand=True, padx=6, pady=(2, 6))

        cols = ("num", "denominacion", "total", "inv", "fal", "avance")
        self.tree_denos = ttk.Treeview(f_tree, columns=cols, show="headings", style="Stats.Treeview")

        self.tree_denos.heading("num", text="#")
        self.tree_denos.heading("denominacion", text="Denominación del Bien", command=lambda: sort_by(self.tree_denos, "denominacion", False))
        self.tree_denos.heading("total", text="Total Activos (Alta)", command=lambda: sort_by(self.tree_denos, "total", True))
        self.tree_denos.heading("inv", text="Inventariados", command=lambda: sort_by(self.tree_denos, "inv", True))
        self.tree_denos.heading("fal", text="Faltantes", command=lambda: sort_by(self.tree_denos, "fal", True))
        self.tree_denos.heading("avance", text="% Avance", command=lambda: sort_by(self.tree_denos, "avance", True))

        self.tree_denos.column("num", width=40, anchor="center")
        self.tree_denos.column("denominacion", width=460, anchor="w")
        self.tree_denos.column("total", width=120, anchor="e")
        self.tree_denos.column("inv", width=120, anchor="e")
        self.tree_denos.column("fal", width=110, anchor="e")
        self.tree_denos.column("avance", width=100, anchor="center")

        scr_y = ttk.Scrollbar(f_tree, orient="vertical", command=self.tree_denos.yview)
        scr_x = ttk.Scrollbar(f_tree, orient="horizontal", command=self.tree_denos.xview)
        self.tree_denos.configure(yscrollcommand=scr_y.set, xscrollcommand=scr_x.set)

        self.tree_denos.grid(row=0, column=0, sticky="nsew")
        scr_y.grid(row=0, column=1, sticky="ns")
        scr_x.grid(row=1, column=0, sticky="ew")

        f_tree.columnconfigure(0, weight=1)
        f_tree.rowconfigure(0, weight=1)

        self.tree_denos.tag_configure("totales", font=("Segoe UI", 9, "bold"), background="#e2e8f0", foreground="#0f172a")
        self.tree_denos.tag_configure("par", background="#f8fafc")
        self.tree_denos.tag_configure("impar", background="#ffffff")

    # ─────────────────────────────────────────────────────────────────────────
    # PESTAÑA 6: BIENES DE BAJA (INFORMATIVO)
    # ─────────────────────────────────────────────────────────────────────────
    def _construir_tab_bajas(self, parent):
        f_bar = tk.Frame(parent, bg="#ffffff", bd=1, relief="solid")
        f_bar.pack(fill="x", padx=6, pady=(6, 2))

        tk.Label(f_bar, text="🔍 Buscar en Bienes de Baja:", font=("Segoe UI", 9, "bold"), fg="#475569", bg="#ffffff").pack(side="left", padx=(8, 4), pady=6)
        etr_s = ttk.Entry(f_bar, textvariable=self.var_search_bajas, width=32)
        etr_s.pack(side="left", padx=4, pady=6)
        etr_s.bind("<KeyRelease>", lambda _e: self._filtrar_tabla_bajas())

        btn_clr = ttk.Button(f_bar, text="✕ Limpiar", command=lambda: (self.var_search_bajas.set(""), self._filtrar_tabla_bajas()))
        btn_clr.pack(side="left", padx=4)

        tk.Label(
            f_bar,
            text="⚠️ Estos bienes no computan en el avance ni faltantes del inventario",
            font=("Segoe UI", 8, "italic"),
            fg="#dc2626", bg="#ffffff"
        ).pack(side="left", padx=(12, 0))

        self.lbl_count_bajas = tk.Label(f_bar, text="", font=("Segoe UI", 9, "italic"), fg="#64748b", bg="#ffffff")
        self.lbl_count_bajas.pack(side="right", padx=10)

        f_tree = tk.Frame(parent, bg="#ffffff")
        f_tree.pack(fill="both", expand=True, padx=6, pady=(2, 6))

        cols = ("num", "codint", "codpat", "denominacion", "ubicacion", "estado_cons", "cta_cont", "val_adq")
        self.tree_bajas = ttk.Treeview(f_tree, columns=cols, show="headings", style="Stats.Treeview")

        self.tree_bajas.heading("num", text="#")
        self.tree_bajas.heading("codint", text="Cód. Interno", command=lambda: sort_by(self.tree_bajas, "codint", True))
        self.tree_bajas.heading("codpat", text="Cód. Patrimonial", command=lambda: sort_by(self.tree_bajas, "codpat", False))
        self.tree_bajas.heading("denominacion", text="Denominación del Bien", command=lambda: sort_by(self.tree_bajas, "denominacion", False))
        self.tree_bajas.heading("ubicacion", text="Sede / Ubicación Registrada", command=lambda: sort_by(self.tree_bajas, "ubicacion", False))
        self.tree_bajas.heading("estado_cons", text="Conservación", command=lambda: sort_by(self.tree_bajas, "estado_cons", False))
        self.tree_bajas.heading("cta_cont", text="Cuenta", command=lambda: sort_by(self.tree_bajas, "cta_cont", False))
        self.tree_bajas.heading("val_adq", text="Val. Adq. (S/)", command=lambda: sort_by(self.tree_bajas, "val_adq", True))

        self.tree_bajas.column("num", width=40, anchor="center")
        self.tree_bajas.column("codint", width=85, anchor="center")
        self.tree_bajas.column("codpat", width=120, anchor="center")
        self.tree_bajas.column("denominacion", width=340, anchor="w")
        self.tree_bajas.column("ubicacion", width=260, anchor="w")
        self.tree_bajas.column("estado_cons", width=95, anchor="center")
        self.tree_bajas.column("cta_cont", width=85, anchor="center")
        self.tree_bajas.column("val_adq", width=110, anchor="e")

        scr_y = ttk.Scrollbar(f_tree, orient="vertical", command=self.tree_bajas.yview)
        scr_x = ttk.Scrollbar(f_tree, orient="horizontal", command=self.tree_bajas.xview)
        self.tree_bajas.configure(yscrollcommand=scr_y.set, xscrollcommand=scr_x.set)

        self.tree_bajas.grid(row=0, column=0, sticky="nsew")
        scr_y.grid(row=0, column=1, sticky="ns")
        scr_x.grid(row=1, column=0, sticky="ew")

        f_tree.columnconfigure(0, weight=1)
        f_tree.rowconfigure(0, weight=1)

        self.tree_bajas.tag_configure("totales", font=("Segoe UI", 9, "bold"), background="#e2e8f0", foreground="#0f172a")
        self.tree_bajas.tag_configure("par", background="#f8fafc")
        self.tree_bajas.tag_configure("impar", background="#ffffff")

    # ─────────────────────────────────────────────────────────────────────────
    # CARGA ASÍNCRONA DE DATOS Y CONSULTAS SQL
    # ─────────────────────────────────────────────────────────────────────────
    def cargar_datos_asincrono(self):
        """Dispara la recolección de estadísticas en un hilo secundario sin congelar la UI."""
        if self.is_loading:
            return
        self.is_loading = True
        self.lbl_status.config(text="⏳ Cargando estadísticas del inventario y bienes faltantes...")

        sede_sel = self.var_sede_filtro.get().strip()
        filtro_sede = None if sede_sel in ("[ TODAS LAS SEDES / LOCALES ]", "") else sede_sel
        modo_condicion = self.var_condicion_modo.get().strip()

        while not self._data_queue.empty():
            try:
                self._data_queue.get_nowait()
            except Exception:
                break

        threading.Thread(target=self._hilo_consultas, args=(filtro_sede, modo_condicion), daemon=True).start()
        self.after(100, self._verificar_cola_datos)

    def _verificar_cola_datos(self):
        try:
            msg_type, data = self._data_queue.get_nowait()
            if msg_type == "SUCCESS":
                self._actualizar_ui(data)
            elif msg_type == "ERROR":
                self.lbl_status.config(text=f"❌ Error al consultar estadísticas: {data}")
            self.is_loading = False
            return
        except queue.Empty:
            pass

        if self.is_loading and self.winfo_exists():
            self.after(100, self._verificar_cola_datos)

    def _hilo_consultas(self, filtro_sede, modo_condicion):
        try:
            con = iniciar_conexion_sqlite()
            cur = con.cursor()

            cond_sql = "UPPER(TRIM(COALESCE(ir.estado, 'ALTA'))) != 'BAJA'"
            if modo_condicion == "TODOS":
                cond_sql = "1=1"
            elif modo_condicion == "BAJA":
                cond_sql = "UPPER(TRIM(COALESCE(ir.estado, 'ALTA'))) = 'BAJA'"

            where_parts = [cond_sql]
            params = []

            if filtro_sede:
                where_parts.append("UPPER(TRIM(COALESCE(loc.local, ''))) = ?")
                params.append(filtro_sede.upper())

            where_str = "WHERE " + " AND ".join(where_parts)

            # 1. KPIs Globales de Bienes Activos (Condición ALTA)
            q_kpi_activos = f"""
                SELECT 
                    COUNT(*) as total_alta,
                    SUM(CASE WHEN ir.inventariado=1 AND ir.codigo_ubicacion_final NOT IN ('', '0') THEN 1 ELSE 0 END) as inv_alta,
                    SUM(CASE WHEN ir.inventariado=0 OR ir.inventariado IS NULL OR ir.codigo_ubicacion_final IN ('', '0') THEN 1 ELSE 0 END) as fal_alta,
                    COALESCE(SUM(ir.val_adq), 0.0) as val_adq_alta,
                    COALESCE(SUM(ir.valor_neto), 0.0) as val_neto_alta
                FROM inventory_records ir
                LEFT JOIN locations loc ON CAST(loc.codigo_ubicacion AS TEXT) = CAST(ir.codigo_ubicacion_inicial AS TEXT)
                {where_str}
            """
            cur.execute(q_kpi_activos, params)
            row_alta = cur.fetchone() or (0, 0, 0, 0.0, 0.0)
            tot_alta = int(row_alta[0] or 0)
            inv_alta = int(row_alta[1] or 0)
            fal_alta = int(row_alta[2] or 0)
            val_adq_alta = float(row_alta[3] or 0.0)

            # 2. Conteo y valor de Bienes Dados de BAJA (Informativo)
            where_baja_parts = ["UPPER(TRIM(COALESCE(ir.estado, 'ALTA'))) = 'BAJA'"]
            params_baja = []
            if filtro_sede:
                where_baja_parts.append("UPPER(TRIM(COALESCE(loc.local, ''))) = ?")
                params_baja.append(filtro_sede.upper())
            where_baja_str = "WHERE " + " AND ".join(where_baja_parts)

            q_kpi_baja = f"""
                SELECT 
                    COUNT(*) as total_baja,
                    COALESCE(SUM(ir.val_adq), 0.0) as val_adq_baja
                FROM inventory_records ir
                LEFT JOIN locations loc ON CAST(loc.codigo_ubicacion AS TEXT) = CAST(ir.codigo_ubicacion_inicial AS TEXT)
                {where_baja_str}
            """
            cur.execute(q_kpi_baja, params_baja)
            row_baja = cur.fetchone() or (0, 0.0)
            tot_baja = int(row_baja[0] or 0)
            val_adq_baja = float(row_baja[1] or 0.0)

            # 3. Consulta Sobrantes
            try:
                cur.execute("SELECT COUNT(*) FROM surplus")
                sob_bienes = int(cur.fetchone()[0] or 0)
            except Exception:
                try:
                    cur.execute("SELECT COUNT(*) FROM sobrantes")
                    sob_bienes = int(cur.fetchone()[0] or 0)
                except Exception:
                    sob_bienes = 0

            # 4. Estados de Conservación (sobre condición ALTA / activa)
            q_est = f"""
                SELECT 
                    UPPER(TRIM(COALESCE(ir.estado_conservacion, 'SIN ESTADO'))) as estado,
                    COUNT(*) as total,
                    SUM(CASE WHEN ir.inventariado=1 AND ir.codigo_ubicacion_final NOT IN ('', '0') THEN 1 ELSE 0 END) as inv,
                    SUM(CASE WHEN ir.inventariado=0 OR ir.inventariado IS NULL OR ir.codigo_ubicacion_final IN ('', '0') THEN 1 ELSE 0 END) as fal
                FROM inventory_records ir
                LEFT JOIN locations loc ON CAST(loc.codigo_ubicacion AS TEXT) = CAST(ir.codigo_ubicacion_inicial AS TEXT)
                {where_str}
                GROUP BY UPPER(TRIM(COALESCE(ir.estado_conservacion, 'SIN ESTADO')))
                ORDER BY total DESC
            """
            cur.execute(q_est, params)
            estados_data = cur.fetchall()

            # 5. Avance por Sede / Local (sobre bienes activos)
            q_loc = f"""
                SELECT 
                    UPPER(TRIM(COALESCE(loc.local, 'SIN SEDE/LOCAL'))) as sede,
                    COUNT(ir.id) as total,
                    SUM(CASE WHEN ir.inventariado=1 AND ir.codigo_ubicacion_final NOT IN ('', '0') THEN 1 ELSE 0 END) as inv,
                    SUM(CASE WHEN ir.inventariado=0 OR ir.inventariado IS NULL OR ir.codigo_ubicacion_final IN ('', '0') THEN 1 ELSE 0 END) as fal
                FROM inventory_records ir
                LEFT JOIN locations loc ON CAST(loc.codigo_ubicacion AS TEXT) = CAST(ir.codigo_ubicacion_inicial AS TEXT)
                WHERE {cond_sql}
                GROUP BY UPPER(TRIM(COALESCE(loc.local, 'SIN SEDE/LOCAL')))
                ORDER BY total DESC
            """
            cur.execute(q_loc)
            locales_data = cur.fetchall()
            sedes_combo = ["[ TODAS LAS SEDES / LOCALES ]"] + [r[0] for r in locales_data if r[0] != "SIN SEDE/LOCAL"]

            # 6. Por Cuenta Contable (sobre bienes activos)
            q_cta = f"""
                SELECT 
                    COALESCE(ir.cuenta_contable, 'SIN CUENTA') as cta,
                    COALESCE(ir.denominacion_cuenta, '') as den_cta,
                    COUNT(ir.id) as total,
                    SUM(CASE WHEN ir.inventariado=1 AND ir.codigo_ubicacion_final NOT IN ('', '0') THEN 1 ELSE 0 END) as inv,
                    SUM(CASE WHEN ir.inventariado=0 OR ir.inventariado IS NULL OR ir.codigo_ubicacion_final IN ('', '0') THEN 1 ELSE 0 END) as fal,
                    COALESCE(SUM(ir.val_adq), 0.0) as val_adq,
                    COALESCE(SUM(ir.valor_neto), 0.0) as val_neto
                FROM inventory_records ir
                LEFT JOIN locations loc ON CAST(loc.codigo_ubicacion AS TEXT) = CAST(ir.codigo_ubicacion_inicial AS TEXT)
                {where_str}
                GROUP BY ir.cuenta_contable, ir.denominacion_cuenta
                ORDER BY total DESC
            """
            cur.execute(q_cta, params)
            cuentas_data = cur.fetchall()

            # 7. Por Inventariador / Equipo (sobre bienes inventariados)
            q_per = f"""
                SELECT 
                    COALESCE(NULLIF(TRIM(ir.inventariador_local), ''), 'NO ASIGNADO') as inventariador,
                    COALESCE(NULLIF(TRIM(ir.equipo_local), ''), '-') as equipo,
                    COUNT(ir.id) as total_inv,
                    MIN(ir.fecha_inventariado) as primer_reg,
                    MAX(ir.fecha_inventariado) as ultimo_reg
                FROM inventory_records ir
                LEFT JOIN locations loc ON CAST(loc.codigo_ubicacion AS TEXT) = CAST(ir.codigo_ubicacion_inicial AS TEXT)
                WHERE ir.inventariado = 1 AND ir.codigo_ubicacion_final NOT IN ('', '0')
                  AND {cond_sql}
                """ + (f" AND UPPER(TRIM(COALESCE(loc.local, ''))) = ?" if filtro_sede else "") + """
                GROUP BY COALESCE(NULLIF(TRIM(ir.inventariador_local), ''), 'NO ASIGNADO'), COALESCE(NULLIF(TRIM(ir.equipo_local), ''), '-')
                ORDER BY total_inv DESC
            """
            cur.execute(q_per, params if filtro_sede else [])
            personal_data = cur.fetchall()

            # 8. Top 30 Denominaciones (sobre bienes activos)
            q_den = f"""
                SELECT 
                    UPPER(TRIM(ir.denominacion)) as denominacion,
                    COUNT(ir.id) as total,
                    SUM(CASE WHEN ir.inventariado=1 AND ir.codigo_ubicacion_final NOT IN ('', '0') THEN 1 ELSE 0 END) as inv,
                    SUM(CASE WHEN ir.inventariado=0 OR ir.inventariado IS NULL OR ir.codigo_ubicacion_final IN ('', '0') THEN 1 ELSE 0 END) as fal
                FROM inventory_records ir
                LEFT JOIN locations loc ON CAST(loc.codigo_ubicacion AS TEXT) = CAST(ir.codigo_ubicacion_inicial AS TEXT)
                WHERE ir.denominacion IS NOT NULL AND TRIM(ir.denominacion) != ''
                  AND {cond_sql}
                """ + (f" AND UPPER(TRIM(COALESCE(loc.local, ''))) = ?" if filtro_sede else "") + """
                GROUP BY UPPER(TRIM(ir.denominacion))
                ORDER BY total DESC
                LIMIT 30
            """
            cur.execute(q_den, params if filtro_sede else [])
            denos_data = cur.fetchall()

            # 9. Bienes de Baja (Informativo)
            q_bajas_det = f"""
                SELECT 
                    COALESCE(ir.codigo_interno, CAST(ir.id AS TEXT)) as codint,
                    COALESCE(ir.codigo_patrimonial, '') as codpat,
                    COALESCE(ir.denominacion, '') as denominacion,
                    COALESCE(loc.local || ' - ' || loc.oficina, 'SIN UBICACION') as ubicacion,
                    COALESCE(ir.estado_conservacion, '') as estado_cons,
                    COALESCE(ir.cuenta_contable, '') as cta_cont,
                    COALESCE(ir.val_adq, 0.0) as val_adq
                FROM inventory_records ir
                LEFT JOIN locations loc ON CAST(loc.codigo_ubicacion AS TEXT) = CAST(ir.codigo_ubicacion_inicial AS TEXT)
                {where_baja_str}
                ORDER BY ir.codigo_interno ASC
            """
            cur.execute(q_bajas_det, params_baja)
            bajas_data = cur.fetchall()

            # 10. BIENES FALTANTES DETALLADO (Activos en ALTA pendientes de inventariar)
            q_faltantes = f"""
                SELECT 
                    COALESCE(ir.codigo_interno, CAST(ir.id AS TEXT)) as codint,
                    COALESCE(ir.codigo_patrimonial, '') as codpat,
                    COALESCE(ir.denominacion, '') as denominacion,
                    COALESCE(NULLIF(TRIM(per.nombres || ' ' || per.apellidos), ''), NULLIF(TRIM(loc.codigo_personal), ''), 'SIN ASIGNAR') as responsable,
                    COALESCE(NULLIF(TRIM(loc.local), ''), 'SIN LOCAL') as local,
                    COALESCE(NULLIF(TRIM(loc.area), ''), 'SIN AREA') as area,
                    COALESCE(NULLIF(TRIM(loc.oficina), ''), 'SIN OFICINA') as oficina,
                    COALESCE(ir.cuenta_contable, '') as cta_cont,
                    COALESCE(ir.estado_conservacion, '') as estado,
                    COALESCE(ir.marca, '') as marca,
                    COALESCE(ir.modelo, '') as modelo,
                    COALESCE(ir.serie, '') as serie,
                    COALESCE(ir.val_adq, 0.0) as val_adq
                FROM inventory_records ir
                LEFT JOIN locations loc ON CAST(loc.codigo_ubicacion AS TEXT) = CAST(ir.codigo_ubicacion_inicial AS TEXT)
                LEFT JOIN personnel per ON CAST(per.codigo_personal AS TEXT) = CAST(loc.codigo_personal AS TEXT)
                WHERE UPPER(TRIM(COALESCE(ir.estado, 'ALTA'))) != 'BAJA'
                  AND (ir.inventariado = 0 OR ir.inventariado IS NULL OR ir.codigo_ubicacion_final IN ('', '0'))
                """ + (f" AND UPPER(TRIM(COALESCE(loc.local, ''))) = ?" if filtro_sede else "") + """
                ORDER BY loc.local, loc.area, loc.oficina, ir.codigo_interno ASC
            """
            cur.execute(q_faltantes, params if filtro_sede else [])
            faltantes_data = cur.fetchall()

            con.close()

            payload = {
                "tot_alta": tot_alta,
                "inv_alta": inv_alta,
                "fal_alta": fal_alta,
                "tot_baja": tot_baja,
                "sob_bienes": sob_bienes,
                "val_adq_alta": val_adq_alta,
                "val_adq_baja": val_adq_baja,
                "estados_data": estados_data,
                "locales_data": locales_data,
                "sedes_combo": sedes_combo,
                "cuentas_data": cuentas_data,
                "personal_data": personal_data,
                "denos_data": denos_data,
                "bajas_data": bajas_data,
                "faltantes_data": faltantes_data
            }
            self._data_queue.put(("SUCCESS", payload))

        except Exception as e:
            print(f"[ESTADISTICAS][ERROR] Falló hilo de consultas: {e}")
            import traceback
            traceback.print_exc()
            self._data_queue.put(("ERROR", str(e)))

    def _actualizar_ui(self, p):
        """Aplica los datos obtenidos a las tarjetas, gráficos y tablas."""
        tot = p["tot_alta"]
        inv = p["inv_alta"]
        fal = p["fal_alta"]
        baja = p["tot_baja"]
        sob = p["sob_bienes"]
        v_adq = p["val_adq_alta"]
        v_baja = p["val_adq_baja"]

        pct = (inv / tot * 100) if tot > 0 else 0.0

        # Tarjetas KPI con distinción explícita
        self.var_kpi_total.set(f"{tot:,}")
        self.var_kpi_inv.set(f"{inv:,}")
        self.var_kpi_fal.set(f"{fal:,}")
        self.var_kpi_pct.set(f"{pct:.1f}%")
        self.var_kpi_sob.set(f"{sob:,}")
        self.var_kpi_baja.set(f"{baja:,}")
        self.var_kpi_val_adq.set(f"S/ {v_adq:,.2f}")
        self.var_kpi_val_baja.set(f"S/ {v_baja:,.2f}")

        # Combobox Sedes
        if len(p["sedes_combo"]) > len(self.lista_sedes_combo):
            self.lista_sedes_combo = p["sedes_combo"]
            self.cbx_sede.config(values=self.lista_sedes_combo)

        # 0. Pestaña Resumen & Gráficos
        self.raw_estados = p["estados_data"]
        self._cargar_tabla_estados(self.raw_estados, tot)
        self._redibujar_graficos_canvas(self.raw_estados, tot, inv, fal, sob, baja)

        # 1. Pestaña Faltantes Detallado (¡NUEVA!)
        self.raw_faltantes = p["faltantes_data"]
        self._actualizar_filtros_combos_faltantes()
        self._filtrar_tabla_faltantes()

        # 2. Pestaña Locales
        self.raw_locales = p["locales_data"]
        self._filtrar_tabla_locales()

        # 3. Pestaña Cuentas
        self.raw_cuentas = p["cuentas_data"]
        self._filtrar_tabla_cuentas()

        # 4. Pestaña Personal
        self.raw_personal = p["personal_data"]
        self._filtrar_tabla_personal()

        # 5. Pestaña Denominaciones
        self.raw_denos = p["denos_data"]
        self._filtrar_tabla_denos()

        # 6. Pestaña Bienes de Baja (Informativo)
        self.raw_bajas = p["bajas_data"]
        self._filtrar_tabla_bajas()

        self.lbl_status.config(
            text=f"✓ Estadísticas calculadas: {tot:,} bienes en Alta | {inv:,} inventariados ({pct:.1f}%) | {len(self.raw_faltantes):,} faltantes reales | {baja:,} bajas informativas."
        )

    def _actualizar_filtros_combos_faltantes(self):
        """Puebla los desplegables de filtros para la pestaña de Faltantes."""
        locales = ["[ TODOS ]"] + sorted(list(set(r[4] for r in self.raw_faltantes if r[4] and r[4] != "SIN LOCAL")))
        areas = ["[ TODAS ]"] + sorted(list(set(r[5] for r in self.raw_faltantes if r[5] and r[5] != "SIN AREA")))
        oficinas = ["[ TODAS ]"] + sorted(list(set(r[6] for r in self.raw_faltantes if r[6] and r[6] != "SIN OFICINA")))
        cuentas = ["[ TODAS ]"] + sorted(list(set(r[7] for r in self.raw_faltantes if r[7])))
        responsables = ["[ TODOS ]"] + sorted(list(set(r[3] for r in self.raw_faltantes if r[3] and r[3] != "SIN ASIGNAR")))

        self.lista_fal_locales = locales
        self.lista_fal_areas = areas
        self.lista_fal_oficinas = oficinas
        self.lista_fal_cuentas = cuentas
        self.lista_fal_responsables = responsables

        self.cbx_fal_local.config(values=self.lista_fal_locales)
        self.cbx_fal_area.config(values=self.lista_fal_areas)
        if hasattr(self, 'cbx_fal_oficina') and isinstance(self.cbx_fal_oficina, ttk.Combobox):
            self.cbx_fal_oficina.config(values=self.lista_fal_oficinas)
        self.cbx_fal_cta.config(values=self.lista_fal_cuentas)
        self.cbx_fal_resp.config(values=self.lista_fal_responsables)

    # ─────────────────────────────────────────────────────────────────────────
    # CARGA Y FILTRADO DE TABLAS
    # ─────────────────────────────────────────────────────────────────────────
    def _cargar_tabla_estados(self, data, tot_global):
        for item in self.tree_estados.get_children():
            self.tree_estados.delete(item)

        sum_tot, sum_inv, sum_fal = 0, 0, 0
        for idx, (estado, tot, inv, fal) in enumerate(data):
            sum_tot += tot
            sum_inv += inv
            sum_fal += fal
            pct_av = f"{(inv / tot * 100):.1f}%" if tot > 0 else "0.0%"
            pct_padron = f"{(tot / tot_global * 100):.1f}%" if tot_global > 0 else "0.0%"
            tag = "par" if idx % 2 == 0 else "impar"
            self.tree_estados.insert("", "end", values=(estado, f"{tot:,}", f"{inv:,}", f"{fal:,}", pct_av, pct_padron), tags=(tag,))

        pct_av_total = f"{(sum_inv / sum_tot * 100):.1f}%" if sum_tot > 0 else "0.0%"
        self.tree_estados.insert("", "end", values=("TOTALES (ALTA)", f"{sum_tot:,}", f"{sum_inv:,}", f"{sum_fal:,}", pct_av_total, "100.0%"), tags=("totales",))

    def _filtrar_tabla_locales(self):
        for item in self.tree_locales.get_children():
            self.tree_locales.delete(item)

        search = self.var_search_locales.get().strip().upper()
        sum_tot, sum_inv, sum_fal = 0, 0, 0
        count = 0

        for r in self.raw_locales:
            sede = str(r[0] or "")
            if search and search not in sede.upper():
                continue

            tot = int(r[1] or 0)
            inv = int(r[2] or 0)
            fal = int(r[3] or 0)
            sum_tot += tot
            sum_inv += inv
            sum_fal += fal
            count += 1

            pct = (inv / tot * 100) if tot > 0 else 0.0
            if pct >= 95.0:
                tag, est_txt = "completa", "COMPLETA"
            elif pct >= 60.0:
                tag, est_txt = "alta", "AVANZADA"
            elif pct >= 25.0:
                tag, est_txt = "media", "EN PROCESO"
            else:
                tag, est_txt = "baja", "INICIAL"

            self.tree_locales.insert(
                "", "end",
                values=(count, sede, f"{tot:,}", f"{inv:,}", f"{fal:,}", f"{pct:.1f}%", est_txt),
                tags=(tag,)
            )

        pct_tot = (sum_inv / sum_tot * 100) if sum_tot > 0 else 0.0
        self.tree_locales.insert(
            "", "end",
            values=("TOTAL", f"TOTAL ({count} LOCALES)", f"{sum_tot:,}", f"{sum_inv:,}", f"{sum_fal:,}", f"{pct_tot:.1f}%", ""),
            tags=("totales",)
        )
        self.lbl_count_loc.config(text=f"{count} locales listados (Condición Alta)")

    def _filtrar_tabla_cuentas(self):
        for item in self.tree_cuentas.get_children():
            self.tree_cuentas.delete(item)

        search = self.var_search_cuentas.get().strip().upper()
        sum_tot, sum_inv, sum_fal = 0, 0, 0
        sum_adq, sum_net = 0.0, 0.0
        count = 0

        for idx, r in enumerate(self.raw_cuentas):
            cta = str(r[0] or "")
            den = str(r[1] or "")
            if search and (search not in cta.upper() and search not in den.upper()):
                continue

            tot = int(r[2] or 0)
            inv = int(r[3] or 0)
            fal = int(r[4] or 0)
            adq = float(r[5] or 0.0)
            net = float(r[6] or 0.0)

            sum_tot += tot
            sum_inv += inv
            sum_fal += fal
            sum_adq += adq
            sum_net += net
            count += 1

            pct = (inv / tot * 100) if tot > 0 else 0.0
            tag = "par" if idx % 2 == 0 else "impar"
            self.tree_cuentas.insert(
                "", "end",
                values=(cta, den, f"{tot:,}", f"{inv:,}", f"{fal:,}", f"{pct:.1f}%", f"{adq:,.2f}", f"{net:,.2f}"),
                tags=(tag,)
            )

        pct_tot = (sum_inv / sum_tot * 100) if sum_tot > 0 else 0.0
        self.tree_cuentas.insert(
            "", "end",
            values=("TOTALES", f"TOTAL ({count} CUENTAS)", f"{sum_tot:,}", f"{sum_inv:,}", f"{sum_fal:,}", f"{pct_tot:.1f}%", f"{sum_adq:,.2f}", f"{sum_net:,.2f}"),
            tags=("totales",)
        )
        self.lbl_count_cta.config(text=f"{count} cuentas listadas (Condición Alta)")

    def _filtrar_tabla_personal(self):
        for item in self.tree_personal.get_children():
            self.tree_personal.delete(item)

        search = self.var_search_personal.get().strip().upper()
        sum_inv = 0
        tot_inventariados = sum([int(r[2] or 0) for r in self.raw_personal])
        count = 0

        for r in self.raw_personal:
            usr = str(r[0] or "")
            eq = str(r[1] or "")
            if search and (search not in usr.upper() and search not in eq.upper()):
                continue

            inv = int(r[2] or 0)
            p_reg = str(r[3] or "")
            u_reg = str(r[4] or "")
            sum_inv += inv
            count += 1

            pct = (inv / tot_inventariados * 100) if tot_inventariados > 0 else 0.0
            tag = "par" if count % 2 == 0 else "impar"
            self.tree_personal.insert(
                "", "end",
                values=(count, usr, eq, f"{inv:,}", f"{pct:.1f}%", p_reg, u_reg),
                tags=(tag,)
            )

        self.tree_personal.insert(
            "", "end",
            values=("TOTAL", f"TOTAL ({count} USUARIOS/EQUIPOS)", "", f"{sum_inv:,}", "100.0%", "", ""),
            tags=("totales",)
        )
        self.lbl_count_per.config(text=f"{count} inventariadores listados")

    def _filtrar_tabla_denos(self):
        for item in self.tree_denos.get_children():
            self.tree_denos.delete(item)

        search = self.var_search_denos.get().strip().upper()
        sum_tot, sum_inv, sum_fal = 0, 0, 0
        count = 0

        for r in self.raw_denos:
            deno = str(r[0] or "")
            if search and search not in deno.upper():
                continue

            tot = int(r[1] or 0)
            inv = int(r[2] or 0)
            fal = int(r[3] or 0)
            sum_tot += tot
            sum_inv += inv
            sum_fal += fal
            count += 1

            pct = (inv / tot * 100) if tot > 0 else 0.0
            tag = "par" if count % 2 == 0 else "impar"
            self.tree_denos.insert(
                "", "end",
                values=(count, deno, f"{tot:,}", f"{inv:,}", f"{fal:,}", f"{pct:.1f}%"),
                tags=(tag,)
            )

        pct_tot = (sum_inv / sum_tot * 100) if sum_tot > 0 else 0.0
        self.tree_denos.insert(
            "", "end",
            values=("TOTAL", f"TOTAL ({count} TIPOS)", f"{sum_tot:,}", f"{sum_inv:,}", f"{sum_fal:,}", f"{pct_tot:.1f}%"),
            tags=("totales",)
        )
        self.lbl_count_deno.config(text=f"{count} denominaciones listadas (Condición Alta)")

    def _filtrar_tabla_bajas(self):
        """Filtra y renderiza la tabla informativa de bienes dados de baja."""
        for item in self.tree_bajas.get_children():
            self.tree_bajas.delete(item)

        search = self.var_search_bajas.get().strip().upper()
        sum_adq = 0.0
        count = 0

        for r in self.raw_bajas:
            codint = str(r[0] or "")
            codpat = str(r[1] or "")
            deno = str(r[2] or "")
            ubi = str(r[3] or "")
            cons = str(r[4] or "")
            cta = str(r[5] or "")
            val = float(r[6] or 0.0)

            if search:
                coincide = (
                    search in codint.upper() or
                    search in codpat.upper() or
                    search in deno.upper() or
                    search in ubi.upper() or
                    search in cta.upper() or
                    search in cons.upper()
                )
                if not coincide:
                    continue

            count += 1
            sum_adq += val
            tag = "par" if count % 2 == 0 else "impar"
            self.tree_bajas.insert(
                "", "end",
                values=(count, codint, codpat, deno, ubi, cons, cta, f"{val:,.2f}"),
                tags=(tag,)
            )

        self.tree_bajas.insert(
            "", "end",
            values=("TOTAL", f"{count} BIENES", "", "TOTAL BIENES DADOS DE BAJA (INFORMATIVO)", "", "", "", f"{sum_adq:,.2f}"),
            tags=("totales",)
        )
        self.lbl_count_bajas.config(text=f"{count} bienes de baja listados (Informativo)")

    # ─────────────────────────────────────────────────────────────────────────
    # EXPORTACIÓN A EXCEL
    # ─────────────────────────────────────────────────────────────────────────
    def exportar_pestana_activa(self):
        """Exporta la tabla de la pestaña activa actualmente."""
        tab_idx = self.notebook.index(self.notebook.select())

        if tab_idx == 0:
            tree = self.tree_estados
            nombre_base = "Estadisticas_Estados_Alta"
            columnas = ["Estado", "Total", "Inventariados", "Faltantes", "% Avance", "% del Total"]
        elif tab_idx == 1:
            tree = self.tree_faltantes
            nombre_base = "Bienes_Faltantes_Detallado_Alta"
            columnas = [
                "#", "Cód. Interno", "Cód. Patrimonial", "Denominación del Bien",
                "Responsable / Usuario", "Sede / Local", "Área", "Oficina",
                "Cuenta Contable", "Estado Conservación", "Marca", "Modelo", "Serie", "Val. Adquisición (S/)"
            ]
        elif tab_idx == 2:
            tree = self.tree_locales
            nombre_base = "Estadisticas_Por_Sede_Alta"
            columnas = ["#", "Sede / Local", "Total Bienes Activos", "Inventariados", "Faltantes", "% Avance", "Estado"]
        elif tab_idx == 3:
            tree = self.tree_cuentas
            nombre_base = "Estadisticas_Por_Cuenta_Alta"
            columnas = ["Cuenta", "Denominación", "Total Bienes Activos", "Inventariados", "Faltantes", "% Avance", "Val. Adquisición (S/)", "Val. Neto (S/)"]
        elif tab_idx == 4:
            tree = self.tree_personal
            nombre_base = "Estadisticas_Por_Inventariador"
            columnas = ["#", "Inventariador", "Equipo", "Bienes Inventariados", "% de Aporte", "Primer Registro", "Último Registro"]
        elif tab_idx == 5:
            tree = self.tree_denos
            nombre_base = "Estadisticas_Top_Bienes_Alta"
            columnas = ["#", "Denominación del Bien", "Total en Padrón Activo", "Inventariados", "Faltantes", "% Avance"]
        elif tab_idx == 6:
            tree = self.tree_bajas
            nombre_base = "Bienes_Dados_de_Baja_Informativo"
            columnas = ["#", "Cód. Interno", "Cód. Patrimonial", "Denominación del Bien", "Sede / Ubicación", "Estado Conservación", "Cuenta", "Val. Adquisición (S/)"]
        else:
            return

        datos = []
        for item in tree.get_children():
            datos.append(list(tree.item(item, "values")))

        if not datos:
            mb.showwarning("Sin Datos", "No hay datos en la tabla activa para exportar.", parent=self)
            return

        try:
            exportar_excel(nombre_base, columnas, datos)
            self.focus_set()
        except Exception as e:
            mb.showerror("Error al Exportar", f"No se pudo exportar a Excel:\n{e}", parent=self)
