import os
import tkinter as tk
from datetime import datetime
from tkinter import ttk, PhotoImage, messagebox as mb

from reportes.faltantes import iniciar_reporte
from label.label_gen import build_label
from data.exp_excel import exportar_excel
from utils.order_utils import sort_by
from utils.helpers import resource_path
from db.conex import iniciar_conexion_sqlite
from db.query import (
    detalle_bienes,
    detalle_bienes_faltantes,
    buscar_criterio_acta_ant,
    registrar_codpat_test,
)


class Window_detalle(tk.Toplevel):
    def __init__(self, frame_app=None, root=None, acta=None, valor=None, user=None, team=None, *args, **kwargs):
        super().__init__(root)

        self.frame_app = frame_app
        self.root = root
        self.acta = str(acta).strip() if acta is not None else ""
        self.valor = valor if valor is not None else 1
        self.user = user
        self.team = team

        # Definir título según el tipo de consulta
        tipo_str = "Bienes Pendientes / Faltantes" if self.valor == 2 else "Bienes del Acta"
        acta_str = f" - Acta Nº {self.acta}" if self.acta else ""
        self.title(f"Detalle de {tipo_str}{acta_str} - AEC S.A.C.")

        # Tamaño y límites de ventana
        self.geometry("1200x700")
        self.minsize(980, 560)
        self.configure(bg="#f8fafc")

        # Configurar icono de ventana
        icon_path = resource_path(os.path.join("img", "favicon.ico"))
        if os.path.exists(icon_path):
            try:
                self.iconbitmap(icon_path)
            except Exception:
                pass

        # Cargar iconos de forma segura
        self.iconoxls = self._cargar_icono("img/excel.png")
        self.iconopdf = self._cargar_icono("img/pdf.png")
        self.iconodow = self._cargar_icono("img/descargas.png")
        self.iconobus = self._cargar_icono("img/buscar.png")

        # Variables de estado
        self.cb = tk.IntVar(value=0)
        self.crit = tk.StringVar(value="DenBien")
        self.camp = tk.StringVar()
        self.total_registros_var = tk.StringVar(value="0 bienes")
        self.ubicacion_info_var = tk.StringVar(value="")

        # Configurar estilos visuales
        self._configurar_estilos()

        # Construir interfaz
        self._crear_encabezado()
        self._crear_panel_kpis()
        self._crear_barra_herramientas()
        self._crear_tabla()

        # Cargar datos iniciales y métricas
        self.iniciar_filtro()

        # Centrar ventana
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

        style.configure(
            "DetalleTitle.TLabel",
            background="#ffffff",
            foreground="#0f172a",
            font=("Segoe UI", 12, "bold")
        )
        style.configure(
            "DetalleMeta.TLabel",
            background="#ffffff",
            foreground="#64748b",
            font=("Segoe UI", 9)
        )
        style.configure(
            "DetalleField.TLabel",
            background="#ffffff",
            foreground="#334155",
            font=("Segoe UI", 9, "bold")
        )

        style.configure(
            "DetalleAction.TButton",
            font=("Segoe UI", 9),
            padding=(8, 4)
        )
        style.configure(
            "DetalleSuccess.TButton",
            font=("Segoe UI", 9, "bold"),
            padding=(10, 5)
        )
        style.configure(
            "DetallePrimary.TButton",
            font=("Segoe UI", 9, "bold"),
            padding=(8, 4)
        )

        style.configure(
            "Detalle.Treeview",
            font=("Segoe UI", 9),
            rowheight=26,
            background="#ffffff",
            fieldbackground="#ffffff",
            bordercolor="#e2e8f0",
            borderwidth=1
        )
        style.configure(
            "Detalle.Treeview.Heading",
            font=("Segoe UI", 9, "bold"),
            background="#f1f5f9",
            foreground="#1e293b",
            padding=(5, 6)
        )
        style.map("Detalle.Treeview", background=[("selected", "#2563eb")], foreground=[("selected", "#ffffff")])

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

    def _crear_encabezado(self):
        """Crea la tarjeta superior con información contextual del Acta y su ubicación."""
        header_card = tk.Frame(self, bg="#ffffff", bd=1, relief="solid", highlightthickness=0)
        header_card.pack(fill="x", padx=12, pady=(10, 6))

        content = tk.Frame(header_card, bg="#ffffff")
        content.pack(fill="x", padx=16, pady=9)

        # Lado izquierdo: Título y Metadata
        left_box = tk.Frame(content, bg="#ffffff")
        left_box.pack(side="left", fill="y")

        title_row = tk.Frame(left_box, bg="#ffffff")
        title_row.pack(anchor="w")

        acta_txt = f"Acta Nº {self.acta}" if self.acta else "Acta General"
        lbl_acta = ttk.Label(title_row, text=f"📋 {acta_txt}", style="DetalleTitle.TLabel")
        lbl_acta.pack(side="left", padx=(0, 10))

        es_faltante = (self.valor == 2)
        badge_bg = "#fef3c7" if es_faltante else "#e0f2fe"
        badge_fg = "#b45309" if es_faltante else "#0369a1"
        badge_txt = "⚠️ Vista: Bienes Faltantes" if es_faltante else "📦 Vista: Todos los Bienes del Acta"

        self.badge_lbl = tk.Label(
            title_row,
            text=badge_txt,
            bg=badge_bg,
            fg=badge_fg,
            font=("Segoe UI", 9, "bold"),
            padx=8,
            pady=2,
            relief="flat"
        )
        self.badge_lbl.pack(side="left")

        # Subtítulo con ubicación y usuario
        lbl_ubi = ttk.Label(left_box, textvariable=self.ubicacion_info_var, style="DetalleMeta.TLabel")
        lbl_ubi.pack(anchor="w", pady=(3, 0))

        # Lado derecho: Contador en vista
        right_box = tk.Frame(content, bg="#ffffff")
        right_box.pack(side="right", fill="y")

        lbl_chip_tit = ttk.Label(right_box, text="Mostrando en tabla:", style="DetalleMeta.TLabel")
        lbl_chip_tit.pack(anchor="e")

        chip_box = tk.Frame(right_box, bg="#eff6ff", padx=10, pady=2, bd=1, relief="solid")
        chip_box.pack(anchor="e", pady=(2, 0))

        lbl_total = tk.Label(
            chip_box,
            textvariable=self.total_registros_var,
            bg="#eff6ff",
            fg="#1d4ed8",
            font=("Segoe UI", 10, "bold")
        )
        lbl_total.pack()

    def _crear_panel_kpis(self):
        """Crea las tarjetas superiores con Total Bienes, Total Inventariados, Total Faltantes, Total Sobrantes y Avance."""
        self.kpis_frame = tk.Frame(self, bg="#f8fafc")
        self.kpis_frame.pack(fill="x", padx=10, pady=(0, 6))

        self.kpi_widgets = {}
        tarjetas = [
            ("total_bienes",  "📦 Total Bienes (Acta Ant.)", "0", "Asignados a la oficina", "#ffffff", "#0f172a", lambda: self._cambiar_modo_vista(1)),
            ("inventariados", "✅ Total Inventariados",      "0", "0.0% de avance",         "#f0fdf4", "#166534", lambda: self._cambiar_modo_vista(1)),
            ("faltantes",     "⚠️ Total Faltantes",          "0", "Pendientes de ubicar",   "#fef2f2", "#991b1b", lambda: self._cambiar_modo_vista(2)),
            ("sobrantes",     "➕ Total Sobrantes",          "0", "Registrados en el acta", "#fffbeb", "#92400e", None),
            ("valor_vista",   "💰 Valor Total en Vista",     "S/ 0.00", "Suma de bienes listados", "#eff6ff", "#1e40af", None),
        ]

        for key, titulo, val_ini, sub_ini, bg_c, fg_c, cmd in tarjetas:
            cursor_type = "hand2" if cmd else "arrow"
            card = tk.Frame(self.kpis_frame, bg=bg_c, bd=1, relief="solid", padx=12, pady=6, cursor=cursor_type)
            card.pack(side="left", fill="both", expand=True, padx=3)

            lbl_t = tk.Label(card, text=titulo, bg=bg_c, fg=fg_c, font=("Segoe UI", 8, "bold"), anchor="w", cursor=cursor_type)
            lbl_t.pack(fill="x")

            lbl_v = tk.Label(card, text=val_ini, bg=bg_c, fg=fg_c, font=("Segoe UI", 14, "bold"), anchor="w", cursor=cursor_type)
            lbl_v.pack(fill="x", pady=(1, 1))

            lbl_s = tk.Label(card, text=sub_ini, bg=bg_c, fg=fg_c, font=("Segoe UI", 8), anchor="w", cursor=cursor_type)
            lbl_s.pack(fill="x")

            if cmd:
                for w in (card, lbl_t, lbl_v, lbl_s):
                    w.bind("<Button-1>", lambda _e, c=cmd: c())

            self.kpi_widgets[key] = {"val": lbl_v, "sub": lbl_s}

    def _cambiar_modo_vista(self, nuevo_valor: int):
        """Permite alternar entre ver Todos los Bienes del Acta (1) y Solo Faltantes (2) al hacer clic en los KPIs."""
        if self.valor == nuevo_valor:
            return
        self.valor = nuevo_valor
        es_faltante = (self.valor == 2)
        self.badge_lbl.configure(
            text="⚠️ Vista: Bienes Faltantes" if es_faltante else "📦 Vista: Todos los Bienes del Acta",
            bg="#fef3c7" if es_faltante else "#e0f2fe",
            fg="#b45309" if es_faltante else "#0369a1",
        )
        self.iniciar_filtro()

    def _crear_barra_herramientas(self):
        """Barra de búsqueda y botones de exportación/acción."""
        toolbar = tk.Frame(self, bg="#ffffff", bd=1, relief="solid")
        toolbar.pack(fill="x", padx=12, pady=(0, 8))

        inner = tk.Frame(toolbar, bg="#ffffff")
        inner.pack(fill="x", padx=12, pady=8)

        # ---- Sección de Filtro (Izquierda) ----
        filter_box = tk.Frame(inner, bg="#ffffff")
        filter_box.pack(side="left", fill="y")

        ttk.Label(filter_box, text="Criterio:", style="DetalleField.TLabel").pack(side="left", padx=(0, 6))

        cbxCri = ttk.Combobox(
            filter_box,
            textvariable=self.crit,
            state="readonly",
            values=['CodInt', 'CodPat', 'DenBien', 'Estado', 'Dimension', 'Marca',
                    'Modelo', 'Serie', 'Color', 'ValAdq', 'Obs'],
            width=13,
            font=("Segoe UI", 9)
        )
        cbxCri.pack(side="left", padx=(0, 8))

        etrCrit = ttk.Entry(filter_box, textvariable=self.camp, font=("Segoe UI", 9), width=22)
        etrCrit.pack(side="left", padx=(0, 6))
        etrCrit.bind("<Return>", lambda e: self.buscar_criterio())
        etrCrit.bind("<KeyRelease>", lambda e: self.buscar_criterio())

        btnBuscar = ttk.Button(
            filter_box,
            text=" Buscar",
            image=self.iconobus if self.iconobus else None,
            compound="left",
            style="DetallePrimary.TButton",
            command=self.buscar_criterio
        )
        btnBuscar.pack(side="left", padx=(0, 6))

        btnLimpiar = ttk.Button(
            filter_box,
            text="Limpiar",
            style="DetalleAction.TButton",
            command=self._limpiar_filtro
        )
        btnLimpiar.pack(side="left")

        # ---- Sección de Acciones (Derecha) ----
        actions_box = tk.Frame(inner, bg="#ffffff")
        actions_box.pack(side="right", fill="y")

        self.btnXls = ttk.Button(
            actions_box,
            text=" Exportar Excel",
            image=self.iconoxls if self.iconoxls else None,
            compound="left",
            style="DetalleAction.TButton",
            command=self.exportar_datos
        )
        self.btnXls.pack(side="left", padx=(0, 8))

        self.btnPdf = ttk.Button(
            actions_box,
            text=" Generar PDF",
            image=self.iconopdf if self.iconopdf else None,
            compound="left",
            style="DetalleAction.TButton",
            command=self.generar_pdf
        )
        self.btnPdf.pack(side="left", padx=(0, 8))

        if self.valor == 2:
            check_frame = tk.Frame(actions_box, bg="#ffffff")
            check_frame.pack(side="left", padx=(0, 10))

            self.checkB = ttk.Checkbutton(
                check_frame,
                text="Imprimir Etiquetas",
                variable=self.cb,
                onvalue=1,
                offvalue=0
            )
            self.checkB.pack(side="left")

            self.btnReg = ttk.Button(
                actions_box,
                text="✔️ Registrar Todo",
                style="DetalleSuccess.TButton",
                command=self.registrar
            )
            self.btnReg.pack(side="left")

    def _crear_tabla(self):
        """Contenedor de la tabla Treeview con scrollbars y barra de resumen de totales."""
        table_card = tk.Frame(self, bg="#ffffff", bd=1, relief="solid")
        table_card.pack(fill="both", expand=True, padx=12, pady=(0, 10))

        grid_frame = tk.Frame(table_card, bg="#ffffff")
        grid_frame.pack(fill="both", expand=True, padx=6, pady=6)
        grid_frame.rowconfigure(0, weight=1)
        grid_frame.columnconfigure(0, weight=1)

        self.lista = [
            'Item', 'Inv. Anterior', 'Inventario', 'Código Interno', 'Código Patrimonial', 'Denominación',
            'Estado', 'Dimensión', 'Marca', 'Modelo', 'Serie', 'Color', 'Valor', 'Obs'
        ]
        cab = tuple(range(1, 15))

        self.tree = ttk.Treeview(
            grid_frame,
            columns=cab,
            show='headings',
            style="Detalle.Treeview",
            selectmode="extended"
        )

        headers = [
            (1, 'Item', 50, "center"),
            (2, 'Inv. Anterior', 80, "center"),
            (3, 'Inventario', 80, "center"),
            (4, 'Cód. Interno', 85, "center"),
            (5, 'Cód. Patrimonial', 110, "center"),
            (6, 'Denominación del Bien', 280, "w"),
            (7, 'Estado', 65, "center"),
            (8, 'Dimensión', 85, "w"),
            (9, 'Marca', 90, "w"),
            (10, 'Modelo', 90, "w"),
            (11, 'Serie', 90, "w"),
            (12, 'Color', 85, "w"),
            (13, 'Valor Adq.', 85, "e"),
            (14, 'Observación', 110, "w"),
        ]

        for col_id, titulo, ancho, alineacion in headers:
            self.tree.heading(col_id, text=titulo, command=lambda c=col_id: sort_by(self.tree, c, False))
            self.tree.column(col_id, width=ancho, minwidth=40, stretch=(col_id == 6), anchor=alineacion)

        self.tree.tag_configure("evenrow", background="#ffffff")
        self.tree.tag_configure("oddrow", background="#f8fafc")
        self.tree.tag_configure("faltante_row", foreground="#b91c1c")
        self.tree.tag_configure("inventariado_row", foreground="#15803d")
        self.tree.tag_configure("totales", background="#e2e8f0", foreground="#0f172a", font=("Segoe UI", 9, "bold"))

        scrollbarV = ttk.Scrollbar(grid_frame, orient=tk.VERTICAL, command=self.tree.yview)
        scrollbarH = ttk.Scrollbar(grid_frame, orient=tk.HORIZONTAL, command=self.tree.xview)
        self.tree.configure(yscroll=scrollbarV.set, xscroll=scrollbarH.set)

        self.tree.grid(column=0, row=0, sticky="nsew")
        scrollbarV.grid(column=1, row=0, sticky="ns")
        scrollbarH.grid(column=0, row=1, sticky="ew")

        self.tree.bind("<Double-1>", self._on_doble_clic)

        # Barra inferior de resumen de totales + ayuda
        footer = tk.Frame(table_card, bg="#f1f5f9", bd=1, relief="solid")
        footer.pack(fill="x", side="bottom")

        self.lbl_resumen_totales = tk.Label(
            footer,
            text="∑ RESUMEN DEL ACTA: Cargando...",
            bg="#f1f5f9",
            fg="#0f172a",
            font=("Segoe UI", 9, "bold"),
            padx=12,
            pady=5,
            anchor="w"
        )
        self.lbl_resumen_totales.pack(side="left", fill="x", expand=True)

        lbl_tip = tk.Label(
            footer,
            text="💡 Doble clic en un bien para editar sus detalles | Clic en las tarjetas superiores para filtrar",
            bg="#f1f5f9",
            fg="#64748b",
            font=("Segoe UI", 8, "italic"),
            padx=10,
            pady=5
        )
        lbl_tip.pack(side="right")

    def _consultar_metricas_acta(self) -> dict:
        """Obtiene de forma rápida todos los totales del Acta desde SQLite."""
        metricas = {
            "local": "",
            "area": "",
            "oficina": "",
            "responsable": "",
            "total_bienes": 0,
            "total_inventariados": 0,
            "total_en_acta": 0,
            "total_faltantes": 0,
            "total_sobrantes": 0,
        }
        if not self.acta:
            return metricas

        conn = iniciar_conexion_sqlite()
        if not conn:
            return metricas
        try:
            cur = conn.cursor()
            cur.execute("""
                SELECT local, area, oficina,
                       TRIM(COALESCE(nombre, '') || ' ' || COALESCE(apellidoPat, '') || ' ' || COALESCE(apellidoMat, ''))
                FROM personal
                WHERE CAST(Acta AS TEXT) = ?
                LIMIT 1
            """, (self.acta,))
            p_row = cur.fetchone()
            if p_row:
                metricas["local"] = str(p_row[0] or "")
                metricas["area"] = str(p_row[1] or "")
                metricas["oficina"] = str(p_row[2] or "")
                metricas["responsable"] = str(p_row[3] or "")

            cur.execute("""
                SELECT
                    COUNT(*) AS tb,
                    SUM(CASE WHEN COALESCE(inventariado, 0) = 1 AND COALESCE(CAST(codigo_ubicacion_final AS TEXT), '') NOT IN ('', '0') THEN 1 ELSE 0 END) AS ti,
                    SUM(CASE WHEN COALESCE(inventariado, 0) = 0 OR COALESCE(CAST(codigo_ubicacion_final AS TEXT), '') IN ('', '0') THEN 1 ELSE 0 END) AS tf
                FROM inventory_records
                WHERE CAST(codigo_ubicacion_inicial AS TEXT) = ?
            """, (self.acta,))
            b_row = cur.fetchone()
            if b_row:
                metricas["total_bienes"] = int(b_row[0] or 0)
                metricas["total_inventariados"] = int(b_row[1] or 0)
                metricas["total_faltantes"] = int(b_row[2] or 0)

            cur.execute("""
                SELECT COUNT(*)
                FROM inventory_records
                WHERE COALESCE(inventariado, 0) = 1
                  AND CAST(codigo_ubicacion_final AS TEXT) = ?
            """, (self.acta,))
            inv_acta_row = cur.fetchone()
            if inv_acta_row:
                metricas["total_en_acta"] = int(inv_acta_row[0] or 0)

            cur.execute("""
                SELECT COUNT(*)
                FROM surplus
                WHERE CAST(codigo_ubicacion AS TEXT) = ?
            """, (self.acta,))
            s_row = cur.fetchone()
            if s_row:
                metricas["total_sobrantes"] = int(s_row[0] or 0)
        except Exception as e:
            print(f"Error consultando métricas de acta: {e}")
        finally:
            conn.close()
        return metricas

    def _actualizar_kpis_y_resumen(self, registros_mostrados):
        """Refresca las tarjetas KPI superiores y la barra inferior de totales."""
        m = self._consultar_metricas_acta()
        tb = m["total_bienes"]
        ti = m["total_inventariados"]
        t_acta = m["total_en_acta"]
        tf = m["total_faltantes"]
        ts = m["total_sobrantes"]
        pct = (ti / tb * 100.0) if tb > 0 else (100.0 if t_acta > 0 else 0.0)

        # Información de ubicación y responsable en el encabezado
        partes_ubi = [p for p in (m["local"], m["area"], m["oficina"]) if p]
        ubi_str = " - ".join(partes_ubi) if partes_ubi else "Ubicación General"
        resp_str = m["responsable"] or "Sin responsable asignado"
        usuario_str = self.user if self.user else "N/A"
        equipo_str = self.team if self.team else "N/A"
        self.ubicacion_info_var.set(
            f"🏢 {ubi_str}   |   👔 Resp.: {resp_str}   |   👤 Operador: {usuario_str} ({equipo_str})"
        )

        # Calcular suma de Valor Adq. de los registros en tabla
        suma_valor = 0.0
        for row in (registros_mostrados or []):
            try:
                suma_valor += float(str(row[11]).replace(",", ""))
            except Exception:
                pass

        n_mostrados = len(registros_mostrados) if registros_mostrados else 0

        if hasattr(self, "kpi_widgets"):
            self.kpi_widgets["total_bienes"]["val"].config(text=f"{tb:,}")
            self.kpi_widgets["total_bienes"]["sub"].config(text="Asignados (Acta Ant.)")

            self.kpi_widgets["inventariados"]["val"].config(text=f"{ti:,}")
            self.kpi_widgets["inventariados"]["sub"].config(text=f"{pct:.1f}% avance ({t_acta:,} en acta)")

            self.kpi_widgets["faltantes"]["val"].config(text=f"{tf:,}")
            self.kpi_widgets["faltantes"]["sub"].config(text="Pendientes de ubicar")

            self.kpi_widgets["sobrantes"]["val"].config(text=f"{ts:,}")
            self.kpi_widgets["sobrantes"]["sub"].config(text="Sobrantes en esta oficina")

            self.kpi_widgets["valor_vista"]["val"].config(text=f"S/ {suma_valor:,.2f}")
            self.kpi_widgets["valor_vista"]["sub"].config(text=f"En {n_mostrados:,} bienes listados")

        if hasattr(self, "lbl_resumen_totales"):
            self.lbl_resumen_totales.config(
                text=(
                    f"∑ TOTALES DEL ACTA Nº {self.acta}:   "
                    f"📦 Total Bienes: {tb:,}   |   "
                    f"✅ Total Inventariados: {ti:,} ({pct:.1f}%)   |   "
                    f"⚠️ Total Faltantes: {tf:,}   |   "
                    f"➕ Total Sobrantes: {ts:,}   |   "
                    f"💰 Valor en Vista: S/ {suma_valor:,.2f}"
                )
            )

        return m, suma_valor

    def _on_doble_clic(self, event):
        """Abre la ventana de edición individual si existe el bien seleccionado."""
        seleccion = self.tree.selection()
        if not seleccion:
            return
        if "totales" in self.tree.item(seleccion[0], "tags"):
            return
        item_vals = self.tree.item(seleccion[0], "values")
        if item_vals and len(item_vals) > 3:
            codint = item_vals[3]
            if str(codint).strip().startswith(("∑", "TOTAL")):
                return
            try:
                from gui.gui_detalles import Window_detalles
                Window_detalles(root=self, user=self.user, team=self.team, codigo=codint)
            except Exception:
                pass

    def _limpiar_filtro(self):
        self.camp.set("")
        self.iniciar_filtro()

    def _cargar_datos_en_tree(self, registros):
        """Limpia e inserta registros en el árbol con colores alternados y fila de totales."""
        children = self.tree.get_children()
        if children:
            self.tree.delete(*children)

        metricas, suma_valor = self._actualizar_kpis_y_resumen(registros)
        total = len(registros) if registros else 0

        if registros:
            for idx, contact in enumerate(registros, 1):
                b = list(contact)
                b.insert(0, str(idx))
                tag_bg = "evenrow" if idx % 2 == 0 else "oddrow"
                inv_val = str(contact[1] or "").strip() if len(contact) > 1 else ""
                tag_estado = "faltante_row" if inv_val == "" else "inventariado_row"
                self.tree.insert('', tk.END, values=b, tags=(tag_bg, tag_estado))

            fila_totales = [
                "∑ TOTALES",
                f"Acta {self.acta}",
                f"{metricas['total_inventariados']} inv.",
                f"{metricas['total_faltantes']} falt.",
                f"{metricas['total_sobrantes']} sobr.",
                f"RESUMEN: {total} bienes listados (Total Bienes: {metricas['total_bienes']} | Inventariados: {metricas['total_inventariados']} | Faltantes: {metricas['total_faltantes']} | Sobrantes: {metricas['total_sobrantes']})",
                "", "", "", "", "", "",
                f"S/ {suma_valor:,.2f}",
                "",
            ]
            self.tree.insert('', tk.END, values=fila_totales, tags=("totales",))

        self.total_registros_var.set(f"{total} bienes")

    def iniciar_filtro(self, *args):
        try:
            if self.valor == 1:
                r = detalle_bienes(self.acta)
            elif self.valor == 2:
                r = detalle_bienes_faltantes(self.acta)
            else:
                r = []
            self._cargar_datos_en_tree(r)
        except Exception as e:
            mb.showerror("Error al consultar", f"No se pudieron cargar los datos del acta:\n{e}", parent=self)

    def buscar_criterio(self):
        campo_busqueda = self.camp.get().strip()
        criterio = self.crit.get()

        if not campo_busqueda:
            self.iniciar_filtro()
            return

        try:
            if self.valor == 1:
                base = detalle_bienes(self.acta) or []
                col_map = {
                    'CodInt': 2, 'CodPat': 3, 'DenBien': 4, 'Estado': 5,
                    'Dimension': 6, 'Marca': 7, 'Modelo': 8, 'Serie': 9,
                    'Color': 10, 'ValAdq': 11, 'Obs': 12
                }
                idx = col_map.get(criterio, 4)
                busq_low = campo_busqueda.lower()
                r = [row for row in base if idx < len(row) and busq_low in str(row[idx] or "").lower()]
            else:
                r = buscar_criterio_acta_ant(self.acta, criterio, campo_busqueda)
            self._cargar_datos_en_tree(r)
        except Exception as e:
            mb.showerror("Error de Búsqueda", f"Ocurrió un error al realizar la búsqueda:\n{e}", parent=self)

    def registrar(self):
        try:
            now = datetime.now()
            F_inv = now.strftime("%d/%m/%Y %H:%M:%S")
            data = [self.acta, F_inv, self.user, self.team]

            filas = [
                row_id for row_id in self.tree.get_children()
                if "totales" not in self.tree.item(row_id, "tags")
            ]
            if not filas:
                mb.showinfo("Sin registros", "No hay bienes pendientes en la lista para registrar.", parent=self)
                return

            pregunta = mb.askokcancel(
                "¡Atención!",
                f"¿Estás seguro de registrar los {len(filas)} bienes pendientes del acta Nº {self.acta}?",
                icon="question",
                parent=self
            )
            if pregunta:
                dataTree = [self.tree.item(row_id)['values'] for row_id in filas]
                for i in dataTree:
                    if len(i) > 3:
                        codint = i[3]
                        registrar_codpat_test(codint, data)
                        if self.cb.get() == 1:
                            try:
                                build_label(1, codint, self.acta)
                            except Exception as ex_label:
                                print(f"Error imprimiendo etiqueta para {codint}: {ex_label}")

                if self.frame_app and hasattr(self.frame_app, 'iniciar_filtro'):
                    self.frame_app.iniciar_filtro()

                mb.showinfo("Acontar S.A.C.", "¡Bienes registrados correctamente!", parent=self)

                if self.cb.get() == 1:
                    mb.showinfo("Acontar S.A.C.", "Etiquetas enviadas al proceso de impresión.", parent=self)

                r = detalle_bienes_faltantes(self.acta)
                self._cargar_datos_en_tree(r)

            self.focus_set()

        except Exception as e:
            mb.showerror("Error", f"Ocurrió un error al registrar: {str(e)}", parent=self)
            self.focus_set()

    def generar_pdf(self):
        try:
            iniciar_reporte(self.acta)
            mb.showinfo("¡Atención!", "Reporte PDF generado con éxito.", parent=self)
            self.focus_set()
        except Exception as e:
            mb.showerror("Error de Reporte", f"Error al generar el acta:\n{str(e)}", parent=self)
            self.focus_set()

    def exportar_datos(self):
        datos = []
        for item in self.tree.get_children():
            values = self.tree.item(item, "values")
            datos.append(values)

        if not datos:
            mb.showwarning("Sin datos", "No hay registros disponibles para exportar.", parent=self)
            return

        try:
            nombre_archivo = f"Detalle_Acta_{self.acta or 'General'}_"
            exportar_excel(nombre_archivo, self.lista, datos)
            mb.showinfo("Exportación Exitosa", "Archivo Excel generado con éxito en la carpeta 'exportar/'.", parent=self)
            self.focus_set()
        except Exception as e:
            mb.showerror("Error al Exportar", f"No se pudo exportar el archivo Excel: {e}", parent=self)
            self.focus_set()
