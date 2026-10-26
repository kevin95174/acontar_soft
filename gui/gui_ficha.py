import tkinter as tk
from datetime import date
from tkinter import ttk, filedialog
from tkinter import messagebox as mb
from reportes.ficha import iniciar_reporte
from gui.gui_detalles import Window_detalles
from db.query import (
	buscar_criterio_acta_ant,
	ficha_levantamiento,
	analisis_ficha,
	mostrar_d_personal,
	inventariador,
	select_inventariador,
	select_equipo
)
from utils.helpers import resource_path


class Window_Acta(tk.Toplevel):
	"""Ventana de consulta, análisis y generación de Ficha de Levantamiento de Información."""

	def __init__(self, root=None, acta=None, valor=None, user=None, team=None):
		super().__init__(root)
		self.title("Ficha de Levantamiento de Información")
		self.geometry("1260x760")
		self.minsize(1060, 620)
		self.configure(bg="#f8fafc")
		self.transient(root)

		self._acta_inicial = acta
		self.valor = valor
		self.user = user
		self.team = team

		self._cargar_icono()
		self._centrar_ventana(1260, 760)
		self._configurar_estilos()

		self.variables()
		self.widgets()
		self.tree_view()
		self.tree.bind("<Double-Button-1>", self.mostrar_datos_)

		if self._acta_inicial:
			self.acta.set(str(self._acta_inicial))
			self.after(50, self.iniciar_filtro)

	# -------------------------------------------------------------------------
	# CONFIGURACIÓN DE VENTANA Y ESTILOS
	# -------------------------------------------------------------------------
	def _cargar_icono(self):
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

	def _configurar_estilos(self):
		style = ttk.Style(self)

		# LabelFrame Card
		style.configure("Ficha.TLabelframe",
			background="#ffffff",
			relief="solid",
			borderwidth=1,
			bordercolor="#e2e8f0"
		)
		style.configure("Ficha.TLabelframe.Label",
			background="#ffffff",
			foreground="#334155",
			font=("Segoe UI", 9, "bold")
		)

		# Treeview moderno
		style.configure("Ficha.Treeview",
			background="#ffffff",
			fieldbackground="#ffffff",
			foreground="#0f172a",
			font=("Segoe UI", 9),
			rowheight=24
		)
		style.configure("Ficha.Treeview.Heading",
			background="#f1f5f9",
			foreground="#475569",
			font=("Segoe UI", 8, "bold"),
			relief="flat",
			padding=(6, 6)
		)
		style.map("Ficha.Treeview",
			background=[("selected", "#2563eb")],
			foreground=[("selected", "#ffffff")]
		)

	def variables(self):
		self.acta = tk.StringVar()
		self.ubic = tk.StringVar()
		self.usua = tk.StringVar()
		self.ndni = tk.StringVar()
		self.inve = tk.StringVar()
		self.idni = tk.StringVar()
		self.equi = tk.StringVar()
		self.fech = tk.StringVar()
		self.crit = tk.StringVar(value="Denominación")
		self.camp = tk.StringVar()

		# Estadísticas de estado
		self.nuev = tk.StringVar(value="0")
		self.buen = tk.StringVar(value="0")
		self.regu = tk.StringVar(value="0")
		self.malo = tk.StringVar(value="0")
		self.Best = tk.StringVar(value="0")
		self.test = tk.StringVar(value="0")

		# Estadísticas de situación
		self.euso = tk.StringVar(value="0")
		self.desu = tk.StringVar(value="0")
		self.Bsit = tk.StringVar(value="0")
		self.tsit = tk.StringVar(value="0")

		# Balance general
		self.Tban = tk.StringVar(value="0")
		self.Tida = tk.StringVar(value="0")
		self.Tiea = tk.StringVar(value="0")
		self.Tfal = tk.StringVar(value="0")
		self.Tsob = tk.StringVar(value="0")
		self.Tinv = tk.StringVar(value="0")

		self.nacta = tk.StringVar()
		self.ba = tk.IntVar()

	# -------------------------------------------------------------------------
	# CONSTRUCCIÓN DE INTERFAZ
	# -------------------------------------------------------------------------
	def widgets(self):
		self.contenedor = tk.Frame(self, bg="#f8fafc")
		self.contenedor.pack(fill="both", expand=True, padx=12, pady=10)

		# Panel Superior dividido en 2 Cards (Izquierda: Datos de Ficha | Derecha: Resumen Estadístico)
		f_top = tk.Frame(self.contenedor, bg="#f8fafc")
		f_top.pack(fill="x", pady=(0, 10))

		# =====================================================================
		# CARD 1 (IZQUIERDA): DATOS DE LA FICHA Y FILTROS
		# =====================================================================
		card_ficha = ttk.LabelFrame(
			f_top,
			text=" 📋 Datos de la Ficha y Responsables ",
			style="Ficha.TLabelframe",
			padding=10
		)
		card_ficha.pack(side="left", fill="both", expand=True, padx=(0, 6))

		try:
			lista_inv = inventariador() or []
			personal = [i[0] for i in lista_inv if i]
		except Exception:
			personal = []

		today = date.today()
		self.fech.set(today.strftime("%d/%m/%Y"))

		# Fila 0: Nro de Ficha + Botones Buscar y PDF + Fecha
		ttk.Label(card_ficha, text="N° de Ficha:", font=("Segoe UI", 9, "bold")).grid(row=0, column=0, padx=4, pady=3, sticky="w")

		f_acta_bar = tk.Frame(card_ficha, bg="#ffffff")
		f_acta_bar.grid(row=0, column=1, columnspan=3, padx=4, pady=3, sticky="ew")

		self.etrnAct = ttk.Entry(f_acta_bar, textvariable=self.acta, width=10, justify="center", font=("Segoe UI", 9, "bold"))
		self.etrnAct.pack(side="left", padx=(0, 6))
		self.etrnAct.bind("<Return>", lambda _e: self.iniciar_filtro())

		btnBusc = ttk.Button(f_acta_bar, text="🔍 Buscar Ficha", command=self.iniciar_filtro)
		btnBusc.pack(side="left", padx=(0, 6))

		btnGene = ttk.Button(f_acta_bar, text="📄 Exportar PDF", command=self.acta_inventario)
		btnGene.pack(side="left", padx=(0, 12))

		ttk.Label(f_acta_bar, text="Fecha Inv.:").pack(side="left", padx=(4, 4))
		ttk.Entry(f_acta_bar, textvariable=self.fech, width=12, justify="center").pack(side="left")

		# Fila 1: Ubicación
		ttk.Label(card_ficha, text="Ubicación:").grid(row=1, column=0, padx=4, pady=3, sticky="w")
		ttk.Entry(card_ficha, textvariable=self.ubic).grid(row=1, column=1, columnspan=3, padx=4, pady=3, sticky="ew")

		# Fila 2: Usuario y DNI Usuario
		ttk.Label(card_ficha, text="Responsable:").grid(row=2, column=0, padx=4, pady=3, sticky="w")
		ttk.Entry(card_ficha, textvariable=self.usua).grid(row=2, column=1, padx=4, pady=3, sticky="ew")

		ttk.Label(card_ficha, text="DNI Resp.:").grid(row=2, column=2, padx=(8, 4), pady=3, sticky="w")
		ttk.Entry(card_ficha, textvariable=self.ndni, width=14, justify="center").grid(row=2, column=3, padx=4, pady=3, sticky="ew")

		# Fila 3: Inventariador
		ttk.Label(card_ficha, text="Inventariador:").grid(row=3, column=0, padx=4, pady=3, sticky="w")
		cbxInve = ttk.Combobox(card_ficha, textvariable=self.inve, state="readonly", values=personal)
		cbxInve.grid(row=3, column=1, columnspan=3, padx=4, pady=3, sticky="ew")
		cbxInve.bind("<<ComboboxSelected>>", self.actualizar_entry)

		# Fila 4: DNI Inventariador y Equipo
		ttk.Label(card_ficha, text="DNI Inv.:").grid(row=4, column=0, padx=4, pady=3, sticky="w")
		ttk.Entry(card_ficha, textvariable=self.idni, width=16, justify="center").grid(row=4, column=1, padx=4, pady=3, sticky="ew")

		ttk.Label(card_ficha, text="Equipo:").grid(row=4, column=2, padx=(8, 4), pady=3, sticky="w")
		ttk.Entry(card_ficha, textvariable=self.equi, width=14, justify="center").grid(row=4, column=3, padx=4, pady=3, sticky="ew")

		# Separador horizontal antes del filtro
		ttk.Separator(card_ficha, orient="horizontal").grid(row=5, column=0, columnspan=4, sticky="ew", pady=(8, 6))

		# Fila 6: Filtro en tabla
		ttk.Label(card_ficha, text="Filtrar tabla:").grid(row=6, column=0, padx=4, pady=2, sticky="w")

		f_filtro = tk.Frame(card_ficha, bg="#ffffff")
		f_filtro.grid(row=6, column=1, columnspan=3, padx=4, pady=2, sticky="ew")

		self.criterios_filtro = [
			'Código Interno', 'Código Patrimonial', 'Denominación', 'Marca', 'Modelo',
			'Tipo', 'Color', 'Serie', 'Dimensiones', 'Otros', 'Situacion',
			'Estado de Conservación', 'Observaciones'
		]
		cbxCri = ttk.Combobox(f_filtro, textvariable=self.crit, state="readonly", values=self.criterios_filtro, width=18)
		cbxCri.pack(side="left", padx=(0, 6))

		etrCrit = ttk.Entry(f_filtro, textvariable=self.camp)
		etrCrit.pack(side="left", fill="x", expand=True, padx=(0, 6))
		etrCrit.bind("<Return>", lambda _e: self.filtrar())

		btnCrit = ttk.Button(f_filtro, text="🔎 Filtrar", command=self.filtrar)
		btnCrit.pack(side="left", padx=(0, 4))

		btnReset = ttk.Button(f_filtro, text="🔄 Todos", command=self.iniciar_filtro)
		btnReset.pack(side="left")

		card_ficha.columnconfigure(1, weight=2)
		card_ficha.columnconfigure(3, weight=1)

		# =====================================================================
		# CARD 2 (DERECHA): RESUMEN ESTADÍSTICO DE LA FICHA
		# =====================================================================
		card_stats = ttk.LabelFrame(
			f_top,
			text=" 📊 Resumen y Balance de la Ficha ",
			style="Ficha.TLabelframe",
			padding=10
		)
		card_stats.pack(side="right", fill="both", padx=(6, 0))

		# Encabezados de sección
		tk.Label(card_stats, text="Conservación", bg="#ffffff", fg="#1e293b", font=("Segoe UI", 8, "bold")).grid(row=0, column=0, columnspan=2, sticky="w", padx=4, pady=(0, 4))
		tk.Label(card_stats, text="Situación", bg="#ffffff", fg="#1e293b", font=("Segoe UI", 8, "bold")).grid(row=0, column=2, columnspan=2, sticky="w", padx=(12, 4), pady=(0, 4))
		tk.Label(card_stats, text="Balance General", bg="#ffffff", fg="#1e293b", font=("Segoe UI", 8, "bold")).grid(row=0, column=4, columnspan=2, sticky="w", padx=(12, 4), pady=(0, 4))

		# Columna Conservación
		est_fields = [
			("Nuevos:", self.nuev, False),
			("Buenos:", self.buen, False),
			("Regulares:", self.regu, False),
			("Malos:", self.malo, False),
			("En Blanco:", self.Best, False),
			("Total Est.:", self.test, True),
		]
		for r_idx, (label_txt, var, is_bold) in enumerate(est_fields, start=1):
			font_st = ("Segoe UI", 8, "bold") if is_bold else ("Segoe UI", 8)
			ttk.Label(card_stats, text=label_txt, font=font_st).grid(row=r_idx, column=0, padx=4, pady=2, sticky="w")
			ttk.Entry(card_stats, textvariable=var, width=7, justify="center", font=font_st, state="readonly").grid(row=r_idx, column=1, padx=4, pady=2)

		# Columna Situación
		sit_fields = [
			("En Uso:", self.euso, False),
			("En Desuso:", self.desu, False),
			("En Blanco:", self.Bsit, False),
		]
		for r_idx, (label_txt, var, is_bold) in enumerate(sit_fields, start=1):
			ttk.Label(card_stats, text=label_txt, font=("Segoe UI", 8)).grid(row=r_idx, column=2, padx=(12, 4), pady=2, sticky="w")
			ttk.Entry(card_stats, textvariable=var, width=7, justify="center", font=("Segoe UI", 8), state="readonly").grid(row=r_idx, column=3, padx=4, pady=2)

		ttk.Label(card_stats, text="Total Sit.:", font=("Segoe UI", 8, "bold")).grid(row=6, column=2, padx=(12, 4), pady=2, sticky="w")
		ttk.Entry(card_stats, textvariable=self.tsit, width=7, justify="center", font=("Segoe UI", 8, "bold"), state="readonly").grid(row=6, column=3, padx=4, pady=2)

		# Columna Balance General
		bal_fields = [
			("Inv. Anterior:", self.Tban, False),
			("De otras áreas:", self.Tida, False),
			("En otras áreas:", self.Tiea, False),
			("Faltantes:", self.Tfal, False),
			("Sobrantes:", self.Tsob, False),
			("Total Inv.:", self.Tinv, True),
		]
		for r_idx, (label_txt, var, is_bold) in enumerate(bal_fields, start=1):
			font_st = ("Segoe UI", 8, "bold") if is_bold else ("Segoe UI", 8)
			ttk.Label(card_stats, text=label_txt, font=font_st).grid(row=r_idx, column=4, padx=(12, 4), pady=2, sticky="w")
			ttk.Entry(card_stats, textvariable=var, width=8, justify="center", font=font_st, state="readonly").grid(row=r_idx, column=5, padx=4, pady=2)

	def tree_view(self):
		# Card de Tabla
		frame_tabla = ttk.LabelFrame(
			self.contenedor,
			text=" 📦 Bienes Registrados en la Ficha ",
			style="Ficha.TLabelframe",
			padding=8
		)
		frame_tabla.pack(fill="both", expand=True)

		cab = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15]
		self.lista = [
			'', 'Item', 'Código Interno', 'Código Patrimonial', 'Denominación',
			'Marca', 'Modelo', 'Tipo', 'Color', 'Serie', 'Dimensiones',
			'Otros', 'Situacion', 'Estado de Conservación', 'Observaciones'
		]

		self.tree = ttk.Treeview(frame_tabla, columns=cab, show="headings", style="Ficha.Treeview")

		self.tree.heading(1,  text="",               anchor="center")
		self.tree.heading(2,  text="Item",           anchor="center")
		self.tree.heading(3,  text="Cód. Interno",   anchor="center")
		self.tree.heading(4,  text="Cód. Patrimonial", anchor="center")
		self.tree.heading(5,  text="Denominación",   anchor="w")
		self.tree.heading(6,  text="Marca")
		self.tree.heading(7,  text="Modelo")
		self.tree.heading(8,  text="Tipo")
		self.tree.heading(9,  text="Color")
		self.tree.heading(10, text="Serie")
		self.tree.heading(11, text="Dimensión")
		self.tree.heading(12, text="Otros")
		self.tree.heading(13, text="Situación",      anchor="center")
		self.tree.heading(14, text="Conservación",   anchor="center")
		self.tree.heading(15, text="Observaciones")

		self.tree.column(1,  width=0,   stretch=False, anchor="center")
		self.tree.column(2,  width=50,  stretch=False, anchor="center")
		self.tree.column(3,  width=95,  stretch=False, anchor="center")
		self.tree.column(4,  width=110, stretch=False, anchor="center")
		self.tree.column(5,  width=290, stretch=False, anchor="w")
		self.tree.column(6,  width=100, stretch=False)
		self.tree.column(7,  width=100, stretch=False)
		self.tree.column(8,  width=100, stretch=False)
		self.tree.column(9,  width=90,  stretch=False)
		self.tree.column(10, width=105, stretch=False)
		self.tree.column(11, width=95,  stretch=False)
		self.tree.column(12, width=100, stretch=False)
		self.tree.column(13, width=90,  stretch=False, anchor="center")
		self.tree.column(14, width=100, stretch=False, anchor="center")
		self.tree.column(15, width=130, stretch=False)

		self.tree.tag_configure("odd",  background="#ffffff")
		self.tree.tag_configure("even", background="#f8fafc")

		scrollbarV = ttk.Scrollbar(frame_tabla, orient=tk.VERTICAL,   command=self.tree.yview)
		scrollbarH = ttk.Scrollbar(frame_tabla, orient=tk.HORIZONTAL, command=self.tree.xview)
		self.tree.configure(yscroll=scrollbarV.set, xscroll=scrollbarH.set)

		self.tree.grid(column=0, row=0, sticky="nsew")
		scrollbarV.grid(column=1, row=0, sticky="ns")
		scrollbarH.grid(column=0, row=1, sticky="ew")

		frame_tabla.rowconfigure(0, weight=1)
		frame_tabla.columnconfigure(0, weight=1)

		# Barra inferior
		frame_footer = tk.Frame(self.contenedor, bg="#f8fafc")
		frame_footer.pack(fill="x", pady=(8, 0))

		frame_chip = tk.Frame(frame_footer, bg="#eff6ff", bd=1, relief="solid")
		frame_chip.pack(side="left")
		self.lbl_total = tk.Label(
			frame_chip,
			text="📋  0 bienes en ficha",
			bg="#eff6ff",
			fg="#1d4ed8",
			font=("Segoe UI", 9, "bold"),
			padx=10,
			pady=4
		)
		self.lbl_total.pack()

		lbl_tip = tk.Label(
			frame_footer,
			text="💡 Doble clic sobre cualquier bien de la lista para ver o editar sus detalles",
			bg="#f8fafc",
			fg="#64748b",
			font=("Segoe UI", 8, "italic")
		)
		lbl_tip.pack(side="left", padx=12)

	# -------------------------------------------------------------------------
	# LÓGICA DE DATOS Y EVENTOS
	# -------------------------------------------------------------------------
	def iniciar_filtro(self, *args):
		acta_val = self.acta.get().strip()
		if not acta_val:
			mb.showwarning(title="Atención", message="Ingrese un número de Ficha para consultar.", parent=self)
			return

		for item in self.tree.get_children():
			self.tree.delete(item)

		try:
			r = ficha_levantamiento(acta_val) or []
			for idx, row in enumerate(r, 1):
				tag = "odd" if idx % 2 == 1 else "even"
				self.tree.insert("", tk.END, values=row, tags=(tag,))

			n = len(r)
			self.lbl_total.config(text=f"📋  {n} {'bien en ficha' if n == 1 else 'bienes en ficha'}")

			datos_usu = mostrar_d_personal(acta_val)
			if datos_usu and len(datos_usu) > 0:
				u = datos_usu[0]
				self.ubic.set(f"{u[1] or ''} - {u[2] or ''} - {u[3] or ''}")
				self.ndni.set(u[4] or "")
				self.usua.set(u[5] or "")

				if len(u) > 6 and u[6]:
					equipo = select_equipo(u[6])
					if equipo and len(equipo) > 0:
						self.inve.set(equipo[0][0] or "")
						self.idni.set(equipo[0][1] or "")
						self.equi.set(equipo[0][2] or "")

			analisis = analisis_ficha(acta_val)
			if analisis and len(analisis) >= 17:
				self.nuev.set(analisis[1])
				self.buen.set(analisis[2])
				self.regu.set(analisis[3])
				self.malo.set(analisis[4])
				self.test.set(analisis[13])
				self.euso.set(analisis[5])
				self.desu.set(analisis[6])
				self.tsit.set(analisis[14])
				self.Tban.set(analisis[7])
				self.Tida.set(analisis[8])
				self.Tiea.set(analisis[9])
				self.Tfal.set(analisis[10])
				self.Tsob.set(analisis[11])
				self.Tinv.set(analisis[12])
				self.Best.set(analisis[15])
				self.Bsit.set(analisis[16])
		except Exception as e:
			print(f"Error en iniciar_filtro: {e}")
			mb.showerror(title="Error", message=f"No se pudieron cargar todos los datos de la ficha [{acta_val}]:\n{e}", parent=self)

	def buscar_criterio(self):
		for item in self.tree.get_children():
			self.tree.delete(item)
		r = buscar_criterio_acta_ant(self.acta.get(), self.crit.get(), self.camp.get()) or []
		for cell, contact in enumerate(r, 1):
			b = list(contact)
			b.insert(0, str(cell))
			tag = "odd" if cell % 2 == 1 else "even"
			self.tree.insert("", tk.END, values=b, tags=(tag,))
		self.lbl_total.config(text=f"📋  {len(r)} bienes filtrados")

	def acta_inventario(self):
		if not self.acta.get().strip():
			mb.showwarning(title="Atención", message="Busque una ficha antes de exportar a PDF.", parent=self)
			return
		try:
			file_path = filedialog.askdirectory(initialdir="fichas_inventario", title="Seleccionar carpeta de destino")
			if file_path:
				iniciar_reporte(
					self.acta.get(),
					file_path,
					self.inve.get(),
					self.idni.get(),
					self.equi.get(),
					self.ba.get(),
					self.fech.get(),
					self.acta.get()
				)
				mb.showinfo(title="¡Atención!", message="Ficha PDF generada con éxito.", parent=self)
			self.focus_set()
		except Exception as e:
			mb.showerror(title="Error", message=f"Error al generar el acta:\n{e}", parent=self)
			self.focus_set()
			print(e)

	def mostrar_datos_(self, *args):
		try:
			curActa = self.tree.focus()
			if not curActa:
				return
			vnb = self.tree.item(curActa).get("values", [])
			if not vnb or len(vnb) < 3:
				return
			dato = vnb[2]
			ventana_detalles = Window_detalles(codigo=dato)
			ventana_detalles.wait_window(ventana_detalles)
			self.focus_set()
			self.after(50, self.iniciar_filtro)
		except Exception as e:
			self.focus_set()
			print(e)

	def actualizar_entry(self, event=None):
		try:
			resultado = select_inventariador(self.inve.get())
			if resultado and len(resultado) >= 2:
				self.idni.set(resultado[0])
				self.equi.set(resultado[1])
		except Exception as e:
			print(f"Error en actualizar_entry: {e}")

	def filtrar(self):
		columna = self.crit.get().strip()
		valor = self.camp.get().strip().lower()

		if not valor:
			self.iniciar_filtro()
			return

		# Mapear nombre limpio o con salto de línea
		col_clean = columna.replace("\n", " ")
		lista_clean = [c.replace("\n", " ") for c in self.lista]
		if col_clean not in lista_clean:
			col_idx = 4  # Denominación por defecto
		else:
			col_idx = lista_clean.index(col_clean)

		filas_coinciden = []
		for item in self.tree.get_children():
			valores = self.tree.item(item)["values"]
			if col_idx < len(valores) and valor in str(valores[col_idx]).lower():
				filas_coinciden.append(tuple(valores))

		for item in self.tree.get_children():
			self.tree.delete(item)

		for idx, valores in enumerate(filas_coinciden, 1):
			tag = "odd" if idx % 2 == 1 else "even"
			self.tree.insert("", "end", text="", values=valores, tags=(tag,))

		n = len(filas_coinciden)
		self.lbl_total.config(text=f"📋  {n} {'bien encontrado' if n == 1 else 'bienes encontrados'}")
