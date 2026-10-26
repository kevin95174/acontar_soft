import tkinter as tk
from tkinter import ttk, PhotoImage, filedialog
from tkinter import messagebox as mb
import os
import threading

from db.query import analisis_1
from reportes.analisis import iniciar_reporte
from data.exp_excel import exportar_excel
from gui.gui_detalle_analisis import Window_d_analisis
from utils.order_utils import sort_by
from utils.helpers import resource_path

_RENDER_CHUNK_SIZE = 400


class Window_analisis(tk.Toplevel):
    """Ventana de análisis gerencial por Ubicación, Cuenta Contable, Denominación o Usuario."""

    def __init__(self, root=None, valor=None):
        super().__init__(root)
        self.root = root
        self.valor = valor if valor is not None else 1

        # Título según tipo de análisis
        if self.valor == 1:
            self.title("Análisis por Ubicación — Control de Oficinas")
        elif self.valor == 2:
            self.title("Análisis por Cuenta Contable")
        elif self.valor == 3:
            self.title("Análisis por Denominación del Bien")
        elif self.valor == 4:
            self.title("Análisis por Usuario / Responsable")
        else:
            self.title("Análisis de Resultados")

        self.configure(bg="#f8fafc")
        self.geometry("1240x740")
        self.minsize(1060, 620)

        self._cargar_favicon()
        self._centrar_ventana(1240, 740)
        try:
            self.state("zoomed")
        except Exception:
            pass

        self._configurar_estilos()

        # Cargar iconos de manera segura con resource_path
        self.iconoxls = self._cargar_icono("img/excel.png")
        self.iconopdf = self._cargar_icono("img/pdf.png")
        self.iconobus = self._cargar_icono("img/lupa.png")
        self.iconobor = self._cargar_icono("img/borrar.png")

        # Variables de datos y control de fluidez
        self.datos_ubicacion = []      # Lista de dicts procesados para valor == 1
        self.datos_generales = []      # Filas procesadas para valor 2, 3, 4
        self.totales_generales = []    # Fila de totales precalculada en memoria
        self.locales_lista = []
        self._query_lock = False
        self._render_token = 0
        self._debounce_job = None

        # Contenedor principal
        self.contenedor = tk.Frame(self, bg="#f8fafc")
        self.contenedor.pack(fill="both", expand=True, padx=12, pady=10)

        # Cabecera y KPIs
        self.Frame_top = tk.Frame(self.contenedor, bg="#f8fafc")
        self.Frame_top.pack(fill="x", side="top", pady=(0, 8))

        self.Frame_kpis = tk.Frame(self.Frame_top, bg="#f8fafc")

        # Card de Filtros
        self.Frame_filtros = ttk.LabelFrame(
            self.contenedor,
            text=" 🔎 Filtros de Búsqueda y Exportación ",
            style="Analisis.TLabelframe",
            padding=(10, 6)
        )
        self.Frame_filtros.pack(fill="x", side="top", pady=(0, 8))

        # Card de Tabla de Resultados
        self.Frame2 = ttk.LabelFrame(
            self.contenedor,
            text=" 📋 Resultados del Análisis ",
            style="Analisis.TLabelframe",
            padding=8
        )
        self.Frame2.rowconfigure(0, weight=1)
        self.Frame2.columnconfigure(0, weight=1)
        self.Frame2.pack(fill="both", expand=True)

        # Barra Inferior de Estado
        self.Frame_status = tk.Frame(self.contenedor, bg="#f8fafc")
        self.Frame_status.pack(fill="x", side="bottom", pady=(6, 0))

        # Barra Fija de Resumen de Totales (siempre visible sin necesidad de bajar el scroll)
        self.Frame_resumen = tk.Frame(
            self.contenedor,
            bg="#f1f5f9",
            bd=1,
            relief="solid",
            padx=12,
            pady=7,
        )
        self.Frame_resumen.pack(fill="x", side="bottom", pady=(8, 0))
        self.resumen_items_frame = tk.Frame(self.Frame_resumen, bg="#f1f5f9")
        self.resumen_items_frame.pack(fill="x")

        frame_chip = tk.Frame(self.Frame_status, bg="#eff6ff", bd=1, relief="solid")
        frame_chip.pack(side="left")
        self.lbl_chip = tk.Label(
            frame_chip,
            text="📊  0 registros",
            bg="#eff6ff",
            fg="#1d4ed8",
            font=("Segoe UI", 9, "bold"),
            padx=10,
            pady=4
        )
        self.lbl_chip.pack()

        self.lbl_status = tk.Label(
            self.Frame_status,
            text="",
            bg="#f8fafc",
            fg="#475569",
            font=("Segoe UI", 9),
            anchor="w",
            padx=12
        )
        self.lbl_status.pack(side="left", fill="x", expand=True)

        # Construir interfaz y diferir consulta para mostrar la ventana al instante
        self.construir_encabezado()
        self.tree_view()
        self.tree.bind("<Double-Button-1>", self.mostrar_datos)

        self.lbl_status.config(text="⏳ Cargando análisis...")
        self.after(20, self.realizar_query)

    # -------------------------------------------------------------------------
    # CONFIGURACIÓN DE ESTILOS E ICONOS
    # -------------------------------------------------------------------------
    def _cargar_favicon(self):
        try:
            self.iconbitmap(resource_path("img/favicon.ico"))
        except Exception:
            pass

    def _centrar_ventana(self, w, h):
        self.update_idletasks()
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        x = (sw - w) // 2
        y = (sh - h) // 2
        self.geometry(f"{w}x{h}+{x}+{y}")

    def _cargar_icono(self, ruta):
        try:
            full_path = resource_path(ruta)
            if os.path.exists(full_path):
                return PhotoImage(file=full_path)
        except Exception:
            pass
        return None

    def _configurar_estilos(self):
        style = ttk.Style(self)

        # LabelFrame Card
        style.configure("Analisis.TLabelframe",
            background="#ffffff",
            relief="solid",
            borderwidth=1,
            bordercolor="#e2e8f0"
        )
        style.configure("Analisis.TLabelframe.Label",
            background="#ffffff",
            foreground="#334155",
            font=("Segoe UI", 9, "bold")
        )

        # Treeview moderno
        style.configure("Analisis.Treeview",
            background="#ffffff",
            fieldbackground="#ffffff",
            foreground="#0f172a",
            font=("Segoe UI", 9),
            rowheight=25
        )
        style.configure("Analisis.Treeview.Heading",
            background="#f1f5f9",
            foreground="#475569",
            font=("Segoe UI", 8, "bold"),
            relief="flat",
            padding=(6, 6)
        )
        style.map("Analisis.Treeview",
            background=[("selected", "#2563eb")],
            foreground=[("selected", "#ffffff")]
        )

    # -------------------------------------------------------------------------
    # CONSTRUCCIÓN DE CABECERA, KPIS Y FILTROS
    # -------------------------------------------------------------------------
    def construir_encabezado(self):
        # 1. Tarjeta de Cabecera / Título
        header_bar = tk.Frame(self.Frame_top, bg="#ffffff", bd=1, relief="solid", padx=14, pady=10)
        header_bar.pack(fill="x", pady=(0, 6 if self.valor == 1 else 0))

        titulos = {
            1: ("🏢  ANÁLISIS POR UBICACIÓN", "Control de avance por oficinas, cobertura y detección de faltantes"),
            2: ("📑  ANÁLISIS POR CUENTA CONTABLE", "Resumen valorizado de bienes registrados, inventariados y faltantes por cuenta"),
            3: ("📦  ANÁLISIS POR DENOMINACIÓN DEL BIEN", "Consolidado de existencias y valores agrupados por descripción del bien"),
            4: ("👤  ANÁLISIS POR USUARIO / RESPONSABLE", "Resumen de bienes asignados, inventariados, faltantes y sobrantes por persona"),
        }
        t_main, t_sub = titulos.get(self.valor, ("📊  ANÁLISIS DE RESULTADOS", "Resumen general del inventario"))

        tk.Label(
            header_bar,
            text=t_main,
            font=("Segoe UI", 13, "bold"),
            fg="#0f172a",
            bg="#ffffff"
        ).pack(side="left")

        tk.Label(
            header_bar,
            text=f"   —   {t_sub}",
            font=("Segoe UI", 9),
            fg="#64748b",
            bg="#ffffff"
        ).pack(side="left", pady=(2, 0))

        btn_ref = ttk.Button(header_bar, text="🔄 Actualizar Datos", command=self.realizar_query)
        btn_ref.pack(side="right")

        # 2. Panel de KPIs interactivo (Solo para valor == 1)
        if self.valor == 1:
            self.Frame_kpis.pack(fill="x")
            self.kpi_cards = {}
            kpis_config = [
                ("total",       "🏢 Total Oficinas",    "0",    "Registradas",       "#ffffff", "#0f172a", lambda: self.seleccionar_kpi("TODOS")),
                ("pendientes",  "🔴 Falta Inventariar", "0",    "0% avance",         "#fef2f2", "#991b1b", lambda: self.seleccionar_kpi("PENDIENTE")),
                ("proceso",     "🟡 En Proceso",        "0",    "Incompletas",       "#fffbeb", "#92400e", lambda: self.seleccionar_kpi("EN PROCESO")),
                ("completadas", "🟢 Completadas",       "0",    "100% inventariadas", "#f0fdf4", "#166534", lambda: self.seleccionar_kpi("COMPLETADA")),
                ("avance",      "📊 Avance Global",     "0.0%", "0 / 0 bienes",      "#eff6ff", "#1e40af", lambda: self.seleccionar_kpi("TODOS")),
            ]

            for key, titulo, val_ini, sub, bg_c, fg_c, cmd in kpis_config:
                card = tk.Frame(self.Frame_kpis, bg=bg_c, bd=1, relief="solid", cursor="hand2", padx=10, pady=6)
                card.pack(side="left", expand=True, fill="both", padx=4, pady=2)

                lbl_t = tk.Label(card, text=titulo, font=("Segoe UI", 9, "bold"), bg=bg_c, fg=fg_c, cursor="hand2")
                lbl_t.pack(anchor="w")

                lbl_v = tk.Label(card, text=val_ini, font=("Segoe UI", 15, "bold"), bg=bg_c, fg=fg_c, cursor="hand2")
                lbl_v.pack(anchor="w", pady=(1, 1))

                lbl_s = tk.Label(card, text=sub, font=("Segoe UI", 8), bg=bg_c, fg=fg_c, cursor="hand2")
                lbl_s.pack(anchor="w")

                for widget in (card, lbl_t, lbl_v, lbl_s):
                    widget.bind("<Button-1>", lambda e, c=cmd: c())

                self.kpi_cards[key] = {
                    "card": card,
                    "val": lbl_v,
                    "sub": lbl_s,
                    "bg": bg_c
                }

        # 3. Barra de Filtros
        if self.valor == 1:
            self.filtro_estado = tk.StringVar(value="Todos los estados")
            self.filtro_local = tk.StringVar(value="Todos los locales")
            self.filtro_buscar = tk.StringVar(value="")

            ttk.Label(self.Frame_filtros, text="Estado:", font=("Segoe UI", 9, "bold")).pack(side="left", padx=(2, 4), pady=4)

            self.opciones_estado = [
                "Todos los estados",
                "⚠️ Solo las que faltan (Pendientes + En Proceso)",
                "🔴 Solo Pendientes (0% - Sin iniciar)",
                "🟡 Solo En Proceso (Incompletas)",
                "🟢 Solo Completadas (100%)",
                "⚪ Sin Bienes Asignados"
            ]
            self.cbx_estado = ttk.Combobox(
                self.Frame_filtros,
                textvariable=self.filtro_estado,
                values=self.opciones_estado,
                state="readonly",
                width=36
            )
            self.cbx_estado.current(0)
            self.cbx_estado.pack(side="left", padx=(0, 10), pady=4)
            self.cbx_estado.bind("<<ComboboxSelected>>", lambda e: self.aplicar_filtros_ubicacion())

            ttk.Label(self.Frame_filtros, text="Local:", font=("Segoe UI", 9, "bold")).pack(side="left", padx=(0, 4), pady=4)

            self.cbx_local = ttk.Combobox(
                self.Frame_filtros,
                textvariable=self.filtro_local,
                values=["Todos los locales"],
                state="readonly",
                width=22
            )
            self.cbx_local.current(0)
            self.cbx_local.pack(side="left", padx=(0, 10), pady=4)
            self.cbx_local.bind("<<ComboboxSelected>>", lambda e: self.aplicar_filtros_ubicacion())

            ttk.Label(self.Frame_filtros, text="Buscar:", font=("Segoe UI", 9, "bold")).pack(side="left", padx=(0, 4), pady=4)

            self.etr_buscar = ttk.Entry(self.Frame_filtros, textvariable=self.filtro_buscar, width=22, font=("Segoe UI", 9))
            self.etr_buscar.pack(side="left", padx=(0, 6), pady=4)
            self.etr_buscar.bind("<KeyRelease>", lambda e: self._debounce_filtro(self.aplicar_filtros_ubicacion))

            btn_limpiar = ttk.Button(
                self.Frame_filtros,
                text=" ✖ Limpiar" if not self.iconobor else " Limpiar",
                command=self.limpiar_filtros_ubicacion
            )
            if self.iconobor:
                btn_limpiar.config(image=self.iconobor, compound="left")
            btn_limpiar.pack(side="left", padx=(0, 8), pady=4)

            btn_pdf = ttk.Button(
                self.Frame_filtros,
                text=" 📄 Exportar PDF" if not self.iconopdf else " Exportar PDF",
                command=self.generar_pdf
            )
            if self.iconopdf:
                btn_pdf.config(image=self.iconopdf, compound="left")
            btn_pdf.pack(side="right", padx=(4, 2), pady=4)

            btn_excel = ttk.Button(
                self.Frame_filtros,
                text=" 📊 Exportar Excel" if not self.iconoxls else " Exportar Excel",
                command=self.exportar_datos
            )
            if self.iconoxls:
                btn_excel.config(image=self.iconoxls, compound="left")
            btn_excel.pack(side="right", padx=4, pady=4)

        else:
            # Filtros estándar para valor in (2, 3, 4)
            self.crit = tk.StringVar()
            self.camp = tk.StringVar()

            ttk.Label(self.Frame_filtros, text="Criterio:", font=("Segoe UI", 9, "bold")).pack(side="left", padx=(4, 4), pady=4)
            self.cbxCri = ttk.Combobox(self.Frame_filtros, textvariable=self.crit, state="readonly", width=24)
            self.cbxCri.pack(side="left", padx=(0, 10), pady=4)

            ttk.Label(self.Frame_filtros, text="Buscar:", font=("Segoe UI", 9, "bold")).pack(side="left", padx=(0, 4), pady=4)
            etrCrit = ttk.Entry(self.Frame_filtros, textvariable=self.camp, width=28, font=("Segoe UI", 9))
            etrCrit.pack(side="left", padx=(0, 6), pady=4)
            etrCrit.bind("<KeyRelease>", lambda e: self._debounce_filtro(self.filtrar_general))
            etrCrit.bind("<Return>", lambda e: self.filtrar_general())

            btnCrit = ttk.Button(
                self.Frame_filtros,
                text=" 🔍 Filtrar" if not self.iconobus else " Filtrar",
                command=self.filtrar_general
            )
            if self.iconobus:
                btnCrit.config(image=self.iconobus, compound="left")
            btnCrit.pack(side="left", padx=4, pady=4)

            btnLimpiarGen = ttk.Button(
                self.Frame_filtros,
                text=" ✖ Limpiar" if not self.iconobor else " Limpiar",
                command=self.limpiar_filtros_general
            )
            if self.iconobor:
                btnLimpiarGen.config(image=self.iconobor, compound="left")
            btnLimpiarGen.pack(side="left", padx=4, pady=4)

            btnPdf = ttk.Button(
                self.Frame_filtros,
                text=" 📄 Exportar PDF" if not self.iconopdf else " Exportar PDF",
                command=self.generar_pdf
            )
            if self.iconopdf:
                btnPdf.config(image=self.iconopdf, compound="left")
            btnPdf.pack(side="right", padx=(4, 2), pady=4)

            btnCsv = ttk.Button(
                self.Frame_filtros,
                text=" 📊 Exportar Excel" if not self.iconoxls else " Exportar Excel",
                command=self.exportar_datos
            )
            if self.iconoxls:
                btnCsv.config(image=self.iconoxls, compound="left")
            btnCsv.pack(side="right", padx=4, pady=4)

    def seleccionar_kpi(self, estado):
        """Acción rápida al hacer clic en las tarjetas superiores de KPI."""
        if self.valor != 1:
            return
        if estado == "TODOS":
            self.cbx_estado.current(0)
        elif estado == "PENDIENTE":
            self.cbx_estado.current(2)  # Solo Pendientes
        elif estado == "EN PROCESO":
            self.cbx_estado.current(3)  # Solo En Proceso
        elif estado == "COMPLETADA":
            self.cbx_estado.current(4)  # Solo Completadas
        self.aplicar_filtros_ubicacion()

    def limpiar_filtros_ubicacion(self):
        """Restablece los filtros a su estado inicial."""
        self.filtro_estado.set("Todos los estados")
        self.cbx_estado.current(0)
        self.filtro_local.set("Todos los locales")
        self.cbx_local.current(0)
        self.filtro_buscar.set("")
        self.aplicar_filtros_ubicacion()

    def _debounce_filtro(self, callback, delay_ms=140):
        """Agrupa pulsaciones rápidas de teclado para evitar reconstruir la tabla en cada tecla."""
        if self._debounce_job is not None:
            try:
                self.after_cancel(self._debounce_job)
            except Exception:
                pass
        self._debounce_job = self.after(delay_ms, callback)

    def limpiar_filtros_general(self):
        """Restablece el filtro en análisis 2, 3 y 4 desde memoria sin reconsultar SQLite."""
        self.camp.set("")
        self.filtrar_general()

    # -------------------------------------------------------------------------
    # CONFIGURACIÓN DE TABLA (TREEVIEW)
    # -------------------------------------------------------------------------
    def tree_view(self):
        cab = []
        if self.valor == 1:
            self.arc = "ANÁLISIS POR UBICACIÓN "
            self.lista = [
                'Acta', 'Local', 'Área', 'Oficina',
                'Total\nBienes', 'Total\nInventariados', 'Total\nFaltantes',
                'Total\nSobrantes', '%\nAvance', 'Estado'
            ]
            self.lista_cabecera = [
                'Acta', 'Local', 'Área', 'Oficina',
                'Total Bienes', 'Total Inventariados', 'Total Faltantes',
                'Total Sobrantes', '% Avance', 'Estado'
            ]
            self.colWidths = [35, 120, 120, 140, 55, 60, 55, 55, 55, 65]
            self.orientacion = 0
            self.columna = 4

            for i in range(1, len(self.lista_cabecera) + 1):
                cab.append(i)

            self.tree = ttk.Treeview(self.Frame2, columns=cab, show="headings", style="Analisis.Treeview")
            for i, val in enumerate(self.lista_cabecera, start=1):
                self.tree.heading(i, text=val, command=lambda c=i: sort_by(self.tree, c, False), anchor="center")

            self.tree.column(1,  width=55,  stretch=False, anchor="center")
            self.tree.column(2,  width=125, stretch=False, anchor="w")
            self.tree.column(3,  width=135, stretch=False, anchor="w")
            self.tree.column(4,  width=190, stretch=True,  anchor="w")
            self.tree.column(5,  width=105, anchor="center", stretch=False)
            self.tree.column(6,  width=130, anchor="center", stretch=False)
            self.tree.column(7,  width=110, anchor="center", stretch=False)
            self.tree.column(8,  width=110, anchor="center", stretch=False)
            self.tree.column(9,  width=85,  anchor="center", stretch=False)
            self.tree.column(10, width=110, anchor="center", stretch=False)

        elif self.valor == 2:
            self.arc = "ANÁLISIS POR CUENTA CONTABLE "
            self.lista = [
                'Cuenta', 'SubCuenta', 'Denominación', 'Registro\nPatrimonial\nValor',
                'Total\nBienes', 'Resultado\nde Inventario\nValor', 'Total\nInventariados',
                'Valor\nFaltantes', 'Total\nFaltantes'
            ]
            self.lista_cabecera = [
                'Cuenta', 'SubCuenta', 'Denominación', 'Valor Patrimonial',
                'Total Bienes', 'Valor Inventariado', 'Total Inventariados',
                'Valor Faltantes', 'Total Faltantes'
            ]
            self.colWidths = [55, 70, 180, 75, 65, 75, 65, 75, 65]
            self.orientacion = 0
            self.columna = 3
            for i in range(1, len(self.lista_cabecera) + 1):
                cab.append(i)

            self.tree = ttk.Treeview(self.Frame2, columns=cab, show="headings", style="Analisis.Treeview")
            for i, val in enumerate(self.lista_cabecera, start=1):
                self.tree.heading(i, text=val, command=lambda c=i: sort_by(self.tree, c, False), anchor="center")

            self.tree.column(1, width=70,  stretch=False, anchor="center")
            self.tree.column(2, width=95,  stretch=False, anchor="center")
            self.tree.column(3, width=320, stretch=True,  anchor="w")
            self.tree.column(4, width=125, stretch=False, anchor="e")
            self.tree.column(5, width=105, stretch=False, anchor="center")
            self.tree.column(6, width=125, stretch=False, anchor="e")
            self.tree.column(7, width=130, stretch=False, anchor="center")
            self.tree.column(8, width=115, stretch=False, anchor="e")
            self.tree.column(9, width=110, stretch=False, anchor="center")

        elif self.valor == 3:
            self.arc = "ANÁLISIS POR BIEN "
            self.lista = [
                'Denominación', 'Registro\nPatrimonial\nValor',
                'Total\nBienes', 'Resultado\nde Inventario\nValor', 'Total\nInventariados',
                'Valor\nFaltantes', 'Total\nFaltantes'
            ]
            self.lista_cabecera = [
                'Denominación', 'Valor Patrimonial',
                'Total Bienes', 'Valor Inventariado', 'Total Inventariados',
                'Valor Faltantes', 'Total Faltantes'
            ]
            self.colWidths = [160, 60, 60, 60, 60, 60, 60]
            self.orientacion = 1
            self.columna = 1
            for i in range(1, len(self.lista_cabecera) + 1):
                cab.append(i)

            self.tree = ttk.Treeview(self.Frame2, columns=cab, show="headings", style="Analisis.Treeview")
            for i, val in enumerate(self.lista_cabecera, start=1):
                self.tree.heading(i, text=val, command=lambda c=i: sort_by(self.tree, c, False), anchor="center")

            self.tree.column(1, width=380, stretch=True,  anchor="w")
            self.tree.column(2, width=125, stretch=False, anchor="e")
            self.tree.column(3, width=105, stretch=False, anchor="center")
            self.tree.column(4, width=125, stretch=False, anchor="e")
            self.tree.column(5, width=130, stretch=False, anchor="center")
            self.tree.column(6, width=115, stretch=False, anchor="e")
            self.tree.column(7, width=110, stretch=False, anchor="center")

        elif self.valor == 4:
            self.arc = "ANÁLISIS POR USUARIO "
            self.listaT = ['Usuario', 'Local', 'Área', 'Oficina', 'Total Bienes', 'Total Inventariados', 'Total Faltantes', 'Total Sobrantes']
            self.lista_cabecera = self.listaT
            self.lista = ['Usuario', 'Ubicación', 'Total\nBienes', 'Total\nInventariados', 'Total\nFaltantes', 'Total\nSobrantes']
            self.colWidths = [150, 300, 60, 60, 60, 60]
            self.orientacion = 0
            self.columna = 2
            for i in range(1, len(self.listaT) + 1):
                cab.append(i)

            self.tree = ttk.Treeview(self.Frame2, columns=cab, show="headings", style="Analisis.Treeview")
            for i, val in enumerate(self.listaT, start=1):
                self.tree.heading(i, text=val, command=lambda c=i: sort_by(self.tree, c, False), anchor="center")

            self.tree.column(1, width=180, stretch=False, anchor="w")
            self.tree.column(2, width=125, stretch=False, anchor="w")
            self.tree.column(3, width=135, stretch=False, anchor="w")
            self.tree.column(4, width=170, stretch=True,  anchor="w")
            self.tree.column(5, width=105, anchor="center", stretch=False)
            self.tree.column(6, width=130, anchor="center", stretch=False)
            self.tree.column(7, width=110, anchor="center", stretch=False)
            self.tree.column(8, width=110, anchor="center", stretch=False)

        # Poblar valores para combo criterio en opciones 2, 3, 4
        if self.valor != 1 and hasattr(self, 'cbxCri'):
            opciones_limpias = [c.replace('\n', ' ') for c in self.lista_cabecera]
            self.cbxCri.configure(values=opciones_limpias)
            if opciones_limpias:
                self.cbxCri.current(0)

        # Configurar tags de fila y colores semánticos
        self.tree.tag_configure('odd',        background='#ffffff')
        self.tree.tag_configure('even',       background='#f8fafc')
        self.tree.tag_configure('pendiente',  foreground='#b91c1c')
        self.tree.tag_configure('proceso',    foreground='#b45309')
        self.tree.tag_configure('completada', foreground='#15803d')
        self.tree.tag_configure('sin_bienes', foreground='#64748b')
        self.tree.tag_configure('totales',    background='#e2e8f0', foreground='#0f172a', font=('Segoe UI', 9, 'bold'))

        # Scrollbars
        self.tree.grid(column=0, row=0, sticky="nsew")
        scrollbarV = ttk.Scrollbar(self.Frame2, orient=tk.VERTICAL, command=self.tree.yview)
        scrollbarH = ttk.Scrollbar(self.Frame2, orient=tk.HORIZONTAL, command=self.tree.xview)
        self.tree.configure(yscroll=scrollbarV.set, xscroll=scrollbarH.set)
        scrollbarV.grid(column=1, row=0, sticky="ns")
        scrollbarH.grid(column=0, row=1, sticky="ew")

    # -------------------------------------------------------------------------
    # PROCESAMIENTO DE DATOS Y CONSULTAS (ASÍNCRONO Y EN LOTES FLUIDOS)
    # -------------------------------------------------------------------------
    def _actualizar_barra_resumen(self, bloques_resumen):
        """
        Actualiza la barra fija inferior de 'Resumen de Totales' con etiquetas explícitas:
        `bloques_resumen` = lista de tuplas `(etiqueta, valor_texto, color_fg)`.
        """
        if not hasattr(self, "resumen_items_frame") or not self.winfo_exists():
            return
        for child in self.resumen_items_frame.winfo_children():
            child.destroy()

        tk.Label(
            self.resumen_items_frame,
            text="∑ RESUMEN DE TOTALES:",
            bg="#f1f5f9",
            fg="#0f172a",
            font=("Segoe UI", 9, "bold"),
        ).pack(side="left", padx=(0, 12))

        for idx, (etiqueta, valor_txt, fg_color) in enumerate(bloques_resumen):
            if idx > 0:
                tk.Label(
                    self.resumen_items_frame,
                    text="|",
                    bg="#f1f5f9",
                    fg="#cbd5e1",
                    font=("Segoe UI", 9, "bold"),
                ).pack(side="left", padx=8)

            item_f = tk.Frame(self.resumen_items_frame, bg="#f1f5f9")
            item_f.pack(side="left")

            tk.Label(
                item_f,
                text=f"{etiqueta}: ",
                bg="#f1f5f9",
                fg="#475569",
                font=("Segoe UI", 9),
            ).pack(side="left")

            tk.Label(
                item_f,
                text=valor_txt,
                bg="#f1f5f9",
                fg=fg_color,
                font=("Segoe UI", 9, "bold"),
            ).pack(side="left")

    def _limpiar_tree_rapido(self):
        """Limpia todas las filas del Treeview en una sola instrucción Tcl."""
        children = self.tree.get_children()
        if children:
            self.tree.delete(*children)

    def _insertar_lotes_tree(self, filas_con_tags, fila_totales=None):
        """Inserta filas en el Treeview por bloques para mantener la interfaz fluida en todo momento."""
        self._render_token += 1
        token_actual = self._render_token
        self._limpiar_tree_rapido()
        total_filas = len(filas_con_tags)

        def _insertar_bloque(inicio=0):
            if token_actual != self._render_token or not self.winfo_exists():
                return
            fin = min(inicio + _RENDER_CHUNK_SIZE, total_filas)
            tree_insert = self.tree.insert
            for idx in range(inicio, fin):
                vals, tags = filas_con_tags[idx]
                tree_insert('', tk.END, values=vals, tags=tags)

            if fin < total_filas:
                self.after(1, _insertar_bloque, fin)
            elif fila_totales is not None:
                tree_insert('', tk.END, values=fila_totales, tags=('totales',))

        _insertar_bloque(0)

    def realizar_query(self):
        """Consulta la base de datos en un hilo en segundo plano sin bloquear la ventana."""
        if self._query_lock:
            return
        self._query_lock = True
        self.lbl_status.config(text="⏳ Consultando y procesando datos...")

        valor_actual = self.valor

        def _worker():
            try:
                registros = analisis_1(valor_actual) or []
            except Exception as e:
                print(f"Error en consulta de análisis: {e}")
                registros = []

            if not self.winfo_exists():
                self._query_lock = False
                return

            if valor_actual == 1:
                paquete = self._preparar_datos_ubicacion_worker(registros)
                self.after(0, self._aplicar_paquete_ubicacion, paquete)
            else:
                paquete = self._preparar_datos_generales_worker(valor_actual, registros)
                self.after(0, self._aplicar_paquete_generales, paquete)

        threading.Thread(target=_worker, daemon=True).start()

    def _preparar_datos_ubicacion_worker(self, registros):
        """Preprocesa en segundo plano estados, porcentajes, KPIs y textos de búsqueda."""
        datos_ubicacion = []
        locales_set = set()

        total_bienes_global = 0
        total_inv_global = 0
        total_falt_global = 0
        total_sobr_global = 0

        count_pend = 0
        count_proc = 0
        count_comp = 0
        count_sin = 0

        for row in registros:
            acta = str(row[0] or '').strip()
            local = str(row[1] or '').strip()
            area = str(row[2] or '').strip()
            oficina = str(row[3] or '').strip()

            tb = int(row[4] or 0)
            ti = int(row[5] or 0)
            tf = int(row[6] or 0)
            ts = int(row[7] or 0)

            if local:
                locales_set.add(local)

            total_bienes_global += tb
            total_inv_global += ti
            total_falt_global += tf
            total_sobr_global += ts

            if tb > 0:
                pct = round((ti / tb) * 100.0, 1)
            else:
                pct = 100.0 if ti > 0 else 0.0

            if tb == 0 and ti == 0:
                estado = "SIN BIENES"
                tag = "sin_bienes"
                count_sin += 1
            elif ti == 0:
                estado = "PENDIENTE"
                tag = "pendiente"
                count_pend += 1
            elif tf == 0 and ti >= tb:
                estado = "COMPLETADA"
                tag = "completada"
                count_comp += 1
            else:
                estado = "EN PROCESO"
                tag = "proceso"
                count_proc += 1

            pct_str = f"{pct:.1f}%"
            datos_ubicacion.append({
                "acta": acta,
                "local": local,
                "area": area,
                "oficina": oficina,
                "search_blob": f"{acta} {local} {area} {oficina}".lower(),
                "tb": tb,
                "ti": ti,
                "tf": tf,
                "ts": ts,
                "pct": pct,
                "pct_str": pct_str,
                "estado": estado,
                "tag": tag,
                "values": [acta, local, area, oficina, tb, ti, tf, ts, pct_str, estado]
            })

        return {
            "datos_ubicacion": datos_ubicacion,
            "locales_ordenados": ["Todos los locales"] + sorted(locales_set),
            "total_bienes_global": total_bienes_global,
            "total_inv_global": total_inv_global,
            "count_pend": count_pend,
            "count_proc": count_proc,
            "count_comp": count_comp,
        }

    def _aplicar_paquete_ubicacion(self, paquete):
        """Actualiza los widgets de KPIs y aplica los filtros en el hilo principal."""
        self._query_lock = False
        if not self.winfo_exists():
            return

        self.datos_ubicacion = paquete["datos_ubicacion"]
        if hasattr(self, 'cbx_local'):
            self.cbx_local.configure(values=paquete["locales_ordenados"])

        if hasattr(self, 'kpi_cards'):
            total_oficinas = len(self.datos_ubicacion)
            tb_g = paquete["total_bienes_global"]
            ti_g = paquete["total_inv_global"]
            pct_global = (ti_g / tb_g * 100.0) if tb_g > 0 else 0.0

            self.kpi_cards["total"]["val"].config(text=str(total_oficinas))
            self.kpi_cards["total"]["sub"].config(text=f"{tb_g} bienes reg.")

            self.kpi_cards["pendientes"]["val"].config(text=str(paquete["count_pend"]))
            self.kpi_cards["pendientes"]["sub"].config(text="0% avance")

            self.kpi_cards["proceso"]["val"].config(text=str(paquete["count_proc"]))
            self.kpi_cards["proceso"]["sub"].config(text="Con faltantes")

            self.kpi_cards["completadas"]["val"].config(text=str(paquete["count_comp"]))
            self.kpi_cards["completadas"]["sub"].config(text="100% avance")

            self.kpi_cards["avance"]["val"].config(text=f"{pct_global:.1f}%")
            self.kpi_cards["avance"]["sub"].config(text=f"{ti_g} / {tb_g} bienes")

        self.aplicar_filtros_ubicacion()

    def aplicar_filtros_ubicacion(self):
        """Filtra en memoria y renderiza en lotes fluidos las filas de ubicación."""
        estado_filtro = self.filtro_estado.get()
        local_filtro = self.filtro_local.get()
        texto_filtro = self.filtro_buscar.get().strip().lower()

        filtrar_faltan = "Solo las que faltan" in estado_filtro
        filtrar_pend = "Solo Pendientes" in estado_filtro
        filtrar_proc = "Solo En Proceso" in estado_filtro
        filtrar_comp = "Solo Completadas" in estado_filtro
        filtrar_sin = "Sin Bienes" in estado_filtro
        filtrar_local = bool(local_filtro and local_filtro != "Todos los locales")

        filas_para_tree = []
        sum_tb = 0
        sum_ti = 0
        sum_tf = 0
        sum_ts = 0

        visibles_pend = 0
        visibles_proc = 0
        visibles_comp = 0

        for item in self.datos_ubicacion:
            est = item["estado"]
            if filtrar_faltan:
                if est not in ("PENDIENTE", "EN PROCESO"):
                    continue
            elif filtrar_pend:
                if est != "PENDIENTE":
                    continue
            elif filtrar_proc:
                if est != "EN PROCESO":
                    continue
            elif filtrar_comp:
                if est != "COMPLETADA":
                    continue
            elif filtrar_sin:
                if est != "SIN BIENES":
                    continue

            if filtrar_local and item["local"] != local_filtro:
                continue

            if texto_filtro and texto_filtro not in item["search_blob"]:
                continue

            sum_tb += item["tb"]
            sum_ti += item["ti"]
            sum_tf += item["tf"]
            sum_ts += item["ts"]

            if est == "PENDIENTE":
                visibles_pend += 1
            elif est == "EN PROCESO":
                visibles_proc += 1
            elif est == "COMPLETADA":
                visibles_comp += 1

            row_bg = "odd" if (len(filas_para_tree) % 2 == 0) else "even"
            filas_para_tree.append((item["values"], (row_bg, item["tag"])))

        pct_visible = (sum_ti / sum_tb * 100.0) if sum_tb > 0 else 0.0
        n_ofi_visibles = len(filas_para_tree)
        fila_totales = [
            '∑ TOTALES',
            f"{n_ofi_visibles} oficinas",
            '',
            'Suma total de bienes en las oficinas listadas:',
            f"{sum_tb:,} reg.",
            f"{sum_ti:,} inv.",
            f"{sum_tf:,} falt.",
            f"{sum_ts:,} sobr.",
            f"{pct_visible:.1f}%",
            ''
        ]
        self._insertar_lotes_tree(filas_para_tree, fila_totales)

        self._actualizar_barra_resumen([
            ("Oficinas listadas", f"{n_ofi_visibles}", "#0f172a"),
            ("Total Bienes Registrados (Acta Ant.)", f"{sum_tb:,} bienes", "#1e40af"),
            ("Total Bienes Inventariados", f"{sum_ti:,} bienes", "#15803d"),
            ("Total Bienes Faltantes", f"{sum_tf:,} bienes", "#b91c1c"),
            ("Total Bienes Sobrantes", f"{sum_ts:,} bienes", "#b45309"),
            ("Avance Global", f"{pct_visible:.1f}%", "#0f172a"),
        ])

        total_ofi = len(self.datos_ubicacion)
        self.lbl_chip.config(text=f"🏢  {n_ofi_visibles} / {total_ofi} oficinas")
        self.lbl_status.config(
            text=f"🔴 Oficinas sin iniciar: {visibles_pend}   |   "
                 f"🟡 Oficinas en proceso: {visibles_proc}   |   "
                 f"🟢 Oficinas completadas: {visibles_comp}   |   "
                 f"💡 Doble clic en una fila para ver el detalle de bienes"
        )

    def _calcular_totales_generales(self, filas):
        """Calcula la fila de totales explícita y los bloques del resumen para análisis 2, 3 y 4."""
        n_filas = len(filas)

        if self.valor == 2:
            total_01 = sum(float(str(r[3]).replace(',', '')) for r in filas)
            total_02 = sum(int(r[4] or 0) for r in filas)
            total_03 = sum(float(str(r[5]).replace(',', '')) for r in filas)
            total_04 = sum(int(r[6] or 0) for r in filas)
            total_05 = sum(float(str(r[7]).replace(',', '')) for r in filas)
            total_06 = sum(int(r[8] or 0) for r in filas)

            fila_totales = [
                '∑ TOTALES',
                f"{n_filas} cuentas",
                'TOTAL CONSOLIDADO DE CUENTAS CONTABLES:',
                f"S/ {total_01:,.2f}",
                f"{total_02:,} reg.",
                f"S/ {total_03:,.2f}",
                f"{total_04:,} inv.",
                f"S/ {total_05:,.2f}",
                f"{total_06:,} falt.",
            ]
            bloques = [
                ("Cuentas Contables", f"{n_filas}", "#0f172a"),
                ("Patrimonio Registrado", f"S/ {total_01:,.2f} ({total_02:,} bienes)", "#1e40af"),
                ("Resultado Inventariado", f"S/ {total_03:,.2f} ({total_04:,} bienes)", "#15803d"),
                ("Total Faltantes", f"S/ {total_05:,.2f} ({total_06:,} bienes)", "#b91c1c"),
            ]
            return fila_totales, bloques

        elif self.valor == 3:
            total_01 = sum(float(str(r[1]).replace(',', '')) for r in filas)
            total_02 = sum(int(r[2] or 0) for r in filas)
            total_03 = sum(float(str(r[3]).replace(',', '')) for r in filas)
            total_04 = sum(int(r[4] or 0) for r in filas)
            total_05 = sum(float(str(r[5]).replace(',', '')) for r in filas)
            total_06 = sum(int(r[6] or 0) for r in filas)

            fila_totales = [
                f"∑ TOTAL CONSOLIDADO ({n_filas} denominaciones de bienes):",
                f"S/ {total_01:,.2f}",
                f"{total_02:,} reg.",
                f"S/ {total_03:,.2f}",
                f"{total_04:,} inv.",
                f"S/ {total_05:,.2f}",
                f"{total_06:,} falt.",
            ]
            bloques = [
                ("Denominaciones", f"{n_filas} tipos de bien", "#0f172a"),
                ("Valor Patrimonial Registrado", f"S/ {total_01:,.2f} ({total_02:,} bienes)", "#1e40af"),
                ("Valor Inventariado", f"S/ {total_03:,.2f} ({total_04:,} bienes)", "#15803d"),
                ("Valor Faltantes", f"S/ {total_05:,.2f} ({total_06:,} bienes)", "#b91c1c"),
            ]
            return fila_totales, bloques

        else:  # self.valor == 4
            total_bienes = sum(int(r[4] or 0) for r in filas)
            total_inventariados = sum(int(r[5] or 0) for r in filas)
            total_faltantes = sum(int(r[6] or 0) for r in filas)
            total_sobrantes = sum(int(r[7] or 0) for r in filas)

            fila_totales = [
                '∑ TOTALES',
                f"{n_filas} usuarios",
                '',
                'Suma total de bienes de los responsables listados:',
                f"{total_bienes:,} reg.",
                f"{total_inventariados:,} inv.",
                f"{total_faltantes:,} falt.",
                f"{total_sobrantes:,} sobr.",
            ]
            bloques = [
                ("Responsables listados", f"{n_filas}", "#0f172a"),
                ("Total Bienes Asignados (Acta Ant.)", f"{total_bienes:,} bienes", "#1e40af"),
                ("Total Bienes Inventariados", f"{total_inventariados:,} bienes", "#15803d"),
                ("Total Bienes Faltantes", f"{total_faltantes:,} bienes", "#b91c1c"),
                ("Total Bienes Sobrantes", f"{total_sobrantes:,} bienes", "#b45309"),
            ]
            return fila_totales, bloques

    def _preparar_datos_generales_worker(self, valor_actual, registros):
        """Formatea las filas y calcula los totales en Python sin cruzar Tcl/Tk."""
        datos_generales = []
        filas_con_tags = []

        if valor_actual == 2:
            for idx, row in enumerate(registros, 1):
                v_pat = float(row[3] or 0)
                c_pat = int(row[4] or 0)
                v_inv = float(row[5] or 0)
                c_inv = int(row[6] or 0)
                v_fal = float(row[7] or 0)
                c_fal = int(row[8] or 0)

                valores = [
                    row[0], row[1], row[2],
                    f"{v_pat:,.2f}", c_pat,
                    f"{v_inv:,.2f}", c_inv,
                    f"{v_fal:,.2f}", c_fal,
                ]
                datos_generales.append(valores)
                tag = "odd" if idx % 2 == 1 else "even"
                filas_con_tags.append((valores, (tag,)))

        elif valor_actual == 3:
            for idx, row in enumerate(registros, 1):
                v_pat = float(row[1] or 0)
                c_pat = int(row[2] or 0)
                v_inv = float(row[3] or 0)
                c_inv = int(row[4] or 0)
                v_fal = float(row[5] or 0)
                c_fal = int(row[6] or 0)

                valores = [
                    row[0],
                    f"{v_pat:,.2f}", c_pat,
                    f"{v_inv:,.2f}", c_inv,
                    f"{v_fal:,.2f}", c_fal,
                ]
                datos_generales.append(valores)
                tag = "odd" if idx % 2 == 1 else "even"
                filas_con_tags.append((valores, (tag,)))

        elif valor_actual == 4:
            for idx, row in enumerate(registros, 1):
                tb = int(row[4] or 0)
                ti = int(row[5] or 0)
                tf = int(row[6] or 0)
                ts = int(row[7] or 0)

                valores = [row[0], row[1], row[2], row[3], tb, ti, tf, ts]
                datos_generales.append(valores)
                tag = "odd" if idx % 2 == 1 else "even"
                filas_con_tags.append((valores, (tag,)))

        fila_totales, bloques_resumen = self._calcular_totales_generales(datos_generales)
        return {
            "datos_generales": datos_generales,
            "filas_con_tags": filas_con_tags,
            "fila_totales": fila_totales,
            "bloques_resumen": bloques_resumen,
        }

    def _aplicar_paquete_generales(self, paquete):
        """Renderiza en el hilo principal los datos procesados para análisis 2, 3 y 4."""
        self._query_lock = False
        if not self.winfo_exists():
            return

        self.datos_generales = paquete["datos_generales"]
        self.totales_generales = paquete["fila_totales"]
        self.bloques_resumen_generales = paquete["bloques_resumen"]
        self._insertar_lotes_tree(paquete["filas_con_tags"], self.totales_generales)
        self._actualizar_barra_resumen(self.bloques_resumen_generales)

        self.lbl_chip.config(text=f"📊  {len(self.datos_generales)} registros")
        self.lbl_status.config(
            text="💡 Doble clic en cualquier fila para inspeccionar el detalle de bienes"
        )

    def filtrar_general(self):
        """Filtra registros en memoria para análisis 2, 3 y 4 y recalcula los totales del filtro."""
        columna = self.crit.get().strip()
        valor = self.camp.get().strip().lower()

        if not valor:
            filas_todas = [
                (row, ("odd" if idx % 2 == 1 else "even",))
                for idx, row in enumerate(self.datos_generales, 1)
            ]
            self._insertar_lotes_tree(filas_todas, self.totales_generales)
            self._actualizar_barra_resumen(getattr(self, "bloques_resumen_generales", []))
            self.lbl_chip.config(text=f"📊  {len(self.datos_generales)} registros")
            self.lbl_status.config(
                text="💡 Doble clic en cualquier fila para inspeccionar el detalle de bienes"
            )
            return

        lista_ref = getattr(self, "lista_cabecera", self.listaT if self.valor == 4 else self.lista)
        lista_limpia = [c.replace('\n', ' ') for c in lista_ref]
        col_limpia = columna.replace('\n', ' ')

        try:
            col_idx = lista_limpia.index(col_limpia) if col_limpia in lista_limpia else 0
        except Exception:
            col_idx = 0

        coincidentes = []
        filas_filtradas = []
        for row in self.datos_generales:
            val_col = str(row[col_idx]).lower() if col_idx < len(row) else ''
            if valor in val_col:
                coincidentes.append(row)
                tag = "odd" if (len(filas_filtradas) % 2 == 0) else "even"
                filas_filtradas.append((row, (tag,)))

        fila_totales_filtro, bloques_filtro = self._calcular_totales_generales(coincidentes)
        self._insertar_lotes_tree(filas_filtradas, fila_totales_filtro)
        self._actualizar_barra_resumen(bloques_filtro)
        self.lbl_chip.config(text=f"📊  {len(filas_filtradas)} / {len(self.datos_generales)} registros")
        self.lbl_status.config(
            text=f"Filtro activo por '{col_limpia}': '{self.camp.get().strip()}'   |   💡 Doble clic en una fila para ver el detalle"
        )

    # -------------------------------------------------------------------------
    # EXPORTACIÓN Y DETALLE
    # -------------------------------------------------------------------------
    def generar_pdf(self):
        """Exporta el contenido de la tabla a formato PDF."""
        try:
            data = []
            for row_id in self.tree.get_children():
                row = list(self.tree.item(row_id)['values'])
                if self.valor == 4:
                    ubicacion = f"{row[1]} - {row[2]} - {row[3]}"
                    row[1] = ubicacion
                    row = [row[0]] + [row[1]] + row[4:]
                data.append(row)

            if not data:
                mb.showwarning("Atención", "No hay datos para exportar a PDF.", parent=self)
                return

            file_path = filedialog.askdirectory(initialdir='report_actas/reporte_analisis/', parent=self)
            if file_path:
                iniciar_reporte(data, file_path, self.colWidths, self.arc, self.lista, self.orientacion, self.columna)
                mb.showinfo(message="Reporte PDF exportado con éxito.", title="¡Atención!", parent=self)
        except Exception as e:
            mb.showerror(message=f"Ha ocurrido un error al exportar:\n{e}", title="Error", parent=self)
            print(str(e))
        self.focus_set()

    def exportar_datos(self):
        """Exporta el contenido de la tabla a un archivo Excel formateado."""
        datos = []
        for item in self.tree.get_children():
            values = list(self.tree.item(item, "values"))
            datos.append(values)

        if not datos:
            mb.showwarning("Atención", "No hay datos para exportar a Excel.", parent=self)
            return

        encabezados_limpios = [str(c).replace('\n', ' ') for c in self.lista]
        exportar_excel(self.arc.strip(), encabezados_limpios, datos)
        self.focus_set()

    def mostrar_datos(self, *args):
        """Abre la ventana de detalle de la oficina o elemento seleccionado."""
        curActa = self.tree.focus()
        if not curActa:
            return
        if 'totales' in self.tree.item(curActa, 'tags'):
            return
        vnb = self.tree.item(curActa)['values']
        if not vnb:
            return
        if str(vnb[0]).strip().upper().startswith(('TOTAL', '∑')):
            return

        # Para ubicación, vnb[0] es el número de acta/código de ubicación
        Window_d_analisis(acta=vnb[0], valor=vnb, analisis=self.valor)
