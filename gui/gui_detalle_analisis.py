import os
import tkinter as tk
from tkinter import ttk, PhotoImage
from tkinter import messagebox as mb
from reportes.faltantes import iniciar_reporte
from data.exp_excel import exportar_excel
from gui.gui_detalles import Window_detalles
from utils.order_utils import sort_by
from utils.helpers import resource_path
from db.query import detalle_analisis, detalle_analisis_crit


class Window_d_analisis(tk.Toplevel):
    """Ventana de desglose detallado de bienes según el tipo de análisis seleccionado."""

    def __init__(self, root=None, acta=None, valor=None, analisis=None):
        super().__init__(root)
        self.root = root
        self.acta = acta if acta is not None else (valor[0] if valor else None)
        self.valor = valor or []
        self.analisis = analisis if analisis is not None else 1
        self.datos_completos = []

        self.title("Detalle de Análisis — Acontar Especialistas Contables S.A.C.")
        self.geometry("1180x680")
        self.minsize(960, 540)
        self.configure(bg="#f8fafc")
        if root:
            self.transient(root)

        self._cargar_favicon()
        self._centrar_ventana(1180, 680)
        self._configurar_estilos()

        self.iconoxls = self._cargar_icono("img/excel.png")
        self.iconopdf = self._cargar_icono("img/pdf.png")
        self.iconobus = self._cargar_icono("img/lupa.png")
        self.iconobor = self._cargar_icono("img/borrar.png")

        self.crit = tk.StringVar()
        self.camp = tk.StringVar()

        self._construir_interfaz()
        self.tree_view()
        self.iniciar_filtro()
        self.focus_set()

    # -------------------------------------------------------------------------
    # CONFIGURACIÓN DE VENTANA Y ESTILOS
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
        style.configure("DetAnalisis.TLabelframe",
            background="#ffffff",
            relief="solid",
            borderwidth=1,
            bordercolor="#e2e8f0"
        )
        style.configure("DetAnalisis.TLabelframe.Label",
            background="#ffffff",
            foreground="#334155",
            font=("Segoe UI", 9, "bold")
        )

        # Treeview moderno
        style.configure("DetAnalisis.Treeview",
            background="#ffffff",
            fieldbackground="#ffffff",
            foreground="#0f172a",
            font=("Segoe UI", 9),
            rowheight=24
        )
        style.configure("DetAnalisis.Treeview.Heading",
            background="#f1f5f9",
            foreground="#475569",
            font=("Segoe UI", 8, "bold"),
            relief="flat",
            padding=(6, 6)
        )
        style.map("DetAnalisis.Treeview",
            background=[("selected", "#2563eb")],
            foreground=[("selected", "#ffffff")]
        )

    # -------------------------------------------------------------------------
    # CONSTRUCCIÓN DE INTERFAZ
    # -------------------------------------------------------------------------
    def _obtener_subtitulo_contexto(self):
        try:
            if self.analisis == 1 and len(self.valor) >= 4:
                return f"📍 Ubicación [Acta {self.valor[0]}]:  {self.valor[1]}  —  {self.valor[2]}  —  {self.valor[3]}"
            elif self.analisis == 2 and len(self.valor) >= 3:
                return f"📑 Cuenta Contable [{self.valor[1]}]:  {self.valor[2]}"
            elif self.analisis == 3 and len(self.valor) >= 1:
                return f"📦 Denominación del Bien:  {self.valor[0]}"
            elif self.analisis == 4 and len(self.valor) >= 1:
                ubi = f" ({self.valor[1]} - {self.valor[3]})" if len(self.valor) >= 4 else ""
                return f"👤 Usuario / Responsable:  {self.valor[0]}{ubi}"
        except Exception:
            pass
        return f"📋 Detalle de Bienes — {self.acta or ''}"

    def _construir_interfaz(self):
        self.contenedor = tk.Frame(self, bg="#f8fafc")
        self.contenedor.pack(fill="both", expand=True, padx=12, pady=10)

        # 1. Tarjeta de Cabecera Contextual
        header_card = tk.Frame(self.contenedor, bg="#ffffff", bd=1, relief="solid", padx=14, pady=10)
        header_card.pack(fill="x", pady=(0, 8))

        tk.Label(
            header_card,
            text=self._obtener_subtitulo_contexto(),
            bg="#ffffff",
            fg="#0f172a",
            font=("Segoe UI", 11, "bold"),
            anchor="w"
        ).pack(side="left", fill="x", expand=True)

        frame_badge = tk.Frame(header_card, bg="#eff6ff", bd=1, relief="solid")
        frame_badge.pack(side="right")
        self.lbl_badge = tk.Label(
            frame_badge,
            text="📦  0 bienes",
            bg="#eff6ff",
            fg="#1d4ed8",
            font=("Segoe UI", 9, "bold"),
            padx=10,
            pady=3
        )
        self.lbl_badge.pack()

        # 1.b Franja de KPIs de Totales del grupo seleccionado (si self.valor trae los conteos)
        self.frame_kpis = tk.Frame(self.contenedor, bg="#f8fafc")
        self.frame_kpis.pack(fill="x", pady=(0, 8))
        self._construir_kpis_contexto()

        # 2. Card de Filtros y Acciones
        self.Frame1 = ttk.LabelFrame(
            self.contenedor,
            text=" 🔎 Búsqueda Rápida y Exportación ",
            style="DetAnalisis.TLabelframe",
            padding=(10, 6)
        )
        self.Frame1.pack(fill="x", pady=(0, 8))

        ttk.Label(self.Frame1, text="Criterio:", font=("Segoe UI", 9, "bold")).pack(side="left", padx=(2, 4), pady=4)

        self.cbxCri = ttk.Combobox(self.Frame1, textvariable=self.crit, state="readonly", width=20)
        self.cbxCri.pack(side="left", padx=(0, 8), pady=4)

        ttk.Label(self.Frame1, text="Buscar:", font=("Segoe UI", 9, "bold")).pack(side="left", padx=(0, 4), pady=4)

        self.etrCrit = ttk.Entry(self.Frame1, textvariable=self.camp, width=28, font=("Segoe UI", 9))
        self.etrCrit.pack(side="left", padx=(0, 6), pady=4)
        self.etrCrit.bind("<Return>", lambda _e: self.filtrar())
        self.etrCrit.bind("<KeyRelease>", lambda _e: self.filtrar())

        btnCrit = ttk.Button(
            self.Frame1,
            text=" 🔍 Buscar" if not self.iconobus else " Buscar",
            command=self.filtrar
        )
        if self.iconobus:
            btnCrit.config(image=self.iconobus, compound="left")
        btnCrit.pack(side="left", padx=4, pady=4)

        btnLimpiar = ttk.Button(
            self.Frame1,
            text=" ✖ Limpiar" if not self.iconobor else " Limpiar",
            command=self.limpiar_filtro
        )
        if self.iconobor:
            btnLimpiar.config(image=self.iconobor, compound="left")
        btnLimpiar.pack(side="left", padx=4, pady=4)

        # Botones de exportación a la derecha
        self.btnPdf = ttk.Button(
            self.Frame1,
            text=" 📄 Generar PDF" if not self.iconopdf else " Generar PDF",
            command=self.generar_pdf_faltantes
        )
        if self.iconopdf:
            self.btnPdf.config(image=self.iconopdf, compound="left")
        self.btnPdf.pack(side="right", padx=(4, 2), pady=4)

        self.btnExcel = ttk.Button(
            self.Frame1,
            text=" 📊 Exportar Excel" if not self.iconoxls else " Exportar Excel",
            command=self.exportar_datos_excel
        )
        if self.iconoxls:
            self.btnExcel.config(image=self.iconoxls, compound="left")
        self.btnExcel.pack(side="right", padx=4, pady=4)

        # 3. Card de Tabla (Treeview)
        self.Frame2 = ttk.LabelFrame(
            self.contenedor,
            text=" 📋 Relación Detallada de Bienes ",
            style="DetAnalisis.TLabelframe",
            padding=8
        )
        self.Frame2.rowconfigure(0, weight=1)
        self.Frame2.columnconfigure(0, weight=1)
        self.Frame2.pack(fill="both", expand=True)

        # 4. Barra Fija de Resumen de Totales
        self.frame_resumen_totales = tk.Frame(
            self.contenedor, bg="#1e293b", bd=1, relief="solid", padx=12, pady=7
        )
        self.frame_resumen_totales.pack(fill="x", pady=(6, 0))

        tk.Label(
            self.frame_resumen_totales,
            text="∑ RESUMEN DE TOTALES:",
            bg="#1e293b",
            fg="#38bdf8",
            font=("Segoe UI", 9, "bold")
        ).pack(side="left", padx=(0, 10))

        self.lbl_resumen_totales = tk.Label(
            self.frame_resumen_totales,
            text="Calculando totales...",
            bg="#1e293b",
            fg="#f8fafc",
            font=("Segoe UI", 9, "bold"),
            anchor="w"
        )
        self.lbl_resumen_totales.pack(side="left", fill="x", expand=True)

        # 5. Barra Inferior (Footer)
        frame_footer = tk.Frame(self.contenedor, bg="#f8fafc")
        frame_footer.pack(fill="x", pady=(6, 0))

        self.lbl_footer_info = tk.Label(
            frame_footer,
            text="💡 Doble clic en cualquier fila para abrir la ficha detallada del bien  |  Clic en los encabezados para ordenar",
            bg="#f8fafc",
            fg="#64748b",
            font=("Segoe UI", 8, "italic")
        )
        self.lbl_footer_info.pack(side="left")

    def _construir_kpis_contexto(self):
        for w in self.frame_kpis.winfo_children():
            w.destroy()

        tarjetas = []
        try:
            if self.analisis in (1, 4) and len(self.valor) >= 9:
                tarjetas = [
                    ("📦 Total Bienes Asignados", str(self.valor[4]), "#1e40af", "#eff6ff"),
                    ("✅ Total Inventariados", str(self.valor[5]), "#15803d", "#f0fdf4"),
                    ("⚠️ Total Faltantes", str(self.valor[6]), "#b91c1c", "#fef2f2"),
                    ("➕ Total Sobrantes", str(self.valor[7]), "#b45309", "#fffbeb"),
                    ("📈 % Avance", str(self.valor[8]), "#0f172a", "#f1f5f9"),
                ]
            elif self.analisis == 2 and len(self.valor) >= 9:
                tarjetas = [
                    ("📦 Total Bienes Asignados", str(self.valor[3]), "#1e40af", "#eff6ff"),
                    ("✅ Total Inventariados", str(self.valor[4]), "#15803d", "#f0fdf4"),
                    ("⚠️ Total Faltantes", str(self.valor[5]), "#b91c1c", "#fef2f2"),
                    ("💰 Valor Adq. Cuenta (S/)", str(self.valor[6]), "#0f766e", "#f0fdfa"),
                    ("📊 Valor Neto Cuenta (S/)", str(self.valor[8]), "#0f172a", "#f1f5f9"),
                ]
            elif self.analisis == 3 and len(self.valor) >= 5:
                tarjetas = [
                    ("📦 Total Bienes Asignados", str(self.valor[1]), "#1e40af", "#eff6ff"),
                    ("✅ Total Inventariados", str(self.valor[2]), "#15803d", "#f0fdf4"),
                    ("⚠️ Total Faltantes", str(self.valor[3]), "#b91c1c", "#fef2f2"),
                    ("📈 % Avance", str(self.valor[4]), "#0f172a", "#f1f5f9"),
                ]
        except Exception:
            tarjetas = []

        # Agregar tarjeta dinámica para Valor Total en Vista
        tarjetas.append(("💵 Valor Total en Vista (S/)", "S/ 0.00", "#4338ca", "#eef2ff"))

        self.lbl_kpi_valor_vista = None
        for idx, (titulo, valor_txt, fg_color, bg_color) in enumerate(tarjetas):
            self.frame_kpis.columnconfigure(idx, weight=1)
            card = tk.Frame(
                self.frame_kpis, bg=bg_color, bd=1, relief="solid", padx=10, pady=5
            )
            card.grid(row=0, column=idx, sticky="nsew", padx=(0 if idx == 0 else 4, 0))
            tk.Label(
                card, text=titulo, bg=bg_color, fg="#475569", font=("Segoe UI", 8, "bold"), anchor="w"
            ).pack(fill="x")
            lbl_val = tk.Label(
                card, text=valor_txt, bg=bg_color, fg=fg_color, font=("Segoe UI", 11, "bold"), anchor="w"
            )
            lbl_val.pack(fill="x")
            if "Valor Total en Vista" in titulo:
                self.lbl_kpi_valor_vista = lbl_val

    # -------------------------------------------------------------------------
    # CONFIGURACIÓN DEL TREEVIEW
    # -------------------------------------------------------------------------
    def tree_view(self):
        cab = []

        if self.analisis == 1:
            self.arc = "Análisis por Ubicación"
            self.lista = [
                'Item', 'Código\nInterno', 'Código\nPatrimonial', 'Denominación', 'Estado',
                'Dimensión', 'Marca', 'Modelo', 'Serie', 'Color', 'Valor de\nAdquisición', 'Obs'
            ]
        elif self.analisis == 2:
            self.arc = "Análisis por Cuenta Contable"
            self.lista = [
                'Item', 'Cuenta', 'Código\nInterno', 'Código\nPatrimonial', 'Denominación',
                'Fecha de\nAdquisición', 'Nro. Doc.\nAdquisición', 'Valor de\nAdquisición'
            ]
        elif self.analisis == 3:
            self.arc = "Análisis por Denominación"
            self.lista = [
                'Item', 'Código\nInterno', 'Código\nPatrimonial', 'Denominación', 'Estado',
                'Dimensión', 'Marca', 'Modelo', 'Serie', 'Color', 'Valor de\nAdquisición', 'Obs'
            ]
        else:
            self.arc = "Análisis por Usuario"
            self.lista = [
                'Item', 'Código\nInterno', 'Código\nPatrimonial', 'Denominación', 'Estado',
                'Dimensión', 'Marca', 'Modelo', 'Serie', 'Color', 'Valor de\nAdquisición', 'Obs'
            ]

        for i in range(1, len(self.lista) + 1):
            cab.append(i)

        self.tree = ttk.Treeview(self.Frame2, columns=cab, show="headings", style="DetAnalisis.Treeview")

        for i, val in enumerate(self.lista, start=1):
            self.tree.heading(i, text=val.replace("\n", " "), command=lambda col=i: sort_by(self.tree, col, False), anchor="center")

        if self.analisis == 2:
            self.tree.column(1, width=55,  stretch=False, anchor="center")
            self.tree.column(2, width=90,  stretch=False, anchor="center")
            self.tree.column(3, width=105, stretch=False, anchor="center")
            self.tree.column(4, width=120, stretch=False, anchor="center")
            self.tree.column(5, width=320, stretch=True,  anchor="w")
            self.tree.column(6, width=130, stretch=False, anchor="center")
            self.tree.column(7, width=135, stretch=False, anchor="center")
            self.tree.column(8, width=130, stretch=False, anchor="e")
        else:
            self.tree.column(1,  width=50,  stretch=False, anchor="center")
            self.tree.column(2,  width=105, stretch=False, anchor="center")
            self.tree.column(3,  width=120, stretch=False, anchor="center")
            self.tree.column(4,  width=250, stretch=True,  anchor="w")
            self.tree.column(5,  width=85,  stretch=False, anchor="center")
            self.tree.column(6,  width=95,  stretch=False, anchor="w")
            self.tree.column(7,  width=95,  stretch=False, anchor="w")
            self.tree.column(8,  width=95,  stretch=False, anchor="w")
            self.tree.column(9,  width=100, stretch=False, anchor="w")
            self.tree.column(10, width=85,  stretch=False, anchor="w")
            self.tree.column(11, width=125, stretch=False, anchor="e")
            self.tree.column(12, width=125, stretch=False, anchor="w")

        self.tree.tag_configure("odd",  background="#ffffff")
        self.tree.tag_configure("even", background="#f8fafc")
        self.tree.tag_configure("totales", background="#e2e8f0", foreground="#0f172a", font=("Segoe UI", 9, "bold"))

        # Poblar combobox de criterios sin saltos de línea
        self.lista_limpia = [c.replace("\n", " ") for c in self.lista]
        self.cbxCri.configure(values=self.lista_limpia)
        if "Denominación" in self.lista_limpia:
            self.crit.set("Denominación")
        elif self.lista_limpia:
            self.cbxCri.current(0)

        self.tree.grid(column=0, row=0, sticky="nsew")
        scrollbarV = ttk.Scrollbar(self.Frame2, orient=tk.VERTICAL,   command=self.tree.yview)
        scrollbarH = ttk.Scrollbar(self.Frame2, orient=tk.HORIZONTAL, command=self.tree.xview)
        self.tree.configure(yscroll=scrollbarV.set, xscroll=scrollbarH.set)
        scrollbarV.grid(column=1, row=0, sticky="ns")
        scrollbarH.grid(column=0, row=1, sticky="ew")

        self.tree.bind("<Double-Button-1>", self.abrir_detalle_bien)

    # -------------------------------------------------------------------------
    # LÓGICA DE CONSULTA Y FILTRADO
    # -------------------------------------------------------------------------
    def _actualizar_totales_vista(self, filas_mostradas):
        n_mostrados = len(filas_mostradas)
        n_total = len(self.datos_completos)
        val_idx = 7 if self.analisis == 2 else 10
        suma_val = 0.0
        for row in filas_mostradas:
            if val_idx < len(row):
                try:
                    suma_val += float(str(row[val_idx]).replace(",", "").strip() or 0)
                except (ValueError, TypeError):
                    pass

        if self.lbl_kpi_valor_vista is not None:
            self.lbl_kpi_valor_vista.config(text=f"S/ {suma_val:,.2f}")

        if n_mostrados > 0:
            if self.analisis == 2:
                fila_tot = [
                    "∑",
                    "TOTALES",
                    "",
                    "",
                    f"TOTAL BIENES EN VISTA: {n_mostrados:,}",
                    "",
                    "VALOR TOTAL (S/):",
                    f"{suma_val:,.2f}",
                ]
            else:
                fila_tot = [
                    "∑",
                    "TOTALES",
                    "",
                    f"TOTAL BIENES EN VISTA: {n_mostrados:,}",
                    "",
                    "",
                    "",
                    "",
                    "",
                    "VALOR TOTAL (S/):",
                    f"{suma_val:,.2f}",
                    "",
                ]
            self.tree.insert("", tk.END, values=fila_tot, tags=("totales",))

        partes_resumen = [f"Bienes Mostrados: {n_mostrados:,} de {n_total:,}"]
        try:
            if self.analisis in (1, 4) and len(self.valor) >= 9:
                partes_resumen.extend([
                    f"Total Bienes Asignados: {self.valor[4]}",
                    f"Total Inventariados: {self.valor[5]}",
                    f"Total Faltantes: {self.valor[6]}",
                    f"Total Sobrantes: {self.valor[7]}",
                ])
            elif self.analisis == 2 and len(self.valor) >= 9:
                partes_resumen.extend([
                    f"Total Bienes Cuenta: {self.valor[3]}",
                    f"Total Inventariados: {self.valor[4]}",
                    f"Total Faltantes: {self.valor[5]}",
                ])
            elif self.analisis == 3 and len(self.valor) >= 5:
                partes_resumen.extend([
                    f"Total Bienes Denominación: {self.valor[1]}",
                    f"Total Inventariados: {self.valor[2]}",
                    f"Total Faltantes: {self.valor[3]}",
                ])
        except Exception:
            pass
        partes_resumen.append(f"Valor Adquisición en Vista: S/ {suma_val:,.2f}")
        self.lbl_resumen_totales.config(text="   |   ".join(partes_resumen))

    def iniciar_filtro(self, *args):
        for item in self.tree.get_children():
            self.tree.delete(item)

        if self.analisis == 2 and len(self.valor) > 1:
            criterio = self.valor[1]
        elif len(self.valor) > 0:
            criterio = self.valor[0]
        else:
            criterio = self.acta

        r = detalle_analisis(self.analisis, criterio) or []
        self.datos_completos = []

        for cell, contact in enumerate(r, 1):
            b = list(contact)
            b.insert(0, str(cell))
            self.datos_completos.append(b)
            tag = "odd" if cell % 2 == 1 else "even"
            self.tree.insert("", tk.END, values=b, tags=(tag,))

        n = len(self.datos_completos)
        self.lbl_badge.config(text=f"📦  {n} {'bien' if n == 1 else 'bienes'}")
        self._actualizar_totales_vista(self.datos_completos)

    def buscar_criterio(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        r = detalle_analisis_crit(self.acta, self.crit.get(), self.camp.get()) or []
        filas = []
        for cell, contact in enumerate(r, 1):
            b = list(contact)
            b.insert(0, str(cell))
            filas.append(b)
            tag = "odd" if cell % 2 == 1 else "even"
            self.tree.insert("", tk.END, values=b, tags=(tag,))
        self.lbl_badge.config(text=f"📦  {len(r)} bienes")
        self._actualizar_totales_vista(filas)

    def filtrar(self):
        columna = self.crit.get().strip().replace("\n", " ")
        valor = self.camp.get().strip().lower()

        for item in self.tree.get_children():
            self.tree.delete(item)

        if not valor:
            for cell, row in enumerate(self.datos_completos, 1):
                fila_mod = [str(cell)] + list(row[1:])
                tag = "odd" if cell % 2 == 1 else "even"
                self.tree.insert("", tk.END, values=fila_mod, tags=(tag,))
            n = len(self.datos_completos)
            self.lbl_badge.config(text=f"📦  {n} {'bien' if n == 1 else 'bienes'}")
            self._actualizar_totales_vista(self.datos_completos)
            return

        col_idx = self.lista_limpia.index(columna) if columna in self.lista_limpia else 0

        coincidentes = []
        for row in self.datos_completos:
            if col_idx < len(row) and valor in str(row[col_idx]).lower():
                coincidentes.append(row)

        for cell, row in enumerate(coincidentes, 1):
            fila_mod = [str(cell)] + list(row[1:])
            tag = "odd" if cell % 2 == 1 else "even"
            self.tree.insert("", tk.END, values=fila_mod, tags=(tag,))

        self.lbl_badge.config(text=f"📦  {len(coincidentes)} / {len(self.datos_completos)} bienes")
        self._actualizar_totales_vista(coincidentes)

    def limpiar_filtro(self):
        self.camp.set("")
        self.filtrar()

    # -------------------------------------------------------------------------
    # ACCIONES Y EXPORTACIÓN
    # -------------------------------------------------------------------------
    def generar_pdf_faltantes(self):
        try:
            iniciar_reporte(self.acta)
            self.focus_set()
        except Exception as e:
            mb.showerror("Error", f"No se pudo generar el reporte PDF:\n{e}", parent=self)

    def exportar_datos_excel(self):
        datos = [list(self.tree.item(item, "values")) for item in self.tree.get_children()]
        if not datos:
            mb.showwarning("Atención", "No hay datos en la tabla para exportar.", parent=self)
            return
        exportar_excel(self.arc.strip(), self.lista_limpia, datos)
        self.focus_set()

    def abrir_detalle_bien(self, _event=None):
        sel = self.tree.focus()
        if not sel:
            return
        if "totales" in (self.tree.item(sel, "tags") or ()):
            return
        vals = self.tree.item(sel).get("values", [])
        if not vals:
            return
        # En análisis 2 el código interno está en índice 2; en los demás en índice 1
        cod_idx = 2 if self.analisis == 2 else 1
        if cod_idx < len(vals) and vals[cod_idx]:
            win = Window_detalles(codigo=vals[cod_idx])
            win.wait_window(win)
            self.focus_set()
            self.iniciar_filtro()
