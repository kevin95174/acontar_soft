import tkinter as tk
from datetime import datetime
from tkinter import ttk
from tkinter import messagebox as mb
from db.query import (
	buscar_bien_d,
	actualizar_detalles,
	actualizar_registro,
	cambio_detalles,
	insertar_tabla2
)
from utils.helpers import resource_path


class Window_detalles(tk.Toplevel):
	"""Ventana emergente para consultar y editar las especificaciones técnicas de un bien."""

	def __init__(self, root=None, user=None, team=None, codigo=None):
		super().__init__(root)
		self.root = root
		self.user = user
		self.team = team
		self.codigo = codigo
		self.accion = None

		self.title("Ficha Detallada del Bien — AcontarSoft")
		self.geometry("860x560")
		self.resizable(False, False)
		self.configure(bg="#f8fafc")
		if root:
			self.transient(root)

		self.protocol("WM_DELETE_WINDOW", self.on_closing)

		self._cargar_icono()
		self._centrar_ventana(860, 560)
		self._configurar_estilos()

		self.variables()
		self.widgets()
		self.buscar_cod()
		self.focus_set()

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
		style.configure("Detalles.TLabelframe",
			background="#ffffff",
			relief="solid",
			borderwidth=1,
			bordercolor="#e2e8f0"
		)
		style.configure("Detalles.TLabelframe.Label",
			background="#ffffff",
			foreground="#334155",
			font=("Segoe UI", 9, "bold")
		)

	def on_closing(self):
		self.cancelar_codigo()

	def variables(self):
		self.codi = tk.StringVar()
		self.deno = tk.StringVar()
		self.inve = tk.StringVar()
		self.codp = tk.StringVar()
		self.acta = tk.StringVar()
		self.marc = tk.StringVar()
		self.seri = tk.StringVar()
		self.fech = tk.StringVar()
		self.dadq = tk.StringVar()
		self.mode = tk.StringVar()
		self.colo = tk.StringVar()
		self.aact = tk.StringVar()
		self.esta = tk.StringVar()
		self.dime = tk.StringVar()
		self.obse = tk.StringVar()

		self.otro = tk.StringVar()
		self.situ = tk.StringVar()
		self.tipo = tk.StringVar()
		self.valo = tk.StringVar()
		self.ctac = tk.StringVar()
		self.cint = tk.StringVar()

	# -------------------------------------------------------------------------
	# CONSTRUCCIÓN DE INTERFAZ
	# -------------------------------------------------------------------------
	def widgets(self):
		self.frameU = tk.Frame(self, bg="#f8fafc")
		self.frameU.pack(fill="both", expand=True, padx=14, pady=12)

		# 1. Cabecera: Identificación principal del Bien
		card_header = tk.Frame(self.frameU, bg="#ffffff", bd=1, relief="solid", padx=12, pady=10)
		card_header.pack(fill="x", pady=(0, 10))

		tk.Label(
			card_header,
			text="📦  Código:",
			bg="#ffffff",
			fg="#475569",
			font=("Segoe UI", 9, "bold")
		).pack(side="left", padx=(0, 6))

		etrCod = ttk.Entry(
			card_header,
			textvariable=self.codi,
			state="readonly",
			width=16,
			font=("Segoe UI", 9, "bold"),
			justify="center"
		)
		etrCod.pack(side="left", padx=(0, 12))

		tk.Label(
			card_header,
			text="Denominación:",
			bg="#ffffff",
			fg="#475569",
			font=("Segoe UI", 9, "bold")
		).pack(side="left", padx=(0, 6))

		etrDen = ttk.Entry(
			card_header,
			textvariable=self.deno,
			font=("Segoe UI", 9, "bold")
		)
		etrDen.pack(side="left", fill="x", expand=True)

		# 2. Panel Central en 2 Columnas (Izquierda: Datos Patrimoniales y Complementarios | Derecha: Especificaciones Técnicas Obligatorias)
		f_body = tk.Frame(self.frameU, bg="#f8fafc")
		f_body.pack(fill="both", expand=True, pady=(0, 10))

		# --- Columna Izquierda: Datos Patrimoniales y Contables ---
		f_left = tk.Frame(f_body, bg="#f8fafc")
		f_left.pack(side="left", fill="both", expand=True, padx=(0, 6))

		card_pat = ttk.LabelFrame(
			f_left,
			text=" 🏛️ Información Patrimonial y Contable ",
			style="Detalles.TLabelframe",
			padding=10
		)
		card_pat.pack(fill="x", pady=(0, 8))

		ttk.Label(card_pat, text="Ubicación Actual:").grid(row=0, column=0, padx=4, pady=3, sticky="w")
		ttk.Entry(card_pat, textvariable=self.inve, state="readonly").grid(row=0, column=1, columnspan=3, padx=4, pady=3, sticky="ew")

		ttk.Label(card_pat, text="Ubicación Ant.:").grid(row=1, column=0, padx=4, pady=3, sticky="w")
		ttk.Entry(card_pat, textvariable=self.acta, state="readonly").grid(row=1, column=1, columnspan=3, padx=4, pady=3, sticky="ew")

		ttk.Label(card_pat, text="Cuenta Contable:").grid(row=2, column=0, padx=4, pady=3, sticky="w")
		ttk.Entry(card_pat, textvariable=self.ctac, state="readonly").grid(row=2, column=1, columnspan=3, padx=4, pady=3, sticky="ew")

		ttk.Label(card_pat, text="Cód. Patrimonial:").grid(row=3, column=0, padx=4, pady=3, sticky="w")
		ttk.Entry(card_pat, textvariable=self.codp, state="readonly", width=16).grid(row=3, column=1, padx=4, pady=3, sticky="ew")

		ttk.Label(card_pat, text="Cód. Interno:").grid(row=3, column=2, padx=(8, 4), pady=3, sticky="w")
		ttk.Entry(card_pat, textvariable=self.cint, state="readonly", width=14).grid(row=3, column=3, padx=4, pady=3, sticky="ew")

		ttk.Label(card_pat, text="Fecha Adquisición:").grid(row=4, column=0, padx=4, pady=3, sticky="w")
		ttk.Entry(card_pat, textvariable=self.fech, state="readonly", width=16).grid(row=4, column=1, padx=4, pady=3, sticky="ew")

		ttk.Label(card_pat, text="Valor Adqui. (S/):").grid(row=4, column=2, padx=(8, 4), pady=3, sticky="w")
		ttk.Entry(card_pat, textvariable=self.valo, state="readonly", justify="right", width=14).grid(row=4, column=3, padx=4, pady=3, sticky="ew")

		ttk.Label(card_pat, text="Doc. Adquisición:").grid(row=5, column=0, padx=4, pady=3, sticky="w")
		ttk.Entry(card_pat, textvariable=self.dadq, state="readonly").grid(row=5, column=1, columnspan=3, padx=4, pady=3, sticky="ew")

		card_pat.columnconfigure(1, weight=1)
		card_pat.columnconfigure(3, weight=1)

		# --- Sub-card Izquierda Inferior: Datos Complementarios y Nota ---
		card_comp = ttk.LabelFrame(
			f_left,
			text=" 📝 Datos Complementarios y Notas ",
			style="Detalles.TLabelframe",
			padding=10
		)
		card_comp.pack(fill="both", expand=True)

		ttk.Label(card_comp, text="Situación:").grid(row=0, column=0, padx=4, pady=3, sticky="w")
		ttk.Entry(card_comp, textvariable=self.situ, width=16).grid(row=0, column=1, padx=4, pady=3, sticky="ew")

		ttk.Label(card_comp, text="Otros:").grid(row=0, column=2, padx=(8, 4), pady=3, sticky="w")
		ttk.Entry(card_comp, textvariable=self.otro, width=16).grid(row=0, column=3, padx=4, pady=3, sticky="ew")

		ttk.Label(card_comp, text="Observaciones:").grid(row=1, column=0, padx=4, pady=3, sticky="w")
		ttk.Entry(card_comp, textvariable=self.obse).grid(row=1, column=1, columnspan=3, padx=4, pady=3, sticky="ew")

		ttk.Label(card_comp, text="Nota:").grid(row=2, column=0, padx=4, pady=3, sticky="nw")
		self.txtNota = tk.Text(
			card_comp,
			height=3,
			font=("Segoe UI", 9),
			bg="#ffffff",
			fg="#0f172a",
			relief="solid",
			bd=1
		)
		self.txtNota.grid(row=2, column=1, columnspan=3, padx=4, pady=3, sticky="nsew")

		card_comp.columnconfigure(1, weight=1)
		card_comp.columnconfigure(3, weight=1)
		card_comp.rowconfigure(2, weight=1)

		# --- Columna Derecha: Especificaciones Físicas Obligatorias ---
		card_fis = ttk.LabelFrame(
			f_body,
			text=" 🔧 Especificaciones Físicas (* Obligatorios) ",
			style="Detalles.TLabelframe",
			padding=12
		)
		card_fis.pack(side="right", fill="both", padx=(6, 0))

		campos_obligatorios = [
			("Estado *",    self.esta),
			("Marca *",     self.marc),
			("Modelo *",    self.mode),
			("Serie *",     self.seri),
			("Tipo *",      self.tipo),
			("Color *",     self.colo),
			("Dimensión *", self.dime),
		]

		self._entries_obligatorios = []
		for idx, (lbl_txt, var) in enumerate(campos_obligatorios):
			tk.Label(
				card_fis,
				text=lbl_txt,
				bg="#ffffff",
				fg="#1e293b",
				font=("Segoe UI", 9, "bold")
			).grid(row=idx, column=0, padx=(2, 10), pady=6, sticky="w")

			etr = tk.Entry(
				card_fis,
				textvariable=var,
				width=24,
				font=("Segoe UI", 9),
				bg="#f8fafc",
				fg="#0f172a",
				relief="solid",
				bd=1,
				highlightbackground="#93c5fd",
				highlightcolor="#2563eb",
				highlightthickness=1
			)
			etr.grid(row=idx, column=1, padx=2, pady=6, sticky="ew")
			etr.bind("<Return>", lambda _e: self.actualizar_det())
			self._entries_obligatorios.append(etr)

		tk.Label(
			card_fis,
			text="* Todos estos campos son requeridos\npara validar el registro del bien.",
			bg="#ffffff",
			fg="#64748b",
			font=("Segoe UI", 8, "italic"),
			justify="left"
		).grid(row=len(campos_obligatorios), column=0, columnspan=2, sticky="w", padx=2, pady=(10, 0))

		card_fis.columnconfigure(1, weight=1)

		# 3. Barra de Acciones Inferior
		frame_actions = tk.Frame(self.frameU, bg="#f8fafc")
		frame_actions.pack(fill="x")

		tk.Label(
			frame_actions,
			text="💡 Presione Enter para guardar o Esc para cancelar",
			bg="#f8fafc",
			fg="#64748b",
			font=("Segoe UI", 8, "italic")
		).pack(side="left")

		btnCanc = ttk.Button(frame_actions, text="✖ Cancelar", width=14, command=self.cancelar_codigo)
		btnCanc.pack(side="right", padx=(6, 0))

		btnDeta = ttk.Button(frame_actions, text="💾 Aceptar y Guardar", width=20, command=self.actualizar_det)
		btnDeta.pack(side="right")

		self.bind("<Escape>", lambda _e: self.cancelar_codigo())

	# -------------------------------------------------------------------------
	# LÓGICA DE DATOS Y ACTUALIZACIÓN
	# -------------------------------------------------------------------------
	def cancelar_codigo(self):
		self.accion = 1
		self.destroy()

	def buscar_cod(self, *args):
		r = buscar_bien_d(1, self.codigo)
		self.codi.set(self.codigo or "")
		try:
			datos = [
				'deno', 'inve', 'acta', 'marc', 'seri', 'mode', 'fech', 'dadq', 'colo', 'esta',
				'dime', 'obse', 'otro', 'situ', 'codp', 'txtNota', 'tipo', 'valo', 'ctac', 'cint'
			]
			for i, dato in enumerate(datos):
				valor_original = r[0][i]
				valor = str(valor_original) if valor_original is not None else ''
				if dato == 'valo':
					valor = '{:,.2f}'.format(float(valor_original or 0))
					getattr(self, dato).set(valor)
				elif dato == 'txtNota':
					self.txtNota.delete("1.0", "end")
					self.txtNota.insert("1.0", valor)
				else:
					getattr(self, dato).set(valor)
		except Exception as e:
			mb.showinfo(message=f"El código no existe. Detalle: {str(e)}", title="¡Atención!", parent=self)
			print(str(e))

	def actualizar_det(self):
		self.data = [
			self.marc.get().strip(), self.mode.get().strip(), self.colo.get().strip(), self.seri.get().strip(),
			self.esta.get().strip(), self.dime.get().strip(), self.obse.get().strip(), self.otro.get().strip(),
			self.situ.get().strip(), self.fech.get().strip(), self.dadq.get().strip(),
			self.txtNota.get("1.0", "end-1c").strip(), self.tipo.get().strip()
		]

		self.data_c = [
			self.marc.get().strip(), self.mode.get().strip(), self.colo.get().strip(), self.seri.get().strip(),
			self.esta.get().strip(), self.dime.get().strip(), self.tipo.get().strip()
		]

		if any(val == "" for val in self.data_c):
			mb.showwarning(
				message="Los campos Marca, Modelo, Color, Tipo, Serie, Estado y Dimensión son obligatorios.",
				title="¡Atención!",
				parent=self
			)
			return

		try:
			self.validar_datos()
			actualizar_detalles(self.codi.get(), self.data)
			self.buscar_cod()
			mb.showinfo(message="Se actualizó correctamente.", title="Acontar S.A.C.", parent=self)
			self.destroy()
		except Exception as e:
			mb.showerror(message=f"Error al actualizar: {str(e)}", title="Error", parent=self)

	def actualizar_cod(self):
		j = self.codi.get().strip()
		if j == "":
			mb.showinfo(message="Ingrese un número de acta.", title="¡Atención!", parent=self)
		else:
			try:
				Acta = self.aact.get()
				now = datetime.now()
				F_inv = now.strftime("%d/%m/%Y %H:%M:%S")
				data = [Acta, F_inv, self.user, self.team]

				actualizar_registro(self.codi.get(), data)
				self.buscar()
				self.buscar_cod()
				mb.showinfo(message="Se actualizó correctamente.", title="Actualización", parent=self)
			except Exception:
				mb.showerror(message="Ocurrió un error al actualizar el registro.", title="Error", parent=self)

	def validar_datos(self):
		r = buscar_bien_d(2, self.codigo)
		r_lista = list(r[0])
		if self.data_c == r_lista:
			print("Si coinciden")
		else:
			insertar = cambio_detalles(self.codigo)
			try:
				insertar_tabla2(insertar)
			except Exception as e:
				print(f"Este es el error se duplican {str(e)}")
			print("No coinciden")
