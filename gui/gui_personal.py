import tkinter as tk
from tkinter import ttk
from tkinter import messagebox as mb
from utils.order_utils import sort_by
from utils.helpers import resource_path
from db.query import mostrar_personal, actualizar_personal, registrar_personal, delete_personal

class Window_personal(tk.Toplevel):
	def __init__(self, root=None):
		super().__init__(root)
		self.title("Gestión de Personal y Ubicaciones")
		self.geometry("1180x720")
		self.minsize(1000, 600)
		self.configure(bg="#f8fafc")
		self.transient(root)

		self._cargar_icono()
		self._centrar_ventana(1180, 720)
		self._configurar_estilos()

		self.variables()
		self.widgets()
		self.mostrar()

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

		# LabelFrame Cards
		style.configure("Personal.TLabelframe",
			background="#ffffff",
			relief="solid",
			borderwidth=1,
			bordercolor="#e2e8f0"
		)
		style.configure("Personal.TLabelframe.Label",
			background="#ffffff",
			foreground="#334155",
			font=("Segoe UI", 9, "bold")
		)

		# Treeview
		style.configure("Personal.Treeview",
			background="#ffffff",
			fieldbackground="#ffffff",
			foreground="#0f172a",
			font=("Segoe UI", 9),
			rowheight=24
		)
		style.configure("Personal.Treeview.Heading",
			background="#f1f5f9",
			foreground="#475569",
			font=("Segoe UI", 8, "bold"),
			relief="flat",
			padding=(6, 6)
		)
		style.map("Personal.Treeview",
			background=[("selected", "#2563eb")],
			foreground=[("selected", "#ffffff")]
		)

	def variables(self):
		self.nomb = tk.StringVar()
		self.aPat = tk.StringVar()
		self.aMat = tk.StringVar()
		self.dni = tk.StringVar()

		self.acta = tk.StringVar()
		self.dep = tk.StringVar()
		self.prov = tk.StringVar()
		self.dist = tk.StringVar()
		self.local = tk.StringVar()
		self.area = tk.StringVar()
		self.oficina = tk.StringVar()
		self.equipo = tk.StringVar()

	def widgets(self):
		# Contenedor principal
		contenedor = tk.Frame(self, bg="#f8fafc")
		contenedor.pack(fill="both", expand=True, padx=14, pady=12)

		# =========================================================================
		# 1. TARJETAS DEL FORMULARIO SUPERIOR
		# =========================================================================
		f_cards = tk.Frame(contenedor, bg="#f8fafc")
		f_cards.pack(fill="x", pady=(0, 10))

		# Card 1: Datos Personales
		card_personal = ttk.LabelFrame(f_cards, text=" 👤 Datos del Responsable ", style="Personal.TLabelframe", padding=10)
		card_personal.pack(side="left", fill="both", expand=True, padx=(0, 8))

		ttk.Label(card_personal, text="Nombres:").grid(column=0, row=0, padx=6, pady=4, sticky="w")
		ttk.Entry(card_personal, textvariable=self.nomb).grid(column=1, row=0, padx=6, pady=4, sticky="ew")

		ttk.Label(card_personal, text="Ape. Paterno:").grid(column=0, row=1, padx=6, pady=4, sticky="w")
		ttk.Entry(card_personal, textvariable=self.aPat).grid(column=1, row=1, padx=6, pady=4, sticky="ew")

		ttk.Label(card_personal, text="Ape. Materno:").grid(column=0, row=2, padx=6, pady=4, sticky="w")
		ttk.Entry(card_personal, textvariable=self.aMat).grid(column=1, row=2, padx=6, pady=4, sticky="ew")

		ttk.Label(card_personal, text="DNI:").grid(column=0, row=3, padx=6, pady=4, sticky="w")
		ttk.Entry(card_personal, textvariable=self.dni).grid(column=1, row=3, padx=6, pady=4, sticky="ew")

		card_personal.columnconfigure(1, weight=1)

		# Card 2: Ubicación y Ficha
		card_ubic = ttk.LabelFrame(f_cards, text=" 📍 Ubicación y Asignación de Ficha ", style="Personal.TLabelframe", padding=10)
		card_ubic.pack(side="left", fill="both", expand=True, padx=4)

		ttk.Label(card_ubic, text="Ficha / Acta:").grid(column=0, row=0, padx=6, pady=4, sticky="w")
		ttk.Entry(card_ubic, textvariable=self.acta).grid(column=1, row=0, padx=6, pady=4, sticky="ew")

		ttk.Label(card_ubic, text="Departamento:").grid(column=0, row=1, padx=6, pady=4, sticky="w")
		ttk.Entry(card_ubic, textvariable=self.dep).grid(column=1, row=1, padx=6, pady=4, sticky="ew")

		ttk.Label(card_ubic, text="Provincia:").grid(column=0, row=2, padx=6, pady=4, sticky="w")
		ttk.Entry(card_ubic, textvariable=self.prov).grid(column=1, row=2, padx=6, pady=4, sticky="ew")

		ttk.Label(card_ubic, text="Distrito:").grid(column=0, row=3, padx=6, pady=4, sticky="w")
		ttk.Entry(card_ubic, textvariable=self.dist).grid(column=1, row=3, padx=6, pady=4, sticky="ew")

		ttk.Label(card_ubic, text="Local:").grid(column=2, row=0, padx=(12, 6), pady=4, sticky="w")
		ttk.Entry(card_ubic, textvariable=self.local).grid(column=3, row=0, padx=6, pady=4, sticky="ew")

		ttk.Label(card_ubic, text="Área:").grid(column=2, row=1, padx=(12, 6), pady=4, sticky="w")
		ttk.Entry(card_ubic, textvariable=self.area).grid(column=3, row=1, padx=6, pady=4, sticky="ew")

		ttk.Label(card_ubic, text="Oficina:").grid(column=2, row=2, padx=(12, 6), pady=4, sticky="w")
		ttk.Entry(card_ubic, textvariable=self.oficina).grid(column=3, row=2, padx=6, pady=4, sticky="ew")

		ttk.Label(card_ubic, text="Equipo Inv.:").grid(column=2, row=3, padx=(12, 6), pady=4, sticky="w")
		ttk.Entry(card_ubic, textvariable=self.equipo).grid(column=3, row=3, padx=6, pady=4, sticky="ew")

		card_ubic.columnconfigure(1, weight=1)
		card_ubic.columnconfigure(3, weight=1)

		# Card 3: Acciones
		card_acciones = ttk.LabelFrame(f_cards, text=" ⚡ Acciones ", style="Personal.TLabelframe", padding=10)
		card_acciones.pack(side="left", fill="y", padx=(8, 0))

		btnRegN = ttk.Button(card_acciones, text="➕ Registrar", command=self.registrar_nuevo)
		btnRegN.pack(fill="x", pady=3)

		btnReg = ttk.Button(card_acciones, text="💾 Modificar", command=self.modificar)
		btnReg.pack(fill="x", pady=3)

		btnDel = ttk.Button(card_acciones, text="🗑️ Eliminar", command=self.eliminar_personal)
		btnDel.pack(fill="x", pady=3)

		btnLimpiar = ttk.Button(card_acciones, text="🧹 Limpiar", command=self.limpiar_campos)
		btnLimpiar.pack(fill="x", pady=3)

		# =========================================================================
		# 2. TABLA DE REGISTROS
		# =========================================================================
		frame_tabla = ttk.LabelFrame(contenedor, text=" 📋 Directorio de Personal y Ubicaciones ", style="Personal.TLabelframe", padding=8)
		frame_tabla.pack(fill="both", expand=True)

		cab = (1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12)
		self.tree = ttk.Treeview(frame_tabla, columns=cab, show="headings", style="Personal.Treeview")     

		self.tree.heading(1,  text="Acta",         command=lambda: sort_by(self.tree, 1,  False))
		self.tree.heading(2,  text="Departamento", command=lambda: sort_by(self.tree, 2,  False))
		self.tree.heading(3,  text="Provincia",    command=lambda: sort_by(self.tree, 3,  False))
		self.tree.heading(4,  text="Distrito",     command=lambda: sort_by(self.tree, 4,  False))
		self.tree.heading(5,  text="Local",        command=lambda: sort_by(self.tree, 5,  False))
		self.tree.heading(6,  text="Área",         command=lambda: sort_by(self.tree, 6,  False))
		self.tree.heading(7,  text="Oficina",      command=lambda: sort_by(self.tree, 7,  False))
		self.tree.heading(8,  text="DNI",          command=lambda: sort_by(self.tree, 8,  False))
		self.tree.heading(9,  text="Nombres",      command=lambda: sort_by(self.tree, 9,  False))
		self.tree.heading(10, text="Ape. Paterno", command=lambda: sort_by(self.tree, 10, False))
		self.tree.heading(11, text="Ape. Materno", command=lambda: sort_by(self.tree, 11, False))
		self.tree.heading(12, text="Equipo Inv.",  command=lambda: sort_by(self.tree, 12, False))

		self.tree.column(1,  width=55,  anchor="center", stretch=False)
		self.tree.column(2,  width=100, stretch=False)
		self.tree.column(3,  width=100, stretch=False)
		self.tree.column(4,  width=100, stretch=False)
		self.tree.column(5,  width=170, stretch=False)
		self.tree.column(6,  width=170, stretch=False)
		self.tree.column(7,  width=180, stretch=False)
		self.tree.column(8,  width=80,  anchor="center", stretch=False)
		self.tree.column(9,  width=130, stretch=False)
		self.tree.column(10, width=120, stretch=False)
		self.tree.column(11, width=120, stretch=False)
		self.tree.column(12, width=100, stretch=False)

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

		self.tree.bind("<Double-Button-1>", self.mostrar_datos)

		# =========================================================================
		# 3. BARRA INFERIOR / ESTADÍSTICAS
		# =========================================================================
		frame_footer = tk.Frame(contenedor, bg="#f8fafc")
		frame_footer.pack(fill="x", pady=(8, 0))

		frame_chip = tk.Frame(frame_footer, bg="#eff6ff", bd=1, relief="solid")
		frame_chip.pack(side="left")
		self.lbl_total = tk.Label(
			frame_chip,
			text="👥  0 registros",
			bg="#eff6ff",
			fg="#1d4ed8",
			font=("Segoe UI", 9, "bold"),
			padx=10,
			pady=4
		)
		self.lbl_total.pack()

		lbl_tip = tk.Label(
			frame_footer,
			text="💡 Doble clic en cualquier fila para cargar los datos en el formulario",
			bg="#f8fafc",
			fg="#64748b",
			font=("Segoe UI", 8, "italic")
		)
		lbl_tip.pack(side="left", padx=12)

	def limpiar_campos(self):
		self.nomb.set("")
		self.aPat.set("")
		self.aMat.set("")
		self.dni.set("")
		self.acta.set("")
		self.dep.set("")
		self.prov.set("")
		self.dist.set("")
		self.local.set("")
		self.area.set("")
		self.oficina.set("")
		self.equipo.set("")

	def mostrar(self):
		for item in self.tree.get_children():
			self.tree.delete(item)     
		r = mostrar_personal()
		for i, b in enumerate(r, 1):
			tag = "odd" if i % 2 == 1 else "even"
			self.tree.insert("", tk.END, values=b, tags=(tag,))
		n = len(r)
		self.lbl_total.config(text=f"👥  {n} {'registro' if n == 1 else 'registros'}")

	def modificar(self):
		if not self.acta.get().strip():
			mb.showwarning(title="Atención", message="Seleccione un registro o ingrese el número de Ficha/Acta.", parent=self)
			self.focus_set()
			return

		vnomb = self.nomb.get()
		vaPat = self.aPat.get()
		vaMat = self.aMat.get()
		vndni = self.dni.get()

		departamento = self.dep.get()
		provincia = self.prov.get()
		distrito = self.dist.get()
		vlocal = self.local.get()
		varea = self.area.get()
		voficina = self.oficina.get()
		vequipo = self.equipo.get()

		data = [vnomb, vaPat, vaMat, vndni, departamento, provincia, distrito, vlocal, varea, voficina, vequipo]
		try:
			actualizar_personal(self.acta.get(), data)
			self.mostrar()
			mb.showinfo(title="Acontar S.A.C.", message="¡Actualizado correctamente!", parent=self)
			self.focus_set()
		except Exception as e:
			print(e)
			mb.showerror(title="Error", message=f"Ocurrió un error al actualizar:\n{e}", parent=self)
			self.focus_set()

	def registrar_nuevo(self):
		if not self.acta.get().strip():
			mb.showwarning(title="Atención", message="Ingrese un número de Ficha / Acta para registrar.", parent=self)
			self.focus_set()
			return

		try:
			registrar_personal(
				self.acta.get(), self.dep.get(), self.prov.get(), self.dist.get(),
				self.local.get(), self.area.get(), self.oficina.get(), self.dni.get(),
				self.nomb.get(), self.aPat.get(), self.aMat.get()
			)
			self.mostrar()
			mb.showinfo(title="Acontar S.A.C.", message="¡Registrado correctamente!", parent=self)
			self.focus_set()
		except Exception as e:
			print(e)
			mb.showerror(title="Error", message=f"Ocurrió un error al registrar:\n{e}", parent=self)
			self.focus_set()

	def eliminar_personal(self):
		curItem = self.tree.focus()
		if not curItem:
			mb.showwarning(title="Atención", message="Seleccione un registro de la tabla para eliminar.", parent=self)
			self.focus_set()
			return

		vals = self.tree.item(curItem).get("values", [])
		if not vals:
			return

		acta_val = vals[0]
		nomb_val = f"{vals[8]} {vals[9]}" if len(vals) > 9 else str(acta_val)

		confirm = mb.askyesno(
			title="Confirmar Eliminación",
			message=f"¿Está seguro de eliminar el registro de la Ficha [{acta_val}] ({nomb_val})?",
			parent=self
		)
		if not confirm:
			return

		try:
			delete_personal(acta_val)
			self.mostrar()
			self.limpiar_campos()
			mb.showinfo(title="Acontar S.A.C.", message="Eliminado correctamente.", parent=self)
			self.focus_set()
		except Exception as e:
			print(e)
			mb.showerror(title="Error", message=f"Ocurrió un error al eliminar:\n{e}", parent=self)
			self.focus_set()

	def mostrar_datos(self, event=None):
		curActa = self.tree.focus()
		if not curActa:
			return

		vals = self.tree.item(curActa).get("values", [])
		if not vals or len(vals) < 12:
			return

		self.acta.set(vals[0] if vals[0] is not None else "")
		self.dep.set(vals[1] if vals[1] is not None else "")
		self.prov.set(vals[2] if vals[2] is not None else "")
		self.dist.set(vals[3] if vals[3] is not None else "")
		self.local.set(vals[4] if vals[4] is not None else "")
		self.area.set(vals[5] if vals[5] is not None else "")
		self.oficina.set(vals[6] if vals[6] is not None else "")
		self.dni.set(vals[7] if vals[7] is not None else "")
		self.nomb.set(vals[8] if vals[8] is not None else "")
		self.aPat.set(vals[9] if vals[9] is not None else "")
		self.aMat.set(vals[10] if vals[10] is not None else "")
		self.equipo.set(vals[11] if vals[11] is not None else "")
