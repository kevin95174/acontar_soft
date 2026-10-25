import os
import configparser
import tkinter as tk
import fitz
from tkinter import EW, ttk, filedialog
from tkinter import messagebox as mb
from PIL import Image, ImageTk
from db.query import (
	mostrar_datos_print, 
	data_label_ubi, 
	datos_iniciales, 
	actualizar_datos, 
	mostrar_datos_sobrante
)
from label.label_gen import build_label, build_label_batch
from label.label_sobrante import build_label_sobrante
from services.label_batch_service import (
	obtener_oficinas, 
	filtrar_bienes_oficina, 
	buscar_bien_por_codigo,
	filtrar_oficinas_predictivo,
	buscar_oficina_por_codigo
)

class Window_print(tk.Toplevel):
	"""Ventana principal de impresión de etiquetas en lote y por oficina."""
	def __init__(self, root=None, valor=1):
		super().__init__(root)
		self.root = root
		self.valor = valor or 1
		self.title("Impresión de Etiquetas - Gestión en Lote y por Oficina")
		self.iconbitmap('./img/favicon.ico')
		self.geometry("1060x720")
		self.minsize(980, 640)
		self.config_path = 'config.ini'
		self.config = configparser.ConfigParser()
		self.img_label_path = None
		self.grab_set()
		self.focus_set()

		self.nbk = ttk.Notebook(self)
		self.tab_lote = ttk.Frame(self.nbk)
		self.tab_ajustes = tk.Frame(self.nbk)

		self.nbk.add(self.tab_lote, text="Impresión en Lote / Por Oficina")
		self.nbk.add(self.tab_ajustes, text="Ajustes")
		self.nbk.pack(fill="both", expand=True)

		self.tab_lote_init()
		self.tab_ajustes_init()
		self.load_config()
		self.cargar_imagen_guardada()

		# Si se abrió explícitamente para sobrantes (valor == 2), abrir popup de sobrante
		if self.valor == 2:
			self.after(150, lambda: self.abrir_popup_individual(valor=2))

	# -------------------------------------------------------------------------
	# PESTAÑA PRINCIPAL: IMPRESIÓN EN LOTE / POR OFICINA
	# -------------------------------------------------------------------------
	def tab_lote_init(self):
		self.lote_oficinas_data = []
		self.lote_cod_oficina = tk.StringVar()
		self.lote_oficina_sel = tk.StringVar()
		self.lote_filtro_sel = tk.StringVar(value="Ubicados (Inventariados en esta oficina)")
		self.lote_ofic_personalizada = tk.StringVar()
		self.lote_codigo_agregar = tk.StringVar()
		self.imprimir_al_agregar = tk.BooleanVar(value=False)
		self.lote_items = []
		self.lote_photo = None

		# Variables para los campos de detalle del bien seleccionado
		self.prev_codpat = tk.StringVar()
		self.prev_codint = tk.StringVar()
		self.prev_deno = tk.StringVar()
		self.prev_actaant = tk.StringVar()
		self.prev_ubic = tk.StringVar()
		self.prev_ofic_etiqueta = tk.StringVar()
		self.prev_estado = tk.StringVar()
		self._bien_pendiente_agregar = None
		self._codigo_previsualizado = None

		container = ttk.Frame(self.tab_lote, padding=8)
		container.pack(fill="both", expand=True)

		# 1. Panel Superior: Filtros, Selección y Acciones de Entrada
		frame_filtros = ttk.LabelFrame(container, text=" Selección de Oficina, Filtros y Entrada de Bienes ", padding=8)
		frame_filtros.pack(fill="x", padx=4, pady=(0, 6))

		# Fila 0: Búsqueda por Código, Combobox Predictivo, Filtro de Estado y Botón Cargar
		lblCodOfi = ttk.Label(frame_filtros, text="Cód. Oficina:")
		lblCodOfi.grid(row=0, column=0, padx=4, pady=4, sticky="w")

		self.etr_cod_oficina = ttk.Entry(frame_filtros, textvariable=self.lote_cod_oficina, width=8)
		self.etr_cod_oficina.grid(row=0, column=1, padx=(0, 8), pady=4, sticky="w")
		self.etr_cod_oficina.bind("<KeyRelease>", self._on_cod_oficina_keyrelease)
		self.etr_cod_oficina.bind("<Return>", lambda _e: self.cargar_bienes_lote())

		lblOfi = ttk.Label(frame_filtros, text="Oficina:")
		lblOfi.grid(row=0, column=2, padx=4, pady=4, sticky="w")

		self.cbx_lote_oficinas = ttk.Combobox(frame_filtros, textvariable=self.lote_oficina_sel, state="normal", width=34)
		self.cbx_lote_oficinas.grid(row=0, column=3, padx=4, pady=4, sticky="ew")
		self.cbx_lote_oficinas.bind("<KeyRelease>", self._on_oficina_keyrelease)
		self.cbx_lote_oficinas.bind("<<ComboboxSelected>>", self._on_lote_oficina_select)
		self.cbx_lote_oficinas.bind("<Return>", self._on_oficina_return)

		lblFiltro = ttk.Label(frame_filtros, text="Estado:")
		lblFiltro.grid(row=0, column=4, padx=(8, 4), pady=4, sticky="w")

		self.cbx_lote_filtro = ttk.Combobox(
			frame_filtros, 
			textvariable=self.lote_filtro_sel, 
			state="readonly", 
			width=30,
			values=[
				"Ubicados (Inventariados en esta oficina)",
				"Faltantes (No inventariados de esta oficina)",
				"Primera Ubicación (Asignados originalmente)",
				"Todos (Ubicados + Asignados)"
			]
		)
		self.cbx_lote_filtro.grid(row=0, column=5, padx=4, pady=4, sticky="ew")

		btnCargar = ttk.Button(frame_filtros, text="🔍 Cargar Bienes", command=self.cargar_bienes_lote)
		btnCargar.grid(row=0, column=6, columnspan=2, padx=(6, 4), pady=4, sticky="ew")

		# Fila 1: Oficina directa editable (sin checkbox), Agregar por código, Check imprimir y Popup
		lblOfiLote = ttk.Label(frame_filtros, text="Oficina etiqueta:")
		lblOfiLote.grid(row=1, column=0, columnspan=2, padx=4, pady=4, sticky="w")

		self.etr_lote_ofic = ttk.Entry(frame_filtros, textvariable=self.lote_ofic_personalizada)
		self.etr_lote_ofic.grid(row=1, column=2, columnspan=2, padx=4, pady=4, sticky="ew")

		lblAdd = ttk.Label(frame_filtros, text="Cód. Bien:")
		lblAdd.grid(row=1, column=4, padx=(8, 4), pady=4, sticky="w")

		self.etr_lote_add = ttk.Entry(frame_filtros, textvariable=self.lote_codigo_agregar, width=15)
		self.etr_lote_add.grid(row=1, column=5, padx=4, pady=4, sticky="ew")
		self.etr_lote_add.bind("<Return>", self.on_enter_codigo_lote)
		self.etr_lote_add.bind("<KP_Enter>", self.on_enter_codigo_lote)

		self.btnAdd = ttk.Button(frame_filtros, text="➕ Agregar", command=self.agregar_codigo_lote, default="active")
		self.btnAdd.grid(row=1, column=6, padx=(4, 4), pady=4, sticky="ew")
		self.btnAdd.bind("<Return>", lambda _e: self.agregar_codigo_lote())
		self.btnAdd.bind("<KP_Enter>", lambda _e: self.agregar_codigo_lote())

		btnPopup = ttk.Button(frame_filtros, text="🔍 Búsqueda Detallada...", command=self.abrir_popup_individual)
		btnPopup.grid(row=1, column=7, padx=(4, 4), pady=4, sticky="ew")

		# Fila 2: Checkbox para imprimir automáticamente al agregar
		chkImpAlAgregar = ttk.Checkbutton(
			frame_filtros, 
			text="🖨️ Imprimir automáticamente al agregar a la lista", 
			variable=self.imprimir_al_agregar
		)
		chkImpAlAgregar.grid(row=2, column=2, columnspan=5, padx=4, pady=(2, 4), sticky="w")

		frame_filtros.columnconfigure(3, weight=2)
		frame_filtros.columnconfigure(5, weight=1)

		# 2. Panel de Previsualización y Detalle del Bien Seleccionado (ENCIMA DE LA LISTA)
		frame_preview_panel = ttk.LabelFrame(container, text=" Detalle y Vista Previa del Bien Seleccionado ", padding=6)
		frame_preview_panel.pack(fill="x", padx=4, pady=(0, 6))

		# Lado Izquierdo: Campos donde se previsualizan los datos del bien
		frame_datos_bien = ttk.Frame(frame_preview_panel)
		frame_datos_bien.pack(side="left", fill="both", expand=True, padx=(2, 8))

		# Fila 0: Denominación (ancho completo)
		ttk.Label(frame_datos_bien, text="Denominación:").grid(row=0, column=0, padx=4, pady=2, sticky="w")
		self.etr_prev_deno = ttk.Entry(frame_datos_bien, textvariable=self.prev_deno, state="readonly", font=("Segoe UI", 9, "bold"))
		self.etr_prev_deno.grid(row=0, column=1, columnspan=5, padx=4, pady=2, sticky="ew")

		# Fila 1: Códigos y Acta/Ficha
		ttk.Label(frame_datos_bien, text="Cód. Patrimonial:").grid(row=1, column=0, padx=4, pady=2, sticky="w")
		ttk.Entry(frame_datos_bien, textvariable=self.prev_codpat, state="readonly", width=16).grid(row=1, column=1, padx=4, pady=2, sticky="ew")

		ttk.Label(frame_datos_bien, text="Cód. Interno:").grid(row=1, column=2, padx=(8, 4), pady=2, sticky="w")
		ttk.Entry(frame_datos_bien, textvariable=self.prev_codint, state="readonly", width=14).grid(row=1, column=3, padx=4, pady=2, sticky="ew")

		ttk.Label(frame_datos_bien, text="Ficha / Acta:").grid(row=1, column=4, padx=(8, 4), pady=2, sticky="w")
		ttk.Entry(frame_datos_bien, textvariable=self.prev_actaant, state="readonly", width=14).grid(row=1, column=5, padx=4, pady=2, sticky="ew")

		# Fila 2: Ubicación/Inv, Estado y Oficina Etiqueta
		ttk.Label(frame_datos_bien, text="Ubicación / Inv.:").grid(row=2, column=0, padx=4, pady=2, sticky="w")
		ttk.Entry(frame_datos_bien, textvariable=self.prev_ubic, state="readonly", width=16).grid(row=2, column=1, padx=4, pady=2, sticky="ew")

		ttk.Label(frame_datos_bien, text="Estado Inv.:").grid(row=2, column=2, padx=(8, 4), pady=2, sticky="w")
		ttk.Entry(frame_datos_bien, textvariable=self.prev_estado, state="readonly", width=14).grid(row=2, column=3, padx=4, pady=2, sticky="ew")

		ttk.Label(frame_datos_bien, text="Oficina Etiqueta:").grid(row=2, column=4, padx=(8, 4), pady=2, sticky="w")
		self.etr_prev_ofic = ttk.Entry(frame_datos_bien, textvariable=self.prev_ofic_etiqueta, width=14)
		self.etr_prev_ofic.grid(row=2, column=5, padx=4, pady=2, sticky="ew")
		self.etr_prev_ofic.bind("<Return>", lambda _e: self._actualizar_oficina_bien_seleccionado())

		# Fila 3: Botones de Acción sobre el bien seleccionado
		f_sub_acciones = ttk.Frame(frame_datos_bien)
		f_sub_acciones.grid(row=3, column=0, columnspan=6, pady=(6, 2), sticky="ew")

		btnImpUno = ttk.Button(f_sub_acciones, text="🖨️ Imprimir Esta Etiqueta", command=self.imprimir_seleccionado_lote)
		btnImpUno.pack(side="left", padx=(0, 6))

		btnGuardarOfi = ttk.Button(f_sub_acciones, text="💾 Aplicar Oficina al Bien", command=self._actualizar_oficina_bien_seleccionado)
		btnGuardarOfi.pack(side="left", padx=4)

		self.lbl_prev_info = ttk.Label(
			f_sub_acciones, 
			text="Seleccione un bien de la lista para ver su información y etiqueta", 
			font=("Segoe UI", 8, "italic"), 
			foreground="#555555"
		)
		self.lbl_prev_info.pack(side="left", padx=8)

		frame_datos_bien.columnconfigure(1, weight=1)
		frame_datos_bien.columnconfigure(3, weight=1)
		frame_datos_bien.columnconfigure(5, weight=2)

		# Lado Derecho: Previsualización gráfica de la etiqueta (50mm x 25mm)
		frame_etiqueta_lateral = ttk.Frame(frame_preview_panel)
		frame_etiqueta_lateral.pack(side="right", fill="y", padx=(4, 2))

		frame_img_box = tk.Frame(frame_etiqueta_lateral, bg="#ffffff", bd=2, relief="groove", width=320, height=155)
		frame_img_box.pack_propagate(False)
		frame_img_box.pack(side="top", pady=2)

		self.lbl_lote_preview = tk.Label(
			frame_img_box, 
			text="Vista previa de la etiqueta\n\n(50mm x 25mm)", 
			bg="#ffffff", 
			fg="#777777",
			font=("Segoe UI", 9)
		)
		self.lbl_lote_preview.pack(fill="both", expand=True)

		# 3. Panel Inferior: Tabla de Etiquetas (Ocupa todo el ancho abajo)
		frame_tabla = ttk.LabelFrame(container, text=" Lista de Etiquetas a Generar ", padding=6)
		frame_tabla.pack(fill="both", expand=True, padx=4, pady=(0, 4))

		columnas = ("num", "codpat", "codint", "deno", "acta_ant", "estado", "oficina")
		self.tree_lote = ttk.Treeview(frame_tabla, columns=columnas, show="headings", selectmode="extended")
		self.tree_lote.heading("num", text="#")
		self.tree_lote.heading("codpat", text="Cód. Patrimonial")
		self.tree_lote.heading("codint", text="Cód. Interno")
		self.tree_lote.heading("deno", text="Denominación")
		self.tree_lote.heading("acta_ant", text="Ficha / Acta")
		self.tree_lote.heading("estado", text="Estado Inv.")
		self.tree_lote.heading("oficina", text="Oficina Etiqueta")

		self.tree_lote.column("num", width=35, anchor="center")
		self.tree_lote.column("codpat", width=120, anchor="w")
		self.tree_lote.column("codint", width=90, anchor="w")
		self.tree_lote.column("deno", width=270, anchor="w")
		self.tree_lote.column("acta_ant", width=85, anchor="center")
		self.tree_lote.column("estado", width=95, anchor="center")
		self.tree_lote.column("oficina", width=180, anchor="w")

		scroll_y = ttk.Scrollbar(frame_tabla, orient="vertical", command=self.tree_lote.yview)
		scroll_x = ttk.Scrollbar(frame_tabla, orient="horizontal", command=self.tree_lote.xview)
		self.tree_lote.configure(yscrollcommand=scroll_y.set, xscrollcommand=scroll_x.set)

		self.tree_lote.grid(row=0, column=0, sticky="nsew")
		scroll_y.grid(row=0, column=1, sticky="ns")
		scroll_x.grid(row=1, column=0, sticky="ew")
		frame_tabla.rowconfigure(0, weight=1)
		frame_tabla.columnconfigure(0, weight=1)

		self.tree_lote.bind("<<TreeviewSelect>>", self._on_tree_lote_select)
		self.tree_lote.bind("<Double-Button-1>", lambda _e: self.previsualizar_seleccionado_lote())

		# 3. Panel Inferior: Estadísticas y Botones de Acción
		frame_inferior = ttk.Frame(container, padding=4)
		frame_inferior.pack(fill="x", padx=4, pady=(6, 0))

		self.lbl_total_lote = ttk.Label(frame_inferior, text="Total en lista: 0 etiquetas", font=("Segoe UI", 10, "bold"))
		self.lbl_total_lote.pack(side="left", padx=5)

		btnQuitar = ttk.Button(frame_inferior, text="🗑️ Quitar Seleccionado(s)", command=self.quitar_seleccionados_lote)
		btnQuitar.pack(side="left", padx=8)

		btnNueva = ttk.Button(frame_inferior, text="✨ Limpiar / Nueva Lista", command=self.nueva_lista_lote)
		btnNueva.pack(side="left", padx=5)

		btnImpLote = ttk.Button(frame_inferior, text="🖨️ Imprimir Lote Completo", command=self.imprimir_lote)
		btnImpLote.pack(side="right", padx=5)

		btnGenPdf = ttk.Button(frame_inferior, text="📄 Generar PDF en Lote", command=self.generar_pdf_lote)
		btnGenPdf.pack(side="right", padx=5)

		self._cargar_oficinas_combobox()

	# -------------------------------------------------------------------------
	# LÓGICA DE BÚSQUEDA Y SINCRONIZACIÓN DE OFICINA
	# -------------------------------------------------------------------------
	def _cargar_oficinas_combobox(self):
		try:
			self.lote_oficinas_data = obtener_oficinas()
			valores = [o["display"] for o in self.lote_oficinas_data]
			self.cbx_lote_oficinas["values"] = valores
			if self.lote_oficinas_data:
				primera = self.lote_oficinas_data[0]
				self.lote_cod_oficina.set(primera["acta"])
				self.lote_oficina_sel.set(primera["display"])
				self.lote_ofic_personalizada.set(primera["oficina"])
		except Exception as e:
			print(f"Error cargando oficinas en lote: {e}")

	def _on_cod_oficina_keyrelease(self, _event=None):
		codigo = self.lote_cod_oficina.get().strip()
		if not codigo:
			return
		ofi = buscar_oficina_por_codigo(codigo, self.lote_oficinas_data)
		if ofi:
			self.lote_oficina_sel.set(ofi["display"])
			self.lote_ofic_personalizada.set(ofi["oficina"])
		else:
			coincidentes = filtrar_oficinas_predictivo(codigo, self.lote_oficinas_data)
			if coincidentes:
				self.cbx_lote_oficinas["values"] = [o["display"] for o in coincidentes]

	def _on_oficina_keyrelease(self, event):
		if event.keysym in ("Up", "Down", "Left", "Right", "Tab", "Escape"):
			return
		if event.keysym == "Return":
			return self._on_oficina_return()

		texto = self.cbx_lote_oficinas.get().strip()
		if not texto:
			self.cbx_lote_oficinas["values"] = [o["display"] for o in self.lote_oficinas_data]
			return

		coincidentes = filtrar_oficinas_predictivo(texto, self.lote_oficinas_data)
		valores = [o["display"] for o in coincidentes]
		self.cbx_lote_oficinas["values"] = valores

		if coincidentes:
			primer_ofi = coincidentes[0]
			if primer_ofi["acta"] == texto or primer_ofi["oficina"].lower().startswith(texto.lower()):
				self.lote_cod_oficina.set(primer_ofi["acta"])
				self.lote_ofic_personalizada.set(primer_ofi["oficina"])

	def _on_oficina_return(self, _event=None):
		valores = self.cbx_lote_oficinas["values"]
		if valores and len(valores) > 0:
			primer_display = valores[0]
			self.lote_oficina_sel.set(primer_display)
			for o in self.lote_oficinas_data:
				if o["display"] == primer_display:
					self.lote_cod_oficina.set(o["acta"])
					self.lote_ofic_personalizada.set(o["oficina"])
					break
			self.cbx_lote_oficinas["values"] = [o["display"] for o in self.lote_oficinas_data]
			self.cargar_bienes_lote()

	def _on_lote_oficina_select(self, _event=None):
		sel = self.lote_oficina_sel.get().strip()
		for o in self.lote_oficinas_data:
			if o["display"] == sel:
				self.lote_cod_oficina.set(o["acta"])
				self.lote_ofic_personalizada.set(o["oficina"])
				break
		self.cbx_lote_oficinas["values"] = [o["display"] for o in self.lote_oficinas_data]

	def _resolver_acta_actual(self):
		cod = self.lote_cod_oficina.get().strip()
		if cod:
			ofi = buscar_oficina_por_codigo(cod, self.lote_oficinas_data)
			if ofi:
				return ofi["acta"]
			return cod
		sel = self.lote_oficina_sel.get().strip()
		if sel.startswith("[") and "]" in sel:
			return sel[1:sel.index("]")]
		for o in self.lote_oficinas_data:
			if o["display"] == sel or o["oficina"] == sel:
				return o["acta"]
		return None

	def cargar_bienes_lote(self):
		acta = self._resolver_acta_actual()
		if not acta:
			mb.showerror(title="Atención", message="Ingrese un código de oficina válido o seleccione una oficina de la lista.")
			return

		filtro_txt = self.lote_filtro_sel.get()
		if "Ubicados" in filtro_txt:
			filtro = "ubicados"
		elif "Faltantes" in filtro_txt:
			filtro = "faltantes"
		elif "Primera" in filtro_txt:
			filtro = "primera_ubicacion"
		else:
			filtro = "todos"

		bienes = filtrar_bienes_oficina(acta, filtro)
		if not bienes:
			mb.showinfo(title="Resultado", message=f"No se encontraron bienes con el filtro '{filtro_txt}' para la oficina [{acta}].")
			self.nueva_lista_lote()
			return

		# Si el usuario escribió un nombre directo en 'Oficina etiqueta', aplicarlo
		ofic_personalizada = self.lote_ofic_personalizada.get().strip()
		if ofic_personalizada:
			for b in bienes:
				b["oficina_etiqueta"] = ofic_personalizada

		self.lote_items = bienes
		self._refrescar_tabla_lote()
		if self.tree_lote.get_children():
			first = self.tree_lote.get_children()[0]
			self.tree_lote.selection_set(first)
			self.previsualizar_seleccionado_lote()

	def _refrescar_tabla_lote(self):
		for item in self.tree_lote.get_children():
			self.tree_lote.delete(item)

		for i, b in enumerate(self.lote_items, 1):
			self.tree_lote.insert(
				"",
				tk.END,
				values=(
					i,
					b.get("codpat", "") or b.get("CodPat", ""),
					b.get("codint", "") or b.get("CodInt", ""),
					b.get("deno", "") or b.get("DenBien", ""),
					b.get("acta_ant", "") or b.get("ActaAnt", ""),
					b.get("estado_filtro", "") or b.get("estado_bien", ""),
					b.get("oficina_etiqueta", "")
				)
			)
		self.lbl_total_lote.config(text=f"Total en lista: {len(self.lote_items)} etiquetas")

	def on_enter_codigo_lote(self, _event=None):
		"""
		Gestión con la tecla Enter en la caja de texto 'Cód. Bien':
		  - 1er Enter: Previsualiza los datos del bien y la etiqueta sin agregarlo a la lista.
		  - 2do Enter (sobre el mismo código): Agrega el bien a la lista y lo imprime si está activa la opción.
		"""
		codigo = self.lote_codigo_agregar.get().strip()
		if not codigo:
			mb.showwarning(title="Atención", message="Ingrese un código patrimonial o interno.")
			return

		# Si este mismo código ya fue previsualizado en el primer ENTER, el 2do ENTER lo agrega e imprime
		if self._codigo_previsualizado == codigo and self._bien_pendiente_agregar is not None:
			bien_a_agregar = self._bien_pendiente_agregar
			self._bien_pendiente_agregar = None
			self._codigo_previsualizado = None
			if self._ejecutar_agregar_bien(bien_a_agregar):
				self.lote_codigo_agregar.set("")
			self.etr_lote_add.focus_set()
		else:
			# Primer ENTER: Previsualización de datos y etiqueta
			self.previsualizar_codigo_entrada(codigo)

	def previsualizar_codigo_entrada(self, codigo):
		"""Primer Enter: busca y previsualiza el bien ingresado sin agregarlo aún a la lista."""
		bien = buscar_bien_por_codigo(codigo)
		if not bien:
			mb.showerror(title="No encontrado", message=f"No se encontró ningún bien con el código '{codigo}'.")
			self._bien_pendiente_agregar = None
			self._codigo_previsualizado = None
			return False

		# Asignar la oficina activa si existe
		ofic_activa = self.lote_ofic_personalizada.get().strip()
		if ofic_activa:
			bien["oficina_etiqueta"] = ofic_activa

		self._bien_pendiente_agregar = bien
		self._codigo_previsualizado = codigo

		# Llenar los campos de datos del bien en el panel superior
		codpat = bien.get("codpat", "") or bien.get("CodPat", "")
		codint = bien.get("codint", "") or bien.get("CodInt", "")
		deno = bien.get("deno", "") or bien.get("DenBien", "")
		acta_ant = bien.get("acta_ant", "") or bien.get("ActaAnt", "")
		inv_val = bien.get("inv", "") or bien.get("Inv", "")
		ofi_act = bien.get("oficina_actual", "")
		ofi_ant = bien.get("oficina_anterior", "")
		estado = bien.get("estado_filtro", "") or bien.get("estado_bien", "") or ""
		ofic_etiq = bien.get("oficina_etiqueta", "")

		self.prev_codpat.set(codpat)
		self.prev_codint.set(codint)
		self.prev_deno.set(deno)
		self.prev_actaant.set(acta_ant)
		ubi_txt = f"[{inv_val}] {ofi_act}" if (inv_val and ofi_act) else (inv_val or ofi_act or ofi_ant)
		self.prev_ubic.set(ubi_txt)
		self.prev_estado.set(estado)
		self.prev_ofic_etiqueta.set(ofic_etiq)

		imp_aviso = " e IMPRIMIR" if self.imprimir_al_agregar.get() else ""
		if hasattr(self, 'lbl_prev_info'):
			self.lbl_prev_info.config(
				text=f"👁️ Previsualizado: [{codpat or codint}] {deno[:28]} ➔ Presione ENTER de nuevo para AGREGAR{imp_aviso}",
				foreground="#d9534f"
			)

		# Renderizar imagen de la etiqueta
		try:
			pdf_path = build_label_batch([bien], valor=0, output_name="lote_preview_single.pdf", oficina_personalizada_global=ofic_etiq)
			if pdf_path and os.path.exists(pdf_path):
				with fitz.open(pdf_path) as pdf_doc:
					if pdf_doc.page_count:
						pix = pdf_doc[0].get_pixmap(matrix=fitz.Matrix(2.2, 2.2), alpha=False)
						pil_img = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
						self.lote_photo = ImageTk.PhotoImage(pil_img)
						self.lbl_lote_preview.config(image=self.lote_photo, text="")
		except Exception as e:
			print(f"Error generando vista previa de entrada: {e}")

		self.etr_lote_add.focus_set()
		return True

	def agregar_codigo_lote(self):
		"""Acción del botón ➕ Agregar (o confirmación directa)."""
		codigo = self.lote_codigo_agregar.get().strip()
		if not codigo:
			mb.showwarning(title="Atención", message="Ingrese un código patrimonial o interno.")
			return

		if self._codigo_previsualizado == codigo and self._bien_pendiente_agregar is not None:
			bien_a_agregar = self._bien_pendiente_agregar
		else:
			bien_a_agregar = buscar_bien_por_codigo(codigo)
			if not bien_a_agregar:
				mb.showerror(title="No encontrado", message=f"No se encontró ningún bien con el código '{codigo}'.")
				return
			ofic_activa = self.lote_ofic_personalizada.get().strip()
			if ofic_activa:
				bien_a_agregar["oficina_etiqueta"] = ofic_activa

		self._bien_pendiente_agregar = None
		self._codigo_previsualizado = None
		if self._ejecutar_agregar_bien(bien_a_agregar):
			self.lote_codigo_agregar.set("")
		self.etr_lote_add.focus_set()

	def _ejecutar_agregar_bien(self, bien):
		"""Agrega un bien a self.lote_items, imprime si está habilitado y actualiza tabla."""
		# Si se modificó la oficina en el panel de detalle antes de confirmar, usarla
		ofic_detalle = self.prev_ofic_etiqueta.get().strip()
		ofic_global = self.lote_ofic_personalizada.get().strip()
		if ofic_detalle:
			bien["oficina_etiqueta"] = ofic_detalle
		elif ofic_global:
			bien["oficina_etiqueta"] = ofic_global

		# Verificar si ya existe en la lista
		cod_id = bien.get("codpat") or bien.get("codint")
		for item in self.lote_items:
			if (item.get("codpat") and item["codpat"] == bien.get("codpat")) or (item.get("codint") and item["codint"] == bien.get("codint")):
				if not mb.askyesno(title="Ya existe", message=f"El bien con código {cod_id} ya está en la lista.\n¿Desea agregarlo nuevamente?"):
					return False
				break

		# Si está activado imprimir al agregar, enviar inmediatamente a la impresora
		if self.imprimir_al_agregar.get():
			try:
				cod_print = bien.get("codpat") or bien.get("codint")
				acta_print = bien.get("inv") or bien.get("acta_ant") or "1"
				build_label(1, cod_print, acta_print, oficina_personalizada=bien.get("oficina_etiqueta"))
			except Exception as e:
				mb.showerror(title="Error al imprimir", message=f"No se pudo imprimir la etiqueta automáticamente:\n{e}")

		self.lote_items.append(bien)
		self._refrescar_tabla_lote()

		children = self.tree_lote.get_children()
		if children:
			last = children[-1]
			self.tree_lote.selection_set(last)
			self.tree_lote.see(last)
			self.previsualizar_seleccionado_lote()

		if hasattr(self, 'lbl_prev_info'):
			imp_txt = " (🖨️ Impreso)" if self.imprimir_al_agregar.get() else ""
			self.lbl_prev_info.config(
				text=f"✅ Agregado a la lista: [{cod_id}]{imp_txt}", 
				foreground="green"
			)
		return True

	def agregar_bien_desde_popup(self, bien):
		"""Callback recibido desde la ventana emergente de búsqueda individual."""
		self._bien_pendiente_agregar = None
		self._codigo_previsualizado = None
		self.lote_items.append(bien)
		self._refrescar_tabla_lote()
		children = self.tree_lote.get_children()
		if children:
			last = children[-1]
			self.tree_lote.selection_set(last)
			self.tree_lote.see(last)
			self.previsualizar_seleccionado_lote()
			self.previsualizar_seleccionado_lote()

	def abrir_popup_individual(self, valor=None):
		v = valor if valor is not None else self.valor
		codigo = self.lote_codigo_agregar.get().strip() if hasattr(self, "lote_codigo_agregar") else None
		Window_individual_popup(
			parent=self, 
			valor=v, 
			codigo_inicial=codigo,
			callback_agregar=self.agregar_bien_desde_popup,
			imprimir_al_agregar_var=self.imprimir_al_agregar
		)

	def _limpiar_detalle_preview(self):
		self._bien_pendiente_agregar = None
		self._codigo_previsualizado = None
		self.prev_codpat.set("")
		self.prev_codint.set("")
		self.prev_deno.set("")
		self.prev_actaant.set("")
		self.prev_ubic.set("")
		self.prev_ofic_etiqueta.set("")
		self.prev_estado.set("")
		self.lbl_lote_preview.config(image="", text="Vista previa de la etiqueta\n\n(50mm x 25mm)")
		if hasattr(self, 'lbl_prev_info'):
			self.lbl_prev_info.config(text="Seleccione un bien de la lista para ver su información y etiqueta", foreground="#555555")

	def _actualizar_oficina_bien_seleccionado(self):
		nueva_ofic = self.prev_ofic_etiqueta.get().strip()

		# Si hay un bien pendiente de agregar en previsualización:
		if self._bien_pendiente_agregar is not None:
			self._bien_pendiente_agregar["oficina_etiqueta"] = nueva_ofic
			try:
				pdf_path = build_label_batch([self._bien_pendiente_agregar], valor=0, output_name="lote_preview_single.pdf", oficina_personalizada_global=nueva_ofic)
				if pdf_path and os.path.exists(pdf_path):
					with fitz.open(pdf_path) as pdf_doc:
						if pdf_doc.page_count:
							pix = pdf_doc[0].get_pixmap(matrix=fitz.Matrix(2.2, 2.2), alpha=False)
							pil_img = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
							self.lote_photo = ImageTk.PhotoImage(pil_img)
							self.lbl_lote_preview.config(image=self.lote_photo, text="")
			except Exception as e:
				print(f"Error actualizando preview de bien pendiente: {e}")
			if hasattr(self, 'lbl_prev_info'):
				imp_aviso = " e IMPRIMIR" if self.imprimir_al_agregar.get() else ""
				self.lbl_prev_info.config(text=f"✅ Oficina asignada: {nueva_ofic} ➔ Presione ENTER en 'Cód. Bien' para agregar{imp_aviso}", foreground="green")
			return

		seleccion = self.tree_lote.selection()
		if not seleccion:
			mb.showwarning(title="Atención", message="Seleccione un bien de la tabla para modificar su oficina.")
			return
		item_idx = self.tree_lote.index(seleccion[0])
		if item_idx < 0 or item_idx >= len(self.lote_items):
			return
		self.lote_items[item_idx]["oficina_etiqueta"] = nueva_ofic
		self.tree_lote.set(seleccion[0], column="oficina", value=nueva_ofic)
		self.previsualizar_seleccionado_lote()
		if hasattr(self, 'lbl_prev_info'):
			self.lbl_prev_info.config(text=f"✅ Oficina actualizada: {nueva_ofic}", foreground="green")

	def imprimir_seleccionado_lote(self):
		seleccion = self.tree_lote.selection()
		if not seleccion:
			mb.showwarning(title="Atención", message="Seleccione un bien de la tabla para imprimir.")
			return
		item_idx = self.tree_lote.index(seleccion[0])
		if item_idx < 0 or item_idx >= len(self.lote_items):
			return
		item = self.lote_items[item_idx]
		try:
			cod = item.get("codpat", "") or item.get("codint", "")
			acta = item.get("inv", "") or item.get("acta_ant", "") or "1"
			ofic = self.prev_ofic_etiqueta.get().strip() or item.get("oficina_etiqueta", "")
			build_label(1, cod, acta, oficina_personalizada=ofic)
			if hasattr(self, 'lbl_prev_info'):
				self.lbl_prev_info.config(text=f"🖨️ Etiqueta impresa para: {cod}", foreground="blue")
		except Exception as e:
			mb.showerror(title="Error al imprimir", message=f"No se pudo imprimir la etiqueta:\n{e}")

	def quitar_seleccionados_lote(self):
		seleccion = self.tree_lote.selection()
		if not seleccion:
			mb.showwarning(title="Atención", message="Seleccione al menos un bien de la tabla para quitar.")
			return

		indices_a_quitar = sorted([self.tree_lote.index(s) for s in seleccion], reverse=True)
		for idx in indices_a_quitar:
			if 0 <= idx < len(self.lote_items):
				self.lote_items.pop(idx)

		self._refrescar_tabla_lote()
		if self.tree_lote.get_children():
			first = self.tree_lote.get_children()[0]
			self.tree_lote.selection_set(first)
			self.previsualizar_seleccionado_lote()
		else:
			self._limpiar_detalle_preview()

	def nueva_lista_lote(self):
		self.lote_items.clear()
		self._refrescar_tabla_lote()
		self._limpiar_detalle_preview()

	def _on_tree_lote_select(self, _event=None):
		self._bien_pendiente_agregar = None
		self._codigo_previsualizado = None
		seleccion = self.tree_lote.selection()
		if seleccion:
			self.previsualizar_seleccionado_lote()

	def previsualizar_seleccionado_lote(self):
		seleccion = self.tree_lote.selection()
		if not seleccion:
			self._limpiar_detalle_preview()
			return
		item_idx = self.tree_lote.index(seleccion[0])
		if item_idx < 0 or item_idx >= len(self.lote_items):
			self._limpiar_detalle_preview()
			return
		item = self.lote_items[item_idx]

		# Llenar los campos de datos del bien seleccionado
		codpat = item.get("codpat", "") or item.get("CodPat", "")
		codint = item.get("codint", "") or item.get("CodInt", "")
		deno = item.get("deno", "") or item.get("DenBien", "")
		acta_ant = item.get("acta_ant", "") or item.get("ActaAnt", "")
		inv_val = item.get("inv", "") or item.get("Inv", "")
		ofi_act = item.get("oficina_actual", "")
		ofi_ant = item.get("oficina_anterior", "")
		estado = item.get("estado_filtro", "") or item.get("estado_bien", "") or ""
		ofic_etiq = item.get("oficina_etiqueta", "") or self.lote_ofic_personalizada.get().strip()

		self.prev_codpat.set(codpat)
		self.prev_codint.set(codint)
		self.prev_deno.set(deno)
		self.prev_actaant.set(acta_ant)
		ubi_txt = f"[{inv_val}] {ofi_act}" if (inv_val and ofi_act) else (inv_val or ofi_act or ofi_ant)
		self.prev_ubic.set(ubi_txt)
		self.prev_estado.set(estado)
		self.prev_ofic_etiqueta.set(ofic_etiq)

		if hasattr(self, 'lbl_prev_info'):
			self.lbl_prev_info.config(
				text=f"Bien #{item_idx + 1} de {len(self.lote_items)}: [{codpat or codint}] {deno[:38]}",
				foreground="#004488"
			)

		# Renderizar etiqueta
		try:
			ofi_render = self.prev_ofic_etiqueta.get().strip() or ofic_etiq or self.lote_ofic_personalizada.get().strip()
			pdf_path = build_label_batch([item], valor=0, output_name="lote_preview_single.pdf", oficina_personalizada_global=ofi_render)
			if not pdf_path or not os.path.exists(pdf_path):
				return
			with fitz.open(pdf_path) as pdf_doc:
				if not pdf_doc.page_count:
					return
				pix = pdf_doc[0].get_pixmap(matrix=fitz.Matrix(2.2, 2.2), alpha=False)
			pil_img = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
			self.lote_photo = ImageTk.PhotoImage(pil_img)
			self.lbl_lote_preview.config(image=self.lote_photo, text="")
		except Exception as e:
			print(f"Error generando vista previa en lote: {e}")

	def generar_pdf_lote(self):
		if not self.lote_items:
			mb.showwarning(title="Atención", message="La lista está vacía. Cargue bienes de una oficina o agregue códigos.")
			return

		ofic_global = self.lote_ofic_personalizada.get().strip()
		sugerido = f"Etiquetas_Lote_{len(self.lote_items)}_items.pdf"
		
		destino = filedialog.asksaveasfilename(
			title="Guardar PDF de etiquetas en lote",
			initialdir="labels/lotes",
			initialfile=sugerido,
			defaultextension=".pdf",
			filetypes=[("Archivos PDF", "*.pdf")]
		)
		if not destino:
			return

		try:
			dir_padre = os.path.dirname(destino)
			nombre_archivo = os.path.basename(destino)
			if dir_padre:
				os.makedirs(dir_padre, exist_ok=True)

			pdf_path = build_label_batch(
				self.lote_items, 
				valor=0, 
				output_name=nombre_archivo, 
				oficina_personalizada_global=ofic_global if ofic_global else None
			)
			if not pdf_path or not os.path.exists(pdf_path):
				raise RuntimeError("No se generó el archivo PDF.")

			if os.path.abspath(pdf_path) != os.path.abspath(destino):
				import shutil
				shutil.copy2(pdf_path, destino)
				pdf_path = destino

			abrir = mb.askyesno(
				title="Lote Generado Exitosamente",
				message=f"Se generó el PDF con {len(self.lote_items)} etiquetas en:\n{pdf_path}\n\n¿Desea abrir el archivo ahora?"
			)
			if abrir:
				try:
					os.startfile(pdf_path)
				except Exception as err:
					mb.showerror(title="Error al abrir", message=f"No se pudo abrir el visor de PDF:\n{err}")

		except Exception as e:
			mb.showerror(title="Error", message=f"Ocurrió un error al generar el lote en PDF:\n{e}")

	def imprimir_lote(self):
		if not self.lote_items:
			mb.showwarning(title="Atención", message="La lista está vacía. Cargue bienes de una oficina o agregue códigos.")
			return

		confirm = mb.askyesno(
			title="Confirmar Impresión en Lote",
			message=f"Se enviarán {len(self.lote_items)} etiquetas a la impresora predeterminada.\n\n¿Desea continuar con la impresión?"
		)
		if not confirm:
			return

		ofic_global = self.lote_ofic_personalizada.get().strip()
		try:
			pdf_path = build_label_batch(
				self.lote_items, 
				valor=1, 
				oficina_personalizada_global=ofic_global if ofic_global else None
			)
			if pdf_path:
				mb.showinfo(title="Impresión enviada", message=f"Se han enviado {len(self.lote_items)} etiquetas a la cola de impresión.")
		except Exception as e:
			mb.showerror(title="Error de impresión", message=f"No se pudo enviar el lote a la impresora:\n{e}")

	# -------------------------------------------------------------------------
	# PESTAÑA 2: AJUSTES Y CONFIGURACIÓN
	# -------------------------------------------------------------------------
	def tab_ajustes_init(self):
		self.ent = tk.StringVar()
		self.per = tk.StringVar()

		frame_izq = tk.Frame(self.tab_ajustes, bg="#ffffff")
		frame_izq.pack(fill='both', side='left', expand=True, padx=20, pady=20)

		lblEnt = ttk.Label(frame_izq, text="Entidad:")
		lblEnt.grid(row=0, column=0, sticky="w", pady=6)
		etrEnt = ttk.Entry(frame_izq, textvariable=self.ent, width=40)
		etrEnt.grid(row=0, column=1, sticky="ew", pady=6, padx=5)

		lblPer = ttk.Label(frame_izq, text="Periodo:")
		lblPer.grid(row=1, column=0, sticky="w", pady=6)
		cbxPer = ttk.Combobox(frame_izq, values=[2020, 2021, 2022, 2023, 2024, 2025, 2026], textvariable=self.per, state="readonly", width=38)
		cbxPer.grid(row=1, column=1, sticky="ew", pady=6, padx=5)

		btnActualizar = ttk.Button(frame_izq, text="💾 Guardar Ajustes", command=self.actualizar)
		btnActualizar.grid(row=2, column=1, sticky="e", pady=15, padx=5)

		frame_der = tk.Frame(self.tab_ajustes, bg="#ffffff")
		frame_der.pack(fill='both', side='right', padx=20, pady=20)

		ttk.Label(frame_der, text="Logo de etiqueta:").pack(pady=4)
		self.img_label = tk.Label(frame_der, bg="#eaeaea", width=25, height=12)
		self.img_label.pack(pady=4)

		datos = datos_iniciales()
		if datos and len(datos) > 2:
			self.ent.set(str(datos[1]))
			self.per.set(str(datos[2]))

	def load_config(self):
		if os.path.exists(self.config_path):
			self.config.read(self.config_path)
			if 'Settings' in self.config:
				self.img_label_path = self.config['Settings'].get('img_label_path', '')

	def cargar_imagen_guardada(self):
		if self.img_label_path and os.path.exists(self.img_label_path):
			try:
				image = Image.open(self.img_label_path)
				image.thumbnail((180, 180))
				self.photo = ImageTk.PhotoImage(image)
				self.img_label.config(image=self.photo)
			except Exception as e:
				print(f"Error cargando imagen de ajustes: {e}")

	def actualizar(self):
		lista = [self.ent.get(), self.per.get()]
		try:
			actualizar_datos(1, lista)
			mb.showinfo(title="Acontar S.A.C.", message="¡Ajustes actualizados con éxito!")
		except Exception as e:
			mb.showerror(title="Error", message=f"Ocurrió un error: {e}")
		finally:
			self.focus_set()


