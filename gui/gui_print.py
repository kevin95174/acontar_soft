import os
import traceback
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
	mostrar_datos_sobrante,
	buscar_oficinas_predictivo
)
from label.label_gen import (
	build_label, 
	build_label_batch,
	obtener_impresoras_sistema,
	obtener_impresora_configurada,
	guardar_impresora_configurada
)
from label.label_sobrante import build_label_sobrante
from services.label_batch_service import (
	obtener_oficinas, 
	filtrar_bienes_oficina, 
	buscar_bien_por_codigo,
	filtrar_oficinas_predictivo,
	buscar_oficina_por_codigo
)


def _resolver_codigo_impresion(bien):
	"""
	Obtiene el código más específico para buscar/imprimir un bien:
	si codpat es vacío, 'NO CATALOGADO' o 'S/C', prioriza codint.
	"""
	if not isinstance(bien, dict):
		return str(bien or "").strip()
	codpat = str(bien.get("codpat") or bien.get("CodPat") or "").strip()
	codint = str(bien.get("codint") or bien.get("CodInt") or "").strip()
	if codpat and codpat.upper() not in ("NO CATALOGADO", "S/C", "SIN CODIGO", "SIN CÓDIGO", "---", "-"):
		return codpat
	return codint or codpat

class Window_print(tk.Toplevel):
	"""Ventana principal de impresión de etiquetas en lote y por oficina."""
	def __init__(self, root=None, valor=1):
		super().__init__(root)
		self.root = root
		self.valor = valor or 1
		self.title("Impresión de Etiquetas — Gestión en Lote y por Oficina")
		self.geometry("1100x740")
		self.minsize(980, 640)
		self.config_path = 'config.ini'
		self.config = configparser.ConfigParser()
		self.img_label_path = None
		self.impresora_var = tk.StringVar()
		self.grab_set()
		self.focus_set()

		self._cargar_icono()
		self._configurar_estilos()
		self._centrar_ventana(1100, 740)

		self.nbk = ttk.Notebook(self, style="Print.TNotebook")
		self.tab_lote   = tk.Frame(self.nbk, bg="#f8fafc")
		self.tab_ajustes = tk.Frame(self.nbk, bg="#f8fafc")

		self.nbk.add(self.tab_lote,    text="  🖨️  Impresión en Lote / Por Oficina  ")
		self.nbk.add(self.tab_ajustes, text="  ⚙️  Ajustes  ")
		self.nbk.pack(fill="both", expand=True, padx=0, pady=0)

		self.tab_lote_init()
		self.tab_ajustes_init()
		self.load_config()
		self.cargar_imagen_guardada()
		self._cargar_impresoras()

		# Si se abrió explícitamente para sobrantes (valor == 2), abrir popup de sobrante
		if self.valor == 2:
			self.after(150, lambda: self.abrir_popup_individual(valor=2))

	# -------------------------------------------------------------------------
	# HELPERS DE ESTILO E ICONO
	# -------------------------------------------------------------------------
	def _cargar_icono(self):
		try:
			from utils.helpers import resource_path
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

		# Notebook moderno
		style.configure("Print.TNotebook",
			background="#f1f5f9",
			tabmargins=[0, 0, 0, 0]
		)
		style.configure("Print.TNotebook.Tab",
			font=("Segoe UI", 9, "bold"),
			padding=[14, 6],
			background="#e2e8f0",
			foreground="#475569"
		)
		style.map("Print.TNotebook.Tab",
			background=[("selected", "#ffffff")],
			foreground=[("selected", "#1e293b")]
		)

		# LabelFrame card
		style.configure("Print.TLabelframe",
			background="#ffffff",
			relief="solid",
			borderwidth=1,
			bordercolor="#e2e8f0"
		)
		style.configure("Print.TLabelframe.Label",
			background="#ffffff",
			foreground="#475569",
			font=("Segoe UI", 8, "bold")
		)

		# Treeview moderno
		style.configure("Print.Treeview",
			background="#ffffff",
			fieldbackground="#ffffff",
			foreground="#0f172a",
			font=("Segoe UI", 9),
			rowheight=24
		)
		style.configure("Print.Treeview.Heading",
			background="#f1f5f9",
			foreground="#475569",
			font=("Segoe UI", 8, "bold"),
			relief="flat"
		)
		style.map("Print.Treeview",
			background=[("selected", "#2563eb")],
			foreground=[("selected", "#ffffff")]
		)

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

		# Variables para el popup predictivo de búsqueda de oficinas (igual a gui_app.py)
		self._popup_oficinas = None
		self._listbox_oficinas = None
		self._lbl_popup_info = None
		self._resultados_oficinas_actuales = []
		self._entry_activo_oficina = None
		self.bind("<Unmap>", lambda _e: self._cerrar_popup_oficinas())
		self.bind("<Destroy>", lambda _e: self._cerrar_popup_oficinas())

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

		container = tk.Frame(self.tab_lote, bg="#f8fafc")
		container.pack(fill="both", expand=True, padx=10, pady=10)

		# 1. Panel Superior: Filtros, Selección y Acciones de Entrada
		frame_filtros = ttk.LabelFrame(container, text=" 🔎 Selección de Oficina, Filtros y Entrada de Bienes ", style="Print.TLabelframe", padding=8)
		frame_filtros.pack(fill="x", pady=(0, 8))

		# Fila 0: Búsqueda por Código, Buscador Predictivo de Oficina, Filtro de Estado y Botón Cargar
		lblCodOfi = ttk.Label(frame_filtros, text="Cód. Oficina:")
		lblCodOfi.grid(row=0, column=0, padx=4, pady=4, sticky="w")

		self.etr_cod_oficina = ttk.Entry(frame_filtros, textvariable=self.lote_cod_oficina, width=8)
		self.etr_cod_oficina.grid(row=0, column=1, padx=(0, 8), pady=4, sticky="w")
		self.etr_cod_oficina.bind("<KeyRelease>", self._on_cod_oficina_keyrelease)
		self.etr_cod_oficina.bind("<Return>", lambda _e: self.cargar_bienes_lote())

		lblOfi = ttk.Label(frame_filtros, text="Buscar Oficina:")
		lblOfi.grid(row=0, column=2, padx=4, pady=4, sticky="w")

		frame_busq_ofi = tk.Frame(frame_filtros, bg="#ffffff")
		frame_busq_ofi.grid(row=0, column=3, padx=4, pady=4, sticky="ew")
		frame_busq_ofi.columnconfigure(0, weight=1)

		self.etr_lote_oficinas = ttk.Entry(
			frame_busq_ofi,
			textvariable=self.lote_oficina_sel,
			width=32,
			font=("Segoe UI", 9)
		)
		self.etr_lote_oficinas.grid(row=0, column=0, sticky="ew")
		self.etr_lote_oficinas.bind("<FocusIn>", lambda _e: self.etr_lote_oficinas.select_range(0, tk.END))
		self.cbx_lote_oficinas = self.etr_lote_oficinas

		self.btn_desplegar_ofi = ttk.Button(
			frame_busq_ofi,
			text="▼",
			width=3,
			command=lambda: self._desplegar_todas_oficinas(self.etr_lote_oficinas)
		)
		self.btn_desplegar_ofi.grid(row=0, column=1, padx=(3, 0))

		self._vincular_busqueda_predictiva_oficina(self.etr_lote_oficinas)

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
				"Todos (Ubicados + Asignados)",
				"Crear una nueva lista"
			]
		)
		self.cbx_lote_filtro.grid(row=0, column=5, padx=4, pady=4, sticky="ew")
		self.cbx_lote_filtro.bind("<<ComboboxSelected>>", self._on_estado_filtro_select)

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

		# Fila 2: Selector de Impresora y Checkbox para imprimir automáticamente al agregar
		lblImp = ttk.Label(frame_filtros, text="Impresora:")
		lblImp.grid(row=2, column=0, columnspan=2, padx=4, pady=(2, 4), sticky="w")

		frame_imp_sel = tk.Frame(frame_filtros, bg="#ffffff")
		frame_imp_sel.grid(row=2, column=2, columnspan=2, padx=4, pady=(2, 4), sticky="ew")
		frame_imp_sel.columnconfigure(0, weight=1)

		self.cbx_impresora_lote = ttk.Combobox(
			frame_imp_sel,
			textvariable=self.impresora_var,
			state="readonly",
			font=("Segoe UI", 9)
		)
		self.cbx_impresora_lote.grid(row=0, column=0, sticky="ew")
		self.cbx_impresora_lote.bind("<<ComboboxSelected>>", self._on_impresora_seleccionada)

		btn_refresh_imp = ttk.Button(
			frame_imp_sel,
			text="🔄",
			width=3,
			command=self._cargar_impresoras
		)
		btn_refresh_imp.grid(row=0, column=1, padx=(3, 0))

		chkImpAlAgregar = ttk.Checkbutton(
			frame_filtros, 
			text="🖨️ Imprimir automáticamente al agregar a la lista", 
			variable=self.imprimir_al_agregar
		)
		chkImpAlAgregar.grid(row=2, column=4, columnspan=4, padx=(8, 4), pady=(2, 4), sticky="w")

		frame_filtros.columnconfigure(3, weight=2)
		frame_filtros.columnconfigure(5, weight=1)

		# 2. Panel de Previsualización y Detalle del Bien Seleccionado
		frame_preview_panel = ttk.LabelFrame(container, text=" 📋 Detalle y Vista Previa del Bien Seleccionado ", style="Print.TLabelframe", padding=8)
		frame_preview_panel.pack(fill="x", pady=(0, 8))

		# Lado Izquierdo: Campos donde se previsualizan los datos del bien
		frame_datos_bien = tk.Frame(frame_preview_panel, bg="#ffffff")
		frame_datos_bien.pack(side="left", fill="both", expand=True, padx=(2, 8))

		# Fila 0: Denominación (ancho completo)
		ttk.Label(frame_datos_bien, text="Denominación:").grid(row=0, column=0, padx=4, pady=3, sticky="w")
		self.etr_prev_deno = ttk.Entry(frame_datos_bien, textvariable=self.prev_deno, state="readonly", font=("Segoe UI", 9, "bold"))
		self.etr_prev_deno.grid(row=0, column=1, columnspan=5, padx=4, pady=3, sticky="ew")

		# Fila 1: Códigos y Acta/Ficha
		ttk.Label(frame_datos_bien, text="Cód. Patrimonial:").grid(row=1, column=0, padx=4, pady=3, sticky="w")
		ttk.Entry(frame_datos_bien, textvariable=self.prev_codpat, state="readonly", width=16).grid(row=1, column=1, padx=4, pady=3, sticky="ew")

		ttk.Label(frame_datos_bien, text="Cód. Interno:").grid(row=1, column=2, padx=(8, 4), pady=3, sticky="w")
		ttk.Entry(frame_datos_bien, textvariable=self.prev_codint, state="readonly", width=14).grid(row=1, column=3, padx=4, pady=3, sticky="ew")

		ttk.Label(frame_datos_bien, text="Ficha / Acta:").grid(row=1, column=4, padx=(8, 4), pady=3, sticky="w")
		ttk.Entry(frame_datos_bien, textvariable=self.prev_actaant, state="readonly", width=14).grid(row=1, column=5, padx=4, pady=3, sticky="ew")

		# Fila 2: Ubicación/Inv, Estado y Oficina Etiqueta
		ttk.Label(frame_datos_bien, text="Ubicación / Inv.:").grid(row=2, column=0, padx=4, pady=3, sticky="w")
		ttk.Entry(frame_datos_bien, textvariable=self.prev_ubic, state="readonly", width=16).grid(row=2, column=1, padx=4, pady=3, sticky="ew")

		ttk.Label(frame_datos_bien, text="Estado Inv.:").grid(row=2, column=2, padx=(8, 4), pady=3, sticky="w")
		ttk.Entry(frame_datos_bien, textvariable=self.prev_estado, state="readonly", width=14).grid(row=2, column=3, padx=4, pady=3, sticky="ew")

		ttk.Label(frame_datos_bien, text="Oficina Etiqueta:").grid(row=2, column=4, padx=(8, 4), pady=3, sticky="w")
		self.etr_prev_ofic = ttk.Entry(frame_datos_bien, textvariable=self.prev_ofic_etiqueta, width=14)
		self.etr_prev_ofic.grid(row=2, column=5, padx=4, pady=3, sticky="ew")
		self.etr_prev_ofic.bind("<Return>", lambda _e: self._actualizar_oficina_bien_seleccionado())

		# Fila 3: Botones de Acción sobre el bien seleccionado
		f_sub_acciones = tk.Frame(frame_datos_bien, bg="#ffffff")
		f_sub_acciones.grid(row=3, column=0, columnspan=6, pady=(8, 2), sticky="ew")

		btnImpUno = ttk.Button(f_sub_acciones, text="🖨️ Imprimir Esta Etiqueta", command=self.imprimir_seleccionado_lote)
		btnImpUno.pack(side="left", padx=(0, 6))

		btnGuardarOfi = ttk.Button(f_sub_acciones, text="💾 Aplicar Oficina al Bien", command=self._actualizar_oficina_bien_seleccionado)
		btnGuardarOfi.pack(side="left", padx=4)

		self.lbl_prev_info = ttk.Label(
			f_sub_acciones, 
			text="Seleccione un bien de la lista para ver su información y etiqueta", 
			font=("Segoe UI", 8, "italic"), 
			foreground="#64748b"
		)
		self.lbl_prev_info.pack(side="left", padx=8)

		frame_datos_bien.columnconfigure(1, weight=1)
		frame_datos_bien.columnconfigure(3, weight=1)
		frame_datos_bien.columnconfigure(5, weight=2)

		# Lado Derecho: Previsualización gráfica de la etiqueta (50mm x 25mm)
		frame_etiqueta_lateral = tk.Frame(frame_preview_panel, bg="#ffffff")
		frame_etiqueta_lateral.pack(side="right", fill="y", padx=(4, 2))

		frame_img_box = tk.Frame(frame_etiqueta_lateral, bg="#f1f5f9", bd=1, relief="solid", width=320, height=155)
		frame_img_box.pack_propagate(False)
		frame_img_box.pack(side="top", pady=2)

		self.lbl_lote_preview = tk.Label(
			frame_img_box, 
			text="Vista previa de la etiqueta\n\n(50mm x 25mm)", 
			bg="#f1f5f9", 
			fg="#94a3b8",
			font=("Segoe UI", 9)
		)
		self.lbl_lote_preview.pack(fill="both", expand=True)

		btnAjustarDiseno = ttk.Button(
			frame_etiqueta_lateral,
			text="📐 Diseñar / Ajustar Etiqueta...",
			command=self.abrir_disenador_etiqueta
		)
		btnAjustarDiseno.pack(side="top", fill="x", pady=(4, 0))

		# 3. Panel Inferior: Tabla de Etiquetas
		frame_tabla = ttk.LabelFrame(container, text=" 📋 Lista de Etiquetas a Generar ", style="Print.TLabelframe", padding=6)
		frame_tabla.pack(fill="both", expand=True, pady=(0, 4))

		columnas = ("num", "codpat", "codint", "deno", "acta_ant", "estado", "oficina")
		self.tree_lote = ttk.Treeview(frame_tabla, columns=columnas, show="headings", selectmode="extended", style="Print.Treeview")
		self.tree_lote.heading("num",      text="#")
		self.tree_lote.heading("codpat",   text="Cód. Patrimonial")
		self.tree_lote.heading("codint",   text="Cód. Interno")
		self.tree_lote.heading("deno",     text="Denominación")
		self.tree_lote.heading("acta_ant", text="Ficha / Acta")
		self.tree_lote.heading("estado",   text="Estado Inv.")
		self.tree_lote.heading("oficina",  text="Oficina Etiqueta")

		self.tree_lote.column("num",      width=35,  anchor="center")
		self.tree_lote.column("codpat",   width=120, anchor="w")
		self.tree_lote.column("codint",   width=90,  anchor="w")
		self.tree_lote.column("deno",     width=270, anchor="w")
		self.tree_lote.column("acta_ant", width=85,  anchor="center")
		self.tree_lote.column("estado",   width=95,  anchor="center")
		self.tree_lote.column("oficina",  width=180, anchor="w")

		self.tree_lote.tag_configure("odd",  background="#ffffff")
		self.tree_lote.tag_configure("even", background="#f8fafc")

		scroll_y = ttk.Scrollbar(frame_tabla, orient="vertical",   command=self.tree_lote.yview)
		scroll_x = ttk.Scrollbar(frame_tabla, orient="horizontal", command=self.tree_lote.xview)
		self.tree_lote.configure(yscrollcommand=scroll_y.set, xscrollcommand=scroll_x.set)

		self.tree_lote.grid(row=0, column=0, sticky="nsew")
		scroll_y.grid(row=0, column=1, sticky="ns")
		scroll_x.grid(row=1, column=0, sticky="ew")
		frame_tabla.rowconfigure(0, weight=1)
		frame_tabla.columnconfigure(0, weight=1)

		self.tree_lote.bind("<<TreeviewSelect>>", self._on_tree_lote_select)
		self.tree_lote.bind("<Double-Button-1>", lambda _e: self.previsualizar_seleccionado_lote())

		# Panel Inferior: Estadísticas y Botones de Acción
		frame_inferior = tk.Frame(container, bg="#f8fafc")
		frame_inferior.pack(fill="x", pady=(8, 0))

		# Chip contador
		frame_chip = tk.Frame(frame_inferior, bg="#eff6ff", bd=1, relief="solid")
		frame_chip.pack(side="left", padx=(0, 10), pady=2)
		self.lbl_total_lote = tk.Label(
			frame_chip,
			text="📋  0 etiquetas en lista",
			bg="#eff6ff",
			fg="#1d4ed8",
			font=("Segoe UI", 9, "bold"),
			padx=10, pady=4
		)
		self.lbl_total_lote.pack()

		btnQuitar = ttk.Button(frame_inferior, text="🗑️ Quitar Seleccionado(s)", command=self.quitar_seleccionados_lote)
		btnQuitar.pack(side="left", padx=6)

		btnNueva = ttk.Button(frame_inferior, text="✨ Limpiar / Nueva Lista", command=self.nueva_lista_lote)
		btnNueva.pack(side="left", padx=4)

		btnImpLote = ttk.Button(frame_inferior, text="🖨️ Imprimir Lote Completo", command=self.imprimir_lote)
		btnImpLote.pack(side="right", padx=5)

		btnGenPdf = ttk.Button(frame_inferior, text="📄 Generar PDF en Lote", command=self.generar_pdf_lote)
		btnGenPdf.pack(side="right", padx=5)

		self._cargar_oficinas_combobox()

	# -------------------------------------------------------------------------
	# LÓGICA DE BÚSQUEDA Y SINCRONIZACIÓN DE OFICINA (POPUP PREDICTIVO)
	# -------------------------------------------------------------------------
	def _cargar_oficinas_combobox(self):
		try:
			self.lote_oficinas_data = obtener_oficinas()
			if self.lote_oficinas_data:
				primera = self.lote_oficinas_data[0]
				self.lote_cod_oficina.set(primera["acta"])
				self.lote_oficina_sel.set(primera["oficina"])
				self.lote_ofic_personalizada.set(primera["oficina"])
		except Exception as e:
			print(f"Error cargando oficinas en lote: {e}")

	def _vincular_busqueda_predictiva_oficina(self, entry_widget):
		entry_widget.bind("<KeyRelease>", lambda e, w=entry_widget: self._on_keyrelease_oficina(e, w))
		entry_widget.bind("<Down>", lambda e, w=entry_widget: self._navegar_popup_oficina(1, w))
		entry_widget.bind("<Up>", lambda e, w=entry_widget: self._navegar_popup_oficina(-1, w))
		entry_widget.bind("<Next>", lambda e, w=entry_widget: self._navegar_popup_oficina(5, w))
		entry_widget.bind("<Prior>", lambda e, w=entry_widget: self._navegar_popup_oficina(-5, w))
		entry_widget.bind("<Return>", lambda e, w=entry_widget: self._confirmar_oficina_predictiva(w))
		entry_widget.bind("<Escape>", lambda e: self._cerrar_popup_oficinas())
		entry_widget.bind("<FocusOut>", lambda e: self.after(180, self._verificar_foco_popup_oficinas))

	def _formatear_item_oficina_predictiva(self, fila):
		acta, local, area, oficina, _dni, full_name = fila
		ofi_txt = oficina or "(Sin nombre de oficina)"
		detalles = []
		if area:
			detalles.append(area)
		if local and local != area:
			detalles.append(local)
		ubic_txt = f" — {' / '.join(detalles)}" if detalles else ""
		resp_txt = f"  |  👤 {full_name}" if full_name else ""
		return f"🏢 {ofi_txt}   [Ficha: {acta}]{ubic_txt}{resp_txt}"

	def _on_keyrelease_oficina(self, event, entry_widget):
		teclas_ignorar = {
			"Up", "Down", "Left", "Right", "Return", "Escape", "Tab",
			"Shift_L", "Shift_R", "Control_L", "Control_R", "Alt_L", "Alt_R",
			"Caps_Lock", "Prior", "Next", "Home", "End"
		}
		if event.keysym in teclas_ignorar:
			return

		termino = entry_widget.get().strip()
		if not termino:
			self._cerrar_popup_oficinas()
			return

		resultados = buscar_oficinas_predictivo(termino, limite=35)
		if not resultados:
			self._mostrar_popup_oficinas(entry_widget, [], termino)
			return

		self._mostrar_popup_oficinas(entry_widget, resultados, termino)

	def _desplegar_todas_oficinas(self, entry_widget=None):
		target = entry_widget or self.etr_lote_oficinas
		if self._popup_oficinas is not None and self._popup_oficinas.winfo_exists():
			self._cerrar_popup_oficinas()
			return
		termino = target.get().strip()
		# Si el texto actual coincide exactamente con la oficina ya cargada, mostrar todas para facilitar cambiar
		if termino and (termino == self.lote_ofic_personalizada.get().strip() or termino.startswith("[")):
			resultados = buscar_oficinas_predictivo("", limite=60)
		else:
			resultados = buscar_oficinas_predictivo(termino, limite=60)
		target.focus_set()
		self._mostrar_popup_oficinas(target, resultados, termino)

	def _mostrar_popup_oficinas(self, entry_widget, resultados, termino=""):
		self._resultados_oficinas_actuales = list(resultados)
		self._entry_activo_oficina = entry_widget

		if self._popup_oficinas is None or not self._popup_oficinas.winfo_exists():
			popup = tk.Toplevel(self)
			popup.wm_overrideredirect(True)
			popup.transient(self)
			popup.configure(bg="#2563eb")

			contenedor = tk.Frame(popup, bg="#ffffff", bd=0)
			contenedor.pack(fill="both", expand=True, padx=1, pady=1)

			header = tk.Frame(contenedor, bg="#eff6ff", padx=8, pady=4)
			header.pack(fill="x")

			self._lbl_popup_info = tk.Label(
				header,
				text="",
				bg="#eff6ff",
				fg="#1e40af",
				font=("Segoe UI", 8, "bold"),
				anchor="w"
			)
			self._lbl_popup_info.pack(side="left", fill="x", expand=True)

			lbl_Cerrar = tk.Label(
				header,
				text="✕",
				bg="#eff6ff",
				fg="#64748b",
				font=("Segoe UI", 8, "bold"),
				cursor="hand2",
				padx=4
			)
			lbl_Cerrar.pack(side="right")
			lbl_Cerrar.bind("<Button-1>", lambda _e: self._cerrar_popup_oficinas())

			body = tk.Frame(contenedor, bg="#ffffff")
			body.pack(fill="both", expand=True)

			scrollbar = ttk.Scrollbar(body, orient=tk.VERTICAL)
			listbox = tk.Listbox(
				body,
				font=("Segoe UI", 9),
				bg="#ffffff",
				fg="#0f172a",
				selectbackground="#2563eb",
				selectforeground="#ffffff",
				activestyle="none",
				highlightthickness=0,
				bd=0,
				yscrollcommand=scrollbar.set,
				cursor="hand2"
			)
			scrollbar.config(command=listbox.yview)
			listbox.pack(side="left", fill="both", expand=True, padx=(4, 0), pady=2)
			scrollbar.pack(side="right", fill="y", pady=2)

			listbox.bind("<ButtonRelease-1>", self._seleccionar_item_popup_oficina)
			listbox.bind("<Return>", self._seleccionar_item_popup_oficina)
			listbox.bind("<Escape>", lambda _e: self._cerrar_popup_oficinas())
			listbox.bind("<Motion>", self._on_hover_popup_oficina)

			self._popup_oficinas = popup
			self._listbox_oficinas = listbox

		listbox = self._listbox_oficinas
		listbox.delete(0, tk.END)

		if not resultados:
			self._lbl_popup_info.config(
				text=f"⚠️ Sin coincidencias para '{termino}'",
				fg="#b91c1c"
			)
			listbox.insert(tk.END, "  No se encontraron oficinas que coincidan con la búsqueda.")
			listbox.config(height=2, fg="#64748b")
		else:
			n = len(resultados)
			primera = resultados[0]
			self._lbl_popup_info.config(
				text=f"✨ {n} {'oficina encontrada' if n == 1 else 'oficinas encontradas'} — ↑↓ navegar | Enter o clic: cargar [Ficha {primera[0]}]",
				fg="#1e40af"
			)
			listbox.config(fg="#0f172a")
			for fila in resultados:
				listbox.insert(tk.END, self._formatear_item_oficina_predictiva(fila))
			listbox.config(height=min(max(n, 2), 9))
			listbox.selection_clear(0, tk.END)
			listbox.selection_set(0)
			listbox.activate(0)

		self._posicionar_popup_oficinas(entry_widget)

	def _posicionar_popup_oficinas(self, entry_widget):
		if self._popup_oficinas is None or not self._popup_oficinas.winfo_exists():
			return
		try:
			self.update_idletasks()
			x = entry_widget.winfo_rootx()
			y = entry_widget.winfo_rooty() + entry_widget.winfo_height() + 2
			ancho = max(entry_widget.winfo_width() + 34, 480)
			sw = self.winfo_screenwidth()
			if x + ancho > sw - 12:
				x = max(8, sw - ancho - 12)
			self._popup_oficinas.geometry(f"{ancho}x{self._popup_oficinas.winfo_reqheight()}+{x}+{y}")
			self._popup_oficinas.lift()
		except Exception:
			pass

	def _on_hover_popup_oficina(self, event):
		if not self._resultados_oficinas_actuales or self._listbox_oficinas is None:
			return
		idx = self._listbox_oficinas.nearest(event.y)
		if 0 <= idx < len(self._resultados_oficinas_actuales):
			self._listbox_oficinas.selection_clear(0, tk.END)
			self._listbox_oficinas.selection_set(idx)
			self._listbox_oficinas.activate(idx)
			fila = self._resultados_oficinas_actuales[idx]
			if self._lbl_popup_info is not None:
				self._lbl_popup_info.config(
					text=f"✨ Seleccionar: {fila[3] or fila[2]} [Ficha {fila[0]}] — Enter o clic para cargar"
				)

	def _navegar_popup_oficina(self, delta, entry_widget):
		if self._popup_oficinas is None or not self._popup_oficinas.winfo_exists():
			self._desplegar_todas_oficinas(entry_widget)
			return "break"

		if not self._resultados_oficinas_actuales or self._listbox_oficinas is None:
			return "break"

		sel = self._listbox_oficinas.curselection()
		actual = int(sel[0]) if sel else 0
		nuevo = max(0, min(len(self._resultados_oficinas_actuales) - 1, actual + delta))
		self._listbox_oficinas.selection_clear(0, tk.END)
		self._listbox_oficinas.selection_set(nuevo)
		self._listbox_oficinas.activate(nuevo)
		self._listbox_oficinas.see(nuevo)

		fila = self._resultados_oficinas_actuales[nuevo]
		if self._lbl_popup_info is not None:
			self._lbl_popup_info.config(
				text=f"✨ Seleccionar: {fila[3] or fila[2]} [Ficha {fila[0]}] — Presione Enter para cargar"
			)
		return "break"

	def _seleccionar_item_popup_oficina(self, _event=None):
		if not self._resultados_oficinas_actuales or self._listbox_oficinas is None:
			self._cerrar_popup_oficinas()
			return "break"

		sel = self._listbox_oficinas.curselection()
		idx = int(sel[0]) if sel else 0
		if 0 <= idx < len(self._resultados_oficinas_actuales):
			fila = self._resultados_oficinas_actuales[idx]
			self._aplicar_oficina_seleccionada(fila)
		return "break"

	def _confirmar_oficina_predictiva(self, entry_widget=None):
		target = entry_widget or self.etr_lote_oficinas
		if (
			self._popup_oficinas is not None
			and self._popup_oficinas.winfo_exists()
			and self._resultados_oficinas_actuales
		):
			return self._seleccionar_item_popup_oficina()

		termino = target.get().strip()
		if not termino:
			return "break"

		resultados = buscar_oficinas_predictivo(termino, limite=35)
		if not resultados:
			mb.showinfo(
				title="Búsqueda de Oficina",
				message=f"No se encontró ninguna oficina que coincida con '{termino}'.",
				parent=self
			)
			return "break"

		if len(resultados) == 1:
			self._aplicar_oficina_seleccionada(resultados[0])
		else:
			self._mostrar_popup_oficinas(target, resultados, termino)
		return "break"

	def _aplicar_oficina_seleccionada(self, fila_personal):
		acta, local, area, oficina, _dni, _full_name = fila_personal
		self._cerrar_popup_oficinas()
		nombre_ofi = (oficina or area or local or "").strip()
		self.lote_cod_oficina.set(str(acta or "").strip())
		self.lote_oficina_sel.set(nombre_ofi)
		self.lote_ofic_personalizada.set(nombre_ofi)
		self.cargar_bienes_lote()

	def _verificar_foco_popup_oficinas(self):
		if self._popup_oficinas is None or not self._popup_oficinas.winfo_exists():
			return
		try:
			foco = self.focus_get()
			if foco in (self.etr_lote_oficinas, self._listbox_oficinas, self.btn_desplegar_ofi):
				return
		except Exception:
			pass
		self._cerrar_popup_oficinas()

	def _cerrar_popup_oficinas(self, _event=None):
		if self._popup_oficinas is not None:
			try:
				if self._popup_oficinas.winfo_exists():
					self._popup_oficinas.destroy()
			except Exception:
				pass
		self._popup_oficinas = None
		self._listbox_oficinas = None
		self._lbl_popup_info = None
		self._resultados_oficinas_actuales = []

	def _on_cod_oficina_keyrelease(self, _event=None):
		self._cerrar_popup_oficinas()
		codigo = self.lote_cod_oficina.get().strip()
		if not codigo:
			return
		ofi = buscar_oficina_por_codigo(codigo, self.lote_oficinas_data)
		if ofi:
			self.lote_oficina_sel.set(ofi["oficina"])
			self.lote_ofic_personalizada.set(ofi["oficina"])

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
		if sel:
			coincidencias = buscar_oficinas_predictivo(sel, limite=5)
			if len(coincidencias) == 1:
				fila = coincidencias[0]
				self.lote_cod_oficina.set(str(fila[0] or "").strip())
				nombre_ofi = (fila[3] or fila[2] or fila[1] or "").strip()
				self.lote_oficina_sel.set(nombre_ofi)
				self.lote_ofic_personalizada.set(nombre_ofi)
				return str(fila[0] or "").strip()
		return None

	def _on_estado_filtro_select(self, _event=None):
		filtro_txt = self.lote_filtro_sel.get()
		if "nueva lista" in filtro_txt.lower():
			self.nueva_lista_lote()
			if hasattr(self, "lbl_prev_info"):
				self.lbl_prev_info.config(
					text="✨ Nueva lista vacía creada. Ingrese o escanee códigos en 'Cód. Bien' para agregarlos.",
					foreground="#2563eb"
				)
			if hasattr(self, "etr_lote_add"):
				self.etr_lote_add.focus_set()

	def cargar_bienes_lote(self):
		if (
			self._popup_oficinas is not None
			and self._popup_oficinas.winfo_exists()
			and self._resultados_oficinas_actuales
		):
			self._seleccionar_item_popup_oficina()
			return

		self._cerrar_popup_oficinas()

		filtro_txt = self.lote_filtro_sel.get()
		if "nueva lista" in filtro_txt.lower():
			self.nueva_lista_lote()
			if hasattr(self, "lbl_prev_info"):
				self.lbl_prev_info.config(
					text="✨ Nueva lista vacía creada. Ingrese o escanee códigos en 'Cód. Bien' para agregarlos.",
					foreground="#2563eb"
				)
			if hasattr(self, "etr_lote_add"):
				self.etr_lote_add.focus_set()
			return

		acta = self._resolver_acta_actual()
		if not acta:
			termino_ofi = self.lote_oficina_sel.get().strip()
			if termino_ofi:
				coincidencias = buscar_oficinas_predictivo(termino_ofi, limite=35)
				if len(coincidencias) > 1:
					self._mostrar_popup_oficinas(self.etr_lote_oficinas, coincidencias, termino_ofi)
					return
			mb.showerror(title="Atención", message="Ingrese un código de oficina válido o seleccione una oficina de la lista.", parent=self)
			return

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
			mb.showinfo(title="Resultado", message=f"No se encontraron bienes con el filtro '{filtro_txt}' para la oficina [{acta}].", parent=self)
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
			tag = "odd" if i % 2 == 1 else "even"
			self.tree_lote.insert(
				"",
				tk.END,
				tags=(tag,),
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
		n = len(self.lote_items)
		self.lbl_total_lote.config(text=f"📋  {n} {'etiqueta' if n == 1 else 'etiquetas'} en lista")

	def on_enter_codigo_lote(self, _event=None):
		"""
		Gestión con la tecla Enter en la caja de texto 'Cód. Bien':
		  - 1er Enter: Previsualiza los datos del bien y la etiqueta sin agregarlo a la lista.
		  - 2do Enter (sobre el mismo código): Agrega el bien a la lista y lo imprime si está activa la opción.
		"""
		codigo = self.lote_codigo_agregar.get().strip()
		if not codigo:
			mb.showwarning(title="Atención", message="Ingrese un código patrimonial o interno.", parent=self)
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
			mb.showerror(title="No encontrado", message=f"No se encontró ningún bien con el código '{codigo}'.", parent=self)
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
		codpat   = bien.get("codpat", "")   or bien.get("CodPat", "")
		codint   = bien.get("codint", "")   or bien.get("CodInt", "")
		deno     = bien.get("deno", "")     or bien.get("DenBien", "")
		acta_ant = bien.get("acta_ant", "") or bien.get("ActaAnt", "")
		inv_val  = bien.get("inv", "")      or bien.get("Inv", "")
		ofi_act  = bien.get("oficina_actual", "")
		ofi_ant  = bien.get("oficina_anterior", "")
		estado   = bien.get("estado_filtro", "") or bien.get("estado_bien", "") or ""
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
				foreground="#d97706"
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
			print(f"[GUI_PRINT][ERROR] Error generando vista previa de entrada para '{codigo}': {e}")
			traceback.print_exc()

		self.etr_lote_add.focus_set()
		return True

	def agregar_codigo_lote(self):
		"""Acción del botón ➕ Agregar (o confirmación directa)."""
		codigo = self.lote_codigo_agregar.get().strip()
		if not codigo:
			mb.showwarning(title="Atención", message="Ingrese un código patrimonial o interno.", parent=self)
			return

		if self._codigo_previsualizado == codigo and self._bien_pendiente_agregar is not None:
			bien_a_agregar = self._bien_pendiente_agregar
		else:
			bien_a_agregar = buscar_bien_por_codigo(codigo)
			if not bien_a_agregar:
				print(f"[GUI_PRINT][WARN] agregar_codigo_lote: no se encontró ningún bien con el código '{codigo}'")
				mb.showerror(title="No encontrado", message=f"No se encontró ningún bien con el código '{codigo}'.", parent=self)
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
		ofic_global  = self.lote_ofic_personalizada.get().strip()
		if ofic_detalle:
			bien["oficina_etiqueta"] = ofic_detalle
		elif ofic_global:
			bien["oficina_etiqueta"] = ofic_global

		# Verificar si ya existe en la lista
		cod_id = _resolver_codigo_impresion(bien)
		for item in self.lote_items:
			mismo_codpat = bool(item.get("codpat") and bien.get("codpat") and item["codpat"] == bien.get("codpat") and str(bien.get("codpat")).upper() != "NO CATALOGADO")
			mismo_codint = bool(item.get("codint") and bien.get("codint") and str(item["codint"]) == str(bien.get("codint")))
			if mismo_codpat or mismo_codint:
				if not mb.askyesno(title="Ya existe", message=f"El bien con código {cod_id} ya está en la lista.\n¿Desea agregarlo nuevamente?", parent=self):
					return False
				break

		# Si está activado imprimir al agregar, enviar inmediatamente a la impresora
		impreso_ok = False
		if self.imprimir_al_agregar.get():
			cod_print  = _resolver_codigo_impresion(bien)
			acta_print = bien.get("inv") or bien.get("acta_ant") or "1"
			ofic_print = bien.get("oficina_etiqueta")
			imp_activa = self.impresora_var.get().strip()
			print(
				f"[GUI_PRINT][_ejecutar_agregar_bien] Impresión automática activada -> "
				f"cod_print='{cod_print}', acta_print='{acta_print}', oficina='{ofic_print}', impresora='{imp_activa}', bien={bien}"
			)
			try:
				build_label(
					1,
					cod_print,
					acta_print,
					oficina_personalizada=ofic_print,
					bien_data=bien,
					impresora=imp_activa
				)
				impreso_ok = True
				print(f"[GUI_PRINT][_ejecutar_agregar_bien] Impresión automática exitosa para '{cod_print}' en '{imp_activa}'")
			except Exception as e:
				print(
					f"[GUI_PRINT][ERROR CRÍTICO] Falló la impresión automática al agregar -> "
					f"cod_print='{cod_print}', acta_print='{acta_print}', oficina='{ofic_print}', impresora='{imp_activa}', error={type(e).__name__}: {e}"
				)
				traceback.print_exc()
				mb.showerror(title="Error al imprimir", message=f"No se pudo imprimir la etiqueta automáticamente:\n{e}", parent=self)

		self.lote_items.append(bien)
		self._refrescar_tabla_lote()

		children = self.tree_lote.get_children()
		if children:
			last = children[-1]
			self.tree_lote.selection_set(last)
			self.tree_lote.see(last)
			self.previsualizar_seleccionado_lote()

		if hasattr(self, 'lbl_prev_info'):
			imp_txt = " (🖨️ Impreso)" if impreso_ok else (" (⚠️ Error al imprimir)" if self.imprimir_al_agregar.get() else "")
			self.lbl_prev_info.config(
				text=f"✅ Agregado a la lista: [{cod_id}]{imp_txt}", 
				foreground="#16a34a" if (not self.imprimir_al_agregar.get() or impreso_ok) else "#dc2626"
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
			imprimir_al_agregar_var=self.imprimir_al_agregar,
			impresora_var=self.impresora_var
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
			self.lbl_prev_info.config(text="Seleccione un bien de la lista para ver su información y etiqueta", foreground="#64748b")

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
				self.lbl_prev_info.config(text=f"✅ Oficina asignada: {nueva_ofic} ➔ Presione ENTER en 'Cód. Bien' para agregar{imp_aviso}", foreground="#16a34a")
			return

		seleccion = self.tree_lote.selection()
		if not seleccion:
			mb.showwarning(title="Atención", message="Seleccione un bien de la tabla para modificar su oficina.", parent=self)
			return
		item_idx = self.tree_lote.index(seleccion[0])
		if item_idx < 0 or item_idx >= len(self.lote_items):
			return
		self.lote_items[item_idx]["oficina_etiqueta"] = nueva_ofic
		self.tree_lote.set(seleccion[0], column="oficina", value=nueva_ofic)
		self.previsualizar_seleccionado_lote()
		if hasattr(self, 'lbl_prev_info'):
			self.lbl_prev_info.config(text=f"✅ Oficina actualizada: {nueva_ofic}", foreground="#16a34a")

	def imprimir_seleccionado_lote(self):
		seleccion = self.tree_lote.selection()
		if not seleccion:
			mb.showwarning(title="Atención", message="Seleccione un bien de la tabla para imprimir.", parent=self)
			return
		item_idx = self.tree_lote.index(seleccion[0])
		if item_idx < 0 or item_idx >= len(self.lote_items):
			return
		item = self.lote_items[item_idx]
		cod  = _resolver_codigo_impresion(item)
		acta = item.get("inv", "") or item.get("acta_ant", "") or "1"
		ofic = self.prev_ofic_etiqueta.get().strip() or item.get("oficina_etiqueta", "")
		imp_activa = self.impresora_var.get().strip()
		print(f"[GUI_PRINT][imprimir_seleccionado_lote] Imprimiendo item individual -> cod='{cod}', acta='{acta}', ofic='{ofic}', impresora='{imp_activa}', item={item}")
		try:
			build_label(1, cod, acta, oficina_personalizada=ofic, bien_data=item, impresora=imp_activa)
			if hasattr(self, 'lbl_prev_info'):
				self.lbl_prev_info.config(text=f"🖨️ Etiqueta impresa para: {cod} ({imp_activa})", foreground="#2563eb")
		except Exception as e:
			print(f"[GUI_PRINT][ERROR] Error en imprimir_seleccionado_lote para '{cod}': {e}")
			traceback.print_exc()
			mb.showerror(title="Error al imprimir", message=f"No se pudo imprimir la etiqueta:\n{e}", parent=self)

	def quitar_seleccionados_lote(self):
		seleccion = self.tree_lote.selection()
		if not seleccion:
			mb.showwarning(title="Atención", message="Seleccione al menos un bien de la tabla para quitar.", parent=self)
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
		codpat   = item.get("codpat", "")   or item.get("CodPat", "")
		codint   = item.get("codint", "")   or item.get("CodInt", "")
		deno     = item.get("deno", "")     or item.get("DenBien", "")
		acta_ant = item.get("acta_ant", "") or item.get("ActaAnt", "")
		inv_val  = item.get("inv", "")      or item.get("Inv", "")
		ofi_act  = item.get("oficina_actual", "")
		ofi_ant  = item.get("oficina_anterior", "")
		estado   = item.get("estado_filtro", "") or item.get("estado_bien", "") or ""
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
				foreground="#2563eb"
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
			mb.showwarning(title="Atención", message="La lista está vacía. Cargue bienes de una oficina o agregue códigos.", parent=self)
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
				message=f"Se generó el PDF con {len(self.lote_items)} etiquetas en:\n{pdf_path}\n\n¿Desea abrir el archivo ahora?",
				parent=self
			)
			if abrir:
				try:
					os.startfile(pdf_path)
				except Exception as err:
					print(f"[GUI_PRINT][ERROR] Error abriendo visor PDF '{pdf_path}': {err}")
					traceback.print_exc()
					mb.showerror(title="Error al abrir", message=f"No se pudo abrir el visor de PDF:\n{err}", parent=self)

		except Exception as e:
			print(f"[GUI_PRINT][ERROR] Error en generar_pdf_lote: {e}")
			traceback.print_exc()
			mb.showerror(title="Error", message=f"Ocurrió un error al generar el lote en PDF:\n{e}", parent=self)

	def imprimir_lote(self):
		if not self.lote_items:
			mb.showwarning(title="Atención", message="La lista está vacía. Cargue bienes de una oficina o agregue códigos.", parent=self)
			return

		imp_activa = self.impresora_var.get().strip()
		confirm = mb.askyesno(
			title="Confirmar Impresión en Lote",
			message=f"Se enviarán {len(self.lote_items)} etiquetas a la impresora:\n'{imp_activa or 'Predeterminada'}'\n\n¿Desea continuar con la impresión?",
			parent=self
		)
		if not confirm:
			return

		ofic_global = self.lote_ofic_personalizada.get().strip()
		print(f"[GUI_PRINT][imprimir_lote] Enviando lote de {len(self.lote_items)} ítems a imprimir (oficina_global='{ofic_global}', impresora='{imp_activa}')")
		try:
			pdf_path = build_label_batch(
				self.lote_items, 
				valor=1, 
				oficina_personalizada_global=ofic_global if ofic_global else None,
				impresora=imp_activa
			)
			if pdf_path:
				print(f"[GUI_PRINT][imprimir_lote] Lote enviado exitosamente: '{pdf_path}'")
				mb.showinfo(title="Impresión enviada", message=f"Se han enviado {len(self.lote_items)} etiquetas a la cola de impresión ({imp_activa or 'Predeterminada'}).", parent=self)
		except Exception as e:
			print(f"[GUI_PRINT][ERROR] Error en imprimir_lote: {e}")
			traceback.print_exc()
			mb.showerror(title="Error de impresión", message=f"No se pudo enviar el lote a la impresora:\n{e}", parent=self)

	# -------------------------------------------------------------------------
	# PESTAÑA 2: AJUSTES Y CONFIGURACIÓN
	# -------------------------------------------------------------------------
	def tab_ajustes_init(self):
		self.ent = tk.StringVar()
		self.per = tk.StringVar()

		outer = tk.Frame(self.tab_ajustes, bg="#f8fafc")
		outer.pack(fill="both", expand=True, padx=16, pady=16)

		# ---- Card izquierda: Datos de la Entidad ----
		card_ent = ttk.LabelFrame(outer, text=" 🏢 Datos de la Entidad ", style="Print.TLabelframe", padding=14)
		card_ent.pack(side="left", fill="both", expand=True, padx=(0, 10))

		ttk.Label(card_ent, text="Entidad:", font=("Segoe UI", 9)).grid(row=0, column=0, sticky="w", pady=8)
		ttk.Entry(card_ent, textvariable=self.ent, width=38).grid(row=0, column=1, sticky="ew", pady=8, padx=(8, 0))

		ttk.Label(card_ent, text="Periodo:", font=("Segoe UI", 9)).grid(row=1, column=0, sticky="w", pady=8)
		ttk.Combobox(
			card_ent,
			values=[2020, 2021, 2022, 2023, 2024, 2025, 2026],
			textvariable=self.per,
			state="readonly",
			width=36
		).grid(row=1, column=1, sticky="ew", pady=8, padx=(8, 0))

		ttk.Button(card_ent, text="💾 Guardar Ajustes", command=self.actualizar).grid(
			row=2, column=1, sticky="e", pady=(12, 0), padx=(8, 0)
		)

		ttk.Separator(card_ent, orient="horizontal").grid(row=3, column=0, columnspan=2, sticky="ew", pady=(14, 10))

		ttk.Label(card_ent, text="Impresora:", font=("Segoe UI", 9)).grid(row=4, column=0, sticky="w", pady=6)
		frame_imp_ajustes = tk.Frame(card_ent, bg="#ffffff")
		frame_imp_ajustes.grid(row=4, column=1, sticky="ew", pady=6, padx=(8, 0))
		frame_imp_ajustes.columnconfigure(0, weight=1)

		self.cbx_impresora_ajustes = ttk.Combobox(
			frame_imp_ajustes,
			textvariable=self.impresora_var,
			state="readonly",
			width=32
		)
		self.cbx_impresora_ajustes.grid(row=0, column=0, sticky="ew")
		self.cbx_impresora_ajustes.bind("<<ComboboxSelected>>", self._on_impresora_seleccionada)

		ttk.Button(
			frame_imp_ajustes,
			text="🔄",
			width=3,
			command=self._cargar_impresoras
		).grid(row=0, column=1, padx=(4, 0))

		ttk.Separator(card_ent, orient="horizontal").grid(row=5, column=0, columnspan=2, sticky="ew", pady=(14, 10))

		ttk.Label(card_ent, text="Diseño y Formato de Etiqueta:", font=("Segoe UI", 9, "bold")).grid(
			row=6, column=0, columnspan=2, sticky="w", pady=(0, 8)
		)
		ttk.Button(
			card_ent,
			text="📐 Diseñador de Etiqueta (Editar Posiciones y Tamaños)...",
			command=self.abrir_disenador_etiqueta
		).grid(row=7, column=0, columnspan=2, sticky="ew", pady=6)

		card_ent.columnconfigure(1, weight=1)

		# ---- Card derecha: Logo ----
		card_logo = ttk.LabelFrame(outer, text=" 🖼️ Logo de la Etiqueta ", style="Print.TLabelframe", padding=14)
		card_logo.pack(side="right", fill="y", padx=(10, 0))

		frame_img_box = tk.Frame(card_logo, bg="#f1f5f9", bd=1, relief="solid", width=200, height=140)
		frame_img_box.pack_propagate(False)
		frame_img_box.pack(pady=(0, 8))

		self.img_label = tk.Label(frame_img_box, bg="#f1f5f9", fg="#94a3b8", text="Sin imagen", font=("Segoe UI", 9))
		self.img_label.pack(fill="both", expand=True)

		datos = datos_iniciales()
		if datos and len(datos) > 2:
			self.ent.set(str(datos[1]))
			self.per.set(str(datos[2]))

	def _cargar_impresoras(self):
		"""Obtiene las impresoras del sistema y sincroniza los comboboxes de lote y ajustes."""
		try:
			impresoras, predeterminada = obtener_impresoras_sistema()
			guardada = obtener_impresora_configurada(self.config_path)
			seleccion = guardada or predeterminada or (impresoras[0] if impresoras else "")
			self.impresora_var.set(seleccion)

			valores = impresoras if impresoras else ([seleccion] if seleccion else ["(No se encontraron impresoras)"])
			if hasattr(self, 'cbx_impresora_lote'):
				self.cbx_impresora_lote['values'] = valores
			if hasattr(self, 'cbx_impresora_ajustes'):
				self.cbx_impresora_ajustes['values'] = valores
			print(f"[GUI_PRINT] Impresoras cargadas: {valores} | Activa: '{seleccion}'")
		except Exception as e:
			print(f"[GUI_PRINT][ERROR] Error al cargar impresoras del sistema: {e}")

	def _on_impresora_seleccionada(self, _event=None):
		"""Persiste la impresora seleccionada en config.ini y sincroniza ambos comboboxes."""
		nom = self.impresora_var.get().strip()
		if nom and nom != "(No se encontraron impresoras)":
			guardar_impresora_configurada(nom, self.config_path)
			print(f"[GUI_PRINT] Impresora seleccionada guardada: '{nom}'")
			if hasattr(self, 'lbl_prev_info'):
				self.lbl_prev_info.config(text=f"🖨️ Impresora activa: {nom}", foreground="#2563eb")

	def load_config(self):
		if os.path.exists(self.config_path):
			self.config.read(self.config_path)
			if 'Settings' in self.config:
				self.img_label_path = self.config['Settings'].get('img_label_path', '')
				imp_cfg = self.config['Settings'].get('printer_name', '').strip()
				if imp_cfg:
					self.impresora_var.set(imp_cfg)

	def cargar_imagen_guardada(self):
		if self.img_label_path and os.path.exists(self.img_label_path):
			try:
				image = Image.open(self.img_label_path)
				image.thumbnail((180, 180))
				self.photo = ImageTk.PhotoImage(image)
				self.img_label.config(image=self.photo, text="")
			except Exception as e:
				print(f"Error cargando imagen de ajustes: {e}")

	def actualizar(self):
		lista = [self.ent.get(), self.per.get()]
		try:
			actualizar_datos(1, lista)
			nom_imp = self.impresora_var.get().strip()
			if nom_imp and nom_imp != "(No se encontraron impresoras)":
				guardar_impresora_configurada(nom_imp, self.config_path)
			mb.showinfo(title="Acontar S.A.C.", message="¡Ajustes actualizados con éxito!", parent=self)
		except Exception as e:
			mb.showerror(title="Error", message=f"Ocurrió un error: {e}", parent=self)
		finally:
			self.focus_set()

	def abrir_disenador_etiqueta(self):
		"""Abre la ventana del diseñador y editor interactivo de etiquetas."""
		from gui.gui_label_designer import Window_label_designer
		Window_label_designer(self, on_save_callback=self._on_layout_actualizado)

	def _on_layout_actualizado(self):
		"""Callback ejecutado al guardar cambios en el diseñador para refrescar previsualizaciones."""
		try:
			from db.query import datos_iniciales
			datos = datos_iniciales()
			if datos and len(datos) > 2:
				if hasattr(self, 'ent') and datos[1]:
					self.ent.set(str(datos[1]))
				if hasattr(self, 'per') and datos[2]:
					self.per.set(str(datos[2]))

			if hasattr(self, 'tree_lote') and self.tree_lote.selection():
				self.previsualizar_seleccionado_lote()
			elif hasattr(self, '_bien_pendiente_agregar') and self._bien_pendiente_agregar is not None:
				codigo = self.lote_codigo_agregar.get().strip()
				if codigo:
					self.previsualizar_codigo_entrada(codigo)
		except Exception as e:
			print(f"Error al refrescar tras actualizar diseño: {e}")


# =============================================================================
# VENTANA EMERGENTE (POPUP): BÚSQUEDA INDIVIDUAL Y AGREGAR A LA LISTA
# =============================================================================
class Window_individual_popup(tk.Toplevel):
	"""Ventana emergente para consultar bien en detalle y agregarlo a la lista de impresión."""
	def __init__(self, parent, valor=1, codigo_inicial=None, callback_agregar=None, imprimir_al_agregar_var=None, impresora_var=None):
		super().__init__(parent)
		self.parent = parent
		self.valor = valor or 1
		self.callback_agregar = callback_agregar
		self.imprimir_al_agregar_var = imprimir_al_agregar_var
		self.impresora_var = impresora_var if impresora_var is not None else tk.StringVar(value=obtener_impresora_configurada())
		self.title("Búsqueda Detallada — Agregar Bien a la Lista")
		self.geometry("860x550")
		self.minsize(780, 480)
		self.configure(bg="#f8fafc")
		self.transient(parent)
		self.grab_set()

		self._cargar_icono()
		self._centrar_ventana(860, 550)

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

	# -------------------------------------------------------------------------
	def _cargar_icono(self):
		try:
			from utils.helpers import resource_path
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

	def _crear_widgets(self):
		contenedor = tk.Frame(self, bg="#f8fafc")
		contenedor.pack(fill="both", expand=True, padx=10, pady=10)

		# Marco Izquierdo: Formulario
		frame_form = tk.Frame(contenedor, bg="#ffffff", bd=1, relief="solid", padx=10, pady=10)
		frame_form.pack(side="left", fill="both", expand=True, padx=(0, 8))

		# Marco Derecho: Vista Previa
		frame_der = tk.Frame(contenedor, bg="#ffffff", bd=1, relief="solid", padx=8, pady=8)
		frame_der.pack(side="right", fill="y")

		# Caja de imagen preview
		frame_popup_img = tk.Frame(frame_der, bg="#f1f5f9", bd=1, relief="solid", width=320, height=160)
		frame_popup_img.pack_propagate(False)
		frame_popup_img.pack(fill="none", expand=False, pady=4)

		self.lbl_preview = tk.Label(
			frame_popup_img,
			text="Vista previa de la etiqueta\n\n(50mm x 25mm)",
			bg="#f1f5f9",
			fg="#94a3b8",
			font=("Segoe UI", 9)
		)
		self.lbl_preview.pack(fill="both", expand=True)

		if self.valor == 1:
			# Labels
			ttk.Label(frame_form, text="Código Pat/Int:").grid(column=0, row=0, padx=4, pady=4, sticky=EW)
			ttk.Label(frame_form, text="Ficha:").grid(column=0, row=1, padx=4, pady=4, sticky=EW)
			ttk.Label(frame_form, text="Denominación:").grid(column=0, row=2, padx=4, pady=4, sticky=EW)
			ttk.Label(frame_form, text="Código Interno:").grid(column=0, row=3, padx=4, pady=4, sticky=EW)
			ttk.Label(frame_form, text="Código Patrimonial:").grid(column=0, row=4, padx=4, pady=4, sticky=EW)
			ttk.Label(frame_form, text="Ubicación actual:").grid(column=0, row=5, padx=4, pady=4, sticky=EW)
			ttk.Label(frame_form, text="Ubicación anterior:").grid(column=0, row=6, padx=4, pady=4, sticky=EW)
			ttk.Label(frame_form, text="Oficina etiqueta:").grid(column=0, row=7, padx=4, pady=4, sticky=EW)

			# Entrys
			self.etrCod = ttk.Entry(frame_form, textvariable=self.codi, width=18)
			self.etrCod.grid(column=1, row=0, padx=4, pady=4, sticky=EW)
			self.etrCod.bind("<Return>", lambda _e: self.buscar())

			self.etrAct = ttk.Entry(frame_form, textvariable=self.acta)
			self.etrAct.grid(column=1, row=1, padx=4, pady=4, sticky=EW)
			self.acta.trace_add("write", self._acta_cambiada)

			ttk.Button(frame_form, text="🔍 Buscar",       command=self.buscar).grid(      column=2, row=0, padx=4, pady=4, sticky="nsew")
			ttk.Button(frame_form, text="👁️ Previsualizar", command=self.preview_pdf).grid(column=2, row=1, padx=4, pady=4, sticky="nsew")

			ttk.Entry(frame_form, textvariable=self.deno).grid(column=1, row=2, columnspan=2, padx=4, pady=4, sticky=EW)
			ttk.Entry(frame_form, textvariable=self.codI).grid(column=1, row=3, columnspan=2, padx=4, pady=4, sticky=EW)
			ttk.Entry(frame_form, textvariable=self.codP).grid(column=1, row=4, columnspan=2, padx=4, pady=4, sticky=EW)
			ttk.Entry(frame_form, textvariable=self.inve).grid(column=1, row=5, columnspan=2, padx=4, pady=4, sticky=EW)
			ttk.Entry(frame_form, textvariable=self.ubic).grid(column=1, row=6, columnspan=2, padx=4, pady=4, sticky=EW)

			# OFICINA DIRECTAMENTE EDITABLE (Sin checkbox)
			self.etrOfi = ttk.Entry(frame_form, textvariable=self.ofic)
			self.etrOfi.grid(column=1, row=7, columnspan=2, padx=4, pady=4, sticky=EW)
			self.etrOfi.bind("<Return>", lambda _e: self.preview_pdf())

		elif self.valor == 2:
			ttk.Label(frame_form, text="Item:").grid(column=0, row=0, padx=4, pady=4, sticky=EW)
			ttk.Label(frame_form, text="Local:").grid(column=0, row=1, padx=4, pady=4, sticky=EW)
			ttk.Label(frame_form, text="Área:").grid(column=0, row=2, padx=4, pady=4, sticky=EW)
			ttk.Label(frame_form, text="Oficina etiqueta:").grid(column=0, row=3, padx=4, pady=4, sticky=EW)
			ttk.Label(frame_form, text="Denominación:").grid(column=0, row=4, padx=4, pady=4, sticky=EW)

			self.etrCod = ttk.Entry(frame_form, textvariable=self.codi, width=18)
			self.etrCod.grid(column=1, row=0, padx=4, pady=4, sticky=EW)
			self.etrCod.bind("<Return>", lambda _e: self.buscar_sobrante())

			ttk.Button(frame_form, text="🔍 Buscar", command=self.buscar_sobrante).grid(column=2, row=0, padx=4, pady=4, sticky="nsew")

			ttk.Entry(frame_form, textvariable=self.loca).grid(column=1, row=1, columnspan=2, padx=4, pady=4, sticky=EW)
			ttk.Entry(frame_form, textvariable=self.area).grid(column=1, row=2, columnspan=2, padx=4, pady=4, sticky=EW)
			self.etrOfi = ttk.Entry(frame_form, textvariable=self.ofic)
			self.etrOfi.grid(column=1, row=3, columnspan=2, padx=4, pady=4, sticky=EW)
			ttk.Entry(frame_form, textvariable=self.deno).grid(column=1, row=4, columnspan=2, padx=4, pady=4, sticky=EW)

		frame_form.columnconfigure(1, weight=1)

		# Marco de Botones de Acción inferior
		frame_acciones = tk.Frame(self, bg="#f1f5f9", bd=0)
		frame_acciones.pack(fill="x", side="bottom", padx=10, pady=(0, 10))

		# Separador visual
		sep = ttk.Separator(self, orient="horizontal")
		sep.pack(fill="x", side="bottom", padx=10, pady=(0, 2))

		chkImp = ttk.Checkbutton(
			frame_acciones, 
			text="🖨️ Imprimir al agregar", 
			variable=self.imprimir_aqui,
			command=self._sync_imprimir_var
		)
		chkImp.pack(side="left", padx=(10, 4), pady=8)

		ttk.Label(frame_acciones, text="Impresora:").pack(side="left", padx=(6, 2))
		impresoras_sys, _ = obtener_impresoras_sistema()
		cbx_imp_pop = ttk.Combobox(
			frame_acciones,
			textvariable=self.impresora_var,
			values=impresoras_sys or ([self.impresora_var.get()] if self.impresora_var.get() else []),
			state="readonly",
			width=22
		)
		cbx_imp_pop.pack(side="left", padx=2)
		cbx_imp_pop.bind("<<ComboboxSelected>>", lambda _e: guardar_impresora_configurada(self.impresora_var.get()))

		btnCerrar = ttk.Button(frame_acciones, text="Cerrar", command=self.destroy)
		btnCerrar.pack(side="right", padx=5, pady=8)

		self.btnAgregar = ttk.Button(frame_acciones, text="➕ Agregar a la Lista de Lote", command=self.agregar_a_lista, default="active")
		self.btnAgregar.pack(side="right", padx=5, pady=8)
		self.btnAgregar.bind("<Return>",   lambda _e: self.agregar_a_lista())
		self.btnAgregar.bind("<KP_Enter>", lambda _e: self.agregar_a_lista())

		self.btnImpYAdd = ttk.Button(frame_acciones, text="🖨️ Imprimir y Agregar", command=self.imprimir_y_agregar)
		self.btnImpYAdd.pack(side="right", padx=5, pady=8)
		self.btnImpYAdd.bind("<Return>",   lambda _e: self.imprimir_y_agregar())
		self.btnImpYAdd.bind("<KP_Enter>", lambda _e: self.imprimir_y_agregar())

		self.lbl_estado = ttk.Label(frame_acciones, text="", foreground="#16a34a", font=("Segoe UI", 9, "italic"))
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
			mb.showerror(title="Atención", message="Ingrese un código a consultar.", parent=self)
			return False
		try:
			r = mostrar_datos_print(codigo)
			if not r:
				print(f"[GUI_PRINT][Popup.buscar] No se encontraron datos para el código '{codigo}'")
				mb.showerror(title="No encontrado", message="No se encontraron datos para el código ingresado.", parent=self)
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
			print(f"[GUI_PRINT][ERROR en Popup.buscar] Código='{codigo}': {e}")
			traceback.print_exc()
			mb.showerror(title="Error", message=f"No se pudieron consultar los datos:\n{e}", parent=self)
			return False

	def buscar_sobrante(self):
		codigo = self.codi.get().strip()
		if not codigo:
			mb.showerror(title="Atención", message="Ingrese un código de bien sobrante.", parent=self)
			return False
		try:
			r = mostrar_datos_sobrante(codigo)
			if not r:
				print(f"[GUI_PRINT][Popup.buscar_sobrante] No se encontraron datos de sobrante para '{codigo}'")
				mb.showerror(title="Error", message="No se encontraron datos para el código de sobrante.", parent=self)
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
			print(f"[GUI_PRINT][ERROR en Popup.buscar_sobrante] Código='{codigo}': {e}")
			traceback.print_exc()
			mb.showerror(title="Error", message=f"No se pudo consultar el sobrante:\n{e}", parent=self)
			return False

	def preview_pdf(self):
		bien_tmp = {
			"codpat": self.codP.get().strip(),
			"codint": self.codI.get().strip(),
			"deno": self.deno.get().strip(),
		}
		codigo = _resolver_codigo_impresion(bien_tmp) or self.codi.get().strip()
		acta = self.acta.get().strip() or "1"
		if not codigo:
			return False
		try:
			pdf_path = build_label(0, codigo, acta, oficina_personalizada=self.ofic.get().strip(), bien_data=bien_tmp)
			self._mostrar_pdf(pdf_path)
			return True
		except Exception as e:
			print(f"[GUI_PRINT][ERROR en Popup.preview_pdf] Código='{codigo}': {e}")
			traceback.print_exc()
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
			print(f"[GUI_PRINT][ERROR mostrando PDF en popup] Ruta='{pdf_path}': {e}")
			traceback.print_exc()

	def agregar_a_lista(self):
		codpat = self.codP.get().strip() or self.codi.get().strip()
		codint = self.codI.get().strip() or self.codi.get().strip()
		deno   = self.deno.get().strip()

		if not codpat and not codint:
			mb.showwarning(title="Atención", message="Debe buscar o ingresar al menos un código válido antes de agregar.", parent=self)
			return

		ofic_val = self.ofic.get().strip()
		acta_val = self.acta.get().strip() or "1"

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

		# Imprimir si el checkbox está activo
		if self.imprimir_aqui.get():
			cod_print = _resolver_codigo_impresion(bien_dict)
			imp_activa = self.impresora_var.get().strip()
			print(f"[GUI_PRINT][Popup.agregar_a_lista] Imprimiendo etiqueta -> cod_print='{cod_print}', acta='{acta_val}', oficina='{ofic_val}', impresora='{imp_activa}'")
			try:
				build_label(1, cod_print, acta_val, oficina_personalizada=ofic_val, bien_data=bien_dict, impresora=imp_activa)
			except Exception as e:
				print(f"[GUI_PRINT][ERROR en Popup.agregar_a_lista] Error al imprimir '{cod_print}': {e}")
				traceback.print_exc()
				mb.showerror(title="Error al imprimir", message=f"No se pudo imprimir la etiqueta:\n{e}", parent=self)

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
