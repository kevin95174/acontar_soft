import os
import tkinter as tk
from tkinter import ttk, PhotoImage, filedialog
from tkinter import messagebox as mb
from db.query import reporte_01
from reportes.reportes import iniciar_reporte
from reportes.conciliacion import iniciar_conciliacion
from reportes.reporte_contable import iniciar_reporte_contable
from data.exp_excel import exportar_excel
from gui.gui_detalles import Window_detalles
from utils.order_utils import sort_by
from utils.helpers import resource_path


class Window_reporte(tk.Toplevel):
    """Ventana unificada de generación, consulta y exportación de reportes del inventario."""

    SUBTITULOS_REPORTE = {
        1:  "Relación general de bienes verificados y ubicados físicamente en el inventario",
        2:  "Bienes localizados que pertenecen o están registrados por otras instituciones",
        3:  "Bienes cuya descripción física difiere de la denominación en el catálogo",
        4:  "Relación valorizada de bienes para actualización de valor neto y depreciación",
        5:  "Bienes identificados en condición de desuso o almacenados en depósitos",
        6:  "Bienes entregados o recibidos bajo modalidad de afectación en uso o préstamo",
        7:  "Bienes registrados en el patrimonio que aún no han sido localizados (Faltantes)",
        8:  "Bienes encontrados físicamente sin código o registro patrimonial previo (Sobrantes)",
        9:  "Bienes dados de baja que aún permanecen físicamente sin disposición final",
        10: "Resumen contable comparativo entre el registro patrimonial y el inventario físico",
        11: "Bienes que presentan datos técnicos incompletos o requieren actualización",
        12: "Detalle contable de bienes ubicados agrupados por cuenta patrimonial",
        13: "Detalle contable de bienes faltantes agrupados por cuenta patrimonial",
    }

    def __init__(self, root=None, valor=None, user=None, team=None):
        super().__init__(root)
        self.root = root
        self.user = user
        self.team = team
        self.valor = valor if valor is not None else 1
        self.datos_completos = []
        self.fila_totales_10 = None

        self.title("Visor y Generador de Reportes — AcontarSoft")
        self.geometry("1240x740")
        self.minsize(1020, 600)
        self.configure(bg="#f8fafc")
        if root:
            self.transient(root)

        self._cargar_favicon()
        self._centrar_ventana(1240, 740)
        self._configurar_estilos()

        self.iconoxls = self._cargar_icono("img/excel.png")
        self.iconopdf = self._cargar_icono("img/pdf.png")
        self.iconobus = self._cargar_icono("img/lupa.png")
        self.iconobor = self._cargar_icono("img/borrar.png")

        self.crit = tk.StringVar()
        self.camp = tk.StringVar()

        self._construir_interfaz()
        self.tree_view()
        self.realizar_query()

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
        style.configure("Reporte.TLabelframe",
            background="#ffffff",
            relief="solid",
            borderwidth=1,
            bordercolor="#e2e8f0"
        )
        style.configure("Reporte.TLabelframe.Label",
            background="#ffffff",
            foreground="#334155",
            font=("Segoe UI", 9, "bold")
        )

        # Treeview moderno
        style.configure("Reporte.Treeview",
            background="#ffffff",
            fieldbackground="#ffffff",
            foreground="#0f172a",
            font=("Segoe UI", 9),
            rowheight=24
        )
        style.configure("Reporte.Treeview.Heading",
            background="#f1f5f9",
            foreground="#475569",
            font=("Segoe UI", 8, "bold"),
            relief="flat",
            padding=(6, 6)
        )
        style.map("Reporte.Treeview",
            background=[("selected", "#2563eb")],
            foreground=[("selected", "#ffffff")]
        )

    # -------------------------------------------------------------------------
    # CONSTRUCCIÓN DE INTERFAZ
    # -------------------------------------------------------------------------
    def _construir_interfaz(self):
        self.contenedor = tk.Frame(self, bg="#f8fafc")
        self.contenedor.pack(fill="both", expand=True, padx=12, pady=10)

        # 1. Tarjeta de Cabecera
        self.header_card = tk.Frame(self.contenedor, bg="#ffffff", bd=1, relief="solid", padx=14, pady=10)
        self.header_card.pack(fill="x", pady=(0, 8))

        f_titles = tk.Frame(self.header_card, bg="#ffffff")
        f_titles.pack(side="left", fill="x", expand=True)

        self.lblTit = tk.Label(
            f_titles,
            text="REPORTE DE INVENTARIO",
            font=("Segoe UI", 12, "bold"),
            bg="#ffffff",
            fg="#0f172a",
            anchor="w"
        )
        self.lblTit.pack(fill="x")

        sub_txt = self.SUBTITULOS_REPORTE.get(self.valor, "Consulta y exportación de registros del inventario")
        self.lblSub = tk.Label(
            f_titles,
            text=sub_txt,
            font=("Segoe UI", 9),
            bg="#ffffff",
            fg="#64748b",
            anchor="w"
        )
        self.lblSub.pack(fill="x", pady=(1, 0))

        # Badge Contador a la derecha de la cabecera
        frame_badge = tk.Frame(self.header_card, bg="#eff6ff", bd=1, relief="solid")
        frame_badge.pack(side="right", padx=(8, 0))
        self.lbl_badge = tk.Label(
            frame_badge,
            text="📋  0 registros",
            bg="#eff6ff",
            fg="#1d4ed8",
            font=("Segoe UI", 9, "bold"),
            padx=12,
            pady=4
        )
        self.lbl_badge.pack()

        # 2. Card de Filtros y Exportación
        self.Frame1 = ttk.LabelFrame(
            self.contenedor,
            text=" 🔎 Filtros de Búsqueda y Exportación ",
            style="Reporte.TLabelframe",
            padding=(10, 6)
        )
        self.Frame1.pack(fill="x", pady=(0, 8))

        ttk.Label(self.Frame1, text="Criterio:", font=("Segoe UI", 9, "bold")).pack(side="left", padx=(2, 4), pady=4)

        self.cbxCri = ttk.Combobox(self.Frame1, textvariable=self.crit, state="readonly", width=22)
        self.cbxCri.pack(side="left", padx=(0, 10), pady=4)

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

        btnRecargar = ttk.Button(self.Frame1, text="🔄 Recargar", command=self.realizar_query)
        btnRecargar.pack(side="left", padx=4, pady=4)

        # Botones de Exportación a la derecha
        btnPdf = ttk.Button(
            self.Frame1,
            text=" 📄 Exportar PDF" if not self.iconopdf else " Exportar PDF",
            command=self.exportar_pdf
        )
        if self.iconopdf:
            btnPdf.config(image=self.iconopdf, compound="left")
        btnPdf.pack(side="right", padx=(4, 2), pady=4)

        btnCsv = ttk.Button(
            self.Frame1,
            text=" 📊 Exportar Excel" if not self.iconoxls else " Exportar Excel",
            command=self.exportar_datos
        )
        if self.iconoxls:
            btnCsv.config(image=self.iconoxls, compound="left")
        btnCsv.pack(side="right", padx=4, pady=4)

        # 3. Card de Tabla (Treeview)
        self.Frame2 = ttk.LabelFrame(
            self.contenedor,
            text=" 📋 Detalle de Registros del Reporte ",
            style="Reporte.TLabelframe",
            padding=8
        )
        self.Frame2.rowconfigure(0, weight=1)
        self.Frame2.columnconfigure(0, weight=1)
        self.Frame2.pack(fill="both", expand=True)

        # 4. Barra Inferior (Footer)
        frame_footer = tk.Frame(self.contenedor, bg="#f8fafc")
        frame_footer.pack(fill="x", pady=(8, 0))

        self.lbl_footer = tk.Label(
            frame_footer,
            text="💡 Haga clic en cualquier encabezado de columna para ordenar ascendente/descendente  |  Doble clic en una fila para ver detalles del bien",
            bg="#f8fafc",
            fg="#64748b",
            font=("Segoe UI", 8, "italic")
        )
        self.lbl_footer.pack(side="left")

    # -------------------------------------------------------------------------
    # CONFIGURACIÓN DE COLUMNAS POR TIPO DE REPORTE
    # -------------------------------------------------------------------------
    def tree_view(self):
        cab = []

        # 1. Bienes Ubicados
        if self.valor == 1:
            self.arc = "REPORTE DE BIENES UBICADOS"
            self.lista = [
                'Nro', 'Código\nInterno', 'Código\nPatrimonial', 'Denominación', 'Marca', 'Modelo',
                'Serie', 'Color', 'Tipo', 'Dimensión', 'Estado', 'Ubicación'
            ]
            self.colwidths = [25, 40, 60, 160, 38, 62, 62, 62, 62, 62, 62]
            widths_ui = [50, 90, 110, 260, 95, 95, 100, 85, 90, 95, 85, 360]

        # 2. Bienes de otras entidades
        elif self.valor == 2:
            self.arc = "REPORTE DE BIENES DE OTRAS ENTIDADES"
            self.lista = ['Item', 'Cod\nPatrimonial', 'Denominación', 'Ubicacion', 'Estado', 'Entidad afectante']
            self.colwidths = [28, 70, 170, 260, 38, 210]
            widths_ui = [55, 120, 280, 280, 90, 240]

        # 3. Bienes que no coinciden con la descripción
        elif self.valor == 3:
            self.arc = "REPORTE DE BIENES QUE NO COINCIDEN CON LA DESCRIPCIÓN"
            self.lista = [
                'Item', 'Cod\nInterno', 'Cod\nPatrimonial', 'Denominación registrada',
                'Ubicación', 'Estado', 'Denominacion corregida'
            ]
            self.colwidths = [28, 40, 68, 160, 260, 38, 160]
            widths_ui = [55, 90, 115, 250, 260, 85, 250]

        # 4. Bienes para actualización de valor neto
        elif self.valor == 4:
            self.arc = "REPORTE DE BIENES PARA ACTUALIZACIÓN DE VALOR NETO"
            self.lista = [
                'Item', 'Cod\nInterno', 'Cod\nPatrimonial', 'Denominación', 'Cuenta\nContable',
                'Denominación\nCuenta contable', 'Documento de\nAdquisición', 'Fecha de\nAdquisición',
                'Valor de\nAdquisición', 'Depreciación\nAcumulada', 'Valor Neto'
            ]
            self.colwidths = [28, 40, 65, 150, 60, 150, 65, 55, 62, 62, 62]
            widths_ui = [50, 85, 110, 240, 95, 220, 115, 100, 105, 105, 100]

        # 5. Bienes en desuso o depósitos
        elif self.valor == 5:
            self.arc = "REPORTE DE BIENES EN DESUSO O DEPÓSITOS"
            self.lista = [
                'Item', 'Cod\nInterno', 'Cod\nPatrimonial', 'Denominación', 'Ubicación',
                'Estado', 'Marca', 'Modelo', 'Serie', 'Color', 'Situación'
            ]
            self.colwidths = [28, 40, 65, 150, 150, 40, 60, 60, 60, 60, 50]
            widths_ui = [50, 90, 110, 250, 230, 85, 95, 95, 100, 85, 95]

        # 6. Bienes afectados en uso o préstamo
        elif self.valor == 6:
            self.arc = "REPORTE DE BIENES AFECTADOS EN USO O PRÉSTAMO"
            self.lista = [
                'Item', 'Cod\nInterno', 'Cod\nPatrimonial', 'Denominación', 'Estado',
                'Marca', 'Modelo', 'Serie', 'Color', 'Afectante o Beneficiario'
            ]
            self.colwidths = [28, 40, 68, 160, 38, 62, 62, 62, 62, 160]
            widths_ui = [50, 90, 110, 260, 85, 95, 95, 100, 85, 240]

        # 7. Bienes Faltantes
        elif self.valor == 7:
            self.arc = "REPORTE DE BIENES FALTANTES"
            self.lista = [
                'Nro', 'Código\nInterno', 'Código\nPatrimonial', 'Denominación', 'Marca', 'Modelo',
                'Serie', 'Color', 'Tipo', 'Dimensión', 'Estado', 'Ubicación'
            ]
            self.colwidths = [25, 40, 60, 160, 38, 62, 62, 62, 62, 62, 62]
            widths_ui = [50, 90, 110, 260, 95, 95, 100, 85, 90, 95, 85, 360]

        # 8. Bienes Sobrantes
        elif self.valor == 8:
            self.arc = "REPORTE DE BIENES SOBRANTES"
            self.lista = [
                'Nro', 'Ubicación', 'Denominación', 'Estado', 'Marca',
                'Modelo', 'Serie', 'Tipo', 'Color', 'Dimensiones'
            ]
            self.colwidths = [28, 160, 160, 40, 60, 60, 60, 60, 60, 62]
            widths_ui = [50, 240, 260, 85, 95, 95, 100, 90, 85, 105]

        # 9. Bienes dados de baja sin disposición
        elif self.valor == 9:
            self.arc = "REPORTE DE BIENES DADOS DE BAJA SIN DISPOSICIÓN"
            self.lista = [
                'Nro', 'Código\nInterno', 'Código\nPatrimonial', 'Denominación', 'Ubicación',
                'Estado', 'Marca', 'Modelo', 'Serie', 'Color', 'Tipo', 'Resolución'
            ]
            self.colwidths = [28, 40, 68, 160, 160, 60, 60, 60, 60, 60, 60]
            widths_ui = [50, 90, 110, 250, 220, 85, 95, 95, 100, 85, 90, 140]

        # 10. Conciliación de Inventario
        elif self.valor == 10:
            self.arc = "CONCILIACIÓN DE INVENTARIO"
            self.lista = [
                'Cuenta', 'SubCuenta', 'Denominación', 'Registro\nPatrimonial\nValor',
                'Cantidad\nRegistrados', 'Resultado\nde Inventario\nValor', 'Cantidad\nInventariados',
                'Valor\nFaltantes', 'Cantidad\nFaltantes'
            ]
            self.colwidths = [28, 60, 200, 62, 62, 62, 62, 62, 62]
            widths_ui = [75, 100, 380, 115, 95, 115, 95, 115, 95]

        # 11. Bienes que requieren actualización técnica
        elif self.valor == 11:
            self.arc = "REPORTE DE BIENES QUE REQUIEREN ACTUALIZACIÓN TÉCNICA"
            self.lista = [
                'Item', 'Código\nInterno', 'Código\nPatrimonial', 'Denominación', 'Detalle',
                'Estado', 'Marca', 'Modelo', 'Tipo', 'Serie', 'Color', 'Dimensiones', 'Obs'
            ]
            self.colwidths = [25, 35, 60, 140, 56, 25, 60, 60, 60, 60, 60, 60, 60]
            widths_ui = [50, 85, 110, 260, 160, 80, 95, 95, 90, 100, 85, 95, 140]

        # 12 y 13. Reportes Contables (Ubicados / Faltantes por cuenta)
        else:
            if self.valor == 12:
                self.arc = "REPORTE DE BIENES UBICADOS POR CUENTA"
            else:
                self.arc = "REPORTE DE BIENES FALTANTES POR CUENTA"

            self.lista = [
                'Item', 'Código\nInterno', 'Código\nPatrimonial', 'Denominación', 'Cuenta contable',
                'Denominacion', 'Documenton\nAdquisición', 'Fecha\nAdquisición', 'Valor\nAdquisición'
            ]
            self.colwidths = [25, 35, 60, 200, 56, 200, 56, 56, 56]
            widths_ui = [50, 85, 110, 260, 105, 240, 115, 100, 105]

        # Actualizar títulos de ventana y cabecera
        self.lblTit.config(text=f"📊  {self.arc}")
        self.title(f"{self.arc.title()} — AcontarSoft")

        cab = list(range(1, len(self.lista) + 1))
        self.tree = ttk.Treeview(self.Frame2, columns=cab, show="headings", style="Reporte.Treeview")

        for i, val in enumerate(self.lista, start=1):
            self.tree.heading(i, text=val, command=lambda col=i: sort_by(self.tree, col, False), anchor="center")
            w = widths_ui[i - 1] if i - 1 < len(widths_ui) else 100

            # Alineación según tipo de columna
            if self.valor == 4 and i in (9, 10, 11):
                anc = "e"
            elif self.valor == 10 and i in (4, 6, 8):
                anc = "e"
            elif self.valor == 10 and i in (5, 7, 9):
                anc = "center"
            elif self.valor in (12, 13) and i == 9:
                anc = "e"
            elif i == 1:
                anc = "center"
            else:
                anc = "w"

            self.tree.column(i, width=w, stretch=False, anchor=anc)

        self.tree.tag_configure("odd",     background="#ffffff")
        self.tree.tag_configure("even",    background="#f8fafc")
        self.tree.tag_configure("totales", background="#e2e8f0", foreground="#0f172a", font=("Segoe UI", 9, "bold"))

        # Configurar combobox de criterios limpio (sin saltos de línea)
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
    # CONSULTA Y FILTRADO DE DATOS
    # -------------------------------------------------------------------------
    def realizar_query(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

        r = reporte_01(self.valor) or []
        self.datos_completos = []
        self.fila_totales_10 = None

        if self.valor == 10:
            for idx, row in enumerate(r, 1):
                t01 = '{:,.2f}'.format(float(row[3]))
                t02 = '{:,.2f}'.format(float(row[5]))
                t03 = '{:,.2f}'.format(float(row[7]))
                valores = [row[0], row[1], row[2], t01, row[4], t02, row[6], t03, row[8]]
                self.datos_completos.append(valores)
                tag = "odd" if idx % 2 == 1 else "even"
                self.tree.insert("", tk.END, values=valores, tags=(tag,))

            items = self.tree.get_children()
            total_01 = sum(float(self.tree.item(item, 'values')[3].replace(',', '')) for item in items)
            total_03 = sum(float(self.tree.item(item, 'values')[5].replace(',', '')) for item in items)
            total_05 = sum(float(self.tree.item(item, 'values')[7].replace(',', '')) for item in items)

            total_01_f = f"{total_01:,.2f}"
            total_03_f = f"{total_03:,.2f}"
            total_05_f = f"{total_05:,.2f}"

            total_02 = sum(int(self.tree.item(item, 'values')[4]) for item in items)
            total_04 = sum(int(self.tree.item(item, 'values')[6]) for item in items)
            total_06 = sum(int(self.tree.item(item, 'values')[8]) for item in items)

            self.fila_totales_10 = ['TOTALES', '', '', total_01_f, total_02, total_03_f, total_04, total_05_f, total_06]
            self.tree.insert("", tk.END, values=self.fila_totales_10, tags=("totales",))
        else:
            for cell, contact in enumerate(r, 1):
                self.b = list(contact)
                self.b.insert(0, str(cell))
                self.datos_completos.append(self.b)
                tag = "odd" if cell % 2 == 1 else "even"
                self.tree.insert("", tk.END, values=self.b, tags=(tag,))

        n = len(self.datos_completos)
        self.lbl_badge.config(text=f"📋  {n} {'registro' if n == 1 else 'registros'}")

    def filtrar(self):
        columna = self.crit.get().strip().replace("\n", " ")
        valor = self.camp.get().strip().lower()

        for item in self.tree.get_children():
            self.tree.delete(item)

        if not valor:
            for idx, row in enumerate(self.datos_completos, 1):
                fila_mod = list(row) if self.valor == 10 else [str(idx)] + list(row[1:])
                tag = "odd" if idx % 2 == 1 else "even"
                self.tree.insert("", tk.END, values=fila_mod, tags=(tag,))
            if self.valor == 10 and self.fila_totales_10:
                self.tree.insert("", tk.END, values=self.fila_totales_10, tags=("totales",))
            n = len(self.datos_completos)
            self.lbl_badge.config(text=f"📋  {n} {'registro' if n == 1 else 'registros'}")
            return

        col_idx = self.lista_limpia.index(columna) if columna in self.lista_limpia else 0

        filas_coinciden = []
        for row in self.datos_completos:
            if col_idx < len(row) and valor in str(row[col_idx]).lower():
                filas_coinciden.append(row)

        for idx, row in enumerate(filas_coinciden, 1):
            fila_mod = list(row) if self.valor == 10 else [str(idx)] + list(row[1:])
            tag = "odd" if idx % 2 == 1 else "even"
            self.tree.insert("", "end", text="", values=fila_mod, tags=(tag,))

        self.lbl_badge.config(text=f"📋  {len(filas_coinciden)} / {len(self.datos_completos)} registros")

    def limpiar_filtro(self):
        self.camp.set("")
        self.filtrar()

    # -------------------------------------------------------------------------
    # EXPORTACIÓN Y DETALLE
    # -------------------------------------------------------------------------
    def exportar_datos(self):
        datos = []
        for item in self.tree.get_children():
            values = self.tree.item(item, "values")
            datos.append(values)

        if not datos:
            mb.showwarning(title="Atención", message="No hay datos en la tabla para exportar a Excel.", parent=self)
            return

        exportar_excel(self.arc, self.lista, datos)
        self.focus_set()

    def exportar_pdf(self):
        datos = []
        datos_pdf = []

        for item in self.tree.get_children():
            values = self.tree.item(item, "values")
            datos.append(values)

        if not datos:
            mb.showwarning(title="Atención", message="No hay datos en la tabla para exportar a PDF.", parent=self)
            return

        file_path = filedialog.askdirectory(initialdir='report_actas/fichas_vehiculares/', parent=self)
        if not file_path:
            return

        try:
            if self.valor in [1, 7]:
                for item in datos:
                    marca = 'MARCA: ' + item[4] if item[4] else ''
                    modelo = 'MODELO: ' + item[5] if item[5] else ''
                    serie = 'SERIE: ' + item[6] if item[6] else ''
                    color = 'COLOR: ' + item[7] if item[7] else ''
                    tipo = 'TIPO: ' + item[8] if item[8] else ''
                    dimension = 'DIMENSIÓN: ' + item[9] if item[9] else ''

                    detalles_tecnicos = ' - '.join(filter(None, [marca, modelo, serie, color, tipo, dimension]))
                    datos_pdf.append((item[0], item[1], item[2], item[3], detalles_tecnicos, item[10], item[11]))

                lista = ['Nro', 'Código\nInterno', 'Código\nPatrimonial', 'Denominación', 'Detalles tecnicos', 'Estado', 'Ubicación']
                colwidths = [25, 33, 60, 170, 200, 25, 200]
                iniciar_reporte(self.arc, lista, datos_pdf, colwidths, file_path)
            elif self.valor == 10:
                iniciar_conciliacion(self.arc, self.lista, datos, self.colwidths, file_path)
            elif self.valor > 11:
                iniciar_reporte_contable(self.arc, self.lista, datos, self.colwidths, file_path)
            else:
                iniciar_reporte(self.arc, self.lista, datos, self.colwidths, file_path)

            mb.showinfo(title="Acontar S.A.C.", message="Reporte PDF generado con éxito.", parent=self)
            self.focus_set()
        except Exception as e:
            mb.showerror(title="Error", message=f"Error al exportar PDF:\n{e}", parent=self)
            print(e)
            self.focus_set()

    def abrir_detalle_bien(self, _event=None):
        """Abre la ficha detallada del bien al hacer doble clic (en reportes de bienes individuales)."""
        if self.valor in (8, 10):
            return
        sel = self.tree.focus()
        if not sel:
            return
        vals = self.tree.item(sel).get("values", [])
        if not vals or len(vals) < 2:
            return
        codigo = vals[1]
        if codigo and str(codigo).strip().upper() != "TOTALES":
            win = Window_detalles(codigo=codigo)
            win.wait_window(win)
            self.focus_set()
            self.realizar_query()