# =============================================================================
# VENTANA EMERGENTE (POPUP): BÚSQUEDA INDIVIDUAL Y AGREGAR A LA LISTA
# =============================================================================
class Window_individual_popup(tk.Toplevel):
	"""Ventana emergente para consultar bien en detalle y agregarlo a la lista de impresión."""
	def __init__(self, parent, valor=1, codigo_inicial=None, callback_agregar=None, imprimir_al_agregar_var=None):
		super().__init__(parent)
		self.parent = parent
		self.valor = valor or 1
		self.callback_agregar = callback_agregar
		self.imprimir_al_agregar_var = imprimir_al_agregar_var
		self.title("Búsqueda Detallada - Agregar Bien a la Lista")
		self.iconbitmap('./img/favicon.ico')
		self.geometry("820x520")
		self.minsize(780, 480)
		self.transient(parent)
		self.grab_set()

		self.acta = tk.StringVar()
		self.codi = tk.StringVar()
		self.deno = tk.StringVar()
		self.codI = tk.StringVar()
		self.inve = tk.StringVar()
		self.codP = tk.StringVar()
		self.ubic = tk.StringVar()
		self.ofic = tk.StringVar()
		self.loca = tk.StringVar()
		self.area = tk.StringVar()
		self.imprimir_aqui = tk.BooleanVar(value=imprimir_al_agregar_var.get() if imprimir_al_agregar_var else False)
		self._codigo_consultado = None

		self._crear_widgets()

		if codigo_inicial:
			self.codi.set(codigo_inicial)
			if self.valor == 1:
				self.buscar()
			elif self.valor == 2:
				self.buscar_sobrante()

		# Iniciar foco directamente en el botón Agregar
		self.btnAgregar.focus_set()
		self.after(50, lambda: self.btnAgregar.focus_set())

	def _crear_widgets(self):
		contenedor = ttk.Frame(self, padding=10)
		contenedor.pack(fill="both", expand=True)

		# Marco Izquierdo: Formulario
		frame_form = tk.Frame(contenedor, bg="#ffffff", bd=1, relief="groove", padx=8, pady=8)
		frame_form.pack(side="left", fill="both", expand=True, padx=(0, 8))

		# Marco Derecho: Vista Previa
		frame_der = tk.Frame(contenedor, bd=1, relief="groove", padx=6, pady=6)
		frame_der.pack(side="right", fill="y")

		frame_popup_img = tk.Frame(frame_der, bg="#ffffff", bd=2, relief="groove", width=320, height=160)
		frame_popup_img.pack_propagate(False)
		frame_popup_img.pack(fill="none", expand=False, pady=4)

		self.lbl_preview = tk.Label(frame_popup_img, text="Vista previa de la etiqueta\n\n(50mm x 25mm)", bg="#ffffff", fg="#666666", font=("Segoe UI", 9))
		self.lbl_preview.pack(fill="both", expand=True)

		if self.valor == 1:
			# Labels
			ttk.Label(frame_form, text="Código Pat/Int:").grid(column=0, row=0, padx=4, pady=3, sticky=EW)
			ttk.Label(frame_form, text="Ficha:").grid(column=0, row=1, padx=4, pady=3, sticky=EW)
			ttk.Label(frame_form, text="Denominación:").grid(column=0, row=2, padx=4, pady=3, sticky=EW)
			ttk.Label(frame_form, text="Código Interno:").grid(column=0, row=3, padx=4, pady=3, sticky=EW)
			ttk.Label(frame_form, text="Código Patrimonial:").grid(column=0, row=4, padx=4, pady=3, sticky=EW)
			ttk.Label(frame_form, text="Ubicación actual:").grid(column=0, row=5, padx=4, pady=3, sticky=EW)
			ttk.Label(frame_form, text="Ubicación anterior:").grid(column=0, row=6, padx=4, pady=3, sticky=EW)
			ttk.Label(frame_form, text="Oficina etiqueta:").grid(column=0, row=7, padx=4, pady=3, sticky=EW)

			# Entrys
			self.etrCod = ttk.Entry(frame_form, textvariable=self.codi, width=18)
			self.etrCod.grid(column=1, row=0, padx=4, pady=3, sticky=EW)
			self.etrCod.bind("<Return>", lambda _e: self.buscar())

			self.etrAct = ttk.Entry(frame_form, textvariable=self.acta)
			self.etrAct.grid(column=1, row=1, padx=4, pady=3, sticky=EW)
			self.acta.trace_add("write", self._acta_cambiada)

			ttk.Button(frame_form, text="🔍 Buscar", command=self.buscar).grid(column=2, row=0, padx=4, pady=3, sticky="nsew")
			ttk.Button(frame_form, text="👁️ Previsualizar", command=self.preview_pdf).grid(column=2, row=1, padx=4, pady=3, sticky="nsew")

			ttk.Entry(frame_form, textvariable=self.deno).grid(column=1, row=2, columnspan=2, padx=4, pady=3, sticky=EW)
			ttk.Entry(frame_form, textvariable=self.codI).grid(column=1, row=3, columnspan=2, padx=4, pady=3, sticky=EW)
			ttk.Entry(frame_form, textvariable=self.codP).grid(column=1, row=4, columnspan=2, padx=4, pady=3, sticky=EW)
			ttk.Entry(frame_form, textvariable=self.inve).grid(column=1, row=5, columnspan=2, padx=4, pady=3, sticky=EW)
			ttk.Entry(frame_form, textvariable=self.ubic).grid(column=1, row=6, columnspan=2, padx=4, pady=3, sticky=EW)

			# OFICINA DIRECTAMENTE EDITABLE (Sin checkbox)
			self.etrOfi = ttk.Entry(frame_form, textvariable=self.ofic)
			self.etrOfi.grid(column=1, row=7, columnspan=2, padx=4, pady=3, sticky=EW)
			self.etrOfi.bind("<Return>", lambda _e: self.preview_pdf())

		elif self.valor == 2:
			ttk.Label(frame_form, text="Item:").grid(column=0, row=0, padx=4, pady=3, sticky=EW)
			ttk.Label(frame_form, text="Local:").grid(column=0, row=1, padx=4, pady=3, sticky=EW)
			ttk.Label(frame_form, text="Área:").grid(column=0, row=2, padx=4, pady=3, sticky=EW)
			ttk.Label(frame_form, text="Oficina etiqueta:").grid(column=0, row=3, padx=4, pady=3, sticky=EW)
			ttk.Label(frame_form, text="Denominación:").grid(column=0, row=4, padx=4, pady=3, sticky=EW)

			self.etrCod = ttk.Entry(frame_form, textvariable=self.codi, width=18)
			self.etrCod.grid(column=1, row=0, padx=4, pady=3, sticky=EW)
			self.etrCod.bind("<Return>", lambda _e: self.buscar_sobrante())

			ttk.Button(frame_form, text="🔍 Buscar", command=self.buscar_sobrante).grid(column=2, row=0, padx=4, pady=3, sticky="nsew")

			ttk.Entry(frame_form, textvariable=self.loca).grid(column=1, row=1, columnspan=2, padx=4, pady=3, sticky=EW)
			ttk.Entry(frame_form, textvariable=self.area).grid(column=1, row=2, columnspan=2, padx=4, pady=3, sticky=EW)
			self.etrOfi = ttk.Entry(frame_form, textvariable=self.ofic)
			self.etrOfi.grid(column=1, row=3, columnspan=2, padx=4, pady=3, sticky=EW)
			ttk.Entry(frame_form, textvariable=self.deno).grid(column=1, row=4, columnspan=2, padx=4, pady=3, sticky=EW)

		frame_form.columnconfigure(1, weight=1)

		# Marco de Botones de Acción inferior
		frame_acciones = ttk.Frame(self, padding=8)
		frame_acciones.pack(fill="x", side="bottom")

		chkImp = ttk.Checkbutton(
			frame_acciones, 
			text="🖨️ Imprimir etiqueta al agregar", 
			variable=self.imprimir_aqui,
			command=self._sync_imprimir_var
		)
		chkImp.pack(side="left", padx=10)

		btnCerrar = ttk.Button(frame_acciones, text="Cerrar", command=self.destroy)
		btnCerrar.pack(side="right", padx=5)

		self.btnAgregar = ttk.Button(frame_acciones, text="➕ Agregar a la Lista de Lote", command=self.agregar_a_lista, default="active")
		self.btnAgregar.pack(side="right", padx=5)
		self.btnAgregar.bind("<Return>", lambda _e: self.agregar_a_lista())
		self.btnAgregar.bind("<KP_Enter>", lambda _e: self.agregar_a_lista())

		self.btnImpYAdd = ttk.Button(frame_acciones, text="🖨️ Imprimir y Agregar", command=self.imprimir_y_agregar)
		self.btnImpYAdd.pack(side="right", padx=5)
		self.btnImpYAdd.bind("<Return>", lambda _e: self.imprimir_y_agregar())
		self.btnImpYAdd.bind("<KP_Enter>", lambda _e: self.imprimir_y_agregar())

		self.lbl_estado = ttk.Label(frame_acciones, text="", foreground="green", font=("Segoe UI", 9, "italic"))
		self.lbl_estado.pack(side="left", padx=10)

	def _sync_imprimir_var(self):
		if self.imprimir_al_agregar_var:
			self.imprimir_al_agregar_var.set(self.imprimir_aqui.get())

	def _acta_cambiada(self, *_args):
		acta = self.acta.get().strip()
		if acta:
			try:
				ubi = data_label_ubi(acta)
				if ubi and len(ubi) > 0 and len(ubi[0]) > 0 and ubi[0][0] is not None:
					self.ofic.set(str(ubi[0][0]))
			except Exception:
				pass

	def buscar(self):
		codigo = self.codi.get().strip()
		if not codigo:
			mb.showerror(title="Atención", message="Ingrese un código a consultar.")
			return False
		try:
			r = mostrar_datos_print(codigo)
			if not r:
				mb.showerror(title="No encontrado", message="No se encontraron datos para el código ingresado.")
				return False
			self.deno.set(r[0] or "")
			self.codI.set(r[1] or "")
			self.codP.set(r[2] or "")
			self.inve.set(r[3] or "")
			self.ubic.set(r[4] or "")
			self._codigo_consultado = codigo

			# Extraer acta de inventario o anterior si no se había escrito
			if not self.acta.get().strip():
				if r[3] and " - " in str(r[3]):
					self.acta.set(str(r[3]).split(" - ")[0].strip())
				elif r[4] and " - " in str(r[4]):
					self.acta.set(str(r[4]).split(" - ")[0].strip())

			self.preview_pdf()
			self.btnAgregar.focus_set()
			return True
		except Exception as e:
			mb.showerror(title="Error", message=f"No se pudieron consultar los datos:\n{e}")
			return False

	def buscar_sobrante(self):
		codigo = self.codi.get().strip()
		if not codigo:
			mb.showerror(title="Atención", message="Ingrese un código de bien sobrante.")
			return False
		try:
			r = mostrar_datos_sobrante(codigo)
			if not r:
				mb.showerror(title="Error", message="No se encontraron datos para el código de sobrante.")
				return False
			self.loca.set(str(r[0]))
			self.area.set(str(r[1]))
			self.ofic.set(str(r[2]))
			self.deno.set(str(r[3]))
			pdf_path = build_label_sobrante(0, self.loca.get(), self.area.get(), self.ofic.get(), self.deno.get())
			self._mostrar_pdf(pdf_path)
			self.btnAgregar.focus_set()
			return True
		except Exception as e:
			mb.showerror(title="Error", message=f"No se pudo consultar el sobrante:\n{e}")
			return False

	def preview_pdf(self):
		codigo = self.codi.get().strip() or self.codP.get().strip() or self.codI.get().strip()
		acta = self.acta.get().strip() or "1"
		if not codigo:
			return False
		try:
			pdf_path = build_label(0, codigo, acta, oficina_personalizada=self.ofic.get().strip())
			self._mostrar_pdf(pdf_path)
			return True
		except Exception as e:
			print(f"Error generando preview: {e}")
			return False

	def _mostrar_pdf(self, pdf_path):
		try:
			with fitz.open(pdf_path) as pdf_doc:
				if not pdf_doc.page_count:
					return
				pix = pdf_doc[0].get_pixmap(matrix=fitz.Matrix(2.2, 2.2), alpha=False)
			pil_img = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
			self.photo = ImageTk.PhotoImage(pil_img)
			self.lbl_preview.config(image=self.photo, text="")
		except Exception as e:
			print(f"Error mostrando PDF en popup: {e}")

	def agregar_a_lista(self):
		codpat = self.codP.get().strip() or self.codi.get().strip()
		codint = self.codI.get().strip() or self.codi.get().strip()
		deno = self.deno.get().strip()

		if not codpat and not codint:
			mb.showwarning(title="Atención", message="Debe buscar o ingresar al menos un código válido antes de agregar.")
			return

		ofic_val = self.ofic.get().strip()
		acta_val = self.acta.get().strip() or "1"

		# Imprimir si el checkbox está activo
		if self.imprimir_aqui.get():
			try:
				build_label(1, codpat or codint, acta_val, oficina_personalizada=ofic_val)
			except Exception as e:
				mb.showerror(title="Error al imprimir", message=f"No se pudo imprimir la etiqueta:\n{e}")

		bien_dict = {
			"codpat": codpat,
			"codint": codint,
			"deno": deno,
			"acta_ant": acta_val,
			"inv": self.inve.get().strip(),
			"oficina_actual": self.inve.get().strip(),
			"oficina_anterior": self.ubic.get().strip(),
			"estado_bien": "",
			"estado_filtro": "Manual",
			"oficina_etiqueta": ofic_val
		}

		if self.callback_agregar:
			self.callback_agregar(bien_dict)

		self.lbl_estado.config(text=f"✅ Agregado a la lista: {codpat or codint}")

		# Limpiar código para el siguiente escaneo y mantener el foco en el botón agregar
		self.codi.set("")
		self.btnAgregar.focus_set()

	def imprimir_y_agregar(self):
		self.imprimir_aqui.set(True)
		self._sync_imprimir_var()
		self.agregar_a_lista()
