import tkinter as tk
from tkinter import ttk
from tkinter import messagebox as mb
from gui.gui_print import Window_print
from db.query import (
	delete_sobrante, 
	registrar_sobrantes, 
	mostrar_sobrantes, 
	mostrar_d_personal, 
	actualizar_sobrante
)
from label.label_sobrante import build_label_sobrante
from utils.helpers import resource_path

class Window_surplus(tk.Toplevel):
	"""Ventana de registro, consulta y administración de bienes sobrantes."""
	def __init__(self, root=None, valor=None):
		super().__init__(root)
		self.title("Gestión de Bienes Sobrantes")
		self.geometry("1240x760")
		self.minsize(1050, 620)
		self.configure(bg="#f8fafc")
		self.transient(root)

		self._cargar_icono()
		self._centrar_ventana(1240, 760)
		self._configurar_estilos()

		self.variables()
		self.widgets()
		self.tree_view()

		if valor:
			self.acta.set(valor)
			self.buscar()
		else:
			self.mostrar_todos()

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

		# Cards Frame
		style.configure("Sobrante.TLabelframe",
			background="#ffffff",
			relief="solid",
			borderwidth=1,
			bordercolor="#e2e8f0"
		)
		style.configure("Sobrante.TLabelframe.Label",
			background="#ffffff",
			foreground="#334155",
			font=("Segoe UI", 9, "bold")
		)

		# Treeview
		style.configure("Sobrante.Treeview",
			background="#ffffff",
			fieldbackground="#ffffff",
			foreground="#0f172a",
			font=("Segoe UI", 9),
			rowheight=24
		)
		style.configure("Sobrante.Treeview.Heading",
			background="#f1f5f9",
			foreground="#475569",
			font=("Segoe UI", 8, "bold"),
			relief="flat",
			padding=(6, 6)
		)
		style.map("Sobrante.Treeview",
			background=[("selected", "#2563eb")],
			foreground=[("selected", "#ffffff")]
		)

	def variables(self):
		self.acta = tk.StringVar()
		self.local = tk.StringVar()
		self.area = tk.StringVar()
		self.oficina = tk.StringVar()
		self.den = tk.StringVar()
		self.estado = tk.StringVar(value="BUENO")
		self.marca = tk.StringVar(value="S/M")
		self.modelo = tk.StringVar(value="S/M")
		self.serie = tk.StringVar(value="S/S")
		self.color = tk.StringVar()
		self.dim = tk.StringVar(value="S/D")
		self.obs = tk.StringVar(value="N/A")
		self.tip = tk.StringVar(value="S/T")
		self.otr = tk.StringVar()
		self.sit = tk.StringVar()
		self.cb = tk.IntVar(value=1)
		self.item_actual = None

	def widgets(self):
		contenedor = tk.Frame(self, bg="#f8fafc")
		contenedor.pack(fill="both", expand=True, padx=12, pady=10)

		# =========================================================================
		# PANEL SUPERIOR: CARDS DE FORMULARIO Y ACCIONES
		# =========================================================================
		f_top = tk.Frame(contenedor, bg="#f8fafc")
		f_top.pack(fill="x", pady=(0, 10))

		# 1. Card Ubicación y Ficha
		card_ubi = ttk.LabelFrame(f_top, text=" 📍 Ficha y Ubicación ", style="Sobrante.TLabelframe", padding=10)
		card_ubi.pack(side="left", fill="both", padx=(0, 8))

		ttk.Label(card_ubi, text="Ficha / Acta:").grid(row=0, column=0, padx=4, pady=3, sticky="w")
		f_acta = tk.Frame(card_ubi, bg="#ffffff")
		f_acta.grid(row=0, column=1, padx=4, pady=3, sticky="ew")

		self.etrActa = ttk.Entry(f_acta, textvariable=self.acta, width=8, justify="center")
		self.etrActa.pack(side="left", padx=(0, 4))
		self.etrActa.bind("<Return>", lambda _e: self.buscar())

		btnBuscarActa = ttk.Button(f_acta, text="🔍", width=3, command=self.buscar)
		btnBuscarActa.pack(side="left")

		ttk.Label(card_ubi, text="Local:").grid(row=1, column=0, padx=4, pady=3, sticky="w")
		ttk.Entry(card_ubi, textvariable=self.local, width=22).grid(row=1, column=1, padx=4, pady=3, sticky="ew")

		ttk.Label(card_ubi, text="Área:").grid(row=2, column=0, padx=4, pady=3, sticky="w")
		ttk.Entry(card_ubi, textvariable=self.area, width=22).grid(row=2, column=1, padx=4, pady=3, sticky="ew")

		ttk.Label(card_ubi, text="Oficina:").grid(row=3, column=0, padx=4, pady=3, sticky="w")
		ttk.Entry(card_ubi, textvariable=self.oficina, width=22).grid(row=3, column=1, padx=4, pady=3, sticky="ew")

		card_ubi.columnconfigure(1, weight=1)

		# 2. Card Datos del Bien Sobrante
		card_bien = ttk.LabelFrame(f_top, text=" 📦 Especificaciones del Bien Sobrante ", style="Sobrante.TLabelframe", padding=10)
		card_bien.pack(side="left", fill="both", expand=True, padx=4)

		# Fila 0: Denominación (ancho completo)
		ttk.Label(card_bien, text="Denominación:").grid(row=0, column=0, padx=4, pady=2, sticky="w")
		ttk.Entry(card_bien, textvariable=self.den, font=("Segoe UI", 9, "bold")).grid(row=0, column=1, columnspan=5, padx=4, pady=2, sticky="ew")

		# Fila 1: Estado, Marca, Modelo
		ttk.Label(card_bien, text="Estado:").grid(row=1, column=0, padx=4, pady=2, sticky="w")
		cbx_estado = ttk.Combobox(card_bien, textvariable=self.estado, values=["BUENO", "REGULAR", "MALO", "CHATARRA"], width=12)
		cbx_estado.grid(row=1, column=1, padx=4, pady=2, sticky="ew")

		ttk.Label(card_bien, text="Marca:").grid(row=1, column=2, padx=(8, 4), pady=2, sticky="w")
		ttk.Entry(card_bien, textvariable=self.marca, width=14).grid(row=1, column=3, padx=4, pady=2, sticky="ew")

		ttk.Label(card_bien, text="Modelo:").grid(row=1, column=4, padx=(8, 4), pady=2, sticky="w")
		ttk.Entry(card_bien, textvariable=self.modelo, width=14).grid(row=1, column=5, padx=4, pady=2, sticky="ew")

		# Fila 2: Serie, Tipo, Color
		ttk.Label(card_bien, text="Serie:").grid(row=2, column=0, padx=4, pady=2, sticky="w")
		ttk.Entry(card_bien, textvariable=self.serie, width=12).grid(row=2, column=1, padx=4, pady=2, sticky="ew")

		ttk.Label(card_bien, text="Tipo:").grid(row=2, column=2, padx=(8, 4), pady=2, sticky="w")
		ttk.Entry(card_bien, textvariable=self.tip, width=14).grid(row=2, column=3, padx=4, pady=2, sticky="ew")

		ttk.Label(card_bien, text="Color:").grid(row=2, column=4, padx=(8, 4), pady=2, sticky="w")
		ttk.Entry(card_bien, textvariable=self.color, width=14).grid(row=2, column=5, padx=4, pady=2, sticky="ew")

		# Fila 3: Dimensión, Situación, Otros
		ttk.Label(card_bien, text="Dimensión:").grid(row=3, column=0, padx=4, pady=2, sticky="w")
		ttk.Entry(card_bien, textvariable=self.dim, width=12).grid(row=3, column=1, padx=4, pady=2, sticky="ew")

		ttk.Label(card_bien, text="Situación:").grid(row=3, column=2, padx=(8, 4), pady=2, sticky="w")
		ttk.Entry(card_bien, textvariable=self.sit, width=14).grid(row=3, column=3, padx=4, pady=2, sticky="ew")

		ttk.Label(card_bien, text="Otros:").grid(row=3, column=4, padx=(8, 4), pady=2, sticky="w")
		ttk.Entry(card_bien, textvariable=self.otr, width=14).grid(row=3, column=5, padx=4, pady=2, sticky="ew")

		# Fila 4: Observaciones y Nota
		ttk.Label(card_bien, text="Observación:").grid(row=4, column=0, padx=4, pady=2, sticky="w")
		ttk.Entry(card_bien, textvariable=self.obs).grid(row=4, column=1, columnspan=2, padx=4, pady=2, sticky="ew")

		ttk.Label(card_bien, text="Nota:").grid(row=4, column=3, padx=(8, 4), pady=2, sticky="w")
		self.txtNota = tk.Text(card_bien, height=2, width=16, font=("Segoe UI", 9), relief="solid", bd=1)
		self.txtNota.grid(row=4, column=4, columnspan=2, padx=4, pady=2, sticky="ew")

		card_bien.columnconfigure(1, weight=1)
		card_bien.columnconfigure(3, weight=1)
		card_bien.columnconfigure(5, weight=1)

		# 3. Card Acciones
		card_acc = ttk.LabelFrame(f_top, text=" ⚡ Acciones ", style="Sobrante.TLabelframe", padding=10)
		card_acc.pack(side="left", fill="y", padx=(8, 0))

		btnReg = ttk.Button(card_acc, text="➕ Registrar", command=self.registrar)
		btnReg.pack(fill="x", pady=2)

		btnMod = ttk.Button(card_acc, text="💾 Modificar", command=self.modificar)
		btnMod.pack(fill="x", pady=2)

		btnDel = ttk.Button(card_acc, text="🗑️ Eliminar", command=self.eliminar)
		btnDel.pack(fill="x", pady=2)

		btnImp = ttk.Button(card_acc, text="🖨️ Imprimir", command=self.imprimir_etiqueta)
		btnImp.pack(fill="x", pady=2)

		btnLimpiar = ttk.Button(card_acc, text="🧹 Limpiar", command=self.limpiar)
		btnLimpiar.pack(fill="x", pady=2)

		# =========================================================================
		# PANEL INFERIOR: TREEVIEW Y TABLA
		# =========================================================================
		frame_tabla = ttk.LabelFrame(contenedor, text=" 📋 Lista de Bienes Sobrantes Registrados ", style="Sobrante.TLabelframe", padding=8)
		frame_tabla.pack(fill="both", expand=True)

		self.frame_tabla = frame_tabla

	def tree_view(self):
		cab = (1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18)
		self.tree = ttk.Treeview(self.frame_tabla, columns=cab, show="headings", style="Sobrante.Treeview")

		self.tree.heading(1,  text="#",             anchor="center")
		self.tree.heading(2,  text="Item",          anchor="center")
		self.tree.heading(3,  text="Acta",          anchor="center")
		self.tree.heading(4,  text="Local")
		self.tree.heading(5,  text="Área")
		self.tree.heading(6,  text="Oficina")
		self.tree.heading(7,  text="Denominación")
		self.tree.heading(8,  text="Estado",        anchor="center")
		self.tree.heading(9,  text="Marca")
		self.tree.heading(10, text="Modelo")
		self.tree.heading(11, text="Serie")
		self.tree.heading(12, text="Tipo")
		self.tree.heading(13, text="Color")
		self.tree.heading(14, text="Dimensión")
		self.tree.heading(15, text="Otros")
		self.tree.heading(16, text="Situación")
		self.tree.heading(17, text="Observaciones")
		self.tree.heading(18, text="Nota")

		self.tree.column(1,  width=40,  anchor="center", stretch=False)
		self.tree.column(2,  width=50,  anchor="center", stretch=False)
		self.tree.column(3,  width=55,  anchor="center", stretch=False)
		self.tree.column(4,  width=120, stretch=False)
		self.tree.column(5,  width=120, stretch=False)
		self.tree.column(6,  width=130, stretch=False)
		self.tree.column(7,  width=260, stretch=False)
		self.tree.column(8,  width=75,  anchor="center", stretch=False)
		self.tree.column(9,  width=95,  stretch=False)
		self.tree.column(10, width=95,  stretch=False)
		self.tree.column(11, width=95,  stretch=False)
		self.tree.column(12, width=90,  stretch=False)
		self.tree.column(13, width=90,  stretch=False)
		self.tree.column(14, width=90,  stretch=False)
		self.tree.column(15, width=90,  stretch=False)
		self.tree.column(16, width=90,  stretch=False)
		self.tree.column(17, width=120, stretch=False)
		self.tree.column(18, width=120, stretch=False)

		self.tree.tag_configure("odd",  background="#ffffff")
		self.tree.tag_configure("even", background="#f8fafc")

		scrollbarV = ttk.Scrollbar(self.frame_tabla, orient=tk.VERTICAL,   command=self.tree.yview)
		scrollbarH = ttk.Scrollbar(self.frame_tabla, orient=tk.HORIZONTAL, command=self.tree.xview)
		self.tree.configure(yscroll=scrollbarV.set, xscroll=scrollbarH.set)

		self.tree.grid(column=0, row=0, sticky="nsew")
		scrollbarV.grid(column=1, row=0, sticky="ns")
		scrollbarH.grid(column=0, row=1, sticky="ew")

		self.frame_tabla.rowconfigure(0, weight=1)
		self.frame_tabla.columnconfigure(0, weight=1)

		self.tree.bind("<Double-Button-1>", self.mostrar_datos)

		# =========================================================================
		# FOOTER BAR: CONTADOR Y TIPS
		# =========================================================================
		frame_footer = tk.Frame(self.frame_tabla.master, bg="#f8fafc")
		frame_footer.pack(fill="x", pady=(8, 0))

		frame_chip = tk.Frame(frame_footer, bg="#eff6ff", bd=1, relief="solid")
		frame_chip.pack(side="left")
		self.lbl_total = tk.Label(
			frame_chip,
			text="📦  0 bienes sobrantes",
			bg="#eff6ff",
			fg="#1d4ed8",
			font=("Segoe UI", 9, "bold"),
			padx=10,
			pady=4
		)
		self.lbl_total.pack()

		btnVerTodos = ttk.Button(frame_footer, text="🔄 Ver Todos", command=self.mostrar_todos)
		btnVerTodos.pack(side="left", padx=10)

		lbl_tip = tk.Label(
			frame_footer,
			text="💡 Doble clic en una fila para cargar datos en el formulario",
			bg="#f8fafc",
			fg="#64748b",
			font=("Segoe UI", 8, "italic")
		)
		lbl_tip.pack(side="left", padx=4)

	# -------------------------------------------------------------------------
	# LÓGICA DE DATOS
	# -------------------------------------------------------------------------
	def buscar(self):
		acta_val = self.acta.get().strip()
		if acta_val == "":
			valores = mostrar_sobrantes(1, 2)
		else:
			valores = mostrar_sobrantes(acta_val, 1)
			try:
				r = mostrar_d_personal(acta_val)
				if r and len(r) > 0 and len(r[0]) > 3:
					self.local.set(r[0][1] or "")
					self.area.set(r[0][2] or "")
					self.oficina.set(r[0][3] or "")
			except Exception:
				pass

		try:
			for item in self.tree.get_children():
				self.tree.delete(item)
			for cell, lista in enumerate(valores or [], 1):
				b = list(lista)
				b.insert(0, str(cell))
				tag = "odd" if cell % 2 == 1 else "even"
				self.tree.insert("", tk.END, values=b, tags=(tag,))
			n = len(valores or [])
			self.lbl_total.config(text=f"📦  {n} {'sobrante' if n == 1 else 'bienes sobrantes'}")
		except Exception as e:
			mb.showerror(title="Error", message=f"Ocurrió un error al buscar:\n{e}", parent=self)
			self.focus_set()

	def mostrar_todos(self):
		try:
			valores = mostrar_sobrantes(1, 2)
			for item in self.tree.get_children():
				self.tree.delete(item)
			for cell, lista in enumerate(valores or [], 1):
				b = list(lista)
				b.insert(0, str(cell))
				tag = "odd" if cell % 2 == 1 else "even"
				self.tree.insert("", tk.END, values=b, tags=(tag,))
			n = len(valores or [])
			self.lbl_total.config(text=f"📦  {n} {'sobrante' if n == 1 else 'bienes sobrantes'}")
		except Exception as e:
			print(f"Error en mostrar_todos: {e}")

	def mostrar(self):
		acta_val = self.acta.get().strip()
		if acta_val:
			self.buscar()
		else:
			self.mostrar_todos()

	def registrar(self, *args):
		aa = str(self.acta.get()).strip()
		bb = str(self.local.get()).strip()
		cc = str(self.area.get()).strip()
		dd = str(self.oficina.get()).strip()
		ee = str(self.den.get()).strip()
		ff = str(self.estado.get()).strip()
		gg = str(self.dim.get()).strip()
		hh = str(self.marca.get()).strip()
		ii = str(self.modelo.get()).strip()
		jj = str(self.serie.get()).strip()
		kk = str(self.color.get()).strip()
		ll = str(self.obs.get()).strip()
		mm = str(self.tip.get()).strip()
		nn = str(self.otr.get()).strip()
		oo = str(self.sit.get()).strip()
		pp = self.txtNota.get("1.0", "end-1c").strip()

		if not aa:
			mb.showwarning(title="Atención", message="Ingrese el número de Ficha / Acta.", parent=self)
			self.focus_set()
			return

		if not ee:
			mb.showwarning(title="Atención", message="Ingrese la denominación del bien sobrante.", parent=self)
			self.focus_set()
			return

		try:
			registrar_sobrantes(aa, bb, cc, dd, ee, ff, gg, hh, ii, jj, kk, ll, mm, nn, oo, pp)
			self.mostrar()
			self.limpiar()
			mb.showinfo(title="Acontar S.A.C.", message="Bien sobrante registrado con éxito.", parent=self)
			self.focus_set()
		except Exception as e:
			mb.showerror(title="Error al registrar", message=f"No se pudo registrar el bien sobrante:\n{e}", parent=self)
			self.focus_set()

	def modificar(self):
		curItem = self.tree.focus()
		if not curItem:
			mb.showwarning(title="Atención", message="Seleccione un registro de la tabla para modificar.", parent=self)
			self.focus_set()
			return

		vals = self.tree.item(curItem).get("values", [])
		if not vals or len(vals) < 2:
			return

		vnb = vals[1]  # item id
		v1 = self.acta.get().strip()
		v2 = self.local.get().strip()
		v3 = self.area.get().strip()
		v4 = self.oficina.get().strip()
		v5 = self.den.get().strip()
		v6 = self.estado.get().strip()
		v7 = self.dim.get().strip()
		v8 = self.marca.get().strip()
		v9 = self.modelo.get().strip()
		v10 = self.serie.get().strip()
		v11 = self.color.get().strip()
		v12 = self.obs.get().strip()
		v13 = self.tip.get().strip()
		v14 = self.otr.get().strip()
		v15 = self.sit.get().strip()
		v16 = self.txtNota.get("1.0", "end-1c").strip()

		data = [v1, v2, v3, v4, v5, v6, v7, v8, v9, v10, v11, v12, v13, v14, v15, v16]

		try:
			actualizar_sobrante(vnb, data)
			self.mostrar()
			mb.showinfo(title="Acontar S.A.C.", message="Registro actualizado correctamente.", parent=self)
			self.focus_set()
		except Exception as e:
			mb.showerror(title="Error al actualizar", message=f"Ocurrió un error:\n{e}", parent=self)
			self.focus_set()

	def eliminar(self, *args):
		curItem = self.tree.focus()
		if not curItem:
			mb.showwarning(title="Atención", message="Seleccione un bien de la tabla para eliminar.", parent=self)
			self.focus_set()
			return

		vals = self.tree.item(curItem).get("values", [])
		if not vals or len(vals) < 7:
			return

		item_id = vals[1]
		den_val = vals[6]

		confirm = mb.askyesno(
			title="Confirmar Eliminación",
			message=f"¿Está seguro de eliminar el bien sobrante Item [{item_id}]?\n\n{den_val}",
			parent=self
		)
		if not confirm:
			return

		try:
			delete_sobrante(item_id)
			self.mostrar()
			self.limpiar()
			mb.showinfo(title="Acontar S.A.C.", message="Registro eliminado exitosamente.", parent=self)
			self.focus_set()
		except Exception as e:
			mb.showerror(title="Error al eliminar", message=f"No se pudo eliminar el registro:\n{e}", parent=self)
			self.focus_set()

	def imprimir_etiqueta(self):
		"""Abre la ventana de impresión de etiquetas para sobrantes o genera la etiqueta directa."""
		curItem = self.tree.focus()
		if curItem:
			vals = self.tree.item(curItem).get("values", [])
			if vals and len(vals) > 6:
				item_id = vals[1]
				loc = vals[3] or self.local.get().strip()
				are = vals[4] or self.area.get().strip()
				ofi = vals[5] or self.oficina.get().strip()
				den = vals[6] or self.den.get().strip()
				try:
					build_label_sobrante(item_id, loc, are, ofi, den, 1)
					mb.showinfo(title="Impresión", message=f"Etiqueta enviada para el Item [{item_id}].", parent=self)
					return
				except Exception as e:
					print(f"Error generando etiqueta directa: {e}")

		# Si no hay selección o falla, abrir la ventana Window_print con valor=2
		Window_print(self, valor=2)

	def limpiar(self):
		self.item_actual = None
		self.den.set("")
		self.estado.set("BUENO")
		self.marca.set("S/M")
		self.modelo.set("S/M")
		self.serie.set("S/S")
		self.color.set("")
		self.dim.set("S/D")
		self.obs.set("N/A")
		self.tip.set("S/T")
		self.otr.set("")
		self.sit.set("")
		self.txtNota.delete("1.0", "end")

	def mostrar_datos(self, *args):
		curItem = self.tree.focus()
		if not curItem:
			return

		vnb = self.tree.item(curItem).get("values", [])
		if not vnb or len(vnb) < 17:
			return

		self.item_actual = vnb[1]
		self.acta.set(vnb[2] if vnb[2] is not None else "")
		self.local.set(vnb[3] if vnb[3] is not None else "")
		self.area.set(vnb[4] if vnb[4] is not None else "")
		self.oficina.set(vnb[5] if vnb[5] is not None else "")
		self.den.set(vnb[6] if vnb[6] is not None else "")
		self.estado.set(vnb[7] if vnb[7] is not None else "BUENO")
		self.marca.set(vnb[8] if vnb[8] is not None else "S/M")
		self.modelo.set(vnb[9] if vnb[9] is not None else "S/M")
		self.serie.set(vnb[10] if vnb[10] is not None else "S/S")
		self.tip.set(vnb[11] if vnb[11] is not None else "S/T")
		self.color.set(vnb[12] if vnb[12] is not None else "")
		self.dim.set(vnb[13] if vnb[13] is not None else "S/D")
		self.otr.set(vnb[14] if vnb[14] is not None else "")
		self.sit.set(vnb[15] if vnb[15] is not None else "")
		self.obs.set(vnb[16] if vnb[16] is not None else "N/A")
		self.txtNota.delete("1.0", "end")
		if len(vnb) > 17 and vnb[17]:
			self.txtNota.insert("1.0", str(vnb[17]))
