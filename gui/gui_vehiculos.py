import tkinter as tk
from tkinter import ttk, filedialog
from tkinter import messagebox as mb
from db.query import (
	rep_vehiculos, 
	registrar_vehiculo, 
	selec_vehiculos, 
	selec_vehiculos_tab1, 
	actualizar_vehiculo
)
from reportes.ficha_vehicular import iniciar_reporte
from gui.gui_detalles import Window_detalles
from utils.helpers import resource_path

class Window_vehiculos(tk.Toplevel):
	"""Ventana de gestión, inventario y ficha técnica de vehículos."""
	def __init__(self, root=None):
		super().__init__(root)
		self.title("Gestión y Ficha Técnica de Vehículos")
		self.geometry("1260x780")
		self.minsize(1100, 640)
		self.configure(bg="#f8fafc")
		self.transient(root)

		self._cargar_icono()
		self._centrar_ventana(1260, 780)
		self._configurar_estilos()

		# Variables para los 18 campos del vehículo (Tab 1)
		self.codi = tk.StringVar()
		self.v = [tk.StringVar() for _ in range(18)]

		# Variables de filtrado
		self.crit = tk.StringVar(value="Cod Patrimonial")
		self.camp = tk.StringVar()

		# Variables para los 11 campos técnicos (Tab 2)
		self.cod_tec = tk.StringVar()
		self.txt_tecnicos = []

		# Notebook
		self.notebook = ttk.Notebook(self, style="Vehiculos.TNotebook")
		self.tab1 = tk.Frame(self.notebook, bg="#f8fafc")
		self.tab2 = tk.Frame(self.notebook, bg="#f8fafc")

		self.notebook.add(self.tab1, text="  🚗  Información General e Inventario  ")
		self.notebook.add(self.tab2, text="  🔧  Inspección Técnica por Sistemas  ")
		self.notebook.pack(fill="both", expand=True, padx=8, pady=8)

		self.tab1_init()
		self.tab2_init()
		self.mostra_datos()

	# -------------------------------------------------------------------------
	# CONFIGURACIÓN Y ESTILOS
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

		# Notebook
		style.configure("Vehiculos.TNotebook",
			background="#f1f5f9",
			tabmargins=[0, 0, 0, 0]
		)
		style.configure("Vehiculos.TNotebook.Tab",
			font=("Segoe UI", 9, "bold"),
			padding=[14, 6],
			background="#e2e8f0",
			foreground="#475569"
		)
		style.map("Vehiculos.TNotebook.Tab",
			background=[("selected", "#ffffff")],
			foreground=[("selected", "#1e293b")]
		)

		# Cards Frame
		style.configure("Vehiculos.TLabelframe",
			background="#ffffff",
			relief="solid",
			borderwidth=1,
			bordercolor="#e2e8f0"
		)
		style.configure("Vehiculos.TLabelframe.Label",
			background="#ffffff",
			foreground="#334155",
			font=("Segoe UI", 9, "bold")
		)

		# Treeview
		style.configure("Vehiculos.Treeview",
			background="#ffffff",
			fieldbackground="#ffffff",
			foreground="#0f172a",
			font=("Segoe UI", 9),
			rowheight=24
		)
		style.configure("Vehiculos.Treeview.Heading",
			background="#f1f5f9",
			foreground="#475569",
			font=("Segoe UI", 8, "bold"),
			relief="flat",
			padding=(6, 6)
		)
		style.map("Vehiculos.Treeview",
			background=[("selected", "#2563eb")],
			foreground=[("selected", "#ffffff")]
		)

	# -------------------------------------------------------------------------
	# PESTAÑA 1: INFORMACIÓN GENERAL E INVENTARIO
	# -------------------------------------------------------------------------
	def tab1_init(self):
		contenedor = tk.Frame(self.tab1, bg="#f8fafc")
		contenedor.pack(fill="both", expand=True, padx=8, pady=8)

		# 1. Card Superior: Toolbar de búsqueda y acciones
		card_top = ttk.LabelFrame(contenedor, text=" ⚡ Búsqueda y Acciones del Vehículo ", style="Vehiculos.TLabelframe", padding=8)
		card_top.pack(fill="x", pady=(0, 8))

		# Fila de acciones principales
		ttk.Label(card_top, text="Código Patrimonial / Interno:", font=("Segoe UI", 9, "bold")).grid(row=0, column=0, padx=(4, 6), pady=4, sticky="w")
		self.etrCod = ttk.Entry(card_top, textvariable=self.codi, width=18, font=("Segoe UI", 9))
		self.etrCod.grid(row=0, column=1, padx=(0, 6), pady=4, sticky="w")
		self.etrCod.bind("<Return>", lambda _e: self.buscar_codigo(self.codi.get()))

		btnBus = ttk.Button(card_top, text="🔍 Buscar", command=lambda: self.buscar_codigo(self.codi.get()))
		btnBus.grid(row=0, column=2, padx=4, pady=4)

		btnAct = ttk.Button(card_top, text="💾 Guardar Cambios", command=self.actualizar)
		btnAct.grid(row=0, column=3, padx=4, pady=4)

		btnPdf = ttk.Button(card_top, text="📄 Generar Ficha Vehicular", command=self.generar_ficha)
		btnPdf.grid(row=0, column=4, padx=4, pady=4)

		btnLimpiar = ttk.Button(card_top, text="🧹 Limpiar", command=self.limpiar_campos)
		btnLimpiar.grid(row=0, column=5, padx=4, pady=4)

		# Separador
		ttk.Separator(card_top, orient="vertical").grid(row=0, column=6, sticky="ns", padx=10, pady=2)

		# Sección de filtro en la tabla
		ttk.Label(card_top, text="Filtrar por:").grid(row=0, column=7, padx=(4, 4), pady=4, sticky="w")

		self.lista_columnas = [
			'Item', 'Cod Interno', 'Acta', 'Ubicación', 'Entidad', 'Cod Patrimonial', 'Denominación', 
			'Nro de Placa', 'Carroceria', 'Marca', 'Modelo', 'Categoria', 'Nro Chasis', 'Nro de Ejes', 
			'Nro de Motor', 'Nro de Serie', 'Año Fabricación', 'Color', 'Combustible', 'Transmisión', 
			'Cilindrada', 'Kilometraje', 'Nro Tarjeta Vehicular'
		]

		self.cbxCri = ttk.Combobox(card_top, textvariable=self.crit, values=self.lista_columnas, state="readonly", width=16)
		self.cbxCri.grid(row=0, column=8, padx=4, pady=4)

		self.etrCrit = ttk.Entry(card_top, textvariable=self.camp, width=16)
		self.etrCrit.grid(row=0, column=9, padx=4, pady=4)
		self.etrCrit.bind("<Return>", lambda _e: self.filtrar())

		btnFiltrar = ttk.Button(card_top, text="🔎 Filtrar", command=self.filtrar)
		btnFiltrar.grid(row=0, column=10, padx=4, pady=4)

		btnTodos = ttk.Button(card_top, text="🔄 Ver Todos", command=self.mostra_datos)
		btnTodos.grid(row=0, column=11, padx=(4, 6), pady=4)

		# 2. Card Media: Formulario en 3 columnas estilizadas
		card_form = ttk.LabelFrame(contenedor, text=" 📋 Especificaciones Técnicas del Vehículo ", style="Vehiculos.TLabelframe", padding=8)
		card_form.pack(fill="x", pady=(0, 8))

		# Columna 1
		ttk.Label(card_form, text="Entidad:").grid(row=0, column=0, padx=4, pady=2, sticky="w")
		ttk.Entry(card_form, textvariable=self.v[0], width=20).grid(row=0, column=1, padx=4, pady=2, sticky="ew")

		ttk.Label(card_form, text="Denominación:").grid(row=1, column=0, padx=4, pady=2, sticky="w")
		ttk.Entry(card_form, textvariable=self.v[1], width=20).grid(row=1, column=1, padx=4, pady=2, sticky="ew")

		ttk.Label(card_form, text="N° Placa:").grid(row=2, column=0, padx=4, pady=2, sticky="w")
		ttk.Entry(card_form, textvariable=self.v[2], width=20).grid(row=2, column=1, padx=4, pady=2, sticky="ew")

		ttk.Label(card_form, text="Carrocería:").grid(row=3, column=0, padx=4, pady=2, sticky="w")
		ttk.Entry(card_form, textvariable=self.v[3], width=20).grid(row=3, column=1, padx=4, pady=2, sticky="ew")

		ttk.Label(card_form, text="Marca:").grid(row=4, column=0, padx=4, pady=2, sticky="w")
		ttk.Entry(card_form, textvariable=self.v[4], width=20).grid(row=4, column=1, padx=4, pady=2, sticky="ew")

		ttk.Label(card_form, text="Modelo:").grid(row=5, column=0, padx=4, pady=2, sticky="w")
		ttk.Entry(card_form, textvariable=self.v[5], width=20).grid(row=5, column=1, padx=4, pady=2, sticky="ew")

		# Columna 2
		ttk.Label(card_form, text="Categoría:").grid(row=0, column=2, padx=(12, 4), pady=2, sticky="w")
		ttk.Entry(card_form, textvariable=self.v[6], width=20).grid(row=0, column=3, padx=4, pady=2, sticky="ew")

		ttk.Label(card_form, text="N° Chasis (VIN):").grid(row=1, column=2, padx=(12, 4), pady=2, sticky="w")
		ttk.Entry(card_form, textvariable=self.v[7], width=20).grid(row=1, column=3, padx=4, pady=2, sticky="ew")

		ttk.Label(card_form, text="N° de Ejes:").grid(row=2, column=2, padx=(12, 4), pady=2, sticky="w")
		ttk.Entry(card_form, textvariable=self.v[8], width=20).grid(row=2, column=3, padx=4, pady=2, sticky="ew")

		ttk.Label(card_form, text="N° de Motor:").grid(row=3, column=2, padx=(12, 4), pady=2, sticky="w")
		ttk.Entry(card_form, textvariable=self.v[9], width=20).grid(row=3, column=3, padx=4, pady=2, sticky="ew")

		ttk.Label(card_form, text="N° de Serie:").grid(row=4, column=2, padx=(12, 4), pady=2, sticky="w")
		ttk.Entry(card_form, textvariable=self.v[10], width=20).grid(row=4, column=3, padx=4, pady=2, sticky="ew")

		ttk.Label(card_form, text="Año Fabricación:").grid(row=5, column=2, padx=(12, 4), pady=2, sticky="w")
		ttk.Entry(card_form, textvariable=self.v[11], width=20).grid(row=5, column=3, padx=4, pady=2, sticky="ew")

		# Columna 3
		ttk.Label(card_form, text="Color:").grid(row=0, column=4, padx=(12, 4), pady=2, sticky="w")
		ttk.Entry(card_form, textvariable=self.v[12], width=20).grid(row=0, column=5, padx=4, pady=2, sticky="ew")

		ttk.Label(card_form, text="Combustible:").grid(row=1, column=4, padx=(12, 4), pady=2, sticky="w")
		ttk.Entry(card_form, textvariable=self.v[13], width=20).grid(row=1, column=5, padx=4, pady=2, sticky="ew")

		ttk.Label(card_form, text="Transmisión:").grid(row=2, column=4, padx=(12, 4), pady=2, sticky="w")
		ttk.Entry(card_form, textvariable=self.v[14], width=20).grid(row=2, column=5, padx=4, pady=2, sticky="ew")

		ttk.Label(card_form, text="Cilindrada:").grid(row=3, column=4, padx=(12, 4), pady=2, sticky="w")
		ttk.Entry(card_form, textvariable=self.v[15], width=20).grid(row=3, column=5, padx=4, pady=2, sticky="ew")

		ttk.Label(card_form, text="Kilometraje:").grid(row=4, column=4, padx=(12, 4), pady=2, sticky="w")
		ttk.Entry(card_form, textvariable=self.v[16], width=20).grid(row=4, column=5, padx=4, pady=2, sticky="ew")

		ttk.Label(card_form, text="N° Tarjeta Vehicular:").grid(row=5, column=4, padx=(12, 4), pady=2, sticky="w")
		ttk.Entry(card_form, textvariable=self.v[17], width=20).grid(row=5, column=5, padx=4, pady=2, sticky="ew")

		card_form.columnconfigure(1, weight=1)
		card_form.columnconfigure(3, weight=1)
		card_form.columnconfigure(5, weight=1)

		# 3. Card Inferior: Directorio de Vehículos
		card_tree = ttk.LabelFrame(contenedor, text=" 📋 Directorio de Vehículos Registrados ", style="Vehiculos.TLabelframe", padding=8)
		card_tree.pack(fill="both", expand=True)

		cab = list(range(1, len(self.lista_columnas) + 1))
		self.tree = ttk.Treeview(card_tree, columns=cab, show="headings", style="Vehiculos.Treeview")

		for i, header in enumerate(self.lista_columnas):
			self.tree.heading(i + 1, text=header, anchor="center")
			self.tree.column(i + 1, width=105, stretch=False)

		# Anchos optimizados para columnas comunes
		self.tree.column(1, width=45, anchor="center")   # Item
		self.tree.column(2, width=90, anchor="center")   # CodInt
		self.tree.column(3, width=55, anchor="center")   # Acta
		self.tree.column(4, width=180, anchor="w")       # Ubicación
		self.tree.column(5, width=140, anchor="w")       # Entidad
		self.tree.column(6, width=120, anchor="center")  # CodPat
		self.tree.column(7, width=220, anchor="w")       # Denominación
		self.tree.column(8, width=95, anchor="center")   # Placa

		self.tree.tag_configure("odd",  background="#ffffff")
		self.tree.tag_configure("even", background="#f8fafc")

		scrollbarV = ttk.Scrollbar(card_tree, orient=tk.VERTICAL, command=self.tree.yview)
		scrollbarH = ttk.Scrollbar(card_tree, orient=tk.HORIZONTAL, command=self.tree.xview)
		self.tree.configure(yscroll=scrollbarV.set, xscroll=scrollbarH.set)

		self.tree.grid(row=0, column=0, sticky="nsew")
		scrollbarV.grid(row=0, column=1, sticky="ns")
		scrollbarH.grid(row=1, column=0, sticky="ew")

		card_tree.rowconfigure(0, weight=1)
		card_tree.columnconfigure(0, weight=1)

		self.tree.bind("<Double-Button-1>", self.mostrar_datos_)
		self.tree.bind("<Triple-Button-1>", self.mostrar_detalles_)

		# Barra Footer
		frame_footer = tk.Frame(contenedor, bg="#f8fafc")
		frame_footer.pack(fill="x", pady=(8, 0))

		frame_chip = tk.Frame(frame_footer, bg="#eff6ff", bd=1, relief="solid")
		frame_chip.pack(side="left")
		self.lbl_total = tk.Label(
			frame_chip,
			text="🚗  0 vehículos",
			bg="#eff6ff",
			fg="#1d4ed8",
			font=("Segoe UI", 9, "bold"),
			padx=10,
			pady=4
		)
		self.lbl_total.pack()

		lbl_tip = tk.Label(
			frame_footer,
			text="💡 Doble clic en una fila para cargar datos | Triple clic para ver ficha detallada del bien",
			bg="#f8fafc",
			fg="#64748b",
			font=("Segoe UI", 8, "italic")
		)
		lbl_tip.pack(side="left", padx=12)

	# -------------------------------------------------------------------------
	# PESTAÑA 2: INSPECCIÓN TÉCNICA POR SISTEMAS
	# -------------------------------------------------------------------------
	def tab2_init(self):
		contenedor = tk.Frame(self.tab2, bg="#f8fafc")
		contenedor.pack(fill="both", expand=True, padx=8, pady=8)

		# Barra superior de la Ficha Técnica
		card_top_tec = ttk.LabelFrame(contenedor, text=" 🔍 Identificación del Vehículo a Inspeccionar ", style="Vehiculos.TLabelframe", padding=8)
		card_top_tec.pack(fill="x", pady=(0, 8))

		ttk.Label(card_top_tec, text="Código Patrimonial o Interno:", font=("Segoe UI", 9, "bold")).pack(side="left", padx=(4, 6))
		self.etr_tec_cod = ttk.Entry(card_top_tec, textvariable=self.cod_tec, width=20, font=("Segoe UI", 9))
		self.etr_tec_cod.pack(side="left", padx=(0, 8))
		self.etr_tec_cod.bind("<Return>", lambda _e: self.cargar_datos_tecnicos())

		btnCargarTec = ttk.Button(card_top_tec, text="🔍 Cargar Sistemas", command=self.cargar_datos_tecnicos)
		btnCargarTec.pack(side="left", padx=4)

		btnGuardarTec = ttk.Button(card_top_tec, text="💾 Guardar Ficha Técnica", command=self.guardar_datos_tecnicos)
		btnGuardarTec.pack(side="left", padx=4)

		btnLimpiarTec = ttk.Button(card_top_tec, text="🧹 Limpiar Campos", command=self.limpiar_tecnicos)
		btnLimpiarTec.pack(side="left", padx=4)

		# Área con Scroll para los 11 sistemas
		card_scroll = ttk.LabelFrame(contenedor, text=" 🛠️ Detalle de los Sistemas y Componentes Mecánicos ", style="Vehiculos.TLabelframe", padding=6)
		card_scroll.pack(fill="both", expand=True)

		canvas = tk.Canvas(card_scroll, bg="#f8fafc", highlightthickness=0)
		scrollbar = ttk.Scrollbar(card_scroll, orient=tk.VERTICAL, command=canvas.yview)
		canvas.configure(yscrollcommand=scrollbar.set)

		scrollbar.pack(side="right", fill="y")
		canvas.pack(side="left", fill="both", expand=True)

		inner_frame = tk.Frame(canvas, bg="#f8fafc")
		canvas_window = canvas.create_window((0, 0), window=inner_frame, anchor="nw")

		def _configurar_canvas(event):
			canvas.itemconfig(canvas_window, width=event.width)
			canvas.configure(scrollregion=canvas.bbox("all"))

		canvas.bind("<Configure>", _configurar_canvas)
		inner_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))

		# Configuración de los 11 sistemas
		sistemas = [
			("1. SISTEMA DE MOTOR", "Cilindros, Carburador/cárter, Distribuidor/bomba de inyección, Bomba de gasolina, Purificador de aire"),
			("2. SISTEMA DE FRENOS", "Bomba de frenos, Zapatas y tambores, Discos y pastillas, Líquido de freno"),
			("3. SISTEMA DE REFRIGERACIÓN", "Radiador, Ventilador, Bomba de agua, Mangueras, Termostato"),
			("4. SISTEMA ELÉCTRICO", "Motor de arranque, Batería, Alternador, Bobina, Faros, Luces y cableados"),
			("5. SISTEMA DE TRANSMISIÓN", "Caja de cambios, Bomba de embrague, Caja de transferencia, Diferencial"),
			("6. SISTEMA DE DIRECCIÓN", "Volante, Caña de dirección, Cremallera, Rótulas, Terminales"),
			("7. SISTEMA DE SUSPENSIÓN", "Amortiguadores/muelles, Barra de torsión, Barra estabilizadora, Llantas"),
			("8. CARROCERÍA", "Capot, Maletera, Parachoques, Lunas, Parabrisas, Puertas, Asientos"),
			("9. ACCESORIOS", "Aire acondicionado, Alarma, Plumillas, Espejos, Cinturones, Antena"),
			("10. OTRAS CARACTERÍSTICAS", "Otras especificaciones relevantes del estado y componentes"),
			("11. APRECIACIÓN TÉCNICA GENERAL", "Conclusión general sobre el estado operativo del vehículo")
		]

		self.txt_tecnicos = []
		for idx, (titulo, subtitulo) in enumerate(sistemas):
			col = idx % 2
			row = idx // 2

			card_sys = tk.Frame(inner_frame, bg="#ffffff", bd=1, relief="solid", padx=8, pady=6)
			card_sys.grid(row=row, column=col, padx=6, pady=6, sticky="nsew")

			lbl_tit = tk.Label(card_sys, text=titulo, font=("Segoe UI", 9, "bold"), bg="#ffffff", fg="#1e293b", anchor="w")
			lbl_tit.pack(fill="x")

			lbl_sub = tk.Label(card_sys, text=subtitulo, font=("Segoe UI", 8, "italic"), bg="#ffffff", fg="#64748b", anchor="w")
			lbl_sub.pack(fill="x", pady=(0, 4))

			txt = tk.Text(card_sys, height=4, font=("Segoe UI", 9), relief="solid", bd=1, bg="#ffffff")
			txt.pack(fill="both", expand=True)

			self.txt_tecnicos.append(txt)

		inner_frame.columnconfigure(0, weight=1)
		inner_frame.columnconfigure(1, weight=1)

	# -------------------------------------------------------------------------
	# LÓGICA DE NEGOCIO (TAB 1)
	# -------------------------------------------------------------------------
	def buscar_codigo(self, buscar):
		codigo = str(buscar).strip()
		if not codigo:
			mb.showwarning(title="Atención", message="Ingrese un código patrimonial o interno.", parent=self)
			return

		try:
			k = selec_vehiculos_tab1(codigo)
			if k and len(k) > 0 and len(k[0]) >= 18:
				for i in range(18):
					val = k[0][i]
					self.v[i].set(str(val) if val is not None else "")
				# Sincronizar también con la pestaña técnica
				self.cod_tec.set(codigo)
			else:
				mb.showinfo(title="No encontrado", message=f"No se encontraron datos para el vehículo con código '{codigo}'.", parent=self)
		except Exception as e:
			mb.showerror(title="Error al buscar", message=f"Ocurrió un error:\n{e}", parent=self)

	def actualizar(self):
		codigo = self.codi.get().strip()
		if not codigo:
			mb.showwarning(title="Atención", message="Ingrese el código del vehículo a actualizar.", parent=self)
			return

		data = [self.v[i].get().strip() for i in range(18)]
		try:
			actualizar_vehiculo(codigo, data)
			self.mostra_datos()
			mb.showinfo(title="Acontar S.A.C.", message="Datos del vehículo actualizados correctamente.", parent=self)
			self.focus_set()
		except Exception as e:
			mb.showerror(title="Error", message=f"Ocurrió un error al actualizar:\n{e}", parent=self)
			self.focus_set()

	def generar_ficha(self):
		codigo = self.codi.get().strip()
		if not codigo:
			mb.showwarning(title="Atención", message="Seleccione o busque un vehículo para generar su ficha.", parent=self)
			return

		try:
			file_path = filedialog.askdirectory(initialdir='report_actas/fichas_vehiculares/', title="Seleccionar carpeta de destino")
			if file_path:
				iniciar_reporte(codigo, file_path)
				mb.showinfo(title='Acontar S.A.C.', message="La Ficha Vehicular se generó con éxito.", parent=self)
				self.focus_set()
		except Exception as e:
			mb.showerror(title='¡Atención!', message=f"Ocurrió un error al generar la ficha:\n{e}", parent=self)
			self.focus_set()

	def mostra_datos(self):
		for item in self.tree.get_children():
			self.tree.delete(item)

		try:
			r = rep_vehiculos()
			for cell, contact in enumerate(r or [], 1):
				b = list(contact)
				b.insert(0, str(cell))
				tag = "odd" if cell % 2 == 1 else "even"
				self.tree.insert("", tk.END, values=b, tags=(tag,))
			n = len(r or [])
			self.lbl_total.config(text=f"🚗  {n} {'vehículo' if n == 1 else 'vehículos'}")
		except Exception as e:
			print(f"Error cargando vehículos: {e}")

	def mostrar_datos_(self, *args):
		fila = self.tree.focus()
		if not fila:
			return
		vnb = self.tree.item(fila).get("values", [])
		if not vnb or len(vnb) < 2:
			return

		# Columna 1 en la tupla es CodInt, Columna 5 es CodPat
		cod_int = str(vnb[1]) if vnb[1] is not None else ""
		cod_pat = str(vnb[5]) if len(vnb) > 5 and vnb[5] is not None else ""
		codigo = cod_pat or cod_int

		self.codi.set(codigo)
		self.cod_tec.set(codigo)
		self.buscar_codigo(codigo)

	def mostrar_detalles_(self, *args):
		fila = self.tree.focus()
		if not fila:
			return
		vnb = self.tree.item(fila).get("values", [])
		if not vnb or len(vnb) < 2:
			return

		codigo = str(vnb[1])
		self.codi.set(codigo)
		self.buscar_codigo(codigo)

		ventana = Window_detalles(codigo=codigo)
		ventana.wait_window(ventana)
		self.focus_set()
		self.after(50, self.mostra_datos)

	def filtrar(self):
		columna = self.crit.get().strip()
		valor = self.camp.get().strip().lower()

		if not valor:
			self.mostra_datos()
			return

		if columna not in self.lista_columnas:
			columna = "Cod Patrimonial"

		col_idx = self.lista_columnas.index(columna)

		filas_coinciden = []
		for item in self.tree.get_children():
			valores = self.tree.item(item)["values"]
			if col_idx < len(valores) and valor in str(valores[col_idx]).lower():
				filas_coinciden.append(valores)

		for item in self.tree.get_children():
			self.tree.delete(item)

		for cell, valores in enumerate(filas_coinciden, 1):
			tag = "odd" if cell % 2 == 1 else "even"
			v_mod = list(valores)
			v_mod[0] = str(cell)
			self.tree.insert("", tk.END, values=v_mod, tags=(tag,))

		n = len(filas_coinciden)
		self.lbl_total.config(text=f"🚗  {n} {'vehículo encontrado' if n == 1 else 'vehículos encontrados'}")

	def limpiar_campos(self):
		self.codi.set("")
		for var in self.v:
			var.set("")

	# -------------------------------------------------------------------------
	# LÓGICA DE NEGOCIO (TAB 2: FICHA TÉCNICA)
	# -------------------------------------------------------------------------
	def cargar_datos_tecnicos(self):
		codigo = self.cod_tec.get().strip()
		if not codigo:
			mb.showwarning(title="Atención", message="Ingrese el código patrimonial o interno del vehículo.", parent=self)
			return

		try:
			j = selec_vehiculos(codigo)
			if j and len(j) > 0 and len(j[0]) >= 11:
				datos = j[0]
				for widget, dato in zip(self.txt_tecnicos, datos):
					widget.delete("1.0", "end")
					widget.insert("end", str(dato) if dato is not None else "")
			else:
				mb.showinfo(title="Sin registro previo", message=f"No se encontró ficha técnica para [{codigo}]. Puede ingresar la información ahora.", parent=self)
		except Exception as e:
			mb.showerror(title="Error al cargar", message=f"Ocurrió un error:\n{e}", parent=self)

	def guardar_datos_tecnicos(self):
		codigo = self.cod_tec.get().strip()
		if not codigo:
			mb.showwarning(title="Atención", message="Ingrese el código patrimonial o interno del vehículo.", parent=self)
			return

		try:
			data = [txt.get("1.0", "end-1c").strip() for txt in self.txt_tecnicos]
			registrar_vehiculo(codigo, data)
			mb.showinfo(title="Acontar S.A.C.", message="Ficha de inspección técnica guardada exitosamente.", parent=self)
			self.focus_set()
		except Exception as e:
			mb.showerror(title="Error al guardar", message=f"No se pudo guardar la ficha técnica:\n{e}", parent=self)
			self.focus_set()

	def limpiar_tecnicos(self):
		for txt in self.txt_tecnicos:
			txt.delete("1.0", "end")
